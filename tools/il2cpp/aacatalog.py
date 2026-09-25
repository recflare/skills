"""Resolve Unity Addressables keys -> asset paths -> the .bundle files that hold them.

Parses StreamingAssets/aa/catalog.json (ContentCatalogData: m_KeyDataString /
m_BucketDataString / m_EntryDataString are base64 blobs, not JSON). Keys include the
32-hex asset GUIDs that Rec Room's desc registry stores, so this turns a desc lookup
straight into a file on disk.

The FIRST bundle listed for an entry is the one containing the asset; the rest are
shared dependencies. Confirm with bundlepeek.py.

usage: py aacatalog.py <aa-dir> <key-or-substring> [...]
   e.g. py aacatalog.py "C:\Games\recflare-2023\RecRoom_Data\StreamingAssets\aa" 1140dd63dbf4ba9408ef7aefad1cfb28
"""
import json, base64, struct, os, sys

AA = sys.argv[1]
WANT = [w.lower() for w in sys.argv[2:]]
P = os.path.join(AA, "catalog.json")
BUN = os.path.join(AA, "StandaloneWindows64")

d = json.load(open(P, encoding="utf-8"))
kd = base64.b64decode(d["m_KeyDataString"])
bd = base64.b64decode(d["m_BucketDataString"])
ed = base64.b64decode(d["m_EntryDataString"])
ids = d["m_InternalIds"]

def readkey(o):
    t = kd[o]; o += 1
    if t == 0:
        n = struct.unpack_from("<i", kd, o)[0]; return kd[o+4:o+4+n].decode("ascii", "replace")
    if t == 1:
        n = struct.unpack_from("<i", kd, o)[0]; return kd[o+4:o+4+n].decode("utf-16-le", "replace")
    if t == 2:
        return struct.unpack_from("<i", kd, o)[0]
    if t in (3, 4):
        return "hash:" + kd[o:o+16].hex()
    return "?type%d" % t

nb = struct.unpack_from("<i", bd, 0)[0]; o = 4; buckets = []
for _ in range(nb):
    doff, ne = struct.unpack_from("<ii", bd, o); o += 8
    buckets.append((doff, list(struct.unpack_from("<%di" % ne, bd, o)))); o += 4 * ne

def entry(i):
    return struct.unpack_from("<7i", ed, 4 + i * 28)

SEP = chr(92)
for doff, ents in buckets:
    k = str(readkey(doff))
    if not any(w in k.lower() for w in WANT):
        continue
    for ei in ents:
        iid, prov, depk, _dh, _di, _pk, _rt = entry(ei)
        print(k)
        print("   asset : " + ids[iid])
        if 0 <= depk < len(buckets):
            for n, de in enumerate(buckets[depk][1]):
                b = ids[entry(de)[0]].split(SEP)[-1]
                fp = os.path.join(BUN, b)
                sz = os.path.getsize(fp) if os.path.exists(fp) else -1
                tag = "OWNER " if n == 0 else "dep   "
                print("   %s: %-45s %s" % (tag, b, ("%.1f KB" % (sz / 1024)) if sz >= 0 else "MISSING"))
        print()
