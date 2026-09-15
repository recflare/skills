"""Scan MetadataRegistration.types for genericinst types over a given generic type definition.

usage: py ginstscan.py <GenericTypeName> [...]
"""
import os, struct, sys
DLL  = os.environ.get("GAMEASSEMBLY", r"C:\Games\recnet-patcher\tools\metadump\out\GameAssembly.dll")
META = os.environ.get("GA_METADATA",  r"C:\Games\recnet-patcher\tools\metadump\out\global-metadata.dat")
IMGBASE = 0x180000000; MR = 0xC1A5770
disk = open(DLL, "rb").read(); m = open(META, "rb").read()
pe = struct.unpack_from("<I", disk, 0x3C)[0]
soff = pe + 24 + struct.unpack_from("<H", disk, pe + 20)[0]
secs = []
for i in range(struct.unpack_from("<H", disk, pe + 6)[0]):
    o = soff + i * 40
    vs, va, rs, rp = struct.unpack_from("<IIII", disk, o + 8); secs.append((va, rs, rp))
def va2raw(v):
    r = v - IMGBASE
    for va, rs, rp in secs:
        if va <= r < va + rs: return rp + (r - va)
def hdr(o): return struct.unpack_from("<ii", m, o)
STR = hdr(0x18)[0]; TD = hdr(0xA0)[0]
def s(i):
    o = STR + i; return m[o:m.index(b"\0", o)].decode("utf-8", "replace")
def tdname(t):
    b = TD + t * 88
    ns = struct.unpack_from("<i", m, b + 4)[0]
    nm = s(struct.unpack_from("<i", m, b)[0])
    return f"{s(ns)}.{nm}" if ns else nm
_mr = struct.unpack_from("<16Q", disk, MR); TY_N, TY_P = _mr[6], _mr[7]
PRIM = {1:"void",2:"bool",3:"char",4:"sbyte",5:"byte",6:"short",7:"ushort",8:"int",9:"uint",
        0xA:"long",0xB:"ulong",0xC:"float",0xD:"double",0xE:"string",0x1C:"object"}
def tname(p, d=0):
    r = va2raw(p)
    if r is None or d > 5: return "?"
    data, bits = struct.unpack_from("<QI", disk, r)
    k = (bits >> 16) & 0xFF
    if k in (0x11, 0x12): return tdname(data & 0xFFFFFFFF)
    if k == 0x1D: return tname(data, d+1) + "[]"
    if k == 0x15:
        gtd, ci, mi = struct.unpack_from("<3Q", disk, va2raw(data))
        return f"{tdname(gtd & 0xFFFFFFFF)}<{', '.join(args(ci, d+1))}>"
    return PRIM.get(k, f"k{k:#x}")
def args(p, d=0):
    if p == 0: return []
    n, argv = struct.unpack_from("<QQ", disk, va2raw(p))
    ar = va2raw(argv)
    return [tname(struct.unpack_from("<Q", disk, ar + j*8)[0], d+1) for j in range(min(n, 8))]
want = [w.lower() for w in sys.argv[1:]]
seen = set()
for i in range(TY_N):
    p = struct.unpack_from("<Q", disk, va2raw(TY_P + i * 8))[0]
    r = va2raw(p)
    if r is None: continue
    data, bits = struct.unpack_from("<QI", disk, r)
    if ((bits >> 16) & 0xFF) != 0x15: continue
    gr = va2raw(data)
    if gr is None: continue
    gtd = struct.unpack_from("<Q", disk, gr)[0]
    base = tdname(gtd & 0xFFFFFFFF) if gtd < 0x100000 else tname(gtd)
    if not any(w in base.lower() for w in want): continue
    t = f"{base}<{', '.join(args(struct.unpack_from('<3Q', disk, gr)[1]))}>"
    if t not in seen:
        seen.add(t); print(t)
