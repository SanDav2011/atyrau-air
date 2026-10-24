"""kk-беттерден ru/ және en/ көшірмелерін жасау (және kk-беттерге ауыстырғыш пен hreflang қосу).
Қолдану: python tools/make_lang.py            (барлық тілдер, BUILT тізіміндегі беттер)
Сөздік: tools/i18n/<тіл>.json = {"common": {kk: аударма}, "<бет>": {kk: аударма}}.
Қазақша бет өзгермейді, тек <!-- lang --> және <!-- hreflang --> белгілері арасы жаңартылады."""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITE = "https://sandav2011.github.io/atyrau-air/"
LANGS = ["ru", "en"]
BUILT = ["about"]  # аударылған беттер; жаңасын осында қос
LABEL = {"kk": "KK", "ru": "RU", "en": "EN"}
LOCALE = {"ru": "ru_RU", "en": "en_US"}
KK_LETTERS = re.compile("[ӘәҒғҚқҢңӨөҰұҮүҺһІі]")
CYRILLIC = re.compile("[А-Яа-яЁё]")
ALLOWED_KK = ["ҚР ДСМ", "Қазақша", "Русский"]  # ресми белгілеу, аударылмайды

LANG_CSS = ("/* lang */ header nav details.lang { position: relative; margin-left: 4px; } "
            "header nav details.lang summary { list-style: none; cursor: pointer; color: #fff; font-weight: 700; font-size: 14px; min-height: 44px; "
            "display: inline-flex; align-items: center; gap: 4px; padding: 0 8px; border-radius: 10px; user-select: none; } "
            "header nav details.lang summary::-webkit-details-marker { display: none; } "
            "header nav details.lang summary::after { content: '▾'; font-size: 12px; } "
            "header nav details.lang .menu { position: absolute; right: 0; top: 100%; z-index: 20; min-width: 130px; background: #fff; border-radius: 12px; "
            "box-shadow: 0 8px 30px rgba(0,40,90,.3); padding: 6px; display: grid; } "
            "header nav details.lang .menu a { color: #10233f !important; padding: 0 12px !important; font-size: 15px !important; min-height: 44px; border-radius: 8px; "
            "display: flex !important; align-items: center; text-decoration: none; } "
            "header nav details.lang .menu a::after { display: none !important; } "
            "header nav details.lang .menu a:hover { background: #e8f1fb; } "
            "header nav details.lang .menu a.cur { font-weight: 800; } /* /lang */")
NAME = {"kk": "Қазақша", "ru": "Русский", "en": "English"}


def page_url(frm, to, page):
    """frm тілі бетінен to тіліндегі бетке қатысты сілтеме."""
    prefix = "" if frm == "kk" else "../"
    base = "" if to == "kk" else to + "/"
    f = "" if page == "index" else page + ".html"
    return (prefix + base + f) or "./"


def strip_marked(html, name):
    return re.sub(r"[ \t]*<!-- %s -->.*?<!-- /%s -->\n?" % (name, name), "", html, flags=re.S)


def add_lang_blocks(html, page, cur):
    """hreflang және тіл ауыстырғышты қосу (қайталап орындауға болады)."""
    html = strip_marked(html, "hreflang")
    html = strip_marked(html, "lang")
    html = re.sub(r"/\* lang \*/.*?/\* /lang \*/ ?", "", html, flags=re.S)
    hl = "<!-- hreflang -->\n"
    for lg in ["kk"] + LANGS:
        hl += '<link rel="alternate" hreflang="%s" href="%s">\n' % (
            lg, SITE + ("" if lg == "kk" else lg + "/") + ("" if page == "index" else page + ".html"))
    hl += '<link rel="alternate" hreflang="x-default" href="%s">\n<!-- /hreflang -->\n' % (
        SITE + ("" if page == "index" else page + ".html"))
    html = re.sub(r'(<link rel="canonical"[^>]*>\n)', lambda m: m.group(1) + hl, html, count=1)
    menu = "".join('<a href="%s" hreflang="%s"%s>%s</a>' % (
        page_url(cur, lg, page), lg, ' class="cur" aria-current="true"' if lg == cur else "", NAME[lg])
        for lg in ["kk"] + LANGS)
    det = ('<details class="lang"><summary aria-label="Language">%s</summary><div class="menu">%s</div></details>'
           '<script>document.addEventListener("click",function(e){document.querySelectorAll("details.lang[open]").forEach(function(d){if(!d.contains(e.target))d.open=false})})</script>') % (LABEL[cur], menu)
    html = html.replace("</nav>", "  <!-- lang -->%s<!-- /lang -->\n  </nav>" % det, 1)
    html = html.replace("</style>", LANG_CSS + "\n</style>", 1)
    return html


def build(page, lang):
    html = (ROOT / (page + ".html")).read_text(encoding="utf-8")
    tr = json.loads((ROOT / "tools" / "i18n" / (lang + ".json")).read_text(encoding="utf-8"))
    d = {**tr.get("common", {}), **tr.get(page, {})}
    keys = sorted(d, key=len, reverse=True)
    used = set()
    rx = re.compile("|".join(re.escape(k) for k in keys)) if keys else None

    def sub(m):
        used.add(m.group(0))
        return d[m.group(0)]
    if rx:
        html = rx.sub(sub, html)
    # Бет ішіндегі кілттер: тек осы беттің сөздігіндегілер ескіргенін білдіреді
    stale = [k for k in tr.get(page, {}) if k not in used]

    html = html.replace('<html lang="kk">', '<html lang="%s">' % lang)
    html = html.replace('content="kk_KZ"', 'content="%s"' % LOCALE[lang])
    html = html.replace('"inLanguage": "kk"', '"inLanguage": "%s"' % lang)
    # canonical және og:url — осы тілдің бетіне
    html = re.sub(r'(<link rel="canonical" href=|<meta property="og:url" content=)"%s' % re.escape(SITE),
                  lambda m: '%s"%s%s/' % (m.group(1), SITE, lang), html)
    # ресурстар жолы: data/, img/, model.js т.б. — бір деңгей жоғары
    html = re.sub(r"""(['"])(data/|img/|sources[\w.]*\.json|(?:model|scene|mol)\.js)""", r"\1../\2", html)
    html = re.sub(r'(<script src=")((?:model|scene|mol)\.js)', r"\1../\2", html)

    # ішкі сілтемелер: аударылған бет — сол жерде, әйтпесе қазақша түпнұсқаға
    def fix_href(m):
        h = m.group(2)
        if re.match(r"^(https?:|mailto:|#|\.\./)", h):
            return m.group(0)
        pg = "index" if h in ("./", "") else re.sub(r"\.html.*$", "", h)
        if pg in BUILT or (pg == "index" and "index" in BUILT):
            return m.group(0)
        return m.group(1) + ("../" if h == "./" else "../" + h) + m.group(3)
    html = re.sub(r'(<a\b[^>]*?\bhref=")([^"]*)(")', fix_href, html)

    html = add_lang_blocks(html, page, lang)
    out = ROOT / lang
    out.mkdir(exist_ok=True)
    (out / (page + ".html")).write_text(html, encoding="utf-8")

    # Қалған қазақ әріптері (ресми белгілеуден басқа) — аударылмаған жолдар
    left = []
    for ln in html.splitlines():
        t = ln
        for a in ALLOWED_KK:
            t = t.replace(a, "")
        if KK_LETTERS.search(t) or (lang == "en" and CYRILLIC.search(t)):
            left.append(ln.strip()[:160])
    return stale, left


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    bad = False
    for page in BUILT:
        src = ROOT / (page + ".html")
        src.write_text(add_lang_blocks(src.read_text(encoding="utf-8"), page, "kk"), encoding="utf-8")
        for lang in LANGS:
            stale, left = build(page, lang)
            print("%s/%s.html: жасалды" % (lang, page))
            for k in stale:
                print("  ЕСКІРГЕН кілт:", k[:80])
            for ln in left:
                bad = True
                print("  АУДАРЫЛМАҒАН:", ln)
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
