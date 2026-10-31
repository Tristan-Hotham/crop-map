"""Shared paths and helpers for the crop-map project. Raw inputs are read in place (paths below); intermediates live in
memory (/dev/shm), not in the repo."""
import json, gzip, os, re, unicodedata

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAWD = "/home/claude/newdata/raw"
CG = f"{RAWD}/cg"                     # CROPGRIDS v1.08 NetCDF files, one per crop, plus Countries_2018.nc (figshare 22491997)
FAO = f"{RAWD}/fao"                   # FAOSTAT bulk downloads (Production_Crops_Livestock, Inputs_LandUse), latin1 CSV
QCL = f"{FAO}/Production_Crops_Livestock_E_All_Data_(Normalized).csv"
RL = f"{FAO}/Inputs_LandUse_E_All_Data_(Normalized).csv"
GEO = f"{RAWD}/geo"                   # Natural Earth and UK boundaries
NE50 = f"{GEO}/ne_50m_admin_0_countries.geojson"
NE10 = f"{GEO}/ne_10m_admin_0_countries.geojson"
NELAND = f"{GEO}/ne_50m_land.geojson"
NEPLACES = f"{GEO}/ne_10m_populated_places_simple.geojson"
UKCTY = f"{GEO}/counties_uk.geojson"
DATA = os.path.join(ROOT, "data")
PAGE_D = os.path.join(DATA, "page")
SHM = os.environ.get("CROPTMP", "/dev/shm/crop")
WORK = os.path.join(SHM, "work")
for d in (DATA, PAGE_D, WORK):
    os.makedirs(d, exist_ok=True)

SLUG = "crop-map"
PAGE = "https://maps.tristanhotham.com/crop-map/"
REPO = "https://github.com/Tristan-Hotham/crop-map"
DOI = os.environ.get("CROP_DOI", "{{DOI}}")            # set CROP_DOI=10.5281/zenodo.N and rerun 06, 08, 10 to fill it in
BLOG = os.environ.get("CROP_BLOG", "https://blog.tristanhotham.com/2026/10/31/crop-map/")
RETRIEVED_FAO = "2026"
AI = ("I wrote the text, with drafting and editing assistance from Claude (Anthropic), which also helped "
      "prepare the analysis code. I reviewed and checked all text and results.")

# The 34 CROPGRIDS crops used here: key, display name, family, FAOSTAT item code(s)
CROPS = [
    ("wheat", "Wheat", "cereal", [15]), ("maize", "Maize", "cereal", [56]), ("rice", "Rice", "cereal", [27]),
    ("barley", "Barley", "cereal", [44]), ("sorghum", "Sorghum", "cereal", [83]), ("millet", "Millet", "cereal", [79]),
    ("oats", "Oats", "cereal", [75]), ("rye", "Rye", "cereal", [71]),
    ("soybean", "Soya beans", "oil", [236]), ("rapeseed", "Rapeseed", "oil", [270]), ("sunflower", "Sunflower", "oil", [267]),
    ("groundnut", "Groundnuts", "oil", [242]), ("sesame", "Sesame", "oil", [289]),
    ("bean", "Dry beans", "pulse", [176]), ("chickpea", "Chickpeas", "pulse", [191]), ("cowpea", "Cowpeas", "pulse", [195]),
    ("lentil", "Lentils", "pulse", [201]), ("pea", "Dry peas", "pulse", [187]),
    ("cassava", "Cassava", "root", [125]), ("potato", "Potatoes", "root", [116]), ("yam", "Yams", "root", [137]),
    ("sugarcane", "Sugar cane", "sugar", [156]), ("sugarbeet", "Sugar beet", "sugar", [157]),
    ("oilpalm", "Oil palm", "tree", [254]), ("coconut", "Coconut", "tree", [249]), ("coffee", "Coffee", "tree", [656]),
    ("cocoa", "Cocoa", "tree", [661]), ("tea", "Tea", "tree", [667]), ("rubber", "Rubber", "tree", [836]),
    ("olive", "Olives", "tree", [260]), ("grape", "Grapes", "tree", [560]), ("banana", "Bananas", "tree", [486]),
    ("plantain", "Plantains", "tree", [489]),
    ("cotton", "Cotton", "fibre", [328]),
]
CK = [c[0] for c in CROPS]
CNAME = {c[0]: c[1] for c in CROPS}
CFAM = {c[0]: c[2] for c in CROPS}
CFAO = {c[0]: c[3] for c in CROPS}
FAMS = [("cereal", "Cereals", "#D9A21B"), ("oil", "Oilseeds", "#7DB343"), ("pulse", "Pulses", "#B5562E"),
        ("root", "Roots and tubers", "#7B4F9E"), ("sugar", "Sugar crops", "#D2559B"),
        ("tree", "Tree and plantation crops", "#1F6B4A"), ("fibre", "Fibre (cotton)", "#7F8CA8")]
FAMN = {f[0]: f[1] for f in FAMS}
FAMC = {f[0]: f[2] for f in FAMS}
# one colour per crop; the four big crops get clearly different hues (rice is paddy blue), the rest are shades of their family
CCOL = {
    "wheat": "#E3B23C", "maize": "#EE8434", "rice": "#4A90B8", "barley": "#C9A66B", "sorghum": "#A65A2A", "millet": "#8C6A2C",
    "oats": "#E3D29B", "rye": "#9E8A55",
    "soybean": "#7DB343", "rapeseed": "#D2DC3C", "sunflower": "#4E7A23", "groundnut": "#B2A86A", "sesame": "#5B6B2E",
    "bean": "#B5562E", "chickpea": "#D98A5E", "cowpea": "#8E3B1F", "lentil": "#C46A4A", "pea": "#E0A487",
    "cassava": "#7B4F9E", "potato": "#B095CF", "yam": "#5A347A",
    "sugarcane": "#D2559B", "sugarbeet": "#EB9BC6",
    "oilpalm": "#1F6B4A", "coconut": "#5FA88A", "coffee": "#5B3A29", "cocoa": "#8A5A3C", "tea": "#2E8B57", "rubber": "#3C4F3F",
    "olive": "#8C9A5B", "grape": "#7A2E5A", "banana": "#3FA76A", "plantain": "#2A7F5F",
    "cotton": "#7F8CA8",
}


def jload(path):
    op = gzip.open if path.endswith(".gz") else open
    with op(path, "rt", encoding="utf-8") as f:
        return json.load(f)


def jsave(obj, path, indent=None):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=indent, separators=None if indent else (",", ":"))


def norm(s):
    s = unicodedata.normalize("NFKD", str(s))
    s = "".join(ch for ch in s if not unicodedata.combining(ch)).lower()
    return re.sub(r"[\W_]+", " ", s).strip()


def get(R, path):
    v = R
    for k in path.split("."):
        v = v[int(k)] if isinstance(v, list) else v[k]
    return v


def fmt(v, f):
    """Number formats used in templates: int (thousands commas), pc (rounded per cent), f1, f2, mha (millions of hectares, 0 dp),
    mha1 (1 dp), raw."""
    if f is None or f == "raw": return str(v)
    if f == "int": return f"{round(float(v)):,}"
    if f == "pc": return f"{round(float(v))}%"
    if f == "pc1": return f"{float(v):.1f}%"
    if f == "f1": return f"{float(v):.1f}"
    if f == "f2": return f"{float(v):.2f}"
    if f == "mha": return f"{float(v) / 1e6:,.0f}"
    if f == "mha1": return f"{float(v) / 1e6:,.1f}"
    if f == "kmha": return f"{float(v) / 1e3:,.1f}"          # thousand ha -> million ha, 1 dp
    if f == "kmhaabs": return f"{abs(float(v)) / 1e3:,.1f}"
    if f == "pcabs": return f"{round(abs(float(v)))}%"
    if f == "x": return f"{float(v):.0f}"                     # a multiple, no decimals
    raise ValueError(f)


def fill(text, R, fmtfun=fmt, skip=("IMG", "TABLE_", "DOI", "BLOG_URL")):
    pat = r"\{\{(?!" + "|".join(skip) + r")([^}|]+)(\|(\w+))?\}\}"
    return re.sub(pat, lambda m: fmtfun(get(R, m.group(1)), m.group(3)), text)
