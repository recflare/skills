"""Build methods.pkl -- the sorted (rva, name) table every other script here depends on.

script.json is ~300MB, so parsing it takes minutes; the pickle makes every later lookup instant.
Run this ONCE per game build, from this directory, with Il2CppDumper's output in ./out/.

    py mkmethods.py

Regenerate it whenever GameAssembly.dll changes. A stale methods.pkl is worse than none: every
address resolves to a plausible but WRONG method name, with no error.
"""
import ijson, pickle, os, sys, struct, datetime

SCRIPT = "out/script.json"
OUT = "methods.pkl"
DLL = os.environ.get("GAMEASSEMBLY", r"C:\Games\recflare-client\GameAssembly.dll")

if not os.path.exists(SCRIPT):
    sys.exit(f"{SCRIPT} not found -- run Il2CppDumper first and put its output in ./out/")

print(f"parsing {SCRIPT} ({os.path.getsize(SCRIPT)/1e6:.0f} MB), this takes a few minutes...")

addrs, names, cur = [], [], None
with open(SCRIPT, "rb") as f:
    for prefix, event, value in ijson.parse(f):
        if prefix == "ScriptMethod.item.Address":
            cur = value
        elif prefix == "ScriptMethod.item.Name":
            addrs.append(cur)
            names.append(value)
        elif prefix.startswith("ScriptString"):
            break   # ScriptMethod is fully consumed by now; don't parse the rest

tbl = sorted(zip(addrs, names), key=lambda p: p[0])
with open(OUT, "wb") as f:
    pickle.dump(tbl, f)

# Stamp which binary this table describes, so a mismatch is noticeable later.
stamp = "unknown"
if os.path.exists(DLL):
    st = os.stat(DLL)
    stamp = f"{DLL}  mtime={datetime.datetime.fromtimestamp(st.st_mtime)}  size={st.st_size}"
with open("methods.pkl.txt", "w", encoding="utf-8") as f:
    f.write(f"{len(tbl)} methods\nbuilt {datetime.datetime.now()}\nfrom {stamp}\n")

print(f"wrote {OUT}: {len(tbl)} methods")
print(f"built from {stamp}")
