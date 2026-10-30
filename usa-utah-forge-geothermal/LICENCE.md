# Licence and credits

| What | Licence |
|---|---|
| Code (`*.py`, the notebooks' code cells) | MIT, © 2026 KAI Water & Energy (see the repository's `LICENSE`) |
| Figures, result files (`figures/`, `results/`), text | CC BY 4.0, © 2026 KAI Water & Energy. Model results are simulated by the KAI Reservoir Lab engine (not open source); the notebooks check them against the data |
| Derived data (`data/`) | CC BY 4.0, derived from Utah FORGE data (credit below) |

CC BY 4.0: https://creativecommons.org/licenses/by/4.0/

## Sources (credit when you reuse the data)

**Utah FORGE, U.S. Department of Energy, via the Geothermal Data Repository (OpenEI), CC BY 4.0.**

| GDR submission | Title | DOI | Licence | Used for |
|---|---|---|---|---|
| [1205](https://gdr.openei.org/submissions/1205) | Utah FORGE: Data for 3-D Model Development - Lithology, Temperature, Pressure, and Stress (Podgorney, 2020) | [10.15121/1605155](https://doi.org/10.15121/1605155) | CC BY 4.0 | lithology, temperature, pressure, depth, stress formulas |
| [1101](https://gdr.openei.org/submissions/1101) | Utah FORGE: Milford Deep Test Well 58-32 (MU-ESW1) Pressure and Temperature Logs | [10.15121/1493769](https://doi.org/10.15121/1493769) | CC BY 4.0 | 58-32 temperature log, 8 Nov 2018 |
| [1358](https://gdr.openei.org/submissions/1358) | Utah FORGE: Updated Well, Well Pad, and Seismic Station GPS Coordinates December, 2021 | — | CC BY 4.0 | well-head coordinates |
| [1299](https://gdr.openei.org/submissions/1299) | Utah FORGE: Well 58-32 (MU-ESW1) FMI Log Fracture Results (Blochowicz, 2021) | — | CC BY 4.0 | fracture density and apertures (notebook 2) |
| [1646](https://gdr.openei.org/submissions/1646) | Utah FORGE: 2024 Discrete Fracture Network Model Data (Finnila and Jones, 2024) | [10.15121/2440870](https://doi.org/10.15121/2440870) | CC BY 4.0 | well trajectories, natural-fracture orientations and sizes, stimulated DFN (notebooks 2, 3) |
| [1683](https://gdr.openei.org/submissions/1683) | Utah FORGE: Wells 16A(78)-32 and 16B(78)-32 Extended Circulation Test Data, Aug–Sep 2024 (McLennan, England and Swearingen, 2024) | [10.15121/2475065](https://doi.org/10.15121/2475065) | CC BY 4.0 | calibration and validation (notebook 3) |
| [1611](https://gdr.openei.org/submissions/1611) | Utah FORGE: Wells 16A(78)-32 and 16B(78)-32 Stimulation Pressure and Circulation Data, April 2024 | [10.15121/2371032](https://doi.org/10.15121/2371032) | CC BY 4.0 | validation (notebook 3) |
| [1701](https://gdr.openei.org/submissions/1701) | Utah FORGE: QuantumPro Well 16A(78)-32 and 16B(78)-32 Stimulation and Circulation Tracer Test Results - 2024 (Guo, Oliver and Shokanov, 2024) | [10.15121/2507443](https://doi.org/10.15121/2507443) | CC BY 4.0 | tracer injection times and concentrations at 16B (notebook 4) |
| [1721](https://gdr.openei.org/submissions/1721) | Utah FORGE: Well 16B(78)-32 DTS, RFS DSS Strain, and Absolute Strain Circulation Test Fiber Optic Data - August 2024 (Neubrex) | — | CC BY 4.0 | the two DTS files only (notebook 4); the strain files are not used |
| [1570](https://gdr.openei.org/submissions/1570) | Utah FORGE 2439: Well 16B(78)-32 Field-Test Data from Mini-Frac Tests (Kelley, Skopec, Mawalkar, Raziperchikolaee and Barrios, Battelle, 2023) | — | CC BY 4.0 | `Baker Hughes Minifrac.zip` only (interval pressure and rate); ISIPs derived here (notebook 6). The 2.7 GB log archive is not used |
| [1596](https://gdr.openei.org/submissions/1596) | Utah FORGE 2439: Report on Minifrac Tests for Stress Characterization (Battelle) | — | CC BY 4.0 | two numbers quoted (the MF-2 ISIPs and the cooling adjustment of +0.2 to +0.34 psi/ft); no file used in code |
| [1608](https://gdr.openei.org/submissions/1608) | Utah FORGE: Well 16B(78)-32 Pressure-Temperature Logs March - April 2024 (McLennan and Baker Hughes, 2024) | [10.15121/2368548](https://doi.org/10.15121/2368548) | CC BY 4.0 | the gauge at 7,056.67 ft MD, hourly medians (notebook 6) |
| [1421](https://gdr.openei.org/submissions/1421) | Utah FORGE: Deep Wells Temperature Surveys as of September 2022 | — | CC BY 4.0 | the 16A(78)-32 temperature log of 16 Aug 2021, 5 m medians (notebook 6) |
| [1222](https://gdr.openei.org/submissions/1222) | Utah FORGE: Discrete Fracture Network (DFN) Data (Finnila and Podgorney, 2020) | — | CC BY 4.0 | stress summary only (SHmax direction and range, Shmin gradient), quoted; no file used |

Only derived values are published here (`data/`); the GDR files are not redistributed. `rebuild_data.py` downloads them
and checks their SHA-256 (listed in `forge_tools.py` and the repository's `DATA.md`). The licence of each submission was
read from its GDR page on 30 October 2026.

KAI Water & Energy is not affiliated with Utah FORGE, the University of Utah or the U.S. Department of Energy. The
analysis and any errors are KAI's.
