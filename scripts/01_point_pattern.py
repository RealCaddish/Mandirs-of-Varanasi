import json, collections, math, itertools, os, sys
import numpy as np
from pyproj import Transformer
from shapely.geometry import MultiPoint

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
S = os.path.join(ROOT, 'scripts', 'cache'); os.makedirs(S, exist_ok=True)

d = json.load(open(os.path.join(ROOT, 'data', 'raw', 'temple', 'temple.json'), encoding='utf-8'))
feats = d['features']
props = [f['properties'] for f in feats]
lon = np.array([f['geometry']['coordinates'][0] for f in feats])
lat = np.array([f['geometry']['coordinates'][1] for f in feats])
tr = Transformer.from_crs('EPSG:4326', 'EPSG:32644', always_xy=True)
x, y = tr.transform(lon, lat)
x = np.array(x); y = np.array(y)
n = len(x)
print('n', n, 'UTM44N x', x.min(), x.max(), 'y', y.min(), y.max())
hull = MultiPoint(list(zip(x, y))).convex_hull
A = hull.area
print('convex hull area km2', A / 1e6, ' bbox area km2', (x.max() - x.min()) * (y.max() - y.min()) / 1e6)
print('overall density per km2 (hull)', n / (A / 1e6))

dx = x[:, None] - x[None, :]; dy = y[:, None] - y[None, :]
D = np.sqrt(dx * dx + dy * dy)
np.fill_diagonal(D, np.inf)
nn = D.min(axis=1)
print('\nNEAREST NEIGHBOUR: mean', nn.mean(), 'median', np.median(nn), 'p10', np.percentile(nn, 10), 'p90', np.percentile(nn, 90), 'max', nn.max())
print('zero-distance NN (exact dup coords):', int((nn == 0).sum()))
lam = n / A
expected = 0.5 / math.sqrt(lam)
R = nn.mean() / expected
se = 0.26136 / math.sqrt(n * lam)
z = (nn.mean() - expected) / se
print(f'Clark-Evans R = {R:.3f} (expected NN {expected:.1f} m, observed {nn.mean():.1f} m), z = {z:.1f}')
nn2 = nn[nn > 0]
print('mean NN excluding zeros', nn2.mean(), 'median', np.median(nn2))
for r in [10, 25, 50, 100, 200]:
    print(f'  share of mandirs with a neighbour within {r} m: {(nn <= r).mean() * 100:.1f}%')

np.fill_diagonal(D, np.nan)
print('\nRIPLEY K/L (no edge correction):')
ripley = []
for r in [50, 100, 200, 300, 500, 750, 1000, 1500, 2000]:
    k = (np.nansum(D <= r)) / (n * lam)
    Lr = math.sqrt(k / math.pi)
    ripley.append({'r': r, 'K': k, 'L_minus_r': Lr - r})
    print(f'  r={r:5d} m  K={k:12.0f}  L(r)-r={Lr - r:8.1f} m  (CSR expects 0)')

def toks(s):
    return [t.strip() for t in (s or '').split(',') if t.strip()]

canon = {
    'Siva': 'Shiva', 'Siva-Parvati': 'Shiva-Parvati', 'Siva family': 'Shiva family',
    'Hanuman': 'Hanuman', 'Ganesh': 'Ganesh', 'Devi': 'Devi',
    '__ Maa': 'Local Maa', 'Shaayari maa': 'Local Maa', 'caura maa': 'Local Maa',
    'Sitla Maa': 'Sitala Maa', '__ Bir Baabaa': 'Bir Baba', 'Krishna': 'Krishna',
    'Rama family': 'Rama', 'Rama-Sita': 'Rama', 'RAMA': 'Rama',
    'gramadevata': 'Village deity', 'Other': 'Other'}
fam = {'Shiva': 'Shaiva', 'Shiva-Parvati': 'Shaiva', 'Shiva family': 'Shaiva', 'Hanuman': 'Hanuman', 'Ganesh': 'Ganesh',
       'Devi': 'Goddess', 'Local Maa': 'Goddess', 'Sitala Maa': 'Goddess', 'Bir Baba': 'Folk', 'Village deity': 'Folk',
       'Krishna': 'Vaishnava', 'Rama': 'Vaishnava', 'Other': 'Other'}
sc = {'Free-standing': 'Free-standing', 'Built into a wall': 'Built into a wall', 'Part of a temple complex': 'Temple complex',
      'Tree-temple [temple built around a tree]': 'Tree-temple', 'Tree': 'Tree', 'Built-around': 'Built-around'}

rows = []
for p, xx, yy, lo, la in zip(props, x, y, lon, lat):
    t = toks(p['deity']); c = sorted(set(canon.get(a, a) for a in t))
    rows.append(dict(t=t, c=c, f=sorted(set(fam[a] for a in c)), x=float(xx), y=float(yy), lon=float(lo), lat=float(la),
                     n=p['deities_pr'], s=[sc.get(a, a) for a in toks(p['temple_str'])], name=(p['temple_nam'] or '').strip()))
tokc = collections.Counter(a for r in rows for a in r['c'])
print('\nCANONICAL deity presence (share of mandirs where present):')
for k, v in tokc.most_common(): print(f'{v:5d} {v / n * 100:5.1f}%  {k}')
print('mandirs with 1 deity category:', sum(1 for r in rows if len(r['c']) == 1), ' 2:', sum(1 for r in rows if len(r['c']) == 2), ' 3+:', sum(1 for r in rows if len(r['c']) >= 3))
famc = collections.Counter(f for r in rows for f in r['f'])
print('\nFAMILY presence:')
for k, v in famc.most_common(): print(f'{v:5d} {v / n * 100:5.1f}%  {k}')
only = collections.Counter(tuple(r['f']) for r in rows)
print('\nFAMILY combos (top 15):')
for k, v in only.most_common(15): print(f'{v:5d}  {"+".join(k)}')
print('single-family shrines:', sum(1 for r in rows if len(r['f']) == 1), f'({sum(1 for r in rows if len(r["f"]) == 1) / n * 100:.1f}%)')

cats = [k for k, _ in tokc.most_common() if tokc[k] >= 30]
print('\nCO-OCCURRENCE lift (observed pair / expected under independence):')
cooc = []
for a, b in itertools.combinations(cats, 2):
    ab = sum(1 for r in rows if a in r['c'] and b in r['c'])
    exp = tokc[a] * tokc[b] / n
    cooc.append((a, b, ab, exp, ab / exp))
for a, b, ab, exp, lift in sorted(cooc, key=lambda t: -t[2]):
    if ab >= 15: print(f'  {a:14s} & {b:14s}  n={ab:4d}  expected={exp:6.1f}  lift={lift:4.2f}')
print('  --- strongest negative (lift<0.5, expected>=15)')
for a, b, ab, exp, lift in sorted(cooc, key=lambda t: t[4]):
    if exp >= 15 and lift < 0.5: print(f'  {a:14s} & {b:14s}  n={ab:4d}  expected={exp:6.1f}  lift={lift:4.2f}')

stc = collections.Counter(a for r in rows for a in set(r['s']))
print('\nSTRUCTURE presence:')
for k, v in stc.most_common(): print(f'{v:5d} {v / n * 100:5.1f}%  {k}')
print('any tree association:', sum(1 for r in rows if any(a in ('Tree', 'Tree-temple') for a in r['s'])))
print('blank structure:', sum(1 for r in rows if not r['s']))

def prim_s(r): return r['s'][0] if r['s'] else 'Unrecorded'
structs = ['Free-standing', 'Built into a wall', 'Temple complex', 'Tree-temple', 'Tree', 'Built-around', 'Unrecorded']
fams = ['Shaiva', 'Hanuman', 'Ganesh', 'Goddess', 'Folk', 'Vaishnava', 'Other']
print('\nCROSSTAB family presence x first-listed structure (row %):')
print(f'{"":12s}' + ''.join(f'{s[:12]:>13s}' for s in structs) + '    n')
for f in fams:
    sub = [r for r in rows if f in r['f']]
    cnt = collections.Counter(prim_s(r) for r in sub)
    print(f'{f:12s}' + ''.join(f'{cnt[s] / len(sub) * 100:12.1f}%' for s in structs) + f' {len(sub):5d}')
cnt = collections.Counter(prim_s(r) for r in rows)
print(f'{"ALL":12s}' + ''.join(f'{cnt[s] / n * 100:12.1f}%' for s in structs) + f' {n:5d}')

def chi2_sf(xx, k):
    a = k / 2.0; xv = xx / 2.0
    if xv <= 0: return 1.0
    if xv < a + 1:
        ap = a; s = 1.0 / a; dl = s
        for _ in range(2000):
            ap += 1; dl *= xv / ap; s += dl
            if abs(dl) < abs(s) * 1e-15: break
        return 1.0 - s * math.exp(-xv + a * math.log(xv) - math.lgamma(a))
    b = xv + 1 - a; c = 1e300; dd = 1 / b; h = dd
    for i in range(1, 2000):
        an = -i * (i - a); b += 2; dd = an * dd + b
        if abs(dd) < 1e-300: dd = 1e-300
        c = b + an / c
        if abs(c) < 1e-300: c = 1e-300
        dd = 1 / dd; de = dd * c; h *= de
        if abs(de - 1) < 1e-15: break
    return math.exp(-xv + a * math.log(xv) - math.lgamma(a)) * h

excl = [r for r in rows if len(r['f']) == 1 and r['s']]
st6 = structs[:-1]
M = np.array([[sum(1 for r in excl if r['f'][0] == f and prim_s(r) == s) for s in st6] for f in fams], float)
E = M.sum(1, keepdims=True) * M.sum(0, keepdims=True) / M.sum()
chi = float(((M - E) ** 2 / E).sum()); dof = (M.shape[0] - 1) * (M.shape[1] - 1)
V = math.sqrt(chi / (M.sum() * min(M.shape[0] - 1, M.shape[1] - 1)))
p_chi = chi2_sf(chi, dof)
print(f'\nCHI-SQUARE family x structure (single-family shrines, n={int(M.sum())}): chi2={chi:.1f} dof={dof} p={p_chi:.2e}  Cramer V={V:.3f}')
Rz = (M - E) / np.sqrt(E)
print('standardized residuals:')
print(f'{"":12s}' + ''.join(f'{s[:12]:>13s}' for s in st6))
for f, row in zip(fams, Rz): print(f'{f:12s}' + ''.join(f'{v:13.1f}' for v in row))

print('\nDEITIES PRESENT (images) by family:')
for f in fams:
    sub = np.array([r['n'] for r in rows if f in r['f']])
    print(f'  {f:10s} n={len(sub):4d} median={np.median(sub):.0f} mean={sub.mean():.2f}  share zero={np.mean(sub == 0) * 100:.0f}%  share>=5={np.mean(sub >= 5) * 100:.0f}%')
print('DEITIES PRESENT by structure:')
for s in structs:
    sub = np.array([r['n'] for r in rows if prim_s(r) == s])
    if len(sub): print(f'  {s:18s} n={len(sub):4d} median={np.median(sub):.0f} mean={sub.mean():.2f} share>=5={np.mean(sub >= 5) * 100:.0f}%')
allimg = np.array([r['n'] for r in rows])
print('images: total', allimg.sum(), 'gini-like share: top 10% of shrines hold', np.sort(allimg)[::-1][:n // 10].sum() / allimg.sum() * 100, '% of images')

named = [r for r in rows if r['name'] and r['name'].lower() not in ('none', 'see photo')]
shivakeys = ('mahadev', 'shiv', 'eshwar', 'eshvar', 'esvar', 'ishwar', 'nath', 'mahaadev', 'esvar')
print('\nNAMED shrines:', len(named), ' of which Shiva-type name:', sum(1 for r in named if any(k in r['name'].lower() for k in shivakeys)))
print('named: family presence', collections.Counter(f for r in named for f in r['f']).most_common())
print('named: structure', collections.Counter(prim_s(r) for r in named).most_common())
print('named: median images', np.median([r['n'] for r in named]), ' unnamed median', np.median([r['n'] for r in rows if r not in named]))

print('\nSPATIAL CENTRE / STANDARD DISTANCE by family:')
cx, cy = x.mean(), y.mean()
back = Transformer.from_crs('EPSG:32644', 'EPSG:4326', always_xy=True)
print('  all mean centre lon/lat', back.transform(cx, cy), ' std distance', math.sqrt(((x - cx) ** 2 + (y - cy) ** 2).mean()))
centres = {}
for f in fams:
    idx = [i for i, r in enumerate(rows) if f in r['f']]
    fx, fy = x[idx].mean(), y[idx].mean()
    sd = math.sqrt(((x[idx] - fx) ** 2 + (y[idx] - fy) ** 2).mean())
    ll = back.transform(fx, fy)
    centres[f] = dict(n=len(idx), lon=ll[0], lat=ll[1], sd=sd)
    print(f'  {f:10s} n={len(idx):4d} offset dx={fx - cx:6.0f} m dy={fy - cy:6.0f} m  std dist={sd:5.0f} m  lon/lat={ll[0]:.5f},{ll[1]:.5f}')

np.save(os.path.join(S, 'xy.npy'), np.stack([x, y], 1))
json.dump(rows, open(os.path.join(S, 'rows.json'), 'w'))
json.dump({'n': n, 'hull_km2': A / 1e6, 'nn_mean': float(nn.mean()), 'nn_median': float(np.median(nn)), 'clark_evans_R': R, 'clark_evans_z': z,
           'ripley': ripley, 'chi2': chi, 'chi2_dof': dof, 'chi2_p': p_chi, 'cramers_v': V, 'centres': centres,
           'crosstab_fams': fams, 'crosstab_structs': st6, 'crosstab_M': M.tolist(), 'crosstab_resid': Rz.tolist()},
          open(os.path.join(S, 'pointstats.json'), 'w'), indent=1)
print('\nsaved rows.json / xy.npy / pointstats.json')
