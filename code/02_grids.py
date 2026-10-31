"""Read the 34 CROPGRIDS v1.08 crop grids (0.05 degree, circa 2020) and build:
  GW/crops01.npy     : harvested area (ha) per crop on a 0.1 degree grid, 72N to 56S (1280 x 3600), float32
  GW/phys01.npy      : physical crop area (ha) per crop on the same grid
  GW/uk05.npz        : native 0.05 degree harvested area per crop for the UK and Ireland window (for the UK figure)
  WORK/cg_country.json : harvested and physical area per crop per country (country raster from CROPGRIDS) and the
                       harvested-area-weighted mean data quality per crop
Native-resolution totals (all 34 crops) are also summarised: number of cells with any crop, and the share of harvested
area in cells whose dominant crop has at least half of it."""
import re
import numpy as np, netCDF4 as nc
from common import *

GW = os.environ.get("CROPGRID", "/home/claude/_cropwork")
os.makedirs(GW, exist_ok=True)
N0, S0 = 72.0, -56.0                      # page window
R05 = (np.arange(3600) * -0.05 + 89.975)  # row latitudes after flipping to north-up
r0 = int(round((89.975 - (N0 - 0.025)) / 0.05)); r1 = int(round((89.975 - (S0 + 0.025)) / 0.05)) + 1
NR, NC = (r1 - r0) // 2, 3600
UKW = dict(n=61.0, s=49.8, w=-11.0, e=2.0)
ukr0 = int(round((89.975 - (UKW["n"] - 0.025)) / 0.05)); ukr1 = int(round((89.975 - (UKW["s"] + 0.025)) / 0.05)) + 1
ukc0 = int(round((UKW["w"] + 179.975) / 0.05)); ukc1 = int(round((UKW["e"] - 0.025 + 179.975) / 0.05)) + 1


def read(fn, var):
    d = nc.Dataset(f"{CG}/{fn}.nc")
    a = np.asarray(d[var][:].filled(0), dtype=np.float32)[::-1]   # north-up
    d.close()
    a[~np.isfinite(a)] = 0; a[a < 0] = 0
    return a


def agg2(a):
    a = a[r0:r1]
    return a.reshape(NR, 2, NC, 2).sum(axis=(1, 3))


# country raster and its ISO3 list
cd = nc.Dataset(f"{CG}/Countries_2018.nc")
attr = cd["country"].getncattr("List of countries")
CID = {}
for m in re.finditer(r"(\d+) - ([A-Z/]{2}), ([A-Z/]{3});\s*(\d+): ([^>]+?) > ", attr):
    CID[int(m.group(1))] = m.group(3) if m.group(3) != "///" else None
cr = np.asarray(cd["country"][:].filled(0))[::-1]
cr = np.where(np.isfinite(cr) & (cr >= 1), cr, 0).astype(np.int32)   # 0 = sea or no country
cd.close()
assert CID[207] == "GBR" and CID[40] == "CHN" and CID[208] == "USA", (CID.get(207), CID.get(40))
ncodes = int(cr.max()) + 1

H01 = np.zeros((len(CK), NR, NC), np.float32); P01 = np.zeros_like(H01)
UK = np.zeros((len(CK), ukr1 - ukr0, ukc1 - ukc0), np.float32)
Htot = np.zeros((3600, 7200), np.float32); Hmax = np.zeros_like(Htot)
byc = {}; qual = {}; tot = {}
for i, k in enumerate(CK):
    h = read(k, "harvarea"); p = read(k, "croparea"); q = read(k, "qual")
    H01[i] = agg2(h); P01[i] = agg2(p); UK[i] = h[ukr0:ukr1, ukc0:ukc1]
    Htot += h; np.maximum(Hmax, h, out=Hmax)
    s = np.bincount(cr.ravel(), weights=h.ravel().astype(np.float64), minlength=ncodes)
    sp = np.bincount(cr.ravel(), weights=p.ravel().astype(np.float64), minlength=ncodes)
    byc[k] = {CID[c]: [round(float(s[c]), 1), round(float(sp[c]), 1)] for c in range(1, ncodes) if CID.get(c) and (s[c] > 0 or sp[c] > 0)}
    qual[k] = round(float((q * h).sum() / h.sum()), 3)
    tot[k] = [float(h.sum()), float(p.sum()), float(s[0])]     # last: area outside any country cell
    print(k, round(h.sum() / 1e6, 2), "Mha harvested", round(p.sum() / 1e6, 2), "Mha physical, qual", qual[k], flush=True)
    del h, p, q
np.save(f"{GW}/crops01.npy", H01); np.save(f"{GW}/phys01.npy", P01)
np.savez_compressed(f"{GW}/uk05.npz", h=UK, n=UKW["n"], s=UKW["s"], w=UKW["w"], e=UKW["e"])
cells = int((Htot > 0).sum())
dom_half = float(Htot[(Hmax >= 0.5 * Htot) & (Htot > 0)].sum() / Htot.sum())
outside = float(Htot[:r0].sum() + Htot[r1:].sum())
jsave({"by_country": byc, "qual": qual, "tot": tot, "native_cells": cells, "native_dom_half_share": dom_half,
       "outside_window_ha": outside, "grid": {"n": N0, "s": S0, "rows": NR, "cols": NC, "cell": 0.1}}, f"{WORK}/cg_country.json")
print("cells", cells, "dominant >= half share", round(dom_half, 3), "outside window ha", outside)
