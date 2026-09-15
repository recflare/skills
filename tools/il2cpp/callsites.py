import struct,pickle,bisect,sys,re
tbl=pickle.load(open("methods.pkl","rb"))
addrs=[a for a,_ in tbl]; names=[n for _,n in tbl]
def owner(rva):
    j=bisect.bisect_right(addrs,rva)-1
    return names[j] if j>=0 else "?"
DLL = __import__("os").environ.get("GAMEASSEMBLY", r"C:\Games\recflare-client\GameAssembly.dll")
data=open(DLL,'rb').read()
pe=struct.unpack_from("<I",data,0x3C)[0]
n=struct.unpack_from("<H",data,pe+6)[0]; o=struct.unpack_from("<H",data,pe+20)[0]
so=pe+24+o; secs=[]
for i in range(n):
    p=so+i*40
    nm=data[p:p+8].rstrip(b"\x00").decode('latin1')
    vs,va,rs,rp=struct.unpack_from("<IIII",data,p+8)
    ch=struct.unpack_from("<I",data,p+36)[0]
    if ch & 0x20000000: secs.append((va,vs,rp,rs))
TARGETS={int(a,16) for a in sys.argv[1:-1]}
FILT=re.compile(sys.argv[-1], re.I)
hits=[]
for va,vs,rp,rs in secs:
    blob=data[rp:rp+rs]
    for i in range(len(blob)-5):
        if blob[i]!=0xE8: continue
        d=struct.unpack_from("<i",blob,i+1)[0]
        t=va+i+5+d
        if t in TARGETS:
            src=va+i
            ow=owner(src)
            if FILT.search(ow): hits.append((src,ow,t))
for s,ow,t in hits: print(f"0x{s:x}  in {ow}   -> 0x{t:x}")
print(len(hits),"filtered call sites")
