import os,sys,struct,re,time
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from lz4b import lz4_decompress
root=sys.argv[1]; needles=[x.lower().encode() for x in sys.argv[2].split(',')]
pats=[]
for nd in needles:
    pats.append((nd,'ascii')); pats.append((b''.join(bytes([c,0]) for c in nd),'utf16'))
limit=int(sys.argv[3]) if len(sys.argv)>3 else 10**9
files=sorted(os.listdir(root))[:limit]
t0=time.time(); hits=0; done=0; failed=[]
for fn in files:
    p=os.path.join(root,fn)
    try:
        b=open(p,'rb').read()
        if b[:7]!=b'UnityFS': continue
        o=b.index(b'\0')+1; ver=struct.unpack_from('>I',b,o)[0]; o+=4; o=b.index(b'\0',o)+1; o=b.index(b'\0',o)+1
        size,cbi,ubi,flags=struct.unpack_from('>QIII',b,o); o+=20
        # UnityFS aligns the header for version>=7. Testing only the 0x200 flag MISSES v7
        # bundles (Unity 2020 / the 20230414 build): payload decodes EMPTY with no error.
        if ver>=7 or (flags & 0x200): o=(o+15)&~15
        bi=lz4_decompress(b[o:o+cbi],ubi) if (flags&0x3F) in (2,3) else b[o:o+cbi]
        o+=cbi
        q=16; cnt=struct.unpack_from('>I',bi,q)[0]; q+=4
        blocks=[struct.unpack_from('>IIH',bi,q+10*i) for i in range(cnt)]
        out=None
        for start in (o,(o+15)&~15):
            pp=start; acc=bytearray()
            try:
                for us,cs,fl in blocks:
                    acc += lz4_decompress(b[pp:pp+cs],us) if (fl&0x3F) in (2,3) else b[pp:pp+cs]
                    pp+=cs
                out=acc; break
            except Exception: continue
        if out is None: failed.append(fn); continue
        low=bytes(out).lower()
        for pat,kind in pats:
            i=low.find(pat)
            while i>=0:
                s=max(0,i-70); e=min(len(out),i+90)
                ctx=re.sub(rb'[^\x20-\x7e]',b'.',bytes(out[s:e]))
                print(f"{fn} @{i} [{kind}] {ctx.decode('ascii','replace')}"); hits+=1
                i=low.find(pat,i+1)
        done+=1
    except Exception:
        failed.append(fn)
print(f"scanned={done} failed={len(failed)} hits={hits} secs={time.time()-t0:.1f}")
if failed[:5]: print("sample failures:",failed[:5])
