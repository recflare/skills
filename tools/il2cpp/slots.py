"""Resolve the Il2Cpp metadata slots a method references -> real generic instantiations / type names.

    py slots.py <rva_hex> [len_hex]

Il2CppDumper's ScriptMetadataMethod / ScriptMetadata tables name every metadata slot, so a
`mov r8, [rip+X]` before a generic call tells you the *actual* T, which methods.pkl cannot
(generic-shared code has one address for every instantiation).
Builds meta.pkl on first run.
"""
import struct,pickle,bisect,sys,os,ijson
from capstone import Cs,CS_ARCH_X86,CS_MODE_64,x86

if os.path.exists("meta.pkl"):
    meta=pickle.load(open("meta.pkl","rb"))
else:
    meta={}
    for key in ("ScriptMetadataMethod","ScriptMetadata"):
        with open("out/script.json","rb") as f:
            for it in ijson.items(f,key+".item"):
                meta.setdefault(int(it["Address"]),it["Name"])
    pickle.dump(meta,open("meta.pkl","wb"))

DLL=__import__("os").environ.get("GAMEASSEMBLY", r"C:\Games\recflare-client\GameAssembly.dll")
data=open(DLL,'rb').read()
pe=struct.unpack_from("<I",data,0x3C)[0]
n=struct.unpack_from("<H",data,pe+6)[0]; o=struct.unpack_from("<H",data,pe+20)[0]
so=pe+24+o; secs=[]
for i in range(n):
    p=so+i*40
    vs,va,rs,rp=struct.unpack_from("<IIII",data,p+8)
    secs.append((va,vs,rp,rs))
def off(r):
    for va,vs,rp,rs in secs:
        if va<=r<va+max(vs,rs): return rp+(r-va)

RVA=int(sys.argv[1],16); LEN=int(sys.argv[2],16) if len(sys.argv)>2 else 0x400
md=Cs(CS_ARCH_X86,CS_MODE_64); md.detail=True
seen=set()
for ins in md.disasm(data[off(RVA):off(RVA)+LEN], RVA):
    for op in ins.operands:
        if op.type==x86.X86_OP_MEM and op.mem.base==x86.X86_REG_RIP:
            s=ins.address+ins.size+op.mem.disp
            if s in meta and s not in seen:
                seen.add(s)
                print(f"0x{ins.address:x}  slot 0x{s:x}  {meta[s]}")
