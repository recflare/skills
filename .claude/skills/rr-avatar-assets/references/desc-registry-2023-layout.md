# 2023 avatar item desc registry — layout and the base64url form

> In the 20230414 build, avatar item descs live in `RecRoom_Data/resources.assets` in TWO forms: dashed GUIDs AND 22-char base64url GUIDs. A raw scan for the decoded dashed GUID finds nothing for a base64url desc — search the token verbatim. There is also a separate item table that maps an item id to its human name, e.g. `E9VTiIVFPEa-OuQRto0e_Q` = `Shirt_SteamPunk`.

Added **2026-09-25**. Companion to [avatar-item-desc-registry](../../rr-client-bringup/references/avatar-item-desc-registry.md) (which covers the 2025 build's
in-memory `descToCaidMapping`) and [unity-bundle-text-scanning](../../il2cpp-analysis/references/unity-bundle-text-scanning.md).

## Two encodings, same registry

Every entry is a length-prefixed UTF-8 string, 4-byte aligned. Both of these appear interleaved in
the same table:

| form | example | len |
|---|---|---|
| dashed GUID | `f76b709c-b173-426e-81f2-279a67d2fde1` | 0x24 |
| dashed pair | `f750de46-3758-4f7d-9709-0a84b1027009,2c8924aa-68f8-4912-9759-18992f72f08a,` | 0x4A |
| **base64url GUID** | `E9VTiIVFPEa-OuQRto0e_Q` | 0x16 |
| **base64url pair** | `fD5vtKxBWECH54Jj4FbnUg,C8gCmBZ8RUG83vvDw_UYew,` | 0x2E |

⚠️ **Decoding a base64url token to a dashed GUID and searching for that finds nothing.** The
base64url is `Guid.ToByteArray()` (little-endian first three fields) base64url-encoded with the `==`
stripped; the dashed spelling of the *same* GUID is simply not in the file. Search the token
verbatim. A raw scan of the whole 7.4 GB install plus all 6499 addressable bundles for the decoded
GUIDs returns 0 — a clean-looking false negative.

Sanity control that the scan is working at all: `f76b709c-b173-426e-81f2-279a67d2fde1` must hit
`resources.assets` at ~`0x0DBC7790`.

## Two hash tables, not one

The same desc appears in two separate string→string tables, each mapping it to a different 32-hex
Unity asset GUID:

| desc | table A (~`0x0DBC….`) | table B (~`0x0DC1…`/`0x0DC3…`) |
|---|---|---|
| `f76b709c-…-2fde1` (`Shirt_Golfer`) | `890287b0c3a1aee4e80e87f6ca9e96a6` | `5fed34e041584fd4b92ae46464113308` |
| `E9VTiIVFPEa-OuQRto0e_Q` (`Shirt_SteamPunk`) | `98e9d4b331b049c4a8854992a366cb2c` | `1140dd63dbf4ba9408ef7aefad1cfb28` |
| `fD5vtKxBWECH54Jj4FbnUg,C8gCmBZ8RUG83vvDw_UYew,` | `2c70bbd1f09082d4fad94a43d15a4e3c` | `18f7b6b0a8313a34aa5f437d1ae98ce2` |

Pairing is **desc → the string that follows it** (the direction that produced the confirmed
`f76b709c` → `890287b0`). The values are **Unity asset GUIDs, not bundle hashes** — none of them
exist as `StreamingAssets/aa/StandaloneWindows64/*.bundle` filenames.

**What the two tables actually are** — resolved through the Addressables catalog (below), the split
is by asset kind, not by table precedence:

| table | kind | `Shirt_SteamPunk` | the `fD5vtKxB…` combination desc |
|---|---|---|---|
| A | **material** | `Avatar/Materials/SteamPunk_Shirt_mat.mat` | `Avatar/Combinations/Steampunk_Shirt_Contest_Mat.mat` |
| B | **prefab / combination asset** | `Avatar/Props/Shirts/(SteamPunk_Shirt).prefab` | `Avatar/Combinations/Steampunk_Shirt_Contest_Combination.asset` |

## GUID → asset path → .bundle on disk

`StreamingAssets/aa/catalog.json` is Addressables `ContentCatalogData`: `m_KeyDataString`,
`m_BucketDataString` and `m_EntryDataString` are **base64 blobs, not JSON**, so grepping the file
gets you nothing. `tools/il2cpp/aacatalog.py` parses them; the 32-hex asset GUIDs from the desc
registry are catalog **keys** verbatim, so a desc lookup turns straight into a file on disk.

```
py aacatalog.py "<...>/StreamingAssets/aa" 1140dd63dbf4ba9408ef7aefad1cfb28
1140dd63dbf4ba9408ef7aefad1cfb28
   asset : Assets/Core/Content/Avatar/Props/Shirts/(SteamPunk_Shirt).prefab
   OWNER : 6959b3a9a30c23f95b3e8c80b488eea2.bundle       248.3 KB
   dep   : e22cddbfa295e85c69acfb02a7e52522.bundle         2.8 KB
   dep   : 682ba40059cd6c037bace975e7aea07f.bundle     41840.2 KB
   ...
```

**The first bundle in an entry's dependency list owns the asset; the rest are shared deps.** That is
an observation, not something the catalog labels — confirm it with `tools/il2cpp/bundlepeek.py`,
which decompresses named bundles and reports which one actually contains the asset's name string.
For the SteamPunk shirt each "OWNER" guess was confirmed exactly:

| asset | owning bundle | payload |
|---|---|---|
| `(SteamPunk_Shirt).prefab` | `6959b3a9a30c23f95b3e8c80b488eea2.bundle` | 645,892 B |
| `SteamPunk_Shirt_mat.mat` | `bdfdd143d65e3f759ed0c08c3fd3e114.bundle` | 1,407,920 B |
| `Steampunk_Shirt_Contest_Combination.asset` | `72ac2c11e9c197e4edcf04dc51cb937d.bundle` | 5,300 B |
| `Steampunk_Shirt_Contest_Mat.mat` | `5e689c90fb414d93e2cc9b02e50b8a68.bundle` | 4,204,744 B |

`682ba40059cd6c037bace975e7aea07f.bundle` (41.8 MB) and `e22cddbfa295e85c69acfb02a7e52522.bundle`
(2.8 KB) are dependencies of **every** avatar asset here — the shared shader/monoscript bundles.
Nothing needs extracting: the bundles ship as discrete files, so "extract the assetbundle" is a copy.

## The item table: id → human name

A third region (~`0x0DCD…`) holds the wardrobe/store records. Each record is a run of
length-prefixed strings shaped `[itemId] [desc] [name] [itemId]`, with a ~0x74-byte binary block
between records:

```
@0dcd66d8  E9VTiIVFPEa-OuQRto0e_Q
@0dcd66f4  fD5vtKxBWECH54Jj4FbnUg,C8gCmBZ8RUG83vvDw_UYew,
@0dcd6728  (Shirt_SteamPunk)
@0dcd6740  E9VTiIVFPEa-OuQRto0e_Q
@0dcd67b4  E9VTiIVFPEa-OuQRto0e_Q
@0dcd67d0  gy-xeYKKREaBlx9fUmuW2w,C8gCmBZ8RUG83vvDw_UYew,
@0dcd6804  (Neck_SteamPunk)
@0dcd6818  sOREgAGs-06CeGGsG-WIkw
```

**This is the fastest way to put a human name on an opaque desc token.** The name is parenthesised
in the data (`(Shirt_SteamPunk)`), which also makes it greppable.

⚠️ The record boundary is genuinely ambiguous from bytes alone — a desc sits between two copies of
an item id and a name, so it can be read as belonging to either neighbour. Use the **semantics** to
break the tie: in the block above `fD5vtKxB…` and `gy-xeYKK…` share their second GUID
(`C8gCmBZ8RUG83vvDw_UYew` = the SteamPunk colour/material) and differ in the first (the per-garment
mesh), which matches Shirt vs Neck.

## Item id and desc are ADJACENT FIELDS, not one string

A three-token string like

```
E9VTiIVFPEa-OuQRto0e_Q,fD5vtKxBWECH54Jj4FbnUg,C8gCmBZ8RUG83vvDw_UYew,
```

does **not** exist anywhere in the build. It is `[itemId]` concatenated with the two-token
`[desc]` that follows it in the record. Each piece resolves on its own; the concatenation resolves to
nothing, and searching for it is the kind of clean `hits=0` that looks like "the item isn't in this
build" when it actually is. Split on the first comma and re-check before concluding anything.
