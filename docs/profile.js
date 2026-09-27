// Elevation-profile charts for runs, shared by the app (index.html) and the
// generated station pages (/estacion/<slug>/). Plain global functions: loaded
// with a classic <script> before the page's own code.
// OpenSkiMap's run geometry carries elevation as a third [lon, lat, ele]
// value per point (same source the pipeline already uses for ascent_m/
// avg_pitch_percent); this turns that into a distance-vs-elevation profile,
// colored by how steep each stretch actually is.
function haversineM(a, b) {
  var R = 6371000;
  var lon1 = a[0] * Math.PI / 180, lat1 = a[1] * Math.PI / 180;
  var lon2 = b[0] * Math.PI / 180, lat2 = b[1] * Math.PI / 180;
  var dLat = lat2 - lat1, dLon = lon2 - lon1;
  var h = Math.sin(dLat / 2) * Math.sin(dLat / 2) + Math.cos(lat1) * Math.cos(lat2) * Math.sin(dLon / 2) * Math.sin(dLon / 2);
  return 2 * R * Math.asin(Math.sqrt(h));
}

// Pitch-zone thresholds mirror how skiers already read piste colors
// (green/blue/red/black), applied here to the *local* steepness of a
// stretch rather than the run's overall difficulty rating.
var PITCH_ZONES = [
  { max: 15, key: 'novice', label: 'Suave (<15%)' },
  { max: 25, key: 'easy', label: 'Moderada (15-25%)' },
  { max: 40, key: 'intermediate', label: 'Pronunciada (25-40%)' },
  { max: Infinity, key: 'advanced', label: 'Muy pronunciada (>40%)' }
];
function pitchZoneFor(pct) {
  var p = Math.abs(pct);
  for (var i = 0; i < PITCH_ZONES.length; i++) if (p < PITCH_ZONES[i].max) return PITCH_ZONES[i];
  return PITCH_ZONES[PITCH_ZONES.length - 1];
}

// Builds one { dist, ele } series (meters) per geometry part of a run
// group, each oriented so it reads start -> end in the skiing direction
// (downhill, left to right) regardless of which way OSM happened to draw
// it. Parts are never bridged into each other: OpenStreetMap often maps
// one named piste as several disconnected way segments (see "N tramos" in
// the run list), and the gap between one segment's end and the next one's
// start isn't skiable terrain -- joining them into a single line would
// fabricate a climb or descent that doesn't exist.
// Some pistes are mapped in OpenStreetMap as a single closed-loop way --
// starting and ending at (almost) the same point -- that runs down to the
// bottom and back up along a second, roughly parallel lane (a
// there-and-back trace, or two side-by-side lanes digitized as one line)
// instead of two separate ways. Charted naively that reads as a "V":
// descending then climbing back up, which isn't a real climb on skis.
// Detect the loop by its endpoints sharing (almost) the same elevation
// with a genuine, comparably-sized drop on each side of the interior low
// point, and split there so each side becomes its own downhill profile
// instead of one misleading dip. The same-elevation-endpoints check is
// what keeps this from also firing on a real traverse that legitimately
// dips and climbs to a different elevation than it started at.
function splitOutAndBack(pts) {
  var minIdx = 0;
  for (var i = 1; i < pts.length; i++) if (pts[i][2] < pts[minIdx][2]) minIdx = i;
  if (minIdx <= 0 || minIdx >= pts.length - 1) return null;
  var descentBefore = pts[0][2] - pts[minIdx][2];
  var ascentAfter = pts[pts.length - 1][2] - pts[minIdx][2];
  if (descentBefore <= 0 || ascentAfter <= 0) return null;
  if (Math.abs(pts[0][2] - pts[pts.length - 1][2]) > 10) return null;
  var smaller = Math.min(descentBefore, ascentAfter);
  var larger = Math.max(descentBefore, ascentAfter);
  if (smaller < 15 || smaller / larger < 0.4) return null;
  return [pts.slice(0, minIdx + 1), pts.slice(minIdx).reverse()];
}

function buildElevationProfiles(geomParts) {
  var profiles = [];
  function addProfile(pts) {
    if (pts.length < 2) return;
    if (pts[pts.length - 1][2] > pts[0][2]) pts = pts.slice().reverse();
    var profile = [{ dist: 0, ele: pts[0][2] }];
    var cum = 0;
    for (var i = 1; i < pts.length; i++) {
      cum += haversineM(pts[i - 1], pts[i]);
      profile.push({ dist: cum, ele: pts[i][2] });
    }
    // Drop degenerate slivers (near-duplicate points, mapping noise) too
    // short to show a meaningful profile of their own.
    if (cum >= 15) profiles.push(profile);
  }
  (geomParts || []).forEach(function (part) {
    var pts = (part || []).filter(function (p) { return p && p.length >= 3; });
    if (pts.length < 2) return;
    var halves = splitOutAndBack(pts);
    if (halves) halves.forEach(addProfile);
    else addProfile(pts);
  });
  return profiles;
}

// OSM elevation samples are noisy at the point-to-point scale -- smooth
// over a ~30m window before computing pitch, so the coloring reflects the
// terrain's real steepness rather than digitization jitter.
function smoothProfile(profile, windowM) {
  return profile.map(function (p, i) {
    var lo = i, hi = i;
    while (lo > 0 && p.dist - profile[lo - 1].dist < windowM / 2) lo--;
    while (hi < profile.length - 1 && profile[hi + 1].dist - p.dist < windowM / 2) hi++;
    var sum = 0, n = 0;
    for (var k = lo; k <= hi; k++) { sum += profile[k].ele; n++; }
    return { dist: p.dist, ele: sum / n };
  });
}

// Formats a distance in meters as "850 m" below 1km, "1.5 km" above.
function fmtDist(m) {
  return m < 1000 ? Math.round(m) + ' m' : (Math.round(m / 100) / 10) + ' km';
}

// Formats a start/end pair for the steepest-section callout, falling back
// to extra decimal precision if the default rounding would otherwise make
// both ends of a short, steep stretch print as the same value.
function fmtDistRange(startM, endM) {
  function f(m, decimals) {
    return m < 1000 ? Math.round(m) + ' m' : (m / 1000).toFixed(decimals) + ' km';
  }
  var decimals = 1;
  while (f(startM, decimals) === f(endM, decimals) && decimals < 3) decimals++;
  return { start: f(startM, decimals), end: f(endM, decimals) };
}

// Picks an X-axis tick spacing close to the requested "every ~0.5km",
// widening it for longer runs and narrowing it for short ones so a run
// of a few hundred meters still gets a handful of ticks.
function pickDistanceStep(totalDist) {
  if (totalDist <= 1200) return 200;
  if (totalDist <= 3000) return 500;
  if (totalDist <= 8000) return 1000;
  return 2000;
}

// Finds the steepest stretch of at least windowM meters, sliding a window
// over the smoothed profile. A fixed physical window (rather than just the
// steepest pair of adjacent smoothed points) keeps the reported stretch
// long enough to describe meaningfully instead of a near-zero-length spike.
function findSteepestSection(smoothed, windowM) {
  var best = null;
  for (var i = 0; i < smoothed.length; i++) {
    var startP = smoothed[i];
    var j = i;
    while (j < smoothed.length - 1 && smoothed[j + 1].dist - startP.dist < windowM) j++;
    // Sparse points (few samples over a segment) can mean the very next
    // point already exceeds windowM -- fall back to it rather than
    // skipping this starting point entirely, since that's the finest
    // resolution the data actually offers here.
    if (j === i) j = Math.min(i + 1, smoothed.length - 1);
    if (j === i) continue;
    var endP = smoothed[j];
    var d = endP.dist - startP.dist;
    if (d <= 0) continue;
    var pitchPct = ((startP.ele - endP.ele) / d) * 100;
    if (!best || Math.abs(pitchPct) > Math.abs(best.pitchPct)) {
      best = { pitchPct: pitchPct, startDist: startP.dist, endDist: endP.dist };
    }
  }
  return best;
}

function buildProfileChart(raw) {
  var smoothed = smoothProfile(raw, 30);
  var totalDist = smoothed[smoothed.length - 1].dist;
  var eles = smoothed.map(function (p) { return p.ele; });
  var minEle = Math.min.apply(null, eles), maxEle = Math.max.apply(null, eles);
  if (maxEle === minEle) maxEle = minEle + 1;

  var SVGNS = 'http://www.w3.org/2000/svg';
  var W = 320, H = 128, padL = 30, padR = 8, padT = 10, padB = 20;
  function x(d) { return padL + (d / totalDist) * (W - padL - padR); }
  function y(e) { return padT + (1 - (e - minEle) / (maxEle - minEle)) * (H - padT - padB); }

  var svg = document.createElementNS(SVGNS, 'svg');
  svg.setAttribute('viewBox', '0 0 ' + W + ' ' + H);
  svg.setAttribute('role', 'img');

  // gridlines at min/max elevation + their labels
  [minEle, maxEle].forEach(function (e) {
    var line = document.createElementNS(SVGNS, 'line');
    line.setAttribute('x1', padL); line.setAttribute('x2', W - padR);
    line.setAttribute('y1', y(e)); line.setAttribute('y2', y(e));
    line.setAttribute('class', 'run-profile-gridline');
    svg.appendChild(line);
    var label = document.createElementNS(SVGNS, 'text');
    label.setAttribute('x', padL - 4); label.setAttribute('y', y(e) + 3);
    label.setAttribute('text-anchor', 'end'); label.setAttribute('class', 'run-profile-endlabel');
    label.textContent = Math.round(e) + 'm';
    svg.appendChild(label);
  });

  // X-axis distance ticks, spaced ~every 0.5km (adaptive for short/long runs).
  // Skipped near either end so their labels don't collide with Salida/Final
  // (margin sized from those labels' actual text length, not a flat guess).
  var startLabelText = 'Salida · ' + Math.round(smoothed[0].ele) + 'm';
  var endLabelText = 'Final · ' + Math.round(smoothed[smoothed.length - 1].ele) + 'm';
  var CHAR_W = 4.4;
  var startLabelEndX = padL + startLabelText.length * CHAR_W + 6;
  var endLabelStartX = (W - padR) - endLabelText.length * CHAR_W - 6;
  var step = pickDistanceStep(totalDist);
  for (var t = step; t < totalDist; t += step) {
    var tx = x(t);
    if (tx < startLabelEndX || tx > endLabelStartX) continue;
    var tickLine = document.createElementNS(SVGNS, 'line');
    tickLine.setAttribute('x1', x(t)); tickLine.setAttribute('x2', x(t));
    tickLine.setAttribute('y1', padT); tickLine.setAttribute('y2', y(minEle));
    tickLine.setAttribute('class', 'run-profile-gridline');
    svg.appendChild(tickLine);
    var tickLabel = document.createElementNS(SVGNS, 'text');
    tickLabel.setAttribute('x', x(t)); tickLabel.setAttribute('y', H - 4);
    tickLabel.setAttribute('text-anchor', 'middle'); tickLabel.setAttribute('class', 'run-profile-endlabel');
    tickLabel.textContent = fmtDist(t);
    svg.appendChild(tickLabel);
  }

  // colored fill, one quad per smoothed segment, colored by that segment's pitch
  for (var i = 0; i < smoothed.length - 1; i++) {
    var a = smoothed[i], b = smoothed[i + 1];
    var dDist = b.dist - a.dist;
    if (dDist <= 0) continue;
    var pitchPct = ((a.ele - b.ele) / dDist) * 100;
    var zone = pitchZoneFor(pitchPct);
    var poly = document.createElementNS(SVGNS, 'polygon');
    var pts = [
      x(a.dist) + ',' + y(minEle), x(a.dist) + ',' + y(a.ele),
      x(b.dist) + ',' + y(b.ele), x(b.dist) + ',' + y(minEle)
    ].join(' ');
    poly.setAttribute('points', pts);
    poly.setAttribute('fill', 'var(--diff-' + zone.key + ')');
    poly.setAttribute('opacity', '0.55');
    svg.appendChild(poly);
  }

  var steepest = findSteepestSection(smoothed, 50);

  // outline on top for a crisp silhouette
  var outlinePts = smoothed.map(function (p) { return x(p.dist).toFixed(1) + ',' + y(p.ele).toFixed(1); }).join(' ');
  var outline = document.createElementNS(SVGNS, 'polyline');
  outline.setAttribute('points', outlinePts);
  outline.setAttribute('fill', 'none');
  outline.setAttribute('stroke', 'var(--text-primary)');
  outline.setAttribute('stroke-width', '1.4');
  outline.setAttribute('stroke-linejoin', 'round');
  outline.setAttribute('vector-effect', 'non-scaling-stroke');
  svg.appendChild(outline);

  // baseline
  var baseline = document.createElementNS(SVGNS, 'line');
  baseline.setAttribute('x1', padL); baseline.setAttribute('x2', W - padR);
  baseline.setAttribute('y1', y(minEle)); baseline.setAttribute('y2', y(minEle));
  baseline.setAttribute('class', 'run-profile-axis');
  svg.appendChild(baseline);

  // start / end markers + labels
  [{ p: smoothed[0], anchor: 'start', dx: 0 }, { p: smoothed[smoothed.length - 1], anchor: 'end', dx: 0 }].forEach(function (e) {
    var dot = document.createElementNS(SVGNS, 'circle');
    dot.setAttribute('cx', x(e.p.dist)); dot.setAttribute('cy', y(e.p.ele)); dot.setAttribute('r', 2.6);
    dot.setAttribute('fill', 'var(--text-primary)');
    svg.appendChild(dot);
  });
  var startLabel = document.createElementNS(SVGNS, 'text');
  startLabel.setAttribute('x', x(smoothed[0].dist)); startLabel.setAttribute('y', H - 4);
  startLabel.setAttribute('text-anchor', 'start'); startLabel.setAttribute('class', 'run-profile-endlabel');
  startLabel.textContent = startLabelText;
  svg.appendChild(startLabel);
  var endLabel = document.createElementNS(SVGNS, 'text');
  endLabel.setAttribute('x', x(smoothed[smoothed.length - 1].dist)); endLabel.setAttribute('y', H - 4);
  endLabel.setAttribute('text-anchor', 'end'); endLabel.setAttribute('class', 'run-profile-endlabel');
  endLabel.textContent = endLabelText;
  svg.appendChild(endLabel);

  var ariaLabel = 'Perfil de altitud de la pista, de ' + Math.round(smoothed[0].ele) + ' a ' + Math.round(smoothed[smoothed.length - 1].ele) + ' metros a lo largo de ' + Math.round(totalDist) + ' metros.';
  if (steepest) {
    var ariaRange = fmtDistRange(steepest.startDist, steepest.endDist);
    ariaLabel += ' Tramo más pronunciado: ' + Math.round(Math.abs(steepest.pitchPct)) + '% de pendiente, entre ' + ariaRange.start + ' y ' + ariaRange.end + '.';
  }
  svg.setAttribute('aria-label', ariaLabel);

  return { svg: svg, steepest: steepest };
}

function renderRunProfile(container, group) {
  var profiles = buildElevationProfiles(group.geomParts);
  if (!profiles.length) {
    container.className = 'run-profile empty';
    container.textContent = 'Todavía no tenemos datos de altitud punto a punto para esta pista.';
    return;
  }
  // A piste mapped as several disconnected segments gets one independent
  // chart per segment (see buildElevationProfiles) instead of one line
  // that would fake a climb/descent across the gap between them.
  profiles.forEach(function (profile, idx) {
    if (profiles.length > 1) {
      var heading = document.createElement('div');
      heading.className = 'run-profile-part-heading';
      heading.textContent = 'Tramo ' + (idx + 1) + ' de ' + profiles.length;
      container.appendChild(heading);
    }
    var chart = buildProfileChart(profile);
    container.appendChild(chart.svg);
    if (chart.steepest) {
      var steepestNote = document.createElement('div');
      steepestNote.className = 'run-profile-steepest';
      var noteRange = fmtDistRange(chart.steepest.startDist, chart.steepest.endDist);
      steepestNote.textContent = 'Tramo más pronunciado: ' + Math.round(Math.abs(chart.steepest.pitchPct)) + '% de pendiente, entre ' + noteRange.start + ' y ' + noteRange.end + '.';
      container.appendChild(steepestNote);
    }
  });
  var caption = document.createElement('div');
  caption.className = 'run-profile-caption';
  PITCH_ZONES.forEach(function (z) {
    var key = document.createElement('span'); key.className = 'zone-key';
    var sw = document.createElement('span'); sw.className = 'zone-swatch'; sw.style.background = 'var(--diff-' + z.key + ')';
    key.appendChild(sw); key.appendChild(document.createTextNode(z.label));
    caption.appendChild(key);
  });
  var note = document.createElement('div');
  note.style.marginTop = '4px';
  note.textContent = 'El color indica la inclinación real en cada punto del perfil, no la dificultad oficial de la pista.';
  caption.appendChild(note);
  container.appendChild(caption);
}
