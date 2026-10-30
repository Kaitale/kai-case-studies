"""Builds the Utah FORGE phase 4 notebooks 04 and 05 (run: python make_notebooks_phase4.py, then execute them)."""
import nbformat as nbf

from make_notebooks import nb

SETUP4 = """import json, pathlib, warnings
import numpy as np, pandas as pd, matplotlib.pyplot as plt
import forge_tools as ft
warnings.filterwarnings("ignore")
plt.rcParams.update({"figure.dpi": 110, "axes.grid": False, "axes.spines.top": False, "axes.spines.right": False, "font.size": 10,
                     "axes.titleweight": "bold", "axes.titlesize": 11, "legend.frameon": False, "savefig.bbox": "tight", "savefig.facecolor": "white"})
GOLD, CHARCOAL, GRANITE, BLUE, GREY = "#c9a227", "#26292e", "#b5838d", "#2a78d6", "#8a8f98"     # KAI energy palette
pathlib.Path("results").mkdir(exist_ok=True); pathlib.Path("figures").mkdir(exist_ok=True)
E = json.loads(pathlib.Path("results/kai_engine_phase4.json").read_text())      # KAI engine run (simulated)
ens = E["ensemble"]
def pct(d, f="{:.1f}"):
    fm = lambda v: v if isinstance(v, str) else f.format(v)
    return f"{fm(d['P50'])} ({fm(d['P10'])}–{fm(d['P90'])})"
print(E["label"]); print(f"ensemble: {ens['members'] - ens['failed']}/{ens['members']} members ran, {ens['calibration_converged']} calibrated")"""

CHECK = """published = PUBLISHED
for k, v in published.items():
    x = now[k]
    if isinstance(v, str) or isinstance(x, str) or v is None or x is None:
        assert x == v, (k, x, v)
    else:
        assert abs(x - v) <= 0.02 * abs(v) + 0.01, (k, x, v)
pathlib.Path("results/RESULTFILE").write_text(json.dumps({"published": now}, indent=1))
print(f"all {len(published)} published numbers reproduced")"""

nb4 = nb([
("md", """# 4 · Checking the model, and the upscaling check

**KAI-GeoEnergy · KAI Reservoir Lab · Utah FORGE, Milford, Utah (USA)**

**Questions.**
1. Is the +24 °C produced-temperature misfit of notebook 3 in the wellbore or in the reservoir?
2. Do the 2024 tracers travel between the wells as fast as the model says?
3. With apertures that open and close with pressure, which rates can the well pair run without exceeding the minimum horizontal stress?
4. Does keeping the full fracture permeability tensor (not only its diagonal) change the answers?
5. **The upscaling check.** How much does a coarse model, the usual industry practice, change the breakthrough time against the fine model? With a P10–P90 over the ensemble.

**New data** (DOE Geothermal Data Repository, CC BY 4.0; `data/` holds only derived values, rebuilt by `rebuild_data.py`):
* **Tracers** (GDR 1701, Guo, Oliver and Shokanov 2024, DOI [10.15121/2507443](https://doi.org/10.15121/2507443)): ten nanoparticle tracers injected into 16A(78)-32 every other day from 11 August 2024, sampled at 16B(78)-32.
* **Fibre temperatures** in 16B (GDR 1721, Neubrex): distributed temperature sensing (DTS) on 4 August (before the test) and 12–16 August 2024 (during it).

The 2024 circulation tests, trajectories and fracture data are those of notebooks 2 and 3. *Credit: Utah FORGE, U.S. Department of Energy, via the Geothermal Data Repository (OpenEI), CC BY 4.0.*

**What changed in the model since notebook 3.**
* Bottom-hole pressures and the injection temperature now come from a **wellbore model**. It uses Hasan–Kabir heat loss and single-phase friction along the surveyed trajectories, with the notebook 1 temperature model as the geotherm.
* The stimulated fractures have **Barton–Bandis apertures**. Their effective normal stress is Shmin − p. The calibrated apertures are the apertures at the August 2024 pressures. The fractures can close or open up to their unloaded width; no new fractures are created.
* The forecasts are run **the way the 2024 test was**: 16A at a rate, 16B at its August bottom-hole pressure. A rate is pressure-feasible when 16A stays at or below Shmin for 30 years.
* The ensemble has two more uncertain inputs, the Barton–Bandis stiffness and maximum closure.

**Labels.** Every model number is **simulated** by the KAI Reservoir Lab engine (`results/kai_engine_phase4.json`). Data-derived numbers are recomputed here with the MIT helpers in `forge_tools.py`; the notebook stops if the engine disagrees."""),
("code", SETUP4),
("md", """## 1 · The wellbore: where the temperature misfit is

The 16B wellhead temperature (189.8 °C over days 14–26, the in-line reading corrected with the manual gun) is turned into a bottom-hole temperature with the wellbore model. The table shows the P10–P90 over rock and cement conductivity, hole size, geotherm offset (±10 °C) and the gun correction (P10–P90 of 73 checks)."""),
("code", """W = E["wellbore"]
rows = [
    {"quantity": "cooling from bottom hole to wellhead, 24.5 kg/s (°C)", "P50 (P10–P90)": pct(W["cooling_implied_c"])},
    {"quantity": "bottom-hole temperature implied by the measured wellhead (°C)", "P50 (P10–P90)": pct(W["T_bottom_implied_c"])},
    {"quantity": "producer bottom-hole pressure from 1.73 MPa at the wellhead (MPa)", "P50 (P10–P90)": pct(W["producer_bhp_mpa"], "{:.2f}")},
    {"quantity": "injector bottom-hole pressure from 19.6 MPa at the wellhead (MPa)", "P50 (P10–P90)": pct(W["injector_bhp_mpa"], "{:.2f}")},
    {"quantity": "injector bottom-hole temperature from 25 °C pit water (°C)", "P50 (P10–P90)": pct(W["injector_T_bottom_c"])},
]
display(pd.DataFrame(rows))
V = ens["validation"]
for kind in ("constant_apertures", "barton_bandis"):
    print(f"{kind.replace('_', ' ')}: model bottom-hole {pct(V[kind]['produced_T_bottomhole_c'])} °C; "
          f"misfit against the implied bottom-hole value {pct(V[kind]['T_misfit_bottomhole_c'], '{:+.1f}')} °C")"""),
("md", """### The fibre temperatures (DTS)

The DTS files are checked before they are used. During the test the profile has a step of 80–90 °C between 2,800 and 3,200 ft. Above the step, readings drift by up to 66 °C in four days. Below it, the profile is smooth (spread over a day about 0.2 °C). So only the shape of the deep section can be compared, not its level."""),
("code", """dts = pd.read_csv("data/dts_16B_2024.csv"); deep = json.loads(pathlib.Path("data/dts_16B_2024_deep.json").read_text())
D = E["dts"]
assert abs(deep["slope_c_per_km_md"] - D["deep"]["slope_c_per_km_md"]) < 1e-3 and abs(deep["T_bottom_c"] - D["deep"]["T_bottom_c"]) < 1e-3
jump = np.abs(np.diff(dts.flowing_days_6p5_7p7_c.values)); k = int(np.nanargmax(jump))
assert dts.md_ft[k] == D["step_md_ft"][0]
dT_dts = deep["T_bottom_c"] - deep["T_top_c"]
print(f"step: {dts.md_ft[k]:.0f}–{dts.md_ft[k + 1] + 200:.0f} ft, {jump[k]:.0f} °C; deep section 3,200–9,240 ft: +{dT_dts:.1f} °C "
      f"({deep['slope_c_per_km_md']:.1f} °C per km of hole)")
print(f"wellbore model over the same section, day 7: +{pct(W['dts_section_delta_model_c'])} °C; "
      f"no completion resistance and λ = 3.2 W/m/K (an upper bound): +{pct(W['dts_section_delta_upper_bound_c'])} °C")
fig, ax = plt.subplots(1, 2, figsize=(12, 4.6))
pr = W["profile_p50"]
ax[0].plot(pr["T_e"], np.array(pr["md_m"]) / ft.FT, color=GREY, label="undisturbed rock (geotherm)")
ax[0].plot(pr["T_c"], np.array(pr["md_m"]) / ft.FT, color=GOLD, lw=2, label="flowing water, model (P50)")
ax[0].plot(dts.flowing_days_6p5_7p7_c, dts.md_ft + 100, ".", color=CHARCOAL, ms=4, label="DTS, days 6.5–7.7 (raw)")
ax[0].plot(dts.static_4aug_c, dts.md_ft + 100, ".", color=BLUE, ms=3, alpha=0.6, label="DTS, 4 Aug (after the clean-out)")
ax[0].plot(E["tests"]["T_16B_wellhead_c"] if "tests" in E else 189.8, 0, "s", color=GRANITE, label="wellhead, measured")
ax[0].invert_yaxis(); ax[0].set_xlabel("°C"); ax[0].set_ylabel("measured depth (ft)"); ax[0].set_title("16B: model and DTS"); ax[0].legend(fontsize=7.5)
labels = ["DTS", "model (P50)", "upper bound"]
vals = [dT_dts, W["dts_section_delta_model_c"]["P50"], W["dts_section_delta_upper_bound_c"]["P50"]]
ax[1].bar(labels, vals, color=[CHARCOAL, GOLD, GREY])
ax[1].set_ylabel("°C"); ax[1].set_title("Warming from 3,200 to 9,240 ft MD")
fig.savefig("figures/forge_wellbore_16B.png")"""),
("md", """**Reading it.** Between 3,200 and 9,240 ft, the DTS warms 2.6 times as much as the energy-balance upper bound allows. That bound has no completion resistance and the highest rock conductivity. A fluid flowing at 24.5 kg/s cannot lose that much heat to rock that is at most at the geotherm. The deep gradient is therefore not the fluid's. A depth-proportional error is what uncorrected differential attenuation in a Raman DTS looks like. With the step and the drift, we do not use the DTS absolute values. We state this as a limit of the data, not as a model fit. The 4 August profile was taken right after the clean-out of 1–4 August, so it is not the undisturbed geotherm either.

The wellbore model explains about 13 °C of the 24 °C misfit of notebook 3. **About 11 °C is left in the reservoir model** (see *what this says* below)."""),
("md", """## 2 · Tracers: travel time between the wells

Tracers 1–3 arrived after 34, 64 and 16 hours, while the fractures were still filling (the report's reading). From tracer 4 on, every first detection was at the first sample after injection, 10.5 hours later; for tracer 4 the sample 6 hours earlier was clean. The model is a 30-minute pulse in the steady August flow field. Its mobile porosity is the fracture porosity only, because nanoparticles do not enter the granite matrix."""),
("code", """tc = pd.read_csv("data/tracers_2024_circulation.csv")
meas = []
for n, g in tc.groupby("tracer"):
    d = ft.tracer_detection(g.sample_t_h.values, g.injected_t_h.iloc[0], g.c_ppb.values)
    eng = next(x for x in E["tracers_measured"]["summary"] if x["tracer"] == n)
    assert abs(d["first_positive_h"] - eng["first_positive_h"]) < 1e-3 and abs(d["peak_h"] - eng["peak_h"]) < 1e-3
    assert abs(d["first_positive_h"] - eng["report_first_detection_h"]) < 0.3        # agrees with the report's Table 7
    meas.append({"tracer": n, **d})
meas = pd.DataFrame(meas); display(meas.round(1))
late = meas[meas.tracer >= 4]
Tm = ens["tracer"]
print(f"measured, tracers 4–10: first detection {late.first_positive_h.min():.1f}–{late.first_positive_h.max():.1f} h after injection "
      f"(tracer 4: between {meas.loc[meas.tracer == 4, 'last_clean_h'].item():.1f} and {meas.loc[meas.tracer == 4, 'first_positive_h'].item():.1f} h); "
      f"peak samples {late.peak_h.min():.0f}–{late.peak_h.max():.0f} h")
print(f"model (fracture porosity): 5 % of the tracer back after {pct(Tm['recovery_5pct_h'], '{:.2f}')} h; peak {pct(Tm['peak_time_h'], '{:.2f}')} h; "
      f"mean residence {pct(Tm['mean_residence_h'], '{:.1f}')} h; swept fracture pore volume {pct(Tm['pore_volume_m3'], '{:.0f}')} m³")
fac = {"lo": 4.5 / Tm["recovery_5pct_h"]["P50"], "hi": 10.5 / Tm["recovery_5pct_h"]["P50"]}
print(f"to arrive when measured, the model's transport porosity would have to be {fac['lo']:.0f}–{fac['hi']:.0f} × its fracture porosity")
c = E["median_member"]["tracer"]["curve"]
fig, ax = plt.subplots(figsize=(8, 3.6))
ax.plot(c["t_h"], c["c_rel"], color=GOLD, lw=2, label="model, median member (relative concentration)")
r4 = meas[meas.tracer == 4].iloc[0]
ax.plot([r4.last_clean_h, r4.first_positive_h], [1.08, 1.08], color=CHARCOAL, lw=4, label="tracer 4: first detected between these samples")
ax.plot(late.first_positive_h, 0.95 + 0.02 * (late.tracer - 4), "v", color=GRANITE, ms=6, label="tracers 4–10: present in the first sample (an upper bound)")
ax.set_xscale("log"); ax.set_xlim(0.01, 100); ax.set_xlabel("hours after injection"); ax.set_yticks([])
ax.set_title("Tracer travel time, 16A → 16B (model simulated)"); ax.legend(fontsize=8, loc="center left")
fig.savefig("figures/forge_tracers.png")"""),
("md", """**Reading it.** In the model the water crosses in minutes; in the field the first tracer took at least 4.5 hours. The model's flow paths have too little pore space. That is expected for the way the apertures were set: one factor on the GDR 1646 apertures was fitted to the pressure, and the same factor sets the porosity. Hydraulic apertures from pressure are known to be much smaller than the apertures that hold the water (the transport apertures). The tracers put that ratio at tens. It hardly changes the heat results: with water and rock at the same temperature in a cell, the thermal front moves with the rock's heat capacity, not with the fracture volume. But it is a misfit, and it is reported as one."""),
("md", """## 3 · Pressure-dependent apertures: which rates are feasible

For each rate, the table gives the highest injector bottom-hole pressure over 30 years. It is compared with Shmin at the injector's top completion (17 kPa/m, GDR 1222). The two columns use the same calibrated network: apertures fixed, or apertures following Barton–Bandis."""),
("code", """R = ens["rates"]
rows = []
for q in [k for k in R["barton_bandis"] if k != "max_feasible_rate_kg_s"]:
    a, b_ = R["constant_apertures"][q], R["barton_bandis"][q]
    n = ens["members"] - ens["failed"]
    rows.append({"rate (kg/s)": int(q), "max injector BHP, fixed apertures (MPa)": pct(a["injector_bhp_max_mpa"]), "feasible (fixed)": f"{a['feasible_members']}/{n}",
                 "max injector BHP, Barton–Bandis (MPa)": pct(b_["injector_bhp_max_mpa"]), "feasible (B–B)": f"{b_['feasible_members']}/{n}",
                 "k multiplier at 16A (B–B)": pct(b_["k_multiplier_injector"], "{:.2f}"), "T year 30 (°C, B–B)": pct(b_["T_prod_end_c"]),
                 "breakthrough (years, B–B, 35 m)": pct(b_["breakthrough_years"], "{:.2f}")})
display(pd.DataFrame(rows))
sh = R["barton_bandis"]["10"]["shmin_injector_mpa"]
print(f"Shmin at the injector's top completion: {sh:.1f} MPa; 16B held at {R['barton_bandis']['10']['producer_bhp_mpa']:.1f} MPa")
print(f"highest pressure-feasible rate: fixed apertures {pct(R['constant_apertures']['max_feasible_rate_kg_s'])} kg/s, "
      f"Barton–Bandis {pct(R['barton_bandis']['max_feasible_rate_kg_s'])} kg/s")
qs = [int(q) for q in R["barton_bandis"] if q != "max_feasible_rate_kg_s"]
fig, ax = plt.subplots(figsize=(7, 4))
for kind, c, lab in (("constant_apertures", GREY, "fixed apertures"), ("barton_bandis", GOLD, "Barton–Bandis apertures")):
    p = [R[kind][str(q)]["injector_bhp_max_mpa"] for q in qs]
    ax.fill_between(qs, [x["P10"] for x in p], [x["P90"] for x in p], color=c, alpha=0.3); ax.plot(qs, [x["P50"] for x in p], "o-", color=c, label=lab)
ax.axhline(sh, color=CHARCOAL, ls="--", lw=1); ax.text(qs[-1], sh + 0.8, "Shmin at 16A", ha="right", fontsize=8)
ax.set_xlabel("circulation rate (kg/s)"); ax.set_ylabel("highest injector BHP in 30 years (MPa)"); ax.legend(fontsize=8)
ax.set_title("Which rates fit under Shmin (simulated, P10–P90)")
fig.savefig("figures/forge_rates_feasible.png")"""),
("md", """**Reading it.** Below the August rate, the fracture pressure is lower than in August, so the fractures close a little and the network gets tighter. At higher rates they open, but by less than the extra pressure needs. Cooling also makes the water near 16A more viscous year by year. So Barton–Bandis apertures **do not make the higher rates feasible**: the highest feasible rate stays near or below 10 kg/s. The August test itself ran 26.5 kg/s with the injector about 2.5 MPa above the recommended Shmin, which is where the field team saw signs of fracture growth. Growth is not modelled. Rates above the feasible rate stay what-if numbers."""),
("md", """## 4 · The full permeability tensor

The fractures are not aligned with the grid. In the stimulated cells the off-diagonal Oda terms are 0.3–0.4 of the diagonal. The engine now keeps them: a full-tensor finite-volume scheme, two-point flux plus cross-derivative terms. On a doublet with an exact answer it converges to the exact breakthrough (+0.7 %), while the diagonal-only scheme stays 39 % early. Here the median member is recalibrated with each scheme and grid."""),
("code", """F = E["full_tensor"]
rows = []
for r in F["runs"]:
    for q, f in r["forecast"].items():
        rows.append({"cells (m)": round(r["cell_m"], 1), "scheme": r["scheme"], "rate (kg/s)": int(q), "calibrated λ": round(r["stim_aperture_factor"], 3),
                     "breakthrough (years)": round(f["breakthrough_years"], 3), "T year 30 (°C)": round(f["T_prod_end_c"], 1),
                     "tracer 5 % back (h)": round(r["tracer"]["recovery_5pct_h"], 3)})
ft_tab = pd.DataFrame(rows); display(ft_tab)
B = E["benchmarks"]["anisotropic_doublet"]
print(f"benchmark (exact anisotropic doublet): full tensor {B['full_vs_exact']:+.1%}, diagonal {B['diagonal_vs_exact']:+.1%} (converged breakthrough)")"""),
("md", """## 5 · The upscaling check

The usual practice is a coarse model (here 70 m cells), with the fracture tensor averaged into each cell and Peaceman well indices, recalibrated on the test. The fine model has 23.3 m cells. Both use the same fractures: same seed, and natural discs of 35 m and more placed one by one. The KAI coarse model takes its transmissibilities and well indices from the fine model's well-pair solution (global plus near-well upscaling) and is **not** recalibrated. Breakthrough change = coarse / fine − 1, member by member."""),
("code", """U = E["upscaling"]
rows = []
for q, d in U["rates"].items():
    for model, lab in (("coarse_usual", "70 m, usual (Oda average + Peaceman, recalibrated)"), ("coarse_kai", "70 m, KAI (global + near-well upscaling)")):
        rows.append({"rate (kg/s)": int(q), "coarse model": lab, "fine breakthrough (years)": pct(d["fine"]["breakthrough_years"], "{:.2f}"),
                     "coarse breakthrough (years)": pct(d[model]["breakthrough_years"], "{:.2f}"),
                     "breakthrough change": pct({k: d[model]["breakthrough_change"][k] * 100 for k in ("P10", "P50", "P90")}, "{:+.0f} %"),
                     "T year 30 change (°C)": pct(d[model]["T30_change_c"], "{:+.1f}")})
display(pd.DataFrame(rows))
print(f"{U['members'] - U['failed']}/{U['members']} members; August pressure difference: target {pct(U['august_dp_target_mpa'])} MPa, "
      f"KAI coarse (not recalibrated) {pct(U['coarse_kai_august_dp_mpa'])} MPa, usual coarse before recalibration {pct(U['coarse_usual_uncalibrated_august_dp_mpa'])} MPa")
fig, ax = plt.subplots(1, 2, figsize=(11, 3.8))
for i, q in enumerate(U["rates"]):
    for j, (model, c) in enumerate((("coarse_usual", GREY), ("coarse_kai", GOLD))):
        vals = [m["rates"][q][model]["breakthrough_change"] * 100 for m in E["upscaling_members"] if m["ok"] and m["rates"][q][model]["breakthrough_change"] is not None]
        ax[0].scatter(np.full(len(vals), i * 3 + j) + np.random.default_rng(j).uniform(-0.2, 0.2, len(vals)), vals, color=c, s=18)
        vals = [m["rates"][q][model]["T30_change_c"] for m in E["upscaling_members"] if m["ok"]]
        ax[1].scatter(np.full(len(vals), i * 3 + j) + np.random.default_rng(j).uniform(-0.2, 0.2, len(vals)), vals, color=c, s=18)
for a_, lab in zip(ax, ("breakthrough change (%)", "30-year temperature change (°C)")):
    a_.axhline(0, color=CHARCOAL, lw=0.8); a_.set_ylabel(lab)
    a_.set_xticks([0, 1, 3, 4]); a_.set_xticklabels([f"{q} kg/s\\n{m}" for q in U["rates"] for m in ("usual", "KAI")], fontsize=8)
ax[0].set_title("Coarse (70 m) against fine (23.3 m)"); ax[1].set_title("Same, 30-year produced temperature")
fig.suptitle("The upscaling check, one dot per member (simulated)", y=1.03, fontweight="bold")
fig.savefig("figures/forge_upscaling.png")"""),
("md", """## How much the breakthrough time depends on the grid (Barton–Bandis forecasts)"""),
("code", """G = E["grid_convergence"]
rows = []
for q, g in G["rates"].items():
    b = g["breakthrough_years"]
    rows.append({"rate (kg/s)": int(q), **{f"{r['cell_m']:.1f} m": round(r["breakthrough_years"], 3) for r in g["runs"]},
                 "converged ± GCI (years)": f"{b['converged']:.3f} ± {b['error_abs']:.3f}", "observed order": None if b["order"] is None else round(b["order"], 2),
                 "T year 30 converged (°C)": f"{g['T_prod_end_c']['converged']:.1f} ± {g['T_prod_end_c']['error_abs']:.1f}"})
display(pd.DataFrame(rows))"""),
("md", """## Published numbers"""),
("code", """now = {}
for k in ("cooling_implied_c", "T_bottom_implied_c", "injector_bhp_mpa", "injector_T_bottom_c"):
    for p in ("P10", "P50", "P90"):
        now[f"wb_{k}_{p}"] = W[k][p]
for p in ("P10", "P50", "P90"):
    now[f"Tmisfit_bb_{p}"] = V["barton_bandis"]["T_misfit_bottomhole_c"][p]
    now[f"tracer_rec5_{p}"] = Tm["recovery_5pct_h"][p]
    for kind in ("constant_apertures", "barton_bandis"):
        now[f"maxrate_{kind}_{p}"] = R[kind]["max_feasible_rate_kg_s"][p]
    for q in U["rates"]:
        for model in ("coarse_usual", "coarse_kai"):
            now[f"ups_{q}_{model}_{p}"] = U["rates"][q][model]["breakthrough_change"][p]
now["dts_delta"] = dT_dts; now["dts_model_P50"] = W["dts_section_delta_model_c"]["P50"]; now["dts_bound_P50"] = W["dts_section_delta_upper_bound_c"]["P50"]
for q in G["rates"]:
    now[f"bt_converged_{q}"] = G["rates"][q]["breakthrough_years"]["converged"]; now[f"bt_gci_{q}"] = G["rates"][q]["breakthrough_years"]["error_abs"]
""" + CHECK.replace("PUBLISHED", "PUBLISHED_NB4").replace("RESULTFILE", "nb4_upscaling_check.json")),
("md", """## What this says, and what it does not

SUMMARY_NB4

**Limits.** Equivalent continuum with local thermal equilibrium. Barton–Bandis with assumed stiffness and closure ranges and σn = Shmin for every stimulated fracture. No fracture growth, shear dilation or thermal opening. Steady flow for the tracer, with no dispersion beyond the numerical one. Single-phase water in the wellbore. The DTS is used only as a check, and it fails that check.

*References:* Hasan, A. R. and Kabir, C. S. (1991). Heat transfer during two-phase flow in wellbores. SPE-22866 · Barton, N., Bandis, S. and Bakhtar, K. (1985). Strength, deformation and conductivity coupling of rock joints. Int. J. Rock Mech. 22(3) · Oda, M. (1985). Permeability tensor for discontinuous rock masses. Géotechnique 35(4) · Ding, Y. (1995). Scaling-up in the vicinity of wells in heterogeneous field. SPE-29137 · Chen, Y., Durlofsky, L. J. et al. (2003). A coupled local–global upscaling approach. Adv. Water Resour. 26 · Guo, Q., Oliver, J. and Shokanov, T. (2024). GDR 1701, DOI 10.15121/2507443."""),
])

nb5 = nb([
("md", """# 5 · The decision chart: what spacing would a 30-year doublet need?

**KAI-GeoEnergy · KAI Reservoir Lab · Utah FORGE, Milford, Utah (USA)**

**This well pair is a test bed, not a power plant.** 16A and 16B are about 96 m apart. At 10 kg/s their produced water starts to cool within a year (notebooks 3 and 4). The question here is what a doublet built for 30 years would need: how far apart, at what rate, and with what uncertainty.

**Method.**
1. **A proxy doublet.** Two parallel horizontal laterals with 480 m of open hole each, like 16A and 16B. They sit in a stimulated slab of fractured granite, which reaches 100 m beyond each well. The slab is an equivalent continuum, with the same physics as the FORGE model: TVD heat advection, conduction, and a log-normal, spatially correlated permeability. Rates are balanced and reinjection is at 60 °C.
2. **Tied to FORGE.** The slab thickness is the one free knob. At 96 m spacing and 10 kg/s, it is set so that the proxy gives the FORGE ensemble's 30-year temperature (P10, P50, P90; notebook 4, Barton–Bandis). The chart then keeps that thickness and changes only spacing and rate.
3. **A surrogate.** A Gaussian-process regression is trained on full proxy runs and tested on held-out runs. It fills the chart with P10–P90 values from a Monte Carlo over the uncertain inputs: thickness, heterogeneity, correlation length and rock conductivity. Outside its training range it returns nothing, and a full run is needed there.
4. **Variance-based sensitivity.** Sobol indices of the 30-year temperature, from the surrogate.

**The criterion.** A 30-year doublet here is one whose produced temperature after 30 years is still within 10 % of the way from initial to reinjection temperature: at least 198.6 °C for 214 °C initial and 60 °C reinjection.

**Assumptions that FORGE data do not show.** At larger spacings, stimulation would make a network of the same kind (same thickness, heterogeneity and conductivity), and that network would connect the wells. The pressure needed grows with spacing; the chart reports it as a multiple of the August 2024 pressure difference.

**Labels.** Proxy runs are **simulated**. Chart values and Sobol indices are **surrogate** values, with the surrogate's error published below."""),
("code", SETUP4 + """
Dd = E["decision"]
ch = Dd["chart"]"""),
("md", """## Tie to FORGE"""),
("code", """tie = Dd["tie_to_forge"]
display(pd.DataFrame({"slab thickness (m)": tie["slabs_m"], "proxy T year 30 at 96 m, 10 kg/s (°C)": np.round(tie["T30_c"], 1)}))
print("FORGE ensemble targets (°C):", {k: round(v, 1) for k, v in tie["targets_c"].items()})
print("slab thickness that reproduces them (m):", {k: (None if v is None else round(v, 0)) for k, v in tie["slab_m"].items()})
print(f"used: log-normal, median {Dd['slab_distribution']['median']:.0f} m, P10–P90 factor {Dd['slab_distribution']['factor']:.2f}; training range "
      f"{Dd['slab_training_range_m'][0]:.0f}–{Dd['slab_training_range_m'][1]:.0f} m")"""),
("md", """## The surrogate and its error

Its error on held-out full runs, and in 5-fold cross-validation. A quadratic regression is shown as the baseline, to show the Gaussian process is needed."""),
("code", """rows = []
for key, v in Dd["surrogate_validation"].items():
    for part in ("held_out", "cross_validation"):
        g, q_ = v[part]["gp"], v[part]["quadratic_baseline"]
        rows.append({"output": key, "test": part.replace("_", " "), "RMSE": round(g["rmse"], 3), "max |error|": round(g["max_abs"], 3), "R²": round(g["r2"], 4),
                     "90 % band coverage": round(g["coverage_90"], 2), "quadratic baseline RMSE": round(q_["rmse"], 3)})
display(pd.DataFrame(rows))
print(f"{Dd['training_runs']} training runs, {Dd['test_runs']} held-out runs, {Dd['failed_runs']} failed")
ho = Dd["held_out_predictions"]["T_prod_end_c"]
fig, ax = plt.subplots(figsize=(4.6, 4.4))
ax.errorbar(ho["full"], ho["surrogate"], yerr=1.645 * np.array(ho["std"]), fmt="o", color=GOLD, ms=4, ecolor=GREY, elinewidth=0.8)
lo, hi = min(ho["full"]) - 5, max(ho["full"]) + 5
ax.plot([lo, hi], [lo, hi], color=CHARCOAL, lw=0.8); ax.set_xlabel("full run, T year 30 (°C)"); ax.set_ylabel("surrogate (°C)")
ax.set_title("Held-out runs (surrogate vs simulated)"); fig.savefig("figures/forge_surrogate_error.png")
chk = pd.DataFrame(Dd["chart_full_run_checks"]); display(chk)"""),
("md", """## The chart"""),
("code", """cells = pd.DataFrame([{**{k: c[k] for k in ("spacing_m", "rate_kg_s", "fallback_share")}, **({f"T30_{p}": c["T30_c"][p] for p in ("P10", "P50", "P90")} if "T30_c" in c else {}),
                        **({f"MW_{p}": c["power_mean_mw"][p] for p in ("P10", "P50", "P90")} if "T30_c" in c else {}),
                        **({"dp_ratio_P50": c["dp_ratio_max"]["P50"], "meets": c["meets_criterion_share"]} if "T30_c" in c else {})} for c in ch["cells"]])
crit = ch["T_criterion_c"]
Ls, Qs = ch["spacings_m"], ch["rates_kg_s"]
piv = cells.pivot(index="rate_kg_s", columns="spacing_m", values="T30_P50")
fig, ax = plt.subplots(1, 2, figsize=(13, 4.6))
im = ax[0].imshow(piv.values, origin="lower", cmap="inferno", vmin=60, vmax=215, aspect="auto")
for i, q in enumerate(piv.index):
    for j, L in enumerate(piv.columns):
        r = cells[(cells.rate_kg_s == q) & (cells.spacing_m == L)].iloc[0]
        if np.isfinite(r.get("T30_P50", np.nan)):
            ax[0].text(j, i, f"{r.T30_P50:.0f}\\n{r.T30_P10:.0f}–{r.T30_P90:.0f}", ha="center", va="center", fontsize=6.5,
                       color="white" if r.T30_P50 < 150 else CHARCOAL, fontweight="bold" if r.T30_P10 >= crit else "normal")
ax[0].set_xticks(range(len(piv.columns))); ax[0].set_xticklabels([f"{L:.0f}" for L in piv.columns]); ax[0].set_yticks(range(len(piv.index))); ax[0].set_yticklabels([f"{q:.0f}" for q in piv.index])
ax[0].set_xlabel("well spacing (m)"); ax[0].set_ylabel("rate (kg/s)"); fig.colorbar(im, ax=ax[0], label="T year 30, P50 (°C)")
ax[0].set_title(f"30-year produced temperature, P50 and P10–P90 (bold: P10 ≥ {crit:.0f} °C)")
need = ch["spacing_needed_m"]
for lvl, c, mk in (("P50", GOLD, "o-"), ("P10", CHARCOAL, "s--")):
    xs = [need[str(int(q))][lvl] for q in Qs]
    ax[1].plot([x if x is not None else np.nan for x in xs], Qs, mk, color=c, label=f"spacing at which the {lvl} meets the criterion")
ax[1].axvline(96, color=GRANITE, lw=1, ls=":"); ax[1].text(100, 5, "16A–16B", color=GRANITE, fontsize=8, va="bottom")
beyond = [int(q) for q in Qs if need[str(int(q))]["P50"] is None]
if beyond:
    ax[1].text(0.98, 0.30, f"{', '.join(map(str, beyond))} kg/s: more than {max(Ls):.0f} m (beyond the chart)", transform=ax[1].transAxes, ha="right", fontsize=8)
ax[1].set_xscale("log"); ax[1].set_xlabel("well spacing (m)"); ax[1].set_ylabel("rate (kg/s)"); ax[1].legend(fontsize=8)
ax[1].set_title(f"Spacing a 30-year doublet needs (T30 ≥ {crit:.0f} °C)")
fig.suptitle("Decision chart (surrogate of simulated proxy runs, tied to the FORGE ensemble)", y=1.02, fontweight="bold")
fig.savefig("figures/forge_decision_chart.png")
rows = []
for q in Qs:
    n_ = need[str(int(q))]
    sel = cells[(cells.rate_kg_s == q)]
    rows.append({"rate (kg/s)": q, "spacing needed, P50 (m)": None if n_["P50"] is None else round(n_["P50"]), "spacing needed, P10 (m)": None if n_["P10"] is None else round(n_["P10"])})
display(pd.DataFrame(rows))
sel = cells[(cells.spacing_m == 400) & (cells.rate_kg_s == 40)].iloc[0]
print(f"example: 400 m at 40 kg/s: T year 30 {sel.T30_P50:.0f} ({sel.T30_P10:.0f}–{sel.T30_P90:.0f}) °C; mean heat {sel.MW_P50:.1f} ({sel.MW_P10:.1f}–{sel.MW_P90:.1f}) MWth; "
      f"pressure difference {sel.dp_ratio_P50:.1f} × the August 2024 value at today's network conductivity")"""),
("md", """## Which inputs matter (Sobol)"""),
("code", """S = Dd["sobol_T30"]
fig, ax = plt.subplots(1, len(S), figsize=(4.2 * len(S), 3.4))
rows = []
for a_, (lab, s) in zip(ax, S.items()):
    names = s["ranking"]
    a_.barh(names, [s["indices"][n]["ST"] for n in names], color=GOLD, label="total (ST)")
    a_.barh(names, [s["indices"][n]["S1"] for n in names], color=CHARCOAL, height=0.4, label="first order (S1)")
    a_.invert_yaxis(); a_.set_xlim(0, 1); a_.set_title(lab.replace("_", " "), fontsize=9)
    for n in names:
        rows.append({"case": lab, "input": n, "S1": round(s["indices"][n]["S1"], 3), "ST": round(s["indices"][n]["ST"], 3),
                     "ST 90 % CI": f"{s['indices'][n]['ST_ci'][0]:.2f}–{s['indices'][n]['ST_ci'][1]:.2f}"})
ax[0].legend(fontsize=8); fig.suptitle("Sobol indices of the 30-year temperature (surrogate)", y=1.04, fontweight="bold")
fig.savefig("figures/forge_sobol.png"); display(pd.DataFrame(rows))
sp = E["spearman"]
display(pd.DataFrame({o: {i: round(v["rho"], 2) for i, v in d.items()} for o, d in sp.items()}).T)
print("rank correlations in the 20-member FORGE ensemble (the full model; too few members for Sobol)")"""),
("md", """## Published numbers"""),
("code", """now = {"criterion_c": crit, "slab_P50": Dd["slab_distribution"]["median"]}
for q in Qs:
    for lvl in ("P50", "P10"):
        now[f"need_{int(q)}_{lvl}"] = need[str(int(q))][lvl]
for key in Dd["surrogate_validation"]:
    now[f"rmse_{key}"] = Dd["surrogate_validation"][key]["held_out"]["gp"]["rmse"]
for lab, s in S.items():
    now[f"top_{lab}"] = s["ranking"][0]
""" + CHECK.replace("PUBLISHED", "PUBLISHED_NB5").replace("RESULTFILE", "nb5_decision_chart.json")),
("md", """## What this says, and what it does not

SUMMARY_NB5

**Limits.** The proxy is a simplification: parallel laterals and a uniform slab, tied to FORGE at one spacing. Extrapolating to larger spacings assumes that stimulation scales. Heat exchange assumes local thermal equilibrium. The pressure column assumes today's network conductivity; a real design would add stimulation. The chart values are surrogate values: their error against full runs is given above, and the chart is blank wherever the surrogate would extrapolate.

*References:* Gringarten, A. C. and Sauty, J. P. (1975). A theoretical study of heat extraction from aquifers with uniform regional flow. JGR 80(35) · Saltelli, A. et al. (2010). Variance based sensitivity analysis of model output. Comput. Phys. Commun. 181 · Rasmussen, C. E. and Williams, C. K. I. (2006). Gaussian Processes for Machine Learning. MIT Press."""),
])


if __name__ == "__main__":
    import json
    import pathlib
    import sys

    pub = json.loads(pathlib.Path("results/published_phase4.json").read_text()) if pathlib.Path("results/published_phase4.json").exists() else None
    if pub is None:
        sys.exit("results/published_phase4.json missing")
    for name, book, key in (("04_upscaling_check.ipynb", nb4, "nb4"), ("05_decision_chart.ipynb", nb5, "nb5")):
        for c in book.cells:
            c.source = c.source.replace(f"PUBLISHED_{key.upper()}", repr(pub[key])).replace(f"SUMMARY_{key.upper()}", pub.get(f"summary_{key}", ""))
        nbf.write(book, name)
        print("wrote", name)
