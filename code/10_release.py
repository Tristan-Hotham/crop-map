"""Blog post and meta (release/blog), Zenodo files and metadata (release/zenodo).
Zenodo copies of files that also live elsewhere in the repo are hard links."""
import re, zipfile, json as _json
from common import *
import importlib.util
spec_ = importlib.util.spec_from_file_location("b", os.path.join(ROOT, "code", "06_build_site.py")); spec_.loader.exec_module(importlib.util.module_from_spec(spec_))  # shared asserts

R = jload(f"{DATA}/results.json")
REL = os.path.join(ROOT, "release"); NAME = "Hotham_What_the_World_Grows"
fs = R["land"]["world_series"]
# facts in the blog alt text
assert round(fs["forest"][29], -1) == 4340 and round(fs["forest"][-1], -1) == 4150 and 3150 < fs["past"][0] < 3250 and 3250 < max(fs["past"]) < 3350 and 3050 < fs["past"][-1] < 3150
assert round(fs["crop"][0], -1) == 1340 and round(fs["crop"][-1], -1) == 1580
assert [round(R["crops"]["by_k"][k]["ha_2024"] / 1e6) for k in ("wheat", "maize", "rice", "soybean")] == [220, 210, 172, 143]
sp = {i: round(R["spec"][i]["lq"]) for i in ("SAU", "MDG", "NZL", "BOL", "BEL", "PER", "GBR", "IND")}
assert sp == {"SAU": 374, "MDG": 328, "NZL": 314, "BOL": 229, "BEL": 157, "PER": 133, "GBR": 24, "IND": 5}, sp
assert R["spec"]["BEL"]["name"] == "Flax" and R["spec"]["PER"]["name"] == "Quinoa" and R["spec"]["IND"]["name"] == "Pigeon peas"
DOI_URL = "https://doi.org/" + DOI if not DOI.startswith("{{") else "{{DOI_URL}}"

post = open(os.path.join(ROOT, "code", "blog_template.html"), encoding="utf-8").read()
post = fill(post, R).replace("{{DOI_URL}}", DOI_URL)
used = re.findall(r"\{\{IMG\|([^|]+)\|", post)
assert 5 <= len(used) <= 8
for img in used:
    assert os.path.exists(f"{REL}/blog/{img}"), img
for fn in os.listdir(f"{REL}/blog"):
    if fn.startswith("b_") and fn not in used:
        os.remove(f"{REL}/blog/{fn}")
vis = re.sub(r"<!--.*?-->", "", post, flags=re.S)
for bad in ("\u2014", "\u2013", "--", "DSIT", "DCMS"):
    assert bad not in vis, bad
assert not re.search(r"\{\{(?!IMG\||DOI_URL\}\})", post)
open(f"{REL}/blog/post.html", "w", encoding="utf-8").write(post)
words = len(re.sub(r"<[^>]+>|\{\{IMG\|[^}]*\}\}", " ", vis).split())
meta = {"title": "What the world grows: farmland and crops on one map",
        "slug": "crop-map",
        "excerpt": f"The leading crop on every 10 km square of the world's farmland, and sixty years of change in how much land we farm. Wheat, maize, rice and soya beans cover {R['crops']['top4_share_2024']:.0f}% of the harvest, and half of it grows on {R['grid']['half_on_land_pct']:.1f}% of the world's land.",
        "seo_description": "A world map of what farmers grow: the leading crop on every 10 km of farmland, 34 crops, and every country's cropland since 1961.",
        "tags": ["farming", "crops", "agriculture", "land use", "maps", "data visualisation", "FAOSTAT", "CROPGRIDS"],
        "header_alt": f"Title card reading 'What the world grows' in black and terracotta on cream, beside a world map colouring farmland by its leading crop: gold wheat across Europe and the steppes, orange maize, blue rice in Asia and green soya beans in the Americas. Text: half the harvest of 34 crops grows on {R['grid']['half_on_land_pct']:.1f}% of the world's land."}
assert len(meta["seo_description"]) < 160, len(meta["seo_description"])
jsave(meta, f"{REL}/blog/meta.json", indent=2)

# Zenodo
Z = f"{REL}/zenodo"; os.makedirs(Z, exist_ok=True)


def link(src, dst):
    if os.path.exists(dst): os.remove(dst)
    os.link(src, dst)


link(f"{REL}/paper/{NAME}.pdf", f"{Z}/{NAME}.pdf")
zp = f"{Z}/crop-map_code_and_data.zip"
with zipfile.ZipFile(zp, "w", zipfile.ZIP_DEFLATED) as z:
    for d in ("code", "data", "data/page"):
        for fn in sorted(os.listdir(os.path.join(ROOT, d))):
            p = os.path.join(ROOT, d, fn)
            if os.path.isdir(p) or fn.endswith(".pyc"):
                continue
            z.write(p, f"crop-map/{d}/{fn}")
    for fn in ("README.md", "LICENSE"):
        z.write(os.path.join(ROOT, fn), f"crop-map/{fn}")
tex = open(f"{REL}/paper/{NAME}.tex", encoding="utf-8").read()
ab = re.search(r"\\begin\{center\}\\textbf\{Abstract\}\\end\{center\}\n(.*?)\n\n\\textbf\{Keywords", tex, re.S).group(1)
ab = ab.replace("\\%", "%").replace("\\&", "&")
zmeta = {"metadata": {
    "title": "What the World Grows: Farmland and Crops on One Map, from CROPGRIDS and FAOSTAT",
    "upload_type": "publication", "publication_type": "workingpaper",
    "description": f"<p>{ab}</p><p>Interactive version: {PAGE}. Data and code: {REPO}.</p>",
    "creators": [{"name": "Hotham, Tristan", "affiliation": "Independent researcher", "orcid": "0000-0003-4931-9349"}],
    "keywords": ["crops", "farmland", "agriculture", "land use", "cropland", "pasture", "CROPGRIDS", "FAOSTAT", "maps"],
    "license": "cc-by-4.0", "access_right": "open", "language": "eng",
    "related_identifiers": [{"identifier": REPO, "relation": "isSupplementedBy", "resource_type": "software"},
                            {"identifier": PAGE, "relation": "isSupplementedBy", "resource_type": "other"},
                            {"identifier": "10.1038/s41597-024-03247-7", "relation": "isDerivedFrom", "resource_type": "dataset"},
                            {"identifier": "https://www.fao.org/faostat/", "relation": "isDerivedFrom", "resource_type": "dataset"},
                            {"identifier": "https://www.naturalearthdata.com/", "relation": "isDerivedFrom", "resource_type": "dataset"}],
    "notes": AI},
    "files": [f"{NAME}.pdf", "crop-map_code_and_data.zip"]}
jsave(zmeta, f"{Z}/metadata.json", indent=2)
s = _json.dumps(zmeta, ensure_ascii=False) + _json.dumps(meta, ensure_ascii=False)
assert "\u2014" not in s and "\u2013" not in s and "--" not in s
print("blog words", words, "figures", len(used), "; zenodo", sorted(os.listdir(Z)), os.path.getsize(zp) // 1024, "KB zip")
