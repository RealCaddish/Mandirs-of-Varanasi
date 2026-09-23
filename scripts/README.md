# Analysis pipeline

Four scripts, run in order by `run_all.py`. Each writes intermediate files to `scripts/cache/` (ignored by git) and the last writes the web data to `data/`.

| Script | Reads | Computes |
|---|---|---|
| `01_point_pattern.py` | `data/raw/temple/temple.json` | Projection to UTM 44N; nearest-neighbour distances; Clark-Evans R; Ripley's K/L; canonical deity groups and families; co-occurrence lift; structure tokens; family x structure chi-square, Cramer's V and standardised residuals; images per shrine; named shrines; mean centres. |
| `02_hex_hotspots.py` | `data/raw/hex_final.geojson`, cache | Reconstructs the QGIS hex lattice (100 m column pitch, 115.47 m row pitch, 66.67 m circumradius); bins the points into it and compares with the original counts; Moran's I; Getis-Ord Gi* with Benjamini-Hochberg FDR; writes `hex_stats.geojson`. |
| `03_river_distance.py` | `data/raw/osm/ganga_water_overpass.json`, `places_of_worship_overpass.json`, cache | Builds the river polygon from OSM ways and multipolygon relations; distance from every shrine to the bank; density by distance band per km2 of land; distances by family and structure; Mann-Whitney tests; Spearman correlation; comparison with OSM places of worship. |
| `04_build_web_data.py` | cache, `data/raw/osm/ghats_landmarks_overpass.json` | Writes `data/mandirs.geojson`, `data/mandirs.csv`, `data/hex.geojson`, `data/ganga.geojson`, `data/landmarks.json`, `data/stats.json`. |

Dependencies: numpy, shapely, pyproj (`pip install -r requirements.txt`). Python 3.10 or newer.

The OSM extracts were fetched from the Overpass API with the `.overpassql` queries stored beside them, for example:

```
curl -H "Accept: */*" --data-urlencode "data@data/raw/osm/ganga_water.overpassql" https://overpass-api.de/api/interpreter -o data/raw/osm/ganga_water_overpass.json
```
