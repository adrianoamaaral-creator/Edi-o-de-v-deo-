"""Vídeo ilustrado estilo stories (BBLips · Estética Avanzada). Uso: illustrated.py FONTS_DIR OUT_RAW_PIPE(stdout) [--preview DIR]"""
import sys, math
from PIL import Image, ImageDraw, ImageFont, ImageFilter
FD=sys.argv[1]; PREVIEW=sys.argv[3] if len(sys.argv)>3 else None
W,H,FPS,DUR=1080,1920,30,40.17
SERIF=FD+"/NotoSerif.ttf"; SERIFI=FD+"/NotoSerif-Italic.ttf"; SANS=FD+"/NotoSans.ttf"
def font(p,s,w=400):
    f=ImageFont.truetype(p,s)
    try: f.set_variation_by_axes([w,100])
    except Exception: pass
    return f
LIGHT=dict(bg=((248,236,231),(236,204,201)),ink=(58,36,48),rose=(140,74,94),soft=(110,80,92),bar=(140,74,94),circ=(239,211,210))
DARK=dict(bg=((52,38,50),(40,30,40)),ink=(246,232,228),rose=(232,186,192),soft=(214,190,196),bar=(240,222,218),circ=(74,54,68))
MX=97
def gradient(c1,c2):
    g=Image.new("RGB",(1,H)); 
    for y in range(H):
        k=y/(H-1); g.putpixel((0,y),tuple(int(c1[i]+(c2[i]-c1[i])*k) for i in range(3)))
    im=g.resize((W,H)).convert("RGBA")
    # leve vinheta diagonal
    ov=Image.new("L",(W,H),0); d=ImageDraw.Draw(ov); d.ellipse((-400,-300,W+200,H*0.7),fill=40); ov=ov.filter(ImageFilter.GaussianBlur(200))
    white=Image.new("RGBA",(W,H),(255,255,255,0)); white.putalpha(ov); return Image.alpha_composite(im,white)
def spaced(d,x,y,t,f,fill,sp):
    for ch in t: d.text((x,y),ch,font=f,fill=fill); x+=d.textlength(ch,font=f)+sp
def spaced_w(d,t,f,sp): return sum(d.textlength(c,font=f)+sp for c in t)-sp
def header(th):
    im=Image.new("RGBA",(W,H),(0,0,0,0)); d=ImageDraw.Draw(im)
    spaced(d,MX,150,"BBLIPS",font(SANS,22,700),th["rose"]+(255,),7)
    f=font(SANS,20,700); t="ESTÉTICA AVANZADA"; d.text((W-MX-d.textlength(t,font=f),152),t,font=f,fill=th["rose"]+(255,))
    d.line((MX,208,W-MX,208),fill=th["ink"]+(70,),width=2); return im
def text_layer(t,f,color,y,spacing=14):
    im=Image.new("RGBA",(W,H),(0,0,0,0)); d=ImageDraw.Draw(im)
    d.multiline_text((W/2,y),t,font=f,fill=color+(255,),anchor="ma",align="center",spacing=spacing)
    bb=im.getbbox(); return (im.crop(bb),bb[:2])
# ---------- ilustrações (desenhadas 2x e reduzidas) ----------
S2=2; IS=640
def icanvas(): im=Image.new("RGBA",(IS*S2,IS*S2),(0,0,0,0)); return im,ImageDraw.Draw(im)
def fin(im): return im.resize((IS,IS),Image.LANCZOS)
C=IS*S2/2
def P(x,y): return (C+x*S2,C+y*S2)
def catmull(pts,n=24,closed=True):
    out=[]; L=len(pts); rng=range(L) if closed else range(L-1)
    for i in rng:
        p0,p1,p2,p3=pts[(i-1)%L],pts[i],pts[(i+1)%L],pts[(i+2)%L]
        if not closed: p0=pts[max(i-1,0)]; p3=pts[min(i+2,L-1)]
        for k in range(n):
            t=k/n; t2=t*t; t3=t2*t
            out.append(tuple(0.5*((2*p1[j])+(-p0[j]+p2[j])*t+(2*p0[j]-5*p1[j]+4*p2[j]-p3[j])*t2+(-p0[j]+3*p1[j]-3*p2[j]+p3[j])*t3) for j in range(2)))
    return out
def star(d,x,y,r,fill):
    pts=[]
    for i in range(8):
        a=math.pi/4*i-math.pi/2; rr=r if i%2==0 else r*0.28; pts.append(P(x+rr*math.cos(a),y+rr*math.sin(a)))
    d.polygon(pts,fill=fill)
def rings(d,th,r=210):
    d.ellipse([*P(-r,-r),*P(r,r)],fill=th["circ"]+(255,))
    R=r+34; d.arc([*P(-R,-R),*P(R,R)],200,320,fill=th["rose"]+(200,),width=3*S2)
    d.arc([*P(-R,-R),*P(R,R)],20,140,fill=th["rose"]+(200,),width=3*S2)
    d.ellipse([*P(-r-8,-r-8),*P(r+8,r+8)],outline=th["rose"]+(60,),width=2*S2)
def lips(d,cx=0,cy=0,s=1.0,up=(176,104,124),lo=(200,138,154)):
    a=150*s; h=70*s
    upper=[(-a,0),(-a*0.6,-h*0.45),(-a*0.28,-h*0.78),(0,-h*0.5),(a*0.28,-h*0.78),(a*0.6,-h*0.45),(a,0),(a*0.5,h*0.06),(0,h*0.12),(-a*0.5,h*0.06)]
    lower=[(-a,0),(-a*0.5,h*0.12),(0,h*0.16),(a*0.5,h*0.12),(a,0),(a*0.6,h*0.55),(0,h*0.85),(-a*0.6,h*0.55)]
    d.polygon([P(cx+x,cy+y) for x,y in catmull(lower)],fill=lo+(255,))
    d.polygon([P(cx+x,cy+y) for x,y in catmull(upper)],fill=up+(255,))
    d.line([P(cx+x,cy+y) for x,y in catmull([(-a*0.95,0),(-a*0.5,h*0.09),(0,h*0.14),(a*0.5,h*0.09),(a*0.95,0)],closed=False)],fill=(150,82,102,255),width=3*S2)
    d.ellipse([*P(cx-a*0.25,cy+h*0.36),*P(cx+a*0.15,cy+h*0.5)],fill=(255,235,238,110))
def ico_lips(th):
    im,d=icanvas(); rings(d,th); lips(d,0,10); star(d,190,-170,22,th["rose"]+(255,)); star(d,-200,150,14,th["rose"]+(255,)); return fin(im)
def ico_volume(th):
    im,d=icanvas(); rings(d,th); lips(d,0,40,1.05)
    for x in (-90,0,90):
        d.line([P(x,-40),P(x,-140)],fill=th["rose"]+(255,),width=5*S2)
        d.polygon([P(x-18,-125),P(x+18,-125),P(x,-150)],fill=th["rose"]+(255,))
    star(d,200,-150,20,th["rose"]+(255,)); return fin(im)
def rot(pts,a,ox=0,oy=0):
    c,s=math.cos(a),math.sin(a); return [P(ox+x*c-y*s,oy+x*s+y*c) for x,y in pts]
def ico_syringe(th):
    im,d=icanvas(); rings(d,th); a=math.radians(-40); col=th["ink"]+(255,); w=5*S2
    d.polygon(rot([(-110,-28),(70,-28),(70,28),(-110,28)],a),outline=col,width=w)
    d.polygon(rot([(-60,-28),(70,-28),(70,28),(-60,28)],a),fill=th["rose"]+(90,))
    d.line(rot([(70,0),(170,0)],a),fill=col,width=3*S2)
    d.line(rot([(-110,0),(-170,0)],a),fill=col,width=w); d.line(rot([(-170,-30),(-170,30)],a),fill=col,width=w)
    d.line(rot([(-110,-50),(-110,50)],a),fill=col,width=w)
    for x in (-30,10,50): d.line(rot([(x,-28),(x,-10)],a),fill=col,width=2*S2)
    r=175; d.ellipse([*P(-r,-r),*P(r,r)],outline=(176,70,90,255),width=10*S2)
    d.line(rot([(-r,0),(r,0)],math.radians(45)),fill=(176,70,90,255),width=10*S2); return fin(im)
def ico_pen(th):
    im,d=icanvas(); rings(d,th); a=math.radians(-35)
    body=[(-190,-34),(110,-34),(110,34),(-190,34)]
    d.polygon(rot(body,a),fill=(214,120,146,255))
    d.polygon(rot([(-190,-34),(-120,-34),(-120,34),(-190,34)],a),fill=(150,70,96,255))
    d.polygon(rot([(110,-34),(160,-22),(160,22),(110,34)],a),fill=(90,80,90,255))
    d.polygon(rot([(160,-22),(195,-10),(195,10),(160,22)],a),fill=(160,160,170,255))
    d.line(rot([(-100,-14),(90,-14)],a),fill=(255,230,236,150),width=5*S2)
    star(d,-170,-150,22,th["rose"]+(255,)); star(d,175,150,15,th["rose"]+(255,)); return fin(im)
def ico_sparkle(th):
    im,d=icanvas(); rings(d,th); c=th["rose"]+(255,)
    star(d,-30,10,120,c); star(d,95,-95,55,c); star(d,90,110,32,c); star(d,-140,-120,24,c); return fin(im)
def ico_heart(th):
    im,d=icanvas(); rings(d,th)
    pts=[(16*math.sin(t)**3, -(13*math.cos(t)-5*math.cos(2*t)-2*math.cos(3*t)-math.cos(4*t))) for t in [i/200*2*math.pi for i in range(200)]]
    d.polygon([P(x*9,y*9-10) for x,y in pts],fill=(200,120,140,255))
    lips(d,0,-10,0.55,up=(255,236,238),lo=(255,246,247)); star(d,170,-150,22,th["rose"]+(255,)); star(d,-180,140,14,th["rose"]+(255,)); return fin(im)
def ico_final(th):
    im,d=icanvas(); rings(d,th); lips(d,0,10,1.0)
    for x,y,r in ((-170,-140,26),(185,-110,18),(150,165,22),(-185,130,14),(0,-175,12)): star(d,x,y,r,th["rose"]+(255,))
    return fin(im)
def ico_lotus(col):
    im,d=icanvas(); w=4*S2; c=col+(255,)
    def petal(ang,L,Wd):
        pts=catmull([(0,0),(Wd,-L*0.5),(0,-L),(-Wd,-L*0.5)],closed=True)
        a=math.radians(ang); d.line(rot(pts,a,0,90)+[rot(pts,a,0,90)[0]],fill=c,width=w,joint="curve")
    for ang,L,Wd in ((0,230,70),(-24,205,62),(24,205,62),(-50,170,55),(50,170,55),(-78,130,45),(78,130,45)): petal(ang,L,Wd)
    d.line([P(-200,95),P(200,95)],fill=c,width=w); return fin(im)
# ---------- slides ----------
TS=font(SERIF,84,400); TSs=font(SERIF,76,400); SUBI=font(SERIFI,44,400); BODY=font(SANS,38,400)
TS=font(SERIF,84,400); TSs=font(SERIF,78,400)
slides=[
 dict(t0=0.0,t1=7.3,th=LIGHT,title="Hyaluron Pen",sub="Labios con volumen,\nsin agujas",icon=ico_lips),
 dict(t0=7.3,t1=13.3,th=LIGHT,title="¿Quieres más\nvolumen?",body="Unos labios más llenos\ny definidos.",icon=ico_volume),
 dict(t0=13.3,t1=17.3,th=LIGHT,title="¿Te dan miedo\nlas agujas?",body="Muchas personas no se atreven\njustamente por eso.",icon=ico_syringe),
 dict(t0=17.3,t1=22.3,th=DARK,title="Hyaluron Pen",sub="Volumen en labios sin agujas",icon=ico_pen),
 dict(t0=22.3,t1=26.3,th=LIGHT,title="Más sutil,\nmás natural",body="Un resultado suave\ny armonioso.",icon=ico_sparkle),
 dict(t0=26.3,t1=29.8,th=LIGHT,title="Te encantará\nel resultado",icon=ico_heart),
 dict(t0=29.8,t1=34.5,th=LIGHT,title="Ya no hay excusa",sub="para lucir tus labios\ncon volumen",icon=ico_final),
 dict(t0=34.5,t1=DUR,th=DARK,end=True),
]
N=len(slides)
def build(s):
    th=s["th"]; s["bg"]=gradient(*th["bg"]); s["hdr"]=header(th); L=[]
    if s.get("end"):
        lot=ico_lotus(th["rose"]).resize((420,420),Image.LANCZOS); L.append(("icon",lot,((W-420)//2,300),0.0))
        L.append(("txt",*text_layer("BBLips",font(SERIF,110,400),th["ink"],740),0.25))
        im=Image.new("RGBA",(W,H),(0,0,0,0)); d=ImageDraw.Draw(im); f=font(SANS,28,600); t="ESTÉTICA AVANZADA"; w=spaced_w(d,t,f,10)
        spaced(d,(W-w)/2,900,t,f,th["rose"]+(255,),10); d.line((W/2-160,880,W/2+160,880),fill=th["rose"]+(120,),width=2); bb=im.getbbox(); L.append(("txt",im.crop(bb),bb[:2],0.4))
        L.append(("txt",*text_layer("Bruna Borges",font(SERIFI,64,400),th["ink"],990),0.55))
        L.append(("txt",*text_layer("Especialista en labios",font(SANS,34,400),th["soft"],1095),0.65))
        im=Image.new("RGBA",(W,H),(0,0,0,0)); d=ImageDraw.Draw(im)
        d.rounded_rectangle((W/2-250,1230,W/2+250,1336),radius=53,fill=(232,186,192,255)); d.text((W/2,1283),"Reserva tu cita",font=font(SANS,42,600),fill=(52,38,50,255),anchor="mm")
        d.text((W/2,1410),"@brunaborgesestetic",font=font(SANS,36,500),fill=th["soft"]+(255,),anchor="mm"); bb=im.getbbox(); L.append(("txt",im.crop(bb),bb[:2],0.85))
    else:
        y=330; tf=TS if max(len(l) for l in s["title"].split("\n"))<=14 else TSs
        L.append(("txt",*text_layer(s["title"],tf,th["ink"],y),0.0))
        y+= (tf.size+18)*(s["title"].count("\n")+1)+30
        if s.get("sub"): L.append(("txt",*text_layer(s["sub"],SUBI,th["rose"],y),0.18)); y+=(62)*(s["sub"].count("\n")+1)+20
        if s.get("body"): L.append(("txt",*text_layer(s["body"],BODY,th["soft"],y+10),0.3)); y+=(56)*(s["body"].count("\n")+1)+30
        ic=s["icon"](th); s["icy"]=max(y+40,880)
        L.append(("icon",ic,((W-IS)//2,s["icy"]),0.35))
    s["layers"]=L
for s in slides: build(s)
def ease(x): x=min(max(x,0),1); return 1-(1-x)**3
def with_alpha(im,k):
    if k>=0.999: return im
    a=im.getchannel("A").point(lambda v:int(v*k)); im=im.copy(); im.putalpha(a); return im
def render_slide(s,lt):
    fr=s["bg"].copy(); fr.alpha_composite(s["hdr"])
    for kind,im,(x,y),delay in s["layers"]:
        p=ease((lt-delay)/0.6)
        if p<=0: continue
        if kind=="icon":
            sc=0.9+0.1*p; fl=math.sin((lt-delay)*1.6)*6
            ii=im if sc>0.999 else im.resize((int(im.width*sc),int(im.height*sc)),Image.BICUBIC)
            fr.alpha_composite(with_alpha(ii,p),(int(x+(im.width-ii.width)/2),int(y+(im.height-ii.height)/2+fl)))
        else:
            fr.alpha_composite(with_alpha(im,p),(int(x),int(y+(1-p)*30)))
    return fr
def bars(fr,t,th):
    ov=Image.new("RGBA",(W,H),(0,0,0,0)); d=ImageDraw.Draw(ov); gap=16; segw=(W-2*MX-gap*(N-1))/N; y=1690
    for i,s in enumerate(slides):
        x=MX+i*(segw+gap); d.rounded_rectangle((x,y,x+segw,y+5),radius=2,fill=th["bar"]+(70,))
        p=min(max((t-s["t0"])/(s["t1"]-s["t0"]),0),1)
        if p>0: d.rounded_rectangle((x,y,x+max(segw*p,5),y+5),radius=2,fill=th["bar"]+(255,))
    fr.alpha_composite(ov)
XF=0.4
out=sys.stdout.buffer
nfr=int(round(DUR*FPS)); prev_ts=[0.5,3,9,15,19,24,28,32,37] if PREVIEW else None
for n in range(nfr):
    t=n/FPS
    if PREVIEW and not any(abs(t-pt)<0.5/FPS for pt in prev_ts): continue
    i=max(k for k,s in enumerate(slides) if s["t0"]<=t)
    s=slides[i]; fr=render_slide(s,t-s["t0"])
    if i>0 and t-s["t0"]<XF:
        ps=slides[i-1]; pf=render_slide(ps,t-ps["t0"]); fr=Image.blend(pf,fr,ease((t-s["t0"])/XF))
    th=s["th"] if not (i>0 and t-s["t0"]<XF/2) else slides[i-1]["th"]
    bars(fr,t,th)
    if n<8: fr=Image.blend(Image.new("RGBA",(W,H),(0,0,0,255)),fr,n/8)
    if PREVIEW: fr.convert("RGB").resize((360,640)).convert("RGB").save(f"{PREVIEW}/p{t:05.1f}.png")
    else: out.write(fr.convert("RGB").tobytes())
