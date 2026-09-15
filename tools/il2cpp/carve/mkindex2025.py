"""Stage 4: build the il2cpp-tools index for recflare-2025 without Il2CppDumper.

Il2CppDumper's auto-search can't find CodeRegistration on this build (its fields are permuted and
codeGenModules is shuffled out of image order), and its PE-loader fallback dies trying to
LoadLibrary a DLL that imports Referee. Everything the tools actually need is recoverable directly:

  methods.pkl              (rva, "Namespace.Class$$Method") from metadata tokens + codeGenModules
  out/stringliteral.json   {"value", "address"} where address is the metadata-usage SLOT rva --
                           the same thing fxref.py takes as its target

Metadata-usage slots are statically initialised in .data with (kind << 29) | (index * 2 + 1); the
runtime overwrites them with real pointers, which is exactly why .data has to come from disk.
"""
import json
import os
import pickle
import struct

DLL = "out/GameAssembly.dll"
META = "out/global-metadata.dat"
OUTDIR = r"C:\Games\recnet-patcher\il2cpp-2025"
IMGBASE = 0x180000000
CODEGEN_MODULES_RAW = 0xCD16D00
CODEGEN_MODULES_N = 405

# canonical table offsets from rebuild_metadata.py
T = {
    "stringLiteral": (0x18703AC, 0x98880), "stringLiteralData": (0x2B1AF94, 0x26CA90),
    "string": (0x100, 0x5E3908), "methods": (0xAA8748, 0xD3E324),
    "typeDefinitions": (0x2269158, 0x503380), "images": (0x5E3A08, 0x3F48),
}

disk = open(DLL, "rb").read()
meta = open(META, "rb").read()

pe = struct.unpack_from("<I", disk, 0x3C)[0]
nsec = struct.unpack_from("<H", disk, pe + 6)[0]
soff = pe + 24 + struct.unpack_from("<H", disk, pe + 20)[0]
secs = []
for i in range(nsec):
    o = soff + i * 40
    name = disk[o:o + 8].rstrip(b"\0").decode()
    vs, va, rs, rp = struct.unpack_from("<IIII", disk, o + 8)
    secs.append((name, vs, va, rs, rp))


def rva2raw(rva):
    for _n, _vs, va, rs, rp in secs:
        if va <= rva < va + rs:
            return rp + (rva - va)
    return None


def va2raw(va):
    return rva2raw(va - IMGBASE) if IMGBASE <= va < IMGBASE + 0xE700000 else None


def mstr(idx):
    o = T["string"][0] + idx
    z = meta.index(b"\0", o)
    return meta[o:z].decode("utf-8", "replace")


def cstr(va, n=96):
    r = va2raw(va)
    if r is None:
        return None
    b = disk[r:r + n]
    z = b.find(b"\0")
    if z <= 0:
        return None
    s = b[:z]
    return s.decode() if all(0x20 <= c <= 0x7E for c in s) else None


# ---- codeGenModules: name -> method pointer array -------------------------------------------
modules = {}
for i in range(CODEGEN_MODULES_N):
    p = struct.unpack_from("<Q", disk, CODEGEN_MODULES_RAW + i * 8)[0]
    r = va2raw(p)
    if r is None:
        continue
    name = cstr(struct.unpack_from("<Q", disk, r)[0])
    cnt = struct.unpack_from("<I", disk, r + 8)[0]
    mp = struct.unpack_from("<Q", disk, r + 16)[0]
    if name:
        modules[name] = (cnt, mp)
print(f"codeGenModules: {len(modules)} named modules")

# Some methodPointers arrays sit in the BSS tail of .data, which has no raw bytes on disk. Those
# come from the memory image instead, where the values are runtime pointers (LOAD_BASE-relative).
mem = open("out/ga_image.bin", "rb").read()
LOAD_BASE = 0x7FFC4CB80000
from_bss = 0


def ptr_array_rvas(mp_va, count):
    """Return `count` method RVAs (0 for a null slot) from the pointer array at VA `mp_va`."""
    global from_bss
    if count == 0 or count > 500000 or not (IMGBASE <= mp_va < IMGBASE + 0xE700000):
        return None
    raw = va2raw(mp_va)
    if raw is not None:
        vals = struct.unpack_from(f"<{count}Q", disk, raw)
        return [(v - IMGBASE) if IMGBASE <= v < IMGBASE + 0xE700000 else 0 for v in vals]
    off = mp_va - IMGBASE
    if off + count * 8 > len(mem):
        return None
    from_bss += 1
    vals = struct.unpack_from(f"<{count}Q", mem, off)
    return [(v - LOAD_BASE) if LOAD_BASE <= v < LOAD_BASE + 0xE700000 else 0 for v in vals]

# ---- walk images -> types -> methods ---------------------------------------------------------
IMG_OFF, IMG_SIZE = T["images"]
TD_OFF, _ = T["typeDefinitions"]
M_OFF, _ = T["methods"]
table = []
missing = 0
for i in range(IMG_SIZE // 40):
    b = IMG_OFF + i * 40
    nameIdx, _asm, typeStart, typeCount = struct.unpack_from("<4i", meta, b)
    img_name = mstr(nameIdx)
    mod = modules.get(img_name)
    if not mod:
        missing += 1
        continue
    cnt, mp_va = mod
    rvas = ptr_array_rvas(mp_va, cnt)
    if rvas is None:
        missing += 1
        continue
    for t in range(typeStart, typeStart + typeCount):
        tb = TD_OFF + t * 88
        tname = mstr(struct.unpack_from("<i", meta, tb)[0])
        tns = struct.unpack_from("<i", meta, tb + 4)[0]
        ns = mstr(tns) if tns else ""
        mstart = struct.unpack_from("<i", meta, tb + 36)[0]
        mcount = struct.unpack_from("<H", meta, tb + 64)[0]
        full = f"{ns}.{tname}" if ns else tname
        for k in range(mstart, mstart + mcount):
            mb = M_OFF + k * 36
            mname = mstr(struct.unpack_from("<i", meta, mb)[0])
            token = struct.unpack_from("<I", meta, mb + 24)[0]
            rid = (token & 0xFFFFFF) - 1
            if not (0 <= rid < cnt):
                continue
            rva = rvas[rid]
            if not rva:
                continue
            table.append((rva, f"{full}$${mname}"))
print(f"images without a code module: {missing}; method arrays read from BSS: {from_bss}")

table.sort(key=lambda p: p[0])
os.makedirs(OUTDIR, exist_ok=True)
with open(os.path.join(OUTDIR, "methods.pkl"), "wb") as f:
    pickle.dump(table, f)
with open(os.path.join(OUTDIR, "methods.pkl.txt"), "w", encoding="utf-8") as f:
    f.write(f"{len(table)} methods\nfrom recflare-2025 (build 20250718.01) live capture\n"
            f"binary {os.path.abspath(DLL)}\nmetadata {os.path.abspath(META)}\n")
print(f"methods.pkl: {len(table)} methods")

# ---- string literal usage slots ---------------------------------------------------------------
LIT_OFF, LIT_SIZE = T["stringLiteral"]
LD_OFF, _ = T["stringLiteralData"]
nlit = LIT_SIZE // 8


def literal(i):
    ln, di = struct.unpack_from("<II", meta, LIT_OFF + i * 8)
    return meta[LD_OFF + di:LD_OFF + di + ln].decode("utf-8", "replace")


out = []
for name, _vs, va, rs, rp in secs:
    if name not in (".data", ".rdata"):
        continue
    for off in range(rp, rp + rs - 8, 8):
        v = struct.unpack_from("<Q", disk, off)[0]
        if v == 0 or v >> 32:
            continue
        if (v >> 29) != 5:
            continue
        idx = v & 0x1FFFFFFF
        if not idx & 1:
            continue
        li = (idx - 1) >> 1
        if li >= nlit:
            continue
        out.append({"value": literal(li), "address": f"0x{va + (off - rp):X}"})
os.makedirs(os.path.join(OUTDIR, "out"), exist_ok=True)
with open(os.path.join(OUTDIR, "out", "stringliteral.json"), "w", encoding="utf-8") as f:
    json.dump(out, f, indent=2, ensure_ascii=False)
print(f"stringliteral.json: {len(out)} literal usage slots")
