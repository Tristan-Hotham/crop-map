# What the world grows

A world map of farmland and crops: the leading crop on every 10 km square of the world's farmland, 34 crops one by one, crop diversity, and every country's cropland, pasture, biggest crop and speciality since 1961. Built from CROPGRIDS v1.08 (0.05 degree crop grids for about 2020) and FAOSTAT (country statistics from 1961).

Interactive page: https://maps.tristanhotham.com/crop-map/
Paper: https://doi.org/10.5281/zenodo.23842987
Blog post: https://blog.tristanhotham.com/2026/10/31/crop-map/

## Headline results

- Farmland: FAOSTAT counts 4,682 million hectares of agricultural land in 2023 (36% of the world's land); 66% of it is pasture. Cropland covers 1,583 million hectares, 18% more than in 1961. Total farmland peaked in 2000.
- Where farmland moved: the largest gains in cropland since 1961 were in Brazil (+31.5 million ha), Argentina (+28.4), Indonesia (+24.6) and China (+23.8); the largest loss in the United States (-25.9).
- Crops: wheat, maize, rice and soya beans cover 50% of the world's harvested area (2024). Soya beans, oil palm and maize account for 48% of the growth in harvested area since 1961; oil palm grew ×8.0, soya beans ×6.0, while rye fell 88% and oats 78%.
- Concentration: half of the harvested area of the 34 crops lies on 6.4% of the world's land, nine tenths on 21%. Wheat is the leading crop on 26% of farmed 0.1 degree squares, maize on 23%.
- Belts: 85% of rice area is in South, Southeast and East Asia; 74% of soya beans in the Americas; 67% of oil palm in Indonesia and Malaysia; 66% of cocoa in West Africa.
- Specialities (location quotients): Saudi Arabia dates (×374 the world share), Madagascar vanilla, New Zealand kiwi fruit, Bolivia quinoa, Türkiye hazelnuts, UK field beans (×24).
- UK: wheat, barley and rapeseed fill 76% of harvested area; rapeseed rose from 600 ha in 1961 to 755,717 ha in 2012.
- How detailed: CROPGRIDS at 0.05 degrees (2,851,739 cells with crops), effectively about 10 km, for one year around 2020; country by year since 1961 from FAOSTAT. The 34 crops cover 87% of FAOSTAT's world harvested area.

## Files

| File | What it is |
|---|---|
| `index.html` | The interactive page (built by `code/06_build_site.py`; page data embedded, grids and series loaded from `data/page/`). |
| `header.png` | Social card, 1200 x 630. |
| `data/results.json` | Every number used in the page, paper, blog, collage and post. |
| `data/crop_totals.csv` | The 34 crops: family, FAOSTAT item codes, CROPGRIDS harvested and physical area and quality, FAOSTAT area 1961, 2020, 2024, share of farmed squares where dominant. |
| `data/country_landuse.csv` | Every country, 2023: land, cropland, arable, permanent crops, pasture, forest (1000 ha and % of land), cropland per person, change in cropland since 1961 (or first year). |
| `data/country_crops.csv` | Every country and FAOSTAT crop item, 2022 to 2024 average: harvested area, share of the country, share of the world, location quotient (0.5 MB). |
| `data/world_crops_by_year.csv` | World harvested area and production by crop and year, 1961 to 2024. |
| `data/cropgrids_0p1deg_summary.tif` | GeoTIFF, 0.1 degree: dominant crop, harvested ha, physical ha, diversity x 100 (4.4 MB). |
| `data/page/` | Page grids (PNG-encoded, documented in `code/05_page_data.py`) and per-country series. |
| `data/site.json`, `data/world.json`, `data/countries_geo.json`, `data/cities.json` | Page data and Natural Earth geometry. |
| `code/` | Scripts, run in order (below), and the page, paper and blog templates. |
| `release/` | Paper PDF and LaTeX source with figures, blog post, figures and meta, Zenodo files. |
| `reddit/` | Collage (`collage.py`, PNG) and post text. |

## Method in brief

- Grid: CROPGRIDS harvested area of 34 crops summed from 0.05 to 0.1 degree squares; dominant and second crop by harvested area; diversity as the effective number of crops (exp Shannon); farmed squares have at least 1% of their land harvested.
- Concentration: squares ranked by harvested area per hectare of land; share of land holding 50% and 90% of the total.
- Countries: FAOSTAT land use and crops, regional aggregates removed (including 'Sub-Saharan Africa', code 420), China counted once (mainland and Taiwan separately). Crops averaged over 2022 to 2024. Specialities: highest location quotient among items with at least 1% of the country's harvested area and 2,000 ha, for countries with at least 100,000 ha.
- Caveats: area, not production or value; 34 of 173 crops (no vegetables, most fruit, fodder or grass); CROPGRIDS is modelled and has local errors (for example 830,562 ha of maize in the UK where FAOSTAT has none, left out of the UK analysis); FAOSTAT figures are partly estimates.

## How to rerun

Needs Python 3 with numpy, pandas, netCDF4, rasterio, shapely, pyproj, matplotlib, fontTools and Pillow, plus xelatex and pdftotext. Raw inputs are read in place from the paths in `code/common.py`: CROPGRIDS v1.08 NetCDF files (34 crops and `Countries_2018.nc`, figshare article 22491997), the FAOSTAT bulk files `Production_Crops_Livestock_E_All_Data_(Normalized).csv` and `Inputs_LandUse_E_All_Data_(Normalized).csv` (retrieved in 2026), and Natural Earth 1:50m countries and populated places.

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

Hotham, T. (2026) What the world grows: farmland and crops on one map, from CROPGRIDS and FAOSTAT. Zenodo. https://doi.org/10.5281/zenodo.23842987

Dr Tristan Hotham, Independent researcher. ORCID 0000-0003-4931-9349.

I wrote the text, with drafting and editing assistance from Claude (Anthropic), which also helped prepare the analysis code. I reviewed and checked all text and results.
