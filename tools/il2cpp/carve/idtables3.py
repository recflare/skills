"""Stage 2d: pin the last 16 tables.

Chains outward from what is already known:
  images(405) -> assemblies(405) -> referencedAssemblies (sum of referencedAssemblyCount)
  typeDefs/methods genericContainerIndex -> genericContainers -> genericParameters -> constraints
  attributeDataRange is (token, startOffset) with startOffset monotone, tiling attributeData
  the three 12-byte side tables are told apart by which index space their first field lives in
"""
import struct

data = open("out/metadata.bin", "rb").read()

LAYOUT = [
    (0x100, 0x5E3908), (0x5E3A08, 0x3F48), (0x5E7950, 0x30E08), (0x618758, 0xA950),
    (0x6230A8, 0x0), (0x6230A8, 0x407CE8), (0xA2AD90, 0x7D9B8), (0xAA8748, 0x0),
    (0xAA8748, 0xD3E324), (0x17E6A6C, 0x89940), (0x18703AC, 0x98880), (0x1908C2C, 0x2EE220),
    (0x1BF6E4C, 0x173888), (0x1D6A6D4, 0x1647E0), (0x1ECEEB4, 0x21DD0), (0x1EF0C84, 0x4418),
    (0x1EF509C, 0x1B5D0), (0x1F1066C, 0x31D7F8), (0x222DE64, 0x3B2F4), (0x2269158, 0x503380),
    (0x276C4D8, 0x1A984), (0x2786E5C, 0x2C0424), (0x2A47280, 0x4C64), (0x2A4BEE4, 0x3FD50),
    (0x2A8BC34, 0x21990), (0x2AAD5C4, 0x3E24), (0x2AB13E8, 0x69BAC), (0x2B1AF94, 0x26CA90),
    (0x2D87A24, 0x6540), (0x2D8DF64, 0x2150), (0x2D900B4, 0x2D7E0),
]
KNOWN = {0: "string", 1: "images", 3: "events", 5: "parameters", 6: "interfaceOffsets",
         8: "methods", 10: "stringLiteral", 12: "properties", 16: "nestedTypes",
         17: "vtableMethods", 19: "typeDefinitions", 20: "interfaces", 21: "fields",
         27: "stringLiteralData", 28: "assemblies"}
NFIELD, NMETHOD, NPARAM, NTYPE = 240387, 385729, 352190, 59728

# ---- referencedAssemblies -----------------------------------------------------------------
aoff, asize = LAYOUT[28]
nasm = asize // 64
ref_max = 0
for i in range(nasm):
    _img, _tok, rstart, rcount = struct.unpack_from("<4i", data, aoff + i * 64)
    if rstart >= 0:
        ref_max = max(ref_max, rstart + rcount)
print(f"assemblies={nasm}  referencedAssemblies count={ref_max} -> want size {ref_max*4:#x} "
      f"regions {[i for i,(o,s) in enumerate(LAYOUT) if s == ref_max*4]}")

# ---- genericContainers --------------------------------------------------------------------
toff, _ = LAYOUT[19]
moff, _ = LAYOUT[8]
gc = -1
for i in range(NTYPE):
    v = struct.unpack_from("<i", data, toff + i * 88 + 24)[0]
    if 0 <= v < 1_000_000:
        gc = max(gc, v)
for i in range(NMETHOD):
    v = struct.unpack_from("<i", data, moff + i * 36 + 20)[0]
    if 0 <= v < 1_000_000:
        gc = max(gc, v)
ngc = gc + 1
print(f"genericContainers count={ngc} -> want size {ngc*16:#x} "
      f"regions {[i for i,(o,s) in enumerate(LAYOUT) if s == ngc*16]}")

# ---- everything else: validator sweep -----------------------------------------------------
def sample(n, cap=4000):
    step = max(1, n // cap)
    return range(0, n, step)

def try_generic_params(off, n):
    """Il2CppGenericParameter: ownerIndex, nameIndex, constraintsStart/Count/num/flags (u16)."""
    cmax = 0
    for i in sample(n):
        owner, name = struct.unpack_from("<2i", data, off + i * 16)
        cs, cc, num, _fl = struct.unpack_from("<4H", data, off + i * 16 + 8)
        if not (0 <= owner < ngc) or not (0 <= name < LAYOUT[0][1]):
            return None
        cmax = max(cmax, cs + cc)
    return cmax

def first_field_range(off, stride, n, lo, hi):
    for i in sample(n):
        v = struct.unpack_from("<i", data, off + i * stride)[0]
        if not (lo <= v < hi):
            return False
    return True

def monotone_pairs(off, n):
    """attributeDataRange: (token, startOffset) with startOffset non-decreasing."""
    prev = -1
    for i in range(n):
        _tok, start = struct.unpack_from("<2I", data, off + i * 8)
        if start < prev:
            return None
        prev = start
    return prev  # final startOffset == size of the attribute blob

print("\n# candidate roles for the unassigned regions")
for idx, (off, size) in enumerate(LAYOUT):
    if idx in KNOWN or size == 0:
        continue
    notes = []
    if size % 16 == 0:
        r = try_generic_params(off, size // 16)
        if r is not None:
            notes.append(f"genericParameters(n={size//16}, constraints_max={r})")
    if size % 12 == 0:
        n = size // 12
        if first_field_range(off, 12, n, 0, NFIELD):
            notes.append(f"field-indexed 12B (n={n})  [fieldDefaultValues|fieldMarshaledSizes]")
        if first_field_range(off, 12, n, 0, NPARAM):
            notes.append(f"param-indexed 12B (n={n})  [parameterDefaultValues]")
    if size % 8 == 0:
        n = size // 8
        m = monotone_pairs(off, n)
        if m is not None:
            notes.append(f"monotone (u32,u32) n={n} last={m:#x}  [attributeDataRange?]")
        if first_field_range(off, 8, n, 0, NTYPE):
            notes.append(f"type-indexed 8B (n={n})  [fieldRefs?]")
    if size % 4 == 0:
        n = size // 4
        if first_field_range(off, 4, n, 0, ngc if ngc else 1):
            notes.append(f"gc-indexed 4B (n={n})")
    printable = sum(1 for b in data[off:off + min(size, 4096)] if 0x20 <= b <= 0x7E or b == 0)
    if printable > min(size, 4096) * 0.95:
        notes.append("looks like a blob of text/zeros")
    print(f"  region {idx:2} size={size:#9x}: " + ("; ".join(notes) if notes else "-"))
