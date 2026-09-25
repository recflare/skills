# CustomAvatarItem export format

> The `S:\RecRoom\1\(Name)` exports are fully specified and reproducible: hashes are base64(SHA-256(file)), `N_save.json` is a byte-identical copy of `avatarItem.json`, and the JSON is System.Text.Json with the default encoder. `tools/il2cpp/caiexport.py` rebuilds one byte-for-byte. But every bundle in that library is Unity **6000.0.27f1** while recflare-2025 runs **2021.3.41f1** — they are from a newer client than the one being brought up.

Derived **2026-09-25** from `S:\RecRoom\1\(Floaties_Wrist)` and the 2023/2025 client data.
Companion to [desc-registry-2023-layout](desc-registry-2023-layout.md) (which resolves a desc to a shipped asset) and
[avatar-item-desc-registry](../../rr-client-bringup/references/avatar-item-desc-registry.md) (why built-ins cannot be smuggled in as CAI).

## Layout

```
(Name)[  <CombinationName>]/          <- two spaces before the combination suffix
    avatarItem.json                   <- the only file that matters
    0/  0_save.json                   <- redundant byte-identical copy of avatarItem.json
        <UnityAsset>.assetbundle
        <UnityAsset2>.assetbundle
        <ThumbnailFileName>.png
    1/  ...                           <- one folder per CurrentSaves entry; index == BodyType
    2/  ...
```

Asset filenames are 25-char lowercase base36 CDN names (`3ol0a7cf9pbftz52vvwzn2h50`), not hashes.

## Formats, all confirmed by round-trip

| rule | evidence |
|---|---|
| `UnityAssetHash` = `base64(SHA-256(UnityAsset file))`, same for `UnityAsset2Hash` | recomputed, exact match on all 6 bundles |
| `avatarItem.json` == every `N_save.json`, byte for byte | `cmp` clean; all three are the same 2942 bytes. **User-confirmed 2026-09-25: this holds across the entire library, and `avatarItem.json` is the only one that matters** — the `N_save.json` copies are redundant, so a consumer should read the root file and a producer can emit the copies purely for shape-compatibility (or skip them) |
| JSON = **System.Text.Json, default `JavaScriptEncoder`**: compact, declaration-order properties, `"` → `\u0022` and `+` → `\u002B` (**uppercase** hex) | re-serializing the parsed DTO reproduces all 2942 bytes |

`tools/il2cpp/caiexport.py verify <dir>` checks all of the above; `caiexport.py build <spec> <out>`
writes one. Rebuilding `(Floaties_Wrist)` from its own parts gives **13 files, 0 differences**.

## The two bundles are a fixed pair, named from `UnityAssetId`

The **internal** AssetBundle name (inside the UnityFS payload) is
`<UnityAssetId with dashes stripped>.AvatarItem.<Variant>.<major>.<minor>.assetbundle`:

| DTO field | internal name | content |
|---|---|---|
| `UnityAsset` | `636241fd0f1c46728801eb196bbf5f09.AvatarItem.**Main**.0.5.assetbundle` | mesh + prefab (`Floaties_Wrist_LOD0/1/2`, `Hand.Rig`, `BlendShapeData`) |
| `UnityAsset2` | `636241fd0f1c46728801eb196bbf5f09.AvatarItem.**Material**.0.6.assetbundle` | materials/textures, ~4 MB payload |

So the file names on disk are arbitrary but the **internal** name is derived from `UnityAssetId` —
renaming a bundle is not enough to repoint it.

## `AdditionalConfiguration` decoded

A JSON **string** containing JSON:

```json
{"v":1,"d":{"n":"(Floaties_Wrist)","o":200,"b":0,
            "p":"3efa4ffb-74e7-4622-a7ea-1569ddb78f0a",
            "a":"c7c85554-e118-4433-8d6b-b61a2971e045"},"ls":1}
```

| key | meaning |
|---|---|
| `n` | item name (the `(Name)` or `(Name)  Combination` form) |
| `o` | `OutfitType` (repeated from the save) |
| `b` | body/base flag |
| **`a`** | **the built-in avatar item id** — the same value the 2023 item table stores next to `(Floaties_Wrist)` |
| `p` | a second GUID, not present in the 2023 registry (prefab/base parent) |
| `ir` | initial rotation, e.g. `[0,-64,0]` |
| `ls` | present (=1) only on saves that carry `b`/`p`/`a` |

**`a` is verifiable.** `c7c85554-e118-4433-8d6b-b61a2971e045` sits directly beside
`(Floaties_Wrist)` in `RecRoom_Data/resources.assets` at `0x0DC00298`, in exactly the slot
`E9VTiIVFPEa-OuQRto0e_Q` occupies for `(Shirt_SteamPunk)`. Chasing it further:
registry → asset GUID `923298a891971db4b809b97e9fff47e3` → catalog →
`Assets/Core/Content/Avatar/Props/Wrist/(Floaties_Wrist).prefab` →
`338c2e2fb195fb9b23bf72f4828cfee6.bundle`. The chain closes.

Saves **without** `b`/`p`/`a`/`ls` (e.g. Floaties BodyType 1 and 2) are genuine uploaded meshes;
saves **with** them reference a shipped built-in.

## ⚠️ Two blockers for reusing shipped assets as CAI

**1. Unity version.** Every one of the **15,376** bundles across **2,830** item folders in
`S:\RecRoom\1` is **`6000.0.27f1`**. The clients here are:

| build | Unity |
|---|---|
| recflare-2023 (`20230414`) | `2020.3.33f1` |
| recflare-2025 (`20250718.01`) | `2021.3.41f1` |
| the `S:` export library | **`6000.0.27f1`** |

Unity will not load a bundle built by a newer major version, so that library targets a client newer
than either local build. Confirm the runtime version before assuming an export will load.

**2. Packaging.** Shipped built-ins are **Addressables** bundles with external dependency bundles
(`(Floaties_Wrist).prefab` alone pulls four, including a 41.8 MB shared one). CAI bundles are
self-contained Main+Material pairs with an `AvatarItemId`-derived internal name. Copying a shipped
`.bundle` into the `UnityAsset` slot produces a structurally valid export whose bundle cannot
resolve its dependencies. Converting one to the other is a Unity **rebuild**, not a file copy —
`caiexport.py` handles the wrapper, not the repack.


## Re-exporting must not mint duplicates: key ids off the DESC

The system name is **not** unique -- `(Shirt_SteamPunk)` the base item and the
`fD5vtKxBWECH54Jj4FbnUg,C8gCmBZ8RUG83vvDw_UYew,` combination both resolve to the prefab
`(SteamPunk_Shirt)`. Naming an id after the prefab collides across variants. The **desc** is the
unique key, so `tools/il2cpp/caiids.py` derives every identity from it:

    item_id(desc)               -> CustomAvatarItemId / RankedEntityId
    unity_asset_id(desc, body)  -> that save's UnityAssetId

Canonicalisation first, because one desc has many spellings: tokens are folded to lowercase dashed
guids in three fixed slots with a trailing comma (matching `NPHONPGHNPF`, where an absent member is
Guid.Empty). Verified equal across base64url vs dashed vs mixed, uppercase, whitespace, and missing
or extra trailing commas; verified distinct for the base item, the combination, `(Neck_SteamPunk)`
and a slot-order swap.

Ids are **v4-shaped but hash-derived** -- SHA-256 with the version/variant nibbles forced -- because
the real exports are v4 (`(Floaties_Wrist)` is `51a5bf06-f926-474a-a9fb-aed9a5e48d11`, v4, as are its
three `UnityAssetId`s). Nothing in the client checks, but they should not look odd.

`caiexport.py fromdesc <data-dir> <desc> <out-root> [outfitType]` is the idempotent path: ids **and**
the 25-char CDN-style filenames are seeded from the canonical desc, and an existing folder is
replaced rather than added to. Re-running with a *different spelling of the same desc* reproduces
**13 files, 0 byte differences, 0 orphans**.
