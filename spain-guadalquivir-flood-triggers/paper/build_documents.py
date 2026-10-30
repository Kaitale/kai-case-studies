"""Builds the paper and the technical report (HTML, then PDF with Chromium) from the case's result files.

    python paper/build_documents.py            (run from the case folder; needs Playwright with Chromium)

Every number in the text is read from results/ and data/, so the documents follow the analysis.
"""
import base64
import json
import pathlib
import sys

import pandas as pd

HERE = pathlib.Path(__file__).resolve().parent
CASE = HERE.parent
R = CASE / "results"
VERSION, DATE = "2.0", "30 October 2026"
AUTHOR, AFFIL = "Charles Kakooza", "KAI Water &amp; Energy, Kampala, Uganda"
REPO = "https://github.com/Kaitale/kai-case-studies/tree/main/spain-guadalquivir-flood-triggers"
CASE_URL = "https://kai-water.charkaks0.workers.dev/case-guadalquivir"

eng = json.loads((R / "kai_engine_results.json").read_text())
nb = json.loads((R / "nb1_results.json").read_text())
ps = json.loads((R / "paper_stats.json").read_text())
sk = pd.read_csv(R / "skill_scores.csv")
pg = pd.read_csv(R / "per_gauge_1in5.csv")
lv = pd.read_csv(R / "return_levels.csv")
gauges = pd.read_csv(CASE / "data" / "gauges.csv")
am = pd.read_csv(CASE / "data" / "annual_maxima.csv")
S = eng["summary"]
tm = pd.read_csv(R / "trigger_methods.csv")
win = pd.read_csv(R / "rain_windows.csv").set_index("index")
rw = json.loads((R / "rain_vs_river.json").read_text())
rcat = pd.read_csv(CASE / "data" / "rain_catchments.csv")
v45 = json.loads((R / "v4_v5_comparison.json").read_text())
V4M, V5M, V5F = v45["matched_v4"], v45["matched_v5"], v45["full_v5"]
def vk(d, T, m):
    return next(r for r in d["skill"] if r["T"] == T and r["written_as"] == m)
V5R, V5A, V4R, V4A = vk(V5M, 5, "return period"), vk(V5M, 5, "fixed m3/s"), vk(V4M, 5, "return period"), vk(V4M, 5, "fixed m3/s")
V5FR, V5FA = vk(V5F, 5, "return period"), vk(V5F, 5, "fixed m3/s")
assert (V4R["hits"], V4A["hits"]) == (30, 6)  # GloFAS 4.0 on the matched years reproduces the version 1 result
TITLE = "River flow or rainfall, GloFAS 4.0 or 5.0? Writing parametric flood triggers from global data, tested gauge by gauge in the Guadalquivir basin, Spain"
RIV, STORM, SEAS = "River flow (GloFAS)", "Storm rainfall (wettest 3 days)", "Wet-season rainfall (Oct–Apr total)"


def k(T, m):
    return sk[(sk["T"] == T) & (sk.method == m)].iloc[0]


def M(index, method, T=5):
    return tm[(tm["index"] == index) & (tm.method == method) & (tm["T"] == T)].iloc[0]


r5, a5 = k(5, "rp"), k(5, "abs")
P5 = ps["pair"]["5"]
N_GY = len(am)
YRS = (int(pg.years.min()), int(pg.years.max()))
AREA = (int(gauges.catchment_km2.min()), int(gauges.catchment_km2.max()))
WITHIN2 = S["gauges_with_10yr_level_within_x2"]
MEANR = float(gauges.glofas_mean_flow_ratio.median())
RHO_SH = ps["rho_vs_share"]
MR_R10 = ps["meanratio_vs_ratio10"]
AR_R10 = ps["area_vs_ratio10"]
GEV_G = int((pg.fit_g == "GEV").sum())
GEV_M = int((pg.fit_m == "GEV").sum())


rS, rQ = M(SEAS, "Return period"), M(STORM, "Return period")
aR, aS3, aSe = M(RIV, "Absolute value"), M(STORM, "Absolute value"), M(SEAS, "Absolute value")
OWN = tm[(tm["index"] == RIV) & (tm["T"] == 5) & (tm.method != "Absolute value")]
WIN_SHORT = [win.loc[f"rain_max_{n}d_mm", "peirce_1in5"] for n in (1, 3, 5, 10)]
AREA_R = (float(rcat.area_ratio.min()), float(rcat.area_ratio.median()), float(rcat.area_ratio.max()))


def img(name):
    b = (CASE / "figures" / name).read_bytes()
    return "data:image/png;base64," + base64.b64encode(b).decode()


def fig(name, n, caption, width="100%"):
    return f'<figure><img src="{img(name)}" style="width:{width}" alt=""><figcaption><b>Figure {n}.</b> {caption}</figcaption></figure>'


def p_fmt(p):
    p = float(p)
    if p < 0.001:
        e = f"{p:.1e}".split("e")
        return f"{e[0]}&nbsp;×&nbsp;10<sup>{int(e[1])}</sup>"
    return f"{p:.2g}"


CSS = """
html { font-family: 'Liberation Serif', 'Times New Roman', serif; font-size: 10.6pt; line-height: 1.45; color: #111; }
body { margin: 0; }
h1, h2, h3, .meta, figcaption, table, .kicker, .abstract h2, .box h3 { font-family: Inter, 'DejaVu Sans', sans-serif; }
.kicker { font-size: 8pt; letter-spacing: .12em; text-transform: uppercase; color: #1d4ed8; font-weight: 600; margin: 0 0 6px; }
h1 { font-size: 19pt; line-height: 1.18; margin: 0 0 10px; font-weight: 700; letter-spacing: -.01em; }
.meta { font-size: 9pt; color: #333; margin: 0 0 2px; }
.meta b { font-weight: 600; }
h2 { font-size: 12pt; margin: 18px 0 6px; font-weight: 700; }
h3 { font-size: 10.4pt; margin: 12px 0 4px; font-weight: 600; }
p { margin: 0 0 7px; text-align: justify; hyphens: auto; }
.abstract { border-top: 1.5px solid #1d4ed8; border-bottom: 1px solid #c8d3e6; padding: 8px 0 6px; margin: 12px 0 10px; }
.abstract h2 { margin: 0 0 4px; font-size: 9.5pt; text-transform: uppercase; letter-spacing: .08em; color: #1d4ed8; }
.abstract p { font-size: 9.8pt; }
.kw { font-size: 8.8pt; color: #333; font-family: Inter, sans-serif; }
figure { margin: 10px 0 12px; break-inside: avoid; text-align: center; }
figure img { max-width: 100%; }
figcaption { font-size: 8.4pt; color: #333; text-align: left; margin-top: 4px; line-height: 1.4; }
table { border-collapse: collapse; width: 100%; font-size: 7.9pt; margin: 6px 0 4px; break-inside: avoid; }
th, td { white-space: nowrap; padding: 2.6px 4px; border-bottom: 0.5px solid #c9d2dc; text-align: right; font-variant-numeric: tabular-nums; }
th { border-bottom: 1px solid #333; font-weight: 600; vertical-align: bottom; white-space: normal; }
td:first-child, th:first-child { text-align: left; }
tr.sep td { border-top: 1px solid #333; }
.tcap { font-family: Inter, sans-serif; font-size: 8.4pt; color: #333; margin: 10px 0 2px; }
.tnote { font-family: Inter, sans-serif; font-size: 7.6pt; color: #555; margin: 0 0 10px; }
.tblock { break-inside: avoid; }
table.long { break-inside: auto; } table.long tr { break-inside: avoid; } thead { display: table-header-group; }
h2, h3, .tcap { break-after: avoid; }
ol.refs { font-size: 8.6pt; padding-left: 18px; line-height: 1.38; } ol.refs li { margin-bottom: 3px; }
.box { border: 1px solid #c8d3e6; background: #f4f7fc; border-radius: 4px; padding: 8px 11px; margin: 10px 0; break-inside: avoid; }
.box h3 { margin-top: 0; color: #1d4ed8; }
.box ul, .box ol { margin: 4px 0; padding-left: 18px; } .box li { margin-bottom: 3px; }
.small { font-size: 8.8pt; }
.pb { break-before: page; }
.cover-line { height: 4px; background: linear-gradient(90deg, #1d4ed8, #2a78d6 60%, #eda100); margin: 0 0 14px; border-radius: 2px; }
.lic { font-family: Inter, sans-serif; font-size: 7.8pt; color: #555; margin-top: 4px; }
sup { font-size: 70%; }
"""


def table_skill():
    rows = ""
    for T in (2, 5, 10, 25):
        for m, lab in (("rp", "Return period"), ("abs", "Fixed m³/s")):
            x = k(T, m)
            rows += (f'<tr{" class=sep" if m == "rp" and T != 2 else ""}><td>1 in {T}</td><td style="text-align:left">{lab}</td><td>{int(x.hits)}</td><td>{int(x.misses)}</td><td>{int(x.false_payouts)}</td>'
                     f'<td>{x.hit_rate:.2f}</td><td>{x.false_alarm_rate:.3f}</td><td>{x.peirce:.2f}</td><td>{x.chance_hits:.1f}</td><td>{p_fmt(x.p_vs_chance)}</td></tr>')
    return ('<table><thead><tr><th>Trigger</th><th style="text-align:left">Written as</th><th>Caught</th><th>Missed</th><th>False payouts</th><th>Hit rate</th><th>False-alarm rate</th>'
            f'<th>Peirce skill</th><th>Caught by chance</th><th>p (vs chance)</th></tr></thead><tbody>{rows}</tbody></table>')


def table_gauges():
    rows = ""
    for _, r in pg.iterrows():
        rows += (f"<tr><td>{r.gauge}</td><td>{r.area:,}</td><td>{r.years}</td><td>{r.mean_ratio:.2f}</td><td>{r.q10_gauge:.0f} ({r.q10_gauge_band})</td><td>{r.q10_glofas:.0f} ({r.q10_glofas_band})</td>"
                 f"<td>{r.ratio10:.2f}</td><td>{r.rho:.2f}</td><td>{r.floods}</td><td>{r.caught}</td><td>{r.fp}</td></tr>")
    return ('<table><thead><tr><th>Gauge</th><th>Catchment km²</th><th>Years</th><th>Mean-flow ratio</th><th>Q10 gauge, m³/s (90 % band)</th><th>Q10 GloFAS, m³/s (90 % band)</th>'
            f'<th>Q10 ratio</th><th>Rank corr.</th><th>Flood years</th><th>Caught</th><th>False payouts</th></tr></thead><tbody>{rows}</tbody></table>')


def table_methods():
    rows = ""
    for i, ix in enumerate((RIV, STORM, SEAS)):
        for j, m in enumerate(("Absolute value", "Quantile", "Return period", "Share of a reference")):
            x = M(ix, m)
            lab = ix if j == 0 else ""
            lvl = "" if pd.isna(x.common_level) else (f"{x.common_level:.1f} m³/s per 1,000 km²" if ix == RIV else f"{x.common_level:.0f} mm") if m == "Absolute value" else f"{x.common_level:.2f} × mean"
            rows += (f'<tr{" class=sep" if j == 0 and i else ""}><td>{lab}</td><td style="text-align:left">{m}</td><td style="text-align:left">{lvl}</td>'
                     f'<td>{x.paid_share_min:.0%}–{x.paid_share_max:.0%}</td><td>{int(x.hits)}</td><td>{int(x.false_payouts)}</td><td>{x.false_payout_share:.0%}</td>'
                     f'<td>{x.peirce:.2f}</td><td>{p_fmt(x.p_vs_chance)}</td></tr>')
    for lab, key in (("River and wet-season rainfall both pass", "both"), ("Either passes", "either")):
        x = rw[key]
        rows += (f'<tr{" class=sep" if key == "both" else ""}><td colspan=2>{lab}</td><td style="text-align:left">each at its own 1-in-5 level</td><td></td>'
                 f'<td>{x["hits"]}</td><td>{x["false_payouts"]}</td><td>{x["false_payout_share"]:.0%}</td><td>{x["peirce"]:.2f}</td><td>{p_fmt(x["p_vs_chance"])}</td></tr>')
    return ('<table><thead><tr><th>Index</th><th style="text-align:left">Method</th><th style="text-align:left">One level for all gauges</th><th>Pays, range across gauges</th>'
            f'<th>Caught (of 60)</th><th>False payouts</th><th>Share of payouts false</th><th>Peirce skill</th><th>p (vs chance)</th></tr></thead><tbody>{rows}</tbody></table>')


REFS = [
    "Alfieri, L., Burek, P., Dutra, E., Krzeminski, B., Muraro, D., Thielen, J. and Pappenberger, F. (2013) GloFAS – global ensemble streamflow forecasting and flood early warning. <i>Hydrology and Earth System Sciences</i> 17, 1161–1175.",
    "CEDEX (2024) <i>Anuario de Aforos 2021-2022</i>. Centro de Estudios y Experimentación de Obras Públicas for the Ministerio para la Transición Ecológica y el Reto Demográfico, Madrid.",
    "Clarke, D.J. (2016) A theory of rational demand for index insurance. <i>American Economic Journal: Microeconomics</i> 8(1), 283–306.",
    "Coughlan de Perez, E., van den Hurk, B., van Aalst, M.K., Jongman, B., Klose, T. and Suarez, P. (2015) Forecast-based financing: an approach for catalyzing humanitarian action based on extreme weather and climate forecasts. <i>Natural Hazards and Earth System Sciences</i> 15, 895–904.",
    "England, J.F., Cohn, T.A., Faber, B.A., Stedinger, J.R., Thomas, W.O., Veilleux, A.G., Kiang, J.E. and Mason, R.R. (2019) <i>Guidelines for Determining Flood Flow Frequency – Bulletin 17C</i>. U.S. Geological Survey Techniques and Methods, book 4, chap. B5.",
    "Gelaro, R., McCarty, W., Suárez, M.J., Todling, R., Molod, A., Takacs, L. et al. (2017) The Modern-Era Retrospective Analysis for Research and Applications, Version 2 (MERRA-2). <i>Journal of Climate</i> 30(14), 5419–5454.",
    "Gringorten, I.I. (1963) A plotting rule for extreme probability paper. <i>Journal of Geophysical Research</i> 68(3), 813–814.",
    "Harrigan, S., Zsoter, E., Alfieri, L., Prudhomme, C., Salamon, P., Wetterhall, F., Barnard, C., Cloke, H. and Pappenberger, F. (2020) GloFAS-ERA5 operational global river discharge reanalysis 1979–present. <i>Earth System Science Data</i> 12, 2043–2060.",
    "Hirpa, F.A., Salamon, P., Beck, H.E., Lorini, V., Alfieri, L., Zsoter, E. and Dadson, S.J. (2018) Calibration of the Global Flood Awareness System (GloFAS) using daily streamflow data. <i>Journal of Hydrology</i> 566, 595–606.",
    "Hosking, J.R.M., Wallis, J.R. and Wood, E.F. (1985) Estimation of the generalized extreme-value distribution by the method of probability-weighted moments. <i>Technometrics</i> 27(3), 251–261.",
    "Hosking, J.R.M. and Wallis, J.R. (1997) <i>Regional Frequency Analysis: An Approach Based on L-Moments</i>. Cambridge University Press.",
    "Lehner, B. and Grill, G. (2013) Global river hydrography and network routing: baseline data and new approaches to study the world's large river systems. <i>Hydrological Processes</i> 27(15), 2171–2186.",
    "McNemar, Q. (1947) Note on the sampling error of the difference between correlated proportions or percentages. <i>Psychometrika</i> 12(2), 153–157.",
    "Model Library (2026) <i>Four ways to set a parametric trigger, tested on Andalucía rainfall and yields</i>. Article, 9 October 2026. https://modelibrary.com",
    "NASA POWER (2026) Prediction Of Worldwide Energy Resources, daily point API, precipitation PRECTOTCORR. NASA Langley Research Center. https://power.larc.nasa.gov (accessed 30 October 2026).",
    "Peirce, C.S. (1884) The numerical measure of the success of predictions. <i>Science</i> 4(93), 453–454.",
]
REF_IDX = {k: i + 1 for i, k in enumerate(["alfieri", "cedex", "clarke", "coughlan", "b17c", "gelaro", "gringorten", "harrigan", "hirpa", "hww", "hw", "lehner", "mcnemar", "modellib", "nasa", "peirce"])}
c = lambda *keys: "[" + ", ".join(str(REF_IDX[x]) for x in keys) + "]"

ABSTRACT = f"""A parametric flood policy pays when an index crosses an agreed trigger. Where a river has no gauge, the
index has to come from global data: a flood model's river flow, or rainfall. We test both against {S['gauges']} river gauges in
the Guadalquivir basin, Spain ({AREA[0]:,}–{AREA[1]:,} km², water years 1985–2022, {N_GY} gauge-years), in the region where a
recent industry study compared four ways of setting rainfall triggers for drought cover. Flood-frequency curves were fitted by
L-moments (GEV and log-Pearson III) to the annual maxima of the gauges, of the GloFAS reanalysis and of catchment rainfall from
NASA POWER, and 1-in-T triggers were scored year by year against the floods the gauges measured. The model's 10-year flood is
{S['median_ratio_glofas_to_observed']['10']:.2f} of the gauged one at the median gauge, so a trigger written in m³/s from the
model caught only {int(a5.hits)} of {int(a5.hits + a5.misses)} 1-in-5 flood years (Peirce skill {a5.peirce:.2f}); written as
the model's own 1-in-5 level it caught {int(r5.hits)} (Peirce {r5.peirce:.2f}; McNemar p = {p_fmt(P5['mcnemar_p'])}). Set from
each gauge's own record, as a quantile, a return period or a share of the mean annual maximum, triggers on the same index
performed alike; one absolute level shared by all gauges paid in {aR.paid_share_min:.0%} to {aR.paid_share_max:.0%} of years
from one gauge to the next and lost skill (Peirce {aR.peirce:.2f}). Storm rainfall (the wettest three days) was a weaker index
than river flow ({int(rQ.hits)} of 60, Peirce {rQ.peirce:.2f}); the October–April rainfall total matched it
({int(rS.hits)} of 60, Peirce {rS.peirce:.2f}), and the two disagreed on few flood years ({rw['river_only_caught']} against
{rw['rain_only_caught']}). Requiring both to pass cut false payouts from {rw['river']['false_payout_share']:.0%} to
{rw['both']['false_payout_share']:.0%} of payouts, at the cost of {rw['river']['hits'] - rw['both']['hits']} flood years. These results
use GloFAS 4.0. Repeated on the same gauge-years with GloFAS 5.0, the model's 10-year flood was {V5M['median_ratio10']:.2f} of the
gauged one, and the trigger written in m³/s caught {V5A['hits']} of 60 flood years (Peirce {V5A['peirce']:.2f}) against
{V5R['hits']} for the model's own 1-in-5 level (Peirce {V5R['peirce']:.2f}; McNemar p = {p_fmt(V5M['pair']['5']['mcnemar_p'])}): the bias
had largely gone, the frequency-based trigger still scored higher, and about half of all payouts were still false. Basis
risk remained high in every design, and the rank correlation of the gauge's annual maxima with the index's predicted where it
would be (Spearman ρ = {RHO_SH[0]:.2f} across gauges for river flow). Triggers from global data should be set from each site's
own record, written in the index's own terms, screened with local evidence and calibrated before they enter a contract. Data,
code and a notebook that reproduce every number are published with this paper."""


def paper():
    body = f"""
<div class="cover-line"></div>
<p class="kicker">Research paper · version {VERSION} · {DATE}</p>
<h1>{TITLE}</h1>
<p class="meta"><b>{AUTHOR}</b> · {AFFIL}</p>
<p class="meta">Correspondence: through {CASE_URL.replace('/case-guadalquivir', '/contact')}</p>
<div class="abstract"><h2>Abstract</h2><p>{ABSTRACT}</p>
<p class="kw"><b>Keywords:</b> parametric insurance; flood trigger; basis risk; GloFAS; GloFAS 5.0; rainfall index; NASA POWER; flood frequency; L-moments; verification; Guadalquivir</p></div>

<h2>1. Introduction</h2>
<p>Parametric (index) insurance pays a fixed sum when a measured index passes an agreed level, instead of after a loss
assessment. Payouts are fast and cheap to administer, which is why the approach has spread from crop and weather cover to
flood risk, risk pools and forecast-based humanitarian finance {c('coughlan')}. Its weakness is basis risk: the index can
pass the trigger when the insured suffers no loss, or stay below it when they do. Basis risk is the main reason that demand for
index cover stays lower than its price alone would suggest {c('clarke')}.</p>
<p>For river floods the natural index is discharge at a gauge. Most places at risk have no gauge, and where one exists its
record is often too short, interrupted or not public. Global hydrological reanalyses fill the gap. The Global Flood Awareness
System (GloFAS) runs the LISFLOOD model over the whole land surface at about 5 km resolution, driven by atmospheric
reanalysis, and publishes daily river discharge from 1979 onwards {c('alfieri', 'harrigan')}. A trigger for any river reach can
therefore be read from GloFAS in minutes. The question a buyer and an insurer must answer first is whether that trigger pays in
the years the river actually floods.</p>
<p>Global models are calibrated against a subset of the world's gauges {c('hirpa')} and are known to struggle where rivers are
regulated by reservoirs and abstractions, and in semi-arid climates where runoff is a small and variable share of rainfall.
Both conditions describe the Guadalquivir in southern Spain.</p>
<p>The other common index is rainfall, which is estimated everywhere and does not depend on river engineering. Model Library
{c('modellib')} recently set out four ways of fixing a trigger level (an absolute physical value, a quantile of each location's
own record, a return period from a fitted extreme-value model, and a share of a reference value) and tested them on a drought
cover in Andalucía indexed on October–April rainfall from NASA POWER at three cells. One absolute level of 280 mm, the central
cell's 1-in-5, would have paid in 12 % of seasons at the western cell and 64 % at the eastern one. That test concerns drought, the
dry tail of seasonal rainfall. Floods are the wet tail, and a river carries rain that fell days earlier and far upstream.</p>
<p>This paper asks four practical questions in the Guadalquivir basin, which drains most of Andalucía: (1) how close a global
model's flood magnitudes are to the gauged ones; (2) whether a trigger written as a fixed flow, or as the model's own return
period, pays in the right years; (3) how the four ways of setting the level, and a rainfall index instead of river flow, change
the answer; and (4) whether the basis risk at a site can be anticipated before a policy is written. We answer them with an
open, reproducible test on {S['gauges']} gauges.</p>

<h2>2. Data</h2>
<p><b>Gauges.</b> Daily mean river flow and station metadata come from the <i>Anuario de Aforos 2021-2022</i> for the
Guadalquivir basin, published by CEDEX for Spain's Ministry for the Ecological Transition {c('cedex')}. We kept every gauge
with a catchment of at least 500 km² and at least 25 years of daily flow in water years 1985–2022 (October to September). This
gave {S['gauges']} gauges with catchments of {AREA[0]:,} to {AREA[1]:,} km² (Table 1; Figure 1). The raw CEDEX files are not
redistributed; they are fetched from CEDEX and checked against published SHA-256 checksums.</p>
<p><b>Global model.</b> Daily river discharge (24-hour mean) from the GloFAS reanalysis, LISFLOOD, consolidated product,
version 4.0, at 0.05° resolution, retrieved through the Open-Meteo flood API, which serves the Copernicus Emergency Management
Service data under CC BY 4.0. For each gauge, all cells within ±0.1° (about 10 km) were retrieved, and the cell whose mean flow
over the common period was closest to the gauge's (in log ratio) was used. This choice uses the gauge and is therefore the
model's best case; at an ungauged site the cell has to be found from the upstream area alone. Version 2 of this paper adds
the GloFAS reanalysis version 5.0 (consolidated, 0.05°), downloaded for the whole basin from the Copernicus Early Warning Data
Store for water years 1984–2022, with cells chosen the same way. GloFAS 5.0 is compared with 4.0 on the same {N_GY} gauge-years
(section 4.5); the 39 yearly files are listed with their SHA-256 values in the data package.</p>
<p><b>Rainfall.</b> Daily precipitation (PRECTOTCORR: MERRA-2, bias-corrected, on a 0.5° × 0.625° grid) from the NASA POWER
daily API {c('nasa', 'gelaro')}, the source of the Model Library study. Each gauge's catchment was taken from HydroBASINS level 8
{c('lehner')}: of the sub-catchments within about 13 km of the gauge, the one whose upstream area best matched the gauge's
catchment area (ratio {AREA_R[0]:.2f} to {AREA_R[2]:.2f}, median {AREA_R[1]:.2f}). Catchment rainfall is the mean of the POWER
cells that overlap the catchment, weighted by overlap area.</p>
{fig('gq_map.png', 1, f'The {S["gauges"]} gauges (dots, sized by catchment area, coloured by the ratio of GloFAS mean flow to gauged mean flow) and their matched GloFAS river cells (squares). An interactive version with basemaps, rivers and sub-catchments is at ' + CASE_URL + '.', '86%')}

<h2>3. Methods</h2>
<h3>3.1 Annual maxima and flood frequency</h3>
<p>For each source, the largest daily flow of each water year was taken, keeping years with at least 80 % of days; the
comparison uses the years both sources cover ({YRS[0]} to {YRS[1]} per gauge, {N_GY} gauge-years in total). The generalised
extreme value (GEV) distribution and the log-Pearson type III (LP3) distribution were fitted by L-moments
{c('hww', 'hw')}, the latter to log<sub>10</sub> flows as in flood-frequency practice {c('b17c')}. The better fit was chosen
by the probability-plot correlation with Gringorten plotting positions {c('gringorten')}; the GEV was chosen at {GEV_G} of
{S['gauges']} gauges and at {GEV_M} of {S['gauges']} GloFAS cells (LP3 is not fitted where a year's maximum is zero). Return
levels for 1-in-2 to 1-in-50 years carry a 90 % percentile bootstrap band (300 resamples of the annual maxima, refitted).</p>
<h3>3.2 Triggers</h3>
<p>A year is a <i>flood year</i> at a gauge when its annual maximum reached the gauge's own fitted 1-in-T level. Two triggers
were set from the model for each T = 2, 5, 10 and 25 years. The <i>fixed-flow</i> trigger pays when the model's annual maximum
reaches the gauge's 1-in-T level in m³/s: the trigger a buyer would write by reading a design flow off a gauge-based study and
applying it to the model. The <i>return-period</i> trigger pays when the model's annual maximum reaches the model's own 1-in-T
level, i.e. the trigger is defined by frequency rather than by magnitude. Payouts are counted per gauge-year: a
<i>hit</i> (flood year, paid), a <i>miss</i> (flood year, not paid) or a <i>false payout</i> (paid, no flood year).</p>
<p><b>Four ways to set the level, on three indices.</b> Following Model Library {c('modellib')}, every 1-in-T trigger was also set
in four ways, all aimed at paying once in T years: (i) <i>absolute</i>, one level for every gauge, the median of the gauges' own
fitted 1-in-T levels (in mm for rainfall; for river flow per 1,000 km² of catchment, since one flow in m³/s cannot be shared by
catchments of {AREA[0]:,} to {AREA[1]:,} km²); (ii) <i>quantile</i>, each gauge's own empirical 1 − 1/T quantile (Weibull
plotting position); (iii) <i>return period</i>, each gauge's fitted 1-in-T level; and (iv) <i>share of a reference</i>, one share
of each gauge's mean annual maximum, the same for all gauges (the median ratio of the fitted 1-in-T level to the mean). Each was
applied to three indices: river flow from GloFAS; storm rainfall, the catchment's largest 3-day total of the year, as in
excess-rainfall flood cover; and wet-season rainfall, the October–April catchment total, the index of the Model Library study.
Both rainfall windows were fixed in advance; 1-, 5-, 10- and 30-day windows are reported as a sensitivity test. Two-index
triggers pay when river flow and wet-season rainfall both pass their own 1-in-5 levels, or when either does.</p>
<h3>3.3 Verification</h3>
<p>From the pooled 2 × 2 table of all gauge-years we report the hit rate H, the false-alarm rate F (false payouts as a share
of non-flood years), the share of payouts that were false, and the Peirce skill score H − F {c('peirce')}, which is 0 for a
trigger with no skill and 1 for a perfect one, whatever the base rate. Against chance, we test whether a trigger that paid out
the same number of times at random would have caught as many flood years (one-sided hypergeometric test). Two triggers
are compared on the same flood years with McNemar's test {c('mcnemar')} on the flood years caught by one but not the other.
Across gauges, Spearman's rank correlation relates basis risk to the agreement between the two annual-maximum series.</p>
<h3>3.4 Reproducibility</h3>
<p>The analysis was run by the KAI engine and reproduced independently by an open notebook built on textbook formulas
(NumPy, SciPy, pandas). The notebook re-derives every trigger count exactly and the median magnitude ratio to within 0.02 of
the engine's results, and stops with an error if they drift. A rebuild script regenerates the derived data files from the
CEDEX and GloFAS sources; it reproduced all {N_GY} annual maxima and all {S['gauges']} cell choices exactly. A second script
builds the catchments and catchment rainfall from HydroBASINS and NASA POWER, and a third sets and scores the triggers in the
four ways on the three indices.</p>

<h2>4. Results</h2>
<h3>4.1 GloFAS 4.0 sees these floods at about a fifth of their size</h3>
<p>GloFAS mean flow was within a factor of 2 of the gauge at only 4 of {S['gauges']} gauges (median ratio {MEANR:.2f}), and the
model's 10-year flood was {S['median_ratio_glofas_to_observed']['10']:.2f} of the gauged one at the median gauge, within a
factor of 2 at {WITHIN2} gauges (Figure 2; Table 1). The low bias held at every return period (median ratios
{S['median_ratio_glofas_to_observed']['2']:.2f}, {S['median_ratio_glofas_to_observed']['5']:.2f},
{S['median_ratio_glofas_to_observed']['10']:.2f}, {S['median_ratio_glofas_to_observed']['25']:.2f} and
{S['median_ratio_glofas_to_observed']['50']:.2f} for 1-in-2 to 1-in-50). It did not depend on catchment size (Spearman
ρ = {AR_R10[0]:.2f}, p = {AR_R10[1]:.2g}) but did follow the mean-flow bias (ρ = {MR_R10[0]:.2f}, p = {MR_R10[1]:.2g}): where
the model's water balance is low, so are its floods. A search up to 25 km around the largest gauge (Mengibar, 16,166 km²)
found no river cell with a larger flow, so the bias is in the model, not in the choice of cell.</p>
{fig('gq_levels.png', 2, f'The 10-year flood at each gauge against the 10-year flood in GloFAS (log scales; dot size: catchment area). Blue: GloFAS mean flow within a factor of 2 of the gauge; orange: far below. Shading: within a factor of 2 of the 1 : 1 line.', '58%')}
{fig('gq_frequency.png', 3, 'Flood-frequency curves at four gauges: annual maxima at their plotting positions, the preferred fit and its 90 % bootstrap band, for the gauge (blue) and GloFAS (orange). Where the curves run roughly parallel (Mengibar), a trigger written as a return period can still work; where the model is flatter or noisier, it cannot.')}

<h3>4.2 Write the trigger as a return period, not in m³/s</h3>
<p>Because the model's floods are too small, a trigger written in m³/s from a gauge-based design flow almost never fired:
at 1-in-5 it caught {int(a5.hits)} of {int(a5.hits + a5.misses)} flood years, with a Peirce skill of {a5.peirce:.2f}, no
better than a trigger paying at random (p = {p_fmt(a5.p_vs_chance)}; Table 2). Written as the model's own 1-in-5 level, the
same trigger caught {int(r5.hits)} flood years with a false-alarm rate of {r5.false_alarm_rate:.2f} (Peirce skill
{r5.peirce:.2f}; p = {p_fmt(r5.p_vs_chance)} against chance). On the same flood years, {P5['rp_only']} were caught by the
return-period trigger but not the fixed-flow one, and {P5['abs_only']} the other way round (McNemar p = {p_fmt(P5['mcnemar_p'])}).
The ranking held at every trigger level (Figure 4): skill peaked at 1-in-5 ({r5.peirce:.2f}) and fell to
{k(25, 'rp').peirce:.2f} at 1-in-25, where only {int(k(25, 'rp').hits + k(25, 'rp').misses)} flood years exist in the pooled
record. The return-period trigger is not free of basis risk: at 1-in-5 it also paid {int(r5.false_payouts)} times without a
flood, so {r5.false_payout_share:.0%} of its payouts would have been false.</p>
{fig('gq_skill.png', 4, 'Pooled verification of the two triggers at four trigger levels: hit rate and false-alarm rate (left) and the Peirce skill score (right). The return-period trigger keeps a positive skill at every level; the fixed-flow trigger has almost none.')}
<div class="tblock"><p class="tcap"><b>Table 2.</b> Verification of 1-in-T triggers set from GloFAS, pooled over {S['gauges']} gauges and {N_GY} gauge-years.</p>
{table_skill()}
<p class="tnote">Caught by chance: expected hits of a trigger that paid the same number of times at random; p: one-sided hypergeometric probability of at least as many hits by chance.</p></div>

<h3>4.3 Four ways to set the level, on river flow and on rainfall</h3>
<p>On each index, the three methods set from each gauge's own record gave almost the same trigger. At 1-in-5, the quantile,
return-period and share triggers on river flow caught {int(OWN.hits.min())} to {int(OWN.hits.max())} flood years with Peirce
skill {OWN.peirce.min():.2f} to {OWN.peirce.max():.2f}, and paid in {OWN.paid_share_min.min():.0%} to {OWN.paid_share_max.max():.0%}
of years at any gauge (Table 3; Figure 5). One absolute level for all gauges did not: {aR.common_level:.1f} m³/s per 1,000 km² of
catchment, the median gauge's 1-in-5 level, paid in {aR.paid_share_min:.0%} of years at one gauge and {aR.paid_share_max:.0%} at
another, and its skill fell to {aR.peirce:.2f} with {int(aR.false_payouts)} false payouts. Rainfall showed the same pattern
({aS3.paid_share_min:.0%} to {aS3.paid_share_max:.0%} of years for storm rainfall, {aSe.paid_share_min:.0%} to
{aSe.paid_share_max:.0%} for wet-season rainfall), as in the Andalucía drought case, where 280 mm paid in 12 to 64 % of
seasons across three cells {c('modellib')}.</p>
<p>Storm rainfall was the weaker index. Written as each catchment's own 1-in-5 three-day total, it caught {int(rQ.hits)} of 60
flood years (Peirce {rQ.peirce:.2f}), and other storm windows did no better (1 to 10 days: Peirce {min(WIN_SHORT):.2f} to
{max(WIN_SHORT):.2f}; 30 days: {win.loc['rain_max_30d_mm', 'peirce_1in5']:.2f}). Wet-season rainfall matched river flow:
{int(rS.hits)} flood years caught against {int(r5.hits)} (Peirce {rS.peirce:.2f} against {r5.peirce:.2f}), with
{int(rS.false_payouts)} and {int(r5.false_payouts)} false payouts. The two indices largely agreed (median rank correlation of
their annual series {rw['median_rank_corr_river_vs_rain']:.2f}): {rw['river_only_caught']} flood years were caught by river flow
alone and {rw['rain_only_caught']} by rainfall alone (McNemar p = {rw['mcnemar_p']:.2g}). Requiring both to pass caught
{rw['both']['hits']} flood years with {rw['both']['false_payouts']} false payouts, so the share of payouts that were false fell
from {rw['river']['false_payout_share']:.0%} to {rw['both']['false_payout_share']:.0%}; paying when either passed caught
{rw['either']['hits']} with {rw['either']['false_payouts']} false payouts.</p>
{fig('gq_methods.png', 5, 'Triggers set to pay once in five years, in four ways, on river flow and on rainfall. Left: Peirce skill against the gauges\' flood years, pooled over 14 gauges. Right: how often each trigger pays at each gauge (dot: median gauge; bar: lowest to highest). One absolute level for all gauges pays in very different shares of years from one gauge to the next.')}
<div class="tblock"><p class="tcap"><b>Table 3.</b> 1-in-5 triggers set in four ways on three indices, and two-index triggers, pooled over {S['gauges']} gauges ({N_GY} gauge-years, 60 flood years).</p>
{table_methods()}
<p class="tnote">Pays: share of years the trigger pays at a gauge, lowest and highest gauge (target 20 %). One level for all gauges: the absolute level, or the share of each gauge's mean annual maximum. Peirce skill: hit rate − false-alarm rate. p: one-sided hypergeometric test against a trigger paying as often at random.</p></div>

<h3>4.4 Basis risk can be anticipated from a short record</h3>
<p>Skill varied strongly between gauges (Table 1). The share of 1-in-5 flood years caught ranged from 0.20 to 1.00, and it
followed the rank correlation of the gauge's annual maxima with the model's (Spearman ρ = {RHO_SH[0]:.2f}, p = {RHO_SH[1]:.1g};
Figure 6). The median rank correlation was {S['median_rank_correlation']:.2f}. Gauges where the model ranked the big years well
(ρ ≥ 0.6: Mengibar, Castro del Río, Central de Cala, Aznalcázar Puente) caught half or more of their flood years, up to all of
them; gauges where it did not (ρ near zero or negative: Villanueva de las Torres, Llano de Vela, Arroyo María) caught a fifth
to two-fifths.</p>
{fig('gq_rho_share.png', 6, 'Share of 1-in-5 flood years caught by the return-period trigger at each gauge against the rank correlation of annual maxima, gauge against GloFAS (dot size: catchment area; dashed: least-squares line).', '56%')}

<div class="tblock"><p class="tcap"><b>Table 1.</b> Gauges, 10-year floods (Q10) with 90 % bootstrap bands, and the 1-in-5 return-period trigger at each gauge.</p>
{table_gauges()}
<p class="tnote">Mean-flow ratio: GloFAS mean flow ÷ gauged mean flow over the common days. Q10 ratio: GloFAS ÷ gauge. Rank corr.: Spearman correlation of annual maxima. Years: water years both sources cover.</p></div>


<h3>4.5 GloFAS 5.0: the bias has largely gone; the advice on frequency stands</h3>
<p>On the same {V5M['gauge_years']} gauge-years, GloFAS 5.0's 10-year flood was {V5M['median_ratio10']:.2f} of the gauged one at the
median gauge (4.0: {V4M['median_ratio10']:.2f}) and within a factor of 2 at {V5M['gauges_ratio10_within_x2']} of {S['gauges']} gauges
(4.0: {V4M['gauges_ratio10_within_x2']}); its mean flow was within a factor of 2 at 13 of {S['gauges']} gauges (Figure 7; Table 4).
The model also ranked the big years better (median rank correlation {V5M['median_rank_corr']:.2f} against {V4M['median_rank_corr']:.2f}).
With the bias gone, a trigger written in m³/s from a gauge-based design flow worked: at 1-in-5 it caught {V5A['hits']} of 60 flood
years (Peirce {V5A['peirce']:.2f}; 4.0: {V4A['hits']}, {V4A['peirce']:.2f}). Written as the model's own 1-in-5 level it caught
{V5R['hits']} (Peirce {V5R['peirce']:.2f}); {V5M['pair']['5']['rp_only']} flood years were caught by the return-period trigger alone and
{V5M['pair']['5']['abs_only']} by the fixed-flow trigger alone (McNemar p = {p_fmt(V5M['pair']['5']['mcnemar_p'])}). Basis risk did not
fall: {V5R['false_payouts']} false payouts for the return-period trigger and {V5A['false_payouts']} for the fixed-flow one, so about half
of all payouts were still false. The link between a gauge's rank correlation and the share of floods caught weakened
(Spearman ρ = {V5M['rho_vs_share_caught'][0]:.2f}, p = {V5M['rho_vs_share_caught'][1]:.2g}). Over every year that GloFAS 5.0 and the
gauges both cover (1985–2022, {V5F['gauge_years']} gauge-years, {V5FR['hits'] + V5FR['misses']} flood years), the return-period trigger
caught {V5FR['hits']} with {V5FR['false_payouts']} false payouts (Peirce {V5FR['peirce']:.2f}) and the fixed-flow trigger {V5FA['hits']}
with {V5FA['false_payouts']} (Peirce {V5FA['peirce']:.2f}; McNemar p = {p_fmt(V5F['pair']['5']['mcnemar_p'])}).</p>
{fig('gq_v4_v5.png', 7, f'GloFAS 4.0 against 5.0 on the same {V5M["gauge_years"]} gauge-years. Left: the 10-year flood at each gauge against the model (log scales; shading: within a factor of 2). Right: 1-in-5 flood years paid and false payouts, pooled over {S["gauges"]} gauges, for the two ways of writing the trigger.')}
<div class="tblock"><p class="tcap"><b>Table 4.</b> GloFAS 4.0 and 5.0 on the same {V5M['gauge_years']} gauge-years (60 flood years at 1-in-5).</p>
<table><thead><tr><th style="text-align:left">Measure</th><th>GloFAS 4.0</th><th>GloFAS 5.0</th></tr></thead><tbody>
<tr><td style="text-align:left">10-year flood, model ÷ gauge (median)</td><td>{V4M['median_ratio10']:.2f}</td><td>{V5M['median_ratio10']:.2f}</td></tr>
<tr><td style="text-align:left">Gauges with the 10-year flood within ×2</td><td>{V4M['gauges_ratio10_within_x2']}</td><td>{V5M['gauges_ratio10_within_x2']}</td></tr>
<tr><td style="text-align:left">Rank correlation of annual maxima (median)</td><td>{V4M['median_rank_corr']:.2f}</td><td>{V5M['median_rank_corr']:.2f}</td></tr>
<tr><td style="text-align:left">Return period: caught · false payouts · Peirce</td><td>{V4R['hits']} · {V4R['false_payouts']} · {V4R['peirce']:.2f}</td><td>{V5R['hits']} · {V5R['false_payouts']} · {V5R['peirce']:.2f}</td></tr>
<tr><td style="text-align:left">Fixed m³/s: caught · false payouts · Peirce</td><td>{V4A['hits']} · {V4A['false_payouts']} · {V4A['peirce']:.2f}</td><td>{V5A['hits']} · {V5A['false_payouts']} · {V5A['peirce']:.2f}</td></tr>
<tr><td style="text-align:left">McNemar, flood years caught by one only (RP vs fixed)</td><td>{V4M['pair']['5']['rp_only']} vs {V4M['pair']['5']['abs_only']}, p = {p_fmt(V4M['pair']['5']['mcnemar_p'])}</td><td>{V5M['pair']['5']['rp_only']} vs {V5M['pair']['5']['abs_only']}, p = {p_fmt(V5M['pair']['5']['mcnemar_p'])}</td></tr>
</tbody></table></div>

<h2>5. Discussion</h2>
<p><b>Frequency, not magnitude.</b> A global model can be biased in magnitude and still carry useful information on which
years are large. Writing the trigger as the model's own return period uses that information and discards the bias; writing it
in m³/s keeps the bias and discards the information. In this basin the difference was between a trigger with clear skill and
one with none. The same holds for a trigger written as a percentile of the model's flows, or as a share of a named past flood
in the model, which are also defined in the model's own terms: on this record the quantile, return-period and share triggers
were interchangeable.</p>
<p><b>A better model narrows the gap, it does not close it.</b> GloFAS 5.0 removed most of the low bias, and with it most of
the penalty for writing the trigger in m³/s. The trigger defined by the model's own frequency still caught more flood years, and
it is the one that does not depend on the model version: when a reanalysis is upgraded, a level written in the model's own terms
is re-derived from the new record, while a fixed flow can suddenly pay far more or far less often. Basis risk was the same with
both versions; the model's ranking of years, not its magnitudes, limits the trigger.</p>
<p><b>One level for all sites hides the frequency.</b> An absolute level is easy to read and to settle, but it pays at a
different frequency at every site, which Model Library {c('modellib')} showed for drought and which holds more strongly for
floods: catchments differ in size, climate and regulation, and dividing by area does not remove the spread. Each site needs its
own level, set from its own record; the agreed level can then be written into the contract in m³/s or mm for settlement.</p>
<p><b>Rainfall or river flow.</b> In this basin, flood years follow wet winters more than single storms: reservoirs absorb the
first rains and spill or release once full, and soils and aquifers fill slowly. A season total therefore ranked flood years as
well as the river model, and storm rainfall did not. For prompt flood payouts that favours river flow: a season total is known
only at the end of April and marks a flood year, not the flood, so it suits seasonal or anticipatory finance rather than event
cover. Where both indices are available, requiring them to agree is a simple way to cut false payouts; it lowers the payout
frequency, which the price must reflect.</p>
<p><b>Basis risk remains, and can be screened.</b> Even the better trigger paid without a flood in {r5.false_payout_share:.0%}
of payouts at 1-in-5. For a buyer that is a large risk, and in a regulated basin it is expected: reservoirs cut and delay
flood peaks in some years and not in others, which a model without the reservoirs' operation cannot reproduce. The strong link
between rank correlation and the share of floods caught offers a practical screen: a few years of local evidence (a short gauge
record, flood marks, satellite flood extents or insurance claims) give a rank correlation that indicates, before the policy is
written, whether the global index can carry the trigger or needs local calibration.</p>
<p><b>Limits.</b> One basin, strongly regulated and semi-arid, so the size of the bias will differ elsewhere. The four-way and
rainfall comparisons use GloFAS 4.0; GloFAS 5.0 was compared for the two river-flow triggers. Daily means, so instantaneous peaks are higher than the values used. 17 to 24
years per gauge, so levels beyond 1-in-25 are extrapolations and the 1-in-25 scores rest on 11 flood years. The cell was
matched with the gauge's mean flow, the model's best case. Rainfall comes from one reanalysis-based product on a grid of about
50 km, coarse for the smaller catchments, and the HydroBASINS catchments differ in area from the gauges' by up to a factor of
{AREA_R[2]:.1f}. Flood years are defined from the gauges' daily flows, not from losses; a contract would also have to consider
where and how losses occur.</p>

<h2>6. Conclusions</h2>
<p>On {S['gauges']} gauges in the Guadalquivir basin, GloFAS 4.0 saw floods at about a fifth of their measured size; GloFAS 5.0
saw them at about their measured size ({V5M['median_ratio10']:.2f}), which made a trigger written in m³/s work, though still less well
than one written as the model's own return period, and left basis risk unchanged.
A parametric trigger written in m³/s from the model was no better than chance; the same trigger written as the model's own
1-in-5 level caught half the flood years with a false-alarm rate of {r5.false_alarm_rate:.2f}, but a large share of its payouts
were still false. Set from each gauge's own record, quantile, return-period and share triggers performed alike; one level for all
gauges did not. Storm rainfall was a weaker index than river flow, wet-season rainfall an equal one, and the two together cut
false payouts. Four recommendations follow for anyone writing flood triggers from global data: set the level from each site's own
record and write it in the index's own terms, never as a flow read from another source; prefer river flow for event cover and
test a second index alongside it; screen basis risk with the rank correlation against any local record before the policy is
written; and calibrate locally before the trigger enters a contract. Re-test every trigger when the model is upgraded.</p>

<h2>Data and code availability</h2>
<p class="small">The data package published with this paper on Zenodo contains the derived data (annual maxima at the gauges
and at their GloFAS 4.0 and 5.0 cells; catchment rainfall maxima and the catchments and rainfall cells behind them; gauge list), the result files, the figures, the notebook that reproduces every number, the shared
functions, the scripts that rebuild the derived data from the sources, the script that sets and scores the triggers in four
ways, and the scripts that compute the statistics quoted here and
build this paper from them. The same material is maintained at {REPO}
(code MIT; text, figures and derived data CC BY 4.0). An interactive version with maps is at {CASE_URL}.</p>
<h2>Acknowledgements and competing interests</h2>
<p class="small">Gauge data: <i>Fuente: CEDEX, Anuario de Aforos 2021-2022 (MITECO)</i>. Global model: contains modified
Copernicus Emergency Management Service information 2026 (GloFAS 4.0, served by Open-Meteo, CC BY 4.0; GloFAS 5.0, from the
Copernicus Early Warning Data Store). Rainfall: data
obtained from the NASA Langley Research Center POWER Project, funded through the NASA Earth Science/Applied Science Program.
Catchments: HydroBASINS {c('lehner')}. The comparison of four ways to set a trigger follows Model Library {c('modellib')}, whose
published figures are quoted; Model Library had no part in this study. The author founded KAI Water &amp; Energy, which offers parametric trigger
studies (KAI-Hydro).</p>
<h2>References</h2>
<ol class="refs">{''.join(f'<li>{r}</li>' for r in REFS)}</ol>
<p class="lic">© 2026 {AUTHOR}. This work is licensed under the Creative Commons Attribution 4.0 International licence (CC BY 4.0).
Cite as: Kakooza, C. (2026) {TITLE}. Version {VERSION}. Zenodo.</p>
"""
    return f"<!doctype html><html lang=en><head><meta charset=utf-8><title>River flow or rainfall, GloFAS 4.0 or 5.0? Parametric flood triggers — Guadalquivir</title><style>{CSS}</style></head><body>{body}</body></html>"


def report():
    rows = ""
    for name in pg.gauge:
        for i, T in enumerate((2, 5, 10, 25, 50)):
            o = lv[(lv.name == name) & (lv.period == T) & (lv.source == "gauge")].iloc[0]
            m = lv[(lv.name == name) & (lv.period == T) & (lv.source == "glofas")].iloc[0]
            rows += (f'<tr{" class=sep" if i == 0 and rows else ""}><td>{name if i == 0 else ""}</td><td>1 in {T}</td>'
                     f'<td>{o.level_m3s:.1f}</td><td>{o.band_low:.0f}–{o.band_high:.0f}</td><td>{m.level_m3s:.1f}</td><td>{m.band_low:.0f}–{m.band_high:.0f}</td>'
                     f'<td>{m.level_m3s / o.level_m3s:.2f}</td></tr>')
    levels_tbl = ('<table class="long"><thead><tr><th>Gauge</th><th>Return period</th><th>Gauge, m³/s</th><th>90 % band</th><th>GloFAS, m³/s</th><th>90 % band</th>'
                  f'<th>GloFAS ÷ gauge</th></tr></thead><tbody>{rows}</tbody></table>')
    files = [("data/annual_maxima.csv", f"{N_GY} rows: gauge_id, water_year, gauge_max_m3s, glofas_max_m3s"),
             ("data/gauges.csv", f"{S['gauges']} gauges: catchment, position, record length, matched GloFAS cell, mean-flow ratio"),
             ("results/return_levels.csv", "1-in-2 to 1-in-50 levels with 90 % bands, both sources, per gauge"),
             ("results/trigger_scores.csv", "caught, missed and false payouts at 1-in-2 to 1-in-25, both triggers, pooled"),
             ("results/skill_scores.csv", "hit rate, false-alarm rate, Peirce skill, test against chance"),
             ("results/per_gauge_1in5.csv", "Table 1 of the paper"),
             ("results/kai_engine_results.json", "the KAI engine's published results, checked by the notebook"),
             ("01_global_model_flood_triggers.ipynb", "the notebook: fits, triggers, figures and the check against the engine"),
             ("data/rainfall_maxima.csv", "each water year's largest 1-, 3-, 5-, 10- and 30-day catchment rainfall, and the October–April total (mm)"),
             ("data/rain_catchments.csv · rain_cell_weights.csv", "HydroBASINS sub-catchments used for each gauge, and the NASA POWER cells with their weights"),
             ("results/trigger_methods.csv · trigger_methods_sites.csv", "triggers set four ways on three indices: pooled scores, and how often each pays at each gauge"),
             ("results/rain_windows.csv · rain_vs_river.json", "rainfall windows compared; river against wet-season rainfall, and the two combined"),
             ("flood_tools.py · rebuild_data.py", "shared functions (L-moments, GEV, LP3, bootstrap, scoring) and the rebuild script"),
             ("rebuild_rainfall.py · compare_triggers.py", "catchments and catchment rainfall; the four-way comparison and its figure"),
             ("paper/paper_stats.py", "the skill scores, per-gauge table, McNemar and Spearman tests, and the skill and basis-risk figures"),
             ("data/annual_maxima_v5.csv · gauges_v5.csv", "GloFAS 5.0 annual maxima and matched cells, water years 1985–2022"),
             ("paper/compare_v4_v5.py", "GloFAS 4.0 against 5.0 on the same gauge-years: Table 4 and Figure 7 of the paper"),
             ("paper/build_documents.py · print.js", "builds the paper and this report from the result files, and prints them to PDF")]
    ftbl = "<table><thead><tr><th>File</th><th style='text-align:left'>What it holds</th></tr></thead><tbody>" + "".join(f"<tr><td>{a}</td><td style='text-align:left'>{b}</td></tr>" for a, b in files) + "</tbody></table>"
    wrows = "".join(f"<tr><td>{lab}</td><td>{win.loc[key, 'median_rank_corr']:.2f}</td><td>{int(win.loc[key, 'caught_1in5'])}</td><td>{int(win.loc[key, 'false_payouts_1in5'])}</td><td>{win.loc[key, 'peirce_1in5']:.2f}</td></tr>"
                    for key, lab in (("glofas_max_m3s", "River flow (GloFAS), for comparison"), ("rain_max_1d_mm", "Rainfall, wettest day"), ("rain_max_3d_mm", "Rainfall, wettest 3 days"),
                                     ("rain_max_5d_mm", "Rainfall, wettest 5 days"), ("rain_max_10d_mm", "Rainfall, wettest 10 days"), ("rain_max_30d_mm", "Rainfall, wettest 30 days"),
                                     ("rain_oct_apr_mm", "Rainfall, October–April total")))
    wtbl = ("<table><thead><tr><th>Index</th><th>Median rank corr. with gauge</th><th>Caught (of 60)</th><th>False payouts</th><th>Peirce skill</th></tr></thead>"
            f"<tbody>{wrows}</tbody></table>")
    body = f"""
<div class="cover-line"></div>
<p class="kicker">KAI-Hydro technical report KH-TR-2026-01 · version {VERSION} · {DATE}</p>
<h1>Flood triggers from global data, tested on 14 river gauges: river flow or rainfall, GloFAS 4.0 or 5.0? The Guadalquivir reference case</h1>
<p class="meta"><b>{AUTHOR}</b> · {AFFIL}</p>
<p class="meta">Companion to the research paper of the same data · interactive case: {CASE_URL}</p>

<div class="box"><h3>Summary for insurers, brokers and risk pools</h3><ul>
<li><b>The question.</b> Where a river has no gauge, can a global flood model carry a parametric flood trigger?</li>
<li><b>The test.</b> {S['gauges']} gauges in Spain's Guadalquivir basin, {N_GY} gauge-years (1985–2022). Triggers were set from
the GloFAS global reanalysis as if no gauge existed, and scored against the floods the gauges measured.</li>
<li><b>Magnitude.</b> The model's 10-year flood is {S['median_ratio_glofas_to_observed']['10']:.0%} of the gauged one at the
median gauge. A trigger written in m³/s from it caught {int(a5.hits)} of {int(a5.hits + a5.misses)} 1-in-5 flood years: no
better than chance.</li>
<li><b>Frequency.</b> Written as the model's own 1-in-5 level, the same trigger caught {int(r5.hits)} of
{int(r5.hits + r5.misses)} flood years, with clear skill (Peirce {r5.peirce:.2f}).</li>
<li><b>Four ways to set the level.</b> A quantile, a return period or a share of the mean flood, each from the site's own
record, gave the same skill. One level for all sites paid in {aR.paid_share_min:.0%} to {aR.paid_share_max:.0%} of years from one
gauge to the next.</li>
<li><b>River flow or rainfall.</b> Storm rainfall (wettest 3 days) caught {int(rQ.hits)} of 60 flood years; wet-season rainfall
(October–April) caught {int(rS.hits)}, as many as river flow. Requiring both to pass cut the share of false payouts from
{rw['river']['false_payout_share']:.0%} to {rw['both']['false_payout_share']:.0%}.</li>
<li><b>GloFAS 5.0.</b> On the same gauge-years the new version sees floods at {V5M['median_ratio10']:.0%} of their size. A
trigger in m³/s now caught {V5A['hits']} of 60 flood years; the model's own 1-in-5 level caught {V5R['hits']}. About half of all
payouts were still false.</li>
<li><b>Basis risk.</b> {r5.false_payout_share:.0%} of that trigger's payouts came in years without a flood. Where the model
ranks a site's big years well, the trigger works; where it does not, it fails. The rank correlation against any short local
record predicts which (ρ = {RHO_SH[0]:.2f} across gauges).</li>
<li><b>So.</b> Write triggers in the model's own terms, screen basis risk with local evidence, and calibrate before the
trigger enters a contract.</li></ul></div>

<h2>1. Why this test</h2>
<p>A parametric policy pays on an index, not on an assessed loss. Its value to the buyer depends on how often the index and
the loss move together. For river floods without a gauge, the index usually comes from a global flood model such as GloFAS,
which publishes daily discharge for every river reach on Earth from 1979. Before a trigger from such a model is priced, three
facts are needed: how big the model thinks the floods are, whether the trigger would have paid in the years the river flooded,
and how often it would have paid when it did not. This report gives those facts for one basin and sets out how KAI-Hydro
uses them when it writes a trigger for a client.</p>

<h2>2. Data and method in brief</h2>
<p>Gauges: daily flow at every Guadalquivir gauge with at least 500 km² and 25 years of record (CEDEX, <i>Anuario de Aforos
2021-2022</i>). Model: GloFAS reanalysis 4.0 at 0.05°, the cell within 10 km whose mean flow best matches the gauge (the
model's best case). Each water year's largest daily flow from both; GEV and log-Pearson III fitted by L-moments, the better one
kept, with 90 % bootstrap bands. Flood years are years in which a gauge reached its own 1-in-T level; triggers pay when the model
reaches either the gauge's level in m³/s (fixed flow) or the model's own 1-in-T level (return period). Rainfall: catchment
means of NASA POWER daily rainfall over HydroBASINS catchments. Each trigger was also set four ways (one absolute level for all
gauges, each gauge's own quantile, return period, or share of its mean annual maximum) on river flow, storm rainfall and
wet-season rainfall, following Model Library's Andalucía study. Full method: the paper, section 3.</p>
{fig('gq_map.png', 1, 'The 14 gauges and their GloFAS river cells. Interactive map with basemaps, rivers, admin boundaries and sub-catchments: ' + CASE_URL + '.', '84%')}

<h2>3. Results</h2>
{fig('gq_levels.png', 2, 'The 10-year flood, gauge against GloFAS, one dot per gauge.', '55%')}
{fig('gq_triggers.png', 3, 'Share of flood years caught, pooled over all gauges, at four trigger levels, for the two ways of writing the trigger.', '74%')}
{fig('gq_mengibar_years.png', 4, 'Year by year at Mengibar (16,166 km²): a 1-in-5 trigger written as GloFAS\'s own return period caught 5 of 6 flood years with no false payout; written in m³/s it would have caught none.')}
{fig('gq_skill.png', 5, 'Hit rate, false-alarm rate and Peirce skill for both triggers at 1-in-2 to 1-in-25.')}
<div class="tblock"><p class="tcap"><b>Table 1.</b> Pooled verification, {S['gauges']} gauges, {N_GY} gauge-years.</p>
{table_skill()}</div>
{fig('gq_rank.png', 6, 'Basis risk by gauge: rank correlation of annual floods, gauge against GloFAS.', '70%')}
{fig('gq_rho_share.png', 7, 'Share of 1-in-5 flood years caught at each gauge against the rank correlation: a screen for basis risk.', '55%')}
<h3>GloFAS 4.0 or 5.0</h3>
{fig('gq_v4_v5.png', 8, f'GloFAS 4.0 against 5.0 on the same {V5M["gauge_years"]} gauge-years: the 10-year flood (left) and 1-in-5 flood years paid and false payouts (right).')}
<p>GloFAS 5.0 removes most of the low bias (10-year flood {V5M['median_ratio10']:.2f} of the gauged one against {V4M['median_ratio10']:.2f}).
The fixed-flow trigger now caught {V5A['hits']} of 60 flood years (4.0: {V4A['hits']}); the return-period trigger {V5R['hits']} (4.0:
{V4R['hits']}). False payouts: {V5R['false_payouts']} and {V5A['false_payouts']}. Write the trigger in the model's own terms and it is
re-derived when the model is upgraded; a fixed flow is not.</p>
<h3>River flow or rainfall, four ways</h3>
{fig('gq_methods.png', 9, 'Triggers set to pay once in five years, four ways, on river flow and on rainfall: skill (left) and how often each pays at each gauge (right).')}
<div class="tblock"><p class="tcap"><b>Table 2.</b> 1-in-5 triggers set four ways on three indices, and two-index triggers ({N_GY} gauge-years, 60 flood years).</p>
{table_methods()}</div>

<h2>4. How KAI-Hydro writes a trigger from these findings</h2>
<div class="box"><h3>Setting the level: what the test says</h3><ol>
<li><b>From each site's own record, in the index's own terms:</b> its 1-in-T return period, its own quantile, or a share of its
mean annual flood. All three gave the same skill here; the return period is the only one that reaches beyond the record.</li>
<li><b>Never one level for all sites.</b> It pays at a different frequency at each site. Once each site's level is agreed, write
it into the contract in m³/s or mm for settlement.</li>
<li><b>River flow for event cover;</b> wet-season rainfall as a second index. Paying only when both agree cut the share of false
payouts from about half to under a third; price the lower payout frequency.</li>
<li><b>Never a flow read from another source</b> (a gauge study or a design report) applied to the model.</li></ol>
<p class="small">Each comes with an attachment level (payout starts) and an exhaustion level (full payout), so the payout can
rise with the size of the event.</p></div>
<div class="box"><h3>The study a client receives</h3><ol>
<li><b>Snap</b> the site onto the river by catchment area; flag catchments too small for a 5 km model.</li>
<li><b>Flood history:</b> 40+ years of daily discharge from GloFAS 5.0, plus any gauge or record the client holds; triggers
re-tested whenever the model is upgraded.</li>
<li><b>Return levels</b> with 90 % bands; levels beyond the record flagged as extrapolations.</li>
<li><b>Basis-risk screen:</b> rank correlation of the model's big years against any local evidence (short gauge record, flood
marks, satellite flood extents, claims).</li>
<li><b>Back-test</b> of the trigger set four ways on river flow and on rainfall: hits, misses and false payouts, year by year.</li>
<li><b>Calibration</b> where the screen says so, before the trigger enters a contract.</li>
<li><b>Delivery:</b> a trigger sheet, a method note, and the same study as design floods for engineers.</li></ol></div>

<h2>5. Limits</h2>
<p>One basin, strongly regulated and semi-arid; four-way and rainfall comparisons on GloFAS 4.0, GloFAS 5.0 for the two
river-flow triggers; daily means rather than instantaneous
peaks; 17 to 24 years per gauge; the cell choice uses the gauge's mean flow (best case); rainfall from one product on a 50 km
grid, over HydroBASINS catchments up to {AREA_R[2]:.1f} times the gauge's area; flood years are defined by flow, not by losses.</p>

<div class="pb"></div>
<h2>Appendix A. Return levels at every gauge</h2>
<p class="small">Preferred fit per series (GEV or LP3, by probability-plot correlation), with 90 % percentile bootstrap bands (300 resamples).</p>
{levels_tbl}
<h2>Appendix B. The 1-in-5 trigger at every gauge</h2>
{table_gauges()}
<h2>Appendix C. Rainfall windows</h2>
<p class="small">Each rainfall index written as the catchment's own 1-in-5 level and scored against the same 60 flood years. The
3-day and October–April indices were chosen in advance; the others are a sensitivity test.</p>
{wtbl}
<h2>Appendix D. Data package and how to reproduce</h2>
{ftbl}
<p class="small">To reproduce: install Python 3.11 or newer and the packages in <i>requirements.txt</i>, then run the notebook
from its folder; it stops if any trigger count drifts from the published results. To rebuild the derived data from the sources,
run <i>rebuild_data.py</i> on a connection that CEDEX serves; it fetches the CEDEX files (SHA-256 checked) and the GloFAS cells,
and writes <i>*_rebuilt.csv</i> files to compare with the published ones. <i>rebuild_rainfall.py</i> rebuilds the catchments and
catchment rainfall from HydroBASINS (level-8 shapefile, downloaded separately) and the NASA POWER API, and
<i>compare_triggers.py</i> sets and scores the triggers four ways on the three indices.</p>
<h2>Data credits and licence</h2>
<p class="small"><i>Fuente: CEDEX, Anuario de Aforos 2021-2022 (MITECO).</i> Contains modified Copernicus Emergency Management
Service information 2026 (GloFAS 4.0 via Open-Meteo, CC BY 4.0; GloFAS 5.0 from the Copernicus Early Warning Data Store). GloFAS data are provided for information purposes only and
are not a flood warning. Rainfall: NASA Langley Research Center POWER Project, funded through the NASA Earth Science/Applied
Science Program. Catchments: HydroBASINS (Lehner and Grill, 2013). Four-way comparison after Model Library, <i>Four ways to set a
parametric trigger, tested on Andalucía rainfall and yields</i> (9 October 2026). This report: © 2026 {AUTHOR}, CC BY 4.0.</p>
"""
    return f"<!doctype html><html lang=en><head><meta charset=utf-8><title>KAI-Hydro technical report KH-TR-2026-01 — river flow or rainfall, Guadalquivir</title><style>{CSS}</style></head><body>{body}</body></html>"


if __name__ == "__main__":
    out = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else HERE
    out.mkdir(parents=True, exist_ok=True)
    (out / "paper.html").write_text(paper(), encoding="utf-8")
    (out / "technical_report.html").write_text(report(), encoding="utf-8")
    print("wrote", out / "paper.html", out / "technical_report.html")
