"""Generate the social-share preview images (Open Graph, 1200x630 JPEG).

One image per station and language, /og/<slug>.jpg (Spanish) and
/og/en/<slug>.jpg (English), with its piste map drawn from the station's own
run/lift geometry next to its name and key numbers, plus a generic
ski-info.jpg for the home and country pages in each. These are what
WhatsApp, Telegram, X, Facebook... show when someone shares a link.

Runs in the Pages deploy workflow after build_seo_pages.py (which writes the
docs/slugs.json it reads); the images are not committed. Needs Pillow.

Usage: python3 data-pipeline/scripts/build_share_images.py [--only <slug>...]
"""
from __future__ import annotations

import argparse
import json
import math
import re
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_seo_pages import (display_name, fmt, fmt_en, is_downhill, latin_name, load_app_metadata, load_i18n,  # noqa: E402
                             localized_meta, read_app_sources, short_name)
from build_guides import shown_difficulty  # noqa: E402

REPO = Path(__file__).resolve().parents[2]
DOCS = REPO / "docs"
FONTS = REPO / "data-pipeline" / "fonts"
W, H = 1200, 630
SS = 2  # drawn at 2x and downsampled, for anti-aliased lines and text

# The app's dark-theme piste colours (they read best on the navy background).
DIFF_COLORS = {
    "novice": "#31c43f", "easy": "#4ba3ef", "intermediate": "#ec5b60",
    "advanced": "#e6e6e6", "expert": "#e6e6e6", "double": "#e6e6e6", "freeride": "#f2a33a",
    "extreme": "#f2a33a", "other": "#8c8c8c",
}
LIFT_COLOR = "#a79ef0"
TOP, BOTTOM = (15, 42, 72), (29, 92, 170)
SYSTEM_FALLBACK = Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf")


def font(name: str, size: int, text: str = "") -> ImageFont.FreeTypeFont:
    # The web fonts only carry the Latin subset: fall back to DejaVu for names
    # with other characters (Polish, Czech, Turkish... accents) if present.
    if any(ord(c) > 0xFF and c not in "‘’“”–—…·" for c in text) and SYSTEM_FALLBACK.exists():
        return ImageFont.truetype(str(SYSTEM_FALLBACK), int(size * SS * 0.86))
    return ImageFont.truetype(str(FONTS / name), size * SS)


BARLOW = "barlow-condensed-latin-700-normal.woff"
PLEX = "ibm-plex-sans-latin-500-normal.woff"
PLEX_B = "ibm-plex-sans-latin-600-normal.woff"


def background() -> Image.Image:
    mask = Image.linear_gradient("L").resize((W * SS, H * SS))
    img = Image.composite(Image.new("RGB", mask.size, BOTTOM), Image.new("RGB", mask.size, TOP), mask)
    over = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(over)
    sx, sy = W * SS / 400, H * SS / 140
    for pts, alpha in (([0, 140, 0, 100, 60, 62, 110, 92, 170, 50, 230, 88, 290, 60, 340, 95, 400, 72, 400, 140], 16),
                       ([0, 140, 0, 118, 90, 82, 150, 108, 210, 76, 270, 112, 330, 86, 400, 112, 400, 140], 22)):
        d.polygon([(pts[i] * sx, pts[i + 1] * sy) for i in range(0, len(pts), 2)], fill=(255, 255, 255, alpha))
    img.paste(over, (0, 0), over)
    return img


_LOGO = None


def paste_logo(img: Image.Image, x: int, y: int, size: int) -> None:
    """The site logo (docs/icons/icon-512.png, rendered from docs/favicon.svg)."""
    global _LOGO
    if _LOGO is None:
        _LOGO = Image.open(DOCS / "icons" / "icon-512.png").convert("RGBA")
    logo = _LOGO.resize((size * SS, size * SS), Image.LANCZOS)
    img.paste(logo, (x * SS, y * SS), logo)


def draw_map(img: Image.Image, raw: dict, box: tuple) -> bool:
    """Runs (by difficulty) and lifts, fitted into box = (x0, y0, x1, y1) in 1x px."""
    runs = [r for r in raw.get("runs", []) if is_downhill(r) and r.get("geom")]
    lifts = [l for l in raw.get("lifts", []) if l.get("geom")]
    pts = [p for f in runs + lifts for part in f["geom"] for p in part]
    if len(pts) < 2:
        return False
    lat0 = math.radians(sum(p[1] for p in pts) / len(pts))
    k = math.cos(lat0)
    xs, ys = [p[0] * k for p in pts], [-p[1] for p in pts]
    minx, maxx, miny, maxy = min(xs), max(xs), min(ys), max(ys)
    bw, bh = box[2] - box[0], box[3] - box[1]
    scale = min(bw / max(maxx - minx, 1e-9), bh / max(maxy - miny, 1e-9))
    ox = box[0] + (bw - (maxx - minx) * scale) / 2
    oy = box[1] + (bh - (maxy - miny) * scale) / 2
    proj = lambda p: ((ox + (p[0] * k - minx) * scale) * SS, (oy + (-p[1] - miny) * scale) * SS)
    d = ImageDraw.Draw(img)
    # Line width follows the resort size a little so tiny areas don't look empty.
    n = sum(len(part) for f in runs for part in f["geom"])
    lw = 3.2 if n < 1500 else 2.4 if n < 6000 else 1.7
    for l in lifts:
        for part in l["geom"]:
            if len(part) > 1:
                d.line([proj(p) for p in part], fill=LIFT_COLOR, width=int(1.3 * SS))
    order = ["other", "novice", "easy", "intermediate", "freeride", "extreme", "advanced", "expert", "double"]
    shown = lambda r: shown_difficulty(r.get("difficulty"), raw.get("run_convention"))
    for r in sorted(runs, key=lambda r: order.index(shown(r)) if shown(r) in order else 0):
        color = DIFF_COLORS.get(shown(r), DIFF_COLORS["other"])
        for part in r["geom"]:
            if len(part) > 1:
                line = [proj(p) for p in part]
                d.line(line, fill=(8, 20, 36), width=int((lw + 2.2) * SS), joint="curve")
                d.line(line, fill=color, width=int(lw * SS), joint="curve")
    return True


def wrap(text: str, fnt, max_w: int) -> list[str]:
    # Break at spaces and after "/" ("Verbier/La Tzoumaz/Nendaz..." is one word).
    words, lines, cur = re.findall(r"[^\s/]+/?|/", text), [], ""
    for w in words:
        trial = cur + w if cur.endswith("/") or not cur else cur + " " + w
        if fnt.getlength(trial) <= max_w * SS or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def fit_title(text: str, max_w: int, max_lines: int = 3):
    for size in (92, 84, 76, 68, 60, 54, 48, 42):
        f = font(BARLOW, size, text)
        lines = wrap(text, f, max_w)
        if len(lines) <= max_lines and all(f.getlength(l) <= max_w * SS for l in lines):
            return f, lines, size
    f = font(BARLOW, 42, text)
    lines = wrap(text, f, max_w)[:max_lines]
    return f, lines, 42


def chips(d: ImageDraw.ImageDraw, x: int, y: int, items: list[str], max_x: int) -> None:
    f = font(PLEX_B, 22)
    for t in items:
        tw = f.getlength(t) / SS
        if x + tw + 32 > max_x:
            break
        d.rounded_rectangle([x * SS, y * SS, (x + tw + 28) * SS, (y + 44) * SS], radius=22 * SS, fill=(255, 255, 255, 38))
        d.text(((x + 14) * SS, (y + 22) * SS), t, font=f, fill="#ffffff", anchor="lm")
        x += tw + 38


def left_column(img: Image.Image, title: str, sub: str, stats: list[str], width: int, max_lines: int = 3) -> None:
    paste_logo(img, 60, 54, 46)
    d = ImageDraw.Draw(img, "RGBA")
    d.text((118 * SS, 77 * SS), "SKI INFO", font=font(PLEX_B, 24), fill=(255, 255, 255, 215), anchor="lm")
    f, lines, size = fit_title(title, width, max_lines)
    y = 150
    line_h = size * 1.02
    for line in lines:
        d.text((58 * SS, y * SS), line, font=f, fill="#ffffff")
        y += line_h
    if sub:
        sf = font(PLEX, 27, sub)
        sub_lines = wrap(sub, sf, width)[:1 if len(lines) >= 3 else 2]
        y += 12
        for line in sub_lines:
            d.text((60 * SS, y * SS), line, font=sf, fill=(214, 229, 247))
            y += 38
    chips(d, 60, min(500, max(468, round(y) + 22)), stats, 60 + width + 20)
    d.text((60 * SS, 560 * SS), "skiinfoapp.com", font=font(PLEX_B, 24), fill=(255, 255, 255, 230))


def finish(img: Image.Image, out: Path, thumb: bool = False) -> None:
    out.parent.mkdir(parents=True, exist_ok=True)
    img.resize((W, H), Image.LANCZOS).save(out, "JPEG", quality=84, optimize=True, progressive=True)
    if thumb:
        # Just the map panel, for the guide/ranking lists (/og/thumb/<slug>.jpg).
        t = out.parent / "thumb" / out.name
        t.parent.mkdir(parents=True, exist_ok=True)
        img.crop((646 * SS, 42 * SS, 1158 * SS, 588 * SS)).resize((144, 154), Image.LANCZOS).save(
            t, "JPEG", quality=82, optimize=True)


# Text on the images, per language (Spanish at /og/, English at /og/en/).
IMG_TX = {
    "es": {"km": "{0} km de pistas", "lifts": "{0} remontes", "resort": "Estación de esquí", "resort_in": "Estación de esquí en {0}",
           "home_title": "Mapas de pistas y previsión de nieve", "home_sub": "{0}+ estaciones de esquí en {1} países",
           "home_chips": ["Pendiente real", "Nieve a 7 días", "Gratis"]},
    "en": {"km": "{0} km of pistes", "lifts": "{0} lifts", "resort": "Ski resort", "resort_in": "Ski resort in {0}",
           "home_title": "Piste maps and snow forecasts", "home_sub": "{0}+ ski resorts in {1} countries",
           "home_chips": ["Real gradients", "7-day snow", "Free"]},
}
NUM = {"es": fmt, "en": fmt_en}


def station_images(raw: dict, metas: dict, outs: dict) -> None:
    """One image per language (outs: {lang: path}); the map is drawn once."""
    img = background()
    # Map panel on the right.
    panel = Image.new("RGBA", img.size, (0, 0, 0, 0))
    pd = ImageDraw.Draw(panel)
    pd.rounded_rectangle([640 * SS, 36 * SS, 1164 * SS, 594 * SS], radius=26 * SS, fill=(6, 18, 34, 120))
    img.paste(panel, (0, 0), panel)
    has_map = draw_map(img, raw, (672, 66, 1132, 564))
    if not has_map:
        paste_logo(img, 827, 240, 150)

    runs = [r for r in raw.get("runs", []) if is_downhill(r)]
    km = sum(r.get("length_m") or 0 for r in runs) / 1000
    lo, hi = raw.get("min_elevation_m"), raw.get("max_elevation_m")
    cc = raw.get("country_code")
    for i, (lang, out) in enumerate(outs.items()):
        tx, f = IMG_TX[lang], NUM[lang]
        country = metas[lang]["countries"].get(cc, (cc or "", ""))[0]
        name = short_name(display_name(raw.get("name") or "", raw.get("id"))) or raw.get("name") or ""
        # The fonts have no CJK glyphs: use a Latin form of the name when there is one.
        if any(ord(c) >= 0x2E80 for c in name):
            name = latin_name(raw.get("name") or "", False) or tx["resort_in"].format(raw.get("region") or country)
        name = name or tx["resort"]
        place = ", ".join(p for p in [raw.get("region"), country] if p)
        stats = []
        if km >= 0.5:
            stats.append(tx["km"].format(f(round(km))))
        if raw.get("lifts"):
            stats.append(tx["lifts"].format(len(raw["lifts"])))
        if lo is not None and hi is not None:
            stats.append(f"{f(round(lo))}–{f(round(hi))} m")
        page_img = img.copy()
        left_column(page_img, name, place, stats, 540)
        finish(page_img, out, thumb=(i == 0))


def home_image(stations: list, outs: dict) -> None:
    """Generic image: title + a grid of six of the biggest resorts' piste maps."""
    img = background()
    top = sorted(stations, key=lambda s: -(s.get("pisteKm") or 0))
    # Mid-sized, compact resorts draw the clearest mini maps (the biggest
    # conglomerates spread over whole valleys and come out as specks).
    def compact(s):
        try:
            raw = json.loads((DOCS / "data" / f"{s['id']}.json").read_text(encoding="utf-8"))
        except OSError:
            return False
        pts = [p for r in raw.get("runs", []) for part in r.get("geom") or [] for p in part]
        if not pts:
            return False
        k = math.cos(math.radians(pts[0][1]))
        w = (max(p[0] for p in pts) - min(p[0] for p in pts)) * 111 * k
        h = (max(p[1] for p in pts) - min(p[1] for p in pts)) * 111
        return max(w, h) < 9
    mid = [s for s in top if 60 <= (s.get("pisteKm") or 0) <= 260]
    picks = ([s for s in mid if s.get("country") in ("ES", "AD") and compact(s)][:3]
             + [s for s in mid if s.get("country") in ("FR", "AT", "CH", "IT") and compact(s)][:3])
    panel = Image.new("RGBA", img.size, (0, 0, 0, 0))
    pd = ImageDraw.Draw(panel)
    cells = []
    for i in range(6):
        cx, cy = 640 + (i % 3) * 178, 40 + (i // 3) * 278
        pd.rounded_rectangle([cx * SS, cy * SS, (cx + 166) * SS, (cy + 266) * SS], radius=20 * SS, fill=(6, 18, 34, 120))
        cells.append((cx + 12, cy + 12, cx + 154, cy + 254))
    img.paste(panel, (0, 0), panel)
    for s, box in zip(picks, cells):
        try:
            raw = json.loads((DOCS / "data" / f"{s['id']}.json").read_text(encoding="utf-8"))
        except OSError:
            continue
        draw_map(img, raw, box)
    n = len(stations)
    countries = len({s.get("country") or "ES" for s in stations})
    for lang, out in outs.items():
        tx = IMG_TX[lang]
        hundreds = f"{n // 100 * 100:,}".replace(",", ".") if lang == "es" else f"{n // 100 * 100:,}"
        page_img = img.copy()
        left_column(page_img, tx["home_title"], tx["home_sub"].format(hundreds, countries), tx["home_chips"], 540, max_lines=2)
        finish(page_img, out)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--only", nargs="*", help="only these station slugs (for testing)")
    args = ap.parse_args()
    meta = load_app_metadata(read_app_sources(DOCS))
    metas = {"es": meta, "en": localized_meta(meta, load_i18n(DOCS))}
    slugs = json.loads((DOCS / "slugs.json").read_text(encoding="utf-8"))
    dirs = {"es": DOCS / "og", "en": DOCS / "og" / "en"}
    home_image(meta["stations"], {lang: d / "ski-info.jpg" for lang, d in dirs.items()})
    count = 0
    for s in meta["stations"]:
        slug = slugs.get(s["id"])
        if not slug or (args.only and slug not in args.only):
            continue
        raw = json.loads((DOCS / "data" / f"{s['id']}.json").read_text(encoding="utf-8"))
        station_images(raw, metas, {lang: d / f"{slug}.jpg" for lang, d in dirs.items()})
        count += 1
    print(f"{count} stations x {len(dirs)} languages of share images + ski-info.jpg")


if __name__ == "__main__":
    main()
