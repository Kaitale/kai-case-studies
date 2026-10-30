# Licence and credits

| What | Licence |
|---|---|
| Code (`*.py`, `paper/*.py`, `paper/print.js`, the notebook's code cells) | MIT, © 2026 KAI Water & Energy (see the repository's `LICENSE`) |
| Paper and technical report (`paper/*.pdf`), figures, result files | CC BY 4.0, © 2026 Charles Kakooza |
| Derived data (`data/*.csv`) | CC BY 4.0, © 2026 KAI Water & Energy, with the source credits below |

CC BY 4.0: https://creativecommons.org/licenses/by/4.0/

## Sources (credit when you reuse the data)

* **Gauges.** *Fuente: CEDEX, Anuario de Aforos 2021-2022 (MITECO).* https://ceh-flumen64.cedex.es/anuarioaforos/.
  Only derived values (each water year's largest daily flow; station area and position) are published here. The daily
  CEDEX files are not redistributed; `rebuild_data.py` downloads them and checks their SHA-256.
* **Global model.** GloFAS reanalysis 4.0 (LISFLOOD), Copernicus Emergency Management Service, through the Open-Meteo
  flood API (CC BY 4.0; the free API is for non-commercial use). *Contains modified Copernicus Emergency Management
  Service information 2026.* GloFAS data are provided for information purposes only and are not a flood warning.
* **Rainfall.** NASA POWER daily precipitation (PRECTOTCORR), https://power.larc.nasa.gov. *These data were obtained from
  the NASA Langley Research Center (LaRC) POWER Project funded through the NASA Earth Science/Applied Science Program.*
  Only derived values (catchment rainfall maxima and season totals) are published here.
* **Catchments.** HydroBASINS level 8, WWF / HydroSHEDS (Lehner and Grill, 2013), https://www.hydrosheds.org. Only the
  sub-catchment IDs used for each gauge are published here; `rebuild_rainfall.py` needs the shapefile, downloaded separately.
* **Method comparison.** The four ways of setting a trigger follow Model Library (2026), *Four ways to set a parametric
  trigger, tested on Andalucía rainfall and yields*; their published figures are quoted in the paper.
