"""Builds the three Zeerijp-3A notebooks (run: python make_notebooks.py, then execute them)."""
import nbformat as nbf
def nb(cells):
    n = nbf.v4.new_notebook(); n.cells = [nbf.v4.new_markdown_cell(c[1]) if c[0] == "md" else nbf.v4.new_code_cell(c[1]) for c in cells]
    n.metadata["kernelspec"] = {"name": "python3", "display_name": "Python 3", "language": "python"}; return n
COMMON = """import json, pathlib, warnings
import numpy as np, pandas as pd, matplotlib.pyplot as plt, lasio
import subsurface_tools as kt
warnings.filterwarnings("ignore")
plt.rcParams.update({"figure.dpi": 110, "axes.grid": False, "axes.spines.top": False, "axes.spines.right": False, "font.size": 10,
                     "axes.titleweight": "bold", "axes.titlesize": 11, "legend.frameon": False, "savefig.bbox": "tight", "savefig.facecolor": "white"})
SAND, MUD, INK = "#d9a441", "#5b4237", "#1f2a36"
pathlib.Path("results").mkdir(exist_ok=True); pathlib.Path("figures").mkdir(exist_ok=True)
core_file = kt.fetch_nlog("core"); log_file = kt.fetch_nlog("logs"); sonic_file = kt.fetch_nlog("sonic")
plugs = kt.read_zrp_plugs(core_file)
print(len(plugs), "plug measurements from", plugs.sheet.nunique(), "sheets")"""

nb1 = nb([
("md", """# 1 · Core quality control and rock typing: Zeerijp-3A, Groningen Rotliegend

**Question.** Can a few rock types, defined from core porosity and permeability, predict permeability better than one porosity–permeability trend?

**Data.** Routine core analysis of well **ZEERIJP-03-SIDETRACK1 (ZRP-3A)**, operated by NAM and drilled in 2015 into the Rotliegend (Slochteren) sandstone of the Groningen field, published by the Dutch government on [NLOG](https://www.nlog.nl). 199.8 m of core in 8 runs. The notebook downloads the public file from NLOG and checks its SHA-256; the raw file is not copied into this repository.

**Method.** Quality control of the plugs, then the flow zone indicator (FZI) of Amaefule et al. (1993) and Gaussian-mixture rock types on log(FZI), with the number of types chosen by the Bayesian information criterion (BIC). This is the KAI-Subsurface rock typing workflow."""),
("code", COMMON),
("md", "## Quality control\nPlugs described as fractured, broken, cracked or disintegrated measure the damage, not the rock, and are set aside. Permeabilities reported as below the 0.01 mD detection limit are kept as a count but not in the fits."),
("code", """h = plugs[(plugs.orient == "H") & plugs.k_kl.notna() & (plugs.k_kl > 0) & plugs.phi.notna()]
qc = {"horizontal plugs with k": int(len(h)), "damaged (set aside)": int(h.damaged.sum()),
      "below 0.01 mD detection (all plugs)": int(plugs.k_below_detection.sum())}
h = h[~h.damaged].drop_duplicates("depth").sort_values("depth").copy()
qc["used"] = int(len(h)); print(qc)
print(h.groupby("core").size().rename("plugs per core").to_dict())"""),
("code", """fig, ax = plt.subplots(1, 3, figsize=(12, 6), sharey=True)
ax[0].plot(h.phi, h.depth, ".", ms=3, color=INK); ax[0].set_xlabel("porosity (-)"); ax[0].set_ylabel("depth (m along hole)"); ax[0].invert_yaxis()
ax[1].semilogx(h.k_kl, h.depth, ".", ms=3, color=SAND); ax[1].set_xlabel("Klinkenberg k (mD)")
v = plugs[(plugs.orient == "V") & plugs.k_kl.notna() & ~plugs.damaged]
ax[2].semilogx(v.k_kl, v.depth, "^", ms=4, color=MUD); ax[2].set_xlabel("vertical plug k (mD)")
fig.suptitle("ZRP-3A core: 8 cores, 3521-3867 m"); fig.tight_layout(); fig.savefig("figures/zrp_core_profile.png")"""),
("md", "## Flow zone indicator and rock types"),
("code", """h["RQI"], h["FZI"] = kt.fzi(h.phi, h.k_kl)
h["RT"], bic, n_rt = kt.rock_types(h.FZI, n=3)
_, bic, n_bic = kt.rock_types(h.FZI)
print("BIC by number of types:", {k: round(v, 1) for k, v in bic.items()}, "-> BIC choice", n_bic, "; used here:", n_rt)
fz = h.groupby("RT").FZI.apply(lambda s: float(np.exp(np.log(s).mean())))
print(pd.DataFrame({"plugs": h.RT.value_counts().sort_index(), "mean FZI (micron)": fz.round(2),
                    "median k (mD)": h.groupby("RT").k_kl.median().round(1), "median phi": h.groupby("RT").phi.median().round(3)}))"""),
("md", "**Why three types and not the BIC choice.** BIC prefers two types; a third splits off the tight, cemented sandstones (27 plugs) that behave differently in flow. Both are shown below; the choice is a geological one, checked against the plug descriptions."),
("code", """lk = np.log10(h.k_kl)
a = np.polyfit(h.phi, lk, 1); single = np.polyval(a, h.phi)
typed = np.log10(kt.k_from_fzi(h.phi, h.RT.map(fz)))
res1 = {"one trend: within x3": round(kt.within(single, lk), 3), "three rock types: within x3": round(kt.within(typed, lk), 3),
        "one trend: rmse log10 k": round(float(np.sqrt(np.mean((single - lk) ** 2))), 3),
        "three rock types: rmse log10 k": round(float(np.sqrt(np.mean((typed - lk) ** 2))), 3)}
print(res1)
fig, ax = plt.subplots(1, 2, figsize=(11, 4.6))
pp = np.linspace(.02, .34, 50)
RTC = {1: MUD, 2: "#b07a3b", 3: SAND}
for t in sorted(fz.index):
    s = h[h.RT == t]; ax[0].semilogy(s.phi, s.k_kl, "o", ms=3.5, alpha=.75, color=RTC[t], label=f"RT{t} (FZI {fz[t]:.2f})")
    ax[0].semilogy(pp, kt.k_from_fzi(pp, fz[t]), "-", lw=1.6, color=RTC[t])
ax[0].semilogy(pp, 10 ** np.polyval(a, pp), "k--", label="one trend"); ax[0].set_ylim(1e-3, 1e4)
ax[0].set_xlabel("porosity (-)"); ax[0].set_ylabel("k (mD)"); ax[0].legend(fontsize=8); ax[0].set_title("Rock types on the poro-perm plot")
ax[1].plot(lk, single, "o", ms=3, alpha=.45, color="#9aa7b4", label=f"one trend ({res1['one trend: within x3']:.0%} within x3)")
ax[1].plot(lk, typed, "o", ms=3, alpha=.6, color=SAND, label=f"rock types ({res1['three rock types: within x3']:.0%} within x3)")
ax[1].plot([-3, 4], [-3, 4], "k-", lw=.8); ax[1].set_xlabel("measured log10 k"); ax[1].set_ylabel("predicted log10 k"); ax[1].legend(fontsize=8)
fig.tight_layout(); fig.savefig("figures/zrp_rock_types.png")"""),
("md", "## Vertical against horizontal: what the plugs say about kv/kh"),
("code", """v = plugs[(plugs.orient == "V") & plugs.k_kl.notna() & ~plugs.damaged].sort_values("depth")
pair = pd.merge_asof(v, h[["depth", "k_kl"]], on="depth", direction="nearest", tolerance=0.3, suffixes=("_v", "_h")).dropna(subset=["k_kl_h"])
pair["kv_kh"] = pair.k_kl_v / pair.k_kl_h
kvkh = {"pairs within 0.3 m": int(len(pair)), "P10": round(float(pair.kv_kh.quantile(.1)), 3),
        "P50": round(float(pair.kv_kh.median()), 3), "P90": round(float(pair.kv_kh.quantile(.9)), 3)}
print(kvkh)"""),
("md", "At plug scale the sandstone is close to isotropic (median kv/kh about 1). That does **not** mean the reservoir is: the plugs are cut from sandstone, and the claystone laminae that control vertical flow are rarely plugged (9 of 10 claystone plugs measured below 0.01 mD). Notebook 3 takes this to the bed scale."),
("code", """h[["depth", "core", "phi", "k_kl", "FZI", "RT", "remark"]].to_csv("results/zrp3a_rock_types.csv", index=False)
json.dump({"qc": qc, "rock_types": {str(k): {"plugs": int((h.RT == k).sum()), "fzi": round(v, 3)} for k, v in fz.items()},
           "bic_choice": int(n_bic), "core_level": res1, "plug_kv_kh": kvkh}, open("results/nb1_rock_types.json", "w"), indent=1)
assert res1["three rock types: within x3"] > res1["one trend: within x3"]"""),
("md", """## Result and limits
Three rock types reproduce the measured permeability within a factor of 3 for most plugs, clearly better than one trend. The rock types still need porosity **and** permeability, so they only exist where there is core. Notebook 2 asks how well they can be predicted from logs alone, in uncored intervals or wells.

*References:* Amaefule, J.O. et al. (1993) SPE 26436 · Data: NAM / NLOG, public under the Dutch Mining Act."""),
])

nb2 = nb([
("md", """# 2 · Permeability from logs, tested blind: Zeerijp-3A

**Question.** In a well or interval without core, how well can permeability be predicted from logs, and how much do rock types help?

**Test.** *Leave one core out*: each of the cored intervals is hidden in turn, the methods are trained on the others, and their prediction for the hidden core is compared with its plugs. Three methods: (A) one trend of log k on log density porosity; (B) rock types predicted from logs by a random forest, then k from each type's FZI; (C) a random forest that predicts log k directly from the logs.

**Logs.** Density, neutron, photoelectric, gamma ray, induction resistivity and sonic of ZRP-3A (Schlumberger runs of 18 Aug 2015), from NLOG."""),
("code", COMMON + """
L = lasio.read(log_file, engine="normal").df().reset_index().sort_values("DEPTH")
S = lasio.read(sonic_file, engine="normal").df().reset_index()[["DEPTH", "MCDT"]].sort_values("DEPTH")
L = pd.merge_asof(L, S, on="DEPTH", direction="nearest", tolerance=0.06)
L.loc[(L.DPOR < -20) | (L.DPOR > 60), "DPOR"] = np.nan   # tool start-up values
feats = ["GRGC", "DEN", "NPOR", "DPOR", "RILD", "PDPE", "MCDT"]
print(L[["DEPTH"] + feats].describe().loc[["min", "max"]].round(2))"""),
("md", "## Depth match\nCore depths are driller's depths; logs are wireline depths. The shift that best lines up core porosity with log density porosity is searched in 0.1 m steps."),
("code", """h = plugs[(plugs.orient == "H") & plugs.k_kl.notna() & (plugs.k_kl > 0) & plugs.phi.notna() & ~plugs.damaged].drop_duplicates("depth").sort_values("depth").copy()
best = max(((round(s, 1), pd.merge_asof(h.assign(D=h.depth + s).sort_values("D"), L, left_on="D", right_on="DEPTH", direction="nearest", tolerance=0.06)
           .pipe(lambda m: m.phi.corr(m.DPOR))) for s in np.arange(-3, 3.01, 0.1)), key=lambda t: t[1])
print("best shift (m):", best[0], " correlation core phi vs log DPOR:", round(best[1], 3))
m = pd.merge_asof(h.assign(D=h.depth + best[0]).sort_values("D"), L, left_on="D", right_on="DEPTH", direction="nearest", tolerance=0.06).dropna(subset=feats)
m["RQI"], m["FZI"] = kt.fzi(m.phi, m.k_kl); m["RT"], _, _ = kt.rock_types(m.FZI, n=3); m["lk"] = np.log10(m.k_kl)
print(len(m), "plugs with a full log suite, cores", sorted(m.core.unique()))"""),
("code", """from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
rows = []
for c in sorted(m.core.unique()):
    tr, te = m[m.core != c], m[m.core == c]
    a = np.polyfit(tr.DPOR / 100, tr.lk, 1)
    clf = RandomForestClassifier(400, min_samples_leaf=3, random_state=0).fit(tr[feats], tr.RT)
    fzt = tr.groupby("RT").FZI.apply(lambda s: np.exp(np.log(s).mean()))
    rtp = clf.predict(te[feats])
    reg = RandomForestRegressor(400, min_samples_leaf=3, random_state=0).fit(tr[feats], tr.lk)
    rows.append(pd.DataFrame({"depth": te.depth, "core": c, "obs": te.lk, "rt": te.RT, "rt_pred": rtp,
        "A_trend": np.polyval(a, te.DPOR / 100),
        "B_rocktypes": np.log10(kt.k_from_fzi((te.DPOR / 100).clip(.02, .4), pd.Series(rtp, index=te.index).map(fzt))),
        "C_forest": reg.predict(te[feats])}))
B = pd.concat(rows)
blind = {k: {"within x3": round(kt.within(B[k], B.obs), 3), "within x10": round(kt.within(B[k], B.obs, 10), 3),
             "rmse log10 k": round(float(np.sqrt(np.mean((B[k] - B.obs) ** 2))), 3)} for k in ["A_trend", "B_rocktypes", "C_forest"]}
blind["rock type from logs: accuracy"] = round(float((B.rt == B.rt_pred).mean()), 3)
print(json.dumps(blind, indent=1))"""),
("code", """fig, ax = plt.subplots(1, 2, figsize=(11, 4.6))
for k, c in [("A_trend", "#9aa7b4"), ("C_forest", SAND)]:
    ax[0].plot(B.obs, B[k], ".", ms=3, alpha=.6, color=c, label=f"{k}: {blind[k]['within x3']:.0%} within x3")
ax[0].plot([-3, 4], [-3, 4], "k-", lw=.8); ax[0].set_xlabel("measured log10 k (hidden core)"); ax[0].set_ylabel("predicted from logs"); ax[0].legend(fontsize=8)
ax[0].set_title("Blind test, one core hidden at a time")
w = pd.Series({k: blind[k]["within x3"] for k in ["A_trend", "B_rocktypes", "C_forest"]})
ax[1].bar(["one trend", "rock types\\nfrom logs", "random forest"], w.values, color=["#9aa7b4", "#b07a3b", SAND])
ax[1].set_ylim(0, 1); ax[1].set_ylabel("share of plugs within a factor of 3"); ax[1].set_title("Logs only, uncored case")
fig.tight_layout(); fig.savefig("figures/zrp_blind_test.png")"""),
("md", "## The deliverable: a permeability log with its uncertainty\nTrained on all cores, the forest predicts k every 0.1 m over the logged interval. The band is the spread of the individual trees, widened to match the blind-test error."),
("code", """reg = RandomForestRegressor(400, min_samples_leaf=3, random_state=0).fit(m[feats], m.lk)
W = L.dropna(subset=feats).copy(); trees = np.stack([t.predict(W[feats].values) for t in reg.estimators_])
W["k50"] = 10 ** np.median(trees, 0); spread = trees.std(0)
lo, hi = m[feats].quantile(.01), m[feats].quantile(.99)
W["inside"] = ((W[feats] >= lo) & (W[feats] <= hi)).all(axis=1)   # log responses seen in the cored rock
scale = blind["C_forest"]["rmse log10 k"] / float(np.sqrt(np.mean(spread ** 2)))
W["k10"] = 10 ** (np.log10(W.k50) - 1.28 * spread * scale); W["k90"] = 10 ** (np.log10(W.k50) + 1.28 * spread * scale)
fig, ax = plt.subplots(1, 3, figsize=(10, 8), sharey=True)
ax[0].plot(W.GRGC, W.DEPTH, lw=.6, color="#4c7a3d"); ax[0].set_xlabel("GR (API)"); ax[0].invert_yaxis(); ax[0].set_ylabel("depth (m)")
ax[1].plot(W.DPOR / 100, W.DEPTH, lw=.6, color=INK, label="log"); ax[1].plot(h.phi, h.depth + best[0], "o", ms=2, color=SAND, label="core"); ax[1].set_xlabel("porosity"); ax[1].legend(fontsize=7)
Wi = W.where(W.inside); Wo = W.where(~W.inside)
ax[2].fill_betweenx(W.DEPTH, Wi.k10, Wi.k90, color=SAND, alpha=.35, lw=0, label="P10-P90"); ax[2].semilogx(Wi.k50, W.DEPTH, lw=.7, color="#8a5a1f", label="P50 from logs")
ax[2].semilogx(Wo.k50, W.DEPTH, lw=.7, color="0.7", label="outside the cored rock (not trusted)")
ax[2].semilogx(h.k_kl, h.depth + best[0], ".", ms=2, color="k", label="core plugs"); ax[2].set_xlabel("k (mD)"); ax[2].legend(fontsize=7)
fig.suptitle("ZRP-3A: permeability from logs with uncertainty"); fig.tight_layout(); fig.savefig("figures/zrp_k_log.png")
print(f"{W.inside.mean():.0%} of the logged interval has log responses inside the range of the cored rock")
W[["DEPTH", "k10", "k50", "k90", "inside"]].round(4).to_csv("results/zrp3a_k_from_logs.csv", index=False)"""),
("code", """json.dump({"depth_shift_m": best[0], "core_log_phi_corr": round(best[1], 3), "blind_test": blind, "plugs": int(len(m))},
          open("results/nb2_blind_test.json", "w"), indent=1)
assert blind["C_forest"]["within x3"] >= blind["A_trend"]["within x3"] - 0.05"""),
("md", """## Result and limits
From logs alone, about 6 in 10 plugs of a hidden core are predicted within a factor of 3. Rock types predicted from logs do not beat the simpler methods here: the logs (about 0.5 m vertical resolution) cannot see the centimetre laminae that separate the types. That is the honest limit to state to a client, and the reason the product reports P10–P90, not one number. The gain from rock typing is real where there is core (notebook 1)."""),
])

nb3 = nb([
("md", """# 3 · Bedding templates, the representative elementary volume and upscaling (calibrated on Zeerijp-3A)

**Question.** Plugs are 3.8 cm across; reservoir grid blocks are tens of metres. At what size does permeability stop depending on the sample (the *representative elementary volume*, REV), and how wrong are plug values for vertical flow?

**Method** (after Nordahl and Ringrose, 2008; an SBED-style workflow with open tools). Ripple-laminated bedding templates are built from sets of asymmetric current ripples with mud drapes that thicken in the troughs: flaser bedding when mud is scarce, wavy bedding, and lenticular bedding when sand survives only as ripple lenses. Sand and mud permeabilities come from the Zeerijp-3A plugs. For windows of growing size the effective kx and kz are computed by solving single-phase flow (no-flow sides); the spread between ten realisations shows when the REV is reached."""),
("code", COMMON + """
r = plugs.remark.astype(str).str.lower()
clean = plugs[(plugs.orient == "H") & plugs.k_kl.notna() & ~plugs.damaged & r.str.contains("sst") & ~r.str.contains("lam|cement")]
clay = plugs[r.str.contains("claystone|siltstone") & ~r.str.contains("clast")]
k_sand = float(clean.k_kl.median()); k_mud = 0.005   # most claystone plugs are below the 0.01 mD detection limit
print(f"clean sandstone plugs: {len(clean)}, median k {k_sand:.1f} mD; claystone/siltstone plugs: {len(clay)}, "
      f"{int(clay.k_below_detection.sum())} below 0.01 mD -> mud k set to {k_mud} mD")"""),
("md", "## The bedding templates\nThree templates rendered as 3D blocks. The same generator, cut as 1 m x 1 m vertical sections at 5 mm, is used for the flow calculations below."),
("code", """def block_k(mf, seed=0):
    mud, _ = kt.calibrated_bedding(200, 1, 200, mf, seed=seed)
    k = np.where(mud[:, 0, :], k_mud, k_sand); return kt.keff(k, "x"), kt.keff(k, "z")
labels = []
for mf in (0.12, 0.35, 0.62):
    kx, kz = block_k(mf); labels.append(f"kx {kx:.1f} mD · kz {kz:.3f} mD · kv/kh {kz/kx:.4f}")
kt.bedding_figure("figures/bedding_blocks.png", kvals=labels)
from IPython.display import Image; Image("figures/bedding_blocks.png")"""),
("code", """mud_fractions = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6]; sizes = np.unique(np.round(np.geomspace(8, 200, 14)).astype(int)); cell = 0.005; NR = 10
def lab_plugs(mud2d, n=8, count=20, seed=0):
    # vertical plugs (n cells, 4 cm) cut where a lab would: in the cleanest sandstone of a few candidate spots
    g = np.random.default_rng(seed); out = []
    for _ in range(count):
        best = None
        for _ in range(60):
            i, j = g.integers(0, mud2d.shape[1] - n), g.integers(0, mud2d.shape[0] - n); w = mud2d[j:j + n, i:i + n]
            if best is None or w.mean() < best.mean(): best = w
            if w.mean() <= 0.05: break
        out.append(kt.keff(np.where(best, k_mud, k_sand), "z"))
    return out
rows, plugk = [], {}
for mf in mud_fractions:
    for rlz in range(NR):
        mud, _ = kt.calibrated_bedding(200, 1, 200, mf, seed=100 * int(mf * 10) + rlz)
        rs = kt.rev_scan(np.where(mud[:, 0, :], k_mud, k_sand), sizes); rs["mud"] = mf; rs["rlz"] = rlz; rows.append(rs)
        plugk.setdefault(mf, []).extend(lab_plugs(mud[:, 0, :], seed=rlz))
R = pd.concat(rows); R["size_m"] = R.cells * cell
stats = R.groupby(["mud", "size_m"]).agg(kx=("kx", "mean"), kz=("kz", "mean"), cvx=("kx", lambda s: s.std() / s.mean()),
                                          cvz=("kz", lambda s: s.std() / s.mean())).reset_index()
def rev(cv, th):
    for i in range(len(cv)):
        if (cv.values[i:] < th).all(): return float(cv.index[i])
    return None
summary = []
for mf, g in stats.groupby("mud"):
    g = g.set_index("size_m"); plug = R[(R.mud == mf) & (R.cells == sizes[0])]; full = g.iloc[-1]
    summary.append({"mud fraction": mf, "kx 1 m (mD)": round(full.kx, 2), "kz 1 m (mD)": round(full.kz, 4), "kv/kh 1 m": round(full.kz / full.kx, 5),
                    "REV kx (m)": rev(g.cvx, 0.1), "REV kz (m)": rev(g.cvz, 0.5),
                    "random plug kz P90 / bed kz": round(float(plug.kz.quantile(.9) / full.kz), 1),
                    "lab plug kz median / bed kz": round(float(np.median(plugk[mf]) / full.kz), 1)})
summary = pd.DataFrame(summary); print(summary.to_string(index=False))"""),
("md", "## Permeability against sample size\nEach line is one realisation of wavy bedding (35 % mud), measured in windows of growing size centred on the section. The dots are 4 cm plugs cut where a laboratory would cut them, in the cleanest sandstone: they sit two to three orders of magnitude above the bed-scale vertical permeability."),
("code", """Wm = [kt.calibrated_bedding(200, 1, 200, 0.35, seed=500 + i)[0][:, 0, :] for i in range(12)]
W = pd.concat([kt.rev_scan(np.where(m2, k_mud, k_sand), sizes).assign(rlz=i) for i, m2 in enumerate(Wm)])
LP = np.concatenate([lab_plugs(m2, count=6, seed=i) for i, m2 in enumerate(Wm)])
W["size_m"] = W.cells * cell
fig, ax = plt.subplots(1, 3, figsize=(14, 4.2))
for i, g in W.groupby("rlz"):
    ax[0].loglog(g.size_m, g.kx, color=SAND, lw=1.2, alpha=.8); ax[1].loglog(g.size_m, g.kz, color=MUD, lw=1.2, alpha=.8)
ax[1].scatter(0.04 * np.exp(np.random.default_rng(1).normal(0, .08, len(LP))), LP, s=16, color=SAND, edgecolor=INK, lw=.4, zorder=5, label="plugs cut in sandstone")
ax[1].legend(loc="center right", fontsize=8, frameon=False)
for a_, t in zip(ax[:2], ["Horizontal permeability kx", "Vertical permeability kz"]):
    a_.axvspan(0.03, 0.045, color="#e8eef4"); a_.text(0.037, a_.get_ylim()[0] * 1.15, "plug", ha="center", fontsize=8, color="#555")
    a_.set_xlabel("sample size (m)"); a_.set_ylabel("effective k (mD)"); a_.set_title(t, loc="left")
m_ = np.array(mud_fractions); ari = (1 - m_) * k_sand + m_ * k_mud; har = 1 / ((1 - m_) / k_sand + m_ / k_mud); geo = k_sand ** (1 - m_) * k_mud ** m_
ax[2].semilogy(m_, ari, color="#999", lw=1, ls="--"); ax[2].semilogy(m_, geo, color="#999", lw=1, ls=":"); ax[2].semilogy(m_, har, color="#999", lw=1, ls="-.")
ax[2].semilogy(m_, summary["kx 1 m (mD)"], "o-", color=SAND, lw=2.2, ms=6, label="kx at 1 m"); ax[2].semilogy(m_, summary["kz 1 m (mD)"], "s-", color=MUD, lw=2.2, ms=6, label="kz at 1 m")
for y, t in [(ari[-1], "arithmetic"), (geo[-1], "geometric"), (har[-1], "harmonic")]: ax[2].text(m_[-1] + .01, y, t, fontsize=8, color="#777", va="center")
ax[2].set_xlim(.08, .72); ax[2].set_xlabel("mud fraction"); ax[2].set_ylabel("effective k (mD)"); ax[2].set_title("Which average applies", loc="left"); ax[2].legend(loc="lower left")
fig.tight_layout(); fig.savefig("figures/rev_upscaling.png", dpi=150)"""),
("code", """summary.to_csv("results/rev_summary.csv", index=False)
json.dump({"k_sand_mD": round(k_sand, 2), "k_mud_mD": k_mud, "cell_m": cell, "realisations": NR, "template": "ripple-laminated (flaser-wavy-lenticular)",
           "summary": summary.to_dict("records")}, open("results/nb3_rev.json", "w"), indent=1, default=float)
mid = summary[summary["mud fraction"].between(0.2, 0.4)]
assert mid["kv/kh 1 m"].max() < 0.2 and mid["lab plug kz median / bed kz"].min() > 10"""),
("md", """## Result and limits
* Horizontal permeability settles within decimetres in sand-rich bedding and stays close to the arithmetic average; it needs longer windows as mud increases.
* Vertical permeability is the problem. A plug cut where a laboratory cuts it, in competent sandstone, overstates bed-scale kz by one to three orders of magnitude in wavy bedding (column `lab plug kz median / bed kz`); random plugs scatter both ways (`random plug kz P90 / bed kz`), and bed-scale kv/kh falls far below the plug value of about 1 (notebook 1). kz moves from the geometric towards the harmonic average as mud increases: the flow upscaling regimes of Ringrose et al. (2005).
* Limits: 2D sections for the flow, one ripple geometry, two components. Real templates come from the core description of each facies; the workflow, not these exact numbers, is what transfers to a client's core.

*References:* Nordahl, K. and Ringrose, P.S. (2008) Math. Geosci. 40, 753-771 · Ringrose, P.S., Nordahl, K. and Wen, R. (2005) Petroleum Geoscience 11, 29–36."""),
])
for name, n in [("01_core_qc_rock_typing.ipynb", nb1), ("02_permeability_from_logs_blind_test.ipynb", nb2), ("03_bedding_rev_upscaling.ipynb", nb3)]:
    nbf.write(n, name)
print("written")
