#!/usr/bin/env bash
# Uso: tools/render.sh VIDEO_ORIGINAL.mp4 FONTS_DIR
# FONTS_DIR precisa de: PlayfairDisplay*.ttf, Montserrat*.ttf, NotoSerif.ttf, NotoSerif-Italic.ttf, NotoSans.ttf (Google Fonts)
set -euo pipefail
V="$1"; FD="$2"; R="$(cd "$(dirname "$0")/.." && pwd)"; OV="$(mktemp -d)"
export LOGO="$R/assets/logo_bblips_mask.png"
[ -f "$LOGO" ] || python3 -I "$R/tools/logo_mask.py" "$R/assets/logo_bblips_original.jpg" "$LOGO"
python3 -I "$R/tools/overlays.py" "$FD" "$OV"
M=$(ffmpeg -hide_banner -i "$V" -af highpass=f=70,loudnorm=I=-14:TP=-1.5:LRA=11:print_format=json -f null - 2>&1 | sed -n '/^{/,/^}/p')
g(){ echo "$M" | python3 -c "import json,sys;print(json.load(sys.stdin)['$1'])"; }
LN="loudnorm=I=-14:TP=-1.5:LRA=11:measured_I=$(g input_i):measured_TP=$(g input_tp):measured_LRA=$(g input_lra):measured_thresh=$(g input_thresh):offset=$(g target_offset):linear=true"
fo(){ echo "format=rgba,fade=t=in:st=$1:d=0.35:alpha=1,fade=t=out:st=$(echo "$2-0.35"|bc):d=0.35:alpha=1"; }
Z="if(between(t,9.6,14),1.07,if(between(t,18.3,23),1.10,if(between(t,26,29.3),1.06,1)))"
FC="[0:v]scale=w='trunc(720*$Z/2)*2':h='trunc(1280*$Z/2)*2':eval=frame:flags=bicubic,crop=720:1280:(iw-720)/2:(ih-1280)*0.35,eq=contrast=1.05:saturation=1.08:brightness=0.01,colorbalance=rs=0.03:bs=-0.02:rm=0.02,unsharp=5:5:0.5,setsar=1[base];
[1:v]$(fo 3.6 34.4)[b];[2:v]$(fo 3.8 9.8)[h];[3:v]$(fo 18.4 23.0)[p];[4:v]$(fo 23.3 26.8)[n];[5:v]$(fo 29.3 34.4)[c];[6:v]format=rgba,fade=t=in:st=34.5:d=0.4:alpha=1[e];
[base][b]overlay=enable='between(t,3.6,34.4)'[v1];[v1][h]overlay=enable='between(t,3.8,9.8)'[v2];[v2][p]overlay=enable='between(t,18.4,23)'[v3];[v3][n]overlay=enable='between(t,23.3,26.8)'[v4];[v4][c]overlay=enable='between(t,29.3,34.4)'[v5];[v5][e]overlay=enable='gte(t,34.5)',format=yuv420p[vout];
[0:a]highpass=f=70,$LN,alimiter=limit=0.8,afade=t=out:st=37.4:d=1,apad[aout]"
mkdir -p "$R/output"
ffmpeg -v error -y -i "$V" $(for n in brand hook product benefit cta end; do echo "-loop 1 -t 40.17 -i $OV/$n.png"; done) -filter_complex "$FC" -map "[vout]" -map "[aout]" -c:v libx264 -preset slow -crf 19 -profile:v high -r 30 -c:a aac -b:a 192k -ar 44100 -movflags +faststart -t 40.17 "$R/output/BB_Estetica_Avanzada_Hyaluron_Pen.mp4"
python3 -I "$R/tools/illustrated.py" "$FD" - | ffmpeg -v error -y -f rawvideo -pix_fmt rgb24 -s 1080x1920 -r 30 -i - -i "$V" -map 0:v -map 1:a -af "highpass=f=70,$LN,alimiter=limit=0.8,afade=t=out:st=37.4:d=1,apad" -c:v libx264 -preset slow -crf 18 -pix_fmt yuv420p -tune animation -c:a aac -b:a 192k -movflags +faststart -t 40.17 "$R/output/BB_Estetica_Avanzada_Hyaluron_Pen_Ilustrado.mp4"
rm -rf "$OV"

# ---- Versão curta (25 s, só pontos principais, sem o efeito sonoro da abertura) ----
AW="$(mktemp -d)"; ffmpeg -v error -y -i "$V" -vn -ac 2 -ar 44100 "$AW/orig.wav"; python3 -I "$R/tools/cut_audio.py" "$AW/orig.wav" "$AW/curto.wav"
M2=$(ffmpeg -hide_banner -i "$AW/curto.wav" -af highpass=f=70,loudnorm=I=-14:TP=-1.5:LRA=11:print_format=json -f null - 2>&1 | sed -n '/^{/,/^}/p')
h(){ echo "$M2" | python3 -c "import json,sys;print(json.load(sys.stdin)['$1'])"; }
LN2="loudnorm=I=-14:TP=-1.5:LRA=11:measured_I=$(h input_i):measured_TP=$(h input_tp):measured_LRA=$(h input_lra):measured_thresh=$(h input_thresh):offset=$(h target_offset):linear=true"
CURTO=1 python3 -I "$R/tools/illustrated.py" "$FD" - | ffmpeg -v error -y -f rawvideo -pix_fmt rgb24 -s 1080x1920 -r 30 -i - -i "$AW/curto.wav" -map 0:v -map 1:a -af "highpass=f=70,$LN2,alimiter=limit=0.8" -c:v libx264 -preset slow -crf 18 -pix_fmt yuv420p -tune animation -c:a aac -b:a 192k -movflags +faststart -t 25 "$R/output/BB_Hyaluron_Pen_Curto.mp4"
rm -rf "$AW"

# ---- Versão curta em estética editorial "estilo Claude" (mesmo áudio curto) ----
AW="$(mktemp -d)"; ffmpeg -v error -y -i "$V" -vn -ac 2 -ar 44100 "$AW/orig.wav"; python3 -I "$R/tools/cut_audio.py" "$AW/orig.wav" "$AW/curto.wav" >/dev/null
M3=$(ffmpeg -hide_banner -i "$AW/curto.wav" -af highpass=f=70,loudnorm=I=-14:TP=-1.5:LRA=11:print_format=json -f null - 2>&1 | sed -n '/^{/,/^}/p')
k(){ echo "$M3" | python3 -c "import json,sys;print(json.load(sys.stdin)['$1'])"; }
LN3="loudnorm=I=-14:TP=-1.5:LRA=11:measured_I=$(k input_i):measured_TP=$(k input_tp):measured_LRA=$(k input_lra):measured_thresh=$(k input_thresh):offset=$(k target_offset):linear=true"
python3 -I "$R/tools/claude_style.py" "$FD" - | ffmpeg -v error -y -f rawvideo -pix_fmt rgb24 -s 1080x1920 -r 30 -i - -i "$AW/curto.wav" -map 0:v -map 1:a -af "highpass=f=70,$LN3,alimiter=limit=0.8" -c:v libx264 -preset slow -crf 19 -pix_fmt yuv420p -tune animation -c:a aac -b:a 160k -movflags +faststart -t 25 "$R/output/BB_Hyaluron_Pen_Estilo_Claude.mp4"
rm -rf "$AW"
