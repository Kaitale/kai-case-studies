"""Export the Zeerijp-3A results to one compact JSON for the interactive case page on the KAI website."""
import json, warnings
import numpy as np, pandas as pd, lasio
import subsurface_tools as kt
from sklearn.ensemble import RandomForestRegressor
warnings.filterwarnings("ignore")
plugs = kt.read_zrp_plugs(kt.fetch_nlog("core"))
L = lasio.read(kt.fetch_nlog("logs"), engine="normal").df().reset_index().sort_values("DEPTH")
S = lasio.read(kt.fetch_nlog("sonic"), engine="normal").df().reset_index()[["DEPTH", "MCDT"]].sort_values("DEPTH")
L = pd.merge_asof(L, S, on="DEPTH", direction="nearest", tolerance=0.06)
L.loc[(L.DPOR < -20) | (L.DPOR > 60), "DPOR"] = np.nan
feats = ["GRGC", "DEN", "NPOR", "DPOR", "RILD", "PDPE", "MCDT"]
nb1 = json.load(open("results/nb1_rock_types.json")); nb2 = json.load(open("results/nb2_blind_test.json")); nb3 = json.load(open("results/nb3_rev.json"))
shift = nb2["depth_shift_m"]
h = plugs[(plugs.orient == "H") & plugs.k_kl.notna() & (plugs.k_kl > 0) & plugs.phi.notna() & ~plugs.damaged].drop_duplicates("depth").sort_values("depth").copy()
h["RQI"], h["FZI"] = kt.fzi(h.phi, h.k_kl); h["RT"], _, _ = kt.rock_types(h.FZI, n=3)
fz = h.groupby("RT").FZI.apply(lambda s: float(np.exp(np.log(s).mean())))
lk = np.log10(h.k_kl); a = np.polyfit(h.phi, lk, 1)
h["pred_trend"] = np.polyval(a, h.phi); h["pred_rt"] = np.log10(kt.k_from_fzi(h.phi, h.RT.map(fz)))
# blind test, leave one core out (same as notebook 2, forest and trend)
m = pd.merge_asof(h.assign(D=h.depth + shift).sort_values("D"), L, left_on="D", right_on="DEPTH", direction="nearest", tolerance=0.06).dropna(subset=feats)
m["lk"] = np.log10(m.k_kl); rows = []
for c in sorted(m.core.unique()):
    tr, te = m[m.core != c], m[m.core == c]
    aa = np.polyfit(tr.DPOR / 100, tr.lk, 1)
    reg = RandomForestRegressor(400, min_samples_leaf=3, random_state=0).fit(tr[feats], tr.lk)
    rows.append(pd.DataFrame({"core": c, "obs": te.lk, "trend": np.polyval(aa, te.DPOR / 100), "forest": reg.predict(te[feats])}))
B = pd.concat(rows)
W = pd.read_csv("results/zrp3a_k_from_logs.csv")
Lw = pd.merge_asof(W.sort_values("DEPTH"), L[["DEPTH", "GRGC", "DPOR"]], on="DEPTH", direction="nearest", tolerance=0.06)
Lw = Lw.iloc[::2]   # 0.2 m for display
v = plugs[(plugs.orient == "V") & plugs.k_kl.notna() & ~plugs.damaged].sort_values("depth")
pair = pd.merge_asof(v, h[["depth", "k_kl"]], on="depth", direction="nearest", tolerance=0.3, suffixes=("_v", "_h")).dropna(subset=["k_kl_h"])
r = lambda x, n: [None if pd.isna(y) else round(float(y), n) for y in x]
out = {
  "well": "ZEERIJP-03-SIDETRACK1 (ZRP-3A)", "source": "NAM, via NLOG (www.nlog.nl)", "depth_shift_m": shift,
  "log": {"depth": r(Lw.DEPTH, 1), "gr": r(Lw.GRGC, 1), "phi": r(Lw.DPOR / 100, 3), "k10": r(Lw.k10, 3), "k50": r(Lw.k50, 3), "k90": r(Lw.k90, 3), "inside": [int(b) for b in Lw.inside]},
  "plugs": {"depth": r(h.depth + shift, 2), "phi": r(h.phi, 3), "k": r(h.k_kl, 3), "rt": [int(x) for x in h.RT], "core": [int(x) for x in h.core],
            "pred_trend": r(h.pred_trend, 3), "pred_rt": r(h.pred_rt, 3)},
  "rock_types": {str(k): {"fzi": round(float(fv), 3), "plugs": int((h.RT == k).sum()), "median_k": round(float(h[h.RT == k].k_kl.median()), 2)} for k, fv in fz.items()},
  "trend": [round(float(a[0]), 4), round(float(a[1]), 4)],
  "core_level": nb1["core_level"],
  "blind": {"summary": nb2["blind_test"], "core": [int(x) for x in B.core], "obs": r(B.obs, 3), "trend": r(B.trend, 3), "forest": r(B.forest, 3)},
  "kvkh_pairs": r(pair.k_kl_v / pair.k_kl_h, 4),
  "rev": [{k: (None if isinstance(v, float) and v != v else v) for k, v in row.items()} for row in nb3["summary"]], "k_sand": nb3["k_sand_mD"],
}
json.dump(out, open("results/zeerijp-3a-web.json", "w"), separators=(",", ":"), allow_nan=False)
import os; print(os.path.getsize("results/zeerijp-3a-web.json"), "bytes;", len(Lw), "log rows;", len(h), "plugs;", len(B), "blind")
print({k: round(kt.within(B[k], B.obs), 3) for k in ["trend", "forest"]}, nb2["blind_test"]["C_forest"]["within x3"])
