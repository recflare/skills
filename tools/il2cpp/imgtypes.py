"""List the types (and optionally methods) an image/assembly contributes, from carved metadata.

Useful for version-fingerprinting a bundled package when assembly versions are stripped to 0.0.0.0,
which Unity does for asmdef-compiled and UPM packages.

usage: py imgtypes.py <image-name-substring> [--methods <TypeName>]
"""
import os, struct, sys

META = os.environ.get("GA_METADATA", r"C:\Games\recnet-patcher\tools\metadump\out\global-metadata.dat")
meta = open(META, "rb").read()
STR = 0x100
IMG = (0x5E3A08, 0x3F48)
TD = 0x2269158
M = 0xAA8748


def s(i):
    o = STR + i
    return meta[o:meta.index(b"\0", o)].decode("utf-8", "replace")


want = sys.argv[1].lower()
show_methods = sys.argv[2] if len(sys.argv) > 2 else None

for i in range(IMG[1] // 40):
    b = IMG[0] + i * 40
    nameIdx, _asm, typeStart, typeCount = struct.unpack_from("<4i", meta, b)
    img = s(nameIdx)
    if want not in img.lower():
        continue
    print(f"=== {img}  ({typeCount} types)")
    for t in range(typeStart, typeStart + typeCount):
        tb = TD + t * 88
        nm = s(struct.unpack_from("<i", meta, tb)[0])
        nsi = struct.unpack_from("<i", meta, tb + 4)[0]
        ns = s(nsi) if nsi else ""
        full = f"{ns}.{nm}" if ns else nm
        if show_methods and show_methods.lower() not in nm.lower():
            continue
        print("   ", full)
        if show_methods:
            ms = struct.unpack_from("<i", meta, tb + 36)[0]
            mc = struct.unpack_from("<H", meta, tb + 64)[0]
            for k in range(ms, ms + mc):
                print("        ", s(struct.unpack_from("<i", meta, M + k * 36)[0]))
