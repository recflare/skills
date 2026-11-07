"""Find an enum by its MEMBER names, when you do not know the type name.

`enumvals.py` needs the exact typedef name. The obfuscator re-rolls type names on every build but
**keeps enum member names and values**, so when you have a mask/flag value and no idea what declares
it, search the members instead:

    py enumfind.py subrooms tags loadscreens
      === RecNet.Rooms.RoomDetailFeatureMask : int  (typedef #23485, 22 members)
         None                            = 0
         SubRooms                        = 1
         ...
         StandardDetails                 = 767277

Every argument must match (case-insensitively, as a substring of) some member name of the same enum,
so two or three distinctive members narrow 60k typedefs to one. That is how
`include=767277` on `GET rooms/{id}` was resolved to `RoomDetailFeatureMask.StandardDetails` after
guessing type names ("RoomIncludeFlags", "RoomIncludes", …) found nothing —
see wire-shapes `references/endpoints/rooms-room-by-id-wire-shape.md`.

⚠️ **`MR` (MetadataRegistration) is build-specific.** The default below is `20250718.01`; export
`GA_MR` for another build — `0xEBF5810` for `20260323.14`. A wrong `MR` either raises
`struct.error: unpack_from requires a buffer of at least ...` or silently prints junk enum base
types, so set it together with `GA_METADATA`/`GAMEASSEMBLY`. The `idtables*` carve stages print the
replacement.

Reads the same metadata structures as enumvals.py; see that file's note on compressed-int defaults.
"""
import os, struct, sys

META = os.environ.get("GA_METADATA", r"C:\Games\recnet-patcher\tools\metadump\out\global-metadata.dat")
DLL  = os.environ.get("GAMEASSEMBLY", r"C:\Games\recnet-patcher\tools\metadump\out\GameAssembly.dll")
IMGBASE = 0x180000000
MR = int(os.environ.get("GA_MR", "0xC1A5770"), 0)

m = open(META, "rb").read(); disk = open(DLL, "rb").read()
pe = struct.unpack_from("<I", disk, 0x3C)[0]
soff = pe + 24 + struct.unpack_from("<H", disk, pe + 20)[0]
secs = []
for i in range(struct.unpack_from("<H", disk, pe + 6)[0]):
    o = soff + i * 40
    vs, va, rs, rp = struct.unpack_from("<IIII", disk, o + 8); secs.append((va, rs, rp))
def va2raw(v):
    r = v - IMGBASE
    for va, rs, rp in secs:
        if va <= r < va + rs: return rp + (r - va)
_mr = struct.unpack_from("<16Q", disk, MR); TY_P = _mr[7]
def kind_of(ti):
    p = struct.unpack_from("<Q", disk, va2raw(TY_P + ti * 8))[0]
    return (struct.unpack_from("<QI", disk, va2raw(p))[1] >> 16) & 0xFF
SIGNED = {4: "sbyte", 6: "short", 8: "int", 0xA: "long"}
UNSIGN = {2: "bool", 5: "byte", 7: "ushort", 9: "uint", 0xB: "ulong"}

def cuint(b, i):
    x = b[i]
    if x < 0x80: return x
    if x & 0xC0 == 0x80: return ((x & 0x3F) << 8) | b[i+1]
    if x & 0xE0 == 0xC0: return ((x & 0x1F) << 24) | (b[i+1] << 16) | (b[i+2] << 8) | b[i+3]
    if x == 0xF0: return struct.unpack_from("<I", b, i+1)[0]
    if x == 0xFE: return 0xFFFFFFFE
    return 0xFFFFFFFF
def cint(b, i):
    e = cuint(b, i)
    if e == 0xFFFFFFFF: return -2147483648
    neg = e & 1; e >>= 1
    return -(e + 1) if neg else e

def hdr(o): return struct.unpack_from("<ii", m, o)
STR = hdr(0x18)[0]; FDV, FDV_SZ = hdr(0x40); DV = hdr(0x48)[0]
FIELDS = hdr(0x60)[0]; TD, TD_SZ = hdr(0xA0); TD_N = TD_SZ // 88
def s(i):
    o = STR + i; return m[o:m.index(b"\0", o)].decode("utf-8", "replace")
def tdname(t):
    b = TD + t * 88
    ns = struct.unpack_from("<i", m, b + 4)[0]
    nm = s(struct.unpack_from("<i", m, b)[0])
    return f"{s(ns)}.{nm}" if ns else nm

defaults = {}
for i in range(FDV_SZ // 12):
    fi, ti, di = struct.unpack_from("<3i", m, FDV + i * 12); defaults[fi] = (ti, di)

pats = [p.lower() for p in sys.argv[1:]]
if not pats:
    sys.exit(__doc__)

for t in range(TD_N):
    b = TD + t * 88
    fs = struct.unpack_from("<i", m, b + 32)[0]; fc = struct.unpack_from("<H", m, b + 68)[0]
    base = None
    for f in range(fs, fs + fc):
        if s(struct.unpack_from("<i", m, FIELDS + f * 12)[0]) == "value__":
            base = kind_of(struct.unpack_from("<i", m, FIELDS + f * 12 + 4)[0])
    if base is None:           # not an enum
        continue
    members = []
    for f in range(fs, fs + fc):
        nm = s(struct.unpack_from("<i", m, FIELDS + f * 12)[0])
        if nm == "value__" or f not in defaults: continue
        di = defaults[f][1]
        if base in (2, 4, 5):
            v = m[DV + di]
            if base == 4 and v > 127: v -= 256
        else:
            v = cint(m, DV + di) if base in SIGNED else cuint(m, DV + di)
        members.append((nm, v))
    low = [nm.lower() for nm, _ in members]
    if not all(any(p in L for L in low) for p in pats):
        continue
    tn = SIGNED.get(base) or UNSIGN.get(base) or f"kind{base:#x}"
    print(f"=== {tdname(t)} : {tn}  (typedef #{t}, {len(members)} members)")
    for nm, v in members:
        print(f"   {nm:<44} = {v}")
