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

Phase 3 (notebooks 2 and 3):

* read_fmi()           58-32 FMI fracture picks (GDR 1299): depth and apertures
* fmi_stats()          P10 and aperture percentiles of a pick list
* read_trajectory()    16A(78)-32 / 16B(78)-32 surveyed trajectories (GDR 1646)
* read_fractures()     FracMan CSV fracture lists (GDR 1646): centre, pole, radius, aperture
* pole()               unit pole (east, north, up) from trend and plunge
* terzaghi_p32()       P32 from P10 along a borehole, Terzaghi-corrected with an orientation sample
* oda_homogeneous()    expected Oda permeability tensor of a homogeneous fracture network
* circulation_daily()  GDR 1683 extended circulation test: daily medians and the steady-window summary

Phase 4 (notebooks 4 and 5):

* read_tracers()       QuantumPro circulation-test tracers 1–10 (GDR 1701): injection times, samples at 16B (ppb)
* tracer_detection()   per tracer: the first-detection bracket and the peak sample, hours after injection
* read_dts()           16B fibre temperatures (GDR 1721, HDF5): °C on (time, measured depth)
* dts_bins()           200-ft medians of a DTS profile; the step and the gradient of the deep section

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
    # phase 3
    "fmi": ("1299/University_of_Utah_MU-ESW1_FMI-HD_7390-7527ft_Dip Final 3rdRun_Frac_Aps_Only.txt",
            "5bad91b813661bbd51fe7d8083c96ad4a5f85e7702ae218156393716dfbbcb4c"),
    "dfn_feb": ("1646/2024 02A Feb Reference DFN.zip", "107fef6f2c11f6de3f9916ccea5df09d16c21da062126b8644f2464c9d18b809"),
    "dfn_may": ("1646/2024 05 May New MEQ DFN.zip", "fe9845773de0054c682b9acdfb25b9c276024a660d80d1803e1785d019d7d095"),
    "ect": ("1683/Extended Circulation Test.zip", "ce5a8d4c69ac649024b472219d38601dbd6227ff29cd8c737fe5fe39670786f7"),
    "circ_apr": ("1611/16A-16B Injection-Circulation.zip", "68ee7e43dde01e6aca5f5c205105ce1d7a530e67582e1cc340af00d8842d74cf"),
    # phase 4
    "tracer": ("1701/Qpro_tracers.zip", "4fae497068ccf5185d04576d252355d37515b218ff46ce2e514d420b05caa53b"),
    "dts_static": ("1721/Utah Forge 16B(78)-32 - DTS - mmf 2 - evo 4 - part 1.h5",
                   "168951d5fda18c25b226707fa32a403bc0e3842ffd14b90431131efe82a40898"),
    "dts_flowing": ("1721/Utah Forge 16B(78)-32 - DTS - mmf 2 - evo 4 - part 2.h5",
                    "77faaec9d7d10982c215ed233d5477ed5b87892464ea0a89a4c87c4e755eedb7"),
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



# ---------------------------------------------------------------------- phase 3
PSI, BBL_L, GAL_L = 6894.757, 158.987295, 3.785411784
STEAM_FRACTION = 0.196          # GDR 1683 report, Fig. 29


def member(path, part: str) -> bytes:
    with zipfile.ZipFile(path) as z:
        (name,) = [n for n in z.namelist() if part in n and not n.endswith("/")]
        return z.read(name)


def read_fmi(path):
    a = np.array([ln.split() for ln in pathlib.Path(path).read_text().splitlines()[1:] if ln.strip()], float)
    return {"depth_m": a[:, 0] * FT, "fva_mm": a[:, 1], "fvah_mm": a[:, 2]}


def fmi_stats(depth_m, aperture_mm, null=-9999.0):
    d, a = np.asarray(depth_m, float), np.asarray(aperture_mm, float)
    ok = a != null
    span = d.max() - d.min()
    return {"n": int(len(d)), "n_with_aperture": int(ok.sum()), "span_m": float(span), "p10_per_m": len(d) / span,
            "aperture_mm_P10": float(np.percentile(a[ok], 10)), "aperture_mm_P50": float(np.percentile(a[ok], 50)),
            "aperture_mm_P90": float(np.percentile(a[ok], 90)), "aperture_mm_cubic_mean": float(np.mean(a[ok] ** 3) ** (1 / 3))}


def _csv_array(raw: bytes):
    lines = [ln for ln in raw.decode("utf-8-sig").splitlines() if ln.strip()]
    return [h.strip() for h in lines[0].split(",")], np.array([[float(v) for v in ln.split(",")] for ln in lines[1:]])


def read_trajectory(dfn_feb_zip, well):
    head, a = _csv_array(member(dfn_feb_zip, f"Global Coordinates/Well Trajectories/{well}.csv"))
    return {"E": a[:, 0], "N": a[:, 1], "elev": a[:, 2], "md": a[:, 3]}


def read_fractures(raw: bytes):
    head, a = _csv_array(raw)
    c = {h.split("[")[0]: i for i, h in enumerate(head)}
    return {"E": a[:, c["FractureX"]], "N": a[:, c["FractureY"]], "elev": a[:, c["FractureZ"]], "radius": a[:, c["FractureRadius"]],
            "trend": a[:, c["Trend"]], "plunge": a[:, c["Plunge"]], "aperture": a[:, c["Aperture"]]}


def pole(trend_deg, plunge_deg):
    t, p = np.radians(np.asarray(trend_deg, float)), np.radians(np.asarray(plunge_deg, float))
    return np.c_[np.cos(p) * np.sin(t), np.cos(p) * np.cos(t), -np.sin(p)]


def terzaghi_p32(p10, poles, weights, hole=(0.0, 0.0, -1.0), min_cos=0.1):
    c = np.maximum(np.abs(np.asarray(poles) @ np.asarray(hole)), min_cos)
    m = float(np.sum(weights * c) / np.sum(weights))
    return p10 / m, m


def oda_homogeneous(p32, poles, weights, apertures_m):
    """(k_east, k_north, k_vertical) of a homogeneous network, m²: P32 E[a³]/12 (1 − E[n_i²])."""
    w = np.asarray(weights, float) / np.sum(weights)
    a3 = float(np.mean(np.asarray(apertures_m, float) ** 3))
    return p32 * a3 / 12 * (1 - (w[:, None] * np.asarray(poles) ** 2).sum(0))


def water_density(T_c):
    """kg/m3 at 1 atm (Kell 1975)."""
    T = np.asarray(T_c, float)
    return (999.83952 + 16.945176 * T - 7.9870401e-3 * T**2 - 46.170461e-6 * T**3 + 105.56302e-9 * T**4
            - 280.54253e-12 * T**5) / (1 + 16.879850e-3 * T)


def circulation_daily(ect_zip):
    """GDR 1683 30-second data → daily medians; and the steady 10 bpm window (days 14-26) summary with the
    field flow-meter calibration and the 19.6 % flash fraction (report, Fig. 29)."""
    import datetime as dt

    import openpyxl
    import pandas as pd

    def rows(part):
        ws = openpyxl.load_workbook(io.BytesIO(member(ect_zip, part)), read_only=True, data_only=True).worksheets[0]
        return list(ws.iter_rows(values_only=True))

    num = lambda v: float(v) if isinstance(v, (int, float)) else np.nan  # noqa: E731
    data = [r for r in rows("Extended Circulation Test Data") if isinstance(r[0], dt.datetime)]
    t0 = data[0][0]
    df = pd.DataFrame({"day": [(r[0] - t0).total_seconds() / 86400 for r in data],
                       "whp_16B_psi": [num(r[1]) for r in data], "T_16B_raw_f": [num(r[4]) for r in data],
                       "sep1_gpm": [num(r[5]) for r in data], "sep2_gpm": [num(r[6]) for r in data],
                       "whp_16A_psi": [num(r[8]) for r in data], "inj_bpm": [num(r[9]) for r in data]})
    cal = np.array([[num(v) for v in r[1:7]] for r in rows("Field Calibration of Flow Meters")
                    if isinstance(r[1], (int, float)) and isinstance(r[4], (int, float))])
    slope = {k: float(np.sum(cal[:, 1] * cal[:, c]) / np.sum(cal[:, c] ** 2)) for k, c in (("sep1", 3), ("sep2", 4))}
    dT = np.array([float(r[8]) for r in rows("Manual Temperature and Pressure Data") if isinstance(r[8], (int, float))])
    df["liquid_gpm_cal"] = df.sep1_gpm * slope["sep1"] + df.sep2_gpm * slope["sep2"]
    daily = df.assign(d=np.floor(df.day).astype(int)).groupby("d").median(numeric_only=True).drop(columns="day")
    w = df[(df.day >= 14) & (df.day < 26)]
    inj = float(w.inj_bpm.median()) * BBL_L / 60 * float(water_density(25.0)) / 1000
    prod = float(w.liquid_gpm_cal.median()) * GAL_L / 60 * float(water_density((202.2 - 32) / 1.8)) / 1000 / (1 - STEAM_FRACTION)
    T_raw = (float(w.T_16B_raw_f.median()) - 32) / 1.8
    summary = {"injection_kg_s": inj, "produced_kg_s": prod, "recovery": prod / inj,
               "whp_16A_mpa": float(w.whp_16A_psi.median()) * PSI / 1e6, "whp_16B_mpa": float(w.whp_16B_psi.median()) * PSI / 1e6,
               "T_16B_raw_c": T_raw, "manual_offset_c": float(np.median(dT)) / 1.8, "T_16B_wellhead_c": T_raw + float(np.median(dT)) / 1.8,
               "meter_slopes": slope}
    return daily, summary


# ---------------------------------------------------------------------- phase 4
def read_tracers(tracer_zip):
    """GDR 1701: the circulation-test tracers 1–10. Times in hours since the GDR 1683 test start (8 Aug 2024 07:00).
    Injection times are from the report's Table 7 (all at 07:00 except tracer 1 at 07:25)."""
    import datetime as dt
    import re

    import openpyxl

    start = dt.datetime(2024, 8, 8, 7, 0)
    with zipfile.ZipFile(tracer_zip) as z:
        x = z.read([n for n in z.namelist() if n.endswith(".xlsx")][0])
        d = z.read([n for n in z.namelist() if n.endswith(".docx")][0])
    rows = list(openpyxl.load_workbook(io.BytesIO(x), read_only=True, data_only=True).worksheets[0].iter_rows(values_only=True))
    first = next(i for i, r in enumerate(rows) if r and r[1] == "FloTrac tracer #1")
    hdr = max(i for i, r in enumerate(rows[:first]) if r and "Time (min)" in r)
    j = list(rows[hdr]).index("Time (min)")
    tmin = []
    for v in rows[hdr][j + 1:]:
        if not isinstance(v, (int, float)):
            break
        tmin.append(float(v))
    t_h = np.array(tmin) / 60 + (dt.datetime(2024, 8, 9, 17, 26) - start).total_seconds() / 3600
    with zipfile.ZipFile(io.BytesIO(d)) as dz:
        txt = re.sub(r"<[^>]+>", "", re.sub(r"</w:p>", "\n", dz.read("word/document.xml").decode("utf8")))
    i = txt.find("Table 7: Summary of tracers")
    lines = [ln.strip() for ln in txt[i:i + 3000].splitlines() if ln.strip()]
    k = lines.index("Comment") + 1
    table = {}
    while k + 6 < len(lines) and len(table) < 10:
        num, d0, h0, _, _, hrs, _ = lines[k:k + 7]
        mo, dd = (int(v) for v in d0.split("/"))
        hh, mm = (int(v) for v in re.findall(r"(\d+):(\d+)", h0)[0])
        table[int(num)] = {"injected_t_h": (dt.datetime(2024, mo, dd, hh + (12 if "PM" in h0 and hh != 12 else 0), mm) - start).total_seconds() / 3600,
                           "report_first_detection_h": float(hrs)}
        k += 7
    out = []
    for r in rows[first:first + 12]:
        if r and isinstance(r[1], str) and r[1].startswith("FloTrac tracer #"):
            n = int(r[1].split("#")[1])
            c = [float(v) if isinstance(v, (int, float)) else 0.0 for v in r[2:2 + len(t_h)]]
            out.append({"tracer": n, **table[n], "c_ppb": c})
    return t_h, out


def tracer_detection(sample_t_h, injected_t_h, c_ppb):
    """First-detection bracket (last clean sample, first positive sample) and the peak sample, hours after injection."""
    t = np.asarray(sample_t_h, float)
    c = np.asarray(c_ppb, float)
    a = t > injected_t_h
    ta, ca = t[a] - injected_t_h, c[a]
    pos = np.nonzero(ca > 0)[0]
    if not len(pos):
        return None
    i = pos[0]
    return {"last_clean_h": float(ta[i - 1]) if i > 0 else 0.0, "first_positive_h": float(ta[i]), "peak_h": float(ta[int(np.argmax(ca))]),
            "peak_ppb": float(ca.max())}


def read_dts(path):
    """GDR 1721 DTS file: temperature in °C (converted from °F) on (time, depth), depth in ft MD RKB, time in hours since
    the GDR 1683 test start (the file is in UTC; local time is UTC − 6 h)."""
    import datetime as dt

    import h5py

    with h5py.File(path, "r") as h:
        a = h["data"][:].astype(float)
        unit = h["data"].attrs.get("DataUnitLabel")
        z = h["depth"][:].astype(float)
        st = [dt.datetime.strptime(s.decode(), "%m/%d/%Y %H:%M:%S.%f") for s in h["stamps"][:]]
    if (unit.decode() if isinstance(unit, bytes) else unit) == "F":
        a = (a - 32) / 1.8
    t = np.array([(s - dt.datetime(2024, 8, 8, 7, 0)).total_seconds() / 3600 - 6.0 for s in st])
    return t, z, a


def dts_bins(md_ft, T_c, width=200.0, top=0.0, bottom=10400.0):
    """Median temperature in ``width``-ft bins."""
    b = np.arange(top, bottom, width)
    return b, np.array([np.median(T_c[(md_ft >= x) & (md_ft < x + width)]) if ((md_ft >= x) & (md_ft < x + width)).any() else np.nan for x in b])
