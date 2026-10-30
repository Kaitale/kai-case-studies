# Utah FORGE: what a geothermal well pair in hot granite will deliver

**KAI-GeoEnergy · KAI Reservoir Lab · tested in the open on public U.S. Department of Energy data.**

Utah FORGE is the U.S. Department of Energy's field laboratory for enhanced geothermal systems (EGS), near Milford,
Utah: hot granitoid under basin fill, deep deviated wells, stimulation and circulation tests. Its data are public on
the DOE Geothermal Data Repository (GDR) under CC BY 4.0. This case builds the site model in the KAI Reservoir Lab and
asks the question a geothermal client pays for: *what will a well pair deliver over 30 years, with an honest P10–P90?*

| Notebook | Question | Key result |
|---|---|---|
| [1 · Structure and temperature](01_structure_and_temperature.ipynb) | Where is the hot granitoid, how hot is it, and does the 3-D temperature model hold at the deep well? | The granitoid lies **533–1,911 m** below ground across the 2.5 × 2.5 km site and **985 m** at well 58-32. The temperature model matches the 2018 log of 58-32 to **1.7 °C** RMSE (bias +1.4 °C; not a blind test). **7.9 km³** of granitoid is hotter than 175 °C inside the model volume |
| [2 · Fractured granite ensemble](02_fractured_granite_ensemble.ipynb) | What do the 58-32 image log and the FORGE fracture models say, and what survives the 2024 circulation test? | The FMI log gives **3.65 fractures/m** (P32 ≈ **11 m²/m³** with the reference-DFN orientations). Taken as in-situ apertures, the FMI apertures make the well pair **72 ×** easier to circulate than measured. Calibrated on the August 2024 test, the stimulated fractures carry about **0.13 ×** (P10–P90 0.06–0.15) the apertures of the 2024 DFN |
| [3 · A well pair over 30 years](03_doublet_30_years.ipynb) | What would 16A(78)-32 / 16B(78)-32 deliver at 10–80 kg/s for 30 years? | Not fitted, the model predicts the August 2024 recovery (**94 %**, P10–P90 91–96 %, measured 93 %) but not the produced temperature (+13 °C after a wellbore estimate) or the April test. Only **10 kg/s** stays pressure-feasible: produced temperature **214 → 130 °C** (P10–P90 116–148) in 30 years, heat **6.4 → 2.9 MWth**, thermal breakthrough after **1.35 ± 0.11 years** (grid-converged, median member; ensemble 0.9–2.6 years on 35 m cells, about 25 % late). *Simulated* |
| [4 · Checks and the upscaling check](04_upscaling_check.ipynb) | Is the temperature misfit in the wellbore? Do the tracers agree? Which rates are feasible with pressure-dependent apertures? Does a coarse model change the answer? | A wellbore model accounts for **13 °C** of the misfit; **+11 °C** (P10–P90 10–13) is left at the bottom hole. Tracers arrive in **4.5–10.5 h**, against minutes in the model: the transport porosity is **23–55 ×** the pressure-fitted one. With Barton–Bandis apertures the highest feasible rate is **9.7 kg/s** (9.3–10.5). On 70 m cells the usual coarse model is **+11 °C** optimistic at 30 years (P10–P90 +3 to +14). KAI global + near-well upscaling, not recalibrated, is **+2 °C** (0 to +5). Early breakthrough is unreliable on 70 m cells either way. *Simulated* |
| [5 · Decision chart](05_decision_chart.ipynb) | This well pair is a test bed, not a power plant: what spacing would a 30-year doublet need? | To keep ≥ 198.6 °C for 30 years: about **320 m** at 10 kg/s (P10 case 470 m), **630 m** at 20 kg/s (780 m), and more than 800 m at 40 kg/s and above. Sobol: rate and spacing first, then the thickness of the stimulated network. *Surrogate of simulated proxy runs*; held-out error 10 °C RMSE |
| [6 · Phase 5 checks](06_phase5_checks.ipynb) | Where is the last +11 °C? Can a coarse model give early breakthrough? What do the 16B mini-frac tests say about Shmin? | The temperature model is **hot at the wells**: +7 °C along a 16A log after 216 days of recovery, about **+8 °C** at the 16B producing zone. Local thermal non-equilibrium explains the rest with flowing sheets **10–20 m** apart (all of the +11 °C would need 21–41 m); it leaves the 30-year temperature unchanged but brings breakthrough into the first months. The 16B mini-frac ISIPs give **0.61 psi/ft**, about **33 MPa** at 16A, below the 40 MPa used so far: the highest feasible rate falls from **9.5 to 5.8 kg/s** (P10–P90 5.3–6.3); with the report's cooling correction it would be 11–17 kg/s. A streamline front correction for coarse models **fails** its stated test (about 40–48 % early), so coarse models still give only the 30-year heat. *Simulated where stated* |

![Depth to the granitoid and a section through 58-32](figures/forge_structure.png)

![The temperature model against the 58-32 log](figures/forge_58_32_check.png)

![Median member against the August 2024 circulation test (simulated vs measured)](figures/forge_validation_2024.png)

![Produced temperature and heat power over 30 years, P10–P90 (simulated)](figures/forge_30_years.png)

![Which rates fit under Shmin, fixed and Barton–Bandis apertures (simulated)](figures/forge_rates_feasible.png)

![The upscaling check: 70 m against 23.3 m, one dot per member (simulated)](figures/forge_upscaling.png)

![Decision chart: spacing × rate against the 30-year temperature (surrogate)](figures/forge_decision_chart.png)

![The temperature model against the 16A log and the 16B gauge](figures/forge_geotherm_check.png)

![Which block size closes the misfit, and the 30-year effect (simulated)](figures/forge_ltne.png)

## Data

All from the GDR, CC BY 4.0 (details and DOIs in [LICENCE.md](LICENCE.md)):

* **3-D model export** (GDR 1205): lithology (granitoid / basin fill) on 137,500 cells of 50 m, and temperature,
  pressure and depth at 145,656 nodes, from Seequent Leapfrog Geothermal.
* **Well 58-32 temperature log**, 8 November 2018 (GDR 1101).
* **Surveyed well heads**, December 2021 (GDR 1358).
* **58-32 FMI fracture picks** (GDR 1299): depth and apertures of 147 fractures.
* **FORGE 2024 discrete fracture network** (GDR 1646, Finnila and Jones): the 16A(78)-32 / 16B(78)-32 trajectories, four
  natural-fracture sets (orientation, size) and the connected DFN of the stimulated reservoir.
* **2024 circulation tests**: the extended test of 8 Aug – 5 Sep 2024 (GDR 1683) and the 9-hour test of 27 April 2024
  (GDR 1611).
* **2024 nanoparticle tracers** (GDR 1701, QuantumPro; DOI 10.15121/2507443): ten tracers injected into 16A during the
  August test and sampled at 16B.
* **16B fibre temperatures** (GDR 1721, Neubrex DTS), 4 August and 12–16 August 2024.
* **16B mini-frac tests**, June–July 2023 (GDR 1570, Battelle with Baker Hughes): interval pressure and rate of seven
  straddle-packer tests at 5,202–5,980 ft. Two numbers are quoted from the interpretation report (GDR 1596).
* **16B pressure-temperature gauge** at 7,056.67 ft MD, 26 March – 20 April 2024 (GDR 1608, DOI 10.15121/2368548).
* **16A(78)-32 temperature log**, 16 August 2021, about 216 days after drilling (GDR 1421 workbook).
* The SHmax direction (N25E, N10E–N40E) and the minimum-stress gradient are quoted from the FORGE stress summary in
  GDR 1222.

`data/` holds only derived values: `forge_model.npz` (granitoid flag, temperature, pressure and depth as float32; the
grid's map transform), `well_58_32_log_2018.csv` (the log every 5 m) and `wells.csv`; for notebooks 2 and 3
`fmi_58_32.csv`, `trajectories_16A_16B.csv` (every 10 m), `natural_fracture_poles.csv`, `stimulated_dfn.csv`,
`circulation_2024_aug_daily.csv` and `circulation_2024_summary.json`; for notebooks 4 and 5
`tracers_2024_circulation.csv`, `dts_16B_2024.csv` and `dts_16B_2024_deep.json`; for notebook 6
`minifrac_16B_2023_isip.csv`, `minifrac_16B_2023_mf2.csv`, `pt_gauge_16B_2024_hourly.csv` and
`temperature_16A_2021.csv`. `rebuild_data.py` downloads the
GDR files into `gdr_cache/`, checks their SHA-256 and rebuilds `data/` byte for byte.

## Method

`forge_tools.py` (MIT) holds the shared functions: the GDR download with checksum, the Leapfrog and LAS readers, the
local-to-UTM fit, the granitoid surface, interpolation along a well and isotherm depths. The KAI engine builds the same
model from the raw files on its own grid (`kai-engine reference forge`); its results are in
`results/kai_engine_results.json`, and notebook 1 stops if the two disagree.

Notebooks 2 and 3 show the KAI engine's fractured-granite runs (`kai-engine reference forge-pair`; results in
`results/kai_engine_phase3.json` and `results/forge_pair_fields.npz`). The fractures are an **equivalent continuum**:
each fracture adds its Oda permeability tensor to the cells it crosses (35 m cells, 1,050 × 630 × 630 m around the open
intervals). Natural fractures come from the FMI density with the reference-DFN orientations and sizes; the stimulated
network is the GDR 1646 connected DFN. Each of 20 ensemble members varies fracture density, natural aperture, set
orientation and the spread of stimulated apertures, and calibrates one factor on the stimulated apertures to the
August 2024 injection pressure. Flow and heat use a two-point-flux solver with flux-limited (TVD) heat advection.
Breakthrough times are checked on three grids (52.5, 35, 23.3 m) and quoted grid-converged with their error.
The notebooks recompute the data-derived numbers with `forge_tools.py` and stop if the engine disagrees or a published
number changes. All model numbers are **simulated**.

Notebooks 4 and 5 show the phase 4 runs (`kai-engine reference forge-phase4`; results in
`results/kai_engine_phase4.json`). They add four things:
* a wellbore model (Hasan–Kabir heat loss, single-phase friction);
* Barton–Bandis apertures on the stimulated fractures;
* a full-tensor option;
* KAI global plus near-well upscaling.

They also add a proxy doublet tied to the FORGE ensemble, a Gaussian-process surrogate with its held-out error, and
Sobol indices. Surrogate values are labelled as such. `make_notebooks_phase4.py` builds the two notebooks.

Notebook 6 shows the phase 5 runs (`kai-engine reference forge-phase5`; results in `results/kai_engine_phase5.json`).
It adds:
* a dual-continuum heat option: in each stimulated cell, the fracture water exchanges heat with nested matrix shells by
  conduction (MINC-like). It is checked against the parallel-fracture solution of Gringarten, Witherspoon and Ohnishi
  (1975). Each run is recalibrated on the August injection pressure;
* streamline (Pollock) thermal time of flight on the fine flux field, tested as a coarse-model front correction against a
  criterion written down before the run;
* ISIPs of the 16B mini-frac tests, derived here, and the feasible rates against the resulting Shmin;
* a check of the temperature model against the 16A 2021 log and the 16B gauge.

`make_notebooks_phase5.py` builds the notebook.

## Limits

* The temperature model is the source's, not a KAI interpretation. 58-32 was used to build it, so the log comparison
  checks consistency, not predictive skill. Its accuracy away from the deep wells is not tested here.
* The stresses are the depth gradients defined in the source workbook, not a stress model.
* 50 m cells place the granitoid contact to ±25 m.
* Phase 3: equivalent continuum with a diagonal permeability per cell; fracture apertures do not change with pressure or
  temperature and no new fractures form, so rates above 10 kg/s are what-if results (not pressure-feasible); no wellbore
  model; single-phase water; one calibration test. See the limits at the end of notebooks 2 and 3.
* Phase 4:
  * Water and rock share one temperature in each cell, which may explain the remaining +11 °C (tested in phase 5).
  * Barton–Bandis uses assumed stiffness and closure, with σn = Shmin. Fractures do not grow, slip or open thermally.
  * The 16B DTS fails an energy-balance check and is not used to fit.
  * The decision chart rests on a proxy that assumes stimulation scales with spacing. Its values are surrogate values,
    with a 10 °C held-out error.
* Phase 5:
  * LTNE uses one block size for all stimulated cells and slab blocks. The block size is fitted to the misfit, not
    measured.
  * The geotherm check rests on one 16A log (216 days of recovery, so possibly still slightly cold) and one 16B gauge
    that was still warming. GDR 1608 is a single gauge, not a log.
  * The mini-frac tests are 550–800 m above 16A's completion; the gradient is carried down unchanged. An ISIP is an
    upper bound of closure. The cooling correction is the report's, not derived here.
  * Coarse-model breakthrough is still not reliable: the streamline correction failed its test. The 23.3 m reference
    is itself not grid-converged.

## What this becomes in KAI

The model is the starting point of the KAI Reservoir Lab's geothermal workflow: a fractured-granite ensemble, a 30-year
well-pair forecast with P10–P90, and an audit of how much coarse models change the answer.

*Credit: Utah FORGE, U.S. Department of Energy, via the Geothermal Data Repository (OpenEI), CC BY 4.0.*
