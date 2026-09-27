"""Generate static, crawlable pages for search engines from the app's data.

The web app (docs/index.html) renders every station client-side from one URL,
so search engines only ever see a single page. This script writes one plain
HTML page per station (/estacion/<slug>/), one per country (/pais/<slug>/), a
country index (/pais/), and sitemap.xml -- each station page linking into the
interactive app via /?estacion=<id>.

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


# ---------- reading the app's own metadata out of index.html ----------

def js_block(src: str, var: str) -> str:
    start = src.index(f"var {var} = ")
    return src[start:src.index("\n  };", start)]


def load_app_metadata(index_html: str) -> dict:
    stations_line = next(l for l in index_html.splitlines() if l.startswith("  var STATIONS = "))
    groups_line = next(l for l in index_html.splitlines() if l.startswith("  var STATION_GROUPS = "))
    diff = dict(re.findall(r'(\w+):\s*\{ label: "([^"]+)"', js_block(index_html, "DIFF")))
    lift_types = dict(re.findall(r'"?([\w-]+)"?:\s*"([^"]+)"', js_block(index_html, "LIFT_TYPE")))
    services = {k: (label, icon) for k, label, icon in re.findall(
        r'(\w+): \{ label: "([^"]+)", icon: "([^"]+)"', js_block(index_html, "SERVICE_CATEGORIES"))}
    countries = {cc: name for cc, name in re.findall(
        r"(\w\w): \{ name: '([^']+)', flag: '[^']+' \}", js_block(index_html, "COUNTRY_META"))}
    diff_order = json.loads(re.search(r"var DIFF_ORDER = (\[.*?\]);", index_html).group(1))
    return {
        "stations": json.loads(stations_line.split(" = ", 1)[1].rstrip(";")),
        "groups": json.loads(groups_line.split(" = ", 1)[1].rstrip(";")),
        "diff": diff, "diff_order": diff_order, "lift_types": lift_types,
        "services": services, "countries": countries,
    }


# ---------- helpers ----------

PARENS = re.compile(r"\s*[(（][^)）]*[)）]")


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


def fmt_int(n: float) -> str:
    return f"{round(n):,}".replace(",", ".")


def fmt_km(m: float) -> str:
    km = m / 1000
    return (f"{km:.1f}".replace(".", ",") if km < 100 else fmt_int(km)) + " km"


def haversine_km(a: tuple, b: tuple) -> float:
    lat1, lon1, lat2, lon2 = map(math.radians, (a[0], a[1], b[0], b[1]))
    h = math.sin((lat2 - lat1) / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin((lon2 - lon1) / 2) ** 2
    return 2 * 6371 * math.asin(math.sqrt(h))


def e(text) -> str:
    return html.escape(str(text if text is not None else ""), quote=True)


def is_downhill(run: dict) -> bool:
    # Same filter as the app: untagged runs count, cross-country-only ones don't.
    uses = run.get("uses")
    return not uses or "downhill" in uses.split(",")


# ---------- page shell ----------

def page(*, title: str, description: str, url: str, body: str, jsonld: dict | None = None, noindex: bool = False) -> str:
    head_extra = '<meta name="robots" content="noindex">\n' if noindex else ""
    if jsonld:
        head_extra += ('<script type="application/ld+json">'
                       + json.dumps(jsonld, ensure_ascii=False).replace("</", "<\\/") + "</script>\n")
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
<meta name="theme-color" content="#14345C">
<link rel="stylesheet" href="/static-pages.css">
{head_extra}</head>
<body>
<div class="wrap">
{body}
<footer>
<a href="/">Ski Info</a> · <a href="/pais/">Estaciones por país</a> · <a href="/privacy.html">Privacidad</a><br>
Datos de OpenSkiMap / OpenStreetMap (licencia ODbL).
</footer>
</div>
</body>
</html>
"""


# ---------- station page ----------

def station_page(raw: dict, meta: dict, ctx: dict) -> tuple[str, bool]:
    base, sid = ctx["base_url"], raw["id"]
    country_name = meta["countries"].get(raw.get("country_code"), raw.get("country_code") or "")
    name = raw.get("name") or "Estación de esquí"
    short = short_name(name) or name
    place = ", ".join(p for p in [raw.get("locality"), raw.get("region")] if p)
    place_full = ", ".join(p for p in [place, country_name] if p)
    url = f"{base}/estacion/{ctx['slug'][sid]}/"
    app_link = f"/?estacion={sid}&amp;vista=mapa"

    runs = [r for r in raw.get("runs", []) if is_downhill(r)]
    lifts = raw.get("lifts", [])
    services = [s for s in raw.get("services") or [] if s.get("category") in meta["services"]]
    total_m = sum(r.get("length_m") or 0 for r in runs)

    diff_key = lambda d: d if d in meta["diff"] else "other"
    by_diff: dict[str, dict] = {}
    groups: dict[str, dict] = {}
    for r in runs:
        k = diff_key(r.get("difficulty"))
        by_diff.setdefault(k, {"count": 0, "m": 0.0})
        by_diff[k]["m"] += r.get("length_m") or 0
        nm = (r.get("name") or "").strip()
        if nm:
            g = groups.setdefault(nm, {"diff": k, "m": 0.0})
            g["m"] += r.get("length_m") or 0
    for g in groups.values():
        by_diff[g["diff"]]["count"] += 1
    named_count = len(groups)

    lo, hi = raw.get("min_elevation_m"), raw.get("max_elevation_m")
    indexable = bool(runs or lifts)

    # ----- hero -----
    stats = []
    if total_m:
        stats.append((fmt_km(total_m), "de pistas"))
    if named_count:
        stats.append((fmt_int(named_count), "pistas"))
    if lifts:
        stats.append((fmt_int(len(lifts)), "remontes"))
    if lo is not None and hi is not None:
        stats.append((f"{fmt_int(lo)}–{fmt_int(hi)} m", "altitud"))
        stats.append((f"{fmt_int(hi - lo)} m", "desnivel"))
    stats_html = "".join(f'<div class="stat"><span class="v">{e(v)}</span><span class="k">{e(k)}</span></div>' for v, k in stats)
    country_slug = ctx["country_slug"].get(raw.get("country_code"))
    crumbs = '<a href="/">Ski Info</a> › <a href="/pais/">Países</a>'
    if country_slug:
        crumbs += f' › <a href="/pais/{country_slug}/">{e(country_name)}</a>'
    parts = [f"""<header class="hero">
<nav class="crumbs">{crumbs}</nav>
<h1>{e(name)}</h1>
<p class="place">{e(place_full)}</p>
<div class="stats">{stats_html}</div>
<a class="cta" href="{app_link}">Abrir el mapa interactivo de pistas</a>
</header>
<main>"""]

    # ----- intro -----
    intro = [f"{e(short)} es una estación de esquí"]
    if place_full:
        intro[0] += f" en {e(place_full)}"
    intro[0] += "."
    if total_m and named_count:
        intro.append(f"Tiene {fmt_km(total_m)} de pistas repartidos en {fmt_int(named_count)} pistas con nombre"
                     + (f" y {fmt_int(len(lifts))} remontes" if lifts else "") + ".")
    if lo is not None and hi is not None:
        intro.append(f"Su dominio va de {fmt_int(lo)} a {fmt_int(hi)} m de altitud, con {fmt_int(hi - lo)} m de desnivel.")
    intro.append("En Ski Info puedes ver su mapa de pistas sobre imagen de satélite, el perfil de pendiente de cada pista "
                 "y los remontes y servicios en pistas.")
    site = (raw.get("websites") or [None])[0]
    site_html = f' <a href="{e(site)}" rel="noopener">Web oficial de la estación</a>.' if site else ""
    parts.append(f'<section><h2>{e(short)}: mapa de pistas y datos</h2><p>{" ".join(intro)}{site_html}</p></section>')

    # ----- difficulty table -----
    if by_diff:
        rows = "".join(
            f'<tr><td><span class="dot" style="background:var(--diff-{k})"></span>{e(meta["diff"][k])}</td>'
            f'<td class="num">{fmt_int(by_diff[k]["count"])}</td><td class="num">{fmt_km(by_diff[k]["m"])}</td></tr>'
            for k in meta["diff_order"] if k in by_diff)
        parts.append(f'<section><h2>Pistas de {e(short)} por dificultad</h2>'
                     f'<table><tr><th>Dificultad</th><th class="num">Pistas</th><th class="num">Longitud</th></tr>{rows}</table></section>')

    # ----- lifts by type -----
    if lifts:
        counts: dict[str, int] = {}
        for l in lifts:
            label = meta["lift_types"].get(l.get("lift_type"), l.get("lift_type") or "Otro")
            counts[label] = counts.get(label, 0) + 1
        rows = "".join(f'<tr><td>{e(k)}</td><td class="num">{fmt_int(v)}</td></tr>'
                       for k, v in sorted(counts.items(), key=lambda kv: -kv[1]))
        parts.append(f'<section><h2>Remontes de {e(short)}</h2>'
                     f'<table><tr><th>Tipo</th><th class="num">Número</th></tr>{rows}</table></section>')

    # ----- services -----
    if services:
        counts = {}
        for s in services:
            counts[s["category"]] = counts.get(s["category"], 0) + 1
        items = "".join(f'<li>{meta["services"][k][1]} {e(meta["services"][k][0])} <span class="m">· {v}</span></li>'
                        for k, v in sorted(counts.items(), key=lambda kv: -kv[1]))
        parts.append(f'<section><h2>Servicios en pistas</h2><ul class="cols">{items}</ul></section>')

    # ----- every named run -----
    if groups:
        blocks = []
        for k in meta["diff_order"]:
            names = sorted((n for n, g in groups.items() if g["diff"] == k), key=lambda n: -groups[n]["m"])
            if not names:
                continue
            lis = "".join(f'<li>{e(n)}' + (f' <span class="m">· {fmt_km(groups[n]["m"])}</span>' if groups[n]["m"] else "") + "</li>"
                          for n in names)
            blocks.append(f'<h3><span class="dot" style="background:var(--diff-{k})"></span>{e(meta["diff"][k])} ({len(names)})</h3>'
                          f'<ul class="cols">{lis}</ul>')
        parts.append(f'<section><h2>Todas las pistas de {e(short)}</h2>{"".join(blocks)}'
                     f'<p style="margin-top:12px"><a href="{app_link}">Ver cada pista en el mapa y su perfil de pendiente →</a></p></section>')

    # ----- named lifts -----
    named_lifts = [l for l in lifts if (l.get("name") or "").strip()]
    if named_lifts:
        lis = "".join(
            f'<li>{e(l["name"].strip())} <span class="m">· {e(meta["lift_types"].get(l.get("lift_type"), l.get("lift_type") or ""))}</span></li>'
            for l in sorted(named_lifts, key=lambda l: l["name"].strip().lower()))
        parts.append(f'<section><h2>Lista de remontes</h2><ul class="cols">{lis}</ul></section>')

    # ----- connected + nearby stations -----
    def station_li(s, extra=""):
        return f'<li><a href="/estacion/{ctx["slug"][s["id"]]}/">{e(s["name"])}</a><span class="m">{extra}</span></li>'

    group = ctx["group_of"].get(sid)
    if group:
        lis = "".join(station_li(ctx["by_id"][o], f'{fmt_int(ctx["by_id"][o].get("pisteKm") or 0)} km')
                      for o in group if o != sid and o in ctx["by_id"])
        if lis:
            parts.append(f'<section><h2>Dominio esquiable conectado</h2><p>Estaciones unidas por pistas o remontes con {e(short)}:</p>'
                         f'<ul class="links">{lis}</ul></section>')
    nearby = ctx["nearby"].get(sid) or []
    if nearby:
        lis = "".join(station_li(s, f"a {fmt_int(d)} km") for s, d in nearby)
        parts.append(f'<section><h2>Estaciones de esquí cerca de {e(short)}</h2><ul class="links">{lis}</ul></section>')

    parts.append(f'<section><p><a class="cta" style="background:var(--accent);color:#fff" href="{app_link}">Abrir el mapa interactivo de {e(short)}</a></p></section>')
    parts.append("</main>")

    title = f"{short}: mapa de pistas, remontes y datos | Ski Info"
    desc_bits = []
    if total_m:
        desc_bits.append(f"{fmt_km(total_m)} de pistas")
    if named_count:
        desc_bits.append(f"{fmt_int(named_count)} pistas")
    if lifts:
        desc_bits.append(f"{fmt_int(len(lifts))} remontes")
    description = f"{short}" + (f" ({place_full})" if place_full else "") + ": " + (", ".join(desc_bits) + ". " if desc_bits else "")
    if lo is not None and hi is not None:
        description += f"Altitud {fmt_int(lo)}–{fmt_int(hi)} m. "
    description += "Mapa de pistas interactivo sobre satélite y pendiente real de cada pista."

    jsonld = {"@context": "https://schema.org", "@type": "SkiResort", "name": name, "url": url,
              "address": {"@type": "PostalAddress", "addressRegion": raw.get("region") or None,
                          "addressLocality": raw.get("locality") or None, "addressCountry": raw.get("country_code")}}
    if raw.get("latitude") is not None:
        jsonld["geo"] = {"@type": "GeoCoordinates", "latitude": round(raw["latitude"], 5), "longitude": round(raw["longitude"], 5)}
    same_as = [x for x in [site, f"https://www.wikidata.org/wiki/{raw['wikidata_id']}" if raw.get("wikidata_id") else None] if x]
    if same_as:
        jsonld["sameAs"] = same_as
    jsonld["address"] = {k: v for k, v in jsonld["address"].items() if v}

    return page(title=title, description=description, url=url, body="\n".join(parts), jsonld=jsonld, noindex=not indexable), indexable


# ---------- country pages ----------

def country_page(cc: str, stations: list, meta: dict, ctx: dict) -> str:
    name = meta["countries"].get(cc, cc)
    url = f"{ctx['base_url']}/pais/{ctx['country_slug'][cc]}/"
    total = sum(s.get("pisteKm") or 0 for s in stations)
    lis = "".join(
        f'<li><a href="/estacion/{ctx["slug"][s["id"]]}/">{e(s["name"])}</a>'
        f'<span class="m">{e(s.get("region") or "")}{" · " if s.get("region") else ""}{fmt_int(s.get("pisteKm") or 0)} km</span></li>'
        for s in stations)
    body = f"""<header class="hero">
<nav class="crumbs"><a href="/">Ski Info</a> › <a href="/pais/">Países</a></nav>
<h1>Estaciones de esquí en {e(name)}</h1>
<p class="place">{len(stations)} estaciones · {fmt_int(total)} km de pistas</p>
<a class="cta" href="/">Abrir Ski Info</a>
</header>
<main>
<section><p>Mapas de pistas interactivos sobre imagen de satélite, perfil de pendiente de cada pista, remontes y servicios de las estaciones de esquí de {e(name)}, ordenadas por kilómetros de pistas.</p>
<ul class="links">{lis}</ul></section>
</main>"""
    return page(title=f"Estaciones de esquí en {name}: mapas de pistas | Ski Info",
                description=f"Las {len(stations)} estaciones de esquí de {name} con mapa de pistas interactivo, perfil de pendiente, remontes y servicios.",
                url=url, body=body)


def countries_index(by_country: dict, meta: dict, ctx: dict) -> str:
    order = sorted(by_country, key=lambda cc: -sum(s.get("pisteKm") or 0 for s in by_country[cc]))
    lis = "".join(
        f'<li><a href="/pais/{ctx["country_slug"][cc]}/">{e(meta["countries"].get(cc, cc))}</a>'
        f'<span class="m">{len(by_country[cc])} estaciones · {fmt_int(sum(s.get("pisteKm") or 0 for s in by_country[cc]))} km</span></li>'
        for cc in order)
    n = sum(len(v) for v in by_country.values())
    body = f"""<header class="hero">
<nav class="crumbs"><a href="/">Ski Info</a></nav>
<h1>Estaciones de esquí por país</h1>
<p class="place">{n} estaciones en {len(by_country)} países</p>
<a class="cta" href="/">Abrir Ski Info</a>
</header>
<main><section><ul class="links">{lis}</ul></section></main>"""
    return page(title="Estaciones de esquí por país: mapas de pistas | Ski Info",
                description=f"Mapas de pistas interactivos de {n} estaciones de esquí en {len(by_country)} países: pistas, remontes, pendientes y servicios.",
                url=f"{ctx['base_url']}/pais/", body=body)


# ---------- main ----------

def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--docs", type=Path, default=REPO / "docs")
    ap.add_argument("--base-url", default="https://skiinfoapp.com")
    ap.add_argument("--write-slugs", action="store_true", help="persist slugs for new stations")
    args = ap.parse_args()

    meta = load_app_metadata((args.docs / "index.html").read_text(encoding="utf-8"))
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

    by_country: dict[str, list] = {}
    for s in stations:
        by_country.setdefault(s.get("country") or "ES", []).append(s)
    for lst in by_country.values():
        lst.sort(key=lambda s: -(s.get("pisteKm") or 0))
    country_slug = {cc: slugify(meta["countries"].get(cc, cc)) for cc in by_country}

    group_of = {sid: g for g in meta["groups"] for sid in g}
    coords = {s["id"]: (s["lat"], s["lon"]) for s in stations if s.get("lat") is not None}
    nearby = {}
    for sid, c in coords.items():
        dists = sorted((haversine_km(c, oc), oid) for oid, oc in coords.items() if oid != sid)
        nearby[sid] = [(by_id[oid], d) for d, oid in dists[:6] if d <= 150]

    ctx = {"base_url": args.base_url.rstrip("/"), "slug": slug, "country_slug": country_slug,
           "by_id": by_id, "group_of": group_of, "nearby": nearby}

    urls = [f"{ctx['base_url']}/", f"{ctx['base_url']}/pais/"]
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

    sitemap = ['<?xml version="1.0" encoding="UTF-8"?>',
               '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    sitemap += [f"  <url><loc>{html.escape(u)}</loc></url>" for u in urls]
    sitemap.append("</urlset>")
    (args.docs / "sitemap.xml").write_text("\n".join(sitemap) + "\n", encoding="utf-8")
    print(f"{len(stations)} station pages, {len(by_country)} country pages, {len(urls)} URLs in sitemap")


if __name__ == "__main__":
    main()
