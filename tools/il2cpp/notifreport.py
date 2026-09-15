"""Pass 2: pair each registrar call with the channel-id literal loaded beside it."""
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
slots = pickle.load(open("_notifslots.pkl", "rb"))
md = Cs(CS_ARCH_X86, CS_MODE_64); md.detail = True

owners = {}
cur = None
for line in open("_nmx.txt"):
    mm = re.match(r"=== 0x([0-9a-f]+):", line)
    if mm: cur = int(mm.group(1), 16); continue
    mm = re.search(r"in (0x[0-9a-f]+)\s+(\S+)", line)
    if mm: owners.setdefault((int(mm.group(1), 16), mm.group(2)), set()).add(cur)

out = []
for (rva, name), used in sorted(owners.items()):
    j = bisect.bisect_right(addrs, rva)
    ln = min((tbl[j][0] - rva) if j < len(tbl) else 0x800, 0x2000)
    off = rva2off(rva)
    last_lit, pend_T = None, None
    for ins in md.disasm(data[off:off+ln], IMGBASE := 0x180000000 + rva):
        for op in ins.operands:
            if op.type == x86.X86_OP_MEM and op.mem.base == x86.X86_REG_RIP:
                tgt = ins.address + ins.size + op.mem.disp - 0x180000000
                if tgt in lits: last_lit = lits[tgt]
                elif tgt in slots: pend_T = slots[tgt]
        # Reset BOTH after a register call: a method that registers several channels in a row
        # would otherwise re-pair a stale literal with the next slot and invent a subscription.
        if ins.mnemonic == "call" and pend_T is not None:
            if last_lit is not None:
                out.append((last_lit, pend_T, name))
            pend_T = None; last_lit = None
seen = set()
for idv, T, owner in out:
    k = (idv, T)
    if k in seen: continue
    seen.add(k)
    print(f"{idv:<44} {T:<44} {owner}")
print(f"\n{len(seen)} subscriptions")
