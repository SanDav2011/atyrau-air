/* Газ молекулаларының суреттері (SVG) — «Газдар туралы» беті үшін.
   Атом түстері — химиядағы әдеттегі CPK түстері; бұрыштар — молекуланың нақты пішіні. */
const MOL_ATOM = {
  H: { r: 13, fill: '#f1f5f9', text: '#334155' },
  C: { r: 20, fill: '#475569', text: '#fff' },
  N: { r: 20, fill: '#2563eb', text: '#fff' },
  O: { r: 20, fill: '#dc2626', text: '#fff' },
  S: { r: 24, fill: '#eab308', text: '#422006' },
};

// Ортадағы атом + бұрышпен орналасқан көршілер. ang — байланыстар арасындағы бұрыш (градус).
function molBent(center, side, ang, len) {
  const a = (90 + ang / 2) * Math.PI / 180, b = (90 - ang / 2) * Math.PI / 180;
  return { atoms: [[center, 0, -18], [side, len * Math.cos(a), -18 + len * Math.sin(a)], [side, len * Math.cos(b), -18 + len * Math.sin(b)]],
           bonds: [[0, 1], [0, 2]] };
}

const MOL_SHAPES = {
  H2S: { ...molBent('S', 'H', 92, 52), note: 'бұрыш 92°' },
  SO2: { ...molBent('S', 'O', 119, 60), note: 'бұрыш 119°', double: true },
  NO2: { ...molBent('N', 'O', 134, 58), note: 'бұрыш 134°', double: true },
  O3:  { ...molBent('O', 'O', 117, 56), note: 'бұрыш 117°', double: true },
  NO:  { atoms: [['N', -30, 0], ['O', 30, 0]], bonds: [[0, 1]], note: 'екі атом', double: true },
  CO:  { atoms: [['C', -30, 0], ['O', 30, 0]], bonds: [[0, 1]], note: 'екі атом', triple: true },
  // NH3 — пирамида: N жоғарыда, үш H төменде (біреуі алдыңғы жақта — үлкенірек)
  NH3: { atoms: [['N', 0, -20], ['H', -46, 14], ['H', 46, 14], ['H', 0, 30, 1.15]], bonds: [[0, 1], [0, 2], [0, 3]], note: 'пирамида, 107°' },
};

function molSVG(key, size = 120) {
  const m = MOL_SHAPES[key];
  if (!m) return '';
  const id = 'm' + key.replace(/\W/g, '');
  const grads = Object.entries(MOL_ATOM).map(([el, a]) =>
    `<radialGradient id="${id}${el}" cx="35%" cy="30%" r="70%"><stop offset="0" stop-color="#fff" stop-opacity=".85"/><stop offset=".35" stop-color="${a.fill}"/><stop offset="1" stop-color="${a.fill}" stop-opacity=".95"/></radialGradient>`).join('');
  const lines = m.bonds.map(([i, j]) => {
    const [, x1, y1] = m.atoms[i], [, x2, y2] = m.atoms[j];
    const n = m.triple ? 3 : m.double ? 2 : 1, dx = y2 - y1, dy = x1 - x2, L = Math.hypot(dx, dy) || 1;
    return Array.from({ length: n }, (_, k) => {
      const o = (k - (n - 1) / 2) * 7, ox = dx / L * o, oy = dy / L * o;
      return `<line x1="${x1 + ox}" y1="${y1 + oy}" x2="${x2 + ox}" y2="${y2 + oy}" stroke="#94a3b8" stroke-width="5" stroke-linecap="round"/>`;
    }).join('');
  }).join('');
  // Артқы атомдар алдымен салынады (y кіші — артта), алдыңғысы соңында
  const order = m.atoms.map((a, i) => i).sort((i, j) => (m.atoms[i][3] || 1) - (m.atoms[j][3] || 1));
  const atoms = order.map(i => {
    const [el, x, y, k = 1] = m.atoms[i], a = MOL_ATOM[el], r = a.r * k;
    return `<circle cx="${x}" cy="${y}" r="${r}" fill="url(#${id}${el})" stroke="rgba(0,0,0,.25)"/>` +
           `<text x="${x}" y="${y + r * 0.38}" text-anchor="middle" font-size="${r * 1.0}" font-weight="700" fill="${a.text}" font-family="system-ui,sans-serif">${el}</text>`;
  }).join('');
  return `<svg viewBox="-80 -70 160 130" width="${size}" height="${size * 130 / 160}" role="img" aria-label="${key} молекуласы, ${m.note}">` +
         `<defs>${grads}</defs>${lines}${atoms}<text x="0" y="56" text-anchor="middle" font-size="12" fill="#6b7280" font-family="system-ui,sans-serif">${m.note}</text></svg>`;
}

// PM — молекула емес, бөлшек: шашпен салыстыру (шамамен 70 мкм, PM10 = 10, PM2,5 = 2,5)
function pmSVG(size = 120) {
  return `<svg viewBox="0 0 160 130" width="${size}" height="${size * 130 / 160}" role="img" aria-label="Шаш, PM10 және PM2,5 өлшемін салыстыру">` +
    `<circle cx="70" cy="58" r="49" fill="#e7d3b5" stroke="#b08d57"/><text x="70" y="40" text-anchor="middle" font-size="11" fill="#6b4f1d" font-family="system-ui,sans-serif">шаш ≈70 мкм</text>` +
    `<circle cx="70" cy="66" r="7" fill="#64748b"/><text x="70" y="88" text-anchor="middle" font-size="11" fill="#334155" font-family="system-ui,sans-serif">PM10</text>` +
    `<circle cx="132" cy="66" r="1.8" fill="#334155"/><text x="132" y="88" text-anchor="middle" font-size="11" fill="#334155" font-family="system-ui,sans-serif">PM2,5</text>` +
    `<text x="80" y="124" text-anchor="middle" font-size="12" fill="#6b7280" font-family="system-ui,sans-serif">масштаб сақталған</text></svg>`;
}
