"""Print full signatures (return type + params) for every method of a type, from carved metadata.

usage: py msig.py <TypeName> [...]
"""
import os, struct, sys
META = os.environ.get("GA_METADATA", r"C:\Games\recnet-patcher\tools\metadump\out\global-metadata.dat")
DLL  = os.environ.get("GAMEASSEMBLY", r"C:\Games\recnet-patcher\tools\metadump\out\GameAssembly.dll")
IMGBASE = 0x180000000; MR = 0xC1A5770
m = open(META, "rb").read(); disk = open(DLL, "rb").read()
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
_mr = struct.unpack_from("<16Q", disk, MR); TY_P = _mr[7]
def hdr(o): return struct.unpack_from("<ii", m, o)
STR = hdr(0x18)[0]; METH = hdr(0x30)[0]; PARAMS = hdr(0x58)[0]
TD, TD_SZ = hdr(0xA0); TD_N = TD_SZ // 88
def s(i):
    o = STR + i; return m[o:m.index(b"\0", o)].decode("utf-8", "replace")
def tdname(t):
    b = TD + t * 88
    ns = struct.unpack_from("<i", m, b + 4)[0]
    nm = s(struct.unpack_from("<i", m, b)[0])
    return f"{s(ns)}.{nm}" if ns else nm
PRIM = {1:"void",2:"bool",3:"char",4:"sbyte",5:"byte",6:"short",7:"ushort",8:"int",9:"uint",
        0xA:"long",0xB:"ulong",0xC:"float",0xD:"double",0xE:"string",0x18:"IntPtr",0x19:"UIntPtr",
        0x1C:"object",0x13:"!T",0x1E:"!!T"}
def tname_p(p, d=0):
    r = va2raw(p)
    if r is None or d > 6: return f"<t@{p:#x}>"
    data, bits = struct.unpack_from("<QI", disk, r)
    k = (bits >> 16) & 0xFF
    byref = (bits >> 30) & 1
    out = _core(k, data, d)
    return out + "&" if byref else out
def _core(k, data, d):
    if k in (0x11, 0x12): return tdname(data & 0xFFFFFFFF)
    if k == 0x1D: return tname_p(data, d+1) + "[]"
    if k == 0x1B: return tname_p(data, d+1) + "*"
    if k == 0x15:
        gtd, cinst, minst = struct.unpack_from("<3Q", disk, va2raw(data))
        base = tdname(gtd & 0xFFFFFFFF) if gtd < 0x100000 else tname_p(gtd, d+1)
        return f"{base}<{', '.join(_inst(cinst, d+1))}>"
    return PRIM.get(k, f"kind{k:#x}")
def _inst(p, d=0):
    if p == 0: return []
    n, argv = struct.unpack_from("<QQ", disk, va2raw(p))
    ar = va2raw(argv)
    return [tname_p(struct.unpack_from("<Q", disk, ar + j*8)[0], d+1) for j in range(min(n, 16))]
def tname_i(ti): return tname_p(struct.unpack_from("<Q", disk, va2raw(TY_P + ti * 8))[0])
for want in sys.argv[1:]:
    for t in range(TD_N):
        n = tdname(t)
        if n.split(".")[-1] != want and n != want: continue
        b = TD + t * 88
        ms = struct.unpack_from("<i", m, b + 36)[0]; mc = struct.unpack_from("<H", m, b + 64)[0]
        print(f"=== {n} ({mc} methods)")
        for k in range(ms, ms + mc):
            mb = METH + k * 36
            nm = s(struct.unpack_from("<i", m, mb)[0])
            rt = struct.unpack_from("<i", m, mb + 8)[0]
            ps = struct.unpack_from("<i", m, mb + 16)[0]
            flags = struct.unpack_from("<H", m, mb + 28)[0]
            pc = struct.unpack_from("<H", m, mb + 34)[0]
            args = []
            for j in range(ps, ps + pc):
                pbn = PARAMS + j * 12
                args.append(f"{tname_i(struct.unpack_from('<i', m, pbn + 8)[0])} {s(struct.unpack_from('<i', m, pbn)[0])}")
            st = "static " if flags & 0x10 else ""
            print(f"  {st}{tname_i(rt)} {nm}({', '.join(args)})")
