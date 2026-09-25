"""Deterministic CustomAvatarItem ids derived from an AvatarItemDesc.

The desc is the unique key -- the *name* is not. Several descs resolve to the same
system name (`(Shirt_SteamPunk)` the base item and the
`fD5vtKxBWECH54Jj4FbnUg,C8gCmBZ8RUG83vvDw_UYew,` combination both come back as
`(SteamPunk_Shirt)`), so naming the id after the prefab collides across variants.

    item_id(desc)                  -> CustomAvatarItemId / RankedEntityId
    unity_asset_id(desc, body)     -> that save's UnityAssetId

Both are stable: the same desc always yields the same id, so rebuilding an export does
not mint a new identity, and two different variants can never collide.

## Canonicalisation

Descs appear in two spellings and with a varying number of trailing commas, all meaning
the same tuple (see rr-client-bringup/references/desc-registry-2023-layout.md):

    E9VTiIVFPEa-OuQRto0e_Q,fD5vtKxBWECH54Jj4FbnUg,C8gCmBZ8RUG83vvDw_UYew,
    8853d513-4585-463c-be3a-e411b68d1efd,b46f3e7c-...,9802c80b-...,

`canon()` folds both to lowercase dashed guids in three fixed slots with a trailing comma,
empty slots left empty -- matching `NPHONPGHNPF`, the 3-guid desc struct, where an absent
member is Guid.Empty. So `a,b,` and `a,b,,` are the same item and get the same id, which
is correct.

## UUID version

Real Rec Room ids are **v4** (`(Floaties_Wrist)` is `51a5bf06-f926-474a-a9fb-aed9a5e48d11`,
and its three UnityAssetIds are v4 too). These are hash-derived but the version and variant
nibbles are forced to v4/RFC-4122, so they are indistinguishable from a random v4 to
anything that inspects them. They are NOT random -- that is the point -- but nothing in the
client checks, and a deterministic id is what makes a rebuild idempotent.

usage: py caiids.py <desc>
"""

import base64
import hashlib
import sys
import uuid

# Fixed namespace for this project. Changing it re-mints every id, so do not.
NS = uuid.uuid5(uuid.NAMESPACE_URL, "recflare/customavataritem")
SLOTS = 3


def _dashed(tok):
    """One token -> lowercase dashed guid, accepting either wire spelling."""
    tok = tok.strip()
    if not tok:
        return ""
    try:
        if len(tok) == 36 and "-" in tok:
            return str(uuid.UUID(tok))
        if len(tok) == 22:
            return str(uuid.UUID(bytes_le=base64.urlsafe_b64decode(tok + "==")))
    except Exception:
        pass
    return tok.lower()          # unparseable: keep it verbatim rather than silently drop


def canon(desc):
    """Canonical desc: three slots, lowercase dashed, trailing comma."""
    toks = [_dashed(t) for t in desc.split(",")]
    while toks and not toks[-1]:
        toks.pop()
    if len(toks) > SLOTS:
        raise ValueError("desc has %d tokens, expected at most %d: %r" % (len(toks), SLOTS, desc))
    toks += [""] * (SLOTS - len(toks))
    return ",".join(toks) + ","


def _v4_from(name):
    """Deterministic, v4-shaped uuid from a name string."""
    b = bytearray(hashlib.sha256(name.encode("utf-8")).digest()[:16])
    b[6] = (b[6] & 0x0F) | 0x40          # version 4
    b[8] = (b[8] & 0x3F) | 0x80          # RFC 4122 variant
    return uuid.UUID(bytes=bytes(b))


def item_id(desc):
    return _v4_from("%s|item|%s" % (NS, canon(desc)))


def unity_asset_id(desc, body_type):
    return _v4_from("%s|asset|%s|%d" % (NS, canon(desc), body_type))


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(2)
    d = sys.argv[1]
    print("desc      : %s" % d)
    print("canonical : %s" % canon(d))
    i = item_id(d)
    print("item id   : %s  (v%d)" % (i, i.version))
    for bt in range(3):
        a = unity_asset_id(d, bt)
        print("  asset[%d]: %s  (v%d)" % (bt, a, a.version))
