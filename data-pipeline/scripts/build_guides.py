"""Guides and rankings (/guias/...) built from the stations' own data.

Called by build_seo_pages.py: collect() is fed every station's stats first,
then guides() works out each ranking (and which stations appear in which, so
station pages can link back), and write() renders the pages. Everything is
derived from OpenStreetMap data, the same numbers the app shows, so the pages
stay correct as data is refreshed -- and "Dónde nieva esta semana" changes
with every daily deploy (snow.json).
"""
from __future__ import annotations

import json
import math
import re
from dataclasses import dataclass, field
from pathlib import Path

# Official piste grades only: freeride/extreme itineraries and ungraded
# "descenso" ways would otherwise fill the steepest-run lists.
GRADED = {"novice", "easy", "intermediate", "advanced", "expert"}
IBERIA = {"ES", "AD"}
# Unpatrolled ski routes / itineraries sometimes carry a piste grade in OSM.
NOT_A_PISTE = re.compile(r"^descenso|ski ?route|skiroute|itin[eé]rai|itinerar|freeride|variante", re.IGNORECASE)
ALPS_CC = {"FR", "CH", "IT", "AT", "DE", "SI", "LI"}

CITIES = {
    "madrid": ("Madrid", 40.4168, -3.7038),
    "barcelona": ("Barcelona", 41.3874, 2.1686),
    "valencia": ("Valencia", 39.4699, -0.3763),
    "bilbao": ("Bilbao", 43.2630, -2.9350),
    "zaragoza": ("Zaragoza", 41.6488, -0.8891),
    "sevilla": ("Sevilla", 37.3891, -5.9845),
    "malaga": ("Málaga", 36.7213, -4.4214),
    "pamplona": ("Pamplona", 42.8125, -1.6458),
}


def in_pyrenees(s: dict) -> bool:
    return s["cc"] in {"ES", "AD", "FR"} and 42.0 <= s["lat"] <= 43.4 and -2.0 <= s["lon"] <= 3.3


def in_alps(s: dict) -> bool:
    return s["cc"] in ALPS_CC and 43.8 <= s["lat"] <= 48.2 and 5.0 <= s["lon"] <= 16.5


def haversine_km(lat1, lon1, lat2, lon2) -> float:
    p = math.pi / 180
    a = (math.sin((lat2 - lat1) * p / 2) ** 2
         + math.cos(lat1 * p) * math.cos(lat2 * p) * math.sin((lon2 - lon1) * p / 2) ** 2)
    return 12742 * math.asin(math.sqrt(a))


def station_stats(raw: dict, is_downhill) -> dict:
    """The per-station numbers the rankings need (no geometry kept)."""
    runs = [r for r in raw.get("runs", []) if is_downhill(r)]
    km = sum(r.get("length_m") or 0 for r in runs) / 1000
    easy_km = sum(r.get("length_m") or 0 for r in runs if r.get("difficulty") in ("novice", "easy")) / 1000
    groups: dict[str, dict] = {}
    for r in runs:
        if not r.get("name"):
            continue
        g = groups.setdefault(r["name"], {"name": r["name"], "len": 0.0, "vert": 0.0, "diff": r.get("difficulty")})
        g["len"] += r.get("length_m") or 0
        g["vert"] += r.get("vertical_m") or 0
    return {
        "km": km, "easy_km": easy_km,
        "lo": raw.get("min_elevation_m"), "hi": raw.get("max_elevation_m"),
        "n_runs": len(groups), "n_lifts": len(raw.get("lifts") or []),
        "runs": [g for g in groups.values() if g["len"] >= 300 and not NOT_A_PISTE.search(g["name"])],
    }


@dataclass
class Item:
    station: dict                 # {"id", "name", "cc", "region", "slug", ...stats}
    metric: str                   # big number, e.g. "154 km"
    metric_label: str             # small label under it
    meta: str = ""                # secondary line
    title: str | None = None      # run name for run rankings (else the station name)
    diff: str | None = None       # run difficulty (dot colour)
    spark: list | None = None     # daily snowfall (snow guide)


@dataclass
class Guide:
    slug: str
    group: str
    title: str                    # <title> / card title
    h1: str
    intro: str
    method: str
    items: list[Item] = field(default_factory=list)
    kind: str = "station"         # station | run | snow
    rank_label: str = ""          # "Estaciones más grandes de España y Andorra" (for station-page chips)
    empty_text: str = ""
    updated: str = ""             # ISO date of the data behind it (snow guide)


def build_guides(stations: list[dict], snow: dict, snow_date: str, fmt_es, diff_labels: dict,
                 snow_updated: str = "") -> list[Guide]:
    """stations: dicts with id, name (display), cc, country, region, slug, lat, lon + station_stats()."""
    fmt = fmt_es
    real = [s for s in stations if s["km"] >= 3]
    guides: list[Guide] = []

    def place(s):
        return ", ".join(p for p in [s.get("region"), s["country"]] if p)

    def station_meta(s):
        bits = [f"{s['n_runs']} pistas" if s["n_runs"] else None, f"{s['n_lifts']} remontes" if s["n_lifts"] else None]
        if s["lo"] is not None and s["hi"] is not None:
            bits.append(f"{fmt(round(s['lo']))}–{fmt(round(s['hi']))} m")
        return " · ".join(b for b in bits if b)

    # ---- biggest ----
    for slug, zone, zone_txt, pick, n in (
        ("estaciones-mas-grandes-espana-andorra", "España y Andorra", "de España y Andorra", lambda s: s["cc"] in IBERIA, 20),
        ("estaciones-mas-grandes-pirineos", "los Pirineos", "de los Pirineos", in_pyrenees, 20),
        ("estaciones-mas-grandes-alpes", "los Alpes", "de los Alpes", in_alps, 25),
        ("estaciones-mas-grandes-del-mundo", "el mundo", "del mundo", lambda s: True, 25),
    ):
        lst = sorted((s for s in real if pick(s)), key=lambda s: -s["km"])[:n]
        if not lst:
            continue
        top = lst[0]
        intro = (f"Las {len(lst)} estaciones de esquí con más kilómetros de pistas {zone_txt}. "
                 f"La más grande es {top['name']} ({place(top)}), con {fmt(round(top['km']))} km de pistas"
                 + (f", seguida de {lst[1]['name']} ({fmt(round(lst[1]['km']))} km)" if len(lst) > 1 else "")
                 + (f" y {lst[2]['name']} ({fmt(round(lst[2]['km']))} km)." if len(lst) > 2 else ".")
                 + " Pulsa cualquiera para ver su mapa de pistas, el perfil de cada pista y la previsión de nieve.")
        guides.append(Guide(
            slug=slug, group="Estaciones", kind="station",
            title=f"Las estaciones de esquí más grandes {zone_txt}",
            h1=f"Las estaciones de esquí más grandes {zone_txt}",
            intro=intro,
            method="Ordenadas por la suma de la longitud de todas sus pistas de esquí alpino según OpenStreetMap "
                   "(no se cuentan los circuitos de fondo). Las cifras oficiales de cada estación pueden variar algo "
                   "porque cada una mide sus pistas a su manera.",
            rank_label=f"Estaciones más grandes {zone_txt}",
            items=[Item(s, f"{fmt(round(s['km']))} km", "de pistas", station_meta(s)) for s in lst]))

    # ---- beginners ----
    for slug, zone_txt, pick, min_km, n in (
        ("estaciones-para-principiantes-espana-andorra", "de España y Andorra", lambda s: s["cc"] in IBERIA, 10, 15),
        ("estaciones-para-principiantes-alpes", "de los Alpes", in_alps, 40, 20),
    ):
        lst = [s for s in real if pick(s) and s["km"] >= min_km and s["easy_km"] > 0]
        lst.sort(key=lambda s: (-s["easy_km"] / s["km"], -s["km"]))
        lst = lst[:n]
        if not lst:
            continue
        top = lst[0]
        intro = (f"Las estaciones {zone_txt} donde más proporción de pistas son verdes y azules: ideales para aprender "
                 f"o para esquiar tranquilo. Encabeza la lista {top['name']}, con un {fmt(round(100 * top['easy_km'] / top['km']))} % "
                 f"de sus {fmt(round(top['km']))} km en pistas fáciles. Solo entran estaciones de al menos {min_km} km, "
                 "para que haya terreno suficiente para progresar.")
        guides.append(Guide(
            slug=slug, group="Estaciones", kind="station",
            title=f"Mejores estaciones de esquí para principiantes {zone_txt}",
            h1=f"Las mejores estaciones para principiantes {zone_txt}",
            intro=intro,
            method="Porcentaje de kilómetros de pistas verdes y azules sobre el total de pistas de esquí alpino, "
                   f"entre las estaciones con al menos {min_km} km. Datos de dificultad de OpenStreetMap.",
            rank_label=f"Mejores para principiantes {zone_txt}",
            items=[Item(s, f"{fmt(round(100 * s['easy_km'] / s['km']))} %", "pistas fáciles",
                        f"{fmt(round(s['easy_km']))} de {fmt(round(s['km']))} km verdes o azules · {station_meta(s)}") for s in lst]))

    # ---- highest / biggest vertical ----
    for slug, zone_txt, pick, key, label, n in (
        ("estaciones-mas-altas-espana-andorra", "de España y Andorra", lambda s: s["cc"] in IBERIA, "hi", "altas", 15),
        ("estaciones-mas-altas-alpes", "de los Alpes", in_alps, "hi", "altas", 20),
        ("estaciones-con-mas-desnivel-espana-andorra", "de España y Andorra", lambda s: s["cc"] in IBERIA, "vert", "desnivel", 15),
    ):
        pool = [s for s in real if pick(s) and s["hi"] is not None and s["lo"] is not None]
        val = (lambda s: s["hi"]) if key == "hi" else (lambda s: s["hi"] - s["lo"])
        lst = sorted(pool, key=lambda s: -val(s))[:n]
        if not lst:
            continue
        top = lst[0]
        if key == "hi":
            title = f"Las estaciones de esquí más altas {zone_txt}"
            intro = (f"Las estaciones {zone_txt} que llegan más alto. Más altitud suele significar nieve de más calidad "
                     f"y temporadas más largas. La más alta es {top['name']}, que alcanza los {fmt(round(top['hi']))} m.")
            method = "Cota más alta a la que llega una pista o un remonte de la estación, según OpenStreetMap y el modelo de elevación."
            rank = f"Estaciones más altas {zone_txt}"
            items = [Item(s, f"{fmt(round(s['hi']))} m", "cota máxima", f"desde {fmt(round(s['lo']))} m · {fmt(round(s['km']))} km de pistas") for s in lst]
        else:
            title = f"Las estaciones de esquí con más desnivel {zone_txt}"
            intro = (f"Las estaciones {zone_txt} con más metros de desnivel entre su punto más bajo y el más alto: "
                     f"las bajadas más largas del día. Lidera {top['name']}, con {fmt(round(val(top)))} m de desnivel.")
            method = "Diferencia entre la cota más alta y la más baja de las pistas y remontes de la estación."
            rank = f"Estaciones con más desnivel {zone_txt}"
            items = [Item(s, f"{fmt(round(val(s)))} m", "de desnivel", f"{fmt(round(s['lo']))}–{fmt(round(s['hi']))} m · {fmt(round(s['km']))} km de pistas") for s in lst]
        guides.append(Guide(slug=slug, group="Estaciones", kind="station", title=title, h1=title,
                            intro=intro, method=method, rank_label=rank, items=items))

    # ---- runs: steepest / longest ----
    for slug, zone_txt, pick, key, n in (
        ("pistas-mas-empinadas-espana-andorra", "de España y Andorra", lambda s: s["cc"] in IBERIA, "steep", 25),
        ("pistas-mas-empinadas-alpes", "de los Alpes", in_alps, "steep", 25),
        ("pistas-mas-largas-espana-andorra", "de España y Andorra", lambda s: s["cc"] in IBERIA, "long", 25),
        ("pistas-mas-largas-alpes", "de los Alpes", in_alps, "long", 25),
    ):
        rows, seen = [], set()
        for s in real:
            if not pick(s):
                continue
            for r in s["runs"]:
                if r["diff"] not in GRADED or r["len"] <= 0:
                    continue
                # Overlapping OSM areas (a resort and its whole ski circuit) share runs.
                key_ = (r["name"].lower(), round(r["len"] / 250))
                if key_ in seen:
                    continue
                seen.add(key_)
                rows.append((s, r, 100 * r["vert"] / r["len"]))
        if key == "steep":
            rows.sort(key=lambda x: -x[2])
        else:
            rows.sort(key=lambda x: -x[1]["len"])
        rows = rows[:n]
        if not rows:
            continue
        s0, r0, p0 = rows[0]
        if key == "steep":
            title = f"Las pistas de esquí más empinadas {zone_txt}"
            intro = (f"Las {len(rows)} pistas con más pendiente media {zone_txt}, medida de arriba abajo con el modelo de elevación. "
                     f"La más empinada es {r0['name']}, en {s0['name']}, con un {fmt(round(p0))} % de pendiente media "
                     f"en {fmt(round(r0['len']))} m. En la ficha de cada estación puedes ver el perfil de la pista tramo a tramo.")
            method = ("Pendiente media = desnivel total ÷ longitud de la pista (en %), para pistas oficiales (verde a negra) "
                      "de al menos 300 m. En los tramos más duros la inclinación puntual es mayor que la media.")
            items = [Item(s, f"{fmt(round(p))} %", "pend. media",
                          f"{fmt(round(r['len']))} m · desnivel {fmt(round(r['vert']))} m · {diff_labels.get(r['diff'], '')}",
                          title=r["name"], diff=r["diff"]) for s, r, p in rows]
            rank = f"Pistas más empinadas {zone_txt}"
        else:
            title = f"Las pistas de esquí más largas {zone_txt}"
            intro = (f"Las {len(rows)} pistas más largas {zone_txt}. La primera es {r0['name']}, en {s0['name']}, "
                     f"con {fmt(r0['len'] / 1000, 1)} km de bajada y {fmt(round(r0['vert']))} m de desnivel.")
            method = ("Longitud total de cada pista con nombre (sumando sus tramos) según OpenStreetMap, para pistas oficiales "
                      "de verde a negra.")
            items = [Item(s, f"{fmt(r['len'] / 1000, 1)} km", "de bajada",
                          f"desnivel {fmt(round(r['vert']))} m · pend. media {fmt(round(p))} % · {diff_labels.get(r['diff'], '')}",
                          title=r["name"], diff=r["diff"]) for s, r, p in rows]
            rank = f"Pistas más largas {zone_txt}"
        guides.append(Guide(slug=slug, group="Pistas", kind="run", title=title, h1=title,
                            intro=intro, method=method, rank_label=rank, items=items))

    # ---- near a city ----
    near_pool = [s for s in real if s["cc"] in {"ES", "AD", "FR"}]
    for cslug, (cname, clat, clon) in CITIES.items():
        rows = sorted(((haversine_km(clat, clon, s["lat"], s["lon"]), s) for s in near_pool), key=lambda x: x[0])
        rows = [(d, s) for d, s in rows if d <= 450][:12]
        if not rows:
            continue
        d0, s0 = rows[0]
        intro = (f"Las estaciones de esquí más cercanas a {cname}, de la más próxima a la más lejana. "
                 f"La más cercana es {s0['name']}, a unos {fmt(round(d0))} km en línea recta"
                 + (f"; a menos de 250 km tienes {sum(1 for d, _ in rows if d <= 250)} estaciones." if rows else ".")
                 + " Pulsa «Cómo llegar» en la ficha de cada una para ver la ruta en coche.")
        guides.append(Guide(
            slug=f"estaciones-de-esqui-cerca-de-{cslug}", group="Cerca de tu ciudad", kind="station",
            title=f"Estaciones de esquí cerca de {cname}",
            h1=f"Estaciones de esquí cerca de {cname}",
            intro=intro,
            method="Distancia en línea recta desde el centro de la ciudad hasta la estación; por carretera siempre es más. "
                   "Incluye estaciones de España, Andorra y Francia con al menos 3 km de pistas.",
            rank_label=f"Estaciones cerca de {cname}",
            items=[Item(s, f"{fmt(round(d))} km", "en línea recta", f"{fmt(round(s['km']))} km de pistas · {station_meta(s)}") for d, s in rows]))

    # ---- snow this week ----
    by_id = {s["id"]: s for s in stations}
    snow_rows = []
    for sid, f in (snow or {}).items():
        s = by_id.get(sid)
        if s and f.get("sf"):
            total = sum(v or 0 for v in f["sf"])
            if total >= 1:
                snow_rows.append((total, s, f["sf"]))
    snow_rows.sort(key=lambda x: -x[0])
    world = snow_rows[:20]
    when = f" (previsión del {snow_date})" if snow_date else ""
    if world:
        t0, s0, _ = world[0]
        intro = (f"Las estaciones de esquí donde más nieve se espera en los próximos 7 días{when}, en su cota más alta. "
                 f"Encabeza la lista {s0['name']} ({place(s0)}), con unos {fmt(round(t0))} cm previstos. "
                 "Se actualiza cada día; en la ficha de cada estación tienes la previsión día a día.")
    else:
        intro = (f"Ahora mismo no se esperan nevadas significativas en ninguna estación en los próximos 7 días{when}. "
                 "Esta página se actualiza cada día con la previsión de nieve de más de 1.200 estaciones.")
    guides.append(Guide(
        slug="donde-nieva-esta-semana", group="Nieve", kind="snow", updated=snow_updated[:10],
        title="Dónde va a nevar esta semana: previsión de nieve en las estaciones",
        h1="Dónde va a nevar esta semana",
        intro=intro,
        method="Suma de la nieve prevista para los próximos 7 días por los modelos meteorológicos (Open-Meteo) en la cota "
               "más alta de cada estación. Es una previsión, no el parte oficial de nieve de la estación.",
        rank_label="",
        items=[Item(s, f"{fmt(round(t))} cm", "en 7 días", station_meta(s), spark=sf) for t, s, sf in world]))
    return guides


# ---------- rendering ----------

def item_html(it: Item, pos: int, e, diff_color) -> str:
    s = it.station
    href = f"/estacion/{s['slug']}/"
    thumb = f'<img class="guide-thumb" src="/og/thumb/{s["slug"]}.jpg" alt="" width="72" height="77" loading="lazy">'
    if it.title:  # a run: run name first, then its station
        name = (f'<span class="guide-name"><span class="dot" style="background:var(--diff-{it.diff or "other"})"></span>'
                f'{e(it.title)}</span><span class="guide-sub">{e(s["name"])} · {e(s["country"])}</span>')
    else:
        name = (f'<span class="guide-name"><img class="flag" src="/flags/{s["cc"].lower()}.svg" alt="" width="20" height="15">'
                f'{e(s["name"])}</span><span class="guide-sub">{e(" · ".join(p for p in [s.get("region"), s["country"]] if p))}</span>')
    spark = ""
    if it.spark:
        mx = max(max(v or 0 for v in it.spark), 5)
        spark = '<span class="guide-spark" aria-hidden="true">' + "".join(
            f'<i style="height:{max(8, (v or 0) / mx * 100):.0f}%"></i>' if (v or 0) > 0.05 else '<i class="z"></i>'
            for v in it.spark) + "</span>"
    return (f'<li><a class="guide-item" href="{href}"><span class="guide-rank">{pos}</span>{thumb}'
            f'<span class="guide-main">{name}<span class="guide-meta">{e(it.meta)}</span></span>{spark}'
            f'<span class="guide-metric"><b>{e(it.metric)}</b><small>{e(it.metric_label)}</small></span></a></li>')


def guide_page(g: Guide, guides: list[Guide], page, e, base_url: str) -> str:
    url = f"{base_url}/guias/{g.slug}/"
    items = "".join(item_html(it, i + 1, e, None) for i, it in enumerate(g.items))
    stale = ""
    if g.updated:
        # The forecast is refreshed by the daily deploy; if that ever stops,
        # say how old it is instead of passing it off as this week's.
        stale = (f'<p class="guide-stale" id="guide-stale" data-updated="{g.updated}" hidden></p>'
                 '<script>(function(){var el=document.getElementById("guide-stale"),d=el.getAttribute("data-updated");'
                 'var days=Math.floor((Date.now()-Date.parse(d+"T12:00:00Z"))/864e5);if(days>=2){el.textContent='
                 '"Atención: esta previsión es del "+new Date(d+"T12:00:00Z").toLocaleDateString("es-ES",{day:"numeric",month:"long"})'
                 '+" y puede estar desactualizada. En la ficha de cada estación tienes la previsión en directo.";el.hidden=false;}})();</script>')
    body_list = stale + (f'<ol class="guide-list">{items}</ol>' if g.items
                 else f'<p class="intro guide-empty">{e(g.empty_text or "Ahora mismo no hay estaciones en esta lista.")}</p>')
    related = [x for x in guides if x.slug != g.slug and x.group == g.group][:6]
    related += [x for x in guides if x.slug != g.slug and x.group != g.group and x not in related][: max(0, 8 - len(related))]
    related_html = "".join(f'<a class="chip" href="/guias/{x.slug}/">{e(x.h1)}</a>' for x in related)
    body = f"""<div class="guide-head">
<div class="eyebrow"><a href="/">Ski Info</a> · <a href="/guias/">Guías</a> · {e(g.group)}</div>
<h1>{e(g.h1)}</h1>
<p class="list-sub">{e(g.intro)}</p>
</div>
<div class="guide-wrap">
{body_list}
<section class="guide-method"><h2>Cómo se ha hecho esta lista</h2><p class="intro">{e(g.method)}</p></section>
<section class="guide-related"><h2>Más guías</h2><div class="chips">{related_html}</div></section>
</div>"""
    jsonld = {
        "@context": "https://schema.org", "@type": "ItemList", "name": g.h1, "url": url,
        "itemListElement": [
            {"@type": "ListItem", "position": i + 1, "url": f"{base_url}/estacion/{it.station['slug']}/",
             "name": (f"{it.title} ({it.station['name']})" if it.title else it.station["name"])}
            for i, it in enumerate(g.items)],
    }
    first = g.items[0].station["slug"] if g.items else None
    return page(title=f"{g.title} | Ski Info", description=g.intro[:300], url=url, body=body, jsonld=jsonld,
                image=f"/og/{first}.jpg" if first else "/og/ski-info.jpg", base_url=base_url)


def index_page(guides: list[Guide], page, e, base_url: str) -> str:
    groups: dict[str, list[Guide]] = {}
    for g in guides:
        groups.setdefault(g.group, []).append(g)
    order = ["Nieve", "Estaciones", "Pistas", "Cerca de tu ciudad"]
    sections = ""
    for name in sorted(groups, key=lambda n: order.index(n) if n in order else 99):
        cards = "".join(
            f'<a class="guide-card" href="/guias/{g.slug}/">'
            + (f'<img src="/og/thumb/{g.items[0].station["slug"]}.jpg" alt="" width="72" height="77" loading="lazy">' if g.items else "")
            + f'<span><span class="guide-card-title">{e(g.h1)}</span>'
            + (f'<span class="guide-card-sub">N.º 1: {e(g.items[0].title or g.items[0].station["name"])}</span>' if g.items else "")
            + '</span></a>' for g in groups[name])
        sections += f'<section class="guide-group"><h2>{e(name)}</h2><div class="guide-cards">{cards}</div></section>'
    body = f"""<div class="guide-head">
<div class="eyebrow"><a href="/">Ski Info</a> · Guías</div>
<h1>Guías y rankings de esquí</h1>
<p class="list-sub">Las estaciones más grandes, las más altas y las mejores para principiantes, las pistas más empinadas y más largas, las estaciones más cerca de tu ciudad y dónde va a nevar esta semana. Todo calculado con los datos de más de 1.200 estaciones.</p>
</div>
<div class="guide-wrap">{sections}</div>"""
    return page(title="Guías y rankings de estaciones de esquí | Ski Info",
                description="Rankings de estaciones de esquí: las más grandes, las más altas, las mejores para principiantes, "
                            "las pistas más empinadas y largas, estaciones cerca de tu ciudad y dónde nieva esta semana.",
                url=f"{base_url}/guias/", body=body, base_url=base_url)


def station_ranks(guides: list[Guide], top: int = 10) -> dict[str, list[tuple[str, str]]]:
    """station id -> [(chip text, guide url)] for the station pages' "En los rankings" block."""
    out: dict[str, list[tuple[str, str]]] = {}
    for g in guides:
        if not g.rank_label or g.kind == "snow":
            continue
        seen = set()
        for i, it in enumerate(g.items[:top]):
            sid = it.station["id"]
            if sid in seen:
                continue
            seen.add(sid)
            what = g.rank_label[0].lower() + g.rank_label[1:]  # keep "España", "Alpes"... capitalised
            label = f"{it.title}: {i + 1}.ª en {what}" if it.title else f"{i + 1}.ª en {what}"
            out.setdefault(sid, []).append((label, f"/guias/{g.slug}/"))
    return out


def write_all(docs: Path, guides: list[Guide], page, e, base_url: str) -> list[str]:
    urls = [f"{base_url}/guias/"]
    (docs / "guias").mkdir(parents=True, exist_ok=True)
    (docs / "guias" / "index.html").write_text(index_page(guides, page, e, base_url), encoding="utf-8")
    for g in guides:
        out = docs / "guias" / g.slug / "index.html"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(guide_page(g, guides, page, e, base_url), encoding="utf-8")
        urls.append(f"{base_url}/guias/{g.slug}/")
    # Small index for the app's home page (docs/index.html).
    (docs / "guias.json").write_text(json.dumps(
        [{"slug": g.slug, "group": g.group, "title": g.h1,
          "top": (g.items[0].title or g.items[0].station["name"]) if g.items else None,
          "thumb": g.items[0].station["slug"] if g.items else None} for g in guides],
        ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    return urls
