"""Writes results/published_phase4.json: the numbers notebooks 04, 04b and 05 assert, plus their summaries.

Run the three notebooks once without results/published_phase4.json (each writes results/nbX.json), then this
script, then make_notebooks4.py and the notebooks again. Do this only when the engine results are meant to change."""
import json
import pathlib

SUMMARY_NB4B = """* **Wellbore.** Heat loss up 16B is 14.4 °C (P10–P90 13.5–15.4) from the model's bottom-hole temperature. The measured wellhead then implies 202.9 °C (200.0–205.9) at the bottom hole. The reservoir model gives 214.0 °C, so **+11.2 °C (9.7–12.6) remains**. The wellbore model explains about 2 °C of the 13 °C left in notebook 3.
* **DTS.** Up the deep hole the fibre shows 18.4 °C of cooling; conduction to the rock allows 5.8 °C (at most 8.2). Either cooler water enters 16B higher up, or the fibre drifts. Not resolved here.
* **Barton–Bandis.** **No rate above 10 kg/s becomes feasible.** The highest feasible rate is 9.7 kg/s (9.3–10.5), against 10.5 (10.1–11.0) with constant apertures. The apertures are calibrated at the August pressure, which was already above Shmin (42.9 against 40.3 MPa). Below it the fractures close; they open further only above Shmin, where new fractures would form.
* **Tracers.** The model's water crosses in under 30 minutes. The tracers took 4.5–64 hours to first appear and 10–180 hours to peak. The mobile pore volume would have to be at least 17–360 × larger. This is the largest misfit in the case.

**Limits.** Equivalent continuum on 35 m cells. Feasibility depends on the grid: at 10 kg/s the median member's highest injector pressure is 2.9 MPa lower on 23.3 m cells than on 35 m cells. Shmin is a depth gradient, not a measurement at 16A. One calibration number (the August injection pressure). Single-phase water, no new fractures."""

SUMMARY_NB4 = """* **Full tensor.** Breakthrough changes by +8 % on 35 m cells and by −1 % on 23.3 m cells; the 30-year temperature by −0.6 to −1.6 °C. The injector pressure does not change, because both schemes are calibrated to the same measured pressure. The diagonal tensor of phase 3 was a small error next to the grid.
* **70 m against 23.3 m (12 members).** Usual practice: breakthrough **+25 % (−32 to +62 %)** at 10 kg/s and +39 % (−26 to +84 %) at 40 kg/s; 30-year temperature 10.8 °C too warm at 10 kg/s. KAI upscaling, not recalibrated: 30-year temperature within 2.4 °C (0 to 5.1) at 10 kg/s and 3.6 °C too cold at 40 kg/s, but breakthrough **+54 % (−26 to +115 %)** and +72 %. Neither coarse model gets breakthrough right: 70 m cells cannot hold the narrow channels that bring the first cold water.
* **Near-well upscaling.** Not recalibrated, KAI's upscaled well indices and transmissibilities give 17.0 MPa (16.3–18.3) for the August pressure difference of 20.9 MPa (−19 %). The usual coarse model gives 13.2 MPa (−37 %).
* **Grid convergence.** Breakthrough at 10 kg/s with Barton–Bandis apertures: **1.26 ± 0.13 years** (median member). The 35 m value is 31 % late.

**What to use.** Quote breakthrough from fine or grid-converged runs. A 70 m model upscaled from the fine one is fit for the 30-year temperature and the pressure, not for breakthrough."""

SUMMARY_NB5 = """**This well pair is a test bed, not a power plant.** At 96 m and 10 kg/s the produced water cools from 214 to 129 °C (P10–P90 116–147) in 30 years.

For the produced temperature to stay within 10 % of its drop (at least 198.6 °C) for 30 years, a doublet in this kind of stimulated granite needs about **190 m at 5 kg/s, 290 m at 10 kg/s and 580 m at 20 kg/s** (P50, surrogate). That is 3 × the FORGE spacing at 10 kg/s and 6 × at 20 kg/s. 40 kg/s and more needs more than 800 m.

* Full runs at those spacings give 204, 204 and 211 °C (P50), so the P50 answer holds. Their low cases (P10 174–176 °C) are lower than the surrogate's, so the P10 spacings in the table (240, 360, 670 m) are probably too small.
* Heat: about 3.3 MWth on average at 5 kg/s, 6.5 at 10 kg/s and 13 at 20 kg/s.
* A wider spacing needs more pressure: at 290 m and 10 kg/s about 1.5–1.8 × the August 2024 pressure difference, at 580 m and 20 kg/s about 6–8 ×, at the network conductivity FORGE has now. The August test already ran at Shmin, so such a doublet would also need a network several times more conductive than the 2024 one.
* What matters most (Sobol): the design (rate, then spacing). Among the rock inputs, the effective thickness of the stimulated network, then its heterogeneity. Rock conductivity hardly matters.
* Surrogate error on 30 held-out runs: 9.0 °C RMSE for the 30-year temperature (R² 0.97), 0.80 MW for the heat power, 3.4 for the pressure ratio.

**Limits.** A proxy doublet, tied to FORGE through one output (the 30-year temperature at 10 kg/s). It assumes a network of the same kind can be stimulated at a larger spacing and still connects the wells; FORGE data do not show that. Single-phase water, no new fractures, no thermal or chemical change of the fractures."""

pub = {}
for k in ("nb4", "nb4b", "nb5"):
    pub[k] = json.loads(pathlib.Path(f"results/{k}.json").read_text())["published"]
pub["summary_nb4"], pub["summary_nb4b"], pub["summary_nb5"] = SUMMARY_NB4, SUMMARY_NB4B, SUMMARY_NB5
pathlib.Path("results/published_phase4.json").write_text(json.dumps(pub, indent=1, ensure_ascii=False))
print({k: len(v) for k, v in pub.items() if not k.startswith("summary")})
