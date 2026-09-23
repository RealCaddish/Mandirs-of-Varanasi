"""Write the web data files into the repo's data/ folder:
  data/mandirs.geojson  - 2,296 shrines, cleaned attributes, river distance, hot-spot class
  data/hex.geojson      - hex grid with survey count (n), point count (np), Gi* z (gz), hot class
  data/ganga.geojson    - river polygon (OSM)
  data/landmarks.json   - ghats and landmarks for labels
  data/stats.json       - every precomputed statistic the page displays
  data/mandirs.csv      - flat download
"""
import json, os, csv, math, collections
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
S = os.path.join(ROOT, 'scripts', 'cache'); os.makedirs(S, exist_ok=True)
OUT = os.path.join(ROOT, 'data'); os.makedirs(OUT, exist_ok=True)
rows = json.load(open(os.path.join(S, 'rows.json')))
dd = np.load(os.path.join(S, 'river_dist.npy'))
ps = json.load(open(os.path.join(S, 'pointstats.json')))
hs = json.load(open(os.path.join(S, 'hexstats.json')))
rs = json.load(open(os.path.join(S, 'river_stats.json')))
hexg = json.load(open(os.path.join(S, 'hex_stats.geojson')))

FAM = {'Shaiva': 'S', 'Hanuman': 'H', 'Ganesh': 'G', 'Goddess': 'D', 'Vaishnava': 'V', 'Folk': 'F', 'Other': 'O'}
STR = {'Free-standing': 'fs', 'Built into a wall': 'w', 'Temple complex': 'c', 'Tree-temple': 'tt', 'Tree': 't', 'Built-around': 'ba'}
# hot-spot class per point: locate the hex containing each point (polygon test on hex.geojson)
from shapely.geometry import shape, Point
from shapely.strtree import STRtree
hpolys = [shape(f['geometry']) for f in hexg['features']]
tree = STRtree(hpolys)
def hot_of(lon, lat):
    p = Point(lon, lat)
    for i in tree.query(p):
        if hpolys[i].contains(p): return hexg['features'][i]['properties']['hot']
    return 0
feats = []; csvrows = []
for i, r in enumerate(rows):
    hot = hot_of(r['lon'], r['lat'])
    props = {'f': ''.join(FAM[a] for a in r['f']), 'c': r['c'], 's': [STR.get(a, a) for a in r['s']], 'n': r['n'], 'r': int(round(dd[i])), 'h': hot}
    if r['name'] and r['name'].lower() not in ('none', 'see photo'): props['nm'] = r['name']
    feats.append({'type': 'Feature', 'properties': props, 'geometry': {'type': 'Point', 'coordinates': [round(r['lon'], 6), round(r['lat'], 6)]}})
    csvrows.append({'id': i + 1, 'latitude': round(r['lat'], 6), 'longitude': round(r['lon'], 6), 'deities_recorded': ','.join(r['t']), 'deity_groups': ','.join(r['c']),
                    'families': ','.join(r['f']), 'structure': ','.join(r['s']), 'images_present': r['n'], 'temple_name': r['name'] if r['name'].lower() not in ('none',) else '',
                    'distance_to_ganga_m': int(round(dd[i])), 'hotspot_class': hot})
json.dump({'type': 'FeatureCollection', 'features': feats}, open(os.path.join(OUT, 'mandirs.geojson'), 'w', encoding='utf-8'), separators=(',', ':'), ensure_ascii=False)
with open(os.path.join(OUT, 'mandirs.csv'), 'w', newline='', encoding='utf-8') as fh:
    w = csv.DictWriter(fh, fieldnames=list(csvrows[0].keys())); w.writeheader(); w.writerows(csvrows)
json.dump(hexg, open(os.path.join(OUT, 'hex.geojson'), 'w'), separators=(',', ':'))
import shutil
shutil.copy(os.path.join(S, 'ganga.geojson'), os.path.join(OUT, 'ganga.geojson'))

# landmarks
gh = json.load(open(os.path.join(ROOT, 'data', 'raw', 'osm', 'ghats_landmarks_overpass.json'), encoding='utf-8'))
pw = json.load(open(os.path.join(ROOT, 'data', 'raw', 'osm', 'places_of_worship_overpass.json'), encoding='utf-8'))
def find(els, needle, key='name:en'):
    for e in els:
        t = e.get('tags', {}); nm = (t.get('name:en') or t.get('name') or '')
        if needle.lower() in nm.lower():
            lo, la = (e['lon'], e['lat']) if e['type'] == 'node' else (e['center']['lon'], e['center']['lat'])
            return [round(la, 5), round(lo, 5), nm]
    return None
want_ghats = ['Assi Ghat', 'Harishchandra Ghat', 'Kedar Ghat', 'Dashashvamedh Ghat', 'Manikarnika', 'Scindia Ghat', 'Panchganga Ghat', 'Trilochan Ghat', 'Raj Ghat', 'Adi Keshava Ghat']
lm = []
for g in want_ghats:
    r = find(gh['elements'], g)
    if r: lm.append({'lat': r[0], 'lon': r[1], 'name': r[2].replace('Manikarnika Ghat(KOSTRI)', 'Manikarnika Ghat').replace('Dashashvamedh', 'Dashashwamedh'), 'kind': 'ghat'})
for nm, kind in [('Vishwanath', 'temple'), ('Sankat Mochan', 'temple'), ('Durga Temple', 'temple'), ('Kal Bhairav', 'temple'), ('Bharat Mata', 'temple')]:
    r = find(pw['elements'], nm)
    if r: lm.append({'lat': r[0], 'lon': r[1], 'name': r[2], 'kind': kind})
for nm, kind in [('Banaras Hindu University', 'place'), ('Varanasi Junction', 'place'), ('Varanasi City', 'place')]:
    r = find(gh['elements'], nm)
    if r: lm.append({'lat': r[0], 'lon': r[1], 'name': r[2], 'kind': kind})
json.dump(lm, open(os.path.join(OUT, 'landmarks.json'), 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
print('landmarks:'); [print('  ', l) for l in lm]

# ---- stats.json
n = len(rows)
img = np.array([r['n'] for r in rows])
famc = collections.Counter(f for r in rows for f in r['f'])
deityc = collections.Counter(a for r in rows for a in r['c'])
combos = collections.Counter('+'.join(r['f']) for r in rows)
stc = collections.Counter(a for r in rows for a in set(r['s']))
prim = collections.Counter((r['s'][0] if r['s'] else 'Unrecorded') for r in rows)
hexcounts = collections.Counter(f['properties']['n'] for f in hexg['features'] if f['properties']['n'] > 0)
# nearest neighbour distribution (ECDF points)
xy = np.load(os.path.join(S, 'xy.npy'))
D = np.sqrt(((xy[:, None, :] - xy[None, :, :]) ** 2).sum(-1)); np.fill_diagonal(D, np.inf); nn = D.min(1)
nn_ecdf = [{'r': r, 'share': round(float((nn <= r).mean()), 4)} for r in [0, 2, 5, 10, 15, 20, 30, 40, 50, 75, 100, 150, 200, 300, 500]]
# co-occurrence lift among deity groups with >=50 presences
cats = [k for k, v in deityc.most_common() if v >= 50]
lift = []
for i, a in enumerate(cats):
    for b in cats[i + 1:]:
        ab = sum(1 for r in rows if a in r['c'] and b in r['c']); exp = deityc[a] * deityc[b] / n
        lift.append({'a': a, 'b': b, 'n': ab, 'expected': round(exp, 1), 'lift': round(ab / exp, 2)})
# images by family / structure
img_fam = {f: {'n': int(sum(1 for r in rows if f in r['f'])), 'median': float(np.median([r['n'] for r in rows if f in r['f']])), 'mean': round(float(np.mean([r['n'] for r in rows if f in r['f']])), 2), 'share5': round(float(np.mean([r['n'] >= 5 for r in rows if f in r['f']])), 3)} for f in FAM}
img_hist = collections.Counter(min(int(v), 10) for v in img)
# family share inside hot spots vs outside
hotpt = np.array([f['properties']['h'] > 0 for f in feats])
fam_hot = {f: {'hot': round(float(np.mean([f in r['f'] for r, h in zip(rows, hotpt) if h])), 3), 'out': round(float(np.mean([f in r['f'] for r, h in zip(rows, hotpt) if not h])), 3)} for f in FAM}
str_hot = {s: {'hot': round(float(np.mean([(r['s'][0] if r['s'] else '') == s for r, h in zip(rows, hotpt) if h])), 3), 'out': round(float(np.mean([(r['s'][0] if r['s'] else '') == s for r, h in zip(rows, hotpt) if not h])), 3)} for s in STR}
named = [r for r in rows if r['name'] and r['name'].lower() not in ('none', 'see photo')]
shivakeys = ('mahadev', 'shiv', 'eshwar', 'eshvar', 'esvar', 'ishwar', 'nath', 'mahaadev')
stats = {
    'n_points': n, 'n_survey_hex_total': hs['orig_sum'], 'n_hex_cells': len([f for f in hexg['features'] if f['properties']['n'] > 0]), 'hex_area_km2': hs['hex_area_km2'], 'hex_radius_m': 66.7,
    'hull_km2': round(ps['hull_km2'], 2), 'land_km2': rs['land_km2'], 'density_per_km2': round(n / rs['land_km2'], 1),
    'nn_mean': round(ps['nn_mean'], 1), 'nn_median': round(ps['nn_median'], 1), 'nn_ecdf': nn_ecdf, 'clark_evans_R': round(ps['clark_evans_R'], 3), 'clark_evans_z': round(ps['clark_evans_z'], 1),
    'ripley': [{'r': p['r'], 'L_minus_r': round(p['L_minus_r'], 1)} for p in ps['ripley']],
    'moran_I': round(hs['moran_I'], 3), 'moran_z': round(hs['moran_z'], 1), 'gi_hot_cells': hs['hot_cells'], 'gi_hot_km2': round(hs['hot_cells'] * hs['hex_area_km2'], 2), 'points_in_hot': hs['points_in_hot'], 'share_in_hot': round(hs['points_in_hot'] / n, 3),
    'hex_max': max(hexcounts), 'hex_median': 2, 'hex_mean': round(hs['orig_sum'] / len([f for f in hexg['features'] if f['properties']['n'] > 0]), 2), 'hex_hist': [{'n': k, 'cells': v} for k, v in sorted(hexcounts.items())],
    'dispersion_index': 9.17, 'corr_survey_vs_points': round(hs['corr_orig_pts'], 3),
    'river': rs,
    'families': [{'key': FAM[f], 'name': f, 'n': famc[f], 'share': round(famc[f] / n, 3)} for f in FAM],
    'deities': [{'name': k, 'n': v, 'share': round(v / n, 3)} for k, v in deityc.most_common()],
    'combos': [{'combo': k, 'n': v} for k, v in combos.most_common(12)], 'single_family_share': round(sum(1 for r in rows if len(r['f']) == 1) / n, 3),
    'structures': [{'key': STR[s], 'name': s, 'n': stc[s], 'share': round(stc[s] / n, 3)} for s in STR], 'structure_primary': dict(prim), 'tree_any': int(sum(1 for r in rows if any(a in ('Tree', 'Tree-temple') for a in r['s']))),
    'chi2': round(ps['chi2'], 1), 'chi2_dof': ps['chi2_dof'], 'chi2_p': ps['chi2_p'], 'cramers_v': round(ps['cramers_v'], 3),
    'crosstab': {'fams': ps['crosstab_fams'], 'structs': ps['crosstab_structs'], 'counts': ps['crosstab_M'], 'resid': [[round(v, 2) for v in row] for row in ps['crosstab_resid']]},
    'lift': lift,
    'images_total': int(img.sum()), 'images_median': float(np.median(img)), 'images_mean': round(float(img.mean()), 2), 'images_zero': int((img == 0).sum()), 'images_top10_share': round(float(np.sort(img)[::-1][:n // 10].sum() / img.sum()), 3), 'images_max': int(img.max()),
    'images_hist': [{'k': k, 'n': img_hist[k]} for k in range(0, 11)], 'images_by_family': img_fam,
    'fam_hot': fam_hot, 'str_hot': str_hot,
    'named_n': len(named), 'named_shiva_n': sum(1 for r in named if any(k in r['name'].lower() for k in shivakeys)),
    'dup_coords_features': 66, 'dup_coord_sites': 28,
    'centres': ps['centres'],
}
json.dump(stats, open(os.path.join(OUT, 'stats.json'), 'w'), indent=1)
for f in os.listdir(OUT):
    p = os.path.join(OUT, f)
    if os.path.isfile(p): print(f'{f:20s} {os.path.getsize(p) / 1024:8.1f} KB')
