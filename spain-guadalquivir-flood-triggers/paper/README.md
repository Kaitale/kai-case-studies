# Paper and technical report

| File | What it is |
|---|---|
| `paper.pdf` · `paper.docx` | Kakooza, C. (2026). *River flow or rainfall? Writing parametric flood triggers from global data, tested gauge by gauge in the Guadalquivir basin, Spain.* Version 1.0. |
| `technical_report.pdf` · `.docx` | KAI-Hydro technical report KH-TR-2026-01: the same test written for insurers, brokers and risk pools, with every return level (Appendix A) and the 1-in-5 trigger at every gauge (Appendix B). |
| `../compare_triggers.py` | Sets and scores triggers four ways on river flow and rainfall: `results/trigger_methods*.csv`, `rain_windows.csv`, `rain_vs_river.json`, `figures/gq_methods.png`. |
| `paper_stats.py` | Recomputes `results/skill_scores.csv`, `results/per_gauge_1in5.csv`, `results/paper_stats.json`, `figures/gq_skill.png` and `figures/gq_rho_share.png` from `data/`. |
| `build_documents.py` | Builds `paper.html` and `technical_report.html` from the result files and figures; every number in the text is read from them. |
| `print.js` | Prints both HTML files to A4 PDF with page numbers (Playwright). |
| `make_docx.py` | Word versions of both documents for editing (`paper.docx`, `technical_report.docx`; needs pandoc and python-docx). |
| `zenodo.json` | Zenodo metadata for the record. |

Rebuild from the case folder:

```bash
pip install -r requirements.txt
python paper/paper_stats.py                 # statistics and two figures (matches the published files exactly)
python compare_triggers.py                  # river flow against rainfall, four ways
python rebuild_rainfall.py <hybas_eu_lev08_v1c.shp>   # optional: rebuild the rainfall data from NASA POWER
python paper/build_documents.py paper/      # HTML
npm i playwright && node paper/print.js paper/   # PDF
python paper/make_docx.py paper/            # Word
```

Licence: text and figures CC BY 4.0, code MIT; see `../LICENCE.md`.
