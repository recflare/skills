"""Find typedefs that declare a field with a given name. usage: py fieldfind.py <fieldName>"""
import os, struct, sys
META = os.environ.get("GA_METADATA", r"C:\Games\recnet-patcher\tools\metadump\out\global-metadata.dat")
m = open(META, "rb").read()
def hdr(o): return struct.unpack_from("<ii", m, o)
STR = hdr(0x18)[0]; FIELDS = hdr(0x60)[0]; TD, TD_SZ = hdr(0xA0); TD_N = TD_SZ // 88
def s(i):
    o = STR + i; return m[o:m.index(b"\0", o)].decode("utf-8", "replace")
def tdname(t):
    b = TD + t * 88
    ns = struct.unpack_from("<i", m, b + 4)[0]
    nm = s(struct.unpack_from("<i", m, b)[0])
    return f"{s(ns)}.{nm}" if ns else nm
want = sys.argv[1]
for t in range(TD_N):
    b = TD + t * 88
    fs = struct.unpack_from("<i", m, b + 32)[0]; fc = struct.unpack_from("<H", m, b + 68)[0]
    for f in range(fs, fs + fc):
        if s(struct.unpack_from("<i", m, FIELDS + f * 12)[0]) == want:
            print(t, tdname(t)); break
