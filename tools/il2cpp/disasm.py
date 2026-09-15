import struct, bisect, ijson
from capstone import Cs, CS_ARCH_X86, CS_MODE_64

DLL = __import__("os").environ.get("GAMEASSEMBLY", r"C:\Games\recflare-client\GameAssembly.dll")
SCRIPT = r"out\script.json"

FUNC_RVA = 0x1723D10
FUNC_LEN = 0x280

with open(DLL, "rb") as f:
    data = f.read()
pe = struct.unpack_from("<I", data, 0x3C)[0]
num_sections = struct.unpack_from("<H", data, pe+6)[0]
size_opt = struct.unpack_from("<H", data, pe+20)[0]
sect_off = pe + 24 + size_opt
sections = []
for i in range(num_sections):
    o = sect_off + i*40
    name = data[o:o+8].rstrip(b"\x00").decode("latin1")
    vsize, vaddr, rawsize, rawptr = struct.unpack_from("<IIII", data, o+8)
    sections.append((name, vaddr, vsize, rawptr, rawsize))

def rva_to_off(rva):
    for name, vaddr, vsize, rawptr, rawsize in sections:
        if vaddr <= rva < vaddr + max(vsize, rawsize):
            return rawptr + (rva - vaddr)
    return None

# ---- load ScriptMethod + ScriptString ----
print("loading maps...")
maddr, mname = [], []
saddr, sval = {}, {}
with open(SCRIPT, "rb") as f:
    section = None
    cur_addr = None
    for prefix, event, value in ijson.parse(f):
        if prefix == "ScriptMethod.item.Address": cur_addr = value
        elif prefix == "ScriptMethod.item.Name":
            maddr.append(cur_addr); mname.append(value)
        elif prefix == "ScriptString.item.Address": cur_addr = value
        elif prefix == "ScriptString.item.Value":
            saddr[cur_addr] = value
        elif prefix.startswith("ScriptMetadata") and prefix != "ScriptMetadataMethod":
            break
order = sorted(range(len(maddr)), key=lambda k: maddr[k])
sorted_maddr = [maddr[k] for k in order]
def method_at(rva):
    j = bisect.bisect_right(sorted_maddr, rva) - 1
    if j < 0: return None
    return mname[order[j]], sorted_maddr[j]

print(f"  {len(maddr)} methods, {len(saddr)} strings\n")

off = rva_to_off(FUNC_RVA)
code = data[off:off+FUNC_LEN]
md = Cs(CS_ARCH_X86, CS_MODE_64)
md.detail = True

for insn in md.disasm(code, FUNC_RVA):
    annot = ""
    # RIP-relative target
    if "rip" in insn.op_str:
        # find disp: capstone gives it in operands
        for op in insn.operands:
            if op.type == 3 and op.mem.base == insn.reg_name(insn.reg_name and 0):
                pass
    # simpler: compute rip target from disp in operands
    tgt = None
    for op in insn.operands:
        if op.type == 3 and op.mem.base != 0 and insn.reg_name(op.mem.base) == "rip":
            tgt = insn.address + insn.size + op.mem.disp
    if tgt is not None:
        if tgt in saddr:
            annot = f'   ; STRING "{saddr[tgt]}"'
        else:
            m = method_at(tgt)
            if m and m[1] == tgt:
                annot = f"   ; -> {m[0]}"
            else:
                annot = f"   ; data 0x{tgt:x}"
    # direct call e8
    if insn.mnemonic in ("call", "jmp") and insn.operands and insn.operands[0].type == 1:
        t = insn.operands[0].imm
        m = method_at(t)
        if m and m[1] == t:
            annot = f"   ; {insn.mnemonic} -> {m[0]}"
        elif m:
            annot = f"   ; {insn.mnemonic} -> {m[0]}+0x{t-m[1]:x}"
    print(f"0x{insn.address:07x}: {insn.mnemonic:6} {insn.op_str}{annot}")
