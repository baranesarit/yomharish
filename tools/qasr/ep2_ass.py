import json
E=json.load(open("ep2/edit.json")); T=E["total"]; END=T+3.1
def ts(t): h=int(t//3600); m=int(t%3600//60); s=t%60; return f"{h}:{m:02d}:{s:05.2f}"
POP="{\\fscx55\\fscy55\\t(0,90,\\fscx112\\fscy112)\\t(90,160,\\fscx100\\fscy100)}"
RLM="‏"; LRM="‎"
head=open("qumran-captions.ass").read().split("[Events]")[0]
o=[head.rstrip(),"","[Events]","Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text"]
o.append(f"Dialogue: 5,{ts(0)},{ts(T)},Hook,,0,0,0,,{{\\fscx40\\fscy40\\t(0,180,\\fscx110\\fscy110)\\t(180,300,\\fscx100\\fscy100)}}מה הסוד של 12 האבנים\\Nמתוך הירדן???{RLM}")
o.append(f"Dialogue: 4,{ts(0.3)},{ts(4.6)},Tag,,0,0,0,,{{\\fad(250,300)\\fscx60\\fscy60\\t(0,200,\\fscx100\\fscy100)}}קאסר אל יהוד • מעברות הירדן{RLM}")
for s,e,t in E["caps"]: o.append(f"Dialogue: 1,{ts(s)},{ts(e)},Cap,,0,0,0,,{POP}{t}{RLM}")
POPE="\\fad(200,0)\\fscx40\\fscy40\\t(0,220,\\fscx108\\fscy108)\\t(220,340,\\fscx100\\fscy100)"
b=T+0.05
for d,sty,y,txt in [(0,"End2",620,"מוזמנים לעקוב אחרינו"+RLM),(0.25,"End",700,"באינסטגרם"+RLM),(0.4,"End2",765,LRM+"@sarita.baranes"+LRM),(0.6,"End",845,"ובטיקטוק"+RLM),(0.75,"End2",910,LRM+"@sarita.baranes"+LRM)]:
    o.append(f"Dialogue: 6,{ts(b+d)},{ts(END)},{sty},,0,0,0,,{{\\pos(288,{y}){POPE}}}{txt}")
open("ep2/captions.ass","w").write("\n".join(o)+"\n"); print(T,END)
