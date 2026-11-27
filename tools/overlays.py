import sys
from PIL import Image, ImageDraw, ImageFont
F=sys.argv[1]; OUT=sys.argv[2]
PF=F+"/PlayfairDisplay%5Bwght%5D.ttf"; PFI=F+"/PlayfairDisplay-Italic%5Bwght%5D.ttf"; MS=F+"/Montserrat%5Bwght%5D.ttf"
def font(p,s,w):
    f=ImageFont.truetype(p,s)
    try: f.set_variation_by_axes([w])
    except Exception: pass
    return f
W,H=720,1280
BLUSH=(232,170,178,235); ROSE=(196,110,128,255); CREAM=(255,248,244,240); INK=(58,40,46,255); GOLD=(201,163,107,255)
def spaced(d,xy,text,f,fill,sp):
    x,y=xy
    for ch in text:
        d.text((x,y),ch,font=f,fill=fill); x+=d.textlength(ch,font=f)+sp
def spaced_w(d,text,f,sp): return sum(d.textlength(c,font=f)+sp for c in text)-sp
def canvas(): return Image.new("RGBA",(W,H),(0,0,0,0))
def shadow_text(d,xy,t,f,fill,anchor="mm"):
    d.text((xy[0]+2,xy[1]+3),t,font=f,fill=(0,0,0,110),anchor=anchor); d.text(xy,t,font=f,fill=fill,anchor=anchor)

# 1 brand bar
im=canvas(); d=ImageDraw.Draw(im)
f1=font(MS,19,600); t="BB · ESTÉTICA AVANZADA"; w=spaced_w(d,t,f1,4)
f2=font(PFI,26,500); t2="Bruna Borges"; w2=d.textlength(t2,font=f2)
bw=max(w,w2)+70; x0=(W-bw)/2
d.rounded_rectangle((x0,48,x0+bw,128),radius=40,fill=CREAM,outline=GOLD,width=2)
spaced(d,((W-w)/2,60),t,f1,INK,4); d.text((W/2,108),t2,font=f2,fill=ROSE,anchor="mm")
im.save(OUT+"/brand.png")

def card(lines,name,y=165,bg=BLUSH):
    im=canvas(); d=ImageDraw.Draw(im)
    widths=[d.textlength(t,font=f) for t,f,c in lines]; hs=[f.size*1.25 for t,f,c in lines]
    bw=max(widths)+80; bh=sum(hs)+44; x0=(W-bw)/2
    d.rounded_rectangle((x0+4,y+6,x0+bw+4,y+bh+6),radius=28,fill=(0,0,0,60))
    d.rounded_rectangle((x0,y,x0+bw,y+bh),radius=28,fill=bg)
    cy=y+22
    for (t,f,c),h in zip(lines,hs):
        d.text((W/2,cy+h/2),t,font=f,fill=c,anchor="mm"); cy+=h
    im.save(OUT+"/"+name+".png")
WHITE=(255,255,255,255)
card([("¿Miedo a las agujas?",font(PFI,50,600),WHITE),("Labios con volumen, sin agujas",font(MS,24,600),INK)],"hook")
card([("HYALURON PEN",font(MS,46,800),WHITE),("Volumen en labios · sin agujas",font(PFI,28,500),INK)],"product")
card([("Más sutil  ·  Más natural",font(PFI,40,600),INK)],"benefit",bg=CREAM)
card([("Reserva tu cita",font(PFI,46,600),WHITE),("Escríbenos por DM  ·  @brunaborgesestetic",font(MS,20,600),INK)],"cta")

# end card: cartela completa com o logo oficial (cobre a cartela original)
import os
from PIL import ImageFilter
g=Image.new("RGB",(1,H))
for y in range(H):
    k=y/(H-1); g.putpixel((0,y),tuple(int(a+(b-a)*k) for a,b in zip((60,44,58),(36,27,36))))
im=g.resize((W,H)).convert("RGBA"); d=ImageDraw.Draw(im)
m=Image.open(os.environ["LOGO"]).getchannel("A"); lw=380; m=m.resize((lw,int(m.height*lw/m.width)),Image.LANCZOS)
logo=Image.new("RGBA",m.size,(246,232,228,255)); logo.putalpha(m); im.alpha_composite(logo,((W-lw)//2,250))
d.text((W/2,690),"Bruna Borges",font=font(PFI,46,500),fill=(232,186,192,255),anchor="mm")
d.text((W/2,748),"Estética avanzada · Especialista en labios",font=font(MS,22,500),fill=(214,190,196,255),anchor="mm")
d.rounded_rectangle((W/2-180,815,W/2+180,887),radius=36,fill=(232,186,192,255))
d.text((W/2,851),"Reserva tu cita",font=font(MS,28,700),fill=INK,anchor="mm")
d.text((W/2,940),"@brunaborgesestetic",font=font(MS,25,500),fill=(214,190,196,255),anchor="mm")
im.save(OUT+"/end.png")
