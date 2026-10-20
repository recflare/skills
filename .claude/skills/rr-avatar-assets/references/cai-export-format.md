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

⚠️ **This is the AssetBundle OBJECT's `m_Name` inside the SerializedFile, not the `CAB-…` directory
name** (clarified 2026-10-16 after conflating the two). A real CAI bundle's blocksInfo names a plain
`CAB-6ba95bca56e91b98d3eb742456b3b9cc`, exactly like any Addressables bundle, so a `CAB-…` name is
**not** a sign of anything wrong. Verified on `(ChickOutfit_Wrist)` BodyType 0, whose payload carries
`25f07e986225475cbd47d142628c1303.AvatarItem.Main.0.5.assetbundle` and whose save's `UnityAssetId`
is `25f07e98-6225-475c-bd47-d142628c1303`.

⚠️ **CORRECTED 2026-10-16: the name is NOT cosmetic.** An earlier revision of this note argued it
was, because `.AvatarItem.`, `AvatarItem.Main`, `Main.0.5` and `.0.5.assetbundle` each have **0
literal occurrences** in `20250718.01` and `20260323.14`. That was the wrong inference from a true
scan — **the client builds the name from pieces**, and every piece is a literal:
`'AvatarItem'` `0xD11B980`, `'Main'` `0xD1EBFB8`, `'Material'` `0xD25B558`. Match the name.

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
| `p` | **the SIBLING variant's desc** — see below |
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

⚠️ **CORRECTED 2026-10-16 — the Unity version string does not gate loading. The bundle FORMAT
version does.** User-confirmed in-game: they were wearing `S:\RecRoom\1\Bog Monster Hood`, all six
of whose bundles are `6000.0.27f1`, in the **2021.3.41f1** client. Measured header format versions:

| artifact | unity | bundle format |
|---|---|---|
| `S:\RecRoom\1` donors | `6000.0.27f1` | **8** |
| recflare-2025 shipped bundles | `2021.3.41f1` | **8** |
| refreshed recflare-2023 | `2021.3.29f1` | **8** |
| `rr_pc_cai_convert.py` output | `2021.3.29f1` | **8** |
| original `20230414` recflare-2023 | `2020.3.33f1` | **7** |

Everything current is format 8 and interoperates in both directions. **So the whole 15,376-bundle
`S:` library is usable as donor material on the 2025 client**, which is what unblocks grafting a
Material bundle. The one real version hazard on record is the original 2023 build's **format 7**
bundles. Check the format byte (big-endian `u32` right after the `"UnityFS\0"` magic), not the
version string.

**2. Packaging — a real CAI bundle has ZERO external references.** Measured 2026-10-16 by
decompressing both payloads and grepping for `archive:/`:

| bundle | `archive:/CAB-…` externals |
|---|---|
| real CAI Main (`(ChickOutfit_Wrist)` BodyType 0) | **0** |
| a shipped Addressables prop bundle wrapped by `fromdesc` | **3** |

A CAI load path takes exactly two files, `UnityAsset` and `UnityAsset2`, so there is **nowhere to put
a third dependency** — and the Addressables `archive:/CAB-…/CAB-…` form only resolves if that bundle
is mounted under that exact archive name, which a CDN-named CAI file never is. For the Curly
Mustache the three were:

```
CAB-2bfcbd17… -> 91aca73acb86d6607f0efa1f803348be.bundle  8.6 MB   shared shaders
CAB-87bcef62… -> 490b8c961642e49683bed53c45d18d46.bundle  3,075 B  monoscripts
CAB-963ae7bd… -> befe519aa765f9884bc170153b44b2b7.bundle  1.3 MB   Mat_Hair.mat  <- shipped AS UnityAsset2
```

Note the third: the material **is** already shipped alongside as `UnityAsset2`, but the prefab
reaches it through an archive path instead of a plain cross-bundle reference, so even that one does
not resolve. Converting a shipped bundle to a CAI is a Unity **rebuild**, not a file copy —
`caiexport.py` handles the wrapper, not the repack.

### Runtime signature of this failure (2025 client)

```
[Exception] Object reference not set to an instance of an object.
   at IPAJMIDFOGP+BBBDDKMKLCL.KNHIMANFDCI (Task`1 …)
[Warning] PrefetchResourcesHelper Promise failed with error: An error occurred for (Mouth_CurlyMustache)
[Error]   OutfitPrefab for AvatarItem "(Mouth_CurlyMustache)" is null
```

`OutfitPrefab … is null` comes from `GHEPCIFAOCN$$GCNBJJDIICE` `0x7FA8520` (literal `0xD0BE0F0`);
the prefetch warning from literal `0xD2A1F20`. Reaching that line means the DTO, the ids and the
download were all fine and the **bundle** is what failed — do not go looking at the JSON.

### A side-load path exists on 2025: `StreamingAssets/avatar/*.assetbundle`

`MCLAMKLJFAP$$MoveNext` `0x2670E50` does
`Path.Combine(Application.streamingAssetsPath, "avatar")` → `Directory.Exists` (else warns
`Avatar folder does not exist in StreamingAssets.`) → `Directory.GetFiles(dir, "*.assetbundle")` →
logs `Number of .assetbundle files in StreamingAssets/Avatar: {0}`. There is also a
`.lz4.assetbundle` literal. **Untested**, and it does not fix self-containment, but it is a much
shorter loop than the CDN path for trying a Studio-built bundle.


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

`caiexport.py fromdesc <data-dir> <desc> <out-root> [outfitType] [itemId]` is the idempotent path:
ids **and** the 25-char CDN-style filenames are seeded from the canonical desc, and an existing
folder is replaced rather than added to. Re-running with a *different spelling of the same desc*
reproduces **13 files, 0 byte differences, 0 orphans**.

### ⚠️ The derived `CustomAvatarItemId` is a FALLBACK, not an authority

Added **2026-10-16** after an export was built with a synthesised id while the caller's own catalogue
row already had one. `caiids.item_id(desc)` exists for the case where **a desc is all you have**. If
any upstream record — a catalogue CSV, a DB row, a request payload — already carries a
`CustomAvatarItemId`, that id wins, and `fromdesc` now takes it as the optional 5th argument:

```
py caiexport.py fromdesc <2023 data> "<desc>" <out> 20 "5f00002b-8092-438c-8763-cc8ebd7eaf4d"
item id   5f00002b-8092-438c-8763-cc8ebd7eaf4d   (supplied; re-running rewrites this same folder)
```

It sets `CustomAvatarItemId` **and** `RankedEntityId` on the item and on every save. **An invented id
that disagrees with the server's is a duplicate item, not a cosmetic difference** — the client keys
ownership, equips and the store row off it.

`UnityAssetId`s stay desc-derived either way: they are per-save *upload* ids with no external source
in this pipeline. Override them too if the catalogue has them.

**How to apply:** before running `fromdesc`, look at whatever row the item came from and check for an
existing id. In a CSV like `Curly Mustache,5f00002b-…,,,6b337a35-…` the **first** GUID is the
`CustomAvatarItemId` and the **last** is the desc — resolve the last, pass the first.

## `n`, `a` and `p` across body types — measured on two reference exports

Established **2026-10-16** from `(ChickOutfit_Wrist)` and `Chupacabra Mutton Chops`, after resolving
every guid in them against the refreshed 2023 build.

### `a` is this save's OWN desc, `p` is the partner variant's

`(ChickOutfit_Wrist)` swaps them between body types, which is what makes the roles unambiguous:

```
BodyType 0  "n":"(ChickOutfit_Wrist)"      "a":"9eb95934-…"  "p":"5c421d21-…"
BodyType 1  "n":"(FB_ChickOutfit_Wrist)"   "a":"5c421d21-…"  "p":"9eb95934-…"
```

and resolving both:

```
9eb95934-90f3-4f48-a6b4-d87d75d9bdc4 -> Props/Wrist/(BB_ChickOutfit_Wrist).prefab
5c421d21-c71a-46ae-8af5-74d57f31ad4b -> Props/FB_Wrist/(FB_ChickOutfit_Wrist).prefab
```

So **`a` = the desc of the asset this save actually uses, `p` = the other body's desc.** This
supersedes the earlier "`p` is a second GUID not present in the registry" reading — on a build whose
registry can be searched, `p` resolves cleanly to the sibling.

### ⚠️ `n` is the ITEM-TABLE name, not the prefab basename

The two differ, and the item table is **inconsistent** about the `BB_` prefix, so neither spelling
can be derived from the other:

| desc resolves to prefab | item-table name | `n` in the real export |
|---|---|---|
| `(BB_ChickOutfit_Wrist)` | `(ChickOutfit_Wrist)` | **`(ChickOutfit_Wrist)`** |
| `(FB_ChickOutfit_Wrist)` | `(FB_ChickOutfit_Wrist)` | `(FB_ChickOutfit_Wrist)` |
| `(BB_MLM_Chupacabra_Mouth)` | `(BB_MLM_Chupacabra_Mouth)` | **`(BB_MLM_Chupacabra_Mouth)`** |
| `(BB_CurlyMustache_Mouth)` | `(Mouth_CurlyMustache)` | *(ours)* `(Mouth_CurlyMustache)` |

Chupacabra keeps its prefix, ChickOutfit drops it, and the mustache reverses the word order
entirely — but **every real export carries the item-table spelling verbatim**. `fromdesc` now takes
`n` (and the folder name) from the item table and falls back to the prefab basename only when the
item table is ambiguous, printing a warning when it does.

### BodyType 1 takes the FB desc; 0 and 2 share the base

Both references do this. `fromdesc`'s optional 6th argument is the FB desc:

```
py caiexport.py fromdesc <data-dir> <desc> <out-root> [outfit-type] [item-id] [fb-desc]
```

### Keys this tool does NOT emit, because they were not derived

`(ChickOutfit_Wrist)` also carries `"hh":1`, `"ir":[0,-64,0]`, `"is":1.3` and, on BodyType 2,
`"m":98304` with **no** `b`/`a`/`p`; Chupacabra's BodyType 1 has `"m":131072` and a nested
`"d":{"c":0,"p":1}`. Their meanings are unmeasured, so an export built by `fromdesc` omits them
rather than guessing a value. ⚠️ Note that BodyType 2 of ChickOutfit keeps `"ls":1` **without**
`b`/`p`/`a`, which contradicts the earlier "`ls` is present only on saves that carry `b`/`p`/`a`"
reading — treat `ls` as independent.

## Converting a shipped Addressables bundle into a CAI bundle — the measured contract

Established **2026-10-16** by loading a real CAI bundle and a `fromdesc`-wrapped shipped bundle side
by side with UnityPy (the venv in `C:\Games\asset-converter` has UnityPy 1.25.3), after the 2025
client rejected the wrapped one with `OutfitPrefab for AvatarItem "(Mouth_CurlyMustache)" is null`.

| | real CAI **Main** | real CAI **Material** | shipped bundle wrapped by `fromdesc` |
|---|---|---|---|
| `m_Name` | `25f07e98….AvatarItem.Main.0.5.assetbundle` | `25f07e98….AvatarItem.Material.0.6.assetbundle` | `dc538c307719a340a9bf3b1ee35bfe7f.bundle` |
| **`m_Container` keys** | **`['prefab']`** | **`['MaterialMap']`** | **8 Addressables asset paths** |
| `m_Dependencies` | `[]` | `['cab-28703d9f…']` (shader) | `['cab-2bfcbd17…','cab-87bcef62…','cab-963ae7bd…']` |
| objects | 17 GO/Transform, 3 SkinnedMeshRenderer, 3 Mesh, 1 LODGroup, MonoBehaviour, MonoScript | 3 Texture2D, Material, MonoBehaviour, MonoScript | same **plus** 6 SkinnedMeshRenderer, 2 LODGroup, `Animator`, `Avatar` |

### ⚠️ `m_Container` is the load key — this is what `OutfitPrefab … is null` means

A CAI Main bundle exposes its prefab under the single container key **`prefab`**, and the Material
bundle under **`MaterialMap`**. Both are client literals (`'prefab'` `0xD08A600`,
`'MaterialMap'` `0xD25E040`), so the client fetches by that key. An Addressables bundle keys its
container by **full asset path**, so the lookup returns nothing and `OutfitPrefab` is null. **That is
a container rewrite, not a mesh problem** — the prefab name inside the bundle
(`(BB_CurlyMustache_Mouth)`) is already correct, and a real CAI bundle uses the `BB_`-prefixed
prefab name too, not the `n` spelling.

### The authoritative output contract

`research/batch_stage_quest_wearables.py::validate_pair()` in `C:\Games\asset-converter` already
encodes it (written for Quest; the platform and texture clauses are the only Android-specific ones):

- `m_Name` = `{UnityAssetId without dashes}.AvatarItem.Main.0.5.assetbundle` / `.Material.0.6.assetbundle`,
  plus a **byte-identical `cab12-` alias of main**
- `m_Container` exactly `['prefab']` and `['MaterialMap']`
- **no `AssetBundle` dependencies on main**, and **no serialized-file externals on main**, with
  **renderer material pointers nulled**
- material's only external/dependency is the shader CAB
- textures fully **inline** (`m_StreamData` zeroed, no `.resS`)
- mesh/LOD counts never exceed the source prefab

### PC → PC is the easy direction

For a 2023→2025 port the expensive half of that tool does not apply: both are
`StandaloneWindows` (`targetPlatform 5`, keep it — do **not** retarget to 13), both are Unity
`2021.3.x`, and the DXT textures need no re-encode. What remains is structural surgery UnityPy can do
without a Unity editor: rewrite `m_Container`/`m_Name`, drop `m_Dependencies` and externals on main,
null the renderer material pointers, and split the material + textures into a second bundle with a
`MaterialMap` container.

⚠️ The shipped bundle also carries **more objects than the contract allows** — 6
SkinnedMeshRenderers and 2 LODGroups against the real 3 and 1, plus an `Animator` and an `Avatar`.
An Addressables prop bundle packs the prefab *and* its source `.fbx` variants, so a conversion has to
prune to the prefab's own hierarchy rather than copy objects wholesale.

### What this retires

The earlier conclusion here — "converting one to the other is a Unity **rebuild**, not a file copy"
— was **too strong**. The dependency and self-containment analysis was right, but the fix is
bundle surgery, not re-authoring: a known-good contract plus UnityPy covers it. `caiexport.py` still
only builds the wrapper.

### The converter: `C:\Games\asset-converter\rr_pc_cai_convert.py`

Written **2026-10-16**. Does the Main-bundle half of the conversion headlessly (UnityPy, no Unity
editor), and its `checks()` is `validate_pair()`'s Main clauses with the Android ones dropped:

```
venv/Scripts/python rr_pc_cai_convert.py --main <shipped.bundle> --asset-id <UnityAssetId> \
    --out <dir> --also-write-cab12 --report report.json
```

Verified on the Curly Mustache (`1ae3f8451f72c546fe47cc4df8cc357c.bundle`, asset id
`23d90fe9-513f-441c-a2fd-68f7f2dde69a`): all four checks pass, header still
`UnityFS … 8 5.x.x 2021.3.29f1` (platform untouched), `m_Container == ['prefab']`,
`m_Dependencies == []`, no externals, 127,860 B plus the `cab12-` alias.

**Still open:** the Material bundle needs a `MaterialMap` MonoBehaviour and UnityPy cannot create
objects, so it needs a donor CAI Material bundle at the target Unity version. Object pruning is also
not done — output keeps the source `.fbx` variants' renderers (6 SkinnedMeshRenderer / 2 LODGroup /
Animator / Avatar vs a real Main's 3 / 1 / none), which is unverified as harmful.

### Packing converted bundles back into an export folder

`C:\Games\asset-converter\cai_pack_converted.py <export-dir>` converts the bundles of a finished
`fromdesc` export **in place**, then fixes the JSON:

```
venv/Scripts/python cai_pack_converted.py "C:\Games\cai-export\(Mouth_CurlyMustache)" \
    --also-write-cab12
```

Two things it gets right that are easy to miss:

- **Each save needs its own `UnityAssetId` in `m_Name`.** The three saves have three different ids,
  so the three Main bundles must not share a name — pass the save's id, not the item's.
- ⚠️ **Recompute `UnityAssetHash` / `UnityAsset2Hash`.** The surgery changes the bundle bytes, so
  the hashes `caiexport.py` wrote are stale immediately and `verify` fails. The driver re-serializes
  with `caiexport.netjson` and rewrites all three `N_save.json` copies from the same blob.

Verified on the Curly Mustache: three Mains at `{saveAssetId}.AvatarItem.Main.0.5.assetbundle` with
`m_Container == ['prefab']`, `cab12-` aliases, recomputed hashes, **`caiexport.py verify` →
VERIFY PASS**.

### Runtime proof that the container rewrite is the fix, and what breaks next

Loading the converted Main in the **2026** client moved the error off the prefab entirely:

```
before:  [Error] OutfitPrefab for AvatarItem "(Mouth_CurlyMustache)" is null
after:   [Exception] Object reference not set to an instance of an object.
           at RecRoom.Avatars.AvatarMaterialKey..ctor (Material material, UpdatableColorType,
                                                       UpdatableTextureType, AvatarBodyPart)
           at RecRoom.Avatars.AvatarDisplaySystem.DJCZTJEJUQO (Dictionary, Material, …)
```

`AvatarMaterialKey..ctor` `0x97D4700` calls **`Material.HasProperty`** (`0x97D47A8`) and
**`Material.GetTexture`** (`0x97D47E5`) on the parameter with no null guard — the only branch is
`lea eax,[rdi-1]; cmp eax,1; jbe` on `updatableTextureType`. So a **null `Material`** reaches it.
That is the expected consequence of nulling the renderer material pointers (which the contract
requires) while the Material bundle still has no `MaterialMap` to supply them from.

**So the prefab now loads and the material is the next blocker** — which is the diagnosis the
container theory predicted, arrived at from the client rather than from structure.

### Borrowing a donor Material bundle to isolate the remaining work

`cai_pack_converted.py --donor-material <real CAI material bundle> --mm-guid <prefabAssetGuid>`
copies a working Material bundle into the save and renames its MonoBehaviour to
`{ourPrefabAssetGuid}-MaterialMap`. Chupacabra Mutton Chops is the only `OutfitType 20` item in the
library, so it is the natural donor for facial hair. Result on the Curly Mustache: all three saves
`['MaterialMap']` with one dependency, `VERIFY PASS` — **rendering with the donor's textures**, which
separates "structure correct" from "textures correct".

### ⚠️ `MaterialMap.entries` is one per MATERIAL SLOT, not one per renderer

Measured **2026-10-16** after the donor-packed item loaded with **no error and nothing visible** —
the "it 200s but shows nothing" failure, so the diff-against-a-working-one technique applied rather
than disassembly:

| item | renderers | material slots per renderer | MaterialMap entries |
|---|---|---|---|
| Chupacabra Mutton Chops bt0 | 3 | **2** | **2** |
| `(ChickOutfit_Wrist)` bt0 | 3 | **1** | **1** |
| converted Curly Mustache bt0 | 6 (3 real + 3 `.fbx` dupes) | **1** | needs **1** |

Entries are indexed by **material slot**, shared across all renderers and LOD levels. So the donor
must be chosen by **slot count, not OutfitType**: Chupacabra is the only `OutfitType 20` item in the
library and is therefore the obvious donor for facial hair, but its 2 entries are wrong for a 1-slot
prefab. `(ChickOutfit_Wrist)` is a Wrist item with a matching 1-entry map and the same `AG/Avatar`
shader.

Read the slot count off the Main bundle (`m_Materials` length on any `SkinnedMeshRenderer`) and pick
a donor whose entry count equals it.

The export now carries a 1-entry map (`VERIFY PASS`). **Untested in-client at the time of writing.**

### ⚠️ The thumbnail is a 1x1 placeholder, and that alone looks like "no model preview"

`fromdesc` writes a **69-byte 1x1 PNG** per save. Real exports carry 850 KB – 1.7 MB renders. If the
wardrobe preview is the *thumbnail image* rather than a live instantiation of the prefab, a 1x1
image renders as nothing and the symptom is indistinguishable from a broken prefab — with no log
line either way.

`cai_pack_converted.py --donor-thumbnail <a real .png>` substitutes a visible stand-in, which
**discriminates the two paths in one test**: if the preview now shows the donor's picture, the
preview is thumbnail-driven and the prefab was never involved; if it stays blank, the preview
instantiates the prefab and the model path is still wrong.

Run that before digging into prefab internals — it is one copy and it eliminates half the
search space.

### The A/B that isolates what Studio actually does

Converting the **same item** two ways settles what a shipped bundle is missing, with everything else
held constant. `(ChickOutfit_Wrist)` exists both as a shipped Addressables bundle in the refreshed
2023 build **and** as a known-working CAI export in `S:\RecRoom\1`:

| | real CAI (works) | our conversion of the shipped bundle |
|---|---|---|
| GameObject / Transform | 17 / 17 | **33 / 33** |
| SkinnedMeshRenderer | 3 | **6** |
| Mesh | 3 | 3 |
| LODGroup | **1** (on `ChickOutfit_Wrist_fbx`) | **2** (also on `BB_ChickOutfit_Wrist`) |
| MonoScript | **`RecRoomStudioAvatarItem`** | **`OutfitPrefab`** |
| extras | — | an `AnimationClip` |

**Studio rebuilds a trimmed prefab with a different root component**; it does not repackage the
shipped one. The working bundle contains **no `OutfitPrefab` whatsoever**. Run this A/B before
theorising about any individual field — it converts "what might matter?" into a diff.

`--studio-marker` on both tools rewrites the bundle's single MonoScript identity to
`RecRoom.Core.Studio.AvatarItems.RecRoomStudioAvatarItem` /
`RecRoom.Studio.Common.Runtime`. The marker declares **no fields**, so the MonoBehaviour's leftover
`_sourceMeshRenderer` / `AllowFitMeshOverride` / `FitMeshPivot` bytes are simply never read.
**Tried in-client: no change.** Leave it off by default — see the correction below.

### ⚠️ "OutfitPrefab for AvatarItem … is null" means the prefab GAMEOBJECT, not the component

Corrected **2026-10-16**. The message comes from
`RecRoom.Avatars.ILFGOWCKVFC$$ISWNSLZPTBJ(uint, AvatarSkinnedMeshBoneOrderRemapsData)`
`0x97DA240`, which null-checks the GameObject held by a
`RecRoom.Avatars.LoadedAvatarItemPrefabHolder` and passes it to `MDCMTXEPGLQ`. It is **not** about
the `RecRoom.Avatars.Outfit.OutfitPrefab` component. Reading it that way is what motivated
`--studio-marker`, and the marker changed nothing in-client.

### What the client actually does with the prefab

`RecRoom.Avatars.ILFGOWCKVFC$$MDCMTXEPGLQ(GameObject outfitObject, uint, bool, bool, …)`
`0x97DA440 .. 0x97DA639` (⚠️ bound it with `fstart.py` — a `names.py <rva> 0x900` overruns into the
next methods and attributes `"Did not have valid skin mesh data for LOD {0}"` and a
`TLXTSWBFKAY..ctor` to it that are not its own):

```
if (outfitObject == null) throw ArgumentNullException("outfitObject")   ; literal 0x97DA5F8
lodGroup = outfitObject.GetComponentInChildren<LODGroup>()              ; 0x97DA4D9, inst #18147
if (lodGroup != null) lods = lodGroup.GetLODs()                         ; 0x97DA533
else                  renderers = outfitObject.GetComponentsInChildren  ; 0x97DA511, inst #1348
… Object.get_name + DVVVWEAHKNV(Renderer[], string, Renderer, Renderer) ; 0x97DA586
… TLXTSWBFKAY.IWPCWBJNIAT                                               ; 0x97DA5C6
```

`GetComponentInChildren` **includes the object itself**, so a `LODGroup` on the prefab root is found
just as a real CAI's child-mounted one is. And `DVVVWEAHKNV` `0x97D97E0` is only the **left/right
mesh pair** matcher — its literals are `'.L'`, `'.R'` and
`'] with HasLeftAndRightMesh not find L.* and R.* renderers list:'` — so it is not a general
LOD-name convention check and does not apply to a single-mesh prop.

## ⚠️ OPEN: converted bundle loads, renders nothing, logs nothing

State as of **2026-10-16** on `20260323.14`. Everything below was **measured and ruled out**, and the
item is still invisible with no exception and no log line:

| checked | result |
|---|---|
| container key | `['prefab']`, pointer resolves to the right root GameObject (transform walk) |
| root `m_IsActive` | `True`, layer 0 — same as both working donors |
| renderers | 3 in-hierarchy `SkinnedMeshRenderer`, all `m_Enabled=True`, `m_CastShadows=1` |
| meshes | real vertex data — 718 / 430 / 44 |
| bones | 1 bone each, `m_RootBone` set and resolving |
| `m_Materials` | `[0]` — **matches** both working donors, so nulled pointers are correct |
| MaterialMap | 1 entry, matching the prefab's 1 material slot; `AvatarMaterialKey..ctor` no longer NREs |
| LODGroup | found by `GetComponentInChildren`; its 3 LODs reference exactly the 3 **reachable** renderers |
| the duplicate `.fbx` hierarchy | its LODGroup and 3 renderers are `reachable=False` from the container root — inert |
| root MonoScript | swapped to the Studio marker: no change |
| thumbnail | replaced with a real 850 KB PNG: no change |

**Static comparison is exhausted.** Every structural difference from a working CAI has either been
matched or shown to be outside the instantiated hierarchy. What remains unmeasurable from the files:
whether the prefab is instantiated at all, whether it is parented/scaled into visibility, and what
material instance the renderers end up with.

**Next instrument: a runtime probe, not more bundle surgery.** `C:\Games\recflare-2023\BepInEx` and
`C:\Games\recnet-patcher` (`Plugin.cs`, `RecNetPlugin.csproj`) already provide a plugin harness. Log,
after the item is applied: the instantiated hierarchy, and per renderer `enabled`, `isVisible`,
`bounds`, `sharedMaterial` and the world-space scale/position. That separates *not instantiated* from
*instantiated but culled* from *null material* from *collapsed at the origin* — four hypotheses one
log line each, against a search space that file diffing can no longer narrow.

Also worth considering: the A/B above shows Studio **rebuilds** a trimmed prefab (17 objects vs 33,
3 renderers vs 6, one LODGroup vs two, a different root component, no `AnimationClip`). Surgery got
from "prefab not found" to "everything resolves", which is most of the way, but it is not evidence
that the remaining gap is closable in place.

### Root-component difference (observed before the A/B; see above for the evidence)

| bundle | root MonoBehaviour |
|---|---|
| real CAI (both donors) | `RecRoom.Core.Studio.AvatarItems.RecRoomStudioAvatarItem` (`RecRoom.Studio.Common.Runtime`), **no fields** |
| converted shipped built-in | `RecRoom.Avatars.Outfit.OutfitPrefab` (`Assembly-CSharp.dll`), `_sourceMeshRenderer` / `AllowFitMeshOverride` / `FitMeshPivot` |

Tempting to call this the blocker, but both `RecRoomStudioAvatarItem` and
`RecRoomStudioAvatarItemBase` have **only a `.ctor`** in the 2026 client — pure marker components
with no behaviour — while `OutfitPrefab` is the one with a surface
(`get_SourceMeshRenderer`, `get_LODGroup`, `get_HatSupportsCustomization`) and
`RecRoom.Avatars.Outfit.OutfitRenderSetup$$AQPBVFLNGOH` `0x15B4680` is what reads it. Our prefab
*has* that component, populated. So the converted prefab is arguably **more** complete here, and the
marker difference is recorded as an observation only.

Hierarchy also differs slightly and is likewise unproven: a real CAI puts the `LODGroup` on the
**child** mesh root, while the shipped prefab has one on the **root as well as** the child. Both have
`HeadPropGroup` / `HandPropGroup` with three `*_LOD0/1/2` `SkinnedMeshRenderer`s, and the container
pointer resolves to the right root GameObject in all three (verified by walking the transform tree),
which also confirms the 3 extra renderers from the `.fbx` variants hang **outside** the instantiated
hierarchy — so they are not the problem.

The remaining structural difference is the **6 renderers / 2 LODGroups** against a real Main's 3 / 1,
from the `.fbx` variants the Addressables bundle packs. Those should never instantiate — the
container names only the prefab root — but that is reasoning, not a measurement.

### The diff that found it

Our `avatarItem.json` against both working exports: **identical key sets**, and after discarding
every field that is an identity (ids, names, filenames, hashes, timestamps) exactly one difference
survived — `CustomAvatarItemSaveId` **`null` in ours, a positive integer in every working one**. The
DTO field is a non-nullable **`long`** (`RecNet.CustomAvatarItemSaveDTO.get_CustomAvatarItemSaveId`),
so `null` deserializes to `0`. Whether `0` is filtered is **not established** — it stayed a suspect
rather than a cause, because the material-slot mismatch is a measured defect and this is not.
