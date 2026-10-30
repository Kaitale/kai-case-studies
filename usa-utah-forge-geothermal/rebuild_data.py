"""Rebuild data/ from the public Utah FORGE files on the DOE Geothermal Data Repository (MIT licence).

    python rebuild_data.py          # downloads ~27 MB into gdr_cache/ (checked by SHA-256), writes data/

Writes only derived values (CC BY 4.0, with the FORGE credit):
* data/forge_model.npz          granitoid flag per cell (50 × 50 × 55); temperature (°C), pressure (MPa) and depth below
                                ground (m) at the 51 × 51 × 56 nodes, as float32; the local → UTM transform
* data/well_58_32_log_2018.csv  58-32 temperature and pressure, 8 Nov 2018, resampled every 5 m of depth below ground
* data/wells.csv                surveyed FORGE well heads (UTM 12N, NAD83; December 2021) and their model coordinates
"""
import json
import pathlib

import numpy as np
import pandas as pd

import forge_tools as ft

out = pathlib.Path("data"); out.mkdir(exist_ok=True)
mesh = ft.read_mesh(ft.fetch("mesh"))
tr = ft.fit_transform(mesh["local"], mesh["utm"])
print(f"transform: +x azimuth {tr['azimuth_x_deg']:.3f}°, residual {tr['max_residual_m']:.2e} m")
ic = ft.read_ic(ft.fetch("ic"))
np.savez_compressed(out / "forge_model.npz", granite=mesh["granite"], T_c=ic["T_c"].astype(np.float32),
                    p_mpa=ic["p_mpa"].astype(np.float32), depth_m=ic["depth_m"].astype(np.float32),
                    transform=np.array(json.dumps(tr)))
pt = ft.read_las_pt(ft.fetch("pt2018"))
d = np.arange(5.0, pt["depth_m"].max(), 5.0)
pd.DataFrame({"depth_m": d, "T_c": np.interp(d, pt["depth_m"], pt["T_c"]).round(3),
              "P_mpa": np.interp(d, pt["depth_m"], pt["P_mpa"]).round(4)}).to_csv(out / "well_58_32_log_2018.csv", index=False)
rows = []
for ln in ft.fetch("wells").read_text().splitlines():
    p = ln.split(",")
    if len(p) > 6 and p[6] == "WELL":
        x, y = ft.to_local(tr, float(p[1]), float(p[2]))
        rows.append({"well": p[0].replace("-WELL", ""), "easting": float(p[1]), "northing": float(p[2]), "lat": float(p[3]),
                     "lon": float(p[4]), "elev_m": float(p[5]), "x_model_m": round(float(x), 2), "y_model_m": round(float(y), 2)})
pd.DataFrame(rows).to_csv(out / "wells.csv", index=False)
print("wrote", ", ".join(sorted(f.name for f in out.iterdir())))
