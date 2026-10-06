#!/usr/bin/env bash
# The home page's pictures, in Claude's sandbox (same machinery as make_video.sh):
# - docs/img/home/<id>.jpg: a 3D still of each popular station (the home's
#   cards and "Tu estación"), 600x500, names on, the app's framing;
# - docs/img/home/hero.mp4 + hero.jpg: the web hero, Formigal turning slowly.
#   marketing/make_home_images.sh [ids...]     (default: every POPULAR station in index.html)
# Satellite tiles are fetched by the fetch-tiles.yml workflow in one go (list
# "home"), then removed again.
set -euo pipefail
cd "$(dirname "$0")/.."
BRANCH=${BRANCH:-claude/ski-stations-database-rhvohj}
WORK=${WORK:-/tmp/home-images}
HERO=${HERO:-0f46917975b8dab5e541edf6469105c3c091ec22}   # Formigal
NAME=home
export CHROMIUM_PATH=${CHROMIUM_PATH:-/opt/pw-browsers/chromium} NODE_PATH=${NODE_PATH:-/opt/node22/lib/node_modules}
export DEM_DIR=$WORK/dem
FF=$(python3 -c "import imageio_ffmpeg; print(imageio_ffmpeg.get_ffmpeg_exe())" 2>/dev/null) || {
  pip install -q imageio-ffmpeg; FF=$(python3 -c "import imageio_ffmpeg; print(imageio_ffmpeg.get_ffmpeg_exe())"); }
mkdir -p "$WORK/logs" marketing/tiles docs/img/home
curl -s -o /dev/null localhost:8903 || (cd docs && (setsid nohup python3 -m http.server 8903 >/dev/null 2>&1 &)); sleep 1
"$FF" -y -loglevel error -f lavfi -i color=c=0x6f7560:s=256x256 -frames:v 1 "$WORK/fake.jpg"
push() { for i in 1 2 3 4; do git fetch -q origin "$BRANCH" && git rebase -q "origin/$BRANCH" && git push -q origin "HEAD:$BRANCH" && return 0; sleep $((2 ** i)); done; return 1; }
STILL=(--width 600 --height 500 --scale 1 --zoom 0.5)
HEROV=(--width 960 --height 600 --scale 1.25 --zoom 0.5 --seconds 24)

if [ $# -gt 0 ]; then IDS=("$@"); else
  mapfile -t IDS < <(node -e '
    const html = require("fs").readFileSync("docs/index.html", "utf8");
    const a = html.indexOf("var POPULAR = {"), b = html.indexOf("};", a);
    console.log([...new Set(html.slice(a, b).match(/[0-9a-f]{40}/g))].join("\n"));')
fi
echo "${#IDS[@]} stations"

echo "== 1. tiles needed"
for id in "${IDS[@]}"; do
  [ -s "$WORK/logs/$id.txt" ] && continue
  TILE_LOG=$WORK/logs/$id.txt FAKE_TILE=$WORK/fake.jpg node marketing/make_video.js --station "$id" --out "$WORK/l" --list-tiles 1 "${STILL[@]}" >/dev/null
done
[ -s "$WORK/logs/hero.txt" ] || TILE_LOG=$WORK/logs/hero.txt FAKE_TILE=$WORK/fake.jpg node marketing/make_video.js --station "$HERO" --out "$WORK/l" --list-tiles 16 "${HEROV[@]}" >/dev/null
cat "$WORK"/logs/*.txt | sort -u | grep -E '^[0-9]+_[0-9]+_[0-9]+$' > "marketing/tiles/$NAME.txt"
echo "$(wc -l < "marketing/tiles/$NAME.txt") tiles"

echo "== 2. downloading them (GitHub Actions)"
missing() { while read -r k; do [ -f "marketing/tiles/$NAME/$k.jpg" ] || echo "$k"; done < "marketing/tiles/$NAME.txt"; }
git add "marketing/tiles/$NAME.txt"
git commit -q -m "Home images: satellite tiles needed" || true
if [ -n "$(missing)" ]; then
  push
  [ -d "marketing/tiles/$NAME" ] && mv "marketing/tiles/$NAME" "$WORK/tiles-kept"
  ok=
  for try in 1 2 3; do
    since=$(date -u +%Y-%m-%dT%H:%M:%SZ)
    gh api -X POST "repos/Sospi01/SKI-APP/actions/workflows/fetch-tiles.yml/dispatches" -f "ref=$BRANCH" -f "inputs[name]=$NAME" >/dev/null
    state=
    for i in $(seq 1 80); do
      sleep 15
      state=$(gh api "repos/Sospi01/SKI-APP/actions/workflows/fetch-tiles.yml/runs?per_page=5&created=>=$since" \
        --jq '[.workflow_runs[]] | sort_by(.created_at) | last | "\(.status) \(.conclusion)"' 2>/dev/null || true)
      case "$state" in "completed success") ok=1; break ;; completed*) break ;; esac
    done
    [ -n "$ok" ] && break
    echo "tile download didn't work ($state), trying again"
  done
  [ -n "$ok" ] || { echo "the tile download failed 3 times: try again later"; exit 1; }
  git fetch -q origin "$BRANCH"; git rebase -q "origin/$BRANCH"
  [ -d "$WORK/tiles-kept" ] && { cp -n "$WORK/tiles-kept/"* "marketing/tiles/$NAME/" 2>/dev/null || true; rm -rf "$WORK/tiles-kept"; }
fi
echo "$(ls "marketing/tiles/$NAME" | wc -l) tiles here, $(missing | wc -l) missing"

echo "== 3. stills"
for id in "${IDS[@]}"; do
  TILE_DIR=marketing/tiles/$NAME FAKE_TILE=$WORK/fake.jpg node marketing/make_video.js --station "$id" --out "$WORK/s" --still "docs/img/home/$id.jpg" "${STILL[@]}" | tail -1
done

echo "== 4. hero video"
rm -rf "$WORK/hero/frames"
TILE_DIR=marketing/tiles/$NAME FAKE_TILE=$WORK/fake.jpg node marketing/make_video.js --station "$HERO" --out "$WORK/hero" "${HEROV[@]}" | grep -v '^frame'
"$FF" -y -loglevel error -framerate 12 -i "$WORK/hero/frames/%04d.jpg" \
  -vf "minterpolate=fps=30:mi_mode=mci:mc_mode=aobmc:me_mode=bidir:vsbmc=1" -an -c:v libx264 -crf 28 -preset slow -pix_fmt yuv420p -movflags +faststart docs/img/home/hero.mp4
cp "$WORK/hero/frames/0001.jpg" docs/img/home/hero.jpg
ls -la docs/img/home | tail -3

echo "== 5. commit"
git rm -rq --ignore-unmatch "marketing/tiles/$NAME" "marketing/tiles/$NAME.txt"; rm -rf "marketing/tiles/$NAME"
git add docs/img/home
git commit -q -m "Home: 3D pictures of the popular stations and the hero video"
echo "done (not pushed)"
