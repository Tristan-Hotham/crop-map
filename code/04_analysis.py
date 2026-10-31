"""All analysis: FAOSTAT land use and crops by country and year, and the CROPGRIDS grids. Writes
  data/results.json      : every number quoted anywhere (page, paper, blog, collage, post)
  data/site.json         : per-country page data (land use, top crops, speciality), embedded in the page
  data/page/series.json  : per-country annual series for the page's country panel (loaded on demand)
  data/country_landuse.csv, data/country_crops.csv, data/world_crops_by_year.csv, data/crop_totals.csv
  WORK/grid.npz          : 0.1 degree derived grids (dominant crop, second crop, totals, diversity, land fraction)"""
import math
import numpy as np, pandas as pd, netCDF4 as nc
from common import *

GW = os.environ.get("CROPGRID", "/home/claude/_cropwork")
A = jload(f"{WORK}/areas.json"); G = jload(f"{DATA}/countries_geo.json"); ITEMS = {int(k): v for k, v in jload(f"{WORK}/qcl_items.json").items()}
n3 = {v["n3"].lstrip("0"): k for k, v in G.items()}
ISO = {int(k): n3.get(v["m49"].lstrip("0")) for k, v in A.items()}
FORMER = {228: ("USSR", ["ARM", "AZE", "BLR", "EST", "GEO", "KAZ", "KGZ", "LVA", "LTU", "MDA", "RUS", "TJK", "TKM", "UKR", "UZB"]),
          248: ("Yugoslavia", ["BIH", "HRV", "MKD", "MNE", "SRB", "SVN"]), 51: ("Czechoslovakia", ["CZE", "SVK"]),
          62: ("Ethiopia PDR", ["ETH", "ERI"]), 15: ("Belgium-Luxembourg", ["BEL", "LUX"]), 206: ("Sudan (former)", ["SDN", "SSD"]),
          186: ("Serbia and Montenegro", ["SRB", "MNE"])}
CN = lambda iso: G[iso]["name"] if iso in G else iso
R = {"meta": {"page": PAGE, "repo": REPO, "doi": DOI, "retrieved": RETRIEVED_FAO, "n_crops": len(CK), "n_crops_cropgrids": 173}}

# ---------------------------------------------------------------- friendly FAO item names and families
OVR = {"Maize (corn)": "Maize", "Seed cotton, unginned": "Cotton", "Rape or colza seed": "Rapeseed", "Natural rubber in primary forms": "Rubber",
       "Oil palm fruit": "Oil palm", "Coffee, green": "Coffee", "Tea leaves": "Tea", "Groundnuts, excluding shelled": "Groundnuts",
       "Cassava, fresh": "Cassava", "Coconuts, in shell": "Coconuts", "Plantains and cooking bananas": "Plantains",
       "Other vegetables, fresh n.e.c.": "Other vegetables", "Beans, dry": "Dry beans", "Peas, dry": "Dry peas", "Chick peas, dry": "Chickpeas",
       "Cow peas, dry": "Cowpeas", "Lentils, dry": "Lentils", "Sunflower seed": "Sunflower", "Sesame seed": "Sesame",
       "Onions and shallots, dry (excluding dehydrated)": "Onions", "Mangoes, guavas and mangosteens": "Mangoes and guavas",
       "Cashew nuts, in shell": "Cashew nuts", "Unmanufactured tobacco": "Tobacco", "Karite nuts (sheanuts)": "Shea nuts",
       "Chillies and peppers, dry (Capsicum spp., Pimenta spp.), raw": "Dried chillies", "Chillies and peppers, green (Capsicum spp. and Pimenta spp.)": "Chillies and peppers",
       "Edible roots and tubers with high starch or inulin content, n.e.c., fresh": "Other roots and tubers",
       "Anise, badian, coriander, cumin, caraway, fennel and juniper berries, raw": "Anise, coriander and cumin",
       "Other nuts (excluding wild edible nuts and groundnuts), in shell, n.e.c.": "Other nuts", "Pigeon peas, dry": "Pigeon peas",
       "Broad beans and horse beans, dry": "Field and broad beans", "Broad beans and horse beans, green": "Green broad beans", "Bambara beans, dry": "Bambara beans",
       "Pepper (Piper spp.), raw": "Pepper", "Nutmeg, mace, cardamoms, raw": "Nutmeg and cardamom", "Cloves (whole stems), raw": "Cloves",
       "Cinnamon and cinnamon-tree flowers, raw": "Cinnamon", "Kenaf, and other textile bast fibres, raw or retted": "Kenaf",
       "Locust beans (carobs)": "Carobs", "Maté leaves": "Maté", "Green corn (maize)": "Green maize", "Eggplants (aubergines)": "Aubergines",
       "Tangerines, mandarins, clementines": "Mandarins", "Pomelos and grapefruits": "Grapefruit", "Lemons and limes": "Lemons and limes",
       "Other berries and fruits of the genus vaccinium n.e.c.": "Other berries", "Pyrethrum, dried flowers": "Pyrethrum",
       "Hop cones": "Hops", "Ginger, raw": "Ginger", "Vanilla, raw": "Vanilla", "Sisal, raw": "Sisal", "Jute, raw or retted": "Jute",
       "Flax, raw or retted": "Flax", "True hemp, raw or retted": "Hemp", "Ramie, raw or retted": "Ramie", "Abaca, manila hemp, raw": "Abacá",
       "Agave fibres, raw, n.e.c.": "Agave fibres", "Cantaloupes and other melons": "Melons", "Carrots and turnips": "Carrots and turnips",
       "Cauliflowers and broccoli": "Cauliflower and broccoli", "Cucumbers and gherkins": "Cucumbers", "Pumpkins, squash and gourds": "Pumpkins and squash",
       "Peaches and nectarines": "Peaches", "Plums and sloes": "Plums", "Leeks and other alliaceous vegetables": "Leeks", "Lettuce and chicory": "Lettuce",
       "Other stimulant, spice and aromatic crops, n.e.c.": "Other spices", "Other tropical fruits, n.e.c.": "Other tropical fruit",
       "Other fruits, n.e.c.": "Other fruit", "Other citrus fruit, n.e.c.": "Other citrus", "Other pulses n.e.c.": "Other pulses",
       "Other oil seeds, n.e.c.": "Other oilseeds", "Other fibre crops, raw, n.e.c.": "Other fibre crops", "Other sugar crops n.e.c.": "Other sugar crops",
       "Cereals n.e.c.": "Other cereals", "Mixed grain": "Mixed grain", "Peppermint, spearmint": "Mint", "Other beans, green": "Green beans",
       "Peas, green": "Green peas", "Onions and shallots, green": "Spring onions", "Castor oil seeds": "Castor beans", "Kapok fruit": "Kapok",
       "Areca nuts": "Areca nuts", "Kola nuts": "Kola nuts", "Tallowtree seeds": "Tallowtree seeds", "Tung nuts": "Tung nuts", "Sweet potatoes": "Sweet potatoes",
       "Almonds, in shell": "Almonds", "Hazelnuts, in shell": "Hazelnuts", "Walnuts, in shell": "Walnuts", "Pistachios, in shell": "Pistachios",
       "Chestnuts, in shell": "Chestnuts", "Cassava leaves": "Cassava leaves", "Safflower seed": "Safflower", "Mustard seed": "Mustard seed",
       "Poppy seed": "Poppy seed", "Melonseed": "Melon seed", "Canary seed": "Canary seed", "Jojoba seeds": "Jojoba", "Hempseed": "Hempseed",
       "Other stone fruits": "Other stone fruit", "Other pome fruits": "Other pome fruit", "Sour cherries": "Sour cherries", "Green garlic": "Garlic"}
CODE2CK = {c: k for k in CK for c in CFAO[k]}
VEG = {"Cabbages", "Artichokes", "Asparagus", "Cauliflowers and broccoli", "Cucumbers and gherkins", "Eggplants (aubergines)", "Green garlic",
       "Leeks and other alliaceous vegetables", "Lettuce and chicory", "Okra", "Onions and shallots, dry (excluding dehydrated)", "Onions and shallots, green",
       "Other vegetables, fresh n.e.c.", "Pumpkins, squash and gourds", "Spinach", "Tomatoes", "Carrots and turnips", "Chillies and peppers, green (Capsicum spp. and Pimenta spp.)",
       "Other beans, green", "Peas, green", "String beans", "Broad beans and horse beans, green", "Green corn (maize)", "Chicory roots", "Cassava leaves", "Watermelons", "Cantaloupes and other melons"}
OTHERF = {"cereal": ["Buckwheat", "Cereals n.e.c.", "Fonio", "Mixed grain", "Quinoa", "Triticale", "Canary seed"],
          "pulse": ["Bambara beans, dry", "Broad beans and horse beans, dry", "Lupins", "Other pulses n.e.c.", "Pigeon peas, dry", "Vetches"],
          "oil": ["Castor oil seeds", "Hempseed", "Jojoba seeds", "Karite nuts (sheanuts)", "Linseed", "Melonseed", "Mustard seed", "Other oil seeds, n.e.c.", "Poppy seed", "Safflower seed", "Tallowtree seeds", "Tung nuts", "Kapok fruit"],
          "root": ["Sweet potatoes", "Taro", "Yautia", "Edible roots and tubers with high starch or inulin content, n.e.c., fresh"],
          "sugar": ["Other sugar crops n.e.c."],
          "fibre": ["Abaca, manila hemp, raw", "Agave fibres, raw, n.e.c.", "Flax, raw or retted", "Jute, raw or retted", "Kenaf, and other textile bast fibres, raw or retted", "Other fibre crops, raw, n.e.c.", "Ramie, raw or retted", "Sisal, raw", "True hemp, raw or retted"]}
IFAM = {}
for code, nm in ITEMS.items():
    if code in CODE2CK: IFAM[code] = CFAM[CODE2CK[code]]
    elif nm in VEG: IFAM[code] = "veg"
    else:
        IFAM[code] = next((f for f, L in OTHERF.items() if nm in L), "fruit")   # fruit, nuts, spices, stimulants, tobacco and the rest
INAME = {c: OVR.get(n, n) for c, n in ITEMS.items()}
ALLFAMS = FAMS + [("veg", "Vegetables", "#9DB8A0"), ("fruit", "Fruit, nuts, spices and other", "#C9A9B6")]
GENERIC = {c for c, n in ITEMS.items() if n.startswith("Other ") or "n.e.c." in n or n == "Mixed grain"}

# ---------------------------------------------------------------- FAOSTAT crops
q = pd.read_pickle(f"{WORK}/qcl.pkl"); q["iso"] = q["area"].map(ISO)
q["ha"] = q["ha"].fillna(0); q["t"] = q["t"].fillna(0)
world = q.groupby(["year", "item"])[["ha", "t"]].sum().reset_index()
wy = world.groupby("year").ha.sum()
c34 = [c for k in CK for c in CFAO[k]]
s34 = world[world.item.isin(c34)].groupby("year").ha.sum()
R["fao"] = {"world_ha_2020": float(wy[2020]), "world_ha_2024": float(wy[2024]), "world_ha_1961": float(wy[1961]),
            "share34_2020": float(100 * s34[2020] / wy[2020]), "share34_2024": float(100 * s34[2024] / wy[2024]),
            "n_items": int(world[(world.year == 2024) & (world.ha > 0)].item.nunique()), "growth_pct": float(100 * (wy[2024] / wy[1961] - 1))}
ww = world.pivot(index="item", columns="year", values="ha").fillna(0)
crop_rows = []
for k in CK:
    v = ww.loc[CFAO[k]].sum()
    crop_rows.append({"k": k, "name": CNAME[k], "fam": CFAM[k], "ha_1961": float(v[1961]), "ha_2024": float(v[2024]), "ha_2020": float(v[2020]),
                      "chg_pct": float(100 * (v[2024] / v[1961] - 1)) if v[1961] > 0 else None, "x": float(v[2024] / v[1961]) if v[1961] > 0 else None})
crop_rows.sort(key=lambda r: -r["ha_2024"])
R["crops"] = {"rows": crop_rows}
cr = {r["k"]: r for r in crop_rows}
R["crops"]["by_k"] = cr
grow = sorted([r for r in crop_rows if r["x"]], key=lambda r: -r["x"])
R["crops"]["fastest"] = [{"k": r["k"], "name": r["name"], "x": r["x"]} for r in grow[:6]]
R["crops"]["shrinking"] = [{"k": r["k"], "name": r["name"], "chg_pct": r["chg_pct"]} for r in sorted(crop_rows, key=lambda r: r["chg_pct"] or 0)[:6]]
R["crops"]["top4_share_2024"] = float(100 * sum(r["ha_2024"] for r in crop_rows[:4]) / wy[2024])
R["crops"]["soy_x"] = cr["soybean"]["x"]; R["crops"]["palm_x"] = cr["oilpalm"]["x"]
# extra added area 1961 to 2024 explained by soy, maize, rice, wheat, oil palm, rapeseed
gain = {r["k"]: r["ha_2024"] - r["ha_1961"] for r in crop_rows}
R["crops"]["gain_mha"] = {k: round(v / 1e6, 1) for k, v in gain.items()}
R["crops"]["world_gain_mha"] = float((wy[2024] - wy[1961]) / 1e6)
R["crops"]["soy_palm_maize_gain_share"] = float(100 * (gain["soybean"] + gain["oilpalm"] + gain["maize"]) / (wy[2024] - wy[1961]))
wsr = world.copy(); wsr["name"] = wsr.item.map(INAME)
wsr[wsr.item.isin(c34) | (wsr.ha > 1e6)].to_csv(f"{DATA}/world_crops_by_year.csv", index=False, columns=["year", "item", "name", "ha", "t"])

# country x item, mean of 2022 to 2024
cq = q[q.year.between(2022, 2024) & q.iso.notna()].groupby(["iso", "item", "year"]).ha.sum().reset_index()
cq = cq.groupby(["iso", "item"]).ha.mean().reset_index()
cq = cq[cq.ha > 0]
ctot = cq.groupby("iso").ha.sum()
wt = cq.groupby("item").ha.sum(); WT = wt.sum()
cq["share"] = cq.ha / cq.iso.map(ctot); cq["wshare"] = cq.ha / cq.item.map(wt); cq["lq"] = cq.share / (cq.item.map(wt) / WT)
cq["name"] = cq.item.map(INAME); cq["fam"] = cq.item.map(IFAM)
cq.sort_values(["iso", "ha"], ascending=[True, False]).to_csv(f"{DATA}/country_crops.csv", index=False, float_format="%.4g",
                                                              columns=["iso", "item", "name", "fam", "ha", "share", "wshare", "lq"])
top = cq.sort_values("ha", ascending=False).groupby("iso").head(1).set_index("iso")
from collections import Counter
topc = Counter(top.item.map(INAME))
R["top_crop"] = {"n_countries": int(len(top)), "counts": [{"name": n, "n": c} for n, c in topc.most_common(15)]}
tc = dict(topc)
R["top_crop"]["by"] = {n: tc.get(n, 0) for n in ("Maize", "Rice", "Wheat", "Soya beans", "Cassava", "Coconuts", "Barley", "Sorghum", "Millet", "Olives", "Oil palm", "Cocoa beans", "Coffee", "Sugar cane", "Dry beans", "Groundnuts")}
for iso in ("GBR", "FRA", "USA", "BRA", "ARG", "IND", "CHN", "IDN", "MYS", "CIV", "GHA", "NGA", "RUS", "UKR", "AUS", "CAN", "ESP", "ITA", "DEU", "THA", "VNM", "BGD", "PAK", "ETH", "KAZ", "TUN", "EGY", "COD", "IRL"):
    t = top.loc[iso]; R["top_crop"][iso] = {"name": INAME[int(t["item"])], "share": float(100 * t.share), "ha": float(t.ha)}
# specialities: highest location quotient among real crops that make up at least 1% of the country's harvested area
big = ctot[ctot >= 100_000].index
sp = cq[cq.iso.isin(big) & (cq.share >= .01) & (cq.ha >= 2000) & ~cq.item.isin(GENERIC)]
spec = sp.sort_values("lq", ascending=False).groupby("iso").head(1).set_index("iso")
R["spec"] = {"n_countries": int(len(spec)), "min_country_ha": 100000}
for iso in ("GBR", "IRL", "FRA", "ESP", "ITA", "NLD", "DEU", "BEL", "DNK", "POL", "USA", "CAN", "MEX", "BRA", "ARG", "PER", "IND", "CHN", "JPN", "IDN", "TUR", "IRN", "ETH", "NGA", "KEN", "EGY", "AUS", "NZL", "UKR", "RUS", "MAR", "CIV", "GHA", "MDG", "PNG", "VNM", "THA", "BOL", "LKA", "SAU"):
    if iso in spec.index:
        s = spec.loc[iso]; R["spec"][iso] = {"name": INAME[int(s["item"])], "lq": float(s.lq), "share": float(100 * s.share), "wshare": float(100 * s.wshare), "ha": float(s.ha)}
# world leaders: which country holds the biggest share of each of the 34 crops
lead = {}
for k in CK:
    x = cq[cq.item.isin(CFAO[k])].groupby("iso").ha.sum().sort_values(ascending=False)
    lead[k] = [{"iso": i, "name": CN(i), "pct": float(100 * v / x.sum())} for i, v in x.head(5).items()]
R["leaders"] = lead
two = lambda k, a, b: float(sum(e["pct"] for e in lead[k] if e["iso"] in (a, b)))
R["belts"] = {"cocoa_civ_gha": two("cocoa", "CIV", "GHA"), "palm_idn_mys": two("oilpalm", "IDN", "MYS"),
              "soy_bra_usa_arg": float(sum(e["pct"] for e in lead["soybean"] if e["iso"] in ("BRA", "USA", "ARG"))),
              "rice_ind_chn": two("rice", "IND", "CHN"),
              "rubber_tha_idn": two("rubber", "THA", "IDN"), "olive_esp": float(next(e["pct"] for e in lead["olive"] if e["iso"] == "ESP"))}
asia = {"AFG", "BGD", "BTN", "BRN", "KHM", "CHN", "IND", "IDN", "JPN", "PRK", "KOR", "LAO", "MYS", "MMR", "NPL", "PAK", "PHL", "LKA", "TWN", "THA", "TLS", "VNM"}
rx = cq[cq.item == 27]; R["belts"]["rice_asia"] = float(100 * rx[rx.iso.isin(asia)].ha.sum() / rx.ha.sum())
wa = {"CIV", "GHA", "NGA", "CMR", "TGO", "LBR", "SLE", "GIN"}
cx = cq[cq.item == 661]; R["belts"]["cocoa_wafrica"] = float(100 * cx[cx.iso.isin(wa)].ha.sum() / cx.ha.sum())
amer = {"USA", "BRA", "ARG", "PRY", "CAN", "BOL", "URY"}
for code, key in ((236, "soy_americas"), (56, "maize_americas")):
    x = cq[cq.item == code]; R["belts"][key] = float(100 * x[x.iso.isin(amer)].ha.sum() / x.ha.sum())

# ---------------------------------------------------------------- FAOSTAT land use
l = pd.read_pickle(f"{WORK}/landuse.pkl"); l = l[l.year <= 2023]   # 2024 land use is not yet complete for all countries
l["iso"] = l["area"].map(ISO)
LI = {6601: "land", 6610: "agri", 6620: "crop", 6621: "arable", 6650: "perm", 6655: "past", 6646: "forest", 6670: "other", 6690: "irrig"}
lw = l[l.item.isin(LI)].groupby(["year", "item"]).kha.sum().unstack()
lw.columns = [LI[c] for c in lw.columns]
R["land"] = {"crop_2023": float(lw.loc[2023, "crop"] * 1e3), "crop_1961": float(lw.loc[1961, "crop"] * 1e3), "past_2023": float(lw.loc[2023, "past"] * 1e3),
             "past_1961": float(lw.loc[1961, "past"] * 1e3), "agri_2023": float(lw.loc[2023, "agri"] * 1e3), "land_2023": float(lw.loc[2023, "land"] * 1e3),
             "forest_2023": float(lw.loc[2023, "forest"] * 1e3), "agri_peak_year": int(lw.agri.idxmax()), "agri_peak": float(lw.agri.max() * 1e3),
             "past_peak_year": int(lw.past.idxmax()), "past_peak": float(lw.past.max() * 1e3), "crop_peak_year": int(lw.crop.idxmax())}
L_ = R["land"]
L_["crop_share"] = 100 * L_["crop_2023"] / L_["land_2023"]; L_["past_share"] = 100 * L_["past_2023"] / L_["land_2023"]; L_["agri_share"] = 100 * L_["agri_2023"] / L_["land_2023"]
L_["forest_share"] = 100 * L_["forest_2023"] / L_["land_2023"]; L_["crop_chg_pct"] = 100 * (L_["crop_2023"] / L_["crop_1961"] - 1)
L_["past_of_agri"] = 100 * L_["past_2023"] / L_["agri_2023"]; L_["crop_of_agri"] = 100 * L_["crop_2023"] / L_["agri_2023"]
L_["crop_gain_mha"] = (L_["crop_2023"] - L_["crop_1961"]) / 1e6
L_["agri_since_peak_mha"] = (L_["agri_peak"] - L_["agri_2023"]) / 1e6
wl = lw.reset_index(); wl.columns = ["year"] + list(lw.columns)
R["land"]["world_series"] = {c: [round(float(v) / 1e3, 1) for v in lw[c].values] for c in ("crop", "past", "forest", "agri")}
R["land"]["years"] = [int(y) for y in lw.index]
R["land"]["year"] = int(lw.index.max())
R["land"]["forest_first_year"] = int(lw.forest.first_valid_index())
lc = l[l.iso.notna() & l.item.isin(LI)].copy()
lc["k"] = lc.item.map(LI)
piv = lc.pivot_table(index=["iso", "year"], columns="k", values="kha", aggfunc="sum")
pc = l[l.iso.notna() & (l.item == 6620) & l.pc.notna()].groupby(["iso", "year"]).pc.sum()
rows = []
for iso in sorted(piv.index.get_level_values(0).unique()):
    d = piv.loc[iso]
    if 2023 not in d.index or not d.loc[2023].get("land", 0) > 0:
        continue
    v = d.loc[2023]; landA = v["land"]
    cs = d["crop"].dropna(); cs = cs[cs.index <= 2023]
    if len(cs) == 0:
        continue
    y0 = int(cs.index.min())
    b0 = cs.loc[y0:y0 + 2].mean(); b1 = cs.loc[2021:2023].mean()
    rows.append({"iso": iso, "name": CN(iso), "land_kha": landA, "crop_kha": v.get("crop", np.nan), "arable_kha": v.get("arable", np.nan), "perm_kha": v.get("perm", np.nan),
                 "past_kha": v.get("past", np.nan), "forest_kha": v.get("forest", np.nan), "agri_kha": v.get("agri", np.nan),
                 "crop_pct": 100 * v.get("crop", np.nan) / landA, "past_pct": 100 * v.get("past", np.nan) / landA, "forest_pct": 100 * v.get("forest", np.nan) / landA,
                 "agri_pct": 100 * v.get("agri", np.nan) / landA, "crop_ha_pp": pc.get((iso, 2023), np.nan),
                 "crop_first_year": y0, "crop_chg_pct": 100 * (b1 / b0 - 1) if b0 > 0 else np.nan, "crop_chg_kha": b1 - b0})
LU = pd.DataFrame(rows).set_index("iso")
LU.to_csv(f"{DATA}/country_landuse.csv", float_format="%.4g")
big_lu = LU[LU.land_kha >= 1000]   # countries of at least 10,000 km2
R["land"]["n_countries"] = int(len(LU))
tl = lambda col, n=5, asc=False, d=big_lu: [{"iso": i, "name": CN(i), "v": float(r[col])} for i, r in d.sort_values(col, ascending=asc).head(n).iterrows()]
R["land"]["top_crop_pct"] = tl("crop_pct"); R["land"]["top_past_pct"] = tl("past_pct"); R["land"]["top_crop_kha"] = tl("crop_kha", 6, d=LU)
R["land"]["top_crop_pp"] = tl("crop_ha_pp", 5, d=big_lu[big_lu.crop_ha_pp.notna()])
since61 = LU[LU.crop_first_year == 1961]
R["land"]["n_since_1961"] = int(len(since61))
R["land"]["top_gain_kha"] = tl("crop_chg_kha", 6, d=since61); R["land"]["top_loss_kha"] = tl("crop_chg_kha", 6, True, d=since61)
R["land"]["top_gain_pct"] = tl("crop_chg_pct", 5, d=since61[since61.crop_kha >= 1000])
R["land"]["n_grew"] = int((since61.crop_chg_pct > 0).sum()); R["land"]["n_shrank"] = int((since61.crop_chg_pct < 0).sum())
for iso in ("GBR", "BRA", "IDN", "ARG", "USA", "IND", "CHN", "RUS", "UKR", "KAZ", "AUS", "NGA", "ITA", "JPN", "BGD", "NLD", "DNK", "IRL", "MNG", "SAU", "FRA", "DEU"):
    if iso in LU.index:
        r = LU.loc[iso]; R["land"][iso] = {k: (None if pd.isna(r[k]) else float(r[k])) for k in ("crop_pct", "past_pct", "forest_pct", "agri_pct", "crop_ha_pp", "crop_chg_pct", "crop_kha", "past_kha", "crop_first_year")}
# former USSR as a whole
ussr = l[(l.area == 228) & (l.item == 6620)].set_index("year").kha
succ = l[l.iso.isin(FORMER[228][1]) & (l.item == 6620)].groupby("year").kha.sum()
R["land"]["ussr"] = {"crop_1961": float(ussr.loc[1961:1963].mean() * 1e3), "crop_1990": float(ussr.loc[1988:1990].mean() * 1e3),
                     "crop_2023": float(succ.loc[2021:2023].mean() * 1e3)}
R["land"]["ussr"]["chg_since_1990_pct"] = 100 * (R["land"]["ussr"]["crop_2023"] / R["land"]["ussr"]["crop_1990"] - 1)
R["land"]["ussr"]["loss_since_1990_mha"] = (R["land"]["ussr"]["crop_1990"] - R["land"]["ussr"]["crop_2023"]) / 1e6

# ---------------------------------------------------------------- UK
uk = q[q.iso == "GBR"].pivot_table(index="year", columns="item", values="ha", aggfunc="sum").fillna(0)
ukt = {k: CFAO[k][0] for k in ("wheat", "barley", "rapeseed", "potato", "sugarbeet", "oats", "pea")}
ukt["fieldbean"] = 181   # UK beans are field beans (broad and horse beans, dry), not dry beans
R["uk"] = {k: {"1961": float(uk.loc[1961, c]), "2024": float(uk.loc[2024, c]), "peak_year": int(uk[c].idxmax()), "peak": float(uk[c].max()),
               "m2224": float(uk.loc[2022:2024, c].mean())} for k, c in ukt.items()}
R["uk"]["rapeseed"]["first_10k_year"] = int(uk.index[uk[270] >= 10000][0])
R["uk"]["total_2024"] = float(uk.loc[2024].sum()); R["uk"]["total_1961"] = float(uk.loc[1961].sum())
R["uk"]["wheat_share_2224"] = float(100 * uk.loc[2022:2024, 15].mean() / uk.loc[2022:2024].sum(axis=1).mean())
R["uk"]["wbr_share_2224"] = float(100 * uk.loc[2022:2024, [15, 44, 270]].sum(axis=1).mean() / uk.loc[2022:2024].sum(axis=1).mean())
R["uk"]["series"] = {k: [round(float(v)) for v in uk[c].values] for k, c in ukt.items()}
R["uk"]["years"] = [int(y) for y in uk.index]
R["uk"]["spec"] = R["spec"]["GBR"]
R["uk"]["lu"] = R["land"]["GBR"]

# ---------------------------------------------------------------- grids
H = np.load(f"{GW}/crops01.npy", mmap_mode="r"); P = np.load(f"{GW}/phys01.npy", mmap_mode="r")
CG_ = jload(f"{WORK}/cg_country.json"); g = CG_["grid"]; NR, NC = g["rows"], g["cols"]
lat_n = g["n"] - 0.1 * np.arange(NR); lat_s = lat_n - 0.1
cell_ha = (6371.0072e3 ** 2) * math.radians(0.1) * (np.sin(np.radians(lat_n)) - np.sin(np.radians(lat_s))) / 1e4   # ha per cell, by row
tot = np.zeros((NR, NC), np.float64); phys = np.zeros((NR, NC), np.float64)
best = np.zeros((NR, NC), np.float32); bi = np.zeros((NR, NC), np.uint8)
for i in range(len(CK)):
    h = np.asarray(H[i]); tot += h; phys += P[i]
    up = h > best
    best = np.where(up, h, best); bi = np.where(up, i + 1, bi).astype(np.uint8)
# second crop: the largest crop that is not the dominant one
sec = np.zeros((NR, NC), np.float32); si = np.zeros((NR, NC), np.uint8)
for i in range(len(CK)):
    h = np.asarray(H[i]); m = (h > sec) & (bi != i + 1)
    sec = np.where(m, h, sec); si = np.where(m, i + 1, si).astype(np.uint8)
ent = np.zeros((NR, NC), np.float64)
with np.errstate(divide="ignore", invalid="ignore"):
    for i in range(len(CK)):
        p = np.asarray(H[i]) / tot; ent -= np.where(p > 0, p * np.log(p), 0)
div = np.where(tot > 0, np.exp(ent), 0)
dens = tot / cell_ha[:, None]
pdens = phys / cell_ha[:, None]
# land fraction per 0.1 degree cell, from the CROPGRIDS country raster (any country code = land)
cd = nc.Dataset(f"{CG}/Countries_2018.nc"); crn = np.asarray(cd["country"][:].filled(0))[::-1]; cd.close()
crn = np.where(np.isfinite(crn) & (crn >= 1), crn, 0).astype(np.int16)
r0 = int(round((89.975 - (g["n"] - 0.025)) / 0.05))
sub = crn[r0:r0 + 2 * NR]
landf = (sub > 0).reshape(NR, 2, NC, 2).mean(axis=(1, 3))
cid = sub.reshape(NR, 2, NC, 2).max(axis=(1, 3))
np.savez_compressed(f"{WORK}/grid.npz", bi=bi, si=si, tot=tot.astype(np.float32), phys=phys.astype(np.float32), div=div.astype(np.float32),
                    dens=dens.astype(np.float32), pdens=pdens.astype(np.float32), landf=landf.astype(np.float32), cid=cid, cell_ha=cell_ha)
farmed = dens >= 0.01
Wtot = tot.sum()
gr = {"cells_any": int((tot > 0).sum()), "cells_farmed": int(farmed.sum()), "farmed_share_of_area": float(100 * tot[farmed].sum() / Wtot),
      "total_ha": float(Wtot), "phys_ha": float(phys.sum()), "native_cells": CG_["native_cells"], "native_dom_half": float(100 * CG_["native_dom_half_share"])}
# concentration: share of land area that holds half the harvested area
landA = (landf * cell_ha[:, None]).ravel(); hv = tot.ravel(); o = np.argsort(-(hv / np.maximum(landA, 1)))
cum = np.cumsum(hv[o]); k50 = np.searchsorted(cum, .5 * Wtot); k90 = np.searchsorted(cum, .9 * Wtot)
gr["half_on_land_pct"] = float(100 * landA[o][:k50 + 1].sum() / landA.sum()); gr["ninety_on_land_pct"] = float(100 * landA[o][:k90 + 1].sum() / landA.sum())
gr["land_ha"] = float(landA.sum())
# dominant crop: farmed cells and harvested area in the cells each crop dominates
domc = Counter(); doma = Counter()
for i, k in enumerate(CK):
    m = farmed & (bi == i + 1); domc[k] = int(m.sum()); doma[k] = float(tot[m].sum())
nf = farmed.sum()
gr["dom_cells"] = [{"k": k, "name": CNAME[k], "n": n, "pct": float(100 * n / nf)} for k, n in domc.most_common()]
gr["dom_area"] = [{"k": k, "name": CNAME[k], "pct": float(100 * a / tot[farmed].sum())} for k, a in doma.most_common()]
famc = Counter()
for k, n in domc.items(): famc[CFAM[k]] += n
gr["dom_fam_cells"] = {f: float(100 * famc[f] / nf) for f, _, _ in FAMS}
gr["dom_by_k"] = {d["k"]: d["pct"] for d in gr["dom_cells"]}
gr["n_dom_crops"] = int(sum(1 for k in CK if domc[k] > 0))
# monoculture and diversity
gr["share_area_dom_half"] = float(100 * tot[farmed & (best >= .5 * tot)].sum() / tot[farmed].sum())
gr["div_mean_area_weighted"] = float((div * tot)[farmed].sum() / tot[farmed].sum())
gr["div_hi_cells_pct"] = float(100 * (farmed & (div >= 6)).sum() / nf)
gr["div_lo_cells_pct"] = float(100 * (farmed & (div < 1.5)).sum() / nf)
# per-country area-weighted diversity, from cells assigned to a country
C2I = {}
cdd = nc.Dataset(f"{CG}/Countries_2018.nc"); import re as _re
for m in _re.finditer(r"(\d+) - ([A-Z/]{2}), ([A-Z/]{3});", cdd["country"].getncattr("List of countries")):
    if m.group(3) != "///": C2I[int(m.group(1))] = m.group(3)
cdd.close()
dsum = np.bincount(cid[farmed].astype(int), weights=(div * tot)[farmed], minlength=300); tsum = np.bincount(cid[farmed].astype(int), weights=tot[farmed], minlength=300)
cdiv = {C2I[c]: float(dsum[c] / tsum[c]) for c in range(300) if c in C2I and tsum[c] > 2e5}
sd = sorted(cdiv.items(), key=lambda x: -x[1])
gr["div_top"] = [{"iso": i, "name": CN(i), "v": v} for i, v in sd[:5]]; gr["div_bottom"] = [{"iso": i, "name": CN(i), "v": v} for i, v in sd[-5:][::-1]]
gr["div_country"] = {i: round(v, 2) for i, v in cdiv.items()}
gr["div_n_countries"] = len(cdiv)
for iso in ("GBR", "USA", "BRA", "IND", "CHN", "ETH", "NGA", "FRA"):
    gr["div_" + iso] = cdiv.get(iso)
# CROPGRIDS against FAOSTAT 2020 by country (34 crops)
cg_c = Counter()
for k in CK:
    for iso, (hv_, pv_) in CG_["by_country"][k].items(): cg_c[iso] += hv_
fao20 = q[(q.year == 2020) & q.item.isin(c34) & q.iso.notna()].groupby("iso").ha.sum()
both = [(cg_c[i], fao20[i]) for i in fao20.index if i in cg_c and fao20[i] > 1e4 and cg_c[i] > 0]
xa, ya = np.log10([b[0] for b in both]), np.log10([b[1] for b in both])
gr["cg_fao_r_log"] = float(np.corrcoef(xa, ya)[0, 1]); gr["cg_fao_n"] = len(both)
gr["cg_total_34"] = float(sum(CG_["tot"][k][0] for k in CK)); gr["fao_2020_34"] = float(s34[2020])
gr["cg_vs_fao_pct"] = float(100 * gr["cg_total_34"] / gr["fao_2020_34"])
gr["qual"] = CG_["qual"]
gr["qual_mean"] = float(sum(CG_["qual"][k] * CG_["tot"][k][0] for k in CK) / gr["cg_total_34"])
gr["qual_low"] = sorted([{"k": k, "name": CNAME[k], "q": CG_["qual"][k]} for k in CK], key=lambda x: x["q"])[:4]
gr["multi_crop_ratio"] = float(gr["total_ha"] / gr["phys_ha"])
gr["rice_multi"] = float(CG_["tot"]["rice"][0] / CG_["tot"]["rice"][1])
R["grid"] = gr
# UK at native 0.05 degree
U = np.load(f"{GW}/uk05.npz"); UH = U["h"]
ukr0 = int(round((89.975 - (float(U["n"]) - 0.025)) / 0.05)); ukc0 = int(round((float(U["w"]) + 179.975) / 0.05))
ukm = crn[ukr0:ukr0 + UH.shape[1], ukc0:ukc0 + UH.shape[2]] == 207
# CROPGRIDS maize in the UK (0.83 Mha) comes from its European source (dataset 7) and FAOSTAT records no grain maize in the
# UK at all: it is most likely fodder maize. The UK zoom leaves maize out and says so; the with-maize figures are kept for the caveat.
mi = CK.index("maize")
for tag, arr in (("dom_with_maize", UH), ("dom", np.delete(UH, mi, axis=0))):
    keys = CK if tag == "dom_with_maize" else [k for k in CK if k != "maize"]
    ut = arr.sum(0); ub = arr.argmax(0); ucell = (ut > 0) & ukm
    ucnt = Counter()   # harvested area in the cells each crop dominates
    for i, kk in enumerate(keys): ucnt[kk] = float(ut[ucell & (ub == i)].sum())
    R["uk"][tag] = [{"k": k, "name": CNAME[k], "pct": float(100 * n / ut[ucell].sum())} for k, n in ucnt.most_common(6)]
    R["uk"]["cells" if tag == "dom" else "cells_with_maize"] = int(ucell.sum())
R["uk"]["dom_by_k"] = {d["k"]: d["pct"] for d in R["uk"]["dom"]}
R["uk"]["dom_with_maize_by_k"] = {d["k"]: d["pct"] for d in R["uk"]["dom_with_maize"]}
eum = {i: float(CG_["by_country"]["maize"].get(i, [0])[0]) for i in ("GBR", "IRL", "FIN")}
R["grid"]["eu_maize"] = eum
R["grid"]["eu_maize_fao"] = {i: float(q[(q.iso == i) & (q.year == 2020) & (q.item == 56)].ha.sum()) for i in eum}
R["uk"]["cg"] = {k: float(CG_["by_country"][k].get("GBR", [0])[0]) for k in ("wheat", "barley", "rapeseed", "potato", "sugarbeet", "oats", "maize", "pea", "bean")}
R["uk"]["div"] = cdiv.get("GBR")

# ---------------------------------------------------------------- crop totals table (CROPGRIDS and FAOSTAT)
ct = pd.DataFrame([{"crop": k, "name": CNAME[k], "family": FAMN[CFAM[k]], "fao_items": ";".join(map(str, CFAO[k])),
                    "cropgrids_harvested_ha": round(CG_["tot"][k][0]), "cropgrids_physical_ha": round(CG_["tot"][k][1]),
                    "cropgrids_quality": CG_["qual"][k], "faostat_ha_1961": round(cr[k]["ha_1961"]), "faostat_ha_2020": round(cr[k]["ha_2020"]),
                    "faostat_ha_2024": round(cr[k]["ha_2024"]), "dominant_cells_pct": round(gr["dom_by_k"].get(k, 0), 3)} for k in CK])
ct.to_csv(f"{DATA}/crop_totals.csv", index=False)

# ---------------------------------------------------------------- page data (site.json) and series
site = {"crops": [[k, CNAME[k], CFAM[k], CCOL[k]] for k in CK], "fams": [list(f) for f in ALLFAMS], "c": {}, "cname": {i: v["name"] for i, v in G.items()},
        "cpos": {i: [v["lon"], v["lat"], v["pop"]] for i, v in G.items()}}
icol = {}
for code in ITEMS:
    icol[code] = CCOL[CODE2CK[code]] if code in CODE2CK else dict((f[0], f[2]) for f in ALLFAMS)[IFAM[code]]
site["items"] = {str(c): [INAME[c], IFAM[c], icol[c]] for c in ITEMS}
for iso in set(LU.index) | set(ctot.index):
    e = {}
    if iso in LU.index:
        r = LU.loc[iso]
        e["lu"] = [None if pd.isna(r[k]) else round(float(r[k]), 2) for k in ("crop_pct", "past_pct", "forest_pct", "crop_ha_pp", "crop_chg_pct", "crop_kha", "past_kha", "land_kha")] + [int(r["crop_first_year"])]
    if iso in ctot.index:
        x = cq[cq.iso == iso].sort_values("ha", ascending=False)
        e["tot"] = round(float(ctot[iso]))
        e["top"] = [[int(t.item), round(float(t.ha)), round(float(100 * t.share), 1), round(float(t.lq), 2)] for t in x.head(8).itertuples()]
        if iso in spec.index:
            s = spec.loc[iso]; e["sp"] = [int(s["item"]), round(float(s.lq), 1), round(float(100 * s.share), 1), round(float(100 * s.wshare), 1)]
    if iso in cdiv: e["div"] = round(cdiv[iso], 2)
    site["c"][iso] = e
jsave(site, f"{DATA}/site.json")
ser = {"years_c": list(range(1961, 2025)), "years_l": list(range(1961, 2024)), "c": {}}
for iso in ctot.index:
    x = q[(q.iso == iso)].pivot_table(index="year", columns="item", values="ha", aggfunc="sum").reindex(range(1961, 2025)).fillna(0)
    items = [t[0] for t in site["c"][iso]["top"][:6]]
    e = {"i": items, "v": [[round(float(v) / 1e3, 1) for v in x[c].values] if c in x else [] for c in items]}
    e["all"] = [round(float(v) / 1e3, 1) for v in x.sum(axis=1).values]
    ser["c"][iso] = e
for iso in LU.index:
    d = piv.loc[iso].reindex(range(1961, 2024))
    ser["c"].setdefault(iso, {})["lu"] = {k: [None if pd.isna(v) else round(float(v), 1) for v in d[k].values] if k in d else [] for k in ("crop", "past", "forest")}
jsave(ser, f"{PAGE_D}/series.json")

# ---------------------------------------------------------------- tidy and save
def clean(o):
    if isinstance(o, dict): return {str(k): clean(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)): return [clean(v) for v in o]
    if isinstance(o, (np.floating, float)): return None if not np.isfinite(o) else round(float(o), 4)
    if isinstance(o, np.integer): return int(o)
    return o
R = clean(R)
jsave(R, f"{DATA}/results.json", indent=1)
print(json.dumps({k: R[k] for k in ("fao", "land")}, indent=0)[:3000])
print({k: v for k, v in R["grid"].items() if k not in ("div_country", "qual")})
print(R["top_crop"]["counts"]); print({k: v for k, v in R["spec"].items()}); print(R["belts"]); print(R["uk"]["dom"], R["crops"]["fastest"], R["crops"]["shrinking"])
