## Title

[OC] What the world grows: the leading crop on every 10 km square of farmland. Half the harvested area of 34 major crops lies on just 6.4% of the world's land

## Body

I mapped CROPGRIDS, a 2024 open dataset of crop areas on a 5 km grid (about 2020), summed to 10 km squares and coloured by the crop with the largest harvested area, using its 34 biggest crops (87% of the world's harvested area). Wheat, maize, rice and soya beans cover 50% of all harvested land (FAOSTAT 2024), soya bean area has grown ×6 since 1961 and oil palm ×8, and 66% of the world's farmland is pasture rather than crops. 85% of rice is in South, Southeast and East Asia, 66% of cocoa in West Africa. Caveats: this is harvested area, not production; CROPGRIDS is modelled, so read regions rather than single squares (it puts maize in western Britain, for instance, where FAOSTAT records none). Interactive map with all 34 crops, crop diversity and every country's farmland since 1961: https://maps.tristanhotham.com/crop-map/

## Source comment

Source: CROPGRIDS v1.08, Tang, Nguyen, Conchedda, Casse, Tubiello and Maggi (2024), Scientific Data 11:413, https://doi.org/10.1038/s41597-024-03247-7 (CC BY 4.0); FAOSTAT Crops and livestock products and Land use bulk downloads (FAO, CC BY 4.0); Natural Earth outlines (public domain).

Tools: Python (numpy, netCDF4, pandas, pyproj, matplotlib); Leaflet for the interactive map.

Interactive version: https://maps.tristanhotham.com/crop-map/
Paper: https://doi.org/10.5281/zenodo.23842987
Blog post: https://blog.tristanhotham.com/2026/10/31/crop-map/
