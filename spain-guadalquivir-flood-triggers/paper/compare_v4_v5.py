"""GloFAS 4.0 against 5.0 on the same 14 gauges (MIT licence).

Run from the case folder:  python paper/compare_v4_v5.py
Matched: the 286 gauge-years both versions cover (water years 1998-2022), so the two are compared like for like.
Full v5: every year v5 and the gauges both cover (1985-2022).
Writes results/v4_v5_comparison.json, results/v4_v5_skill.csv and figures/gq_v4_v5.png.
"""
from __future__ import annotations

import json
import pathlib
import sys
import warnings

import numpy as np
import pandas as pd
from scipy import stats

HERE = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE))
import flood_tools as ft  # noqa: E402

warnings.filterwarnings("ignore")
LEVELS = [2, 5, 10, 25]


def sig(p):
    return float(f"{p:.2g}")


def analyse(am: pd.DataFrame, col: str) -> dict:
    N = len(am)
    fits, rows_g, flags = {}, [], {}
    for gid, s in am.groupby("gauge_id"):
        for src, c in (("gauge", "gauge_max_m3s"), ("model", col)):
            b, f = ft.fit_best(s[c].values); fits[(gid, src)] = f[b]
        lg10, lm10 = ft.level(fits[(gid, "gauge")], 10), ft.level(fits[(gid, "model")], 10)
        rows_g.append({"gauge_id": gid, "q10_gauge": lg10, "q10_model": lm10, "ratio10": lm10 / lg10, "rho": float(stats.spearmanr(s.gauge_max_m3s, s[col]).statistic)})
        for t in LEVELS:
            lg, lm = ft.level(fits[(gid, "gauge")], t), ft.level(fits[(gid, "model")], t)
            flags[(gid, t)] = (s.gauge_max_m3s.values >= lg, s[col].values >= lm, s[col].values >= lg)
    g = pd.DataFrame(rows_g)
    ids = sorted(am.gauge_id.unique())
    skill, pair = [], {}
    for t in LEVELS:
        fl = np.concatenate([flags[(i, t)][0] for i in ids])
        for m, k in (("return period", 1), ("fixed m3/s", 2)):
            pdv = np.concatenate([flags[(i, t)][k] for i in ids])
            h, mi, f, c = int((fl & pdv).sum()), int((fl & ~pdv).sum()), int((~fl & pdv).sum()), int((~fl & ~pdv).sum())
            K, n = h + mi, h + f
            skill.append({"T": t, "written_as": m, "hits": h, "misses": mi, "false_payouts": f, "hit_rate": round(h / K, 3),
                          "false_alarm_rate": round(f / (f + c), 3), "false_payout_share": round(f / n, 3) if n else None,
                          "peirce": round(h / K - f / (f + c), 3), "p_vs_chance": sig(stats.hypergeom.sf(h - 1, N, K, n))})
        rp = np.concatenate([flags[(i, t)][1] for i in ids]); ab = np.concatenate([flags[(i, t)][2] for i in ids])
        b, cc = int((fl & rp & ~ab).sum()), int((fl & ab & ~rp).sum())
        pair[str(t)] = {"rp_only": b, "abs_only": cc, "mcnemar_p": sig(stats.binomtest(b, b + cc, .5).pvalue) if b + cc else 1.0}
    share = []
    for i in ids:
        fl, rp, _ = flags[(i, 5)]; share.append((fl & rp).sum() / max(fl.sum(), 1))
    r = stats.spearmanr(g.rho, share)
    return {"gauge_years": N, "median_ratio10": round(float(g.ratio10.median()), 3),
            "gauges_ratio10_within_x2": int(((g.ratio10 >= .5) & (g.ratio10 <= 2)).sum()),
            "median_rank_corr": round(float(g.rho.median()), 3), "rho_vs_share_caught": [round(float(r.statistic), 3), sig(r.pvalue)],
            "per_gauge": g.round(3).to_dict("records"), "skill": skill, "pair": pair}


def figure(out):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    plt.rcParams.update({"figure.dpi": 150, "axes.grid": True, "grid.color": "#dfe8e8", "axes.spines.top": False, "axes.spines.right": False,
                         "font.size": 10, "axes.titleweight": "bold", "axes.titlesize": 11, "legend.frameon": False, "savefig.bbox": "tight", "savefig.facecolor": "white"})
    V4, V5, GREY = "#eb6834", "#2a78d6", "#898781"
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(11, 4.4), gridspec_kw={"width_ratios": [1, 1.15]})
    d = np.array([2, 2000.0]); a1.fill_between(d, d / 2, d * 2, color="#2a78d6", alpha=.08, lw=0); a1.plot(d, d, color=GREY, lw=1)
    for key, col, lab in (("matched_v4", V4, "GloFAS 4.0"), ("matched_v5", V5, "GloFAS 5.0")):
        g = pd.DataFrame(out[key]["per_gauge"])
        a1.scatter(g.q10_gauge, g.q10_model, s=34, color=col, edgecolor="white", lw=.8, label=f"{lab} (median ratio {out[key]['median_ratio10']:.2f})", zorder=3)
    a1.set(xscale="log", yscale="log", xlim=(4, 1000), ylim=(2, 1000), xlabel="10-year flood at the gauge (m³/s)", ylabel="10-year flood in the model (m³/s)",
           title="The 10-year flood, gauge against model"); a1.legend(loc="upper left", fontsize=8)
    lab = ["return period\n(model's own 1-in-5)", "fixed m³/s\n(gauge's 1-in-5)"]; x = np.arange(2); w = .2
    for i, (key, col, name) in enumerate((("matched_v4", V4, "4.0"), ("matched_v5", V5, "5.0"))):
        sk = [r for r in out[key]["skill"] if r["T"] == 5]
        for j, (vals, alpha, what) in enumerate((([r["hits"] for r in sk], 1, "flood years paid"), ([r["false_payouts"] for r in sk], .35, "false payouts"))):
            xs = x + (i * 2 + j - 1.5) * w
            a2.bar(xs, vals, w * .92, color=col, alpha=alpha, label=f"GloFAS {name}: {what}")
            for xi, v in zip(xs, vals): a2.text(xi, v + .8, str(v), ha="center", fontsize=8.5, color=col, fontweight="bold")
    a2.set(xticks=x, xticklabels=lab, ylim=(0, 48), ylabel="gauge-years (60 flood years in all)", title="Same 286 gauge-years, 1-in-5 trigger")
    a2.legend(loc="upper right", fontsize=7.5, ncol=2)
    fig.tight_layout(); fig.savefig(HERE / "figures/gq_v4_v5.png"); plt.close(fig)


def main():
    am4 = pd.read_csv(HERE / "data/annual_maxima.csv")
    am5 = pd.read_csv(HERE / "data/annual_maxima_v5.csv")
    matched = am4.merge(am5[["gauge_id", "water_year", "glofas5_max_m3s"]], on=["gauge_id", "water_year"])
    assert len(matched) == len(am4) == 286
    out = {"matched_v4": analyse(matched, "glofas_max_m3s"), "matched_v5": analyse(matched, "glofas5_max_m3s"),
           "full_v5": analyse(am5, "glofas5_max_m3s")}
    (HERE / "results/v4_v5_comparison.json").write_text(json.dumps(out, indent=1))
    rows = [dict(r, set=k) for k in out for r in out[k]["skill"]]
    pd.DataFrame(rows)[["set", "T", "written_as", "hits", "misses", "false_payouts", "hit_rate", "false_alarm_rate", "false_payout_share", "peirce", "p_vs_chance"]].to_csv(HERE / "results/v4_v5_skill.csv", index=False)
    figure(out)
    for k, v in out.items():
        s5 = [r for r in v["skill"] if r["T"] == 5]
        print(f"{k}: {v['gauge_years']} gauge-years, median ratio10 {v['median_ratio10']}, within x2 {v['gauges_ratio10_within_x2']}, median rho {v['median_rank_corr']}, rho-vs-share {v['rho_vs_share_caught']}")
        for r in s5: print("   1-in-5", r["written_as"], r["hits"], "/", r["hits"] + r["misses"], "fp", r["false_payouts"], "Peirce", r["peirce"], "p", r["p_vs_chance"])
        print("   McNemar 1-in-5", v["pair"]["5"])


if __name__ == "__main__":
    main()
