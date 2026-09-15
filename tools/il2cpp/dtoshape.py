"""Print a DTO's JSON wire shape: keys in declaration order, paired with CLR types.

Finds the Utf8Json generated formatter (`class F : MJFBLDENKJM<T>`), disassembles its
.ctor and takes the *last* occurrence of each string literal -- that run is
____stringByteKeys, which is emitted in member-declaration order. Pairs those against
the members parsed out of dump.cs (derived class first, then each base, which is the
order Utf8Json emits for an inherited DTO).

usage: py dtoshape.py <TypeName> [<TypeName> ...]
"""
import struct, json, sys, re, pickle, bisect
from capstone import Cs, CS_ARCH_X86, CS_MODE_64, x86

DLL = __import__("os").environ.get("GAMEASSEMBLY", r"C:\Games\recflare-client\GameAssembly.dll")
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

_tbl = pickle.load(open("methods.pkl", "rb"))
_addrs = [a for a, _ in _tbl]
def method_end(rva):
    """next method start -- the ctor runs right up to it, so this bounds the disasm."""
    j = bisect.bisect_right(_addrs, rva)
    return _addrs[j] if j < len(_addrs) else rva + 0x1200
SRC = open("out/dump.cs", encoding="utf-8", errors="replace").read().split("\n")

PROP = re.compile(r"^\tpublic ([\w\.<>,\[\]\? ]+?) (\w+) \{ get; ")
# Utf8Json serialises public FIELDS too, and several DTOs here are all-fields (e.g. the
# single-`Id` frames). A property-only parse undercounts and shifts the tail slice.
FIELD = re.compile(r"^\tpublic (?!const |static |readonly )([\w\.<>,\[\]\? ]+?) (\w+); //")
CLS = re.compile(r"^public (?:sealed |abstract )?class ([\w\.<>,]+)(?: : ([\w\.<>,]+))?")

def find_class(name):
    pat = re.compile(r"^public (?:sealed |abstract )?class " + re.escape(name) + r"(?:<[^>]*>)?(?: : |\s*//)")
    for i, l in enumerate(SRC):
        if pat.match(l):
            return i
    return None

def members(name, seen=None):
    """(clrtype, propname) in Utf8Json emission order: this class, then its bases."""
    seen = seen or set()
    if name in seen:
        return []
    seen.add(name)
    i = find_class(name)
    if i is None:
        return []
    m = CLS.match(SRC[i])
    base = m.group(2) if m and m.group(2) else None
    out, ignored = [], False
    for l in SRC[i + 1:]:
        if l.startswith("}"):
            break
        if "IgnoreDataMemberAttribute" in l:
            ignored = True
            continue
        p = PROP.match(l) or FIELD.match(l)
        if p:
            if p.group(2).startswith("<") or "k__BackingField" in p.group(2):
                continue                      # compiler-generated backing store
            if ignored:
                ignored = False
                continue
            out.append((p.group(1).strip(), p.group(2)))
    if base and base not in ("GHAILDIJJJO", "object"):
        out += members(base, seen)
    return out

def formatter_ctor(name):
    pat = re.compile(r"^public sealed class (\w+) : MJFBLDENKJM<" + re.escape(name) + r">")
    for i, l in enumerate(SRC):
        if pat.match(l):
            for j in range(i, min(i + 30, len(SRC))):
                if ".ctor()" in SRC[j]:
                    r = re.search(r"RVA: 0x([0-9A-Fa-f]+)", SRC[j - 1])
                    if r:
                        return pat.match(l).group(1), int(r.group(1), 16)
    return None, None

def wire_keys(rva):
    length = min(method_end(rva) - rva, 0x4000)
    md = Cs(CS_ARCH_X86, CS_MODE_64)
    md.detail = True
    order = {}
    for ins in md.disasm(data[off(rva):off(rva) + length], rva):
        if ins.mnemonic != "mov":
            continue
        for op in ins.operands:
            if op.type == x86.X86_OP_MEM and op.mem.base == x86.X86_REG_RIP:
                t = ins.address + ins.size + op.mem.disp
                if t in lits:
                    order[lits[t]] = ins.address       # keep LAST address
    return [k for k, _ in sorted(order.items(), key=lambda kv: kv[1])]

for name in sys.argv[1:]:
    fmt, rva = formatter_ctor(name)
    if rva is None:
        print(f"## {name}\n   (no Utf8Json formatter found)\n")
        continue
    allkeys = wire_keys(rva)
    mem = members(name)
    # the ctor builds ____keyMapping (every accepted casing) and THEN ____stringByteKeys
    # (one entry per member, declaration order) -- so the tail is the shape.
    # ____stringByteKeys is the trailing run, one entry per member, and it can hold no two
    # keys differing only by case -- whereas ____keyMapping before it lists every casing of
    # every key. So the shape is the longest suffix whose lowercased keys are all distinct.
    # This beats slicing to the member count parsed from dump.cs, which miscounts on DTOs
    # with nested types or non-serialised members.
    keys, seen = [], set()
    for k in reversed(allkeys):
        if k.lower() in seen:
            break
        seen.add(k.lower())
        keys.insert(0, k)
    # sanity: ____stringByteKeys holds one entry per member, so the tail must contain no
    # two keys differing only by case. If it does, we sliced into ____keyMapping and the
    # whole row is untrustworthy (usually a truncated/desynced disasm of a big ctor).
    # the pairing (not the key list) is only as good as the member parse agreeing on count
    ok = bool(mem) and len(keys) == len(mem)
    print(f"## {name}   formatter {fmt} @ 0x{rva:x}" + ("" if ok else "   [UNRELIABLE]"))
    if not ok:
        print(f"   !! {len(keys)} wire key(s) vs {len(mem)} parsed member(s) -- KEYS are still "
              f"good, but the key->type pairing below is not; verify types against dump.cs")
    for i, k in enumerate(keys):
        t = mem[i][0] if i < len(mem) else "?"
        clr = mem[i][1] if i < len(mem) else "?"
        flag = "   <- renamed" if i < len(mem) and k.lower() != clr.lower() else ""
        print(f"   {k:34} {t}{flag}")
    print()
