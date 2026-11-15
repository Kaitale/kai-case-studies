"""From trigger to flood map: the Guadalquivir from Mengibar to Andujar under each trigger index (MIT licence).

The trigger case asks *whether* a policy would have paid. This script asks *what was under water* when it did:
it runs the SFINCS flood model on 54 km of the Guadalquivir below the Mengibar gauge (CEDEX 5004) for the
2010-11 flood, the largest in the gauge's record, once for each way of reading that year:

* what the gauge measured (the reference);
* GloFAS 4.0 and GloFAS 5.0, read in m3/s straight from the model;
* GloFAS 4.0, GloFAS 5.0 and catchment rainfall (the case's first, rain-only index), read as a return period and
  turned into the flow of that return period on the gauge's own curve: how a return-period trigger is written;

plus the gauge's 10-year and 100-year floods, compared with the Copernicus (JRC) global flood hazard map.

Every input is open and fetched on your own connection, checked by SHA-256 and cached in map_cache/:
Copernicus DEM GLO-30 (AWS open data), ESA WorldCover 2021 v200 (AWS open data) and the JRC/CEMS global river
flood hazard maps v2.1 (JRC Data Store). SFINCS (Deltares, GNU GPL-3.0) is built from its open source code and
run as a separate program: set SFINCS_EXE to the executable, or SFINCS_IMAGE to a Docker image built from source.

    python flood_maps.py            # build, run every scenario, write data/flood_maps/, results/, figures/
    python flood_maps.py --reuse    # skip the SFINCS runs whose output already exists in map_runs/
"""
from __future__ import annotations

import hashlib
import json
import math
import os
import shutil
import subprocess
import sys
import urllib.request
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import ndimage
from scipy.optimize import brentq

import flood_tools as ft

HERE = Path(__file__).resolve().parent
CACHE = HERE / "map_cache"
RUNS = HERE / "map_runs"
OUT = HERE / "data" / "flood_maps"

# ----------------------------------------------------------------------------- the reach
CRS = "EPSG:25830"                                  # ETRS89 / UTM 30N
DX = 30.0
X0, Y0, X1, Y1 = 402_000.0, 4_203_300.0, 431_100.0, 4_213_500.0
SOURCE_XY = (430_215.0, 4_204_545.0)                # the river 0.5 km below the Mengibar gauge (CEDEX 5004)
GAUGE = 5004
EVENT_YEAR = 2011                                   # water year Oct 2010 - Sep 2011
BASE_FLOW = 30.0                                    # m3/s: the river in its banks, removed from every flood map
FLOOD_DEPTH = 0.15                                  # m: a cell counts as flooded from this depth
HAND_MAX = 25.0                                     # m above the river: higher ground is left out of the model
CHANNEL_DEPTH = 1.5                                 # m burnt below the DEM's water surface (it holds no riverbed)
RIPARIAN_M = 300                                    # m from the river: tree canopy there is taken out of the DEM
OPENING_CELLS = 7                                   # 210 m grey opening: removes strips of canopy narrower than that
TSTOP_H = 48
TOWNS = {"Mengibar": (-3.8086, 37.9686), "Espeluy": (-3.8617, 38.0336),
         "Villanueva de la Reina": (-3.9136, 38.0042), "Andujar": (-4.0503, 38.0392)}

# WorldCover 2021 class -> (name, Manning's n)
LANDCOVER = {10: ("Trees (mostly olive groves)", 0.07), 20: ("Shrubland", 0.06), 30: ("Grassland", 0.04),
             40: ("Cropland", 0.045), 50: ("Built-up", 0.12), 60: ("Bare ground", 0.03), 80: ("Water", 0.03),
             90: ("Wetland", 0.05), 95: ("Mangroves", 0.08), 100: ("Moss", 0.04)}
N_CHANNEL = 0.035

COP = "https://copernicus-dem-30m.s3.amazonaws.com/Copernicus_DSM_COG_10_{t}_DEM/Copernicus_DSM_COG_10_{t}_DEM.tif"
WC = "https://esa-worldcover.s3.eu-central-1.amazonaws.com/v200/2021/map/ESA_WorldCover_10m_2021_v200_N36W006_Map.tif"
JRC = "https://jeodpp.jrc.ec.europa.eu/ftp/jrc-opendata/CEMS-GLOFAS/flood_hazard/RP{rp}/ID108_N40_W10_RP{rp}_depth.tif"
FILES = {  # name: (url, sha256)
    "cop_N37_W004.tif": (COP.format(t="N37_00_W004_00"), None),
    "cop_N38_W004.tif": (COP.format(t="N38_00_W004_00"), None),
    "cop_N37_W005.tif": (COP.format(t="N37_00_W005_00"), None),
    "cop_N38_W005.tif": (COP.format(t="N38_00_W005_00"), None),
    "worldcover_N36W006.tif": (WC, None),
    "jrc_RP10.tif": (JRC.format(rp=10), None),
    "jrc_RP100.tif": (JRC.format(rp=100), None),
}
SHA_FILE = HERE / "flood_maps_files.sha256"
# Spain's official flood zones (SNCZI, MITECO): free to reuse with credit, but the download page asks the browser to
# solve a challenge, so fetch them yourself from https://www.miteco.gob.es/es/cartografia-y-sig/ide/descargas/agua/zi-lamina.html
# and put the zips in map_cache/. When they are there, the 10- and 100-year floods are also checked against them.
SNCZI = {10: "laminasPB-q10.zip", 100: "laminasPB-q100.zip"}


# ----------------------------------------------------------------------------- downloads
def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def pinned() -> dict:
    if not SHA_FILE.exists():
        return {}
    return {name: sha for sha, name in (ln.split() for ln in SHA_FILE.read_text().splitlines() if ln.strip())}


def fetch(name: str) -> Path:
    """Download once into map_cache/, then check the file against flood_maps_files.sha256."""
    CACHE.mkdir(exist_ok=True)
    p = CACHE / name
    if not p.exists():
        url = FILES[name][0]
        print(f"downloading {name} …", flush=True)
        tmp = p.with_suffix(".part")
        with urllib.request.urlopen(url, timeout=300) as r, open(tmp, "wb") as f:
            shutil.copyfileobj(r, f)
        tmp.rename(p)
    want = pinned().get(name)
    if want and sha256(p) != want:
        raise SystemExit(f"{name}: SHA-256 differs from flood_maps_files.sha256 (the source changed); stop.")
    return p


# ----------------------------------------------------------------------------- grid
def shape() -> tuple[int, int]:
    return int(round((Y1 - Y0) / DX)), int(round((X1 - X0) / DX))


def transform():
    from rasterio.transform import from_origin
    return from_origin(X0, Y1, DX, DX)


def warp(paths, resampling, dtype="float32", nodata=np.nan, clip_negative=False) -> np.ndarray:
    import rasterio
    from rasterio.merge import merge
    from rasterio.warp import Resampling, reproject, transform_bounds
    lon0, lat0, lon1, lat1 = transform_bounds(CRS, "EPSG:4326", X0, Y0, X1, Y1)
    pad = 0.01
    srcs = [rasterio.open(p) for p in paths]
    mos, tr = merge(srcs, bounds=(lon0 - pad, lat0 - pad, lon1 + pad, lat1 + pad))
    a = mos[0]
    if clip_negative:
        a = np.where(np.isfinite(a) & (a > 0), a, 0)
    out = np.full(shape(), nodata, dtype=dtype)
    reproject(a.astype(dtype), out, src_transform=tr, src_crs="EPSG:4326", dst_transform=transform(), dst_crs=CRS,
              resampling=getattr(Resampling, resampling), src_nodata=None, dst_nodata=nodata)
    return out


def to_xy(rows, cols):
    return X0 + (np.asarray(cols) + 0.5) * DX, Y1 - (np.asarray(rows) + 0.5) * DX


def to_rc(x, y):
    return int((Y1 - y) // DX), int((x - X0) // DX)


def build_grid() -> dict:
    """DEM, land cover, river path, burnt channel, Manning's n and the model mask on the 30 m grid."""
    import pyflwdir
    raw = warp([fetch(n) for n in FILES if n.startswith("cop_")], "bilinear")
    wc = warp([fetch("worldcover_N36W006.tif")], "mode", dtype="uint8", nodata=0)
    ny, nx = raw.shape
    z = np.where(np.isfinite(raw), raw, -9999).astype("float32")
    fd = pyflwdir.from_dem(z, nodata=-9999, transform=transform(), latlon=False, outlets="edge")
    upa = fd.upstream_area(unit="km2")
    r, c = to_rc(*SOURCE_XY)
    w = 10
    sub = upa[r - w:r + w, c - w:c + w]
    i = np.unravel_index(np.argmax(sub), sub.shape)
    src = (r - w + i[0], c - w + i[1])
    path = np.array(fd.path(idxs=np.array([src[0] * nx + src[1]]))[0][0])
    pr, pc = path // nx, path % nx
    # The Copernicus DEM is a surface model: the poplar and tamarisk galleries along the banks stand in it as
    # walls a few metres high. Within RIPARIAN_M of the river, tree-covered cells are lowered to a grey opening of
    # the surface (a strip of canopy narrower than the window disappears; wider ground keeps its height).
    onpath = np.zeros((ny, nx), bool)
    onpath[pr, pc] = True
    dist = ndimage.distance_transform_edt(~onpath) * DX
    filled = np.where(np.isfinite(raw), raw, np.nanmax(raw))
    opened = ndimage.grey_opening(filled, size=(OPENING_CELLS, OPENING_CELLS))
    riparian = (wc == 10) & (dist <= RIPARIAN_M) & (dist > 1.5 * DX)
    dem = np.where(riparian, np.minimum(raw, opened), raw)
    # The DEM shows the water surface on the day it was flown; take its lower envelope along the river
    # (a 0.9 km running minimum), keep it falling downstream, and burn a channel below it.
    zp = dem[pr, pc]
    prof = ndimage.minimum_filter1d(zp, size=31, mode="nearest")
    prof = np.minimum.accumulate(prof)
    chan = np.zeros((ny, nx), bool)
    chan[pr, pc] = True
    chan = ndimage.binary_dilation(chan, structure=ndimage.generate_binary_structure(2, 1))
    # profile at every cell from its nearest river cell: channel bed and height above the river (HAND)
    pz = np.full((ny, nx), np.nan)
    pz[pr, pc] = prof
    _, (ir, ic) = ndimage.distance_transform_edt(~onpath, return_indices=True)
    near = pz[ir, ic]
    zb = dem.copy()
    zb[chan] = near[chan] - CHANNEL_DEPTH
    hand = dem - near
    mask = (hand < HAND_MAX) & np.isfinite(dem)
    lab, _ = ndimage.label(mask)
    mask = lab == lab[pr[0], pc[0]]
    n = np.full((ny, nx), 0.05, "float32")
    for k, (_, v) in LANDCOVER.items():
        n[wc == k] = v
    n[chan] = N_CHANNEL
    return {"dem": raw, "dem_ground": dem, "riparian_lowering_m": float((raw - dem)[riparian].mean()),
            "riparian_cells": int(riparian.sum()), "zb": zb, "wc": wc, "chan": chan, "mask": mask, "manning": n, "path": path, "src": src,
            "profile": prof, "hand": hand}


# ----------------------------------------------------------------------------- SFINCS
def _order(mask):
    nn, mm = np.nonzero(mask.T)
    return np.stack([mm, nn], axis=1)


def write_run(run: Path, g: dict, q: float) -> None:
    """SFINCS's binary regular-grid inputs and one river inflow, ramped up over 6 hours then held."""
    run.mkdir(parents=True, exist_ok=True)
    ny, nx = shape()
    msk = g["mask"].astype("int8")
    west = np.zeros_like(msk, dtype=bool)
    west[:, 0] = True
    msk[west & g["mask"]] = 3                                   # the river leaves the model on the west edge
    # SFINCS rows run south to north
    msk_s, zb_s, n_s = msk[::-1], g["zb"][::-1], g["manning"][::-1]
    order = _order(msk_s > 0)
    n_idx, m_idx = order[:, 0], order[:, 1]
    idx = (m_idx * ny + n_idx + 1).astype("<i4")
    (run / "sfincs.ind").write_bytes(np.array([len(idx)], "<i4").tobytes() + idx.tobytes())
    (run / "sfincs.msk").write_bytes(msk_s[n_idx, m_idx].astype("i1").tobytes())
    (run / "sfincs.dep").write_bytes(np.nan_to_num(zb_s[n_idx, m_idx], nan=500).astype("<f4").tobytes())
    (run / "sfincs.man").write_bytes(n_s[n_idx, m_idx].astype("<f4").tobytes())
    sx, sy = to_xy(*g["src"])
    (run / "sfincs.src").write_text(f"{float(sx):.1f} {float(sy):.1f}\n")
    ts = [0, 6 * 3600, TSTOP_H * 3600]
    (run / "sfincs.dis").write_text("".join(f"{t:.1f} {v:.3f}\n" for t, v in zip(ts, [min(q, 5.0), q, q])))
    path = g["path"]
    pts = path[:: max(1, len(path) // 8)][1:]
    ox, oy = to_xy(pts // nx, pts % nx)
    (run / "sfincs.obs").write_text("".join(f"{a:.1f} {b:.1f}\n" for a, b in zip(ox, oy)))
    tref = datetime(2000, 1, 1)
    keys = {"mmax": nx, "nmax": ny, "dx": f"{DX:g}", "dy": f"{DX:g}", "x0": f"{X0:.1f}", "y0": f"{Y0:.1f}",
            "rotation": 0, "tref": tref.strftime("%Y%m%d %H%M%S"),
            "tstart": tref.strftime("%Y%m%d %H%M%S"),
            "tstop": (tref + timedelta(hours=TSTOP_H)).strftime("%Y%m%d %H%M%S"),
            "inputformat": "bin", "outputformat": "net", "depfile": "sfincs.dep", "mskfile": "sfincs.msk",
            "indexfile": "sfincs.ind", "manningfile": "sfincs.man", "srcfile": "sfincs.src", "disfile": "sfincs.dis",
            "obsfile": "sfincs.obs", "advection": 0, "alpha": 0.5, "theta": 0.9, "huthresh": 0.05, "qinf": 0.0,
            "dtmapout": TSTOP_H * 3600, "dtmaxout": TSTOP_H * 3600, "dthisout": 1800}
    (run / "sfincs.inp").write_text("".join(f"{k:<14}= {v}\n" for k, v in keys.items()), newline="\n")


def run_sfincs(run: Path) -> None:
    exe, image = os.environ.get("SFINCS_EXE"), os.environ.get("SFINCS_IMAGE")
    if exe:
        cmd = [exe]
    elif image:
        cmd = ["docker", "run", "--rm", "-v", f"{run.resolve()}:/job", "-w", "/job", image, "sfincs"]
    else:
        raise SystemExit("Set SFINCS_EXE (a SFINCS executable built from source) or SFINCS_IMAGE (a Docker image).")
    with open(run / "sfincs_stdout.txt", "w") as log:
        subprocess.run(cmd, cwd=run, stdout=log, stderr=subprocess.STDOUT, check=True)


def read_hmax(run: Path, g: dict) -> np.ndarray:
    import netCDF4
    ny, nx = shape()
    with netCDF4.Dataset(run / "sfincs_map.nc") as ds:
        zsmax = np.ma.filled(ds["zsmax"][:].astype(float), np.nan)
    zsmax = np.squeeze(zsmax)
    if zsmax.ndim == 3:
        zsmax = np.nanmax(zsmax, axis=0)
    if zsmax.shape == (nx, ny):
        zsmax = zsmax.T
    zsmax = zsmax[::-1]                                          # back to north-up rows
    h = zsmax - g["zb"]
    h = np.where(np.isfinite(h) & g["mask"] & (np.abs(zsmax) < 1e5), np.clip(h, 0, None), 0.0)
    return h


def steady(run: Path) -> float:
    """Largest change of water level between the last two half-hour outputs at the river points (m)."""
    import netCDF4
    with netCDF4.Dataset(run / "sfincs_his.nc") as ds:
        zs = np.ma.filled(ds["point_zs"][:].astype(float), np.nan)
    return float(np.nanmax(np.abs(zs[-1] - zs[-2])))


# ----------------------------------------------------------------------------- the scenarios
def return_period(x, v) -> float:
    m, fits = ft.fit_best(np.asarray(x, float))
    d = fits[m]
    if v >= ft.level(d, 10_000):
        return 10_000.0
    if v <= ft.level(d, 1.001):
        return 1.0
    return float(brentq(lambda t: ft.level(d, t) - v, 1.001, 10_000))


def scenarios() -> tuple[list[dict], dict]:
    am = pd.read_csv(HERE / "data/annual_maxima.csv")
    am5 = pd.read_csv(HERE / "data/annual_maxima_v5.csv")
    rf = pd.read_csv(HERE / "data/rainfall_maxima.csv")
    g4, g5, r = am[am.gauge_id == GAUGE], am5[am5.gauge_id == GAUGE], rf[rf.gauge_id == GAUGE]
    gauge = pd.concat([g4[["water_year", "gauge_max_m3s"]], g5[["water_year", "gauge_max_m3s"]]])
    gauge = gauge.drop_duplicates("water_year").sort_values("water_year")
    mg, fg = ft.fit_best(gauge.gauge_max_m3s.to_numpy())
    curve = fg[mg]
    flow_at = lambda t: ft.level(curve, t)  # noqa: E731
    y = EVENT_YEAR
    obs = float(gauge.loc[gauge.water_year == y, "gauge_max_m3s"].iloc[0])
    v4 = float(g4.loc[g4.water_year == y, "glofas_max_m3s"].iloc[0])
    v5 = float(g5.loc[g5.water_year == y, "glofas5_max_m3s"].iloc[0])
    season = float(r.loc[r.water_year == y, "rain_oct_apr_mm"].iloc[0])
    storm = float(r.loc[r.water_year == y, "rain_max_3d_mm"].iloc[0])
    t_obs = return_period(gauge.gauge_max_m3s, obs)
    t4 = return_period(g4.glofas_max_m3s, v4)
    t5 = return_period(g5.glofas5_max_m3s, v5)
    t_season = return_period(r.rain_oct_apr_mm, season)
    t_storm = return_period(r.rain_max_3d_mm, storm)
    t5_trig = 5
    q5_gauge = flow_at(t5_trig)
    s = [
        {"id": "measured", "label": "Measured at the gauge", "index_value": obs, "unit": "m3/s", "T": t_obs,
         "q": obs, "read_as": "measured", "pays_1in5": t_obs >= t5_trig},
        {"id": "v4_flow", "label": "GloFAS 4.0, in m3/s", "index_value": v4, "unit": "m3/s", "T": t4, "q": v4,
         "read_as": "m3/s", "pays_1in5": v4 >= q5_gauge},
        {"id": "v5_flow", "label": "GloFAS 5.0, in m3/s", "index_value": v5, "unit": "m3/s", "T": t5, "q": v5,
         "read_as": "m3/s", "pays_1in5": v5 >= q5_gauge},
        {"id": "v4_rp", "label": "GloFAS 4.0, as a return period", "index_value": v4, "unit": "m3/s", "T": t4,
         "q": flow_at(t4), "read_as": "return period", "pays_1in5": t4 >= t5_trig},
        {"id": "v5_rp", "label": "GloFAS 5.0, as a return period", "index_value": v5, "unit": "m3/s", "T": t5,
         "q": flow_at(t5), "read_as": "return period", "pays_1in5": t5 >= t5_trig},
        {"id": "rain_season", "label": "Rainfall only, Oct-Apr total", "index_value": season, "unit": "mm",
         "T": t_season, "q": flow_at(t_season), "read_as": "return period", "pays_1in5": t_season >= t5_trig},
        {"id": "rain_storm", "label": "Rainfall only, wettest 3 days", "index_value": storm, "unit": "mm",
         "T": t_storm, "q": flow_at(t_storm), "read_as": "return period", "pays_1in5": t_storm >= t5_trig},
        {"id": "design_T10", "label": "Gauge's 10-year flood", "index_value": flow_at(10), "unit": "m3/s", "T": 10.0,
         "q": flow_at(10), "read_as": "design", "pays_1in5": None},
        {"id": "design_T100", "label": "Gauge's 100-year flood", "index_value": flow_at(100), "unit": "m3/s",
         "T": 100.0, "q": flow_at(100), "read_as": "design", "pays_1in5": None},
        {"id": "base", "label": "River in its banks", "index_value": BASE_FLOW, "unit": "m3/s", "T": None,
         "q": BASE_FLOW, "read_as": "base", "pays_1in5": None},
    ]
    meta = {"gauge_fit": mg, "gauge_years": int(len(gauge)), "gauge_1in5_m3s": q5_gauge,
            "gauge_levels": {str(t): flow_at(t) for t in (2, 5, 10, 25, 50, 100)}}
    return s, meta


# ----------------------------------------------------------------------------- results
def save_depth(name: str, h: np.ndarray) -> Path:
    """Depth in decimetres (0-250, 255 = outside the model) as a small GeoTIFF."""
    import rasterio
    OUT.mkdir(parents=True, exist_ok=True)
    p = OUT / f"{name}_depth_dm.tif"
    a = np.clip(np.round(h * 10), 0, 250).astype("uint8")
    with rasterio.open(p, "w", driver="GTiff", height=a.shape[0], width=a.shape[1], count=1, dtype="uint8",
                       crs=CRS, transform=transform(), nodata=255, compress="deflate", predictor=2) as dst:
        dst.write(a, 1)
        dst.update_tags(units="decimetres", source="SFINCS run by KAI, flood_maps.py")
    return p


def save_hillshade(dem: np.ndarray) -> Path:
    """A shaded relief of the Copernicus DEM (sun from the north-west), 0-254, for the map backgrounds."""
    import rasterio
    z = np.nan_to_num(dem, nan=float(np.nanmean(dem)))
    gy, gx = np.gradient(z, DX)
    slope = np.arctan(np.hypot(gx, gy))
    aspect = np.arctan2(-gx, gy)
    az, alt = np.radians(315), np.radians(45)
    hs = np.sin(alt) * np.cos(slope) + np.cos(alt) * np.sin(slope) * np.cos(az - aspect)
    a = np.clip(hs * 254, 0, 254).astype("uint8")
    p = OUT / "hillshade.tif"
    with rasterio.open(p, "w", driver="GTiff", height=a.shape[0], width=a.shape[1], count=1, dtype="uint8",
                       crs=CRS, transform=transform(), nodata=255, compress="deflate", predictor=2) as dst:
        dst.write(a, 1)
        dst.update_tags(source="Shaded relief of Copernicus DEM GLO-30 (c) DLR e.V. 2010-2014 and (c) Airbus Defence "
                               "and Space GmbH 2014-2018, provided under COPERNICUS by the European Union and ESA")
    return p


def official_zone(rp: int) -> np.ndarray | None:
    """SNCZI flood zone for return period rp on the model grid, or None when the zip is not in map_cache/."""
    p = CACHE / SNCZI[rp]
    if not p.exists():
        return None
    import zipfile
    import geopandas as gpd
    from rasterio.features import rasterize
    from shapely.geometry import box
    clip = gpd.GeoSeries([box(X0, Y0, X1, Y1)], crs=CRS)
    shapes = []
    for name in (n for n in zipfile.ZipFile(p).namelist() if n.lower().endswith(".shp")):
        g = gpd.read_file(f"zip://{p}!{name}", bbox=clip)
        if len(g):
            shapes += [geom for geom in g.to_crs(CRS).geometry if geom is not None]
    if not shapes:
        return np.zeros(shape(), bool)
    return rasterize(((s, 1) for s in shapes), out_shape=shape(), transform=transform(), fill=0, dtype="uint8") > 0


def flooded(h: np.ndarray, base: np.ndarray) -> np.ndarray:
    return (h >= FLOOD_DEPTH) & ~(base >= FLOOD_DEPTH)


def compare(a: np.ndarray, ref: np.ndarray) -> dict:
    inter, union = (a & ref).sum(), (a | ref).sum()
    return {"hit_rate": float(inter / ref.sum()) if ref.sum() else None,
            "false_share": float((a & ~ref).sum() / a.sum()) if a.sum() else None,
            "csi": float(inter / union) if union else None}


def exposure(f: np.ndarray, wc: np.ndarray) -> dict:
    ha = DX * DX / 1e4
    out = {LANDCOVER[k][0]: round(float((f & (wc == k)).sum() * ha), 1) for k in LANDCOVER if (f & (wc == k)).any()}
    return out


def river_km(path: np.ndarray) -> float:
    ny, nx = shape()
    x, y = to_xy(path // nx, path % nx)
    x, y = ndimage.uniform_filter1d(x, 9, mode="nearest"), ndimage.uniform_filter1d(y, 9, mode="nearest")  # D8 zigzag out
    return round(float(np.hypot(np.diff(x), np.diff(y)).sum()) / 1000, 1)


def main(reuse: bool = False) -> dict:
    g = build_grid()
    scen, meta = scenarios()
    depth = {}
    for s in scen:
        run = RUNS / s["id"]
        if not (reuse and (run / "sfincs_map.nc").exists()):
            if run.exists():
                shutil.rmtree(run)
            write_run(run, g, s["q"])
            print(f"SFINCS {s['id']}: {s['q']:.0f} m3/s …", flush=True)
            run_sfincs(run)
        depth[s["id"]] = read_hmax(run, g)
        s["steady_check_m"] = steady(run)
    base = depth["base"]
    meas = flooded(depth["measured"], base)
    ha = DX * DX / 1e4
    for s in scen:
        h = depth[s["id"]]
        f = flooded(h, base)
        s["flooded_ha"] = round(float(f.sum() * ha), 1)
        s["max_depth_m"] = round(float(h[f].max()) if f.any() else 0.0, 2)
        s["exposure_ha"] = exposure(f, g["wc"])
        if s["read_as"] not in ("design", "base"):
            s["vs_measured"] = compare(f, meas)
        save_depth(s["id"], h)
    save_hillshade(g["dem"])
    # the gauge's 10- and 100-year floods against the Copernicus (JRC) global flood hazard map
    jrc = {}
    for rp in (10, 100):
        j = warp([fetch(f"jrc_RP{rp}.tif")], "nearest", nodata=0.0, clip_negative=True)
        jf = (j >= FLOOD_DEPTH) & g["mask"] & ~(base >= FLOOD_DEPTH)
        ours = flooded(depth[f"design_T{rp}"], base)
        jrc[f"T{rp}"] = {"jrc_flooded_ha": round(float(jf.sum() * ha), 1),
                         "kai_flooded_ha": round(float(ours.sum() * ha), 1), **compare(ours, jf)}
        save_depth(f"jrc_T{rp}", np.where(g["mask"], j, 0))
        zone = official_zone(rp)
        if zone is not None:
            zf = zone & g["mask"] & ~(base >= FLOOD_DEPTH)
            jrc[f"T{rp}"]["snczi"] = {"snczi_flooded_ha": round(float(zf.sum() * ha), 1), **compare(ours, zf),
                                      "jrc": compare(jf, zf)}
            save_depth(f"snczi_T{rp}", np.where(g["mask"] & zone, 1.0, 0.0))
    res = {"reach": {"crs": CRS, "bbox": [X0, Y0, X1, Y1], "dx_m": DX, "river_km": river_km(g["path"]),
                     "model_cells": int(g["mask"].sum()), "source_xy": SOURCE_XY, "event_water_year": EVENT_YEAR},
           "settings": {"base_flow_m3s": BASE_FLOW, "flood_depth_m": FLOOD_DEPTH, "hand_max_m": HAND_MAX,
                        "channel_depth_m": CHANNEL_DEPTH, "tstop_h": TSTOP_H,
                        "riparian_canopy_removed": {"within_m": RIPARIAN_M, "opening_m": OPENING_CELLS * DX,
                                                    "cells": g["riparian_cells"], "mean_lowering_m": round(g["riparian_lowering_m"], 2)}, "manning": {v[0]: v[1] for v in LANDCOVER.values()},
                        "manning_channel": N_CHANNEL},
           "gauge": meta, "scenarios": scen, "jrc_check": jrc}
    (HERE / "results").mkdir(exist_ok=True)
    (HERE / "results/flood_maps.json").write_text(json.dumps(res, indent=1, default=float))
    np.savez_compressed(OUT.parent.parent / "map_runs" / "grid.npz", zb=g["zb"], dem=g["dem"], wc=g["wc"],
                        mask=g["mask"], chan=g["chan"], path=g["path"])
    return res


if __name__ == "__main__":
    r = main(reuse="--reuse" in sys.argv)
    for s in r["scenarios"]:
        print(f"{s['id']:12} q={s['q']:7.1f}  T={s['T'] if s['T'] is None else round(s['T'], 1)}  "
              f"flooded={s['flooded_ha']:8.1f} ha  steady={s['steady_check_m']:.3f} m  {s.get('vs_measured', '')}")
    print(json.dumps(r["jrc_check"], indent=1))
