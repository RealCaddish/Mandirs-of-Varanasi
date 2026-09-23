"""Reconstruct the full flat-topped hex lattice used for hex_final.geojson (UTM 44N,
column pitch 100 m, row pitch 115.47 m, circumradius 66.67 m), bin the 2,296 survey
points into it, compare with the original deity_count, and compute Moran's I and
Getis-Ord Gi* hot spots on the original counts with zero cells restored."""
import json, math, collections, os
import numpy as np
from pyproj import Transformer

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
S = os.path.join(ROOT, 'scripts', 'cache'); os.makedirs(S, exist_ok=True)
h = json.load(open(os.path.join(ROOT, 'data', 'raw', 'hex_final.geojson'), encoding='utf-8'))
hf = h['features']
L = np.array([f['properties']['left'] for f in hf]); B = np.array([f['properties']['bottom'] for f in hf])
Rr = np.array([f['properties']['right'] for f in hf]); T = np.array([f['properties']['top'] for f in hf])
cnt0 = np.array([f['properties']['deity_count'] for f in hf], float)
W = float(np.round((Rr - L).mean(), 4)); H = float(np.round((T - B).mean(), 4))  # 133.3334, 115.4701
PX = 100.0; PY = H
x0 = L.min(); y0 = B.min()
col0 = np.round((L - x0) / PX).astype(int)
row0 = np.round((B - y0 - (col0 % 2 == 0) * PY / 2) / PY).astype(int)  # even cols offset by half row (from parity check)
# check parity assumption
res = (B - y0 - (col0 % 2 == 0) * PY / 2) / PY - row0
print('max row residual', np.abs(res).max())
orig = {(c, r): v for c, r, v in zip(col0.tolist(), row0.tolist(), cnt0.tolist())}
print('original hexes', len(orig), 'unique keys', len(set(orig)))

# full lattice covering original extent + 1 ring
cmin, cmax = col0.min() - 1, col0.max() + 1
rmin, rmax = row0.min() - 1, row0.max() + 1
cells = [(c, r) for c in range(cmin, cmax + 1) for r in range(rmin, rmax + 1)]
def centre(c, r):
    return x0 + c * PX + W / 2, y0 + r * PY + ((c % 2 == 0) * PY / 2) + H / 2
# bin the points
xy = np.load(os.path.join(S, 'xy.npy'))
rows = json.load(open(os.path.join(S, 'rows.json')))
R_ = W / 2
def point_cell(px, py):
    # candidate columns near px
    c = int(round((px - x0 - W / 2) / PX))
    best = None
    for cc in (c - 1, c, c + 1):
        r = int(round((py - y0 - ((cc % 2 == 0) * PY / 2) - H / 2) / PY))
        for rr in (r - 1, r, r + 1):
            cx, cy = centre(cc, rr)
            d = math.hypot(px - cx, py - cy)
            if best is None or d < best[0]: best = (d, (cc, rr))
    return best[1]
pcount = collections.Counter(); pcells = []
for (px, py) in xy:
    k = point_cell(px, py); pcount[k] += 1; pcells.append(k)
print('point-binned hexes', len(pcount), 'points', sum(pcount.values()))
# compare
keys = sorted(set(orig) | set(pcount))
o = np.array([orig.get(k, 0) for k in keys]); p = np.array([pcount.get(k, 0) for k in keys])
print('hexes orig>0:', (o > 0).sum(), ' pts>0:', (p > 0).sum(), ' both:', ((o > 0) & (p > 0)).sum(), ' orig only:', ((o > 0) & (p == 0)).sum(), ' pts only:', ((o == 0) & (p > 0)).sum())
print('corr(orig, pts) over union cells:', np.corrcoef(o, p)[0, 1])
print('sum orig', o.sum(), 'sum pts', p.sum(), 'cells where pts>orig:', (p > o).sum(), ' sum excess', (p - o)[p > o].sum())
diff = o - p
print('orig-minus-points: mean', diff.mean(), ' cells with orig>=pts+5:', (diff >= 5).sum())
# where are the "missing" ones? centroid of orig-only mass vs all
back = Transformer.from_crs('EPSG:32644', 'EPSG:4326', always_xy=True)
mass = np.array([centre(*k) for k in keys])
mo = (mass * o[:, None]).sum(0) / o.sum(); mp = (mass * p[:, None]).sum(0) / p.sum()
md = (mass * np.clip(diff, 0, None)[:, None]).sum(0) / np.clip(diff, 0, None).sum()
print('centroid orig', back.transform(*mo), ' pts', back.transform(*mp), ' missing-mass', back.transform(*md))
# top cells
print('top 10 original cells (count, points, lon/lat):')
for i in np.argsort(-o)[:10]:
    print('  ', int(o[i]), int(p[i]), [round(v, 5) for v in back.transform(*mass[i])])

# ---- spatial autocorrelation on original counts with zero cells restored inside the study window
# study window: cells within the bounding lattice range (all `cells`)
allkeys = cells
idx = {k: i for i, k in enumerate(allkeys)}
vals = np.array([orig.get(k, 0) for k in allkeys], float)
N = len(vals)
# neighbours: 6 adjacent hexes (flat-topped, even-col shifted up by half)
def nbrs(c, r):
    if c % 2 == 0:  # even col is shifted +half row
        return [(c, r + 1), (c, r - 1), (c + 1, r), (c + 1, r + 1), (c - 1, r), (c - 1, r + 1)]
    return [(c, r + 1), (c, r - 1), (c + 1, r - 1), (c + 1, r), (c - 1, r - 1), (c - 1, r)]
# verify neighbour geometry: distances between centres should all be ~115.47
c_, r_ = 5, 5
print('nbr distances', sorted(round(math.hypot(*(np.array(centre(*k)) - np.array(centre(c_, r_)))), 1) for k in nbrs(c_, r_)))
c_, r_ = 6, 5
print('nbr distances (odd col)', sorted(round(math.hypot(*(np.array(centre(*k)) - np.array(centre(c_, r_)))), 1) for k in nbrs(c_, r_)))
nb = [[idx[k] for k in nbrs(*key) if k in idx] for key in allkeys]

# restrict study window to a convex hull of original hexes (with 2-ring buffer) to avoid huge empty margins
from shapely.geometry import MultiPoint, Point
hullpoly = MultiPoint([centre(*k) for k in orig]).convex_hull.buffer(2 * PY)
inwin = np.array([hullpoly.contains(Point(*centre(*k))) for k in allkeys])
print('lattice cells', N, ' in study window', inwin.sum(), ' of which occupied', (vals[inwin] > 0).sum())
win = np.where(inwin)[0]; wpos = {i: j for j, i in enumerate(win)}
v = vals[win]; Nw = len(v)
wn = [[wpos[j] for j in nb[i] if j in wpos] for i in win]
# Moran's I (binary contiguity, row-unstandardised)
z = v - v.mean()
S0 = sum(len(a) for a in wn)
num = sum(z[i] * z[j] for i in range(Nw) for j in wn[i])
I = (Nw / S0) * num / (z ** 2).sum()
EI = -1 / (Nw - 1)
# variance under randomisation
S1 = 0.5 * sum(4 for i in range(Nw) for j in wn[i]) / 2 * 2  # each pair (w_ij + w_ji)^2 = 4, counted twice in double loop -> S1 = 0.5*sum = 2*pairs
pairs = S0 / 2
S1 = 0.5 * (pairs * 2 * 4) / 2 * 2  # simplify: S1 = 0.5*sum_ij (w_ij+w_ji)^2 = 0.5 * (2*pairs*4) = 4*pairs
S1 = 4 * pairs
deg = np.array([len(a) for a in wn], float)
S2 = ((2 * deg) ** 2).sum()
b2 = Nw * (z ** 4).sum() / ((z ** 2).sum() ** 2)
VI = (Nw * ((Nw ** 2 - 3 * Nw + 3) * S1 - Nw * S2 + 3 * S0 ** 2) - b2 * ((Nw ** 2 - Nw) * S1 - 2 * Nw * S2 + 6 * S0 ** 2)) / ((Nw - 1) * (Nw - 2) * (Nw - 3) * S0 ** 2) - EI ** 2
zI = (I - EI) / math.sqrt(VI)
print(f"\nMORAN'S I (queen/6-neighbour contiguity, N={Nw}): I={I:.4f}, E[I]={EI:.4f}, z={zI:.1f}")
# same on occupied-only cells for comparison
# Getis-Ord Gi* with self-included neighbourhood
xbar = v.mean(); s = v.std()
gi = np.zeros(Nw);
for i in range(Nw):
    ids = [i] + wn[i]; wsum = len(ids)
    num_ = v[ids].sum() - xbar * wsum
    den_ = s * math.sqrt((Nw * wsum - wsum ** 2) / (Nw - 1))
    gi[i] = num_ / den_ if den_ > 0 else 0
print('Gi* z: min', gi.min(), 'max', gi.max())
for thr in [1.65, 1.96, 2.58, 3.29]:
    print(f'  cells with Gi* z >= {thr}: {(gi >= thr).sum():4d}  (occupied among them {(v[gi >= thr] > 0).sum()}), z <= -{thr}: {(gi <= -thr).sum()}')
# FDR (Benjamini-Hochberg) correction on two-sided p-values
pv = np.array([math.erfc(abs(g) / math.sqrt(2)) for g in gi])
order = np.argsort(pv); m = Nw; crit = 0.05 * (np.arange(1, m + 1)) / m
passed = pv[order] <= crit
kmax = np.where(passed)[0].max() + 1 if passed.any() else 0
fdr_sig = np.zeros(Nw, bool); fdr_sig[order[:kmax]] = True
print(f'  FDR(0.05)-significant cells: {fdr_sig.sum()} hot={((gi > 0) & fdr_sig).sum()} cold={((gi < 0) & fdr_sig).sum()}')

# write hex_stats.geojson: all occupied original hexes + Gi* z + significance + point-based count + hull-window cold cells? keep only occupied + hot cells
def hexpoly(c, r):
    cx, cy = centre(c, r); pts = []
    for k in range(6):
        ang = math.radians(60 * k)
        pts.append(back.transform(cx + R_ * math.cos(ang), cy + R_ * math.sin(ang)))
    pts.append(pts[0]); return [[round(a, 5), round(b, 5)] for a, b in pts]
def cls(g, sig):
    if not sig: return 0
    return 3 if g >= 3.29 else 2 if g >= 2.58 else 1 if g > 0 else -1
feats = []
hot_cells = 0
for j, i in enumerate(win):
    k = allkeys[i]
    c0 = int(vals[i]); pc = int(pcount.get(k, 0))
    if c0 == 0 and pc == 0 and not (fdr_sig[j] and gi[j] > 0): continue
    feats.append({'type': 'Feature', 'properties': {'n': c0, 'np': pc, 'gz': round(float(gi[j]), 2), 'hot': cls(gi[j], fdr_sig[j])},
                  'geometry': {'type': 'Polygon', 'coordinates': [hexpoly(*k)]}})
out = {'type': 'FeatureCollection', 'features': feats}
json.dump(out, open(os.path.join(S, 'hex_stats.geojson'), 'w'), separators=(',', ':'))
print('wrote hex_stats.geojson', len(feats), 'features, size', os.path.getsize(os.path.join(S, 'hex_stats.geojson')))
print('hot classes', collections.Counter(f['properties']['hot'] for f in feats))
# deity family composition of hot-spot cells vs elsewhere (using point cells)
hotkeys = {allkeys[i] for j, i in enumerate(win) if fdr_sig[j] and gi[j] > 0}
inhot = np.array([k in hotkeys for k in pcells])
print('points inside FDR hot spots:', inhot.sum(), f'({inhot.mean() * 100:.1f}%) in', len(hotkeys), 'cells =', len(hotkeys) * 0.011547, 'km2')
fams = ['Shaiva', 'Hanuman', 'Ganesh', 'Goddess', 'Folk', 'Vaishnava', 'Other']
print('family share inside hot spots vs outside:')
for f in fams:
    a = np.array([f in r['f'] for r in rows])
    print(f'  {f:10s} hot {a[inhot].mean() * 100:5.1f}%  outside {a[~inhot].mean() * 100:5.1f}%  ratio {a[inhot].mean() / a[~inhot].mean():.2f}')
sts = ['Free-standing', 'Built into a wall', 'Temple complex', 'Tree-temple', 'Tree', 'Built-around']
print('structure share inside hot spots vs outside:')
for st in sts:
    a = np.array([(r['s'][0] if r['s'] else '') == st for r in rows])
    print(f'  {st:18s} hot {a[inhot].mean() * 100:5.1f}%  outside {a[~inhot].mean() * 100:5.1f}%')
img = np.array([r['n'] for r in rows])
print('median images hot', np.median(img[inhot]), 'outside', np.median(img[~inhot]))
json.dump({'moran_I': I, 'moran_z': zI, 'N_window': int(Nw), 'gi_hot_fdr': int(((gi > 0) & fdr_sig).sum()), 'gi_cold_fdr': int(((gi < 0) & fdr_sig).sum()),
           'points_in_hot': int(inhot.sum()), 'hot_cells': len(hotkeys), 'hex_area_km2': 0.011547,
           'orig_sum': int(o.sum()), 'pts_sum': int(p.sum()), 'corr_orig_pts': float(np.corrcoef(o, p)[0, 1])},
          open(os.path.join(S, 'hexstats.json'), 'w'), indent=1)
