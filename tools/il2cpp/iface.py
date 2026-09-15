"""List the typedefs that implement a given interface, from carved metadata.

usage: py iface.py <InterfaceName>
"""
import os, struct, sys
META = os.environ.get("GA_METADATA", r"C:\Games\recnet-patcher\tools\metadump\out\global-metadata.dat")
m = open(META, "rb").read()
def hdr(o): return struct.unpack_from("<ii", m, o)
STR = hdr(0x18)[0]; IFACES = hdr(0x88)[0]; TD, TD_SZ = hdr(0xA0); TD_N = TD_SZ // 88
def s(i):
    o = STR + i; return m[o:m.index(b"\0", o)].decode("utf-8", "replace")
def tdname(t):
    b = TD + t * 88
    ns = struct.unpack_from("<i", m, b + 4)[0]
    nm = s(struct.unpack_from("<i", m, b)[0])
    return f"{s(ns)}.{nm}" if ns else nm
want = sys.argv[1]
# find the interface's byval type index so we can match interfaces[] entries (which are TypeIndex)
targets = {t for t in range(TD_N) if tdname(t).split(".")[-1] == want}
tgt_types = {struct.unpack_from("<i", m, TD + t * 88 + 8)[0] for t in targets}
for t in range(TD_N):
    b = TD + t * 88
    istart = struct.unpack_from("<i", m, b + 52)[0]
    icount = struct.unpack_from("<H", m, b + 76)[0]
    for k in range(istart, istart + icount):
        ti = struct.unpack_from("<i", m, IFACES + k * 4)[0]
        if ti in tgt_types:
            print(tdname(t))
