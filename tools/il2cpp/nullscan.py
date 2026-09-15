# Report every method matching a name regex that directly calls Nullable<T>.get_Value.
# Usage: py nullscan.py "<regex over method names>"
import struct, pickle, bisect, sys, re

DLL = __import__("os").environ.get("GAMEASSEMBLY", r"C:\Games\recflare-client\GameAssembly.dll")

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

from capstone import Cs, CS_ARCH_X86, CS_MODE_64
md = Cs(CS_ARCH_X86, CS_MODE_64)

PAT = re.compile(sys.argv[1])
DEREF = re.compile(r"Nullable<.*>\$\$get_Value")

targets = [(a, n) for a, n in tbl if PAT.search(n)]
print(f"# {len(targets)} methods match {sys.argv[1]!r}\n", file=sys.stderr)

hits = 0
for i, (start, name) in enumerate(targets):
    j = bisect.bisect_right(addrs, start) - 1
    end = addrs[j + 1] if j + 1 < len(addrs) else start + 0x400
    ln = min(max(end - start, 0x40), 0x6000)
    o = off(start)
    if o is None:
        continue
    for ins in md.disasm(data[o:o + ln], start):
        if ins.mnemonic != "call" or not ins.op_str.startswith("0x"):
            continue
        t = int(ins.op_str, 16)
        _, tname = owner(t)
        if tname and DEREF.search(tname):
            hits += 1
            print(f"{name}\n    @0x{ins.address:x}  ->  {tname}")
print(f"\n# {hits} get_Value call sites", file=sys.stderr)
