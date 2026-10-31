"""README.md and LICENSE, with every number from data/results.json."""
from common import *

R = jload(f"{DATA}/results.json"); L, C, G, U, B = R["land"], R["crops"], R["grid"], R["uk"], R["belts"]
sz = lambda p: f"{os.path.getsize(os.path.join(ROOT, p)) / 1e6:.1f} MB"
doi = f"https://doi.org/{DOI}" if not DOI.startswith("{{") else "https://doi.org/{{DOI}}"
md = f"""# What the world grows

A world map of farmland and crops: the leading crop on every 10 km square of the world's farmland, {R['meta']['n_crops']} crops one by one, crop diversity, and every country's cropland, pasture, biggest crop and speciality since 1961. Built from CROPGRIDS v1.08 (0.05 degree crop grids for about 2020) and FAOSTAT (country statistics from 1961).

Interactive page: {PAGE}
Paper: {doi}
Blog post: {BLOG}

## Headline results

- Farmland: FAOSTAT counts {L['agri_2023'] / 1e6:,.0f} million hectares of agricultural land in {L['year']} ({L['agri_share']:.0f}% of the world's land); {L['past_of_agri']:.0f}% of it is pasture. Cropland covers {L['crop_2023'] / 1e6:,.0f} million hectares, {L['crop_chg_pct']:.0f}% more than in 1961. Total farmland peaked in {L['agri_peak_year']}.
- Where farmland moved: the largest gains in cropland since 1961 were in Brazil (+{L['top_gain_kha'][0]['v'] / 1e3:.1f} million ha), Argentina (+{L['top_gain_kha'][1]['v'] / 1e3:.1f}), Indonesia (+{L['top_gain_kha'][2]['v'] / 1e3:.1f}) and China (+{L['top_gain_kha'][3]['v'] / 1e3:.1f}); the largest loss in the United States ({L['top_loss_kha'][0]['v'] / 1e3:.1f}).
- Crops: wheat, maize, rice and soya beans cover {C['top4_share_2024']:.0f}% of the world's harvested area (2024). Soya beans, oil palm and maize account for {C['soy_palm_maize_gain_share']:.0f}% of the growth in harvested area since 1961; oil palm grew ×{C['by_k']['oilpalm']['x']:.1f}, soya beans ×{C['by_k']['soybean']['x']:.1f}, while rye fell {abs(C['by_k']['rye']['chg_pct']):.0f}% and oats {abs(C['by_k']['oats']['chg_pct']):.0f}%.
- Concentration: half of the harvested area of the {R['meta']['n_crops']} crops lies on {G['half_on_land_pct']:.1f}% of the world's land, nine tenths on {G['ninety_on_land_pct']:.0f}%. Wheat is the leading crop on {G['dom_by_k']['wheat']:.0f}% of farmed 0.1 degree squares, maize on {G['dom_by_k']['maize']:.0f}%.
- Belts: {B['rice_asia']:.0f}% of rice area is in South, Southeast and East Asia; {B['soy_americas']:.0f}% of soya beans in the Americas; {B['palm_idn_mys']:.0f}% of oil palm in Indonesia and Malaysia; {B['cocoa_wafrica']:.0f}% of cocoa in West Africa.
- Specialities (location quotients): Saudi Arabia dates (×{R['spec']['SAU']['lq']:.0f} the world share), Madagascar vanilla, New Zealand kiwi fruit, Bolivia quinoa, Türkiye hazelnuts, UK field beans (×{R['spec']['GBR']['lq']:.0f}).
- UK: wheat, barley and rapeseed fill {U['wbr_share_2224']:.0f}% of harvested area; rapeseed rose from {U['rapeseed']['1961']:,.0f} ha in 1961 to {U['rapeseed']['peak']:,.0f} ha in {U['rapeseed']['peak_year']}.
- How detailed: CROPGRIDS at 0.05 degrees ({G['native_cells']:,} cells with crops), effectively about 10 km, for one year around 2020; country by year since 1961 from FAOSTAT. The {R['meta']['n_crops']} crops cover {R['fao']['share34_2020']:.0f}% of FAOSTAT's world harvested area.

## Files

| File | What it is |
|---|---|
| `index.html` | The interactive page (built by `code/06_build_site.py`; page data embedded, grids and series loaded from `data/page/`). |
| `header.png` | Social card, 1200 x 630. |
| `data/results.json` | Every number used in the page, paper, blog, collage and post. |
| `data/crop_totals.csv` | The {R['meta']['n_crops']} crops: family, FAOSTAT item codes, CROPGRIDS harvested and physical area and quality, FAOSTAT area 1961, 2020, 2024, share of farmed squares where dominant. |
| `data/country_landuse.csv` | Every country, {L['year']}: land, cropland, arable, permanent crops, pasture, forest (1000 ha and % of land), cropland per person, change in cropland since 1961 (or first year). |
| `data/country_crops.csv` | Every country and FAOSTAT crop item, 2022 to 2024 average: harvested area, share of the country, share of the world, location quotient ({sz('data/country_crops.csv')}). |
| `data/world_crops_by_year.csv` | World harvested area and production by crop and year, 1961 to 2024. |
| `data/cropgrids_0p1deg_summary.tif` | GeoTIFF, 0.1 degree: dominant crop, harvested ha, physical ha, diversity x 100 ({sz('data/cropgrids_0p1deg_summary.tif')}). |
| `data/page/` | Page grids (PNG-encoded, documented in `code/05_page_data.py`) and per-country series. |
| `data/site.json`, `data/world.json`, `data/countries_geo.json`, `data/cities.json` | Page data and Natural Earth geometry. |
| `code/` | Scripts, run in order (below), and the page, paper and blog templates. |
| `release/` | Paper PDF and LaTeX source with figures, blog post, figures and meta, Zenodo files. |
| `reddit/` | Collage (`collage.py`, PNG) and post text. |

## Method in brief

- Grid: CROPGRIDS harvested area of {R['meta']['n_crops']} crops summed from 0.05 to 0.1 degree squares; dominant and second crop by harvested area; diversity as the effective number of crops (exp Shannon); farmed squares have at least 1% of their land harvested.
- Concentration: squares ranked by harvested area per hectare of land; share of land holding 50% and 90% of the total.
- Countries: FAOSTAT land use and crops, regional aggregates removed (including 'Sub-Saharan Africa', code 420), China counted once (mainland and Taiwan separately). Crops averaged over 2022 to 2024. Specialities: highest location quotient among items with at least 1% of the country's harvested area and 2,000 ha, for countries with at least 100,000 ha.
- Caveats: area, not production or value; 34 of 173 crops (no vegetables, most fruit, fodder or grass); CROPGRIDS is modelled and has local errors (for example {G['eu_maize']['GBR']:,.0f} ha of maize in the UK where FAOSTAT has none, left out of the UK analysis); FAOSTAT figures are partly estimates.

## How to rerun

Needs Python 3 with numpy, pandas, netCDF4, rasterio, shapely, pyproj, matplotlib, fontTools and Pillow, plus xelatex and pdftotext. Raw inputs are read in place from the paths in `code/common.py`: CROPGRIDS v1.08 NetCDF files (34 crops and `Countries_2018.nc`, figshare article 22491997), the FAOSTAT bulk files `Production_Crops_Livestock_E_All_Data_(Normalized).csv` and `Inputs_LandUse_E_All_Data_(Normalized).csv` (retrieved {RETRIEVED_FAO}), and Natural Earth 1:50m countries and populated places.

```
python3 code/01_fao.py          # parse FAOSTAT
python3 code/02_grids.py        # CROPGRIDS to 0.1 degree grids, country sums
python3 code/03_geo.py          # world outlines and cities
python3 code/04_analysis.py     # results.json, site data, CSVs
python3 code/05_page_data.py    # page PNG grids and GeoTIFF
python3 code/06_build_site.py   # index.html (and checks of facts stated in words)
python3 code/07_figures.py      # header, blog and paper figures
python3 code/08_paper.py        # paper PDF
python3 code/09_readme.py       # README and LICENSE
python3 code/10_release.py      # blog post, Zenodo files
python3 reddit/collage.py       # collage
```

## Sources and licences

- CROPGRIDS v1.08: Tang, F.H.M., Nguyen, T.H., Conchedda, G., Casse, L., Tubiello, F.N. and Maggi, F. (2024) CROPGRIDS: a global geo-referenced dataset of 173 crops. Scientific Data 11, 413. https://doi.org/10.1038/s41597-024-03247-7. Data on figshare (article 22491997). CC BY 4.0.
- FAOSTAT, Crops and livestock products and Land use, FAO (https://www.fao.org/faostat/). CC BY 4.0.
- Natural Earth (public domain).
- Base map tiles on the page: © Esri.

Code is MIT; text, figures and derived data are CC BY 4.0 (see LICENSE).

## Citation

Hotham, T. (2026) What the world grows: farmland and crops on one map, from CROPGRIDS and FAOSTAT. Zenodo. {doi}

Dr Tristan Hotham, Independent researcher. ORCID 0000-0003-4931-9349.

{AI}
"""
for bad in ("—", "–", "--", "DSIT", "DCMS"):
    assert bad not in md.replace("```", "").replace("|---|---|", ""), (bad, md[max(0, md.find(bad) - 80):md.find(bad) + 20])
open(os.path.join(ROOT, "README.md"), "w", encoding="utf-8").write(md)
lic = """MIT License (code)

Copyright (c) 2026 Tristan Hotham

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

Text, figures and derived data (everything outside code/): Creative Commons Attribution 4.0 International (CC BY 4.0), https://creativecommons.org/licenses/by/4.0/
Derived from CROPGRIDS v1.08 (Tang et al. 2024, CC BY 4.0) and FAOSTAT (FAO, CC BY 4.0). Natural Earth data are public domain.
"""
open(os.path.join(ROOT, "LICENSE"), "w", encoding="utf-8").write(lic)
print("README", len(md.split()), "words")
