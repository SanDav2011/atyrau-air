"""Сборщик: посты качества воздуха (карта Казгидромета ecodata.kz) + погода (Open-Meteo) — по городам из CITIES.

Запуск раз в час. ecodata.kz открывается только из Казахстана, поэтому:
  ноутбук:  collect.py --only stations,kgm,weather --log local.log --push   (всё → сразу в GitHub, каждый час)
  GitHub:   collect.py --only weather,kgm --log cloud.log  (запасной: только если ноутбук не присылал данные > 1,5 ч)
"""
import argparse
import csv
import json
import math
import os
import subprocess
import sys
import time
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
LOG = DATA / "collect.log"  # меняется аргументом --log

ECODATA_URL = "http://ecodata.kz:3838/app_dem_visual/"
# Города: рамка постов, точка ветра (Open-Meteo), папка с данными. Атырау — в корне data/ (как было).
CITIES = {
    # Атырауская область с запасом (город, Кульсары, Тенгиз, Жанбай, Макат, Ганюшкино — 48.5)
    "atyrau": {"bbox": {"lat_min": 45.5, "lat_max": 48.5, "lng_min": 48.5, "lng_max": 55.0},
               "wind": (47.11, 51.92), "tz": "Asia%2FAtyrau", "dir": DATA},
    # Алматы с пригородами (Боралдай, Талгар)
    "almaty": {"bbox": {"lat_min": 43.05, "lat_max": 43.55, "lng_min": 76.55, "lng_max": 77.45},
               "wind": (43.24, 76.92), "tz": "Asia%2FAlmaty", "dir": DATA / "almaty"},
    # Астана с пригородами
    "astana": {"bbox": {"lat_min": 50.9, "lat_max": 51.4, "lng_min": 71.2, "lng_max": 71.7},
               "wind": (51.13, 71.43), "tz": "Asia%2FAlmaty", "dir": DATA / "astana"},
}


def city_files(c):
    d = CITIES[c]["dir"]
    return d / "stations.csv", d / "wind.csv", d / "kgm.csv"
ATYRAU_TZ = timezone(timedelta(hours=5))  # Казахстан UTC+5; сервер GitHub работает в UTC
# На Windows — установленный Edge, на сервере GitHub — Chromium из Playwright (BROWSER_CHANNEL пустой)
BROWSER_CHANNEL = os.environ.get("BROWSER_CHANNEL", "msedge" if os.name == "nt" else "") or None

STATION_FIELDS = ["fetched_at_utc", "station", "address", "lat", "lng", "measured_at", "pollutant", "value"]
WIND_FIELDS = ["time_local", "wind_dir_deg", "wind_speed_ms", "wind_gust_ms", "radiation_wm2", "cloud_pct", "temp_c"]
WEATHER_START = "2026-10-12"  # погода нужна с начала сбора постов (с запасом)

# tabigat.gov.kz (портал Минэкологии): слой «Состояние атмосферного воздуха» — посты Казгидромета
# с десятичными значениями и СВОИМ ветром. Открытый GeoServer WFS, координаты EPSG:3857.
TABIGAT_LAYER_ID = "85a41068-0bd1-427d-8958-86b44a696eba"
TABIGAT_ATTRS = f"https://tabigat.gov.kz/api/v1/gis/main/open-api-layers/{TABIGAT_LAYER_ID}/attrs"
TABIGAT_WFS = ("https://tabigat.gov.kz/geoserver/gis/wfs?service=WFS&version=1.0.0&request=GetFeature"
               "&typeName=gis:layer_48572&outputFormat=application/json&maxFeatures=5000")
KGM_PARAMS = {  # nameRu поля → код в kgm.csv (единицы как в источнике)
    "Направление ветра (градусы)": "wind_dir", "Скорость ветра (м/с)": "wind_speed",
    "Температура (°C)": "temp", "Давление (мм рт. ст.)": "pressure",
    "Сероводород (мкг/м3)": "H2S", "Диоксид серы (мкг/м3)": "SO2", "Оксид азота (мкг/м3)": "NO",
    "Диоксид азота (мкг/м3)": "NO2", "Оксид углерода (мкг/м3)": "CO",
    "Частицы PM2.5 (мг/м3)": "PM2.5_mg", "Частицы PM10 (мг/м3)": "PM10_mg",
    "Взвешенные вещества (частицы, мг/м3)": "PMtot_mg",
}
KGM_FIELDS = ["fetched_at_utc", "station_id", "lat", "lng", "measured_at", "param", "value"]

# Достаёт из карты все точки в рамке BBOX и разбирает таблицу во всплывающем окне
EXTRACT_JS = """(b) => {
  const el = document.querySelector('.leaflet.html-widget');
  const map = HTMLWidgets.find('#' + el.id).getMap();
  const out = [];
  map.eachLayer(l => {
    if (!l.getLatLng || !l.getPopup || !l.getPopup()) return;
    const p = l.getLatLng();
    if (p.lat < b.lat_min || p.lat > b.lat_max || p.lng < b.lng_min || p.lng > b.lng_max) return;
    const html = String(l.getPopup().getContent());
    // в заголовке сайта лишний <tr>, поэтому заголовок берём из сырого текста, а не из DOM
    const capRaw = (html.match(/<caption>([\\s\\S]*?)<\\/caption>/) || [, ''])[1];
    const cap = capRaw.replace(/<[^>]+>/g, ' ').replace(/\\s+/g, ' ');
    const div = document.createElement('div');
    div.innerHTML = html;
    const m = cap.match(/^\\s*(.*?)\\s*:\\s*(.*?)\\s+(\\d{4}-\\d{2}-\\d{2}(?: \\d{2}:\\d{2}:\\d{2})?)\\s*$/s);
    const rows = [...div.querySelectorAll('tbody tr')].map(tr => [...tr.querySelectorAll('td')].map(td => td.textContent.trim()));
    out.push({
      station: m ? m[1] : cap.trim(), address: m ? m[2] : '', measured_at: m ? m[3] : '',
      lat: p.lat, lng: p.lng,
      values: rows.filter(r => r.length >= 2 && r[1] !== '').map(r => ({ pollutant: r[0], value: r[1] })),
    });
  });
  return out;
}"""


def log(msg):
    DATA.mkdir(exist_ok=True)
    line = f"{datetime.now(ATYRAU_TZ):%Y-%m-%d %H:%M:%S} {msg}"
    if sys.stdout:  # из планировщика (pythonw) консоли нет
        sys.stdout.reconfigure(encoding="utf-8")
        print(line)
    with LOG.open("a", encoding="utf-8") as f:
        f.write(line + "\n")


def read_keys(path, key_fn):
    if not path.exists():
        return set()
    with path.open(encoding="utf-8-sig", newline="") as f:
        return {key_fn(r) for r in csv.DictReader(f)}


def append_rows(path, fields, rows):
    new_file = not path.exists()
    with path.open("a", encoding="utf-8-sig" if new_file else "utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        if new_file:
            w.writeheader()
        w.writerows(rows)


def fetch_stations(cities):
    """Одна загрузка карты — точки для каждого города (по его рамке)."""
    from playwright.sync_api import sync_playwright  # нужен только для постов

    with sync_playwright() as p:
        browser = p.chromium.launch(channel=BROWSER_CHANNEL, headless=True)
        page = browser.new_page()
        page.goto(ECODATA_URL, timeout=90_000)
        # ждём, пока Shiny нарисует карту с маркерами
        page.wait_for_function(
            """() => { const el = document.querySelector('.leaflet.html-widget');
                       if (!el || !window.HTMLWidgets) return false;
                       const w = HTMLWidgets.find('#' + el.id); if (!w || !w.getMap) return false;
                       let n = 0; w.getMap().eachLayer(l => { if (l.getPopup && l.getPopup()) n++; });
                       return n > 50; }""",
            timeout=120_000,
        )
        points = {c: page.evaluate(EXTRACT_JS, CITIES[c]["bbox"]) for c in cities}
        browser.close()
    return points


def collect_stations(cities):
    try:
        by_city = fetch_stations(cities)
    except Exception as e:  # разовые сбои запуска браузера/сайта — одна повторная попытка
        log(f"посты: повтор после ошибки {e!r}")
        by_city = fetch_stations(cities)
    key = lambda r: (r["station"], r["lat"][:7], r["lng"][:7], r["measured_at"], r["pollutant"])
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    res = {}
    for c, points in by_city.items():
        path = city_files(c)[0]
        path.parent.mkdir(parents=True, exist_ok=True)
        seen = read_keys(path, key)
        rows = []
        for pt in points:
            for v in pt["values"]:
                r = {"fetched_at_utc": now, "station": pt["station"], "address": pt["address"],
                     "lat": f"{pt['lat']:.5f}", "lng": f"{pt['lng']:.5f}",
                     "measured_at": pt["measured_at"], "pollutant": v["pollutant"], "value": v["value"]}
                if key(r) not in seen:
                    seen.add(key(r))
                    rows.append(r)
        append_rows(path, STATION_FIELDS, rows)
        res[c] = (len(points), len(rows))
    return res


def get_json(url, attempts=3):
    for i in range(attempts):
        try:
            with urllib.request.urlopen(url, timeout=30) as resp:
                return json.load(resp)
        except Exception:  # сервис иногда отвечает 503 — пробуем ещё
            if i == attempts - 1:
                raise
            time.sleep(10 * (i + 1))


def collect_kgm(cities):
    """Посты Казгидромета с tabigat.gov.kz: дописывает новые (пост, час, параметр) в kgm.csv каждого города."""
    attrs = get_json(TABIGAT_ATTRS)
    code = {a["attrname"]: KGM_PARAMS[a["nameRu"]] for a in attrs if a.get("nameRu") in KGM_PARAMS}
    name = {a["nameRu"]: a["attrname"] for a in attrs}
    date_attr, id_attr = name["Дата"], name["ID Станции"]
    feats = get_json(TABIGAT_WFS)["features"]
    key = lambda r: (r["station_id"], r["measured_at"], r["param"])
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    return {c: _kgm_city(c, feats, code, date_attr, id_attr, key, now) for c in cities}


def _kgm_city(c, feats, code, date_attr, id_attr, key, now):
    B = CITIES[c]["bbox"]
    path = city_files(c)[2]
    path.parent.mkdir(parents=True, exist_ok=True)
    seen = read_keys(path, key)
    rows, n_pts = [], 0
    for f in feats:
        x, y = f["geometry"]["coordinates"]
        lng = x / 6378137 * 180 / math.pi
        lat = math.degrees(2 * math.atan(math.exp(y / 6378137)) - math.pi / 2)
        if not (B["lat_min"] <= lat <= B["lat_max"] and B["lng_min"] <= lng <= B["lng_max"]):
            continue
        p = f["properties"]
        if not p.get(date_attr):
            continue
        n_pts += 1
        t = datetime.fromisoformat(p[date_attr].replace("Z", "+00:00")).astimezone(ATYRAU_TZ)
        for attr, c in code.items():
            v = p.get(attr)
            if v is None:
                continue
            r = {"fetched_at_utc": now, "station_id": p.get(id_attr), "lat": f"{lat:.5f}", "lng": f"{lng:.5f}",
                 "measured_at": t.strftime("%Y-%m-%d %H:%M:%S"), "param": c, "value": round(float(v), 4)}
            if key({k: str(v2) for k, v2 in r.items()}) not in seen:
                seen.add(key({k: str(v2) for k, v2 in r.items()}))
                rows.append(r)
    append_rows(path, KGM_FIELDS, rows)
    return n_pts, len(rows)


def collect_wind(c):
    """Погода по часам с WEATHER_START до текущего часа; файл пересобирается целиком (Open-Meteo уточняет прошлые часы)."""
    lat, lng = CITIES[c]["wind"]
    wind_csv = city_files(c)[1]
    wind_csv.parent.mkdir(parents=True, exist_ok=True)
    now_local = datetime.now(ATYRAU_TZ).replace(tzinfo=None)
    url = (f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lng}"
           "&hourly=wind_direction_10m,wind_speed_10m,wind_gusts_10m,shortwave_radiation,cloud_cover,temperature_2m"
           f"&wind_speed_unit=ms&timezone={CITIES[c]['tz']}&start_date={WEATHER_START}&end_date={now_local:%Y-%m-%d}")
    h = get_json(url)["hourly"]
    rows = []
    for t, d, s, g, rad, cl, tc in zip(h["time"], h["wind_direction_10m"], h["wind_speed_10m"], h["wind_gusts_10m"],
                                       h["shortwave_radiation"], h["cloud_cover"], h["temperature_2m"]):
        if datetime.fromisoformat(t) > now_local or d is None:
            continue  # только прошедшие часы, без прогноза
        rows.append({"time_local": t, "wind_dir_deg": d, "wind_speed_ms": s, "wind_gust_ms": g,
                     "radiation_wm2": rad, "cloud_pct": cl, "temp_c": tc})
    tmp = wind_csv.with_suffix(".tmp")
    with tmp.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=WIND_FIELDS)
        w.writeheader()
        w.writerows(rows)
    tmp.replace(wind_csv)
    return len(rows)


def git(*args):
    flags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0  # без всплывающих окон из планировщика
    return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True, encoding="utf-8",
                          creationflags=flags, timeout=120)


def push(paths):
    """Отправить новые данные в GitHub (чтобы страница в интернете их видела)."""
    git("add", *[str(p.relative_to(ROOT)) for p in paths])
    if git("diff", "--cached", "--quiet").returncode == 0:
        return "нет изменений"
    git("commit", "-m", f"Посты {datetime.now(ATYRAU_TZ):%Y-%m-%d %H:%M}")
    # -X theirs: при конфликте в файлах данных побеждает свежий локальный сбор (ноутбук)
    pull = git("pull", "--rebase", "-X", "theirs", "-q")
    if pull.returncode != 0:
        git("rebase", "--abort")
        return f"ОШИБКА pull: {pull.stderr.strip()[:300]}"
    res = git("push", "-q")
    return "отправлено" if res.returncode == 0 else f"ОШИБКА push: {res.stderr.strip()[:300]}"


def main():
    global LOG
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", default="all", help="через запятую: stations, weather, kgm (или all)")
    ap.add_argument("--log", default="collect.log")
    ap.add_argument("--push", action="store_true", help="после сбора отправить данные в GitHub")
    ap.add_argument("--city", default="all", help="через запятую: " + ", ".join(CITIES) + " (или all)")
    a = ap.parse_args()
    LOG = DATA / a.log
    parts = {"stations", "weather", "kgm"} if a.only == "all" else set(a.only.split(","))
    cities = list(CITIES) if a.city == "all" else a.city.split(",")
    tag = lambda c: "" if c == "atyrau" else f"[{c}] "  # строки Атырау в логе — как раньше
    ok = True
    if "stations" in parts:
        try:
            for c, (n_points, n_rows) in collect_stations(cities).items():
                log(f"{tag(c)}посты: {n_points} точек, новых строк {n_rows}")
        except Exception as e:
            ok = False
            log(f"ОШИБКА посты: {e!r}")
    if "kgm" in parts:
        try:
            for c, (n_pts, n_rows) in collect_kgm(cities).items():
                log(f"{tag(c)}казгидромет (tabigat): {n_pts} постов, новых строк {n_rows}")
        except Exception as e:
            ok = False
            log(f"ОШИБКА казгидромет: {e!r}")
    if "weather" in parts:
        for c in cities:
            try:
                log(f"{tag(c)}погода: часов в файле {collect_wind(c)}")
            except Exception as e:
                ok = False
                log(f"{tag(c)}ОШИБКА погода: {e!r}")
    if a.push:
        try:
            r = push([f for c in cities for f in city_files(c) if f.exists()] + [LOG])
            log(f"github: {r}")
            ok = ok and not r.startswith("ОШИБКА")
        except Exception as e:
            ok = False
            log(f"ОШИБКА github: {e!r}")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
