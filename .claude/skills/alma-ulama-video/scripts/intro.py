"""Animated "עלמא ולמה?" intro: logo + episode title, sized to the theme song.

RULE: the logo AND the episode title are fully visible from frame 0
(well inside the first 0.5s), so the very first frame works as a thumbnail
and viewers who scroll in see what the episode is immediately.

usage: intro.py LOGO OUT_DIR --title "קאסר אל יהוד" [--subtitle "..."] [--title-size 82] [--dur 9.6]
"""
import argparse, math, os, random
from PIL import Image, ImageDraw, ImageFont, ImageFilter

ap = argparse.ArgumentParser()
ap.add_argument("logo"); ap.add_argument("out")
ap.add_argument("--title", required=True)
ap.add_argument("--subtitle", default="")
ap.add_argument("--title-size", type=int, default=0, help="0 = auto-fit to width")
ap.add_argument("--dur", type=float, default=9.6)
ap.add_argument("--font", default=os.path.join(os.path.dirname(__file__), "..", "assets", "fonts", "Heebo-Black-HebLatin.ttf"))
A = ap.parse_args()

W, H, FPS = 576, 1024, 30
N = int(FPS * A.dur)
os.makedirs(A.out, exist_ok=True)
FONT = A.font

logo = Image.open(A.logo).convert("RGBA")
LW = 560
logo = logo.resize((LW, int(logo.height * LW / logo.width)), Image.LANCZOS)

def clamp(x): return max(0.0, min(1.0, x))
def punch(t, start, amp=0.10, dur=0.45):
    """1.0 at t<=start, quick swell to 1+amp and settle back -> never hidden."""
    if t <= start: return 1.0
    k = (t - start) / dur
    if k >= 1: return 1.0
    return 1.0 + amp * math.sin(math.pi * k) * (1 - k * 0.3)

# background gradient + rotating rays + glow
grad = Image.new("RGB", (W, H)); gd = ImageDraw.Draw(grad)
top, bot = (255, 196, 77), (232, 93, 36)
for y in range(H):
    t = y / H
    gd.line([(0, y), (W, y)], fill=tuple(int(top[i] * (1 - t) + bot[i] * t) for i in range(3)))
R = 1400
rays = Image.new("L", (R, R), 0); rd = ImageDraw.Draw(rays)
for k in range(18):
    rd.pieslice([0, 0, R, R], k * 20, k * 20 + 10, fill=55)
rays = rays.filter(ImageFilter.GaussianBlur(3))
glow = Image.new("L", (W, H), 0)
ImageDraw.Draw(glow).ellipse([W / 2 - 300, 30, W / 2 + 300, 630], fill=150)
glow = glow.filter(ImageFilter.GaussianBlur(90))
random.seed(7)
sparks = [(random.uniform(0, W), random.uniform(0, H), random.uniform(0.6, 2.2), random.uniform(0, 6.28), random.uniform(4, 11)) for _ in range(38)]

def star(d, x, y, r, a):
    pts = []
    for i in range(8):
        rr = r if i % 2 == 0 else r * 0.38
        ang = a + i * math.pi / 4
        pts.append((x + rr * math.cos(ang), y + rr * math.sin(ang)))
    d.polygon(pts, fill=(255, 255, 235, 230))

def text_img(txt, size, fill, stroke, sw, shadow=True):
    f = ImageFont.truetype(FONT, size)
    bb = f.getbbox(txt, direction="rtl")
    w, h = bb[2] - bb[0] + sw * 2 + 20, bb[3] - bb[1] + sw * 2 + 24
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    if shadow:
        d.text((10 + sw - bb[0] + 5, 12 + sw - bb[1] + 7), txt, font=f, fill=(60, 20, 0, 140), direction="rtl", stroke_width=sw, stroke_fill=(60, 20, 0, 140))
    d.text((10 + sw - bb[0], 12 + sw - bb[1]), txt, font=f, fill=fill, direction="rtl", stroke_width=sw, stroke_fill=stroke)
    return im

t_small = text_img("הפרק של היום", 40, (255, 255, 255), (29, 53, 87), 6)
size = A.title_size or 118
while True:
    t_big = text_img(A.title, size, (255, 214, 10), (29, 53, 87), 10)
    if A.title_size or t_big.width <= W - 50 or size <= 50: break
    size -= 4
t_sub = None
if A.subtitle:
    ss = 38
    while True:
        ts_ = text_img(A.subtitle, ss, (29, 53, 87), (255, 255, 255), 5, shadow=False)
        if ts_.width + 40 <= W - 40 or ss <= 24: break
        ss -= 2
    t_sub = Image.new("RGBA", (ts_.width + 40, ts_.height + 8), (0, 0, 0, 0))
    ImageDraw.Draw(t_sub).rounded_rectangle([0, 0, t_sub.width - 1, t_sub.height - 1], radius=26, fill=(255, 255, 255, 235))
    t_sub.alpha_composite(ts_, (20, 0))

def paste_scaled(fr, im, cx, cy, s, rot=0):
    w, h = max(1, int(im.width * s)), max(1, int(im.height * s))
    t = im.resize((w, h), Image.LANCZOS)
    if rot: t = t.rotate(rot, resample=Image.BICUBIC, expand=True)
    fr.alpha_composite(t, (int(cx - t.width / 2), int(cy - t.height / 2)))

for i in range(N):
    t = i / FPS
    fr = grad.copy().convert("RGBA")
    r = rays.rotate(t * 12, resample=Image.BICUBIC)
    rc = r.crop((R // 2 - W // 2, R // 2 - 330, R // 2 - W // 2 + W, R // 2 - 330 + H))
    fr.paste((255, 255, 230), (0, 0), rc); fr.paste((255, 250, 220), (0, 0), glow)
    d = ImageDraw.Draw(fr)
    for (x, y, sp, ph, sz) in sparks:
        star(d, x, (y - t * sp * 40) % H, sz * (0.5 + 0.5 * math.sin(t * 4 * sp + ph)), t * sp)
    # everything is on screen from frame 0; only "punch" accents + gentle bob
    bob = math.sin(t * 2.2) * 7
    wob = math.sin(t * 9) * 3 * (1 - clamp(t / 0.6))
    paste_scaled(fr, logo, W / 2, 360 + bob, punch(t, 0.0, 0.08, 0.5), wob)
    paste_scaled(fr, t_small, W / 2, 700, punch(t, 0.10, 0.12))
    paste_scaled(fr, t_big, W / 2, 790, punch(t, 0.15, 0.14, 0.5) * (1 + 0.025 * math.sin(max(0, t - 0.7) * 6)))
    if t_sub is not None:
        paste_scaled(fr, t_sub, W / 2, 895, punch(t, 0.25, 0.10))
    if t > A.dur - 0.35:  # white flash into the episode
        k = clamp((t - (A.dur - 0.35)) / 0.35)
        fr.alpha_composite(Image.new("RGBA", (W, H), (255, 255, 255, int(255 * k))))
    fr.convert("RGB").save(f"{A.out}/f{i:04d}.png")
