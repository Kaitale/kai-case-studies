"""Shared functions for the Utah FORGE geothermal case (MIT licence).

* fetch()              download a public GDR file (once) and check its SHA-256 (rebuild only)
* read_mesh()          Leapfrog cell export: lithology (granitoid / basin fill) on the 50 × 50 × 55 grid
* fit_transform()      rotation + translation from the model's local metres to UTM 12N
* read_ic()            initial conditions at the 51 × 51 × 56 nodes: temperature, pressure, depth
* read_las_pt()        a pressure-temperature log in LAS 2.0
* granite_top()        elevation of the top of the granitoid in each column
* column_profile()     a node field along a vertical line (bilinear across the map)
* cell_average()       node field → cell field
* isotherm_depth()     depth at which a temperature profile reaches a value

Data credit: Utah FORGE, U.S. Department of Energy, via the Geothermal Data Repository (OpenEI), CC BY 4.0.
"""
from __future__ import annotations

import hashlib
import io
import math
import pathlib
import urllib.parse
import urllib.request
import zipfile

import numpy as np

GDR = "https://gdr.openei.org/files/"
FILES = {   # pinned 30 Oct 2026; all CC BY 4.0
    "mesh": ("1205/Mesh Files.zip", "ee4b35dffcceb4916d44bc3ac8882e715f154a0f9603d524940aee74a7534704"),
    "ic": ("1205/Initial Conditions.zip", "fc29649f321cff916849032c27c949e383709caeddae75b0a501c8334bbf826b"),
    "pt2018": ("1101/58-32_Temp_Pres_11_08_18.zip", "04de1f0aebe92e6b3963fcc43f054033d0898cab3d9a238f78d8038ec2826ec8"),
    "wells": ("1358/Utah FORGE Well and Seismic Locations.csv", "7bfc9cf730b8521a71a878ab38381a772ea06821e20f07c06c7ee5e3a5351471"),
}
CELL, NXY, NZ = 50.0, 50, 55
Z_BOTTOM, Z_TOP = -1500.0, 1250.0
FT, KB_FT = 0.3048, 21.5
STRESS_GRADIENTS_KPA_M = {"Sv": (1 - 0.12) * 2500 * 9.8 / 1000, "SHmax": 17.4, "Shmin": 14.6}   # as in the source workbook


def fetch(key: str, folder="gdr_cache") -> pathlib.Path:
    path, sha = FILES[key]
    d = pathlib.Path(folder); d.mkdir(exist_ok=True)
    p = d / pathlib.Path(path).name
    if not p.exists():
        urllib.request.urlretrieve(GDR + urllib.parse.quote(path), p)
    h = hashlib.sha256(p.read_bytes()).hexdigest()
    if h != sha:
        raise ValueError(f"{p.name}: checksum {h} differs from the published {sha}")
    return p


def _member(path, suffix):
    with zipfile.ZipFile(path) as z:
        (name,) = [n for n in z.namelist() if n.endswith(suffix) and not n.startswith("__MACOSX")]
        return z.read(name)


def _rows(raw: bytes):
    lines = [ln for ln in raw.decode("utf-8", "replace").splitlines() if ln and not ln.startswith("#")]
    return [h.strip() for h in lines[0].split(",")], [ln.split(",") for ln in lines[1:]]


def read_mesh(path):
    hg, rg = _rows(_member(path, "2019.08.21_global_cell.csv"))
    _, rl = _rows(_member(path, "2019.08.22_local_cell.csv"))
    g = sorted(((int(r[0]), float(r[1]), float(r[2]), r[hg.index("GM_8_19_2019")].strip()) for r in rg))
    loc = sorted(((int(r[0]), float(r[1]), float(r[2]), float(r[3])) for r in rl))
    assert [a[0] for a in g] == [a[0] for a in loc], "cell lists differ"
    L = np.array([a[1:] for a in loc]); U = np.array([a[1:3] for a in g]); lith = np.array([a[3] for a in g])
    i = np.rint((L[:, 0] - CELL / 2) / CELL).astype(int); j = np.rint((L[:, 1] - CELL / 2) / CELL).astype(int)
    k = np.rint((L[:, 2] - Z_BOTTOM - CELL / 2) / CELL).astype(int)
    granite = np.zeros((NZ, NXY, NXY), bool)
    granite[k, j, i] = np.char.startswith(np.char.lower(lith), "granit")     # the source spells it "Granitiod"
    return {"local": L, "utm": U, "granite": granite}


def fit_transform(local, utm):
    A = np.c_[local[:, :2], np.ones(len(local))]
    cE, *_ = np.linalg.lstsq(A, utm[:, 0], rcond=None); cN, *_ = np.linalg.lstsq(A, utm[:, 1], rcond=None)
    res = np.hypot(A @ cE - utm[:, 0], A @ cN - utm[:, 1])
    return {"E0": float(cE[2]), "N0": float(cN[2]), "aE": cE[:2].tolist(), "aN": cN[:2].tolist(),
            "azimuth_x_deg": math.degrees(math.atan2(cE[0], cN[0])), "max_residual_m": float(res.max())}


def to_local(t, E, N):
    return np.linalg.solve(np.array([t["aE"], t["aN"]]), np.array([np.asarray(E, float) - t["E0"], np.asarray(N, float) - t["N0"]]))


def to_utm(t, x, y):
    x, y = np.asarray(x, float), np.asarray(y, float)
    return t["E0"] + t["aE"][0] * x + t["aE"][1] * y, t["N0"] + t["aN"][0] * x + t["aN"][1] * y


def read_ic(path):
    import openpyxl
    ws = openpyxl.load_workbook(io.BytesIO(_member(path, "IC_local_node_v2.xlsx")), read_only=True).worksheets[0]
    rows, started = [], False
    for r in ws.iter_rows(values_only=True):
        if not started:
            started = bool(r) and r[0] == "Id"
            continue
        rows.append(r[:10])
    a = np.array(rows, float)
    i = np.rint(a[:, 1] / CELL).astype(int); j = np.rint(a[:, 2] / CELL).astype(int); k = np.rint((a[:, 3] - Z_BOTTOM) / CELL).astype(int)
    out = {}
    for name, col in (("p_pa", 7), ("T_k", 8), ("depth_m", 9)):
        f = np.full((NZ + 1, NXY + 1, NXY + 1), np.nan); f[k, j, i] = a[:, col]; out[name] = f
    return {"T_c": out["T_k"] - 273.15, "p_mpa": out["p_pa"] / 1e6, "depth_m": out["depth_m"]}


def read_las_pt(path):
    text = _member(path, ".las").decode("latin-1")
    a = np.array([[float(v) for v in ln.split()] for ln in text.split("~A", 1)[1].splitlines()[1:] if ln.strip()])
    ok = (a[:, 1] != -999.25) & (a[:, 4] != -999.25) & (a[:, 1] > 0)
    return {"depth_m": (a[ok, 0] - KB_FT) * FT, "T_c": (a[ok, 1] - 32) / 1.8, "P_mpa": a[ok, 4] * 0.00689476}


def granite_top(granite):
    top = np.full(granite.shape[1:], np.nan)
    ztop = Z_BOTTOM + (np.arange(granite.shape[0]) + 1) * CELL
    for j in range(granite.shape[1]):
        for i in range(granite.shape[2]):
            k = np.nonzero(granite[:, j, i])[0]
            if len(k):
                top[j, i] = ztop[k.max()]
    return top


def column_profile(f, x, y):
    fx, fy = x / CELL, y / CELL
    i0, j0 = int(np.clip(math.floor(fx), 0, NXY - 1)), int(np.clip(math.floor(fy), 0, NXY - 1))
    tx, ty = fx - i0, fy - j0
    return ((1 - tx) * (1 - ty) * f[:, j0, i0] + tx * (1 - ty) * f[:, j0, i0 + 1]
            + (1 - tx) * ty * f[:, j0 + 1, i0] + tx * ty * f[:, j0 + 1, i0 + 1])


def cell_average(f):
    return 0.125 * (f[:-1, :-1, :-1] + f[1:, :-1, :-1] + f[:-1, 1:, :-1] + f[:-1, :-1, 1:]
                    + f[1:, 1:, :-1] + f[1:, :-1, 1:] + f[:-1, 1:, 1:] + f[1:, 1:, 1:])


def isotherm_depth(T_bottom_up, depth_bottom_up, T):
    d, t = depth_bottom_up[::-1], T_bottom_up[::-1]
    above = np.nonzero(t >= T)[0]
    if not len(above) or above[0] == 0:
        return None
    k = above[0]
    return float(np.interp(T, [t[k - 1], t[k]], [d[k - 1], d[k]]))
