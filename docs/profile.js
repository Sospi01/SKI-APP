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
  { max: 15, key: 'novice', label: T('Suave (<15%)') },
  { max: 25, key: 'easy', label: T('Moderada (15-25%)') },
  { max: 40, key: 'intermediate', label: T('Pronunciada (25-40%)') },
  { max: Infinity, key: 'advanced', label: T('Muy pronunciada (>40%)') }
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
// The same loop also comes the other way round -- drawn from the bottom up
// one lane and back down the other (several of Formigal's runs) -- which
// reads as a "Λ", a mountain: split at the interior high point then.
// Mirrored in docs/routes.js (splitLoop), which must not ski a lane uphill.
function splitOutAndBack(pts) {
  if (!pts || pts.length < 3 || pts[0][2] == null || pts[pts.length - 1][2] == null) return null;
  if (Math.abs(pts[0][2] - pts[pts.length - 1][2]) > 10) return null;
  function at(sign) {
    var k = 0;
    for (var i = 1; i < pts.length; i++) if (pts[i][2] != null && sign * (pts[i][2] - pts[k][2]) > 0) k = i;
    if (k <= 0 || k >= pts.length - 1) return null;
    var a = sign * (pts[k][2] - pts[0][2]), b = sign * (pts[k][2] - pts[pts.length - 1][2]);
    if (a <= 0 || b <= 0 || Math.min(a, b) < 15 || Math.min(a, b) / Math.max(a, b) < 0.4) return null;
    return [pts.slice(0, k + 1), pts.slice(k).reverse()];
  }
  return at(-1) || at(1);   // "V": split at the low point; "Λ": at the high point
}

function buildElevationProfiles(geomParts) {
  var profiles = [];
  function addProfile(pts) {
    if (pts.length < 2) return;
    if (pts[pts.length - 1][2] > pts[0][2]) pts = pts.slice().reverse();
    var profile = [{ dist: 0, ele: pts[0][2], lon: pts[0][0], lat: pts[0][1] }];
    var cum = 0;
    for (var i = 1; i < pts.length; i++) {
      cum += haversineM(pts[i - 1], pts[i]);
      profile.push({ dist: cum, ele: pts[i][2], lon: pts[i][0], lat: pts[i][1] });
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

// A run's steepest stretch of at least 50 m, in % (the profile's "Tramo más
// pronunciado", over all its segments), or null without elevation data.
// OpenStreetMap's labels mean different things in different countries; this
// is the figure skiers compare. Mirrored by run_max_pitch() in
// build_seo_pages.py for the generated station pages.
function runMaxPitch(geomParts) {
  var best = null;
  buildElevationProfiles(geomParts).forEach(function (p) {
    var st = findSteepestSection(smoothProfile(p, 30), 50);
    if (st && (best == null || Math.abs(st.pitchPct) > best)) best = Math.abs(st.pitchPct);
  });
  return best;
}
// The badge shown next to a run's name: "máx. 38%" with a dot in that
// slope's colour (the profile's pitch zones), beside the official colour.
function maxPitchBadge(pct) {
  var span = document.createElement('span');
  span.className = 'max-pitch';
  span.title = T('Pendiente máxima: el tramo más empinado de al menos 50 m');
  var dot = document.createElement('i');
  dot.style.background = 'var(--diff-' + pitchZoneFor(pct).key + ')';
  span.appendChild(dot);
  span.appendChild(document.createTextNode(T('máx. {0}%', Math.round(pct))));
  return span;
}

function buildProfileChart(raw) {
  var smoothed = smoothProfile(raw, 30);
  var totalDist = smoothed[smoothed.length - 1].dist;
  var eles = smoothed.map(function (p) { return p.ele; });
  var minEle = Math.min.apply(null, eles), maxEle = Math.max.apply(null, eles);
  if (maxEle === minEle) maxEle = minEle + 1;

  var SVGNS = 'http://www.w3.org/2000/svg';
  // padT leaves room above the profile for the scrubber's readout.
  var W = 320, H = 140, padL = 30, padR = 8, padT = 22, padB = 20;
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
  var startLabelText = T('Salida · {0}m', Math.round(smoothed[0].ele));
  var endLabelText = T('Final · {0}m', Math.round(smoothed[smoothed.length - 1].ele));
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

  addProfileScrubber(svg, raw, smoothed, totalDist, W, padL, padR, padT, x, y, minEle);

  var ariaLabel = T('Perfil de altitud de la pista, de {0} a {1} metros a lo largo de {2} metros.', Math.round(smoothed[0].ele), Math.round(smoothed[smoothed.length - 1].ele), Math.round(totalDist));
  if (steepest) {
    var ariaRange = fmtDistRange(steepest.startDist, steepest.endDist);
    ariaLabel += ' ' + T('Tramo más pronunciado: {0}% de pendiente, entre {1} y {2}.', Math.round(Math.abs(steepest.pitchPct)), ariaRange.start, ariaRange.end);
  }
  svg.setAttribute('aria-label', ariaLabel);

  return { svg: svg, steepest: steepest };
}

// Sliding a finger (or the mouse) along the chart shows, for that point,
// the distance from the start, the altitude and the slope of that stretch
// (the same pitch that colours it). Pages with a map can follow along:
// window.onProfilePoint gets the point's [lon, lat], or null when it's gone.
function addProfileScrubber(svg, raw, smoothed, totalDist, W, padL, padR, padT, x, y, minEle) {
  var SVGNS = 'http://www.w3.org/2000/svg';
  function el(tag, attrs) {
    var e = document.createElementNS(SVGNS, tag);
    for (var k in attrs) e.setAttribute(k, attrs[k]);
    return e;
  }
  var g = el('g', { 'pointer-events': 'none', display: 'none' });
  var line = el('line', { y1: padT, y2: y(minEle), stroke: 'var(--text-primary)', 'stroke-width': 1, 'stroke-dasharray': '2 2' });
  var dot = el('circle', { r: 3.4, stroke: 'var(--bg, #fff)', 'stroke-width': 1.5 });
  var box = el('rect', { y: 0, height: 15, rx: 4, fill: 'var(--bg, #fff)', stroke: 'var(--border, #ccc)', 'stroke-width': 0.8 });
  var text = el('text', { y: 10.5, 'text-anchor': 'middle', 'font-size': 9, 'font-weight': 600, 'font-family': "'IBM Plex Sans', sans-serif", fill: 'var(--text-primary)' });
  var tDist = el('tspan', {}), tPct = el('tspan', {});
  text.appendChild(tDist); text.appendChild(tPct);
  g.appendChild(line); g.appendChild(dot); g.appendChild(box); g.appendChild(text);
  svg.appendChild(g);
  svg.style.touchAction = 'pan-y';
  svg.style.cursor = 'crosshair';

  function showAt(clientX) {
    var r = svg.getBoundingClientRect();
    if (!r.width) return;
    var vx = (clientX - r.left) / r.width * W;
    var d = Math.max(0, Math.min(totalDist, (vx - padL) / (W - padL - padR) * totalDist));
    var i = 0;
    while (i < smoothed.length - 2 && smoothed[i + 1].dist < d) i++;
    var a = smoothed[i], b = smoothed[i + 1], span = b.dist - a.dist;
    var f = span > 0 ? (d - a.dist) / span : 0;
    var ele = a.ele + (b.ele - a.ele) * f;
    var pct = span > 0 ? Math.abs((a.ele - b.ele) / span * 100) : 0;
    var color = 'var(--diff-' + pitchZoneFor(pct).key + ')';
    var px = x(d), py = y(ele);
    line.setAttribute('x1', px); line.setAttribute('x2', px);
    dot.setAttribute('cx', px); dot.setAttribute('cy', py); dot.setAttribute('fill', color);
    tDist.textContent = fmtDist(d) + ' · ' + Math.round(ele) + ' m · ';
    tPct.textContent = Math.round(pct) + '%';
    tPct.setAttribute('fill', color);
    g.setAttribute('display', '');
    var w = text.getComputedTextLength ? text.getComputedTextLength() + 12 : 110;
    var cx = Math.max(padL + w / 2, Math.min(W - padR - w / 2, px));
    // In the strip above the profile, so it never hides the profile itself.
    box.setAttribute('x', cx - w / 2); box.setAttribute('width', w); box.setAttribute('y', padT - 19);
    text.setAttribute('x', cx); text.setAttribute('y', padT - 8.5);
    if (typeof window.onProfilePoint === 'function') {
      var ra = raw[i], rb = raw[i + 1] || ra;
      if (ra && ra.lon != null) window.onProfilePoint([ra.lon + (rb.lon - ra.lon) * f, ra.lat + (rb.lat - ra.lat) * f]);
    }
  }
  function hide() {
    g.setAttribute('display', 'none');
    if (typeof window.onProfilePoint === 'function') window.onProfilePoint(null);
  }
  svg.addEventListener('pointerdown', function (e) { showAt(e.clientX); });
  svg.addEventListener('pointermove', function (e) { if (e.pointerType === 'mouse' || e.buttons || e.pressure) showAt(e.clientX); });
  svg.addEventListener('pointerleave', function (e) { if (e.pointerType === 'mouse') hide(); });
}

function renderRunProfile(container, group) {
  var profiles = buildElevationProfiles(group.geomParts);
  if (!profiles.length) {
    container.className = 'run-profile empty';
    container.textContent = T('Todavía no tenemos datos de altitud punto a punto para esta pista.');
    return;
  }
  // A piste mapped as several disconnected segments gets one independent
  // chart per segment (see buildElevationProfiles) instead of one line
  // that would fake a climb/descent across the gap between them.
  profiles.forEach(function (profile, idx) {
    if (profiles.length > 1) {
      var heading = document.createElement('div');
      heading.className = 'run-profile-part-heading';
      heading.textContent = T('Tramo {0} de {1}', idx + 1, profiles.length);
      container.appendChild(heading);
    }
    var chart = buildProfileChart(profile);
    container.appendChild(chart.svg);
    if (chart.steepest) {
      var steepestNote = document.createElement('div');
      steepestNote.className = 'run-profile-steepest';
      var noteRange = fmtDistRange(chart.steepest.startDist, chart.steepest.endDist);
      steepestNote.textContent = T('Tramo más pronunciado: {0}% de pendiente, entre {1} y {2}.', Math.round(Math.abs(chart.steepest.pitchPct)), noteRange.start, noteRange.end);
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
  note.textContent = T('El color indica la inclinación real en cada punto del perfil, no la dificultad oficial de la pista.');
  caption.appendChild(note);
  var tip = document.createElement('div');
  tip.style.marginTop = '2px';
  tip.textContent = T('Desliza por el perfil para ver la distancia desde la salida, la altitud y la pendiente de cada punto.');
  caption.appendChild(tip);
  container.appendChild(caption);
}
