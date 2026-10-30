# Paper and technical report

| File | What it is |
|---|---|
| `paper.pdf` | Kakooza, C. (2026). *Writing parametric flood triggers from a global flood model: a gauge-by-gauge test in the Guadalquivir basin, Spain.* Version 1.0. |
| `technical_report.pdf` | KAI-Hydro technical report KH-TR-2026-01: the same test written for insurers, brokers and risk pools, with every return level (Appendix A) and the 1-in-5 trigger at every gauge (Appendix B). |
| `paper_stats.py` | Recomputes `results/skill_scores.csv`, `results/per_gauge_1in5.csv`, `results/paper_stats.json`, `figures/gq_skill.png` and `figures/gq_rho_share.png` from `data/`. |
| `build_documents.py` | Builds `paper.html` and `technical_report.html` from the result files and figures; every number in the text is read from them. |
| `print.js` | Prints both HTML files to A4 PDF with page numbers (Playwright). |
| `zenodo.json` | Zenodo metadata for the record. |

Rebuild from the case folder:

```bash
pip install -r requirements.txt
python paper/paper_stats.py                 # statistics and two figures (matches the published files exactly)
python paper/build_documents.py paper/      # HTML
npm i playwright && node paper/print.js paper/   # PDF
```

Licence: text and figures CC BY 4.0, code MIT; see `../LICENCE.md`.
