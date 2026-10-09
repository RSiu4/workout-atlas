#!/usr/bin/env python3
"""Generate dist/demo.html: the app with two *synthetic* people baked in, used for README screenshots.

The routes are made up: random trips routed along the real street network of a Vienna area
(OpenStreetMap data, (c) OpenStreetMap contributors, ODbL), so they line up with the map. No real
person's data is used, so screenshots made from it are safe to publish.

The street network is downloaded once from the Overpass API and cached in dist/.

Usage:  python tools/make_demo.py [--tab compare]
"""
import sys, os, json, math, random, heapq, urllib.request, urllib.parse
import datetime as dt

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
BBOX = (48.190, 16.355, 48.245, 16.450)          # south, west, north, east: Leopoldstadt / Prater / Donaukanal
CENTER = (48.2175, 16.4025)
KX = 111320 * math.cos(math.radians(CENTER[0])); KY = 110540
HIGHWAYS = 'residential|tertiary|secondary|primary|cycleway|footway|path|pedestrian|living_street|unclassified'
SPEEDUP = {'cycleway': 1.5, 'primary': 1.1, 'secondary': 1.15, 'tertiary': 1.1, 'footway': .95, 'path': .9}


def ll(x, y):
    return CENTER[0] + y / KY, CENTER[1] + x / KX


def load_osm():
    cache = os.path.join(ROOT, 'dist', 'osm_demo_area.json')
    if not os.path.exists(cache):
        os.makedirs(os.path.dirname(cache), exist_ok=True)
        q = '[out:json][timeout:120];way["highway"~"^(%s)$"]["access"!~"private|no"](%s,%s,%s,%s);out geom;' % ((HIGHWAYS,) + BBOX)
        req = urllib.request.Request('https://overpass-api.de/api/interpreter', data=urllib.parse.urlencode({'data': q}).encode(),
                                     headers={'User-Agent': 'workout-atlas-demo/1.0 (README screenshots)'})
        print('downloading street network from Overpass ...')
        with urllib.request.urlopen(req, timeout=150) as r:
            open(cache, 'wb').write(r.read())
    return json.load(open(cache, encoding='utf-8'))['elements']


def build_graph():
    node = {}; adj = {}
    key = lambda p: (round(p['lat'], 6), round(p['lon'], 6))
    for way in load_osm():
        g = way.get('geometry') or []
        mult = SPEEDUP.get(way.get('tags', {}).get('highway'), 1.0)
        for p, q in zip(g, g[1:]):
            a, b = key(p), key(q)
            for k, pt in ((a, p), (b, q)):
                if k not in node:
                    node[k] = ((pt['lon'] - CENTER[1]) * KX, (pt['lat'] - CENTER[0]) * KY); adj[k] = []
            if a == b:
                continue
            d = math.hypot(node[a][0] - node[b][0], node[a][1] - node[b][1]) / mult
            adj[a].append((b, d)); adj[b].append((a, d))
    # keep only the largest connected piece so every pick is reachable
    seen = set(); best = []
    for s in adj:
        if s in seen:
            continue
        comp = [s]; seen.add(s); i = 0
        while i < len(comp):
            for v, _ in adj[comp[i]]:
                if v not in seen:
                    seen.add(v); comp.append(v)
            i += 1
        if len(comp) > len(best):
            best = comp
    keep = set(best)
    node = {k: v for k, v in node.items() if k in keep}
    adj = {k: [(v, d) for v, d in adj[k] if v in keep] for k in keep}
    return node, adj


node, adj = build_graph()
NODES = list(node)
print(f'street network: {len(NODES)} nodes')


def nearest(x, y):
    return min(NODES, key=lambda n: (node[n][0] - x) ** 2 + (node[n][1] - y) ** 2)


def route(a, b, wobble=.0):
    dist = {a: 0.0}; prev = {}
    pq = [(0.0, a)]
    while pq:
        d, u = heapq.heappop(pq)
        if u == b:
            break
        if d > dist.get(u, 1e18):
            continue
        for v, w in adj[u]:
            nd = d + w * (1 + wobble * random.random())
            if nd < dist.get(v, 1e18):
                dist[v] = nd; prev[v] = u
                heapq.heappush(pq, (nd, v))
    if b not in prev and a != b:
        return [a]
    out = [b]
    while out[-1] != a:
        out.append(prev[out[-1]])
    return out[::-1]


_cache = {}


def variant(a, b, wob):
    """A few precomputed variants per trip so repeated trips share a path but not always."""
    k = (a, b, wob > 0)
    if k not in _cache:
        _cache[k] = [route(a, b, 0.0)] + [route(a, b, wob) for _ in range(2)] if wob > 0 else [route(a, b, 0.0)]
    return random.choice(_cache[k])


def trace(nodes, step=32, noise=2.0):
    pts = [node[n] for n in nodes]
    out = [pts[0]]
    for p in pts[1:-1]:
        if math.hypot(p[0] - out[-1][0], p[1] - out[-1][1]) >= step:
            out.append(p)
    out.append(pts[-1])
    return [(x + random.gauss(0, noise), y + random.gauss(0, noise)) for x, y in out]


def encode(pts, speed_kmh):
    la0 = lo0 = t0 = 0
    flat = []; t = 0.0; prev = None
    for x, y in pts:
        lat, lon = ll(x, y)
        if prev:
            t += math.hypot(x - prev[0], y - prev[1]) / (speed_kmh / 3.6)
        prev = (x, y)
        la, lo, tt = round(lat * 1e5), round(lon * 1e5), round(t)
        flat += [la - la0, lo - lo0, tt - t0]
        la0, lo0, t0 = la, lo, tt
    return flat


def length_km(pts):
    return sum(math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip(pts, pts[1:])) / 1000


def pick(cx, cy, r):
    ang = random.uniform(0, 6.283); rad = r * math.sqrt(random.random())
    return nearest(cx + rad * math.cos(ang), cy + rad * math.sin(ang))


def person(name, home_xy, work_xy, start, end, mix, seed):
    random.seed(seed)
    home, work = nearest(*home_xy), nearest(*work_xy)
    rides = [(pick(*home_xy, 3200), pick(*home_xy, 3200)) for _ in range(4)]      # favourite loops (two waypoints each)
    runs = [(pick(*home_xy, 1300), pick(*home_xy, 1300)) for _ in range(2)]
    walks = [pick(*home_xy, 1100) for _ in range(8)]
    recs = []; day = start
    while day <= end:
        wd = day.weekday(); season = 1.0 if 3 <= day.month <= 10 else .5
        legs = []                                              # (type, hour or None = right after previous leg, from, to, km/h, wobble)
        if wd < 5 and random.random() < mix['commute'] * season:
            legs += [('Cycling', 7.6 + random.uniform(-.4, .6), home, work, 17.5, .25)]
            if random.random() < .85:
                legs += [('Cycling', 17.4 + random.uniform(-.5, 1), work, home, 17.5, .25)]
        if wd >= 5 and random.random() < mix['ride'] * season:
            a, b = random.choice(rides)
            legs += [('Cycling', 9.0 + random.uniform(0, 1.5), home, a, 21, .3), ('Cycling', None, a, b, 21, .3), ('Cycling', None, b, home, 21, .3)]
        if random.random() < mix['run']:
            a, b = random.choice(runs)
            h = random.choice([6.5, 18.5]) + random.uniform(0, 1)
            legs += [('Running', h, home, a, 10.5, .2), ('Running', None, a, b, 10.5, .2), ('Running', None, b, home, 10.5, .2)]
        if random.random() < mix['walk']:
            a = random.choice(walks)
            legs += [('Walking', random.choice([12.3, 19.0]) + random.uniform(0, 1), home, a, 4.8, .5), ('Walking', None, a, home, 4.8, .5)]
        t_prev = None
        for typ, hour, a, b, speed, wob in legs:
            if hour is None:
                if t_prev is None:
                    continue
                hour = t_prev + .02
            if a == b:
                continue
            pts = trace(variant(a, b, wob))
            km = length_km(pts)
            if km < .3:
                continue
            speed *= random.uniform(.9, 1.1)
            dur = km / speed * 60
            t_prev = hour + dur / 60
            start_s = dt.datetime(day.year, day.month, day.day, min(int(hour), 23), int((hour % 1) * 60)).strftime('%Y-%m-%dT%H:%M:%S')
            lat, lon = ll(*pts[0])
            recs.append(dict(type=typ, start=start_s, off=60, dur=round(dur, 2), km=round(km, 3), gpsKm=round(km, 3),
                             gain=round(km * random.uniform(2, 7)), kcal=round(dur * (9 if typ != 'Walking' else 4.5)), src='Apple Watch',
                             lat=round(lat, 4), lon=round(lon, 4), p=encode(pts, speed)))
        day += dt.timedelta(days=1)
    return dict(id=name.lower().split()[0], name=name, workouts=recs)


def main():
    alex = person('Alex (demo)', (-1500, -600), (1300, 900), dt.date(2023, 1, 1), dt.date(2026, 9, 30),
                  dict(commute=.45, ride=.4, run=.1, walk=.15), 1)
    sam = person('Sam (demo)', (900, -1100), (-900, 700), dt.date(2024, 6, 1), dt.date(2026, 9, 30),
                 dict(commute=.12, ride=.2, run=.35, walk=.3), 2)
    data = json.dumps(dict(datasets=[alex, sam], name='demo'), separators=(',', ':'))
    html = open(os.path.join(ROOT, 'index.html'), encoding='utf-8').read().replace('/*__DATA__*/null', data)
    tab = sys.argv[sys.argv.index('--tab') + 1] if '--tab' in sys.argv else 'filters'
    # fixed, screenshot-friendly state; this is a throwaway file, not the app
    prelude = ("<script>try{Object.defineProperty(window,'indexedDB',{value:null,configurable:true});}catch(e){}try{localStorage.clear();"
               "localStorage.setItem('wa.theme','\"dark\"');localStorage.setItem('wa.base','\"dark\"');"
               "localStorage.setItem('wa.heatR','3');localStorage.setItem('wa.heatVer','2');localStorage.setItem('wa.lineW','1.5');"
               "}catch(e){}</script>")
    html = html.replace('<script src="https://unpkg.com/leaflet', prelude + '<script src="https://unpkg.com/leaflet', 1)
    if tab == 'compare':
        html = html.replace('</body>', "<script>setTimeout(function(){document.querySelector('[data-tab=compare]').click();},1500);</script></body>")
    os.makedirs(os.path.join(ROOT, 'dist'), exist_ok=True)
    out = os.path.join(ROOT, 'dist', 'demo.html' if tab == 'filters' else f'demo_{tab}.html')
    open(out, 'w', encoding='utf-8').write(html)
    n = sum(len(d['workouts']) for d in (alex, sam))
    print(f'{n} synthetic routes ({len(alex["workouts"])} + {len(sam["workouts"])}) -> {out} ({os.path.getsize(out)/1e6:.1f} MB)')


main()
