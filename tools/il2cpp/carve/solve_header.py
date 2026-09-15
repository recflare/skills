"""Stage 2a of the carve: recover the metadata table layout from the permuted header.

These builds overwrite the magic/version and shuffle which header slot belongs to which table, but
the 31 tables still tile the file end to end from 0x100. So search for an assignment of the 64
header ints into 31 (offset, size) pairs whose offsets chain: off[i] + size[i] == off[i+1], starting
at 0x100 and ending at the file length. Two ints are left over -- the old sanity/version slots.

Tiling alone is not proof (DUMPING.md): more than one assignment can tile perfectly. This prints
every solution it finds so the tables can then be identified by content.
"""
import struct
import sys

PATH = sys.argv[1] if len(sys.argv) > 1 else "out/metadata.bin"
ALLOC_LEN = None  # upper bound on file length; default = size of the captured allocation

data = open(PATH, "rb").read()
if ALLOC_LEN is None:
    ALLOC_LEN = len(data)

vals = list(struct.unpack("<64I", data[:0x100]))
print(f"# {PATH}: {len(data)} bytes captured, {len(vals)} header ints")

# Multiset of available ints (index -> value); we consume indices, not values, so duplicates work.
from collections import defaultdict

by_val = defaultdict(list)
for i, v in enumerate(vals):
    by_val[v].append(i)

solutions = []


def search(cur, used, chain):
    """cur = next offset that must be covered. used = set of consumed header indices."""
    if len(chain) == 31:
        # All tables placed; the last one must end at the file length.
        if cur <= ALLOC_LEN and ALLOC_LEN - cur < 0x1000:
            solutions.append((list(chain), set(used), cur))
        return
    # An int equal to `cur` must exist and be unconsumed: that is this table's offset slot.
    off_idx = None
    for i in by_val.get(cur, ()):
        if i not in used:
            off_idx = i
            break
    if off_idx is None:
        return
    used.add(off_idx)
    # Try every remaining int as this table's size.
    for j, s in enumerate(vals):
        if j in used:
            continue
        nxt = cur + s
        if nxt > ALLOC_LEN:
            continue
        # The next offset must itself appear in the header, unless this is the final table.
        if len(chain) < 30:
            avail = [k for k in by_val.get(nxt, ()) if k not in used and k != j]
            if not avail:
                continue
        used.add(j)
        chain.append((cur, s, off_idx, j))
        search(nxt, used, chain)
        chain.pop()
        used.discard(j)
    used.discard(off_idx)


search(0x100, set(), [])

print(f"# {len(solutions)} tiling solution(s)\n")
for n, (chain, used, endv) in enumerate(solutions):
    leftover = [(i, vals[i]) for i in range(64) if i not in used]
    print(f"=== solution {n}: ends at {endv:#x} ({endv}); leftover slots {leftover}")
    for k, (off, size, oi, si) in enumerate(chain):
        print(f"  [{k:2}] off={off:#10x} size={size:#10x}  (hdr idx {oi:2}/{si:2})")
    print()
