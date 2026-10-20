"""Resolve a Rec Room AvatarItemDesc to shipped assets, with no item name needed.

Given only the desc (the asset ids), walks:

    desc token  ->  resources.assets registry  ->  32-hex Unity asset GUID
                ->  Addressables catalog       ->  Assets/.../(Name).prefab  + owning .bundle

and reports the **system name** as the prefab's basename, e.g. `(SteamPunk_Shirt)`.

Registry entry layout in `RecRoom_Data/resources.assets` (confirmed byte-wise):

    [int32 len][desc ascii][pad to 4][int32 count][int32 len=0x20][32-hex asset guid] ...

The desc appears in more than one table -- typically one entry whose value is the
**material** guid and one whose value is the **prefab** guid -- so every hit is printed.

Descs come in two spellings and BOTH are live; a decoded dashed guid frequently is not
present at all (see rr-client-bringup/references/desc-registry-2023-layout.md):
  * dashed   `f76b709c-b173-426e-81f2-279a67d2fde1`
  * base64url `E9VTiIVFPEa-OuQRto0e_Q`   (Guid.ToByteArray() -> urlsafe b64, '=' stripped)
Both spellings of each token are searched.

usage:
    py descresolve.py <data-dir> <desc>
      <data-dir>  e.g. C:\\Games\\recflare-2023\\RecRoom_Data
      <desc>      one token, or a full comma-separated desc; each token resolved separately
"""

import base64
import json
import os
import re
import struct
import sys
import uuid

HEX32 = re.compile(r"^[0-9a-f]{32}$")


def spellings(tok):
    """Both wire spellings of one desc token."""
    out = [tok]
    try:
        if "-" in tok and len(tok) == 36:
            out.append(base64.urlsafe_b64encode(uuid.UUID(tok).bytes_le).decode().rstrip("="))
        elif len(tok) == 22:
            out.append(str(uuid.UUID(bytes_le=base64.urlsafe_b64decode(tok + "=="))))
    except Exception:
        pass
    return out


def entries_after(data, i, length):
    """Read the value string(s) that follow the key string at `i`.

    Two shapes exist and both are live:
      table A  [key][pad][int32 count][int32 len][value] ...
      table B  [key][pad][int32 len][value]              -- no count field
    """
    o = (i + length + 3) & ~3
    out = []

    def readstr(p):
        n = struct.unpack_from("<i", data, p)[0]
        if not (0 < n < 200):
            return None, p
        return data[p + 4:p + 4 + n].decode("ascii", "replace"), (p + 4 + n + 3) & ~3

    try:
        v, _ = readstr(o)                      # table B: value sits right here
        if v is not None and HEX32.match(v):
            return [v]
        count = struct.unpack_from("<i", data, o)[0]
        o += 4
        if not (0 < count < 8):
            return out
        for _ in range(count):
            v, o = readstr(o)
            if v is None:
                break
            out.append(v)
    except Exception:
        pass
    return out


def neighbours(data, i, length, span=60):
    """Strings immediately around a hit -- the item table stores the human name here."""
    lo, hi = max(0, i - span), min(len(data), i + length + span)
    out, j = [], lo
    while j < hi:
        try:
            n = struct.unpack_from("<i", data, j)[0]
        except Exception:
            break
        if 0 < n < 120 and all(32 <= c < 127 for c in data[j + 4:j + 4 + n]):
            out.append(data[j + 4:j + 4 + n].decode())
            j = (j + 4 + n + 3) & ~3
        else:
            j += 4
    return out


def binary_guid_hits(data, tok, span=600):
    """Newer builds store descs as RAW 16-byte Guid.ToByteArray() instead of ASCII.

    Confirmed on the 2021.3.29f1 refresh of the 20230414 install, where every dashed and
    base64url spelling vanished from resources.assets while the item table kept its
    `(Name)` strings. The record is

        [16 raw bytes][int32 len]"(Name)"[16 raw bytes][int32 len]...binary...
        [int32 0x20]"<32-hex asset guid>" [int32 n][int32 0x20]"<32-hex asset guid>"

    so the asset guids are length-prefixed 32-hex strings a short way FORWARD of the hit.
    The forward walk STOPS at the second `(Name)` string: a record carries exactly one name,
    so a second one means the next record has started. Without that stop a 400-byte window
    silently harvests the neighbours' prefabs -- the same record-boundary trap the ASCII
    tables have, one layer down. Returns (guids, names) in file order; ordering carries no
    meaning -- fromdesc classifies by the catalog path suffix (.prefab vs .mat).
    """
    try:
        raw = uuid.UUID(tok.strip()).bytes_le
    except Exception:
        return [], []
    guids, names, start = [], [], 0
    while True:
        i = data.find(raw, start)
        if i < 0:
            break
        start = i + 1
        # Only the record's OWN key slot is immediately followed by its `(Name)` string.
        # The same guid also appears inside OTHER records (as a parent/related desc slot),
        # and walking forward from those harvests the neighbours' prefabs.
        try:
            n0 = struct.unpack_from("<i", data, i + 16)[0]
        except Exception:
            continue
        if not (0 < n0 < 120):
            continue
        head = data[i + 20:i + 20 + n0]
        if not (head[:1] == b"(" and head[-1:] == b")" and all(32 <= c < 127 for c in head)):
            continue
        j, hi, seen_name = i + 16, min(len(data), i + 16 + span), False
        while j < hi:
            try:
                n = struct.unpack_from("<i", data, j)[0]
            except Exception:
                break
            if 2 < n < 120 and all(32 <= c < 127 for c in data[j + 4:j + 4 + n]):
                v = data[j + 4:j + 4 + n].decode()
                if v.startswith("(") and v.endswith(")"):
                    if seen_name:
                        break              # a record holds ONE name -- this is the next record
                    seen_name = True
                    if v not in names:
                        names.append(v)
                elif HEX32.match(v) and v not in guids:
                    guids.append(v)
                j = (j + 4 + n + 3) & ~3
            else:
                j += 4
    return guids, names


def find_guids(data, tok):
    """All asset guids the registry maps this token to, plus any human name seen nearby."""
    guids, names = [], []
    for spelling in spellings(tok):
        b = spelling.encode()
        start = 0
        while True:
            i = data.find(b, start)
            if i < 0:
                break
            start = i + 1
            if i < 4 or struct.unpack_from("<i", data, i - 4)[0] != len(b):
                continue                       # not a length-prefixed string
            for v in entries_after(data, i, len(b)):
                if HEX32.match(v) and v not in guids:
                    guids.append(v)
            for v in neighbours(data, i, len(b)):
                if v.startswith("(") and v.endswith(")") and v not in names:
                    names.append(v)
    if not guids:                              # newer builds: raw 16-byte guid, no ASCII spelling
        bg, bn = binary_guid_hits(data, tok)
        guids += [g for g in bg if g not in guids]
        names += [n for n in bn if n not in names]
    return guids, names


class Catalog:
    def __init__(self, aa):
        self.bun = os.path.join(aa, "StandaloneWindows64")
        d = json.load(open(os.path.join(aa, "catalog.json"), encoding="utf-8"))
        self.kd = base64.b64decode(d["m_KeyDataString"])
        bd = base64.b64decode(d["m_BucketDataString"])
        self.ed = base64.b64decode(d["m_EntryDataString"])
        self.ids = d["m_InternalIds"]
        n = struct.unpack_from("<i", bd, 0)[0]
        o, self.buckets = 4, []
        for _ in range(n):
            doff, ne = struct.unpack_from("<ii", bd, o)
            o += 8
            self.buckets.append((doff, list(struct.unpack_from("<%di" % ne, bd, o))))
            o += 4 * ne
        self.by_key = {}
        for doff, ents in self.buckets:
            self.by_key.setdefault(str(self.key(doff)), ents)

    def key(self, o):
        t = self.kd[o]
        o += 1
        if t == 0:
            n = struct.unpack_from("<i", self.kd, o)[0]
            return self.kd[o + 4:o + 4 + n].decode("ascii", "replace")
        if t == 1:
            n = struct.unpack_from("<i", self.kd, o)[0]
            return self.kd[o + 4:o + 4 + n].decode("utf-16-le", "replace")
        if t == 2:
            return struct.unpack_from("<i", self.kd, o)[0]
        return "hash:" + self.kd[o:o + 16].hex()

    def entry(self, i):
        return struct.unpack_from("<7i", self.ed, 4 + i * 28)

    def lookup(self, guid):
        out = []
        for ei in self.by_key.get(guid, []):
            iid, _prov, depk, _dh, _di, _pk, _rt = self.entry(ei)
            bundles = []
            if 0 <= depk < len(self.buckets):
                for de in self.buckets[depk][1]:
                    bundles.append(self.ids[self.entry(de)[0]].split(chr(92))[-1])
            out.append((self.ids[iid], bundles))
        return out


def candidates(desc):
    """Keys to try: the desc as given, each bare token, and each adjacent `a,b,` pair.

    A registry key is not always one token -- `(Shirt_SteamPunk)`'s mesh+material live under
    the single key `fD5vtKxBWECH54Jj4FbnUg,C8gCmBZ8RUG83vvDw_UYew,` and neither half resolves
    on its own.
    """
    toks = [t.strip() for t in desc.split(",") if t.strip()]
    out = [desc.strip()] if len(toks) > 1 else []
    out += toks
    for a, b in zip(toks, toks[1:]):
        out.append("%s,%s," % (a, b))
    seen, uniq = set(), []
    for c in out:
        if c not in seen:
            seen.add(c)
            uniq.append(c)
    return uniq


def main():
    data_dir, desc = sys.argv[1], sys.argv[2]
    data = open(os.path.join(data_dir, "resources.assets"), "rb").read()
    cat = Catalog(os.path.join(data_dir, "StreamingAssets", "aa"))

    system_name = None
    for tok in candidates(desc):
        guids, names = find_guids(data, tok)
        print("=== %s" % tok)
        if names:
            print("    item-table name(s): %s" % ", ".join(names))
        if not guids:
            print("    no registry entry")
            continue
        for g in guids:
            hits = cat.lookup(g)
            if not hits:
                print("    %s  -> not in catalog" % g)
                continue
            for path, bundles in hits:
                print("    %s  -> %s" % (g, path))
                if bundles:
                    print("       owner: %s   (+%d dep%s)"
                          % (bundles[0], len(bundles) - 1, "" if len(bundles) == 2 else "s"))
                if path.endswith(".prefab") and system_name is None:
                    system_name = os.path.basename(path)[:-len(".prefab")]
    print()
    print("SYSTEM NAME: %s" % (system_name or "<no prefab found>"))


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(2)
    main()
