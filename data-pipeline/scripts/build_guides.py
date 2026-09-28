"""Guides and rankings (/guias/... in Spanish, /en/guides/... in English) built
from the stations' own data.

Called by build_seo_pages.py: station_stats() is run on every station first,
then build_guides() works out each ranking for one language (and which
stations appear in which, so station pages can link back), and write_all()
renders the pages. Everything is derived from OpenStreetMap data, the same
numbers the app shows, so the pages stay correct as data is refreshed -- and
the snow guide changes with every daily deploy (snow.json).

Each guide has a language-independent `key` (e.g. "biggest:alps"); guides with
the same key in both languages are each other's translation (hreflang).
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


def in_pyrenees(s: dict) -> bool:
    return s["cc"] in {"ES", "AD", "FR"} and 42.0 <= s["lat"] <= 43.4 and -2.0 <= s["lon"] <= 3.3


def in_alps(s: dict) -> bool:
    return s["cc"] in ALPS_CC and 43.8 <= s["lat"] <= 48.2 and 5.0 <= s["lon"] <= 16.5


# zone -> (filter, {lang: phrase used in titles})
ZONES = {
    "iberia": (lambda s: s["cc"] in IBERIA, {"es": "de España y Andorra", "en": "in Spain & Andorra"}),
    "pyrenees": (in_pyrenees, {"es": "de los Pirineos", "en": "in the Pyrenees"}),
    "alps": (in_alps, {"es": "de los Alpes", "en": "in the Alps"}),
    "world": (lambda s: True, {"es": "del mundo", "en": "in the world"}),
    "north_america": (lambda s: s["cc"] in {"US", "CA"}, {"es": "de Norteamérica", "en": "in North America"}),
    "japan": (lambda s: s["cc"] == "JP", {"es": "de Japón", "en": "in Japan"}),
}

# What each language publishes: (slug, zone, list size[, min km]). Spanish slugs
# are live URLs already known to search engines: never change them.
SPECS = {
    "es": {
        "biggest": [("estaciones-mas-grandes-espana-andorra", "iberia", 20), ("estaciones-mas-grandes-pirineos", "pyrenees", 20),
                    ("estaciones-mas-grandes-alpes", "alps", 25), ("estaciones-mas-grandes-del-mundo", "world", 25)],
        "beginners": [("estaciones-para-principiantes-espana-andorra", "iberia", 15, 10),
                      ("estaciones-para-principiantes-alpes", "alps", 20, 40)],
        "highest": [("estaciones-mas-altas-espana-andorra", "iberia", 15), ("estaciones-mas-altas-alpes", "alps", 20)],
        "vertical": [("estaciones-con-mas-desnivel-espana-andorra", "iberia", 15)],
        "steep": [("pistas-mas-empinadas-espana-andorra", "iberia", 25), ("pistas-mas-empinadas-alpes", "alps", 25)],
        "long": [("pistas-mas-largas-espana-andorra", "iberia", 25), ("pistas-mas-largas-alpes", "alps", 25)],
        "snow": "donde-nieva-esta-semana",
    },
    "en": {
        "biggest": [("biggest-ski-resorts-in-the-world", "world", 25), ("biggest-ski-resorts-in-the-alps", "alps", 25),
                    ("biggest-ski-resorts-in-north-america", "north_america", 20), ("biggest-ski-resorts-in-japan", "japan", 15),
                    ("biggest-ski-resorts-in-the-pyrenees", "pyrenees", 20),
                    ("biggest-ski-resorts-in-spain-and-andorra", "iberia", 20)],
        "beginners": [("best-ski-resorts-for-beginners-in-the-alps", "alps", 20, 40),
                      ("best-ski-resorts-for-beginners-in-north-america", "north_america", 20, 30),
                      ("best-ski-resorts-for-beginners-in-spain-and-andorra", "iberia", 15, 10)],
        "highest": [("highest-ski-resorts-in-the-alps", "alps", 20), ("highest-ski-resorts-in-north-america", "north_america", 20)],
        "vertical": [("ski-resorts-with-the-most-vertical-in-the-alps", "alps", 20),
                     ("ski-resorts-with-the-most-vertical-in-north-america", "north_america", 20)],
        "steep": [("steepest-ski-runs-in-the-alps", "alps", 25), ("steepest-ski-runs-in-north-america", "north_america", 25),
                  ("steepest-ski-runs-in-spain-and-andorra", "iberia", 25)],
        "long": [("longest-ski-runs-in-the-alps", "alps", 25), ("longest-ski-runs-in-north-america", "north_america", 25)],
        "snow": "where-it-will-snow-this-week",
    },
}

# Cities for "near ..." guides: slug -> (name, lat, lon); the pool of resorts
# each language considers (Spanish readers drive to Spain, Andorra, France).
CITIES = {
    "es": {"madrid": ("Madrid", 40.4168, -3.7038), "barcelona": ("Barcelona", 41.3874, 2.1686),
           "valencia": ("Valencia", 39.4699, -0.3763), "bilbao": ("Bilbao", 43.2630, -2.9350),
           "zaragoza": ("Zaragoza", 41.6488, -0.8891), "sevilla": ("Sevilla", 37.3891, -5.9845),
           "malaga": ("Málaga", 36.7213, -4.4214), "pamplona": ("Pamplona", 42.8125, -1.6458)},
    "en": {"geneva": ("Geneva", 46.2044, 6.1432), "zurich": ("Zurich", 47.3769, 8.5417),
           "munich": ("Munich", 48.1351, 11.5820), "milan": ("Milan", 45.4642, 9.1900),
           "innsbruck": ("Innsbruck", 47.2692, 11.4041), "lyon": ("Lyon", 45.7640, 4.8357),
           "denver": ("Denver", 39.7392, -104.9903), "salt-lake-city": ("Salt Lake City", 40.7608, -111.8910),
           "vancouver": ("Vancouver", 49.2827, -123.1207), "tokyo": ("Tokyo", 35.6762, 139.6503)},
}
CITY_POOL = {"es": lambda s: s["cc"] in {"ES", "AD", "FR"}, "en": lambda s: True}

# Where each language's pages live.
PATHS = {
    "es": {"home": "/", "guides": "/guias/", "station": "/estacion/", "index_json": "guias.json"},
    "en": {"home": "/en/", "guides": "/en/guides/", "station": "/en/resort/", "index_json": "en/guides.json"},
}

GROUP_ORDER = {"es": ["Nieve", "Estaciones", "Pistas", "Cerca de tu ciudad"],
               "en": ["Snow", "Resorts", "Runs", "Near your city"]}


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
    station: dict                 # {"id", "name", "cc", "country", "region", "slug", ...stats}
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
    key: str = ""                 # same key in both languages = translations of each other
    items: list[Item] = field(default_factory=list)
    kind: str = "station"         # station | run | snow
    rank_label: str = ""          # for the station pages' "In the rankings" chips
    empty_text: str = ""
    updated: str = ""             # ISO date of the data behind it (snow guide)


def build_guides(stations: list[dict], snow: dict, snow_date: str, fmt, diff_labels: dict,
                 snow_updated: str = "", lang: str = "es") -> list[Guide]:
    """stations: dicts with id, name (display), cc, country (in `lang`), region,
    slug, lat, lon + station_stats(). fmt formats numbers for `lang`."""
    es = lang == "es"
    spec = SPECS[lang]
    real = [s for s in stations if s["km"] >= 3]
    guides: list[Guide] = []

    def place(s):
        return ", ".join(p for p in [s.get("region"), s["country"]] if p)

    def station_meta(s):
        runs_w, lifts_w = ("pistas", "remontes") if es else ("runs", "lifts")
        bits = [f"{s['n_runs']} {runs_w}" if s["n_runs"] else None, f"{s['n_lifts']} {lifts_w}" if s["n_lifts"] else None]
        if s["lo"] is not None and s["hi"] is not None:
            bits.append(f"{fmt(round(s['lo']))}–{fmt(round(s['hi']))} m")
        return " · ".join(b for b in bits if b)

    km_pistes = "km de pistas" if es else "km of pistes"

    # ---- biggest ----
    for slug, zone, n in spec["biggest"]:
        pick, phrases = ZONES[zone]
        zone_txt = phrases[lang]
        lst = sorted((s for s in real if pick(s)), key=lambda s: -s["km"])[:n]
        if not lst:
            continue
        top = lst[0]
        if es:
            intro = (f"Las {len(lst)} estaciones de esquí con más kilómetros de pistas {zone_txt}. "
                     f"La más grande es {top['name']} ({place(top)}), con {fmt(round(top['km']))} km de pistas"
                     + (f", seguida de {lst[1]['name']} ({fmt(round(lst[1]['km']))} km)" if len(lst) > 1 else "")
                     + (f" y {lst[2]['name']} ({fmt(round(lst[2]['km']))} km)." if len(lst) > 2 else ".")
                     + " Pulsa cualquiera para ver su mapa de pistas, el perfil de cada pista y la previsión de nieve.")
            title = f"Las estaciones de esquí más grandes {zone_txt}"
            method = ("Ordenadas por la suma de la longitud de todas sus pistas de esquí alpino según OpenStreetMap "
                      "(no se cuentan los circuitos de fondo). Las cifras oficiales de cada estación pueden variar algo "
                      "porque cada una mide sus pistas a su manera.")
            rank = f"Estaciones más grandes {zone_txt}"
        else:
            intro = (f"The {len(lst)} ski resorts {zone_txt} with the most kilometres of pistes. "
                     f"The biggest is {top['name']} ({place(top)}), with {fmt(round(top['km']))} km of pistes"
                     + (f", followed by {lst[1]['name']} ({fmt(round(lst[1]['km']))} km)" if len(lst) > 1 else "")
                     + (f" and {lst[2]['name']} ({fmt(round(lst[2]['km']))} km)." if len(lst) > 2 else ".")
                     + " Tap any of them for its piste map, the gradient profile of every run and the snow forecast.")
            title = f"The biggest ski resorts {zone_txt}"
            method = ("Ranked by the total length of their alpine runs in OpenStreetMap (cross-country trails don't count). "
                      "Official figures may differ a little, as every resort measures its runs its own way.")
            rank = f"the biggest ski resorts {zone_txt}"
        guides.append(Guide(slug=slug, key=f"biggest:{zone}", group="Estaciones" if es else "Resorts", kind="station",
                            title=title, h1=title, intro=intro, method=method, rank_label=rank,
                            items=[Item(s, f"{fmt(round(s['km']))} km", "de pistas" if es else "of pistes", station_meta(s))
                                   for s in lst]))

    # ---- beginners ----
    for slug, zone, n, min_km in spec["beginners"]:
        pick, phrases = ZONES[zone]
        zone_txt = phrases[lang]
        lst = [s for s in real if pick(s) and s["km"] >= min_km and s["easy_km"] > 0]
        lst.sort(key=lambda s: (-s["easy_km"] / s["km"], -s["km"]))
        lst = lst[:n]
        if not lst:
            continue
        top = lst[0]
        pct = lambda s: fmt(round(100 * s["easy_km"] / s["km"]))
        if es:
            intro = (f"Las estaciones {zone_txt} donde más proporción de pistas son verdes y azules: ideales para aprender "
                     f"o para esquiar tranquilo. Encabeza la lista {top['name']}, con un {pct(top)} % "
                     f"de sus {fmt(round(top['km']))} km en pistas fáciles. Solo entran estaciones de al menos {min_km} km, "
                     "para que haya terreno suficiente para progresar.")
            title = f"Mejores estaciones de esquí para principiantes {zone_txt}"
            h1 = f"Las mejores estaciones para principiantes {zone_txt}"
            method = ("Porcentaje de kilómetros de pistas verdes y azules sobre el total de pistas de esquí alpino, "
                      f"entre las estaciones con al menos {min_km} km. Datos de dificultad de OpenStreetMap.")
            rank = f"Mejores para principiantes {zone_txt}"
            items = [Item(s, f"{pct(s)} %", "pistas fáciles",
                          f"{fmt(round(s['easy_km']))} de {fmt(round(s['km']))} km verdes o azules · {station_meta(s)}") for s in lst]
        else:
            intro = (f"The resorts {zone_txt} where the largest share of the pistes are green and blue: ideal for learning "
                     f"or for relaxed skiing. Top of the list is {top['name']}, with {pct(top)}% of its "
                     f"{fmt(round(top['km']))} km on easy runs. Only resorts with at least {min_km} km are included, "
                     "so there's enough terrain to progress.")
            title = f"Best ski resorts for beginners {zone_txt}"
            h1 = f"The best ski resorts for beginners {zone_txt}"
            method = ("Share of green and blue kilometres over all alpine pistes, among resorts with at least "
                      f"{min_km} km. Difficulty data from OpenStreetMap.")
            rank = f"the best resorts for beginners {zone_txt}"
            items = [Item(s, f"{pct(s)}%", "easy runs",
                          f"{fmt(round(s['easy_km']))} of {fmt(round(s['km']))} km green or blue · {station_meta(s)}") for s in lst]
        guides.append(Guide(slug=slug, key=f"beginners:{zone}", group="Estaciones" if es else "Resorts", kind="station",
                            title=title, h1=h1, intro=intro, method=method, rank_label=rank, items=items))

    # ---- highest / biggest vertical ----
    for kind in ("highest", "vertical"):
        for slug, zone, n in spec[kind]:
            pick, phrases = ZONES[zone]
            zone_txt = phrases[lang]
            pool = [s for s in real if pick(s) and s["hi"] is not None and s["lo"] is not None]
            val = (lambda s: s["hi"]) if kind == "highest" else (lambda s: s["hi"] - s["lo"])
            lst = sorted(pool, key=lambda s: -val(s))[:n]
            if not lst:
                continue
            top = lst[0]
            if kind == "highest" and es:
                title = f"Las estaciones de esquí más altas {zone_txt}"
                intro = (f"Las estaciones {zone_txt} que llegan más alto. Más altitud suele significar nieve de más calidad "
                         f"y temporadas más largas. La más alta es {top['name']}, que alcanza los {fmt(round(top['hi']))} m.")
                method = "Cota más alta a la que llega una pista o un remonte de la estación, según OpenStreetMap y el modelo de elevación."
                rank = f"Estaciones más altas {zone_txt}"
                items = [Item(s, f"{fmt(round(s['hi']))} m", "cota máxima", f"desde {fmt(round(s['lo']))} m · {fmt(round(s['km']))} {km_pistes}") for s in lst]
            elif kind == "highest":
                title = f"The highest ski resorts {zone_txt}"
                intro = (f"The resorts {zone_txt} that reach highest. More altitude usually means better snow and longer "
                         f"seasons. The highest is {top['name']}, topping out at {fmt(round(top['hi']))} m.")
                method = "Highest point reached by a run or lift of the resort, from OpenStreetMap and the elevation model."
                rank = f"the highest ski resorts {zone_txt}"
                items = [Item(s, f"{fmt(round(s['hi']))} m", "top elevation", f"from {fmt(round(s['lo']))} m · {fmt(round(s['km']))} {km_pistes}") for s in lst]
            elif es:
                title = f"Las estaciones de esquí con más desnivel {zone_txt}"
                intro = (f"Las estaciones {zone_txt} con más metros de desnivel entre su punto más bajo y el más alto: "
                         f"las bajadas más largas del día. Lidera {top['name']}, con {fmt(round(val(top)))} m de desnivel.")
                method = "Diferencia entre la cota más alta y la más baja de las pistas y remontes de la estación."
                rank = f"Estaciones con más desnivel {zone_txt}"
                items = [Item(s, f"{fmt(round(val(s)))} m", "de desnivel", f"{fmt(round(s['lo']))}–{fmt(round(s['hi']))} m · {fmt(round(s['km']))} {km_pistes}") for s in lst]
            else:
                title = f"Ski resorts with the most vertical {zone_txt}"
                intro = (f"The resorts {zone_txt} with the biggest vertical drop between their lowest and highest points: "
                         f"the longest descents of the day. {top['name']} leads with {fmt(round(val(top)))} m of vertical.")
                method = "Difference between the highest and lowest points of the resort's runs and lifts."
                rank = f"the resorts with the most vertical {zone_txt}"
                items = [Item(s, f"{fmt(round(val(s)))} m", "vertical", f"{fmt(round(s['lo']))}–{fmt(round(s['hi']))} m · {fmt(round(s['km']))} {km_pistes}") for s in lst]
            guides.append(Guide(slug=slug, key=f"{kind}:{zone}", group="Estaciones" if es else "Resorts", kind="station",
                                title=title, h1=title, intro=intro, method=method, rank_label=rank, items=items))

    # ---- runs: steepest / longest ----
    for kind in ("steep", "long"):
        for slug, zone, n in spec[kind]:
            pick, phrases = ZONES[zone]
            zone_txt = phrases[lang]
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
            rows.sort(key=(lambda x: -x[2]) if kind == "steep" else (lambda x: -x[1]["len"]))
            rows = rows[:n]
            if not rows:
                continue
            s0, r0, p0 = rows[0]
            dl = lambda r: diff_labels.get(r["diff"], "")
            if kind == "steep" and es:
                title = f"Las pistas de esquí más empinadas {zone_txt}"
                intro = (f"Las {len(rows)} pistas con más pendiente media {zone_txt}, medida de arriba abajo con el modelo de elevación. "
                         f"La más empinada es {r0['name']}, en {s0['name']}, con un {fmt(round(p0))} % de pendiente media "
                         f"en {fmt(round(r0['len']))} m. En la ficha de cada estación puedes ver el perfil de la pista tramo a tramo.")
                method = ("Pendiente media = desnivel total ÷ longitud de la pista (en %), para pistas oficiales (verde a negra) "
                          "de al menos 300 m. En los tramos más duros la inclinación puntual es mayor que la media.")
                items = [Item(s, f"{fmt(round(p))} %", "pend. media",
                              f"{fmt(round(r['len']))} m · desnivel {fmt(round(r['vert']))} m · {dl(r)}",
                              title=r["name"], diff=r["diff"]) for s, r, p in rows]
                rank = f"Pistas más empinadas {zone_txt}"
            elif kind == "steep":
                title = f"The steepest ski runs {zone_txt}"
                intro = (f"The {len(rows)} runs {zone_txt} with the highest average gradient, measured top to bottom with the elevation model. "
                         f"The steepest is {r0['name']} at {s0['name']}, averaging {fmt(round(p0))}% over "
                         f"{fmt(round(r0['len']))} m. Each resort's page shows the profile of every run, section by section.")
                method = ("Average gradient = total vertical ÷ run length (as %), for graded runs (green to black) of at least "
                          "300 m. On the hardest pitches the local gradient is steeper than the average.")
                items = [Item(s, f"{fmt(round(p))}%", "avg. gradient",
                              f"{fmt(round(r['len']))} m · {fmt(round(r['vert']))} m vertical · {dl(r)}",
                              title=r["name"], diff=r["diff"]) for s, r, p in rows]
                rank = f"the steepest runs {zone_txt}"
            elif es:
                title = f"Las pistas de esquí más largas {zone_txt}"
                intro = (f"Las {len(rows)} pistas más largas {zone_txt}. La primera es {r0['name']}, en {s0['name']}, "
                         f"con {fmt(r0['len'] / 1000, 1)} km de bajada y {fmt(round(r0['vert']))} m de desnivel.")
                method = ("Longitud total de cada pista con nombre (sumando sus tramos) según OpenStreetMap, para pistas oficiales "
                          "de verde a negra.")
                items = [Item(s, f"{fmt(r['len'] / 1000, 1)} km", "de bajada",
                              f"desnivel {fmt(round(r['vert']))} m · pend. media {fmt(round(p))} % · {dl(r)}",
                              title=r["name"], diff=r["diff"]) for s, r, p in rows]
                rank = f"Pistas más largas {zone_txt}"
            else:
                title = f"The longest ski runs {zone_txt}"
                intro = (f"The {len(rows)} longest runs {zone_txt}. First is {r0['name']} at {s0['name']}, "
                         f"a {fmt(r0['len'] / 1000, 1)} km descent with {fmt(round(r0['vert']))} m of vertical.")
                method = "Total length of each named run (adding up its sections) in OpenStreetMap, for graded runs from green to black."
                items = [Item(s, f"{fmt(r['len'] / 1000, 1)} km", "long",
                              f"{fmt(round(r['vert']))} m vertical · avg. gradient {fmt(round(p))}% · {dl(r)}",
                              title=r["name"], diff=r["diff"]) for s, r, p in rows]
                rank = f"the longest runs {zone_txt}"
            guides.append(Guide(slug=slug, key=f"{kind}:{zone}", group="Pistas" if es else "Runs", kind="run",
                                title=title, h1=title, intro=intro, method=method, rank_label=rank, items=items))

    # ---- near a city ----
    near_pool = [s for s in real if CITY_POOL[lang](s)]
    for cslug, (cname, clat, clon) in CITIES[lang].items():
        rows = sorted(((haversine_km(clat, clon, s["lat"], s["lon"]), s) for s in near_pool), key=lambda x: x[0])
        rows = [(d, s) for d, s in rows if d <= 450][:12]
        if not rows:
            continue
        d0, s0 = rows[0]
        within = sum(1 for d, _ in rows if d <= 250)
        if es:
            intro = (f"Las estaciones de esquí más cercanas a {cname}, de la más próxima a la más lejana. "
                     f"La más cercana es {s0['name']}, a unos {fmt(round(d0))} km en línea recta"
                     f"; a menos de 250 km tienes {within} estaciones."
                     " Pulsa «Cómo llegar» en la ficha de cada una para ver la ruta en coche.")
            guides.append(Guide(
                slug=f"estaciones-de-esqui-cerca-de-{cslug}", key=f"near:{cslug}", group="Cerca de tu ciudad", kind="station",
                title=f"Estaciones de esquí cerca de {cname}", h1=f"Estaciones de esquí cerca de {cname}", intro=intro,
                method="Distancia en línea recta desde el centro de la ciudad hasta la estación; por carretera siempre es más. "
                       "Incluye estaciones de España, Andorra y Francia con al menos 3 km de pistas.",
                rank_label=f"Estaciones cerca de {cname}",
                items=[Item(s, f"{fmt(round(d))} km", "en línea recta", f"{fmt(round(s['km']))} km de pistas · {station_meta(s)}")
                       for d, s in rows]))
        else:
            intro = (f"The ski resorts closest to {cname}, from nearest to farthest. The nearest is {s0['name']}, "
                     f"about {fmt(round(d0))} km away as the crow flies; {within} resorts are within 250 km."
                     " Tap “Directions” on any resort's page for the driving route.")
            guides.append(Guide(
                slug=f"ski-resorts-near-{cslug}", key=f"near:{cslug}", group="Near your city", kind="station",
                title=f"Ski resorts near {cname}", h1=f"Ski resorts near {cname}", intro=intro,
                method="Straight-line distance from the city centre to the resort; by road it is always further. "
                       "Resorts with at least 3 km of pistes.",
                rank_label=f"the ski resorts near {cname}",
                items=[Item(s, f"{fmt(round(d))} km", "as the crow flies", f"{fmt(round(s['km']))} km of pistes · {station_meta(s)}")
                       for d, s in rows]))

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
    if es:
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
            slug=spec["snow"], key="snow", group="Nieve", kind="snow", updated=snow_updated[:10],
            title="Dónde va a nevar esta semana: previsión de nieve en las estaciones",
            h1="Dónde va a nevar esta semana", intro=intro,
            method="Suma de la nieve prevista para los próximos 7 días por los modelos meteorológicos (Open-Meteo) en la cota "
                   "más alta de cada estación. Es una previsión, no el parte oficial de nieve de la estación.",
            items=[Item(s, f"{fmt(round(t))} cm", "en 7 días", station_meta(s), spark=sf) for t, s, sf in world]))
    else:
        when = f" (forecast of {snow_date})" if snow_date else ""
        if world:
            t0, s0, _ = world[0]
            intro = (f"The ski resorts expecting the most snow over the next 7 days{when}, at their highest point. "
                     f"Top of the list is {s0['name']} ({place(s0)}), with around {fmt(round(t0))} cm forecast. "
                     "Updated every day; each resort's page has the day-by-day forecast.")
        else:
            intro = (f"No resort is expecting significant snowfall over the next 7 days{when}. "
                     "This page is updated every day with the snow forecast for over 1,200 resorts.")
        guides.append(Guide(
            slug=spec["snow"], key="snow", group="Snow", kind="snow", updated=snow_updated[:10],
            title="Where it will snow this week: ski resort snow forecast",
            h1="Where it will snow this week", intro=intro,
            method="Total snowfall forecast for the next 7 days by weather models (Open-Meteo) at each resort's highest "
                   "point. It's a forecast, not the resort's official snow report.",
            items=[Item(s, f"{fmt(round(t))} cm", "in 7 days", station_meta(s), spark=sf) for t, s, sf in world]))
    return guides


# ---------- rendering ----------

TEXTS = {
    "es": {"guides": "Guías", "method": "Cómo se ha hecho esta lista", "more": "Más guías", "no1": "N.º 1: {0}",
           "empty": "Ahora mismo no hay estaciones en esta lista.",
           "stale": "Atención: esta previsión es del {0} y puede estar desactualizada. En la ficha de cada estación tienes la previsión en directo.",
           "index_h1": "Guías y rankings de esquí",
           "index_sub": "Las estaciones más grandes, las más altas y las mejores para principiantes, las pistas más empinadas y más largas, "
                        "las estaciones más cerca de tu ciudad y dónde va a nevar esta semana. Todo calculado con los datos de más de 1.200 estaciones.",
           "index_title": "Guías y rankings de estaciones de esquí | Ski Info",
           "index_desc": "Rankings de estaciones de esquí: las más grandes, las más altas, las mejores para principiantes, "
                         "las pistas más empinadas y largas, estaciones cerca de tu ciudad y dónde nieva esta semana."},
    "en": {"guides": "Guides", "method": "How this list was made", "more": "More guides", "no1": "No. 1: {0}",
           "empty": "There are no resorts in this list right now.",
           "stale": "Note: this forecast is from {0} and may be out of date. Each resort's page has the live forecast.",
           "index_h1": "Ski guides & rankings",
           "index_sub": "The biggest and highest resorts, the best for beginners, the steepest and longest runs, the resorts near your "
                        "city and where it will snow this week. All worked out from the data of over 1,200 ski resorts.",
           "index_title": "Ski resort guides & rankings | Ski Info",
           "index_desc": "Ski resort rankings: the biggest, the highest, the best for beginners, the steepest and longest runs, "
                         "resorts near your city and where it will snow this week."},
}


def item_html(it: Item, pos: int, e, lang: str) -> str:
    s = it.station
    href = f"{PATHS[lang]['station']}{s['slug']}/"
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


def guide_url(base_url: str, lang: str, slug: str | None = None) -> str:
    return f"{base_url}{PATHS[lang]['guides']}" + (f"{slug}/" if slug else "")


def guide_page(g: Guide, guides: list[Guide], page, e, base_url: str, lang: str, alternates: dict) -> str:
    tx = TEXTS[lang]
    gpath = PATHS[lang]["guides"]
    url = guide_url(base_url, lang, g.slug)
    items = "".join(item_html(it, i + 1, e, lang) for i, it in enumerate(g.items))
    stale = ""
    if g.updated:
        # The forecast is refreshed by the daily deploy; if that ever stops,
        # say how old it is instead of passing it off as this week's.
        locale = "es-ES" if lang == "es" else "en-GB"
        msg = json.dumps(tx["stale"], ensure_ascii=False)
        stale = (f'<p class="guide-stale" id="guide-stale" data-updated="{g.updated}" hidden></p>'
                 '<script>(function(){var el=document.getElementById("guide-stale"),d=el.getAttribute("data-updated");'
                 'var days=Math.floor((Date.now()-Date.parse(d+"T12:00:00Z"))/864e5);if(days>=2){el.textContent='
                 f'{msg}.replace("{{0}}",new Date(d+"T12:00:00Z").toLocaleDateString("{locale}",{{day:"numeric",month:"long"}}));'
                 'el.hidden=false;}})();</script>')
    body_list = stale + (f'<ol class="guide-list">{items}</ol>' if g.items
                         else f'<p class="intro guide-empty">{e(g.empty_text or tx["empty"])}</p>')
    related = [x for x in guides if x.slug != g.slug and x.group == g.group][:6]
    related += [x for x in guides if x.slug != g.slug and x.group != g.group and x not in related][: max(0, 8 - len(related))]
    related_html = "".join(f'<a class="chip" href="{gpath}{x.slug}/">{e(x.h1)}</a>' for x in related)
    body = f"""<div class="guide-head">
<div class="eyebrow"><a href="{PATHS[lang]['home']}">Ski Info</a> · <a href="{gpath}">{tx['guides']}</a> · {e(g.group)}</div>
<h1>{e(g.h1)}</h1>
<p class="list-sub">{e(g.intro)}</p>
</div>
<div class="guide-wrap">
{body_list}
<section class="guide-method"><h2>{tx['method']}</h2><p class="intro">{e(g.method)}</p></section>
<section class="guide-related"><h2>{tx['more']}</h2><div class="chips">{related_html}</div></section>
</div>"""
    jsonld = {
        "@context": "https://schema.org", "@type": "ItemList", "name": g.h1, "url": url, "inLanguage": lang,
        "itemListElement": [
            {"@type": "ListItem", "position": i + 1, "url": f"{base_url}{PATHS[lang]['station']}{it.station['slug']}/",
             "name": (f"{it.title} ({it.station['name']})" if it.title else it.station["name"])}
            for i, it in enumerate(g.items)],
    }
    first = g.items[0].station["slug"] if g.items else None
    og_dir = "/og/" if lang == "es" else "/og/en/"
    return page(title=f"{g.title} | Ski Info", description=g.intro[:300], url=url, body=body, jsonld=jsonld,
                image=f"{og_dir}{first}.jpg" if first else f"{og_dir}ski-info.jpg", base_url=base_url,
                lang=lang, alternates=alternates)


def index_page(guides: list[Guide], page, e, base_url: str, lang: str, alternates: dict) -> str:
    tx = TEXTS[lang]
    gpath = PATHS[lang]["guides"]
    groups: dict[str, list[Guide]] = {}
    for g in guides:
        groups.setdefault(g.group, []).append(g)
    order = GROUP_ORDER[lang]
    sections = ""
    for name in sorted(groups, key=lambda n: order.index(n) if n in order else 99):
        cards = "".join(
            f'<a class="guide-card" href="{gpath}{g.slug}/">'
            + (f'<img src="/og/thumb/{g.items[0].station["slug"]}.jpg" alt="" width="72" height="77" loading="lazy">' if g.items else "")
            + f'<span><span class="guide-card-title">{e(g.h1)}</span>'
            + (f'<span class="guide-card-sub">{e(tx["no1"].format(g.items[0].title or g.items[0].station["name"]))}</span>' if g.items else "")
            + '</span></a>' for g in groups[name])
        sections += f'<section class="guide-group"><h2>{e(name)}</h2><div class="guide-cards">{cards}</div></section>'
    body = f"""<div class="guide-head">
<div class="eyebrow"><a href="{PATHS[lang]['home']}">Ski Info</a> · {tx['guides']}</div>
<h1>{tx['index_h1']}</h1>
<p class="list-sub">{tx['index_sub']}</p>
</div>
<div class="guide-wrap">{sections}</div>"""
    return page(title=tx["index_title"], description=tx["index_desc"], url=guide_url(base_url, lang), body=body,
                base_url=base_url, lang=lang, alternates=alternates,
                image="/og/ski-info.jpg" if lang == "es" else "/og/en/ski-info.jpg")


def station_ranks(guides: list[Guide], lang: str = "es", top: int = 10) -> dict[str, list[tuple[str, str]]]:
    """station id -> [(chip text, guide url)] for the station pages' rankings block."""
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
            if lang == "es":
                what = g.rank_label[0].lower() + g.rank_label[1:]  # keep "España", "Alpes"... capitalised
                label = f"{it.title}: {i + 1}.ª en {what}" if it.title else f"{i + 1}.ª en {what}"
            else:
                label = f"{it.title}: #{i + 1} of {g.rank_label}" if it.title else f"#{i + 1} of {g.rank_label}"
            out.setdefault(sid, []).append((label, f"{PATHS[lang]['guides']}{g.slug}/"))
    return out


def write_all(docs: Path, guides: list[Guide], page, e, base_url: str, lang: str = "es",
              alternates_for=lambda key: {}) -> list[tuple[str, dict]]:
    """Writes the index and every guide; returns [(url, alternates)] for the sitemap.
    alternates_for(key) gives {lang: url} of a guide's translations ("index" for the index)."""
    root = docs / PATHS[lang]["guides"].strip("/")
    root.mkdir(parents=True, exist_ok=True)
    idx_alt = alternates_for("index")
    (root / "index.html").write_text(index_page(guides, page, e, base_url, lang, idx_alt), encoding="utf-8")
    out = [(guide_url(base_url, lang), idx_alt)]
    for g in guides:
        alt = alternates_for(g.key)
        path = root / g.slug / "index.html"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(guide_page(g, guides, page, e, base_url, lang, alt), encoding="utf-8")
        out.append((guide_url(base_url, lang, g.slug), alt))
    # Small index for the app's home page.
    json_path = docs / PATHS[lang]["index_json"]
    json_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(
        [{"slug": g.slug, "key": g.key, "group": g.group, "title": g.h1,
          "top": (g.items[0].title or g.items[0].station["name"]) if g.items else None,
          "thumb": g.items[0].station["slug"] if g.items else None} for g in guides],
        ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    return out
