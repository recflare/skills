"""Resolve GameAssembly RVAs -> method names using the CORRECT Cpp2IL dump for build 2025-04-29.

il2cpp-tools/out/{script.json,dump.cs,...} is a DIFFERENT BUILD -- whatis.py/findm.py read it and
therefore return bogus names for recflare-client-unstable. Sanity check for any dump: BestHTTP
SendRequest must be RVA 0x71D7BE0 (that is the address our working hook uses).

This parses the RVA-annotated C# instead:

    [Cpp2IlInjected.Address(RVA = "0x71D7BE0", Offset = "0x71D6FE0", VA = "0x1871D7BE0")]
    public static HTTPRequest SendRequest(HTTPRequest request) { }

Builds a sorted RVA table and reports the closest preceding method, like whatis.py did. A large
"+0x..." delta means the address is NOT really inside that method (dumps omit compiler-generated and
stripped bodies), so treat big offsets as "unknown", not as a hit.

usage:  py whatis2025.py 7FAC63 111A5C3 ...
        py whatis2025.py --dump <dir> 7FAC63
"""
import bisect, os, re, sys, pickle

DEFAULT_DUMP = r"C:\Games\RecRoom_Info\Code\2025-04-29_02-57-34"
CACHE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "rva2025.pkl")

RVA_RE = re.compile(r'Address\(RVA\s*=\s*"0x([0-9A-Fa-f]+)"')
# The declaration is the next non-attribute, non-blank line after the address attribute.
SKIP_RE = re.compile(r'^\s*(\[|//|$)')
CLASS_RE = re.compile(r'^\s*(?:public|private|internal|protected|sealed|static|abstract|\s)*\s*'
                      r'(?:class|struct|interface|enum)\s+([A-Za-z0-9_.<>`]+)')


def build(dump_dir):
    table = []   # (rva, "Class.method-decl")
    for name in sorted(os.listdir(dump_dir)):
        if not name.endswith(".cs"):
            continue
        path = os.path.join(dump_dir, name)
        cls = "?"
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            lines = f.readlines()
        for i, line in enumerate(lines):
            m = CLASS_RE.match(line)
            if m:
                cls = m.group(1)
                continue
            m = RVA_RE.search(line)
            if not m:
                continue
            rva = int(m.group(1), 16)
            decl = ""
            for j in range(i + 1, min(i + 6, len(lines))):
                if SKIP_RE.match(lines[j]):
                    continue
                decl = lines[j].strip()
                break
            table.append((rva, f"{name}: {cls}.{decl}"))
    table.sort(key=lambda t: t[0])
    return table


def load(dump_dir):
    if os.path.exists(CACHE):
        with open(CACHE, "rb") as f:
            cached_dir, table = pickle.load(f)
        if cached_dir == dump_dir:
            return table
    table = build(dump_dir)
    with open(CACHE, "wb") as f:
        pickle.dump((dump_dir, table), f)
    return table


def main():
    args = sys.argv[1:]
    dump_dir = DEFAULT_DUMP
    # --dump is accepted ANYWHERE in argv. It used to be positional (argv[0] only), so
    # `whatis2025.py <rva> --dump <dir>` silently fell back to DEFAULT_DUMP and resolved
    # against the wrong build. Check the anchor line in the output either way.
    if "--dump" in args:
        i = args.index("--dump")
        dump_dir = args[i + 1]
        args = args[:i] + args[i + 2:]
    if not args:
        print(__doc__)
        return

    table = load(dump_dir)
    addrs = [r for r, _ in table]
    print(f"# {len(table)} methods from {dump_dir}")

    # Self-check. Do NOT hardcode an RVA here: SendRequest moves every build (0x71D7BE0 on
    # 2025-04-29, 0x77E0950 on 2025-07-19), so a fixed constant reports "WRONG DUMP" for every dump
    # except one -- which trains you to ignore the warning, the opposite of the point. Instead look
    # the anchor up BY NAME and print the RVA it lands on; compare that against the RVA your hook
    # actually uses for this build.
    # List every match -- SendRequest is overloaded, so picking just the first prints a plausible
    # but wrong RVA and defeats the check.
    anchor = [(r, n) for r, n in table if "HTTPManager" in n and "SendRequest" in n]
    if anchor:
        print("# anchor HTTPManager.SendRequest (2025-04-29=0x71D7BE0, 2025-07-19=0x77E0950 "
              "-- one of these must match YOUR build):")
        for r, n in anchor:
            print(f"#   0x{r:X}  {n}")
    else:
        print("# anchor: HTTPManager.SendRequest NOT FOUND -- dump did not parse, names are unusable")

    for a in args:
        t = int(a, 16)
        j = bisect.bisect_right(addrs, t) - 1
        if j < 0:
            print(f"0x{t:X}  <below first method>")
            continue
        rva, nm = table[j]
        off = t - rva
        mark = " EXACT" if off == 0 else f" (+0x{off:X})"
        warn = "   <-- offset large; probably NOT this method" if off > 0x1000 else ""
        print(f"0x{t:X}  ->  {nm}  @0x{rva:X}{mark}{warn}")


if __name__ == "__main__":
    main()
