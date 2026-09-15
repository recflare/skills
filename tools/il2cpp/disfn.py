import struct, bisect, ijson, sys
from capstone import Cs, CS_ARCH_X86, CS_MODE_64

DLL = __import__("os").environ.get("GAMEASSEMBLY", r"C:\Games\recflare-client\GameAssembly.dll")
SCRIPT = "out/script.json"
FUNC_RVA = int(sys.argv[1], 16)
FUNC_LEN = int(sys.argv[2], 16) if len(sys.argv) > 2 else 0x200

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

print("loading maps...", file=sys.stderr)
maddr, mname = [], []
saddr = {}
with open(SCRIPT, "rb") as f:
    cur=None
    for prefix, event, value in ijson.parse(f):
        if prefix == "ScriptMethod.item.Address": cur=value
        elif prefix == "ScriptMethod.item.Name": maddr.append(cur); mname.append(value)
        elif prefix == "ScriptString.item.Address": cur=value
        elif prefix == "ScriptString.item.Value": saddr[cur]=value
        elif prefix.startswith("ScriptMetadata") and prefix!="ScriptMetadataMethod": break
order = sorted(range(len(maddr)), key=lambda k: maddr[k])
smaddr=[maddr[k] for k in order]
def method_at(rva):
    j=bisect.bisect_right(smaddr, rva)-1
    return (mname[order[j]], smaddr[j]) if j>=0 else None

code = data[rva_to_off(FUNC_RVA):rva_to_off(FUNC_RVA)+FUNC_LEN]
md = Cs(CS_ARCH_X86, CS_MODE_64); md.detail=True
for insn in md.disasm(code, FUNC_RVA):
    annot=""
    tgt=None
    for op in insn.operands:
        if op.type==3 and op.mem.base!=0 and insn.reg_name(op.mem.base)=="rip":
            tgt=insn.address+insn.size+op.mem.disp
    if tgt is not None:
        if tgt in saddr: annot=f'   ; STR "{saddr[tgt]}"'
        else:
            m=method_at(tgt)
            annot=f"   ; -> {m[0]}" if (m and m[1]==tgt) else f"   ; data 0x{tgt:x}"
    if insn.mnemonic in ("call","jmp") and insn.operands and insn.operands[0].type==1:
        t=insn.operands[0].imm; m=method_at(t)
        if m and m[1]==t: annot=f"   ; {insn.mnemonic} -> {m[0]}"
        elif m: annot=f"   ; {insn.mnemonic} -> {m[0]}+0x{t-m[1]:x}"
    print(f"0x{insn.address:07x}: {insn.mnemonic:6} {insn.op_str}{annot}")
