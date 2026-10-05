#!/usr/bin/env bash
# One "¿Qué estación de esquí es?" video, start to finish, in Claude's sandbox:
#   marketing/make_video.sh <name> <station-id> "<hint>" [more make_video.js options]
#   e.g. marketing/make_video.sh formigal 0f46917975b8dab5e541edf6469105c3c091ec22 "Pirineo aragonés"
# 1. a quick turn lists the satellite tiles the video needs (~3 min);
# 2. the fetch-tiles.yml workflow downloads them (the imagery isn't reachable
#    from the sandbox) and commits them; they're pulled here (~2 min);
# 3. the frames: the map alone, 12 a second (~15 min);
# 4. ffmpeg interpolates them to 30 a second and lays the fixed texts on top;
# 5. commits marketing/videos/<name>.mp4 (+ a preview jpg) and removes the tiles.
set -euo pipefail
NAME=$1 STATION=$2 HINT=$3; shift 3
cd "$(dirname "$0")/.."
BRANCH=${BRANCH:-claude/ski-stations-database-rhvohj}
WORK=${WORK:-/tmp/video-$NAME}
SECONDS_ARG=20
for ((i = 1; i <= $#; i++)); do [ "${!i}" = "--seconds" ] && { j=$((i + 1)); SECONDS_ARG=${!j}; }; done
export CHROMIUM_PATH=${CHROMIUM_PATH:-/opt/pw-browsers/chromium} NODE_PATH=${NODE_PATH:-/opt/node22/lib/node_modules}
export DEM_DIR=$WORK/dem
FF=$(python3 -c "import imageio_ffmpeg; print(imageio_ffmpeg.get_ffmpeg_exe())" 2>/dev/null) || {
  pip install -q imageio-ffmpeg; FF=$(python3 -c "import imageio_ffmpeg; print(imageio_ffmpeg.get_ffmpeg_exe())"); }
mkdir -p "$WORK" marketing/tiles marketing/videos
curl -s -o /dev/null localhost:8903 || (cd docs && (setsid nohup python3 -m http.server 8903 >/dev/null 2>&1 &)); sleep 1
"$FF" -y -loglevel error -f lavfi -i color=c=0x6f7560:s=256x256 -frames:v 1 "$WORK/fake.jpg"
push() { for i in 1 2 3 4; do git fetch -q origin "$BRANCH" && git rebase -q "origin/$BRANCH" && git push -q origin "HEAD:$BRANCH" && return 0; sleep $((2 ** i)); done; return 1; }

echo "== 1. tiles needed"
TILE_LOG=marketing/tiles/$NAME.txt FAKE_TILE=$WORK/fake.jpg node marketing/make_video.js --station "$STATION" --out "$WORK/list" --list-tiles 16 "$@"
echo "$(wc -l < "marketing/tiles/$NAME.txt") tiles"

echo "== 2. downloading them (GitHub Actions)"
# Tiles already here (marketing/tiles/<name>/, e.g. from an earlier try) are kept.
missing() { while read -r k; do [ -f "marketing/tiles/$NAME/$k.jpg" ] || echo "$k"; done < "marketing/tiles/$NAME.txt"; }
git add "marketing/tiles/$NAME.txt"
git commit -q -m "Video: satellite tiles needed for $NAME" || true
if [ -n "$(missing)" ]; then
  push
  [ -d "marketing/tiles/$NAME" ] && mv "marketing/tiles/$NAME" "$WORK/tiles-kept"
  ok=
  for try in 1 2 3; do
    since=$(date -u +%Y-%m-%dT%H:%M:%SZ)
    gh api -X POST "repos/Sospi01/SKI-APP/actions/workflows/fetch-tiles.yml/dispatches" -f "ref=$BRANCH" -f "inputs[name]=$NAME" >/dev/null
    state=
    for i in $(seq 1 80); do   # up to 20 min
      sleep 15
      state=$(gh api "repos/Sospi01/SKI-APP/actions/workflows/fetch-tiles.yml/runs?per_page=5&created=>=$since" \
        --jq '[.workflow_runs[]] | sort_by(.created_at) | last | "\(.status) \(.conclusion)"' 2>/dev/null || true)
      case "$state" in "completed success") ok=1; break ;; completed*) break ;; esac
    done
    [ -n "$ok" ] && break
    echo "tile download didn't work ($state), trying again"
  done
  [ -n "$ok" ] || { echo "the tile download failed 3 times: try again later"; exit 1; }
  git fetch -q origin "$BRANCH"
  git rebase -q "origin/$BRANCH"
  [ -d "$WORK/tiles-kept" ] && { cp -n "$WORK/tiles-kept/"* "marketing/tiles/$NAME/" 2>/dev/null || true; rm -rf "$WORK/tiles-kept"; }
fi
echo "$(ls "marketing/tiles/$NAME" | wc -l) tiles here, $(missing | wc -l) missing"

echo "== 3. frames"
rm -rf "$WORK/frames"
TILE_DIR=marketing/tiles/$NAME FAKE_TILE=$WORK/fake.jpg node marketing/make_video.js --station "$STATION" --hint "$HINT" --out "$WORK" "$@"

echo "== 4. mp4"
T=$SECONDS_ARG
"$FF" -y -loglevel error -framerate 12 -i "$WORK/frames/%04d.jpg" -loop 1 -i "$WORK/overlay.png" -loop 1 -i "$WORK/outro.png" \
  -filter_complex "[0]minterpolate=fps=30:mi_mode=mci:mc_mode=aobmc:me_mode=bidir:vsbmc=1,scale=1080:1920:flags=lanczos[m];[m][1]overlay=enable='lt(t,$T-2.5)'[a];[a][2]overlay=enable='gte(t,$T-2.5)'" \
  -t "$T" -r 30 -c:v libx264 -crf 23 -pix_fmt yuv420p -movflags +faststart "marketing/videos/$NAME.mp4"
"$FF" -y -loglevel error -ss 1 -i "marketing/videos/$NAME.mp4" -frames:v 1 -q:v 3 "marketing/videos/$NAME-preview.jpg"
ls -la "marketing/videos/$NAME.mp4"

echo "== 5. commit"
git rm -rq --ignore-unmatch "marketing/tiles/$NAME" "marketing/tiles/$NAME.txt"; rm -rf "marketing/tiles/$NAME"
git add "marketing/videos/$NAME.mp4" "marketing/videos/$NAME-preview.jpg"
git commit -q -m "Video: $NAME 'which ski resort is it?' for TikTok"
push
echo "done: marketing/videos/$NAME.mp4"
