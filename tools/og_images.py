"""OG суреттері (әлеуметтік желіде сілтеме жібергенде шығатын сурет), 1200×630 → img/og/<бет>.png.

Әр бет үшін: «Қазақстан ауасы» белгісі, үлкен тақырып және бір жол түсініктеме — сайттың аспан/су стилінде.
Edge headless арқылы скриншот. Іске қосу: python tools/og_images.py
"""
import html, pathlib, re, subprocess, tempfile

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / 'img' / 'og'
EDGE = r'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe'

SPECIAL = {  # бет → (тақырып, түсініктеме)
    'index': ('Таза ауа', 'Қазақстан қалаларындағы ауа сапасы — бекеттер мен жел'),
    'karta': ('Қазақстан картасы', 'Облыстар, бекеттер және қалалардағы ауа күйі'),
    'gazdar': ('Газдар туралы', 'H₂S, SO₂, NO₂, PM2,5 — шекті мәндер және денсаулыққа әсері'),
    'about': ('Жоба туралы', 'Ашық ақпараттық жоба · НЗМ оқушысының жобасы'),
    'atyrau': ('Атырау', 'H₂S иісі қайдан келеді? Бекеттер, жел және Гаусс моделі'),
}

TPL = '''<!doctype html><html><head><meta charset="utf-8">
<link href="https://fonts.googleapis.com/css2?family=Onest:wght@500;800&display=block" rel="stylesheet">
<style>
html,body{{margin:0;width:1200px;height:630px;overflow:hidden}}
body{{font-family:Onest,system-ui,sans-serif;color:#fff;position:relative;
  background:linear-gradient(180deg,#0b4f9c 0%,#2a8be0 38%,#8fd3ff 52%,#27c2d6 53%,#0f8fb5 78%,#0b6f95 100%)}}
.sea{{position:absolute;left:0;right:0;top:333px;height:6px;background:rgba(255,255,255,.55);filter:blur(2px)}}
.brand{{position:absolute;left:64px;top:52px;font-weight:800;font-size:34px;letter-spacing:.01em;text-shadow:0 2px 10px rgba(0,40,90,.35)}}
.brand small{{display:block;font-weight:500;font-size:20px;opacity:.85;margin-top:4px}}
h1{{position:absolute;left:64px;right:64px;top:170px;margin:0;font-weight:800;font-size:{size}px;line-height:1.05;letter-spacing:-.02em;
  text-shadow:0 4px 24px rgba(0,40,90,.35)}}
p{{position:absolute;left:64px;right:64px;top:420px;margin:0;font-weight:500;font-size:38px;line-height:1.25;text-shadow:0 2px 12px rgba(0,50,90,.45)}}
.url{{position:absolute;left:64px;bottom:40px;font-weight:500;font-size:24px;opacity:.9}}
</style></head><body><div class="sea"></div>
<div class="brand">Қазақстан ауасы<small>ауа сапасы · бекеттер · жел</small></div>
<h1>{title}</h1><p>{sub}</p><div class="url">sandav2011.github.io/atyrau-air</div></body></html>'''


def pages():
    for p in sorted(ROOT.glob('*.html')):
        slug = p.stem
        if slug in SPECIAL:
            yield slug, *SPECIAL[slug]; continue
        t = p.read_text(encoding='utf-8')
        m = re.search(r'<div class="hero">\s*<h1>(.*?)</h1>\s*<p>(.*?)</p>', t, re.S)
        if m:
            sub = m.group(2).split(' — ')[0].replace('Қысқы түтін: ', '')
            yield slug, m.group(1), 'Ауа сапасы: ' + sub[0].lower() + sub[1:]


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    tmp = pathlib.Path(tempfile.mkdtemp())
    n = 0
    for slug, title, sub in pages():
        size = 150 if len(title) <= 12 else 112
        f = tmp / f'{slug}.html'
        f.write_text(TPL.format(title=html.escape(title), sub=html.escape(sub), size=size), encoding='utf-8')
        png = OUT / f'{slug}.png'
        subprocess.run([EDGE, '--headless=new', '--disable-gpu', '--hide-scrollbars', '--window-size=1200,630',
                        '--virtual-time-budget=4000', f'--screenshot={png}', f.as_uri()], check=True, timeout=120,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        n += 1
    print('суреттер:', n, OUT)


if __name__ == '__main__':
    main()
