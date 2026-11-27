import sys
from PIL import Image
import numpy as np
im=np.asarray(Image.open(sys.argv[1]).convert("RGB")).astype(float)
L=im@[0.299,0.587,0.114]; bg=np.median(L[:40,:40]); print("bg",bg,im.shape)
a=np.clip((bg-12-L)/(bg-60),0,1)
m=Image.fromarray((a*255).astype("uint8")); bb=m.getbbox(); print("bbox",bb); m=m.crop(bb)
out=Image.new("RGBA",m.size,(255,255,255,255)); out.putalpha(m); out.save(sys.argv[2])
