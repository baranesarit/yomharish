import math, random, sys, os
from PIL import Image, ImageDraw, ImageFont, ImageFilter
W,H,FPS,DUR=576,1024,30,9.6
N=int(FPS*DUR); out=sys.argv[2]; os.makedirs(out,exist_ok=True)
logo=Image.open(sys.argv[1]).convert("RGBA")
LW=560; logo=logo.resize((LW,int(logo.height*LW/logo.width)),Image.LANCZOS)
FONT=os.path.expanduser("~/.fonts/heebo-hebrew-900-normal.ttf")
def ease_back(t,s=1.9): t-=1; return t*t*((s+1)*t+s)+1
def elastic(t):
    if t<=0: return 0
    if t>=1: return 1
    return 2**(-10*t)*math.sin((t-0.075)*(2*math.pi)/0.3)+1
def clamp(x): return max(0,min(1,x))
# background: gradient + rays (precompute big ray image, rotate per frame)
grad=Image.new("RGB",(W,H)); gd=ImageDraw.Draw(grad)
top=(255,196,77); bot=(232,93,36)
for y in range(H):
    t=y/H; gd.line([(0,y),(W,y)],fill=tuple(int(top[i]*(1-t)+bot[i]*t) for i in range(3)))
R=1400; rays=Image.new("L",(R,R),0); rd=ImageDraw.Draw(rays)
for k in range(18):
    a0=k*20; rd.pieslice([0,0,R,R],a0,a0+10,fill=55)
rays=rays.filter(ImageFilter.GaussianBlur(3))
glow=Image.new("L",(W,H),0); ImageDraw.Draw(glow).ellipse([W/2-300,330-300,W/2+300,330+300],fill=150); glow=glow.filter(ImageFilter.GaussianBlur(90))
random.seed(7)
sparks=[(random.uniform(0,W),random.uniform(0,H),random.uniform(0.6,2.2),random.uniform(0,6.28),random.uniform(4,11)) for _ in range(38)]
def star(d,x,y,r,a):
    pts=[]
    for i in range(8):
        rr=r if i%2==0 else r*0.38; ang=a+i*math.pi/4
        pts.append((x+rr*math.cos(ang),y+rr*math.sin(ang)))
    d.polygon(pts,fill=(255,255,235,int(230)))
def text_img(txt,size,fill,stroke,sw,shadow=True):
    f=ImageFont.truetype(FONT,size)
    bb=f.getbbox(txt,direction="rtl",features=["-kern"]) 
    w,h=bb[2]-bb[0]+sw*2+20,bb[3]-bb[1]+sw*2+24
    im=Image.new("RGBA",(w,h),(0,0,0,0)); d=ImageDraw.Draw(im)
    if shadow: d.text((10+sw-bb[0]+5,12+sw-bb[1]+7),txt,font=f,fill=(60,20,0,140),direction="rtl",stroke_width=sw,stroke_fill=(60,20,0,140))
    d.text((10+sw-bb[0],12+sw-bb[1]),txt,font=f,fill=fill,direction="rtl",stroke_width=sw,stroke_fill=stroke)
    return im
t_small=text_img("הפרק של היום",40,(255,255,255),(29,53,87),6)
BIG=os.environ.get("BIG","קומראן"); SUB=os.environ.get("SUB","המגילות הגנוזות שבמדבר"); BIGS=int(os.environ.get("BIGS","118"))
t_big=text_img(BIG,BIGS,(255,214,10),(29,53,87),10)
t_sub=text_img(SUB,38,(29,53,87),(255,255,255),5,shadow=False)
def paste_scaled(fr,im,cx,cy,s,alpha=1.0,rot=0):
    if s<=0.01 or alpha<=0: return
    w,h=max(1,int(im.width*s)),max(1,int(im.height*s))
    t=im.resize((w,h),Image.LANCZOS)
    if rot: t=t.rotate(rot,resample=Image.BICUBIC,expand=True)
    if alpha<1:
        a=t.getchannel("A").point(lambda v:int(v*alpha)); t.putalpha(a)
    fr.alpha_composite(t,(int(cx-t.width/2),int(cy-t.height/2)))
for i in range(N):
    t=i/FPS
    fr=grad.copy().convert("RGBA")
    r=rays.rotate(t*12,resample=Image.BICUBIC).crop(((R-W)//2,330-H//2+ (R-H)//2 - (330-H//2) ,0,0)) if False else rays.rotate(t*12,resample=Image.BICUBIC)
    rc=r.crop((R//2-W//2,R//2-330,R//2-W//2+W,R//2-330+H))
    fr.paste((255,255,230),(0,0),rc); fr.paste((255,250,220),(0,0),glow)
    d=ImageDraw.Draw(fr)
    for (x,y,sp,ph,sz) in sparks:
        yy=(y-t*sp*40)%H; tw=0.5+0.5*math.sin(t*4*sp+ph)
        star(d,x,yy,sz*tw,t*sp)
    # logo
    lt=clamp((t-0.15)/1.0); s=elastic(lt)
    bob=math.sin(max(0,t-1.2)*2.2)*8
    rot=(1-clamp(lt*1.4))*-14
    paste_scaled(fr,logo,W/2,360+bob,s,1.0,rot)
    # texts
    a=clamp((t-1.3)/0.45); paste_scaled(fr,t_small,W/2,700,ease_back(a) if a>0 else 0)
    b=clamp((t-1.6)/0.6); paste_scaled(fr,t_big,W/2,790,elastic(b)*(1+0.03*math.sin(max(0,t-2.2)*6)))
    c=clamp((t-2.3)/0.45)
    if c>0:
        sub=Image.new("RGBA",(t_sub.width+40,t_sub.height+8),(0,0,0,0)); ImageDraw.Draw(sub).rounded_rectangle([0,0,sub.width-1,sub.height-1],radius=26,fill=(255,255,255,235)); sub.alpha_composite(t_sub,(20,0))
        paste_scaled(fr,sub,W/2+(1-ease_back(c))*-W,895,1.0,c)
    # outro flash
    if t>DUR-0.35:
        k=clamp((t-(DUR-0.35))/0.35); fr.alpha_composite(Image.new("RGBA",(W,H),(255,255,255,int(255*k))))
    fr.convert("RGB").save(f"{out}/f{i:04d}.png")
