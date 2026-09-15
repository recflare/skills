"""Resolve generic instantiations: methodSpec index -> full generic method signature with type args.

usage: py ginst.py spec <idx> [...]      # methodSpec index (the 'method=' from slots2025)
       py ginst.py inst <idx> [...]      # genericInst index (the 'class='/'method=' operand)
"""
import os, struct, sys

DLL  = os.environ.get("GAMEASSEMBLY", r"C:\Games\recnet-patcher\tools\metadump\out\GameAssembly.dll")
META = os.environ.get("GA_METADATA",  r"C:\Games\recnet-patcher\tools\metadump\out\global-metadata.dat")
IMGBASE = 0x180000000
MR = 0xC1A5770
T = {"string": 0x100, "methods": 0xAA8748, "typeDefinitions": 0x2269158}

disk = open(DLL, "rb").read(); meta = open(META, "rb").read()
pe = struct.unpack_from("<I", disk, 0x3C)[0]
nsec = struct.unpack_from("<H", disk, pe + 6)[0]
soff = pe + 24 + struct.unpack_from("<H", disk, pe + 20)[0]
secs = []
for i in range(nsec):
    o = soff + i * 40
    vs, va, rs, rp = struct.unpack_from("<IIII", disk, o + 8)
    secs.append((va, rs, rp))

def rva2raw(r):
    for va, rs, rp in secs:
        if va <= r < va + rs: return rp + (r - va)
def va2raw(v):
    return rva2raw(v - IMGBASE) if IMGBASE <= v < IMGBASE + 0xE700000 else None
def mstr(i):
    o = T["string"] + i; return meta[o:meta.index(b"\0", o)].decode("utf-8", "replace")
def tdname(td):
    b = T["typeDefinitions"] + td * 88
    ns = struct.unpack_from("<i", meta, b + 4)[0]
    nm = mstr(struct.unpack_from("<i", meta, b)[0])
    return f"{mstr(ns)}.{nm}" if ns else nm

_mr = struct.unpack_from("<16Q", disk, MR)
GI_N, GI_P = _mr[2], _mr[3]
TY_N, TY_P = _mr[6], _mr[7]
SP_N, SP_P = _mr[8], _mr[9]

def typeptr(i):
    return struct.unpack_from("<Q", disk, va2raw(TY_P + i * 8))[0]

def tname(p, depth=0):
    r = va2raw(p)
    if r is None or depth > 6: return f"<t@{p:#x}>"
    data, bits = struct.unpack_from("<QI", disk, r)
    k = (bits >> 16) & 0xFF
    if k in (0x11, 0x12): return tdname(data & 0xFFFFFFFF)
    if k == 0x1D: return tname(data, depth+1) + "[]"
    if k == 0x1B: return tname(data, depth+1) + "*"
    if k == 0x15:
        gr = va2raw(data)
        gtd, cinst, minst = struct.unpack_from("<3Q", disk, gr)
        base = tdname(gtd & 0xFFFFFFFF) if gtd < 0x100000 else tname(gtd, depth+1)
        args = inst_args(cinst, depth+1)
        return f"{base}<{', '.join(args)}>"
    PRIM = {1:"void",2:"bool",3:"char",4:"sbyte",5:"byte",6:"short",7:"ushort",8:"int",9:"uint",
            0xA:"long",0xB:"ulong",0xC:"float",0xD:"double",0xE:"string",0x18:"IntPtr",0x19:"UIntPtr",
            0x1C:"object",0x13:"!T",0x1E:"!!T"}
    return PRIM.get(k, f"kind{k:#x}")

def inst_args(p, depth=0):
    if p == 0: return []
    r = va2raw(p)
    if r is None: return [f"<inst@{p:#x}>"]
    n, argv = struct.unpack_from("<QQ", disk, r)
    ar = va2raw(argv)
    out = []
    for j in range(min(n, 16)):
        out.append(tname(struct.unpack_from("<Q", disk, ar + j*8)[0], depth+1))
    return out

def inst_by_index(i):
    p = struct.unpack_from("<Q", disk, va2raw(GI_P + i*8))[0]
    return inst_args(p)

def mname(mi):
    b = T["methods"] + mi * 36
    return f"{tdname(struct.unpack_from('<i', meta, b+4)[0])}::{mstr(struct.unpack_from('<i', meta, b)[0])}"

mode = sys.argv[1]
for a in sys.argv[2:]:
    i = int(a, 0)
    if mode == "spec":
        md, ci, mi = struct.unpack_from("<3i", disk, va2raw(SP_P + i*12))
        c = inst_by_index(ci) if ci >= 0 else []
        m = inst_by_index(mi) if mi >= 0 else []
        print(f"spec#{i}: {mname(md)}")
        if c: print(f"   class args: {c}")
        if m: print(f"   method args: {m}")
    else:
        print(f"inst#{i}: {inst_by_index(i)}")
