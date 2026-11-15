"""Render a full "עלמא ולמה?" episode from an episode JSON.

usage: render.py EPISODE.json [--preview]   (--preview: also writes a contact sheet PNG next to the output)

Pipeline: intro (logo+title visible from frame 0, theme song) -> tightened
footage with pop-up Hebrew captions, hook box and location tag -> end card
(blurred freeze + logo + Instagram/TikTok handles + last line of the theme).
See SKILL.md for the episode JSON fields.
"""
import json, os, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.join(HERE, "..", "assets")
FONTDIR = os.path.join(ASSETS, "fonts")
W, H = 576, 1024
INTRO = 9.6            # theme song is 11.6s: 9.6s over the intro, last 2s fade under the first shot
THEME_LEN, LAST_LINE = 11.6, 9.0   # "עלמא ולמה?" last sung line starts at 9.0s in theme.mp3
END_CARD = 3.1
Y = "{\\c&H0000E5FF&}"; WH = "{\\c&H00FFFFFF&}"
RLM, LRM = "‏", "‎"

ep_path = sys.argv[1]
E = json.load(open(ep_path))
base = os.path.dirname(os.path.abspath(ep_path))
P = lambda p: p if os.path.isabs(p) else os.path.join(base, p)
work = P(E.get("workdir", "work_" + os.path.splitext(os.path.basename(ep_path))[0]))
os.makedirs(work, exist_ok=True)
logo = P(E.get("logo", os.path.join(ASSETS, "logo.png")))
theme = P(E.get("theme", os.path.join(ASSETS, "theme.mp3")))
video, out = P(E["video"]), P(E["out"])

def run(cmd): subprocess.run(cmd, check=True)
def dur(f): return float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", f]))

# ---------- words -> edited timeline -> caption chunks ----------
words = [w for s in json.load(open(P(E["words"]))) for w in s["words"]]
segs = E.get("segments") or [[0.0, dur(video)]]
fixes = E.get("fixes", {})
glue = set(E.get("glue", []))            # words that must stay on one caption with the next word
hl = set(h.strip(",.?!") for h in E.get("highlights", []))
maxch, maxw = E.get("max_chars", 13), E.get("max_words", 3)

t, items = 0.0, []
for a, b in segs:
    seg = []
    for w in words:
        if w["s"] >= a - 0.05 and w["e"] <= b + 0.15:
            txt = w["w"].strip().lstrip("‫‪-")
            txt = fixes.get(txt, txt)
            if txt: seg.append([txt, w["s"] - a + t, min(w["e"], b) - a + t])
    m = []
    for x in seg:
        if m and (m[-1][0].endswith("־") or m[-1][0] in glue):
            sep = "" if m[-1][0].endswith("־") else " "
            m[-1] = [m[-1][0] + sep + x[0], m[-1][1], x[2]]
        else:
            m.append(x)
    items.append(m); t += b - a
T = t

caps = []
for m in items:
    cur = []
    for i, x in enumerate(m):
        cur.append(x)
        txt = " ".join(c[0] for c in cur)
        nxt = m[i + 1] if i + 1 < len(m) else None
        if nxt is None or x[0][-1] in ",.?!" or len(txt) >= maxch or len(cur) >= maxw or nxt[1] - x[2] > 0.35:
            caps.append([cur[0][1], x[2], cur]); cur = []
for i, c in enumerate(caps):
    nx = caps[i + 1][0] if i + 1 < len(caps) else T
    c[1] = min(max(c[1], c[0] + 0.35), nx, c[1] + 0.5) if nx > c[0] else c[1]

def colour(tok):
    # highlight a whole token, or each highlighted word inside a glued token
    parts = tok.split(" ")
    if tok.strip(",.?!") in hl: return Y + tok + WH
    return " ".join(Y + p + WH if p.strip(",.?!") in hl else p for p in parts)

def ts(x):
    return f"{int(x // 3600)}:{int(x % 3600 // 60):02d}:{x % 60:05.2f}"

POP = "{\\fscx55\\fscy55\\t(0,90,\\fscx112\\fscy112)\\t(90,160,\\fscx100\\fscy100)}"
POPE = "\\fad(200,0)\\fscx40\\fscy40\\t(0,220,\\fscx108\\fscy108)\\t(220,340,\\fscx100\\fscy100)"
END = T + END_CARD
ass = ["[Script Info]", "ScriptType: v4.00+", f"PlayResX: {W}", f"PlayResY: {H}", "WrapStyle: 2", "ScaledBorderAndShadow: yes", "",
       "[V4+ Styles]",
       "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding",
       "Style: Cap,Heebo Black,52,&H00FFFFFF,&H00FFFFFF,&H00000000,&H96000000,0,0,0,0,100,100,0,0,1,4.5,3,2,30,30,250,-1",
       "Style: Hook,Heebo Black,40,&H00000000,&H00000000,&H0000E5FF,&H00000000,0,0,0,0,100,100,0,0,3,14,0,8,30,30,70,-1",
       "Style: Tag,Heebo Black,34,&H00FFFFFF,&H00FFFFFF,&H00573519,&H00000000,0,0,0,0,100,100,0,0,3,12,0,8,30,30,200,-1",
       "Style: End,Heebo Black,56,&H0000E5FF,&H0000E5FF,&H00573519,&H96000000,0,0,0,0,100,100,0,0,1,7,4,5,30,30,0,-1",
       "Style: End2,Heebo Black,40,&H00FFFFFF,&H00FFFFFF,&H00573519,&H96000000,0,0,0,0,100,100,0,0,1,6,3,5,30,30,0,-1", "",
       "[Events]", "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text"]
if E.get("hook"):
    ass.append(f"Dialogue: 5,{ts(0)},{ts(T)},Hook,,0,0,0,,{{\\fscx40\\fscy40\\t(0,180,\\fscx110\\fscy110)\\t(180,300,\\fscx100\\fscy100)}}{E['hook']}{RLM}")
if E.get("tag"):
    ass.append(f"Dialogue: 4,{ts(0.3)},{ts(4.6)},Tag,,0,0,0,,{{\\fad(250,300)\\fscx60\\fscy60\\t(0,200,\\fscx100\\fscy100)}}{E['tag']}{RLM}")
for s, e, cur in caps:
    ass.append(f"Dialogue: 1,{ts(s)},{ts(e)},Cap,,0,0,0,,{POP}{' '.join(colour(c[0]) for c in cur)}{RLM}")
hd = E.get("handles", {"instagram": "sarita.baranes", "tiktok": "sarita.baranes"})
card = [(0, "End2", 620, "מוזמנים לעקוב אחרינו" + RLM),
        (0.25, "End", 700, "באינסטגרם" + RLM), (0.4, "End2", 765, LRM + "@" + hd["instagram"] + LRM),
        (0.6, "End", 845, "ובטיקטוק" + RLM), (0.75, "End2", 910, LRM + "@" + hd["tiktok"] + LRM)]
for d, sty, y, txt in card:
    ass.append(f"Dialogue: 6,{ts(T + 0.05 + d)},{ts(END)},{sty},,0,0,0,,{{\\pos(288,{y}){POPE}}}{txt}")
ass_path = os.path.join(work, "captions.ass")
open(ass_path, "w").write("\n".join(ass) + "\n")
with open(os.path.join(work, "captions.txt"), "w") as f:
    for s, e, cur in caps: f.write(f"{s:6.2f}-{e:6.2f}  {' '.join(c[0] for c in cur)}\n")
print(f"edited footage {T:.1f}s (from {dur(video):.1f}s), {len(caps)} captions -> {work}/captions.txt")

# ---------- intro ----------
intro = os.path.join(work, "intro.mp4")
frames = os.path.join(work, "intro_frames")
cmd = [sys.executable, os.path.join(HERE, "intro.py"), logo, frames, "--title", E["title"], "--dur", str(INTRO)]
if E.get("subtitle"): cmd += ["--subtitle", E["subtitle"]]
if E.get("title_size"): cmd += ["--title-size", str(E["title_size"])]
run(cmd)
run(["ffmpeg", "-v", "error", "-y", "-framerate", "30", "-i", f"{frames}/f%04d.png", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18", intro])

# ---------- main footage ----------
f, c = "", ""
for i, (a, b) in enumerate(segs):
    f += (f"[0:v]trim={a}:{b},setpts=PTS-STARTPTS[v{i}];"
          f"[0:a]atrim={a}:{b},asetpts=PTS-STARTPTS,afade=t=in:d=0.02,afade=t=out:st={max(0, b - a - 0.03):.3f}:d=0.03[a{i}];")
    c += f"[v{i}][a{i}]"
f += c + f"concat=n={len(segs)}:v=1:a=1[cv][ca]"
esc = ass_path.replace(":", "\\:").replace("'", "\\'")
vf = (f"{f};[1:v]scale=440:-1,format=rgba,fade=t=in:st={T}:d=0.3:alpha=1[lg];"
      f"[cv]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},fps=30,setsar=1,"
      f"tpad=stop_mode=clone:stop_duration={END_CARD},trim=0:{END},"
      f"boxblur=12:2:enable='gte(t,{T})',eq=brightness=-0.15:enable='gte(t,{T})',fade=t=in:st=0:d=0.35:color=white[bg];"
      f"[bg][lg]overlay=(W-w)/2:150:enable='gte(t,{T})',ass='{esc}':fontsdir='{FONTDIR}',format=yuv420p[v];"
      f"[ca]aresample=48000,apad,atrim=0:{END}[a]")
main = os.path.join(work, "main.mp4")
run(["ffmpeg", "-v", "error", "-y", "-i", video, "-loop", "1", "-t", f"{END}", "-i", logo, "-filter_complex", vf,
     "-map", "[v]", "-map", "[a]", "-c:v", "libx264", "-crf", "20", "-preset", "medium", "-c:a", "aac", "-b:a", "160k", main])

# ---------- join + music ----------
tail = int((INTRO + T) * 1000)
af = (f"[0:v][1:v]concat=n=2:v=1:a=0[v];"
      f"[2:a]aresample=48000,atrim=0:{THEME_LEN},afade=t=out:st={THEME_LEN - 1.2}:d=1.2,volume=0.9[m];"
      f"[2:a]aresample=48000,atrim=start={LAST_LINE},asetpts=PTS-STARTPTS,afade=t=in:d=0.05,volume=0.9,adelay={tail}|{tail}[tail];"
      f"[1:a]adelay={int(INTRO * 1000)}|{int(INTRO * 1000)}[voice];"
      f"[m][voice][tail]amix=inputs=3:duration=longest:normalize=0,loudnorm=I=-15:TP=-1.5[a]")
run(["ffmpeg", "-v", "error", "-y", "-i", intro, "-i", main, "-i", theme, "-filter_complex", af,
     "-map", "[v]", "-map", "[a]", "-c:v", "libx264", "-crf", "20", "-c:a", "aac", "-b:a", "160k", "-movflags", "+faststart", out])
print(f"done: {out}  ({dur(out):.1f}s)")

if "--preview" in sys.argv:
    total = dur(out)
    pts = [0.0, 0.5, INTRO + 2] + [INTRO + T * k for k in (0.3, 0.6, 0.9)] + [total - 0.5]
    sel = "+".join(f"eq(n\\,{int(p * 30)})" for p in pts)
    run(["ffmpeg", "-v", "error", "-y", "-i", out, "-vf", f"select='{sel}',scale=192:-1,tile={len(pts)}x1", "-frames:v", "1", os.path.splitext(out)[0] + "_preview.png"])
    print("preview:", os.path.splitext(out)[0] + "_preview.png")
