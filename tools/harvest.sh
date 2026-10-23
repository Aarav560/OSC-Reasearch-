#!/usr/bin/env bash
# Harvest subtitles, metadata and frames for every video in research/manifest.tsv.
#
#   tools/harvest.sh [WORKDIR] [PARALLEL]
#
# Per video it writes (repo, small):
#   research/videos/<id>/meta.json        trimmed yt-dlp metadata (title, chapters, description, ...)
#   research/videos/<id>/transcript.txt   de-duplicated caption text with [mm:ss] stamps
#   research/videos/<id>/sheet-NN.jpg     contact sheets of storyboard frames with timestamps
#   research/videos/<id>/thumb.jpg        max-res thumbnail
# and keeps individual frames + raw files in WORKDIR (scratch, not committed).
#
# YouTube rejects most player clients from datacenter IPs with a bot check; the
# web_embedded client still serves captions, metadata and storyboards without cookies.
set -uo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
WORK="${1:-${TMPDIR:-/tmp}/osc-harvest}"
PAR="${2:-3}"
export ROOT WORK
mkdir -p "$WORK"

one() {
  id="$1"
  out="$ROOT/research/videos/$id"; w="$WORK/$id"
  mkdir -p "$out" "$w/frames"
  [ -f "$out/.done" ] && return 0
  ytargs=(--extractor-args "youtube:player_client=web_embedded" --no-progress --retries 5 --sleep-requests 1)
  url="https://www.youtube.com/watch?v=$id"

  # one caption track per request: asking for en-orig and en together trips HTTP 429
  for langs in "en-orig" "en,en-US,en-GB"; do
    [ -f "$w/$id.info.json" ] && ls "$w"/"$id".en*.vtt >/dev/null 2>&1 && break
    yt-dlp "${ytargs[@]}" --skip-download --write-info-json --write-subs --write-auto-subs \
      --sub-langs "$langs" --sub-format vtt -o "$w/$id.%(ext)s" "$url" >>"$w/log.txt" 2>&1
  done
  [ -f "$w/$id.info.json" ] || { echo "FAIL meta $id"; return 1; }
  python3 -I "$ROOT/tools/postprocess.py" meta "$w/$id.info.json" "$out/meta.json"
  vtt="$(ls "$w"/"$id".en-orig.vtt "$w"/"$id".en*.vtt 2>/dev/null | head -1)"
  if [ -n "$vtt" ]; then python3 -I "$ROOT/tools/postprocess.py" vtt "$vtt" "$out/transcript.txt"
  else echo "(no English captions available)" >"$out/transcript.txt"; fi

  # Frames: googlevideo answers 403 to this IP for every client, so frames come from
  # YouTube's storyboards (sb0: 160x90 tiles, one frame every few seconds) plus the
  # max-res thumbnail, all served from i.ytimg.com.
  if [ -z "$(ls "$w/frames" 2>/dev/null)" ]; then
    [ -f "$w/sb.mhtml" ] || yt-dlp "${ytargs[@]}" -f sb0 -o "$w/sb.%(ext)s" "$url" >>"$w/log.txt" 2>&1
    [ -f "$w/sb.mhtml" ] || { echo "FAIL storyboard $id"; return 1; }
    python3 -I "$ROOT/tools/postprocess.py" storyboard "$w/sb.mhtml" "$w/$id.info.json" "$w/frames"
  fi
  [ -f "$out/thumb.jpg" ] || yt-dlp "${ytargs[@]}" --skip-download --write-thumbnail --convert-thumbnails jpg \
      -o "$w/thumb.%(ext)s" "$url" >>"$w/log.txt" 2>&1 && cp "$w/thumb.jpg" "$out/thumb.jpg" 2>/dev/null
  rm -f "$out"/sheet-*.jpg
  python3 -I "$ROOT/tools/postprocess.py" sheets "$w/frames" "$out"
  touch "$out/.done"
  echo "OK $id"
}
export -f one
tail -n +2 "$ROOT/research/manifest.tsv" | cut -f1 | xargs -P "$PAR" -I{} bash -c 'one "$@"' _ {}
