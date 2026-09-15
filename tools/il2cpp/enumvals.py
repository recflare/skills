"""Dump an enum typedef's members with literal values.

IL2CPP stores field default values as il2cpp COMPRESSED ints (zigzag for signed types),
NOT as raw little-endian of the declared width -- dataIndex steps by 1-5 bytes, not 4.

usage: py enumvals.py <TypeName> [...]
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
def kind_of(ti):
    p = struct.unpack_from("<Q", disk, va2raw(TY_P + ti * 8))[0]
    return (struct.unpack_from("<QI", disk, va2raw(p))[1] >> 16) & 0xFF
SIGNED = {4: "sbyte", 6: "short", 8: "int", 0xA: "long"}
UNSIGN = {2: "bool", 5: "byte", 7: "ushort", 9: "uint", 0xB: "ulong"}

def cuint(b, i):
    x = b[i]
    if x < 0x80: return x
    if x & 0xC0 == 0x80: return ((x & 0x3F) << 8) | b[i+1]
    if x & 0xE0 == 0xC0: return ((x & 0x1F) << 24) | (b[i+1] << 16) | (b[i+2] << 8) | b[i+3]
    if x == 0xF0: return struct.unpack_from("<I", b, i+1)[0]
    if x == 0xFE: return 0xFFFFFFFE
    return 0xFFFFFFFF
def cint(b, i):
    e = cuint(b, i)
    if e == 0xFFFFFFFF: return -2147483648
    neg = e & 1; e >>= 1
    return -(e + 1) if neg else e

def hdr(o): return struct.unpack_from("<ii", m, o)
STR = hdr(0x18)[0]; FDV, FDV_SZ = hdr(0x40); DV = hdr(0x48)[0]
FIELDS = hdr(0x60)[0]; TD, TD_SZ = hdr(0xA0); TD_N = TD_SZ // 88
def s(i):
    o = STR + i; return m[o:m.index(b"\0", o)].decode("utf-8", "replace")
def tdname(t):
    b = TD + t * 88
    ns = struct.unpack_from("<i", m, b + 4)[0]
    nm = s(struct.unpack_from("<i", m, b)[0])
    return f"{s(ns)}.{nm}" if ns else nm
defaults = {}
for i in range(FDV_SZ // 12):
    fi, ti, di = struct.unpack_from("<3i", m, FDV + i * 12); defaults[fi] = (ti, di)
for want in sys.argv[1:]:
    for t in range(TD_N):
        n = tdname(t)
        if n.split(".")[-1] != want and n != want: continue
        b = TD + t * 88
        fs = struct.unpack_from("<i", m, b + 32)[0]; fc = struct.unpack_from("<H", m, b + 68)[0]
        base = None
        for f in range(fs, fs + fc):
            if s(struct.unpack_from("<i", m, FIELDS + f * 12)[0]) == "value__":
                base = kind_of(struct.unpack_from("<i", m, FIELDS + f * 12 + 4)[0])
        tn = SIGNED.get(base) or UNSIGN.get(base) or f"kind{base:#x}"
        print(f"=== {n} : {tn}  (typedef #{t})")
        for f in range(fs, fs + fc):
            nm = s(struct.unpack_from("<i", m, FIELDS + f * 12)[0])
            if nm == "value__" or f not in defaults: continue
            di = defaults[f][1]
            # byte/sbyte-backed enums store a RAW byte, not a compressed int:
            # ModerationState.MarkedForDelete is 0xFF = 255, which cuint would read as the
            # 0xFFFFFFFF sentinel. Wider types are compressed (zigzag when signed).
            if base in (2, 4, 5):
                v = m[DV + di]
                if base == 4 and v > 127: v -= 256
            else:
                v = cint(m, DV + di) if base in SIGNED else cuint(m, DV + di)
            print(f"  {nm} = {v}")
