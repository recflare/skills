# Porting a 2023 avatar asset to 2025 — and why grepping the 2025 install lies

> The **2025 build encrypts every Unity serialized file** (`resources.assets`, `sharedassets*`,
> `globalgamemanagers*`, `level*`, **and `StreamingAssets/aa/catalog.json`**) behind an
> `00 00 52 52 00 00 52 52` header. Its **`.bundle` files are NOT encrypted**. So `descresolve.py`
> and `aacatalog.py` are **2023-only**, and a grep of the 2025 data dir for an asset name or a desc
> GUID returns a **clean `0 hits` that proves nothing**. The only honest "is it in 2025?" test is
> `bundlescan.py` over `StreamingAssets/aa/StandaloneWindows64`.

Established **2026-10-16** while locating `Curly Mustache` for a 2023 → 2025 port.

## The encryption header

```
2025  resources.assets            00 00 52 52 00 00 52 52  c3 4e 71 a4 …
2025  sharedassets0.assets        00 00 52 52 00 00 52 52  3d f5 78 67 …
2025  globalgamemanagers          00 00 52 52 00 00 52 52  e3 1e cb 43 …
2025  globalgamemanagers.assets   00 00 52 52 00 00 52 52  51 f0 33 d2 …
2025  level0                      00 00 52 52 00 00 52 52  …
2025  StreamingAssets/aa/catalog.json
                                  00 00 52 52 00 00 52 52  71 3f a0 91 …
2025  aa/StandaloneWindows64/*.bundle   "UnityFS" … 2021.3.41f1   (format ver 8, PLAIN)
2023  RecRoom_Data/globalgamemanagers   plain SerializedFile      2020.3.33f1
2023  aa/StandaloneWindows64/*.bundle   "UnityFS" … 2020.3.33f1   (format ver 7, PLAIN)
```

`RR` is `0x52 0x52`, so the magic is literally the two-byte tag twice with zero padding. The 2023
build has none of this — which is why the whole desc-registry technique in
[desc-registry-2023-layout](desc-registry-2023-layout.md) exists only for 2023.

### What this breaks

| tool | 2023 | 2025 |
|---|---|---|
| `descresolve.py` (reads `resources.assets`) | ✅ | ❌ encrypted |
| `aacatalog.py` (reads `catalog.json`) | ✅ | ❌ `UnicodeDecodeError: 'utf-8' codec can't decode byte 0xa0 in position 10` |
| `bundlescan.py` / `bundlepeek.py` (read `.bundle`) | ✅ | ✅ |

⚠️ **The `aacatalog.py` failure is loud, but the `descresolve.py` / raw-grep failure is silent.**
Searching the 2025 `resources.assets`, `globalgamemanagers.assets`, `sharedassets*.assets`,
`GameAssembly.dll` and `out/stringliteral.json` for `CurlyMustache`, for the desc GUID and for its
base64url spelling returned **0 hits in every file** — and that result is worthless on its own,
because the first four are ciphertext. This is the same false-negative class as the base64url desc
trap, one layer down.

**The scan that does work, with its own control:**

```
py bundlescan.py "<2025>/StreamingAssets/aa/StandaloneWindows64" "curlymustache"
scanned=2745 failed=0 hits=0 secs=60.0
```

and the control proving the scanner reaches prefab names in that same build:

```
py bundlescan.py "<2025>/…/StandaloneWindows64" "curlymustache,mustache,props/mouth"
… Assets/Core/Content/Avatar/Props/Mouth/(BB_SeventiesStache_Mouth).prefab
… Assets/Core/Content/Avatar/Props/Mouth/(BB_VanDyke_Mouth).prefab
… Assets/Core/Content/Avatar/Props/Mouth/(BB_BeardClose_Mouth).prefab
scanned=2745 failed=0 hits=40 secs=63.8
```

666 MB / 2,745 bundles takes about a minute. **Always run the positive control** — a bare `hits=0`
from a scanner you have not exercised on that build is not evidence.

## Worked lookup: `Curly Mustache`

Input was a CSV row, `Curly Mustache,5f00002b-8092-438c-8763-cc8ebd7eaf4d,,,6b337a35-95d9-4b3a-9891-d9fbb06262aa`.

```
py descresolve.py "C:\Games\recflare-2023\RecRoom_Data" "6b337a35-95d9-4b3a-9891-d9fbb06262aa"
    item-table name(s): (Mouth_CurlyMustache), (DarkMagic_Belt)
    472f3daac340d09409de879bbc79664c -> Assets/Core/Content/Avatar/Materials/Hair/Mat_Hair.mat
    f8501df3eefb28c4682c09c1a0c68f71 -> Assets/Core/Content/Avatar/Props/Mouth/(CurlyMustache_Mouth).prefab
SYSTEM NAME: (CurlyMustache_Mouth)
```

| | guid | asset | owning bundle | file | payload |
|---|---|---|---|---|---|
| prefab | `f8501df3eefb28c4682c09c1a0c68f71` | `Avatar/Props/Mouth/(CurlyMustache_Mouth).prefab` | `c3b177b82b28a576c67b1d335b03f7f2.bundle` | 125.8 KB | 324,176 B |
| material | `472f3daac340d09409de879bbc79664c` | `Avatar/Materials/Hair/Mat_Hair.mat` | `f84cefa30edb0a29a2d914f756faea03.bundle` | 1,264.9 KB | 4,227,348 B |
| shared dep | — | shaders / monoscripts | `682ba40059cd6c037bace975e7aea07f.bundle` | 41,840.2 KB | — |
| shared dep | — | — | `e22cddbfa295e85c69acfb02a7e52522.bundle` | 2.8 KB | — |

Both OWNER guesses confirmed with `bundlepeek.py` (`hits: ['CurlyMustache']` /
`hits: ['Mat_Hair']`). Note the material is the **generic** `Mat_Hair.mat`, shared by every hair
item — this prop has no material of its own, which matters when packaging a `Main`+`Material` pair.

### The first GUID is an item id, not an asset

`5f00002b-8092-438c-8763-cc8ebd7eaf4d` (base64url `KwAAX5KAjEOHY8yOvX6vTQ`) has **0 hits in the 2023
build in either spelling**. It is the **`CustomAvatarItemId`** column of that CSV, not a desc token —
the [adjacent-fields trap](desc-registry-2023-layout.md) arriving as separate CSV fields instead of a
concatenation.

**Resolve the last GUID, then pass the first one back in.** Knowing it is "not an asset guid" is only
half the job: it is the catalogue's own item id, so it must become `CustomAvatarItemId` /
`RankedEntityId` in the export rather than letting `fromdesc` synthesise one
([cai-export-format](cai-export-format.md) → *the derived id is a FALLBACK*).

### The record-boundary trap recurred, and here is the proof

`descresolve.py` offered three names for the neighbouring desc `2822aa50-4344-434d-b46f-fd9443f865b9`
— `(CurlyBob_Hair)`, `(ShortCurlyHeadband_Hair)`, `(Mouth_CurlyMustache)` — and its catalog walk
settles it as `(CurlyBob_Hair)` + `Curly_Hair_Mat.mat`. The raw record at `0x0DC7F784` shows why the
name is ambiguous from bytes alone:

```
@0dc7f758  WAXU5lUGoUulTkJtyJpzHw                  (= e6d40558-0655-4ba1-a54e-426dc89a731f)
@0dc7f778  2822aa50-4344-434d-b46f-fd9443f865b9    (CurlyBob's desc)
@0dc7f784  (Mouth_CurlyMustache)
@0dc7f7a0  6b337a35-95d9-4b3a-9891-d9fbb06262aa    (the mustache's desc)
```

A name string sits **between two different items' tokens**. The unambiguous record for this item is
the other hit, `0x0DBF1BE8`, where the desc appears on **both** sides of the name:

```
@0dbf1bb4  6b337a35-95d9-4b3a-9891-d9fbb06262aa
@0dbf1be8  (Mouth_CurlyMustache)
@0dbf1bf8  6b337a35-95d9-4b3a-9891-d9fbb06262aa
```

**Prefer a desc-flanked record over a name sandwiched between two tokens**, and always confirm
through the Addressables catalog rather than the item table alone.

## Is it in 2025? No — and the port is a rebuild, not a copy

The mustache is **absent from the 2025 build** (`hits=0` with a passing control, above). 2025 *does*
ship `Avatar/Props/Mouth/*` prefabs, just a different set (`BB_SeventiesStache_Mouth`,
`BB_VanDyke_Mouth`, `BB_BeardClose_Mouth`, …), so this is a genuinely missing item rather than a
renamed one.

Three things decide how it can get there:

1. **Unity version is in the allowed direction.** 2023 bundles are `2020.3.33f1` (format 7), the 2025
   player is `2021.3.41f1` (format 8). Unity rejects a bundle built by a *newer* editor, not an
   older one, so `2020.3 → 2021.3` is the permitted direction. Not a blocker.
2. **The catalog cannot be edited.** `catalog.json` is encrypted, so the shipped bundle cannot be
   registered as an Addressable in the 2025 build. A built-in avatar item therefore cannot be
   side-loaded by dropping files in `aa/StandaloneWindows64`.
3. **Shipped ≠ CustomAvatarItem.** A shipped bundle depends on the 41.8 MB shared shader/monoscript
   bundle; a CAI bundle must be a self-contained `Main`+`Material` pair whose internal name derives
   from `UnityAssetId` ([cai-export-format](cai-export-format.md)). `caiexport.py fromdesc` builds a
   correct *wrapper* around the shipped bundle, but the bundle inside still cannot resolve its
   dependencies in a 2025 client.

So the realistic route is: extract the prefab's **mesh + textures** out of
`c3b177b82b28a576c67b1d335b03f7f2.bundle`, re-author them in Rec Room Studio, and build a CAI from
that. That is the "converting one to the other is a Unity **rebuild**, not a file copy" warning in
[SKILL.md](../SKILL.md) applied to a concrete item — and the 2025 catalog encryption is a second,
independent reason the file-copy path cannot work.

## Worked export: the Curly Mustache as a CAI folder

⚠️ **Re-done 2026-10-16 against the refreshed install** (Unity `2021.3.29f1`, 9,177 bundles), which
**added a full-body variant** the original `20230414` build did not have, and renamed the base
prefab. The desc is unchanged and still maps to the same asset guid.

| variant | desc | prefab guid | path | owning bundle |
|---|---|---|---|---|
| base / BB | `6b337a35-95d9-4b3a-9891-d9fbb06262aa` | `f8501df3eefb28c4682c09c1a0c68f71` | `Props/Mouth/(BB_CurlyMustache_Mouth).prefab` | `1ae3f8451f72c546fe47cc4df8cc357c.bundle` 124.8 KB |
| **full body** | `c5bc9196-1096-4888-aaec-c48f7118b940` | `97ad61abada82324bb1021aaea7bcaa3` | `Props/FB_Mouth/(FB_CurlyMustache_Mouth).prefab` | `611122adf56af5cfe33452a0368fb794.bundle` 52.9 KB |
| material (both) | — | `472f3daac340d09409de879bbc79664c` | `Materials/Hair/Mat_Hair.mat` | `befe519aa765f9884bc170153b44b2b7.bundle` 1265.3 KB |

Shared deps grew from 2–3 bundles to **16**. A full-build scan independently confirms the two
owners and nothing else, and shows both variants ship their source `.fbx` plus `_LOD1`/`_LOD2`:

```
py bundlescan.py <refreshed 2023 bundles> "curlymustache"
scanned=9177 failed=0 hits=42 secs=288.2
  1ae3f8451f72c546fe47cc4df8cc357c.bundle   (BB_CurlyMustache_Mouth).prefab + BB_CurlyMustache_Mouth.fbx
  611122adf56af5cfe33452a0368fb794.bundle   (FB_CurlyMustache_Mouth).prefab + FB_CurlyMustache_Mouth.fbx
```

```
py caiexport.py fromdesc "C:\Gamesecflare-2023\RecRoom_Data"       "6b337a35-95d9-4b3a-9891-d9fbb06262aa" "C:\Games\cai-export" 20       "5f00002b-8092-438c-8763-cc8ebd7eaf4d" "c5bc9196-1096-4888-aaec-c48f7118b940"
wrote C:\Games\cai-export\(Mouth_CurlyMustache)  (3209 bytes json, 3 saves)
item id   5f00002b-8092-438c-8763-cc8ebd7eaf4d   (supplied)
py caiexport.py verify ...   -> VERIFY PASS (13 files)
```

BodyType 1 carries the 54,145 B FB bundle; 0 and 2 carry the 127,779 B BB bundle. `n`/`a`/`p` follow
the `(ChickOutfit_Wrist)` convention ([cai-export-format](cai-export-format.md)).

### OutfitType for a facial-hair prop is **20 (Beard)** — measured, not guessed

`RecRoom.Avatars.OutfitType : int` has **no `Mouth` member**:

```
None -1  Hat 0  Hair 2  Ear 3  Eye 10  Beard 20
Shoulder 100  Shirt 101  Waist 102  Neck 103  TeamJersey 104  CustomShirt 105
Wrist 200  TeamWrist 203  Legs 300  Feet 301  Roomie_Hat 500  Roomie_Waist 501  Roomie_Eye 502
```

Everything under `Avatar/Props/Mouth/` is facial hair, and the one `_Mouth` item in the 2,832-folder
`S:\RecRoom\1` library confirms the mapping:

```
Chupacabra Mutton Chops   {"v":1,"d":{"n":"(BB_MLM_Chupacabra_Mouth)","o":20,"d":{"c":0,"p":1}},"ls":1}
```

Library-wide `OutfitType` histogram, handy for sanity-checking any new export:

```
101 Shirt 909 · 0 Hat 686 · 100 Shoulder 297 · 200 Wrist 260 · 103 Neck 147 · 10 Eye 128
102 Waist 107 · 300 Legs 102 · 301 Feet 100 · 3 Ear 51 · 511 ? 11 · 2 Hair 9
500/501 Roomie 6+6 · 507 ? 4 · 502 Roomie_Eye 3 · 20 Beard 1 · 504/506/510 1 each
```

⚠️ `504`, `506`, `507`, `510`, `511` have **no member in the 2025 enum** — the library is from a
newer client, consistent with its `6000.0.27f1` bundles.

### What `fromdesc` fills, and what a server still has to

| field | generated | needs filling |
|---|---|---|
| `CustomAvatarItemId` / `RankedEntityId` | **the CSV's own id**, passed as `fromdesc`'s 5th arg | — |
| `UnityAssetId` | desc-seeded, stable across re-runs | override if the catalogue has real upload ids |
| `UnityAsset*` / `*Hash` / `ThumbnailFileName` | 25-char base36 names + real SHA-256s | — |
| `AdditionalConfiguration` | `{"v":1,"d":{"n":"(CurlyMustache_Mouth)","o":20,"b":<bodyType>,"a":"<desc>"},"ls":1}` | — |
| `CustomAvatarItemSaveId` | **`null`** | the DB must assign an int (real exports: 13248, 13249, …) |
| `Name` | `(CurlyMustache_Mouth)` | a display name, e.g. `Curly Mustache` |
| `Price`, `Description`, `Tags` | `0`, `null`, `[{"TagType":0,"Value":"export"}]` | per catalogue policy |
| the three `*.png` | **1×1 placeholder, 69 bytes** | real thumbnails |

### Why the bundles inside still will not load

`fromdesc` copies the shipped 2023 Addressables bundles verbatim into the `UnityAsset` /
`UnityAsset2` slots — sizes match exactly (128,865 B and 1,295,307 B). Two reasons that is a
structurally valid export with a non-functional payload:

1. **The internal AssetBundle name is wrong.** The copied bundle's blocksInfo directory names a
   single CAB: `CAB-780a296fa4a19bde991922f97e9915e5`. A CAI bundle must be named
   `<UnityAssetId without dashes>.AvatarItem.Main.0.5.assetbundle` (and `.Material.0.6` for
   `UnityAsset2`) — see [cai-export-format](cai-export-format.md). Renaming the file does not change
   this.
2. **The dependencies are external.** The prefab bundle still expects the 41.8 MB shared
   shader/monoscript bundle and the 2.8 KB one, which a CAI load path never provides.

Also note **all three body types share the same bundle bytes** here (identical `UnityAssetHash`
across saves 0/1/2), whereas a real export gives BodyType 1 its own full-body mesh — the Chupacabra
item uses `(FB_MLM_Chupacabra_Mouth)` with `"m":131072` for BodyType 1 and `(BB_…)` for 0 and 2. The
2023 prefab carries **no `BB_`/`FB_` prefix at all**, and that is not just this item:

```
py bundlescan.py "<2023>/StreamingAssets/aa/StandaloneWindows64" "props/mouth/(fb_,props/mouth/(bb_"
scanned=6499 failed=0 hits=0 secs=200.5
```

**Zero `(FB_*_Mouth)` and zero `(BB_*_Mouth)` prefabs in the entire 2023 build**, while the 2025
build ships `(BB_SeventiesStache_Mouth)`, `(BB_VanDyke_Mouth)`, `(BB_BeardClose_Mouth)`. The
body-variant prefix convention arrived **between** the two builds, so a 2023 mouth asset has no
full-body mesh to point `BodyType 1` at — it has to be authored.

> **Control for that negative** (cheaper than re-running a 200 s scan): `bundlepeek.py` the one
> bundle already known to contain the string.
> ```
> py bundlepeek.py <2023 bundles> c3b177b82b28a576c67b1d335b03f7f2.bundle "Props/Mouth/(,CurlyMustache_Mouth"
>   324176 B payload  hits: ['Props/Mouth/(', 'CurlyMustache_Mouth']
> ```
> `bundlescan.py` lowercases both the payload (`low=bytes(out).lower()`) and the needles, so a real
> `Props/Mouth/(FB_…` would have matched `props/mouth/(fb_`. The scanner reaches these strings in
> this build; the absence is real.

**So the export is the right scaffold to hand a server, and the wrong thing to hand a client.** Use
it for the DTO, the ids and the folder shape; replace the two bundles with Studio-built ones.

**How to apply:** before promising any cross-build asset port, (1) resolve the desc on **2023** where
the registry is readable, (2) prove presence/absence on the target build with `bundlescan.py` **plus
a positive control**, and (3) check the catalog's readability before assuming a bundle can be
registered. Steps 2 and 3 are the ones that turn "just copy the bundle" into a rebuild.
