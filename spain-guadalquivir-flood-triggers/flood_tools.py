"""Shared functions for the Guadalquivir flood-trigger case (MIT licence).

* fetch_cedex()        download the public CEDEX gauge files (once), checked by SHA-256 (rebuild only)
* lmoments()           sample L-moments (Hosking and Wallis, 1997)
* GEV / LP3            fitted by L-moments; quantile = return level
* fit_best()           both fits, the better one chosen by probability-plot correlation (Gringorten positions)
* bootstrap_band()     percentile bootstrap band for each return level
* trigger_score()      flood years caught, missed and paid in error by a trigger
"""
from __future__ import annotations

import hashlib
import math
import pathlib
import urllib.request

import numpy as np
from scipy import special, stats

CEDEX = "https://ceh-flumen64.cedex.es/anuarioaforos/anuario-2021-2022/GUADALQUIVIR%5C"
CEDEX_FILES = {  # Anuario de Aforos 2021-2022, Guadalquivir basin (pinned 29 Oct 2026)
    "estaf.csv": "862e812acb71efb1decc1a4ac3b2c5bdd8f66e9a6f8458a9d7f00156cef42ac8",
    "afliq.csv": "a32995d11447a3b57d642772a14dc046cb5a397ddc5200813d76d39d77ed1ed3",
}


def fetch_cedex(name: str, sha256: str, folder="cedex_cache") -> pathlib.Path:
    """Download one CEDEX file (once) and check its SHA-256. Some servers refuse cloud machines: run it on your own connection."""
    d = pathlib.Path(folder); d.mkdir(exist_ok=True)
    p = d / name
    if not p.exists():
        urllib.request.urlretrieve(CEDEX + name, p)
    h = hashlib.sha256(p.read_bytes()).hexdigest()
    if h != sha256:
        raise ValueError(f"{name}: checksum {h} differs from the published {sha256}")
    return p


# ----------------------------------------------------------------------------- L-moments
def lmoments(x):
    """l1, l2, t3, t4 from probability-weighted moments of the sorted sample."""
    x = np.sort(np.asarray(x, dtype=float)); n = len(x)
    if n < 5 or np.ptp(x) == 0:
        raise ValueError("need at least 5 values that are not all equal")
    j = np.arange(1, n + 1)
    b0 = x.mean()
    b1 = np.sum((j - 1) / (n - 1) * x) / n
    b2 = np.sum((j - 1) * (j - 2) / ((n - 1) * (n - 2)) * x) / n
    b3 = np.sum((j - 1) * (j - 2) * (j - 3) / ((n - 1) * (n - 2) * (n - 3)) * x) / n
    l1, l2, l3, l4 = b0, 2 * b1 - b0, 6 * b2 - 6 * b1 + b0, 20 * b3 - 30 * b2 + 12 * b1 - b0
    return l1, l2, l3 / l2, l4 / l2


class GEV:
    """Generalised extreme value, Hosking's shape k (k > 0: bounded upper tail). Same sign as SciPy's genextreme c."""

    def __init__(self, xi, alpha, k):
        self.xi, self.alpha, self.k = xi, alpha, k

    @classmethod
    def fit(cls, x):
        l1, l2, t3, _ = lmoments(x)
        c = 2 / (3 + t3) - math.log(2) / math.log(3)
        k = 7.8590 * c + 2.9554 * c * c  # Hosking, Wallis and Wood (1985)
        if abs(k) < 1e-6:
            a = l2 / math.log(2)
            return cls(l1 - 0.5772156649 * a, a, 0.0)
        a = l2 * k / ((1 - 2 ** -k) * special.gamma(1 + k))
        return cls(l1 - a * (1 - special.gamma(1 + k)) / k, a, k)

    def quantile(self, f):
        y = -np.log(np.asarray(f, dtype=float))
        return self.xi - self.alpha * np.log(y) if self.k == 0 else self.xi + self.alpha / self.k * (1 - y ** self.k)


class LP3:
    """Log-Pearson type III: Pearson III fitted by L-moments to log10 of the flows."""

    def __init__(self, mu, sigma, gamma):
        self.mu, self.sigma, self.gamma = mu, sigma, gamma

    @classmethod
    def fit(cls, x):
        x = np.asarray(x, dtype=float)
        if np.any(x <= 0):
            raise ValueError("LP3 needs flows above zero")
        l1, l2, t3, _ = lmoments(np.log10(x))
        a3 = abs(t3)
        if a3 < 1e-6:
            return cls(l1, l2 * math.sqrt(math.pi), 0.0)
        if a3 < 1 / 3:  # Hosking and Wallis (1997), appendix A.9: alpha from tau3
            z = 3 * math.pi * t3 * t3
            alpha = (1 + 0.2906 * z) / (z + 0.1882 * z * z + 0.0442 * z ** 3)
        else:
            z = 1 - a3
            alpha = (0.36067 * z - 0.59567 * z * z + 0.25361 * z ** 3) / (1 - 2.78861 * z + 2.56096 * z * z - 0.77045 * z ** 3)
        gamma = math.copysign(2 / math.sqrt(alpha), t3)
        sigma = l2 * math.sqrt(math.pi) * math.sqrt(alpha) * math.exp(special.gammaln(alpha) - special.gammaln(alpha + 0.5))
        return cls(l1, sigma, gamma)

    def quantile(self, f):
        return 10 ** stats.pearson3.ppf(np.asarray(f, dtype=float), self.gamma, loc=self.mu, scale=self.sigma)


def ppcc(dist, x) -> float:
    """Probability-plot correlation with Gringorten plotting positions."""
    x = np.sort(np.asarray(x, dtype=float)); n = len(x)
    p = (np.arange(1, n + 1) - 0.44) / (n + 0.12)
    return float(np.corrcoef(x, dist.quantile(p))[0, 1])


def fit_best(x):
    """Both fits where they apply (LP3 needs every flow above zero); the better one by PPCC."""
    fits = {"GEV": GEV.fit(x)}
    if np.all(np.asarray(x) > 0):
        fits["LP3"] = LP3.fit(x)
    best = max(fits, key=lambda m: ppcc(fits[m], x))
    return best, fits


def level(dist, period) -> float:
    return float(dist.quantile(1 - 1 / period))


def bootstrap_band(x, method: str, periods, n_boot=300, band=0.9, seed=0) -> dict:
    """Resample the annual maxima, refit, and take the percentiles of each return level."""
    rng = np.random.default_rng(seed); x = np.asarray(x, dtype=float)
    cls = GEV if method == "GEV" else LP3
    out = []
    for _ in range(n_boot):
        s = rng.choice(x, size=len(x), replace=True)
        try:
            d = cls.fit(s); out.append([level(d, t) for t in periods])
        except ValueError:
            continue
    a = np.array(out); lo, hi = (1 - band) / 2, 1 - (1 - band) / 2
    return {t: (float(np.nanquantile(a[:, j], lo)), float(np.nanquantile(a[:, j], hi))) for j, t in enumerate(periods)}


def trigger_score(flood_years: set, paid_years: set) -> dict:
    hits = flood_years & paid_years
    return {"caught": len(hits), "missed": len(flood_years - paid_years), "false_payouts": len(paid_years - flood_years),
            "flood_years": len(flood_years)}
