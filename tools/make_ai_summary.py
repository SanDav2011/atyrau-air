"""data/ai-summary.json — қысқа жалпы мәлімет (қала, соңғы өлшеу уақыты, пост саны, газдар).
Тек өз есептеуіміз: Қазгидромет қатарлары, мәндер, координаталар, пост атаулары ЖОҚ.
Іске қосу: python tools/make_ai_summary.py
"""
import csv, json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
OUT = DATA / "ai-summary.json"
csv.field_size_limit(10**9)


def one(path):
    posts, gases, first, last = set(), set(), None, None
    with open(path, encoding="utf-8-sig", newline="") as f:
        for r in csv.DictReader(f):
            t = r.get("measured_at") or ""
            if not t:
                continue
            posts.add(r["station"])  # тек санау үшін, атаулар шығысқа түспейді
            gases.add(r["pollutant"])
            first = t if first is None or t < first else first
            last = t if last is None or t > last else last
    return {"stations_in_data": len(posts), "pollutants": sorted(gases),
            "data_from": first[:10] if first else None,
            "last_measurement_local": last}


def main():
    cities = {}
    # Атырау — data/ түбірінде, қалғандары data/<қала>/ ішінде
    items = [("atyrau", DATA / "stations.csv")]
    for d in sorted(p for p in DATA.iterdir() if p.is_dir()):
        if (d / "stations.csv").exists():
            items.append((d.name, d / "stations.csv"))
    for slug, p in items:
        if p.exists():
            cities[slug] = one(p)
    res = {
        "about": "Қазақстан ауасы: жалпы мәлімет. Мәндер мен координаталар бұл файлда жоқ.",
        "note": "Бұл ресми мониторинг емес; дерек көзі — Қазгидромет (ecodata.kz), жел — Open-Meteo.",
        "cities": cities,
    }
    OUT.write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
    print(len(cities), "cities ->", OUT)


if __name__ == "__main__":
    sys.exit(main())
