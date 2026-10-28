"""Rhine-Meuse delta block for the KAI Heterogeneity Lab: GeoTOP v1.6.1 voxels + BRO BHR-G borehole descriptions.
Block: RD x 122.0-130.0 km, y 427.0-433.0 km, voxel centres z -9.0 .. -2.5 m NAP (100 x 100 x 0.5 m)."""
import netCDF4, numpy as np, json, re, glob, base64, hashlib
X0, X1, Y0, Y1 = 122000, 130000, 427000, 433000
ZC = np.arange(-9.0, -2.49, 0.5)
ds = netCDF4.Dataset("https://www.dinodata.nl/opendap/GeoTOP/geotop.nc"); ds.set_auto_mask(False)
x = ds["x"][:]; y = ds["y"][:]; z = ds["z"][:]
ix = np.where((x >= X0) & (x < X1))[0]; iy = np.where((y >= Y0) & (y < Y1))[0]; iz = np.where((z >= ZC[0] - 1e-6) & (z <= ZC[-1] + 1e-6))[0]
sl = (slice(ix[0], ix[-1] + 1), slice(iy[0], iy[-1] + 1), slice(iz[0], iz[-1] + 1))
print("x", x[ix[0]], x[ix[-1]], "y", y[iy[0]], y[iy[-1]], "z", z[iz[0]], z[iz[-1]])
lk = np.asarray(ds["lithok"][sl]).astype(int)
K = {i: np.asarray(ds[f"kans_{i}"][sl]).astype(float) for i in range(1, 10)}
for i in K: K[i][K[i] < 0] = 0
tot = sum(K.values()); print("prob sum range", np.percentile(tot[lk != -127], [1, 50, 99]))
pm = (K[1] + K[2]) / np.maximum(tot, 1); ph = K[3] / np.maximum(tot, 1); ps = (K[5] + K[6] + K[7] + K[8] + K[9]) / np.maximum(tot, 1)
fac = np.full(lk.shape, -1); fac[np.isin(lk, [0, 1, 2])] = 0; fac[lk == 3] = 1; fac[np.isin(lk, [5, 6, 7, 8, 9])] = 2
# arrays to (z, y, x) order, x fastest
to = lambda a: np.transpose(a, (2, 1, 0))
fac_z = to(fac); P = np.stack([to(pm), to(ph), to(ps)])
print("facies props", [(fac == c).mean().round(3) for c in (0, 1, 2)], "missing", (fac < 0).mean().round(4))
# ---- BRO boreholes
def facies_of(name):
    n = name.lower()
    if "nietgespecificeerd" in n and n.startswith("grond"): return -1
    if n.endswith("zand") or n.endswith("grind") or n.startswith("zand") or n.startswith("grind") or n.startswith("schelpen"):
        return 1 if "kleiig" in n else 2
    if n.endswith("leem"): return 1
    if n.endswith("klei"): return 1 if "zandige" in n else 0
    if n.endswith("veen") or n.startswith("veen") or n.startswith("klei"): return 0
    return -1
wells = []
for f in sorted(glob.glob("data/bhrg/*.xml")):
    s = open(f, encoding="utf-8").read()
    bid = re.search(r"<brocom:broId>(.*?)<", s).group(1)
    pos = re.search(r'deliveredLocation>.*?<gml:pos>(.*?)<', s, re.S)
    srs = re.search(r'deliveredLocation>.*?srsName="([^"]+)"', s, re.S)
    om = re.search(r'offset uom="m">(.*?)<', s)
    if not pos or not om or "28992" not in srs.group(1):
        continue
    off = float(om.group(1))
    X, Y = map(float, pos.group(1).split()[:2])
    if not (X0 <= X < X1 and Y0 <= Y < Y1): continue
    layers = []
    for L in re.findall(r"<bhrgcom:Layer .*?</bhrgcom:Layer>", s, re.S):
        u = float(re.search(r'upperBoundary uom="m">(.*?)<', L).group(1)); l = float(re.search(r'lowerBoundary uom="m">(.*?)<', L).group(1))
        nm = re.search(r"soilNameNEN5104[^>]*>(.*?)<", L)
        if nm: layers.append((off - u, off - l, facies_of(nm.group(1))))
    log = []
    for zc in ZC:
        top, bot = zc + 0.25, zc - 0.25; ov = {0: 0, 1: 0, 2: 0}; cov = 0
        for t, b, c in layers:
            o = max(0, min(t, top) - max(b, bot))
            if o > 0 and c >= 0: ov[c] += o
            if o > 0: cov += o
        log.append(max(ov, key=ov.get) if sum(ov.values()) >= 0.25 else -1)
    if sum(c >= 0 for c in log) < 4: continue
    col, row = int((X - X0) // 100), int((Y - Y0) // 100)
    wells.append({"id": bid, "x": round(X, 1), "y": round(Y, 1), "col": col, "row": row, "nap": off, "log": log})
# one borehole per column: keep the one with most described voxels
best = {}
for w in wells:
    k = (w["col"], w["row"]); n = sum(c >= 0 for c in w["log"])
    if k not in best or n > sum(c >= 0 for c in best[k]["log"]): best[k] = w
wells = sorted(best.values(), key=lambda w: w["id"])
L = np.array([w["log"] for w in wells]); print("wells", len(wells), "described voxels", (L >= 0).sum(), "props", [((L == c).sum() / (L >= 0).sum()).round(3) for c in (0, 1, 2)])
# agreement of GeoTOP most-likely class with the borehole at the same voxel
agree = [fac_z[k, w["row"], w["col"]] == c for w in wells for k, c in enumerate(w["log"]) if c >= 0 and fac_z[k, w["row"], w["col"]] >= 0]
print("GeoTOP most-likely vs boreholes: agreement", np.mean(agree).round(3), len(agree))
b64 = lambda a: base64.b64encode(np.ascontiguousarray(a).astype(np.int8).tobytes()).decode()
out = {"name": "Rhine-Meuse delta, Alblasserwaard (NL)", "crs": "EPSG:28992 (RD New), z in m NAP",
       "x0": X0, "y0": Y0, "dx": 100, "dy": 100, "dz": 0.5, "nx": int(fac.shape[0]), "ny": int(fac.shape[1]), "nz": int(fac.shape[2]), "zc": ZC.tolist(),
       "geotop_facies": b64(fac_z), "geotop_p": b64(np.round(P * 100)), "wells": wells,
       "sources": {"geotop": "GeoTOP v1.6.1, TNO Geological Survey of the Netherlands, via BRO / DINO (www.dinodata.nl/opendap/GeoTOP/geotop.nc)",
                   "boreholes": "BRO Geologisch booronderzoek (BHR-G), publiek.broservices.nl/sr/bhrg/v3"},
       "facies": ["clay and peat", "clayey sand, sandy clay and loam", "sand and gravel"]}
s = json.dumps(out, separators=(",", ":")); open("rhine_meuse_block.json", "w").write(s)
print("json bytes", len(s), "sha256", hashlib.sha256(s.encode()).hexdigest()[:16])
