"""Бір реттік: AirData.kz архивінен (CC BY-NC 4.0) data/<қала>/stations.csv-ға бұрынғы сағаттарды қосу.
Қолдану: python tools/backfill_airdata.py [--write] [--since 2026-10-08]
--write жоқ болса — тек санау (dry-run). Архив: projects/air-data-kz/github (жергілікті, репоға салынбайды).
Бекеттер біздің ecodata бекеттерімен координат бойынша сәйкестіріледі (≤ 500 м, бекеттер бір-бірінен ≥ 1,5 км), әйтпесе жазба өткізіледі."""
import argparse
import csv
import gzip
import math
from datetime import datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ARCH = ROOT.parent / "air-data-kz" / "github"
FIELDS = ["fetched_at_utc", "station", "address", "lat", "lng", "measured_at", "pollutant", "value"]

# біздің қала → (архивтегі қала аты, архив папкасы)
CITIES = {
    "astana": ("Astana", "astana"),
    "aktobe": ("Aktobe", "rest_of_kz"),
    "aktau": ("Aktau", "rest_of_kz"),
    "oral": ("Uralsk", "rest_of_kz"),
    "zko-east": ("Burlin vil.", "rest_of_kz"),
}
# архив файлы → біздегі зат коды
POLS = {"co": "CO", "h2s": "H2S", "nh3": "NH3", "no": "NO", "no2": "NO2", "o3": "O3", "pm10": "PM10",
        "pm25": "PM2.5", "pm2_5": "PM2.5", "pmtot": "PMtot", "so2": "SO2"}
MAX_M = 500


def dist_m(a, b):
    dy = (a[0] - b[0]) * 111320
    dx = (a[1] - b[1]) * 111320 * math.cos(math.radians(a[0]))
    return math.hypot(dx, dy)


def our_stations(path):
    st = {}
    if path.exists():
        for r in csv.DictReader(path.open(encoding="utf-8-sig", newline="")):
            st[(r["station"], r["lat"], r["lng"])] = (r["address"], float(r["lat"]), float(r["lng"]))
    return st


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--since", default="2026-10-08")
    ap.add_argument("--write", action="store_true")
    a = ap.parse_args()
    for slug, (acity, folder) in CITIES.items():
        path = ROOT / "data" / slug / "stations.csv"
        ours = our_stations(path)
        have = set()
        if path.exists():
            for r in csv.DictReader(path.open(encoding="utf-8-sig", newline="")):
                have.add((r["station"], r["measured_at"][:13], r["pollutant"]))
        new, unmatched, matched = [], {}, {}
        for fname, pol in POLS.items():
            f = ARCH / folder / f"{fname}.csv.gz"
            if not f.exists():
                continue
            for r in csv.DictReader(gzip.open(f, "rt", encoding="utf-8")):
                if r.get("city", acity) != acity or r["datetime_utc"] < a.since:
                    continue
                pos = (float(r["lat"]), float(r["lon"]))
                best = min(ours.items(), key=lambda kv: dist_m(pos, kv[1][1:]), default=None)
                if best is None or dist_m(pos, best[1][1:]) > MAX_M:
                    unmatched[r["station_name"]] = unmatched.get(r["station_name"], 0) + 1
                    continue
                (name, lat, lng), (addr, _, _) = best[0], best[1]
                matched[r["station_name"]] = name
                utc = datetime.fromisoformat(r["datetime_utc"])
                loc = (utc + timedelta(hours=5)).replace(tzinfo=None)  # Қазақстан UTC+5, ecodata-дағыдай
                key = (name, loc.strftime("%Y-%m-%d %H"), pol)
                if key in have:
                    continue
                have.add(key)
                # бет 2 тәуліктен ескі жазбаны «істен шыққан» деп өткізеді → fetched = өлшемнен 1 сағат кейін
                fetched = (utc + timedelta(hours=1)).strftime("%Y-%m-%dT%H:%M:%SZ")
                new.append({"fetched_at_utc": fetched, "station": name, "address": addr, "lat": lat, "lng": lng,
                            "measured_at": loc.strftime("%Y-%m-%d %H:00:00"), "pollutant": pol,
                            "value": round(float(r["value_ugm3"]), 2)})
        new.sort(key=lambda x: (x["measured_at"], x["station"], x["pollutant"]))
        span = f"{new[0]['measured_at']} … {new[-1]['measured_at']}" if new else "—"
        print(f"{slug}: новых строк {len(new)} ({span}); сопоставлено {matched}; НЕ сопоставлено {unmatched}")
        if a.write and new:
            old = path.read_text(encoding="utf-8-sig") if path.exists() else ""
            with path.open("w", encoding="utf-8-sig", newline="") as fh:
                w = csv.DictWriter(fh, fieldnames=FIELDS)
                w.writeheader()
                w.writerows(new)
                if old:
                    rows = list(csv.DictReader(old.splitlines()))
                    w.writerows(rows)


if __name__ == "__main__":
    main()
