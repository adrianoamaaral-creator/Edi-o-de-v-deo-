"""Monta a versão curta do áudio só com as falas principais. Uso: cut_audio.py original.wav(44.1k estéreo) saida.wav"""
import sys, wave, numpy as np
SEGS=[  # (início, fim) no áudio original, em segundos
 (6.88,9.25),(9.85,12.62),            # "Es para las personas que tienen miedo de agujas / y les encantaría tener un labio con más volumen"
 (16.98,18.30),(18.85,19.80),(20.25,25.40),  # "Pues os presento el Hyaluron Pen, con él logramos volumen de una manera más sutil, más natural"
 (26.62,34.20),                       # "Os garantizo que os encantará el resultado, así que ya no hay excusa para no tener tus labios con volumen"
]
GAP_AFTER={1:0.30,4:0.30}  # respiro entre blocos de ideia
LEAD=0.5; TOTAL=25.0
w=wave.open(sys.argv[1]); sr=w.getframerate(); ch=w.getnchannels()
a=np.frombuffer(w.readframes(w.getnframes()),dtype=np.int16).reshape(-1,ch).astype(np.float32)
out=[np.zeros((int(LEAD*sr),ch),np.float32)]; t=LEAD
for i,(s,e) in enumerate(SEGS):
    seg=a[int(s*sr):int(e*sr)].copy(); n=len(seg); f=int(0.02*sr)
    ramp=np.linspace(0,1,f)[:,None]; seg[:f]*=ramp; seg[-f:]*=ramp[::-1]
    print(f"seg{i} orig {s:.2f}-{e:.2f} -> out {t:.2f}-{t+n/sr:.2f}"); out.append(seg); t+=n/sr
    g=GAP_AFTER.get(i,0)
    if g: out.append(np.zeros((int(g*sr),ch),np.float32)); t+=g
rest=int(TOTAL*sr)-sum(len(x) for x in out); out.append(np.zeros((max(rest,0),ch),np.float32))
y=np.concatenate(out).clip(-32768,32767).astype(np.int16)
o=wave.open(sys.argv[2],"wb"); o.setnchannels(ch); o.setsampwidth(2); o.setframerate(sr); o.writeframes(y.tobytes()); o.close()
