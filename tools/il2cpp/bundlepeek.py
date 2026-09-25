"""Decompress one or more UnityFS bundles and report which contain a given string.

Same UnityFS/LZ4 path as bundlescan.py (including the version>=7 header alignment fix),
but pointed at named bundles instead of a whole directory -- the confirmation step after
aacatalog.py says which bundle owns an asset.

usage: py bundlepeek.py <bundle-dir> <a.bundle,b.bundle,...> <needle,needle,...>
"""
import os, sys, struct
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lz4b import lz4_decompress

BUN = sys.argv[1] if len(sys.argv) > 1 else "."

def payload(p):
    b = open(p, "rb").read()
    if b[:7] != b"UnityFS":
        return None
    o = b.index(b"\0") + 1
    ver = struct.unpack_from(">I", b, o)[0]; o += 4
    o = b.index(b"\0", o) + 1; o = b.index(b"\0", o) + 1
    _size, cbi, ubi, flags = struct.unpack_from(">QIII", b, o); o += 20
    if ver >= 7 or (flags & 0x200):          # see unity-bundle-text-scanning.md
        o = (o + 15) & ~15
    bi = lz4_decompress(b[o:o+cbi], ubi) if (flags & 0x3F) in (2, 3) else b[o:o+cbi]
    o += cbi
    q = 16; cnt = struct.unpack_from(">I", bi, q)[0]; q += 4
    blocks = [struct.unpack_from(">IIH", bi, q + 10 * i) for i in range(cnt)]
    for start in (o, (o + 15) & ~15):
        pp = start; acc = bytearray()
        try:
            for us, cs, fl in blocks:
                acc += lz4_decompress(b[pp:pp+cs], us) if (fl & 0x3F) in (2, 3) else b[pp:pp+cs]
                pp += cs
            return bytes(acc)
        except Exception:
            continue
    return None

if __name__ == "__main__":          # importable: `from bundlepeek import payload`
    needles = [n.encode() for n in sys.argv[3].split(",")]
    for bn in sys.argv[2].split(","):
        data = payload(os.path.join(BUN, bn))
        if data is None:
            print(bn, "DECODE FAILED"); continue
        found = [n.decode() for n in needles if n in data]
        print("%-45s %9d B payload  hits: %s" % (bn, len(data), found if found else "-"))
