"""r/dataisbeautiful collage for crop-map: 2400 x 3000 px, light background. Numbers from data/results.json."""
import os, sys, importlib.util
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "code"))
from figstyle import *
from matplotlib.patches import Patch
import matplotlib.colors as mcolors

GW = os.environ.get("CROPGRID", "/home/claude/_cropwork")
R = jload(f"{DATA}/results.json"); g = np.load(f"{WORK}/grid.npz"); H = np.load(f"{GW}/crops01.npy", mmap_mode="r")
COLS = np.array([hex2rgb(CCOL[k]) for k in CK])
BGC = "#F7F4EA"; LANDC = "#E6E0CE"
fig = plt.figure(figsize=(12, 15), dpi=200, facecolor=BGC)
fig.text(.045, .972, "What the world grows", fontproperties=DISP, fontsize=56, color=FG, va="top")
fig.text(.045, .912, f"The leading crop on every 10 km square of the world's farmland, from {R['meta']['n_crops']} crops in CROPGRIDS (about 2020).\nFainter squares have less of their land under these crops.",
         fontproperties=SERP, fontsize=16, color=FG, va="top", linespacing=1.4)
ext = (-12.3e6, 15.6e6, -5.9e6, 8.3e6)
ax = fig.add_axes([0, .472, 1, .39]); world(ax, lambda i: LANDC, lw=.3, extent=ext, ec=BGC)
r, c, ok, h = ee_sample(3000, ext); dom = g["bi"][r, c]; dens = g["dens"][r, c]; m = ok & (dom > 0) & (dens >= .002)
rgba = np.zeros((h, 3000, 4)); rgba[m, :3] = COLS[dom[m] - 1]; rgba[m, 3] = np.clip(.2 + .8 * (np.log10(np.clip(dens[m], 1e-3, 1)) + 3) / 2.6, .2, 1)
ax.imshow(rgba, extent=ext, zorder=2, interpolation="nearest")
MAIN = ["wheat", "maize", "rice", "soybean", "barley", "sorghum", "millet", "oats", "rapeseed", "sunflower", "groundnut", "sesame", "bean", "cowpea",
        "cassava", "potato", "sugarcane", "oilpalm", "cocoa", "coffee", "rubber", "coconut", "olive", "cotton"]
LEGP = SERP.copy(); LEGP.set_size(13)
fig.legend(handles=[Patch(fc=CCOL[k], ec="none", label=CNAME[k]) for k in MAIN], loc="upper left", bbox_to_anchor=(.04, .476), ncol=6, frameon=False,
           prop=LEGP, handlelength=1.1, columnspacing=1.3, labelspacing=.5)
fig.text(.045, .362, "Other crops (shown, not listed): rye, chickpeas, lentils, dry peas, yams, sugar beet, tea, grapes, bananas, plantains.", family=MONO, fontsize=10, color=MUT)
nums = [(f"{R['grid']['half_on_land_pct']:.1f}%", "#B5562E", "of the world's land holds\nhalf the harvested area\nof these crops"),
        (f"{R['crops']['top4_share_2024']:.0f}%", "#C9921A", "of all harvested land is\nwheat, maize, rice or\nsoya beans (FAOSTAT 2024)"),
        (f"{R['land']['past_of_agri']:.0f}%", "#5E8A3A", "of the world's farmland\nis pasture, not crops\n(FAOSTAT 2023)"),
        (f"×{R['crops']['by_k']['soybean']['x']:.0f}", "#2E6B4F", f"soya bean area since\n1961; oil palm ×{R['crops']['by_k']['oilpalm']['x']:.0f}")]
for i, (big, col, small) in enumerate(nums):
    x = .045 + i * .235
    fig.text(x, .354, big, fontproperties=DISP, fontsize=44, color=col, va="top")
    fig.text(x, .306, small, family=MONO, fontsize=11, color=FG, va="top", linespacing=1.25)
SM = [("rice", "Rice", f"{R['belts']['rice_asia']:.0f}% in South, Southeast\nand East Asia"), ("soybean", "Soya beans", f"{R['belts']['soy_americas']:.0f}% in the Americas"),
      ("cocoa", "Cocoa", f"{R['belts']['cocoa_wafrica']:.0f}% in West Africa")]
ext2 = (-12.3e6, 15.6e6, -5.2e6, 7.9e6)
for i, (k, n, sub) in enumerate(SM):
    a = fig.add_axes([.02 + i * .325, .088, .315, .12]); world(a, lambda iso: LANDC, lw=.2, extent=ext2, ec=BGC)
    r, c, ok, h = ee_sample(1100, ext2); f = np.asarray(H[CK.index(k)])[r, c] / g["cell_ha"][r]; mm = ok & (f >= 1e-3)
    t = np.clip((np.log10(np.clip(f, 1e-3, 1)) + 3) / 3, 0, 1)
    cm = mcolors.LinearSegmentedColormap.from_list("c", [mix(CCOL[k], "#FFFFFF", .7), CCOL[k], mix(CCOL[k], "#000000", .5)])
    im = np.zeros((h, 1100, 4)); im[mm] = cm(t[mm]); im[mm, 3] = .35 + .65 * t[mm]; a.imshow(im, extent=ext2, zorder=2, interpolation="nearest")
    fig.text(.03 + i * .325, .207, f"{n}: {R['crops']['by_k'][k]['ha_2024'] / 1e6:.0f} million ha", family=MONO, fontsize=12.5, color=FG)
    fig.text(.03 + i * .325, .088, sub, family=MONO, fontsize=10.5, color=MUT, va="top")
fig.text(.045, .234, "Where three crops are grown (darker = more of the land)", fontproperties=SERB, fontsize=14, color=FG)
fig.text(.045, .012, "Sources: CROPGRIDS v1.08, Tang et al. (2024) Scientific Data 11:413 (CC BY 4.0); FAOSTAT crops and land use (FAO, CC BY 4.0); Natural Earth.\n"
         "Harvested area, not production. CROPGRIDS is modelled: read regions, not single squares.\n"
         "Analysis and chart: Tristan Hotham, with Python and matplotlib  ·  maps.tristanhotham.com/crop-map", family=MONO, fontsize=9.5, color=MUT, linespacing=1.5, va="bottom")
out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "what_the_world_grows.png")
fig.savefig(out, facecolor=BGC, dpi=200)
print("ok", out)
