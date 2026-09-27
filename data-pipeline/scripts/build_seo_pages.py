"""Generate static, crawlable pages for search engines from the app's data.

The web app (docs/index.html) renders every station client-side from one URL,
so search engines only ever see a single page. This script writes one plain
HTML page per station (/estacion/<slug>/), one per country (/pais/<slug>/), a
country index (/pais/), and sitemap.xml. Station pages carry the same content
and components as the app's Info tab (styled by docs/static-pages.css, made
interactive by docs/static-pages.js + docs/profile.js) and link into the
interactive map via /?estacion=<id>&vista=mapa.

Runs in the Pages deploy workflow; the generated files are not committed.
Station slugs are pinned in data-pipeline/station_slugs.json so a page's URL
never changes once search engines know it (pass --write-slugs to add new ones).
"""

from __future__ import annotations

import argparse
import html
import json
import math
import re
import unicodedata
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
SLUGS_PATH = REPO / "data-pipeline" / "station_slugs.json"

GENERIC_PREFIX = re.compile(
    r"^(estaci[oó]n? (d'|de )?esqu[ií]( (y|i) (de )?(monta[ñn]a|muntanya))?"
    r"|estaci[oó]n? (invernal|de muntanya)( y de monta[ñn]a)?"
    r"|station (de ski|du)|centro (de )?ski|ski center|ski centre|skigebiet)( del?)?\s+",
    re.IGNORECASE,
)
GENERIC_SUFFIX = re.compile(
    r"\s+(ski resort|ski area|mountain resort|ski centre|ski center|skiarea|ski bowl|resort)$",
    re.IGNORECASE,
)
LATIN = re.compile(r"[A-Za-zÀ-ɏ]")
PARENS = re.compile(r"\s*[(（][^)）]*[)）]")

PEAKS_SVG = ('<svg class="peaks" viewBox="0 0 400 140" preserveAspectRatio="none" aria-hidden="true">'
             '<polygon points="0,140 0,90 60,40 110,80 170,20 230,75 290,35 340,85 400,55 400,140" fill="rgba(255,255,255,0.14)"/>'
             '<polygon points="0,140 0,110 90,60 150,95 210,50 270,100 330,65 400,100 400,140" fill="rgba(255,255,255,0.20)"/></svg>')
PIN_ICON = ('<svg viewBox="0 0 20 20" aria-hidden="true"><path d="M10 2.2c-3 0-5.4 2.4-5.4 5.4C4.6 11.7 10 17.8 10 17.8s5.4-6.1 5.4-10.2c0-3-2.4-5.4-5.4-5.4z" '
            'fill="none" stroke="currentColor" stroke-width="1.7"/><circle cx="10" cy="7.5" r="1.9" fill="currentColor"/></svg>')
SHARE_ICON = ('<svg viewBox="0 0 20 20" aria-hidden="true"><circle cx="14.5" cy="4.5" r="2.3" fill="none" stroke="currentColor" stroke-width="1.6"/>'
              '<circle cx="5.5" cy="10" r="2.3" fill="none" stroke="currentColor" stroke-width="1.6"/><circle cx="14.5" cy="15.5" r="2.3" fill="none" stroke="currentColor" stroke-width="1.6"/>'
              '<path d="M7.5 8.9l5-3.2M7.5 11.1l5 3.2" stroke="currentColor" stroke-width="1.6"/></svg>')
MAP_ICON = ('<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M3.5 6.5l5.5-2.5 6 2.5 5.5-2.5v13.5l-5.5 2.5-6-2.5-5.5 2.5z" '
            'fill="none" stroke="currentColor" stroke-width="1.8" stroke-linejoin="round"/>'
            '<line x1="9" y1="4" x2="9" y2="17.5" stroke="currentColor" stroke-width="1.6"/>'
            '<line x1="15" y1="6.5" x2="15" y2="20" stroke="currentColor" stroke-width="1.6"/></svg>')

# Same filter chips as the app's run list.
RUN_FILTERS = [("all", "Todas", ["all"]), ("novice", "Verde", ["novice"]), ("easy", "Azul", ["easy"]),
               ("intermediate", "Roja", ["intermediate"]), ("advanced", "Negra", ["advanced", "expert"]),
               ("freeride", "Freeride", ["freeride", "extreme"]), ("other", "Sin clasif.", ["other"])]


# ---------- reading the app's own metadata out of index.html ----------

def js_block(src: str, var: str) -> str:
    start = src.index(f"var {var} = ")
    end = src.index("};", start)
    return src[start:end]


def read_app_sources(docs: Path) -> str:
    """index.html plus the station catalogue it loads (docs/stations.js)."""
    return (docs / "index.html").read_text(encoding="utf-8") + "\n" + (docs / "stations.js").read_text(encoding="utf-8")


def load_app_metadata(index_html: str) -> dict:
    """The app's own tables; pass read_app_sources() (index.html + stations.js)."""
    lines = index_html.splitlines()
    stations_line = next(l for l in lines if l.lstrip().startswith("var STATIONS = "))
    groups_line = next(l for l in lines if l.lstrip().startswith("var STATION_GROUPS = "))
    pairs = lambda var: dict(re.findall(r'"?([\w+-]+)"?:\s*"([^"]+)"', js_block(index_html, var)))
    return {
        "stations": json.loads(stations_line.split(" = ", 1)[1].rstrip(";")),
        "groups": json.loads(groups_line.split(" = ", 1)[1].rstrip(";")),
        "diff": dict(re.findall(r'(\w+):\s*\{ label: "([^"]+)"', js_block(index_html, "DIFF"))),
        "diff_order": json.loads(re.search(r"var DIFF_ORDER = (\[.*?\]);", index_html).group(1)),
        "lift_types": pairs("LIFT_TYPE"),
        "activity": pairs("ACTIVITY"),
        "status": pairs("STATUS"),
        "grooming": pairs("GROOMING"),
        "services": {k: (label, icon) for k, label, icon in re.findall(
            r'(\w+): \{ label: "([^"]+)", icon: "([^"]+)"', js_block(index_html, "SERVICE_CATEGORIES"))},
        "countries": {cc: (name, flag) for cc, name, flag in re.findall(
            r"(\w\w): \{ name: '([^']+)', flag: '([^']+)' \}", js_block(index_html, "COUNTRY_META"))},
    }


# ---------- names, slugs, formatting ----------

def latin_name(name: str, keep_parens: bool) -> str:
    """First Latin-script form of a name: "Абзаково (Abzakovo)" -> "Abzakovo"."""
    for part in (p.strip() for p in (name or "").split(",")):
        outside = PARENS.sub("", part).strip()
        if LATIN.search(outside):
            return part if keep_parens else outside
        for inside in re.findall(r"[(（]([^)）]*)[)）]", part):
            if LATIN.search(inside):
                return inside.strip()
    return ""


def strip_generic(text: str) -> str:
    text = GENERIC_PREFIX.sub("", text)
    prev = None
    while prev != text:
        prev, text = text, GENERIC_SUFFIX.sub("", text)
    return text.strip()


def short_name(name: str) -> str:
    """"Estació d'Esquí Baqueira-Beret" -> "Baqueira-Beret"."""
    first = (name or "").split(",")[0].strip()
    return strip_generic(latin_name(name, keep_parens=False)) or first


def slugify(text: str) -> str:
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def station_slug(station: dict) -> str:
    # Parenthesised parts stay in the slug so e.g. the San Isidro sectors differ.
    base = slugify(strip_generic(latin_name(station["name"], keep_parens=True)))
    if base:
        return base
    region = slugify(station.get("region") or "")
    return f"estacion-{region + '-' if region else ''}{station['id'][:6]}"


def fmt(n: float, d: int = 0) -> str:
    """Spanish number format like the app's toLocaleString('es-ES'): no
    thousands separator below 10.000, decimal comma."""
    s = f"{n:,.{d}f}" if abs(n) >= 10000 else f"{n:.{d}f}"
    return s.replace(",", "\0").replace(".", ",").replace("\0", ".")


def format_coord(lat, lon) -> str:
    if lat is None or lon is None:
        return "–"
    return f"{fmt(abs(lat), 2)}°{'N' if lat >= 0 else 'S'} {fmt(abs(lon), 2)}°{'E' if lon >= 0 else 'O'}"


def haversine_km(a: tuple, b: tuple) -> float:
    lat1, lon1, lat2, lon2 = map(math.radians, (a[0], a[1], b[0], b[1]))
    h = math.sin((lat2 - lat1) / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin((lon2 - lon1) / 2) ** 2
    return 2 * 6371 * math.asin(math.sqrt(h))


def base_location(raw: dict):
    """Where "Cómo llegar" should point: the lowest lift end (the base area, where
    the car park usually is) -- the station's centre is often up the mountain.
    Mirrors baseLocation() in docs/station-actions.js."""
    best = None
    for l in raw.get("lifts") or []:
        for part in l.get("geom") or []:
            for p in (part[0], part[-1]) if part else ():
                if len(p) > 2 and p[2] is not None and (best is None or p[2] < best[2]):
                    best = p
    if best:
        return best[1], best[0]
    if raw.get("latitude") is not None:
        return raw["latitude"], raw["longitude"]
    return None


def e(text) -> str:
    return html.escape(str(text if text is not None else ""), quote=True)


def is_downhill(run: dict) -> bool:
    # Same filter as the app: untagged runs count, cross-country-only ones don't.
    uses = run.get("uses")
    return not uses or "downhill" in uses.split(",")


def pill(text: str) -> str:
    return f'<span class="pill">{e(text)}</span>'


# ---------- page shell ----------

# Self-hosted @font-face rules, inlined into every page (one request fewer).
FONT_FACES = "\n".join(l for l in (REPO / "docs" / "fonts.css").read_text(encoding="utf-8").splitlines()
                       if l.startswith("@font-face"))


def page(*, title: str, description: str, url: str, body: str, body_attrs: str = "",
         jsonld: dict | None = None, noindex: bool = False, scripts: bool = False,
         image: str = "/og/ski-info.jpg", base_url: str = "https://skiinfoapp.com") -> str:
    head_extra = '<meta name="robots" content="noindex">\n' if noindex else ""
    if jsonld:
        head_extra += ('<script type="application/ld+json">'
                       + json.dumps(jsonld, ensure_ascii=False).replace("</", "<\\/") + "</script>\n")
    # Stats on every page; station pages report a station view (static-pages.js),
    # the rest a page view.
    # Deferred: they run in order once the page is parsed, without holding up
    # the first paint. track.js with data-page reports a plain page view.
    tail = ('<script defer src="/profile.js"></script>\n<script defer src="/snow.js"></script>\n'
            '<script defer src="/station-actions.js"></script>\n<script defer src="/track.js"></script>\n'
            '<script defer src="/static-pages.js"></script>\n'
            if scripts else '<script defer src="/track.js" data-page></script>\n')
    if scripts:
        # Not needed for the first screen: load it without blocking the paint.
        head_extra = ('<link rel="stylesheet" href="/snow.css" media="print" onload="this.media=\'all\'">\n'
                      '<noscript><link rel="stylesheet" href="/snow.css"></noscript>\n' + head_extra)
    return f"""<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(title)}</title>
<meta name="description" content="{e(description)}">
<link rel="canonical" href="{e(url)}">
<meta property="og:type" content="website">
<meta property="og:site_name" content="Ski Info">
<meta property="og:title" content="{e(title)}">
<meta property="og:description" content="{e(description)}">
<meta property="og:url" content="{e(url)}">
<meta property="og:image" content="{e(base_url + image)}">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:locale" content="es_ES">
<meta name="twitter:card" content="summary_large_image">
<meta name="theme-color" content="#14345C">
<link rel="icon" href="/favicon.svg" type="image/svg+xml">
<link rel="icon" href="/icons/favicon-32.png" sizes="32x32" type="image/png">
<link rel="apple-touch-icon" href="/icons/apple-touch-icon.png">
<link rel="manifest" href="/manifest.webmanifest">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-title" content="Ski Info">
<link rel="preload" href="/fonts/ibm-plex-sans-latin-400-normal.woff2" as="font" type="font/woff2" crossorigin>
<link rel="preload" href="/fonts/ibm-plex-sans-latin-700-normal.woff2" as="font" type="font/woff2" crossorigin>
<link rel="preload" href="/fonts/barlow-condensed-latin-700-normal.woff2" as="font" type="font/woff2" crossorigin>
<style>{FONT_FACES}</style>
<link rel="stylesheet" href="/static-pages.css">
{head_extra}</head>
<body{body_attrs}>
<div class="app">
{body}
<footer class="credit">
<a href="/">Ski Info</a> · <a href="/pais/">Estaciones por país</a> · <a href="/guias/">Guías y rankings</a> · <a href="/app/">App para el móvil</a> · <a href="/privacy.html">Privacidad</a><br>
Datos de OpenSkiMap / OpenStreetMap, licencia ODbL.
</footer>
</div>
{tail}</body>
</html>
"""


def bars(items: list) -> str:
    """App-style bar list; items are (label, value, value_text, color)."""
    if not items:
        return ""
    top = max(v for _, v, _, _ in items) or 1
    return '<div class="barlist">' + "".join(
        f'<div class="bar-row"><div class="bar-row-label">{e(label)}</div>'
        f'<div class="bar-track"><div class="bar-fill" style="width:{max(3, v / top * 100):.1f}%;background:{color}"></div></div>'
        f'<div class="bar-value">{e(text)}</div></div>'
        for label, v, text, color in items) + "</div>"


def chips(list_id: str, defs: list) -> str:
    """defs: (keys, label, count, color|None); the first is the 'all' chip."""
    out = []
    for i, (keys, label, count, color) in enumerate(defs):
        dot = f'<span class="dot" style="background:{color}"></span>' if color else ""
        out.append(f'<button type="button" class="chip" data-keys="{e(" ".join(keys))}" '
                   f'aria-pressed="{"true" if i == 0 else "false"}">{dot}{e(label)} · {count}</button>')
    return f'<div class="chips" data-list="{list_id}">{"".join(out)}</div>'


# ---------- station page ----------

def station_page(raw: dict, meta: dict, ctx: dict) -> tuple[str, bool]:
    base, sid = ctx["base_url"], raw["id"]
    cc = raw.get("country_code")
    country_name = meta["countries"].get(cc, (cc or "", ""))[0]
    name = raw.get("name") or "Estación de esquí"
    short = short_name(name) or name
    place = ", ".join(p for p in [raw.get("locality"), raw.get("region")] if p) or country_name
    place_full = ", ".join(p for p in [raw.get("locality"), raw.get("region"), country_name] if p)
    url = f"{base}/estacion/{ctx['slug'][sid]}/"
    app_link = f"/?estacion={sid}&amp;vista=mapa"

    runs = [r for r in raw.get("runs", []) if is_downhill(r)]
    lifts = raw.get("lifts", [])
    services = [s for s in raw.get("services") or [] if s.get("category") in meta["services"]]
    total_m = sum(r.get("length_m") or 0 for r in runs)
    lo, hi = raw.get("min_elevation_m"), raw.get("max_elevation_m")
    diff_key = lambda d: d if d in meta["diff"] else "other"
    diff_color = lambda k: f"var(--diff-{k})"
    indexable = bool(runs or lifts)

    # ----- hero (badges, title, stats, connected domain) -----
    badges = [meta["activity"].get(a, a) for a in (raw.get("activities") or "").split(",") if a]
    badges += [meta["status"].get(raw.get("status"), raw.get("status")), country_name]
    badges_html = "".join(f'<span class="badge">{e(b)}</span>' for b in badges if b)
    site = (raw.get("websites") or [None])[0]
    site_html = f'<a class="site" href="{e(site)}" target="_blank" rel="noopener">Web oficial ↗</a>' if site else ""
    stats = [
        (f"{fmt(round(lo))}–{fmt(round(hi))} m" if lo is not None and hi is not None else "–", "Altitud"),
        (f"{fmt(round(hi - lo))} m" if lo is not None and hi is not None else "–", "Desnivel"),
        (f"{fmt(round(total_m / 1000))} km", "Km pista"),
        (format_coord(raw.get("latitude"), raw.get("longitude")), "Coordenadas"),
    ]
    stats_html = "".join(f'<div class="hero-stat"><div class="v">{e(v)}</div><div class="k">{e(k)}</div></div>' for v, k in stats)
    domain_html = ""
    group = ctx["group_of"].get(sid)
    if group:
        links = "".join(
            f'<a class="chip" href="/estacion/{ctx["slug"][o]}/">{e(ctx["by_id"][o]["name"])} · {fmt(round(ctx["by_id"][o].get("pisteKm") or 0))} km</a>'
            for o in group if o != sid and o in ctx["by_id"])
        if links:
            domain_html = ('<div class="hero-domain"><div class="hero-domain-title">Dominio esquiable conectado</div>'
                           '<p class="hero-domain-note">Detectado por proximidad geográfica; los km de cada una pueden solaparse:</p>'
                           f'<div class="chips">{links}</div></div>')
    country_slug = ctx["country_slug"].get(cc)
    base_pt = base_location(raw)
    directions_html = (f'<a class="hero-action" href="https://www.google.com/maps/dir/?api=1&amp;destination={base_pt[0]:.5f},{base_pt[1]:.5f}" '
                       f'target="_blank" rel="noopener">{PIN_ICON} Cómo llegar</a>' if base_pt else "")
    back = (f'<a class="back-btn" href="/pais/{country_slug}/"><span class="chev">‹</span> Estaciones de {e(country_name)}</a>'
            if country_slug else '<a class="back-btn" href="/pais/"><span class="chev">‹</span> Países</a>')
    hero = f"""<div class="topbar">{back}<a class="back-btn" href="/">Ski Info</a></div>
<div class="hero">{PEAKS_SVG}<div class="hero-content">
<div class="badges">{badges_html}</div>
<div class="hero-title-row"><h1>{e(name)}</h1>{site_html}</div>
<div class="place">{e(place)}</div>
<div class="hero-stats">{stats_html}</div>
{domain_html}
<div class="hero-cta-row">
<a class="hero-cta" href="{app_link}">{MAP_ICON} Abrir el mapa interactivo de pistas</a>
<div class="hero-actions">{directions_html}<button type="button" class="hero-action js-share" data-url="{e(url)}" data-title="{e(short)}">{SHARE_ICON} Compartir</button></div>
</div>
</div></div>"""

    # ----- intro text (what search engines read first) -----
    groups: dict[str, dict] = {}
    for r in runs:
        nm = r.get("name")
        if not nm:
            continue
        g = groups.setdefault(nm, {"name": nm, "difficulty": r.get("difficulty"), "length_m": 0.0, "vertical_m": 0.0,
                                   "lit": 0, "gladed": 0, "segments": 0, "ref": None, "grooming": None,
                                   "min": None, "max": None})
        g["length_m"] += r.get("length_m") or 0
        g["vertical_m"] += r.get("vertical_m") or 0
        g["lit"] = g["lit"] or (1 if r.get("lit") == 1 else 0)
        g["gladed"] = g["gladed"] or (1 if r.get("gladed") == 1 else 0)
        g["ref"] = g["ref"] or r.get("ref")
        g["grooming"] = g["grooming"] or r.get("grooming")
        if r.get("min_elevation_m") is not None:
            g["min"] = r["min_elevation_m"] if g["min"] is None else min(g["min"], r["min_elevation_m"])
        if r.get("max_elevation_m") is not None:
            g["max"] = r["max_elevation_m"] if g["max"] is None else max(g["max"], r["max_elevation_m"])
        g["segments"] += 1
    run_groups = sorted(groups.values(), key=lambda g: (meta["diff_order"].index(diff_key(g["difficulty"])), -g["length_m"]))

    intro = [f"{e(short)} es una estación de esquí" + (f" en {e(place_full)}" if place_full else "") + "."]
    if total_m and run_groups:
        intro.append(f"Tiene {fmt(round(total_m / 1000))} km de pistas repartidos en {len(run_groups)} pistas con nombre"
                     + (f" y {len(lifts)} remontes" if lifts else "") + ".")
    if lo is not None and hi is not None:
        intro.append(f"Su dominio va de {fmt(round(lo))} a {fmt(round(hi))} m de altitud, con {fmt(round(hi - lo))} m de desnivel.")
    intro.append("Aquí tienes todas sus pistas con su perfil de pendiente, sus remontes y los servicios en pistas; "
                 "en el mapa interactivo las verás sobre imagen de satélite.")
    intro_html = (f'<section><div class="section-head"><h2>{e(short)}: mapa de pistas y datos</h2></div>'
                  f'<p class="intro">{" ".join(intro)}</p></section>')

    # ----- charts: terrain by difficulty, lifts by type (same as the app) -----
    diff_agg: dict[str, list] = {}
    for r in runs:
        a = diff_agg.setdefault(diff_key(r.get("difficulty")), [0.0, 0])
        a[0] += (r.get("length_m") or 0) / 1000
        a[1] += 1
    diff_bars = bars([(meta["diff"][k], diff_agg[k][0], f"{fmt(diff_agg[k][0], 1)} km · {diff_agg[k][1]}", diff_color(k))
                      for k in meta["diff_order"] if k in diff_agg])
    lift_agg: dict[str, list] = {}
    for l in lifts:
        a = lift_agg.setdefault(l.get("lift_type"), [0.0, 0])
        a[0] += (l.get("length_m") or 0) / 1000
        a[1] += 1
    lift_bars = bars([(meta["lift_types"].get(k, k or "Otro"), v[0], f"{fmt(v[0], 1)} km · {v[1]}", "var(--accent)")
                      for k, v in sorted(lift_agg.items(), key=lambda kv: -kv[1][0])])
    charts_html = '<div class="charts">'
    if diff_bars:
        charts_html += f'<section><div class="section-head"><h2>Terreno por dificultad</h2></div>{diff_bars}</section>'
    if lift_bars:
        charts_html += f'<section><div class="section-head"><h2>Remontes por tipo</h2></div>{lift_bars}</section>'
    charts_html += "</div>"

    # ----- catalog: runs / lifts / services -----
    run_items = []
    for g in run_groups:
        k = diff_key(g["difficulty"])
        bits = []
        if g["length_m"]:
            bits.append(f'{fmt(round(g["length_m"]))} m')
        if g["vertical_m"]:
            bits.append(f'desnivel {fmt(round(g["vertical_m"]))} m')
        if g["length_m"]:
            bits.append(f'pend. media {fmt(100 * g["vertical_m"] / g["length_m"], 1)}%')
        if g["min"] is not None and g["max"] is not None:
            bits.append(f'{fmt(round(g["min"]))}–{fmt(round(g["max"]))} m alt.')
        if meta["grooming"].get(g["grooming"]):
            bits.append(meta["grooming"][g["grooming"]])
        if g["segments"] > 1:
            bits.append(f'{g["segments"]} tramos')
        pills = (pill("Nocturna") if g["lit"] else "") + (pill("Arbolada") if g["gladed"] else "")
        label = (f'{g["ref"]} · ' if g["ref"] else "") + g["name"]
        run_items.append(
            f'<div class="item run-item" data-key="{k}" data-run="{e(g["name"])}" role="button" tabindex="0" aria-expanded="false">'
            f'<span class="dot" style="background:{diff_color(k)}"></span><div class="item-main">'
            f'<div class="item-name">{e(label)}</div><div class="item-meta">{e(" · ".join(bits))}{pills}</div></div>'
            f'<span class="item-chevron" aria-hidden="true">›</span></div><div class="run-profile" hidden></div>')
    run_chip_defs = []
    for key, label, keys in RUN_FILTERS:
        count = len(run_groups) if key == "all" else sum(1 for g in run_groups if diff_key(g["difficulty"]) in keys)
        if key == "all" or count:
            run_chip_defs.append((keys, label, count, None if key == "all" else diff_color(key)))

    lift_items, lift_type_counts = [], {}
    for l in lifts:
        t = l.get("lift_type") or "other"
        lift_type_counts[t] = lift_type_counts.get(t, 0) + 1
        bits = []
        if l.get("capacity"):
            bits.append(f'{fmt(l["capacity"])} p/h')
        if l.get("occupancy"):
            bits.append(f'{l["occupancy"]} plazas')
        if l.get("length_m"):
            bits.append(f'{fmt(round(l["length_m"]))} m')
        if l.get("vertical_m"):
            bits.append(f'desnivel {fmt(round(l["vertical_m"]))} m')
        if l.get("duration_s"):
            m = round(l["duration_s"] / 60)
            bits.append((f"{m} min" if m >= 1 else f'{round(l["duration_s"])} s') + " de trayecto")
        pills = ((pill("Desembragable") if l.get("detachable") == 1 else "") + (pill("Burbuja") if l.get("bubble") == 1 else "")
                 + (pill("Calefactado") if l.get("heating") == 1 else "") + (pill("Privado") if l.get("access") == "private" else ""))
        label = ((f'{l["ref"]} · ' if l.get("ref") else "") + (l.get("name") or "Sin nombre")
                 + "  ·  " + meta["lift_types"].get(l.get("lift_type"), l.get("lift_type") or ""))
        lift_items.append(f'<div class="item" data-key="{e(t)}"><span class="dot" style="background:var(--accent)"></span>'
                          f'<div class="item-main"><div class="item-name">{e(label)}</div>'
                          f'<div class="item-meta">{e(" · ".join(bits))}{pills}</div></div></div>')
    lift_chip_defs = [(["all"], "Todos", len(lifts), None)] + [
        ([t], meta["lift_types"].get(t, t), n, None) for t, n in sorted(lift_type_counts.items(), key=lambda kv: -kv[1])]

    cat_order = list(meta["services"])
    svc_items, svc_counts = [], {}
    for s in sorted(services, key=lambda s: (cat_order.index(s["category"]), s.get("name") or "")):
        label, icon = meta["services"][s["category"]]
        svc_counts[s["category"]] = svc_counts.get(s["category"], 0) + 1
        bits = [x for x in [label if s.get("name") else None, s.get("opening_hours"), s.get("phone")] if x]
        svc_items.append(f'<div class="item" data-key="{s["category"]}"><span class="dot" style="background:var(--svc-{s["category"]})"></span>'
                         f'<div class="item-main"><div class="item-name">{icon} {e(s.get("name") or label)}</div>'
                         f'<div class="item-meta">{e(" · ".join(bits))}</div></div></div>')
    svc_chip_defs = [(["all"], "Todos", len(services), None)] + [
        ([k], f"{meta['services'][k][1]} {meta['services'][k][0]}", svc_counts[k], None) for k in cat_order if svc_counts.get(k)]

    def panel(key, items, chip_defs, empty_text, hidden):
        body = (chips(f"{key}-list", chip_defs) + f'<div class="list-scroll" id="{key}-list">{"".join(items)}</div>'
                if items else f'<div class="list-scroll"><div class="catalog-empty">{e(empty_text)}</div></div>')
        return f'<div class="catalog-panel" id="catalog-{key}"{" hidden" if hidden else ""}>{body}</div>'

    no_services = ("No hay servicios registrados en OpenStreetMap para esta estación." if raw.get("services") is not None
                   else "Todavía no tenemos datos de servicios para esta estación.")
    catalog_html = f"""<section>
<div class="section-head"><h2>Pistas, remontes y servicios</h2><span class="sub">pulsa una pista para ver su perfil</span></div>
<div class="segmented" role="tablist" aria-label="Qué listar">
<button type="button" role="tab" class="seg-btn" data-catalog="runs" aria-selected="true">Pistas <span class="seg-count">{len(run_groups)}</span></button>
<button type="button" role="tab" class="seg-btn" data-catalog="lifts" aria-selected="false">Remontes <span class="seg-count">{len(lifts)}</span></button>
<button type="button" role="tab" class="seg-btn" data-catalog="services" aria-selected="false">Servicios <span class="seg-count">{len(services)}</span></button>
</div>
{panel("runs", run_items, run_chip_defs, "No hay pistas con nombre en los datos de esta estación.", False)}
{panel("lifts", lift_items, lift_chip_defs, "No hay remontes en los datos de esta estación.", True)}
{panel("services", svc_items, svc_chip_defs, no_services, True)}
</section>"""

    # ----- data quality (same figures as the app) -----
    run_n, lift_n = len(runs) or 1, len(lifts) or 1
    pct = lambda n, d: f"{fmt(100 * n / d)}%"
    quality = [
        ("Pistas con nombre", f"{sum(1 for r in runs if r.get('name'))} / {len(runs)}"),
        ("Dificultad etiquetada", pct(sum(1 for r in runs if r.get("difficulty")), run_n)),
        ("Iluminación etiquetada", pct(sum(1 for r in runs if r.get("lit") is not None), run_n)),
        ("Nieve artificial etiquetada", pct(sum(1 for r in runs if r.get("snowmaking") is not None), run_n)),
        ("Capacidad de remonte etiquetada", pct(sum(1 for l in lifts if l.get("capacity") is not None), lift_n)),
        ("Tipo de agarre etiquetado", pct(sum(1 for l in lifts if l.get("detachable") is not None), lift_n)),
    ]
    quality_html = ('<section><div class="section-head"><h2>Calidad del dato</h2></div><div class="quality-list">'
                    + "".join(f'<div class="quality-row"><span class="name">{e(k)}</span><span class="val">{e(v)}</span></div>' for k, v in quality)
                    + '</div><p class="quality-note">Nieve artificial y vigilancia rara vez están etiquetadas en OpenStreetMap — '
                      'no significa que no existan, es que casi nadie las mapea todavía.</p></section>')

    # ----- sidebar: map card + nearby stations -----
    map_card = (f'<section class="map-card"><div class="section-head"><h2>Mapa interactivo</h2></div>'
                f'<p class="intro">Las pistas y remontes de {e(short)} sobre imagen de satélite, el sentido de cada pista, '
                f'la pendiente real de cada tramo, los servicios y el tiempo en directo.</p>'
                f'<a class="cta-block" href="{app_link}">{MAP_ICON} Abrir el mapa de {e(short)}</a></section>')
    ranks = ctx["ranks"].get(sid) or []
    ranks_html = ""
    if ranks:
        ranks_html = ('<section><div class="section-head"><h2>En los rankings</h2></div><div class="rank-list">'
                      + "".join(f'<a class="rank-link" href="{href}"><span class="rank-medal">★</span>{e(label)}</a>'
                                for label, href in ranks[:8])
                      + '</div></section>')
    nearby = ctx["nearby"].get(sid) or []
    nearby_html = ""
    if nearby:
        items = "".join(
            f'<a class="item" href="/estacion/{ctx["slug"][s["id"]]}/"><span class="dot" style="background:var(--accent)"></span>'
            f'<div class="item-main"><div class="item-name">{e(s["name"])}</div>'
            f'<div class="item-meta">a {fmt(round(d))} km · {fmt(round(s.get("pisteKm") or 0))} km de pistas</div></div>'
            f'<span class="item-chevron" aria-hidden="true">›</span></a>' for s, d in nearby)
        nearby_html = (f'<section><div class="section-head"><h2>Estaciones cercanas</h2></div>'
                       f'<div class="list-scroll">{items}</div></section>')

    # ----- snow + weather: a server-rendered summary from snow.json (so the
    # page says something about the coming week even without JS), replaced
    # by the full live forecast by static-pages.js + snow.js -----
    snow_html = ""
    if raw.get("latitude") is not None:
        fc = ctx["snow"].get(sid)
        top_txt = f" (cota alta, {fmt(round(hi))} m)" if hi is not None else ""
        if fc and fc.get("sf"):
            total_sf = sum(v or 0 for v in fc["sf"])
            when = ctx["snow_date"]
            summary = (f"Previsión de nieve para los próximos 7 días{top_txt}: "
                       + (f"{fmt(round(total_sf))} cm" if total_sf >= 1 else "sin nevadas significativas")
                       + (f" (actualizada el {when})." if when else "."))
        else:
            summary = f"Previsión de nieve y tiempo para los próximos 7 días en {e(short)}{top_txt}."
        attrs = f' data-lat="{raw["latitude"]:.4f}" data-lon="{raw["longitude"]:.4f}"'
        if lo is not None and hi is not None:
            attrs += f' data-top="{round(hi)}" data-base="{round(lo)}"'
        snow_html = (f'<section id="snow-section"{attrs}><div class="section-head"><h2>Nieve y tiempo en {e(short)}</h2></div>'
                     f'<div class="snow" id="snow-forecast"><p class="intro">{summary}</p></div></section>')

    body = f"""{hero}
<div class="layout">
<div class="main">
{intro_html}
{snow_html}
{charts_html}
{catalog_html}
{quality_html}
</div>
<aside class="sidebar">
{map_card}
{ranks_html}
{nearby_html}
</aside>
</div>"""

    title = f"{short}: mapa de pistas, previsión de nieve y remontes | Ski Info"
    desc_bits = []
    if total_m:
        desc_bits.append(f"{fmt(round(total_m / 1000))} km de pistas")
    if run_groups:
        desc_bits.append(f"{len(run_groups)} pistas")
    if lifts:
        desc_bits.append(f"{len(lifts)} remontes")
    description = short + (f" ({place_full})" if place_full else "") + ": " + (", ".join(desc_bits) + ". " if desc_bits else "")
    if lo is not None and hi is not None:
        description += f"Altitud {fmt(round(lo))}–{fmt(round(hi))} m. "
    description += "Previsión de nieve a 7 días, mapa de pistas interactivo sobre satélite y pendiente real de cada pista."

    jsonld = {"@context": "https://schema.org", "@type": "SkiResort", "name": name, "url": url}
    address = {"@type": "PostalAddress", "addressRegion": raw.get("region"), "addressLocality": raw.get("locality"), "addressCountry": cc}
    jsonld["address"] = {k: v for k, v in address.items() if v}
    if raw.get("latitude") is not None:
        jsonld["geo"] = {"@type": "GeoCoordinates", "latitude": round(raw["latitude"], 5), "longitude": round(raw["longitude"], 5)}
    jsonld["image"] = f"{base}/og/{ctx['slug'][sid]}.jpg"
    same_as = [x for x in [site, f"https://www.wikidata.org/wiki/{raw['wikidata_id']}" if raw.get("wikidata_id") else None] if x]
    if same_as:
        jsonld["sameAs"] = same_as

    return page(title=title, description=description, url=url, body=body,
                body_attrs=f' data-station="{e(sid)}" data-name="{e(name)}" data-country="{e(cc or "")}"',
                jsonld=jsonld, noindex=not indexable, scripts=True,
                image=f"/og/{ctx['slug'][sid]}.jpg", base_url=base), indexable


# ---------- country pages ----------

def station_card(href: str, name: str, sub: str, km: float, label: str = "pista", prefix: str = "") -> str:
    return (f'<a class="station-card" href="{href}"><div class="info"><div class="name">{prefix}{e(name)}</div>'
            f'<div class="region">{e(sub)}</div></div><div class="stats"><div class="km">{fmt(round(km))} km</div>'
            f'<div class="km-label">{e(label)}</div></div><span class="chevron" aria-hidden="true">›</span></a>')


def country_page(cc: str, stations: list, meta: dict, ctx: dict) -> str:
    name = meta["countries"].get(cc, (cc, ""))[0]
    url = f"{ctx['base_url']}/pais/{ctx['country_slug'][cc]}/"
    total = sum(s.get("pisteKm") or 0 for s in stations)
    cards = "".join(station_card(f'/estacion/{ctx["slug"][s["id"]]}/', s["name"], s.get("region") or "", s.get("pisteKm") or 0)
                    for s in stations)
    body = f"""<div class="list-header">
<div class="eyebrow"><a href="/">Ski Info</a> · <a href="/pais/">Países</a></div>
<h1>Estaciones de esquí en {e(name)}</h1>
<p class="list-sub">{len(stations)} estaciones · {fmt(round(total))} km de pistas. Elige una estación para ver todas sus pistas con su perfil de pendiente, sus remontes, servicios y el mapa interactivo sobre satélite.</p>
</div>
<div class="station-list">{cards}</div>"""
    return page(title=f"Estaciones de esquí en {name}: mapas de pistas | Ski Info",
                description=f"Las {len(stations)} estaciones de esquí de {name} con mapa de pistas interactivo, perfil de pendiente, remontes y servicios.",
                url=url, body=body)


def countries_index(by_country: dict, meta: dict, ctx: dict) -> str:
    order = sorted(by_country, key=lambda cc: -sum(s.get("pisteKm") or 0 for s in by_country[cc]))
    cards = "".join(
        station_card(f'/pais/{ctx["country_slug"][cc]}/', meta["countries"].get(cc, (cc, ""))[0], f"{len(by_country[cc])} estaciones",
                     sum(s.get("pisteKm") or 0 for s in by_country[cc]), "pista total",
                     prefix=f'<img class="flag" src="/flags/{cc.lower()}.svg" alt="" width="24" height="18" loading="lazy">')
        for cc in order)
    n = sum(len(v) for v in by_country.values())
    body = f"""<div class="list-header">
<div class="eyebrow"><a href="/">Ski Info</a></div>
<h1>Estaciones de esquí por país</h1>
<p class="list-sub">{n} estaciones en {len(by_country)} países, con mapa de pistas interactivo, perfil de pendiente de cada pista, remontes y servicios.</p>
</div>
<div class="station-list">{cards}</div>"""
    return page(title="Estaciones de esquí por país: mapas de pistas | Ski Info",
                description=f"Mapas de pistas interactivos de {n} estaciones de esquí en {len(by_country)} países: pistas, remontes, pendientes y servicios.",
                url=f"{ctx['base_url']}/pais/", body=body)


# ---------- /app: how to get Ski Info on your phone ----------

# Set to True once the app is in production on Google Play (the listing is
# not public while it's in closed testing).
PLAY_STORE_LIVE = False
PLAY_STORE_URL = "https://play.google.com/store/apps/details?id=com.sospedra.skiinfo"

IOS_SHARE = ('<svg viewBox="0 0 20 20" aria-hidden="true"><path d="M10 12.5V2.8M6.6 6 10 2.6 13.4 6" fill="none" stroke="currentColor" '
             'stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/><path d="M6.5 8.5H5v9h10v-9h-1.5" fill="none" '
             'stroke="currentColor" stroke-width="1.6" stroke-linejoin="round"/></svg>')
IOS_ADD = ('<svg viewBox="0 0 20 20" aria-hidden="true"><rect x="3" y="3" width="14" height="14" rx="3.5" fill="none" stroke="currentColor" '
           'stroke-width="1.6"/><path d="M10 6.5v7M6.5 10h7" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/></svg>')


def phone(inner: str) -> str:
    """A tiny phone mock-up (SVG) for the iPhone install steps."""
    return ('<svg class="phone" viewBox="0 0 120 200" aria-hidden="true">'
            '<rect x="3" y="3" width="114" height="194" rx="18" fill="var(--bg)" stroke="var(--text-muted)" stroke-width="2"/>'
            '<rect x="44" y="9" width="32" height="6" rx="3" fill="var(--text-muted)" opacity=".5"/>' + inner + '</svg>')


def app_page(ctx: dict, n_stations: int) -> str:
    safari_bar = phone(
        '<rect x="12" y="24" width="96" height="120" rx="6" fill="var(--hero-2)" opacity=".85"/>'
        '<path d="M12 110 40 74 58 96 74 80 108 116V144H12Z" fill="#fff" opacity=".85"/>'
        '<rect x="3" y="160" width="114" height="37" rx="0" fill="var(--surface-2)"/>'
        '<g stroke="var(--text-muted)" stroke-width="2" fill="none" stroke-linecap="round"><path d="M20 178l-5-5 5-5M36 168l5 5-5 5"/>'
        '<rect x="86" y="170" width="10" height="10" rx="2"/><rect x="99" y="167" width="10" height="10" rx="2"/></g>'
        '<circle cx="60" cy="176" r="13" fill="none" stroke="var(--accent)" stroke-width="2.5"/>'
        '<g stroke="var(--accent)" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round">'
        '<path d="M60 178v-11M56 170.5l4-4 4 4"/><path d="M55.5 173h-2v10h13v-10h-2"/></g>')
    share_sheet = phone(
        '<rect x="3" y="3" width="114" height="194" rx="18" fill="#000" opacity=".25"/>'
        '<rect x="8" y="70" width="104" height="124" rx="12" fill="var(--surface-2)"/>'
        '<g fill="var(--text-muted)" opacity=".45"><rect x="18" y="84" width="60" height="6" rx="3"/><rect x="18" y="104" width="46" height="6" rx="3"/></g>'
        '<rect x="12" y="120" width="96" height="24" rx="6" fill="var(--accent-soft)" stroke="var(--accent)" stroke-width="2"/>'
        '<text x="18" y="136" font-size="8.5" font-weight="700" fill="var(--text-primary)" font-family="IBM Plex Sans, sans-serif">Añadir a inicio</text>'
        '<g transform="translate(88 124)" stroke="var(--accent)" stroke-width="1.6" fill="none"><rect x="1" y="1" width="14" height="14" rx="3.5"/>'
        '<path d="M8 4.5v7M4.5 8h7" stroke-linecap="round"/></g>'
        '<g fill="var(--text-muted)" opacity=".45"><rect x="18" y="156" width="54" height="6" rx="3"/><rect x="18" y="176" width="40" height="6" rx="3"/></g>')
    home_screen = phone(
        '<rect x="3" y="3" width="114" height="194" rx="18" fill="url(#hs)"/>'
        '<defs><linearGradient id="hs" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#8fb3d9"/><stop offset="1" stop-color="#3c6ea8"/></linearGradient></defs>'
        '<g fill="#fff" opacity=".35"><rect x="16" y="30" width="18" height="18" rx="5"/><rect x="40" y="30" width="18" height="18" rx="5"/>'
        '<rect x="64" y="30" width="18" height="18" rx="5"/><rect x="16" y="62" width="18" height="18" rx="5"/><rect x="40" y="62" width="18" height="18" rx="5"/></g>'
        '<image href="/icons/icon-192.png" x="61" y="59" width="24" height="24"/>'
        '<rect x="58" y="56" width="30" height="30" rx="8" fill="none" stroke="#fff" stroke-width="2"/>'
        '<text x="73" y="96" font-size="7" fill="#fff" text-anchor="middle" font-family="IBM Plex Sans, sans-serif" font-weight="600">Ski Info</text>')

    if PLAY_STORE_LIVE:
        play_html = (f'<a class="store-badge" href="{PLAY_STORE_URL}" target="_blank" rel="noopener">'
                     '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 2.8v18.4c0 .4.4.6.7.4l16-9.2c.3-.2.3-.6 0-.8l-16-9.2c-.3-.2-.7 0-.7.4z" fill="currentColor"/></svg>'
                     '<span><small>Disponible en</small>Google Play</span></a>')
    else:
        play_html = ('<span class="store-badge soon"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 2.8v18.4c0 .4.4.6.7.4l16-9.2c.3-.2.3-.6 0-.8l-16-9.2c-.3-.2-.7 0-.7.4z" fill="currentColor"/></svg>'
                     '<span><small>Muy pronto en</small>Google Play</span></span>'
                     '<p class="app-note">La app está en fase de pruebas. Mientras tanto puedes usar Ski Info desde Chrome e instalarla: '
                     'menú <b>⋮</b> → <b>Añadir a pantalla de inicio</b> (o <b>Instalar aplicación</b>).</p>')

    hundreds = f"{n_stations // 100 * 100:,}".replace(",", ".")
    body = f"""<div class="app-hero">{PEAKS_SVG}<div class="app-hero-inner">
<div class="eyebrow app-eyebrow"><a href="/">Ski Info</a> · App</div>
<img class="app-logo" src="/icons/icon-192.png" alt="" width="84" height="84">
<h1>Ski Info en tu móvil</h1>
<p>Los mapas de pistas, la pendiente de cada pista y la previsión de nieve de {hundreds}+ estaciones, siempre a mano. Gratis y sin registro.</p>
</div></div>
<div class="app-wrap">
<div class="app-benefits">
<div><b>Se abre como una app</b><span>Con su icono en la pantalla de inicio, a pantalla completa.</span></div>
<div><b>Funciona con poca cobertura</b><span>Las estaciones que ya hayas consultado se abren aunque no tengas señal en pistas.</span></div>
<div><b>Siempre actualizada</b><span>Sin actualizaciones que descargar: siempre la última versión.</span></div>
</div>

<section class="app-card" id="app-android">
<h2><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M7 9h10v8a1.5 1.5 0 0 1-1.5 1.5h-7A1.5 1.5 0 0 1 7 17z M8.5 8a3.5 3.5 0 0 1 7 0z M9 5l-1-1.6M15 5l1-1.6" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linejoin="round" stroke-linecap="round"/></svg>Android</h2>
<p class="app-inapp" hidden>Ya estás usando la app de Ski Info. ¡Gracias!</p>
<div class="app-android-body">{play_html}</div>
</section>

<section class="app-card" id="app-ios">
<h2><svg viewBox="0 0 24 24" aria-hidden="true"><rect x="6.5" y="2.5" width="11" height="19" rx="2.5" fill="none" stroke="currentColor" stroke-width="1.6"/><path d="M10.5 18.5h3" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/></svg>iPhone y iPad</h2>
<p class="app-lead">No hace falta App Store: se instala desde <b>Safari</b> en tres pasos.</p>
<ol class="ios-steps">
<li>{safari_bar}<span class="step-n">1</span><span>Abre <b>skiinfoapp.com</b> en Safari y pulsa el botón <b>Compartir</b> <i class="ico">{IOS_SHARE}</i> de la barra de abajo.</span></li>
<li>{share_sheet}<span class="step-n">2</span><span>Desliza hacia abajo y pulsa <b>Añadir a pantalla de inicio</b> <i class="ico">{IOS_ADD}</i>.</span></li>
<li>{home_screen}<span class="step-n">3</span><span>Pulsa <b>Añadir</b>. Ski Info aparecerá en tu pantalla de inicio como cualquier otra app.</span></li>
</ol>
<p class="app-note">Si usas Chrome en el iPhone, el botón Compartir está arriba, junto a la barra de direcciones.</p>
</section>

<section class="app-card" id="app-desktop">
<h2><svg viewBox="0 0 24 24" aria-hidden="true"><rect x="3" y="4.5" width="18" height="12" rx="1.8" fill="none" stroke="currentColor" stroke-width="1.6"/><path d="M8.5 20h7M12 16.5V20" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/></svg>En el ordenador</h2>
<p class="app-lead">No hace falta instalar nada: entra en <a href="/">skiinfoapp.com</a>. En Chrome o Edge también puedes instalarla con el icono <b>Instalar</b> que aparece a la derecha de la barra de direcciones.</p>
</section>
</div>
<script>
(function () {{
  var ua = navigator.userAgent || '';
  var ios = /iPhone|iPad|iPod/.test(ua) || (navigator.platform === 'MacIntel' && navigator.maxTouchPoints > 1);
  var android = /Android/.test(ua);
  var wrap = document.querySelector('.app-wrap');
  var first = ios ? 'app-ios' : android ? 'app-android' : null;
  if (first) wrap.insertBefore(document.getElementById(first), wrap.querySelector('.app-card'));
  if (window.SkiInfoAndroid || /; wv\)/.test(ua)) {{
    document.querySelector('.app-inapp').hidden = false;
    document.querySelector('.app-android-body').hidden = true;
  }}
}})();
</script>"""
    return page(title="Descarga Ski Info: app de mapas de pistas y nieve para Android y iPhone",
                description="Instala Ski Info en tu móvil: mapas de pistas, pendiente de cada pista y previsión de nieve de "
                            f"{hundreds}+ estaciones de esquí. Android y iPhone, gratis y sin registro.",
                url=f"{ctx['base_url']}/app/", body=body, base_url=ctx["base_url"])


# ---------- home-page data inlined into the app ----------

HOME_EUROPE = {"ES", "FR", "AT", "IT", "CH", "AD", "DE", "SI", "NO", "SE", "FI", "PL", "CZ", "SK", "BG", "RO", "GE", "BA",
               "RS", "ME", "IS", "GB", "LI", "MK", "HR", "RU", "TR", "GR", "UA", "AM", "AZ"}
HOME_GUIDES = ["donde-nieva-esta-semana", "estaciones-mas-grandes-espana-andorra", "estaciones-para-principiantes-espana-andorra",
               "pistas-mas-empinadas-espana-andorra", "estaciones-de-esqui-cerca-de-madrid", "estaciones-de-esqui-cerca-de-barcelona"]


def inject_home_data(index_path: Path, snow_doc: dict | None, stations: list, guides_index: list) -> None:
    """Fill the app's <script id="home-data"> placeholder (docs/index.html) with
    the home page's snow ranking and featured guides, so they render with the
    page instead of arriving later and pushing content down. Only the stations
    that can make any zone's top list are included (the page ranks them)."""
    data = {"guides": [g for slug in HOME_GUIDES for g in guides_index if g["slug"] == slug]}
    if snow_doc and snow_doc.get("stations"):
        cc_of = {s["id"]: s.get("country") or "ES" for s in stations}
        ranked = sorted(((sum(v or 0 for v in f.get("sf") or []), sid) for sid, f in snow_doc["stations"].items()
                         if sid in cc_of), reverse=True)
        keep = set()
        for zone in (lambda cc: True, lambda cc: cc in HOME_EUROPE, lambda cc: cc in {"ES", "AD"}):
            keep.update([sid for _, sid in ranked if zone(cc_of[sid])][:30])
        data["snow"] = {"updated": snow_doc.get("updated"),
                        "stations": {sid: snow_doc["stations"][sid] for sid in keep}}
    html_text = index_path.read_text(encoding="utf-8")
    placeholder = re.compile(r'(<script id="home-data" type="application/json">).*?(</script>)', re.DOTALL)
    payload = json.dumps(data, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    new_text, n = placeholder.subn(lambda m: m.group(1) + payload + m.group(2), html_text, count=1)
    if n != 1:
        raise SystemExit(f"home-data placeholder not found in {index_path}")
    index_path.write_text(new_text, encoding="utf-8")


# ---------- main ----------

def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--docs", type=Path, default=REPO / "docs")
    ap.add_argument("--base-url", default="https://skiinfoapp.com")
    ap.add_argument("--write-slugs", action="store_true", help="persist slugs for new stations")
    ap.add_argument("--inject-home", action="store_true",
                    help="inline the home page's data into docs/index.html (deploy only: rewrites a committed file)")
    args = ap.parse_args()

    meta = load_app_metadata(read_app_sources(args.docs))
    stations = meta["stations"]
    by_id = {s["id"]: s for s in stations}

    pinned = json.loads(SLUGS_PATH.read_text()) if SLUGS_PATH.exists() else {}
    slug = {sid: sl for sid, sl in pinned.items() if sid in by_id}
    used = set(slug.values())
    for s in stations:
        if s["id"] in slug:
            continue
        cand = station_slug(s)
        for attempt in (cand, f"{cand}-{(s.get('country') or '').lower()}", f"{cand}-{s['id'][:6]}"):
            if attempt and attempt not in used:
                slug[s["id"]] = attempt
                used.add(attempt)
                break
    if args.write_slugs:
        SLUGS_PATH.write_text(json.dumps(dict(sorted(slug.items())), indent=0, ensure_ascii=False) + "\n")

    # id -> slug, for the app's share button and build_share_images.py.
    (args.docs / "slugs.json").write_text(json.dumps(slug, separators=(",", ":")), encoding="utf-8")

    by_country: dict[str, list] = {}
    for s in stations:
        by_country.setdefault(s.get("country") or "ES", []).append(s)
    for lst in by_country.values():
        lst.sort(key=lambda s: -(s.get("pisteKm") or 0))
    country_slug = {cc: slugify(meta["countries"].get(cc, (cc, ""))[0]) for cc in by_country}

    group_of = {sid: g for g in meta["groups"] for sid in g}
    coords = {s["id"]: (s["lat"], s["lon"]) for s in stations if s.get("lat") is not None}
    nearby = {}
    for sid, c in coords.items():
        dists = sorted((haversine_km(c, oc), oid) for oid, oc in coords.items() if oid != sid)
        nearby[sid] = [(by_id[oid], d) for d, oid in dists[:8] if d <= 150]

    # Written just before by fetch_snow_forecast.py; optional.
    snow, snow_date, snow_updated = {}, "", ""
    snow_path = args.docs / "snow.json"
    if snow_path.exists():
        doc = json.loads(snow_path.read_text(encoding="utf-8"))
        snow = doc.get("stations", {})
        snow_updated = doc.get("updated", "")
        months = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto",
                  "septiembre", "octubre", "noviembre", "diciembre"]
        y, m, d = (int(x) for x in doc.get("updated", "")[:10].split("-"))
        snow_date = f"{d} de {months[m - 1]}"

    ctx = {"base_url": args.base_url.rstrip("/"), "slug": slug, "country_slug": country_slug,
           "by_id": by_id, "group_of": group_of, "nearby": nearby, "snow": snow, "snow_date": snow_date}

    # First pass: the numbers the guides/rankings need, so station pages can
    # link to the rankings they appear in.
    from build_guides import build_guides, station_ranks, station_stats, write_all
    stats = []
    for s in stations:
        raw = json.loads((args.docs / "data" / f"{s['id']}.json").read_text(encoding="utf-8"))
        cc = s.get("country") or "ES"
        st = station_stats(raw, is_downhill)
        st.update(id=s["id"], name=short_name(s["name"]) or s["name"], cc=cc,
                  country=meta["countries"].get(cc, (cc, ""))[0], region=s.get("region"),
                  slug=slug[s["id"]], lat=s.get("lat") or raw.get("latitude") or 0, lon=s.get("lon") or raw.get("longitude") or 0)
        stats.append(st)
    guides = build_guides(stats, snow, snow_date, fmt, meta["diff"], snow_updated)
    ctx["ranks"] = station_ranks(guides)

    urls = [f"{ctx['base_url']}/", f"{ctx['base_url']}/pais/"]
    urls += write_all(args.docs, guides, page, e, ctx["base_url"])
    for s in stations:
        raw = json.loads((args.docs / "data" / f"{s['id']}.json").read_text(encoding="utf-8"))
        html_text, indexable = station_page(raw, meta, ctx)
        out = args.docs / "estacion" / slug[s["id"]] / "index.html"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(html_text, encoding="utf-8")
        if indexable:
            urls.append(f"{ctx['base_url']}/estacion/{slug[s['id']]}/")

    for cc, lst in by_country.items():
        out = args.docs / "pais" / country_slug[cc] / "index.html"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(country_page(cc, lst, meta, ctx), encoding="utf-8")
        urls.append(f"{ctx['base_url']}/pais/{country_slug[cc]}/")
    (args.docs / "pais" / "index.html").write_text(countries_index(by_country, meta, ctx), encoding="utf-8")
    (args.docs / "app").mkdir(exist_ok=True)
    (args.docs / "app" / "index.html").write_text(app_page(ctx, len(stations)), encoding="utf-8")
    urls.append(f"{ctx['base_url']}/app/")

    sitemap = ['<?xml version="1.0" encoding="UTF-8"?>',
               '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    sitemap += [f"  <url><loc>{html.escape(u)}</loc></url>" for u in urls]
    sitemap.append("</urlset>")
    (args.docs / "sitemap.xml").write_text("\n".join(sitemap) + "\n", encoding="utf-8")
    if args.inject_home:
        guides_index = json.loads((args.docs / "guias.json").read_text(encoding="utf-8"))
        snow_doc = json.loads((args.docs / "snow.json").read_text(encoding="utf-8")) if (args.docs / "snow.json").exists() else None
        inject_home_data(args.docs / "index.html", snow_doc, stations, guides_index)

    print(f"{len(stations)} station pages, {len(by_country)} country pages, {len(guides)} guides, {len(urls)} URLs in sitemap")


if __name__ == "__main__":
    main()
