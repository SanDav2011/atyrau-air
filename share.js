/* Картамен бөлісу: картаның күйі ↔ сілтеменің # бөлігі.
   Мысал: atyrau.html#p=H2S&t=2026-11-07T03&w=3&c=47.1065,51.9150
   p — зат, t — сағат (жергілікті уақыт), w — талдау кезеңі (1/3/6/12), c — шағым нүктелері (ең көбі 3, «;» арқылы).
   # бөлігі серверге жіберілмейді — нүкте тек сілтемені алған адамға көрінеді. */
(function () {
  const POL_RE = /^[A-Za-z0-9.,()_-]{1,20}$/;          // беттегі зат атауы ережесімен бірдей
  const HOUR_RE = /^\d{4}-\d{2}-\d{2}T\d{2}$/;
  const PT_RE = /^-?\d{1,2}(\.\d{1,6})?,-?\d{1,3}(\.\d{1,6})?$/;
  const WINDOWS = [1, 3, 6, 12];
  const MAX_PTS = 3;

  const validPt = p => p && Number.isFinite(p.lat) && Number.isFinite(p.lng) && Math.abs(p.lat) <= 90 && Math.abs(p.lng) <= 180;

  // күй → '#p=…&t=…' (бос болса — '')
  function build(st) {
    const parts = [];
    if (st.pollutant && POL_RE.test(st.pollutant)) parts.push('p=' + encodeURIComponent(st.pollutant));
    if (st.hour && HOUR_RE.test(String(st.hour).replace(' ', 'T'))) parts.push('t=' + String(st.hour).replace(' ', 'T'));
    if (WINDOWS.includes(+st.window)) parts.push('w=' + +st.window);
    const pts = (st.points || []).filter(validPt).slice(-MAX_PTS); // ең соңғы қойылған нүктелер
    if (pts.length) parts.push('c=' + pts.map(p => p.lat.toFixed(4) + ',' + p.lng.toFixed(4)).join(';'));
    return parts.length ? '#' + parts.join('&') : '';
  }

  // '#…' → { pollutant, hour: 'YYYY-MM-DD HH', window, points } — тек дұрыс өрістер
  function read(hash) {
    const out = {};
    const s = String(hash || '').replace(/^#/, '');
    for (const kv of s ? s.split('&') : []) {
      const i = kv.indexOf('=');
      if (i < 1) continue;
      const k = kv.slice(0, i);
      let v;
      try { v = decodeURIComponent(kv.slice(i + 1)); } catch { continue; }
      if (k === 'p' && POL_RE.test(v)) out.pollutant = v;
      else if (k === 't' && HOUR_RE.test(v)) out.hour = v.replace('T', ' ');
      else if (k === 'w' && WINDOWS.includes(+v)) out.window = +v;
      else if (k === 'c') {
        const pts = v.split(';').filter(x => PT_RE.test(x))
          .map(x => { const [lat, lng] = x.split(',').map(Number); return { lat, lng }; }).filter(validPt).slice(0, MAX_PTS);
        if (pts.length) out.points = pts;
      }
    }
    return out;
  }

  // сағаттар тізімінен ('YYYY-MM-DD HH', өсу ретімен) ең жақынын табу → { index, exact } немесе null
  function nearestHour(hours, h) {
    if (!hours.length || !h) return null;
    const exact = hours.indexOf(h);
    if (exact >= 0) return { index: exact, exact: true };
    const ms = x => Date.parse(x.replace(' ', 'T') + ':00:00Z');
    const t = ms(h);
    if (!Number.isFinite(t)) return null;
    let best = 0;
    for (let i = 1; i < hours.length; i++) if (Math.abs(ms(hours[i]) - t) < Math.abs(ms(hours[best]) - t)) best = i;
    return { index: best, exact: false };
  }

  globalThis.AirShare = { build, read, nearestHour, MAX_PTS };
})();
