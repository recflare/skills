"""Join non-object-T send slots -> owning method -> its route literal(s).

Disassembles each owning method and resolves rip-relative operands against the string-literal
slot table (same technique as names.py), which is the only correct way to find its route.
"""
import bisect, json, os, pickle, re, struct
from capstone import Cs, CS_ARCH_X86, CS_MODE_64, x86
DLL = os.environ.get("GAMEASSEMBLY", r"C:\Games\recnet-patcher\tools\metadump\out\GameAssembly.dll")
data = open(DLL, "rb").read()
pe = struct.unpack_from("<I", data, 0x3C)[0]
soff = pe + 24 + struct.unpack_from("<H", data, pe + 20)[0]
secs = []
for i in range(struct.unpack_from("<H", data, pe + 6)[0]):
    o = soff + i * 40
    vs, va, rs, rp = struct.unpack_from("<IIII", data, o + 8)
    secs.append((va, max(vs, rs), rp, rs))
def rva2off(r):
    for va, sz, rp, rs in secs:
        if va <= r < va + sz: return rp + (r - va)
lits = {int(x["address"], 16): x["value"] for x in json.load(open("out/stringliteral.json", "rb"))}
tbl = pickle.load(open("methods.pkl", "rb")); addrs = [a for a, _ in tbl]
targets = pickle.load(open("_sendtargets.pkl", "rb"))
md = Cs(CS_ARCH_X86, CS_MODE_64); md.detail = True
ROUTE = re.compile(r"^[A-Za-z0-9_\-\.]+(/[A-Za-z0-9_\-\.{}]*)+$")
def routes(start):
    j = bisect.bisect_right(addrs, start)
    ln = min((tbl[j][0] - start) if j < len(tbl) else 0x600, 0xC00)
    off = rva2off(start)
    out = []
    for ins in md.disasm(data[off:off+ln], 0x180000000 + start):
        for op in ins.operands:
            if op.type == x86.X86_OP_MEM and op.mem.base == x86.X86_REG_RIP:
                s = lits.get(ins.address + ins.size + op.mem.disp - 0x180000000)
                if s and ROUTE.match(s) and s not in out: out.append(s)
    return out
cur, rows = None, {}
for line in open("_mx.txt"):
    mm = re.match(r"=== 0x([0-9a-f]+):", line)
    if mm: cur = int(mm.group(1), 16); continue
    mm = re.search(r"in (0x[0-9a-f]+)\s+(\S+)", line)
    if mm and cur in targets:
        rows.setdefault((targets[cur][1], mm.group(2)), int(mm.group(1), 16))
found = []
for (T, owner), rva in rows.items():
    r = routes(rva)
    if r: found.append((r[0], T, owner))
for route, T, owner in sorted(found):
    print(f"{route:<44} {T:<40} {owner}")
print(f"\n{len(found)} routed / {len(rows)} owner-methods")
