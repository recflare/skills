"""For each DONKHLENABO subscription call site, resolve the handler method and the
instantiated generic BIBPILLJJBN<T> via Il2CppDumper's ScriptMetadataMethod table."""
import struct,pickle,bisect,ijson,sys
from capstone import Cs,CS_ARCH_X86,CS_MODE_64,x86

tbl=pickle.load(open("methods.pkl","rb"))
addrs=[a for a,_ in tbl]; names=[n for _,n in tbl]
def own(r):
    j=bisect.bisect_right(addrs,r)-1
    return (addrs[j],names[j],(addrs[j+1] if j+1<len(addrs) else addrs[j]+0x800))

DLL=r"C:\Games\recflare-client\GameAssembly.dll"
data=open(DLL,'rb').read()
pe=struct.unpack_from("<I",data,0x3C)[0]
n=struct.unpack_from("<H",data,pe+6)[0]; o=struct.unpack_from("<H",data,pe+20)[0]
so=pe+24+o; secs=[]
for i in range(n):
    p=so+i*40
    vs,va,rs,rp=struct.unpack_from("<IIII",data,p+8)
    secs.append((va,vs,rp,rs,struct.unpack_from("<I",data,p+36)[0]))
def off(r):
    for va,vs,rp,rs,_ in secs:
        if va<=r<va+max(vs,rs): return rp+(r-va)

print("loading ScriptMetadataMethod + ScriptMetadata...", file=sys.stderr)
meta={}
with open("out/script.json","rb") as f:
    for it in ijson.items(f,"ScriptMetadataMethod.item"):
        meta[int(it["Address"])]=it["Name"]
with open("out/script.json","rb") as f:
    for it in ijson.items(f,"ScriptMetadata.item"):
        meta.setdefault(int(it["Address"]),it["Name"])

TARGETS={0x2887100,0x2886e80,0x1D17A60,0x1D17AF0}
CALLER=sys.argv[1] if len(sys.argv)>1 else "NHJBBNCKCBK"
md=Cs(CS_ARCH_X86,CS_MODE_64); md.detail=True

start,nm,end=None,None,None
for a,x in tbl:
    if x.endswith(CALLER+"$$IHEKMEOIBOI") or x==CALLER:
        start,nm,end=own(a); break
if start is None: sys.exit("caller not found")
print(f"# {nm}  0x{start:x}..0x{end:x}\n")

pend=[]           # rip-relative loads seen so far, in order
for ins in md.disasm(data[off(start):off(start)+min(end-start,0x8000)], start):
    for op in ins.operands:
        if op.type==x86.X86_OP_MEM and op.mem.base==x86.X86_REG_RIP:
            slot=ins.address+ins.size+op.mem.disp
            if slot in meta: pend.append((ins.address,ins.reg_name(op.reg) if False else None,slot,meta[slot]))
    if ins.mnemonic=="call" and ins.op_str.startswith("0x"):
        t=int(ins.op_str,16)
        if t in TARGETS:
            print(f"call 0x{t:x} @0x{ins.address:x}")
            for a2,_,s,nme in pend[-6:]:
                print(f"      0x{a2:x}  slot 0x{s:x}  {nme}")
            print()
            pend=[]
