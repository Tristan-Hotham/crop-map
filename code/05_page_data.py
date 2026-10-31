"""Page grids as PNGs (0.1 degree, 72N to 56S, 3600 x 1280), decoded in the browser:
  data/page/base.png      : R = dominant crop (1 to 34, 0 none), G = harvested density code (all 34 crops), B = diversity x 20
  data/page/base2.png     : R = second crop, G = dominant crop's share of harvested area (per cent), B = physical crop area density code
  data/page/crops_N.png   : three crops per image (R, G, B), harvested density code, crops in common.CK order
Density code: 0 below 0.01% of the cell; otherwise 1 + 254 * (log10(f) + 4) / (log10(1.5) + 4), f = harvested ha / cell ha.
Also writes data/cropgrids_0p1deg_summary.tif (GeoTIFF: dominant crop, harvested ha, physical ha, diversity x 100)."""
import numpy as np
from PIL import Image
import rasterio
from rasterio.transform import from_origin
from common import *

GW = os.environ.get("CROPGRID", "/home/claude/_cropwork")
g = np.load(f"{WORK}/grid.npz"); H = np.load(f"{GW}/crops01.npy", mmap_mode="r")
cell = g["cell_ha"][:, None]
LO, HI = -4.0, np.log10(1.5)


def code(f):
    c = np.zeros(f.shape, np.uint8)
    m = f >= 1e-4
    c[m] = np.clip(1 + np.round(254 * (np.log10(f[m]) - LO) / (HI - LO)), 1, 255).astype(np.uint8)
    return c


tot = g["tot"].astype(np.float64)
dom = g["bi"]; sec = g["si"]
share = np.zeros_like(tot); best = np.zeros_like(tot)
for i in range(len(CK)):
    best = np.where(dom == i + 1, np.asarray(H[i]), best)
share = np.where(tot > 0, 100 * best / np.maximum(tot, 1e-9), 0)
divc = np.clip(np.round(g["div"] * 20), 0, 255).astype(np.uint8)
dens_c = code(tot / cell)
dom = np.where(dens_c > 0, dom, 0).astype(np.uint8)
sec = np.where(dens_c > 0, sec, 0).astype(np.uint8)
Image.fromarray(np.dstack([dom, dens_c, np.where(dens_c > 0, divc, 0)]), "RGB").save(f"{PAGE_D}/base.png", optimize=True)
Image.fromarray(np.dstack([sec, np.where(dens_c > 0, np.round(share), 0).astype(np.uint8), code(g["phys"] / cell)]), "RGB").save(f"{PAGE_D}/base2.png", optimize=True)
for j in range(0, len(CK), 3):
    ch = [code(np.asarray(H[i]) / cell) if i < len(CK) else np.zeros(tot.shape, np.uint8) for i in range(j, j + 3)]
    Image.fromarray(np.dstack(ch), "RGB").save(f"{PAGE_D}/crops_{j // 3}.png", optimize=True)
tr = from_origin(-180, 72, 0.1, 0.1)
with rasterio.open(f"{DATA}/cropgrids_0p1deg_summary.tif", "w", driver="GTiff", height=tot.shape[0], width=tot.shape[1], count=4, dtype="uint16",
                   crs="EPSG:4326", transform=tr, compress="deflate", predictor=2, nodata=0) as d:
    d.write(g["bi"].astype(np.uint16), 1); d.write(np.clip(np.round(tot), 0, 65535).astype(np.uint16), 2)
    d.write(np.clip(np.round(g["phys"]), 0, 65535).astype(np.uint16), 3); d.write(np.clip(np.round(g["div"] * 100), 0, 65535).astype(np.uint16), 4)
    d.update_tags(1, name="dominant crop index (1 to 34, order as data/crop_totals.csv)"); d.update_tags(2, name="harvested area, ha, 34 crops")
    d.update_tags(3, name="physical crop area, ha, 34 crops"); d.update_tags(4, name="effective number of crops x 100 (exp Shannon)")
    d.update_tags(source="Derived from CROPGRIDS v1.08 (Tang et al. 2024), CC BY 4.0", crops=",".join(CK))
tot_kb = 0
for fn in sorted(os.listdir(PAGE_D)):
    kb = os.path.getsize(f"{PAGE_D}/{fn}") // 1024; tot_kb += kb; print(fn, kb, "KB")
print("page data", tot_kb, "KB; tif", os.path.getsize(f"{DATA}/cropgrids_0p1deg_summary.tif") // 1024, "KB")
