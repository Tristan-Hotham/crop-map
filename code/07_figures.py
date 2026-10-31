"""Static figures: header.png (1200 x 630), blog figures (release/blog/b_*.png) and paper figures (release/paper/f_*.png).
Maps are drawn from the grids and Natural Earth outlines in the Equal Earth projection, no web tiles."""
from collections import Counter
from matplotlib.patches import Patch
from matplotlib.lines import Line2D
import matplotlib.colors as mcolors
import matplotlib.ticker
from figstyle import *

GW = os.environ.get("CROPGRID", "/home/claude/_cropwork")
R = jload(f"{DATA}/results.json"); SITE = jload(f"{DATA}/site.json")
g = np.load(f"{WORK}/grid.npz"); H = np.load(f"{GW}/crops01.npy", mmap_mode="r")
REL = os.path.join(ROOT, "release"); os.makedirs(f"{REL}/blog", exist_ok=True); os.makedirs(f"{REL}/paper", exist_ok=True)
COLS = np.array([hex2rgb(CCOL[k]) for k in CK])
CN = SITE["cname"]


def outs(name):
    return [f"{REL}/blog/b_{name}.png", f"{REL}/paper/f_{name}.png"]


def legend(fig, items, y, ncol=4, x=.03, fs=10, marker=False):
    h = [Line2D([], [], marker="s", ls="", ms=8, mfc=c, mec="none", label=l) for l, c in items] if marker else [Patch(fc=c, ec="none", label=l) for l, c in items]
    fig.legend(handles=h, loc="upper left", bbox_to_anchor=(x, y), ncol=ncol, frameon=False, fontsize=fs, handlelength=1.2,
               handleheight=1.0, columnspacing=1.3, labelspacing=.45)


def dom_rgba(width, extent=WORLD_EXT, fade=True):
    r, c, ok, h = ee_sample(width, extent)
    dom = g["bi"][r, c]; dens = g["dens"][r, c]
    m = ok & (dom > 0) & (dens >= 0.002)
    out = np.zeros((h, width, 4)); out[m, :3] = COLS[dom[m] - 1]
    a = np.clip(.2 + .8 * (np.log10(np.clip(dens[m], 1e-3, 1)) + 3) / 2.6, .2, 1) if fade else 1
    out[m, 3] = a
    return out


def crop_rgba(k, width, extent=WORLD_EXT):
    r, c, ok, h = ee_sample(width, extent)
    f = np.asarray(H[CK.index(k)])[r, c] / g["cell_ha"][r]
    m = ok & (f >= 1e-3)
    t = np.clip((np.log10(np.clip(f, 1e-3, 1)) + 3) / 3, 0, 1)
    cmap = mcolors.LinearSegmentedColormap.from_list("c", [mix(CCOL[k], "#FFFFFF", .75), CCOL[k], mix(CCOL[k], "#000000", .5)])
    out = np.zeros((h, width, 4)); out[m] = cmap(t[m]); out[m, 3] = .35 + .65 * t[m]
    return out


def draw_raster(ax, rgba, extent=WORLD_EXT):
    x0, x1, y0, y1 = extent
    ax.imshow(rgba, extent=(x0, x1, y0, y1), zorder=2, interpolation="nearest")


MAIN = ["wheat", "maize", "rice", "soybean", "barley", "sorghum", "millet", "cassava", "sugarcane", "oilpalm", "cotton", "bean", "rapeseed",
        "sunflower", "groundnut", "cocoa", "coffee", "rubber", "olive", "potato"]

# ---------- header (1200 x 630) ----------
fig = plt.figure(figsize=(6, 3.15), facecolor=BG)
ax = fig.add_axes([.30, .03, .70, .94]); ext = (-12.3e6, 15.6e6, -5.9e6, 8.3e6)
world(ax, lambda i: LAND, lw=.15, extent=ext); draw_raster(ax, dom_rgba(1400, ext), ext)
fig.text(.04, .87, "What the", fontproperties=DISP, fontsize=22, color=FG, va="top")
fig.text(.04, .74, "world grows", fontproperties=DISP, fontsize=22, color=HOT, va="top")
fig.text(.04, .55, f"The leading crop on every\n10 km of farmland. Half the\nharvest of 34 crops grows on\n{R['grid']['half_on_land_pct']:.1f}% of the world's land.",
         fontproperties=SERP, fontsize=8.4, color=FG, va="top", linespacing=1.45)
for i, k in enumerate(["wheat", "maize", "rice", "soybean"]):
    fig.add_artist(Line2D([.046 + (i % 2) * .115], [.215 - (i // 2) * .055], marker="s", ms=3.6, mfc=CCOL[k], mec="none", ls="", transform=fig.transFigure))
    fig.text(.058 + (i % 2) * .115, .228 - (i // 2) * .055, CNAME[k].lower(), fontsize=5.6, color=FG, va="top")
fig.text(.04, .06, "maps.tristanhotham.com/crop-map", fontsize=5.8, color=MUT)
save(fig, os.path.join(ROOT, "header.png"))

# ---------- dominant crop world map ----------
used = Counter(int(v) for v in g["bi"][(g["bi"] > 0) & (g["dens"] >= .01)].ravel())
for out in outs("dominant_map"):
    fig = plt.figure(figsize=(7.6, 5.4), facecolor=BG)
    ax = fig.add_axes([0, .25, 1, .75]); world(ax, lambda i: LAND, lw=.25); draw_raster(ax, dom_rgba(2200))
    legend(fig, [(CNAME[k], CCOL[k]) for k in MAIN], .25, ncol=5, fs=8.6)
    fig.text(.03, .02, "Fainter colour: less of the land under these crops. Other crops: see the interactive map.", fontsize=7.5, color=MUT)
    save(fig, out)

# ---------- world land use since 1961 ----------
L_ = R["land"]; yrs = L_["years"]
for out in outs("land_lines"):
    fig, ax = plt.subplots(figsize=(7.6, 4.2), facecolor=BG); ax.set_facecolor(BG)
    for k, n, c in (("past", "Pasture", "#7FAE5A"), ("crop", "Cropland", "#C9921A"), ("forest", "Forest", "#2E6B4F")):
        v = np.array([np.nan if x is None or x == 0 else x for x in L_["world_series"][k]], float)
        ax.plot(yrs, v, color=c, lw=2.4); i = np.where(np.isfinite(v))[0][-1]; ax.text(yrs[i] + 1, v[i], n, color=c, va="center", fontsize=10)
    ax.set_xlim(1960, 2032); ax.set_ylim(0, 5000); ax.set_ylabel("million hectares"); ax.grid(axis="y", color=RULE, lw=.8)
    fig.tight_layout(); save(fig, out)

# ---------- cropland change map ----------
CHG = ["#8C2D04", "#D06A2A", "#F0B37A", "#EFEADB", "#A8D5A2", "#5DAA6B", "#2E7D4F", "#145232"]; BINS = [-50, -25, -10, 10, 25, 50, 100]


def chg_col(iso):
    c = SITE["c"].get(iso, {}).get("lu")
    if not c or c[4] is None: return None
    k = sum(c[4] >= b for b in BINS); col = CHG[k]
    return mix(col, BG, .55) if c[8] > 1961 else col


for out in outs("change_map"):
    fig = plt.figure(figsize=(7.6, 4.9), facecolor=BG)
    ax = fig.add_axes([0, .16, 1, .84]); world(ax, chg_col, lw=.3)
    legend(fig, list(zip(["below -50%", "-50 to -25%", "-25 to -10%", "-10 to +10%", "+10 to +25%", "+25 to +50%", "+50 to +100%", "over +100%"], CHG)), .16, ncol=4, fs=8.6)
    fig.text(.03, .015, "Cropland, 2021 to 2023 against 1961 to 1963 (FAOSTAT). Paler: states formed after 1961, change since their first year.", fontsize=7.2, color=MUT)
    save(fig, out)

# ---------- crops 1961 and 2024 ----------
rows = R["crops"]["rows"]
for out in outs("crops_change"):
    fig, ax = plt.subplots(figsize=(7.6, 8.4), facecolor=BG); ax.set_facecolor(BG)
    y = np.arange(len(rows))[::-1]
    ax.barh(y, [r["ha_2024"] / 1e6 for r in rows], color=[CCOL[r["k"]] for r in rows], height=.72)
    ax.scatter([r["ha_1961"] / 1e6 for r in rows], y, marker="|", s=110, color=FG, lw=1.8, zorder=3)
    for yi, r in zip(y, rows):
        ax.text(max(r["ha_2024"], r["ha_1961"]) / 1e6 + 2, yi, f"{r['ha_2024'] / 1e6:.1f}" + (f"  ×{r['x']:.1f}" if r["x"] and r["x"] >= 2 else ""), va="center", fontsize=8.5, color=FG)
    ax.set_yticks(y); ax.set_yticklabels([r["name"] for r in rows], fontsize=9); ax.set_xlabel("million hectares harvested (bar: 2024, tick: 1961)")
    ax.set_xlim(0, 250); ax.grid(axis="x", color=RULE, lw=.8); ax.set_axisbelow(True)
    fig.tight_layout(); save(fig, out)

# ---------- belts: six crops ----------
SIX = [("rice", "Rice"), ("wheat", "Wheat"), ("maize", "Maize"), ("soybean", "Soya beans"), ("oilpalm", "Oil palm"), ("cocoa", "Cocoa")]
for out in outs("belts"):
    fig = plt.figure(figsize=(7.6, 6.2), facecolor=BG)
    ext = (-12.3e6, 15.6e6, -5.2e6, 7.9e6)
    for i, (k, n) in enumerate(SIX):
        a = fig.add_axes([.005 + (i % 2) * .5, .645 - (i // 2) * .305, .49, .27])
        world(a, lambda iso: LAND, lw=.12, extent=ext); draw_raster(a, crop_rgba(k, 1000, ext), ext)
        a.text(3.0e6, ext[2] + .1e6, f"{n}\n{R['crops']['by_k'][k]['ha_2024'] / 1e6:.0f} million ha", fontsize=8, color=FG, va="bottom", zorder=5)
    fig.text(.01, .012, "Harvested area as a share of each 10 km square (darker = more), CROPGRIDS about 2020; totals FAOSTAT 2024.", fontsize=7.2, color=MUT)
    save(fig, out)

# ---------- biggest crop by country ----------
topit = {i: c["top"][0][0] for i, c in SITE["c"].items() if c.get("top")}
cnt = Counter(topit.values())
for out in outs("top_crop_map"):
    fig = plt.figure(figsize=(7.6, 5.0), facecolor=BG)
    ax = fig.add_axes([0, .2, 1, .8]); world(ax, lambda i: SITE["items"][str(topit[i])][2] if i in topit else None, lw=.3)
    legend(fig, [(f"{SITE['items'][str(k)][0]} ({n})", SITE["items"][str(k)][2]) for k, n in cnt.most_common(12)], .2, ncol=4, fs=8.4)
    fig.text(.03, .015, "Crop with the largest harvested area in each country, FAOSTAT 2022 to 2024 average.", fontsize=7.2, color=MUT)
    save(fig, out)

# ---------- specialities ----------
SP = [i for i in ("SAU", "MDG", "NZL", "BOL", "PER", "MAR", "VNM", "TUR", "BEL", "FRA", "POL", "NLD", "MEX", "IRN", "IDN", "AUS", "GBR", "ESP", "DEU", "CAN", "IND")]
sp = sorted([(i, R["spec"][i]) for i in SP], key=lambda x: -x[1]["lq"])
for out in outs("specialities"):
    fig, ax = plt.subplots(figsize=(7.6, 6.6), facecolor=BG); ax.set_facecolor(BG)
    y = np.arange(len(sp))[::-1]
    ax.barh(y, [s["lq"] for _, s in sp], color=HOT, height=.7); ax.set_xscale("log")
    ax.set_yticks(y); ax.set_yticklabels([f"{CN.get(i, i)}: {s['name'].lower()}" for i, s in sp], fontsize=9)
    for yi, (_, s) in zip(y, sp): ax.text(s["lq"] * 1.08, yi, f"×{s['lq']:.0f}", va="center", fontsize=8.5)
    ax.set_xlabel("times the world share of harvested area (log scale)"); ax.xaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, p: f"{v:g}"))
    ax.set_xlim(1, 900); ax.grid(axis="x", color=RULE, lw=.8); ax.set_axisbelow(True)
    fig.tight_layout(); save(fig, out)

# ---------- concentration curve ----------
landA = (g["landf"] * g["cell_ha"][:, None]).ravel(); hv = g["tot"].ravel().astype(float)
o = np.argsort(-(hv / np.maximum(landA, 1))); cx = np.cumsum(landA[o]) / landA.sum() * 100; cy = np.cumsum(hv[o]) / hv.sum() * 100
for out in outs("concentration"):
    fig, ax = plt.subplots(figsize=(7.6, 4.2), facecolor=BG); ax.set_facecolor(BG)
    k = slice(None, None, 50); ax.plot(cx[k], cy[k], color=HOT, lw=2.4)
    for p, lab in ((R["grid"]["half_on_land_pct"], "50%"), (R["grid"]["ninety_on_land_pct"], "90%")):
        yy = 50 if lab == "50%" else 90
        ax.plot([0, p, p], [yy, yy, 0], color=MUT, lw=.9, ls="--"); ax.text(p + 1, yy - 7, f"{lab} of the harvest\non {p:.1f}% of the land", fontsize=9, color=FG)
    ax.set_xlim(0, 100); ax.set_ylim(0, 101); ax.set_xlabel("share of the world's land, most intensively farmed first, %"); ax.set_ylabel("share of harvested area, %")
    ax.grid(color=RULE, lw=.6); fig.tight_layout(); save(fig, out)

# ---------- diversity map ----------
DIVC = mcolors.LinearSegmentedColormap.from_list("d", ["#F3E3B2", "#C9D98A", "#7FB77E", "#3B8C78", "#1F5F6B", "#24345E"])
for out in outs("diversity_map"):
    fig = plt.figure(figsize=(7.6, 4.6), facecolor=BG)
    ax = fig.add_axes([0, .1, 1, .9]); world(ax, lambda i: LAND, lw=.25)
    r, c, ok, h = ee_sample(2200); dv = g["div"][r, c]; dn = g["dens"][r, c]; m = ok & (dn >= .01)
    rgba = np.zeros((h, 2200, 4)); rgba[m] = DIVC(np.clip((dv[m] - 1) / 7, 0, 1)); draw_raster(ax, rgba)
    cax = fig.add_axes([.3, .06, .4, .025]); cb = fig.colorbar(plt.cm.ScalarMappable(cmap=DIVC, norm=mcolors.Normalize(1, 8)), cax=cax, orientation="horizontal")
    cb.set_label("effective number of crops (34 crops), farmed squares only", fontsize=8); cb.ax.tick_params(labelsize=8)
    save(fig, out)

# ---------- UK: five crops at 0.05 degrees and the series ----------
U = np.load(f"{GW}/uk05.npz"); UH = U["h"]; n0, w0 = float(U["n"]), float(U["w"])
lat = n0 - .05 * (np.arange(UH.shape[1]) + .5); ucell = (6371.0072e3 ** 2) * np.radians(.05) * np.radians(.05) * np.cos(np.radians(lat)) / 1e4
k_ = np.cos(np.radians(54.5))
FIVE = [("wheat", "Wheat"), ("barley", "Barley"), ("rapeseed", "Rapeseed"), ("potato", "Potatoes"), ("sugarbeet", "Sugar beet")]
ukw = [f for f in W["features"] if f["properties"]["iso"] in ("GBR", "IRL", "IMN")]
for out in outs("uk_crops"):
    fig = plt.figure(figsize=(7.6, 3.5), facecolor=BG)
    for i, (k, n) in enumerate(FIVE):
        a = fig.add_axes([.005 + i * .199, .08, .195, .78]); a.set_facecolor(BG)
        for f in ukw:
            for ring in rings(f["geometry"]): a.add_patch(MPoly(np.column_stack([ring[:, 0] * k_, ring[:, 1]]), closed=True, fc=LAND, ec="#BDB59F", lw=.3))
        fr = UH[CK.index(k)] / ucell[:, None]; t = np.clip((np.log10(np.clip(fr, 1e-3, 1)) + 3) / 3, 0, 1)
        col = CCOL[k] if k != "rapeseed" else "#B6C22A"
        cmap = mcolors.LinearSegmentedColormap.from_list("c", [mix(col, "#FFFFFF", .7), col, mix(col, "#000000", .5)])
        rgba = cmap(t); rgba[..., 3] = np.where(fr >= 1e-3, .3 + .7 * t, 0)
        a.imshow(rgba, extent=(w0 * k_, (w0 + .05 * UH.shape[2]) * k_, n0 - .05 * UH.shape[1], n0), interpolation="nearest", zorder=2)
        a.set_xlim(-8.3 * k_, 2 * k_); a.set_ylim(49.9, 59); a.set_aspect("equal"); a.axis("off")
        a.set_title(f"{n}\n{R['uk']['cg'][k] / 1e3:,.0f} kha", fontsize=9, color=FG)
    fig.text(.01, .02, "Harvested area as a share of each 5 km square, CROPGRIDS about 2020 (darker = more).", fontsize=7.2, color=MUT)
    save(fig, out)
UN = {"wheat": ("Wheat", "#E3B23C"), "barley": ("Barley", "#9E7B3A"), "rapeseed": ("Rapeseed", "#B6C22A"), "oats": ("Oats", "#C8B57A"),
      "potato": ("Potatoes", "#B095CF"), "sugarbeet": ("Sugar beet", "#D2559B"), "fieldbean": ("Field beans", "#B5562E")}
for out in outs("uk_series"):
    fig, ax = plt.subplots(figsize=(7.6, 4.3), facecolor=BG); ax.set_facecolor(BG); ys = R["uk"]["years"]
    for k, (n, c) in UN.items():
        v = np.array(R["uk"]["series"][k]) / 1e3; ax.plot(ys, v, color=c, lw=2.2); ax.text(ys[-1] + 1, v[-1], n, color=c, fontsize=9, va="center")
    ax.set_xlim(1960, 2036); ax.set_ylabel("thousand hectares harvested"); ax.grid(axis="y", color=RULE, lw=.8)
    fig.tight_layout(); save(fig, out)
print("figures done")
