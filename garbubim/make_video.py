#!/usr/bin/env python3
"""Render the Garbubim (sock-puppet) workshop reel: 1080x1920, 30fps.

Usage: python3 make_video.py <photos_dir> <out.mp4> [song.mp3]
Frames are drawn with Pillow (raqm handles Hebrew RTL) and piped to ffmpeg.
"""
import math, os, random, subprocess, sys
from PIL import Image, ImageDraw, ImageFilter, ImageFont

W, H, FPS = 1080, 1920, 30
FONT_DIR = os.path.expanduser("~/.fonts")
F900 = os.path.join(FONT_DIR, "Heebo-900.ttf")
F700 = os.path.join(FONT_DIR, "Heebo-700.ttf")

PHOTOS, OUT = sys.argv[1], sys.argv[2]
SONG = sys.argv[3] if len(sys.argv) > 3 else None

# (file, seconds, zoom0, zoom1, fx0, fx1, fy, caption-lines)
# fx/fy = focus point (0..1) of the crop window; landscape photos pan across.
SEQ = [
    ("1854d9ec", 4.0, 1.00, 1.06, 0.15, 0.55, 0.5, None),  # title over the room
    ("41d14732", 3.6, 1.00, 1.05, 0.10, 0.60, 0.5, ["כולם סביב", "השולחן"]),
    ("649adcca", 3.2, 1.05, 1.00, 0.70, 0.30, 0.5, ["שלושה דורות", "של יצירה"]),
    ("102aaa71", 3.4, 1.00, 1.12, 0.50, 0.50, 0.40, ["גרב, עיניים, נוצות", "וקצת דמיון"]),
    ("cec01ba6", 3.0, 1.00, 1.08, 0.40, 0.40, 0.45, ["וכל גרב"]),
    ("688b0502", 3.0, 1.08, 1.00, 0.50, 0.50, 0.45, ["הופכת לחבר חדש"]),
    ("3625c2dc", 3.2, 1.00, 1.08, 0.50, 0.50, 0.40, ["סבתא ונכדה", "יוצרות יחד"]),
    ("eccebdd3", 3.2, 1.08, 1.00, 0.50, 0.50, 0.45, None),
    ("076dae94", 3.0, 1.00, 1.08, 0.50, 0.50, 0.45, ["כל אחד"]),
    ("cd0e4599", 3.0, 1.08, 1.00, 0.30, 0.30, 0.40, ["עם בובה משלו"]),
    ("50594d64", 3.2, 1.00, 1.06, 0.20, 0.80, 0.5, None),
    ("0bdc0f66", 3.4, 1.00, 1.08, 0.55, 0.55, 0.40, ["והגרבובים", "יוצאים לעולם"]),
    ("b9f62075", 5.4, 1.00, 1.10, 0.55, 0.55, 0.45, None),  # finale
]
XF = 0.5  # crossfade seconds

YELLOW = (255, 214, 0)
PINK = (255, 92, 168)
BLUE = (64, 196, 255)
GREEN = (120, 220, 60)
ORANGE = (255, 140, 30)
POM = [YELLOW, PINK, BLUE, GREEN, ORANGE, (170, 110, 255)]


def font(path, size):
    return ImageFont.truetype(path, size, layout_engine=ImageFont.Layout.RAQM)


def ease(t):
    t = max(0.0, min(1.0, t))
    return t * t * (3 - 2 * t)


def back_out(t):
    t = max(0.0, min(1.0, t))
    c = 1.9
    return 1 + (c + 1) * (t - 1) ** 3 + c * (t - 1) ** 2


# ---------- photos ----------
_cache = {}


def load(name):
    if name not in _cache:
        im = Image.open(os.path.join(PHOTOS, name + "-image.jpg")).convert("RGB")
        # scale so the photo covers the frame at zoom 1.0
        s = max(W / im.width, H / im.height)
        im = im.resize((round(im.width * s * 1.15), round(im.height * s * 1.15)), Image.LANCZOS)
        _cache[name] = (im, s * 1.15)
    return _cache[name]


def photo_frame(item, t):
    name, dur, z0, z1, fx0, fx1, fy, _ = item
    im, _s = load(name)
    p = ease(t / dur)
    z = z0 + (z1 - z0) * p
    fx = fx0 + (fx1 - fx0) * p
    # crop window in the (oversized, 1.15x) image
    cover = max(W / im.width, H / im.height) * 1.15  # zoom 1.0 == cover
    cw, ch = W / (cover * z) * 1.15, H / (cover * z) * 1.15
    cw, ch = min(cw, im.width), min(ch, im.height)
    x = (im.width - cw) * fx
    y = (im.height - ch) * fy
    return im.resize((W, H), Image.BILINEAR, box=(x, y, x + cw, y + ch))


# ---------- overlays ----------
_grad = None


def bottom_gradient():
    global _grad
    if _grad is None:
        g = Image.new("L", (1, H))
        for yy in range(H):
            a = max(0.0, (yy - H * 0.55) / (H * 0.45))
            g.putpixel((0, yy), int(200 * a ** 1.4))
        _grad = g.resize((W, H))
    return _grad


def text_img(text, f, fill, stroke=10, stroke_fill=(20, 20, 40), shadow=True):
    d = ImageDraw.Draw(Image.new("RGBA", (1, 1)))
    l, tp, r, b = d.textbbox((0, 0), text, font=f, stroke_width=stroke, direction="rtl")
    pad = 30
    img = Image.new("RGBA", (r - l + pad * 2, b - tp + pad * 2), (0, 0, 0, 0))
    if shadow:
        sh = Image.new("RGBA", img.size, (0, 0, 0, 0))
        ImageDraw.Draw(sh).text((pad - l + 6, pad - tp + 10), text, font=f, fill=(0, 0, 0, 150),
                                stroke_width=stroke, stroke_fill=(0, 0, 0, 150), direction="rtl")
        img = Image.alpha_composite(img, sh.filter(ImageFilter.GaussianBlur(8)))
    ImageDraw.Draw(img).text((pad - l, pad - tp), text, font=f, fill=fill,
                             stroke_width=stroke, stroke_fill=stroke_fill, direction="rtl")
    return img


_tcache = {}


def cached_text(key, *a, **k):
    if key not in _tcache:
        _tcache[key] = text_img(*a, **k)
    return _tcache[key]


def paste_scaled(frame, img, cx, cy, scale, alpha=1.0, angle=0.0):
    if scale <= 0.01 or alpha <= 0.01:
        return
    im = img
    if abs(scale - 1) > 0.005:
        im = im.resize((max(1, int(im.width * scale)), max(1, int(im.height * scale))), Image.BILINEAR)
    if angle:
        im = im.rotate(angle, resample=Image.BICUBIC, expand=True)
    if alpha < 1:
        a = im.getchannel("A").point(lambda v: int(v * alpha))
        im = im.copy()
        im.putalpha(a)
    frame.alpha_composite(im, (int(cx - im.width / 2), int(cy - im.height / 2)))


def caption(frame, lines, t, dur, idx):
    f = font(F900, 104)
    colors = [(255, 255, 255), YELLOW]
    base_y = 1520 if len(lines) == 2 else 1600
    for i, line in enumerate(lines):
        start = 0.25 + i * 0.35
        k = (t - start) / 0.45
        if k <= 0:
            continue
        out = min(1.0, max(0.0, (dur - t) / 0.35))
        sc = back_out(k) if k < 1 else 1.0
        col = colors[(i + idx) % 2]
        img = cached_text(("cap", line, col), line, f, col)
        wob = math.sin((t + i) * 3.0) * 1.2
        paste_scaled(frame, img, W / 2, base_y + i * 140, sc, alpha=out, angle=wob)


class Pom:
    def __init__(self, rnd, burst=False):
        self.x = rnd.uniform(40, W - 40)
        self.y = rnd.uniform(H * 0.05, H * 0.95) if not burst else H + rnd.uniform(0, 600)
        self.r = rnd.uniform(14, 34)
        self.c = rnd.choice(POM)
        self.v = rnd.uniform(90, 260)
        self.ph = rnd.uniform(0, 6.28)


def pom_layer(frame, poms, t, alpha):
    if alpha <= 0:
        return
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    for p in poms:
        y = (p.y - p.v * t) % (H + 200) - 100
        x = p.x + math.sin(t * 2 + p.ph) * 25
        a = int(235 * alpha)
        d.ellipse((x - p.r, y - p.r, x + p.r, y + p.r), fill=p.c + (a,))
        d.ellipse((x - p.r * 0.45, y - p.r * 0.65, x - p.r * 0.05, y - p.r * 0.25),
                  fill=(255, 255, 255, int(110 * alpha)))
    frame.alpha_composite(lay)


def googly_eyes(frame, cx, cy, size, t):
    d = ImageDraw.Draw(frame)
    for dx in (-size * 1.05, size * 1.05):
        x = cx + dx
        d.ellipse((x - size, cy - size, x + size, cy + size), fill=(255, 255, 255, 255),
                  outline=(20, 20, 40, 255), width=6)
        px = math.sin(t * 2.3) * size * 0.35
        py = math.cos(t * 3.1) * size * 0.3
        pr = size * 0.48
        d.ellipse((x + px - pr, cy + py - pr, x + px + pr, cy + py + pr), fill=(20, 20, 40, 255))


def title_card(frame, t, dur):
    """Opening title: 'סדנת גרבובים' + 'ראש העין'."""
    dim = Image.new("RGBA", (W, H), (10, 10, 40, int(110 * min(1, t / 0.4) * min(1, (dur - t) / 0.4))))
    frame.alpha_composite(dim)
    out = min(1.0, max(0.0, (dur - t) / 0.4))
    googly_eyes_t = (t - 0.1) / 0.4
    if googly_eyes_t > 0:
        s = back_out(googly_eyes_t)
        eye = Image.new("RGBA", (W, 260), (0, 0, 0, 0))
        googly_eyes(eye, W / 2, 130, 95, t)
        paste_scaled(frame, eye, W / 2, 560, s, out)
    l1 = cached_text("t1", "סדנת", font(F900, 120), (255, 255, 255))
    l2 = cached_text("t2", "הגרבובים", font(F900, 200), YELLOW, stroke=14)
    l3 = cached_text("t3", "ראש העין", font(F700, 96), (255, 255, 255), stroke=9)
    for img, y, st in ((l1, 790, 0.45), (l2, 960, 0.7), (l3, 1150, 1.1)):
        k = (t - st) / 0.5
        if k > 0:
            paste_scaled(frame, img, W / 2, y, back_out(k), out, angle=math.sin(t * 2.5) * 1.5)
    # little pill under place name
    k = (t - 1.5) / 0.5
    if k > 0:
        pill = cached_text("t4", "ילדים · הורים · סבים וסבתות", font(F700, 58), (255, 255, 255),
                           stroke=6, stroke_fill=PINK)
        paste_scaled(frame, pill, W / 2, 1290, back_out(k), out)


def finale(frame, t, dur):
    k = (t - 0.5) / 0.5
    if k <= 0:
        return
    out = 1.0
    l1 = cached_text("f1", "ברוכים הבאים", font(F900, 104), (255, 255, 255))
    l2 = cached_text("f2", "לארץ הגרבובים", font(F900, 132), YELLOW, stroke=12)
    l3 = cached_text("f3", "השיר: ארץ הגרבובים", font(F700, 64), (255, 255, 255), stroke=7,
                     stroke_fill=BLUE)
    paste_scaled(frame, l1, W / 2, 1440, back_out(k), out)
    k2 = (t - 0.9) / 0.5
    if k2 > 0:
        paste_scaled(frame, l2, W / 2, 1590, back_out(k2), out, angle=math.sin(t * 2.5) * 1.5)
    k3 = (t - 1.6) / 0.5
    if k3 > 0:
        paste_scaled(frame, l3, W / 2, 1735, back_out(k3), out)


# ---------- timeline ----------
starts, acc = [], 0.0
for it in SEQ:
    starts.append(acc)
    acc += it[1] - XF
TOTAL = acc + XF
NF = int(TOTAL * FPS)
rnd = random.Random(7)
intro_poms = [Pom(rnd) for _ in range(26)]
final_poms = [Pom(rnd, burst=True) for _ in range(16)]


def render(n):
    t = n / FPS
    active = [i for i, s in enumerate(starts) if s <= t < s + SEQ[i][1]]
    base = None
    for i in active:
        lt = t - starts[i]
        fr = photo_frame(SEQ[i], lt)
        if base is None:
            base = fr
        else:
            a = ease(lt / XF)
            base = Image.blend(base, fr, a)
    frame = base.convert("RGBA")
    frame.alpha_composite(Image.new("RGBA", (W, H), (0, 0, 0, 0)), (0, 0))
    shade = Image.new("RGBA", (W, H), (0, 0, 0, 255))
    shade.putalpha(bottom_gradient())
    frame.alpha_composite(shade)

    i = active[-1]
    lt = t - starts[i]
    dur = SEQ[i][1]
    if i == 0:
        pom_layer(frame, intro_poms, t, min(1, (dur - lt) / 0.5))
        title_card(frame, lt, dur)
    elif i == len(SEQ) - 1:
        pom_layer(frame, final_poms, lt, min(1.0, lt / 0.5) * 0.9)
        finale(frame, lt, dur)
    elif SEQ[i][7]:
        # keep caption of the outgoing clip visible only until crossfade ends
        caption(frame, SEQ[i][7], lt, dur, i)
    # fade from / to black
    fade = min(1.0, t / 0.4, (TOTAL - t) / 0.8)
    if fade < 1:
        frame = Image.blend(Image.new("RGBA", (W, H), (0, 0, 0, 255)), frame, max(0, fade))
    return frame.convert("RGB")


if __name__ == "__main__":
    if os.environ.get("PREVIEW"):
        for sec in map(float, os.environ["PREVIEW"].split(",")):
            render(int(sec * FPS)).save(f"{OUT}_{sec:05.1f}.jpg", quality=85)
        sys.exit()
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
           "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-"]
    if SONG:
        afade = max(0, TOTAL - 2.0)
        cmd += ["-i", SONG, "-filter:a", f"afade=t=out:st={afade:.2f}:d=2", "-map", "0:v", "-map", "1:a",
                "-c:a", "aac", "-b:a", "192k", "-shortest"]
    cmd += ["-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p",
            "-movflags", "+faststart", "-t", f"{TOTAL:.2f}", OUT]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for n in range(NF):
        p.stdin.write(render(n).tobytes())
        if n % 150 == 0:
            print(f"frame {n}/{NF}", flush=True)
    p.stdin.close()
    p.wait()
    print("done", OUT, f"{TOTAL:.1f}s")
