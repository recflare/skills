"""Every endpoint whose response T is NOT a plain object — i.e. every route that breaks on a `{}` body.

Scans .data for metadata-usage slots that are MethodRefs to MGPBDIAGCFD's send generics, resolves
the generic instantiation to T, keeps the non-class Ts (list / array / primitive), then finds the
method that references each slot and its route literal.

usage: py sendscan.py
"""
import bisect, os, pickle, struct
import numpy as np

DLL  = os.environ.get("GAMEASSEMBLY", r"C:\Games\recnet-patcher\tools\metadump\out\GameAssembly.dll")
META = os.environ.get("GA_METADATA",  r"C:\Games\recnet-patcher\tools\metadump\out\global-metadata.dat")
IMGBASE = 0x180000000; MR = 0xC1A5770
disk = open(DLL, "rb").read(); m = open(META, "rb").read()
pe = struct.unpack_from("<I", disk, 0x3C)[0]
soff = pe + 24 + struct.unpack_from("<H", disk, pe + 20)[0]
secs, code = [], []
for i in range(struct.unpack_from("<H", disk, pe + 6)[0]):
    o = soff + i * 40
    name = disk[o:o+8].rstrip(b"\0").decode(errors="replace")
    vs, va, rs, rp = struct.unpack_from("<IIII", disk, o + 8)
    ch = struct.unpack_from("<I", disk, o + 36)[0]
    secs.append((va, max(vs, rs), rp, rs))
    if ch & 0x20: code.append((va, rp, rs))
def rva2raw(r):
    for va, sz, rp, rs in secs:
        if va <= r < va + sz and (r - va) < rs: return rp + (r - va)
def va2raw(v): return rva2raw(v - IMGBASE) if IMGBASE <= v < IMGBASE + 0xE700000 else None
def hdr(o): return struct.unpack_from("<ii", m, o)
STR = hdr(0x18)[0]; METH = hdr(0x30)[0]; TD = hdr(0xA0)[0]
SL, SLN = hdr(0x08); SLD = hdr(0x10)[0]
def s(i):
    o = STR + i; return m[o:m.index(b"\0", o)].decode("utf-8", "replace")
def tdname(t):
    b = TD + t * 88
    ns = struct.unpack_from("<i", m, b + 4)[0]
    return (s(ns) + "." if ns else "") + s(struct.unpack_from("<i", m, b)[0])
def mname(mi):
    b = METH + mi * 36
    return f"{tdname(struct.unpack_from('<i', m, b+4)[0])}::{s(struct.unpack_from('<i', m, b)[0])}"
_mr = struct.unpack_from("<16Q", disk, MR)
GI_P = _mr[3]; SP_N, SP_P = _mr[8], _mr[9]
PRIM = {2:"bool",4:"sbyte",5:"byte",6:"short",7:"ushort",8:"int",9:"uint",0xA:"long",0xB:"ulong",
        0xC:"float",0xD:"double",0xE:"string"}
def tinfo(p, d=0):
    r = va2raw(p)
    if r is None or d > 4: return ("?", "?")
    data, bits = struct.unpack_from("<QI", disk, r)
    k = (bits >> 16) & 0xFF
    if k in (0x11, 0x12): return ("class", tdname(data & 0xFFFFFFFF))
    if k == 0x1D: return ("array", tinfo(data, d+1)[1] + "[]")
    if k == 0x15:
        gtd, ci, mi = struct.unpack_from("<3Q", disk, va2raw(data))
        base = tdname(gtd & 0xFFFFFFFF) if gtd < 0x100000 else tinfo(gtd, d+1)[1]
        args = inst(ci, d+1)
        kind = "list" if base.startswith("System.Collections.Generic.List") else "class"
        return (kind, f"{base.split('.')[-1]}<{', '.join(a[1] for a in args)}>")
    if k in PRIM: return ("scalar", PRIM[k])
    return ("other", f"k{k:#x}")
def inst(p, d=0):
    if p == 0: return []
    n, argv = struct.unpack_from("<QQ", disk, va2raw(p))
    ar = va2raw(argv)
    return [tinfo(struct.unpack_from("<Q", disk, ar + j*8)[0], d+1) for j in range(min(n, 8))]

# 1. collect send-generic MethodRef slots
targets = {}
for va, sz, rp, rs in secs:
    for off in range(0, rs - 8, 8):
        v = struct.unpack_from("<Q", disk, rp + off)[0]
        if v == 0 or v >> 32: continue
        kind, idx = v >> 29, v & 0x1FFFFFFF
        if kind != 6 or not idx & 1: continue
        si = (idx - 1) >> 1
        if not (0 <= si < SP_N): continue
        md, ci, mi = struct.unpack_from("<3i", disk, va2raw(SP_P + si * 12))
        nm = mname(md)
        if not any(x in nm for x in ("HPBKMCLEANE", "CJBFDPLCIEJ")): continue
        if mi < 0: continue
        args = inst(struct.unpack_from("<Q", disk, va2raw(GI_P + mi*8))[0])
        if not args: continue
        if args[0][0] in ("list", "array", "scalar"):
            targets[va + off] = (nm.split("::")[1], args[0][1])
print(f"{len(targets)} send slots with non-object T")
pickle.dump(targets, open("_sendtargets.pkl", "wb"))
