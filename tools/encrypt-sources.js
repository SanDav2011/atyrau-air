// Көздер мен мұржаларды шифрлау: private/sources.json + private/stacks.json → sources.enc.json, және ашық карта үшін sources.public.json (орны шамамен).
// Құпиясөз — private/.password (git-те жоқ). Шифр: AES-GCM 256, кілт — PBKDF2-SHA256, 600 000 айналым.
// Іске қосу: node tools/encrypt-sources.js
const fs = require('fs');
const path = require('path');
const { webcrypto } = require('crypto');
const { subtle } = webcrypto;
const getRandomValues = a => webcrypto.getRandomValues(a);

const root = path.join(__dirname, '..');
const read = f => fs.readFileSync(path.join(root, f), 'utf8');
const b64 = buf => Buffer.from(buf).toString('base64');
const ITER = 600000;

(async () => {
  const password = read('private/.password').trim();
  const payload = JSON.stringify({ sources: JSON.parse(read('private/sources.json')), stacks: JSON.parse(read('private/stacks.json')) });
  const salt = getRandomValues(new Uint8Array(16)), iv = getRandomValues(new Uint8Array(12));
  const base = await subtle.importKey('raw', new TextEncoder().encode(password), 'PBKDF2', false, ['deriveKey']);
  const key = await subtle.deriveKey({ name: 'PBKDF2', hash: 'SHA-256', salt, iterations: ITER }, base, { name: 'AES-GCM', length: 256 }, false, ['encrypt']);
  const ct = await subtle.encrypt({ name: 'AES-GCM', iv }, key, new TextEncoder().encode(payload));
  const out = { v: 1, kdf: 'PBKDF2-SHA256', iter: ITER, salt: b64(salt), iv: b64(iv), ct: b64(ct) };
  fs.writeFileSync(path.join(root, 'sources.enc.json'), JSON.stringify(out) + '\n');
  console.log('sources.enc.json дайын:', payload.length, 'байт шифрланды');

  // Ашық картаға — тек атауы, түрі және ШАМАМЕН орны (≈500 м торға дөңгелектенген). Мұржа топтары (pollutants бар) кірмейді.
  const STEP_LAT = 0.0045, STEP_LNG = 0.0066; // ≈ 500 м (Атырау ендігінде)
  const snap = (v, step) => +(Math.round(v / step) * step).toFixed(4);
  const pub = JSON.parse(read('private/sources.json'))
    .filter(s => s.lat != null && !s.pollutants)
    .map(s => ({ id: s.id, name: s.name, kind: s.kind, lat: snap(s.lat, STEP_LAT), lng: snap(s.lng, STEP_LNG) }));
  fs.writeFileSync(path.join(root, 'sources.public.json'), JSON.stringify(pub, null, 1) + '\n');
  console.log('sources.public.json дайын:', pub.length, 'көз, орны шамамен');
})();
