// Көздер мен мұржаларды шифрлау: private/sources.json + private/stacks.json → sources.enc.json (git-ке тек осы түседі).
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
})();
