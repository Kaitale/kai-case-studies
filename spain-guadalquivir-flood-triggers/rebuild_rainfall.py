"""Catchment rainfall for the rainfall-trigger comparison (MIT licence).

For each gauge: its upstream catchment from HydroBASINS level 8 (the sub-catchment near the gauge, within about 13 km,
whose upstream area best matches the gauge's catchment area), the NASA POWER cells (MERRA-2 grid, 0.5° x 0.625°) that
cover it with area weights, and the catchment-mean daily rainfall (PRECTOTCORR, bias-corrected) from the NASA POWER
daily API, the source used by Model Library's Andalucía rainfall-trigger study. Writes
  data/rain_catchments.csv     gauge, HydroBASINS sub-catchments used, their area against the gauge's
  data/rain_cell_weights.csv   NASA POWER cells and the share of each catchment they cover
  data/rainfall_maxima.csv     each water year's largest 1-, 3-, 5-, 10- and 30-day catchment rainfall and its
                               October-April total (mm), the index of Model Library's Andalucía study

Needs geopandas and the HydroBASINS Europe level-8 shapefile (https://www.hydrosheds.org/products/hydrobasins):
  python rebuild_rainfall.py path/to/hybas_eu_lev08_v1c.shp
"""
from __future__ import annotations

import json
import math
import pathlib
import sys
import time
import urllib.parse
import urllib.request

import numpy as np
import pandas as pd

START, END = "1984-10-01", "2022-09-30"
POWER = "https://power.larc.nasa.gov/api/temporal/daily/point"
DLAT, DLON = 0.5, 0.625   # MERRA-2 grid of the POWER precipitation
WINDOWS = [1, 3, 5, 10, 30]
HERE = pathlib.Path(__file__).resolve().parent


def catchments(shp: str, gauges: pd.DataFrame):
    import geopandas as gpd
    from shapely.geometry import Point, box
    g = gpd.read_file(shp, bbox=(-7.5, 36.5, -1.8, 38.9))
    mb = g[g.contains(Point(-3.7994, 37.9842))].MAIN_BAS.iloc[0]          # the Guadalquivir main basin
    b = g[g.MAIN_BAS == mb].copy()
    up: dict[int, list[int]] = {}
    for h, d in zip(b.HYBAS_ID, b.NEXT_DOWN):
        up.setdefault(int(d), []).append(int(h))

    def upstream(h):
        seen, st = [], [int(h)]
        while st:
            x = st.pop(); seen.append(x); st += up.get(x, [])
        return seen

    rows, weights = [], []
    for gid, r in gauges.iterrows():
        pt = Point(r.lon, r.lat)
        best = None
        for h in b[b.distance(pt) < 0.12].HYBAS_ID:
            u = upstream(h); a = float(b[b.HYBAS_ID.isin(u)].SUB_AREA.sum())
            sc = abs(math.log(a / r.catchment_km2))
            if best is None or sc < best[0]:
                best = (sc, u, a)
        _, u, a = best
        poly = b[b.HYBAS_ID.isin(u)].union_all() if hasattr(b, "union_all") else b[b.HYBAS_ID.isin(u)].unary_union
        rows.append({"gauge_id": gid, "name": r["name"], "catchment_km2": r.catchment_km2, "hybas_km2": round(a),
                     "area_ratio": round(a / r.catchment_km2, 2), "hybas_ids": " ".join(map(str, u))})
        x0, y0, x1, y1 = poly.bounds
        cells = []
        for i in range(math.floor(y0 / DLAT) - 1, math.ceil(y1 / DLAT) + 2):
            for j in range(math.floor(x0 / DLON) - 1, math.ceil(x1 / DLON) + 2):
                la, lo = i * DLAT, j * DLON
                inter = poly.intersection(box(lo - DLON / 2, la - DLAT / 2, lo + DLON / 2, la + DLAT / 2)).area
                if inter > 0:
                    cells.append((round(la, 3), round(lo, 4), inter))
        tot = sum(c[2] for c in cells)
        weights += [{"gauge_id": gid, "lat": la, "lon": lo, "weight": round(w / tot, 5)} for la, lo, w in cells]
    return pd.DataFrame(rows), pd.DataFrame(weights)


def power(cells: list[tuple[float, float]], cache=HERE / "power_cache") -> dict:
    cache.mkdir(exist_ok=True)
    out = {}
    for k, (la, lo) in enumerate(cells):
        f = cache / f"{la:.3f}_{lo:.4f}.json"
        for attempt in range(6):
            if f.exists():
                break
            q = {"parameters": "PRECTOTCORR", "community": "AG", "latitude": f"{la:.3f}", "longitude": f"{lo:.4f}",
                 "start": START.replace("-", ""), "end": END.replace("-", ""), "format": "JSON"}
            try:
                f.write_text(urllib.request.urlopen(POWER + "?" + urllib.parse.urlencode(q), timeout=300).read().decode()); time.sleep(1)
            except OSError as e:
                if attempt == 5:
                    raise
                print("  retry:", e); time.sleep(15 * (attempt + 1))
        d = json.loads(f.read_text())["properties"]["parameter"]["PRECTOTCORR"]
        s = pd.Series(d, dtype=float); s.index = pd.to_datetime(s.index, format="%Y%m%d"); s[s < 0] = np.nan   # -999 = missing
        out[(la, lo)] = s
        print(f"  NASA POWER cells {k + 1}/{len(cells)}")
    return out


def main() -> None:
    gauges = pd.read_csv(HERE / "data/gauges.csv").set_index("gauge_id")
    cat, w = catchments(sys.argv[1], gauges)
    cat.to_csv(HERE / "data/rain_catchments.csv", index=False); w.to_csv(HERE / "data/rain_cell_weights.csv", index=False)
    cells = sorted({(r.lat, r.lon) for r in w.itertuples()})
    print(len(cat), "catchments,", len(cells), "NASA POWER cells")
    P = power(cells)
    am = pd.read_csv(HERE / "data/annual_maxima.csv")
    rows = []
    for gid, ww in w.groupby("gauge_id"):
        s = sum(P[(r.lat, r.lon)] * r.weight for r in ww.itertuples())
        wy = s.index.year + (s.index.month >= 10)
        mx = {n: s.rolling(n).sum().groupby(wy).max() for n in WINDOWS}
        octapr = s[(s.index.month >= 10) | (s.index.month <= 4)].groupby(wy[(s.index.month >= 10) | (s.index.month <= 4)]).sum()
        for y in am[am.gauge_id == gid].water_year:
            rows.append({"gauge_id": gid, "water_year": int(y), **{f"rain_max_{n}d_mm": round(float(mx[n][y]), 2) for n in WINDOWS},
                         "rain_oct_apr_mm": round(float(octapr[y]), 1)})
    pd.DataFrame(rows).to_csv(HERE / "data/rainfall_maxima.csv", index=False)
    print("wrote data/rain_catchments.csv, data/rain_cell_weights.csv, data/rainfall_maxima.csv")


if __name__ == "__main__":
    main()
