"""Build the Ganga water polygon from OSM (closed ways + multipolygon relations), verify it
covers the ghats, then compute distance from every mandir to the nearest bank and the
density gradient by distance band. Overwrites river_stats.json / river_dist.npy / ganga.geojson."""
import json, math, os
import numpy as np
from pyproj import Transformer
from shapely.geometry import Polygon, LineString, Point, MultiPoint
from shapely.ops import unary_union, polygonize, linemerge

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
S = os.path.join(ROOT, 'scripts', 'cache'); os.makedirs(S, exist_ok=True)
tr = Transformer.from_crs('EPSG:4326', 'EPSG:32644', always_xy=True)
back = Transformer.from_crs('EPSG:32644', 'EPSG:4326', always_xy=True)
d = json.load(open(os.path.join(ROOT, 'data', 'raw', 'osm', 'ganga_water_overpass.json'), encoding='utf-8'))
els = d['elements']
polys = []; outer_lines = []
for e in els:
    t = e.get('tags', {})
    if e['type'] == 'way' and e.get('geometry'):
        g = e['geometry']
        if t.get('waterway') == 'river' and t.get('natural') != 'water':
            continue  # centreline, skip
        pts = [tr.transform(p['lon'], p['lat']) for p in g]
        if g[0] == g[-1] and len(pts) > 3: polys.append(Polygon(pts))
        else: outer_lines.append(LineString(pts))
    elif e['type'] == 'relation':
        for m in e.get('members', []):
            if m.get('type') == 'way' and m.get('geometry') and m.get('role') in ('outer', ''):
                pts = [tr.transform(p['lon'], p['lat']) for p in m['geometry']]
                if len(pts) > 1: outer_lines.append(LineString(pts))
print('closed polys', len(polys), 'outer lines', len(outer_lines))
pz = list(polygonize(unary_union(outer_lines))) if outer_lines else []
print('polygonized from relation outers:', len(pz), [round(p.area / 1e6, 2) for p in sorted(pz, key=lambda p: -p.area)[:6]])
water = unary_union(polys + pz)
print('water', water.geom_type, 'area km2', round(water.area / 1e6, 2), 'bounds', [round(v) for v in water.bounds])
# sanity: distance from Dashashwamedh Ghat and Panchganga Ghat to the water edge
for name, la, lo in [('Dashashwamedh', 25.30693, 83.01065), ('Panchganga', 25.31502, 83.01798), ('Assi', 25.28904, 83.00697), ('Raj Ghat', 25.32341, 83.03104)]:
    p = Point(*tr.transform(lo, la))
    print(f'  {name:14s} distance to water boundary: {water.boundary.distance(p):6.1f} m  inside={water.contains(p)}')
xy = np.load(os.path.join(S, 'xy.npy'))
rows = json.load(open(os.path.join(S, 'rows.json')))
pts = [Point(*p) for p in xy]
bnd = water.boundary
dist = np.array([bnd.distance(p) for p in pts])
inside = np.array([water.contains(p) for p in pts])
print('\npoints inside water polygon (GPS/bank error):', int(inside.sum()), ' max depth', round(float(dist[inside].max()), 1) if inside.any() else 0)
dd = dist.copy(); dd[inside] = 0.0
print('DISTANCE TO GANGA BANK: median', round(float(np.median(dd)), 1), 'mean', round(float(dd.mean()), 1), 'p25', round(float(np.percentile(dd, 25)), 1), 'p75', round(float(np.percentile(dd, 75)), 1), 'max', round(float(dd.max()), 1))
for r in [50, 100, 250, 500, 1000, 2000, 3000]:
    print(f'  within {r:4d} m: {(dd <= r).sum():4d}  ({(dd <= r).mean() * 100:5.1f}%)')
hull = MultiPoint([tuple(p) for p in xy]).convex_hull
land = hull.difference(water)
print('hull km2', round(hull.area / 1e6, 2), 'land km2', round(land.area / 1e6, 2))
bands = [0, 100, 250, 500, 750, 1000, 1500, 2000, 3000, 5000]
bandstats = []
for i in range(len(bands) - 1):
    a, b = bands[i], bands[i + 1]
    ring = water.buffer(b).difference(water.buffer(a)).intersection(land)
    cnt = int(((dd > a) & (dd <= b)).sum() + (inside.sum() if a == 0 else 0))
    area = ring.area / 1e6
    bandstats.append({'from': a, 'to': b, 'n': cnt, 'area_km2': round(area, 3), 'density': round(cnt / area, 1) if area > 0 else None})
    print(f'  {a:4d}-{b:4d} m: n={cnt:4d}  land area={area:6.2f} km2  density={cnt / area if area else 0:7.1f} /km2')
fams = ['Shaiva', 'Hanuman', 'Ganesh', 'Goddess', 'Folk', 'Vaishnava', 'Other']
famdist = {}
print('\nMEDIAN DISTANCE TO GANGA by family:')
for f in fams:
    m = np.array([f in r['f'] for r in rows])
    famdist[f] = {'n': int(m.sum()), 'median': round(float(np.median(dd[m])), 1), 'p25': round(float(np.percentile(dd[m], 25)), 1), 'p75': round(float(np.percentile(dd[m], 75)), 1), 'share_500': round(float((dd[m] <= 500).mean()), 4)}
    print(f'  {f:10s} n={m.sum():4d} median={np.median(dd[m]):6.0f} m  IQR {np.percentile(dd[m], 25):5.0f}-{np.percentile(dd[m], 75):5.0f}  within 500 m: {(dd[m] <= 500).mean() * 100:4.1f}%')
sts = ['Free-standing', 'Built into a wall', 'Temple complex', 'Tree-temple', 'Tree', 'Built-around']
stdist = {}
print('MEDIAN DISTANCE by structure:')
for s in sts:
    m = np.array([(r['s'][0] if r['s'] else '') == s for r in rows])
    stdist[s] = {'n': int(m.sum()), 'median': round(float(np.median(dd[m])), 1), 'share_500': round(float((dd[m] <= 500).mean()), 4)}
    print(f'  {s:18s} n={m.sum():4d} median={np.median(dd[m]):6.0f} m  within 500 m: {(dd[m] <= 500).mean() * 100:4.1f}%')
def mw(a, b):
    allv = np.concatenate([a, b]); order = np.argsort(allv, kind='stable'); sv = allv[order]; rs = np.empty(len(allv))
    i = 0
    while i < len(allv):
        j = i
        while j + 1 < len(allv) and sv[j + 1] == sv[i]: j += 1
        rs[i:j + 1] = (i + j) / 2 + 1; i = j + 1
    ranks = np.empty(len(allv)); ranks[order] = rs
    n1, n2 = len(a), len(b); U = ranks[:n1].sum() - n1 * (n1 + 1) / 2
    return (U - n1 * n2 / 2) / math.sqrt(n1 * n2 * (n1 + n2 + 1) / 12), U / (n1 * n2)
sh = np.array([r['f'] == ['Shaiva'] for r in rows]); ha = np.array([r['f'] == ['Hanuman'] for r in rows])
z, auc = mw(dd[ha], dd[sh]); print(f'\nMann-Whitney Hanuman-only vs Shaiva-only: z={z:.1f}, P(Hanuman farther from river)={auc:.2f}')
tree = np.array([any(a in ('Tree', 'Tree-temple') for a in r['s']) for r in rows])
z2, auc2 = mw(dd[tree], dd[~tree]); print(f'Mann-Whitney tree-associated vs not: z={z2:.1f}, P(tree farther)={auc2:.2f}')
wall = np.array([(r['s'][0] if r['s'] else '') == 'Built into a wall' for r in rows])
z3, auc3 = mw(dd[wall], dd[~wall]); print(f'Mann-Whitney wall vs not: z={z3:.1f}, P(wall farther)={auc3:.2f}')
D = np.sqrt(((xy[:, None, :] - xy[None, :, :]) ** 2).sum(-1)); np.fill_diagonal(D, np.inf); nn = D.min(1)
rd = np.argsort(np.argsort(dd)); rn = np.argsort(np.argsort(nn))
rho = float(np.corrcoef(rd, rn)[0, 1]); print('Spearman rho (river distance vs nearest-neighbour distance):', round(rho, 3))
# median river distance of the hot-spot cells' points
hs = json.load(open(os.path.join(S, 'hex_stats.geojson')))
print('Top cell (Panchganga) distance:', round(bnd.distance(Point(*tr.transform(83.01826, 25.31504))), 1))
# OSM comparison
pow_ = json.load(open(os.path.join(ROOT, 'data', 'raw', 'osm', 'places_of_worship_overpass.json'), encoding='utf-8'))
osm = []
for e in pow_['elements']:
    t = e.get('tags', {})
    lo, la = (e['lon'], e['lat']) if e['type'] == 'node' else (e['center']['lon'], e['center']['lat'])
    osm.append({'lon': lo, 'lat': la, 'name': t.get('name:en') or t.get('name'), 'religion': t.get('religion'), 'xy': tr.transform(lo, la)})
hin = [o for o in osm if o['religion'] == 'hindu']
oxy = np.array([o['xy'] for o in hin])
dm = np.sqrt(((xy[:, None, :] - oxy[None, :, :]) ** 2).sum(-1))
inhull = sum(1 for o in hin if hull.contains(Point(*o['xy'])))
print('\nOSM places of worship in bbox:', len(osm), ' hindu:', len(hin), ' hindu inside survey hull:', inhull)
print('surveyed mandirs within 50 m of an OSM Hindu temple:', int((dm.min(1) <= 50).sum()), ' OSM temples with a survey point within 50 m:', int((dm.min(0) <= 50).sum()))
# save
ws = water.simplify(4)
geoms = list(ws.geoms) if ws.geom_type == 'MultiPolygon' else [ws]
def ring_ll(ring): return [[round(a, 5) for a in back.transform(*c)] for c in ring.coords]
json.dump({'type': 'FeatureCollection', 'features': [{'type': 'Feature', 'properties': {'name': 'Ganga'}, 'geometry': {'type': 'Polygon', 'coordinates': [ring_ll(g.exterior)] + [ring_ll(i) for i in g.interiors]}} for g in geoms if g.area > 1e5]},
          open(os.path.join(S, 'ganga.geojson'), 'w'), separators=(',', ':'))
print('ganga.geojson size', os.path.getsize(os.path.join(S, 'ganga.geojson')))
np.save(os.path.join(S, 'river_dist.npy'), dd)
json.dump({'river_median': round(float(np.median(dd)), 1), 'river_mean': round(float(dd.mean()), 1), 'river_p25': round(float(np.percentile(dd, 25)), 1), 'river_p75': round(float(np.percentile(dd, 75)), 1),
           'within': {str(r): int((dd <= r).sum()) for r in [50, 100, 250, 500, 1000, 2000, 3000]},
           'bands': bandstats, 'fam': famdist, 'struct': stdist, 'mw_hanuman_vs_shaiva': [round(z, 2), round(auc, 3)], 'mw_tree': [round(z2, 2), round(auc2, 3)], 'mw_wall': [round(z3, 2), round(auc3, 3)],
           'spearman_river_nn': round(rho, 3), 'osm_pow': len(osm), 'osm_hindu': len(hin), 'osm_hindu_in_hull': inhull,
           'survey_near_osm_50': int((dm.min(1) <= 50).sum()), 'osm_near_survey_50': int((dm.min(0) <= 50).sum()), 'land_km2': round(land.area / 1e6, 2), 'hull_km2': round(hull.area / 1e6, 2)},
          open(os.path.join(S, 'river_stats.json'), 'w'), indent=1)
json.dump([{'lon': o['lon'], 'lat': o['lat'], 'name': o['name'], 'religion': o['religion']} for o in osm], open(os.path.join(S, 'osm_pow.json'), 'w'))
print('saved')
