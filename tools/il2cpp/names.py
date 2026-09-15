"""Recover JSON property names from a Utf8Json generated formatter's .ctor.

The generated formatter builds ____keyMapping (AutomataDictionary) and ____stringByteKeys
(byte[][]) from plain string literals, so disassembling the ctor and resolving every
rip-relative data reference against stringliteral.json yields the wire names in order.

usage: python names.py <ctor_rva_hex> [len_hex]
"""
import struct, json, sys
from capstone import Cs, CS_ARCH_X86, CS_MODE_64

DLL = __import__("os").environ.get("GAMEASSEMBLY", r"C:\Games\recflare-client\GameAssembly.dll")
FUNC = int(sys.argv[1], 16)
LEN = int(sys.argv[2], 16) if len(sys.argv) > 2 else 0x400

with open(DLL, "rb") as f:
    data = f.read()
pe = struct.unpack_from("<I", data, 0x3C)[0]
nsec = struct.unpack_from("<H", data, pe + 6)[0]
optsz = struct.unpack_from("<H", data, pe + 20)[0]
soff = pe + 24 + optsz
sections = []
for i in range(nsec):
    o = soff + i * 40
    vsize, vaddr, rawsize, rawptr = struct.unpack_from("<IIII", data, o + 8)
    sections.append((vaddr, vsize, rawptr, rawsize))

def rva_to_off(rva):
    for vaddr, vsize, rawptr, rawsize in sections:
        if vaddr <= rva < vaddr + max(vsize, rawsize):
            return rawptr + (rva - vaddr)
    return None

lits = {int(x["address"], 16): x["value"] for x in json.load(open("out/stringliteral.json", "rb"))}

off = rva_to_off(FUNC)
code = data[off:off + LEN]
md = Cs(CS_ARCH_X86, CS_MODE_64)
md.detail = True

seen = []
for ins in md.disasm(code, FUNC):
    for op in ins.operands:
        if op.type == 3 and op.mem.base == 0x29:  # X86_OP_MEM, RIP-relative
            tgt = ins.address + ins.size + op.mem.disp
            # literal slots are pointers; the value may sit at the slot or one deref away
            for cand in (tgt,):
                if cand in lits:
                    v = lits[cand]
                    if (ins.address, v) not in seen:
                        seen.append((ins.address, v))
                        print(f"0x{ins.address:x}  {ins.mnemonic:6} -> \"{v}\"")

print(f"\n{len(seen)} literal reference(s) in order.")
