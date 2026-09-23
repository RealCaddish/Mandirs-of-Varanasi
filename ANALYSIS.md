# Mandirs of Varanasi: what the survey data says

Analysis of the 2012 and 2015 field survey of street shrines ("tiny temples") in Varanasi by Christian Haskett and Nathaniel Deaton. All figures below were computed from the files in `data/` with the scripts in `scripts/` on 23 September 2026. The interactive version, with charts and a map, is `index.html`.

## Summary

- **The shrines are clustered at every scale.** Half of all shrines have another shrine within 11 m; a random layout of the same density would give 86 m. The Clark–Evans ratio is 0.34 (z = −60). Ripley's L function keeps rising to about 1.5 km, the width of the old city, so clustering operates within lanes, within neighbourhoods and along the river at once.
- **One hot spot holds the old city.** Getis–Ord Gi* with a false-discovery-rate correction marks 247 hexagons (2.9 km², roughly 4% of the surveyed ground) as significant hot spots. They contain 67% of the shrines, and 229 of them form a single contiguous band 4.3 km long behind the ghats from Assi to Trilochan. There are no significant cold spots.
- **The Ganga's pull is measurable and steep.** The median shrine stands 172 m from the river bank and 93% stand within 500 m. Density falls from 124 shrines per km² within 100 m of the bank to 35 at 250–500 m and 13 at 500–750 m. Distance from the river also predicts sparseness (Spearman's ρ = 0.37 with nearest-neighbour distance).
- **It is Shiva's city.** 67% of shrines house a Shaiva deity and 49% house Shiva alone. Hanuman is in 23%, and 43% of his shrines hold no other deity. Ganesh 12%, goddesses 11%, Vaishnava deities 6%, folk figures 3%.
- **Deities keep households.** Shiva-Parvati and the Shiva family co-occur 2.4× more than chance; Hanuman and Rama 2.1×. Hanuman and Shiva-Parvati co-occur only 0.31× as often as chance.
- **Form follows occupant, modestly.** Deity family and shrine structure are not independent (χ² = 126 on 30 df, p < 10⁻¹³) but the effect is weak (Cramér's V = 0.12). Ganesh is over-represented in wall niches (+4.5 standardised residual), Hanuman in tree-temples (+2.7), unidentified deities at trees (+6.4), Vaishnava deities in temple complexes (+2.0).
- **Two landscapes.** Inside the hot spots, 45% of shrines are wall niches and 5% are tree-tied; outside, 13% and 25%. Hanuman is present in 17% of shrines inside the core and 37% outside. The riverside core is a Shaiva landscape carved into walls; the periphery is Hanuman, trees and free-standing boxes.
- **Images and names are unevenly held.** 5,484 images were counted (median 2 per shrine); the richest 10% of shrines hold 35% of them. Only 136 shrines (6%) carry a recorded name; 63 of those are Shiva names of the *-eshwar Mahadev* pattern.

## The data

| File | Records | What it is |
|---|---|---|
| `data/raw/temple/temple.shp` (+ `.json`) | 2,296 points (DBF header says 2,299) | Shrines with GPS position and attributes: `deity`, `deity_othe` (identical to `deity` in every row), `temple_nam`, `deities_pr` (images present), `temple_str` (structure). WGS84. |
| `data/raw/hex_final.geojson` | 990 hexagons, sum of `deity_count` = 3,313 | Flat-topped hexagon grid built in QGIS (UTM 44N, column pitch 100 m, circumradius 66.67 m, cell area 1.155 ha) with a count of survey records per cell. Despite the field name, the count is shrine records, not deities. Zero-count cells were dropped. |
| `data/raw/osm/*` | | OpenStreetMap extracts (Overpass, 22 Sept 2026): Ganga water polygons, places of worship, ghat and landmark names. ODbL. |

### Three totals

The project text cites 2,850 (README) and 3,347 (article) shrines. The hexagon grid sums to 3,313 and the point file has 2,296. The grid was evidently built from a master table of about 3,347 records of which 34 fell outside it; the published shapefile is a subset with full attributes. Binning the 2,296 points into a reconstruction of the same grid gives counts that correlate 0.91 with the original, but 422 original cells have no attributed point at all, and the missing mass is centred about 800 m south-west of the point centroid. The individual-shrine layer therefore under-represents the inland periphery. The map's density and hot-spot views use the original grid counts; everything about deities, structures and distances uses the 2,296 attributed records.

### Cleaning

- Deity strings are comma lists in inconsistent order (`Siva,Siva-Parvati` 383 times, `Siva-Parvati,Siva` 21 times). They were split into 17 tokens and canonicalised: `Siva → Shiva`; `RAMA`, `Rama-Sita`, `Rama family → Rama`; `__ Maa`, `Shaayari maa`, `caura maa → Local Maa` (the `__` is the surveyors' placeholder for a name); `__ Bir Baabaa → Bir Baba`; `gramadevata → Village deity`. Groups were then assigned to seven families: Shaiva, Hanuman, Ganesh, Goddess, Vaishnava, Folk, Other. 78% of shrines belong to one family.
- Structure strings (48 distinct) reduce to six tokens; 40 shrines have none. Where a shrine has several, the first listed is used as its primary structure in cross-tabs.
- 66 shrines share 28 exact coordinates (one location has seven records), typically several shrines in one complex logged from one GPS fix.
- 60 shrines fall inside the OSM river polygon (up to 444 m); their river distance is set to 0. The water line in OSM and on the survey days differ, and GPS is poor at the ghats.

## Methods and results

### Point pattern

Coordinates were projected to UTM 44N. The study area is the convex hull of the points (67.3 km², of which 59.6 km² is land).

| Statistic | Value | Reading |
|---|---|---|
| Mean nearest-neighbour distance | 29.5 m (median 11.3 m) | 47% of shrines have a neighbour within 10 m, 86% within 50 m, 99% within 200 m |
| Expected under complete spatial randomness | 85.6 m | at 34 shrines per km² |
| Clark–Evans R | 0.344, z = −60.1 | strongly clustered |
| Ripley's L(r) − r | 272 m at r = 50 m, rising to 1,681 m at r = 1,500 m, then falling | clustering at all scales, peaking at the scale of the old city. No edge correction. |

### Hexagon grid

The grid was reconstructed from the `left`/`bottom` fields (column pitch 100 m, row pitch 115.47 m, alternate columns offset by half a row), zero cells were restored within a two-cell buffer of the occupied cells' convex hull (7,247 cells), and each cell's six edge neighbours were used as its weights.

| Statistic | Value |
|---|---|
| Occupied cells | 990 (491 with one shrine; max 87 at Panchganga Ghat, 25.31504 N 83.01826 E) |
| Variance-to-mean ratio of counts | 9.2 (random ≈ 1) |
| Moran's I | 0.443, E[I] = −0.0001, z = 66.4 |
| Gi* hot cells (Benjamini–Hochberg FDR 5%) | 247, of which 238 at 99.9% confidence; 0 cold cells |
| Shrines inside hot cells | 1,544 of 2,296 (67%) on 2.85 km² |
| Hot-spot components | 5: the riverside band (229 cells, 1,841 survey records, 4.3 km long, centred near Scindia Ghat), Varanasi City/Adampur (6 cells, 23 records, 1.44 km from the river), Assi Ghat (5 cells, 28), Trilochan (4 cells, 23), and a 3-cell cluster near Kal Bhairav |

Inside the hot cells 47% of attributed shrines are wall niches and 69% Shaiva; the inland north cluster and the Assi cluster have no wall niches at all.

### Distance to the Ganga

Distances are to the boundary of the OSM `natural=water` polygons for the river (checked: Dashashwamedh, Panchganga and Assi ghats lie 2–10 m from the polygon edge).

| Band from bank | Shrines | Land in band (km²) | Shrines per km² |
|---|---|---|---|
| 0–100 m | 808 | 6.54 | 123.5 |
| 100–250 m | 623 | 13.33 | 46.7 |
| 250–500 m | 709 | 20.43 | 34.7 |
| 500–750 m | 140 | 11.08 | 12.6 |
| 750–1,000 m | 15 | 5.37 | 2.8 |
| 1,000–1,500 m | 1 | 2.39 | 0.4 |

Median distance by family: Shaiva 153 m, Ganesh 192 m, Goddess 220 m, Vaishnava 231 m, Folk 238 m, Hanuman 249 m, Other 256 m. By structure: wall niche 109 m, temple complex 153 m, free-standing 207 m, tree 231 m, tree-temple 271 m, built-around 335 m.

Mann–Whitney U: Hanuman-only vs Shiva-only shrines z = 4.3, P(Hanuman farther) = 0.59; tree-tied vs not z = 7.6, P = 0.62; wall vs not z = −13.0, P(wall farther) = 0.34. Spearman's ρ between river distance and nearest-neighbour distance: 0.37.

### Deities

Presence (share of 2,296 shrines): Shiva 62%, Shiva-Parvati 32%, Hanuman 23%, Ganesh 12%, Shiva family 12%, Other 8%, Devi 7%, Local Maa 5%, Rama 4%, Bir Baba 3%, Sitala Maa 3%, Krishna 2%. Families: Shaiva 67%, Hanuman 23%, Ganesh 12%, Goddess 11%, Other 8%, Vaishnava 6%, Folk 3%. Most common combinations: Shaiva only 1,120; Hanuman only 234; Goddess only 164; Hanuman + Shaiva 136; Ganesh only 108.

Lift (observed pairs ÷ expected under independence), pairs with the most support: Devi & Local Maa 10.5 (a recording convention: a named goddess is logged as both); Shiva-Parvati & Shiva family 2.38; Hanuman & Rama 2.13; Ganesh & Rama 1.98; Shiva & Shiva-Parvati 1.44; Hanuman & Ganesh 1.25. Strongest avoidance: Shiva-Parvati & Other 0.17; Shiva & Sitala Maa 0.23; Shiva & Local Maa 0.24; Shiva-Parvati & Hanuman 0.31; Shiva & Devi 0.41.

### Structures

Presence: free-standing 41%, built into a wall 36%, temple complex 10%, tree-temple 10%, tree 9%, built-around 4%; 17% have some tree association. Chi-square test of family × primary structure on the 1,767 single-family shrines with a recorded structure: χ² = 126.1, 30 df, p = 9 × 10⁻¹⁴, Cramér's V = 0.119. Standardised residuals beyond ±2: Ganesh in wall niches +4.5 and free-standing −3.5; Hanuman in tree-temples +2.7 and complexes −2.2; Other at trees +6.4, tree-temples +2.4 and wall niches −2.2; Vaishnava in complexes +2.0.

### Core versus periphery

Shares inside hot cells versus outside: wall niche 45% vs 13%; free-standing 34% vs 55%; temple complex 10% vs 4%; tree-temple 2% vs 14%; tree 3% vs 11%. Shaiva 69% vs 63%; Hanuman 17% vs 37%; Ganesh 11% vs 15%; Goddess 10% vs 13%; Folk 2% vs 6%; Vaishnava 5% vs 7%; Other 3% vs 18%. Median images: 1 inside, 2 outside.

### Images and names

5,484 images across 2,296 shrines; median 2, mean 2.4, 211 shrines with none, maximum 50; the top 10% of shrines hold 35% of images. By family (median, share with 5+): Vaishnava 4 (47%), Folk 3 (37%), Ganesh 3 (30%), Hanuman 2 (23%), Shaiva 2 (17%), Other 2 (20%), Goddess 1 (16%). Wall niches hold the fewest (median 1). 136 shrines are named; 63 names are Shiva names; 79 of the named shrines are free-standing and 18 are in complexes.

### Against OpenStreetMap

OSM lists 143 places of worship in the survey bounding box, 94 of them Hindu and 74 inside the survey hull; the survey has 2,296. 108 surveyed shrines lie within 50 m of an OSM temple and 25 of the 94 OSM temples have a surveyed shrine within 50 m. The two datasets record different things: the monumental and the everyday.

## What was changed in the project

- One page replaces three (`index.html`, `enhanced_index.html`, `dashboard.html`) that disagreed on totals, duplicated code, and in one case ran two competing map-loading routines that drew two legends. The dashboard's "sample" deity chart with invented numbers is gone.
- The map now offers three views (density, Gi* hot spots, individual shrines with deity and structure highlighting), a river outline, ghat and landmark labels, a light basemap that no longer needs an API key (the previous Thunderforest key was committed in three files), a satellite basemap, and story cards that fly to notable places.
- Every chart is drawn from `data/stats.json`, has a hover tooltip, keyboard focus, and a table view; colour ramps were validated for lightness monotonicity and contrast.
- Photos were resized and recompressed from 13.3 MB to 1.8 MB.
- A 6 MB Python installer, an unused font, and the jQuery, Chart.js, D3 and simple-statistics dependencies were removed. Leaflet was updated from 1.7.1 to 1.9.4 and loaded with integrity hashes.
- Raw data moved to `data/raw/`; derived web data lives in `data/`; the analysis is reproducible with `python scripts/run_all.py`.

## Suggested next steps

1. **Recover the missing ~1,050 records.** The hex grid proves they exist. If the master table can be found, rebuilding `mandirs.geojson` from it would make the point layer match the grid and fix the periphery under-count.
2. **Split by survey year.** 2012 vs 2015 is not recorded in the shapefile. If it can be recovered, change over time in the same lanes would be a strong finding.
3. **Add neighbourhood (mohalla) boundaries** and compute shrines per neighbourhood and per resident. Ward boundaries from the Varanasi Nagar Nigam or OSM `admin_level=10` would allow a choropleth normalised by population and a test of the observation about Muslim neighbourhoods.
4. **Network distances.** Distance along the lanes to the nearest ghat, rather than straight-line distance to the water, would better model how people reach shrines. OSMnx makes this a short script.
5. **Kernel density with edge correction**, and Ripley's K with Ripley's edge correction, would make the scale statistics publishable.
6. **Photographs and interviews.** Linking the survey photographs to points (the `See photo` name suggests they exist) would make the individual-shrine view the richest part of the site.
7. **Co-location with other features.** Wells, pipal and neem trees, crossroads and temple-complex boundaries from OSM would let the "junctures of shared space" hypothesis be tested directly with a co-location quotient.

## Reproducibility

```
pip install -r scripts/requirements.txt
python scripts/run_all.py
```

The scripts read `data/raw/` and rewrite `data/*.geojson`, `data/mandirs.csv` and `data/stats.json`. Intermediate files go to `scripts/cache/` (ignored by git). The OSM extracts in `data/raw/osm/` were fetched with the Overpass queries stored beside them.
