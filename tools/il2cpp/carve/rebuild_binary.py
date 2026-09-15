"""Stage 3: splice the decrypted code sections from memory back into the on-disk PE.

`.text` and `il2cpp` ship encrypted at rest (entropy 8.000) and are decrypted during il2cpp_init;
`.rdata`/`.data`/`.pdata`/`.reloc` are untouched on disk. DUMPING.md's rule is to take ONLY the code
sections from memory and everything else from the disk file, because il2cpp_init rewrites `.data`
in place (type indices become live class pointers) and a static tool then reads pointers where it
expects indices.

The memory copy was loaded at an ASLR base, so base relocations landing inside the spliced sections
are undone here, putting the code back at the file's ImageBase.
"""
import struct

DISK = r"C:\Games\recflare-2025\GameAssembly.dll"
MEM = "out/ga_image.bin"
DST = "out/GameAssembly.dll"
LOAD_BASE = 0x7FFC4CB80000      # from manifest.txt
PATCH_SECTIONS = {".text", "il2cpp"}

buf = bytearray(open(DISK, "rb").read())
mem = open(MEM, "rb").read()

e = struct.unpack_from("<I", buf, 0x3C)[0]
nsec = struct.unpack_from("<H", buf, e + 6)[0]
optoff = e + 24
optsize = struct.unpack_from("<H", buf, e + 20)[0]
imgbase = struct.unpack_from("<Q", buf, optoff + 24)[0]
relrva, relsz = struct.unpack_from("<II", buf, optoff + 112 + 5 * 8)
sect = optoff + optsize

secs = []
for i in range(nsec):
    o = sect + i * 40
    name = buf[o:o + 8].rstrip(b"\0").decode()
    vs, va, rs, pr = struct.unpack_from("<IIII", buf, o + 8)
    secs.append((name, vs, va, rs, pr))

def rva_to_raw(rva):
    for name, vs, va, rs, pr in secs:
        if va <= rva < va + max(vs, rs):
            return pr + (rva - va)
    return None

delta = LOAD_BASE - imgbase
print(f"ImageBase={imgbase:#x} LoadBase={LOAD_BASE:#x} delta={delta:#x}")

patched = []
for name, vs, va, rs, pr in secs:
    if name not in PATCH_SECTIONS:
        continue
    n = min(vs, rs)
    buf[pr:pr + n] = mem[va:va + n]
    patched.append((va, va + vs))
    print(f"spliced {name:8} rva {va:#x}..{va+vs:#x} -> raw {pr:#x} ({n} bytes)")

# ---- undo base relocations inside the spliced ranges ---------------------------------------
relraw = rva_to_raw(relrva)
p, end = relraw, relraw + relsz
fixed = skipped = 0
while p < end:
    page, blk = struct.unpack_from("<II", buf, p)
    if blk == 0:
        break
    for q in range(p + 8, p + blk, 2):
        ent = struct.unpack_from("<H", buf, q)[0]
        typ, off = ent >> 12, ent & 0xFFF
        if typ == 0:
            continue
        rva = page + off
        if not any(lo <= rva < hi for lo, hi in patched):
            skipped += 1
            continue
        raw = rva_to_raw(rva)
        if raw is None:
            continue
        if typ == 10:  # DIR64
            v = struct.unpack_from("<Q", buf, raw)[0]
            struct.pack_into("<Q", buf, raw, (v - delta) & 0xFFFFFFFFFFFFFFFF)
            fixed += 1
        elif typ == 3:  # HIGHLOW
            v = struct.unpack_from("<I", buf, raw)[0]
            struct.pack_into("<I", buf, raw, (v - delta) & 0xFFFFFFFF)
            fixed += 1
    p += blk
print(f"relocations undone inside spliced code: {fixed} (outside: {skipped})")

open(DST, "wb").write(bytes(buf))
print(f"wrote {DST} ({len(buf)} bytes)")
