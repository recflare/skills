"""Enumerate every websocket notification subscription: channel id -> payload DTO -> handler method.

The registrar is the generic `LMBGGGGNBOB.KOOMBBKFAEP<TPayload>(string id, ...)`. Its per-
instantiation metadata-usage slots live in .data, so: collect those slots (recovering T from the
generic instantiation), find every method that references one, then disassemble that method and pair
each register call with the string literal loaded just before it.

usage: py notifall.py
"""
import bisect, json, os, pickle, re, struct, sys
from capstone import Cs, CS_ARCH_X86, CS_MODE_64, x86

DLL  = os.environ.get("GAMEASSEMBLY", r"C:\Games\recnet-patcher\tools\metadump\out\GameAssembly.dll")
META = os.environ.get("GA_METADATA",  r"C:\Games\recnet-patcher\tools\metadump\out\global-metadata.dat")
IMGBASE = 0x180000000; MR = 0xC1A5770
REGISTRAR = "KOOMBBKFAEP"

disk = open(DLL, "rb").read(); m = open(META, "rb").read()
pe = struct.unpack_from("<I", disk, 0x3C)[0]
soff = pe + 24 + struct.unpack_from("<H", disk, pe + 20)[0]
secs = []
for i in range(struct.unpack_from("<H", disk, pe + 6)[0]):
    o = soff + i * 40
    vs, va, rs, rp = struct.unpack_from("<IIII", disk, o + 8)
    secs.append((va, max(vs, rs), rp, rs))
def rva2raw(r):
    for va, sz, rp, rs in secs:
        if va <= r < va + sz and (r - va) < rs: return rp + (r - va)
def va2raw(v): return rva2raw(v - IMGBASE) if IMGBASE <= v < IMGBASE + 0xE700000 else None
def hdr(o): return struct.unpack_from("<ii", m, o)
STR = hdr(0x18)[0]; METH = hdr(0x30)[0]; TD = hdr(0xA0)[0]
def s(i):
    o = STR + i; return m[o:m.index(b"\0", o)].decode("utf-8", "replace")
def tdname(t):
    b = TD + t * 88
    ns = struct.unpack_from("<i", m, b + 4)[0]
    return (s(ns) + "." if ns else "") + s(struct.unpack_from("<i", m, b)[0])
def mname(mi):
    b = METH + mi * 36
    return f"{tdname(struct.unpack_from('<i', m, b+4)[0])}::{s(struct.unpack_from('<i', m, b)[0])}"
_mr = struct.unpack_from("<16Q", disk, MR); GI_P = _mr[3]; SP_N, SP_P = _mr[8], _mr[9]
PRIM = {2:"bool",5:"byte",8:"int",0xA:"long",0xE:"string"}
def tname(p, d=0):
    r = va2raw(p)
    if r is None or d > 4: return "?"
    data, bits = struct.unpack_from("<QI", disk, r)
    k = (bits >> 16) & 0xFF
    if k in (0x11, 0x12): return tdname(data & 0xFFFFFFFF).lstrip(".")
    if k == 0x1D: return tname(data, d+1) + "[]"
    if k == 0x15:
        gtd, ci, mi = struct.unpack_from("<3Q", disk, va2raw(data))
        base = tdname(gtd & 0xFFFFFFFF) if gtd < 0x100000 else tname(gtd, d+1)
        n, argv = struct.unpack_from("<QQ", disk, va2raw(ci))
        ar = va2raw(argv)
        args = [tname(struct.unpack_from("<Q", disk, ar + j*8)[0], d+1) for j in range(min(n,4))]
        return f"{base.split('.')[-1]}<{', '.join(args)}>"
    return PRIM.get(k, f"k{k:#x}")

slots = {}
for va, sz, rp, rs in secs:
    for off in range(0, rs - 8, 8):
        v = struct.unpack_from("<Q", disk, rp + off)[0]
        if v == 0 or v >> 32: continue
        kind, idx = v >> 29, v & 0x1FFFFFFF
        if kind != 6 or not idx & 1: continue
        si = (idx - 1) >> 1
        if not (0 <= si < SP_N): continue
        md, ci, mi = struct.unpack_from("<3i", disk, va2raw(SP_P + si * 12))
        if REGISTRAR not in mname(md): continue
        T = "?"
        if mi >= 0:
            p = struct.unpack_from("<Q", disk, va2raw(GI_P + mi*8))[0]
            n, argv = struct.unpack_from("<QQ", disk, va2raw(p))
            ar = va2raw(argv)
            T = ", ".join(tname(struct.unpack_from("<Q", disk, ar + j*8)[0]) for j in range(min(n,4)))
        slots[va + off] = T
sys.stderr.write(f"{len(slots)} registrar slots\n")
pickle.dump(slots, open("_notifslots.pkl", "wb"))
