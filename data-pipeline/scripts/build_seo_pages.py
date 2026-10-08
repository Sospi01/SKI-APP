"""Generate static, crawlable pages for search engines from the app's data.

The web app (docs/index.html) renders every station client-side from one URL,
so search engines only ever see a single page. This script writes, in each of
the site's languages (LOC: Spanish, English, French, German, Italian), one plain
HTML page per station (/estacion/<slug>/, /en/resort/<slug>/...), one per
country, the country indexes, the guides (build_guides.py), the /app page, the
app's own copy in every language but Spanish (/en/, /fr/..., see
build_localized_app) and sitemap.xml with hreflang alternates. The app's
dictionaries are docs/i18n/<lang>.js; page text is in TX here and page_texts.py. Station pages carry the same content
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

from build_guides import shown_difficulty
from guide_texts import PATHS as GUIDE_PATHS
from page_texts import APP_HEAD as MORE_APP_HEAD, APP_TX as MORE_APP_TX, DATE_FMT, MONTHS, TX as MORE_TX

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
FAV_ICON = ('<svg viewBox="0 0 20 20" aria-hidden="true"><path d="M10 2.6l2.2 4.6 5 .7-3.6 3.5.9 5-4.5-2.4-4.5 2.4.9-5L2.8 7.9l5-.7z" '
            'fill="none" stroke="currentColor" stroke-width="1.6" stroke-linejoin="round"/></svg>')
SHARE_ICON = ('<svg viewBox="0 0 20 20" aria-hidden="true"><circle cx="14.5" cy="4.5" r="2.3" fill="none" stroke="currentColor" stroke-width="1.6"/>'
              '<circle cx="5.5" cy="10" r="2.3" fill="none" stroke="currentColor" stroke-width="1.6"/><circle cx="14.5" cy="15.5" r="2.3" fill="none" stroke="currentColor" stroke-width="1.6"/>'
              '<path d="M7.5 8.9l5-3.2M7.5 11.1l5 3.2" stroke="currentColor" stroke-width="1.6"/></svg>')
MAP_ICON = ('<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M3.5 6.5l5.5-2.5 6 2.5 5.5-2.5v13.5l-5.5 2.5-6-2.5-5.5 2.5z" '
            'fill="none" stroke="currentColor" stroke-width="1.8" stroke-linejoin="round"/>'
            '<line x1="9" y1="4" x2="9" y2="17.5" stroke="currentColor" stroke-width="1.6"/>'
            '<line x1="15" y1="6.5" x2="15" y2="20" stroke="currentColor" stroke-width="1.6"/></svg>')

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


# Shown names only (slugs keep strip_generic): more generic words to drop.
DISPLAY_PREFIX = re.compile(
    r"^(domaine skiable|area sciistica|ski ?area|station touristique|skipisten|stacja narciarska"
    r"|o[sś]rodek narciarski|skiare[aá]l|gletscher-skigebiet|ski cent(ar|er|re)|ski resort)( (de|di|du|del))?\s+",
    re.IGNORECASE,
)
# Not "mountain resort" as strip_generic: "Red Mountain Resort" -> "Red Mountain", not "Red".
DISPLAY_SUFFIX = re.compile(r"\s+(alpine resort|ski resort|ski area|ski centre|ski center|skiarea|ski bowl|skigebiet"
                            r"|ski ?arena|resort)$", re.IGNORECASE)
NAMES_JS = Path(__file__).resolve().parents[2] / "docs" / "station-names.js"
NAME_OVERRIDES = json.loads(re.search(r"var STATION_NAMES = (\{.*?\});", re.sub(
    r"^\s*//.*$", "", NAMES_JS.read_text(encoding="utf-8"), flags=re.M), re.S).group(1))


def display_name(name: str, sid: str | None = None) -> str:
    """The name to show: docs/station-names.js if listed, else OSM's first
    Latin-script form ("ニセコユナイテッド, Niseko United" -> "Niseko United")
    without the generic words ("Estació d'Esquí Baqueira-Beret" -> "Baqueira-Beret",
    "Big Sky Resort" -> "Big Sky"). Mirrors displayName() in docs/index.html."""
    if sid and sid in NAME_OVERRIDES:
        return NAME_OVERRIDES[sid]
    if not name:
        return name
    base = latin_name(name, keep_parens=True) or name
    text = DISPLAY_PREFIX.sub("", GENERIC_PREFIX.sub("", base))
    prev = None
    while prev != text:
        prev, text = text, DISPLAY_SUFFIX.sub("", text)
    return text.strip().strip('"“”«»').strip() or base


def feature_name(name: str | None) -> str | None:
    """A run's or lift's name as shown: OSM's "Rabadá BIS;Rabadá baby" (two
    names in one tag) -> "Rabadá BIS / Rabadá baby". Mirrors featureName() in index.html."""
    return " / ".join(p.strip() for p in name.split(";") if p.strip()) if name else name


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


def fmt_en(n: float, d: int = 0) -> str:
    """English number format (en-GB): thousands comma, decimal point."""
    return f"{n:,.{d}f}"


def fmt_de(n: float, d: int = 0) -> str:
    """German and Italian format: "." thousands from 1.000 up, decimal comma."""
    return f"{n:,.{d}f}".replace(",", "\0").replace(".", ",").replace("\0", ".")


def fmt_fr(n: float, d: int = 0) -> str:
    """French format: narrow no-break space for thousands, decimal comma."""
    return f"{n:,.{d}f}".replace(",", "\u202f").replace(".", ",")


def fmt_pl(n: float, d: int = 0) -> str:
    """Polish format like toLocaleString('pl-PL'): no-break space for thousands
    from 10 000 up, decimal comma."""
    s = f"{n:,.{d}f}" if abs(n) >= 10000 else f"{n:.{d}f}"
    return s.replace(",", "\u00a0").replace(".", ",")


FMT = {"es": fmt, "en": fmt_en, "fr": fmt_fr, "de": fmt_de, "it": fmt_de, "nl": fmt_de, "pl": fmt_pl}


def haversine_km(a: tuple, b: tuple) -> float:
    lat1, lon1, lat2, lon2 = map(math.radians, (a[0], a[1], b[0], b[1]))
    h = math.sin((lat2 - lat1) / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin((lon2 - lon1) / 2) ** 2
    return 2 * 6371 * math.asin(math.sqrt(h))


SLOPE_WINDOW_M = 30     # as profile.js
MAX_REAL_PITCH = 90     # a stretch steeper than this is a data error
STEEPEST_M = 50         # the "máx.": steepest stretch at least this long (as profile.js)


def smoothed_elevations(prof: list) -> list:
    """Mirrors smoothProfile() in docs/profile.js: [(dist, ele)] -> one
    smoothed elevation per point (resampled every 10 m, median of 5 against
    spikes, averaged over SLOPE_WINDOW_M)."""
    n, total = len(prof), prof[-1][0]
    if n < 2 or total <= 0:
        return [e for _, e in prof]
    step, grid, k, d = 10, [], 0, 0.0
    while d <= total + 1e-6:
        while k < n - 2 and prof[k + 1][0] < d:
            k += 1
        (da, ea), (db, eb) = prof[k], prof[k + 1]
        span = db - da
        grid.append(ea + (eb - ea) * min(1, max(0, (d - da) / span)) if span > 0 else ea)
        d += step
    med = [sorted(grid[max(0, i - 2):i + 3])[len(grid[max(0, i - 2):i + 3]) // 2] for i in range(len(grid))]
    csum = [0.0]
    for v in med:
        csum.append(csum[-1] + v)
    half = max(1, round(SLOPE_WINDOW_M / 2 / step))
    out = []
    for dist, _ in prof:
        c = min(len(med) - 1, int(dist / step + 0.5))   # as Math.round
        lo, hi = max(0, c - half), min(len(med) - 1, c + half)
        out.append((csum[hi + 1] - csum[lo]) / (hi - lo + 1))
    return out


def split_out_and_back(pts: list):
    """A run drawn as one loop (down one lane, back up the other, or the
    other way round): its two halves. Mirrors splitOutAndBack() in profile.js."""
    if len(pts) < 3 or abs(pts[0][2] - pts[-1][2]) > 10:
        return None
    for sign in (-1, 1):
        k = 0
        for i in range(1, len(pts)):
            if sign * (pts[i][2] - pts[k][2]) > 0:
                k = i
        if k <= 0 or k >= len(pts) - 1:
            continue
        a, b = sign * (pts[k][2] - pts[0][2]), sign * (pts[k][2] - pts[-1][2])
        if a <= 0 or b <= 0 or min(a, b) < 15 or min(a, b) / max(a, b) < 0.4:
            continue
        return [pts[:k + 1], pts[k:][::-1]]
    return None


def run_max_pitch(parts) -> float | None:
    """A run's steepest stretch of at least STEEPEST_M, in % (None without elevation).
    Mirrors runMaxPitch() in docs/profile.js: distance along each segment,
    elevation smoothed (smoothed_elevations), then the steepest window,
    leaving out impossible ones (data errors)."""
    best = None
    segs = []
    for part in parts or []:
        pts = [p for p in part if p and len(p) >= 3 and p[2] is not None]
        if len(pts) >= 2:
            segs += split_out_and_back(pts) or [pts]
    for pts in segs:
        if pts[-1][2] > pts[0][2]:   # read downhill, as profile.js
            pts = pts[::-1]
        prof = [(0.0, pts[0][2])]
        for a, b in zip(pts, pts[1:]):
            prof.append((prof[-1][0] + haversine_km((a[1], a[0]), (b[1], b[0])) * 1000, b[2]))
        if prof[-1][0] < 15:
            continue
        n = len(prof)
        sm = list(zip((d for d, _ in prof), smoothed_elevations(prof)))
        win = min(STEEPEST_M, sm[-1][0] - sm[0][0])
        if win <= 0:
            continue
        j = 0
        for i in range(n):
            # Exactly win metres, the end interpolated (as findSteepestSection).
            j = max(j, i)
            while j < n and sm[j][0] - sm[i][0] < win - 1e-6:
                j += 1
            if j >= n:
                break
            (da, ea), (db, eb) = sm[j - 1], sm[j]
            t = (sm[i][0] + win - da) / (db - da) if db > da else 1
            end_ele = ea + (eb - ea) * min(1, max(0, t))
            pct = abs(sm[i][1] - end_ele) / win * 100
            if pct > MAX_REAL_PITCH:
                continue
            if best is None or pct > best:
                best = pct
    return best


def max_pitch_badge(pct: float, tx: dict, f) -> str:
    """"máx. 38%" with a dot in that slope's colour (profile.js's pitch zones)."""
    # ATUDEM / AFNOR, as PITCH_ZONES; with the angle, which pictures better than % ("31°").
    zone = "novice" if pct < 15 else "easy" if pct < 25 else "intermediate" if pct < 40 else "advanced"
    deg = round(math.degrees(math.atan(abs(pct) / 100)))
    return (f'<span class="max-pitch" title="{html.escape(tx["max_grad_title"])}">'
            f'<i style="background:var(--diff-{zone})"></i>{html.escape(tx["max_grad"].format(f(round(pct))))} · {deg}°</span>')


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


# ---------- languages ----------

# Where each language's pages live, and a few head values.
LOC = {
    "es": {"privacy": "/privacy.html", "html": "es", "og": "es_ES", "home": "/", "station": "/estacion/", "countries": "/pais/", "guides": "/guias/",
           "app": "/app/", "og_dir": "/og/"},
    "en": {"privacy": "/privacy-en.html", "html": "en", "og": "en_GB", "home": "/en/", "station": "/en/resort/", "countries": "/en/country/",
           "guides": "/en/guides/", "app": "/en/app/", "og_dir": "/og/en/"},
    # The other languages reuse the English share images (their own would double the site's size).
    "fr": {"privacy": "/privacy-fr.html", "html": "fr", "og": "fr_FR", "home": "/fr/", "station": "/fr/station/", "countries": "/fr/pays/",
           "guides": "/fr/guides/", "app": "/fr/app/", "og_dir": "/og/en/"},
    "de": {"privacy": "/privacy-de.html", "html": "de", "og": "de_DE", "home": "/de/", "station": "/de/skigebiet/", "countries": "/de/land/",
           "guides": "/de/ratgeber/", "app": "/de/app/", "og_dir": "/og/en/"},
    "it": {"privacy": "/privacy-it.html", "html": "it", "og": "it_IT", "home": "/it/", "station": "/it/stazione/", "countries": "/it/paese/",
           "guides": "/it/guide/", "app": "/it/app/", "og_dir": "/og/en/"},
    "nl": {"privacy": "/privacy-nl.html", "html": "nl", "og": "nl_NL", "home": "/nl/", "station": "/nl/skigebied/", "countries": "/nl/land/",
           "guides": "/nl/gidsen/", "app": "/nl/app/", "og_dir": "/og/en/"},
    "pl": {"privacy": "/privacy-pl.html", "html": "pl", "og": "pl_PL", "home": "/pl/", "station": "/pl/osrodek/", "countries": "/pl/kraj/",
           "guides": "/pl/poradniki/", "app": "/pl/app/", "og_dir": "/og/en/"},
}
LANG_NAMES = {"es": "Español", "en": "English", "fr": "Français", "de": "Deutsch", "it": "Italiano", "nl": "Nederlands", "pl": "Polski"}

# Page text. Spanish is the original wording of the site; English mirrors it
# (French, German and Italian are in page_texts.py).
TX = {
    "es": {
        "resort": "Estación de esquí", "official_site": "Web oficial ↗", "altitude": "Altitud", "vertical": "Desnivel",
        "km_pistes": "Km pista", "coords": "Coordenadas", "linked": "Dominio esquiable conectado",
        "linked_note": "Detectado por proximidad geográfica; los km de cada una pueden solaparse:",
        "directions": "Cómo llegar", "share": "Compartir", "save": "Guardar", "back_country": "Estaciones de {0}", "back_countries": "Países",
        "open_map": "Abrir el mapa interactivo de pistas",
        "intro_1": "{0} es una estación de esquí{1}.", "intro_in": " en {0}",
        "intro_2": "Tiene {0} km de pistas repartidos en {1} pistas con nombre{2}.", "intro_2_lifts": " y {0} remontes",
        "intro_3": "Su dominio va de {0} a {1} m de altitud, con {2} m de desnivel.",
        "intro_4": "Aquí tienes todas sus pistas con su perfil de pendiente, sus remontes y los servicios en pistas; "
                   "en el mapa interactivo las verás sobre imagen de satélite.",
        "intro_h2": "{0}: mapa de pistas y datos", "terrain": "Terreno por dificultad", "lifts_by_type": "Remontes por tipo",
        "other": "Otro", "vert_m": "desnivel {0} m", "avg_grad": "pend. media {0}%", "alt_range": "{0}–{1} m alt.",
        "max_grad": "máx. {0}%", "max_grad_title": "Pendiente máxima: el tramo más empinado de al menos 50 m",
        "sections": "{0} tramos", "floodlit": "Nocturna", "glades": "Arbolada", "all_f": "Todas", "unclassified": "Sin clasif.",
        "pph": "{0} p/h", "seats": "{0} plazas", "ride": "{0} de trayecto", "unnamed": "Sin nombre",
        "detachable": "Desembragable", "bubble": "Burbuja", "heated": "Calefactado", "private": "Privado", "all_m": "Todos",
        "no_services": "No hay servicios registrados en OpenStreetMap para esta estación.",
        "no_services_data": "Todavía no tenemos datos de servicios para esta estación.",
        "catalog_h2": "Pistas, remontes y servicios", "catalog_sub": "pulsa una pista para ver su perfil",
        "what_to_list": "Qué listar", "runs": "Pistas", "lifts": "Remontes", "services": "Servicios",
        "no_runs": "No hay pistas con nombre en los datos de esta estación.",
        "no_lifts": "No hay remontes en los datos de esta estación.",
        "q_named": "Pistas con nombre", "q_diff": "Dificultad etiquetada", "q_lit": "Iluminación etiquetada",
        "q_snow": "Nieve artificial etiquetada", "q_cap": "Capacidad de remonte etiquetada", "q_grip": "Tipo de agarre etiquetado",
        "quality": "Calidad del dato", "about_data": "Sobre estos datos",
        "quality_note": "Nieve artificial y vigilancia rara vez están etiquetadas en OpenStreetMap — "
                        "no significa que no existan, es que casi nadie las mapea todavía.",
        "map_h2": "Mapa interactivo",
        "map_text": "Las pistas y remontes de {0} sobre imagen de satélite, el sentido de cada pista, la pendiente real de cada tramo, "
                    "los servicios y el tiempo en directo.",
        "map_cta": "Abrir el mapa de {0}", "ranks": "En los rankings", "nearby": "Estaciones cercanas",
        "nearby_meta": "a {0} km · {1} km de pistas", "snow_h2": "Nieve y tiempo en {0}", "top_txt": " (cota alta, {0} m)",
        "snow_sum": "Previsión de nieve para los próximos 7 días{0}: {1}{2}", "snow_cm": "{0} cm",
        "snow_none": "sin nevadas significativas", "snow_when": " (actualizada el {0}).",
        "snow_generic": "Previsión de nieve y tiempo para los próximos 7 días en {0}{1}.",
        "title": "{0}: mapa de pistas, previsión de nieve y remontes | Ski Info",
        "d_km": "{0} km de pistas", "d_runs": "{0} pistas", "d_lifts": "{0} remontes", "d_alt": "Altitud {0}–{1} m. ",
        "d_tail": "Previsión de nieve a 7 días, mapa de pistas interactivo sobre satélite y pendiente real de cada pista.",
        # country pages
        "c_eyebrow": "Países", "c_h1": "Estaciones de esquí en {0}",
        "c_sub": "{0} estaciones · {1} km de pistas. Elige una estación para ver todas sus pistas con su perfil de pendiente, "
                 "sus remontes, servicios y el mapa interactivo sobre satélite.",
        "c_title": "Estaciones de esquí en {0}: mapas de pistas | Ski Info",
        "c_desc": "Las {0} estaciones de esquí de {1} con mapa de pistas interactivo, perfil de pendiente, remontes y servicios.",
        "card_pista": "pista", "card_total": "pista total", "n_resorts": "{0} estaciones",
        "ci_h1": "Estaciones de esquí por país",
        "ci_sub": "{0} estaciones en {1} países, con mapa de pistas interactivo, perfil de pendiente de cada pista, remontes y servicios.",
        "ci_title": "Estaciones de esquí por país: mapas de pistas | Ski Info",
        "ci_desc": "Mapas de pistas interactivos de {0} estaciones de esquí en {1} países: pistas, remontes, pendientes y servicios.",
        # footer / language
        "f_countries": "Estaciones por país", "f_guides": "Guías y rankings", "f_app": "App para el móvil", "f_privacy": "Privacidad",
        "f_data": 'Datos © <a href="https://www.openstreetmap.org/copyright" target="_blank" rel="noopener">colaboradores de OpenStreetMap</a> (ODbL), vía OpenSkiMap.',
    },
    "en": {
        "resort": "Ski resort", "official_site": "Official website ↗", "altitude": "Altitude", "vertical": "Vertical",
        "km_pistes": "Km of pistes", "coords": "Coordinates", "linked": "Linked ski area",
        "linked_note": "Detected by geographic proximity; their kilometres may overlap:",
        "directions": "Directions", "share": "Share", "save": "Save", "back_country": "Ski resorts in {0}", "back_countries": "Countries",
        "open_map": "Open the interactive piste map",
        "intro_1": "{0} is a ski resort{1}.", "intro_in": " in {0}",
        "intro_2": "It has {0} km of pistes across {1} named runs{2}.", "intro_2_lifts": " and {0} lifts",
        "intro_3": "The ski area goes from {0} to {1} m of altitude, with {2} m of vertical.",
        "intro_4": "Here you'll find every run with its gradient profile, the lifts and the on-mountain services; "
                   "the interactive map shows them on satellite imagery.",
        "intro_h2": "{0}: piste map and stats", "terrain": "Terrain by difficulty", "lifts_by_type": "Lifts by type",
        "other": "Other", "vert_m": "{0} m vertical", "avg_grad": "avg. gradient {0}%", "alt_range": "{0}–{1} m altitude",
        "max_grad": "max {0}%", "max_grad_title": "Max slope: the steepest stretch of at least 50 m",
        "sections": "{0} sections", "floodlit": "Floodlit", "glades": "Tree skiing", "all_f": "All", "unclassified": "Unclassified",
        "pph": "{0} p/h", "seats": "{0} seats", "ride": "{0} ride", "unnamed": "Unnamed",
        "detachable": "Detachable", "bubble": "Bubble", "heated": "Heated seats", "private": "Private", "all_m": "All",
        "no_services": "No services are recorded in OpenStreetMap for this resort.",
        "no_services_data": "We don't have services data for this resort yet.",
        "catalog_h2": "Runs, lifts and services", "catalog_sub": "tap a run to see its profile",
        "what_to_list": "What to list", "runs": "Runs", "lifts": "Lifts", "services": "Services",
        "no_runs": "There are no named runs in this resort's data.",
        "no_lifts": "There are no lifts in this resort's data.",
        "q_named": "Named runs", "q_diff": "Difficulty tagged", "q_lit": "Lighting tagged",
        "q_snow": "Snowmaking tagged", "q_cap": "Lift capacity tagged", "q_grip": "Grip type tagged",
        "quality": "Data quality", "about_data": "About this data",
        "quality_note": "Snowmaking and ski patrol are rarely tagged in OpenStreetMap — "
                        "it doesn't mean they don't exist, just that hardly anyone maps them yet.",
        "map_h2": "Interactive map",
        "map_text": "The runs and lifts of {0} on satellite imagery, the direction of every run, the real gradient of each section, "
                    "the services and the live weather.",
        "map_cta": "Open the {0} map", "ranks": "In the rankings", "nearby": "Nearby resorts",
        "nearby_meta": "{0} km away · {1} km of pistes", "snow_h2": "Snow and weather at {0}", "top_txt": " (summit, {0} m)",
        "snow_sum": "Snow forecast for the next 7 days{0}: {1}{2}", "snow_cm": "{0} cm",
        "snow_none": "no significant snowfall", "snow_when": " (updated {0}).",
        "snow_generic": "Snow and weather forecast for the next 7 days at {0}{1}.",
        "title": "{0} piste map, snow forecast and lifts | Ski Info",
        "d_km": "{0} km of pistes", "d_runs": "{0} runs", "d_lifts": "{0} lifts", "d_alt": "Altitude {0}–{1} m. ",
        "d_tail": "7-day snow forecast, interactive trail map on satellite imagery and the real gradient of every run.",
        "c_eyebrow": "Countries", "c_h1": "Ski resorts in {0}",
        "c_sub": "{0} resorts · {1} km of pistes. Choose a resort to see every run with its gradient profile, "
                 "its lifts, services and the interactive satellite map.",
        "c_title": "Ski resorts in {0}: piste maps | Ski Info",
        "c_desc": "The {0} ski resorts in {1} with interactive piste maps, gradient profiles, lifts and services.",
        "card_pista": "of pistes", "card_total": "of pistes", "n_resorts": "{0} resorts",
        "ci_h1": "Ski resorts by country",
        "ci_sub": "{0} resorts in {1} countries, with interactive piste maps, the gradient profile of every run, lifts and services.",
        "ci_title": "Ski resorts by country: piste maps | Ski Info",
        "ci_desc": "Interactive piste maps of {0} ski resorts in {1} countries: runs, lifts, gradients and services.",
        "f_countries": "Resorts by country", "f_guides": "Guides & rankings", "f_app": "Mobile app", "f_privacy": "Privacy",
        "f_data": 'Data © <a href="https://www.openstreetmap.org/copyright" target="_blank" rel="noopener">OpenStreetMap contributors</a> (ODbL), via OpenSkiMap.',
    },
}
TX.update(MORE_TX)
# Plain sentences an answer engine can quote ("the steepest run of X is..."),
# with the same figures as the badges: (several, one, longest, "and", item).
for _l, (_many, _one, _long, _and) in {
    "es": ("Sus pistas más empinadas (tramo de 50 m con más pendiente) son {0}.",
           "Su pista más empinada (tramo de 50 m con más pendiente) es {0}.", "La pista más larga es {0} ({1} km).", "y"),
    "en": ("Its steepest runs (steepest 50 m stretch) are {0}.",
           "Its steepest run (steepest 50 m stretch) is {0}.", "The longest run is {0} ({1} km).", "and"),
    "fr": ("Ses pistes les plus raides (tronçon de 50 m le plus pentu) sont {0}.",
           "Sa piste la plus raide (tronçon de 50 m le plus pentu) est {0}.", "La piste la plus longue est {0} ({1} km).", "et"),
    "de": ("Die steilsten Pisten (steilster 50-m-Abschnitt) sind {0}.",
           "Die steilste Piste (steilster 50-m-Abschnitt) ist {0}.", "Die längste Piste ist {0} ({1} km).", "und"),
    "it": ("Le piste più ripide (tratto di 50 m più ripido) sono {0}.",
           "La pista più ripida (tratto di 50 m più ripido) è {0}.", "La pista più lunga è {0} ({1} km).", "e"),
    "nl": ("De steilste pistes (steilste stuk van 50 m) zijn {0}.",
           "De steilste piste (steilste stuk van 50 m) is {0}.", "De langste piste is {0} ({1} km).", "en"),
    "pl": ("Najbardziej strome trasy (najbardziej stromy odcinek 50 m): {0}.",
           "Najbardziej stroma trasa (najbardziej stromy odcinek 50 m): {0}.", "Najdłuższa trasa: {0} ({1} km).", "i"),
}.items():
    TX[_l].update(intro_steep=_many, intro_steep_one=_one, intro_long=_long, and_word=_and)


def load_i18n(docs: Path, lang: str = "en") -> dict:
    """docs/i18n/<lang>.js: 'window.SKI_I18N = {json};' shared with the browser."""
    src = (docs / "i18n" / f"{lang}.js").read_text(encoding="utf-8")
    marker = "window.SKI_I18N ="
    return json.loads(src[src.index(marker) + len(marker):].strip().rstrip(";"))


def localized_meta(meta: dict, i18n: dict) -> dict:
    """The app tables with the dictionary's labels (station list and groups unchanged)."""
    tb = i18n["tables"]
    out = dict(meta)
    out["diff"] = {k: tb["diff"].get(k, v) for k, v in meta["diff"].items()}
    out["lift_types"] = {k: tb["lift_type"].get(k, v) for k, v in meta["lift_types"].items()}
    out["activity"] = {k: tb["activity"].get(k, v) for k, v in meta["activity"].items()}
    out["status"] = {k: tb["status"].get(k, v) for k, v in meta["status"].items()}
    out["grooming"] = {k: tb["grooming"].get(k, v) for k, v in meta["grooming"].items()}
    out["services"] = {k: (tb["services"].get(k, label), icon) for k, (label, icon) in meta["services"].items()}
    out["countries"] = {cc: (tb["countries"].get(cc, name), flag) for cc, (name, flag) in meta["countries"].items()}
    return out


# ---------- page shell ----------

# Self-hosted @font-face rules, inlined into every page (one request fewer).
FONT_FACES = "\n".join(l for l in (REPO / "docs" / "fonts.css").read_text(encoding="utf-8").splitlines()
                       if l.startswith("@font-face"))


def page(*, title: str, description: str, url: str, body: str, body_attrs: str = "",
         jsonld: dict | None = None, noindex: bool = False, scripts: bool = False,
         image: str | None = None, base_url: str = "https://skiinfoapp.com",
         lang: str = "es", alternates: dict | None = None) -> str:
    loc, tx = LOC[lang], TX[lang]
    alternates = dict(alternates or {})
    alternates.setdefault(lang, url)
    image = image or f"{loc['og_dir']}ski-info.jpg"
    head_extra = '<meta name="robots" content="noindex">\n' if noindex else ""
    if len(alternates) > 1:
        head_extra += "".join(f'<link rel="alternate" hreflang="{l}" href="{e(u)}">\n' for l, u in sorted(alternates.items()))
        head_extra += f'<link rel="alternate" hreflang="x-default" href="{e(alternates.get("en", url))}">\n'
    if jsonld:
        head_extra += ('<script type="application/ld+json">'
                       + json.dumps(jsonld, ensure_ascii=False).replace("</", "<\\/") + "</script>\n")
    # Deferred: they run in order once the page is parsed, without holding up
    # the first paint. Station pages report a station view (static-pages.js);
    # track.js with data-page reports a plain page view.
    i18n = (f'<script defer src="/i18n/{lang}.js"></script>\n' if lang != "es" else "") + '<script defer src="/i18n.js"></script>\n'
    tail = (i18n + '<script defer src="/profile.js"></script>\n<script defer src="/snow.js"></script>\n'
            '<script defer src="/station-actions.js"></script>\n<script defer src="/track.js"></script>\n'
            '<script defer src="/static-pages.js"></script>\n'
            if scripts else '<script defer src="/track.js" data-page></script>\n')
    # The "also in your language" bar and remembering a language choice.
    tail += '<script defer src="/lang.js"></script>\n'
    # "Send feedback" (footer, and "report a data error" on station pages):
    # its texts in every language come with it.
    tail += '<script defer src="/feedback.js"></script>\n'
    if scripts:
        # Not needed for the first screen: load it without blocking the paint.
        head_extra = ('<link rel="stylesheet" href="/snow.css" media="print" onload="this.media=\'all\'">\n'
                      '<noscript><link rel="stylesheet" href="/snow.css"></noscript>\n' + head_extra)
    lang_links = " · ".join(
        f'<a class="lang-link" data-lang="{l}" hreflang="{l}" lang="{l}" '
        f'href="{e(re.sub(r"^https?://[^/]+", "", alternates.get(l) or LOC[l]["home"]))}">{LANG_NAMES[l]}</a>'
        for l in LOC if l != lang)
    return f"""<!doctype html>
<html lang="{loc['html']}">
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
<meta property="og:locale" content="{loc['og']}">
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
<a href="{loc['home']}">Ski Info</a> · <a href="{loc['countries']}">{tx['f_countries']}</a> · <a href="{loc['guides']}">{tx['f_guides']}</a> · <a href="{loc['app']}">{tx['f_app']}</a> · <a href="{loc['privacy']}">{tx['f_privacy']}</a> · <a href="#" data-feedback></a><br>
<span class="lang-links">{lang_links}</span><br>
{tx['f_data']}
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

def station_page(raw: dict, meta: dict, ctx: dict, lang: str = "es") -> tuple[str, bool]:
    tx, loc, f = TX[lang], LOC[lang], FMT[lang]
    base, sid = ctx["base_url"], raw["id"]
    slug = ctx["slug"][sid]
    cc = raw.get("country_code")
    country_name = meta["countries"].get(cc, (cc or "", ""))[0]
    name = display_name(raw.get("name"), sid) or tx["resort"]
    short = short_name(name) or name
    place = ", ".join(p for p in [raw.get("locality"), raw.get("region")] if p) or country_name
    place_full = ", ".join(p for p in [raw.get("locality"), raw.get("region"), country_name] if p)
    url = f"{base}{loc['station']}{slug}/"
    alternates = {l: f"{base}{LOC[l]['station']}{slug}/" for l in LOC}
    app_link = f"{loc['home']}?estacion={sid}&amp;vista=mapa"

    convention = raw.get("run_convention")
    runs = [dict(r, name=feature_name(r.get("name")), difficulty=shown_difficulty(r.get("difficulty"), convention))
            for r in raw.get("runs", []) if is_downhill(r)]
    lifts = [dict(l, name=feature_name(l.get("name"))) for l in raw.get("lifts", [])]
    services = [s for s in raw.get("services") or [] if s.get("category") in meta["services"]]
    total_m = sum(r.get("length_m") or 0 for r in runs)
    lo, hi = raw.get("min_elevation_m"), raw.get("max_elevation_m")
    diff_key = lambda d: d if d in meta["diff"] else "other"
    diff_color = lambda k: f"var(--diff-{k})"
    indexable = bool(runs or lifts)

    # ----- hero (badges, title, stats, connected domain) -----
    badges = [meta["activity"].get(a, a) for a in (raw.get("activities") or "").split(",") if a]
    # The status only when it's news (closed, a project...): "operating" said nothing.
    if raw.get("status") and raw.get("status") != "operating":
        badges.append(meta["status"].get(raw.get("status"), raw.get("status")))
    badges.append(country_name)
    badges_html = "".join(f'<span class="badge">{e(b)}</span>' for b in badges if b)
    site = (raw.get("websites") or [None])[0]
    site_html = f'<a class="site" href="{e(site)}" target="_blank" rel="noopener">{tx["official_site"]}</a>' if site else ""
    stats = [
        (f"{f(round(lo))}–{f(round(hi))} m" if lo is not None and hi is not None else "–", tx["altitude"]),
        (f"{f(round(hi - lo))} m" if lo is not None and hi is not None else "–", tx["vertical"]),
        (f"{f(round(total_m / 1000))} km", tx["km_pistes"]),
        (f(len(lifts)), tx["lifts"]),
    ]
    stats_html = "".join(f'<div class="hero-stat"><div class="v">{e(v)}</div><div class="k">{e(k)}</div></div>' for v, k in stats)
    domain_html = ""
    group = ctx["group_of"].get(sid)
    if group:
        links = "".join(
            f'<a class="chip" href="{loc["station"]}{ctx["slug"][o]}/">{e(ctx["by_id"][o]["name"])} · {f(round(ctx["by_id"][o].get("pisteKm") or 0))} km</a>'
            for o in group if o != sid and o in ctx["by_id"])
        if links:
            domain_html = (f'<div class="hero-domain"><div class="hero-domain-title">{tx["linked"]}</div>'
                           f'<p class="hero-domain-note">{tx["linked_note"]}</p>'
                           f'<div class="chips">{links}</div></div>')
    country_slug = ctx["country_slug"][lang].get(cc)
    base_pt = base_location(raw)
    directions_html = (f'<a class="hero-action" href="https://www.google.com/maps/dir/?api=1&amp;destination={base_pt[0]:.5f},{base_pt[1]:.5f}" '
                       f'target="_blank" rel="noopener">{PIN_ICON} {tx["directions"]}</a>' if base_pt else "")
    back = (f'<a class="back-btn" href="{loc["countries"]}{country_slug}/"><span class="chev">‹</span> {e(tx["back_country"].format(country_name))}</a>'
            if country_slug else f'<a class="back-btn" href="{loc["countries"]}"><span class="chev">‹</span> {tx["back_countries"]}</a>')
    hero = f"""<div class="topbar">{back}<a class="back-btn" href="{loc['home']}">Ski Info</a></div>
<div class="hero">{PEAKS_SVG}<div class="hero-content">
<div class="badges">{badges_html}</div>
<div class="hero-title-row"><h1>{e(name)}</h1>{site_html}</div>
<div class="place">{e(place)}</div>
<div class="hero-stats">{stats_html}</div>
{domain_html}
<div class="hero-cta-row">
<a class="hero-cta" href="{app_link}">{MAP_ICON} {tx['open_map']}</a>
<div class="hero-actions"><button type="button" class="hero-action js-fav" aria-pressed="false" data-id="{sid}" data-name="{e(short)}" data-country="{cc}">{FAV_ICON} {tx['save']}</button>{directions_html}<button type="button" class="hero-action js-share" data-url="{e(url)}" data-title="{e(short)}">{SHARE_ICON} {tx['share']}</button></div>
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
                                   "min": None, "max": None, "parts": []})
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
        g["parts"].extend(r.get("geom") or [])
    run_groups = sorted(groups.values(), key=lambda g: (meta["diff_order"].index(diff_key(g["difficulty"])), -g["length_m"]))

    intro = [tx["intro_1"].format(e(short), tx["intro_in"].format(e(place_full)) if place_full else "")]
    if total_m and run_groups:
        intro.append(tx["intro_2"].format(f(round(total_m / 1000)), len(run_groups),
                                          tx["intro_2_lifts"].format(len(lifts)) if lifts else ""))
    if lo is not None and hi is not None:
        intro.append(tx["intro_3"].format(f(round(lo)), f(round(hi)), f(round(hi - lo))))
    for g in run_groups:
        g["max_pitch"] = run_max_pitch(g["parts"])
    # Pisted runs only, and nothing above 60%: steeper than that on a piste is
    # more often the ~30 m relief catching a cliff beside it than the run, and
    # a sentence gets quoted as fact (the badges still show every figure).
    steep = sorted((g for g in run_groups if g["max_pitch"] is not None and g["max_pitch"] <= 60
                    and diff_key(g["difficulty"]) not in ("freeride", "extreme")),
                   key=lambda g: -g["max_pitch"])[:3]
    if steep:
        items = [f'{e(g["name"])} ({f(round(g["max_pitch"]))}%, {round(math.degrees(math.atan(g["max_pitch"] / 100)))}°)'
                 for g in steep]
        joined = items[0] if len(items) == 1 else ", ".join(items[:-1]) + f' {tx["and_word"]} ' + items[-1]
        intro.append((tx["intro_steep"] if len(items) > 1 else tx["intro_steep_one"]).format(joined))
    longest = max(run_groups, key=lambda g: g["length_m"], default=None)
    if longest and longest["length_m"] >= 300:
        intro.append(tx["intro_long"].format(e(longest["name"]), f(longest["length_m"] / 1000, 1)))
    intro.append(e(tx["intro_4"]))
    intro_html = (f'<section><div class="section-head"><h2>{e(tx["intro_h2"].format(short))}</h2></div>'
                  f'<p class="intro">{" ".join(intro)}</p></section>')

    # ----- charts: terrain by difficulty, lifts by type (same as the app) -----
    diff_agg: dict[str, list] = {}
    for r in runs:
        a = diff_agg.setdefault(diff_key(r.get("difficulty")), [0.0, 0])
        a[0] += (r.get("length_m") or 0) / 1000
        a[1] += 1
    diff_bars = bars([(meta["diff"][k], diff_agg[k][0], f"{f(diff_agg[k][0], 1)} km · {diff_agg[k][1]}", diff_color(k))
                      for k in meta["diff_order"] if k in diff_agg])
    lift_agg: dict[str, list] = {}
    for l in lifts:
        a = lift_agg.setdefault(l.get("lift_type"), [0.0, 0])
        a[0] += (l.get("length_m") or 0) / 1000
        a[1] += 1
    lift_bars = bars([(meta["lift_types"].get(k, k or tx["other"]), v[0], f"{f(v[0], 1)} km · {v[1]}", "var(--accent)")
                      for k, v in sorted(lift_agg.items(), key=lambda kv: -kv[1][0])])
    charts_html = '<div class="charts">'
    if diff_bars:
        charts_html += f'<section><div class="section-head"><h2>{tx["terrain"]}</h2></div>{diff_bars}</section>'
    if lift_bars:
        charts_html += f'<section><div class="section-head"><h2>{tx["lifts_by_type"]}</h2></div>{lift_bars}</section>'
    charts_html += "</div>"

    # ----- catalog: runs / lifts / services -----
    run_items = []
    for g in run_groups:
        k = diff_key(g["difficulty"])
        bits = []
        if g["length_m"]:
            bits.append(f'{f(round(g["length_m"]))} m')
        if g["vertical_m"]:
            bits.append(tx["vert_m"].format(f(round(g["vertical_m"]))))
        if g["length_m"]:
            bits.append(tx["avg_grad"].format(f(100 * g["vertical_m"] / g["length_m"], 1)))
        if g["min"] is not None and g["max"] is not None:
            bits.append(tx["alt_range"].format(f(round(g["min"])), f(round(g["max"]))))
        if meta["grooming"].get(g["grooming"]):
            bits.append(meta["grooming"][g["grooming"]])
        if g["segments"] > 1:
            bits.append(tx["sections"].format(g["segments"]))
        pills = (pill(tx["floodlit"]) if g["lit"] else "") + (pill(tx["glades"]) if g["gladed"] else "")
        label = (f'{g["ref"]} · ' if g["ref"] else "") + g["name"]
        if "max_pitch" not in g:
            g["max_pitch"] = run_max_pitch(g["parts"])
        badge = max_pitch_badge(g["max_pitch"], tx, f) if g["max_pitch"] is not None else ""
        run_items.append(
            f'<div class="item run-item" data-key="{k}" data-run="{e(g["name"])}" role="button" tabindex="0" aria-expanded="false">'
            f'<span class="dot" style="background:{diff_color(k)}"></span><div class="item-main">'
            f'<div class="item-name">{e(label)}{badge}</div><div class="item-meta">{e(" · ".join(bits))}{pills}</div></div>'
            f'<span class="item-chevron" aria-hidden="true">›</span></div><div class="run-profile" hidden></div>')
    run_filters = [("all", tx["all_f"], ["all"]), ("novice", meta["diff"]["novice"], ["novice"]),
                   ("easy", meta["diff"]["easy"], ["easy"]), ("intermediate", meta["diff"]["intermediate"], ["intermediate"]),
                   ("advanced", meta["diff"]["advanced"], ["advanced", "expert"]),
                   ("double", meta["diff"]["double"], ["double"]),
                   ("freeride", meta["diff"]["freeride"], ["freeride", "extreme"]), ("other", tx["unclassified"], ["other"])]
    run_chip_defs = []
    for key, label, keys in run_filters:
        count = len(run_groups) if key == "all" else sum(1 for g in run_groups if diff_key(g["difficulty"]) in keys)
        if key == "all" or count:
            run_chip_defs.append((keys, label, count, None if key == "all" else diff_color(key)))

    lift_items, lift_type_counts = [], {}
    for l in lifts:
        t = l.get("lift_type") or "other"
        lift_type_counts[t] = lift_type_counts.get(t, 0) + 1
        bits = []
        if l.get("capacity"):
            bits.append(tx["pph"].format(f(l["capacity"])))
        if l.get("occupancy"):
            bits.append(tx["seats"].format(l["occupancy"]))
        if l.get("length_m"):
            bits.append(f'{f(round(l["length_m"]))} m')
        if l.get("vertical_m"):
            bits.append(tx["vert_m"].format(f(round(l["vertical_m"]))))
        if l.get("duration_s"):
            m = round(l["duration_s"] / 60)
            bits.append(tx["ride"].format(f"{m} min" if m >= 1 else f'{round(l["duration_s"])} s'))
        pills = ((pill(tx["detachable"]) if l.get("detachable") == 1 else "") + (pill(tx["bubble"]) if l.get("bubble") == 1 else "")
                 + (pill(tx["heated"]) if l.get("heating") == 1 else "") + (pill(tx["private"]) if l.get("access") == "private" else ""))
        label = ((f'{l["ref"]} · ' if l.get("ref") else "") + (l.get("name") or tx["unnamed"])
                 + "  ·  " + meta["lift_types"].get(l.get("lift_type"), l.get("lift_type") or ""))
        lift_items.append(f'<div class="item" data-key="{e(t)}"><span class="dot" style="background:var(--accent)"></span>'
                          f'<div class="item-main"><div class="item-name">{e(label)}</div>'
                          f'<div class="item-meta">{e(" · ".join(bits))}{pills}</div></div></div>')
    lift_chip_defs = [(["all"], tx["all_m"], len(lifts), None)] + [
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
    svc_chip_defs = [(["all"], tx["all_m"], len(services), None)] + [
        ([k], f"{meta['services'][k][1]} {meta['services'][k][0]}", svc_counts[k], None) for k in cat_order if svc_counts.get(k)]

    def panel(key, items, chip_defs, empty_text, hidden):
        body = (chips(f"{key}-list", chip_defs) + f'<div class="list-scroll" id="{key}-list">{"".join(items)}</div>'
                if items else f'<div class="list-scroll"><div class="catalog-empty">{e(empty_text)}</div></div>')
        return f'<div class="catalog-panel" id="catalog-{key}"{" hidden" if hidden else ""}>{body}</div>'

    no_services = tx["no_services"] if raw.get("services") is not None else tx["no_services_data"]
    catalog_html = f"""<section>
<div class="section-head"><h2>{tx['catalog_h2']}</h2><span class="sub">{tx['catalog_sub']}</span></div>
<div class="segmented" role="tablist" aria-label="{tx['what_to_list']}">
<button type="button" role="tab" class="seg-btn" data-catalog="runs" aria-selected="true">{tx['runs']} <span class="seg-count">{len(run_groups)}</span></button>
<button type="button" role="tab" class="seg-btn" data-catalog="lifts" aria-selected="false">{tx['lifts']} <span class="seg-count">{len(lifts)}</span></button>
<button type="button" role="tab" class="seg-btn" data-catalog="services" aria-selected="false">{tx['services']} <span class="seg-count">{len(services)}</span></button>
</div>
{panel("runs", run_items, run_chip_defs, tx["no_runs"], False)}
{panel("lifts", lift_items, lift_chip_defs, tx["no_lifts"], True)}
{panel("services", svc_items, svc_chip_defs, no_services, True)}
</section>"""

    # ----- data quality (same figures as the app) -----
    run_n, lift_n = len(runs) or 1, len(lifts) or 1
    pct = lambda n, d: f"{f(100 * n / d)}%"
    quality = [
        (tx["q_named"], f"{sum(1 for r in runs if r.get('name'))} / {len(runs)}"),
        (tx["q_diff"], pct(sum(1 for r in runs if r.get("difficulty")), run_n)),
        (tx["q_lit"], pct(sum(1 for r in runs if r.get("lit") is not None), run_n)),
        (tx["q_snow"], pct(sum(1 for r in runs if r.get("snowmaking") is not None), run_n)),
        (tx["q_cap"], pct(sum(1 for l in lifts if l.get("capacity") is not None), lift_n)),
        (tx["q_grip"], pct(sum(1 for l in lifts if l.get("detachable") is not None), lift_n)),
    ]
    # Folded away: it's for the curious, not what a skier comes for.
    quality_html = (f'<section><details class="about-data"><summary>{tx["about_data"]}</summary>'
                    f'<h3>{tx["quality"]}</h3><div class="quality-list">'
                    + "".join(f'<div class="quality-row"><span class="name">{e(k)}</span><span class="val">{e(v)}</span></div>' for k, v in quality)
                    + f'</div><p class="quality-note">{tx["quality_note"]}</p>'
                    # Filled in and wired by feedback.js; the context is for the email to us.
                    + f'<p class="quality-note"><a href="#" data-feedback="data" data-feedback-station="{e(short)}" '
                    f'data-feedback-context="{e("Datos de " + name + " (" + sid + ")")}"></a></p></details></section>')

    # ----- sidebar: map card, rankings, nearby stations -----
    map_card = (f'<section class="map-card"><div class="section-head"><h2>{tx["map_h2"]}</h2></div>'
                f'<p class="intro">{e(tx["map_text"].format(short))}</p>'
                f'<a class="cta-block" href="{app_link}">{MAP_ICON} {e(tx["map_cta"].format(short))}</a></section>')
    ranks = ctx["ranks"][lang].get(sid) or []
    ranks_html = ""
    if ranks:
        ranks_html = (f'<section><div class="section-head"><h2>{tx["ranks"]}</h2></div><div class="rank-list">'
                      + "".join(f'<a class="rank-link" href="{href}"><span class="rank-medal">★</span>{e(label)}</a>'
                                for label, href in ranks[:8])
                      + '</div></section>')
    nearby = ctx["nearby"].get(sid) or []
    nearby_html = ""
    if nearby:
        items = "".join(
            f'<a class="item" href="{loc["station"]}{ctx["slug"][s["id"]]}/"><span class="dot" style="background:var(--accent)"></span>'
            f'<div class="item-main"><div class="item-name">{e(s["name"])}</div>'
            f'<div class="item-meta">{tx["nearby_meta"].format(f(round(d)), f(round(s.get("pisteKm") or 0)))}</div></div>'
            f'<span class="item-chevron" aria-hidden="true">›</span></a>' for s, d in nearby)
        nearby_html = (f'<section><div class="section-head"><h2>{tx["nearby"]}</h2></div>'
                       f'<div class="list-scroll">{items}</div></section>')

    # ----- snow + weather: a server-rendered summary from snow.json (so the
    # page says something about the coming week even without JS), replaced
    # by the full live forecast by static-pages.js + snow.js -----
    snow_html = ""
    if raw.get("latitude") is not None:
        fc = ctx["snow"].get(sid)
        top_txt = tx["top_txt"].format(f(round(hi))) if hi is not None else ""
        if fc and fc.get("sf"):
            total_sf = sum(v or 0 for v in fc["sf"])
            when = ctx["snow_date"][lang]
            summary = tx["snow_sum"].format(top_txt, tx["snow_cm"].format(f(round(total_sf))) if total_sf >= 1 else tx["snow_none"],
                                            tx["snow_when"].format(when) if when else ".")
        else:
            summary = tx["snow_generic"].format(e(short), top_txt)
        attrs = f' data-lat="{raw["latitude"]:.4f}" data-lon="{raw["longitude"]:.4f}"'
        if lo is not None and hi is not None:
            attrs += f' data-top="{round(hi)}" data-base="{round(lo)}"'
        snow_html = (f'<section id="snow-section"{attrs}><div class="section-head"><h2>{e(tx["snow_h2"].format(short))}</h2></div>'
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

    title = tx["title"].format(short)
    desc_bits = []
    if total_m:
        desc_bits.append(tx["d_km"].format(f(round(total_m / 1000))))
    if run_groups:
        desc_bits.append(tx["d_runs"].format(len(run_groups)))
    if lifts:
        desc_bits.append(tx["d_lifts"].format(len(lifts)))
    description = short + (f" ({place_full})" if place_full else "") + ": " + (", ".join(desc_bits) + ". " if desc_bits else "")
    if lo is not None and hi is not None:
        description += tx["d_alt"].format(f(round(lo)), f(round(hi)))
    description += tx["d_tail"]

    jsonld = {"@context": "https://schema.org", "@type": "SkiResort", "name": name, "url": url, "inLanguage": lang}
    address = {"@type": "PostalAddress", "addressRegion": raw.get("region"), "addressLocality": raw.get("locality"), "addressCountry": cc}
    jsonld["address"] = {k: v for k, v in address.items() if v}
    if raw.get("latitude") is not None:
        jsonld["geo"] = {"@type": "GeoCoordinates", "latitude": round(raw["latitude"], 5), "longitude": round(raw["longitude"], 5)}
    jsonld["image"] = f"{base}{loc['og_dir']}{slug}.jpg"
    same_as = [x for x in [site, f"https://www.wikidata.org/wiki/{raw['wikidata_id']}" if raw.get("wikidata_id") else None] if x]
    if same_as:
        jsonld["sameAs"] = same_as

    return page(title=title, description=description, url=url, body=body,
                body_attrs=f' data-station="{e(sid)}" data-name="{e(name)}" data-country="{e(cc or "")}"',
                jsonld=jsonld, noindex=not indexable, scripts=True,
                image=f"{loc['og_dir']}{slug}.jpg", base_url=base, lang=lang, alternates=alternates), indexable


# ---------- country pages ----------

def station_card(href: str, name: str, sub: str, km: float, label: str, prefix: str = "", lang: str = "es") -> str:
    return (f'<a class="station-card" href="{href}"><div class="info"><div class="name">{prefix}{e(name)}</div>'
            f'<div class="region">{e(sub)}</div></div><div class="stats"><div class="km">{FMT[lang](round(km))} km</div>'
            f'<div class="km-label">{e(label)}</div></div><span class="chevron" aria-hidden="true">›</span></a>')


def country_page(cc: str, stations: list, meta: dict, ctx: dict, lang: str = "es") -> str:
    tx, loc, f = TX[lang], LOC[lang], FMT[lang]
    base = ctx["base_url"]
    name = meta["countries"].get(cc, (cc, ""))[0]
    url = f"{base}{loc['countries']}{ctx['country_slug'][lang][cc]}/"
    alternates = {l: f"{base}{LOC[l]['countries']}{ctx['country_slug'][l][cc]}/" for l in LOC}
    total = sum(s.get("pisteKm") or 0 for s in stations)
    cards = "".join(station_card(f'{loc["station"]}{ctx["slug"][s["id"]]}/', s["name"], s.get("region") or "",
                                 s.get("pisteKm") or 0, tx["card_pista"], lang=lang) for s in stations)
    body = f"""<div class="list-header">
<div class="eyebrow"><a href="{loc['home']}">Ski Info</a> · <a href="{loc['countries']}">{tx['c_eyebrow']}</a></div>
<h1>{e(tx['c_h1'].format(name))}</h1>
<p class="list-sub">{e(tx['c_sub'].format(len(stations), f(round(total))))}</p>
</div>
<div class="station-list">{cards}</div>"""
    return page(title=tx["c_title"].format(name), description=tx["c_desc"].format(len(stations), name),
                url=url, body=body, base_url=base, lang=lang, alternates=alternates)


def countries_index(by_country: dict, meta: dict, ctx: dict, lang: str = "es") -> str:
    tx, loc = TX[lang], LOC[lang]
    base = ctx["base_url"]
    order = sorted(by_country, key=lambda cc: -sum(s.get("pisteKm") or 0 for s in by_country[cc]))
    cards = "".join(
        station_card(f'{loc["countries"]}{ctx["country_slug"][lang][cc]}/', meta["countries"].get(cc, (cc, ""))[0],
                     tx["n_resorts"].format(len(by_country[cc])), sum(s.get("pisteKm") or 0 for s in by_country[cc]),
                     tx["card_total"], lang=lang,
                     prefix=f'<img class="flag" src="/flags/{cc.lower()}.svg" alt="" width="24" height="18" loading="lazy">')
        for cc in order)
    n = sum(len(v) for v in by_country.values())
    body = f"""<div class="list-header">
<div class="eyebrow"><a href="{loc['home']}">Ski Info</a></div>
<h1>{tx['ci_h1']}</h1>
<p class="list-sub">{e(tx['ci_sub'].format(FMT[lang](n), len(by_country)))}</p>
</div>
<div class="station-list">{cards}</div>"""
    return page(title=tx["ci_title"], description=tx["ci_desc"].format(FMT[lang](n), len(by_country)),
                url=f"{base}{loc['countries']}", body=body, base_url=base, lang=lang,
                alternates={l: f"{base}{LOC[l]['countries']}" for l in LOC})


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

APP_TX = {
    "es": {"add_home": "Añadir a inicio", "available": "Disponible en", "soon": "Muy pronto en",
           "soon_note": "La app está en fase de pruebas. Mientras tanto puedes usar Ski Info desde Chrome e instalarla: "
                        "menú <b>⋮</b> → <b>Añadir a pantalla de inicio</b> (o <b>Instalar aplicación</b>).",
           "h1": "Ski Info en tu móvil",
           "lead": "Los mapas de pistas, la pendiente de cada pista y la previsión de nieve de {0}+ estaciones, siempre a mano. Gratis y sin registro.",
           "b1": "Se abre como una app", "b1t": "Con su icono en la pantalla de inicio, a pantalla completa.",
           "b2": "Funciona con poca cobertura", "b2t": "Las estaciones que ya hayas consultado se abren aunque no tengas señal en pistas.",
           "b3": "Siempre actualizada", "b3t": "Sin actualizaciones que descargar: siempre la última versión.",
           "inapp": "Ya estás usando la app de Ski Info. ¡Gracias!", "ios_h2": "iPhone y iPad",
           "ios_lead": "No hace falta App Store: se instala desde <b>Safari</b> en tres pasos.",
           "s1": "Abre <b>skiinfoapp.com</b> en Safari y pulsa el botón <b>Compartir</b> <i class=\"ico\">{0}</i> de la barra de abajo.",
           "s2": "Desliza hacia abajo y pulsa <b>Añadir a pantalla de inicio</b> <i class=\"ico\">{0}</i>.",
           "s3": "Pulsa <b>Añadir</b>. Ski Info aparecerá en tu pantalla de inicio como cualquier otra app.",
           "chrome_ios": "Si usas Chrome en el iPhone, el botón Compartir está arriba, junto a la barra de direcciones.",
           "pc_h2": "En el ordenador",
           "pc": "No hace falta instalar nada: entra en <a href=\"/\">skiinfoapp.com</a>. En Chrome o Edge también puedes instalarla "
                 "con el icono <b>Instalar</b> que aparece a la derecha de la barra de direcciones.",
           "title": "Descarga Ski Info: app de mapas de pistas y nieve para Android y iPhone",
           "desc": "Instala Ski Info en tu móvil: mapas de pistas, pendiente de cada pista y previsión de nieve de "
                   "{0}+ estaciones de esquí. Android y iPhone, gratis y sin registro."},
    "en": {"add_home": "Add to Home", "available": "Get it on", "soon": "Coming soon to",
           "soon_note": "The app is in testing. Meanwhile you can use Ski Info in Chrome and install it: "
                        "menu <b>⋮</b> → <b>Add to Home screen</b> (or <b>Install app</b>).",
           "h1": "Ski Info on your phone",
           "lead": "Piste maps, the gradient of every run and the snow forecast for {0}+ resorts, always at hand. Free, no sign-up.",
           "b1": "Opens like an app", "b1t": "With its own icon on your home screen, full screen.",
           "b2": "Works with poor signal", "b2t": "Resorts you've already opened load even with no signal on the slopes.",
           "b3": "Always up to date", "b3t": "No updates to download: always the latest version.",
           "inapp": "You're already using the Ski Info app. Thank you!", "ios_h2": "iPhone and iPad",
           "ios_lead": "No App Store needed: install it from <b>Safari</b> in three steps.",
           "s1": "Open <b>skiinfoapp.com/en/</b> in Safari and tap the <b>Share</b> button <i class=\"ico\">{0}</i> in the bottom bar.",
           "s2": "Scroll down and tap <b>Add to Home Screen</b> <i class=\"ico\">{0}</i>.",
           "s3": "Tap <b>Add</b>. Ski Info will appear on your home screen like any other app.",
           "chrome_ios": "If you use Chrome on iPhone, the Share button is at the top, next to the address bar.",
           "pc_h2": "On a computer",
           "pc": "Nothing to install: go to <a href=\"/en/\">skiinfoapp.com/en/</a>. In Chrome or Edge you can also install it "
                 "with the <b>Install</b> icon on the right of the address bar.",
           "title": "Get Ski Info: piste map and snow forecast app for Android and iPhone",
           "desc": "Install Ski Info on your phone: piste maps, the gradient of every run and snow forecasts for "
                   "{0}+ ski resorts. Android and iPhone, free, no sign-up."},
}
APP_TX.update(MORE_APP_TX)


def phone(inner: str) -> str:
    """A tiny phone mock-up (SVG) for the iPhone install steps."""
    return ('<svg class="phone" viewBox="0 0 120 200" aria-hidden="true">'
            '<rect x="3" y="3" width="114" height="194" rx="18" fill="var(--bg)" stroke="var(--text-muted)" stroke-width="2"/>'
            '<rect x="44" y="9" width="32" height="6" rx="3" fill="var(--text-muted)" opacity=".5"/>' + inner + '</svg>')


def app_page(ctx: dict, n_stations: int, lang: str = "es") -> str:
    at, loc = APP_TX[lang], LOC[lang]
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
        f'<text x="18" y="136" font-size="8.5" font-weight="700" fill="var(--text-primary)" font-family="IBM Plex Sans, sans-serif">{at["add_home"]}</text>'
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

    play_icon = ('<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 2.8v18.4c0 .4.4.6.7.4l16-9.2c.3-.2.3-.6 0-.8l-16-9.2c-.3-.2-.7 0-.7.4z" '
                 'fill="currentColor"/></svg>')
    if PLAY_STORE_LIVE:
        play_html = (f'<a class="store-badge" href="{PLAY_STORE_URL}" target="_blank" rel="noopener">{play_icon}'
                     f'<span><small>{at["available"]}</small>Google Play</span></a>')
    else:
        play_html = (f'<span class="store-badge soon">{play_icon}<span><small>{at["soon"]}</small>Google Play</span></span>'
                     f'<p class="app-note">{at["soon_note"]}</p>')

    # Always grouped ("1.200"): Spanish only groups from 10.000 up.
    hundreds = f"{n_stations // 100 * 100:,}".replace(",", ".") if lang == "es" else FMT[lang](n_stations // 100 * 100)
    body = f"""<div class="app-hero">{PEAKS_SVG}<div class="app-hero-inner">
<div class="eyebrow app-eyebrow"><a href="{loc['home']}">Ski Info</a> · App</div>
<img class="app-logo" src="/icons/icon-192.png" alt="" width="84" height="84">
<h1>{at['h1']}</h1>
<p>{at['lead'].format(hundreds)}</p>
</div></div>
<div class="app-wrap">
<div class="app-benefits">
<div><b>{at['b1']}</b><span>{at['b1t']}</span></div>
<div><b>{at['b2']}</b><span>{at['b2t']}</span></div>
<div><b>{at['b3']}</b><span>{at['b3t']}</span></div>
</div>

<section class="app-card" id="app-android">
<h2><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M7 9h10v8a1.5 1.5 0 0 1-1.5 1.5h-7A1.5 1.5 0 0 1 7 17z M8.5 8a3.5 3.5 0 0 1 7 0z M9 5l-1-1.6M15 5l1-1.6" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linejoin="round" stroke-linecap="round"/></svg>Android</h2>
<p class="app-inapp" hidden>{at['inapp']}</p>
<div class="app-android-body">{play_html}</div>
</section>

<section class="app-card" id="app-ios">
<h2><svg viewBox="0 0 24 24" aria-hidden="true"><rect x="6.5" y="2.5" width="11" height="19" rx="2.5" fill="none" stroke="currentColor" stroke-width="1.6"/><path d="M10.5 18.5h3" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/></svg>{at['ios_h2']}</h2>
<p class="app-lead">{at['ios_lead']}</p>
<ol class="ios-steps">
<li>{safari_bar}<span class="step-n">1</span><span>{at['s1'].format(IOS_SHARE)}</span></li>
<li>{share_sheet}<span class="step-n">2</span><span>{at['s2'].format(IOS_ADD)}</span></li>
<li>{home_screen}<span class="step-n">3</span><span>{at['s3']}</span></li>
</ol>
<p class="app-note">{at['chrome_ios']}</p>
</section>

<section class="app-card" id="app-desktop">
<h2><svg viewBox="0 0 24 24" aria-hidden="true"><rect x="3" y="4.5" width="18" height="12" rx="1.8" fill="none" stroke="currentColor" stroke-width="1.6"/><path d="M8.5 20h7M12 16.5V20" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/></svg>{at['pc_h2']}</h2>
<p class="app-lead">{at['pc']}</p>
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
  if (window.SkiInfoAndroid || /; wv\\)/.test(ua)) {{
    document.querySelector('.app-inapp').hidden = false;
    document.querySelector('.app-android-body').hidden = true;
  }}
}})();
</script>"""
    base = ctx["base_url"]
    return page(title=at["title"], description=at["desc"].format(hundreds), url=f"{base}{loc['app']}", body=body,
                base_url=base, lang=lang, alternates={l: f"{base}{LOC[l]['app']}" for l in LOC})


# ---------- home-page data inlined into the app ----------

HOME_EUROPE = {"ES", "FR", "AT", "IT", "CH", "AD", "DE", "SI", "NO", "SE", "FI", "PL", "CZ", "SK", "BG", "RO", "GE", "BA",
               "RS", "ME", "IS", "GB", "LI", "MK", "HR", "RU", "TR", "GR", "UA", "AM", "AZ"}
HOME_GUIDES = {
    "es": ["donde-nieva-esta-semana", "estaciones-mas-grandes-espana-andorra", "estaciones-para-principiantes-espana-andorra",
           "pistas-mas-empinadas-espana-andorra", "estaciones-de-esqui-cerca-de-madrid", "estaciones-de-esqui-cerca-de-barcelona"],
    "en": ["where-it-will-snow-this-week", "biggest-ski-resorts-in-the-alps", "best-ski-resorts-for-beginners-in-the-alps",
           "steepest-ski-runs-in-the-alps", "biggest-ski-resorts-in-north-america", "ski-resorts-near-geneva"],
    "fr": ["ou-va-t-il-neiger-cette-semaine", "plus-grandes-stations-de-ski-des-alpes",
           "meilleures-stations-de-ski-pour-debutants-dans-les-alpes", "pistes-de-ski-les-plus-raides-des-alpes",
           "stations-de-ski-pres-de-paris", "stations-de-ski-pres-de-lyon"],
    "de": ["wo-schneit-es-diese-woche", "groesste-skigebiete-der-alpen", "beste-skigebiete-fuer-anfaenger-in-den-alpen",
           "steilste-pisten-der-alpen", "skigebiete-in-der-naehe-von-muenchen", "skigebiete-in-der-naehe-von-zuerich"],
    "it": ["dove-nevichera-questa-settimana", "stazioni-sciistiche-piu-grandi-delle-alpi",
           "migliori-stazioni-sciistiche-per-principianti-nelle-alpi", "piste-da-sci-piu-ripide-delle-alpi",
           "stazioni-sciistiche-vicino-a-milano", "stazioni-sciistiche-vicino-a-torino"],
    "nl": ["waar-gaat-het-deze-week-sneeuwen", "grootste-skigebieden-in-de-alpen", "beste-skigebieden-voor-beginners-in-de-alpen",
           "steilste-pistes-in-de-alpen", "skigebieden-bij-amsterdam", "skigebieden-bij-brussel"],
    "pl": ["gdzie-spadnie-snieg-w-tym-tygodniu", "najwieksze-osrodki-narciarskie-w-polsce", "najwieksze-osrodki-narciarskie-w-alpach",
           "najbardziej-strome-trasy-w-polsce", "osrodki-narciarskie-w-poblizu-krakowa", "osrodki-narciarskie-w-poblizu-warszawy"],
}


def home_data_json(snow_doc: dict | None, stations: list, guides_index: list, lang: str) -> str:
    """The home page's snow ranking and featured guides, inlined into the app
    (<script id="home-data">) so they render with the page instead of arriving
    later and pushing content down. Only the stations that can make any zone's
    top list are included (the page ranks them)."""
    data = {"guides": [g for slug in HOME_GUIDES[lang] for g in guides_index if g["slug"] == slug]}
    if snow_doc and snow_doc.get("stations"):
        cc_of = {s["id"]: s.get("country") or "ES" for s in stations}
        ranked = sorted(((sum(v or 0 for v in f.get("sf") or []), sid) for sid, f in snow_doc["stations"].items()
                         if sid in cc_of), reverse=True)
        keep = set()
        for zone in (lambda cc: True, lambda cc: cc in HOME_EUROPE, lambda cc: cc in {"ES", "AD"}):
            keep.update([sid for _, sid in ranked if zone(cc_of[sid])][:30])
        data["snow"] = {"updated": snow_doc.get("updated"),
                        "stations": {sid: snow_doc["stations"][sid] for sid in keep}}
    return json.dumps(data, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")


def fill_home_data(html_text: str, payload: str) -> str:
    placeholder = re.compile(r'(<script id="home-data" type="application/json">).*?(</script>)', re.DOTALL)
    new_text, n = placeholder.subn(lambda m: m.group(1) + payload + m.group(2), html_text, count=1)
    if n != 1:
        raise SystemExit("home-data placeholder not found in index.html")
    return new_text


# ---------- the app's copy in each language (/en/, /fr/, /de/...) ----------

APP_HEAD = {
    "en": {"title": "Ski Info · Piste maps and snow forecasts for ski resorts",
           "description": "Interactive piste maps on satellite imagery, the gradient profile of every run, lifts, services and 7-day "
                          "snow forecasts for over 1,200 ski resorts in 45 countries.",
           "og_title": "Ski Info · Piste maps and snow forecasts",
           "og_description": "Piste maps on satellite imagery, the real gradient of every run and the snow forecast for over 1,200 ski "
                             "resorts. Free, no sign-up."},
    **MORE_APP_HEAD,
}
# Text nodes that are the same in every language (brand, symbols, numbers, language names...).
SAME_IN_BOTH = {"Ski Info", "Info", "Freeride", "–", "+", "×", "›", "‹", "1.200+", "Android", "3D", "2D", "© Esri · OpenStreetMap"} | set(LANG_NAMES.values())
# "1.200+" in the home's title, per language.
HUNDREDS = {"en": "1,200+", "fr": "1\u00a0200+", "pl": "1200+"}


def build_localized_app(index_html: str, i18n: dict, lang: str, base_url: str) -> str:
    """docs/<lang>/index.html from docs/index.html: the language's head, the
    markup's text and attributes translated from its dictionary, its links, and
    docs/i18n/<lang>.js loaded before the scripts (whose own strings go
    through T()). Fails if any visible Spanish text would be left untranslated."""
    ui, head_tx, loc = i18n["ui"], APP_HEAD[lang], LOC[lang]
    s = index_html
    s = s.replace('<html lang="es">', f'<html lang="{lang}">', 1)
    head_end = s.index("</head>") if "</head>" in s else s.index("<style>")
    head, rest = s[:head_end], s[head_end:]
    head = re.sub(r"<title>.*?</title>", f"<title>{html.escape(head_tx['title'])}</title>", head, count=1)
    head = re.sub(r'(<meta name="description" content=")[^"]*', lambda m: m.group(1) + html.escape(head_tx["description"]), head, count=1)
    head = head.replace(f'<link rel="canonical" href="{base_url}/">', f'<link rel="canonical" href="{base_url}{loc["home"]}">', 1)
    head = re.sub(r'(<meta property="og:title" content=")[^"]*', lambda m: m.group(1) + html.escape(head_tx["og_title"]), head, count=1)
    head = re.sub(r'(<meta property="og:description" content=")[^"]*', lambda m: m.group(1) + html.escape(head_tx["og_description"]), head, count=1)
    head = head.replace(f'<meta property="og:url" content="{base_url}/">', f'<meta property="og:url" content="{base_url}{loc["home"]}">', 1)
    head = head.replace(f'content="{base_url}/og/ski-info.jpg"', f'content="{base_url}{loc["og_dir"]}ski-info.jpg"', 1)
    head = head.replace('<meta property="og:locale" content="es_ES">', f'<meta property="og:locale" content="{loc["og"]}">', 1)
    # The Spanish home's "remembered language" redirect must not run here.
    head = re.sub(r"<script id=\"lang-redirect\">.*?</script>\n?", "", head, flags=re.DOTALL)
    s = head + rest

    start, end = s.index('<div class="app"'), s.index('<script id="home-data"')
    markup = s[start:end]
    missing = []
    links = " · ".join(f'<a class="lang-link" data-lang="{l}" href="{LOC[l]["home"]}" hreflang="{l}" lang="{l}">{LANG_NAMES[l]}</a>'
                       for l in LOC if l != lang)
    markup, n = re.subn(r'<span class="lang-links">.*?</span>', f'<span class="lang-links">{links}</span>', markup, count=1, flags=re.DOTALL)
    if n != 1:
        raise SystemExit("language links (<span class=\"lang-links\">) not found in index.html")

    def tr_text(m):
        raw = m.group(1)
        t = raw.strip()
        if not t or not re.search(r"[A-Za-zÁÉÍÓÚáéíóúñÑ]", t) or t in SAME_IN_BOTH:
            return m.group(0)
        if t in ui:
            return ">" + raw.replace(t, ui[t]) + "<"
        missing.append(t)
        return m.group(0)
    markup = re.sub(r">([^<>]+)<", tr_text, markup)

    def tr_attr(m):
        t = m.group(2)
        if t in ui:
            return f'{m.group(1)}="{ui[t]}"'
        if re.search(r"[A-Za-z]", t) and t not in SAME_IN_BOTH:
            missing.append(t)
        return m.group(0)
    markup = re.sub(r'(placeholder|aria-label|title)="([^"]+)"', tr_attr, markup)
    for page_key, es_path in (("countries", "/pais/"), ("guides", "/guias/"), ("app", "/app/"), ("privacy", "/privacy.html")):
        markup = markup.replace(f'href="{es_path}"', f'href="{loc[page_key]}"')
    if lang in HUNDREDS:
        markup = markup.replace('<span id="home-station-count">1.200+</span>', f'<span id="home-station-count">{HUNDREDS[lang]}</span>')
    if missing:
        raise SystemExit(f"untranslated text in the app markup (add it to docs/i18n/{lang}.js): " + "; ".join(sorted(set(missing))))
    s = s[:start] + markup + s[end:]
    s = s.replace('<script src="/i18n.js"></script>', f'<script src="/i18n/{lang}.js"></script>\n<script src="/i18n.js"></script>', 1)
    return s


def country_slugify(name: str, lang: str) -> str:
    if lang == "de":  # German readers write umlauts out: Österreich -> oesterreich
        name = name.translate(str.maketrans({"ä": "ae", "ö": "oe", "ü": "ue", "Ä": "Ae", "Ö": "Oe", "Ü": "Ue", "ß": "ss"}))
    name = name.replace("ł", "l").replace("Ł", "L")  # not a decomposable letter: Włochy -> wlochy
    return slugify(name)


# ---------- main ----------

def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--docs", type=Path, default=REPO / "docs")
    ap.add_argument("--base-url", default="https://skiinfoapp.com")
    ap.add_argument("--write-slugs", action="store_true", help="persist slugs for new stations")
    ap.add_argument("--inject-home", action="store_true",
                    help="inline the home page's data into docs/index.html (deploy only: rewrites a committed file)")
    args = ap.parse_args()
    base_url = args.base_url.rstrip("/")

    meta_es = load_app_metadata(read_app_sources(args.docs))
    i18n = {l: load_i18n(args.docs, l) for l in LOC if l != "es"}
    metas = {"es": meta_es, **{l: localized_meta(meta_es, d) for l, d in i18n.items()}}
    stations = meta_es["stations"]
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
    # Slugs are settled: from here on names are only shown.
    for s in stations:
        s["name"] = display_name(s["name"], s["id"])

    by_country: dict[str, list] = {}
    for s in stations:
        by_country.setdefault(s.get("country") or "ES", []).append(s)
    for lst in by_country.values():
        lst.sort(key=lambda s: -(s.get("pisteKm") or 0))
    country_slug = {lang: {cc: country_slugify(metas[lang]["countries"].get(cc, (cc, ""))[0], lang) for cc in by_country}
                    for lang in LOC}

    group_of = {sid: g for g in meta_es["groups"] for sid in g}
    coords = {s["id"]: (s["lat"], s["lon"]) for s in stations if s.get("lat") is not None}
    nearby = {}
    for sid, c in coords.items():
        dists = sorted((haversine_km(c, oc), oid) for oid, oc in coords.items() if oid != sid)
        nearby[sid] = [(by_id[oid], d) for d, oid in dists[:8] if d <= 150]

    # Written just before by fetch_snow_forecast.py; optional.
    snow, snow_updated, snow_doc = {}, "", None
    snow_date = {l: "" for l in LOC}
    snow_path = args.docs / "snow.json"
    if snow_path.exists():
        snow_doc = json.loads(snow_path.read_text(encoding="utf-8"))
        snow = snow_doc.get("stations", {})
        snow_updated = snow_doc.get("updated", "")
        months_es = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto",
                     "septiembre", "octubre", "noviembre", "diciembre"]
        months_en = ["January", "February", "March", "April", "May", "June", "July", "August",
                     "September", "October", "November", "December"]
        y, m, d = (int(x) for x in snow_updated[:10].split("-"))
        snow_date = {"es": f"{d} de {months_es[m - 1]}", "en": f"{d} {months_en[m - 1]}",
                     **{l: DATE_FMT[l].format(d=d, m=MONTHS[l][m - 1]) for l in MONTHS}}

    ctx = {"base_url": base_url, "slug": slug, "country_slug": country_slug,
           "by_id": by_id, "group_of": group_of, "nearby": nearby, "snow": snow, "snow_date": snow_date}

    # First pass: the numbers the guides/rankings need, so station pages can
    # link to the rankings they appear in.
    from build_guides import build_guides, station_ranks, station_stats, write_all
    base_stats = []
    for s in stations:
        raw = json.loads((args.docs / "data" / f"{s['id']}.json").read_text(encoding="utf-8"))
        st = station_stats(raw, is_downhill)
        # Named as the app shows it ("San Isidro (Saliencias)", not three "San Isidro").
        st.update(id=s["id"], name=display_name(s["name"], s["id"]) or short_name(s["name"]) or s["name"],
                  cc=s.get("country") or "ES", region=s.get("region"),
                  slug=slug[s["id"]], lat=s.get("lat") or raw.get("latitude") or 0, lon=s.get("lon") or raw.get("longitude") or 0)
        base_stats.append(st)
    guides, ctx["ranks"] = {}, {}
    for lang in LOC:
        stats = [dict(st, country=metas[lang]["countries"].get(st["cc"], (st["cc"], ""))[0]) for st in base_stats]
        guides[lang] = build_guides(stats, snow, snow_date[lang], FMT[lang], metas[lang]["diff"], snow_updated, lang=lang)
        ctx["ranks"][lang] = station_ranks(guides[lang], lang)

    # Guides with the same key in both languages are translations of each other.
    guide_alt: dict[str, dict] = {"index": {l: f"{base_url}{LOC[l]['guides']}" for l in LOC}}
    for lang in LOC:
        for g in guides[lang]:
            guide_alt.setdefault(g.key, {})[lang] = f"{base_url}{LOC[lang]['guides']}{g.slug}/"

    entries: list[tuple[str, dict]] = []  # (url, alternates) for the sitemap
    home_alt = {l: f"{base_url}{LOC[l]['home']}" for l in LOC}
    for lang in LOC:
        entries.append((home_alt[lang], home_alt))
        entries += write_all(args.docs, guides[lang], page, e, base_url, lang, lambda key: guide_alt.get(key, {}))

    for s in stations:
        raw = json.loads((args.docs / "data" / f"{s['id']}.json").read_text(encoding="utf-8"))
        for lang in LOC:
            html_text, indexable = station_page(raw, metas[lang], ctx, lang)
            out = args.docs / LOC[lang]["station"].strip("/") / slug[s["id"]] / "index.html"
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_text(html_text, encoding="utf-8")
            if indexable:
                entries.append((f"{base_url}{LOC[lang]['station']}{slug[s['id']]}/",
                                {l: f"{base_url}{LOC[l]['station']}{slug[s['id']]}/" for l in LOC}))

    for lang in LOC:
        croot = args.docs / LOC[lang]["countries"].strip("/")
        for cc, lst in by_country.items():
            out = croot / country_slug[lang][cc] / "index.html"
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_text(country_page(cc, lst, metas[lang], ctx, lang), encoding="utf-8")
            entries.append((f"{base_url}{LOC[lang]['countries']}{country_slug[lang][cc]}/",
                            {l: f"{base_url}{LOC[l]['countries']}{country_slug[l][cc]}/" for l in LOC}))
        croot.mkdir(parents=True, exist_ok=True)
        (croot / "index.html").write_text(countries_index(by_country, metas[lang], ctx, lang), encoding="utf-8")
        entries.append((f"{base_url}{LOC[lang]['countries']}", {l: f"{base_url}{LOC[l]['countries']}" for l in LOC}))
        aroot = args.docs / LOC[lang]["app"].strip("/")
        aroot.mkdir(parents=True, exist_ok=True)
        (aroot / "index.html").write_text(app_page(ctx, len(stations), lang), encoding="utf-8")
        entries.append((f"{base_url}{LOC[lang]['app']}", {l: f"{base_url}{LOC[l]['app']}" for l in LOC}))

    sitemap = ['<?xml version="1.0" encoding="UTF-8"?>',
               '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:xhtml="http://www.w3.org/1999/xhtml">']
    for u, alt in entries:
        links = "".join(f'<xhtml:link rel="alternate" hreflang="{l}" href="{html.escape(v)}"/>' for l, v in sorted(alt.items())) \
            if len(alt) > 1 else ""
        sitemap.append(f"  <url><loc>{html.escape(u)}</loc>{links}</url>")
    sitemap.append("</urlset>")
    (args.docs / "sitemap.xml").write_text("\n".join(sitemap) + "\n", encoding="utf-8")

    # The app's copies (/en/, /fr/...) are generated from the Spanish one before
    # the latter gets its own home data inlined.
    index_path = args.docs / "index.html"
    index_html = index_path.read_text(encoding="utf-8")
    apps = {l: build_localized_app(index_html, i18n[l], l, base_url) for l in LOC if l != "es"}
    apps["es"] = index_html
    for lang, text in apps.items():
        if args.inject_home:
            guides_index = json.loads((args.docs / GUIDE_PATHS[lang]["index_json"]).read_text(encoding="utf-8"))
            text = fill_home_data(text, home_data_json(snow_doc, stations, guides_index, lang))
        if lang == "es":
            if args.inject_home:
                index_path.write_text(text, encoding="utf-8")
            continue
        (args.docs / lang).mkdir(exist_ok=True)
        (args.docs / lang / "index.html").write_text(text, encoding="utf-8")

    print(f"{len(stations)} stations x {len(LOC)} languages, {len(by_country)} countries, "
          f"{sum(len(g) for g in guides.values())} guides, {len(entries)} URLs in sitemap")


if __name__ == "__main__":
    main()
