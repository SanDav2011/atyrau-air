"""almaty.html → <город>.html: қалаға тән жерлерді ауыстыру (деректер, орталық, шекара, мәтіндер).
Қолдану: python tools/make_city.py astana
Негіз — almaty.html (көздерсіз). Басты зат — "pollutant" параметрі (PM2.5 немесе H2S)."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

CITIES = {
    "astana": {
        "name": "Астана",
        "center": (51.13, 71.43),
        "box": (50.95, 51.35, 71.20, 71.65),  # lat0, lat1, lng0, lng1
        "subtitle": "Ұсақ шаң (PM2,5), NO2, CO, SO2 және H2S — бекеттер мен жел, сағат бойынша",
        "problem": "Басты зат ретінде PM2,5 алынған (жоба шешімі); қосымша заттар — жоғарыдағы зат таңдау тізімінде. "
                   "Бекеттердің кейбірі H2S, SO2, NO2, CO да өлшейді.",
        "start": "2026-10-20",
        "pollutant": "PM2.5",
    },
    "aktobe": {
        "name": "Ақтөбе",
        "ru": "Актобе",
        "center": (50.28, 57.21),
        "box": (50.10, 50.50, 56.90, 57.50),
        "subtitle": "Күкіртсутек (H2S), SO2, NO2 және CO — бекеттер мен жел, сағат бойынша",
        "problem": "Басты зат ретінде H2S алынған (жоба шешімі); қосымша заттар — жоғарыдағы зат таңдау тізімінде. "
                   "Бекеттердің кейбірі SO2, NO2, CO да өлшейді.",
        "start": "2026-10-20",
        "pollutant": "H2S",
    },
    "aktau": {
        "name": "Ақтау",
        "ru": "Актау",
        "center": (43.65, 51.16),
        "box": (43.55, 43.80, 51.00, 51.40),
        "subtitle": "Күкіртсутек (H2S), SO2, NO2 және CO — бекеттер мен жел, сағат бойынша",
        "problem": "Басты зат ретінде H2S алынған (жоба шешімі); қосымша заттар — жоғарыдағы зат таңдау тізімінде. "
                   "Бекеттердің кейбірі SO2, NO2, CO да өлшейді.",
        "start": "2026-10-20",
        "pollutant": "H2S",
    },
    "oral": {
        "name": "Орал",
        "ru": "Уральск",
        "center": (51.23, 51.37),
        "box": (51.00, 51.40, 51.20, 51.60),
        "subtitle": "Күкіртсутек (H2S), SO2, NO2 және CO — бекеттер мен жел, сағат бойынша",
        "problem": "Басты зат ретінде H2S алынған (жоба шешімі); қосымша заттар — жоғарыдағы зат таңдау тізімінде. "
                   "Бекеттердің кейбірі SO2, NO2, CO да өлшейді. Бұл қалада ұсақ шаң (PM2,5, PM10) өлшенбейді.",
        "start": "2026-10-20",
        "pollutant": "H2S",
    },
}


def build(slug):
    c = CITIES[slug]
    t = (ROOT / "almaty.html").read_text(encoding="utf-8")

    def rep(a, b, count=1):
        nonlocal t
        assert t.count(a) == count, (t.count(a), a[:70])
        t = t.replace(a, b)

    name, (lat, lng), (la0, la1, lo0, lo1) = c["name"], c["center"], c["box"]
    rep("<title>Алматы — Қазақстан ауасы</title>", f"<title>{name} — Қазақстан ауасы</title>")
    rep("<h1>Алматы</h1>", f"<h1>{name}</h1>")
    rep("<p>Қысқы түтін: ұсақ шаң (PM2,5), NO2, CO және SO2 — бекеттер мен жел, сағат бойынша</p>", f"<p>{c['subtitle']}</p>")
    # Әдістеме
    rep("қала орталығы (43.24, 76.92).\n          Алматы бойынша жинау 2026 жылғы 20 қазанда басталды — тарих әзірге қысқа.",
        f"қала орталығы ({lat}, {lng}).\n          {name} бойынша жинау 2026 жылғы 20 қазанда басталды — тарих әзірге қысқа.")
    s = t.index("<p>Алматыда ауаның басты ластануы")
    e = t.index("</p>", s) + 4
    t = t[:s] + f"<p>{c['problem']}</p>" + t[e:]
    rep("<p>Алматы үшін әзірге жоқ: ластану көздерінің (ЖЭО, өнеркәсіп, көмір жағатын аудандар) тізімі жиналуда.",
        f"<p>{name} үшін әзірге жоқ: ластану көздерінің тізімі жиналмаған.")
    pol = c["pollutant"]
    if pol != "PM2.5":
        rep("pollutant = 'PM2.5', idx = 0", f"pollutant = '{pol}', idx = 0")
        rep("(b === 'PM2.5') - (a === 'PM2.5')", f"(b === '{pol}') - (a === '{pol}')")
        rep("ДДҰ ұсынысы PM2,5 үшін әлдеқайда қатаң: тәулігіне 15 мкг/м³.", "")
    # Деректер жолдары
    rep("data/almaty/stations.csv", f"data/{slug}/stations.csv")
    rep("data/almaty/wind.csv", f"data/{slug}/wind.csv")
    rep("data/almaty/kgm.csv", f"data/{slug}/kgm.csv")
    # Карта орталығы, қала шекарасы
    rep("setView([43.25, 76.92], 12)", f"setView([{lat}, {lng}], 12)")
    rep("s.lat > 43.15 && s.lat < 43.40 && s.lng > 76.75 && s.lng < 77.10", f"s.lat > {la0} && s.lat < {la1} && s.lng > {lo0} && s.lng < {lo1}")
    rep("const CITY_BOX = { lat0: 43.15, lat1: 43.40, lng0: 76.75, lng1: 77.10 };",
        f"const CITY_BOX = {{ lat0: {la0}, lat1: {la1}, lng0: {lo0}, lng1: {lo1} }};")
    rep("return first === 'Алматы' ? '' : first;", f"return {sorted({name, c.get('ru', name)})}.includes(first) ? '' : first;")
    rep("    Алматы бойынша жинау 2026-10-20 басталды.`;", f"    {name} бойынша жинау {c['start']} басталды.`;")
    rep("Алматы үшін ластану көздерінің тізімі әзірге жиналуда — көзді анықтау кейін қосылады.",
        f"{name} үшін ластану көздерінің тізімі әзірге жоқ — көзді анықтау кейін қосылады.")
    rep("// Алматы: ластану көздерінің тізімі әлі жоқ", f"// {name}: ластану көздерінің тізімі әлі жоқ")
    assert "Алматы" not in t.replace("Алматы облысы", ""), [l for l in t.splitlines() if "Алматы" in l][:3]
    out = ROOT / f"{slug}.html"
    out.write_text(t, encoding="utf-8")
    print("ok", out)


if __name__ == "__main__":
    build(sys.argv[1])
