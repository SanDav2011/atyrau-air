// Запуск: node --test tests/
const test = require('node:test');
const assert = require('node:assert');
require('../share.js');
const { build, read, nearestHour } = globalThis.AirShare;

test('толық күй: жасау → оқу бірдей', () => {
  const hash = build({ pollutant: 'H2S', hour: '2026-11-07 03', window: 3, points: [{ lat: 47.10651, lng: 51.91499 }] });
  assert.strictEqual(hash, '#p=H2S&t=2026-11-07T03&w=3&c=47.1065,51.9150');
  assert.deepStrictEqual(read(hash), { pollutant: 'H2S', hour: '2026-11-07 03', window: 3, points: [{ lat: 47.1065, lng: 51.915 }] });
});

test('бос және бұзылған hash — бос нәтиже', () => {
  assert.deepStrictEqual(read(''), {});
  assert.deepStrictEqual(read('#'), {});
  assert.deepStrictEqual(read('#method'), {});
  assert.deepStrictEqual(read('#p=<script>&t=ертең&w=5&c=,'), {});
  assert.deepStrictEqual(read('#p=%E0%A4%A'), {}); // бұзылған кодтау
});

test('нүктелер: ең көбі 3, бұзылғандары алынады', () => {
  const pts = [1, 2, 3, 4].map(i => ({ lat: 47 + i / 100, lng: 51.9 }));
  const hash = build({ points: pts });
  assert.strictEqual(hash, '#c=47.0200,51.9000;47.0300,51.9000;47.0400,51.9000'); // соңғы үшеуі
  assert.strictEqual(read('#c=47.1,51.9;abc;95,51;47.2,51.8;47.3,51.7;47.4,51.6').points.length, 3);
  assert.deepStrictEqual(read('#c=95,51').points, undefined);
});

test('нүктесіз сілтемеде c жоқ', () => {
  assert.strictEqual(build({ pollutant: 'PM2.5', hour: '2026-11-07 03', window: 12, points: [] }), '#p=PM2.5&t=2026-11-07T03&w=12');
});

test('ең жақын сағат', () => {
  const hours = ['2026-11-06 22', '2026-11-06 23', '2026-11-07 00', '2026-11-07 01'];
  assert.deepStrictEqual(nearestHour(hours, '2026-11-07 00'), { index: 2, exact: true });
  assert.deepStrictEqual(nearestHour(hours, '2026-10-01 05'), { index: 0, exact: false }); // ескі сілтеме
  assert.deepStrictEqual(nearestHour(hours, '2026-12-01 05'), { index: 3, exact: false });
  assert.strictEqual(nearestHour([], '2026-11-07 00'), null);
});
