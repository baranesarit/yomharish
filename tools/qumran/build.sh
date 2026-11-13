#!/bin/bash
# usage: build.sh <video> <logo> <out.mp4> [music.mp3]
set -e
S=$(dirname "$0")/..; V=$1; LOGO=$2; OUT=$3; MUSIC=$4
cd "$S"
[ -f intro.mp4 ] || { python3 scripts/intro.py "$LOGO" intro_frames && ffmpeg -v error -y -framerate 30 -i intro_frames/f%04d.png -c:v libx264 -pix_fmt yuv420p -crf 18 intro.mp4; }
python3 scripts/caps.py 73.3 > qumran-captions.ass
ffmpeg -v error -y -i "$V" -loop 1 -t 73.3 -i "$LOGO" -filter_complex "[1:v]scale=440:-1,format=rgba,fade=t=in:st=70.3:d=0.3:alpha=1[lg];[0:v]scale=576:-2,crop=576:1024,fps=30,setsar=1,tpad=stop_mode=clone:stop_duration=3.1,trim=0:73.3,boxblur=12:2:enable='gte(t,70.3)',eq=brightness=-0.15:enable='gte(t,70.3)',fade=t=in:st=0:d=0.35:color=white[bg];[bg][lg]overlay=(W-w)/2:150:enable='gte(t,70.3)',ass=qumran-captions.ass,format=yuv420p[v];[0:a]aresample=48000,apad,atrim=0:73.3,afade=t=out:st=72.3:d=1[a]" -map "[v]" -map "[a]" -c:v libx264 -crf 20 -preset medium -c:a aac -b:a 160k main.mp4
if [ -n "$MUSIC" ]; then
  # intro music over intro (6s), tail ducked under the first seconds of Alma's video
  ffmpeg -v error -y -i intro.mp4 -i main.mp4 -i "$MUSIC" -filter_complex "[0:v][1:v]concat=n=2:v=1:a=0[v];[2:a]aresample=48000,atrim=0:11.6,afade=t=out:st=10.4:d=1.2,volume=0.9[m];[1:a]adelay=9600|9600[voice];[m][voice]amix=inputs=2:duration=longest:normalize=0,loudnorm=I=-15:TP=-1.5[a]" -map "[v]" -map "[a]" -c:v libx264 -crf 20 -c:a aac -b:a 160k -movflags +faststart "$OUT"
else
  ffmpeg -v error -y -i intro.mp4 -i main.mp4 -filter_complex "anullsrc=r=48000:cl=stereo,atrim=0:9.6[s];[1:a]aresample=48000[ma];[s][ma]concat=n=2:v=0:a=1,loudnorm=I=-15:TP=-1.5[a];[0:v][1:v]concat=n=2:v=1:a=0[v]" -map "[v]" -map "[a]" -c:v libx264 -crf 20 -c:a aac -b:a 160k -movflags +faststart "$OUT"
fi
