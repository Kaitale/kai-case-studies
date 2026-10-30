"""Builds the Utah FORGE phase 4 notebooks 04, 04b and 05 (run: python make_notebooks4.py, then execute them).

The numbers each notebook asserts are in results/published_phase4.json. `python make_notebooks4.py --publish`
writes that file from results/kai_engine_phase4.json (do this only when the engine results are meant to change).
"""
import json
import pathlib
import sys

import nbformat as nbf

from make_notebooks import nb

SETUP4 = """import json, pathlib, warnings
import numpy as np, pandas as pd, matplotlib.pyplot as plt
import forge_tools as ft
warnings.filterwarnings("ignore")
plt.rcParams.update({"figure.dpi": 110, "axes.grid": False, "axes.spines.top": False, "axes.spines.right": False, "font.size": 10,
                     "axes.titleweight": "bold", "axes.titlesize": 11, "legend.frameon": False, "savefig.bbox": "tight", "savefig.facecolor": "white"})
GOLD, CHARCOAL, FILL, GRANITE, BLUE = "#c9a227", "#26292e", "#d8c7a3", "#b5838d", "#2a78d6"     # KAI energy palette
pathlib.Path("figures").mkdir(exist_ok=True)
E = json.loads(pathlib.Path("results/kai_engine_phase4.json").read_text())
PUB = json.loads(pathlib.Path("results/published_phase4.json").read_text()) if pathlib.Path("results/published_phase4.json").exists() else {}
ens = E["ensemble"]
def pct(d, f="{:.1f}"):
    return f"{f.format(d['P50'])} ({f.format(d['P10'])}–{f.format(d['P90'])})"
def check(now, key):
    pathlib.Path(f"results/{key}.json").write_text(json.dumps({"published": now}, indent=1))
    if key not in PUB:
        print(f"{key}: no published numbers yet; wrote results/{key}.json")
        return
    bad = []
    for k, v in PUB[key].items():
        x = now[k]
        if isinstance(v, (str, bool)) or v is None or isinstance(x, (str, bool)) or x is None:
            ok = x == v
        else:
            ok = abs(x - v) <= 0.02 * abs(v) + 1e-3
        if not ok:
            bad.append((k, x, v))
    assert not bad, bad
    print(f"all {len(PUB[key])} published numbers reproduced")
print(f"{ens['members'] - ens['failed']}/{ens['members']} members ran; engine results generated {E['generated']}")"""


# ---------------------------------------------------------------------------------------------- 04b
nb4b = nb([
("md", """# 4b · Wellbore, apertures that respond to pressure, and tracers

**KAI-GeoEnergy · KAI Reservoir Lab · Utah FORGE, wells 16A(78)-32 / 16B(78)-32**

**Questions.** (1) How much of the produced-temperature misfit of notebook 3 (+13 °C after a simple wellbore estimate) does a proper wellbore model explain? (2) If the stimulated fractures open as pressure rises (Barton–Bandis), which circulation rates become possible without exceeding the minimum horizontal stress, and at what injector pressure? (3) Do the modelled travel times between the wells agree with the 2024 tracer test?

**Data.** GDR 1683 (August 2024 circulation test), GDR 1721 (16B fibre-optic temperatures, DTS, 4 Aug and 12–16 Aug 2024), GDR 1701 (QuantumPro nanoparticle tracers, August 2024). All CC BY 4.0. Only derived values are in `data/`.

**Labels.** Every model number is **simulated** (KAI Reservoir Lab). P10 is the 10th percentile of the members (the low case), P90 the 90th. The model creates no new fractures."""),
("code", SETUP4),
("md", """## 1 · The wellbore model on the August 2024 test

16B is modelled from its top open cell to the wellhead along its surveyed trajectory: single-phase water, Colebrook friction, transient heat loss to the rock (Hasan–Kabir), the FORGE 3-D temperature model as the undisturbed rock temperature. 24 members vary rock and cement conductivity, hole size, a ±10 °C offset of the rock temperature and the wellhead-gauge correction. The same model gives the bottom-hole pressures of both wells, which the reservoir model now uses."""),
("code", """W = E["wellbore"]
S = json.loads(pathlib.Path("data/circulation_2024_summary.json").read_text())
V = ens["validation"]
rows = [
    {"quantity": "wellbore cooling, model bottom hole → wellhead (°C)", "value P50 (P10–P90)": pct(W["cooling_from_model_c"])},
    {"quantity": "bottom-hole temperature implied by the measured wellhead (°C)", "value P50 (P10–P90)": pct(W["T_bottom_implied_c"])},
    {"quantity": "reservoir model, produced temperature at the bottom hole (°C)", "value P50 (P10–P90)": pct(V["constant_apertures"]["produced_T_bottomhole_c"])},
    {"quantity": "misfit at the bottom hole, model − implied (°C)", "value P50 (P10–P90)": pct(V["constant_apertures"]["T_misfit_bottomhole_c"])},
    {"quantity": "injector bottom-hole pressure (MPa)", "value P50 (P10–P90)": pct(W["injector_bhp_mpa"], "{:.2f}")},
    {"quantity": "injector bottom-hole temperature (°C)", "value P50 (P10–P90)": pct(W["injector_T_bottom_c"])},
    {"quantity": "producer bottom-hole pressure (MPa)", "value P50 (P10–P90)": pct(W["producer_bhp_mpa"], "{:.2f}")},
]
display(pd.DataFrame(rows))
wh = S["T_16B_wellhead_c"]
a3 = json.loads(pathlib.Path("results/kai_engine_phase3.json").read_text())["ensemble"]["validation"]["august_2024"]
gap3 = a3["produced_T_bottomhole_c"]["P50"] - a3["wellbore_cooling_estimate_c"]["P50"] - a3["measured_T_wellhead_c"]["P50"]
expl = gap3 - V["constant_apertures"]["T_misfit_bottomhole_c"]["P50"]
print(f"measured wellhead {wh:.1f} °C. Phase 3 gap after the Ramey estimate: +{gap3:.0f} °C. "
      f"Now: +{V['constant_apertures']['T_misfit_bottomhole_c']['P50']:.1f} °C, so the wellbore model explains {expl:.1f} °C of it ({expl / gap3:.0%}).")"""),
("md", """## 2 · The 16B fibre temperatures (DTS)

The flowing profile (median of days 6.5–7.7) has an 80 °C step near 3,000 ft, which no flowing well can have: the fibre's absolute level is not trusted, and above the step it also drifts. Below the step the record is smooth (scatter about 0.2 °C), so its *shape* is used: how much the water cools between the top of the open hole (9,240 ft) and 3,200 ft. The data numbers are recomputed here from `data/dts_16B_2024.csv` and must agree with the engine."""),
("code", """dts = pd.read_csv("data/dts_16B_2024.csv")
deep = json.loads(pathlib.Path("data/dts_16B_2024_deep.json").read_text())
D = E["dts"]
assert abs(deep["T_bottom_c"] - deep["T_top_c"] - D["deep"]["delta_c"]) < 0.05
sec = dts[(dts.md_ft >= 3200) & (dts.md_ft < 9200)]
slope = np.polyfit(sec.md_ft * 0.3048, sec.flowing_days_6p5_7p7_c, 1)[0] * 1000
assert abs(slope - D["deep"]["slope_c_per_km_md"]) / D["deep"]["slope_c_per_km_md"] < 0.05, slope
print(f"DTS, 9,240 → 3,200 ft: {D['deep']['delta_c']:.1f} °C of cooling (slope {D['deep']['slope_c_per_km_md']:.1f} °C per km along hole; scatter {D['deep']['sd_median_c']:.2f} °C)")
print(f"wellbore model on the same section: {pct(W['dts_section_delta_model_c'])} °C; upper bound (no insulation, highest conductivity): {pct(W['dts_section_delta_upper_bound_c'])} °C")
pr = W["profile_p50"]
dts = dts[dts.md_ft < 10000]                     # the last bin is past the end of the fibre
fig, ax = plt.subplots(1, 2, figsize=(11, 4.6), sharey=True)
ax[0].plot(dts.static_4aug_c, dts.md_ft * 0.3048, color=CHARCOAL, lw=1.2, label="DTS, 4 Aug (before the test)")
ax[0].plot(dts.flowing_days_6p5_7p7_c, dts.md_ft * 0.3048, color=GRANITE, lw=1.5, label="DTS, flowing (days 6.5–7.7)")
ax[0].plot(pr["T_e"], pr["md_m"], "--", color=CHARCOAL, lw=1, label="rock temperature (FORGE model)")
ax[0].plot(pr["T_c"], pr["md_m"], color=BLUE, lw=2, label="wellbore model, flowing (P50)")
ax[0].axhspan(2700 * 0.3048, 3200 * 0.3048, color=FILL, alpha=0.5, lw=0)
ax[0].invert_yaxis(); ax[0].set_xlabel("°C"); ax[0].set_ylabel("measured depth (m)"); ax[0].set_title("16B temperature, August 2024"); ax[0].legend(fontsize=8, loc="lower left")
sel = (dts.md_ft >= 3200) & (dts.md_ft <= 9240)
o = np.argsort(pr["md_m"]); zz = dts.md_ft[sel] * 0.3048
Tm = np.interp(zz, np.array(pr["md_m"])[o], np.array(pr["T_c"])[o])
ax[1].plot(dts.flowing_days_6p5_7p7_c[sel] - dts.flowing_days_6p5_7p7_c[sel].iloc[-1], zz, color=GRANITE, lw=2, label="DTS (shape, relative to 9,240 ft)")
ax[1].plot(Tm - Tm[-1], zz, color=BLUE, lw=2, label="wellbore model (relative)")
ax[1].set_xlabel("°C relative to the open-hole top"); ax[1].set_title("Below the step: shape only"); ax[1].legend(fontsize=8)
fig.suptitle("16B: fibre temperatures against the wellbore model (simulated vs measured)", y=1.02, fontweight="bold")
fig.savefig("figures/forge_wellbore_dts.png")"""),
("md", """**Reading it.** The wellbore model explains part of the misfit, not all of it. The DTS shape says the water cools about three times faster up the deep hole than conduction to the rock allows, even with no insulation. Two readings fit that: cooler water enters 16B higher up than the model's open cells (which would also explain the remaining bottom-hole misfit), or the fibre's calibration drifts along its length (it clearly does near 3,000 ft). This run cannot tell them apart. A production log (spinner and temperature) in 16B would."""),
("md", """## 3 · Apertures that respond to pressure (Barton–Bandis)

Each stimulated fracture closes or opens with the effective normal stress, Shmin − p (Barton–Bandis, normal stiffness 5–60 MPa/mm and maximum closure 0.1–0.5 mm, both ensemble parameters). The calibrated apertures are the apertures at the August 2024 pressures, so the fit to the test is kept. A rate is **feasible** when the injector bottom-hole pressure stays at or below Shmin at its top open cell for 30 years. Above Shmin new fractures would open; the model does not make them, so that is where it stops."""),
("code", """R = ens["rates"]
rows = []
for kind, lab in (("constant_apertures", "constant apertures (phase 3)"), ("barton_bandis", "Barton–Bandis")):
    for q, r in R[kind].items():
        if q == "max_feasible_rate_kg_s":
            continue
        rows.append({"apertures": lab, "rate (kg/s)": int(q), "injector BHP, max (MPa)": pct(r["injector_bhp_max_mpa"]),
                     "Shmin (MPa)": round(r["shmin_injector_mpa"], 1), "BHP / Shmin": pct(r["injector_bhp_over_shmin"], "{:.2f}"),
                     "feasible members": f"{r['feasible_members']}/{ens['members'] - ens['failed']}",
                     "T year 30 (°C)": pct(r["T_prod_end_c"]), "breakthrough (years, 35 m)": pct(r["breakthrough_years"], "{:.2f}")})
display(pd.DataFrame(rows))
for kind in ("constant_apertures", "barton_bandis"):
    print(f"highest feasible rate, {kind.replace('_', ' ')}: {pct(R[kind]['max_feasible_rate_kg_s'])} kg/s")
fig, ax = plt.subplots(figsize=(7, 4))
for kind, c, lab in (("constant_apertures", CHARCOAL, "constant apertures"), ("barton_bandis", GOLD, "Barton–Bandis")):
    qs = [int(q) for q in R[kind] if q != "max_feasible_rate_kg_s"]
    b = [R[kind][str(q)]["injector_bhp_max_mpa"] for q in qs]
    ax.fill_between(qs, [x["P10"] for x in b], [x["P90"] for x in b], color=c, alpha=0.2)
    ax.plot(qs, [x["P50"] for x in b], "o-", color=c, label=lab)
sh = R["barton_bandis"]["10"]["shmin_injector_mpa"]
ax.axhline(sh, color=GRANITE, ls="--"); ax.text(qs[0], sh + 0.4, f"Shmin {sh:.1f} MPa (new fractures above)", color=GRANITE, fontsize=8)
ax.set_xlabel("circulation rate (kg/s)"); ax.set_ylabel("MPa"); ax.set_title("Highest injector pressure in 30 years, P10–P90 (simulated)"); ax.legend(fontsize=8)
fig.savefig("figures/forge_barton_bandis.png")"""),
("code", """VB, VC = V["barton_bandis"], V["constant_apertures"]
print(f"August test with Barton–Bandis: produced {pct(VB['produced_kg_s'])} kg/s, recovery {pct(VB['recovery'], '{:.3f}')} "
      f"(measured {V['measured']['measured_produced_kg_s']:.1f} kg/s, {V['measured']['measured_recovery']:.3f}); "
      f"build-up misfit, worst day 4–15: {pct(VB['buildup_misfit_mpa_days4_15_max_abs'])} MPa (constant apertures {pct(VC['buildup_misfit_mpa_days4_15_max_abs'])})")"""),
("md", """## 4 · Tracers: travel time between the wells

QuantumPro injected ten nanoparticle tracers into 16A during the August test, one every two days, and sampled 16B every few hours. The first-detection times are recomputed here from `data/tracers_2024_circulation.csv`: between the last clean and the first positive sample. For tracers 5–10 the first sample after injection was already positive, so only an upper bound is known. The model injects a 30-minute pulse at the August flow and tracks it in the fracture porosity only (nanoparticles do not enter the granite matrix)."""),
("code", """trc = pd.read_csv("data/tracers_2024_circulation.csv")
meas = {x["tracer"]: x for x in E["tracers_measured"]["summary"] if x.get("detected")}
for t, g in trc.groupby("tracer"):
    a = g[g.sample_t_h > g.injected_t_h.iloc[0]]
    ta, c = (a.sample_t_h - a.injected_t_h).values, a.c_ppb.values
    i = int(np.argmax(c > 0))
    assert abs(ta[i] - meas[t]["first_positive_h"]) < 0.02 and abs(ta[np.argmax(c)] - meas[t]["peak_h"]) < 0.02, t
TV = E["tracer_validation"]
rows = [{"tracer": r["tracer"], "first detection (h)": (f"{r['first_detection_bracket_h'][0]:.1f}–{r['first_detection_bracket_h'][1]:.1f}" if r["lower_bound_known"] else f"< {r['first_detection_bracket_h'][1]:.1f}"),
         "peak sample (h)": round(r["peak_h"], 1), "measured / modelled first arrival": (f"{r['ratio_first_vs_model_P50'][0]:.0f}–{r['ratio_first_vs_model_P50'][1]:.0f} ×" if r["lower_bound_known"] else f"< {r['ratio_first_vs_model_P50'][1]:.0f} ×"),
         "measured / modelled peak": f"{r['ratio_peak_vs_model_P50']:.0f} ×"}
        for r in TV["tracers"]]
display(pd.DataFrame(rows))
T4 = ens["tracer"]
print(f"model (fracture porosity): first arrival {pct(T4['first_arrival_1pct_peak_h'], '{:.2f}')} h, peak {pct(T4['peak_time_h'], '{:.2f}')} h, "
      f"mean residence {pct(T4['mean_residence_h'], '{:.1f}')} h, pore volume {pct(T4['pore_volume_m3'], '{:.0f}')} m³")
print(f"to match the measured first arrivals, the mobile pore volume would have to be {TV['porosity_factor_to_match_first_arrival'][0]:.0f}–{TV['porosity_factor_to_match_first_arrival'][1]:.0f} × larger; "
      f"to match the peaks {TV['porosity_factor_to_match_peak'][0]:.0f}–{TV['porosity_factor_to_match_peak'][1]:.0f} ×")
cm = E["median_member"]["tracer"]["curve"]
fig, ax = plt.subplots(figsize=(8, 4))
for t, g in trc.groupby("tracer"):
    a = g[g.sample_t_h > g.injected_t_h.iloc[0]]
    if a.c_ppb.max() > 0 and t <= 4:
        ax.plot(a.sample_t_h - a.injected_t_h, a.c_ppb / a.c_ppb.max(), "o-", ms=3, lw=1, color=plt.get_cmap("cividis")(t / 5), label=f"tracer {t} (measured)")
ax.plot(cm["t_h"], cm["c_rel"], color=GOLD, lw=2.5, label="model, median member (simulated)")
ax.set_xscale("log"); ax.set_xlim(0.01, 300); ax.set_xlabel("hours after injection"); ax.set_ylabel("concentration / peak")
ax.set_title("Tracer arrival at 16B: model against measured"); ax.legend(fontsize=8)
fig.savefig("figures/forge_tracers.png")"""),
("md", """**Reading it.** The model's water arrives far too early. Its first arrival falls inside the first time step (2 minutes) and its peak at the end of the 30-minute pulse, so the modelled times are upper bounds and the ratios above are lower bounds on the misfit. With hydraulic apertures (the apertures that fit the pressure, cubic law), the fracture pore volume between the wells is small, so a pulse crosses in minutes to an hour; the tracers took hours to days. Fractures with rough walls hold much more water than their hydraulic aperture says, so a transport aperture larger than the hydraulic one is expected. The factor above is how much larger the mobile pore volume would have to be. The model is not calibrated to the tracers here: doing so changes no pressure and no rate, but it slows the cooling front only if the extra volume also exchanges heat with the rock, which is an open question (see the end of this notebook). This is the most important misfit of phase 4."""),
("md", """## Published numbers"""),
("code", """now = {"T_bottom_implied_P50": W["T_bottom_implied_c"]["P50"], "cooling_from_model_P50": W["cooling_from_model_c"]["P50"],
       "cooling_from_model_P10": W["cooling_from_model_c"]["P10"], "cooling_from_model_P90": W["cooling_from_model_c"]["P90"],
       "misfit_bh_P50": V["constant_apertures"]["T_misfit_bottomhole_c"]["P50"], "misfit_bh_P10": V["constant_apertures"]["T_misfit_bottomhole_c"]["P10"],
       "misfit_bh_P90": V["constant_apertures"]["T_misfit_bottomhole_c"]["P90"], "phase3_gap_after_ramey_c": gap3, "explained_c": expl,
       "dts_delta_measured": D["deep"]["delta_c"], "dts_delta_model_P50": W["dts_section_delta_model_c"]["P50"], "dts_delta_upper_P90": W["dts_section_delta_upper_bound_c"]["P90"]}
for kind in ("constant_apertures", "barton_bandis"):
    for p in ("P10", "P50", "P90"):
        now[f"max_rate_{kind}_{p}"] = R[kind]["max_feasible_rate_kg_s"][p]
    for q in ("10", "20", "40"):
        now[f"feasible_{kind}_{q}"] = R[kind][q]["feasible_members"]
        now[f"bhp_max_{kind}_{q}_P50"] = R[kind][q]["injector_bhp_max_mpa"]["P50"]
for k in ("first_arrival_1pct_peak_h", "peak_time_h", "mean_residence_h"):
    for p in ("P10", "P50", "P90"):
        now[f"tracer_{k}_{p}"] = T4[k][p]
now["tracer_factor_first_lo"], now["tracer_factor_first_hi"] = TV["porosity_factor_to_match_first_arrival"]
check(now, "nb4b")"""),
("md", """## What this says, and what it does not

SUMMARY_NB4B

*References:* Hasan, A. R. and Kabir, C. S. (1991). Heat transfer during two-phase flow in wellbores. SPE 22866 · Barton, N., Bandis, S. and Bakhtar, K. (1985). Strength, deformation and conductivity coupling of rock joints. Int. J. Rock Mech. Min. Sci. 22(3) · McLennan, J., England, K. and Swearingen, L. (2024). GDR 1683, DOI 10.15121/2475065 · Guo, Oliver and Shokanov (2024). GDR 1701, DOI 10.15121/2507443 · Neubrex (2024). GDR 1721."""),
])


# ---------------------------------------------------------------------------------------------- 04
nb4 = nb([
("md", """# 4 · Upscaling check: does a coarse model change the answer?

**KAI-GeoEnergy · KAI Reservoir Lab · Utah FORGE, wells 16A(78)-32 / 16B(78)-32**

**Questions.** (1) Does the full permeability tensor (with its off-diagonal terms) change breakthrough and rate against the diagonal used in phase 3? (2) A 70 m model is usual practice for a reservoir this size. How much does it change the breakthrough time against the 23.3 m model of the same fractures, done the usual way and with KAI's upscaling? (3) What does the near-well part of the upscaling do?

**Labels.** All numbers are **simulated** (KAI Reservoir Lab, equivalent-continuum fractured granite). Breakthrough is the time the produced temperature has fallen by 5 % of (initial − reinjection) temperature, reinjection at 60 °C. P10–P90 over the members."""),
("code", SETUP4),
("md", """## 1 · Full tensor against diagonal

The median member, each scheme calibrated on its own to the August 2024 injection pressure, on 35 m and 23.3 m cells. The full tensor is the Oda tensor with its cross terms (TPFA plus a cross-flux correction); off-diagonal terms reach about 0.4 of the diagonal in the stimulated cells."""),
("code", """FT = E["full_tensor"]
rows = []
for r in FT["runs"]:
    for q, f in r["forecast"].items():
        rows.append({"cells (m)": round(r["cell_m"], 1), "scheme": r["scheme"], "rate (kg/s)": int(q), "aperture factor λ": round(r["stim_aperture_factor"], 4),
                     "breakthrough (years)": round(f["breakthrough_years"], 3), "T year 30 (°C)": round(f["T_prod_end_c"], 1),
                     "injector BHP max (MPa)": round(f["injector_bhp_max_mpa"], 2), "tracer peak (h)": round(r["tracer"]["peak_time_h"], 3)})
tab = pd.DataFrame(rows); display(tab)
chg = {}
for c in FT["cells_m"]:
    d = [r for r in FT["runs"] if abs(r["cell_m"] - c) < 1e-6]
    dg, fl = (next(r for r in d if r["scheme"].startswith(s)) for s in ("diagonal", "full"))
    for q in dg["forecast"]:
        chg[f"{c:.1f}_{q}"] = {"breakthrough": fl["forecast"][q]["breakthrough_years"] / dg["forecast"][q]["breakthrough_years"] - 1,
                               "T30_c": fl["forecast"][q]["T_prod_end_c"] - dg["forecast"][q]["T_prod_end_c"],
                               "lambda": fl["stim_aperture_factor"] / dg["stim_aperture_factor"] - 1}
for k, v in chg.items():
    c, q = k.split("_")
    print(f"{c} m, {q} kg/s: full tensor changes breakthrough by {v['breakthrough']:+.1%}, 30-year temperature by {v['T30_c']:+.1f} °C, calibrated λ by {v['lambda']:+.1%}")"""),
("md", """Calibration absorbs most of the difference: both schemes are fitted to the same measured pressure, so the full tensor mostly moves λ. What remains is the change in *where* the water goes, which shows in the breakthrough time."""),
("md", """## 2 · Coarse against fine

Each of the first members of the ensemble is built twice from the same fracture network: on 23.3 m cells (the reference) and on 70 m cells. The 70 m model is then used two ways:

* **usual practice**: the Oda tensor of the same fractures on 70 m cells, Peaceman well indices, recalibrated on the August test;
* **KAI**: transmissibilities and well indices upscaled from the fine model's own well-pair solution (global plus near-well upscaling), *not* recalibrated.

Rates are balanced (injection = production) for 30 years."""),
("code", """U = E["upscaling"]
rows = []
for q, d in U["rates"].items():
    rows.append({"rate (kg/s)": int(q), "fine 23.3 m: breakthrough (y)": pct(d["fine"]["breakthrough_years"], "{:.2f}"),
                 "70 m usual (y)": pct(d["coarse_usual"]["breakthrough_years"], "{:.2f}"), "70 m usual vs fine": pct({k: 100 * v for k, v in d["coarse_usual"]["breakthrough_change"].items() if k in ("P10", "P50", "P90")}, "{:+.0f}%"),
                 "70 m KAI (y)": pct(d["coarse_kai"]["breakthrough_years"], "{:.2f}"), "70 m KAI vs fine": pct({k: 100 * v for k, v in d["coarse_kai"]["breakthrough_change"].items() if k in ("P10", "P50", "P90")}, "{:+.0f}%"),
                 "T30 change usual (°C)": pct(d["coarse_usual"]["T30_change_c"]), "T30 change KAI (°C)": pct(d["coarse_kai"]["T30_change_c"])})
display(pd.DataFrame(rows))
print(f"members: {U['members'] - U['failed']}/{U['members']} ok")
M = [m for m in E["upscaling_members"] if m["ok"]]
fig, ax = plt.subplots(1, 2, figsize=(11, 4.2))
for a_, q in zip(ax, U["rates"]):
    f = np.array([m["rates"][q]["fine"]["breakthrough_years"] for m in M])
    for k, c, lab in (("coarse_usual", CHARCOAL, "70 m, usual practice"), ("coarse_kai", GOLD, "70 m, KAI upscaling")):
        a_.plot(f, [m["rates"][q][k]["breakthrough_years"] for m in M], "o", color=c, label=lab)
    lim = [0, max(f.max(), max(m["rates"][q]["coarse_usual"]["breakthrough_years"] for m in M)) * 1.1]
    a_.plot(lim, lim, color=FILL, lw=1); a_.set_xlim(lim); a_.set_ylim(lim)
    a_.set_xlabel("fine model, 23.3 m (years)"); a_.set_ylabel("coarse model (years)"); a_.set_title(f"Breakthrough at {q} kg/s"); a_.legend(fontsize=8)
fig.suptitle("Coarse against fine model of the same fractures, one point per member (simulated)", y=1.02, fontweight="bold")
fig.savefig("figures/forge_upscaling_check.png")"""),
("md", """## 3 · The near-well part

The August test fixes the pressure difference between the wells. A coarse model that is not recalibrated shows how much its well indices and transmissibilities miss it."""),
("code", """print(f"August 2024 pressure difference to match: {pct(U['august_dp_target_mpa'], '{:.2f}')} MPa")
print(f"70 m usual, fine-model apertures, not recalibrated: {pct(U['coarse_usual_uncalibrated_august_dp_mpa'], '{:.2f}')} MPa")
print(f"70 m KAI upscaling, not recalibrated: {pct(U['coarse_kai_august_dp_mpa'], '{:.2f}')} MPa")
print(f"aperture factor λ: fine {pct(U['stim_aperture_factor']['fine'], '{:.3f}')}, 70 m usual (recalibrated) {pct(U['stim_aperture_factor']['coarse_usual'], '{:.3f}')}")
print(f"coarse faces where the global upscaling fell back to the local value: {pct(U['fallback_faces'], '{:.0f}')}")"""),
("md", """## 4 · Grid convergence of the phase 4 breakthrough

The median member with Barton–Bandis apertures, rebuilt and recalibrated at 52.5, 35 and 23.3 m. The converged value is the Richardson extrapolation; ± is the grid convergence index (GCI, safety factor 1.25)."""),
("code", """G = E["grid_convergence"]
rows = []
for q, g in G["rates"].items():
    b = g["breakthrough_years"]
    rows.append({"rate (kg/s)": int(q), **{f"{r['cell_m']:.1f} m": round(r["breakthrough_years"], 3) for r in g["runs"]},
                 "converged ± GCI (years)": f"{b['converged']:.3f} ± {b['error_abs']:.3f}", "observed order": None if b.get("order") is None else round(b["order"], 2)})
display(pd.DataFrame(rows))"""),
("md", """## Published numbers"""),
("code", """now = {}
for k, v in chg.items():
    now[f"ft_bt_change_{k}"] = v["breakthrough"]; now[f"ft_T30_change_{k}"] = v["T30_c"]
for q, d in U["rates"].items():
    for m in ("coarse_usual", "coarse_kai"):
        for p in ("P10", "P50", "P90"):
            now[f"up_{m}_{q}_{p}"] = d[m]["breakthrough_change"][p]
    for p in ("P10", "P50", "P90"):
        now[f"up_fine_bt_{q}_{p}"] = d["fine"]["breakthrough_years"][p]
now["up_members_ok"] = U["members"] - U["failed"]
now["kai_dp_P50"] = U["coarse_kai_august_dp_mpa"]["P50"]; now["usual_dp_P50"] = U["coarse_usual_uncalibrated_august_dp_mpa"]["P50"]
now["dp_target_P50"] = U["august_dp_target_mpa"]["P50"]
for q, g in G["rates"].items():
    now[f"bt_converged_{q}"] = g["breakthrough_years"]["converged"]; now[f"bt_gci_{q}"] = g["breakthrough_years"]["error_abs"]
check(now, "nb4")"""),
("md", """## What this says, and what it does not

SUMMARY_NB4"""),
])


# ---------------------------------------------------------------------------------------------- 05
nb5 = nb([
("md", """# 5 · Decision chart: what spacing would a 30-year doublet need?

**KAI-GeoEnergy · KAI Reservoir Lab · Utah FORGE**

**This well pair is a test bed, not a power plant.** 16A and 16B are about 96 m apart where they are open; at 10 kg/s the produced water starts to cool within about two years. This notebook asks the design question instead: for well spacing 75–800 m and rates 5–80 kg/s, what produced temperature and heat power would a doublet in this granite give after 30 years, and what spacing keeps the temperature up?

**Method.** A proxy doublet (two parallel laterals in a stimulated slab of fractured granite, same physics as the FORGE model) is tied to the FORGE ensemble: its one free knob, the effective slab thickness, is set so that at 96 m and 10 kg/s it gives the FORGE ensemble's 30-year temperature (P10, P50, P90). Then only spacing and rate change. A Gaussian-process surrogate is trained on full proxy runs, checked on held-out runs, and used for the chart and the Sobol indices.

**Labels.** Proxy runs are **simulated**; the chart and Sobol indices are **surrogate** values (trained on simulations). The chart assumes stimulation at a larger spacing makes a network of the same kind that still connects the wells. FORGE data do not show that."""),
("code", SETUP4),
("md", """## 1 · The FORGE ensemble with Barton–Bandis apertures (30 years)"""),
("code", """R = ens["rates"]["barton_bandis"]
rows = []
for q, r in R.items():
    if q == "max_feasible_rate_kg_s":
        continue
    rows.append({"rate (kg/s)": int(q), "T year 1 (°C)": pct(r["T_prod_initial_c"]), "T year 10 (°C)": pct(r["T_prod_10y_c"]), "T year 30 (°C)": pct(r["T_prod_end_c"]),
                 "breakthrough (y, 35 m)": pct(r["breakthrough_years"], "{:.2f}"), "MWth year 1": pct(r["power_initial_mw"]), "MWth year 30": pct(r["power_end_mw"]),
                 "feasible": f"{r['feasible_members']}/{ens['members'] - ens['failed']}"})
display(pd.DataFrame(rows))"""),
("md", """## 2 · Tie to FORGE and the surrogate's error"""),
("code", """DC = E["decision"]
tie = DC["tie_to_forge"]
print(f"proxy at 96 m, 10 kg/s: slab {tie['slabs_m']} m gives T30 {[round(t, 1) for t in tie['T30_c']]} °C")
print(f"FORGE targets {({k: round(v, 1) for k, v in tie['targets_c'].items()})} → slab {({k: (None if v is None else round(v, 1)) for k, v in tie['slab_m'].items()})} m")
rows = []
for k, v in DC["surrogate_validation"].items():
    h, cv = v["held_out"]["gp"], v["cross_validation"]
    rows.append({"output": k, "held-out runs": v["held_out"]["n_test"], "RMSE": round(h["rmse"], 3), "max |error|": round(h["max_abs"], 3), "R²": round(h["r2"], 4),
                 "90 % interval coverage": h.get("coverage_90"), "quadratic baseline RMSE": round(v["held_out"]["quadratic_baseline"]["rmse"], 3)})
display(pd.DataFrame(rows))
rows = [{"spacing (m)": c["spacing_m"], "rate (kg/s)": c["rate_kg_s"], "full runs P50 (°C)": round(c["full_P50_c"], 1), "surrogate P50 (°C)": round(c["surrogate_P50_c"], 1),
         "member |error| P50 (°C)": round(c["member_abs_error_c"]["P50"], 2)} for c in DC["chart_full_run_checks"]]
display(pd.DataFrame(rows))"""),
("md", """## 3 · The chart"""),
("code", """CH = DC["chart"]
Ls, Qs = CH["spacings_m"], CH["rates_kg_s"]
def grid(key, lvl="P50"):
    G = np.full((len(Qs), len(Ls)), np.nan)
    for c in CH["cells"]:
        if key in c:
            G[Qs.index(c["rate_kg_s"]), Ls.index(c["spacing_m"])] = c[key][lvl]
    return G
fig, ax = plt.subplots(1, 2, figsize=(13, 4.6))
for a_, key, lab, cmap in ((ax[0], "T30_c", "°C after 30 years (P50)", "inferno"), (ax[1], "power_mean_mw", "mean MWth over 30 years (P50)", "cividis")):
    G = grid(key)
    im = a_.imshow(G, origin="lower", cmap=cmap, aspect="auto")
    for i in range(len(Qs)):
        for j in range(len(Ls)):
            if np.isfinite(G[i, j]):
                a_.text(j, i, f"{G[i, j]:.0f}", ha="center", va="center", fontsize=7, color="white" if key == "T30_c" and G[i, j] < 150 else "black")
    a_.set_xticks(range(len(Ls)), [f"{L:.0f}" for L in Ls]); a_.set_yticks(range(len(Qs)), [f"{q:.0f}" for q in Qs])
    a_.set_xlabel("well spacing (m)"); a_.set_ylabel("rate (kg/s)"); a_.set_title(lab); fig.colorbar(im, ax=a_, shrink=0.85)
fig.suptitle(f"Doublet in FORGE-like stimulated granite: spacing × rate (surrogate; criterion {CH['T_criterion_c']:.0f} °C = 10 % of the drop)", y=1.02, fontweight="bold")
fig.savefig("figures/forge_decision_chart.png")
rows = [{"rate (kg/s)": int(q), "spacing needed, P50 (m)": (None if v["P50"] is None else round(v["P50"])), "spacing needed, P10 (m)": (None if v["P10"] is None else round(v["P10"]))}
        for q, v in CH["spacing_needed_m"].items()]
display(pd.DataFrame(rows))
print(f"criterion: produced temperature after 30 years ≥ {CH['T_criterion_c']:.1f} °C (no more than 10 % of the initial − reinjection drop); P10 = the low case also meets it")"""),
("md", """**Check of the answer with full runs.** The surrogate's 90 % intervals are too narrow (see the table above), so the answer is checked without it: 12 full proxy runs (new draws of the uncertain inputs) at each spacing the chart gives."""),
("code", """SC = DC["spacing_check"]
rows = [{"rate (kg/s)": int(p["rate_kg_s"]), "spacing (m)": round(p["spacing_m"]), "T year 30, full runs (°C)": pct(p["T30_c"]),
         "share meeting the criterion": f"{p['meets_share']:.0%}", "mean MWth": pct(p["power_mean_mw"]), "pressure ratio": pct(p["dp_ratio_max"])} for p in SC["points"]]
display(pd.DataFrame(rows))"""),
("md", """## 4 · What matters most (Sobol indices)

Total-order Sobol indices through the surrogates, for the three headline outputs. Two fixed designs (only the uncertain rock inputs vary) and one where spacing and rate vary too. Beside them, the rank correlations of the 20-member FORGE ensemble (too few members for Sobol on the full model)."""),
("code", """SB = DC["sobol"]["outputs"]
rows = []
for out, d in SB.items():
    for case, s in d.items():
        rows.append({"output": out, "case": case, "ranking (total order)": " > ".join(s["ranking"]),
                     **{f"ST {k}": round(v["ST"], 2) for k, v in s["indices"].items()}})
display(pd.DataFrame(rows))
fig, ax = plt.subplots(1, 3, figsize=(13, 3.8), sharey=True)
names = ["spacing_m", "rate_kg_s", "slab_m", "sigma_lnk", "corr_m", "lam"]
for a_, (out, d) in zip(ax, SB.items()):
    s = d["design_and_uncertainty"]["indices"]
    st = [s[n]["ST"] for n in names]; err = np.array([[s[n]["ST"] - s[n]["ST_ci"][0], s[n]["ST_ci"][1] - s[n]["ST"]] for n in names]).T
    a_.barh(names, st, xerr=np.clip(err, 0, None), color=GOLD); a_.set_title(out); a_.set_xlabel("total-order Sobol index")
ax[0].invert_yaxis(); fig.suptitle("What drives the 30-year outputs (surrogate)", y=1.03, fontweight="bold")
fig.savefig("figures/forge_sobol.png")
sp = E["spearman"]
display(pd.DataFrame({o: {i: round(v["rho"], 2) for i, v in d.items()} for o, d in sp.items()}))"""),
("md", """## Published numbers"""),
("code", """now = {}
for q in ("5", "10", "20"):
    for k in ("T_prod_end_c", "power_initial_mw", "power_end_mw", "breakthrough_years"):
        for p in ("P10", "P50", "P90"):
            now[f"bb_{q}_{k}_{p}"] = R[q][k][p]
for q, v in CH["spacing_needed_m"].items():
    now[f"spacing_needed_{q}_P50"] = v["P50"]; now[f"spacing_needed_{q}_P10"] = v["P10"]
for k, v in DC["surrogate_validation"].items():
    now[f"rmse_{k}"] = v["held_out"]["gp"]["rmse"]; now[f"r2_{k}"] = v["held_out"]["gp"]["r2"]
for p in DC["spacing_check"]["points"]:
    now[f"check_{int(p['rate_kg_s'])}_T30_P50"] = p["T30_c"]["P50"]; now[f"check_{int(p['rate_kg_s'])}_T30_P10"] = p["T30_c"]["P10"]
for out, d in SB.items():
    now[f"top_{out}"] = d["design_and_uncertainty"]["ranking"][0]
    now[f"top_forge_{out}"] = d["forge_spacing_96m_10kgs"]["ranking"][0]
check(now, "nb5")"""),
("md", """## The plain answer

SUMMARY_NB5

*References:* Rasmussen, C. E. and Williams, C. K. I. (2006). Gaussian Processes for Machine Learning. MIT Press · Saltelli, A. et al. (2010). Variance based sensitivity analysis of model output. Comput. Phys. Commun. 181 · Gringarten, A. C. and Sauty, J. P. (1975). A theoretical study of heat extraction from aquifers with uniform regional flow. J. Geophys. Res. 80."""),
])


if __name__ == "__main__":
    pub_path = pathlib.Path("results/published_phase4.json")
    pub = json.loads(pub_path.read_text()) if pub_path.exists() else {}
    for name, book, key in (("04_upscaling_check.ipynb", nb4, "nb4"), ("04b_wellbore_tracers.ipynb", nb4b, "nb4b"), ("05_decision_chart.ipynb", nb5, "nb5")):
        for c in book.cells:
            c.source = c.source.replace(f"SUMMARY_{key.upper()}", pub.get(f"summary_{key}", ""))
        nbf.write(book, name)
        print("wrote", name)
