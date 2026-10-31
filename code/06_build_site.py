"""Build index.html from code/page_template.html. Every number in the text is a {{path|format}} token filled from
data/results.json; page data (results, site.json, world.json, cities) is embedded; data/page/*.png and series.json are
loaded by the page. Facts stated in words are checked here (also imported by the blog and paper builds). The full-screen
map snippet (code/fullscreen_snippet.html, from the reference studies) is pasted before </body>."""
import json, re
from common import *

R = jload(f"{DATA}/results.json")
SITE = jload(f"{DATA}/site.json")
L_, C_, G_, U_ = R["land"], R["crops"], R["grid"], R["uk"]
it = lambda c: SITE["items"][str(c)][0]
iso_list = lambda L: [x["iso"] for x in L]

# ---- facts stated in words (page, blog, paper, collage) ----
assert iso_list(L_["top_crop_kha"][:4]) == ["IND", "USA", "CHN", "RUS"]
assert iso_list(L_["top_crop_pct"][:2]) == ["RWA", "BGD"] and L_["top_crop_pp"][0]["iso"] == "KAZ"
assert iso_list(L_["top_gain_kha"][:6]) == ["BRA", "ARG", "IDN", "CHN", "NGA", "AUS"]
assert iso_list(L_["top_loss_kha"][:5]) == ["USA", "ITA", "POL", "ESP", "FRA"] and L_["top_loss_kha"][0]["v"] < 3 * L_["top_loss_kha"][1]["v"]
assert L_["past_peak_year"] == 2000 and L_["agri_peak_year"] == 2000 and L_["crop_peak_year"] == L_["year"] == 2023
assert 30 <= L_["crop_of_agri"] <= 36 and 64 <= L_["past_of_agri"] <= 70        # "a third" and "two thirds"
assert round(C_["by_k"]["oilpalm"]["x"]) == 8 and round(C_["by_k"]["soybean"]["x"]) == 6   # "eightfold", "sixfold"
assert [r["k"] for r in C_["rows"][:4]] == ["wheat", "maize", "rice", "soybean"]
assert 49.5 <= C_["top4_share_2024"] <= 50.5                                       # "half the harvest"
assert {r["k"] for r in C_["shrinking"][:2]} == {"rye", "oats"}
assert iso_list(G_["div_top"][:4]) == ["BLR", "HTI", "CAF", "NGA"] and iso_list(G_["div_bottom"][:4]) == ["MYS", "AFG", "KAZ", "BGD"]
top1 = {i: it(c["top"][0][0]) for i, c in SITE["c"].items() if c.get("top")}
assert all(top1[i] == "Soya beans" for i in ("USA", "BRA", "ARG")) and top1["UKR"] == "Sunflower" and top1["MYS"] == top1["IDN"] == "Oil palm"
assert top1["CIV"] == "Cocoa beans" and top1["ESP"] == "Olives" and top1["MYS"] == "Oil palm" and top1["BGD"] == "Rice" and top1["KAZ"] == "Wheat"
assert top1["AFG"] == "Wheat" if "AFG" in top1 else True
COCO = {"LCA", "SLB", "KNA", "VUT", "GRD", "WSM", "COM", "SYC", "JAM", "MHL", "PYF", "FSM", "NRU", "COK", "TUV", "KIR", "NIU"}
assert {i for i, n in top1.items() if n == "Coconuts"} <= COCO                        # "all of them island states"
assert R["top_crop"]["counts"][0]["name"] == "Wheat" and R["top_crop"]["counts"][1]["name"] == "Maize" and R["top_crop"]["counts"][2]["name"] == "Rice"
sp = {i: R["spec"][i]["name"] for i in ("SAU", "MDG", "NZL", "BOL", "TUR", "GBR")}
assert sp == {"SAU": "Dates", "MDG": "Vanilla", "NZL": "Kiwi fruit", "BOL": "Quinoa", "TUR": "Hazelnuts", "GBR": "Field and broad beans"}, sp
assert G_["dom_cells"][0]["k"] == "wheat" and G_["dom_cells"][1]["k"] == "maize"
assert U_["dom"][0]["k"] == "wheat" and U_["dom"][1]["k"] == "barley" and U_["lu"]["crop_chg_pct"] < 0
assert U_["rapeseed"]["1961"] < 1000 and U_["fieldbean"]["1961"] < 1000 and U_["oats"]["2024"] < U_["oats"]["1961"] / 3
assert R["grid"]["eu_maize_fao"]["GBR"] == 0
assert 0.0 < G_["half_on_land_pct"] < 10
assert R["meta"]["n_crops"] == 34


def build():
    tpl = open(os.path.join(ROOT, "code", "page_template.html"), encoding="utf-8").read()
    html = fill(tpl, R).replace("{{DOI}}", DOI).replace("https://blog.tristanhotham.com/2026/10/31/crop-map/", BLOG)
    assert not re.search(r"\{\{(?!DOI\}\}|BLOG_URL\}\})", html), re.findall(r"\{\{[^}]*\}\}", html)[:5]
    J = lambda o: json.dumps(o, ensure_ascii=False, separators=(",", ":"))
    html = html.replace("/*RESULTS*/", J(R)).replace("/*SITE*/", J(SITE))
    html = html.replace("/*WORLD*/", open(f"{DATA}/world.json", encoding="utf-8").read())
    html = html.replace("/*CITIES*/", J([{"name": x["name"], "lat": x["lat"], "lon": x["lon"], "pop": x["pop"]} for x in jload(f"{DATA}/cities.json")]))
    html = html.replace("/*FULLSCREEN*/", open(os.path.join(ROOT, "code", "fullscreen_snippet.html"), encoding="utf-8").read())
    vis = re.sub(r"<script.*?</script>|<style.*?</style>|<!--.*?-->", "", html, flags=re.S)
    vis = re.sub(r"<[^>]+>", " ", vis)
    for bad in ("—", "–", "--", "DSIT", "DCMS", "civil serv"):
        assert bad not in vis, bad
    for scr in re.findall(r"<script>(.*?)</script>", html, flags=re.S):
        for bad in ("—", "–"):
            assert bad not in scr, bad
    open(os.path.join(ROOT, "index.html"), "w", encoding="utf-8").write(html)
    print("index.html", len(html.encode()) // 1024, "KB")


if __name__ == "__main__":
    build()
