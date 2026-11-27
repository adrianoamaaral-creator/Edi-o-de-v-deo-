#!/bin/bash
# Efeitos sonoros do vídeo "Como funcionam os ajustes" (gerados no ffmpeg) + junção com o vídeo.
# Uso: anim_ajustes_audio.sh VIDEO_SEM_AUDIO.mp4 SAIDA.mp4 DURACAO
set -e
V="$1"; OUT="$2"; DUR="$3"
D=$(mktemp -d)
cd "$D"
ffmpeg -loglevel error -f lavfi -i "anoisesrc=d=0.45:c=pink:a=0.5" -af "highpass=f=400,lowpass=f=5000,afade=t=in:d=0.25,afade=t=out:st=0.25:d=0.2" -ar 48000 whoosh.wav
ffmpeg -loglevel error -f lavfi -i "aevalsrc='0.8*sin(2*PI*(500+3000*exp(-30*t))*t)*exp(-25*t)':d=0.15:s=48000" pop.wav
ffmpeg -loglevel error -f lavfi -i "aevalsrc='0.5*(sin(2*PI*1318*t)+0.5*sin(2*PI*2637*t))*exp(-5*t)':d=0.9:s=48000" ding.wav
ffmpeg -loglevel error -f lavfi -i "aevalsrc='0.9*sin(2*PI*55*t)*exp(-7*t)+0.2*(random(0)*2-1)*exp(-30*t)':d=0.5:s=48000" impacto.wav
ffmpeg -loglevel error -f lavfi -i "aevalsrc='0.6*sin(2*PI*2200*t)*exp(-120*t)':d=0.04:s=48000" tique.wav
# som : tempo(s) : volume(dB)  — pico no quadro do movimento
EV="whoosh:0.0:-13 whoosh:3.15:-15 pop:5.2:-13 pop:6.6:-13 pop:8.0:-13 whoosh:10.2:-15 pop:12.5:-13 pop:13.9:-13 pop:15.3:-13 whoosh:17.2:-15 impacto:18.0:-8 whoosh:21.0:-15 tique:22.2:-12 ding:25.2:-13"
IN=""; FC=""; N=0
for e in $EV; do
  IFS=: read s t v <<< "$e"
  awk "BEGIN{exit !($t < $DUR)}" || continue
  IN="$IN -i $s.wav"
  ms=$(awk "BEGIN{printf \"%d\", $t*1000}")
  FC="$FC[$N:a]volume=${v}dB,adelay=${ms}|${ms},apad,atrim=0:${DUR}[a$N];"
  N=$((N+1))
done
MIX=""; for i in $(seq 0 $((N-1))); do MIX="$MIX[a$i]"; done
FC="$FC${MIX}amix=inputs=$N:normalize=0,atrim=0:${DUR},aformat=channel_layouts=stereo[a]"
ffmpeg -loglevel error -y $IN -filter_complex "$FC" -map "[a]" -ar 48000 sfx.wav
cd - >/dev/null
ffmpeg -loglevel error -y -i "$V" -i "$D/sfx.wav" -map 0:v -map 1:a -c:v copy -c:a aac -b:a 192k -shortest -movflags +faststart "$OUT"
rm -rf "$D"
