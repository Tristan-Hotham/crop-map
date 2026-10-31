"""Parse the FAOSTAT bulk files (latin1 CSV) into compact tables in WORK:
  qcl.pkl     : country x crop item x year, area harvested (ha) and production (t), primary crop items only
  landuse.pkl : country x land-use item x year, area (1000 ha) and area per capita (ha)
  areas.json  : FAOSTAT area code -> name, M49 code
Aggregate areas (Area Code >= 5000) are dropped, and so is 'China' (code 351, the sum of mainland China, Taiwan,
Hong Kong and Macao) so that China is not counted twice, and 'Sub-Saharan Africa' (420), an aggregate with a low code. Aggregate items (CPC codes starting 'F', such as
'Cereals, primary') are dropped."""
import pandas as pd
from common import *

ENC = "utf-8"   # the brief said latin1, but these bulk files are UTF-8 (checked on the bytes of "Côte d'Ivoire")
ic = pd.read_csv(f"{FAO}/Production_Crops_Livestock_E_ItemCodes.csv", encoding=ENC, dtype=str)
agg_items = set(ic.loc[ic["CPC Code"].fillna("F").str.strip("'").str.startswith("F"), "Item Code"])
keep = []
cols = ["Area Code", "Area", "Area Code (M49)", "Item Code", "Item Code (CPC)", "Item", "Element Code", "Year", "Value", "Flag"]
for ch in pd.read_csv(QCL, encoding=ENC, usecols=cols, dtype={"Item Code (CPC)": str, "Area Code (M49)": str, "Flag": str}, chunksize=2_000_000):
    ch = ch[ch["Element Code"].isin([5312, 5510]) & (ch["Area Code"] < 5000) & ~ch["Area Code"].isin([351, 420])]
    ch = ch[~ch["Item Code (CPC)"].str.strip("'").str.startswith("F")]
    keep.append(ch)
q = pd.concat(keep)
q = q.pivot_table(index=["Area Code", "Item Code", "Year"], columns="Element Code", values="Value", aggfunc="sum").reset_index()
q.columns = ["area", "item", "year", "ha", "t"]
# items that have an area harvested at all (crops, not livestock)
crop_items = set(q.loc[q["ha"].fillna(0) > 0, "item"])
q = q[q["item"].isin(crop_items)]
names = pd.concat(keep)[["Item Code", "Item"]].drop_duplicates().set_index("Item Code")["Item"].to_dict()
anames = pd.concat(keep)[["Area Code", "Area", "Area Code (M49)"]].drop_duplicates("Area Code")
q.to_pickle(f"{WORK}/qcl.pkl")
jsave({str(k): v for k, v in names.items() if k in crop_items}, f"{WORK}/qcl_items.json")
print("qcl", q.shape, "items", len(crop_items), "years", q.year.min(), q.year.max())

keep = []
for ch in pd.read_csv(RL, encoding=ENC, usecols=cols[:4] + ["Item", "Element Code", "Year", "Value", "Flag"], dtype={"Area Code (M49)": str, "Flag": str}, chunksize=2_000_000):
    ch = ch[ch["Element Code"].isin([5110, 7277]) & (ch["Area Code"] < 5000) & ~ch["Area Code"].isin([351, 420])]
    keep.append(ch)
l = pd.concat(keep)
l = l.pivot_table(index=["Area Code", "Item Code", "Year"], columns="Element Code", values="Value", aggfunc="sum").reset_index()
l.columns = ["area", "item", "year", "kha", "pc"]
l.to_pickle(f"{WORK}/landuse.pkl")
an2 = pd.concat(keep)[["Area Code", "Area", "Area Code (M49)"]].drop_duplicates("Area Code")
A = {}
for d in (anames, an2):
    for _, r in d.iterrows():
        A[str(int(r["Area Code"]))] = {"name": r["Area"], "m49": str(r["Area Code (M49)"]).strip("'")}
jsave(A, f"{WORK}/areas.json")
print("landuse", l.shape, "areas", len(A))
