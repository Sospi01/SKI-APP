// Ski routes inside a resort: from where you are (or a point you pick) to a
// run, a lift or a service, by runs (downhill only) and lifts (uphill only),
// optionally avoiding runs above a level. Loaded on demand by index.html; also
// usable from Node (web-tests / quality reports): module.exports = SkiRoutes.
//
// The network comes from the resort's OpenStreetMap data (docs/data/<id>.json):
// - a run is skied from its higher end to its lower one (both ways if flat);
// - a lift goes from its lower end to its upper one, with a boarding wait;
// - short walks join runs and lifts that touch (or nearly), never far uphill.
// Times are estimates; nothing is known about what is open on a given day.
(function (root) {
  var RUN_SPEED = { novice: 5, easy: 7, intermediate: 8, advanced: 7, expert: 6, double: 6, freeride: 5, extreme: 4, other: 6 };   // m/s
  var LIFT_SPEED = { gondola: 5, cable_car: 8, funicular: 6, railway: 6, mixed_lift: 5, chair_lift: 3, drag_lift: 3, 't-bar': 3, platter: 3,
                     'j-bar': 3, rope_tow: 2, magic_carpet: 1 };
  var LIFT_WAIT = 90;          // s, getting on
  var WALK_SPEED = 1;          // m/s on snow in boots or skating
  var LINK_M = 35;             // runs/lifts closer than this are joined by a walk
  var LIFT_LINK_M = 60;        // around a lift's ends (stations are big)
  var FLAT_M = 5, FLAT_GRADE = 0.03;   // a run this level end to end (or under 3 %) can go both ways
  var CLIMB_M = 8;             // a walk can't gain more than this
  var FLAT_LINK_M = 150, FLAT_LINK_DZ = 4;   // skating across a flat (Beret's plateau): longer, if nearly level
  var EASY = { novice: 1, easy: 1, other: 1 };
  var NO_BLACK = { novice: 1, easy: 1, intermediate: 1, other: 1 };

  // A run drawn as one loop, down one lane and back up the other (or up and
  // back down): two downhill lanes, split at the turning point. Mirrors
  // splitOutAndBack() in docs/profile.js.
  function splitLoop(pts) {
    if (pts.length < 3 || pts[0][2] == null || pts[pts.length - 1][2] == null) return [pts];
    if (Math.abs(pts[0][2] - pts[pts.length - 1][2]) > 10) return [pts];
    function at(sign) {
      var k = 0;
      for (var i = 1; i < pts.length; i++) if (pts[i][2] != null && sign * (pts[i][2] - pts[k][2]) > 0) k = i;
      if (k <= 0 || k >= pts.length - 1) return null;
      var a = sign * (pts[k][2] - pts[0][2]), b = sign * (pts[k][2] - pts[pts.length - 1][2]);
      if (a <= 0 || b <= 0 || Math.min(a, b) < 15 || Math.min(a, b) / Math.max(a, b) < 0.4) return null;
      return [pts.slice(0, k + 1), pts.slice(k)];
    }
    return at(-1) || at(1) || [pts];
  }

  function dist(a, b) {
    var k = Math.cos((a[1] + b[1]) / 2 * Math.PI / 180);
    return Math.hypot((a[0] - b[0]) * 111320 * k, (a[1] - b[1]) * 111320);
  }

  // raw: a station's data file. diffOf(run) -> the colour key shown for it
  // (index.html's shownDifficulty/diffKey). Returns the network.
  function build(raw, diffOf) {
    var nodes = [], adj = [], feats = [];
    function node(p, feat) { nodes.push({ p: p, f: feat }); adj.push([]); return nodes.length - 1; }
    function edge(a, b, w, feat) { adj[a].push({ to: b, w: w, f: feat }); }

    (raw.runs || []).forEach(function (r, ri) {
      if (r.uses && r.uses.split(',').indexOf('downhill') === -1) return;
      var diff = diffOf ? diffOf(r) : (r.difficulty || 'other');
      (r.geom || []).forEach(function (part) {
        var all = part.filter(function (p) { return p && p.length >= 2; });
        if (all.length < 2) return;
        splitLoop(all).forEach(function (pts) { addRunLane(r, ri, diff, part, pts); });
      });
    });

    function addRunLane(r, ri, diff, part, pts) {
      {
        var e0 = pts[0][2], e1 = pts[pts.length - 1][2], both = false;
        if (e0 != null && e1 != null) {
          // Nearly level (cat tracks, links between sectors): skied or skated either way.
          var len = 0;
          for (var k = 1; k < pts.length; k++) len += dist(pts[k - 1], pts[k]);
          if (Math.abs(e1 - e0) <= Math.max(FLAT_M, len * FLAT_GRADE)) both = true;
          else if (e1 > e0) pts = pts.slice().reverse();
        }
        var fi = feats.push({ kind: 'run', run: r, ri: ri, diff: diff, part: part }) - 1;
        var speed = RUN_SPEED[diff] || RUN_SPEED.other, prev = null;
        pts.forEach(function (p) {
          var n = node(p, fi);
          if (prev != null) {
            var w = dist(nodes[prev].p, p) / speed;
            edge(prev, n, w, fi);
            if (both) edge(n, prev, w, fi);
          }
          prev = n;
        });
        feats[fi].top = prev - pts.length + 1;   // first node: the run's start
        feats[fi].end = prev;                    // last node: where it ends
      }
    }

    // A lift is sometimes mapped as several sections in a row (Formigal's
    // Tramacastilla drag: three), each tagged with the whole lift's duration.
    // Such sections share the duration by length, and only the first has a wait.
    var sections = [];
    (raw.lifts || []).forEach(function (l, li) {
      (l.geom || []).forEach(function (part) {
        if (!part || part.length < 2) return;
        var a = part[0], b = part[part.length - 1];
        if (a[2] != null && b[2] != null && a[2] > b[2]) { var t = a; a = b; b = t; }
        sections.push({ l: l, li: li, part: part, a: a, b: b, len: l.length_m || dist(a, b) });
      });
    });
    sections.forEach(function (x) {
      var group = sections.filter(function (y) { return y.l.name && y.l.name === x.l.name && y.l.duration_s === x.l.duration_s; });
      var chained = group.length > 1 && group.every(function (y) {
        return group.some(function (z) { return z !== y && (dist(y.b, z.a) < 30 || dist(z.b, y.a) < 30); });
      });
      var total = group.reduce(function (s2, y) { return s2 + y.len; }, 0);
      var speed = LIFT_SPEED[x.l.lift_type] * (x.l.detachable ? 1.6 : 1) || 3;
      x.ride = x.l.duration_s ? (chained ? x.l.duration_s * x.len / total : x.l.duration_s) : x.len / speed;
      x.wait = chained && group.some(function (z) { return z !== x && dist(z.b, x.a) < 30; }) ? 0 : LIFT_WAIT;
    });
    sections.forEach(function (x) {
      var fi = feats.push({ kind: 'lift', lift: x.l, li: x.li, part: x.part, ride: x.ride, wait: x.wait }) - 1;
      var lo = node(x.a, fi), hi = node(x.b, fi);
      edge(lo, hi, x.ride + x.wait, fi);
      feats[fi].bottom = lo; feats[fi].topNode = hi;
    });

    // Walks between features that touch (or skating across a flat), on a
    // ~150-200 m grid so a 3x3 block covers the longest link.
    var grid = {}, G = 600;
    nodes.forEach(function (n, i) {
      var k = Math.floor(n.p[0] * G) + ':' + Math.floor(n.p[1] * G);
      (grid[k] || (grid[k] = [])).push(i);
    });
    nodes.forEach(function (n, i) {
      var gx = Math.floor(n.p[0] * G), gy = Math.floor(n.p[1] * G);
      var isLift = feats[n.f].kind === 'lift';
      for (var dx = -1; dx <= 1; dx++) for (var dy = -1; dy <= 1; dy++) {
        (grid[(gx + dx) + ':' + (gy + dy)] || []).forEach(function (j) {
          if (j === i || nodes[j].f === n.f) return;
          var m = dist(n.p, nodes[j].p);
          if (m > FLAT_LINK_M) return;
          var climb = (nodes[j].p[2] != null && n.p[2] != null) ? nodes[j].p[2] - n.p[2] : 0;
          var reach = Math.abs(climb) <= FLAT_LINK_DZ ? FLAT_LINK_M : isLift || feats[nodes[j].f].kind === 'lift' ? LIFT_LINK_M : LINK_M;
          if (m > reach || climb > CLIMB_M || -climb > m * 0.6 + CLIMB_M) return;   // no climbing, no dropping off a cliff
          edge(i, j, (m > LINK_M ? 20 : 5) + m / WALK_SPEED * (climb > 0 ? 1.5 : 1), -1);
        });
      }
    });
    return { nodes: nodes, adj: adj, feats: feats };
  }

  // Binary-heap Dijkstra from several start nodes (with a starting cost each)
  // to the cheapest of several targets. level: 'all' | 'noblack' | 'easy'.
  function route(net, starts, targets, level) {
    var ok = level === 'easy' ? EASY : level === 'noblack' ? NO_BLACK : null;
    var n = net.nodes.length, best = new Float64Array(n).fill(Infinity), from = new Int32Array(n).fill(-1);
    var via = new Array(n), isTarget = {};
    targets.forEach(function (t) { isTarget[t] = true; });
    var heap = [];
    function push(c, i) {
      heap.push([c, i]);
      for (var k = heap.length - 1; k > 0;) {
        var p = (k - 1) >> 1;
        if (heap[p][0] <= heap[k][0]) break;
        var t = heap[p]; heap[p] = heap[k]; heap[k] = t; k = p;
      }
    }
    function pop() {
      var top = heap[0], last = heap.pop();
      if (heap.length) {
        heap[0] = last;
        for (var k = 0;;) {
          var l = 2 * k + 1, r = l + 1, m = k;
          if (l < heap.length && heap[l][0] < heap[m][0]) m = l;
          if (r < heap.length && heap[r][0] < heap[m][0]) m = r;
          if (m === k) break;
          var t = heap[m]; heap[m] = heap[k]; heap[k] = t; k = m;
        }
      }
      return top;
    }
    starts.forEach(function (s) { if (s.cost < best[s.node]) { best[s.node] = s.cost; push(s.cost, s.node); } });
    var end = -1;
    while (heap.length) {
      var cur = pop(), c = cur[0], i = cur[1];
      if (c > best[i]) continue;
      if (isTarget[i]) { end = i; break; }
      net.adj[i].forEach(function (e) {
        if (ok && e.f >= 0) {
          var f = net.feats[e.f];
          if (f.kind === 'run' && !ok[f.diff]) return;
        }
        var nc = c + e.w;
        if (nc < best[e.to]) { best[e.to] = nc; from[e.to] = i; via[e.to] = e.f; push(nc, e.to); }
      });
    }
    if (end < 0) return null;
    var path = [];
    for (var x = end; x >= 0; x = from[x]) path.push({ node: x, f: from[x] >= 0 ? via[x] : null });
    path.reverse();
    return { cost: best[end], path: path };
  }

  // Starts near a point (within maxM), as route() takes them: the nearest
  // node of each run or lift around, nearest first -- not just the closest
  // run's nodes, which may lead nowhere if that run ends in a gap of the map.
  function near(net, pt, maxM, limit) {
    var byFeat = {};
    net.nodes.forEach(function (n, i) {
      var m = dist(pt, n.p);
      if (m > maxM || !net.adj[i].length) return;
      if (!byFeat[n.f] || m < byFeat[n.f].m) byFeat[n.f] = { node: i, m: m, f: n.f, cost: m / WALK_SPEED };
    });
    var out = Object.keys(byFeat).map(function (k) { return byFeat[k]; });
    out.sort(function (a, b) { return a.m - b.m; });
    return out.slice(0, limit || 12);
  }

  // A route's legs: consecutive stretches on the same run name (or part), the
  // same lift, or on foot. { kind, feat, m (metres), secs, coords: [[lon,lat]...] }
  function legs(net, res) {
    var out = [];
    for (var k = 1; k < res.path.length; k++) {
      var a = net.nodes[res.path[k - 1].node], b = net.nodes[res.path[k].node], fi = res.path[k].f;
      var f = fi >= 0 ? net.feats[fi] : null, kind = f ? f.kind : 'walk';
      var key = !f ? 'walk' : f.kind === 'lift' ? 'lift:' + fi : 'run:' + (f.run.name || fi);
      var m = dist(a.p, b.p), last = out[out.length - 1];
      if (last && last.key === key) { last.m += m; last.coords.push(b.p); last.to = res.path[k].node; }
      else out.push({ key: key, kind: kind, feat: f, m: m, coords: [a.p, b.p], from: res.path[k - 1].node, to: res.path[k].node });
    }
    out.forEach(function (l) {
      if (l.kind === 'lift') l.secs = l.feat.ride + l.feat.wait;
      else if (l.kind === 'run') l.secs = l.m / (RUN_SPEED[l.feat.diff] || RUN_SPEED.other);
      else l.secs = l.m / WALK_SPEED;
    });
    return out;
  }

  // How well connected the network is: the share of (lift A, lift B) pairs
  // where B can be reached from the top of A. 1 = every lift reaches every other.
  function quality(net) {
    var lifts = net.feats.filter(function (f) { return f.kind === 'lift'; });
    if (lifts.length < 2) return null;
    var ok = 0, tot = 0;
    lifts.forEach(function (a) {
      var seen = new Uint8Array(net.nodes.length), stack = [a.topNode];
      seen[a.topNode] = 1;
      while (stack.length) {
        var i = stack.pop();
        net.adj[i].forEach(function (e) { if (!seen[e.to]) { seen[e.to] = 1; stack.push(e.to); } });
      }
      lifts.forEach(function (b) { if (b !== a) { tot++; if (seen[b.bottom]) ok++; } });
    });
    return ok / tot;
  }

  var SkiRoutes = { build: build, route: route, near: near, legs: legs, quality: quality, dist: dist };
  root.SkiRoutes = SkiRoutes;
  if (typeof module !== 'undefined' && module.exports) module.exports = SkiRoutes;
})(typeof window !== 'undefined' ? window : this);
