"""List a type's instance fields with their runtime offsets, straight from the carved metadata.

Cpp2IL only annotates FieldOffset on real fields, so auto-property backing fields (which is all a
RecNet DTO has) show no offsets in the dump. This walks typeDefinitions -> fields and pairs them
with MetadataRegistration.fieldOffsets, which is the independent check that a formatter's
____stringByteKeys run really does line up with the declared members.

usage: py fields2025.py <TypeName> [...]
"""
import os, struct, sys

DLL  = os.environ.get("GAMEASSEMBLY", r"C:\Games\recnet-patcher\tools\metadump\out\GameAssembly.dll")
META = os.environ.get("GA_METADATA", r"C:\Games\recnet-patcher\tools\metadump\out\global-metadata.dat")
IMGBASE = 0x180000000
METADATA_REGISTRATION_RAW = 0xC1A5770

T = {"string": 0x100, "typeDefinitions": 0x2269158, "fields": 0x2786E5C}
TD_N = 59728

disk = open(DLL, "rb").read()
meta = open(META, "rb").read()

pe = struct.unpack_from("<I", disk, 0x3C)[0]
nsec = struct.unpack_from("<H", disk, pe + 6)[0]
soff = pe + 24 + struct.unpack_from("<H", disk, pe + 20)[0]
secs = [struct.unpack_from("<IIII", disk, soff + i * 40 + 8) for i in range(nsec)]


def va2raw(va):
    rva = va - IMGBASE
    for vs, vaddr, rs, rp in secs:
        if vaddr <= rva < vaddr + rs:
            return rp + (rva - vaddr)
    return None


def mstr(idx):
    o = T["string"] + idx
    return meta[o:meta.index(b"\0", o)].decode("utf-8", "replace")


_mr = struct.unpack_from("<16Q", disk, METADATA_REGISTRATION_RAW)
TYPES_N, TYPES_P = _mr[6], _mr[7]
FOFF_N, FOFF_P = _mr[10], _mr[11]


def type_name(td):
    b = T["typeDefinitions"] + td * 88
    ns = struct.unpack_from("<i", meta, b + 4)[0]
    name = mstr(struct.unpack_from("<i", meta, b)[0])
    return f"{mstr(ns)}.{name}" if ns else name


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
    prim = {0x02: "bool", 0x03: "char", 0x04: "sbyte", 0x05: "byte", 0x06: "short", 0x07: "ushort",
            0x08: "int", 0x09: "uint", 0x0A: "long", 0x0B: "ulong", 0x0C: "float", 0x0D: "double",
            0x0E: "string", 0x15: "genericinst", 0x1C: "object", 0x1D: "szarray"}
    return prim.get(kind, hex(kind))


def field_offsets(td):
    p = struct.unpack_from("<Q", disk, va2raw(FOFF_P + td * 8))[0]
    return p


for want in sys.argv[1:]:
    for td in range(TD_N):
        b = T["typeDefinitions"] + td * 88
        if mstr(struct.unpack_from("<i", meta, b)[0]) != want:
            continue
        fstart = struct.unpack_from("<i", meta, b + 32)[0]
        fcount = struct.unpack_from("<H", meta, b + 68)[0]
        op = field_offsets(td)
        opr = va2raw(op) if op else None
        print(f"=== {type_name(td)}  (typedef #{td}, {fcount} field(s))")
        for k in range(fcount):
            fb = T["fields"] + (fstart + k) * 12
            nm, ti = struct.unpack_from("<2i", meta, fb)
            off = struct.unpack_from("<i", disk, opr + k * 4)[0] if opr else -1
            print(f"  {off:#06x}  {il2cpp_type(ti):40} {mstr(nm)}")
