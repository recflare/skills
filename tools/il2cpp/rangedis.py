# Disassemble an arbitrary RVA range with call targets resolved. Usage: py rangedis.py <start> <end>
import struct, pickle, bisect, sys
from capstone import Cs, CS_ARCH_X86, CS_MODE_64

DLL = __import__("os").environ.get("GAMEASSEMBLY", r"C:\Games\recflare-client\GameAssembly.dll")
START = int(sys.argv[1], 16)
END = int(sys.argv[2], 16)

tbl = pickle.load(open("methods.pkl", "rb"))
addrs = [a for a, _ in tbl]
names = [n for _, n in tbl]

def owner(rva):
    j = bisect.bisect_right(addrs, rva) - 1
    return (addrs[j], names[j]) if j >= 0 else (None, None)

data = open(DLL, "rb").read()
pe = struct.unpack_from("<I", data, 0x3C)[0]
nsec = struct.unpack_from("<H", data, pe + 6)[0]
optsz = struct.unpack_from("<H", data, pe + 20)[0]
so = pe + 24 + optsz
secs = []
for i in range(nsec):
    p = so + i * 40
    vs, va, rs, rp = struct.unpack_from("<IIII", data, p + 8)
    secs.append((va, vs, rp, rs))

def off(rva):
    for va, vs, rp, rs in secs:
        if va <= rva < va + max(vs, rs):
            return rp + (rva - va)

md = Cs(CS_ARCH_X86, CS_MODE_64)
o = off(START)
for ins in md.disasm(data[o:o + (END - START)], START):
    annot = ""
    if ins.mnemonic in ("call", "jmp") and ins.op_str.startswith("0x"):
        t = int(ins.op_str, 16)
        st, nm = owner(t)
        if nm:
            annot = f"   ; -> {nm}" + ("" if st == t else f"+0x{t-st:x}")
        else:
            annot = "   ; -> <native runtime helper>"
    print(f"0x{ins.address:x}: {ins.mnemonic:8} {ins.op_str}{annot}")
