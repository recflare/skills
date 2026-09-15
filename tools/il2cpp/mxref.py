"""rip-relative xref scanned over the flattened memory image (ga_image.bin).

Two reasons this exists next to fxref.py, both specific to this build:
  * this client strips IMAGE_SCN_MEM_EXECUTE (code sections are 0xC0000020, exec is granted at
    runtime), so fxref.py's `ch & 0x20000000` section filter matches *nothing* and it silently
    reports 0 refs for every target;
  * the code comes from ga_image.bin, so it is the decrypted image rather than the raw PE.

usage: py mxref.py <target_rva_hex> [...]
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
    if struct.unpack_from("<I", disk, o + 36)[0] & 0x20:   # IMAGE_SCN_CNT_CODE
        code.append((va, min(vs, len(mem) - va)))

tbl = pickle.load(open("methods.pkl", "rb"))
addrs = [a for a, _ in tbl]

targets = [int(a, 16) for a in sys.argv[1:]]
hits = {t: [] for t in targets}
for va, sz in code:
    for base in range(0, sz, CHUNK):
        blob = mem[va + base:va + base + min(CHUNK, sz - base) + 4]
        n = len(blob) - 4
        if n <= 1:
            continue
        disp = (blob[0:n].astype(np.uint32) | (blob[1:n+1].astype(np.uint32) << 8)
                | (blob[2:n+2].astype(np.uint32) << 16) | (blob[3:n+3].astype(np.uint32) << 24))
        nxt = (np.arange(n, dtype=np.uint32) + np.uint32(va + base + 4))
        for t in targets:
            for i in np.nonzero(disp + nxt == np.uint32(t))[0]:
                i = int(i)
                if i >= 1 and (blob[i-1] & 0xC7) == 0x05:   # modrm mod=00 rm=101
                    hits[t].append(va + base + i - 1)

for t in targets:
    print(f"=== 0x{t:x}: {len(hits[t])} rip-relative ref(s)")
    for h in sorted(hits[t]):
        j = bisect.bisect_right(addrs, h) - 1
        print(f"  ref 0x{h:x}  in 0x{addrs[j]:x}  {tbl[j][1]}" if j >= 0 else f"  0x{h:x} (no method)")
