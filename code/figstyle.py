"""House style for static figures: fonts (a static Fraunces Black cut from the variable font in /home/claude/ref/fonts,
written to memory), colours, Natural Earth outlines in the Equal Earth projection, and raster drawing helpers."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
from matplotlib.patches import Polygon as MPoly
import numpy as np
from pyproj import Transformer
from common import *

FONTS = "/home/claude/ref/fonts"
FD = os.path.join(SHM, "fonts"); os.makedirs(FD, exist_ok=True)
if not os.path.exists(f"{FD}/Fraunces-Black.ttf"):
    from fontTools.ttLib import TTFont
    from fontTools.varLib import instancer
    vf = TTFont(f"{FONTS}/FrauncesVar.ttf")
    axes = {a.axisTag: a for a in vf["fvar"].axes}
    loc = {"wght": 900}
    if "opsz" in axes: loc["opsz"] = min(144, axes["opsz"].maxValue)
    for t in ("SOFT", "WONK"):
        if t in axes: loc[t] = 0
    instancer.instantiateVariableFont(vf, loc).save(f"{FD}/Fraunces-Black.ttf")
DISP = fm.FontProperties(fname=f"{FD}/Fraunces-Black.ttf")
SERP = fm.FontProperties(fname=f"{FONTS}/SourceSerif4-Regular.ttf")
SERB = fm.FontProperties(fname=f"{FONTS}/SourceSerif4-Semibold.ttf")
for f in ("IBMPlexMono-Regular.ttf", "IBMPlexMono-Medium.ttf"):
    fm.fontManager.addfont(f"{FONTS}/{f}")
MONO = "IBM Plex Mono"
plt.rcParams.update({"font.family": MONO, "font.size": 12, "axes.edgecolor": "#6B675E", "axes.labelcolor": "#22231E",
                     "xtick.color": "#6B675E", "ytick.color": "#6B675E", "axes.spines.top": False, "axes.spines.right": False})
BG, FG, MUT, LAND, RULE, HOT = "#F7F4EA", "#22231E", "#6B675E", "#E9E4D4", "#DDD6C2", "#B5562E"
SEA = "#F7F4EA"
tr = Transformer.from_crs(4326, 8857, always_xy=True)
W = jload(f"{DATA}/world.json")


def rings(geom):
    cs = geom["coordinates"] if geom["type"] == "MultiPolygon" else [geom["coordinates"]]
    for poly in cs:
        yield np.array(poly[0])


SHAPES = []
for f in W["features"]:
    ps = []
    for ring in rings(f["geometry"]):
        x, y = tr.transform(np.clip(ring[:, 0], -179.9, 179.9), ring[:, 1])
        ps.append(np.column_stack([x, y]))
    SHAPES.append((f["properties"]["iso"], ps))
WORLD_EXT = (-12.3e6, 15.6e6, -6.4e6, 8.3e6)


def world(ax, colour_of=lambda i: LAND, lw=.35, extent=WORLD_EXT, ec="#FFFFFF", z=1, fill=True):
    for iso, ps in SHAPES:
        c = colour_of(iso)
        for p in ps:
            ax.add_patch(MPoly(p, closed=True, fc=(c or LAND) if fill else "none", ec=ec, lw=lw, zorder=z))
    ax.set_xlim(extent[0], extent[1]); ax.set_ylim(extent[2], extent[3]); ax.set_aspect("equal"); ax.axis("off")


def hex2rgb(h):
    return np.array([int(h[i:i + 2], 16) for i in (1, 3, 5)], float) / 255


def mix(a, b, t):
    A = hex2rgb(a); B = hex2rgb(b)
    return "#" + "".join(f"{round(255 * (x + (y - x) * t)):02x}" for x, y in zip(A, B))


# equal-earth raster: for every output pixel, invert the projection and sample the 0.1 degree grid
_inv = Transformer.from_crs(8857, 4326, always_xy=True)


def ee_sample(width, extent=WORLD_EXT, n=72.0, s=-56.0, cell=0.1, ncols=3600):
    x0, x1, y0, y1 = extent
    h = int(round(width * (y1 - y0) / (x1 - x0)))
    xs = np.linspace(x0, x1, width); ys = np.linspace(y1, y0, h)
    X, Y = np.meshgrid(xs, ys)
    lon, lat = _inv.transform(X, Y)
    ok = np.isfinite(lon) & np.isfinite(lat) & (lat < n) & (lat > s) & (np.abs(lon) <= 180)
    r = np.clip(((n - np.nan_to_num(lat)) / cell).astype(int), 0, int((n - s) / cell) - 1)
    c = np.clip(((np.nan_to_num(lon) + 180) / cell).astype(int), 0, ncols - 1)
    return r, c, ok, h


def save(fig, name, dpi=200):
    fig.savefig(name, dpi=dpi, facecolor=fig.get_facecolor())
    plt.close(fig)
