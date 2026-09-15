"""Pass 2: map the non-object-T send slots to owning methods and their route literals."""
import bisect, os, pickle, struct
import numpy as np
DLL  = os.environ.get("GAMEASSEMBLY", r"C:\Games\recnet-patcher\tools\metadump\out\GameAssembly.dll")
META = os.environ.get("GA_METADATA",  r"C:\Games\recnet-patcher\tools\metadump\out\global-metadata.dat")
IMGBASE = 0x180000000
disk = open(DLL, "rb").read(); m = open(META, "rb").read()
pe = struct.unpack_from("<I", disk, 0x3C)[0]
soff = pe + 24 + struct.unpack_from("<H", disk, pe + 20)[0]
secs, code = [], []
for i in range(struct.unpack_from("<H", disk, pe + 6)[0]):
    o = soff + i * 40
    vs, va, rs, rp = struct.unpack_from("<IIII", disk, o + 8)
    ch = struct.unpack_from("<I", disk, o + 36)[0]
    secs.append((va, max(vs, rs), rp, rs))
    if ch & 0x20: code.append((va, rp, rs))
def rva2raw(r):
    for va, sz, rp, rs in secs:
        if va <= r < va + sz and (r - va) < rs: return rp + (r - va)
def hdr(o): return struct.unpack_from("<ii", m, o)
STR = hdr(0x18)[0]; SL, SLN = hdr(0x08); SLD = hdr(0x10)[0]
def lit(i):
    ln, di = struct.unpack_from("<II", m, SL + i * 8)
    return m[SLD + di: SLD + di + ln].decode("utf-8", "replace")
tbl = pickle.load(open("methods.pkl", "rb")); addrs = [a for a, _ in tbl]
targets = pickle.load(open("_sendtargets.pkl", "rb"))
tgt = np.array(sorted(targets), dtype=np.int64)
owners = {}
for va, rp, rs in code:
    buf = np.frombuffer(disk[rp:rp+rs], dtype=np.uint8)
    d32 = np.frombuffer(disk[rp:rp+rs-4], dtype=np.int32)
    # candidate: any 4-byte disp whose rip-target (assume 7-byte lea/mov: next = pos+... ) hits a target
    for insn_len in (7, 8):
        pos = np.arange(len(d32))
        dst = va + pos + insn_len + d32.astype(np.int64)
        hit = np.isin(dst, tgt)
        for p in np.nonzero(hit)[0]:
            slot = int(va + p + insn_len + int(d32[p]))
            rva = int(va + p - 3)
            j = bisect.bisect_right(addrs, rva) - 1
            owners.setdefault(slot, set()).add(tbl[j][1] if j >= 0 else "?")
# route literal per owner method: scan its slots for string literals containing '/'
def method_lits(name):
    for a, n in tbl:
        if n == name: start = a; break
    else: return []
    j = bisect.bisect_right(addrs, start)
    end = tbl[j][0] if j < len(tbl) else start + 0x400
    out = []
    for r in range(start, min(end, start + 0x800)):
        raw = rva2raw(r)
        if raw is None: continue
        v = struct.unpack_from("<Q", disk, raw)[0]
        if v == 0 or v >> 32: continue
        k, idx = v >> 29, v & 0x1FFFFFFF
        if k == 5 and idx & 1:
            s = lit((idx - 1) >> 1)
            if "/" in s or s.islower(): out.append(s)
    return out
rows = []
for slot, (send, T) in sorted(targets.items(), key=lambda kv: kv[1][1]):
    for o in sorted(owners.get(slot, {"<no ref found>"})):
        rows.append((T, o, send))
seen = set()
for T, o, send in rows:
    if (T, o) in seen: continue
    seen.add((T, o))
    print(f"{T:<46} {o}")
