"""Tells Bing (and the other IndexNow engines; ChatGPT's search leans on
Bing) which pages changed in this deploy, so they don't wait to recrawl.

Run after build_seo_pages.py, from the repo root:
    python3 data-pipeline/scripts/indexnow.py [--cache .indexnow/hashes.json] [--dry-run]

A page counts as changed when its HTML differs from the last run's (hashes
kept in --cache, which the deploy workflow restores and saves), leaving out
what changes every day anyway: the snow forecast and the home's data. The
first run, with no cache, sends every page in the sitemap.
"""
import argparse, hashlib, json, re, sys, urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DOCS = ROOT / "docs"
HOST = "skiinfoapp.com"
KEY = "08aa4441f443c25748c0b352af960923"   # public by design: docs/<KEY>.txt proves we own the site
ENDPOINT = "https://api.indexnow.org/indexnow"
BATCH = 10000   # IndexNow's limit per request
DAILY = [re.compile(p, re.S) for p in (r'<section id="snow-section".*?</section>',
                                        r'<script id="home-data"[^>]*>.*?</script>')]


def page_file(url: str) -> Path:
    path = url.split(HOST, 1)[1].lstrip("/")
    return DOCS / path / "index.html" if not path or path.endswith("/") else DOCS / path


def digest(f: Path) -> str:
    s = f.read_text(encoding="utf-8")
    for rx in DAILY:
        s = rx.sub("", s)
    return hashlib.sha256(s.encode()).hexdigest()[:16]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--cache", default=".indexnow/hashes.json")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    urls = re.findall(r"<loc>(.*?)</loc>", (DOCS / "sitemap.xml").read_text(encoding="utf-8"))
    cache = Path(a.cache)
    old = json.loads(cache.read_text()) if cache.exists() else {}
    new, changed = {}, []
    for u in urls:
        f = page_file(u)
        if not f.exists():
            continue
        new[u] = digest(f)
        if old.get(u) != new[u]:
            changed.append(u)
    print(f"{len(changed)} of {len(new)} pages changed since the last run")
    if not a.dry_run:
        for i in range(0, len(changed), BATCH):
            body = json.dumps({"host": HOST, "key": KEY, "keyLocation": f"https://{HOST}/{KEY}.txt",
                               "urlList": changed[i:i + BATCH]}).encode()
            req = urllib.request.Request(ENDPOINT, data=body, headers={"Content-Type": "application/json; charset=utf-8"})
            try:
                with urllib.request.urlopen(req, timeout=60) as r:
                    print(f"IndexNow: {len(changed[i:i + BATCH])} URLs -> HTTP {r.status}")
            except Exception as ex:   # never fail the deploy for this; retry next time
                print(f"IndexNow failed: {ex}", file=sys.stderr)
                return 0
    cache.parent.mkdir(parents=True, exist_ok=True)
    if not a.dry_run:
        cache.write_text(json.dumps(new))
    return 0


if __name__ == "__main__":
    sys.exit(main())
