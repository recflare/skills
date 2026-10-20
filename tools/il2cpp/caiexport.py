"""Build (or verify) a Rec Room CustomAvatarItem export folder.

Mimics the on-disk layout and byte-level formats of the reference exports, e.g.
`S:\\RecRoom\\1\\(Floaties_Wrist)`:

    (Name)[  <CombinationName>]/
        avatarItem.json                       the full CAI DTO
        0/  0_save.json                       redundant byte-identical copy of avatarItem.json
                                              (true across the whole library; only the root
                                               avatarItem.json actually matters)
            <UnityAsset>.assetbundle          mesh/prefab   (internal name ...AvatarItem.Main.0.5)
            <UnityAsset2>.assetbundle         material/tex  (internal name ...AvatarItem.Material.0.6)
            <ThumbnailFileName>.png
        1/ ...                                one folder per CurrentSaves entry, index == BodyType
        2/ ...

Verified against the reference export:
  * UnityAssetHash / UnityAsset2Hash = base64(SHA-256(file))            -- exact match
  * avatarItem.json and every N_save.json are byte-identical
  * JSON is System.Text.Json with the DEFAULT JavaScriptEncoder: compact (no spaces),
    property order preserved, non-ASCII plus " and + escaped as UPPERCASE \\uXXXX.
    Re-serializing the reference DTO with this module reproduces its 2942 bytes exactly.

usage:
    py caiexport.py fromdesc <data-dir> <desc> <out-root> [outfit-type] [item-id] [fb-desc]
    py caiexport.py build    <spec.json> <out-root>
    py caiexport.py verify   <export-dir>

`fromdesc` is the idempotent path: every identity (CustomAvatarItemId, UnityAssetId, and
each CDN-style filename) is derived from the desc via caiids.py, so re-exporting the same
desc rewrites the same folder with the same ids instead of minting a duplicate item.

The derived CustomAvatarItemId is a FALLBACK for when the desc is all you have. If the
catalogue already owns an id for this item, pass it as [item-id] -- an invented id that
disagrees with the server's is a duplicate item, not a cosmetic difference. UnityAssetIds
stay desc-derived either way; they are per-save upload ids with no external source here.
"""

import base64
import hashlib
import json
import os
import shutil
import sys
import uuid

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import caiids

BS = chr(92)
# System.Text.Json's default JavaScriptEncoder escapes these ASCII chars beyond the JSON
# minimum. Only " and + occur in real CAI payloads; the rest are included because the
# encoder does escape them and a name or description could contain one.
DEFAULT_EXTRA = set('"+<>&' + chr(39) + "`")


def netjson(obj, extra=DEFAULT_EXTRA):
    """Serialize exactly like .NET System.Text.Json with JavaScriptEncoder.Default."""

    def esc(s):
        out = []
        for ch in s:
            o = ord(ch)
            if ch == BS:
                out.append(BS + BS)
            elif ch == "\n":
                out.append(BS + "n")
            elif ch == "\r":
                out.append(BS + "r")
            elif ch == "\t":
                out.append(BS + "t")
            elif o < 0x20 or o > 0x7E or ch in extra:
                out.append(BS + "u%04X" % o)
            else:
                out.append(ch)
        return "".join(out)

    def enc(v):
        if v is None:
            return "null"
        if v is True:
            return "true"
        if v is False:
            return "false"
        if isinstance(v, str):
            return '"' + esc(v) + '"'
        if isinstance(v, int):
            return str(v)
        if isinstance(v, float):
            return repr(v)
        if isinstance(v, list):
            return "[" + ",".join(enc(x) for x in v) + "]"
        if isinstance(v, dict):
            return "{" + ",".join('"' + esc(k) + '":' + enc(x) for k, x in v.items()) + "}"
        raise TypeError(type(v))

    return enc(obj)


def filehash(path):
    with open(path, "rb") as f:
        return base64.b64encode(hashlib.sha256(f.read()).digest()).decode()


# Key order as observed in the reference export. System.Text.Json emits properties in
# declaration order, so this order is part of the format, not cosmetic.
ITEM_KEYS = [
    "Accessibility", "BaseAvatarItemColor", "BaseAvatarItemId", "CreatedAt",
    "CreatorAccountId", "CurrentSaves", "CustomAvatarItemId", "CustomBadgeMetadata",
    "Description", "DesignFilename", "ForceCannotPublish", "IsFeatured",
    "IsRecRoomApproved", "ModifiedAt", "Name", "OutfitType", "PreviewOrientation",
    "Price", "RankedEntityId", "RankingContext", "Tags", "ThumbnailImageFilename",
]
SAVE_KEYS = [
    "AdditionalConfiguration", "BodyType", "CreatedAt", "CustomAvatarItemId",
    "CustomAvatarItemSaveId", "Description", "ModifiedAt", "OutfitType", "QAState",
    "ThumbnailFileName", "UnityAsset", "UnityAsset2", "UnityAsset2Hash",
    "UnityAssetHash", "UnityAssetId",
]


def order(d, keys):
    out = {k: d.get(k) for k in keys}
    for k in d:  # keep anything the reference did not have, at the end
        if k not in out:
            out[k] = d[k]
    return out


def build(spec_path, out_root):
    spec = json.load(open(spec_path, encoding="utf-8"))
    item = spec["item"]
    saves = spec["saves"]
    folder = item["Name"]
    dest = os.path.join(out_root, folder)

    built = []
    for i, s in enumerate(saves):
        sub = os.path.join(dest, str(i))
        os.makedirs(sub, exist_ok=True)
        rec = dict(s["fields"])
        for key, hkey, src in (
            ("UnityAsset", "UnityAssetHash", s["main_bundle"]),
            ("UnityAsset2", "UnityAsset2Hash", s["material_bundle"]),
        ):
            name = os.path.basename(src)
            shutil.copyfile(src, os.path.join(sub, name))
            rec[key] = name
            rec[hkey] = filehash(src)
        thumb = os.path.basename(s["thumbnail"])
        shutil.copyfile(s["thumbnail"], os.path.join(sub, thumb))
        rec["ThumbnailFileName"] = thumb
        built.append(order(rec, SAVE_KEYS))

    item = order(dict(item, CurrentSaves=built), ITEM_KEYS)
    blob = netjson(item).encode("utf-8")
    with open(os.path.join(dest, "avatarItem.json"), "wb") as f:
        f.write(blob)
    for i in range(len(built)):
        with open(os.path.join(dest, str(i), "%d_save.json" % i), "wb") as f:
            f.write(blob)
    print("wrote %s  (%d bytes json, %d saves)" % (dest, len(blob), len(built)))


def verify(export_dir):
    root = os.path.join(export_dir, "avatarItem.json")
    raw = open(root, "rb").read()
    item = json.loads(raw.decode("utf-8"))
    ok = True

    again = netjson(item).encode("utf-8")
    print("%-42s %s" % ("re-serializes byte-identical", "OK" if again == raw else "MISMATCH"))
    ok &= again == raw

    for i, s in enumerate(item["CurrentSaves"]):
        sub = os.path.join(export_dir, str(i))
        sv = os.path.join(sub, "%d_save.json" % i)
        same = os.path.exists(sv) and open(sv, "rb").read() == raw
        print("%-42s %s" % ("%d/%d_save.json identical" % (i, i), "OK" if same else "MISMATCH"))
        ok &= same
        for key, hkey in (("UnityAsset", "UnityAssetHash"), ("UnityAsset2", "UnityAsset2Hash")):
            p = os.path.join(sub, s[key])
            if not os.path.exists(p):
                print("%-42s MISSING" % ("%d/%s" % (i, s[key])))
                ok = False
                continue
            good = filehash(p) == s[hkey]
            print("%-42s %s" % ("%d/%s sha256" % (i, key), "OK" if good else "MISMATCH"))
            ok &= good
        t = os.path.join(sub, s["ThumbnailFileName"])
        print("%-42s %s" % ("%d/%s" % (i, s["ThumbnailFileName"]), "OK" if os.path.exists(t) else "MISSING"))
        ok &= os.path.exists(t)
    print("VERIFY", "PASS" if ok else "FAIL")
    return 0 if ok else 1


def cdnname(seed):
    """25-char lowercase base36 name, matching the shipped CDN filename style."""
    n = int.from_bytes(hashlib.sha256(seed.encode()).digest()[:16], "big")
    alpha = "abcdefghijklmnopqrstuvwxyz0123456789"
    return "".join(alpha[(n >> (5 * i)) % 36] for i in range(25))


def _resolve_one(descresolve, data, cat, desc):
    """desc -> (item-table name, prefab bundle, material bundle).

    `n` in AdditionalConfiguration is the ITEM-TABLE name, not the prefab basename. The two
    differ and the item table is inconsistent about the BB_ prefix, so neither can be derived
    from the other -- measured on both reference exports (2026-10-16):
        (ChickOutfit_Wrist)      item table, vs prefab (BB_ChickOutfit_Wrist)
        (BB_MLM_Chupacabra_Mouth) item table AND prefab, prefix kept
        (Mouth_CurlyMustache)    item table, vs prefab (BB_CurlyMustache_Mouth)
    Both real exports carry the item-table spelling verbatim.
    """
    name, prefab_name, main_bundle, mat_bundle = None, None, None, None
    for tok in descresolve.candidates(desc):
        guids, names = descresolve.find_guids(data, tok)
        if len(names) == 1 and name is None:
            name = names[0]
        for g in guids:
            for path, bundles in cat.lookup(g):
                if not bundles:
                    continue
                if path.endswith(".prefab") and main_bundle is None:
                    prefab_name = os.path.basename(path)[: -len(".prefab")]
                    main_bundle = bundles[0]
                elif path.endswith(".mat") and mat_bundle is None:
                    mat_bundle = bundles[0]
    if name is None:                           # ambiguous item table: fall back, and say so
        name = prefab_name
        if name:
            print("  ! item-table name ambiguous for %s; using prefab name %s" % (desc, name))
    if not (name and main_bundle and mat_bundle):
        raise SystemExit("could not resolve %s: name=%r main=%r mat=%r"
                         % (desc, name, main_bundle, mat_bundle))
    return name, main_bundle, mat_bundle


def fromdesc(data_dir, desc, out_root, outfit_type=None, item_id=None, fb_desc=None,
             body_types=(0, 1, 2), when=None):
    """Build an export for a shipped item, keyed off its AvatarItemDesc(s).

    `fb_desc` is the full-body (FB_) variant's desc. BodyType 1 uses it; 0 and 2 use `desc`
    -- the split both reference exports use. With it, each save gets `a` = its OWN desc and
    `p` = the partner's, which is how (ChickOutfit_Wrist) does it (the two swap between
    BodyType 0 and 1; verified by resolving both guids to the BB_ and FB_ prefabs).
    """
    import descresolve

    data = open(os.path.join(data_dir, "resources.assets"), "rb").read()
    cat = descresolve.Catalog(os.path.join(data_dir, "StreamingAssets", "aa"))

    base = _resolve_one(descresolve, data, cat, desc)
    full = _resolve_one(descresolve, data, cat, fb_desc) if fb_desc else None
    name = base[0]

    bun = os.path.join(data_dir, "StreamingAssets", "aa", "StandaloneWindows64")
    canon = caiids.canon(desc)
    if item_id:
        cai = str(uuid.UUID(str(item_id)))   # caller-supplied: the catalogue already owns it
        cai_src = "supplied"
    else:
        cai = str(caiids.item_id(desc))      # fallback: derived from the canonical desc
        cai_src = "derived from desc"
    stamp = when or "2026-01-01T00:00:00.000Z"
    otype = int(outfit_type) if outfit_type is not None else 101
    staging = os.path.join(out_root, ".staging-" + cai)
    os.makedirs(staging, exist_ok=True)

    saves = []
    for bt in body_types:
        use_fb = full is not None and bt == 1
        vname, vmain, vmat = full if use_fb else base
        own, partner = (fb_desc, desc) if use_fb else (desc, fb_desc)
        cfg = {"v": 1, "d": {"n": vname, "o": otype, "b": bt}}
        cfg["d"]["a"] = caiids._dashed(own)
        if partner:
            cfg["d"]["p"] = caiids._dashed(partner)
        cfg["ls"] = 1
        tag = "%s|%s|%%s|%d" % (canon, "fb" if use_fb else "bb", bt)
        m = os.path.join(staging, cdnname(tag % "main") + ".assetbundle")
        t = os.path.join(staging, cdnname(tag % "mat") + ".assetbundle")
        shutil.copyfile(os.path.join(bun, vmain), m)
        shutil.copyfile(os.path.join(bun, vmat), t)
        thumb = os.path.join(staging, cdnname(tag % "thumb") + ".png")
        if not os.path.exists(thumb):
            placeholder_png(thumb)
        saves.append({
            "fields": {
                "AdditionalConfiguration": json.dumps(cfg, separators=(",", ":")),
                "BodyType": bt, "CreatedAt": stamp, "CustomAvatarItemId": cai,
                "CustomAvatarItemSaveId": None, "Description": None, "ModifiedAt": stamp,
                "OutfitType": otype, "QAState": 0,
                "UnityAssetId": str(caiids.unity_asset_id(desc, bt)),
            },
            "main_bundle": m, "material_bundle": t, "thumbnail": thumb,
        })

    item = {
        "Accessibility": 1, "BaseAvatarItemColor": None, "BaseAvatarItemId": None,
        "CreatedAt": stamp, "CreatorAccountId": 1, "CustomAvatarItemId": cai,
        "CustomBadgeMetadata": None, "Description": None, "DesignFilename": None,
        "ForceCannotPublish": False, "IsFeatured": False, "IsRecRoomApproved": True,
        "ModifiedAt": stamp, "Name": name, "OutfitType": otype, "PreviewOrientation": 0,
        "Price": 0, "RankedEntityId": cai, "RankingContext": None,
        "Tags": [{"TagType": 0, "Value": "export"}], "ThumbnailImageFilename": None,
    }
    spec = os.path.join(staging, "spec.json")
    json.dump({"item": item, "saves": saves}, open(spec, "w", encoding="utf-8"))

    dest = os.path.join(out_root, name)
    if os.path.isdir(dest):
        shutil.rmtree(dest)          # same ids -> a re-export REPLACES
    build(spec, out_root)
    shutil.rmtree(staging, ignore_errors=True)
    print("desc      %s" % canon)
    if fb_desc:
        print("fb desc   %s   -> BodyType 1" % caiids._dashed(fb_desc))
    print("item id   %s   (%s; re-running rewrites this same folder)" % (cai, cai_src))


def placeholder_png(path):
    """1x1 PNG stand-in. Built-ins ship no CAI-style thumbnail; replace with a real render."""
    import struct as _s
    import zlib

    def chunk(tag, payload):
        body = tag + payload
        return _s.pack(">I", len(payload)) + body + _s.pack(">I", zlib.crc32(body) & 0xFFFFFFFF)

    ihdr = _s.pack(">IIBBBBB", 1, 1, 8, 2, 0, 0, 0)
    idat = zlib.compress(bytes([0, 40, 40, 48]))
    sig = bytes([137, 80, 78, 71, 13, 10, 26, 10])          # PNG magic
    with open(path, "wb") as f:
        f.write(sig + chunk(b"IHDR", ihdr) + chunk(b"IDAT", idat) + chunk(b"IEND", b""))


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(2)
    if sys.argv[1] == "fromdesc":
        fromdesc(sys.argv[2], sys.argv[3], sys.argv[4], *sys.argv[5:8])
    elif sys.argv[1] == "build":
        build(sys.argv[2], sys.argv[3])
    elif sys.argv[1] == "verify":
        sys.exit(verify(sys.argv[2]))
    else:
        print(__doc__)
        sys.exit(2)
