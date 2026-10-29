"""Rebuild data/gauges.csv and data/annual_maxima.csv from the source data (MIT licence).

Run it on your own connection (CEDEX refuses some cloud machines). It downloads the two public CEDEX files
(checked by SHA-256, cached in cedex_cache/), picks every Guadalquivir gauge with >= 500 km2 and >= 25 years
of daily flow in water years 1985-2022, queries the GloFAS 4.0 reanalysis for the 5 km cells within 0.1 deg
of each gauge from the Open-Meteo flood API (free for non-commercial use, data CC BY 4.0), keeps the cell
whose mean flow is closest to the gauge's, and writes each water year's largest daily flow from both.
    python rebuild_data.py
"""
import json
import math
import pathlib
import time
import urllib.parse
import urllib.request

import pandas as pd

import flood_tools as ft

START, END = "1984-10-01", "2022-09-30"
OM = "https://flood-api.open-meteo.com/v1/flood"


def dms(v):
    v = int(v); s = -1 if v < 0 else 1; v = abs(v)
    return s * (v // 10000 + (v // 100) % 100 / 60 + v % 100 / 3600)


def glofas(lat, lon, cache=pathlib.Path("glofas_cache")):
    cache.mkdir(exist_ok=True)
    q = {"latitude": f"{lat:.4f}", "longitude": f"{lon:.4f}", "daily": "river_discharge", "start_date": START, "end_date": END,
         "models": "consolidated_v4", "cell_selection": "nearest"}
    f = cache / f"{q['latitude']}_{q['longitude']}.json"
    for attempt in range(5):  # the free API drops a connection now and then
        if f.exists():
            break
        try:
            f.write_text(urllib.request.urlopen(OM + "?" + urllib.parse.urlencode(q), timeout=120).read().decode()); time.sleep(0.2)
        except OSError:
            if attempt == 4:
                raise
            time.sleep(5 * (attempt + 1))
    d = json.loads(f.read_text())
    return (round(d["latitude"], 3), round(d["longitude"], 3)), pd.Series(d["daily"]["river_discharge"], index=pd.to_datetime(d["daily"]["time"]), dtype=float)


def water_year_max(s, min_days=292):
    s = s.dropna(); wy = s.index.year + (s.index.month >= 10)
    g = s.groupby(wy); return g.max()[g.size() >= min_days]


est = pd.read_csv(ft.fetch_cedex("estaf.csv", ft.CEDEX_FILES["estaf.csv"]), sep=";", encoding="latin1"); est.columns = est.columns.str.strip()
q = pd.read_csv(ft.fetch_cedex("afliq.csv", ft.CEDEX_FILES["afliq.csv"]), sep=";", encoding="latin1", usecols=["indroea", "fecha", "caudal"])
q["fecha"] = pd.to_datetime(q.fecha, format="%d/%m/%Y", errors="coerce"); q = q.dropna()
q = q[(q.fecha >= START) & (q.fecha <= END) & (q.caudal >= 0)]
daily = {int(k): g.set_index("fecha").caudal.sort_index() for k, g in q.groupby("indroea")}
rows, am = [], []
for _, r in est.iterrows():
    gid = int(r.indroea)
    if gid not in daily or float(r.suprest) < 500 or len(daily[gid]) / 365.25 < 25:
        continue
    lat, lon, obs = dms(r.latwgs84), dms(r.longwgs84), daily[gid]
    best = None
    for di in range(-2, 3):
        for dj in range(-2, 3):
            key, s = glofas(lat + di * 0.05, lon + dj * 0.05)
            both = pd.concat([obs, s], axis=1, join="inner").dropna()
            if len(both) > 365 and both.iloc[:, 1].mean() > 0:
                ratio = both.iloc[:, 1].mean() / both.iloc[:, 0].mean()
                if best is None or abs(math.log(ratio)) < best[0]:
                    best = (abs(math.log(ratio)), key, s, ratio)
    _, cell, model, ratio = best
    ao, amod = water_year_max(obs), water_year_max(model)
    yrs = ao.index.intersection(amod.index)
    rows.append({"gauge_id": gid, "name": str(r.lugar).strip().title(), "catchment_km2": float(r.suprest), "lat": round(lat, 4), "lon": round(lon, 4),
                 "record_years_1985_2022": round(len(obs) / 365.25, 1), "glofas_cell_lat": cell[0], "glofas_cell_lon": cell[1],
                 "glofas_mean_flow_ratio": round(ratio, 3)})
    am += [{"gauge_id": gid, "water_year": int(y), "gauge_max_m3s": round(float(ao[y]), 2), "glofas_max_m3s": round(float(amod[y]), 2)} for y in yrs]
    print(rows[-1]["name"], len(yrs), "years")
pd.DataFrame(rows).to_csv("data/gauges_rebuilt.csv", index=False)
pd.DataFrame(am).to_csv("data/annual_maxima_rebuilt.csv", index=False)
print("wrote data/gauges_rebuilt.csv and data/annual_maxima_rebuilt.csv; compare them with the published files")
