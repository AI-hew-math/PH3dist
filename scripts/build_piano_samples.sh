#!/usr/bin/env bash
# Real-piano note samples for the in-browser "Try it" player.
# Source: Salamander Grand Piano (Alexander Holm), CC-BY 3.0, hosted on tonejs.github.io.
# Downloads every 3 semitones C2..C7, trims to ~3s mono mp3 -> web/audio/piano/piano_<midi>.mp3.
set -e
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
OUT="$ROOT/web/audio/piano"; mkdir -p "$OUT"; rm -f "$OUT"/*.mp3
BASE="https://tonejs.github.io/audio/salamander"
declare -A MAP=( [36]=C2 [39]=Ds2 [42]=Fs2 [45]=A2 [48]=C3 [51]=Ds3 [54]=Fs3 [57]=A3 \
                 [60]=C4 [63]=Ds4 [66]=Fs4 [69]=A4 [72]=C5 [75]=Ds5 [78]=Fs5 [81]=A5 \
                 [84]=C6 [87]=Ds6 [90]=Fs6 [93]=A6 [96]=C7 )
for midi in "${!MAP[@]}"; do
  name="${MAP[$midi]}"; tmp="/tmp/sal_dl_$name.mp3"
  curl -s -m 40 --retry 3 -o "$tmp" "$BASE/$name.mp3"
  ffmpeg -y -i "$tmp" -t 3.2 -ac 1 -af "afade=t=out:st=2.9:d=0.3" \
    -codec:a libmp3lame -q:a 5 "$OUT/piano_$midi.mp3" </dev/null >/dev/null 2>&1
  rm -f "$tmp"
done
echo "piano samples ($(ls "$OUT"/*.mp3 | wc -l)) -> $OUT"
