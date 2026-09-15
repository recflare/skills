"""Stage 2b of the carve: identify each of the 31 metadata regions by its actual contents.

The tiling from solve_header.py gives 31 (offset, size) regions in file order, but the file layout is
shuffled too, so region k is NOT canonical table k. Identify them by what they contain:

  string blob          - holds "mscorlib.dll" / "Assembly-CSharp.dll" (identifier names)
  stringLiteralData    - holds user string literals ("curatedlists/bulk")
  stringLiteral        - 8-byte (length, dataIndex) pairs that tile stringLiteralData exactly
  ...and the rest by struct stride + every string index landing on a real string.
"""
import struct
import sys
from collections import namedtuple

Region = namedtuple("Region", "idx off size")

PATH = sys.argv[1] if len(sys.argv) > 1 else "out/metadata.bin"
data = open(PATH, "rb").read()

# From solve_header.py (unique tiling).
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
REGIONS = [Region(i, o, s) for i, (o, s) in enumerate(LAYOUT)]


def blob_has(r, needle):
    return data.find(needle, r.off, r.off + r.size) >= 0


def is_cstr_at(blob_off, blob_len, idx, maxlen=512):
    """Does `idx` point at a plausible NUL-terminated ASCII string inside the blob?"""
    if idx < 0 or idx >= blob_len:
        return False
    p = blob_off + idx
    end = blob_off + blob_len
    n = 0
    while p < end and n < maxlen:
        c = data[p]
        if c == 0:
            return n > 0
        if c < 0x20 or c > 0x7E:
            return False
        p += 1
        n += 1
    return False


def find_string_blob():
    for r in REGIONS:
        if r.size and blob_has(r, b"mscorlib.dll\0") and blob_has(r, b"Assembly-CSharp.dll\0"):
            return r
    return None


def find_literal_data():
    for r in REGIONS:
        if r.size and blob_has(r, b"curatedlists/bulk"):
            return r
    return None


def find_literal_table(litdata):
    """8-byte (length, dataIndex) entries that tile the literal blob from 0."""
    best = []
    for r in REGIONS:
        if not r.size or r.size % 8:
            continue
        n = r.size // 8
        ent = struct.unpack_from(f"<{n*2}I", data, r.off)
        ok, cursor = True, 0
        for i in range(n):
            ln, di = ent[2 * i], ent[2 * i + 1]
            if di != cursor or ln > litdata.size or di + ln > litdata.size:
                ok = False
                break
            cursor = di + ln
        if ok and n > 1000 and litdata.size - cursor < 64:
            best.append((r, n, cursor))
    return best


sblob = find_string_blob()
ldata = find_literal_data()
print(f"string blob        = region {sblob.idx}  off={sblob.off:#x} size={sblob.size:#x}")
print(f"stringLiteralData  = region {ldata.idx}  off={ldata.off:#x} size={ldata.size:#x}")

cands = find_literal_table(ldata)
for r, n, cursor in cands:
    print(f"stringLiteral      = region {r.idx}  off={r.off:#x} size={r.size:#x} "
          f"-> {n} literals, tiled {cursor:#x} of {ldata.size:#x}")
if not cands:
    print("stringLiteral      = NOT FOUND (no 8-byte region tiles the literal blob)")

print("\n# region strides that could be struct arrays whose first 2 u32 are string-blob offsets")
for r in REGIONS:
    if r.size == 0 or r.idx in (sblob.idx, ldata.idx):
        continue
    hits = []
    for stride in range(4, 100, 4):
        if r.size % stride:
            continue
        n = r.size // stride
        if n < 4:
            continue
        step = max(1, n // 200)
        ok0 = ok1 = True
        checked = 0
        for i in range(0, n, step):
            a, b = struct.unpack_from("<2I", data, r.off + i * stride)
            if not is_cstr_at(sblob.off, sblob.size, a):
                ok0 = False
            if not is_cstr_at(sblob.off, sblob.size, b):
                ok1 = False
            checked += 1
            if not ok0 and not ok1:
                break
        if ok0:
            hits.append(f"{stride}(f0 str,n={n})")
        if ok1:
            hits.append(f"{stride}(f1 str,n={n})")
    if hits:
        print(f"  region {r.idx:2} size={r.size:#9x}: " + "  ".join(hits))
