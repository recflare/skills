# List every game-config class (derives from GHAILDIJJJO) and flag the ones holding a nullable
# DateTime -- i.e. the time-gated configs served by /api/gameconfigs/v1/all.
import re, sys

BASE = sys.argv[1] if len(sys.argv) > 1 else "GHAILDIJJJO"
src = open("out/dump.cs", encoding="utf-8", errors="replace").read().splitlines()

start = re.compile(r"^(?:public|internal|private|protected).*class ([\w.<>`]+)\s*:\s*" + BASE + r"\b")
classdecl = re.compile(r"^(?:public|internal|private|protected)")

found = []
i = 0
while i < len(src):
    m = start.match(src[i])
    if not m:
        i += 1
        continue
    name = m.group(1)
    # Walk the brace-delimited body: opens on the next line, closes when depth returns to 0.
    body, depth, j, opened = [], 0, i + 1, False
    while j < len(src):
        depth += src[j].count("{") - src[j].count("}")
        body.append(src[j])
        if depth > 0:
            opened = True
        if opened and depth == 0:
            break
        j += 1
    text = "\n".join(body)
    dt = [l.strip() for l in body if re.search(r"DateTime\?|Nullable<DateTime>", l)]
    found.append((name, i + 1, dt))
    i = j + 1

print(f"# {len(found)} classes derive from {BASE}\n")
timed = [f for f in found if f[2]]
print(f"# {len(timed)} of them hold a nullable DateTime:\n")
for name, line, dt in timed:
    print(f"{name}   (dump.cs:{line})")
    for d in dt:
        print(f"      {d}")
    print()
print("# --- all config class names ---")
print(", ".join(n for n, _, _ in found))
