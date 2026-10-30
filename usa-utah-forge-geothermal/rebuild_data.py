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

Phase 4 (notebooks 4 and 5):
* data/tracers_2024_circulation.csv  QuantumPro tracers 1–10 (GDR 1701): injection time and the concentration (ppb) in each
                                16B sample, hours since the GDR 1683 test start
* data/dts_16B_2024.csv         16B fibre temperatures (GDR 1721): 200-ft medians before the test (4 Aug) and on days 6.5–7.7
                                of the test, with the spread over that window

Phase 5 (notebook 6):
* data/minifrac_16B_2023_isip.csv   the seven 16B mini-frac tests (GDR 1570): depth, initial pressure and the instantaneous
                                shut-in pressure (ISIP) of every injection cycle, derived here (straight line in √Δt)
* data/minifrac_16B_2023_mf2.csv    the MF-2 test record every 2 s: interval pressure (psi) and rate (cc/s)
* data/pt_gauge_16B_2024_hourly.csv the 16B gauge at 7,056.67 ft MD (GDR 1608): hourly medians of temperature and pressure
* data/temperature_16A_2021.csv     the 16A(78)-32 temperature log of 16 Aug 2021 (GDR 1421): 5 m medians along MD
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

# ---------------------------------------------------------------------- phase 4
t_h, trs = ft.read_tracers(ft.fetch("tracer"))
rows = [{"tracer": x["tracer"], "injected_t_h": round(x["injected_t_h"], 4), "sample_t_h": round(float(t), 4), "c_ppb": round(c, 4)}
        for x in trs for t, c in zip(t_h, x["c_ppb"])]
pd.DataFrame(rows).to_csv(out / "tracers_2024_circulation.csv", index=False)
ts, zs, As = ft.read_dts(ft.fetch("dts_static"))
tf, zf, Af = ft.read_dts(ft.fetch("dts_flowing"))
w = (tf >= 156.0) & (tf < 184.0)
b, Ts = ft.dts_bins(zs, np.median(As, 0))
_, Tf = ft.dts_bins(zf, np.median(Af[w], 0))
_, Sf = ft.dts_bins(zf, np.std(Af[w], 0))
pd.DataFrame({"md_ft": b, "static_4aug_c": np.round(Ts, 3), "flowing_days_6p5_7p7_c": np.round(Tf, 3),
              "flowing_sd_c": np.round(Sf, 3)}).to_csv(out / "dts_16B_2024.csv", index=False)
deep = (zf >= 3200) & (zf <= 9240)
prof = np.median(Af[w], 0)
(out / "dts_16B_2024_deep.json").write_text(json.dumps({"window_h": [156.0, 184.0], "md_ft": [3200.0, 9240.0],
    "slope_c_per_km_md": round(float(np.polyfit(zf[deep] * ft.FT, prof[deep], 1)[0] * 1000), 6),
    "T_top_c": round(float(np.median(prof[(zf >= 3200) & (zf < 3300)])), 4), "T_bottom_c": round(float(np.median(prof[(zf > 9140) & (zf <= 9240)])), 4),
    "traces_in_window": int(w.sum())}, indent=1))
print("wrote phase 4 data: tracers_2024_circulation.csv, dts_16B_2024.csv, dts_16B_2024_deep.json")

# ---------------------------------------------------------------------- phase 5
tests = ft.read_minifrac(ft.fetch("minifrac"))
rows = [{"test": x["test"], "md_ft": x["md_ft"], "tvd_ft_kb": x["tvd_ft_kb"], "p_initial_psi": round(x["p_initial_psi"], 2), "cycle": i + 1,
         "shut_in_s": round(c["shut_in_s"], 3), "isip_psi": round(c["isip_psi"], 2), "max_psi": round(c["max_psi"], 2), "volume_l": round(c["volume_l"], 3)}
        for x in tests for i, c in enumerate(x["cycles"])]
pd.DataFrame(rows).to_csv(out / "minifrac_16B_2023_isip.csv", index=False)
mf2 = next(x for x in tests if x["test"] == 2)["curves"]
k = np.arange(0, len(mf2["TIME"]), 16)                          # 0.125 s samples → every 2 s
pd.DataFrame({"time_s": mf2["TIME"][k].round(3), "p_psi": np.round(mf2["APQJ"][k], 2), "rate_cc_s": np.round(mf2["PTFRC"][k], 3)}).to_csv(
    out / "minifrac_16B_2023_mf2.csv", index=False)
g = pd.DataFrame(ft.read_pt_gauge(ft.fetch("pt_16b")), columns=["time", "p_psi", "T_c"])
g["hour"] = g["time"].dt.floor("h")
h = g.groupby("hour").agg(T_c=("T_c", "median"), p_psi=("p_psi", "median"), n=("T_c", "size")).reset_index()
h["hour"] = h["hour"].dt.strftime("%Y-%m-%dT%H:%M")
h["T_c"] = h["T_c"].round(3); h["p_psi"] = h["p_psi"].round(2)
h.to_csv(out / "pt_gauge_16B_2024_hourly.csv", index=False)
md, T = ft.read_16a_survey(ft.fetch("temp_surveys"))
b5 = np.floor(md / 5.0).astype(int)
t16 = pd.DataFrame({"b": b5, "T": T}).groupby("b")["T"].median()
pd.DataFrame({"md_m": (t16.index.values * 5.0 + 2.5).round(2), "T_c": t16.values.round(3)}).to_csv(out / "temperature_16A_2021.csv", index=False)
print("wrote phase 5 data: minifrac_16B_2023_isip.csv, minifrac_16B_2023_mf2.csv, pt_gauge_16B_2024_hourly.csv, temperature_16A_2021.csv")
