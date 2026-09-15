"""Direct-call xref (E8/E9 rel32) over the decrypted memory image.

mxref.py finds rip-relative *data* references; this finds who CALLs a method. Needed because
callers.py depends on Il2CppDumper's script.json, which this build cannot produce.

usage: py callxref.py <target_rva_hex> [...]
"""
import os, struct, bisect, pickle, sys
import numpy as np

MEM = os.environ.get("GA_IMAGE",    r"C:\Games\recnet-patcher\tools\metadump\out\ga_image.bin")
DLL = os.environ.get("GAMEASSEMBLY", r"C:\Games\recnet-patcher\tools\metadump\out\GameAssembly.dll")
CHUNK = 1 << 25
mem = np.frombuffer(open(MEM, "rb").read(), dtype=np.uint8)
disk = open(DLL, "rb").read()
pe = struct.unpack_from("<I", disk, 0x3C)[0]
nsec = struct.unpack_from("<H", disk, pe + 6)[0]
soff = pe + 24 + struct.unpack_from("<H", disk, pe + 20)[0]
code = []
for i in range(nsec):
    o = soff + i * 40
    vs, va, rs, rp = struct.unpack_from("<IIII", disk, o + 8)
    if struct.unpack_from("<I", disk, o + 36)[0] & 0x20:
        code.append((va, min(vs, len(mem) - va)))

tbl = pickle.load(open("methods.pkl", "rb"))
addrs = [a for a, _ in tbl]
targets = [int(a, 16) for a in sys.argv[1:]]
hits = {t: [] for t in targets}
for va, sz in code:
    for base in range(0, sz, CHUNK):
        blob = mem[va + base:va + base + min(CHUNK, sz - base) + 5]
        n = len(blob) - 5
        if n <= 0:
            continue
        disp = (blob[1:n+1].astype(np.uint32) | (blob[2:n+2].astype(np.uint32) << 8)
                | (blob[3:n+3].astype(np.uint32) << 16) | (blob[4:n+4].astype(np.uint32) << 24))
        nxt = np.arange(n, dtype=np.uint32) + np.uint32(va + base + 5)
        op = blob[0:n]
        for t in targets:
            for i in np.nonzero((disp + nxt == np.uint32(t)) & ((op == 0xE8) | (op == 0xE9)))[0]:
                hits[t].append((va + base + int(i), int(op[int(i)])))

for t in targets:
    print(f"=== 0x{t:x}: {len(hits[t])} call/jmp site(s)")
    for h, o in sorted(hits[t]):
        j = bisect.bisect_right(addrs, h) - 1
        kind = "call" if o == 0xE8 else "jmp "
        print(f"  {kind} 0x{h:x}  in 0x{addrs[j]:x}  {tbl[j][1]}" if j >= 0 else f"  {kind} 0x{h:x}")
