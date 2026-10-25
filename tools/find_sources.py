"""Қала бойынша ықтимал ластану көздерін OSM-нен (Overpass) іздейді.
Нәтиже: memory-bank/analysis/sources-<қала>.json + sources-<қала>.html (тексеруге арналған карта).
Іске қосу: PYTHONUTF8=1 python tools/find_sources.py shymkent pavlodar
Бұл тек ЖОБА: private/sources.json-ға өзі ештеңе жазбайды, Роман растағаннан кейін ғана көшіріледі."""
import json, re, sys, time, math, urllib.request, urllib.parse
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "memory-bank" / "analysis"
MIRRORS = ["https://overpass-api.de/api/interpreter", "https://overpass.kumi.systems/api/interpreter",
           "https://overpass.private.coffee/api/interpreter"]

# қала: (орталық lat, lng) — make_city.py-мен бірдей; рамка қала сыртындағы өнеркәсіпті де қамтиды
CITIES = {
    "shymkent": ("Шымкент", 42.3335, 69.6246),
    "pavlodar": ("Павлодар", 52.2785, 76.9531),
    "oral": ("Орал", 51.23, 51.37),
}
DLAT, DLNG = 0.22, 0.34

# (kind, тип белгісі, OSM сүзгілері)
FILTERS = [
    ("refinery", "МӨЗ / мұнай-химия", ['["industrial"~"refinery|oil|chemical"]', '["man_made"="petroleum_well"]']),
    ("power", "Электр станциясы / ЖЭО", ['["power"="plant"]']),
    ("wastewater", "Тазарту қондырғысы / тоған", ['["man_made"="wastewater_plant"]', '["water"="wastewater"]']),
    ("landfill", "Қоқыс полигоны", ['["landuse"="landfill"]']),   # қоқыс жәшіктері (amenity=waste_disposal) алынбайды — Роман
    ("metal", "Металлургия / цемент / құрылыс материалдары", ['["industrial"~"metal|steel|cement|factory|concrete"]', '["man_made"="works"]']),
    ("fuel", "Мұнай базасы / қойма", ['["industrial"~"depot|oil_storage"]', '["man_made"="storage_tank"]']),
    ("quarry", "Карьер", ['["landuse"="quarry"]']),
    ("chimney", "Мұржа", ['["man_made"="chimney"]']),
    ("industrial", "Өнеркәсіп аймағы", ['["landuse"="industrial"]']),
]


def overpass(q):
    data = urllib.parse.urlencode({"data": q}).encode()
    for url in MIRRORS:
        for _ in range(1):
            try:
                req = urllib.request.Request(url, data, headers={"User-Agent": "atyrau-air-sources/1.0"})
                return json.load(urllib.request.urlopen(req, timeout=70))
            except Exception as e:
                print("  қате", url, e, file=sys.stderr)
                time.sleep(5)
    raise SystemExit("Overpass қолжетімсіз")


def area_km2(ring):
    # шамамен: эквирект проекция
    if len(ring) < 3: return 0
    k = math.cos(math.radians(ring[0][0])) * 111.32
    pts = [(p[1] * k, p[0] * 110.57) for p in ring]
    return abs(sum(pts[i][0] * pts[(i + 1) % len(pts)][1] - pts[(i + 1) % len(pts)][0] * pts[i][1] for i in range(len(pts)))) / 2


def classify(t):
    # сүзгі жолын (["a"~"x|y"] немесе ["a"="x"]) тегтерге қарсы тексереді; тізім реті — басымдық
    for k, _, flt in FILTERS:
        for f in flt:
            m = re.fullmatch(r'\["(\w+)"(~|=)"([^"]+)"\]', f)
            tag, op, val = m.groups()
            v = t.get(tag)
            if v and (v == val if op == "=" else v in val.split("|")):
                return k
    return None


def run(key):
    name, lat, lng = CITIES[key]
    bbox = f"{lat - DLAT},{lng - DLNG},{lat + DLAT},{lng + DLNG}"
    els = []
    for kind, _, flt in FILTERS:   # бір үлкен сұраныс Overpass-ты құлатады → түрі бойынша бөлек
        q = f"[out:json][timeout:60];({''.join(f'nwr{f}({bbox});' for f in flt)});out tags geom;"
        print(name, kind, "…")
        try:
            els += overpass(q)["elements"]
        except SystemExit:
            print("  өткізілді:", kind, file=sys.stderr)
        time.sleep(3)
    res, seen = [], set()
    for e in els:
        t = e.get("tags", {})
        kind = classify(t)
        if kind is None: continue
        if e["type"] == "node":
            c, ring = (e["lat"], e["lon"]), None
        else:
            g = e.get("geometry") or []
            if not g: continue
            ring = [(p["lat"], p["lon"]) for p in g]
            c = (sum(p[0] for p in ring) / len(ring), sum(p[1] for p in ring) / len(ring))
        a = round(area_km2(ring), 3) if ring else 0
        if kind == "industrial" and a < 0.3: continue   # ұсақ өнеркәсіп аймақтары — шу
        if kind in ("metal", "fuel") and e["type"] == "node": continue
        if kind == "landfill" and a < 0.02: continue   # ұсақ нүктелер/жәшіктер — шу, нақты полигон ≥0,02 км²
        uid = (e["type"], e["id"])
        if uid in seen: continue
        seen.add(uid)
        res.append({"osm": f"{e['type']}/{e['id']}", "kind": kind, "name": t.get("name") or t.get("name:ru") or t.get("operator") or "",
                    "tags": {k: v for k, v in t.items() if k in ("industrial", "power", "landuse", "man_made", "water", "operator", "plant:source", "height")},
                    "lat": round(c[0], 5), "lng": round(c[1], 5), "area_km2": a,
                    "dist_km": round(math.hypot((c[0] - lat) * 110.57, (c[1] - lng) * 111.32 * math.cos(math.radians(lat))), 1),
                    "ring": [[round(p[0], 5), round(p[1], 5)] for p in ring[::max(1, len(ring) // 60)]] if ring else None})
    res.sort(key=lambda r: (r["kind"], -r["area_km2"]))
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / f"sources-{key}.json").write_text(json.dumps({"city": key, "center": [lat, lng], "items": res}, ensure_ascii=False, indent=1), encoding="utf-8")
    html_map(key, name, lat, lng, res)
    from collections import Counter
    print(name, len(res), dict(Counter(r["kind"] for r in res)))


COL = {"refinery": "#e11d48", "power": "#ea580c", "wastewater": "#0369a1", "landfill": "#7c3aed", "metal": "#475569",
       "fuel": "#b45309", "quarry": "#a16207", "chimney": "#dc2626", "industrial": "#64748b"}
LBL = {k: l for k, l, _ in FILTERS}


def html_map(key, name, lat, lng, res):
    data = json.dumps(res, ensure_ascii=False)
    h = f"""<!doctype html><html lang="kk"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>{name} — көздер (жоба)</title>
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.min.css"><script src="https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.min.js"></script>
<style>html,body,#m{{height:100%;margin:0}}.lb{{background:#fff;border:1px solid #333;padding:2px 5px;font:600 12px system-ui;border-radius:4px;white-space:nowrap}}
#leg{{position:absolute;z-index:1000;right:8px;top:8px;background:#fff;padding:8px 10px;font:12px system-ui;border-radius:6px;max-height:80vh;overflow:auto}}#leg i{{display:inline-block;width:10px;height:10px;border-radius:50%;margin-right:5px}}</style></head><body><div id="m"></div><div id="leg"></div>
<script>const m=L.map('m').setView([{lat},{lng}],11);
L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{{z}}/{{y}}/{{x}}',{{maxZoom:18,attribution:'Esri'}}).addTo(m);
const COL={json.dumps(COL)},LBL={json.dumps(LBL, ensure_ascii=False)},D={data};
const n={{}};
D.forEach((r,i)=>{{n[r.kind]=(n[r.kind]||0)+1;const c=COL[r.kind];const tip=`#${{i}} ${{LBL[r.kind]}}${{r.name?' · '+r.name:''}} · ${{r.area_km2}} км² · ${{r.dist_km}} км · ${{r.osm}}`;
if(r.ring)L.polygon(r.ring,{{color:c,weight:2,fillOpacity:.2}}).addTo(m).bindTooltip(tip);
L.circleMarker([r.lat,r.lng],{{radius:5,color:'#fff',weight:1,fillColor:c,fillOpacity:1}}).addTo(m).bindTooltip(tip)}});
L.circleMarker([{lat},{lng}],{{radius:7,color:'#000',fill:false}}).addTo(m).bindTooltip('Қала орталығы');
leg.innerHTML=Object.keys(n).map(k=>`<div><i style="background:${{COL[k]}}"></i>${{LBL[k]}}: ${{n[k]}}</div>`).join('');</script></body></html>"""
    (OUT / f"sources-{key}.html").write_text(h, encoding="utf-8")


# Overpass құлаған кезде: Nominatim (1 сұраныс/сек), кілт сөздер бойынша рамка ішінде
NOM_Q = {
    "refinery": ["нефтеперерабатывающий завод", "НПЗ", "нефтехимический", "химический завод", "фосфор", "свинцовый завод"],
    "power": ["ТЭЦ", "ГРЭС", "электростанция", "котельная"],
    "wastewater": ["очистные сооружения", "канализационные очистные", "поля фильтрации", "отстойник", "накопитель сточных вод"],
    "landfill": ["полигон ТБО", "полигон отходов", "свалка", "мусорный полигон", "золоотвал", "шлакоотвал"],
    "metal": ["металлургический завод", "цементный завод", "асфальтобетонный завод", "ферросплавный", "алюминиевый", "комбинат", "кожевенный", "Шымкентцемент", "Стандарт цемент", "ХимФарм", "завод ферросплавов", "мясокомбинат", "птицефабрика"],
    "fuel": ["нефтебаза", "АЗС нефтебаза", "склад ГСМ"],
    "quarry": ["карьер"],
}


def nominatim(key):
    name, lat, lng = CITIES[key]
    vb = f"{lng - DLNG},{lat + DLAT},{lng + DLNG},{lat - DLAT}"
    res, seen = [], set()
    for kind, qs in NOM_Q.items():
        for q in qs:
            url = "https://nominatim.openstreetmap.org/search?" + urllib.parse.urlencode(
                {"q": q, "format": "jsonv2", "viewbox": vb, "bounded": 1, "limit": 40, "accept-language": "ru", "polygon_geojson": 0})
            try:
                req = urllib.request.Request(url, headers={"User-Agent": "atyrau-air-sources/1.0 (sanainwest@gmail.com)"})
                items = json.load(urllib.request.urlopen(req, timeout=60))
            except Exception as e:
                print("  қате", q, e, file=sys.stderr); items = []
            time.sleep(1.2)
            for it in items:
                uid = (it["osm_type"], it["osm_id"])
                if uid in seen: continue
                seen.add(uid)
                if it["category"] in ("highway", "railway", "place", "natural", "amenity", "shop") or (it["category"] == "building" and it["type"] == "yes"):
                    continue   # аялдама, станция, ұсақ ғимарат — көз емес
                b = [float(x) for x in it["boundingbox"]]  # s,n,w,e
                c = (float(it["lat"]), float(it["lon"]))
                ring = [[b[0], b[2]], [b[0], b[3]], [b[1], b[3]], [b[1], b[2]]] if it["osm_type"] != "node" else None
                a = round(area_km2([tuple(p) for p in ring]), 3) if ring else 0
                res.append({"osm": f"{it['osm_type']}/{it['osm_id']}", "kind": kind, "name": it.get("name") or it["display_name"].split(",")[0],
                            "tags": {"найден_по": q, "osm_class": f"{it['category']}={it['type']}"},
                            "lat": round(c[0], 5), "lng": round(c[1], 5), "area_km2": a,
                            "dist_km": round(math.hypot((c[0] - lat) * 110.57, (c[1] - lng) * 111.32 * math.cos(math.radians(lat))), 1),
                            "ring": ring})
        print(name, kind, len(res))
    res.sort(key=lambda r: (r["kind"], -r["area_km2"]))
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / f"sources-{key}.json").write_text(json.dumps({"city": key, "center": [lat, lng], "via": "nominatim", "items": res}, ensure_ascii=False, indent=1), encoding="utf-8")
    html_map(key, name, lat, lng, res)


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    for k in (args or list(CITIES)):
        (nominatim if "--nominatim" in sys.argv else run)(k)
