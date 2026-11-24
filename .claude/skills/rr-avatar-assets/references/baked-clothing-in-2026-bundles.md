# Baked-in clothing in the 2026 build

> **Yes — build `20260323.14` ships a large avatar-clothing library inside its Addressables
> bundles.** 1,026 of the 2,787 shipped `.bundle` files contain wearable clothing assets (meshes,
> materials, textures) — 3,217 clothing-asset hits, ~194 distinct base garments, and **312
> `_Combination` items that carry their desc guids** (registered avatar items, not just art). This is
> NOT CDN-only; the garments are on disk.

Derived **2026-11-10** on `C:\Games\recflare-2026`, build `20260323.14`.

## Where the bundles actually are (trap)

The install has several `*_Data` dirs; only one is real:

| data dir | bundles | note |
|---|---|---|
| `Recroom_Release_Data` | **0** | stub — `StreamingAssets/aa/StandaloneWindows64` is empty |
| `RecRoomData` | 0 | no `aa` payload |
| **`RecRoom_Data`** | **2,787** (6.0 GB) | the live data dir — `StreamingAssets/aa/StandaloneWindows64/*.bundle` |

Scanning the empty `Recroom_Release_Data` (the name the 2025 skill table expects) gives a silent
false "no clothing". Use `RecRoom_Data`.

## Method — scan the bundles, not the catalog

- The catalog is **`catalog.bin`** (Unity binary catalog), header `42 89 E3 0D …` — **not** the
  `00 00 52 52` encryption magic, so it reads, but it stores **addressable keys** (`(Name).prefab`,
  32-hex guids, `<hash>.bundle`), **not** `Assets/…` source paths. Grepping it for `Assets/…` or for
  item names returns almost nothing (only avatar-customization **UI** prefabs like
  `(AvatarCustomization_Category_Clothing)`), which looks like "no clothing" — a false negative.
- The `.bundle` files are **not encrypted**. Scan their LZ4 blocks directly:
  `py -I bundlescan.py <…>/StandaloneWindows64 "<needles>"` (~314 s for all 2,787 on this machine,
  0 failures). Asset names live in the decompressed blocks as `Name_Slot_Variant_{Mat,Tex,Norm,Spec,
  decal,Combination}`.
- **Positive control:** the first 60 bundles alone yield `UntuckedTee_Shirt_KREQ_*`,
  `Mobster_Shirt_HerringBoneTan_Combination` (desc `531b4297-…,33ee376a-…`),
  `PocketTee_Shirt_Reclympics_Combination` (desc `Ris_kNVcgU-EK4SoMckC2Q,74J7skzs9EaIq09bZArjiQ`),
  `Hoodie_Shirt_NonBinary_Combination`, `MaleTShirt_Shirt_2D_Contest_decal` — meshes + materials +
  textures + the desc guids, i.e. real renderable items, not thumbnails.

## What's in there (asset-hit counts by slot)

`_Shirt` 1114 · `_Hair` 673 · `_Hat` 493 · `_Wrist` 305 · `_Shoe` 123 · `_Belt` 94 · `_Glasses` 84 ·
`_Mouth` 65 · `_Watch` 48 · `_Hoodie` 47 · `_Backpack` 42 · `_Wings` 27 · `_Boots` 21 · `_Eyebrows`
15 · `_Pants` 8 · `_Dress` 8 · `_Shorts` 3 · `_Mask` 2 · `_Tail`/`_Shoes` 1. (Counts are asset
occurrences — mesh/material/texture per item — not item totals.)

**312 `_Combination` items** (the registered wearables that carry desc guids): Shirt 220, Hat 67,
Wrist 15, Belt 10. These are the ones resolvable to an `AvatarItemDesc`, e.g. the whole
`Baseball_Hat_*` family (Checkerboard, Holographic, NBA75, Destiny{Hunter,Titan,Warlock},
MLM{Chupacabra,Mothman,Sasquatch}, …), `BasicBelt_Belt_*`, `Blazer_Shirt_CandyCane`, etc.

## Follow-ups from here

- Name → desc → bundle for any one item: scan for the name, read the `_Combination` desc guids it
  prints, then `descresolve`/`aacatalog` logic — but note [cross-build-port-and-2025-encrypted-serializedfiles](cross-build-port-and-2025-encrypted-serializedfiles.md):
  on 2025+/2026 the registry serialized files are encrypted, so pair bundle names with the
  in-bundle desc guids rather than the resources.assets registry.
- Package any of these as a CAI export with `caiexport.py` — the bundle already holds the garment;
  the mesh/material are both on disk (see [cai-export-format](cai-export-format.md)).
- Raw outputs saved this session (scratchpad, not committed): `clothing-scan-2026.txt` (full 3,217
  hits), `baked-clothing-combinations-2026.txt` (312 items), `base_items.txt` (194 base garments).
