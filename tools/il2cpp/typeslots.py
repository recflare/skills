"""Find the metadata-usage slots (kind 1 TypeInfo / kind 2 Il2CppType) for a type name.

Reverse of slots2025.py: given a type, find the .data slots that reference it, so mxref.py can then
list every method that touches that type.

usage: py typeslots.py <TypeName>
"""
import os, struct, sys

DLL  = os.environ.get("GAMEASSEMBLY", r"C:\Games\recnet-patcher\tools\metadump\out\GameAssembly.dll")
META = os.environ.get("GA_METADATA",  r"C:\Games\recnet-patcher\tools\metadump\out\global-metadata.dat")
IMGBASE = 0x180000000
MR = 0xC1A5770
T = {"string": 0x100, "typeDefinitions": 0x2269158}

disk = open(DLL, "rb").read(); meta = open(META, "rb").read()
pe = struct.unpack_from("<I", disk, 0x3C)[0]
nsec = struct.unpack_from("<H", disk, pe + 6)[0]
soff = pe + 24 + struct.unpack_from("<H", disk, pe + 20)[0]
secs = []
for i in range(nsec):
    o = soff + i * 40
    name = disk[o:o+8].rstrip(b"\0").decode()
    vs, va, rs, rp = struct.unpack_from("<IIII", disk, o + 8)
    secs.append((name, vs, va, rs, rp))

def va2raw(va):
    r = va - IMGBASE
    for _n, vs, va2, rs, rp in secs:
        if va2 <= r < va2 + rs:
            return rp + (r - va2)

def s(i):
    o = T["string"] + i
    return meta[o:meta.index(b"\0", o)].decode("utf-8", "replace")

def tname(td):
    b = T["typeDefinitions"] + td * 88
    ns = struct.unpack_from("<i", meta, b + 4)[0]
    nm = s(struct.unpack_from("<i", meta, b)[0])
    return f"{s(ns)}.{nm}" if ns else nm

mr = struct.unpack_from("<16Q", disk, MR)
TYPES_N, TYPES_P = mr[6], mr[7]
want = sys.argv[1]
hits = []
for _n, vs, va, rs, rp in secs:
    if _n not in (".data", ".rdata"):
        continue
    for off in range(rp, rp + rs - 8, 8):
        v = struct.unpack_from("<Q", disk, off)[0]
        if v == 0 or v >> 32:
            continue
        kind, idx = v >> 29, v & 0x1FFFFFFF
        if kind not in (1, 2) or not idx & 1:
            continue
        ti = (idx - 1) >> 1
        if not (0 <= ti < TYPES_N):
            continue
        p = struct.unpack_from("<Q", disk, va2raw(TYPES_P + ti * 8))[0]
        r = va2raw(p)
        if r is None:
            continue
        data, bits = struct.unpack_from("<QI", disk, r)
        if ((bits >> 16) & 0xFF) not in (0x11, 0x12):
            continue
        nm = tname(data & 0xFFFFFFFF)
        if nm.endswith("." + want) or nm == want:
            hits.append((va + (off - rp), kind, nm))
for rva, kind, nm in hits:
    print(f"  slot {rva:#x}  kind={kind}  {nm}")
print(f"{len(hits)} slot(s)")
