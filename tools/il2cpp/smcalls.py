# List, in address order, every direct call inside a method, resolved to a name.
# Usage: py smcalls.py <substring-of-method-name>
import struct, pickle, bisect, sys, re, os, datetime

DLL = __import__("os").environ.get("GAMEASSEMBLY", r"C:\Games\recflare-client\GameAssembly.dll")

tbl = pickle.load(open("methods.pkl", "rb"))
addrs = [a for a, _ in tbl]
names = [n for _, n in tbl]

def owner(rva):
    j = bisect.bisect_right(addrs, rva) - 1
    return (addrs[j], names[j]) if j >= 0 else (None, "?")

def end_of(rva):
    j = bisect.bisect_right(addrs, rva) - 1
    return addrs[j + 1] if j + 1 < len(addrs) else rva + 0x800

st = os.stat(DLL)
print(f"# GameAssembly.dll  mtime={datetime.datetime.fromtimestamp(st.st_mtime)}  size={st.st_size}")
print(f"# methods.pkl entries={len(tbl)}\n")

NEEDLE = sys.argv[1]
matches = [(a, n) for a, n in tbl if NEEDLE in n]
if not matches:
    sys.exit(f"no method name contains {NEEDLE!r}")
for a, n in matches:
    print(f"# candidate 0x{a:x}  {n}")
print()

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

# Framework noise; RecRoom's own obfuscated code matches none of these.
SKIP = re.compile(r"^(System\.|UnityEngine\.|Unity\.|Photon\.|Google\.Protobuf|Newtonsoft"
                  r"|BestHTTP|Il2Cpp|TMPro|Backtrace|Cinemachine|DOTween)")

for start, name in matches:
    end = end_of(start)
    ln = min(max(end - start, 0x40), 0x6000)
    o = off(start)
    if o is None:
        continue
    print(f"===== {name}  @0x{start:x}  len=0x{ln:x}")
    n = 0
    for ins in md.disasm(data[o:o + ln], start):
        if ins.mnemonic != "call" or not ins.op_str.startswith("0x"):
            continue
        t = int(ins.op_str, 16)
        tstart, tname = owner(t)
        # Below the first managed method = a native il2cpp runtime helper, not a managed callee.
        if tstart is None:
            tname, exact = "<native runtime helper>", ""
        else:
            exact = "" if tstart == t else f"+0x{t - tstart:x}"
        mark = "   " if SKIP.match(tname) else "***"   # *** = RecRoom code, patchable target
        if "Nullable" in tname or "ThrowHelper" in tname:
            mark = ">>>"
        n += 1
        print(f"{mark} [{n:3}] 0x{ins.address:x}  ->  {tname}{exact}")
    print()
