"""World outlines, country label points and city names for the page and figures, from Natural Earth (public domain):
  data/world.json         : simplified 1:50m country outlines keyed by ISO3 (Somaliland merged into Somalia, Northern
                            Cyprus into Cyprus, Australian minor territories into Australia)
  data/countries_geo.json : ISO3 -> name, label point, continent, population estimate
  data/cities.json        : the largest populated places, for map labels
  WORK/world_full.json    : unsimplified outlines for figures"""
from shapely.geometry import shape, mapping
from shapely.ops import unary_union
from common import *

MERGE = {"SOL": "SOM", "CYN": "CYP", "IOA": "AUS", "ATC": "AUS", "KAS": "IND"}
NAMES = {"USA": "United States", "GBR": "United Kingdom", "RUS": "Russia", "COD": "DR Congo", "CAF": "Central African Republic",
         "KOR": "South Korea", "PRK": "North Korea", "LAO": "Laos", "VNM": "Vietnam", "BOL": "Bolivia", "VEN": "Venezuela",
         "IRN": "Iran", "SYR": "Syria", "TZA": "Tanzania", "MDA": "Moldova", "CZE": "Czechia", "BIH": "Bosnia and Herzegovina",
         "DOM": "Dominican Republic", "SSD": "South Sudan", "GNQ": "Equatorial Guinea", "CIV": "Côte d'Ivoire", "TUR": "Türkiye",
         "MKD": "North Macedonia", "SWZ": "Eswatini", "TLS": "Timor-Leste", "BRN": "Brunei", "PSE": "Palestine", "ESH": "Western Sahara",
         "SLB": "Solomon Islands", "FLK": "Falkland Islands", "ATF": "French Southern Lands", "CPV": "Cabo Verde"}
src = jload(NE50)
groups = {}
meta = {}
for f in src["features"]:
    p = f["properties"]
    iso = p["ISO_A3_EH"] if p["ISO_A3_EH"] != "-99" else p["ADM0_A3"]
    iso = MERGE.get(p["ADM0_A3"], iso)
    if iso == "ATA":
        continue
    groups.setdefault(iso, []).append(shape(f["geometry"]))
    if p["ADM0_A3"] not in MERGE:
        meta[iso] = {"name": NAMES.get(iso, p["NAME"]), "lon": round(p["LABEL_X"], 3), "lat": round(p["LABEL_Y"], 3),
                     "continent": p["CONTINENT"], "pop": int(p["POP_EST"] or 0), "n3": p["ISO_N3_EH"]}
feats, full = [], []
for iso, gs in groups.items():
    g = unary_union(gs)
    full.append({"type": "Feature", "properties": {"iso": iso}, "geometry": mapping(g)})
    s = g.simplify(0.04, preserve_topology=True)
    if s.is_empty:
        continue
    m = mapping(s)

    def rnd(c):
        return [rnd(x) for x in c] if isinstance(c[0], (list, tuple)) else [round(c[0], 2), round(c[1], 2)]
    m = {"type": m["type"], "coordinates": rnd(m["coordinates"])}
    feats.append({"type": "Feature", "properties": {"iso": iso, "name": meta[iso]["name"]}, "geometry": m})
jsave({"type": "FeatureCollection", "features": feats}, f"{DATA}/world.json")
jsave({"type": "FeatureCollection", "features": full}, f"{WORK}/world_full.json")
jsave(meta, f"{DATA}/countries_geo.json")
pl = jload(NEPLACES)["features"]
cities = sorted(({"name": p["properties"]["name"], "lat": round(p["properties"]["latitude"], 3), "lon": round(p["properties"]["longitude"], 3),
                  "pop": int(p["properties"]["pop_max"] or 0)} for p in pl), key=lambda c: -c["pop"])
seen, out = set(), []
for c in cities:
    k = (c["name"], round(c["lat"]), round(c["lon"]))
    if k in seen or c["pop"] < 60000:
        continue
    seen.add(k); out.append(c)
out = out[:2200]
jsave(out, f"{DATA}/cities.json")
print("countries", len(feats), "cities", len(out), os.path.getsize(f"{DATA}/world.json") // 1024, "KB")
