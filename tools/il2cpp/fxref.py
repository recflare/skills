"""Fast rip-relative xref: same job as xref.py, vectorised with numpy + methods.pkl.

xref.py loops over every byte of .text in pure Python and then streams script.json;
this does the same scan as an array compare and resolves names from methods.pkl.

usage: py fxref.py <target_rva_hex> [...]
"""
import struct, bisect, pickle, sys
import numpy as np

DLL = __import__("os").environ.get("GAMEASSEMBLY", r"C:\Games\recflare-client\GameAssembly.dll")
data = open(DLL, "rb").read()
pe = struct.unpack_from("<I", data, 0x3C)[0]
nsec = struct.unpack_from("<H", data, pe + 6)[0]
optsz = struct.unpack_from("<H", data, pe + 20)[0]
soff = pe + 24 + optsz

tbl = pickle.load(open("methods.pkl", "rb"))
addrs = [a for a, _ in tbl]

secs = []
for i in range(nsec):
    o = soff + i * 40
    vs, va, rs, rp = struct.unpack_from("<IIII", data, o + 8)
    ch = struct.unpack_from("<I", data, o + 36)[0]
    # NB: filter on IMAGE_SCN_CNT_CODE, not MEM_EXECUTE. Rec Room ships .text/il2cpp as
    # 0xC0000020 (exec is granted at runtime), so a MEM_EXECUTE filter matches nothing and
    # this script silently reports "0 refs" for every target. See mxref.py.
    if ch & 0x20:
        secs.append((va, rp, rs))

for arg in sys.argv[1:]:
    target = int(arg, 16)
    hits = []
    for va, rp, rs in secs:
        blob = np.frombuffer(data[rp:rp + rs], dtype=np.uint8)
        # disp32 at file index i covers bytes i..i+3; next-insn rva == va+i+4 for the
        # no-trailing-immediate forms (lea/mov reg,[rip+d]) -- so the stored disp must be
        # target - (va+i+4). Build that expected array once and compare as int32.
        n = len(blob) - 4
        disp = blob[0:n].astype(np.int32) | (blob[1:n + 1].astype(np.int32) << 8) \
             | (blob[2:n + 2].astype(np.int32) << 16) | (blob[3:n + 3].astype(np.int32) << 24)
        want = (target - (va + np.arange(n, dtype=np.int64) + 4)).astype(np.int32)
        cand = np.nonzero(disp == want)[0]
        for i in cand:
            i = int(i)
            if i >= 1 and (blob[i - 1] & 0xC7) == 0x05:   # modrm mod=00 rm=101
                hits.append(va + i - 1)
    print(f"=== 0x{target:x}: {len(hits)} rip-relative ref(s)")
    for h in hits:
        j = bisect.bisect_right(addrs, h) - 1
        if j < 0:
            print(f"  0x{h:x}  (no method below)")
            continue
        print(f"  ref 0x{h:x}  in 0x{addrs[j]:x}  {tbl[j][1]}")
