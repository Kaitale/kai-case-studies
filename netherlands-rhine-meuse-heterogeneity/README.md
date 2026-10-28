# Rhine–Meuse delta: facies between boreholes, tested blind against GeoTOP

**KAI-Subsurface and KAI-GeoEnergy · data behind the [KAI Heterogeneity Lab](https://kai-water.charkaks0.workers.dev/heterogeneity-lab).**

An 8 × 6 km block of the Holocene Rhine–Meuse delta (Alblasserwaard, RD x 122–130 km, y 427–433 km),
2.25 to 9.25 m below NAP: river channel sands in clay and peat, a modern analogue for fluvial reservoirs.

| Source | What is used | Where it comes from |
|---|---|---|
| BRO geological borehole descriptions (BHR-G) | 108 boreholes (one per 100 m cell), NEN 5104 soil names sampled to 0.5 m | `publiek.broservices.nl/sr/bhrg/v3` |
| GeoTOP v1.6.1 (TNO Geological Survey of the Netherlands) | most likely lithoclass and lithoclass probabilities, 100 × 100 × 0.5 m voxels | `www.dinodata.nl/opendap/GeoTOP/geotop.nc` (OPeNDAP) |

Three facies, following GeoTOP's lithoclasses: **clay and peat** (GeoTOP 0–2; NEN *klei*, *veen*),
**heterolithic** (GeoTOP 3, clayey sand, sandy clay and loam; NEN *kleiig zand*, *zandige klei*, *leem*) and
**sand** (GeoTOP 5–9; NEN *zand*, *grind*).

## Reproduce

```bash
python tiles.py        # BHR-G borehole list for the central delta (5 km tiles; the service caps a query at 2,000)
python fetch_bro.py    # borehole XML for the block (cached in data/bhrg/, not committed)
python build_case.py   # GeoTOP subset + borehole logs -> rhine_meuse_block.json (used by the lab)
```

No raw data are stored in this repository; the scripts fetch them from the official services.

## First results (25 % of boreholes hidden)

* The from-logs ensemble names the right facies in **73 %** of hidden half-metre intervals and finds 48 % of the hidden sand; a simple nearest-borehole correlation finds 25 %.
* GeoTOP's most likely class agrees with the boreholes in **68 %** of described voxels. GeoTOP was built from DINO boreholes that may include these, so its blind score (70 %) is flattering.
* The boreholes describe less sand (15 %) and heterolithic (9 %) than GeoTOP holds (24 %, 24 %). The boreholes cluster along dikes and infrastructure; the gap is worth settling before any decision.

Data: Basisregistratie Ondergrond (BRO); GeoTOP, TNO Geological Survey of the Netherlands. Code MIT.
