"""Join a ctor's immediate field stores to field names.

usage: py -I ctordefaults.py <fields.txt> <ctor_disasm.txt> [reg]
Reads `fields2025.py` output and `fn.py` output, decodes `mov dword ptr [reg+OFF], IMM32`
as a float, and prints  OFF  name  value.
"""
import re, struct, sys
fields = {}
for ln in open(sys.argv[1], encoding="utf-8", errors="replace"):
    mm = re.match(r"\s+0x([0-9a-f]{4})\s+(\S+)\s+(\S+)", ln)
    if mm: fields[int(mm.group(1), 16)] = (mm.group(3), mm.group(2))
reg = sys.argv[3] if len(sys.argv) > 3 else "rdi"
pat = re.compile(r"mov\s+dword ptr \[" + reg + r" \+ (0x[0-9a-f]+)\], (0x[0-9a-f]+)")
seen = []
for ln in open(sys.argv[2], encoding="utf-8", errors="replace"):
    mm = pat.search(ln)
    if not mm: continue
    off = int(mm.group(1), 16); imm = int(mm.group(2), 16)
    f = struct.unpack("<f", struct.pack("<I", imm & 0xFFFFFFFF))[0]
    name, ty = fields.get(off, ("<unmapped>", "?"))
    seen.append((off, name, ty, imm, f))
print(f"{'off':>8}  {'field':<46} {'type':<10} {'raw':>10}  value")
for off, name, ty, imm, f in seen:
    print(f"  {off:#06x}  {name:<46} {ty:<10} {imm:#010x}  {f:g}")
print(f"\n{len(seen)} immediate store(s)")
