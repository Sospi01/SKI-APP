// Which resorts the route planner is open for: those whose network is well
// connected (docs/routes.js quality() >= 0.8, the share of lift pairs where
// one can be reached from the top of the other). Too slow to work out on a
// phone for the big ones (Les 3 Vallées: seconds), so it is done here, after
// the weekly data refresh, into docs/routes-ok.json:
//   { "min": 0.8, "s": [ids of resorts], "d": [ids of resorts whose whole domain map is] }
// Ids are cut to their first 12 characters (unique across the catalogue).
// Run from the repo root: node data-pipeline/scripts/build_routes_ok.js
const fs = require('fs'), path = require('path');
const ROOT = path.join(__dirname, '..', '..');
const R = require(path.join(ROOT, 'docs', 'routes.js'));
const MIN = 0.8, ID = 12;
const src = fs.readFileSync(path.join(ROOT, 'docs', 'stations.js'), 'utf8');
const stations = JSON.parse(/var STATIONS = (.*);/.exec(src)[1]);
const groups = JSON.parse(/var STATION_GROUPS = (.*);/.exec(src)[1]);
const cache = {};
function load(id) {
  return cache[id] || (cache[id] = JSON.parse(fs.readFileSync(path.join(ROOT, 'docs', 'data', id + '.json'), 'utf8')));
}
const ok = q => q != null && q >= MIN;
const s = [], d = [];
for (const st of stations) if (ok(R.quality(R.build(load(st.id))))) s.push(st.id.slice(0, ID));
for (const g of groups) {
  // As the map shows it (index.html showDomainMap): every resort's runs and lifts together.
  const all = { runs: [], lifts: [] };
  g.forEach(id => { const x = load(id); all.runs.push(...(x.runs || [])); all.lifts.push(...(x.lifts || [])); });
  if (ok(R.quality(R.build(all)))) g.forEach(id => d.push(id.slice(0, ID)));
}
if (new Set(stations.map(x => x.id.slice(0, ID))).size !== stations.length) throw new Error('ids not unique at ' + ID + ' characters');
fs.writeFileSync(path.join(ROOT, 'docs', 'routes-ok.json'), JSON.stringify({ min: MIN, s: s, d: d }) + '\n');
console.log(`routes open in ${s.length} of ${stations.length} resorts; ${d.length} resorts in well-connected domains`);
