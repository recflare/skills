import re,struct,pickle,bisect,sys
from capstone import Cs, CS_ARCH_X86, CS_MODE_64
tbl=pickle.load(open("methods.pkl","rb"))
addrs=[a for a,_ in tbl]; names=[n for _,n in tbl]
def owner(rva):
    j=bisect.bisect_right(addrs,rva)-1
    return (addrs[j],names[j]) if j>=0 else (None,"?")
def end_of(rva):
    j=bisect.bisect_right(addrs,rva)-1
    return addrs[j+1] if j+1<len(addrs) else rva+0x400
gv={}
cur=None
for line in open('nullable_xref.txt',encoding='utf-8',errors='replace'):
    m=re.match(r'\s+ref 0x[0-9a-f]+ -> method start 0x([0-9a-f]+)',line)
    if m: cur=int(m.group(1),16)
    m2=re.match(r'\s+(System\.Nullable.*|System\.ThrowHelper.*)',line.rstrip())
    if m2: gv[cur]=m2.group(1).strip()
DLL = __import__("os").environ.get("GAMEASSEMBLY", r"C:\Games\recflare-client\GameAssembly.dll")
data=open(DLL,'rb').read()
pe=struct.unpack_from("<I",data,0x3C)[0]
n=struct.unpack_from("<H",data,pe+6)[0]; o=struct.unpack_from("<H",data,pe+20)[0]
so=pe+24+o; secs=[]
for i in range(n):
    p=so+i*40
    vs,va,rs,rp=struct.unpack_from("<IIII",data,p+8); secs.append((va,vs,rp,rs))
def off(rva):
    for va,vs,rp,rs in secs:
        if va<=rva<va+max(vs,rs): return rp+(rva-va)
md=Cs(CS_ARCH_X86,CS_MODE_64)
SKIP=re.compile(r'^(System\.|UnityEngine\.|Unity\.|Photon\.|Google\.Protobuf|Newtonsoft|BestHTTP|Il2Cpp|TMPro|Backtrace)')
def calls_of(rva):
    e=end_of(rva); ln=min(max(e-rva,0x40),0x4000)
    o2=off(rva)
    if o2 is None: return []
    out=[]
    for ins in md.disasm(data[o2:o2+ln],rva):
        if ins.mnemonic=='call' and ins.op_str.startswith('0x'):
            out.append(int(ins.op_str,16))
    return out
ROOT=int(sys.argv[1],16); MAXD=int(sys.argv[2]) if len(sys.argv)>2 else 3
seen={ROOT:None}; frontier=[ROOT]; found=[]
for d in range(MAXD):
    nxt=[]
    for f in frontier:
        for t in calls_of(f):
            if t in gv:
                found.append((f,t)); continue
            st,nm=owner(t)
            if st is None or st in seen or SKIP.match(nm): continue
            seen[st]=f; nxt.append(st)
    frontier=nxt
    print(f"depth {d+1}: frontier={len(frontier)} found={len(found)}",file=sys.stderr)
def path(a):
    p=[]
    while a is not None: p.append(owner(a)[1]); a=seen.get(a)
    return " <- ".join(p)
seenf=set()
for f,t in found:
    key=(owner(f)[0],t)
    if key in seenf: continue
    seenf.add(key)
    print(f"\n{gv[t]}  called by  {owner(f)[1]}")
    print("   path:", path(owner(f)[0]))
