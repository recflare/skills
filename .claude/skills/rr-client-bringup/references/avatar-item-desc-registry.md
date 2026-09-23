# Avatar item desc registry

> 2025 client resolves AvatarItemDesc through a CLIENT-BAKED descToCaidMapping built in Awake from the shipped wardrobe asset; an unknown desc is dropped SILENTLY with no log, and no server payload can add one

Why store/wardrobe avatar items silently fail to render in recflare-2025 (build 20250718.01) with no
network request and no log line. See [two-client-builds-name-check](../../il2cpp-analysis/references/two-client-builds-name-check.md) for build identification.

## The path (all RVAs are the 2025 build)

`OutfitManager.DMCKKOJBGON(List<LOFDJEDAGHN>)` @ **0x148EF80** consumes the
`POST api/avatar/v1/lockeditems/bulk` response (`LOFDJEDAGHN` = that DTO, see
[avatar-lockeditems-bulk-wire-shape](../../wire-shapes/references/endpoints/avatar-lockeditems-bulk-wire-shape.md)). Called only from the async state machine
`MEPHMCKKKBK$$MoveNext` @ 0x14BADF0. Per item it:

1. copies the 48-byte desc struct from `LOFDJEDAGHN+0x40`
2. `AvatarItemWardrobeRuntimeConfig.KNHCEJLILGF(ref desc, out caid)` @ **0x14ADBD0**
   - **false → `je` straight back to the loop head at 0x148F0B0. NO LOG. Item vanishes.**
3. on true: `HICKLGEJGFF.IOMDNBPAFCO` → `ICNBFNNFPIE` → `JPPIHLEDPEB.BDCEBPMLGHE`;
   false here logs `"OutfitManager: Failed to get base avatar item for item {0}. Skipping this item."`

So *two* distinct drop points, and **the common one is silent**. Grepping the log proves nothing.

## AvatarItemDesc is 3 guids, and the whole tuple is the key

`.NPHONPGHNPF` (48 bytes, value type):

| off | field | meaning |
|-----|-------|---------|
| 0x00 | `NJPDBAHKIKN` (`.ENEJMMGDILI` = Guid wrapper) | base asset |
| 0x10 | `MILLADPGFHF` (`.GLNFCDOGKEH` = Guid wrapper) | colour |
| 0x20 | `ELCENCJKGLD` (`System.Guid`) | **CustomAvatarItem guid** |

`KNHCEJLILGF` branches on the *third* guid:

- **guid != Empty** → `ANDDDIIPGEC..ctor` builds a CAID straight from it, `return true`. **Always succeeds.**
- **guid == Empty** (a built-in item, i.e. every `"<base>,<colour>,,"` desc) →
  `descToCaidMapping.TryGetValue(fullDesc, out caid)`. On miss it writes
  `this.emptyCustomAvatarItemId` (field +0xB8) to the out param and **returns false**.

## descToCaidMapping is client-baked and unreachable from the server

`descToCaidMapping` is a plain `Dictionary<NPHONPGHNPF, SerializedCustomAvatarItemId>` at
`AvatarItemWardrobeRuntimeConfig+0x30` — Unity cannot serialize a plain Dictionary, and
`Awake()` @ **0x14AC620** builds it (calls `NPHONPGHNPF..ctor` / `PHGIAKEDBEK` / `IBJBCBHFJAG` plus
7 dictionary adds) from the serialized `builtinAvatarItemDataDictionary` (+0x60).

The **only** runtime insert path is `AOFDCJBIDOF(.ELINGHEBHJB)` @ 0x14AC2E0, and it writes
`downloadableAvatarItemDataDictionary` (+0x18), keyed by CAID guid, from `RecNetCDNAssetReference`s —
i.e. **UGC custom items only**. It never touches +0x30.

**Consequence: a built-in avatar item that isn't in the shipped wardrobe asset can never render, no
matter what the storefront / lockeditems / defaultunlocked payloads say.**

⚠️ **Withdrawn 2026-08 (user correction):** an earlier version of this note suggested presenting the
item as a CustomAvatarItem (non-empty 3rd guid) + serving `ELINGHEBHJB` data and CDN assets. CAI are
**user-created items** — `.NOGPCPONLFN`'s getters (`get_CustomAvatarItemSaveId`,
`get_CustomAvatarItemId`, `get_UnityAsset*`) confirm that whole path is UGC, so it is not a usable
route for shipping built-ins. The `.AOJENEHHIAH` source enum on `ELINGHEBHJB..ctor`
(`None/Precache/DefaultUnlocked/UnknownItem/Storefront/Gifting`) looks server-reachable but only
records *where a CAI was encountered*. The core finding above is unaffected and was re-verified: a
class-wide scan of `0x14ABC90–0x14AFE40` for writes to `+0x30` finds only the `.ctor` allocation
(`0x14AF9DD`) and the `Awake` populate (`0x14AC9A4`).

## Ruled out

- `"{0} does not have an associated browsable avatar item filter."` (`AFOBIGHEEGE.EILONJMFIGF`
  @ 0x14A9BA0, `OutfitType.None` → returns filter `0`) is **benign**. In
  `OutfitManager.UpdateFilteredCustomAvatarItemIdsNonAlloc` @ 0x149BD00 a zero filter makes
  `test sil,3` and `test esi,0x7FFFC` both fall through, so **nothing** is filtered out. It is more
  permissive, not less.
- Body type (`AvatarItemBodyType` / `ModernBeanPrefabAssetReference`): setting playersettings
  `PlayerUsesClassicBeanOverride=True` changed nothing.
- Every field of the item DTO — a rendering and a non-rendering item were identical on `Rarity`,
  `Tooltip`, `TagList`, `IsBaseAvatarItem`, id range and year; only the desc guids differed.

## Settling "is guid X shipped?"

**UPDATED 2026-09-14 — this is now answerable statically.** The original conclusion ("a raw byte scan
of `Recroom_Release_Data` is useless") was right about *why* (the addressable bundles are
LZ4-compressed, so even the known-good control guid isn't found) but is no longer a dead end:
`il2cpp-2025/bundlescan.py` + `lz4b.py` now decompress all 2745 bundles in ~85 s and grep them —
see [unity-bundle-text-scanning](../../il2cpp-analysis/references/unity-bundle-text-scanning.md). Always run its positive control first.

⚠️ **Two traps that produce a clean `hits=0` on a build that does contain the string** (both hit
2026-09-23, both now fixed//documented in that note): the scanner aligned on `flags & 0x200` instead of
`version >= 7`, which silently emptied **every** bundle of the v7 `20230414` build; and the 2023 data
dir is `RecRoom_Data`, not `Recroom_Release_Data`.

⚠️ Caveat: `bundlescan.py` searches **ASCII and UTF-16 text only**. Whether that finds an
`AvatarItemDesc` guid depends on how the wardrobe asset serializes it — Unity cannot serialize
`System.Guid` directly, so the shipped `builtinAvatarItemDataDictionary` plausibly stores the guids
as **strings** (in which case a text scan works). If it stores raw 16-byte values instead, extend the
scanner with a `uuid.bytes_le` / `uuid.bytes` needle.

The runtime route still works and remains the ground truth: hook `KNHCEJLILGF` @ 0x14ADBD0
(call-through, `rdx` = `NPHONPGHNPF*`, `r8` = out CAID) and log the three guids plus the returned
`al`; the dictionary's `Count` off `Config+0x30` gives the registry size.

## The filter enum (for reading the browse code)

`.HEBIFPMJMOM` bits: Store 1, Owned 2, Hat 4, Hair 8, Beard 16, Accessory 32, Torso 64, Glove 128,
Eyes 256, Ears 512, Shoulder 1024, Neck 2048, Waists 4096, CustomShirts 8192, Legs 16384, Feet 32768,
Roomie_Hat/Waist/Eye 0x10000/0x20000/0x40000; `AllOutfitTypeFilters` = 0x7FFFC.
`RecRoom.Avatars.OutfitType`: None -1, Hat 0, Hair 2, Ear 3, Eye 10, Beard 20, Shoulder 100,
Shirt 101, Waist 102, Neck 103, TeamJersey 104, CustomShirt 105, Wrist 200, TeamWrist 203, Legs 300,
Feet 301, Roomie_Hat 500, Roomie_Waist 501, Roomie_Eye 502.

A browsable entry is `.NIFMCGDKDKN`: +0x10 base item (`.HICKLGEJGFF`), +0x40 `AvatarItemMetadata`,
+0x48 store info (`.HCJBFOICEDA`, non-null = purchasable), +0x50 owned bool.

## 2026-09-14 — REAL PAYLOADS: the desc is base64url guids, and the silent drop was the wrong suspect

Field names are confirmed from `NPHONPGHNPF.ToString()` `0x8A82190`, format
`'{0}: {1}, {2}: {3}, {4}: {5}'` with literals **`AvatarItemId`**, **`MaterialCombinationId`**,
**`CustomAvatarItemId`** — so the wire desc is `AvatarItemId,MaterialCombinationId,CustomAvatarItemId,`
(three values, trailing comma, 4 split slots).

**Segments are base64url of the .NET `Guid.ToByteArray()` byte order (`uuid.bytes_le`),** 22 chars,
no padding, `-`/`_` alphabet. Decode with
`uuid.UUID(bytes_le=base64.urlsafe_b64decode(seg+'=='))`.

Two live `giftdropstore` rows from the user, identical in every other field:

| | AvatarItemId | MaterialCombinationId | CustomAvatarItemId | result |
|---|---|---|---|---|
| Winged Hat (Grackle) 12596 | `fe15ca53-c5b8-4acf-9309-ff3f4e610fc9` **hyphenated** | `e9b618a3-…` b64 | `3a16319e-…` b64 | **renders** |
| Steampunk Hat (Silver) 12668 | `JWanxvOHyESg9F_HlmTOfA` = `c6a76625-…` **base64url** | `5d084365-…` b64 | `34391c52-…` b64 | **missing** |

### ⚠️ This pair does NOT hit the silent `descToCaidMapping` drop

**Both descs have a non-empty `CustomAvatarItemId`**, so both take the `guid != Empty` branch of
`KNHCEJLILGF` `0x14ADBD0`, which builds a CAID via `ANDDDIIPGEC..ctor` and **always returns true**.
The dictionary miss documented above requires an **empty** third guid. So the missing item is being
dropped *later*, at `HICKLGEJGFF.IOMDNBPAFCO` → `ICNBFNNFPIE` → `JPPIHLEDPEB.BDCEBPMLGHE` — which
**does** log `"OutfitManager: Failed to get base avatar item for item {0}. Skipping this item."`
(`0xD0BCED8`). **That log line is the check to run.**

### "Is the guid shipped?" is now CLOSED as a line of enquiry

Scanned all **2745** addressable bundles (decompressed, [unity-bundle-text-scanning](../../il2cpp-analysis/references/unity-bundle-text-scanning.md)) **and** all
358 uncompressed files under `Recroom_Release_Data`, for both AvatarItemIds in **five** encodings —
ascii-hyphenated, base64url, UTF-16 of each, raw `bytes_le`, raw `bytes` big-endian.
**Zero hits for either guid — including the one that renders correctly.** That is a valid internal
control: AvatarItemIds are simply not present in the shipped client in any searchable form, so
absence proves nothing and this search route is exhausted. Use the runtime hook if a per-item verdict
is needed.

### Live hypothesis: field-0 encoding

The only structural difference between the two payloads is that the working row's **AvatarItemId is
canonical hyphenated** while the broken row's is base64url (fields 1–2 are base64url in both). If the
segment parser accepts only `Guid.Parse` form for slot 0, a base64url value there yields a wrong or
default AvatarItemId → the base-item lookup fails → "Failed to get base avatar item".

**Decisive 30-second test:** re-serve the failing row with slot 0 hyphenated and nothing else
changed —
`c6a76625-87f3-44c8-a0f4-5fc79664ce7c,ZUMIXcyOpEGiHgslbHQbwA,Uhw5NBQy-EOIiCWiZFiL7g,`

**Not yet located:** the desc-string parser itself. It is not `NPHONPGHNPF.PHGIAKEDBEK` (that is
`op_Equality`), not on the `ENEJMMGDILI`/`GLNFCDOGKEH` wrappers (neither has a Parse), and
`FLMDJANAGJA`'s `Nullable<NPHONPGHNPF>` setter `LNDCLFOHADF` `0x7D90930` has **zero callers and no
metadata-usage slot**, so the parse happens somewhere not yet found.
