"""Statistics and figures used in the paper and the technical report (MIT licence).

Run from the case folder:  python paper/paper_stats.py
Reads data/*.csv, refits with flood_tools, and writes
  results/skill_scores.csv     hit rate, false-alarm rate, Peirce skill, test against chance (pooled)
  results/per_gauge_1in5.csv   Table 1 of the paper
  results/paper_stats.json     McNemar tests and Spearman correlations quoted in the text
  figures/gq_skill.png, figures/gq_rho_share.png
Levels come from the unrounded fits, as in the notebook.
"""
from __future__ import annotations

import json
import pathlib
import sys
import warnings

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats

HERE = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE))
import flood_tools as ft  # noqa: E402

warnings.filterwarnings("ignore")
plt.rcParams.update({"figure.dpi": 150, "axes.grid": True, "grid.color": "#dfe8e8", "axes.spines.top": False,
                     "axes.spines.right": False, "font.size": 10, "axes.titleweight": "bold", "axes.titlesize": 11,
                     "legend.frameon": False, "savefig.bbox": "tight", "savefig.facecolor": "white"})
GAUGE, MODEL, OK, AMBER, GREY = "#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#898781"
LEVELS = [2, 5, 10, 25]


def sig(p: float) -> float:
    return float(f"{p:.2g}")


def main() -> None:
    gauges = pd.read_csv(HERE / "data/gauges.csv").set_index("gauge_id")
    am = pd.read_csv(HERE / "data/annual_maxima.csv")
    N = len(am)

    fits, flags = {}, {}
    for gid in gauges.index:
        s = am[am.gauge_id == gid]
        for src, col in (("gauge", "gauge_max_m3s"), ("glofas", "glofas_max_m3s")):
            best, f = ft.fit_best(s[col].values)
            fits[(gid, src)] = (best, f[best])

    # flood / paid flags per gauge-year and level
    for gid in gauges.index:
        s = am[am.gauge_id == gid]
        for t in LEVELS:
            lg = ft.level(fits[(gid, "gauge")][1], t); lm = ft.level(fits[(gid, "glofas")][1], t)
            flags[(gid, t)] = (s.gauge_max_m3s.values >= lg, s.glofas_max_m3s.values >= lm, s.glofas_max_m3s.values >= lg)

    rows, pair = [], {}
    for t in LEVELS:
        fl = np.concatenate([flags[(g, t)][0] for g in gauges.index])
        for method, k in (("rp", 1), ("abs", 2)):
            pd_ = np.concatenate([flags[(g, t)][k] for g in gauges.index])
            h = int((fl & pd_).sum()); m = int((fl & ~pd_).sum()); f = int((~fl & pd_).sum()); c = int((~fl & ~pd_).sum())
            K, n = h + m, h + f
            H, F = h / K, f / (f + c)
            rows.append({"T": t, "method": method, "hits": h, "misses": m, "false_payouts": f, "correct_no": c,
                         "hit_rate": round(H, 3), "false_alarm_rate": round(F, 3),
                         "false_payout_share": round(f / n, 3) if n else float("nan"), "peirce": round(H - F, 3),
                         "chance_hits": round(K * n / N, 1), "p_vs_chance": sig(stats.hypergeom.sf(h - 1, N, K, n))})
        rp = np.concatenate([flags[(g, t)][1] for g in gauges.index]); ab = np.concatenate([flags[(g, t)][2] for g in gauges.index])
        b, cc = int((fl & rp & ~ab).sum()), int((fl & ab & ~rp).sum())
        pair[str(t)] = {"rp_only": b, "abs_only": cc, "mcnemar_p": sig(stats.binomtest(b, b + cc, 0.5).pvalue) if b + cc else 1.0}
    sk = pd.DataFrame(rows); sk.to_csv(HERE / "results/skill_scores.csv", index=False)

    per = []
    for gid, g in gauges.iterrows():
        s = am[am.gauge_id == gid]
        out = {"gauge": g["name"], "area": int(round(g.catchment_km2)), "years": len(s), "mean_ratio": g.glofas_mean_flow_ratio}
        for src, col, tag in (("gauge", "gauge_max_m3s", "g"), ("glofas", "glofas_max_m3s", "m")):
            best, dist = fits[(gid, src)]
            band = ft.bootstrap_band(s[col].values, best, [2, 5, 10, 25, 50], n_boot=300, seed=0)[10]
            key = "q10_gauge" if tag == "g" else "q10_glofas"
            out[key] = round(ft.level(dist, 10), 2); out[key + "_band"] = f"{band[0]:.0f}–{band[1]:.0f}"; out["fit_" + tag] = best
        out["ratio10"] = round(out["q10_glofas"] / out["q10_gauge"], 2)
        out["rho"] = round(float(stats.spearmanr(s.gauge_max_m3s, s.glofas_max_m3s).statistic), 2)
        fl, rp, _ = flags[(gid, 5)]
        out.update(floods=int(fl.sum()), caught=int((fl & rp).sum()), fp=int((~fl & rp).sum()))
        per.append(out)
    cols = ["gauge", "area", "years", "mean_ratio", "q10_gauge", "q10_gauge_band", "fit_g", "q10_glofas", "q10_glofas_band",
            "fit_m", "ratio10", "rho", "floods", "caught", "fp"]
    pg = pd.DataFrame(per)[cols]; pg.to_csv(HERE / "results/per_gauge_1in5.csv", index=False)

    share = pg.caught / pg.floods
    r1 = stats.spearmanr(pg.rho, share); r2 = stats.spearmanr(pg.area, pg.ratio10); r3 = stats.spearmanr(pg.mean_ratio, pg.ratio10)
    ps = {"pair": pair,
          "rho_vs_share": [round(float(r1.statistic), 3), sig(r1.pvalue)],
          "area_vs_ratio10": [round(float(r2.statistic), 3), sig(r2.pvalue)],
          "meanratio_vs_ratio10": [round(float(r3.statistic), 3), sig(r3.pvalue)]}
    (HERE / "results/paper_stats.json").write_text(json.dumps(ps, indent=1))

    # Figure: skill at four levels
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(10, 3.8))
    x = np.arange(len(LEVELS)); lab = [f"1 in {t}" for t in LEVELS]
    for method, c, name in (("rp", GAUGE, "return period (model's own 1-in-T)"), ("abs", MODEL, "fixed flow (gauge level in m³/s)")):
        d = sk[sk.method == method]
        a1.plot(x, d.hit_rate, "-o", color=c, label=name); a1.plot(x, d.false_alarm_rate, "--o", color=c, alpha=0.55, ms=4)
        a2.plot(x, d.peirce, "-o", color=c)
    a1.set(xticks=x, xticklabels=lab, ylabel="rate", xlabel="trigger level", title="Hit rate (solid) and false-alarm rate (dashed)")
    a1.legend(fontsize=8); a1.set_ylim(0, None)
    a2.axhline(0, color=GREY, lw=0.8)
    a2.set(xticks=x, xticklabels=lab, ylabel="Peirce skill score", xlabel="trigger level", title="Skill: hit rate minus false-alarm rate")
    fig.tight_layout(); fig.savefig(HERE / "figures/gq_skill.png"); plt.close(fig)

    # Figure: rank correlation against share caught
    fig, ax = plt.subplots(figsize=(5.5, 4.1))
    ax.scatter(pg.rho, share, s=12 + pg.area / 80, color=GAUGE, edgecolor="white", lw=0.8, zorder=3)
    k = np.polyfit(pg.rho, share, 1); xx = np.array([pg.rho.min() - 0.03, pg.rho.max() + 0.03])
    ax.plot(xx, np.polyval(k, xx), "--", color=GREY, lw=1)
    for r in pg.itertuples():
        if r.rho >= 0.7 or r.rho <= 0.05:
            ax.annotate(r.gauge, (r.rho, r.caught / r.floods), xytext=(4, 3), textcoords="offset points", fontsize=7, color="#3b5260")
    ax.text(0.02, 0.97, f"Spearman ρ = {r1.statistic:.2f}, p < 0.001, {len(pg)} gauges", transform=ax.transAxes, fontsize=8,
            va="top", color="#3b5260")
    ax.set(xlabel="rank correlation of annual floods, gauge vs GloFAS", ylabel="share of flood years caught (1-in-5, return period)",
           ylim=(0, 1.02), title="Where the model ranks the big years well,\nthe trigger pays in the flood years")
    fig.savefig(HERE / "figures/gq_rho_share.png"); plt.close(fig)
    print(sk.to_string(index=False)); print(json.dumps(ps))


if __name__ == "__main__":
    main()
