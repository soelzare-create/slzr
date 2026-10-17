#!/usr/bin/env python3
"""Radio link planner: distance, azimuth, terrain profile, Fresnel clearance, mast height,
link budget and radio shortlist for point-to-point and point-to-multipoint links.

Usage:
    python3 link_calc.py project.json -o results.json [--offline] [--catalog ../references/radios.json]

project.json (minimal):
{
  "project": "Office to warehouse",
  "freq_ghz": 5.8,                 # centre frequency used for Fresnel / FSPL
  "required_mbps": 100,            # real (TCP) throughput the customer needs
  "sites": [
    {"id": "A", "name": "Office",    "loc": "https://maps.google.com/?q=31.32,48.62", "building_m": 12},
    {"id": "B", "name": "Warehouse", "loc": "31.30, 48.70", "building_m": 6, "existing_mast_m": 3}
  ]
}
Optional keys: links [{"a":"A","b":"B"}], hub "A", clearance (0.6), k (1.333), clutter_m (0),
max_mast_m (36), mast_step_m (1), max_width_mhz (80), fade_margin_db (auto), obstacles
[{"link":"A-B","at_km":1.2,"height_m":25,"name":"Tower"} or {"loc":"lat,lon","height_m":25}],
per-site "ground_m" (overrides DEM), "max_mast_m", "fixed_mast_m".

Elevation sources (tried in order): OpenTopoData SRTM 30 m, Open-Meteo (Copernicus 90 m), Open-Elevation.
--offline uses per-site ground_m (or 0) and a straight line between them, so the output is
clearly marked as "no terrain data".
"""
import argparse, json, math, re, sys, time, urllib.parse, urllib.request
from pathlib import Path

R_EARTH = 6371000.0
HERE = Path(__file__).resolve().parent

# ---------------------------------------------------------------- location parsing
_NUM = r'(-?\d{1,3}(?:\.\d+)?)'
_PATTERNS = [
    re.compile(r'!3d' + _NUM + r'!4d' + _NUM),              # place pin inside data=
    re.compile(r'[?&](?:q|query|ll|destination|daddr|center)=' + _NUM + r'\s*,\s*\+?' + _NUM),
    re.compile(r'@' + _NUM + r',' + _NUM),                  # map viewport
    re.compile(r'^\s*' + _NUM + r'\s*[, ]\s*' + _NUM + r'\s*$'),
]


# ---------------------------------------------------------------- Plus Codes (Open Location Code)
# Google "search" links often carry a Plus Code such as 7PWC+2CC plus a viewport "@lat,lon" that is NOT the pin.
# The Plus Code is the real place, so it wins over the viewport.
_OLC = '23456789CFGHJMPQRVWX'
_OLC_RE = re.compile(r'(?<![0-9A-Z])([23456789CFGHJMPQRVWX]{2,8}\+[23456789CFGHJMPQRVWX]{0,7})(?![0-9A-Z])')


def _olc_decode(code):
    code = code.replace('+', '').upper()
    lat, lng, res = -90.0, -180.0, 20.0
    for i in range(0, min(len(code), 10), 2):
        lat += _OLC.index(code[i]) * res
        if i + 1 < len(code):
            lng += _OLC.index(code[i + 1]) * res
        last_lat, last_lng = res, res
        res /= 20
    rl, rg = last_lat, last_lng
    for ch in code[10:]:
        rl, rg = rl / 5, rg / 4
        v = _OLC.index(ch)
        lat += (v // 4) * rl
        lng += (v % 4) * rg
    return lat + rl / 2, lng + rg / 2


def _olc_encode4(lat, lng):
    lat, lng = lat + 90, lng + 180
    return _OLC[int(lat // 20)] + _OLC[int(lng // 20)] + _OLC[int(lat % 20)] + _OLC[int(lng % 20)]


def plus_code(code, ref):
    """Decode a full or short Plus Code; short codes are recovered nearest to ref (lat, lon)."""
    code = code.upper()
    pad = 8 - code.index('+')
    if pad == 0:
        return _olc_decode(code)
    full = _olc_encode4(*ref)[:pad] + code
    lat, lng = _olc_decode(full)
    res = 20.0 ** (2 - pad / 2)
    if ref[0] + res / 2 < lat: lat -= res
    elif ref[0] - res / 2 > lat: lat += res
    if ref[1] + res / 2 < lng: lng -= res
    elif ref[1] - res / 2 > lng: lng += res
    return lat, lng


def _resolve_short(url):
    req = urllib.request.Request(url, method='GET', headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req, timeout=15) as r:
        return r.geturl()


def parse_location(text):
    """Return (lat, lon) from a Google Maps link, a geo: URI, or 'lat, lon'."""
    if isinstance(text, (list, tuple)):
        return float(text[0]), float(text[1])
    s = urllib.parse.unquote(str(text).strip()).replace('geo:', '')
    if re.search(r'(goo\.gl|maps\.app)', s):
        try:
            s = urllib.parse.unquote(_resolve_short(s))
        except Exception as e:
            raise ValueError(f'Short link could not be opened ({e}). Send the full link or "lat, lon".')
    pc = _OLC_RE.search(s.split('@')[0].upper())
    if pc:
        ref = None
        for p in _PATTERNS:
            m = p.search(s)
            if m:
                ref = (float(m.group(1)), float(m.group(2)))
                break
        if ref or len(pc.group(1).split('+')[0]) == 8:
            return plus_code(pc.group(1), ref or (0, 0))
    for p in _PATTERNS:
        m = p.search(s)
        if m:
            lat, lon = float(m.group(1)), float(m.group(2))
            if -90 <= lat <= 90 and -180 <= lon <= 180:
                return lat, lon
    raise ValueError(f'No coordinates found in: {text}')


# ---------------------------------------------------------------- geodesy
def haversine(a, b):
    p1, p2 = math.radians(a[0]), math.radians(b[0])
    dp, dl = p2 - p1, math.radians(b[1] - a[1])
    h = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * R_EARTH * math.asin(math.sqrt(h))


def bearing(a, b):
    p1, p2 = math.radians(a[0]), math.radians(b[0])
    dl = math.radians(b[1] - a[1])
    x = math.sin(dl) * math.cos(p2)
    y = math.cos(p1) * math.sin(p2) - math.sin(p1) * math.cos(p2) * math.cos(dl)
    return (math.degrees(math.atan2(x, y)) + 360) % 360


def interpolate(a, b, f):
    """Point at fraction f along the great circle a->b."""
    p1, l1, p2, l2 = map(math.radians, (a[0], a[1], b[0], b[1]))
    d = haversine(a, b) / R_EARTH
    if d == 0:
        return a
    A, B = math.sin((1 - f) * d) / math.sin(d), math.sin(f * d) / math.sin(d)
    x = A * math.cos(p1) * math.cos(l1) + B * math.cos(p2) * math.cos(l2)
    y = A * math.cos(p1) * math.sin(l1) + B * math.cos(p2) * math.sin(l2)
    z = A * math.sin(p1) + B * math.sin(p2)
    return math.degrees(math.atan2(z, math.hypot(x, y))), math.degrees(math.atan2(y, x))


def project_on_path(a, b, p):
    """Distance (m) along a->b of the point nearest to p, and its cross-track offset (m)."""
    d13, t13, t12 = haversine(a, p) / R_EARTH, math.radians(bearing(a, p)), math.radians(bearing(a, b))
    xt = math.asin(max(-1, min(1, math.sin(d13) * math.sin(t13 - t12))))
    at = math.acos(max(-1, min(1, math.cos(d13) / max(math.cos(xt), 1e-12))))
    return at * R_EARTH, abs(xt) * R_EARTH


COMPASS_FA = ['شمال', 'شمال‌شرق', 'شرق', 'جنوب‌شرق', 'جنوب', 'جنوب‌غرب', 'غرب', 'شمال‌غرب']


def compass(deg):
    return COMPASS_FA[int((deg + 22.5) // 45) % 8]


# ---------------------------------------------------------------- elevation
def _get_json(url, data=None):
    req = urllib.request.Request(url, data=data, headers={'User-Agent': 'p2p-radio-skill/1.0', 'Content-Type': 'application/json'})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode())


def _opentopodata(pts):
    out = []
    for i in range(0, len(pts), 100):
        chunk = pts[i:i + 100]
        locs = '|'.join(f'{p[0]:.6f},{p[1]:.6f}' for p in chunk)
        j = _get_json('https://api.opentopodata.org/v1/srtm30m?locations=' + urllib.parse.quote(locs, safe='|,.-'))
        out += [r['elevation'] for r in j['results']]
        if i + 100 < len(pts):
            time.sleep(1.1)  # public API: 1 request per second
    return out


def _openmeteo(pts):
    out = []
    for i in range(0, len(pts), 100):
        chunk = pts[i:i + 100]
        lat = ','.join(f'{p[0]:.6f}' for p in chunk)
        lon = ','.join(f'{p[1]:.6f}' for p in chunk)
        out += _get_json(f'https://api.open-meteo.com/v1/elevation?latitude={lat}&longitude={lon}')['elevation']
    return out


def _openelevation(pts):
    body = json.dumps({'locations': [{'latitude': p[0], 'longitude': p[1]} for p in pts]}).encode()
    return [r['elevation'] for r in _get_json('https://api.open-elevation.com/api/v1/lookup', body)['results']]


SOURCES = [('OpenTopoData SRTM 30 m', _opentopodata), ('Open-Meteo Copernicus 90 m', _openmeteo), ('Open-Elevation SRTM', _openelevation)]


def elevations(pts, offline=False):
    if offline:
        return None, 'offline (no terrain data)'
    errors = []
    for name, fn in SOURCES:
        try:
            e = fn(pts)
            if len(e) == len(pts) and all(v is not None for v in e):
                return [float(v) for v in e], name
            errors.append(f'{name}: incomplete')
        except Exception as ex:
            errors.append(f'{name}: {ex}')
    print('WARNING elevation lookup failed -> ' + ' | '.join(errors), file=sys.stderr)
    return None, 'unavailable (' + '; '.join(errors)[:200] + ')'


# ---------------------------------------------------------------- radio maths
SENS_20 = [-95, -93, -91, -88, -85, -81, -79, -77, -72, -70]       # typical 2x2 802.11ac, 20 MHz, dBm
TX_BACKOFF = [0, 0, 0, 0, 0, 0, 2, 2, 4, 5]                        # power drop at high MCS
PHY = {20: [13, 26, 39, 52, 78, 104, 117, 130, 156, 173],
       40: [27, 54, 81, 108, 162, 216, 243, 270, 324, 360],
       80: [58.5, 117, 175.5, 234, 351, 468, 526.5, 585, 702, 780],
       100: [73, 146, 219, 292, 438, 585, 658, 731, 877, 975]}
WIDTH_PENALTY = {20: 0, 40: 3, 80: 6, 100: 7}
MODULATION = ['BPSK 1/2', 'QPSK 1/2', 'QPSK 3/4', '16QAM 1/2', '16QAM 3/4', '64QAM 2/3', '64QAM 3/4', '64QAM 5/6', '256QAM 3/4', '256QAM 5/6']
EFFICIENCY = 0.6     # TDMA protocol overhead (Nv2 / airMAX / Pharos MAXtream) -> real TCP throughput


def fspl(d_m, f_ghz):
    return 92.45 + 20 * math.log10(f_ghz) + 20 * math.log10(max(d_m, 1) / 1000)


def fresnel_r(d1, d2, f_ghz):
    D = d1 + d2
    return 17.32 * math.sqrt((d1 / 1000) * (d2 / 1000) / (f_ghz * (D / 1000))) if D > 0 and d1 > 0 and d2 > 0 else 0.0


def bulge(d1, d2, k):
    return d1 * d2 / (2 * k * R_EARTH)


def default_margin(d_m):
    km = d_m / 1000
    return 15 if km < 5 else 20 if km < 15 else 25


def budget(radio_a, radio_b, d_m, f_ghz, margin_target, max_width, required):
    """Best MCS/width for a pair; returns dict or None."""
    loss = fspl(d_m, f_ghz) + radio_a.get('cable_loss_db', 0) + radio_b.get('cable_loss_db', 0) + 2  # 2 dB alignment/radome
    widths = [w for w in (100, 80, 40, 20) if w <= min(radio_a.get('max_width', 80), radio_b.get('max_width', 80), max_width)]
    cap = min(radio_a['real_mbps'], radio_b['real_mbps'])
    configs = []
    for w in widths:
        for mcs in range(min(radio_a.get('max_mcs', 9), radio_b.get('max_mcs', 9)), -1, -1):
            tx = radio_a['tx_dbm'] - TX_BACKOFF[mcs]
            rx = tx + radio_a['gain_dbi'] + radio_b['gain_dbi'] - loss
            sens = SENS_20[mcs] + WIDTH_PENALTY[w]
            if rx - sens >= margin_target:
                configs.append({'width_mhz': w, 'mcs': mcs, 'modulation': MODULATION[mcs], 'rx_dbm': round(rx, 1), 'sens_dbm': sens,
                                'margin_db': round(rx - sens, 1), 'phy_mbps': PHY[w][mcs], 'real_mbps': round(min(PHY[w][mcs] * EFFICIENCY, cap)),
                                'tx_dbm': tx, 'eirp_dbm': round(tx + radio_a['gain_dbi'] - radio_a.get('cable_loss_db', 0), 1),
                                'loss_db': round(loss, 1), 'fspl_db': round(fspl(d_m, f_ghz), 1)})
    if not configs:
        return None
    top = max(configs, key=lambda c: (c['real_mbps'], c['margin_db']))
    # recommended setting: the narrowest channel and the lowest modulation that already meet the need
    # (less noise, the most fade margin); the capacity headroom is reported separately as max_mbps
    fits = [c for c in configs if c['real_mbps'] >= required]
    rec = dict(min(fits, key=lambda c: (c['width_mhz'], -c['margin_db'])) if fits else top)
    rec.update({'max_mbps': top['real_mbps'], 'max_width_mhz': top['width_mhz'], 'max_modulation': top['modulation'], 'max_margin_db': top['margin_db']})
    return rec


# ---------------------------------------------------------------- link analysis
def analyse_link(A, B, cfg, catalog, offline, ptmp=False):
    a, b = A['latlon'], B['latlon']
    D = haversine(a, b)
    f = cfg['freq_ghz']
    k = cfg.get('k', 4 / 3)
    clr = cfg.get('clearance', 0.6)
    clutter = cfg.get('clutter_m', 0)
    n = int(min(max(D / 25, 30), 300))
    pts = [interpolate(a, b, i / n) for i in range(n + 1)]
    elev, src = elevations(pts, offline)
    if elev is None:
        ga, gb = A.get('ground_m') or 0, B.get('ground_m') or 0
        elev = [ga + (gb - ga) * i / n for i in range(n + 1)]
        terrain_ok = False
    else:
        terrain_ok = True
        if A.get('ground_m') is not None: elev[0] = A['ground_m']
        if B.get('ground_m') is not None: elev[-1] = B['ground_m']
    dist = [D * i / n for i in range(n + 1)]

    # obstacles: explicit ones projected on the path, plus uniform clutter inside the path
    obst = [0.0] * (n + 1)
    named = []
    lid = {f"{A['id']}-{B['id']}", f"{B['id']}-{A['id']}"}
    for o in cfg.get('obstacles', []):
        if 'link' in o and o['link'] not in lid:
            continue
        if 'loc' in o:
            at, xt = project_on_path(a, b, parse_location(o['loc']))
            if xt > 150 or not (0 < at < D):
                continue
        else:
            at = o['at_km'] * 1000
        i = min(range(n + 1), key=lambda j: abs(dist[j] - at))
        width = max(1, int(o.get('width_m', 30) / (D / n) / 2))
        for j in range(max(1, i - width), min(n, i + width) + 1):
            obst[j] = max(obst[j], o['height_m'])
        named.append({'name': o.get('name', 'مانع'), 'at_m': round(at), 'height_m': o['height_m']})
    for j in range(1, n):
        obst[j] = max(obst[j], clutter)

    bul = [bulge(d, D - d, k) for d in dist]
    fr = [fresnel_r(d, D - d, f) for d in dist]
    top = [elev[i] + obst[i] + bul[i] for i in range(n + 1)]

    baseA = elev[0] + A.get('building_m', 0)
    baseB = elev[-1] + B.get('building_m', 0)

    def worst(hA, hB, frac):
        """min over the path of (line - obstacle - frac*F1); >=0 means clear."""
        w, at = 1e9, 0
        for i in range(1, n):
            line = hA + (hB - hA) * dist[i] / D
            v = line - top[i] - frac * fr[i]
            if v < w:
                w, at = v, i
        return w, at

    def solve(frac):
        step = cfg.get('mast_step_m', 1)
        fa, fb = A.get('fixed_mast_m'), B.get('fixed_mast_m')
        ra = [fa] if fa is not None else [x * step for x in range(int(A.get('max_mast_m', cfg.get('max_mast_m', 36)) / step) + 1)]
        rb = [fb] if fb is not None else [x * step for x in range(int(B.get('max_mast_m', cfg.get('max_mast_m', 36)) / step) + 1)]
        best = None
        for ma in ra:
            for mb in rb:
                w, _ = worst(baseA + ma, baseB + mb, frac)
                if w >= 0:
                    key = (max(ma, mb), ma + mb)
                    if best is None or key < best[0]:
                        best = (key, ma, mb)
                    break
        return None if best is None else {'mast_a_m': best[1], 'mast_b_m': best[2]}

    # existing masts count toward the solution: a site with a 6 m mast needs only (required - 6) extra
    exA, exB = A.get('existing_mast_m', 0), B.get('existing_mast_m', 0)
    sol = solve(clr)
    sol_los = solve(0.0)
    sol_full = solve(1.0)

    res = {'a': A['id'], 'b': B['id'], 'distance_m': round(D, 1), 'azimuth_ab': round(bearing(a, b), 1), 'azimuth_ba': round(bearing(b, a), 1),
           'compass_ab': compass(bearing(a, b)), 'compass_ba': compass(bearing(b, a)),
           'ground_a_m': round(elev[0], 1), 'ground_b_m': round(elev[-1], 1), 'ground_diff_m': round(elev[-1] - elev[0], 1),
           'terrain_source': src, 'terrain_ok': terrain_ok, 'max_bulge_m': round(max(bul), 2), 'max_fresnel_m': round(max(fr), 2),
           'freq_ghz': f, 'clearance_target': clr, 'k': round(k, 3), 'clutter_m': clutter, 'obstacles': named,
           'feasible': sol is not None}
    if sol:
        ma, mb = sol['mast_a_m'], sol['mast_b_m']
        hA, hB = baseA + ma, baseB + mb
        w, wi = worst(hA, hB, clr)
        clear_pct = min(((hA + (hB - hA) * dist[i] / D) - top[i]) / fr[i] * 100 if fr[i] else 999 for i in range(1, n))
        tilt = math.degrees(math.atan2(hB - hA, D)) - math.degrees(D / (2 * k * R_EARTH))
        tilt_b = math.degrees(math.atan2(hA - hB, D)) - math.degrees(D / (2 * k * R_EARTH))
        res.update({
            'mast_a_m': ma, 'mast_b_m': mb,
            'new_mast_a_m': max(0, ma - exA), 'new_mast_b_m': max(0, mb - exB),
            'antenna_agl_a_m': round(A.get('building_m', 0) + ma, 1), 'antenna_agl_b_m': round(B.get('building_m', 0) + mb, 1),
            'antenna_asl_a_m': round(hA, 1), 'antenna_asl_b_m': round(hB, 1),
            'tilt_a_deg': round(tilt, 2), 'tilt_b_deg': round(tilt_b, 2),
            'min_clearance_pct': round(clear_pct), 'critical_point_m': round(dist[wi]),
            'mast_los_only': sol_los, 'mast_full_fresnel': sol_full,
        })
    res['profile'] = {'d': [round(x, 1) for x in dist], 'ground': [round(x, 1) for x in elev], 'obstacle': [round(x, 1) for x in obst],
                      'bulge': [round(x, 2) for x in bul], 'fresnel': [round(x, 2) for x in fr],
                      'base_a': round(baseA, 1), 'base_b': round(baseB, 1)}

    # ------------------------------------------------ radio shortlist for this link
    margin = cfg.get('fade_margin_db') or default_margin(D)
    req = cfg.get('required_mbps', 50)
    opts = []
    if ptmp:
        # A is a multipoint base (sector AP); B is one client of the same ecosystem.
        for ap in catalog:
            if 'ap' not in ap['roles'] or D > ap['range_km'] * 1000:
                continue
            best = None
            for c in (c for c in catalog if c['ecosystem'] == ap['ecosystem'] and 'cpe' in c['roles']):
                bud = budget(ap, c, D, f, margin, cfg.get('max_width_mhz', 80), req)
                # the base is bought for capacity: take the client that unlocks the most of it, cheapest on a tie
                if bud and bud['max_mbps'] >= req and (best is None or (bud['max_mbps'], -c['price_rank']) > (best[0]['max_mbps'], -best[1]['price_rank'])):
                    best = (bud, c)
            if best:
                bud, c = best
                bud.update({'id': ap['id'], 'cpe': c['id'], 'band': ap['band'], 'meets': True, 'grx_dbi': c['gain_dbi']})
                opts.append(bud)
        res['ptmp'] = True
        res['fade_margin_target_db'] = margin
        res['radio_options'] = opts
        res['picks'] = pick_tiers(opts, {m['id']: m for m in catalog}, req, margin)
        return res
    for m in catalog:
        if 'ptp' not in m['roles']:
            continue
        if m['band'].startswith('60'):
            if D <= m['range_km'] * 1000:
                opts.append({'id': m['id'], 'band': m['band'], 'real_mbps': m['real_mbps'], 'max_mbps': m['real_mbps'], 'margin_db': None, 'width_mhz': 2160,
                             'meets': m['real_mbps'] >= req, 'note': 'within rated 60 GHz range'})
            continue
        if D > m['range_km'] * 1000 * 1.2:
            continue
        bud = budget(m, m, D, f, margin, cfg.get('max_width_mhz', 80), req)
        if bud:
            bud.update({'id': m['id'], 'band': m['band'], 'meets': bud['max_mbps'] >= req})
            opts.append(bud)
    res['fade_margin_target_db'] = margin
    res['radio_options'] = opts
    res['picks'] = pick_tiers(opts, {m['id']: m for m in catalog}, req, margin)
    return res


def pick_tiers(opts, cat, req, margin):
    ok = [o for o in opts if o['meets']]
    if not ok:
        ok = sorted(opts, key=lambda o: -o['max_mbps'])[:3]
    if not ok:
        return {}
    pr = lambda o: cat[o['id']]['price_rank']
    eco = min(ok, key=lambda o: (pr(o), -(o['margin_db'] or 99)))
    # balanced: best throughput per cost among the rest, with healthy margin
    rest = [o for o in ok if o is not eco] or ok
    roomy = [o for o in rest if o['margin_db'] is None or o['margin_db'] >= margin + 3] or rest
    bal = min(roomy, key=lambda o: (pr(o) - min(o['max_mbps'], 1000) / 150, -(o['margin_db'] or 99)))
    # pro: most capacity and margin, regardless of cost
    rest2 = [o for o in rest if o is not bal] or rest
    pro = max(rest2, key=lambda o: (o['max_mbps'] >= req * 2, (o['margin_db'] or 40) + o['max_mbps'] / 50, -pr(o)))
    return {'economy': eco['id'], 'balanced': bal['id'], 'pro': pro['id']}


def analyse_star(hub, clients, cfg, catalog, links):
    """PtMP: is one sector at the hub enough? which AP model fits?"""
    az = sorted(l['azimuth_ab'] if l['a'] == hub['id'] else l['azimuth_ba'] for l in links)
    if not az:
        return None
    gaps = [(az[(i + 1) % len(az)] - az[i]) % 360 for i in range(len(az))]
    spread = 360 - max(gaps) if len(az) > 1 else 0
    far = max(l['distance_m'] for l in links)
    sectors = 1 if spread <= 80 else 1 if spread <= 110 else 2 if spread <= 220 else 3
    beam = 90 if spread <= 80 else 120
    req = cfg.get('required_mbps', 50)
    aps = []
    for m in catalog:
        if 'ap' not in m['roles'] or far > m['range_km'] * 1000:
            continue
        cpe = [c for c in catalog if c['ecosystem'] == m['ecosystem'] and 'cpe' in c['roles']]
        if not cpe:
            continue
        c = sorted(cpe, key=lambda c: c['price_rank'])
        best = None
        for cm in c:
            bud = budget(m, cm, far, cfg['freq_ghz'], default_margin(far), cfg.get('max_width_mhz', 80), req)
            if bud:
                best = (cm, bud)
                break
        if best:
            aps.append({'ap': m['id'], 'cpe': best[0]['id'], 'worst_client': best[1], 'sector_capacity_mbps': m['real_mbps']})
    return {'hub': hub['id'], 'client_azimuths': [round(x, 1) for x in az], 'spread_deg': round(spread, 1), 'sectors_needed': sectors,
            'sector_beam_deg': beam, 'farthest_m': round(far), 'ap_options': aps,
            'advice': 'ptp' if len(clients) <= 2 or req * len(clients) > 250 else 'ptmp'}


def suggest_hub(sites, cfg):
    best = None
    for h in sites:
        ds = [haversine(h['latlon'], s['latlon']) for s in sites if s is not h]
        key = (max(ds), sum(ds))
        if best is None or key < best[0]:
            best = (key, h['id'])
    return best[1]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('project')
    ap.add_argument('-o', '--out', default='results.json')
    ap.add_argument('--catalog', default=str(HERE.parent / 'references' / 'radios.json'))
    ap.add_argument('--offline', action='store_true', help='skip elevation APIs (flat earth between ground_m values)')
    args = ap.parse_args()
    cfg = json.loads(Path(args.project).read_text(encoding='utf-8'))
    catalog = json.loads(Path(args.catalog).read_text(encoding='utf-8'))['models']
    cfg.setdefault('freq_ghz', 5.8)
    sites = cfg['sites']
    for s in sites:
        s['latlon'] = parse_location(s['loc'])
    by = {s['id']: s for s in sites}

    pairs = [(l['a'], l['b']) for l in cfg.get('links', [])]
    existing = {(l['a'], l['b']) for l in cfg.get('links', []) if l.get('existing')}   # already built; drawn for context only
    ptmp = {(l['a'], l['b']) for l in cfg.get('links', []) if l.get('ptmp')}          # a = multipoint base station, b = client
    hub = cfg.get('hub')
    if not pairs:
        if len(sites) == 2:
            pairs = [(sites[0]['id'], sites[1]['id'])]
        else:
            hub = hub or suggest_hub(sites, cfg)
            pairs = [(hub, s['id']) for s in sites if s['id'] != hub]

    matrix = [{'a': x['id'], 'b': y['id'], 'distance_m': round(haversine(x['latlon'], y['latlon']))}
              for i, x in enumerate(sites) for y in sites[i + 1:]]
    links = []
    for a, b in pairs:
        print(f'analysing {a} -> {b} ...', file=sys.stderr)
        links.append(analyse_link(by[a], by[b], cfg, catalog, args.offline, (a, b) in ptmp))
        links[-1]['existing'] = (a, b) in existing or (b, a) in existing
    star = None
    if hub and len(pairs) > 1:
        star = analyse_star(by[hub], [p[1] for p in pairs], cfg, catalog, links)

    out = {'project': cfg.get('project', 'Radio link'), 'generated': time.strftime('%Y-%m-%d'), 'freq_ghz': cfg['freq_ghz'],
           'required_mbps': cfg.get('required_mbps', 50), 'clearance_target': cfg.get('clearance', 0.6),
           'sites': [{k: v for k, v in s.items()} for s in sites], 'hub': hub, 'pair_matrix': matrix, 'links': links, 'star': star,
           'catalog': {m['id']: m for m in catalog}}
    for s in out['sites']:
        s['lat'], s['lon'] = s.pop('latlon')
    Path(args.out).write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding='utf-8')

    # short human summary on stdout
    for l in links:
        print(f"\n{l['a']} -> {l['b']}: {l['distance_m']/1000:.2f} km, azimuth {l['azimuth_ab']}° / {l['azimuth_ba']}°, "
              f"ground {l['ground_a_m']} / {l['ground_b_m']} m (diff {l['ground_diff_m']} m) [{l['terrain_source']}]")
        if l['feasible']:
            print(f"  masts: {l['a']} {l['mast_a_m']} m, {l['b']} {l['mast_b_m']} m above roof -> antenna {l['antenna_agl_a_m']} / {l['antenna_agl_b_m']} m AGL; "
                  f"clearance {l['min_clearance_pct']}% F1; tilt {l['tilt_a_deg']}° / {l['tilt_b_deg']}°")
        else:
            print('  NOT FEASIBLE within max mast height: needs a relay site or taller structure')
        print(f"  picks: {l['picks']}")
    if star:
        print(f"\nhub {star['hub']}: spread {star['spread_deg']}°, sectors {star['sectors_needed']}x{star['sector_beam_deg']}°, advice {star['advice']}")
    print(f'\nwrote {args.out}')


if __name__ == '__main__':
    main()
