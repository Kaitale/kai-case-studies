"""Build the two KAI Academy practice notebooks (run, then execute with .github/run_notebooks.py or Jupyter)."""
from pathlib import Path

import nbformat as nbf

HERE = Path(__file__).parent


def nb(cells):
    n = nbf.v4.new_notebook()
    n.metadata["kernelspec"] = {"name": "python3", "display_name": "Python 3", "language": "python"}
    n.cells = [nbf.v4.new_markdown_cell(c[3:]) if c.startswith("md:") else nbf.v4.new_code_cell(c) for c in cells]
    return n


LOGS = [
"""md:# Reading drilling logs: from the driller's words to a depth to bedrock

**KAI Academy · practice notebook 1.** You will load a borehole register and its drilling logs, find the errors that
every real register has, turn the driller's descriptions into three classes (cover, weathered rock, fresh rock), and
check the log against the recorded depth to bedrock. Then you will do the same on **real, openly licensed records**
from British Columbia, Canada, where the rock is glacial sand, gravel and clay instead of weathered basement.

* **Part A, synthetic register.** `data/practice_boreholes.csv` and `data/practice_logs.csv` are **invented**
  (`make_practice_data.py`, fixed seed). They have the shape of a national borehole register in weathered
  crystalline basement, as in much of East Africa, but no record, place or coordinate is real.
* **Part B, real records.** `data/langley_wells.csv.gz` and `data/langley_lithology.csv.gz`: 4,288 water-supply wells
  in the Township of Langley from GWELLS, Province of British Columbia, under the Open Government Licence – British
  Columbia (see `DATA.md`).""",
"""import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

b = pd.read_csv("data/practice_boreholes.csv")
logs = pd.read_csv("data/practice_logs.csv")
print(len(b), "boreholes,", len(logs), "log layers,", logs.SourceID.nunique(), "boreholes with a log")
b.head()""",
"""md:## A1. Check the register before you trust it

Three checks every time: what is missing, what is impossible, and what is in the wrong unit. A water level deeper than
the hole was drilled is impossible; a water level several times the area's typical value may be in feet.""",
"""cols = ["TotalDrilledDepth", "DepthToBedRock", "StaticWaterLevel", "ConstantDischargeYield"]
print("missing (share):")
print(b[cols].isna().mean().round(2))
impossible = b[b.StaticWaterLevel > b.TotalDrilledDepth]
med = b.StaticWaterLevel.median()
suspect_feet = b[(b.StaticWaterLevel > 3 * med) & ~b.index.isin(impossible.index)]
print(f"\\nwater level deeper than the hole: {len(impossible)}")
print(f"water level more than 3x the median ({med:.1f} m), possibly feet: {len(suspect_feet)}")
suspect_feet[["SourceID", "StaticWaterLevel", "TotalDrilledDepth"]].head(10)""",
"""md:Do not delete suspect rows silently. Flag them, report how many, and test whether your answer changes without them.""",
"""b["swl_flag"] = b.index.isin(impossible.index) | b.index.isin(suspect_feet.index)
ok = b[~b.swl_flag]
print(f"median water level: all {b.StaticWaterLevel.median():.1f} m, flagged removed {ok.StaticWaterLevel.median():.1f} m")""",
"""md:## A2. Class the driller's words

Drillers write what they see, in their own words: *murram*, *laterite & clay*, *wthd rock, grey*, *fresh granite*.
A short list of keywords, checked in order, turns them into three classes. Always print what was **not** classed:
that list tells you which keyword is missing.""",
"""RULES = [  # checked in order: the first match wins
    ("fresh rock", ["fresh", "hard rock", "massive", "hard grey", "granite gneiss, hard"]),
    ("weathered rock", ["weather", "wthd", "decomposed", "saprolite", "fractur"]),
    ("cover", ["soil", "clay", "laterite", "murram"]),
]

def classify(text):
    t = str(text).lower()
    for cls, words in RULES:
        if any(w in t for w in words):
            return cls
    return "not classed"

logs["class"] = logs.Description.map(classify)
print(logs["class"].value_counts())
print("\\nnot classed:", sorted(logs.loc[logs["class"] == "not classed", "Description"].unique()))""",
"""md:## A3. Depth to bedrock from the log, against the recorded value

The top of the first *fresh rock* layer is the log's depth to bedrock. Compare it with the register's
`DepthToBedRock`. Where they disagree, one of them is wrong, and it is worth knowing which before you map either.""",
"""top_fresh = logs[logs["class"] == "fresh rock"].groupby("SourceID").From_m.min().rename("bedrock_from_log")
cmp = b.set_index("SourceID").join(top_fresh, how="inner").dropna(subset=["DepthToBedRock"])
d = cmp.bedrock_from_log - cmp.DepthToBedRock
print(f"{len(cmp)} boreholes with both; median difference {d.median():+.2f} m; within 1 m: {(d.abs() <= 1).mean():.0%}")
fig, ax = plt.subplots(figsize=(4.5, 4.5))
ax.scatter(cmp.DepthToBedRock, cmp.bedrock_from_log, s=8, alpha=0.6)
ax.plot([0, 100], [0, 100], color="grey", lw=1)
ax.set_xlabel("Depth to bedrock in the register (m)"); ax.set_ylabel("Top of fresh rock in the log (m)")
ax.set_title("Two records of the same thing"); plt.show()""",
"""md:## A4. Where is the aquifer thick, and does it pay?

In weathered basement the water sits in the weathered and fractured zone. Its saturated thickness (from the water
level down to bedrock) is the first thing to map before siting a borehole.""",
"""ok = b[~b.swl_flag].dropna(subset=["DepthToBedRock", "StaticWaterLevel"]).copy()
ok["saturated_m"] = (ok.DepthToBedRock - ok.StaticWaterLevel).clip(lower=0)
fig, axs = plt.subplots(1, 2, figsize=(11, 4.2))
sc = axs[0].scatter(ok.Easting_m / 1000, ok.Northing_m / 1000, c=ok.saturated_m, s=12, cmap="viridis")
plt.colorbar(sc, ax=axs[0], label="saturated weathered zone (m)")
axs[0].set_xlabel("Easting (km, practice grid)"); axs[0].set_ylabel("Northing (km)"); axs[0].set_aspect("equal")
y = ok.dropna(subset=["ConstantDischargeYield"])
axs[1].scatter(y.saturated_m, y.ConstantDischargeYield, s=8, alpha=0.6)
axs[1].set_yscale("log"); axs[1].axhline(0.5, color="tab:red", lw=1, ls="--")
axs[1].set_xlabel("saturated weathered zone (m)"); axs[1].set_ylabel("yield (m³/h)")
plt.tight_layout(); plt.show()
bins = pd.cut(y.saturated_m, [0, 5, 10, 20, 40, 100])
print((y.ConstantDischargeYield >= 0.5).groupby(bins, observed=True).agg(["mean", "size"]).rename(columns={"mean": "share ≥ 0.5 m³/h"}).round(2))""",
"""md:**Your turn.** (1) Add the keyword your class list missed and rerun A2. (2) Repeat A4 for a motorised pump target
of 3 m³/h: how does the success rate change with saturated thickness? (3) Which district would you survey first?""",
"""md:## B. The same steps on real records: Langley, British Columbia

Real wells, real drillers' words, real gaps. The geology is different (glacial and glaciomarine sand, gravel, clay and
till over deep bedrock), so the classes are different: **aquifer** (sand, gravel) and **aquitard** (clay, silt,
till). Everything else carries over.""",
"""w = pd.read_csv("data/langley_wells.csv.gz")
lith = pd.read_csv("data/langley_lithology.csv.gz")
print(len(w), "wells,", len(lith), "layers")
print(w[["depth_m", "swl_m", "yield_m3h", "bedrock_m"]].describe().round(1))""",
"""GL_RULES = [
    ("aquitard", ["clay", "silt", "till", "hardpan", "mud"]),
    ("aquifer", ["sand", "gravel", "w.b.", "water bearing"]),
    ("bedrock", ["bedrock", "sandstone", "shale", "rock"]),
]

def gclass(text):
    t = str(text).lower()
    for cls, words in GL_RULES:
        if any(x in t for x in words):
            return cls
    return "not classed"

lith["class"] = lith.description.map(gclass)
print(lith["class"].value_counts())
print("\\nmost common unclassed words:", lith.loc[lith["class"] == "not classed", "description"].str.lower().value_counts().head(8).to_dict())""",
"""md:**Your turn.** The unclassed list is mostly *top soil*, *fill* and *dirt*. Add a `cover` class for them and rerun.

Note the order of the rules: *"sand and clay"* is classed as aquitard because clay is checked first. Change the
order and see how many layers move. In a real study you would write that choice down.""",
"""thick = (lith.assign(t=lith.bottom_m - lith.top_m)
         .pivot_table(index="well_id", columns="class", values="t", aggfunc="sum", fill_value=0))
ww = w.set_index("well_id").join(thick, how="inner")
ww["sand_share"] = ww.get("aquifer", 0) / (ww.get("aquifer", 0) + ww.get("aquitard", 0)).replace(0, np.nan)
yy = ww.dropna(subset=["yield_m3h", "sand_share"])
bins = pd.cut(yy.sand_share, [0, 0.2, 0.4, 0.6, 0.8, 1.0], include_lowest=True)
print((yy.yield_m3h >= 0.5).groupby(bins, observed=True).agg(["mean", "size"]).rename(columns={"mean": "share ≥ 0.5 m³/h"}).round(2))
fig, ax = plt.subplots(figsize=(6, 5))
sc = ax.scatter(ww.lon, ww.lat, c=ww.sand_share, s=4, cmap="YlOrBr")
plt.colorbar(sc, label="share of logged thickness that is sand or gravel")
ax.set_title("Langley wells (GWELLS, OGL-BC)"); ax.set_xlabel("longitude"); ax.set_ylabel("latitude"); plt.show()""",
"""md:## What to take away

* Check the register first: gaps, impossible values, units.
* Class the driller's words with rules you can read and print what they miss.
* Compare two records of the same thing before mapping either.
* The method carries over from basement to glacial sediments; the classes and the skill do not, so test again on
  local records. KAI's drilling-odds lab runs that blind test on these Langley wells:
  [Heterogeneity Lab](https://kai-water.charkaks0.workers.dev/drilling-lab).

*Part A is synthetic practice data. Part B: GWELLS, Province of British Columbia, Open Government Licence – British
Columbia. Ground elevations from the Copernicus DEM GLO-30 (© DLR e.V. 2010–2014 and © Airbus Defence and Space GmbH
2014–2018, provided under COPERNICUS by the European Union and ESA).*""",
]

WATERPOINTS = [
"""md:# Water points in Nakasongola and Luwero: what works, and for how long?

**KAI Academy · practice notebook 2.** Real, open data from Uganda: the Water Point Data Exchange (WPDx) records for
Nakasongola and Luwero districts, most of them reported by the Ministry of Water and Environment, published under
**CC BY 4.0** (see `DATA.md`). You will clean the status labels, compare technologies, look at age, and map
non-functional points, and you will learn why a status can be years old.""",
"""import pandas as pd
import matplotlib.pyplot as plt

wp = pd.read_csv("data/uganda_waterpoints_nakasongola_luwero.csv", parse_dates=["report_date"])
print(len(wp), "water points")
print(wp.source.value_counts())
wp.head()""",
"""md:## 1. How old is each status?

A water point's status is only as fresh as its last visit. Before counting, look at when each was last reported.""",
"""wp["report_year"] = wp.report_date.dt.year
print(wp.report_year.value_counts().sort_index())
wp["functional"] = wp.status_clean.str.startswith("Functional") & ~wp.status_clean.str.contains("not in use")""",
"""md:## 2. Functionality by technology, and by reporting year""",
"""t = wp.groupby("water_tech_clean").functional.agg(["mean", "size"]).sort_values("size", ascending=False)
print(t.rename(columns={"mean": "share functional"}).round(2))
by_year = wp.groupby("report_year").functional.agg(["mean", "size"])
print(by_year.rename(columns={"mean": "share functional"}).round(2))""",
"""print(pd.crosstab([wp.source, wp.water_tech_clean], wp.functional, margins=True))""",
"""md:The share functional depends strongly on **when** the points were surveyed and **who** surveyed them: here every
India Mark hand pump and motorised pump comes from NGO surveys that recorded all of them as non-functional, while the
Ministry records (mostly 2010) cover the Afridev pumps, tapstands and kiosks. So the technology table above says more
about who surveyed than about the pumps. Compare like with like.""",
"""md:## 3. Age at report""",
"""wp["age_at_report"] = wp.report_year - wp.install_year
a = wp[(wp.age_at_report >= 0) & (wp.age_at_report <= 50)]
bins = pd.cut(a.age_at_report, [0, 2, 5, 10, 20, 50], include_lowest=True)
print(a.functional.groupby(bins, observed=True).agg(["mean", "size"]).rename(columns={"mean": "share functional"}).round(2))""",
"""md:## 4. Map""",
"""fig, ax = plt.subplots(figsize=(6.5, 6.5))
for f, c, lab in [(True, "tab:blue", "functional"), (False, "tab:red", "not functional")]:
    s = wp[wp.functional == f]
    ax.scatter(s.lon_deg, s.lat_deg, s=6, c=c, label=f"{lab} ({len(s)})", alpha=0.7)
ax.set_aspect("equal"); ax.legend(); ax.set_xlabel("longitude"); ax.set_ylabel("latitude")
ax.set_title("WPDx water points, Nakasongola and Luwero (CC BY 4.0)"); plt.show()""",
"""md:**Your turn.** (1) Which sub-county (`clean_adm3`) has the most non-functional hand pumps reported since 2020?
(2) Repeat section 2 using only Ministry records, then only the others. (3) What would you need to know before using
this map to plan repairs?

*Data: Water Point Data Exchange (WPDx), records as published for Uganda, mainly from the Ministry of Water and
Environment, Uganda; licensed CC BY 4.0. Extract of 1 November 2026.*""",
]

nbf.write(nb(LOGS), HERE / "01_reading_drilling_logs.ipynb")
nbf.write(nb(WATERPOINTS), HERE / "02_water_points_uganda.ipynb")
print("wrote 2 notebooks")
