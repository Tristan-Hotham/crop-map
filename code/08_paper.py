"""Build the paper: fill code/paper_template.tex from data/results.json, add the crop table, compile with xelatex.
Output: release/paper/Hotham_What_the_World_Grows.pdf and .tex (figures release/paper/f_*.png)."""
import re, subprocess, csv
from common import *
import importlib.util
spec_ = importlib.util.spec_from_file_location("b", os.path.join(ROOT, "code", "06_build_site.py")); spec_.loader.exec_module(importlib.util.module_from_spec(spec_))  # runs the shared asserts

R = jload(f"{DATA}/results.json")
OUT = os.path.join(ROOT, "release", "paper"); NAME = "Hotham_What_the_World_Grows"
tex = lambda s: str(s).replace("&", "\\&").replace("%", "\\%").replace("_", "\\_").replace("#", "\\#")
# facts stated only in the paper
assert [x["k"] for x in R["crops"]["fastest"][:5]] == ["yam", "oilpalm", "rapeseed", "cowpea", "soybean"] and R["leaders"]["yam"][0]["iso"] == "NGA"
assert [x["iso"] for x in R["land"]["top_crop_pp"][:3]] == ["KAZ", "AUS", "ARG"]
assert {i: R["spec"][i]["name"] for i in ("USA", "UKR", "THA", "CIV", "NGA")} == {"USA": "Soya beans", "UKR": "Sunflower", "THA": "Rubber", "CIV": "Cocoa beans", "NGA": "Yams"}
assert R["spec"]["FRA"]["name"] == "Flax" and R["grid"]["qual_low"][0]["k"] == "sesame" and [x["k"] for x in R["grid"]["qual_low"][:4]] == ["sesame", "rubber", "oats", "rye"]
assert all(v == 0 for v in R["grid"]["eu_maize_fao"].values())


def pfmt(v, f):
    s = fmt(v, f) if f else tex(v)
    return s.replace("%", "\\%")


rows = list(csv.DictReader(open(f"{DATA}/crop_totals.csv", encoding="utf-8")))
body = "".join(f"{r['name']} & {r['family']} & {int(r['cropgrids_harvested_ha']) / 1e6:.1f} & {int(r['faostat_ha_2024']) / 1e6:.1f} & {float(r['cropgrids_quality']):.2f} & {float(r['dominant_cells_pct']):.1f}\\\\\n" for r in rows)
TC = ("\\begin{table}[tbp]\\centering\\small\\caption{The " + str(len(rows)) + " crops: CROPGRIDS harvested area (about 2020), FAOSTAT harvested area (2024), CROPGRIDS area-weighted quality, and share of farmed 0.1 degree squares where the crop is dominant.}\\label{tab:crops}"
      "\\begin{tabular}{llrrrr}\\toprule Crop & Family & CROPGRIDS Mha & FAOSTAT Mha & Quality & Dominant \\%\\\\\\midrule\n" + body + "\\bottomrule\\end{tabular}\\end{table}")
t = open(os.path.join(ROOT, "code", "paper_template.tex"), encoding="utf-8").read()
t = t.replace("\\url{{{meta.page}}}", "\\url{%s}" % PAGE).replace("\\url{{{meta.repo}}}", "\\url{%s}" % REPO)
t = fill(t, R, pfmt)
t = t.replace("{{TABLE_CROPS}}", TC).replace("{{DOI}}", DOI)
assert not re.search(r"\{\{(?!DOI\}\})", t), re.findall(r"\{\{[^}]*\}\}", t)[:5]
for bad in ("--", "—", "–", "DSIT", "DCMS"):
    assert bad not in t, bad
os.makedirs(OUT, exist_ok=True)
open(os.path.join(OUT, NAME + ".tex"), "w", encoding="utf-8").write(t)
for _ in range(2):
    r = subprocess.run(["xelatex", "-interaction=nonstopmode", NAME + ".tex"], cwd=OUT, capture_output=True, text=True)
log = open(os.path.join(OUT, NAME + ".log"), encoding="utf-8", errors="ignore").read()
print([l for l in log.splitlines() if "Missing character" in l or "undefined" in l.lower() or "Overfull" in l][:12])
for ext in (".aux", ".log", ".out"):
    q = os.path.join(OUT, NAME + ext)
    if os.path.exists(q): os.remove(q)
txt = subprocess.run(["pdftotext", os.path.join(OUT, NAME + ".pdf"), "-"], capture_output=True, text=True).stdout
pages = subprocess.run(["pdfinfo", os.path.join(OUT, NAME + ".pdf")], capture_output=True, text=True).stdout
print("paper", r.returncode, len(txt.split()), "words;", [l for l in pages.splitlines() if l.startswith("Pages")], "dashes:", txt.count("—") + txt.count("–") + txt.count("--"))
