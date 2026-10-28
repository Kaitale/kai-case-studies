"""KAI subsurface tools (open demo version).

Small, dependency-light functions used by the Zeerijp-3A notebooks:

* fetch_nlog()          download a public NLOG file by its document id, cached and checked by SHA-256
* read_zrp_plugs()      parse the routine core analysis workbook of ZRP-3A into one tidy table
* fzi()/rock_types()    flow zone indicator and data-driven rock types (Amaefule et al., 1993)
* bedding()             synthetic heterolithic bedding model (sand/mud) with anisotropic lenses
* keff()                flow-based effective permeability of a 2D grid (two-point flux, no-flow sides)
* rev_scan()            effective kx, kz for windows of growing size: the representative elementary volume
* ripple_bedding()      SBED-style ripple-laminated bedding (flaser, wavy, lenticular) in 2D or 3D
* bedding_figure()      clean 3D block renderings of bedding templates

Code: MIT licence, KAI Water & Energy, 2026.
"""
from __future__ import annotations
import hashlib, pathlib, urllib.request, warnings
import numpy as np, pandas as pd, scipy.sparse as sp, scipy.sparse.linalg as spl
from scipy.ndimage import gaussian_filter
from scipy.stats import norm

NLOG = "https://www.nlog.nl/nlog-mapviewer-api/rest/brh/"
# Public NLOG files used here (borehole ZEERIJP-03-SIDETRACK1, NAM, 2015)
FILES = {
    "core":  dict(url=NLOG + "document/3484333644", name="ZRP-3A_final_core_analysis.xlsx",
                  sha256="f362cd8b114573bb6ec6462755190e06b7884ea339330e94df4e9fc69e026049"),
    "logs":  dict(url=NLOG + "logdocument/2085821327", name="mdn_mpd_mai_18aug15_LF1_FRM1.las",
                  sha256="66941d92fd7461f49e457029aade0c10b112be5f6419dc3aee636d6f60965ba5"),
    "sonic": dict(url=NLOG + "logdocument/2085820326", name="cxd_18aug15_LF1_FRM1.las",
                  sha256="0250708406f927d299beb03a1c86a5fc9b496231d9483c9c14c4a273e7668794"),
}
CORES = [(3521, 3537.71), (3537.8, 3556), (3556, 3580.13), (3580.13, 3610.62),
         (3610.62, 3641.59), (3641.59, 3671.45), (3817.76, 3835.71), (3835.72, 3867.25)]


def fetch_nlog(key: str, folder="nlog_cache") -> pathlib.Path:
    """Download one public NLOG file (once) and check its SHA-256."""
    f = FILES[key]; p = pathlib.Path(folder) / f["name"]; p.parent.mkdir(exist_ok=True)
    if not p.exists():
        req = urllib.request.Request(f["url"], headers={"User-Agent": "kai-case-studies"})
        with urllib.request.urlopen(req, timeout=180) as r:
            p.write_bytes(r.read())
    h = hashlib.sha256(p.read_bytes()).hexdigest()
    if f["sha256"] and h != f["sha256"]:
        raise ValueError(f"{p.name}: checksum {h} differs from the published {f['sha256']}")
    return p


def _num(v):
    if isinstance(v, str):
        s = v.strip().replace(" ", "")
        if s.startswith("<"):
            return np.nan
        try:
            return float(s)
        except ValueError:
            return np.nan
    return v


def read_zrp_plugs(xlsx) -> pd.DataFrame:
    """All plug measurements of ZRP-3A in one table (depth, orientation, porosity, Klinkenberg k, remark)."""
    sheets = {"RCAL plugs": (9, 15), "RCA SCAL plugs": (10, 15), "RCA PETRO plugs": (9, 16), "RCA Geomech plugs": (10, 16)}
    out = []
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        for name, (first, rem) in sheets.items():
            raw = pd.read_excel(xlsx, name, header=None).iloc[first:]
            d = raw.iloc[:, [1, 2, 3, 4, 5, 6, 8, rem]].copy()
            d.columns = ["depth", "id", "orient", "phi_hg", "phi_cal", "grain_density", "k_kl", "remark"]
            d = d[pd.to_numeric(d.depth, errors="coerce").notna()].copy()
            d["k_below_detection"] = raw.loc[d.index, 8].astype(str).str.contains("<")
            for c in ["depth", "phi_hg", "phi_cal", "grain_density", "k_kl"]:
                d[c] = d[c].map(_num).astype(float)
            d["sheet"] = name
            out.append(d)
    p = pd.concat(out, ignore_index=True)
    p["phi"] = p.phi_cal.fillna(p.phi_hg)
    r = p.remark.astype(str).str.lower()
    p["damaged"] = r.str.contains("frac|broken|crack|desintegr|half plug")
    p["core"] = [next((i + 1 for i, (a, b) in enumerate(CORES) if a - 0.05 <= z <= b + 0.05), 0) for z in p.depth]
    return p


def fzi(phi, k):
    """Reservoir quality index (micron) and flow zone indicator (Amaefule et al., 1993)."""
    rqi = 0.0314 * np.sqrt(np.asarray(k) / np.asarray(phi))
    return rqi, rqi / (np.asarray(phi) / (1 - np.asarray(phi)))


def k_from_fzi(phi, fzi_value):
    phi = np.asarray(phi)
    return 1014 * np.asarray(fzi_value) ** 2 * phi ** 3 / (1 - phi) ** 2


def rock_types(fzi_values, n=None, max_n=7, seed=0):
    """Gaussian-mixture rock types on log10(FZI); n chosen by BIC if not given. Types are numbered 1..n from tight to good."""
    from sklearn.mixture import GaussianMixture
    x = np.log10(np.asarray(fzi_values)).reshape(-1, 1)
    bic = {m: GaussianMixture(m, random_state=seed, n_init=5).fit(x).bic(x) for m in range(2, max_n + 1)}
    n = n or min(bic, key=bic.get)
    g = GaussianMixture(n, random_state=seed, n_init=10).fit(x)
    order = np.argsort(g.means_.ravel()); rank = {o: i + 1 for i, o in enumerate(order)}
    return np.array([rank[v] for v in g.predict(x)]), bic, n


def within(pred_log10k, obs_log10k, factor=3):
    e = np.asarray(pred_log10k) - np.asarray(obs_log10k)
    return float(np.mean(np.abs(e) < np.log10(factor)))


# --- synthetic bedding and flow-based upscaling -------------------------------------------------
def bedding(nz, nx, mud_fraction, lx=40, lz=2.0, seed=0):
    """Heterolithic bedding: True = mud. Anisotropic Gaussian field (lens length ~lx cells, thickness ~lz cells)
    cut at the mud fraction. Low mud gives isolated mud drapes (flaser), high mud isolated sand lenses (lenticular)."""
    r = np.random.default_rng(seed)
    f = gaussian_filter(r.standard_normal((nz, nx)), (lz, lx), mode="wrap")
    f = (f - f.mean()) / f.std()
    return f < norm.ppf(mud_fraction)


def keff(k, axis="x"):
    """Effective permeability of a 2D grid of unit cells: unit pressure drop along `axis`, no flow on the other sides."""
    nz, nx = k.shape; n = nz * nx; idx = np.arange(n).reshape(nz, nx)
    rows, cols, vals = [], [], []; diag = np.zeros(n); b = np.zeros(n)
    def link(i, j, t):
        rows.extend([i, j]); cols.extend([j, i]); vals.extend([-t, -t]); np.add.at(diag, i, t); np.add.at(diag, j, t)
    link(idx[:, :-1].ravel(), idx[:, 1:].ravel(), (2 / (1 / k[:, :-1] + 1 / k[:, 1:])).ravel())
    link(idx[:-1, :].ravel(), idx[1:, :].ravel(), (2 / (1 / k[:-1, :] + 1 / k[1:, :])).ravel())
    if axis == "x":
        inl, out, kin, kout, length, width = idx[:, 0], idx[:, -1], k[:, 0], k[:, -1], nx, nz
    else:
        inl, out, kin, kout, length, width = idx[0, :], idx[-1, :], k[0, :], k[-1, :], nz, nx
    np.add.at(diag, inl, 2 * kin); b[inl] += 2 * kin; np.add.at(diag, out, 2 * kout)
    A = sp.coo_matrix((np.concatenate(vals + [diag]), (np.concatenate(rows + [np.arange(n)]),
                       np.concatenate(cols + [np.arange(n)]))), shape=(n, n)).tocsr()
    p = spl.spsolve(A, b)
    return float(np.sum(2 * kin * (1 - p[inl])) * length / width)


def rev_scan(k, sizes):
    """Effective kx and kz of square windows of growing size, centred in the model."""
    nz, nx = k.shape; out = []
    for s in sizes:
        a, c = (nz - s) // 2, (nx - s) // 2; sub = k[a:a + s, c:c + s]
        out.append((s, keff(sub, "x"), keff(sub, "z")))
    return pd.DataFrame(out, columns=["cells", "kx", "kz"])


# --- ripple-laminated bedding templates (SBED-style) and 3D block rendering --------------------
def ripple_bedding(nx, ny, nz, mud, cell=0.005, T=0.04, lam=0.09, A=0.014, seed=0):
    """Ripple-laminated heterolithic bedding (SBED-style template).
    Returns mud (bool, nz x ny x nx; True = mud) and lam (0/1 foreset lamina parity in sand)."""
    r = np.random.default_rng(seed)
    x = np.arange(nx) * cell; y = np.arange(ny) * cell; z = np.arange(nz) * cell
    Z, Y, X = np.meshgrid(z, y, x, indexing="ij")
    nsets = int(np.ceil(nz * cell / T)) + 2
    shifts = r.uniform(0, lam, nsets); wob = r.uniform(0.15, 0.3, nsets); ph = r.uniform(0, 2*np.pi, nsets)
    noise = gaussian_filter(r.standard_normal((nsets, ny, nx)), (0, 6, 6)); noise /= noise.std()
    mudv = np.zeros(Z.shape, bool); lamv = np.zeros(Z.shape, float); best = np.full(Z.shape, -1.0)
    for k in range(-1, nsets - 1):
        s = X[0] - shifts[k] + 0.012 * np.sin(2*np.pi*Y[0]/wob[k] + ph[k])
        f = (s / lam) % 1.0
        prof = np.where(f < 0.72, f / 0.72, (1 - f) / 0.28)            # stoss long, lee short
        base = k * T + A * prof                                         # undulating set base
        h = Z - base[None]
        inset = (h >= 0) & (h < T + A)
        newer = inset & (base[None] > best)
        best = np.where(newer, base[None], best)
        d = T * mud * 2.2 * (1.15 - prof) * (1 + 0.35 * noise[k])      # drape thicker in troughs
        m = h < d[None]
        mudv = np.where(newer, m, mudv)
        q = 0.5 + 0.5 * np.sin(2 * np.pi * (s[None] - h * 1.6) / 0.0075)  # dipping foresets, smooth tone
        lamv = np.where(newer, q, lamv)
    return mudv, lamv


def calibrated_bedding(nx, ny, nz, target, seed=0, **kw):
    """Bedding whose mud fraction matches `target` (bisection on the drape parameter)."""
    lo, hi = 0.0, 1.5
    for _ in range(18):
        mid = (lo + hi) / 2
        m, l = ripple_bedding(nx, ny, nz, mid, seed=seed, **kw)
        lo, hi = (mid, hi) if m.mean() < target else (lo, mid)
    return ripple_bedding(nx, ny, nz, (lo + hi) / 2, seed=seed, **kw)


import matplotlib.pyplot as plt
S1=np.array([0.95,0.83,0.55]); S2=np.array([0.82,0.66,0.38]); M1=np.array([0.40,0.30,0.27]); M2=np.array([0.30,0.22,0.20])
def _rgb(mud,lam):
    t=lam[...,None]; sand=S2+(S1-S2)*t; m=M2+(M1-M2)*(0.5+0.5*t)
    return np.where(mud[...,None],m,sand)
def draw_block(ax,mud,lam,cell):
    nz,ny,nx=mud.shape; C=np.clip(_rgb(mud,lam),0,1)
    X=np.arange(nx+1)*cell; Y=np.arange(ny+1)*cell; Zs=np.arange(nz+1)*cell
    kw=dict(shade=False,rstride=1,cstride=1,linewidth=0,antialiased=False)
    xx,zz=np.meshgrid(X,Zs); ax.plot_surface(xx,np.zeros_like(xx),zz,facecolors=C[:,0,:]*0.98,**kw)
    yy,zz=np.meshgrid(Y,Zs); ax.plot_surface(np.full_like(yy,X[-1]),yy,zz,facecolors=C[:,:,-1]*0.80,**kw)
    xx,yy=np.meshgrid(X,Y); ax.plot_surface(xx,yy,np.full_like(xx,Zs[-1]),facecolors=np.clip(C[-1]*1.06,0,1),**kw)
    x1,y1,z1=X[-1],Y[-1],Zs[-1]
    for a,b in [((0,0,0),(x1,0,0)),((x1,0,0),(x1,y1,0)),((0,0,0),(0,0,z1)),((x1,0,0),(x1,0,z1)),((x1,y1,0),(x1,y1,z1)),
                ((0,0,z1),(x1,0,z1)),((x1,0,z1),(x1,y1,z1)),((x1,y1,z1),(0,y1,z1)),((0,y1,z1),(0,0,z1))]:
        ax.plot(*zip(a,b),color="#3a3a3a",lw=0.8)
    ax.set_box_aspect((x1,y1,z1)); ax.view_init(elev=24,azim=-58); ax.set_axis_off()
    ax.set_xlim(0,x1); ax.set_ylim(0,y1); ax.set_zlim(0,z1)
def bedding_figure(path, cases=((0.12,"Flaser"),(0.35,"Wavy"),(0.62,"Lenticular")), cell=0.0025, seed=4, kvals=None):
    fig=plt.figure(figsize=(13.5,4.8),facecolor="white")
    for i,(m,name) in enumerate(cases):
        mud,lam=calibrated_bedding(220,130,110,m,seed=seed,cell=cell)
        ax=fig.add_subplot(1,3,i+1,projection="3d"); draw_block(ax,mud,lam,cell)
        ax.set_title(f"{name} bedding\nmud {mud.mean():.0%}",fontsize=12,pad=-4,color="#222")
        if kvals: ax.text2D(0.5,0.02,kvals[i],transform=ax.transAxes,ha="center",fontsize=10,color="#333")
    fig.text(0.5,0.015,"Synthetic bedding templates, 55 cm x 32 cm x 27 cm, 2.5 mm cells · sand in yellow (foreset laminae shaded), claystone in brown",ha="center",fontsize=9,color="#666")
    fig.subplots_adjust(left=0,right=1,top=0.9,bottom=0.05,wspace=-0.02); fig.savefig(path,dpi=140)
