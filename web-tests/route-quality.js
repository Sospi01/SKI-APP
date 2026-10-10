// How well connected each resort's route network is (docs/routes.js quality()):
// the share of lift pairs where one can be reached from the top of the other.
// Run from the repo root: node web-tests/route-quality.js [out.json]
const R = require(require('path').join(__dirname, '..', 'docs', 'routes.js')), fs = require('fs');
const st = JSON.parse(/var STATIONS = (.*);/.exec(fs.readFileSync('docs/stations.js', 'utf8'))[1]);
const rows = [];
for (const s of st) {
  const raw = JSON.parse(fs.readFileSync('docs/data/' + s.id + '.json', 'utf8'));
  const net = R.build(raw); const q = R.quality(net);
  rows.push({ name: s.name, cc: s.country, km: s.pisteKm || 0, lifts: (raw.lifts || []).length, q });
}
const bands = [[0.9, 1.01], [0.8, 0.9], [0.6, 0.8], [0, 0.6]];
const big = rows.filter(r => r.km >= 30);
for (const [set, label] of [[rows, 'todas'], [big, '>=30 km']]) {
  const withQ = set.filter(r => r.q != null);
  console.log(label, set.length, 'estaciones;', set.length - withQ.length, 'con <2 remontes');
  for (const [a, b] of bands) console.log(`  ${Math.round(a * 100)}-${Math.min(100, Math.round(b * 100))}%:`, withQ.filter(r => r.q >= a && r.q < b).length);
}
const show = n => rows.filter(r => r.name.startsWith(n)).map(r => `${r.name.slice(0, 28)} ${Math.round(r.q * 100)}%`).join(', ');
['Formigal', "Estació d'Esquí Baqueira", 'Grandvalira', 'Cerler', 'Sierra Nevada', 'La Molina', 'Masella', 'Astún', 'Candanchú', 'Les Trois Vallées', 'Val Thorens', 'Sölden', 'Zermatt', 'Whistler', 'Vail', 'Park City'].forEach(n => { const x = show(n); if (x) console.log(x); });
if (process.argv[2]) fs.writeFileSync(process.argv[2], JSON.stringify(rows));
