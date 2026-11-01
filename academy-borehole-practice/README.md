# KAI Academy practice: boreholes and water points

Two practice notebooks for learners: one register you can break things on, and real open records to try the same
steps on. Part of the [KAI Academy](https://kai-water.charkaks0.workers.dev/academy.html).

| Notebook | Data | You will |
|---|---|---|
| [1 · Reading drilling logs](01_reading_drilling_logs.ipynb) | A **synthetic** borehole register in weathered basement (600 boreholes, 2,700 log layers), then **real** GWELLS wells from Langley, British Columbia (4,288 wells, 30,492 layers) | find gaps, impossible values and feet-for-metres slips; class the driller's words into cover, weathered rock and fresh rock; check the log against the recorded depth to bedrock; relate the saturated weathered zone to yield |
| [2 · Water points in Uganda](02_water_points_uganda.ipynb) | **Real** WPDx records for Nakasongola and Luwero (2,050 water points, mostly from the Ministry of Water and Environment), CC BY 4.0 | clean status labels, compare technologies and ages, map non-functional points, and see why who surveyed and when matters |

## Why one synthetic and two real datasets

Real data teach what real data look like. But national borehole registers, with their drilling logs, are rarely
open, and practice data must never be someone's real records. So the register in notebook 1 is **invented**
(`make_practice_data.py`, fixed seed, every row marked `Synthetic = True`): it has the shape and the faults of a real
register, and nothing in it is real. Then the same steps run on **real, openly licensed** wells from British
Columbia, and notebook 2 uses real, open water-point records from Uganda.

## Run

```bash
pip install -r ../requirements.txt
python make_practice_data.py      # optional: rebuilds the synthetic files (same seed, same files)
jupyter lab
```

## Data and licences

See [DATA.md](../DATA.md#kai-academy-practice-boreholes-and-water-points-academy-borehole-practicedata).
GWELLS: Open Government Licence – British Columbia. WPDx: CC BY 4.0. Synthetic register: CC BY 4.0, KAI Water & Energy.
