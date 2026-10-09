#!/usr/bin/env python3
"""Build workout_dashboard.html from an Apple Health export zip.

Usage:  python build.py [path/to/export.zip] [output.html]
        python build.py --empty            (no data baked in: a shareable viewer where each user loads their own files)

Reads Workout metadata from export.xml and the GPX files in workout-routes/
directly from the zip (nothing is extracted), simplifies the routes and bakes
everything into one self-contained HTML file next to this script.
"""
import sys, io, os, re, json, math, zipfile
import datetime as dt
import xml.etree.ElementTree as ET

HERE = os.path.dirname(os.path.abspath(__file__))
ARGS = [a for a in sys.argv[1:] if not a.startswith('--')]
EMPTY = '--empty' in sys.argv
ZIP = ARGS[0] if ARGS else os.path.join(HERE, '..', 'data', 'health', 'export2.zip')
OUT = ARGS[1] if len(ARGS) > 1 else os.path.join(HERE, 'workout_atlas_empty.html' if EMPTY else 'workout_dashboard.html')
SIMPLIFY_M = 2.5          # route simplification tolerance in metres


def hav(a, b, c, d):
    p1, p2 = math.radians(a), math.radians(c)
    x = math.sin((p2 - p1) / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(math.radians(d - b) / 2) ** 2
    return 12742000 * math.asin(math.sqrt(x))


def rdp(pts, eps):
    """Douglas-Peucker on (lat, lon, ...) tuples; returns indices to keep."""
    n = len(pts)
    if n < 3:
        return list(range(n))
    kx = 111320 * math.cos(math.radians(pts[0][0])); ky = 110540
    xy = [(p[1] * kx, p[0] * ky) for p in pts]
    keep = [False] * n; keep[0] = keep[-1] = True
    st = [(0, n - 1)]
    while st:
        i, j = st.pop()
        if j <= i + 1:
            continue
        x1, y1 = xy[i]; x2, y2 = xy[j]; dx, dy = x2 - x1, y2 - y1; L = dx * dx + dy * dy
        md = -1; mi = -1
        for k in range(i + 1, j):
            x, y = xy[k]
            if L == 0:
                dd = math.hypot(x - x1, y - y1)
            else:
                t = max(0, min(1, ((x - x1) * dx + (y - y1) * dy) / L))
                dd = math.hypot(x - (x1 + t * dx), y - (y1 + t * dy))
            if dd > md:
                md, mi = dd, k
        if md > eps:
            keep[mi] = True; st.append((i, mi)); st.append((mi, j))
    return [i for i in range(n) if keep[i]]


def read_workouts(z):
    out = []; buf = None
    with z.open('apple_health_export/export.xml') as f:
        for raw in io.TextIOWrapper(f, encoding='utf-8', newline=None):
            s = raw.strip()
            if buf is None:
                if s.startswith('<Workout '):
                    if s.endswith('/>'):
                        out.append(ET.fromstring(s))
                    else:
                        buf = [s]
            else:
                buf.append(s)
                if s.startswith('</Workout>'):
                    out.append(ET.fromstring('\n'.join(buf))); buf = None
    return out


PT = re.compile(r'<trkpt lon="([-\d.]+)" lat="([-\d.]+)"><ele>([-\d.]+)</ele><time>([^<]+)</time>')
UNIT_KM = {'km': 1, 'm': 0.001, 'mi': 1.609344, 'yd': 0.0009144}


def ts(s):
    return dt.datetime.strptime(s, '%Y-%m-%dT%H:%M:%SZ').replace(tzinfo=dt.timezone.utc).timestamp()


def main():
    if EMPTY:
        html = open(os.path.join(HERE, 'template.html'), encoding='utf-8').read()
        open(OUT, 'w', encoding='utf-8').write(html)
        print(f'empty viewer -> {OUT}')
        return
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    recs = []
    with zipfile.ZipFile(ZIP) as z:
        names = set(z.namelist())
        workouts = read_workouts(z)
        print(f'{len(workouts)} workouts in export')
        for w in workouts:
            refs = [r.find('FileReference').get('path') for r in w.findall('WorkoutRoute')
                    if r.find('FileReference') is not None]
            if not refs:
                continue
            gpx = 'apple_health_export' + refs[0]
            if gpx not in names:
                continue
            raw = [(float(a), float(b), float(c), ts(t)) for b, a, c, t in PT.findall(z.read(gpx).decode('utf-8'))]
            if len(raw) < 2:
                continue
            dist = sum(hav(raw[i-1][0], raw[i-1][1], raw[i][0], raw[i][1]) for i in range(1, len(raw)))
            ele = [p[2] for p in raw]; k = 5
            sm = [sum(ele[max(0, i-k):i+k+1]) / len(ele[max(0, i-k):i+k+1]) for i in range(len(ele))]
            gain = sum(max(0, sm[i] - sm[i-1]) for i in range(1, len(sm)))
            kp = [raw[i] for i in rdp(raw, SIMPLIFY_M)]
            t0 = kp[0][3]
            la = [round(p[0] * 1e5) for p in kp]; lo = [round(p[1] * 1e5) for p in kp]
            tt = [round(p[3] - t0) for p in kp]
            flat = [la[0], lo[0], tt[0]]
            for i in range(1, len(kp)):
                flat += [la[i]-la[i-1], lo[i]-lo[i-1], tt[i]-tt[i-1]]
            stats = {s.get('type').replace('HKQuantityTypeIdentifier', ''): s for s in w.findall('WorkoutStatistics')}
            km = None
            for key in ('DistanceCycling', 'DistanceWalkingRunning', 'DistanceSwimming'):
                if key in stats:
                    km = float(stats[key].get('sum')) * UNIT_KM.get(stats[key].get('unit'), 1); break
            if km is None:
                km = dist / 1000
            kc = stats.get('ActiveEnergyBurned')
            sd = w.get('startDate'); off = sd[20:]
            recs.append(dict(
                type=w.get('workoutActivityType').replace('HKWorkoutActivityType', ''),
                start=sd[:19], off=(1 if off[0] == '+' else -1) * (int(off[1:3]) * 60 + int(off[3:5])),
                dur=round(float(w.get('duration')), 2), km=round(km, 3), gpsKm=round(dist / 1000, 3),
                gain=round(gain), kcal=round(float(kc.get('sum'))) if kc is not None else None,
                src='Runkeeper' if 'Runkeeper' in (w.get('sourceName') or '') else 'Apple Watch',
                lat=raw[0][0], lon=raw[0][1], p=flat))
    recs.sort(key=lambda r: r['start'])

    for r in recs:
        r['lat'] = round(r['lat'], 4); r['lon'] = round(r['lon'], 4)

    data = json.dumps(dict(workouts=recs, name='Apple Health export', built=dt.date.today().isoformat()),
                      separators=(',', ':'), ensure_ascii=False).replace('</', '<\\/')
    html = open(os.path.join(HERE, 'template.html'), encoding='utf-8').read().replace('/*__DATA__*/null', data)
    open(OUT, 'w', encoding='utf-8').write(html)
    print(f'{len(recs)} routes -> {OUT} ({os.path.getsize(OUT)/1e6:.2f} MB)')


main()
