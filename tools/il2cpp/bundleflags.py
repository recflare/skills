"""Report the client's DirectlyLoadableAssetBundleSource verdict for UnityFS files.

Implements RecRoom.Core.Studio.OVWVRFTNJPC.VLRSRJOPTNI / MWXPZYABIXT (2026 0x1ACD680 / 0x1ACD1E0):
  sig=="UnityFS"; version<=8; cbi<=ubi; (archiveFlags & 0x3F)==3 (LZ4HC) else THROW;
  needsRecompression = any block with (blockFlags & 0x3F)!=0 AND (blockFlags & 0x40)!=0
usage: py bundleflags.py <file-or-dir> [...]
"""
import os, sys, struct
sys.path.insert(0, r"C:\Games\skills\tools\il2cpp")
from lz4b import lz4_decompress

COMP = {0: "None", 1: "LZMA", 2: "LZ4", 3: "LZ4HC", 4: "LZHAM"}

def check(p):
    b = open(p, "rb").read(0x4000000)
    if b[:7] != b"UnityFS":
        return None
    o = b.index(b"\0") + 1
    ver = struct.unpack_from(">I", b, o)[0]; o += 4
    uver_s = o; o = b.index(b"\0", o) + 1
    urev_s = o; o = b.index(b"\0", o) + 1
    size, cbi, ubi, flags = struct.unpack_from(">QIII", b, o); o += 20
    out = {"ver": ver, "unity": b[uver_s:b.index(b"\0", uver_s)].decode(),
           "rev": b[urev_s:b.index(b"\0", urev_s)].decode(),
           "size": size, "cbi": cbi, "ubi": ubi, "flags": flags,
           "arch_comp": COMP.get(flags & 0x3F, flags & 0x3F)}
    if ver >= 7 or (flags & 0x200):
        o = (o + 15) & ~15
    if flags & 0x80:                      # blocksInfo at end
        o = len(b) - cbi
    ct = flags & 0x3F
    try:
        bi = lz4_decompress(b[o:o+cbi], ubi) if ct in (2, 3) else b[o:o+cbi]
        cnt = struct.unpack_from(">I", bi, 16)[0]
        blocks = [struct.unpack_from(">IIH", bi, 20 + 10 * i) for i in range(cnt)]
    except Exception as e:
        out["blocks_error"] = repr(e); return out
    out["nblocks"] = len(blocks)
    out["block_flagset"] = sorted({f for _, _, f in blocks})
    bad = [(i, f) for i, (_, _, f) in enumerate(blocks) if (f & 0x3F) and (f & 0x40)]
    out["needs_recompression"] = bool(bad)
    out["offending_blocks"] = bad[:5]
    return out

def walk(a):
    if os.path.isdir(a):
        for r, _, fs in os.walk(a):
            for f in fs: yield os.path.join(r, f)
    else:
        yield a

for a in sys.argv[1:]:
    for p in walk(a):
        try: r = check(p)
        except Exception as e: print(f"{p}: ERR {e}"); continue
        if r is None: continue
        v = "NEEDS RECOMPRESSION -> REJECTED" if r.get("needs_recompression") else "ok"
        if (r["flags"] & 0x3F) != 3: v = f"ARCHIVE COMP {r['arch_comp']} != LZ4HC -> THROWS"
        print(f"{p}")
        print(f"   unity={r['unity']} ver={r['ver']} archComp={r['arch_comp']} "
              f"flags={r['flags']:#x} blocks={r.get('nblocks')} "
              f"blockFlags={r.get('block_flagset')}")
        print(f"   => {v}  {r.get('offending_blocks') or ''} {r.get('blocks_error','')}")
