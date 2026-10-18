/* Газ молекулаларының суреттері — «Газдар туралы» беті үшін.
   Суреттер: Wikimedia Commons, public domain (автор Ben Mills), img/mol/*.png.
   Түстер: S сары, O қызыл, N көк, C сұр, H ақ. */
const MOL_INFO = {
  H2S: { note: 'бұрыш 92°',            file: 'Hydrogen-sulfide-3D-balls.png' },
  SO2: { note: 'бұрыш 119°',           file: 'Sulfur-dioxide-3D-balls.png' },
  NO2: { note: 'бұрыш 134°',           file: 'Nitrogen-dioxide-3D-balls.png' },
  NO:  { note: 'екі атом',             file: 'Nitric-oxide-3D-vdW.png' },
  CO:  { note: 'екі атом',             file: 'Carbon-monoxide-3D-balls.png' },
  O3:  { note: 'бұрыш 117°',           file: 'Ozone-CRC-MW-3D-balls.png' },
  NH3: { note: 'пирамида, бұрыш 107°', file: 'Ammonia-3D-balls-A.png' },
};

// Молекула суреті + астында бұрышы; сурет Commons бетіне сілтеме береді
function molImg(key, width = 160) {
  const m = MOL_INFO[key];
  if (!m) return '';
  return `<figure class="mol" style="margin:0;text-align:center">` +
    `<a href="https://commons.wikimedia.org/wiki/File:${m.file}" target="_blank" rel="noopener">` +
    `<img src="img/mol/${key}.png" width="${width}" alt="${key} молекуласы, ${m.note}" loading="lazy" style="max-width:100%;height:auto"></a>` +
    `<figcaption style="font-size:13px;color:#6b7280">${m.note}</figcaption></figure>`;
}

// PM — молекула емес, бөлшек: шашпен салыстыру (шаш ≈70 мкм, PM10 = 10, PM2,5 = 2,5; масштаб сақталған)
function pmSVG(size = 160) {
  return `<svg viewBox="0 0 160 130" width="${size}" height="${size * 130 / 160}" role="img" aria-label="Шаш, PM10 және PM2,5 өлшемін салыстыру">` +
    `<circle cx="70" cy="58" r="49" fill="#e7d3b5" stroke="#b08d57"/><text x="70" y="40" text-anchor="middle" font-size="11" fill="#6b4f1d" font-family="system-ui,sans-serif">шаш ≈70 мкм</text>` +
    `<circle cx="70" cy="66" r="7" fill="#64748b"/><text x="70" y="88" text-anchor="middle" font-size="11" fill="#334155" font-family="system-ui,sans-serif">PM10</text>` +
    `<circle cx="132" cy="66" r="1.8" fill="#334155"/><text x="132" y="88" text-anchor="middle" font-size="11" fill="#334155" font-family="system-ui,sans-serif">PM2,5</text>` +
    `<text x="80" y="124" text-anchor="middle" font-size="12" fill="#6b7280" font-family="system-ui,sans-serif">масштаб сақталған</text></svg>`;
}
