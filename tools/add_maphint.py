"""Қала беттеріне картаның «?» көмегін қосу (қайталап орындауға болады). Қолдану: python tools/add_maphint.py [бет ...]"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKIP = {"index", "about", "gazdar", "karta"}

CSS = """/* maphint */
  .maphelp { position: relative; }
  .mh-btn { width: 44px; height: 44px; border-radius: 50%; border: 2px solid rgba(0,0,0,.2); background: #fff; color: #0b4f7a; font: 800 22px/1 Onest, system-ui, sans-serif; cursor: pointer; box-shadow: 0 2px 8px rgba(0,40,90,.3); }
  .mh-btn:hover { background: #f1f6fb; }
  .mh-card { position: absolute; right: 0; top: 50px; width: min(300px, calc(100vw - 150px)); background: #fff; border-radius: 12px; padding: 12px 14px 12px 14px; box-shadow: 0 8px 30px rgba(0,40,90,.35); font-size: 13.5px; line-height: 1.45; color: #10233f; text-align: left; }
  .mh-card[hidden] { display: none; }
  .mh-card ul { margin: 6px 0 0; padding-left: 18px; }
  .mh-card li { margin: 4px 0; }
  .mh-x { position: absolute; top: 2px; right: 2px; width: 44px; height: 44px; border: 0; background: none; font-size: 24px; color: #5b6b82; cursor: pointer; }
  .mh-card > b { display: block; padding-right: 36px; }
  /* /maphint */"""

JS = """/* maphint-js */
/* ===== Карта көмегі: «?» түймесі; бірінші кіргенде өзі ашылады, жапқаннан кейін қайта шықпайды ===== */
(() => {
  const KEY = 'atyrau-air-maphint';
  const Help = L.Control.extend({ options: { position: 'topright' }, onAdd() {
    const box = L.DomUtil.create('div', 'maphelp');
    box.innerHTML = '<button type="button" class="mh-btn" aria-label="Карта қалай жұмыс істейді" aria-expanded="false">?</button>'
      + '<div class="mh-card" hidden role="dialog" aria-label="Карта қалай жұмыс істейді"><button type="button" class="mh-x" aria-label="Жабу">×</button>'
      + '<b>Карта қалай жұмыс істейді</b><ul>'
      + '<li><b style="display:inline">Бекетті басыңыз</b> — өлшемдері мен графигі.</li>'
      + '<li><b style="display:inline">Картаны басыңыз</b> — иіс сезілген жерді белгілейді (📍); күлгін сызық — сол жерге жел келген жақ.</li>'
      + '<li><b style="display:inline">Қоңыр сызықтар</b> — бекеттен желге қарсы бағыт: көз осы жақта болуы мүмкін.</li>'
      + '<li><b style="display:inline">Төменгі жүгіргі</b> — сағатты ауыстыру; ▶ — анимация.</li></ul></div>';
    L.DomEvent.disableClickPropagation(box); L.DomEvent.disableScrollPropagation(box);
    const btn = box.querySelector('.mh-btn'), card = box.querySelector('.mh-card');
    const show = on => { card.hidden = !on; btn.setAttribute('aria-expanded', on ? 'true' : 'false');
      if (!on) { try { localStorage.setItem(KEY, '1'); } catch {} } };
    btn.addEventListener('click', () => show(card.hidden));
    box.querySelector('.mh-x').addEventListener('click', () => show(false));
    let seen = false; try { seen = localStorage.getItem(KEY) === '1'; } catch {}
    if (!seen) show(true);
    return box;
  } });
  new Help().addTo(map);
})();
/* /maphint-js */

"""


def patch(path):
    t = path.read_text(encoding="utf-8")
    t = re.sub(r"/\* maphint \*/.*?/\* /maphint \*/\n?", "", t, flags=re.S)
    t = re.sub(r"/\* maphint-js \*/.*?/\* /maphint-js \*/\n\n?", "", t, flags=re.S)
    assert t.count("</style>") >= 1 and t.count("/* ===== Ықтимал көздер:") == 1, path.name
    t = t.replace("</style>", "  " + CSS + "\n</style>", 1)
    t = t.replace("/* ===== Ықтимал көздер:", JS + "/* ===== Ықтимал көздер:", 1)
    path.write_text(t, encoding="utf-8")
    print("ok", path.name)


if __name__ == "__main__":
    names = sys.argv[1:] or sorted(p.stem for p in ROOT.glob("*.html") if p.stem not in SKIP and not p.stem.startswith(("google", "yandex")))
    for n in names:
        patch(ROOT / (n + ".html"))
