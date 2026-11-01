"""Make the synthetic practice boreholes (KAI Academy).

    python make_practice_data.py        # writes data/practice_boreholes.csv and data/practice_logs.csv

Every value is invented. The table has the shape of a national borehole register (one row per borehole, plus a
drilling log of layers with the driller's own words) so learners can practise on the format they will meet at work,
without anyone's real records. The rock model behind it is a weathered crystalline basement, as in much of East
Africa: soil, a cover of clay or laterite, a weathered and fractured zone (the aquifer), then fresh rock.

The overall statistics are chosen to look like published summaries for weathered basement (median drilled depth
about 65 m, depth to bedrock about 27 m, water level about 10 m below ground, yield about 1.5 m³/h), but no record,
place or coordinate comes from any real database. The practice area, its "districts" and the grid are fictional.
Same seed, same files.
"""
from pathlib import Path

import numpy as np
import pandas as pd

SEED = 20261101
N = 600
rng = np.random.default_rng(SEED)
OUT = Path(__file__).parent / "data"


def field(x, y, scale_m, n_waves=24):
    """A smooth random field (sum of random cosines), mean 0, sd about 1."""
    k = rng.normal(0, 2 * np.pi / scale_m, size=(n_waves, 2))
    ph = rng.uniform(0, 2 * np.pi, n_waves)
    return np.sqrt(2 / n_waves) * np.cos(np.outer(x, k[:, 0]) + np.outer(y, k[:, 1]) + ph).sum(axis=1)


# A fictional 40 × 30 km practice area on a local grid (metres), split into two made-up districts
x = rng.uniform(0, 40_000, N)
y = rng.uniform(0, 30_000, N)
district = np.where(x < 22_000, "Practice West", "Practice East")
ground = 1080 + 40 * field(x, y, 15_000) + 0.0015 * x            # m above sea level

# Regolith (cover + weathered zone) thickness: smooth, log-normal, median about 27 m
regolith = np.exp(np.log(27) + 0.45 * field(x, y, 6_000) + 0.25 * rng.normal(size=N)).clip(4, 95)
cover = (regolith * rng.uniform(0.15, 0.45, N)).clip(1.5, None)   # soil + clay/laterite on top of the weathered zone
swl = (np.exp(np.log(10.5) + 0.5 * field(x, y, 8_000) + 0.3 * rng.normal(size=N))).clip(0.5, 60)
drilled = (regolith + rng.gamma(4, 9, N)).clip(25, 150)            # drillers go some way into fresh rock

# Yield grows with the saturated weathered thickness; some holes hit a productive fracture in fresh rock
sat = np.clip(regolith - np.maximum(swl, cover), 0, None)
yld = np.exp(np.log(0.75) + 0.04 * sat + 0.6 * rng.normal(size=N))
yld += np.where(rng.uniform(size=N) < 0.12, rng.gamma(2, 1.5, N), 0)
yld = yld.round(2)

# The register's depth to bedrock is written separately from the log: usually close, sometimes not
bedrock_recorded = regolith + rng.normal(0, 1.2, N)
bad = rng.uniform(size=N) < 0.06
bedrock_recorded[bad] += rng.choice([-1, 1], bad.sum()) * rng.uniform(5, 20, bad.sum())
bedrock_recorded = bedrock_recorded.clip(2, None)

year = rng.integers(1988, 2025, N)
ids = [f"PRAC-{i:04d}" for i in range(1, N + 1)]

# Real registers have gaps and slips: blank fields, a few feet-for-metres, a few swapped digits
def holes(a, share):
    a = a.astype(float).round(1)
    a[rng.uniform(size=N) < share] = np.nan
    return a

boreholes = pd.DataFrame({
    "SourceID": ids,
    "District": district,
    "Easting_m": x.round(0).astype(int),
    "Northing_m": y.round(0).astype(int),
    "GroundLevel_masl": ground.round(1),
    "YearDrilled": year,
    "TotalDrilledDepth": drilled.round(1),
    "DepthToBedRock": holes(bedrock_recorded, 0.14),
    "StaticWaterLevel": holes(swl, 0.10),
    "ConstantDischargeYield": holes(yld, 0.22),
    "Synthetic": True,
})
slip = rng.choice(N, 6, replace=False)                             # recorded in feet by mistake
boreholes.loc[slip, "StaticWaterLevel"] = (boreholes.loc[slip, "StaticWaterLevel"] * 3.281).round(1)

# Drilling logs in the driller's words, with the usual spelling and wording variety
SOIL = ["Top soil", "Topsoil, dark brown", "Black cotton soil", "Red brown sandy soil", "top soil (loamy)"]
COVER = ["Lateritic clay", "Laterite, reddish", "Murram", "Red clay", "Sandy clay, brown", "Hard laterite crust",
         "Clayey murram", "Laterite & clay"]
WEATH = ["Weathered granite", "Highly weathered gneiss", "Wthd rock, grey", "Decomposed granite (saprolite)",
         "Weathered granite gneiss, fractured", "Fractured gneiss - water strike", "Saprolite, sandy",
         "Partly weathered rock", "Weathered & fractured granite W.S."]
FRESH = ["Fresh granite", "Hard grey gneiss", "Fresh rock", "Granite gneiss, hard", "Fresh grey granite, massive",
         "Hard rock (fresh)"]

rows = []
for i in range(N):
    soil_b = round(float(rng.uniform(0.3, 1.5)), 1)
    cov_b = round(float(max(cover[i], soil_b + 0.5)), 1)
    reg_b = round(float(max(regolith[i], cov_b + 1)), 1)
    tot = round(float(max(drilled[i], reg_b + 2)), 1)
    layers = [(0.0, soil_b, rng.choice(SOIL)), (soil_b, cov_b, rng.choice(COVER))]
    # the weathered zone is often logged as two or three layers
    cuts = np.sort(rng.uniform(cov_b, reg_b, rng.integers(0, 3))).round(1)
    tops = [cov_b, *cuts]
    bots = [*cuts, reg_b]
    layers += [(t, b, rng.choice(WEATH)) for t, b in zip(tops, bots) if b - t >= 0.5]
    layers.append((reg_b, tot, rng.choice(FRESH)))
    for t, b, d in layers:
        rows.append({"SourceID": ids[i], "From_m": t, "To_m": b, "Description": d})
logs = pd.DataFrame(rows)

# About 1 in 12 boreholes has no log at all, as in real registers
nolog = rng.choice(ids, N // 12, replace=False)
logs = logs[~logs.SourceID.isin(nolog)]

OUT.mkdir(exist_ok=True)
boreholes.to_csv(OUT / "practice_boreholes.csv", index=False, lineterminator="\n")
logs.to_csv(OUT / "practice_logs.csv", index=False, lineterminator="\n")
print(f"{len(boreholes)} boreholes, {len(logs)} log layers")
print(boreholes[["TotalDrilledDepth", "DepthToBedRock", "StaticWaterLevel", "ConstantDischargeYield"]].median().round(2))
