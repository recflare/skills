"""Find a 32-bit IMMEDIATE in the code image and attribute it to a method.

The complement to `mxref.py`: that one chases rip-relative references to a slot, this one chases a
plain constant baked into an instruction — a flags mask, an enum value, a service id, a magic number.

    py immfind.py 767277 265354
      === 767277 (0xbb52d)
        0x95b625c  prevbyte=0x40  JUUTUQGAYFD$$TBQSRACEFUX @ 0x95b61c0 (+0x9c)
        0x95c5e20  prevbyte=0x48  VBVXDSOHTWJ$$TBQSRACEFUX @ 0x95c5dc0 (+0x60)
      === 265354 (0x40c8a)
        -- 0 hit(s)

Arguments are parsed with base 0, so `0xBB52D` and `767277` both work.

This is what proves a client *never sends* a value: `RoomDetailFeatureMask.ReplicationDetails`
(265354) has zero hits, while `StandardDetails` (767277) is hardcoded at both `include` call sites —
see wire-shapes `references/endpoints/rooms-room-by-id-wire-shape.md`.

Needs `GA_IMAGE`, `GAMEASSEMBLY`, and `methods.pkl` in the current directory. Build-agnostic: reads
`ga_image.bin` by RVA (the flattened image is indexed directly by RVA) and takes the code-section
list from the on-disk PE by `IMAGE_SCN_CNT_CODE`, never by `MEM_EXECUTE` — this client strips the
exec bit, which is the bug that made `fxref.py` report 0 refs for everything.

⚠️ Three caveats, all of them visible in real output:
  * **A match is a byte pattern, not a decoded operand.** Any 4 aligned-or-not bytes that happen to
    equal the value match — including displacements, float payloads and jump tables. `prevbyte` is
    printed so you can sanity-check the opcode: `0xB8`-`0xBF` is `mov r32, imm32`, `0x68` is `push`,
    `0x3D`/`0x81`/`0x25` are `cmp`/`and` forms. A hit inside a vectorised math routine at a
    multi-hundred-kB offset from its "owner" is data, not code.
  * **Owner attribution is by containment in `methods.pkl`**, so a hit in a generic-shared body or
    in padding is credited to the preceding name. Confirm with `fstart.py`.
  * **Small values are useless here** — scanning for 1, 2 or 8 returns thousands of hits. The tool
    earns its keep from values above ~0x1000.
"""
import os, struct, pickle, sys, bisect

MEM = os.environ.get("GA_IMAGE")
DLL = os.environ.get("GAMEASSEMBLY")
if not MEM or not DLL:
    sys.exit("set GA_IMAGE and GAMEASSEMBLY")
if not sys.argv[1:]:
    sys.exit(__doc__)

mem = open(MEM, "rb").read()
disk = open(DLL, "rb").read()
pe = struct.unpack_from("<I", disk, 0x3C)[0]
soff = pe + 24 + struct.unpack_from("<H", disk, pe + 20)[0]
code = []
for i in range(struct.unpack_from("<H", disk, pe + 6)[0]):
    o = soff + i * 40
    vs, va, rs, rp = struct.unpack_from("<IIII", disk, o + 8)
    if struct.unpack_from("<I", disk, o + 36)[0] & 0x20:      # IMAGE_SCN_CNT_CODE
        code.append((va, min(vs, len(mem) - va)))

tbl = sorted(pickle.load(open("methods.pkl", "rb")))
addrs = [a for a, _ in tbl]
def owner(rva):
    i = bisect.bisect_right(addrs, rva) - 1
    if i < 0: return "?"
    return f"{tbl[i][1]} @ {hex(tbl[i][0])} (+{rva - tbl[i][0]:#x})"

for arg in sys.argv[1:]:
    val = int(arg, 0)
    pat = struct.pack("<I", val & 0xFFFFFFFF)
    print(f"=== {val} ({val:#x})")
    n = 0
    for va, sz in code:
        blob = mem[va:va + sz]
        j = blob.find(pat)
        while j != -1:
            prev = blob[j - 1] if j else 0
            print(f"  {hex(va + j)}  prevbyte={prev:#02x}  {owner(va + j)}")
            n += 1
            j = blob.find(pat, j + 1)
    print(f"  -- {n} hit(s)")
