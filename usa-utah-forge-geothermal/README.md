# Utah FORGE: what a geothermal well pair in hot granite will deliver

**KAI-GeoEnergy · KAI Reservoir Lab · tested in the open on public U.S. Department of Energy data.**

Utah FORGE is the U.S. Department of Energy's field laboratory for enhanced geothermal systems (EGS), near Milford,
Utah: hot granitoid under basin fill, deep deviated wells, stimulation and circulation tests. Its data are public on
the DOE Geothermal Data Repository (GDR) under CC BY 4.0. This case builds the site model in the KAI Reservoir Lab and
asks the question a geothermal client pays for: *what will a well pair deliver over 30 years, with an honest P10–P90?*

| Notebook | Question | Key result |
|---|---|---|
| [1 · Structure and temperature](01_structure_and_temperature.ipynb) | Where is the hot granitoid, how hot is it, and does the 3-D temperature model hold at the deep well? | The granitoid lies **533–1,911 m** below ground across the 2.5 × 2.5 km site and **985 m** at well 58-32. The temperature model matches the 2018 log of 58-32 to **1.7 °C** RMSE (bias +1.4 °C; not a blind test). **7.9 km³** of granitoid is hotter than 175 °C inside the model volume |
| 2 · Fractured granite ensemble | *(next)* matrix plus a fracture network from the 58-32 FMI log, ensembles of fracture density and aperture | — |
| 3 · A well pair over 30 years | *(next)* circulation at 10–80 kg/s: produced temperature, breakthrough, pressure, MWth, with P10–P90; checked against the 2024 circulation tests | — |
| 4 · Upscaling check | *(next)* how much a coarse model changes breakthrough time against the fine fractured model | — |

![Depth to the granitoid and a section through 58-32](figures/forge_structure.png)

![The temperature model against the 58-32 log](figures/forge_58_32_check.png)

## Data

All from the GDR, CC BY 4.0 (details and DOIs in [LICENCE.md](LICENCE.md)):

* **3-D model export** (GDR 1205): lithology (granitoid / basin fill) on 137,500 cells of 50 m, and temperature,
  pressure and depth at 145,656 nodes, from Seequent Leapfrog Geothermal.
* **Well 58-32 temperature log**, 8 November 2018 (GDR 1101).
* **Surveyed well heads**, December 2021 (GDR 1358).

`data/` holds only derived values: `forge_model.npz` (granitoid flag, temperature, pressure and depth as float32; the
grid's map transform), `well_58_32_log_2018.csv` (the log every 5 m) and `wells.csv`. `rebuild_data.py` downloads the
GDR files into `gdr_cache/`, checks their SHA-256 and rebuilds `data/` byte for byte.

## Method

`forge_tools.py` (MIT) holds the shared functions: the GDR download with checksum, the Leapfrog and LAS readers, the
local-to-UTM fit, the granitoid surface, interpolation along a well and isotherm depths. The KAI engine builds the same
model from the raw files on its own grid (`kai-engine reference forge`); its results are in
`results/kai_engine_results.json`, and notebook 1 stops if the two disagree.

## Limits

* The temperature model is the source's, not a KAI interpretation. 58-32 was used to build it, so the log comparison
  checks consistency, not predictive skill. Its accuracy away from the deep wells is not tested here.
* The stresses are the depth gradients defined in the source workbook, not a stress model.
* 50 m cells place the granitoid contact to ±25 m.

## What this becomes in KAI

The model is the starting point of the KAI Reservoir Lab's geothermal workflow: a fractured-granite ensemble, a 30-year
well-pair forecast with P10–P90, and an audit of how much coarse models change the answer.

*Credit: Utah FORGE, U.S. Department of Energy, via the Geothermal Data Repository (OpenEI), CC BY 4.0.*
