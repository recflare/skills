"""Enumerate EVERY DONKHLENABO.BIBPILLJJBN subscription in the binary.

For each call site recovers: the channel key (enum id for the KKPEGEACJKF overloads,
string literal for the named-channel overloads), the payload DTO from the instantiated
generic via ScriptMetadataMethod, and the handler method.

usage: py regall.py [> notifications.tsv]
"""
import struct, pickle, bisect, json, sys, re
import ijson
from capstone import Cs, CS_ARCH_X86, CS_MODE_64, x86

DLL = __import__("os").environ.get("GAMEASSEMBLY", r"C:\Games\recflare-client\GameAssembly.dll")

tbl = pickle.load(open("methods.pkl", "rb"))
addrs = [a for a, _ in tbl]
names = [n for _, n in tbl]

def own(r):
    j = bisect.bisect_right(addrs, r) - 1
    end = addrs[j + 1] if j + 1 < len(addrs) else addrs[j] + 0x1000
    return addrs[j], names[j], end

data = open(DLL, "rb").read()
pe = struct.unpack_from("<I", data, 0x3C)[0]
nsec = struct.unpack_from("<H", data, pe + 6)[0]
optsz = struct.unpack_from("<H", data, pe + 20)[0]
soff = pe + 24 + optsz
secs = []
for i in range(nsec):
    o = soff + i * 40
    vs, va, rs, rp = struct.unpack_from("<IIII", data, o + 8)
    secs.append((va, vs, rp, rs))

def off(rva):
    for va, vs, rp, rs in secs:
        if va <= rva < va + max(vs, rs):
            return rp + (rva - va)

lits = {int(x["address"], 16): x["value"] for x in json.load(open("out/stringliteral.json", "rb"))}

print("loading ScriptMetadataMethod + ScriptMetadata...", file=sys.stderr)
meta = {}
with open("out/script.json", "rb") as f:
    for it in ijson.items(f, "ScriptMetadataMethod.item"):
        meta[int(it["Address"])] = it["Name"]
with open("out/script.json", "rb") as f:
    for it in ijson.items(f, "ScriptMetadata.item"):
        meta.setdefault(int(it["Address"]), it["Name"])

# overload RVA -> (key kind, has payload)
TARGETS = {
    0x2887100: ("enum", False),
    0x1D17A60: ("enum", True),
    0x2886E80: ("str",  False),
    0x1D17AF0: ("str",  True),
}

# raw scan for `call rel32` (E8) AND `jmp rel32` (E9) into any target -- the LAST
# registration in a method is usually compiled as a tail jump, not a call.
print("scanning for call sites...", file=sys.stderr)
text_va, text_vs, text_rp, text_rs = next(
    (va, vs, rp, rs) for va, vs, rp, rs in secs if va <= 0x1D17A60 < va + max(vs, rs))
sites = {}
end = text_rp + text_rs
for p in range(text_rp, end - 5):
    if data[p] not in (0xE8, 0xE9):
        continue
    disp = struct.unpack_from("<i", data, p + 1)[0]
    src = text_va + (p - text_rp)
    tgt = src + 5 + disp
    if tgt in TARGETS:
        sites.setdefault(own(src)[0], []).append(src)

print(f"{sum(len(v) for v in sites.values())} call site(s) in {len(sites)} method(s)", file=sys.stderr)

md = Cs(CS_ARCH_X86, CS_MODE_64)
md.detail = True
GENERIC = re.compile(r"^Method\$DONKHLENABO\.BIBPILLJJBN<(.+)>\(\)$")

rows = []
for start in sorted(sites):
    _, mname, mend = own(start)
    want = set(sites[start])
    code = data[off(start):off(start) + min(mend - start, 0x9000)]
    last_imm = None
    last_lit = None
    pend = []
    for ins in md.disasm(code, start):
        # rip-relative data refs -> metadata slot or string literal
        for op in ins.operands:
            if op.type == x86.X86_OP_MEM and op.mem.base == x86.X86_REG_RIP:
                slot = ins.address + ins.size + op.mem.disp
                if slot in meta:
                    pend.append(meta[slot])
                elif slot in lits and ins.mnemonic == "mov":
                    last_lit = lits[slot]
        # constant into (r|e)cx -- both `mov ecx, imm` and the `lea ecx, [rN + imm]` form
        if ins.mnemonic in ("mov", "lea") and len(ins.operands) == 2:
            d, sr = ins.operands
            if d.type == x86.X86_OP_REG and ins.reg_name(d.reg) in ("ecx", "rcx", "cl", "cx"):
                if ins.mnemonic == "mov" and sr.type == x86.X86_OP_IMM:
                    last_imm = sr.imm
                elif (ins.mnemonic == "lea" and sr.type == x86.X86_OP_MEM
                        and sr.mem.base != x86.X86_REG_RIP and sr.mem.index == 0):
                    last_imm = sr.mem.disp
        if ins.mnemonic in ("call", "jmp") and ins.op_str.startswith("0x"):
            t = int(ins.op_str, 16)
            if t in TARGETS and ins.address in want and "BIBPILLJJBN" not in mname:
                kind, hasp = TARGETS[t]
                payload = None
                handler = None
                if not hasp:
                    pend = [n for n in pend if not GENERIC.match(n)]
                for nm in reversed(pend):
                    m = GENERIC.match(nm)
                    if m and payload is None:
                        payload = m.group(1)
                        continue
                    if handler is None and nm.startswith("Method$") and "BIBPILLJJBN" not in nm \
                            and "..ctor" not in nm and "System.Action" not in nm:
                        handler = nm[len("Method$"):].rstrip("()")
                rows.append((
                    str(last_imm) if kind == "enum" else f'"{last_lit}"',
                    kind,
                    payload or "-",
                    handler or "-",
                    mname.replace("$$", "."),
                    f"0x{ins.address:x}",
                ))
                last_imm = last_lit = None
                pend = []

print("key\tkind\tpayload\thandler\towner\tsite")
for r in sorted(rows, key=lambda r: (r[1], int(r[0]) if r[1]=="enum" and r[0].isdigit() else 9999, r[0])):
    print("\t".join(r))
