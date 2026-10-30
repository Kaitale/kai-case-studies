"""Builds the Utah FORGE notebooks (run: python make_notebooks.py, then execute them)."""
import nbformat as nbf


def nb(cells):
    n = nbf.v4.new_notebook()
    n.cells = [nbf.v4.new_markdown_cell(c[1]) if c[0] == "md" else nbf.v4.new_code_cell(c[1]) for c in cells]
    n.metadata["kernelspec"] = {"name": "python3", "display_name": "Python 3", "language": "python"}
    return n


SETUP = """import json, pathlib, warnings
import numpy as np, pandas as pd, matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
import forge_tools as ft
warnings.filterwarnings("ignore")
plt.rcParams.update({"figure.dpi": 110, "axes.grid": False, "axes.spines.top": False, "axes.spines.right": False, "font.size": 10,
                     "axes.titleweight": "bold", "axes.titlesize": 11, "legend.frameon": False, "savefig.bbox": "tight", "savefig.facecolor": "white"})
GOLD, CHARCOAL, FILL, GRANITE, BLUE = "#c9a227", "#26292e", "#d8c7a3", "#b5838d", "#2a78d6"     # KAI energy palette
pathlib.Path("results").mkdir(exist_ok=True); pathlib.Path("figures").mkdir(exist_ok=True)

m = np.load("data/forge_model.npz")
granite, T, P, depth = m["granite"], m["T_c"].astype(float), m["p_mpa"].astype(float), m["depth_m"].astype(float)
tr = json.loads(str(m["transform"]))
wells = pd.read_csv("data/wells.csv").set_index("well")
log = pd.read_csv("data/well_58_32_log_2018.csv")
engine = json.loads(pathlib.Path("results/kai_engine_results.json").read_text())
zn = ft.Z_BOTTOM + np.arange(ft.NZ + 1) * ft.CELL            # node elevations, m a.s.l. (index 0 = deepest)
xn = np.arange(ft.NXY + 1) * ft.CELL                          # node positions along the model axes, m
ground = (zn[:, None, None] + depth).mean(axis=0)             # ground elevation above each node column
print(f"{granite.size:,} cells of {ft.CELL:.0f} m: {granite.sum():,} granitoid, {(~granite).sum():,} basin fill")
print(f"temperature {T.min():.1f} to {T.max():.1f} °C; model +x axis points to azimuth {tr['azimuth_x_deg']:.1f}°")"""

nb1 = nb([
("md", """# 1 · Structure and temperature: the Utah FORGE geothermal site

**KAI-GeoEnergy · KAI Reservoir Lab · Utah FORGE, Milford, Utah (USA)**

**Question.** Where is the hot granitoid under the basin fill, how hot is it, and can the 3-D temperature model be trusted at the deep well?

**Data.** Utah FORGE is the U.S. Department of Energy's field laboratory for enhanced geothermal systems (EGS). Its data are public on the DOE Geothermal Data Repository (GDR) under CC BY 4.0:
* the Phase 2 3-D model export from Leapfrog Geothermal (GDR 1205, Podgorney 2020, DOI [10.15121/1605155](https://doi.org/10.15121/1605155)): lithology on a 2.5 × 2.5 × 2.75 km grid of 50 m cells, and temperature, pressure and stress at its nodes;
* the temperature and pressure log of deep well **58-32 (MU-ESW1)** run on 8 November 2018 (GDR 1101, DOI [10.15121/1493769](https://doi.org/10.15121/1493769));
* the surveyed well-head coordinates of December 2021 (GDR 1358).

This folder holds only values derived from them (`data/`). `rebuild_data.py` downloads the GDR files, checks their SHA-256 and rebuilds `data/`. *Credit: Utah FORGE, U.S. Department of Energy, via the Geothermal Data Repository (OpenEI), CC BY 4.0.*

**Method.** The granitoid surface is the top of the highest granitoid cell in each column. Temperature at the well is interpolated from the model nodes (bilinear across the map, linear with depth). The 58-32 log is converted from measured depth below the kelly bushing (21.5 ft above ground) to depth below ground; the well is treated as vertical (its survey stays within about 40 m of the well head, less than one cell).

**What this check is, and is not.** The source model was built with data from 58-32, so the comparison is a consistency check of the export, the georeferencing and the interpolation. It is not a blind test."""),
("code", SETUP),
("md", """## The grid on the map

The model's local metres are rotated against UTM. A least-squares fit of the 137,500 cell centres in both coordinate systems recovers the rotation and checks it: the ground elevation the model implies at 58-32 should match the surveyed well head."""),
("code", """w = wells.loc["58-32"]
x58, y58 = w.x_model_m, w.y_model_m
g58 = float(ft.column_profile(zn[:, None, None] + depth, x58, y58).mean())
geo = {"azimuth_x_deg": tr["azimuth_x_deg"], "fit_residual_m": tr["max_residual_m"], "x58_m": x58, "y58_m": y58,
       "model_ground_m": g58, "surveyed_ground_m": w.elev_m, "difference_m": g58 - w.elev_m}
print(json.dumps({k: round(v, 3) for k, v in geo.items()}, indent=1))"""),
("md", """## The granitoid under the basin fill"""),
("code", """top = ft.granite_top(granite)                                     # (50, 50) elevation of the granitoid top
gcell = 0.25 * (ground[:-1, :-1] + ground[1:, :-1] + ground[:-1, 1:] + ground[1:, 1:])
d2g = gcell - top
i58, j58 = int(x58 // ft.CELL), int(y58 // ft.CELL)
structure = {"depth_to_granite_min_m": float(d2g.min()), "depth_to_granite_max_m": float(d2g.max()), "depth_to_granite_mean_m": float(d2g.mean()),
             "granite_top_58_32_elev_m": float(top[j58, i58]), "depth_to_granite_58_32_m": float(g58 - top[j58, i58]),
             "granite_volume_km3": float(granite.sum() * ft.CELL**3 / 1e9)}
print(json.dumps({k: round(v, 1) for k, v in structure.items()}, indent=1))

fig, ax = plt.subplots(1, 2, figsize=(12, 5))
ext = [0, 2500, 0, 2500]
im = ax[0].imshow(d2g, origin="lower", extent=ext, cmap="cividis_r"); fig.colorbar(im, ax=ax[0], label="depth to granitoid (m below ground)")
cs = ax[0].contour(np.arange(25, 2500, 50), np.arange(25, 2500, 50), d2g, levels=range(600, 2000, 200), colors="white", linewidths=0.6)
ax[0].clabel(cs, fmt="%d m", fontsize=7)
for name, r in wells.iterrows():
    if 0 <= r.x_model_m <= 2500 and 0 <= r.y_model_m <= 2500:
        ax[0].plot(r.x_model_m, r.y_model_m, "o", color=GOLD, mec=CHARCOAL, ms=6); ax[0].annotate(name, (r.x_model_m, r.y_model_m), xytext=(4, 4), textcoords="offset points", fontsize=8)
ax[0].set_title("Depth to the granitoid"); ax[0].set_xlabel(f"model x (m), towards azimuth {tr['azimuth_x_deg']:.0f}°"); ax[0].set_ylabel("model y (m)")
# cross-section along x through 58-32
sec = granite[:, j58, :]
ax[1].imshow(sec, origin="lower", extent=[0, 2500, ft.Z_BOTTOM, ft.Z_TOP], aspect="auto", cmap=ListedColormap([FILL, GRANITE]))
Tsec = 0.5 * (T[:, j58, :] + T[:, j58 + 1, :])
cs = ax[1].contour(xn, zn, Tsec, levels=[100, 150, 175, 200, 225, 250], colors=CHARCOAL, linewidths=0.8); ax[1].clabel(cs, fmt="%d °C", fontsize=7)
ax[1].plot(xn, 0.5 * (ground[j58] + ground[j58 + 1]), color=CHARCOAL, lw=1.5)
ax[1].axvline(x58, color=GOLD, lw=2); ax[1].text(x58 + 20, 1300, "58-32", color=CHARCOAL, fontsize=8)
ax[1].set_ylim(ft.Z_BOTTOM, 1800); ax[1].set_xlabel("model x (m)"); ax[1].set_ylabel("elevation (m a.s.l.)")
ax[1].set_title("Section through 58-32: basin fill (tan) over granitoid (rose), isotherms")
fig.tight_layout(); fig.savefig("figures/forge_structure.png")"""),
("md", """## Temperature in 3-D

The depth of the 175 °C isotherm (the bottom of the usual EGS temperature window) across the site, and how much granitoid is hotter than each temperature."""),
("code", """def iso_map(t_iso):
    out = np.full((ft.NXY + 1, ft.NXY + 1), np.nan)
    for j in range(ft.NXY + 1):
        for i in range(ft.NXY + 1):
            v = ft.isotherm_depth(T[:, j, i], depth[:, j, i], t_iso)
            out[j, i] = np.nan if v is None else v
    return out

iso175 = iso_map(175.0)
Tc = ft.cell_average(T)
vol = {str(t): float((granite & (Tc >= t)).sum() * ft.CELL**3 / 1e9) for t in (150, 175, 200, 225)}
print("granitoid volume hotter than (km³):", {k: round(v, 2) for k, v in vol.items()})
print(f"175 °C isotherm: {np.nanmin(iso175):.0f} to {np.nanmax(iso175):.0f} m below ground")

fig, ax = plt.subplots(1, 2, figsize=(12, 4.6))
im = ax[0].imshow(iso175, origin="lower", extent=[-25, 2525, -25, 2525], cmap="inferno_r"); fig.colorbar(im, ax=ax[0], label="m below ground")
ax[0].plot(x58, y58, "o", color=GOLD, mec=CHARCOAL); ax[0].set_title("Depth of the 175 °C isotherm"); ax[0].set_xlabel("model x (m)"); ax[0].set_ylabel("model y (m)")
ts = [150, 175, 200, 225]
ax[1].bar([f"≥ {t} °C" for t in ts], [vol[str(t)] for t in ts], color=[GRANITE, GOLD, "#d9822b", "#b23a48"])
for k_, t in enumerate(ts):
    ax[1].text(k_, vol[str(t)] + 0.15, f"{vol[str(t)]:.1f}", ha="center")
ax[1].set_ylabel("granitoid volume in the model (km³)"); ax[1].set_title("Hot granitoid within the 17.2 km³ model")
fig.tight_layout(); fig.savefig("figures/forge_temperature.png")"""),
("md", """## The model against the 58-32 temperature log (8 November 2018)"""),
("code", """Tcol = ft.column_profile(T, x58, y58); dcol = g58 - zn                   # bottom → top
dd = np.arange(np.ceil(dcol.min() / 10) * 10, min(dcol.max(), log.depth_m.max()), 10.0)
T_log = np.interp(dd, log.depth_m, log.T_c); T_mod = np.interp(dd, dcol[::-1], Tcol[::-1]); diff = T_mod - T_log
in_gr = dd > structure["depth_to_granite_58_32_m"]
grad = lambda d, t: float(np.polyfit(d, t, 1)[0] * 1000)
check = {"compared_from_m": float(dd[0]), "compared_to_m": float(dd[-1]), "n": int(len(dd)), "bias_c": float(diff.mean()),
         "rmse_c": float(np.sqrt(np.mean(diff**2))), "max_abs_c": float(np.abs(diff).max()),
         "gradient_basin_fill_log": grad(dd[~in_gr], T_log[~in_gr]), "gradient_basin_fill_model": grad(dd[~in_gr], T_mod[~in_gr]),
         "gradient_granite_log": grad(dd[in_gr], T_log[in_gr]), "gradient_granite_model": grad(dd[in_gr], T_mod[in_gr]),
         "T_log_max_c": float(log.T_c.max()), "log_max_depth_m": float(log.depth_m.max())}
print(json.dumps({k: round(v, 2) for k, v in check.items()}, indent=1))
iso58 = {str(t): ft.isotherm_depth(Tcol, dcol, t) for t in (150, 175, 200, 225)}
print("isotherm depths at 58-32 (m below ground):", {k: round(v) for k, v in iso58.items()})

fig, ax = plt.subplots(1, 2, figsize=(10, 6), sharey=True, gridspec_kw={"width_ratios": [2, 1]})
ax[0].plot(log.T_c, log.depth_m, color=CHARCOAL, lw=1.2, label="58-32 log, 8 Nov 2018")
ax[0].plot(Tcol, dcol, "o-", color=GOLD, ms=3, label="3-D model at 58-32")
ax[0].axhline(structure["depth_to_granite_58_32_m"], color=GRANITE, ls="--", lw=1); ax[0].text(60, structure["depth_to_granite_58_32_m"] - 30, "top of granitoid (model)", color=GRANITE, fontsize=8)
ax[0].invert_yaxis(); ax[0].set_xlabel("temperature (°C)"); ax[0].set_ylabel("depth below ground (m)"); ax[0].legend(loc="lower left")
ax[0].set_title("Temperature at 58-32"); ax[0].set_ylim(2800, 0)
ax[1].plot(diff, dd, color=BLUE); ax[1].axvline(0, color="#999", lw=0.8); ax[1].set_xlabel("model − log (°C)")
ax[1].set_title(f"RMSE {check['rmse_c']:.1f} °C, bias {check['bias_c']:+.1f} °C")
fig.tight_layout(); fig.savefig("figures/forge_58_32_check.png")"""),
("md", """## Pressure and stress

Pore pressure is close to hydrostatic. The source workbook defines the stresses by depth gradients (a normal-faulting regime, Sv > SHmax > Shmin); they are reported as they are defined there, as magnitudes with compression positive."""),
("code", """pc, dc = ft.cell_average(P), ft.cell_average(depth)
pfit = np.polyfit(dc.ravel(), pc.ravel(), 1)
stress = {"pore_pressure_gradient_kpa_m": float(pfit[0] * 1000), **{f"{k}_gradient_kpa_m": v for k, v in ft.STRESS_GRADIENTS_KPA_M.items()},
          **{f"{k}_at_2000m_mpa": v * 2 for k, v in ft.STRESS_GRADIENTS_KPA_M.items()}, "pore_pressure_at_2000m_mpa": float(np.polyval(pfit, 2000))}
print(json.dumps({k: round(v, 2) for k, v in stress.items()}, indent=1))"""),
("md", """## Same answer as the KAI engine

The KAI engine (`kai-engine reference forge`) builds the same model from the raw GDR files on its own Reservoir Lab grid. Its results are in `results/kai_engine_results.json`. The notebook stops if its own numbers drift from them."""),
("code", """e = engine
pairs = {
    "rotation azimuth (°)": (geo["azimuth_x_deg"], e["grid"]["transform"]["azimuth_x_deg"], 1e-6),
    "model vs surveyed ground at 58-32 (m)": (geo["difference_m"], e["well_58_32"]["ground_difference_m"], 0.01),
    "depth to granitoid at 58-32 (m)": (structure["depth_to_granite_58_32_m"], e["well_58_32"]["depth_to_granite_m"], 0.01),
    "depth to granitoid, shallowest (m)": (structure["depth_to_granite_min_m"], e["structure"]["depth_to_granite_m"]["min"], 0.01),
    "depth to granitoid, deepest (m)": (structure["depth_to_granite_max_m"], e["structure"]["depth_to_granite_m"]["max"], 0.01),
    "granitoid volume (km³)": (structure["granite_volume_km3"], e["structure"]["granite_volume_km3"], 1e-6),
    "granitoid ≥ 175 °C (km³)": (vol["175"], e["temperature"]["granite_volume_km3_above"]["175"], 0.01),
    "granitoid ≥ 200 °C (km³)": (vol["200"], e["temperature"]["granite_volume_km3_above"]["200"], 0.01),
    "58-32 log RMSE (°C)": (check["rmse_c"], e["well_58_32"]["log"]["rmse_c"], 0.01),
    "58-32 log bias (°C)": (check["bias_c"], e["well_58_32"]["log"]["bias_c"], 0.01),
    "175 °C isotherm at 58-32 (m)": (iso58["175"], e["well_58_32"]["isotherm_depth_m"]["175"], 0.5),
    "pore-pressure gradient (kPa/m)": (stress["pore_pressure_gradient_kpa_m"], e["pressure"]["gradient_kpa_per_m"], 0.01),
}
rows = []
for name, (mine, theirs, tol) in pairs.items():
    assert abs(mine - theirs) <= tol, f"{name}: notebook {mine} vs engine {theirs}"
    rows.append({"quantity": name, "notebook": round(mine, 2), "KAI engine": round(theirs, 2)})
summary = {"georeferencing": geo, "structure": structure, "granite_volume_km3_above": vol, "well_58_32": check,
           "isotherm_depth_58_32_m": iso58, "pressure_stress": stress}
pathlib.Path("results/nb1_structure_temperature.json").write_text(json.dumps(summary, indent=1))
pd.DataFrame(rows)"""),
("md", """## Published numbers

These are the numbers quoted in the README and on the case page. The notebook stops if they change."""),
("code", """published = {"depth_to_granite_58_32_m": 985, "depth_to_granite_min_m": 533, "depth_to_granite_max_m": 1911,
             "rmse_c": 1.7, "bias_c": 1.4, "granite_175_km3": 7.9, "granite_200_km3": 5.2, "iso175_58_32_m": 1899}
now = {"depth_to_granite_58_32_m": structure["depth_to_granite_58_32_m"], "depth_to_granite_min_m": structure["depth_to_granite_min_m"],
       "depth_to_granite_max_m": structure["depth_to_granite_max_m"], "rmse_c": check["rmse_c"], "bias_c": check["bias_c"],
       "granite_175_km3": vol["175"], "granite_200_km3": vol["200"], "iso175_58_32_m": iso58["175"]}
for k, v in published.items():
    assert abs(now[k] - v) <= (0.5 if isinstance(v, int) else 0.05), (k, now[k], v)
print("all published numbers reproduced")"""),
("md", """## What this gives the Reservoir Lab

* A georeferenced structural model: the granitoid surface lies **533–1,911 m** below ground across the site and **985 m** at 58-32 (at the 50 m resolution of the source grid).
* A temperature model that agrees with the 2018 log of 58-32 to **1.7 °C** RMSE (bias +1.4 °C) between 440 and 2,290 m. The basin fill heats up faster with depth than the granitoid in both.
* **7.9 km³** of granitoid hotter than 175 °C and **5.2 km³** hotter than 200 °C inside the model volume; at 58-32 the 175 °C isotherm is about **1,900 m** below ground.
* Initial pressure and stress for the flow and stress simulations of notebooks 2 and 3.

**Limits.** The temperature model is the source model, not a KAI interpretation; its accuracy away from the deep wells is not tested here. The stresses are depth gradients from the source workbook, not a stress model. The 50 m cells place the granitoid contact to ±25 m.

*References:* Podgorney, R. (2020). Utah FORGE: Data for 3-D Model Development — Lithology, Temperature, Pressure, and Stress. GDR, DOI 10.15121/1605155 · Utah FORGE (2018). Milford Deep Test Well 58-32 (MU-ESW1) Pressure and Temperature Logs. GDR, DOI 10.15121/1493769 · Utah FORGE (2021). Updated Well, Well Pad, and Seismic Station GPS Coordinates. GDR submission 1358."""),
])


SETUP3 = """import json, pathlib, warnings
import numpy as np, pandas as pd, matplotlib.pyplot as plt
import forge_tools as ft
warnings.filterwarnings("ignore")
plt.rcParams.update({"figure.dpi": 110, "axes.grid": False, "axes.spines.top": False, "axes.spines.right": False, "font.size": 10,
                     "axes.titleweight": "bold", "axes.titlesize": 11, "legend.frameon": False, "savefig.bbox": "tight", "savefig.facecolor": "white"})
GOLD, CHARCOAL, GRANITE, BLUE, GREY = "#c9a227", "#26292e", "#b5838d", "#2a78d6", "#8a8f98"     # KAI energy palette
pathlib.Path("results").mkdir(exist_ok=True); pathlib.Path("figures").mkdir(exist_ok=True)
E = json.loads(pathlib.Path("results/kai_engine_phase3.json").read_text())      # KAI engine run (simulated)
ens = E["ensemble"]
def pct(d, f="{:.1f}"):
    fm = lambda v: v if isinstance(v, str) else f.format(v)
    return f"{fm(d['P50'])} ({fm(d['P10'])}–{fm(d['P90'])})"
print(E["label"]); print(f"ensemble: {ens['members'] - ens['failed']}/{ens['members']} members ran, {ens['calibration_converged']} calibrated")"""

nb2 = nb([
("md", """# 2 · The fractured granite: from one image log to a calibrated fracture-network ensemble

**KAI-GeoEnergy · KAI Reservoir Lab · Utah FORGE, Milford, Utah (USA)**

**Question.** What do we know about the fractures in the FORGE granitoid, and how much of it survives a test against the 2024 circulation between wells 16A(78)-32 and 16B(78)-32?

**Data** (all on the DOE Geothermal Data Repository, GDR, under CC BY 4.0; `data/` holds only derived values, rebuilt by `rebuild_data.py`):
* **58-32 FMI fracture picks** (GDR 1299): 147 fractures between 7,393 and 7,527 ft, with apparent (FVA) and hydraulic (FVAH) aperture. The file has no dip or azimuth.
* **Fracture orientations and sizes** from the FORGE 2024 reference discrete fracture network (DFN) of Finnila and Jones (GDR 1646, DOI [10.15121/2440870](https://doi.org/10.15121/2440870)): four natural sets, 17,798 fractures of 13–145 m radius, conditioned on the FORGE image logs.
* **The stimulated network**: the May 2024 connected DFN of the same submission: planes fitted to the 2024 microseismicity, hydraulic fractures at the 16A stages and natural fractures at the wells (120 fractures).
* **Well trajectories** of 16A(78)-32 and 16B(78)-32 (GDR 1646), checked against the well table of the extended circulation test report (GDR 1683).
* **Stress direction**: SHmax N25E (range N10E–N40E) from the FORGE stress summary of Finnila and Podgorney (2020, GDR 1222).

*Credit: Utah FORGE, U.S. Department of Energy, via the Geothermal Data Repository (OpenEI), CC BY 4.0.*

**Method.** The fractures are an **equivalent continuum**: every fracture adds its Oda (1985) permeability tensor, a³A(I − nn)/12V, to the cells it crosses. Natural fractures larger than the cell are placed one by one (Poisson discs, power-law sizes); smaller ones add their expected tensor. The stimulated network is placed as given. In-situ apertures are unknown, so one factor on the stimulated apertures is **calibrated** on the August 2024 test; everything else is checked, not fitted (notebook 3).

**Labels.** Every model number here is **simulated** by the KAI Reservoir Lab engine (`results/kai_engine_phase3.json`). This notebook recomputes the data-derived numbers with the MIT helpers in `forge_tools.py` and stops if they disagree with the engine."""),
("code", SETUP3),
("md", """## What the image log says

Density along the hole (P10) is the count over the logged span. The apertures are skewed: a few wide fractures dominate any cubic-law permeability."""),
("code", """fmi = pd.read_csv("data/fmi_58_32.csv")
st = ft.fmi_stats(fmi.depth_m, fmi.fvah_mm); st_fva = ft.fmi_stats(fmi.depth_m, fmi.fva_mm)
for k in ("n", "n_with_aperture", "span_m", "p10_per_m"):
    assert abs(st[k] - E["fmi"][k]) <= 1e-4 * abs(E["fmi"][k]), k            # depths are stored to the mm
assert abs(st["aperture_mm_P50"] - E["fmi"]["aperture_m"]["P50"] * 1e3) < 1e-4     # apertures stored to 0.01 µm
print(json.dumps({k: round(v, 3) for k, v in st.items()}, indent=1))
print("FVA (apparent) median", round(st_fva["aperture_mm_P50"], 3), "mm")
fig, ax = plt.subplots(1, 2, figsize=(11, 4), gridspec_kw={"width_ratios": [1, 1.4]})
ok = fmi.fvah_mm > 0
ax[0].scatter(fmi.fvah_mm[ok], fmi.depth_m[ok], s=12, color=GRANITE); ax[0].scatter(np.full((~ok).sum(), 0.012), fmi.depth_m[~ok], marker="|", color=GREY, label="no aperture")
ax[0].set_xscale("log"); ax[0].invert_yaxis(); ax[0].set_xlabel("hydraulic aperture FVAH (mm)"); ax[0].set_ylabel("depth along 58-32 (m)"); ax[0].legend()
ax[0].set_title(f"58-32 FMI: {st['n']} fractures in {st['span_m']:.0f} m")
ax[1].hist(np.log10(fmi.fvah_mm[ok]), bins=25, color=GRANITE, alpha=0.8, label="FVAH (hydraulic)")
ax[1].hist(np.log10(fmi.fva_mm[fmi.fva_mm > 0]), bins=25, histtype="step", color=CHARCOAL, label="FVA (apparent)")
ax[1].set_xlabel("log10 aperture (mm)"); ax[1].set_ylabel("fractures"); ax[1].legend(); ax[1].set_title("Aperture distribution")
fig.savefig("figures/forge_fmi_58_32.png")"""),
("md", """## Orientations: the 2024 reference DFN

The FMI file has no orientations, so they come from the four natural sets of the FORGE reference DFN (GDR 1646). A vertical hole under-samples steep fractures; the Terzaghi correction P32 = P10 / E[|cos θ|] turns the count along 58-32 into fracture area per rock volume."""),
("code", """poles = pd.read_csv("data/natural_fracture_poles.csv")
n = ft.pole(poles.trend, poles.plunge); A = np.pi * poles.radius_m**2
p32, mcos = ft.terzaghi_p32(st["p10_per_m"], n, A)
rows = []
for s, g in poles.groupby("set"):
    nn = ft.pole(g.trend, g.plunge); w = np.pi * g.radius_m**2
    T = (nn * w.values[:, None]).T @ nn / w.sum(); ev, vec = np.linalg.eigh(T); m = vec[:, -1] * np.sign(-vec[2, -1] or 1)
    tr, pl = np.degrees(np.arctan2(m[0], m[1])) % 360, np.degrees(np.arcsin(abs(m[2])))
    es = E["natural_sets"][s]
    rows.append({"set": s, "fractures": len(g), "area share": round(w.sum() / A.sum(), 3), "pole trend/plunge (°)": f"{tr:.0f} / {pl:.0f}",
                 "engine": f"{es['trend_deg']:.0f} / {es['plunge_deg']:.0f}", "median radius (m)": round(g.radius_m.median(), 1)})
    assert abs(w.sum() / A.sum() - es["area_share"]) < 1e-3
display(pd.DataFrame(rows))
member = E["members"][0]
print(f"Terzaghi: E[|cos|] = {mcos:.3f}  ->  P32 = {p32:.2f} m²/m³ (P10 {st['p10_per_m']:.2f} /m)")
fig = plt.figure(figsize=(5.2, 5.2)); ax = fig.add_subplot(projection="polar")
cols = dict(zip(sorted(poles.set.unique()), [GRANITE, BLUE, GOLD, CHARCOAL]))
for s, g in poles.groupby("set"):
    sub = g.sample(min(len(g), 1500), random_state=0)
    r = np.sqrt(2) * np.sin(np.radians(90 - sub.plunge) / 2)                       # Lambert equal area, lower hemisphere
    ax.scatter(np.radians(sub.trend), r, s=2, color=cols[s], alpha=0.35, label=s)
for az in (25, 205):
    ax.plot([np.radians(az)] * 2, [0, 1], color="k", lw=1.2)
ax.set_theta_zero_location("N"); ax.set_theta_direction(-1); ax.set_rticks([]); ax.set_ylim(0, 1)
ax.set_title("Poles of the natural sets (lower hemisphere)\\nblack line: SHmax N25E", pad=14); ax.legend(loc="lower left", bbox_to_anchor=(-0.25, -0.22), fontsize=7, markerscale=4)
fig.savefig("figures/forge_fracture_poles.png")"""),
("md", """## Taken at face value, the FMI apertures fail the circulation test

If the FMI hydraulic apertures were the in-situ apertures, the Oda tensor of this network would make the granitoid about as permeable as gravel. The circulation test says otherwise: in August 2024 it took about 21 MPa between the wells to move 26 kg/s."""),
("code", """ap = fmi.fvah_mm[ok].values * 1e-3
k_face = ft.oda_homogeneous(p32, n, A, ap)
pc = E["prior_check"]["FMI and GDR 1646 apertures as published"]
print("Oda k with FMI apertures (east, north, vertical):", np.array2string(k_face, precision=2), "m²")
print(f"engine, 35 m cells, same apertures: median {np.mean(pc['k_natural_median_m2']):.2e} m²")
assert 0.3 < np.mean(k_face) / np.mean(pc["k_natural_median_m2"]) < 3
print(f"inter-well impedance: model {pc['impedance_model_mpa_per_kg_s']:.3f} vs measured {pc['impedance_measured_mpa_per_kg_s']:.2f} MPa per kg/s "
      f"({pc['impedance_measured_mpa_per_kg_s'] / pc['impedance_model_mpa_per_kg_s']:.0f} × too easy)")"""),
("md", """## The wells and the stimulated network

The trajectories (GDR 1646) are checked against the well table of the extended-circulation report (GDR 1683): well heads, kick-off, tangent azimuth, total depth and true vertical depth at the toe. Both wells start on the pad the 2021 survey lists as "16A-32"; "78B-32" is a different well about 1.3 km away."""),
("code", """wh = E["wellheads"]
tab = []
for w in ("16A(78)-32", "16B(78)-32"):
    d = wh[w]
    tab.append({"well": w, "TVD at report TD (ft): trajectory / report": f"{d['tvd_at_report_md_ft']:.0f} / {d['report_tvd_toe_ft']:.0f}",
                "tangent azimuth (°)": f"{d['tangent_azimuth_deg']:.1f} / {d['report_azimuth_deg']}", "inclination (°)": round(d["tangent_inclination_deg"], 1),
                "kick-off (ft)": f"{d['kick_off_ft']:.0f} / {d['report_kop_ft']}"})
    assert abs(d["tvd_at_report_md_ft"] - d["report_tvd_toe_ft"]) < 50 and abs(d["tangent_azimuth_deg"] - d["report_azimuth_deg"]) < 6
display(pd.DataFrame(tab))
print(f"16B head: trajectory vs report {wh['16B_head_traj_vs_report_m']:.1f} m; 16A head {wh['16A_head_traj_vs_report_m']:.1f} m; "
      f"open intervals {wh['open_interval_separation_m']['min']:.0f}–{wh['open_interval_separation_m']['max']:.0f} m apart (median {wh['open_interval_separation_m']['median']:.0f} m)")
tr = pd.read_csv("data/trajectories_16A_16B.csv"); sd = pd.read_csv("data/stimulated_dfn.csv"); wl = pd.read_csv("data/wells.csv").set_index("well")
a = np.radians(105); ux, uy = np.sin(a), np.cos(a)
E0, N0 = 334640.0, 4263443.0
fig, ax = plt.subplots(1, 2, figsize=(12, 4.6))
for w, g in tr.groupby("well"):
    s_ = (g.easting - E0) * ux + (g.northing - N0) * uy
    c = BLUE if w.startswith("16A") else GOLD
    ax[0].plot(g.easting - E0, g.northing - N0, color=c, lw=2, label=w); ax[1].plot(s_, g.elev_m, color=c, lw=2, label=w)
sn = ft.pole(sd.trend, sd.plunge)
for _, r in sd.iterrows():
    e = ((r.easting - E0) * ux + (r.northing - N0) * uy)
    ax[0].plot(r.easting - E0, r.northing - N0, "o", ms=max(2, r.radius_m / 40), mfc="none", color=GRANITE, alpha=0.5)
    ax[1].plot(e, r.elev_m, "o", ms=max(2, r.radius_m / 40), mfc="none", color=GRANITE, alpha=0.5)
ax[0].plot(wl.loc["58-32"].easting - E0, wl.loc["58-32"].northing - N0, "^", color=CHARCOAL, label="58-32")
ax[0].set_aspect("equal"); ax[0].set_xlabel("east of the 16A pad (m)"); ax[0].set_ylabel("north (m)"); ax[0].legend(fontsize=8); ax[0].set_title("Plan: wells and stimulated fractures (circles ∝ radius)")
ax[1].set_xlabel("distance along azimuth 105° (m)"); ax[1].set_ylabel("elevation (m a.s.l.)"); ax[1].set_title("Section along the wells")
fig.savefig("figures/forge_wells_stimulated_dfn.png")"""),
("md", """## The ensemble

Four inputs are uncertain. Each member samples them (Latin hypercube) and then calibrates one number, the factor λ on the stimulated apertures, so that the model's injection pressure after 20 days at 10 bpm matches the August 2024 test.

| Input | Distribution | Why |
|---|---|---|
| P10 of natural fractures | log-normal, median = the 58-32 count, P10–P90 ×/÷ 1.35 | one 40 m log stands for the whole reservoir |
| Natural aperture factor (in situ / FMI) | log-uniform 0.0003–0.003 | FMI apertures are measured at the borehole wall; the test rules out values near 1 |
| Rotation of the natural sets | triangular −15°, 0, +15° | SHmax N10E–N40E around N25E (GDR 1222) |
| Spread of the stimulated apertures | uniform 0–1 (log-normal σ, fracture by fracture) | which stimulated fractures carry the flow |

P10 is the 10th percentile of the members (the low case), P90 the 90th."""),
("code", """inp = ens["inputs"]
labels = {"p10_per_m": ("natural P10 (1/m)", "{:.2f}"), "p32_per_m": ("natural P32 (m²/m³)", "{:.1f}"),
          "bg_aperture_factor": ("natural aperture factor", "{:.5f}"), "k_natural_median_m2": ("natural-network k (m²)", "{:.1e}"),
          "rotation_deg": ("rotation of the sets (°)", "{:.1f}"), "stim_aperture_sigma": ("stimulated aperture spread σ", "{:.2f}"),
          "stim_aperture_factor_calibrated": ("calibrated stimulated aperture factor λ", "{:.3f}")}
display(pd.DataFrame([{"input": l, "P50 (P10–P90)": pct(inp[k], f)} for k, (l, f) in labels.items()]))
m0 = E["median_member"]
print(f"median member: λ = {m0['calibration']['stim_aperture_factor']:.3f} after {m0['calibration']['iterations']} runs; "
      f"Δp target {m0['calibration']['dp_target_pa'] / 1e6:.1f} MPa")
diag = E["members"][0]["model"]
print(f"Oda off-diagonal terms (dropped by the TPFA solver): up to {diag['off_diagonal_max_natural']:.2f} of the diagonal for the natural network, "
      f"90th percentile {diag['off_diagonal_p90_stimulated']:.2f} for the stimulated one")"""),
("md", """## Published numbers

The numbers quoted in the README and on the case page. The notebook stops if they change."""),
("code", """published = PUBLISHED_NB2
now = {"p10_per_m": st["p10_per_m"], "aperture_mm_P50": st["aperture_mm_P50"], "p32_per_m": p32,
       "impedance_ratio": pc["impedance_measured_mpa_per_kg_s"] / pc["impedance_model_mpa_per_kg_s"],
       "lambda_P50": inp["stim_aperture_factor_calibrated"]["P50"], "lambda_P10": inp["stim_aperture_factor_calibrated"]["P10"],
       "lambda_P90": inp["stim_aperture_factor_calibrated"]["P90"]}
for k, v in published.items():
    assert abs(now[k] - v) <= 0.02 * abs(v) + 1e-3, (k, now[k], v)
pathlib.Path("results/nb2_fractured_granite.json").write_text(json.dumps({"fmi": st, "terzaghi_mean_abs_cos": mcos, "p32_per_m": p32,
    "oda_k_fmi_apertures_m2": k_face.tolist(), "published": now}, indent=1))
print("all published numbers reproduced")"""),
("md", """## What this gives the Reservoir Lab, and its limits

* The 58-32 image log gives **3.65 fractures per metre** along the hole; with the reference-DFN orientations that is about **11 m² of fracture per m³** of granitoid.
* Taken as in-situ hydraulic apertures, the FMI apertures would make the well pair about **70 times** easier to circulate than the August 2024 test shows. In-situ apertures are much smaller than those seen at the borehole wall.
* The calibrated ensemble needs the stimulated fractures at about **an eighth** of the apertures assumed in the 2024 DFN (see the table). The rest of the ensemble spread comes from density, orientation and which stimulated fractures carry the flow.

**Limits.** Equivalent continuum: one permeability tensor per 35 m cell; the solver keeps its diagonal (off-diagonal terms are reported above). Oda's tensor assumes the fractures are connected, which holds for this dense network. Apertures do not change with pressure or temperature in the model, although the test injected near the minimum horizontal stress. Heat moves between water and rock in the same cell at once; at 0.28 m mean fracture spacing the rock blocks equilibrate in hours, so this holds for the natural network but may overstate heat sweep if flow is channelled into a few fractures.

*References:* Blochowicz, A. (2021). Utah FORGE: Well 58-32 FMI Log Fracture Results. GDR 1299 · Finnila, A. and Jones, C. (2024). Utah FORGE: 2024 Discrete Fracture Network Model Data. GDR 1646, DOI 10.15121/2440870 · Finnila, A. and Podgorney, R. (2020). Utah FORGE: Discrete Fracture Network (DFN) Data. GDR 1222 · McLennan, J., England, K. and Swearingen, L. (2024). Extended Circulation Test Data. GDR 1683, DOI 10.15121/2475065 · Oda, M. (1985). Permeability tensor for discontinuous rock masses. Géotechnique 35(4) · Terzaghi, R. (1965). Sources of error in joint surveys. Géotechnique 15(3)."""),
])

nb3 = nb([
("md", """# 3 · A well pair over 30 years: what 16A(78)-32 / 16B(78)-32 could deliver

**KAI-GeoEnergy · KAI Reservoir Lab · Utah FORGE, Milford, Utah (USA)**

**Question.** If the FORGE well pair circulated water for 30 years at 10–80 kg/s, what would it produce: temperature, thermal breakthrough, heat power, pressure, and how far would the rock cool? With a P10–P90 for every number, and checked first against the 2024 circulation tests.

**Data.** The extended circulation test of 8 August – 5 September 2024 (GDR 1683, DOI [10.15121/2475065](https://doi.org/10.15121/2475065)): 30-second wellhead pressures, rates and temperature, the field calibration of the flow meters and the manual temperature checks; the 9-hour circulation test of 27 April 2024 (GDR 1611, DOI [10.15121/2371032](https://doi.org/10.15121/2371032)). The fractured-granite ensemble of notebook 2 and the temperature model of notebook 1. *Credit: Utah FORGE, U.S. Department of Energy, via the Geothermal Data Repository (OpenEI), CC BY 4.0.*

**Model.** KAI Reservoir Lab, two-point-flux flow and heat on a 1,050 × 630 × 630 m block of 35 m cells around the open intervals, rotated to the wells' azimuth (105°); water properties follow temperature; heat advection is flux-limited (TVD, van Leer); tight granitoid beyond the block (closed sides; water lost only into storage). Initial temperature and pressure from the FORGE 3-D model (notebook 1). The wells are open over their stimulated intervals (16A from 9,270 ft MD, 16B from 9,240 ft MD, to total depth).

**Labels.** Every model number here is **simulated**; the forecasts are not field data. Breakthrough is the time at which the produced temperature has fallen by 5 % of (initial − reinjection) temperature; reinjection at 60 °C. P10 is the 10th percentile of the members (the low case), P90 the 90th."""),
("code", SETUP3),
("md", """## The 2024 circulation tests

Daily medians of the 30-second data. Produced mass is the calibrated separator outflow plus the 19.6 % flash fraction (as in the report); the in-line temperature reads low, so the manual temperature-gun offset is added."""),
("code", """daily = pd.read_csv("data/circulation_2024_aug_daily.csv", index_col=0)
S = json.loads(pathlib.Path("data/circulation_2024_summary.json").read_text())
T = E["tests"]["august_2024"]
for k in ("injection_kg_s", "produced_kg_s", "recovery", "whp_16A_mpa", "whp_16B_mpa", "T_16B_wellhead_c"):
    assert abs(S[k] - T[k]) < 1e-5 * max(1, abs(T[k])), k
win = daily.loc[14:25]
assert abs(win.inj_bpm.median() * ft.BBL_L / 60 * float(ft.water_density(25)) / 1000 / S["injection_kg_s"] - 1) < 0.01
print(f"steady 10 bpm (days 14–26): {S['injection_kg_s']:.1f} kg/s in, {S['produced_kg_s']:.1f} kg/s out (recovery {S['recovery']:.0%}); "
      f"wellhead pressure 16A {S['whp_16A_mpa']:.1f} MPa, 16B {S['whp_16B_mpa']:.2f} MPa; produced {S['T_16B_wellhead_c']:.1f} °C at the wellhead")
mb = E["members"][0]["measured_bhp"]
print(f"at the top open cell: injector {mb['injector_bhp_pa'] / 1e6:.1f} MPa (cold column, {mb['friction_mpa'] * 1:.1f} MPa friction), producer {mb['producer_bhp_pa'] / 1e6:.1f} MPa")"""),
("md", """## Calibration and validation

Each member is calibrated on one number: the injector bottom-hole pressure after 20 days at 10 bpm. It is then run through the test as it happened (measured daily rates into 16A, 16B at its measured pressure, water and rock compressible) and through the April test. Recovery, produced rate and temperature were **not** fitted."""),
("code", """V = ens["validation"]
aug, apr = V["august_2024"], V["april_2024"]
rows = [
    {"quantity": "injector bottom-hole pressure (MPa)", "measured": round(aug["measured_injector_bhp_mpa"]["P50"], 1), "model P50 (P10–P90)": pct(aug["injector_bhp_mpa"]), "fitted": "yes (steady run)"},
    {"quantity": "produced rate (kg/s)", "measured": round(T["produced_kg_s"], 1), "model P50 (P10–P90)": pct(aug["produced_kg_s"]), "fitted": "no"},
    {"quantity": "recovery (out / in)", "measured": round(T["recovery"], 3), "model P50 (P10–P90)": pct(aug["recovery"], "{:.3f}"), "fitted": "no"},
    {"quantity": "produced temperature (°C): model bottom hole / measured wellhead", "measured": round(T["T_16B_wellhead_c"], 1), "model P50 (P10–P90)": pct(aug["produced_T_bottomhole_c"]), "fitted": "no"},
    {"quantity": "… after an estimated wellbore cooling (Ramey)", "measured": round(T["T_16B_wellhead_c"], 1), "model P50 (P10–P90)": pct({k: (aug["produced_T_bottomhole_c"][k] - aug["wellbore_cooling_estimate_c"]["P50"]) if not isinstance(aug["produced_T_bottomhole_c"][k], str) else 0 for k in ("P10", "P50", "P90")}), "fitted": "no"},
    {"quantity": "April: injector wellhead pressure at 13.9 bpm (MPa)", "measured": round(E["tests"]["april_2024"]["final_whp_mpa"], 1), "model P50 (P10–P90)": pct(apr["injector_whp_equivalent_mpa"]), "fitted": "no"},
    {"quantity": "April: produced rate at the end (bpm)", "measured": 8.2, "model P50 (P10–P90)": pct(apr["produced_bpm_end"]), "fitted": "no"},
]
display(pd.DataFrame(rows))
s = E["median_member"]["validation"]["august_2024"]["series"]
fig, ax = plt.subplots(1, 3, figsize=(13, 3.6))
dd = daily.index.values + 0.5
ax[0].plot(dd, daily.whp_16A_psi * ft.PSI / 1e6, "o", color=CHARCOAL, ms=4, label="16A wellhead (measured)")
ax[0].plot(s["t_days"], np.array(s["injector_bhp_mpa"]) - (mb["injector_bhp_pa"] / 1e6 - S["whp_16A_mpa"]), color=BLUE, label="model, as wellhead")
ax[0].set_xlabel("days from 8 Aug 2024"); ax[0].set_ylabel("MPa"); ax[0].set_title("Injection pressure"); ax[0].legend(fontsize=8)
prod_d = daily.liquid_gpm_cal * ft.GAL_L / 60 * float(ft.water_density((202.2 - 32) / 1.8)) / 1000 / (1 - ft.STEAM_FRACTION)
ax[1].plot(dd, prod_d, "o", color=CHARCOAL, ms=4, label="16B, calibrated"); ax[1].plot(s["t_days"], s["produced_kg_s"], color=GOLD, label="model")
ax[1].set_xlabel("days"); ax[1].set_ylabel("kg/s"); ax[1].set_title("Produced mass rate"); ax[1].legend(fontsize=8)
ax[2].plot(dd, (daily.T_16B_raw_f - 32) / 1.8 + S["manual_offset_c"], "o", color=CHARCOAL, ms=4, label="16B wellhead (corrected)")
ax[2].plot(s["t_days"], s["produced_T_c"], color=GRANITE, label="model, bottom hole")
ax[2].set_xlabel("days"); ax[2].set_ylabel("°C"); ax[2].set_title("Produced temperature"); ax[2].legend(fontsize=8)
fig.suptitle("Median member against the August 2024 test (simulated vs measured)", y=1.03, fontweight="bold")
fig.savefig("figures/forge_validation_2024.png")"""),
("md", """**Reading the misfit.** The injection pressure is fitted at the end of the test, so its agreement there is not a test. Its build-up is: the model reaches the measured pressure more slowly (2–5 MPa low between days 4 and 15), so its storage is too large or its early permeability too high; in the field the pressure rose to near the minimum horizontal stress within a day of the step to 10 bpm. The recovery is a test: the model loses water only into the storage of the fractured rock (fracture compressibility from the 2024 DFN), and that alone gives a recovery close to the measured one. The produced temperature is not reproduced: the model's bottom-hole temperature is well above the corrected wellhead temperature, and a simple wellbore heat-loss estimate explains less than half of the gap. Either the fluid comes from cooler (shallower) paths than the model's, or the FORGE temperature model is too hot at 16B, or the wellbore loses more heat than the estimate. The April injection pressure is not reproduced either: the model needs about 8 MPa less than was measured at 13.9 bpm, although its produced rate at the end (7.7 bpm, P10–P90 3.6–9.0) brackets the measured 8.2 bpm. In April the stimulated fractures had just been drained during the plug drill-out and were refilling (the report says so); the model starts from undisturbed pressure and its fracture apertures do not depend on pressure."""),
("md", """## Thirty years at 10–80 kg/s

Injection equals production; 60 °C reinjection. A rate is **pressure-feasible** in a member when the injector stays below the minimum horizontal stress (17 kPa/m, GDR 1222) and the producer stays at least 1 MPa above the saturation pressure. The model does not create new fractures, so above about twice the 2024 rate the thermal results describe flow paths that the present stimulation cannot drive: they are what the rock could give if circulation at that rate were possible."""),
("code", """R = ens["rates"]
rows = []
for q, r in R.items():
    sc = r["scalars"]
    rows.append({"rate (kg/s)": int(q), "produced T, year 1 (°C)": pct(sc["T_prod_initial_c"]), "year 10 (°C)": pct(sc["T_prod_10y_c"]),
                 "year 30 (°C)": pct(sc["T_prod_end_c"]), "breakthrough (years)": pct(sc["breakthrough_years"], "{:.2f}"),
                 "heat, year 1 (MWth)": pct(sc["power_initial_mw"]), "heat, year 30 (MWth)": pct(sc["power_end_mw"]),
                 "injector BHP max / Shmin": pct(sc["injector_bhp_over_shmin"], "{:.2f}"), "producer BHP min (MPa)": pct(sc["producer_bhp_min_mpa"]),
                 "cooled > 10 °C at 30 y (Mm³)": pct(sc["cooled_volume_30y_mm3"]), "feasible members": f"{r['feasible_members']}/{ens['members'] - ens['failed']}"})
tab = pd.DataFrame(rows); display(tab)
tab.to_csv("results/nb3_forecast_table.csv", index=False)
yrs = np.arange(1, 31)
fig, ax = plt.subplots(1, 2, figsize=(12, 4.2))
cmap = plt.get_cmap("cividis")
for i, (q, r) in enumerate(R.items()):
    c = cmap(i / (len(R) - 1)); s_ = r["series"]["T_prod_yearly_c"]
    ax[0].fill_between(yrs, s_["P10"], s_["P90"], color=c, alpha=0.25); ax[0].plot(yrs, s_["P50"], color=c, lw=2, label=f"{q} kg/s")
    p_ = r["series"]["power_yearly_mw"]
    ax[1].fill_between(yrs, p_["P10"], p_["P90"], color=c, alpha=0.25); ax[1].plot(yrs, p_["P50"], color=c, lw=2, label=f"{q} kg/s" + ("" if r["feasible_members"] else " (not pressure-feasible)"))
ax[0].set_xlabel("year"); ax[0].set_ylabel("°C"); ax[0].set_title("Produced temperature, P10–P90 (simulated)"); ax[0].legend(fontsize=8)
ax[1].set_xlabel("year"); ax[1].set_ylabel("MWth"); ax[1].set_title("Heat power above 60 °C, P10–P90 (simulated)"); ax[1].legend(fontsize=8)
fig.savefig("figures/forge_30_years.png")"""),
("md", """## How much the breakthrough time depends on the grid

Breakthrough is quoted as the grid-converged value with its discretisation error. The median member is rebuilt and recalibrated at 52.5, 35 and 23.3 m cells; Richardson extrapolation gives the converged value and the grid convergence index (GCI) its error. The solver itself is checked the same way on a doublet with an exact answer and against open-DARTS (second table, from the KAI engine's validation suite).

Here the finer grids give *earlier* breakthrough, the opposite of the doublet: finer cells resolve narrower fracture channels, so the change is mostly in how the fractures map to cells, not numerical dispersion. The observed order is above the scheme's formal order, so the coarsest grid is outside the asymptotic range and the GCI should be read as a lower bound. The 35 m ensemble overestimates breakthrough by about 25 % at 10 kg/s and 40 % at 40 kg/s."""),
("code", """G = E["grid_convergence"]
rows = []
for q, g in G["rates"].items():
    b = g["breakthrough_years"]
    rows.append({"rate (kg/s)": int(q), **{f"{r['cell_m']:.1f} m": round(r["breakthrough_years"], 3) for r in g["runs"]},
                 "converged ± GCI (years)": f"{b['converged']:.3f} ± {b['error_abs']:.3f}", "observed order": None if b["order"] is None else round(b["order"], 2),
                 "35 m vs converged": f"{g['runs'][1]['breakthrough_years'] / b['converged'] - 1:+.1%}"})
display(pd.DataFrame(rows))
C = E["solver_convergence"]
rows = []
for part, lab in (("dipole", "doublet with exact answer"), ("closed", "closed box")):
    for k, d in C[part]["schemes"].items():
        rr = d["richardson"]
        rows.append({"case": lab, "scheme": k, **{f"{x['cell_m']:.0f} m": round(x["breakthrough_years"], 3) for x in d["runs"]},
                     "converged ± GCI": f"{rr['converged']:.3f} ± {rr['error_abs']:.3f}"})
display(pd.DataFrame(rows)); print(f"exact: {C['dipole']['exact_years']:.3f} years")"""),
("md", """## The cooling front

Temperature on a vertical section along the wells, median member at 40 kg/s, after 1, 10 and 30 years (simulated)."""),
("code", """F = np.load("results/forge_pair_fields.npz")
nz_, ny_, nx_ = F["shape"]; h = float(F["cell"])
def sec(Tf):
    Tf = Tf.reshape(nz_, ny_, nx_)
    kA = np.unravel_index(F["well_A"], (nz_, ny_, nx_))
    j = int(np.median(kA[1]))
    return Tf[:, j, :], j
fig, ax = plt.subplots(1, 3, figsize=(14, 3.8), sharey=True)
for a_, key, yr in zip(ax, ("T1", "T10", "T30"), (1, 10, 30)):
    s_, j = sec(F[key])
    im = a_.imshow(s_, extent=[0, nx_ * h, float(F["z_top"]) + nz_ * h, float(F["z_top"])], cmap="inferno", vmin=60, vmax=240, aspect="auto")
    for wkey, c in (("well_A", BLUE), ("well_B", GOLD)):
        k, jj, i = np.unravel_index(F[wkey], (nz_, ny_, nx_))
        a_.plot((i + 0.5) * h, float(F["z_top"]) + (k + 0.5) * h, "s", color=c, ms=3)
    a_.set_title(f"year {yr}"); a_.set_xlabel("distance along azimuth 105° (m)")
ax[0].set_ylabel("depth below the 16A pad (m)"); fig.colorbar(im, ax=ax, label="°C", shrink=0.9)
fig.suptitle("Cooling front at 40 kg/s, median member (blue 16A injector, gold 16B producer; simulated)", y=1.02, fontweight="bold")
fig.savefig("figures/forge_cooling_front.png")
r40 = R["40"]["scalars"]
print(f"cooled by more than 10 °C at 40 kg/s: {pct(r40['cooled_volume_10y_mm3'])} Mm³ after 10 years, {pct(r40['cooled_volume_30y_mm3'])} Mm³ after 30 years; "
      f"reach from the injector {pct(r40['cooling_reach_30y_m'], '{:.0f}')} m")"""),
("md", """## Published numbers

The numbers quoted in the README and on the case page. The notebook stops if they change."""),
("code", """published = PUBLISHED_NB3
now = {}
for q in ("10", "20", "40", "80"):
    for k in ("breakthrough_years", "T_prod_end_c", "power_initial_mw", "power_end_mw"):
        for p in ("P10", "P50", "P90"):
            now[f"{q}_{k}_{p}"] = R[q]["scalars"][k][p]
now["recovery_P50"] = aug["recovery"]["P50"]; now["T_bh_P50"] = aug["produced_T_bottomhole_c"]["P50"]
for q in ("10", "40"):
    now[f"bt_converged_{q}"] = G["rates"][q]["breakthrough_years"]["converged"]; now[f"bt_gci_{q}"] = G["rates"][q]["breakthrough_years"]["error_abs"]
for k, v in published.items():
    x = now[k]
    if isinstance(v, str) or isinstance(x, str):
        assert x == v, (k, x, v)
    else:
        assert abs(x - v) <= 0.02 * abs(v) + 0.01, (k, x, v)
pathlib.Path("results/nb3_doublet_30_years.json").write_text(json.dumps({"published": now}, indent=1))
print("all published numbers reproduced")"""),
("md", """## What this says, and what it does not

SUMMARY_NB3

**Limits.** Equivalent continuum on 35 m cells (diagonal permeability); fixed apertures (no pressure or thermal opening, no new fractures), so the forecasts above about twice the 2024 rate are not pressure-feasible and are what-if numbers; local thermal equilibrium between water and rock in a cell; no wellbore model (bottom-hole temperatures; wellbore cooling only estimated); single-phase water; the near-well flow is represented by Peaceman well indices on 35 m cells (near-well upscaling is phase 4). The calibration uses one test and one number.

*References:* McLennan, J., England, K. and Swearingen, L. (2024). Utah FORGE: Wells 16A(78)-32 and 16B(78)-32 Extended Circulation Test Data. GDR 1683, DOI 10.15121/2475065 · Utah FORGE (2024). Stimulation Pressure and Circulation Data, April 2024. GDR 1611, DOI 10.15121/2371032 · Finnila, A. and Jones, C. (2024). 2024 Discrete Fracture Network Model Data. GDR 1646 · Ramey, H. J. (1962). Wellbore heat transmission. J. Petrol. Technol. 14(4) · Roache, P. J. (1994). Perspective: a method for uniform reporting of grid refinement studies. J. Fluids Eng. 116."""),
])


if __name__ == "__main__":
    import json
    import pathlib
    import sys

    nbf.write(nb1, "01_structure_and_temperature.ipynb")
    print("wrote 01_structure_and_temperature.ipynb")
    pub = json.loads(pathlib.Path("results/published_phase3.json").read_text()) if pathlib.Path("results/published_phase3.json").exists() else None
    if pub is None:
        sys.exit("results/published_phase3.json missing: run make_published.py first")
    for name, book, key in (("02_fractured_granite_ensemble.ipynb", nb2, "nb2"), ("03_doublet_30_years.ipynb", nb3, "nb3")):
        for c in book.cells:
            c.source = c.source.replace(f"PUBLISHED_{key.upper()}", json.dumps(pub[key])).replace("SUMMARY_NB3", pub.get("summary_nb3", ""))
        nbf.write(book, name)
        print("wrote", name)
