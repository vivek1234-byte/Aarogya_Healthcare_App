"""
Finds government health facilities (district / sub-district hospitals, CHCs, PHCs,
sub-centres, medical colleges) near a location using OpenStreetMap.
Tries the Overpass API first and falls back to Nominatim search, which is reachable
on networks that block Overpass.
"""

import json
import math
import re
import threading
import time
import urllib.parse
import urllib.request

from app.portal import config

OVERPASS_MIRRORS = [
    'https://overpass-api.de/api/interpreter',
    'https://overpass.private.coffee/api/interpreter',
]
NOMINATIM_URL = 'https://nominatim.openstreetmap.org/search'
NOMINATIM_QUERIES = ['hospital', 'health centre', 'district hospital']
OVERPASS_RETRY_SECONDS = 3600

GOVT_NAME = re.compile(
    r'(primary health|community health|\bphc\b|\bchc\b|sub[\s-]?cent(re|er)|health\s*(and|&)\s*wellness|\bhwc\b|'
    r'district (women\'?s? )?hospital|\bdistrict\b.*hospital|civil hospital|sub[\s-]?divisional|government|\bgovt\.?\b|'
    r'sarkari|rajkiya|\baiims\b|medical college|\besi\b|\besic\b|railway hospital|state hospital|referral hospital|'
    r'सरकारी|राजकीय|जिला|प्राथमिक स्वास्थ्य|सामुदायिक स्वास्थ्य|সরকারি|সদর হাসপাতাল|शासकीय|जिल्हा|ప్రభుత్వ|ప్రాథమిక ఆరోగ్య)',
    re.IGNORECASE)
PRIVATE_NAME = re.compile(r'(private|pvt\.?|nursing home|multi ?speciality|super ?speciality|clinic & diagnostic)', re.IGNORECASE)

_cache = {}
_cache_lock = threading.Lock()
_nominatim_lock = threading.Lock()
_last_nominatim = [0.0]
_overpass_down_until = [0.0]
CACHE_SECONDS = 24 * 3600


def _get_json(url, data=None, timeout=12):
    req = urllib.request.Request(url, data=data, headers={'User-Agent': config.OSM_USER_AGENT, 'Accept': 'application/json'})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode('utf-8'))


def distance_km(lat1, lon1, lat2, lon2):
    r = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = math.radians(lat2 - lat1), math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def facility_level(name, tags):
    n = (name or '').lower()
    if re.search(r'medical college|aiims', n):
        return 'Medical College Hospital'
    if re.search(r'district|जिला|জেলা|सदर|sadar|civil hospital', n):
        return 'District Hospital'
    if re.search(r'sub[\s-]?divisional|referral hospital', n):
        return 'Sub-district Hospital'
    if re.search(r'community health|\bchc\b|सामुदायिक', n):
        return 'Community Health Centre (CHC)'
    if re.search(r'primary health|\bphc\b|प्राथमिक|ప్రాథమిక', n):
        return 'Primary Health Centre (PHC)'
    if re.search(r'sub[\s-]?cent|wellness|\bhwc\b', n):
        return 'Sub-centre / Health & Wellness Centre'
    return 'Government Hospital'


def is_government(name, tags):
    op_type = (tags.get('operator:type') or '').lower()
    if op_type in ('private', 'community', 'religious', 'ngo', 'charity'):
        return False
    if op_type in ('government', 'public'):
        return True
    operator = (tags.get('operator') or '').lower()
    if re.search(r'government|govt|health department|national health mission|\bnhm\b|state of|ministry', operator):
        return True
    if PRIVATE_NAME.search(name or ''):
        return False
    return bool(GOVT_NAME.search(name or ''))


def _make_facility(osm_key, name, lat, lon, tags, address, origin):
    return {
        'id': osm_key,
        'name': name,
        'level': facility_level(name, tags),
        'lat': lat,
        'lon': lon,
        'distance_km': round(distance_km(origin[0], origin[1], lat, lon), 1),
        'phone': tags.get('phone') or tags.get('contact:phone') or tags.get('contact:mobile') or '',
        'address': address,
        'emergency': tags.get('emergency') == 'yes',
        'source': 'OpenStreetMap',
    }


def _from_overpass(lat, lon, radius_km):
    if time.time() < _overpass_down_until[0]:
        raise RuntimeError('Overpass recently unreachable; using Nominatim')
    radius = int(radius_km * 1000)
    q = (f'[out:json][timeout:20];('
         f'nwr["amenity"="hospital"](around:{radius},{lat},{lon});'
         f'nwr["healthcare"="hospital"](around:{radius},{lat},{lon});'
         f'nwr["healthcare"="centre"](around:{radius},{lat},{lon});'
         f'nwr["amenity"="clinic"]["name"~"PHC|CHC|Primary Health|Community Health|Sub ?Cent",i](around:{radius},{lat},{lon});'
         f');out center tags;')
    last_error = None
    for url in OVERPASS_MIRRORS:
        try:
            data = _get_json(url, data=urllib.parse.urlencode({'data': q}).encode(), timeout=6)
            results = []
            for el in data.get('elements', []):
                tags = el.get('tags', {})
                name = tags.get('name') or tags.get('name:en')
                plat = el.get('lat') or (el.get('center') or {}).get('lat')
                plon = el.get('lon') or (el.get('center') or {}).get('lon')
                if not name or plat is None or not is_government(name, tags):
                    continue
                address = ', '.join(x for x in [tags.get('addr:street'), tags.get('addr:village') or tags.get('addr:city'),
                                                tags.get('addr:district'), tags.get('addr:postcode')] if x)
                results.append(_make_facility(f"{el['type']}/{el['id']}", name, float(plat), float(plon), tags, address, (lat, lon)))
            return results
        except Exception as e:  # network blocked / mirror busy: try the next source
            last_error = e
    _overpass_down_until[0] = time.time() + OVERPASS_RETRY_SECONDS
    raise RuntimeError(f'Overpass unavailable: {last_error}')


def _nominatim(params):
    # Nominatim usage policy: at most 1 request per second
    with _nominatim_lock:
        wait = 1.05 - (time.time() - _last_nominatim[0])
        if wait > 0:
            time.sleep(wait)
        try:
            return _get_json(f'{NOMINATIM_URL}?{urllib.parse.urlencode(params)}', timeout=12)
        finally:
            _last_nominatim[0] = time.time()


def _from_nominatim(lat, lon, radius_km):
    d = radius_km / 111.0
    viewbox = f'{lon - d},{lat + d},{lon + d},{lat - d}'
    seen = {}
    for q in NOMINATIM_QUERIES:
        rows = _nominatim({'q': q, 'format': 'jsonv2', 'limit': 50, 'viewbox': viewbox, 'bounded': 1,
                           'extratags': 1, 'addressdetails': 1, 'countrycodes': 'in'})
        for r in rows:
            key = f"{r['osm_type']}/{r['osm_id']}"
            if key in seen or r.get('category') not in ('amenity', 'healthcare'):
                continue
            tags = r.get('extratags') or {}
            name = r.get('name') or ''
            if not name or not is_government(name, tags):
                continue
            a = r.get('address') or {}
            address = ', '.join(x for x in [a.get('road'), a.get('village') or a.get('suburb'), a.get('town') or a.get('city'),
                                            a.get('state_district') or a.get('county'), a.get('postcode')] if x)
            seen[key] = _make_facility(key, name, float(r['lat']), float(r['lon']), tags, address, (lat, lon))
    return list(seen.values())


def find_government_facilities(lat, lon, radius_km=25):
    lat, lon = round(float(lat), 3), round(float(lon), 3)
    radius_km = max(5, min(int(radius_km), 60))
    key = (lat, lon, radius_km)
    with _cache_lock:
        cached = _cache.get(key)
        if cached and time.time() - cached[0] < CACHE_SECONDS:
            return cached[1]

    source = 'overpass'
    try:
        results = _from_overpass(lat, lon, radius_km)
    except RuntimeError:
        source = 'nominatim'
        results = _from_nominatim(lat, lon, radius_km)

    results = [r for r in results if r['distance_km'] <= radius_km * 1.05]
    results.sort(key=lambda r: r['distance_km'])
    payload = {'source': source, 'radius_km': radius_km, 'facilities': results[:40]}
    with _cache_lock:
        _cache[key] = (time.time(), payload)
    return payload
