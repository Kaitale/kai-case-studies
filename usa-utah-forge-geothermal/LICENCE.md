# Licence and credits

| What | Licence |
|---|---|
| Code (`*.py`, the notebooks' code cells) | MIT, © 2026 KAI Water & Energy (see the repository's `LICENSE`) |
| Figures, result files (`figures/`, `results/`), text | CC BY 4.0, © 2026 KAI Water & Energy |
| Derived data (`data/`) | CC BY 4.0, derived from Utah FORGE data (credit below) |

CC BY 4.0: https://creativecommons.org/licenses/by/4.0/

## Sources (credit when you reuse the data)

**Utah FORGE, U.S. Department of Energy, via the Geothermal Data Repository (OpenEI), CC BY 4.0.**

| GDR submission | Title | DOI | Licence | Used for |
|---|---|---|---|---|
| [1205](https://gdr.openei.org/submissions/1205) | Utah FORGE: Data for 3-D Model Development - Lithology, Temperature, Pressure, and Stress (Podgorney, 2020) | [10.15121/1605155](https://doi.org/10.15121/1605155) | CC BY 4.0 | lithology, temperature, pressure, depth, stress formulas |
| [1101](https://gdr.openei.org/submissions/1101) | Utah FORGE: Milford Deep Test Well 58-32 (MU-ESW1) Pressure and Temperature Logs | [10.15121/1493769](https://doi.org/10.15121/1493769) | CC BY 4.0 | 58-32 temperature log, 8 Nov 2018 |
| [1358](https://gdr.openei.org/submissions/1358) | Utah FORGE: Updated Well, Well Pad, and Seismic Station GPS Coordinates December, 2021 | — | CC BY 4.0 | well-head coordinates |

Only derived values are published here (`data/`); the GDR files are not redistributed. `rebuild_data.py` downloads them
and checks their SHA-256 (listed in `forge_tools.py` and the repository's `DATA.md`). The licence of each submission was
read from its GDR page on 30 October 2026.

KAI Water & Energy is not affiliated with Utah FORGE, the University of Utah or the U.S. Department of Energy. The
analysis and any errors are KAI's.
