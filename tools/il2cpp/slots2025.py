"""slots.py for recflare-2025: resolve a method's metadata-usage slots without script.json.

Generated IL2CPP code reaches types/methods through global slots that are statically initialised in
.data with (kind << 29) | (index * 2 + 1) and overwritten with real pointers at runtime -- so the
encoding survives only in the on-disk .data, which is exactly what the carve keeps.

  kind 1 TypeInfo   -> MetadataRegistration.types[i]        (Il2CppType)
  kind 2 Il2CppType -> MetadataRegistration.types[i]
  kind 3 MethodDef  -> metadata methods[i]
  kind 4 FieldInfo  -> fieldRefs[i]
  kind 5 StringLit  -> metadata stringLiteral[i]
  kind 6 MethodRef  -> MetadataRegistration.methodSpecs[i]  (generic instantiation)

usage: py slots2025.py <rva_hex> [len_hex]
"""
import bisect
import os
import pickle
import struct
import sys

import capstone

DLL = os.environ.get("GAMEASSEMBLY", r"C:\Games\recnet-patcher\tools\metadump\out\GameAssembly.dll")
MEM  = os.environ.get("GA_IMAGE",    r"C:\Games\recnet-patcher\tools\metadump\out\ga_image.bin")
META = os.environ.get("GA_METADATA", r"C:\Games\recnet-patcher\tools\metadump\out\global-metadata.dat")
IMGBASE = 0x180000000
METADATA_REGISTRATION_RAW = 0xC1A5770       # found by the NTYPE/NTYPE signature

T = {"string": 0x100, "methods": 0xAA8748, "typeDefinitions": 0x2269158,
     "stringLiteral": 0x18703AC, "stringLiteralData": 0x2B1AF94, "fieldRefs": 0x1EF0C84,
     "fields": 0x2786E5C}

disk = open(DLL, "rb").read()
mem = open(MEM, "rb").read()
meta = open(META, "rb").read()
tbl = pickle.load(open("methods.pkl", "rb"))
addrs = [a for a, _ in tbl]

pe = struct.unpack_from("<I", disk, 0x3C)[0]
nsec = struct.unpack_from("<H", disk, pe + 6)[0]
soff = pe + 24 + struct.unpack_from("<H", disk, pe + 20)[0]
secs = []
for i in range(nsec):
    o = soff + i * 40
    vs, va, rs, rp = struct.unpack_from("<IIII", disk, o + 8)
    secs.append((va, rs, rp))


def rva2raw(rva):
    for va, rs, rp in secs:
        if va <= rva < va + rs:
            return rp + (rva - va)
    return None


def va2raw(va):
    return rva2raw(va - IMGBASE) if IMGBASE <= va < IMGBASE + 0xE700000 else None


def mstr(idx):
    o = T["string"] + idx
    return meta[o:meta.index(b"\0", o)].decode("utf-8", "replace")


def type_name(td):
    b = T["typeDefinitions"] + td * 88
    ns = struct.unpack_from("<i", meta, b + 4)[0]
    name = mstr(struct.unpack_from("<i", meta, b)[0])
    return f"{mstr(ns)}.{name}" if ns else name


def method_name(mi):
    b = T["methods"] + mi * 36
    return f"{type_name(struct.unpack_from('<i', meta, b + 4)[0])}::{mstr(struct.unpack_from('<i', meta, b)[0])}"


# MetadataRegistration: 8 (count, ptr) pairs; [3] types, [4] methodSpecs
_mr = struct.unpack_from("<16Q", disk, METADATA_REGISTRATION_RAW)
TYPES_N, TYPES_P = _mr[6], _mr[7]
SPECS_N, SPECS_P = _mr[8], _mr[9]

IL2CPP_TYPE = {0x11: "valuetype", 0x12: "class", 0x15: "genericinst", 0x1D: "szarray"}


def il2cpp_type(i):
    if not (0 <= i < TYPES_N):
        return f"<type#{i}>"
    p = struct.unpack_from("<Q", disk, va2raw(TYPES_P + i * 8))[0]
    r = va2raw(p)
    if r is None:
        return f"<type@{p:#x}>"
    data, bits = struct.unpack_from("<QI", disk, r)
    kind = (bits >> 16) & 0xFF
    if kind in (0x11, 0x12):
        return type_name(data & 0xFFFFFFFF)
    return f"{IL2CPP_TYPE.get(kind, hex(kind))}"


def method_spec(i):
    if not (0 <= i < SPECS_N):
        return f"<spec#{i}>"
    md, ci, mi = struct.unpack_from("<3i", disk, va2raw(SPECS_P + i * 12))
    return f"{method_name(md)}  <generic inst class={ci} method={mi}>"


def literal(i):
    ln, di = struct.unpack_from("<II", meta, T["stringLiteral"] + i * 8)
    return repr(meta[T["stringLiteralData"] + di:T["stringLiteralData"] + di + ln].decode("utf-8", "replace"))


def field_ref(i):
    ti, fi = struct.unpack_from("<2i", meta, T["fieldRefs"] + i * 8)
    return f"{il2cpp_type(ti)} field#{fi}"


def resolve(kind, idx):
    return {1: il2cpp_type, 2: il2cpp_type, 3: method_name, 4: field_ref,
            5: literal, 6: method_spec}.get(kind, lambda x: f"?{x}")(idx)


def usage(rva):
    raw = rva2raw(rva)
    if raw is None:
        return None
    v = struct.unpack_from("<Q", disk, raw)[0]
    if v == 0 or v >> 32:
        return None
    kind, idx = v >> 29, v & 0x1FFFFFFF
    if not 1 <= kind <= 6 or not idx & 1:
        return None
    return kind, (idx - 1) >> 1


def owner(rva):
    j = bisect.bisect_right(addrs, rva) - 1
    return tbl[j][1] if j >= 0 else "?"


md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_64)
md.detail = True
KIND = {1: "TypeInfo", 2: "Il2CppType", 3: "MethodDef", 4: "FieldInfo", 5: "StringLiteral", 6: "MethodRef"}

for arg in range(1, len(sys.argv), 2):
    start = int(sys.argv[arg], 16)
    ln = int(sys.argv[arg + 1], 16) if arg + 1 < len(sys.argv) else 0x300
    print(f"=== {owner(start)} @ {start:#x} (+{ln:#x})")
    for ins in md.disasm(mem[start:start + ln], IMGBASE + start):
        for op in ins.operands:
            if op.type == capstone.x86.X86_OP_MEM and op.mem.base == capstone.x86.X86_REG_RIP:
                t = ins.address + ins.size + op.mem.disp - IMGBASE
                u = usage(t)
                if u:
                    print(f"  {ins.address:#x} {ins.mnemonic:5} {KIND[u[0]]:13} {resolve(*u)}")
            elif op.type == capstone.x86.X86_OP_IMM and ins.mnemonic == "call":
                t = op.imm - IMGBASE
                j = bisect.bisect_right(addrs, t) - 1
                if j >= 0 and addrs[j] == t:
                    print(f"  {ins.address:#x} call  -> {tbl[j][1]}")
