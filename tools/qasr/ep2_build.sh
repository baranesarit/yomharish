#!/bin/bash
set -e
cd "$(dirname "$0")/.."
V=$1; LOGO=$2; OUT=$3; MUSIC=$4
read T END < <(python3 scripts/ep2_ass.py)
# cut filter
F=$(python3 -c "
import json;E=json.load(open('ep2/edit.json'));f='';c=''
for i,(a,b) in enumerate(E['segs']):
  f+=f'[0:v]trim={a}:{b},setpts=PTS-STARTPTS[v{i}];[0:a]atrim={a}:{b},asetpts=PTS-STARTPTS,afade=t=in:d=0.02,afade=t=out:st={b-a-0.03:.3f}:d=0.03[a{i}];';c+=f'[v{i}][a{i}]'
print(f+c+f'concat=n={len(E[\"segs\"])}:v=1:a=1[cv][ca]')")
[ -f ep2/intro.mp4 ] || { BIG="קאסר אל יהוד" BIGS=82 SUB="מעברות הירדן" python3 scripts/intro.py "$LOGO" ep2/intro_frames && ffmpeg -v error -y -framerate 30 -i ep2/intro_frames/f%04d.png -c:v libx264 -pix_fmt yuv420p -crf 18 ep2/intro.mp4; }
ffmpeg -v error -y -i "$V" -loop 1 -t $END -i "$LOGO" -filter_complex "$F;[1:v]scale=440:-1,format=rgba,fade=t=in:st=$T:d=0.3:alpha=1[lg];[cv]scale=576:-2,crop=576:1024,fps=30,setsar=1,tpad=stop_mode=clone:stop_duration=3.1,trim=0:$END,boxblur=12:2:enable='gte(t,$T)',eq=brightness=-0.15:enable='gte(t,$T)',fade=t=in:st=0:d=0.35:color=white[bg];[bg][lg]overlay=(W-w)/2:150:enable='gte(t,$T)',ass=ep2/captions.ass,format=yuv420p[v];[ca]aresample=48000,apad,atrim=0:$END[a]" -map "[v]" -map "[a]" -c:v libx264 -crf 20 -preset medium -c:a aac -b:a 160k ep2/main.mp4
TAIL=$(python3 -c "print(int((9.6+$T)*1000))")
ffmpeg -v error -y -i ep2/intro.mp4 -i ep2/main.mp4 -i "$MUSIC" -filter_complex "[0:v][1:v]concat=n=2:v=1:a=0[v];[2:a]aresample=48000,atrim=0:11.6,afade=t=out:st=10.4:d=1.2,volume=0.9[m];[2:a]aresample=48000,atrim=start=9.0,asetpts=PTS-STARTPTS,afade=t=in:d=0.05,volume=0.9,adelay=$TAIL|$TAIL[tail];[1:a]adelay=9600|9600[voice];[m][voice][tail]amix=inputs=3:duration=longest:normalize=0,loudnorm=I=-15:TP=-1.5[a]" -map "[v]" -map "[a]" -c:v libx264 -crf 20 -c:a aac -b:a 160k -movflags +faststart "$OUT"
