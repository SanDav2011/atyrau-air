"""Қала беттеріндегі қалаға тән жолдар: kk-беттен regex-пен табылып, ru/en аудармасы шаблон бойынша жасалады.
make_lang.py шақырады: city_rules(slug, html, lang) -> {kk жол: аударма}. Қала атауы ru-да қазақша қалады (Роман)."""
import re

# ағылшынша атаулар (karta.html DN-мен бірдей)
EN = {"almaty": "Almaty", "astana": "Astana", "aktobe": "Aktobe", "aktau": "Aktau", "oral": "Oral", "shymkent": "Shymkent",
      "karaganda": "Karaganda", "pavlodar": "Pavlodar", "oskemen": "Oskemen", "semey": "Semey", "kostanay": "Kostanay",
      "taraz": "Taraz", "taldykorgan": "Taldykorgan", "kyzylorda": "Kyzylorda", "kokshetau": "Kokshetau",
      "turkistan": "Turkistan", "zhezkazgan": "Zhezkazgan", "petropavl": "Petropavl"}

# заттар тізімі (кіші әріппен): kk -> (ru, en)
SUB = {
    "ұсақ шаң (PM2,5), NO2, CO және SO2": ("мелкая пыль (PM2,5), NO2, CO и SO2", "fine dust (PM2.5), NO2, CO and SO2"),
    "күкіртсутек (H2S), SO2, NO2 және CO": ("сероводород (H2S), SO2, NO2 и CO", "hydrogen sulfide (H2S), SO2, NO2 and CO"),
    "азот диоксиді (NO2), CO және SO2": ("диоксид азота (NO2), CO и SO2", "nitrogen dioxide (NO2), CO and SO2"),
    "күкірт диоксиді (SO2), NO2, CO және ұсақ шаң": ("диоксид серы (SO2), NO2, CO и мелкая пыль", "sulfur dioxide (SO2), NO2, CO and fine dust"),
    "ұсақ шаң (PM2,5), NO2, CO, SO2 және H2S": ("мелкая пыль (PM2,5), NO2, CO, SO2 и H2S", "fine dust (PM2.5), NO2, CO, SO2 and H2S"),
}
MONTH = {"қазан": ("октября", "October")}


def up(s):
    return s[:1].upper() + s[1:]


def _sub(kk_phrase, i):
    low = kk_phrase[:1].lower() + kk_phrase[1:]
    t = SUB[low]
    return t[i]


def city_rules(slug, html, lang):
    i = 0 if lang == "ru" else 1
    N = re.search(r"<h1>([^<]+)</h1>", html).group(1)
    E = EN[slug]
    nm = N if lang == "ru" else E
    out = {}

    def add(kk, ru, en):
        out[kk] = (ru, en)[i]

    add(f"{N} — ауа сапасы", f"{N} — качество воздуха", f"{E} — air quality")
    if lang == "en":
        out[f"<h1>{N}</h1>"] = f"<h1>{E}</h1>"
    m = re.search(r'<meta name="description" content="(\S+) ауа сапасы: ([^"]+?)\. Қазгидромет бекеттері мен жел — сағат сайын жаңарады\.">', html)
    if m:
        add(f"{m.group(1)} ауа сапасы: {m.group(2)}. Қазгидромет бекеттері мен жел — сағат сайын жаңарады.",
            f"Качество воздуха, {N}: {_sub(m.group(2), 0)}. Посты Казгидромета и ветер — обновляется каждый час.",
            f"Air quality in {E}: {_sub(m.group(2), 1)}. Kazhydromet stations and wind — updated hourly.")
    m = re.search(r'content="(\S+) ауа сапасының нақты көрсеткіштері: бекеттер мен жел\."', html)
    if m:
        add(f"{m.group(1)} ауа сапасының нақты көрсеткіштері: бекеттер мен жел.",
            f"Реальные показатели качества воздуха, {N}: посты и ветер.", f"Real air quality readings in {E}: stations and wind.")
    m = re.search(r"<p>((?:Қысқы түтін: )?)([^<]+?) — бекеттер мен жел, сағат бойынша</p>", html)
    if m:
        pre, sub = m.group(1), m.group(2)
        pre_t = ("Зимний смог: ", "Winter smog: ")[i] if pre else ""
        body = _sub(sub, i)
        body = body if pre else up(body)
        add(m.group(0), f"<p>{pre_t}{body} — посты и ветер, по часам</p>", f"<p>{pre_t}{body} — stations and wind, hour by hour</p>")
    m = re.search(r"Бекеттер — Қазгидромет картасы \(ecodata\.kz\), сағат сайын\. Жел, күн радиациясы, бұлттылық — Open-Meteo, қала орталығы \(([\d., ]+)\)\.", html)
    if m:
        add(m.group(0), f"Посты — карта Казгидромета (ecodata.kz), каждый час. Ветер, солнечная радиация, облачность — Open-Meteo, центр города ({m.group(1)}).",
            f"Stations — the Kazhydromet map (ecodata.kz), hourly. Wind, solar radiation and cloud cover — Open-Meteo, city centre ({m.group(1)}).")
    # жинау басталған күн
    m = re.search(r"(\S+) бойынша жинау 2026 жылғы (\d+) (қазан)да басталды — тарих әзірге қысқа\.", html)
    if m:
        d, mo = m.group(2), MONTH[m.group(3)]
        add(m.group(0), f"Сбор данных по городу {N} начат {d} {mo[0]} 2026 года — история пока короткая.",
            f"Data collection for {E} began on {d} {mo[1]} 2026 — the history is still short.")
    m = re.search(r"(\S+) бойынша жинау (2026-\d\d-\d\d) басталды\.", html)
    if m:
        add(m.group(0), f"Сбор данных по городу {N} начат {m.group(2)}.", f"Data collection for {E} began on {m.group(2)}.")
    m = re.search(r"(\S+): 2026 жылғы 8–20 қазан аралығы — AirData\.kz архивінен \(CC BY-NC ([\d.]+), Қазгидромет деректері\), 20 қазаннан бастап — біздің сағаттық жинау\. Тарих әзірге қысқа\.", html)
    if m:
        add(m.group(0), f"{N}: с 8 по 20 октября 2026 года — из архива AirData.kz (CC BY-NC {m.group(2)}, данные Казгидромета), с 20 октября — наш почасовой сбор. История пока короткая.",
            f"{E}: 8–20 October 2026 — from the AirData.kz archive (CC BY-NC {m.group(2)}, Kazhydromet data), from 20 October — our hourly collection. The history is still short.")
    m = re.search(r'8–20 қазан аралығы — (<a href="https://airdata\.kz" target="_blank" rel="noopener">AirData\.kz</a>) \(CC BY-NC ([\d.]+)\), одан кейін — біздің жинау\.', html)
    if m:
        add(m.group(0), f"8–20 октября — {m.group(1)} (CC BY-NC {m.group(2)}), далее — наш сбор.", f"8–20 October — {m.group(1)} (CC BY-NC {m.group(2)}), after that — our collection.")
    # басты зат
    for m in re.finditer(r"Басты зат ретінде (\S+) алынған \(жоба шешімі: бекеттердің көбі осыны өлшейді\); қосымша заттар — жоғарыдағы зат таңдау тізімінде\.", html):
        add(m.group(0), f"В качестве основного вещества взят {m.group(1)} (решение проекта: большинство постов измеряют именно его); дополнительные вещества — в списке выбора выше.",
            f"{m.group(1)} was chosen as the main substance (a project decision: most stations measure it); other substances are in the substance list above.")
    m = re.search(r"Басты зат ретінде (\S+) алынған \(жоба шешімі\); қосымша заттар — жоғарыдағы зат таңдау тізімінде\. Бекеттердің кейбірі ([^.<]+?) да өлшейді\.( Бұл қалада ұсақ шаң \(PM2,5, PM10\) өлшенбейді\.)?", html)
    if m:
        extra_ru = " В этом городе мелкая пыль (PM2,5, PM10) не измеряется." if m.group(3) else ""
        extra_en = " Fine dust (PM2.5, PM10) is not measured in this city." if m.group(3) else ""
        add(m.group(0), f"В качестве основного вещества взят {m.group(1)} (решение проекта); дополнительные вещества — в списке выбора выше. Некоторые посты также измеряют {m.group(2).replace(' және ', ' и ')}.{extra_ru}",
            f"{m.group(1)} was chosen as the main substance (a project decision); other substances are in the substance list above. Some stations also measure {m.group(2).replace(' және ', ' and ')}.{extra_en}")
    # көздер тізімі жоқ
    m = re.search(r"(\S+) үшін әзірге жоқ: ластану көздерінің тізімі жиналмаған\. Жел розасы мен «тұрақты жоғары бекеттер» жұмыс істейді\.", html)
    if m:
        add(m.group(0), f"Для города {N} списка источников загрязнения пока нет. Роза ветров и «постоянно высокие посты» работают.",
            f"There is no list of pollution sources for {E} yet. The wind rose and “persistently high stations” work.")
    m = re.search(r"(\S+) үшін ластану көздерінің тізімі әзірге (жоқ|жиналуда) — көзді анықтау кейін қосылады\. Төменде — бекеттер мен жел\.", html)
    if m:
        w_ru, w_en = ("пока нет", "yet") if m.group(2) == "жоқ" else ("пока собирается", "being compiled")
        add(m.group(0), f"Список источников загрязнения для города {N} {w_ru} — определение источника появится позже. Ниже — посты и ветер.",
            (f"The list of pollution sources for {E} is not available yet — source identification will be added later. Below — stations and wind."
             if m.group(2) == "жоқ" else
             f"The list of pollution sources for {E} is being compiled — source identification will be added later. Below — stations and wind."))
    m = re.search(r"(\S+) үшін көздер тізімі — OpenStreetMap пен ашық мәліметтер бойынша жоба: орындары шамамен, биіктіктері болжам, шығарылым құжаттары \(НДВ\) әлі қосылған жоқ\. Нақты орны мен «Көзді анықтау» — құпиясөзбен\. Нәтиже — тек бағыт, нақты кінәлі емес\.", html)
    if m:
        add(m.group(0), f"Список источников для города {N} — черновик по OpenStreetMap и открытым данным: положение примерное, высоты — предположение, документы на выбросы (НДВ) пока не добавлены. Точное положение и «Определение источника» — по паролю. Результат — лишь направление, а не конкретный виновник.",
            f"The list of sources for {E} is a draft based on OpenStreetMap and open data: positions are approximate, heights are assumptions, emission documents (NDV) have not been added yet. Exact positions and “Source identification” need a password. The result shows only a direction, not a specific culprit.")
    m = re.search(r"(\S+) үшін көзді анықтау құпиясөзбен ашылады — төмендегі «Ықтимал көздер» бөлімінде\. Төменде — бекеттер мен жел\.", html)
    if m:
        add(m.group(0), f"Определение источника для города {N} открывается по паролю — в разделе «Возможные источники» ниже. Ниже — посты и ветер.",
            f"Source identification for {E} is unlocked with a password — in the “Possible sources” section below. Below — stations and wind.")
    return out
