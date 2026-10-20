/* Ортақ көрініс (басты бет пен Қазақстан картасы үшін): аспан + жылжитын бұлттар мен ауа ағыны,
   толқынды су беті, су астындағы жарық сәулелері, құм және балдырлар.
   Қолдану: const sc = createScene(canvas, { horizon: 0.46, timeOfDay: false, dim: 0, onResize });
            әр кадрда sc.draw(t) — t секундпен; sc.surfaceY(x, t), sc.horizon, sc.W, sc.H, sc.ctx. */
function createScene(cv, opts = {}) {
  const ctx = cv.getContext('2d');
  const o = Object.assign({ horizon: 0.46, timeOfDay: false, dim: 0, onResize: null }, opts);
  const S = { ctx, W: 0, H: 0, horizon: 0, draw, surfaceY, resize, setDim: v => { o.dim = v; } };
  let DPR = 1, clouds = [], streaks = [], rays = [], raySprite = null, weeds = [], stars = [];

  function makeWeeds() { // балдыр бұталары: шеттерге көбірек, ортасында аз
    const list = [], n = Math.max(8, Math.round(S.W / 70));
    for (let i = 0; i < n; i++) {
      let x = Math.random() * S.W;
      if (Math.abs(x - S.W / 2) < S.W * 0.2) x += (x < S.W / 2 ? -1 : 1) * S.W * 0.2;
      const blades = 2 + Math.floor(Math.random() * 3);
      for (let b = 0; b < blades; b++) list.push({
        x: x + (Math.random() - 0.5) * 26, h: S.H * (0.12 + Math.random() * 0.2), w: 5 + Math.random() * 6,
        ph: Math.random() * 6, sp: 0.6 + Math.random() * 0.6, hue: 140 + Math.random() * 30, light: 28 + Math.random() * 14 });
    }
    return list.sort((a, b) => a.h - b.h);
  }
  function drawWeed(w, t) { // жапырақ: түбінен ұшына дейін жіңішкеретін, синус бойынша иілетін таспа
    const base = S.H + 4, seg = 14, left = [], right = [];
    for (let i = 0; i <= seg; i++) {
      const s = i / seg, y = base - w.h * s;
      const sway = Math.sin(t * w.sp + w.ph + s * 2.2) * 18 * s * s + Math.sin(t * 1.7 + w.ph + s * 5) * 3 * s;
      const half = w.w * (1 - s * 0.85) * (0.8 + 0.25 * Math.sin(s * 9 + w.ph));
      left.push([w.x + sway - half, y]); right.push([w.x + sway + half, y]);
    }
    ctx.beginPath(); ctx.moveTo(left[0][0], left[0][1]);
    for (const [x, y] of left) ctx.lineTo(x, y);
    for (let i = right.length - 1; i >= 0; i--) ctx.lineTo(right[i][0], right[i][1]);
    ctx.closePath();
    const g = ctx.createLinearGradient(0, base, 0, base - w.h);
    g.addColorStop(0, `hsla(${w.hue},55%,${w.light - 10}%,0.95)`); g.addColorStop(1, `hsla(${w.hue - 15},60%,${w.light + 14}%,0.75)`);
    ctx.fillStyle = g; ctx.fill();
    ctx.strokeStyle = `hsla(${w.hue},60%,${w.light + 25}%,0.35)`; ctx.lineWidth = 1; ctx.stroke();
  }
  function makeRay() { // жұмсақ шетті жарық сәулесі (бір рет салынады)
    const c = document.createElement('canvas'); c.width = 200; c.height = 400;
    const g = c.getContext('2d'); g.filter = 'blur(14px)';
    const lg = g.createLinearGradient(0, 0, 0, 400); lg.addColorStop(0, 'rgba(255,255,255,1)'); lg.addColorStop(1, 'rgba(255,255,255,0)');
    g.fillStyle = lg; g.beginPath(); g.moveTo(85, 0); g.lineTo(115, 0); g.lineTo(170, 400); g.lineTo(30, 400); g.fill();
    return c;
  }
  function makeCloud(w) { // бұлт суреті бір рет салынады; шетінде бос орын — бұлдыр шеті кесілмесін
    const pad = Math.round(w * 0.22), h = w * 0.42, c = document.createElement('canvas');
    c.width = w + pad * 2; c.height = h + pad * 2;
    const g = c.getContext('2d');
    g.filter = `blur(${Math.round(w * 0.05)}px)`;
    g.fillStyle = 'rgba(255,255,255,0.9)';
    for (let i = 0; i < 7; i++) {
      const x = pad + w * (0.2 + Math.random() * 0.6), y = pad + h * (0.45 + Math.random() * 0.2), r = w * (0.07 + Math.random() * 0.08);
      g.beginPath(); g.ellipse(x, y, r * 1.6, r, 0, 0, Math.PI * 2); g.fill();
    }
    return c;
  }

  function resize() {
    DPR = Math.min(window.devicePixelRatio || 1, 1.5);
    S.W = innerWidth; S.H = innerHeight;
    cv.width = S.W * DPR; cv.height = S.H * DPR; ctx.setTransform(DPR, 0, 0, DPR, 0, 0);
    S.horizon = Math.round(S.H * o.horizon);
    clouds = Array.from({ length: 6 }, () => {
      const w = Math.max(180, S.W * (0.22 + Math.random() * 0.22));
      return { img: makeCloud(w), x: Math.random() * (S.W + w) - w, y: S.H * (0.04 + Math.random() * 0.26) * (o.horizon / 0.46), v: 6 + Math.random() * 10, a: 0.35 + Math.random() * 0.4 };
    });
    streaks = Array.from({ length: 26 }, () => ({ x: Math.random() * S.W, y: Math.random() * S.horizon * 0.85, len: 60 + Math.random() * 140, v: 30 + Math.random() * 50 }));
    rays = Array.from({ length: 9 }, (_, i) => ({ x: (i + 0.5) / 9 + (Math.random() - 0.5) * 0.06, w: 0.03 + Math.random() * 0.05, ph: Math.random() * 6 }));
    stars = Array.from({ length: 120 }, () => ({ x: Math.random() * S.W, y: Math.random() * S.horizon * 0.9, r: Math.random() * 1.3 + 0.3, ph: Math.random() * 6 }));
    raySprite = makeRay();
    weeds = makeWeeds();
    if (o.onResize) o.onResize(S);
  }

  function surfaceY(x, t) { // су бетінің биіктігі — үш синус қосындысы
    return S.horizon + 6 * Math.sin(x * 0.011 + t * 1.1) + 3 * Math.sin(x * 0.029 - t * 1.6) + 1.4 * Math.sin(x * 0.071 + t * 2.4);
  }

  /* Тәулік уақыты (Атырау, UTC+5): аспан түстері мен түн/жұлдыз үлесі сағатқа қарай тегіс өзгереді */
  const SKY = [ // [сағат, жоғары, орта, көкжиек асты, көкжиек, түн үлесі]
    [0,  '#050b22', '#0d1a40', '#1b2c5c', '#2c3f73', 1],
    [5,  '#0a1838', '#26407a', '#6c6aa0', '#e9a98a', 0.6],
    [7,  '#2d63c4', '#6aa1df', '#f2d3b8', '#fff1e0', 0],
    [10, '#0b46b5', '#3d86d8', '#cfe6f7', '#f4fbff', 0],
    [17, '#0b46b5', '#3d86d8', '#cfe6f7', '#f4fbff', 0],
    [19, '#253f99', '#6a6fb8', '#f0a37c', '#ffd9a8', 0.1],
    [21, '#0b1638', '#1d2c62', '#3a3f7a', '#6a5a8a', 0.8],
    [24, '#050b22', '#0d1a40', '#1b2c5c', '#2c3f73', 1],
  ];
  const hex = h => [1, 3, 5].map(i => parseInt(h.slice(i, i + 2), 16));
  const mix = (a, b, k) => { const x = hex(a), y = hex(b); return `rgb(${x.map((v, i) => Math.round(v + (y[i] - v) * k)).join(',')})`; };
  function skyAt(hour) {
    let i = 0; while (i < SKY.length - 2 && hour >= SKY[i + 1][0]) i++;
    const a = SKY[i], b = SKY[i + 1], k = (hour - a[0]) / (b[0] - a[0]);
    return { c: [1, 2, 3, 4].map(j => mix(a[j], b[j], k)), night: a[5] + (b[5] - a[5]) * k };
  }
  S.localHour = () => { const d = new Date(); return (d.getUTCHours() + 5 + d.getUTCMinutes() / 60) % 24; };

  function draw(t) {
    const { W, H, horizon } = S;
    const sky = o.timeOfDay ? skyAt(S.localHour()) : { c: ['#0b46b5', '#3d86d8', '#cfe6f7', '#f4fbff'], night: 0 };
    // 1) аспан
    let g = ctx.createLinearGradient(0, 0, 0, horizon);
    g.addColorStop(0, sky.c[0]); g.addColorStop(0.45, sky.c[1]); g.addColorStop(0.82, sky.c[2]); g.addColorStop(1, sky.c[3]);
    ctx.fillStyle = g; ctx.fillRect(0, 0, W, horizon + 20);
    if (sky.night > 0.05) for (const s of stars) { // жұлдыздар жыпылықтайды
      ctx.globalAlpha = sky.night * (0.5 + 0.5 * Math.sin(t * 2 + s.ph));
      ctx.fillStyle = '#fff'; ctx.beginPath(); ctx.arc(s.x, s.y, s.r, 0, 7); ctx.fill();
    }
    // 2) бұлттар мен ауа ағыны (солдан оңға)
    for (const c of clouds) {
      const x = ((c.x + c.v * t) % (W + c.img.width)) - c.img.width;
      ctx.globalAlpha = c.a * (1 - sky.night * 0.7); ctx.drawImage(c.img, x, c.y);
    }
    ctx.globalAlpha = 1; ctx.lineCap = 'round'; ctx.lineWidth = 1.2;
    for (const s of streaks) {
      const x = ((s.x + s.v * t) % (W + s.len * 2)) - s.len, y = s.y + 4 * Math.sin(t * 0.8 + s.x);
      const lg = ctx.createLinearGradient(x, 0, x + s.len, 0);
      lg.addColorStop(0, 'rgba(255,255,255,0)'); lg.addColorStop(0.5, 'rgba(255,255,255,0.28)'); lg.addColorStop(1, 'rgba(255,255,255,0)');
      ctx.strokeStyle = lg; ctx.beginPath(); ctx.moveTo(x, y);
      ctx.quadraticCurveTo(x + s.len / 2, y - 5 * Math.sin(t + s.y), x + s.len, y); ctx.stroke();
    }
    // 3) су (беті толқынды)
    const step = 8;
    ctx.beginPath(); ctx.moveTo(0, H);
    for (let x = 0; x <= W + step; x += step) ctx.lineTo(x, surfaceY(x, t));
    ctx.lineTo(W, H); ctx.closePath();
    g = ctx.createLinearGradient(0, horizon, 0, H);
    g.addColorStop(0, '#10a9d6'); g.addColorStop(0.08, '#22c4e4'); g.addColorStop(0.45, '#56dcef'); g.addColorStop(0.72, '#9cecf0'); g.addColorStop(1, '#d9f4e6');
    ctx.fillStyle = g; ctx.fill();
    ctx.save(); ctx.clip();
    // 4) су астындағы жарық сәулелері (түнде әлсіз)
    for (const r of rays) {
      const cx = (r.x + 0.015 * Math.sin(t * 0.5 + r.ph)) * W, w = r.w * W * 3.2;
      ctx.globalAlpha = (0.16 + 0.1 * Math.sin(t * 0.7 + r.ph)) * (1 - sky.night * 0.8);
      ctx.drawImage(raySprite, cx - w / 2, horizon, w, (H - horizon) * 0.95);
    }
    ctx.globalAlpha = 1;
    // 5) құм түбі және балдырлар
    const sandTop = H * 0.8;
    g = ctx.createLinearGradient(0, sandTop, 0, H);
    g.addColorStop(0, 'rgba(236,220,178,0)'); g.addColorStop(0.35, 'rgba(236,220,178,0.75)'); g.addColorStop(1, 'rgba(244,229,192,1)');
    ctx.fillStyle = g; ctx.fillRect(0, sandTop, W, H - sandTop);
    for (const w of weeds) drawWeed(w, t);
    // судың үстіңгі қабатының астыңғы көлеңкесі
    ctx.beginPath();
    for (let x = 0; x <= W + step; x += step) ctx.lineTo(x, surfaceY(x, t) + 16);
    for (let x = W + step; x >= 0; x -= step) ctx.lineTo(x, surfaceY(x, t));
    ctx.fillStyle = 'rgba(8,120,170,0.28)'; ctx.fill();
    // түн — суды қараңғылатамыз
    if (sky.night > 0.05) { ctx.fillStyle = `rgba(4,20,50,${0.55 * sky.night})`; ctx.fillRect(0, horizon - 10, W, H); }
    ctx.restore();
    // 6) су бетіндегі ақ жарқыл сызығы
    ctx.beginPath();
    for (let x = 0; x <= W + step; x += step) { const y = surfaceY(x, t); x ? ctx.lineTo(x, y) : ctx.moveTo(x, y); }
    ctx.strokeStyle = `rgba(255,255,255,${0.75 - 0.4 * sky.night})`; ctx.lineWidth = 2; ctx.stroke();
    ctx.beginPath();
    for (let x = 0; x <= W + step; x += step) { const y = surfaceY(x, t) - 3; x ? ctx.lineTo(x, y) : ctx.moveTo(x, y); }
    ctx.strokeStyle = 'rgba(255,255,255,0.25)'; ctx.lineWidth = 5; ctx.stroke();
    // 7) күңгірттеу (карта алдыңғы планда болғанда)
    if (o.dim > 0) { ctx.fillStyle = `rgba(6,30,60,${o.dim})`; ctx.fillRect(0, 0, W, H); }
  }

  addEventListener('resize', resize);
  resize();
  return S;
}
