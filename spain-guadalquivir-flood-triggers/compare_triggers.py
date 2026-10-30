"""River-flow and rainfall triggers, each written four ways, scored against the gauges' flood years (MIT licence).

Run from the case folder:  python compare_triggers.py
Reads data/annual_maxima.csv, data/rainfall_maxima.csv and data/gauges.csv. Writes
  results/trigger_methods.csv        pooled scores for every index, method and trigger level
  results/trigger_methods_sites.csv  how often each 1-in-5 trigger pays at each gauge
  results/rain_windows.csv           rank correlation and return-period skill for each rainfall window
  results/rain_vs_river.json         river against wet-season rainfall on the same flood years, and the two combined
  figures/gq_methods.png

A flood year is a year in which the gauge passed its own fitted 1-in-T level, as in the notebook. Every trigger is set to
pay on average once in T years, in four ways (Model Library, 2026):
  absolute     one level for every gauge: the median of the gauges' own fitted 1-in-T levels
               (rainfall in mm; river flow per 1,000 km² of catchment, since m³/s cannot be shared across catchments)
  quantile     each gauge's own empirical 1 - 1/T quantile (Weibull plotting position)
  return       each gauge's own fitted 1-in-T level (GEV or LP3 by L-moments, as in the notebook)
  share        a share of each gauge's own mean annual maximum; one share for all gauges, the median ratio of
               the fitted 1-in-T level to the mean
The river index is GloFAS at the matched cell; the rainfall indices are catchment means from NASA POWER: the wettest
3 days of the year (a storm index, as in excess-rainfall flood cover) and the October-April total (the index of Model
Library's Andalucía study). results/rain_windows.csv shows the other windows.
"""
from __future__ import annotations

import json
import pathlib
import sys
import warnings

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import flood_tools as ft  # noqa: E402

warnings.filterwarnings("ignore")
LEVELS = [2, 5, 10, 25]
METHODS = ["absolute", "quantile", "return", "share"]
METHOD_NAME = {"absolute": "Absolute value", "quantile": "Quantile", "return": "Return period", "share": "Share of a reference"}
INDICES = {"glofas_max_m3s": "River flow (GloFAS)", "rain_max_3d_mm": "Storm rainfall (wettest 3 days)",
           "rain_oct_apr_mm": "Wet-season rainfall (Oct–Apr total)"}
WINDOWS = ["rain_max_1d_mm", "rain_max_3d_mm", "rain_max_5d_mm", "rain_max_10d_mm", "rain_max_30d_mm", "rain_oct_apr_mm"]


def levels_for(d: pd.DataFrame, col: str, area: pd.Series, t: int) -> dict:
    """Trigger level per gauge for each method, all aimed at once in t years."""
    fit, mean, q = {}, {}, {}
    for gid, g in d.groupby("gauge_id"):
        x = g[col].values
        best, f = ft.fit_best(x)
        fit[gid] = ft.level(f[best], t); mean[gid] = x.mean()
        q[gid] = float(np.quantile(x, 1 - 1 / t, method="weibull"))
    river = col.startswith("glofas")
    spec = {gid: fit[gid] / area[gid] * 1000 if river else fit[gid] for gid in fit}
    absolute = float(np.median(list(spec.values())))
    share = float(np.median([fit[gid] / mean[gid] for gid in fit]))
    out = {}
    for gid in fit:
        out[gid] = {"absolute": absolute * area[gid] / 1000 if river else absolute, "quantile": q[gid], "return": fit[gid],
                    "share": share * mean[gid]}
    return out, absolute, share


def score(flood: np.ndarray, paid: np.ndarray) -> dict:
    h = int((flood & paid).sum()); m = int((flood & ~paid).sum()); f = int((~flood & paid).sum()); c = int((~flood & ~paid).sum())
    N, K, n = len(flood), h + m, h + f
    H, F = h / K, f / (f + c)
    return {"hits": h, "misses": m, "false_payouts": f, "hit_rate": round(H, 3), "false_alarm_rate": round(F, 3),
            "peirce": round(H - F, 3), "false_payout_share": round(f / n, 3) if n else float("nan"),
            "p_vs_chance": float(f"{stats.hypergeom.sf(h - 1, N, K, n):.2g}")}


def main() -> None:
    gauges = pd.read_csv(HERE / "data/gauges.csv").set_index("gauge_id")
    d = pd.read_csv(HERE / "data/annual_maxima.csv").merge(pd.read_csv(HERE / "data/rainfall_maxima.csv"), on=["gauge_id", "water_year"])
    area = gauges.catchment_km2
    gfit = {gid: (lambda b, f: f[b])(*ft.fit_best(g.gauge_max_m3s.values)) for gid, g in d.groupby("gauge_id")}
    flood_lv = {t: {gid: ft.level(dist, t) for gid, dist in gfit.items()} for t in LEVELS}
    d = d.sort_values(["gauge_id", "water_year"]).reset_index(drop=True)

    rows, site_rows = [], []
    for col, iname in INDICES.items():
        for t in LEVELS:
            lv, absolute, share = levels_for(d, col, area, t)
            flood = np.array([r.gauge_max_m3s >= flood_lv[t][r.gauge_id] for r in d.itertuples()])
            for m in METHODS:
                paid = np.array([getattr(r, col) >= lv[r.gauge_id][m] for r in d.itertuples()])
                freq = pd.Series(paid).groupby(d.gauge_id).mean()
                rows.append({"index": iname, "method": METHOD_NAME[m], "T": t, **score(flood, paid),
                             "paid_share_min": round(freq.min(), 2), "paid_share_median": round(freq.median(), 2),
                             "paid_share_max": round(freq.max(), 2),
                             "common_level": (round(absolute, 1) if m == "absolute" else round(share, 2) if m == "share" else None)})
                if t == 5:
                    for gid, fr in freq.items():
                        site_rows.append({"index": iname, "method": METHOD_NAME[m], "gauge_id": gid, "gauge": gauges.loc[gid, "name"],
                                          "level": round(lv[gid][m], 2), "paid_share": round(fr, 2)})
    tm = pd.DataFrame(rows); tm.to_csv(HERE / "results/trigger_methods.csv", index=False)
    pd.DataFrame(site_rows).to_csv(HERE / "results/trigger_methods_sites.csv", index=False)

    win = []
    for col in ["glofas_max_m3s"] + WINDOWS:
        rho = [stats.spearmanr(g.gauge_max_m3s, g[col]).statistic for _, g in d.groupby("gauge_id")]
        lv, _, _ = levels_for(d, col, area, 5)
        flood = np.array([r.gauge_max_m3s >= flood_lv[5][r.gauge_id] for r in d.itertuples()])
        paid = np.array([getattr(r, col) >= lv[r.gauge_id]["return"] for r in d.itertuples()])
        sc = score(flood, paid)
        win.append({"index": col, "median_rank_corr": round(float(np.median(rho)), 2), "caught_1in5": sc["hits"],
                    "false_payouts_1in5": sc["false_payouts"], "peirce_1in5": sc["peirce"]})
    pd.DataFrame(win).to_csv(HERE / "results/rain_windows.csv", index=False)

    # river and wet-season rainfall, each at its own 1-in-5 level: compared on the same flood years, and combined
    lv_q, _, _ = levels_for(d, "glofas_max_m3s", area, 5); lv_r, _, _ = levels_for(d, "rain_oct_apr_mm", area, 5)
    flood = np.array([r.gauge_max_m3s >= flood_lv[5][r.gauge_id] for r in d.itertuples()])
    q = np.array([r.glofas_max_m3s >= lv_q[r.gauge_id]["return"] for r in d.itertuples()])
    rr = np.array([r.rain_oct_apr_mm >= lv_r[r.gauge_id]["return"] for r in d.itertuples()])
    b, c2 = int((flood & q & ~rr).sum()), int((flood & rr & ~q).sum())
    rho_qr = [stats.spearmanr(g.glofas_max_m3s, g.rain_oct_apr_mm).statistic for _, g in d.groupby("gauge_id")]
    combo = {"river_only_caught": b, "rain_only_caught": c2, "mcnemar_p": float(f"{stats.binomtest(b, b + c2, 0.5).pvalue:.2g}"),
             "both": score(flood, q & rr), "either": score(flood, q | rr), "river": score(flood, q), "rain": score(flood, rr),
             "median_rank_corr_river_vs_rain": round(float(np.median(rho_qr)), 2),
             "absolute_paid_share_river": [float(x) for x in tm[(tm["T"] == 5) & (tm.method == "Absolute value") & (tm["index"] == INDICES["glofas_max_m3s"])][["paid_share_min", "paid_share_max"]].iloc[0]],
             "absolute_paid_share_season": [float(x) for x in tm[(tm["T"] == 5) & (tm.method == "Absolute value") & (tm["index"] == INDICES["rain_oct_apr_mm"])][["paid_share_min", "paid_share_max"]].iloc[0]]}
    (HERE / "results/rain_vs_river.json").write_text(json.dumps(combo, indent=1))

    # figure: Peirce skill at 1-in-5 for every index and method, and payout frequency spread
    plt.rcParams.update({"figure.dpi": 150, "axes.grid": True, "grid.color": "#dfe8e8", "axes.spines.top": False,
                         "axes.spines.right": False, "font.size": 10, "axes.titleweight": "bold", "axes.titlesize": 11,
                         "legend.frameon": False, "savefig.bbox": "tight", "savefig.facecolor": "white"})
    col = dict(zip(INDICES.values(), ["#2a78d6", "#eb6834", "#1baf7a"]))
    t5 = tm[tm["T"] == 5]
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(11, 4.2))
    x = np.arange(len(METHODS)); w = 0.26
    for k, (iname, c) in enumerate(col.items()):
        s = t5[t5["index"] == iname].set_index("method").loc[[METHOD_NAME[m] for m in METHODS]]
        a1.bar(x + (k - 1) * w, s.peirce, w, color=c, label=iname)
        a2.errorbar(x + (k - 1) * w, s.paid_share_median, yerr=[s.paid_share_median - s.paid_share_min, s.paid_share_max - s.paid_share_median],
                    fmt="o", color=c, capsize=4, lw=1.6, label=iname)
    a1.axhline(0, color="#898781", lw=0.8)
    labels = ["Absolute\nvalue", "Quantile", "Return\nperiod", "Share of a\nreference"]
    a1.set(xticks=x, xticklabels=labels, ylabel="Peirce skill (hit rate − false-alarm rate)", ylim=(0, 0.45),
           title="Skill of a 1-in-5 trigger")
    a2.axhline(0.2, color="#898781", lw=1, ls="--"); a2.text(0.5, 0.25, "target:\n1 year in 5", fontsize=8, color="#555", ha="center")
    a2.set(xticks=x, xticklabels=labels, ylabel="share of years the trigger pays", ylim=(0, None),
           title="How often it pays at each gauge (median and range)")
    h, l = a1.get_legend_handles_labels()
    fig.legend(h, l, loc="lower center", ncol=3, fontsize=9, bbox_to_anchor=(0.5, -0.04))
    fig.tight_layout(rect=(0, 0.06, 1, 1)); fig.savefig(HERE / "figures/gq_methods.png"); plt.close(fig)
    print(tm[tm["T"] == 5].to_string(index=False)); print(pd.DataFrame(win).to_string(index=False))


if __name__ == "__main__":
    main()
