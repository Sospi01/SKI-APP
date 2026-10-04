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

from guide_texts import CITIES, GROUPS, GT, PAGE, PATHS, RANK_ITEM, RUN_PREFIX, SPECS, ZONE_TXT

# OSM's piste:difficulty is the same scale everywhere, but each region shows
# it with its own colours (OpenSkiMap's run_convention): "easy" is a blue run
# in Europe but a green circle in North America. Map it to the grade shown,
# named after the European key with that colour ("double" = double black
# diamond). Mirrors DIFF_SHOWN_AS in docs/index.html.
DIFF_SHOWN_AS = {
    "north_america": {"easy": "novice", "intermediate": "easy", "expert": "double"},
    "japan": {"easy": "novice"},
}


def shown_difficulty(difficulty: str | None, convention: str | None) -> str | None:
    return DIFF_SHOWN_AS.get(convention, {}).get(difficulty, difficulty)


# Official piste grades only: freeride/extreme itineraries and ungraded
# "descenso" ways would otherwise fill the steepest-run lists.
GRADED = {"novice", "easy", "intermediate", "advanced", "expert", "double"}
IBERIA = {"ES", "AD"}
# Unpatrolled ski routes / itineraries sometimes carry a piste grade in OSM.
NOT_A_PISTE = re.compile(r"^descenso|ski ?route|skiroute|itin[eé]rai|itinerar|freeride|variante", re.IGNORECASE)
ALPS_CC = {"FR", "CH", "IT", "AT", "DE", "SI", "LI"}


def in_pyrenees(s: dict) -> bool:
    return s["cc"] in {"ES", "AD", "FR"} and 42.0 <= s["lat"] <= 43.4 and -2.0 <= s["lon"] <= 3.3


def in_alps(s: dict) -> bool:
    return s["cc"] in ALPS_CC and 43.8 <= s["lat"] <= 48.2 and 5.0 <= s["lon"] <= 16.5


# Which stations each zone covers; its name in each language is in guide_texts.
ZONES = {
    "iberia": lambda s: s["cc"] in IBERIA,
    "pyrenees": in_pyrenees,
    "alps": in_alps,
    "world": lambda s: True,
    "north_america": lambda s: s["cc"] in {"US", "CA"},
    "japan": lambda s: s["cc"] == "JP",
    "poland": lambda s: s["cc"] == "PL",
}
# The pool of resorts each language's "near <city>" guides consider (Spanish
# readers drive to Spain, Andorra and France; the others' cities are central).
CITY_POOL = {"es": lambda s: s["cc"] in {"ES", "AD", "FR"}}
GROUP_ORDER = ["snow", "resorts", "runs", "near"]


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
    convention = raw.get("run_convention")
    for r in runs:
        if not r.get("name"):
            continue
        g = groups.setdefault(r["name"], {"name": r["name"], "len": 0.0, "vert": 0.0,
                                          "diff": shown_difficulty(r.get("difficulty"), convention)})
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
    slug, lat, lon + station_stats(). fmt formats numbers for `lang`; the words
    come from guide_texts."""
    spec, gt, groups = SPECS[lang], GT[lang], GROUPS[lang]
    real = [s for s in stations if s["km"] >= 3]
    guides: list[Guide] = []
    pct = lambda x: gt["pct"].format(x)

    def place(s):
        return ", ".join(p for p in [s.get("region"), s["country"]] if p)

    def station_meta(s):
        bits = [gt["runs_w"].format(s["n_runs"]) if s["n_runs"] else None,
                gt["lifts_w"].format(s["n_lifts"]) if s["n_lifts"] else None]
        if s["lo"] is not None and s["hi"] is not None:
            bits.append(f"{fmt(round(s['lo']))}–{fmt(round(s['hi']))} m")
        return " · ".join(b for b in bits if b)

    def zones(zone):
        z, z_in = ZONE_TXT[zone][lang]
        return {"zone": z, "zone_in": z_in}

    # ---- biggest ----
    t = gt["biggest"]
    for slug, zone, n in spec["biggest"]:
        lst = sorted((s for s in real if ZONES[zone](s)), key=lambda s: -s["km"])[:n]
        if not lst:
            continue
        z, top = zones(zone), lst[0]
        intro = (t["intro"].format(n=len(lst), top=top["name"], place=place(top), km=fmt(round(top["km"])), **z)
                 + (t["follow"].format(name=lst[1]["name"], km=fmt(round(lst[1]["km"]))) if len(lst) > 1 else "")
                 + (t["and"].format(name=lst[2]["name"], km=fmt(round(lst[2]["km"]))) if len(lst) > 2 else ".")
                 + t["tail"])
        title = t["title"].format(**z)
        guides.append(Guide(slug=slug, key=f"biggest:{zone}", group=groups["resorts"], kind="station",
                            title=title, h1=title, intro=intro, method=t["method"], rank_label=t["rank"].format(**z),
                            items=[Item(s, f"{fmt(round(s['km']))} km", t["label"], station_meta(s)) for s in lst]))

    # ---- beginners ----
    t = gt["beginners"]
    for slug, zone, n, min_km in spec["beginners"]:
        lst = [s for s in real if ZONES[zone](s) and s["km"] >= min_km and s["easy_km"] > 0]
        lst.sort(key=lambda s: (-s["easy_km"] / s["km"], -s["km"]))
        lst = lst[:n]
        if not lst:
            continue
        z, top = zones(zone), lst[0]
        share = lambda s: fmt(round(100 * s["easy_km"] / s["km"]))
        guides.append(Guide(
            slug=slug, key=f"beginners:{zone}", group=groups["resorts"], kind="station",
            title=t["title"].format(**z), h1=t["h1"].format(**z),
            intro=t["intro"].format(top=top["name"], pct=share(top), km=fmt(round(top["km"])), min_km=min_km, **z),
            method=t["method"].format(min_km=min_km), rank_label=t["rank"].format(**z),
            items=[Item(s, pct(share(s)), t["label"],
                        t["meta"].format(easy=fmt(round(s["easy_km"])), km=fmt(round(s["km"])), meta=station_meta(s)))
                   for s in lst]))

    # ---- highest / biggest vertical ----
    for kind in ("highest", "vertical"):
        t = gt[kind]
        for slug, zone, n in spec[kind]:
            pool = [s for s in real if ZONES[zone](s) and s["hi"] is not None and s["lo"] is not None]
            val = (lambda s: s["hi"]) if kind == "highest" else (lambda s: s["hi"] - s["lo"])
            lst = sorted(pool, key=lambda s: -val(s))[:n]
            if not lst:
                continue
            z, top = zones(zone), lst[0]
            title = t["title"].format(**z)
            meta = lambda s: t["meta"].format(lo=fmt(round(s["lo"])), hi=fmt(round(s["hi"])), km=fmt(round(s["km"])),
                                              km_pistes=gt["km_pistes"])
            guides.append(Guide(
                slug=slug, key=f"{kind}:{zone}", group=groups["resorts"], kind="station", title=title, h1=title,
                intro=t["intro"].format(top=top["name"], hi=fmt(round(top["hi"])), v=fmt(round(val(top))), **z),
                method=t["method"], rank_label=t["rank"].format(**z),
                items=[Item(s, f"{fmt(round(val(s)))} m", t["label"], meta(s)) for s in lst]))

    # ---- runs: steepest / longest ----
    for kind in ("steep", "long"):
        t = gt[kind]
        for slug, zone, n in spec[kind]:
            rows, seen = [], set()
            for s in real:
                if not ZONES[zone](s):
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
            z = zones(zone)
            s0, r0, p0 = rows[0]
            nums = lambda r, p: {"len": fmt(round(r["len"])), "vert": fmt(round(r["vert"])), "p": fmt(round(p)),
                                 "km": fmt(r["len"] / 1000, 1), "diff": diff_labels.get(r["diff"], "")}
            metric = (lambda r, p: pct(fmt(round(p)))) if kind == "steep" else (lambda r, p: f"{fmt(r['len'] / 1000, 1)} km")
            title = t["title"].format(**z)
            guides.append(Guide(
                slug=slug, key=f"{kind}:{zone}", group=groups["runs"], kind="run", title=title, h1=title,
                intro=t["intro"].format(n=len(rows), run=r0["name"], station=s0["name"], **nums(r0, p0), **z),
                method=t["method"], rank_label=t["rank"].format(**z),
                items=[Item(s, metric(r, p), t["label"], t["meta"].format(**nums(r, p)), title=r["name"], diff=r["diff"])
                       for s, r, p in rows]))

    # ---- near a city ----
    t = gt["near"]
    in_pool = CITY_POOL.get(lang, lambda s: True)
    near_pool = [s for s in real if in_pool(s)]
    for cslug, (cname, clat, clon) in CITIES[lang].items():
        rows = sorted(((haversine_km(clat, clon, s["lat"], s["lon"]), s) for s in near_pool), key=lambda x: x[0])
        rows = [(d, s) for d, s in rows if d <= 450][:12]
        if not rows:
            continue
        d0, s0 = rows[0]
        within = sum(1 for d, _ in rows if d <= 250)
        title = t["title"].format(city=cname)
        guides.append(Guide(
            slug=t["slug"].format(city=cslug), key=f"near:{cslug}", group=groups["near"], kind="station",
            title=title, h1=title, intro=t["intro"].format(city=cname, top=s0["name"], d=fmt(round(d0)), within=within),
            method=t["method"], rank_label=t["rank"].format(city=cname),
            items=[Item(s, f"{fmt(round(d))} km", t["label"], t["meta"].format(km=fmt(round(s["km"])), meta=station_meta(s)))
                   for d, s in rows]))

    # ---- snow this week ----
    t = gt["snow"]
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
    when = t["when"].format(date=snow_date) if snow_date else ""
    if world:
        t0, s0, _ = world[0]
        intro = t["intro"].format(when=when, top=s0["name"], place=place(s0), cm=fmt(round(t0)))
    else:
        intro = t["none"].format(when=when)
    guides.append(Guide(
        slug=spec["snow"], key="snow", group=groups["snow"], kind="snow", updated=snow_updated[:10],
        title=t["title"], h1=t["h1"], intro=intro, method=t["method"],
        items=[Item(s, f"{fmt(round(total))} cm", t["label"], station_meta(s), spark=sf) for total, s, sf in world]))
    return guides


# ---------- rendering ----------

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
    tx = PAGE[lang]
    gpath = PATHS[lang]["guides"]
    url = guide_url(base_url, lang, g.slug)
    items = "".join(item_html(it, i + 1, e, lang) for i, it in enumerate(g.items))
    stale = ""
    if g.updated:
        # The forecast is refreshed by the daily deploy; if that ever stops,
        # say how old it is instead of passing it off as this week's.
        locale = PATHS[lang]["locale"]
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
    og_dir = PATHS[lang]["og_dir"]
    return page(title=f"{g.title} | Ski Info", description=g.intro[:300], url=url, body=body, jsonld=jsonld,
                image=f"{og_dir}{first}.jpg" if first else f"{og_dir}ski-info.jpg", base_url=base_url,
                lang=lang, alternates=alternates)


def index_page(guides: list[Guide], page, e, base_url: str, lang: str, alternates: dict) -> str:
    tx = PAGE[lang]
    gpath = PATHS[lang]["guides"]
    groups: dict[str, list[Guide]] = {}
    for g in guides:
        groups.setdefault(g.group, []).append(g)
    order = [GROUPS[lang][k] for k in GROUP_ORDER]
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
                image=f"{PATHS[lang]['og_dir']}ski-info.jpg")


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
            what = g.rank_label
            if lang == "es":
                what = what[0].lower() + what[1:]  # keep "España", "Alpes"... capitalised
            label = (RUN_PREFIX[lang].format(title=it.title) if it.title else "") + RANK_ITEM[lang].format(i=i + 1, what=what)
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
