"""Rebuild data/ from the public Utah FORGE files on the DOE Geothermal Data Repository (MIT licence).

    python rebuild_data.py          # downloads ~27 MB into gdr_cache/ (checked by SHA-256), writes data/

Writes only derived values (CC BY 4.0, with the FORGE credit):
* data/forge_model.npz          granitoid flag per cell (50 × 50 × 55); temperature (°C), pressure (MPa) and depth below
                                ground (m) at the 51 × 51 × 56 nodes, as float32; the local → UTM transform
* data/well_58_32_log_2018.csv  58-32 temperature and pressure, 8 Nov 2018, resampled every 5 m of depth below ground
* data/wells.csv                surveyed FORGE well heads (UTM 12N, NAD83; December 2021) and their model coordinates

Phase 3 (notebooks 2 and 3):
* data/fmi_58_32.csv            58-32 FMI picks (GDR 1299): depth along the hole in m, FVA and FVAH apertures in mm
* data/trajectories_16A_16B.csv 16A(78)-32 and 16B(78)-32 trajectories (GDR 1646), every 10 m of measured depth
* data/natural_fracture_poles.csv  the four natural-fracture sets of the 2024 reference DFN (GDR 1646, realisation 1):
                                pole trend and plunge (0.1°) and radius (0.1 m)
* data/stimulated_dfn.csv       the May 2024 connected DFN of the stimulated reservoir (GDR 1646): centre, radius, pole,
                                aperture
* data/circulation_2024_aug_daily.csv  extended circulation test (GDR 1683): daily medians of the 30-second data
* data/circulation_2024_summary.json   the steady 10 bpm window (days 14-26) with the field meter calibration, and the
                                April 2024 9-hour test (GDR 1611) final step
"""
import json
import pathlib

import numpy as np
import pandas as pd

import forge_tools as ft

out = pathlib.Path("data"); out.mkdir(exist_ok=True)
mesh = ft.read_mesh(ft.fetch("mesh"))
tr = ft.fit_transform(mesh["local"], mesh["utm"])
print(f"transform: +x azimuth {tr['azimuth_x_deg']:.3f}°, residual {tr['max_residual_m']:.2e} m")
ic = ft.read_ic(ft.fetch("ic"))
np.savez_compressed(out / "forge_model.npz", granite=mesh["granite"], T_c=ic["T_c"].astype(np.float32),
                    p_mpa=ic["p_mpa"].astype(np.float32), depth_m=ic["depth_m"].astype(np.float32),
                    transform=np.array(json.dumps(tr)))
pt = ft.read_las_pt(ft.fetch("pt2018"))
d = np.arange(5.0, pt["depth_m"].max(), 5.0)
pd.DataFrame({"depth_m": d, "T_c": np.interp(d, pt["depth_m"], pt["T_c"]).round(3),
              "P_mpa": np.interp(d, pt["depth_m"], pt["P_mpa"]).round(4)}).to_csv(out / "well_58_32_log_2018.csv", index=False)
rows = []
for ln in ft.fetch("wells").read_text().splitlines():
    p = ln.split(",")
    if len(p) > 6 and p[6] == "WELL":
        x, y = ft.to_local(tr, float(p[1]), float(p[2]))
        rows.append({"well": p[0].replace("-WELL", ""), "easting": float(p[1]), "northing": float(p[2]), "lat": float(p[3]),
                     "lon": float(p[4]), "elev_m": float(p[5]), "x_model_m": round(float(x), 2), "y_model_m": round(float(y), 2)})
pd.DataFrame(rows).to_csv(out / "wells.csv", index=False)
print("wrote", ", ".join(sorted(f.name for f in out.iterdir())))

# ---------------------------------------------------------------------- phase 3
f = ft.read_fmi(ft.fetch("fmi"))
pd.DataFrame({"depth_m": np.round(f["depth_m"], 3), "fva_mm": np.round(f["fva_mm"], 5), "fvah_mm": np.round(f["fvah_mm"], 5)}).to_csv(
    out / "fmi_58_32.csv", index=False)
feb, may = ft.fetch("dfn_feb"), ft.fetch("dfn_may")
rows = []
for w in ("16A(78)-32", "16B(78)-32"):
    t = ft.read_trajectory(feb, w)
    md = np.arange(0.0, t["md"][-1], 10.0)
    rows.append(pd.DataFrame({"well": w, "md_m": md, "easting": np.interp(md, t["md"], t["E"]).round(2),
                              "northing": np.interp(md, t["md"], t["N"]).round(2), "elev_m": np.interp(md, t["md"], t["elev"]).round(2)}))
pd.concat(rows).to_csv(out / "trajectories_16A_16B.csv", index=False)
rows = []
for name in ("Set 1 Dipping South", "Set 2 Striking SSW", "Set 3 Dipping West", "Set 4 Dipping East"):
    d = ft.read_fractures(ft.member(feb, f"Global Coordinates/Individual Sets/{name} Min 20m Radius_1.csv"))
    rows.append(pd.DataFrame({"set": name, "trend": d["trend"].round(1), "plunge": d["plunge"].round(1), "radius_m": d["radius"].round(1)}))
pd.concat(rows).to_csv(out / "natural_fracture_poles.csv", index=False)
d = ft.read_fractures(ft.member(may, "Global Coordinates/Connected_DFN_Including_20pct_Stochastic.csv"))
pd.DataFrame({"easting": d["E"].round(2), "northing": d["N"].round(2), "elev_m": d["elev"].round(2), "radius_m": d["radius"].round(2),
              "trend": d["trend"].round(2), "plunge": d["plunge"].round(2), "aperture_mm": (d["aperture"] * 1e3).round(5)}).to_csv(
    out / "stimulated_dfn.csv", index=False)
daily, summ = ft.circulation_daily(ft.fetch("ect"))
daily.round(3).to_csv(out / "circulation_2024_aug_daily.csv")
import datetime as _dt  # noqa: E402
import io as _io  # noqa: E402

import openpyxl  # noqa: E402

ws = openpyxl.load_workbook(_io.BytesIO(ft.member(ft.fetch("circ_apr"), "Injection_Circulation_Test")), read_only=True, data_only=True).worksheets[0]
rec = [r for r in ws.iter_rows(values_only=True) if isinstance(r[1], _dt.time) and isinstance(r[2], (int, float))]
th = np.array([r[1].hour * 3600 + r[1].minute * 60 + r[1].second for r in rec], float)
th = (th - th[0]) / 3600
q = np.array([float(r[4]) if isinstance(r[4], (int, float)) else np.nan for r in rec])
pr = np.array([float(r[2]) for r in rec]) * ft.PSI / 1e6
on = q > 0.5
t_off = th[on].max()
last = (th > t_off - 1.5) & (th < t_off - 0.1) & on
summ["april_2024"] = {"final_rate_bpm": float(np.nanmedian(q[last])), "final_whp_mpa": float(np.nanmedian(pr[last])),
                      "rate_bpm_max": float(np.nanmax(q)), "hours": float(t_off - th[on].min()),
                      "reported_production_bpm_end": 8.2, "reported_T_wellhead_end_f": 282.0}
(out / "circulation_2024_summary.json").write_text(json.dumps({k: (round(v, 6) if isinstance(v, float) else v) for k, v in summ.items()}, indent=1))
print("wrote phase 3 data:", ", ".join(sorted(f.name for f in out.iterdir())))
