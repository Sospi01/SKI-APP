// The resort map in 3D: the satellite image draped over the terrain, with the
// runs and lifts on top. Loaded on demand by index.html (the "3D" button of
// the map), after MapLibre GL (docs/vendor/maplibre-gl-*). It draws the same
// features as the 2D map (mapState.features) and hands taps back to it, so
// the run panel, the tap popup and the profile are the 2D map's own.
//
// Elevation: AWS Terrain Tiles (Mapzen's open terrain, "terrarium" encoding,
// public and free, CORS enabled). Imagery: the same Esri tiles as the 2D map.
(function () {
  var TERRAIN = 'https://s3.amazonaws.com/elevation-tiles-prod/terrarium/{z}/{x}/{y}.png';
  var IMAGERY = 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}';
  var PITCH = 62, EXAGGERATION = 1.3;

  // "var(--diff-easy)" or "hsl(208 88% 41%)" -> "#1a73c9" (WebGL needs a plain colour).
  function resolveColor(css, el) {
    var m = /^var\((--[^)]+)\)$/.exec(String(css || '').trim());
    if (m) css = getComputedStyle(el).getPropertyValue(m[1]).trim() || '#888';
    var ctx = document.createElement('canvas').getContext('2d');
    ctx.fillStyle = '#888';
    ctx.fillStyle = css;
    return ctx.fillStyle;
  }

  function line(coords, props) {
    return { type: 'Feature', properties: props, geometry: { type: 'LineString', coordinates: coords.map(function (p) { return [p[0], p[1]]; }) } };
  }
  function collection(list) { return { type: 'FeatureCollection', features: list }; }

  // Compass bearing (degrees) from a to b, both [lon, lat].
  function bearingBetween(a, b) {
    var r = Math.PI / 180;
    var y = Math.sin((b[0] - a[0]) * r) * Math.cos(b[1] * r);
    var x = Math.cos(a[1] * r) * Math.sin(b[1] * r) - Math.sin(a[1] * r) * Math.cos(b[1] * r) * Math.cos((b[0] - a[0]) * r);
    return (Math.atan2(y, x) / r + 360) % 360;
  }

  // Where to put the camera: looking uphill, unless turning it (up to 90°)
  // frames the resort much better -- a long resort seen side-on from a
  // narrow phone screen would mostly fall outside it.
  function frame(pts, uphill, W, H) {
    var lat0 = pts[0][1], lon0 = pts[0][0], k = Math.cos(lat0 * Math.PI / 180), M = 111320;
    var xy = pts.map(function (p) { return [(p[0] - lon0) * M * k, (p[1] - lat0) * M]; });
    var best = null;
    [0, -45, 45, -90, 90].forEach(function (d) {
      var b = (uphill + d + 360) % 360, r = b * Math.PI / 180, s = Math.sin(r), c = Math.cos(r);
      var x0 = Infinity, x1 = -Infinity, y0 = Infinity, y1 = -Infinity;
      xy.forEach(function (q) {
        var x = q[0] * c - q[1] * s, y = q[0] * s + q[1] * c;   // screen right, screen up
        x0 = Math.min(x0, x); x1 = Math.max(x1, x); y0 = Math.min(y0, y); y1 = Math.max(y1, y);
      });
      var fit = Math.min((W - 60) / Math.max(x1 - x0, 50), (H - 60) / Math.max(y1 - y0, 50));   // px per metre
      var score = fit * (1 - Math.abs(d) / 400);   // a slight preference for looking uphill
      if (!best || score > best.score * 1.15) {
        var cx = (x0 + x1) / 2, cy = (y0 + y1) / 2;   // back to east/north
        var e = cx * c + cy * s, n = -cx * s + cy * c;
        best = { score: score, bearing: b, fit: fit, center: [lon0 + e / (M * k), lat0 + n / M] };
      }
    });
    // MapLibre: 512 px tiles, so metres per pixel = 40075016 cos(lat) / (512 * 2^zoom).
    best.zoom = Math.min(16, Math.log2(40075016 * Math.cos(best.center[1] * Math.PI / 180) * best.fit / 512));
    return best;
  }

  // o: { container, features, mode ('diff' | 'slope'), runColor(f), liftColor, haloColor,
  //      slopeStretches(part), attribution, onTap(feature | null, clientX, clientY), onReady(), onError() }
  function open(o) {
    var el = o.container;
    var color = function (c) { return resolveColor(c, el); };
    var runs = [], slope = [], lifts = [], pts = [];
    o.features.forEach(function (f, fi) {
      var part = f.isLift ? f.geo : f.geomPart;
      if (!part || part.length < 2) return;
      pts = pts.concat(part);
      if (f.isLift) { lifts.push(line(part, { fi: fi })); return; }
      var c = color(o.runColor(f));
      runs.push(line(part, { fi: fi, color: c }));
      var st = o.slopeStretches(part);
      if (!st.length) slope.push(line(part, { fi: fi, color: c }));
      st.forEach(function (s) { slope.push(line(s.pts, { fi: fi, color: color(s.color || 'var(--diff-' + s.key + ')') })); });
    });
    if (!pts.length) return null;

    var lonMin = Infinity, lonMax = -Infinity, latMin = Infinity, latMax = -Infinity, low = null, high = null;
    pts.forEach(function (p) {
      lonMin = Math.min(lonMin, p[0]); lonMax = Math.max(lonMax, p[0]);
      latMin = Math.min(latMin, p[1]); latMax = Math.max(latMax, p[1]);
      if (p[2] != null) {
        if (!low || p[2] < low[2]) low = p;
        if (!high || p[2] > high[2]) high = p;
      }
    });
    // Look up the mountain: from the lowest point towards the highest, the
    // way a piste map is drawn.
    var uphill = low && high && (low[0] !== high[0] || low[1] !== high[1]) ? bearingBetween(low, high) : 0;
    var view = frame(pts, uphill, el.clientWidth || 400, el.clientHeight || 400), bearing = view.bearing;
    var halo = color(o.haloColor), liftC = color(o.liftColor);
    var round = { 'line-cap': 'round', 'line-join': 'round' };
    var mode = o.mode === 'slope' ? 'slope' : 'diff';

    var map;
    try { map = new maplibregl.Map({
      container: el,
      center: view.center,
      zoom: view.zoom,
      bearing: bearing,
      maxPitch: 80,
      attributionControl: { compact: true, customAttribution: o.attribution },
      style: {
        version: 8,
        sources: {
          // Declared at half size on sharp (high-DPI) screens, so MapLibre asks for one zoom level more.
          sat: { type: 'raster', tiles: [IMAGERY], tileSize: (window.devicePixelRatio || 1) >= 2 ? 128 : 256, maxzoom: 18, attribution: 'Esri, Maxar, Earthstar Geographics' },
          dem: { type: 'raster-dem', tiles: [TERRAIN], tileSize: 256, maxzoom: 15, encoding: 'terrarium', attribution: 'Terrain Tiles (Mapzen, AWS)' },
          runs: { type: 'geojson', data: collection(runs) },
          slope: { type: 'geojson', data: collection(slope) },
          lifts: { type: 'geojson', data: collection(lifts) },
          sel: { type: 'geojson', data: collection([]) }
        },
        layers: [
          { id: 'sat', type: 'raster', source: 'sat' },
          { id: 'lift-casing', type: 'line', source: 'lifts', paint: { 'line-color': halo, 'line-width': 3.6 } },
          { id: 'lift', type: 'line', source: 'lifts', paint: { 'line-color': liftC, 'line-width': 2, 'line-dasharray': [2, 1.5] } },
          { id: 'sel-glow', type: 'line', source: 'sel', layout: round, paint: { 'line-color': '#ffffff', 'line-width': 10, 'line-blur': 4, 'line-opacity': 0.9 } },
          { id: 'run-halo', type: 'line', source: 'runs', layout: round, paint: { 'line-color': halo, 'line-width': 4.6 } },
          { id: 'run', type: 'line', source: 'runs', layout: Object.assign({ visibility: mode === 'diff' ? 'visible' : 'none' }, round),
            paint: { 'line-color': ['get', 'color'], 'line-width': 2.6 } },
          { id: 'slope', type: 'line', source: 'slope', layout: Object.assign({ visibility: mode === 'slope' ? 'visible' : 'none' }, round),
            paint: { 'line-color': ['get', 'color'], 'line-width': 2.6 } },
          { id: 'sel', type: 'line', source: 'sel', layout: round, paint: { 'line-color': ['get', 'color'], 'line-width': 5 } }
        ],
        terrain: { source: 'dem', exaggeration: EXAGGERATION },
        sky: { 'sky-color': '#7fb2e5', 'horizon-color': '#dfeaf4', 'sky-horizon-blend': 0.6, 'horizon-fog-blend': 0.5, 'fog-color': '#dfeaf4', 'fog-ground-blend': 0.85 }
      }
    }); } catch (e) { return null; }   // no usable WebGL after all
    var home = null;
    // Missing tiles are normal (and MapLibre carries on without them): only
    // give up if the map never manages to draw.
    var watchdog = setTimeout(function () { if (o.onError) o.onError(); }, 25000);
    // 'style.load', not 'load': 'load' waits for every tile, which a slow or
    // blocked tile server can hold up for good.
    map.once('style.load', function () {
      clearTimeout(watchdog);
      // The compact credits open themselves on small screens: keep them folded.
      var attrib = el.querySelector('.maplibregl-ctrl-attrib');
      if (attrib) attrib.classList.remove('maplibregl-compact-show');
      // The mountain rises: start flat over the resort, then tilt. Tilted,
      // the near half of the view grows, so it can come a little closer.
      map.easeTo({ pitch: PITCH, zoom: map.getZoom() + 0.25, duration: 1400 });
      map.once('moveend', function () { home = { center: map.getCenter(), zoom: map.getZoom(), bearing: map.getBearing(), pitch: map.getPitch() }; });
      if (o.onReady) o.onReady();
    });
    map.on('error', function () {});   // logged by MapLibre otherwise; tiles that fail just stay blank

    var tappable = function () { return ['lift', mode === 'slope' ? 'slope' : 'run']; };
    map.on('click', function (e) {
      var p = e.point, box = [[p.x - 12, p.y - 12], [p.x + 12, p.y + 12]];
      var hits = map.queryRenderedFeatures(box, { layers: tappable() });
      // Prefer a run over a lift crossing it.
      hits.sort(function (a, b) { return (a.layer.id === 'lift') - (b.layer.id === 'lift'); });
      var f = hits.length ? o.features[hits[0].properties.fi] : null;
      var ev = e.originalEvent || {};
      o.onTap(f || null, ev.clientX != null ? ev.clientX : p.x, ev.clientY != null ? ev.clientY : p.y);
    });
    map.on('mousemove', function (e) {
      var p = e.point;
      var n = map.queryRenderedFeatures([[p.x - 8, p.y - 8], [p.x + 8, p.y + 8]], { layers: tappable() }).length;
      map.getCanvas().style.cursor = n ? 'pointer' : '';
    });

    var marker = function (cls) {
      var d = document.createElement('div');
      d.className = cls;
      return new maplibregl.Marker({ element: d });
    };
    var locMarker = null, profMarker = null, spinning = false, spinFrame = null;
    function stopSpin() {
      spinning = false;
      if (spinFrame) cancelAnimationFrame(spinFrame);
      spinFrame = null;
      if (api.onSpinChange) api.onSpinChange(false);
    }
    ['mousedown', 'touchstart', 'wheel'].forEach(function (t) { el.addEventListener(t, function () { if (spinning) stopSpin(); }, { passive: true }); });

    var api = {
      map: map,
      setMode: function (m) {
        mode = m === 'slope' ? 'slope' : 'diff';
        if (!map.getLayer('run')) return;
        map.setLayoutProperty('run', 'visibility', mode === 'diff' ? 'visible' : 'none');
        map.setLayoutProperty('slope', 'visibility', mode === 'slope' ? 'visible' : 'none');
      },
      // Indices into the features: the selected run (all its parts) or lift.
      highlight: function (list) {
        var src = map.getSource('sel');
        if (!src) return;
        src.setData(collection((list || []).map(function (fi) {
          var f = o.features[fi];
          if (!f) return null;
          return line(f.isLift ? f.geo : f.geomPart, { color: f.isLift ? liftC : color(o.runColor(f)) });
        }).filter(Boolean)));
      },
      setLocation: function (pt, fly) {
        if (!pt) { if (locMarker) locMarker.remove(); locMarker = null; return; }
        if (!locMarker) locMarker = marker('map3d-loc').setLngLat(pt).addTo(map);
        else locMarker.setLngLat(pt);
        if (fly) map.easeTo({ center: pt, zoom: Math.max(map.getZoom(), 14.5), duration: 900 });
      },
      setProfilePoint: function (pt) {
        if (!pt) { if (profMarker) profMarker.remove(); profMarker = null; return; }
        if (!profMarker) profMarker = marker('map3d-point').setLngLat([pt[0], pt[1]]).addTo(map);
        else profMarker.setLngLat([pt[0], pt[1]]);
      },
      zoomIn: function () { map.zoomIn(); },
      zoomOut: function () { map.zoomOut(); },
      reset: function () {
        stopSpin();
        if (home) map.easeTo(Object.assign({ duration: 900 }, home));
        else map.easeTo({ center: view.center, zoom: view.zoom + 0.25, bearing: bearing, pitch: PITCH, duration: 900 });
      },
      // A slow turn around the resort (also nice to record for a video).
      spin: function () {
        if (spinning) { stopSpin(); return false; }
        spinning = true;
        var last = null;
        (function step(t) {
          if (!spinning) return;
          if (last != null) map.setBearing(map.getBearing() + (t - last) * 0.006);
          last = t;
          spinFrame = requestAnimationFrame(step);
        })();
        return true;
      },
      resize: function () { map.resize(); },
      destroy: function () { clearTimeout(watchdog); stopSpin(); map.remove(); }
    };
    return api;
  }

  window.SkiMap3D = { open: open };
})();
