import struct, bisect, ijson, sys
from capstone import Cs, CS_ARCH_X86, CS_MODE_64

DLL = __import__("os").environ.get("GAMEASSEMBLY", r"C:\Games\recflare-client\GameAssembly.dll")
SCRIPT = "out/script.json"
TARGET = int(sys.argv[1], 16)   # RVA of a method (e.g. ctor) to find callers of

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
    chars = struct.unpack_from("<I", data, o+36)[0]
    sections.append((name, vaddr, vsize, rawptr, rawsize, chars))
exec_secs = [s for s in sections if s[5] & 0x20000000]

print("loading ScriptMethod...", file=sys.stderr)
maddr, mname = [], []
with open(SCRIPT, "rb") as f:
    cur=None
    for prefix, event, value in ijson.parse(f):
        if prefix == "ScriptMethod.item.Address": cur=value
        elif prefix == "ScriptMethod.item.Name": maddr.append(cur); mname.append(value)
        elif prefix.startswith("ScriptString"): break
order = sorted(range(len(maddr)), key=lambda k: maddr[k])
smaddr = [maddr[k] for k in order]
def method_at(rva):
    j = bisect.bisect_right(smaddr, rva) - 1
    return (mname[order[j]], smaddr[j]) if j>=0 else None

# find direct call/jmp rel32 (e8/e9) and rip-relative refs to TARGET
hits = set()
for name, vaddr, vsize, rawptr, rawsize, chars in exec_secs:
    blob = data[rawptr:rawptr+rawsize]
    n = len(blob)
    # direct rel32 call (e8) or jmp (e9): target = pos+5+rel32
    i = 0
    while i < n-5:
        b = blob[i]
        if b in (0xE8, 0xE9):
            rel = struct.unpack_from("<i", blob, i+1)[0]
            if vaddr + i + 5 + rel == TARGET:
                hits.add(vaddr + i)
                i += 5; continue
        i += 1
    # rip-relative refs
    for i in range(1, n-4):
        d = struct.unpack_from("<i", blob, i)[0]
        if vaddr + i + 4 + d == TARGET and (blob[i-1] & 0xC7) == 0x05:
            hits.add(vaddr + i - 1)

print(f"{len(hits)} reference(s) to 0x{TARGET:x}:")
seen = {}
for h in sorted(hits):
    m = method_at(h)
    if m:
        seen.setdefault(m, []).append(h)
for (nm, st), locs in sorted(seen.items(), key=lambda kv: kv[0][1]):
    print(f"  method 0x{st:x}  {nm}")
    for l in locs:
        print(f"      ref at 0x{l:x} (+0x{l-st:x})")
