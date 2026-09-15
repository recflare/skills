"""Stage 2e: write a canonical global-metadata.dat from the captured allocation.

Takes the 31 regions identified by idtables*.py, emits a standard Il2CppGlobalMetadataHeader
(magic 0xFAB11BAF, version 31, tables in canonical order) over the captured body, and repairs the
deliberately corrupted <Module> type definitions (junk nameIndex / genericContainerIndex) that
otherwise make Cpp2IL and Il2CppDumper fall over.
"""
import struct

SRC = "out/metadata.bin"
DST = "out/global-metadata.dat"
LENGTH = 0x2DBD894          # from solve_header.py; the allocation is page-rounded past this
VERSION = 31

# canonical header order -> (offset, size) recovered from the shuffled header
TABLES = [
    ("stringLiteral",                        0x18703AC, 0x98880),
    ("stringLiteralData",                    0x2B1AF94, 0x26CA90),
    ("string",                               0x100,     0x5E3908),
    ("events",                               0x618758,  0xA950),
    ("properties",                           0x1BF6E4C, 0x173888),
    ("methods",                              0xAA8748,  0xD3E324),
    ("parameterDefaultValues",               0x2A8BC34, 0x21990),
    ("fieldDefaultValues",                   0x17E6A6C, 0x89940),
    ("fieldAndParameterDefaultValueData",    0x2AB13E8, 0x69BAC),
    ("fieldMarshaledSizes",                  0x2D900B4, 0x2D7E0),
    ("parameters",                           0x6230A8,  0x407CE8),
    ("fields",                               0x2786E5C, 0x2C0424),
    ("genericParameters",                    0x2A4BEE4, 0x3FD50),
    ("genericParameterConstraints",          0x2A47280, 0x4C64),
    ("genericContainers",                    0x1ECEEB4, 0x21DD0),
    ("nestedTypes",                          0x1EF509C, 0x1B5D0),
    ("interfaces",                           0x276C4D8, 0x1A984),
    ("vtableMethods",                        0x1F1066C, 0x31D7F8),
    ("interfaceOffsets",                     0xA2AD90,  0x7D9B8),
    ("typeDefinitions",                      0x2269158, 0x503380),
    ("images",                               0x5E3A08,  0x3F48),
    ("assemblies",                           0x2D87A24, 0x6540),
    ("fieldRefs",                            0x1EF0C84, 0x4418),
    ("referencedAssemblies",                 0x2AAD5C4, 0x3E24),
    ("attributeData",                        0x1908C2C, 0x2EE220),
    ("attributeDataRange",                   0x1D6A6D4, 0x1647E0),
    ("unresolvedIndirectCallParameterTypes", 0x222DE64, 0x3B2F4),
    ("unresolvedIndirectCallParameterRanges",0x5E7950,  0x30E08),
    ("windowsRuntimeTypeNames",              0x6230A8,  0x0),
    ("windowsRuntimeStrings",                0xAA8748,  0x0),
    ("exportedTypeDefinitions",              0x2D8DF64, 0x2150),
]
assert len(TABLES) == 31

buf = bytearray(open(SRC, "rb").read()[:LENGTH])

hdr = struct.pack("<Ii", 0xFAB11BAF, VERSION)
for _n, off, size in TABLES:
    hdr += struct.pack("<ii", off, size)
assert len(hdr) == 0x100, len(hdr)
buf[:0x100] = hdr

# ---- repair the corrupted <Module> typedefs -----------------------------------------------
STR_OFF, STR_SIZE = 0x100, 0x5E3908
TD_OFF, TD_SIZE = 0x2269158, 0x503380
IMG_OFF, IMG_SIZE = 0x5E3A08, 0x3F48
ntd = TD_SIZE // 88

mod = buf.find(b"<Module>\x00", STR_OFF, STR_OFF + STR_SIZE)
assert mod > 0, "<Module> not found in the string blob"
mod_idx = mod - STR_OFF
print(f"<Module> string index = {mod_idx:#x}")


def valid_str(idx):
    if not (0 <= idx < STR_SIZE):
        return False
    p = STR_OFF + idx
    n = 0
    while p < STR_OFF + STR_SIZE and n < 256:
        c = buf[p]
        if c == 0:
            return n > 0
        if c < 0x20 or c > 0x7E:
            return False
        p += 1
        n += 1
    return False


NGC = 8669
fixed_name = fixed_gc = 0
for i in range(ntd):
    b = TD_OFF + i * 88
    name = struct.unpack_from("<i", buf, b)[0]
    gc = struct.unpack_from("<i", buf, b + 24)[0]
    if not valid_str(name):
        struct.pack_into("<i", buf, b, mod_idx)
        fixed_name += 1
    if not (gc == -1 or 0 <= gc < NGC):
        struct.pack_into("<i", buf, b + 24, -1)
        fixed_gc += 1
print(f"repaired {fixed_name} nameIndex and {fixed_gc} genericContainerIndex fields "
      f"across {ntd} type definitions ({IMG_SIZE // 40} images)")

open(DST, "wb").write(bytes(buf))
print(f"wrote {DST} ({len(buf)} bytes)")
