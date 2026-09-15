import bisect, ijson, sys

SCRIPT = "out/script.json"
TARGETS = [int(a, 16) for a in sys.argv[1:]]

maddr, mname = [], []
cur = None
with open(SCRIPT, "rb") as f:
    for prefix, event, value in ijson.parse(f):
        if prefix == "ScriptMethod.item.Address":
            cur = value
        elif prefix == "ScriptMethod.item.Name":
            maddr.append(cur); mname.append(value)
        elif prefix.startswith("ScriptString"):
            break

order = sorted(range(len(maddr)), key=lambda k: maddr[k])
smaddr = [maddr[k] for k in order]

for t in TARGETS:
    j = bisect.bisect_right(smaddr, t) - 1
    if j < 0:
        print(f"0x{t:x}  <below first method>")
        continue
    st = smaddr[j]
    nm = mname[order[j]]
    off = t - st
    exact = " EXACT" if off == 0 else f" (+0x{off:x})"
    print(f"0x{t:x}  ->  {nm}  @0x{st:x}{exact}")
