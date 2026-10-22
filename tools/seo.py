"""SEO: әр бетке title, description, canonical, Open Graph, Twitter; басты бетке JSON-LD; sitemap.xml.

Іске қосу: python tools/seo.py  (қайта іске қосуға болады — <!-- SEO --> … <!-- /SEO --> блогы ауыстырылады).
make_city.py жаңа қала бетін almaty.html-ден жасайды (Алматының SEO блогымен) — содан кейін осыны қайта іске қос.
OG суреттері: tools/og_images.py → img/og/<бет>.png.
"""
import html, pathlib, re

ROOT = pathlib.Path(__file__).resolve().parent.parent
SITE = 'https://sandav2011.github.io/atyrau-air/'
AUTHOR = 'Санжар Давлетбаев'
SCHOOL = 'Атырау қаласындағы Назарбаев Зияткерлік мектебі (НЗМ)'  # автор — Атырау НЗМ оқушысы

# Қала аты → «-дағы/-дегі» тұлғасы (сипаттама үшін)
LOC = {'Алматы': 'Алматыдағы', 'Астана': 'Астанадағы', 'Ақтөбе': 'Ақтөбедегі', 'Ақтау': 'Ақтаудағы', 'Орал': 'Оралдағы',
       'Шымкент': 'Шымкенттегі', 'Қарағанды': 'Қарағандыдағы', 'Павлодар': 'Павлодардағы', 'Өскемен': 'Өскемендегі',
       'Семей': 'Семейдегі', 'Қостанай': 'Қостанайдағы', 'Тараз': 'Тараздағы', 'Талдықорған': 'Талдықорғандағы',
       'Қызылорда': 'Қызылордадағы', 'Көкшетау': 'Көкшетаудағы', 'Түркістан': 'Түркістандағы', 'Жезқазған': 'Жезқазғандағы',
       'Петропавл': 'Петропавлдағы'}

FIXED = {  # бет → (title, description, og:title, og:description)
    'index.html': ('Таза ауа — Қазақстан ауасы | Ауа сапасы картасы',
                   'Қазақстан қалаларында ауа сапасын бақылау: ластаушы заттар деңгейі, уақыт бойынша өзгерісі және жел бағытына қарай иіс көзінің ықтимал бағыты.',
                   'Таза ауа — Қазақстан ауасы',
                   'Қазақстан қалаларындағы ауа сапасы: нақты бекеттер, жел және Гаусс моделі.'),
    'atyrau.html': ('Атырау — H₂S иісі қайдан келеді? | Қазақстан ауасы',
                    'Атыраудағы күкіртсутек (H₂S) иісінің көзін анықтау. Бекеттер деректері, жел бағыты және Гаусс шлейфі моделі бойынша талдау.',
                    'Атырау — H₂S иісі қайдан келеді?',
                    'Атыраудағы күкіртсутек иісінің ықтимал көздерін нақты бекеттер мен жел бойынша талдау.'),
    'karta.html': ('Қазақстан картасы — ауа сапасы | Қазақстан ауасы',
                   'Қазақстан картасы: облыстар, бекеттер орналасқан елді мекендер, қалалардағы ауа күйі және жел — сағат сайын.',
                   'Қазақстан картасы — ауа сапасы',
                   'Облыстар, бекеттер және қалалардағы ауа күйі бір картада.'),
    'gazdar.html': ('Газдар туралы — H₂S, SO₂, NO₂, PM2,5 | Қазақстан ауасы',
                    'Ауадағы негізгі ластаушы заттар: күкіртсутек, күкірт диоксиді, азот диоксиді, шаң бөлшектері. Шекті мәндер, денсаулыққа әсері және өлшеу әдістері.',
                    'Газдар туралы — H₂S, SO₂, NO₂, PM2,5',
                    'Шекті мәндер, денсаулыққа әсері және өлшеу әдістері.'),
    'about.html': ('Жоба туралы — Қазақстан ауасы',
                   '«Қазақстан ауасы» — ашық жоба. Автор: Санжар Давлетбаев, Атырау НЗМ оқушысы. Дереккөздер: Қазгидромет, Open-Meteo.',
                   'Жоба туралы — Қазақстан ауасы',
                   'Ашық ақпараттық жоба: мақсаты, авторлары, дереккөздері.'),
}

JSON_LD = f'''<script type="application/ld+json">
{{"@context": "https://schema.org", "@type": "WebSite", "name": "Қазақстан ауасы", "url": "{SITE}",
 "description": "Қазақстан қалаларындағы ауа сапасы картасы және талдау",
 "author": {{"@type": "Person", "name": "{AUTHOR}", "affiliation": {{"@type": "EducationalOrganization", "name": "{SCHOOL}"}}}},
 "keywords": "ауа сапасы, Қазақстан, H2S, PM2.5, Қазгидромет, Атырау НЗМ, Назарбаев Зияткерлік мектебі, оқушы жобасы", "inLanguage": "kk"}}
</script>'''


def city_meta(text):
    m = re.search(r'<div class="hero">\s*<h1>(.*?)</h1>\s*<p>(.*?)</p>', text, re.S)
    if not m or m.group(1) not in LOC:
        return None
    city, sub = m.group(1), m.group(2)
    what = sub.split(' — ')[0].replace('Қысқы түтін: ', '')  # заттар тізімі
    what = what[0].lower() + what[1:]
    return (f'{city} — ауа сапасы | Қазақстан ауасы',
            f'{LOC[city]} ауа сапасы: {what}. Қазгидромет бекеттері мен жел — сағат сайын жаңарады.',
            f'{city} — ауа сапасы', f'{LOC[city]} ауа сапасының нақты көрсеткіштері: бекеттер мен жел.')


def block(page, title, desc, og_t, og_d):
    url = SITE if page == 'index.html' else SITE + page
    img = f'{SITE}img/og/{page[:-5]}.png'
    e = lambda s: html.escape(s, quote=True)
    lines = [
        '<!-- SEO (tools/seo.py) -->',
        f'<title>{e(title)}</title>',
        f'<meta name="description" content="{e(desc)}">',
        f'<link rel="canonical" href="{url}">',
        '<meta name="theme-color" content="#0b4f7a">',
        f'<meta name="author" content="{AUTHOR}, Атырау НЗМ оқушысы">',
        '<meta name="robots" content="index, follow">',
        '<meta property="og:site_name" content="Қазақстан ауасы">',
        '<meta property="og:locale" content="kk_KZ">',
        '<meta property="og:type" content="website">',
        f'<meta property="og:title" content="{e(og_t)}">',
        f'<meta property="og:description" content="{e(og_d)}">',
        f'<meta property="og:url" content="{url}">',
        f'<meta property="og:image" content="{img}">',
        '<meta property="og:image:width" content="1200">',
        '<meta property="og:image:height" content="630">',
        '<meta name="twitter:card" content="summary_large_image">',
    ]
    if page in ('index.html', 'about.html'):  # сайт туралы құрылымдық дерек (автор, НЗМ)
        lines.append(JSON_LD)
    lines.append('<!-- /SEO -->')
    return '\n'.join(lines)


def main():
    pages = []
    for p in sorted(ROOT.glob('*.html')):
        t = p.read_text(encoding='utf-8')
        meta = FIXED.get(p.name) or city_meta(t)
        if not meta:
            print('өткізілді:', p.name); continue
        b = block(p.name, *meta)
        if '<!-- SEO (tools/seo.py) -->' in t:
            t = re.sub(r'<!-- SEO \(tools/seo\.py\) -->.*?<!-- /SEO -->', lambda _: b, t, count=1, flags=re.S)
        else:
            assert t.count('<title>') == 1, p.name
            t = re.sub(r'<title>.*?</title>', lambda _: b, t, count=1, flags=re.S)
        p.write_text(t, encoding='utf-8')
        pages.append(p.name)
    # sitemap.xml: басты бет, Атырау және карта жиі жаңарады; анықтама беттері — сирек
    freq = {'index.html': ('daily', '1.0'), 'atyrau.html': ('hourly', '0.9'), 'karta.html': ('daily', '0.8'),
            'gazdar.html': ('monthly', '0.7'), 'about.html': ('monthly', '0.5')}
    urls = sorted(pages, key=lambda n: (n not in freq, n))
    xml = ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for n in urls:
        f, pr = freq.get(n, ('hourly', '0.8'))
        xml.append(f'  <url><loc>{SITE if n == "index.html" else SITE + n}</loc><changefreq>{f}</changefreq><priority>{pr}</priority></url>')
    xml.append('</urlset>')
    (ROOT / 'sitemap.xml').write_text('\n'.join(xml) + '\n', encoding='utf-8')
    print('беттер:', len(pages), '| sitemap.xml жазылды')
    return pages


if __name__ == '__main__':
    main()
