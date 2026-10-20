# `POST api/storefronts/v1/purchasableitems` wire shape (2026 build)

> `POST econ.<host>/api/storefronts/v1/purchasableitems` (svc **28 Econ**) takes a **JSON body**
> `{PurchasableItemIds, GiftDropIds}` and returns a **BARE ARRAY** of the 11-key
> `RecNet.PurchasableGiftDrop`, whose first key `GiftDrop` is a nested 24-key
> `RecNet.StorefrontGiftDrop`.
> ⚠️ **The array must have exactly one entry per requested id, in the same order.** It is zipped
> **positionally**, and every index past the end of the array is faulted with
> `RecNetWebException("RecNet Bulk Request did not return the expected number of results!")`.
> ⚠️ This route is what backs the **Consumables tab of the store**; a 404 here surfaces as
> `Error refreshing store items from source Store: An error occurred`.

Derived **2026-10-13** from build `20260323.14`, from a live `HTTP Error 404` whose formatted async
trace named `RecNet.Storefronts.VLJOMTQFWRE` as the originating frame — see
[2026-send-helper-tiers](../conventions/2026-send-helper-tiers.md) for that workflow.

Route literal `'api/storefronts/v1/purchasableitems'` **`0xFC703C0`** (re-confirmed 2026-10-19 —
`mxref` gives exactly **4** refs, two per state machine: `0x9563282` / `0x9563416` in
`d__34$$MoveNext` `0x95631A0` and `0x9562E02` / `0x9562F96` in `d__33$$MoveNext` `0x9562D20`, which
is the gift-drop-id sibling below). **POST** (`[HttpMethod statics + 0x20]` read at `0x95633ed`),
service **28 Econ** (`mov r8d, 0x1c` at `0x956341B`).

⚠️ On this build the static-fields pointer is `[klass+0x20]`, not 2025's `[klass+0x90]`; the `+0x20`
above is the offset *inside* static fields (= `Post`). See
[custom-badges-2026](custom-badges-2026-wire-shapes.md) for the measured sequence.

## Call chain — read it bottom-up from the log

| frame in the trace | method | RVA |
|---|---|---|
| UI | `RecRoom.RoomEconomy.Store.ANIDAXYBRZA.ITTHUHMXWEE(IReadOnlyList<T>, bool)` | `0xA1B07B0` |
| facade | `RecNet.Storefronts.JYBFFQRTOPH(IEnumerable<PurchasableItemId>, bool, ct)` | `0x955AC50` |
| cache shim | `RecNet.Storefronts.GKUNCWVKWGH<T>(…)` | generic-shared |
| batcher | `RecNet.MNLGCORXIOE<TId,TValue>.Get` / `.VPGDDENWCQP` | generic-shared, see below |
| **fetch** | **`RecNet.Storefronts.VLJOMTQFWRE(IReadOnlyList<PurchasableItemId>, ct) -> Task<List<PurchasableGiftDrop>>`** | `0x955EB40` |
| send | state machine **`<GetPurchasableGiftDropsByPurchasableItemIdsAsTaskInternal>d__34$$MoveNext`** | `0x95631A0` |

Response send is `RGBOOBRDHEB.ZWUODKCINOA<T>` with generic inst **#2968 =
`List<RecNet.PurchasableGiftDrop>`** → **bare array, no envelope**. Request body is
`RGBOOBRDHEB.FZNGWUAGAIN<T>` with inst **#23248 = `.GetPurchasableItemsRequest`** → a **JSON body**,
not form-urlencoded.

**The sibling by gift-drop id** is `YEWHBMZBWGI(IReadOnlyList<GiftDropId>, ct)`, state machine
`<GetPurchasableGiftDropsByGiftDropIdsAsTaskInternal>d__33` `0x9562D20`. It posts the **same**
request DTO to the same route with `GiftDropIds` filled instead, and gets the same response. One
handler serves both.

## Request — JSON, 2 keys

`.GetPurchasableItemsRequest` (`py ftypes.py`):

| key | CLR |
|---|---|
| `PurchasableItemIds` | `List<int>` |
| `GiftDropIds` | `List<int>` |

```json
{ "PurchasableItemIds": [8311, 8312, 8313], "GiftDropIds": [] }
```

Exactly one of the two lists is populated per call (`PurchasableItemIds` from this path,
`GiftDropIds` from `YEWHBMZBWGI`). The ids are unwrapped from the `PurchasableItemId` /
`GiftDropId` strong-id structs by an `Enumerable.Select` projection before serialization, so they go
on the wire as plain ints.

## ⚠️ The positional-zip rule — the thing that will bite

The batcher body is **generic-shared**, so it has no own `methods.pkl` entry; `mxref` on the literal
`'RecNet Bulk Request did not return the expected number of results!'` (`0xFDC9CB0`) resolves it to
**`UnityEngine.Localization.Tables.AssetTableEntry$$set_PreloadAsyncOperation` `0x6A9AD10`, which is
a MISATTRIBUTION** — `py fstart.py 0x6bd7283` gives the real bounds **`0x6BD7220..0x6BD7F40`**. That
body is `MNLGCORXIOE<TId,TValue>.VPGDDENWCQP`, and the loop is:

```
for (i = 0; i < requestedIds.Count; i++) {          ; cmp r15d, [rbp+0x28] / jge   0x6BD7913
    if (i < results.Count)                          ; cmp r15d, eax / jl 0x6BD7A54
        complete(requestedIds[i], results[i]);      ; positional pairing
    else
        fault(requestedIds[i], new RecNetWebException(
            "RecNet Bulk Request did not return the expected number of results!"));
}                                                   ; ctor at 0x6BD79EC
```

So:

- **One entry per requested id, same order.** The pairing is by **index**, never by matching
  `PurchasableItemId` — the client caches each result under the id it *asked for*
  (`<>c.UBLDBWRCTLE` `0x9567850`, logging `'HandleResult for ID {0}'` then
  `'Cached PurchasableGiftDrop for ID {0}'`). An entry whose own `PurchasableItemId` disagrees with
  the requested id is still accepted and cached under the requested one.
- **A short array faults only the missing ids**, each with its own `RecNetWebException`. Those
  exceptions aggregate through `Task.WhenAllPromise` in `MNLGCORXIOE.Get` and take the whole store
  refresh down, so a short array is as fatal as a 404 here.
- **Extra entries past `requestedIds.Count` are ignored** — the loop is bounded by the request.
- **For an unknown id, return a placeholder entry, not a gap.** There is no "not found" vocabulary.
- A `null` *element* is tolerated by the caching closure (`test rdi,rdi / je 0x9567996` skips the
  cache write) but hands the caller a null `PurchasableGiftDrop`; the store UI then dereferences it.
  Serve real objects.

**Not checked:** whether the faulted per-id task is retained in the batcher's dictionary (no
`Remove`/`Clear` was resolvable in the shared body). Relaunch between server-side attempts rather
than assuming a reopened tab retries cleanly.

## Response — bare array of `PurchasableGiftDrop`, 11 keys

`RecNet.PurchasableGiftDrop` derives from **`RecNet.PurchasableItem`**, and Utf8Json emits
**derived-class members before base members** — so `GiftDrop` comes first and the 10 base keys
follow. Formatter `Utf8Json.Formatters.RecNet.IFJNXZNHNTF` `.ctor` **`0x8E00F80`** (confirmed with
`py msig.py IFJNXZNHNTF`); trailing `____stringByteKeys` run:

| # | key | CLR | from |
|---|---|---|---|
| 1 | `GiftDrop` | `StorefrontGiftDrop` | `PurchasableGiftDrop` |
| 2 | `PurchasableItemId` | `int` | `PurchasableItem` |
| 3 | `Type` | `PurchasableItemType` enum | `PurchasableItem` |
| 4 | `Prices` | `List<PurchasablePrice>` | `PurchasableItem` |
| 5 | `SubscriberPrices` | `List<PurchasablePrice>` | `PurchasableItem` |
| 6 | `IsFeatured` | bool | `PurchasableItem` |
| 7 | `AvailableAt` | `DateTime?` | `PurchasableItem` |
| 8 | `AvailableUntil` | `DateTime?` | `PurchasableItem` |
| 9 | `NewUntil` | `DateTime?` | `PurchasableItem` |
| 10 | `CanBeGifted` | bool | `PurchasableItem` |
| 11 | `OnlyAvailableThroughCv2` | bool | `PurchasableItem` |

⚠️ **`RecNet.ItemPurchaseInfoDTO` is a different, similar-looking 10-field type** (`ItemId`,
`PurchaseMethodId`, `Prices`, `NewUntil`, `AvailableAt`, `AvailableUntil`, `CanBeGifted`,
`CanApplySubscriberDiscount`, `SubscribersOnly`, `IsFeatured`). It belongs to
`GYVRRKIELRB -> List<ItemPurchaseInfoDTO>`, **not** here. Do not mix the two — `PurchasableItem` has
`PurchasableItemId`/`Type`/`SubscriberPrices`/`OnlyAvailableThroughCv2` and no `PurchaseMethodId`.

### The two leaf DTOs — formatter-confirmed

| type | formatter | `.ctor` | keys |
|---|---|---|---|
| `RecNet.PurchasablePrice` | `Utf8Json.Formatters.RecNet.RCVWGWHTBRP` | `0x8E072B0` | `CurrencyType` enum · `Price` int · `StorefrontSaleData` obj\|null |
| `RecNet.StorefrontSaleData` | `Utf8Json.Formatters.RecNet.DIIJWELXXGH` | `0x8E88CA0` | `SalePercent` int · `SaleStartDate` `DateTime?` · `SaleEndDate` `DateTime?` |

Both were first read off `ftypes` field lists and have since been confirmed against their generated
formatters (`py msig.py` names the concrete DTO in the `Serialize` signature), so no key in this
response is now a field-list inference.

### Key counts are provably complete

`names.py` output can be truncated by a short window, so each run was checked arithmetically:
`____keyMapping` holds one entry per accepted casing (3 for a multi-word key, **2 for a single word**,
because camelCase and all-lowercase collide), each appearing twice (`lea` in the metadata-init block,
`mov` at the use site), plus one `____stringByteKeys` entry per serialized member:

| formatter | unique casings | expected refs | observed |
|---|---|---|---|
| `IFJNXZNHNTF` (PurchasableGiftDrop, 11 keys) | 31 | 31×2 + 11 = **73** | 73 ✓ |
| `LGMONMNKGKT` (StorefrontGiftDrop, 24 keys) | 67 | 67×2 + 24 = **158** | 158 ✓ |
| `RCVWGWHTBRP` (PurchasablePrice, 3 keys) | 8 | 8×2 + 3 = **19** | 19 ✓ |
| `DIIJWELXXGH` (StorefrontSaleData, 3 keys) | 9 | 9×2 + 3 = **21** | 21 ✓ |

Every count matches exactly, so 11 / 24 / 3 / 3 are the complete shapes — nothing was cut off.

## Nested `RecNet.StorefrontGiftDrop` — 24 wire keys from 26 fields

Formatter `Utf8Json.Formatters.RecNet.LGMONMNKGKT` `.ctor` **`0x8E8EBC0`** (confirmed by signature).
Trailing key run, in order:

`GiftDropId` int · `FriendlyName` · `Tooltip` · `TagList` · `ConsumableItemDesc` ·
**`AvatarItemDesc`** · `CustomAvatarItemId` Guid? · `PurchasableXpBoostId` Guid? ·
`AvatarItemType` enum? · `EquipmentPrefabName` · `EquipmentModificationGuid` · `IsQuery` bool ·
`Unique` bool · `SubscribersOnly` bool · `Rarity` enum · `CurrencyType` enum · `Currency` int ·
`Context` enum · `ItemCount` int · `ItemSetId` int? · `ItemSetFriendlyName` · `AvatarItemId` int? ·
`EquipmentItemId` int? · `ThumbnailImageName`.

⚠️ **The two fields with no wire key:**

- **`AvatarItemDescOverride`** (`Nullable<RecRoom.AssetIds.AvatarItemDesc>`) — the *parsed struct*.
  The wire key **`AvatarItemDesc` is the string `AvatarItemDescOrHairDyeDesc`**. This is the same
  trap recorded for 2025's `FLMDJANAGJA` in [giftdropstore-v3](giftdropstore-v3-wire-shape.md), now confirmed by
  2026's de-obfuscated names.
- **`Content`** (`GiftBoxContents`) — ⚠️ `Content` is **not a key at all**, in the run *or* the
  casing map (no `content`/`Content` literal anywhere in the `.ctor`). `PurchasableGiftDrop`
  exposes `get_GiftBoxContent()`, so the value is derived client-side. Emitting `Content` is
  silently dropped. Note `Context` **is** on the wire — the two are one letter apart.

⚠️ `ConsumableItemDesc` must be **unique and non-null across the catalogue** — the consumables load
path `Dictionary.Add`s by it ([consumables-v1-v2-routes](consumables-v1-v2-routes-wire-shapes.md)).

## Post-deserialize hooks — all three are REAL, none is a no-op

`EMSIIQRWASQ` is 2026's `CPOBHIECLEN` (the post-deserialize hook). All three DTOs in this response
have one at a **distinct RVA** — none folds onto a shared `nop; ret` stub, so all three run:

| type | hook | what it does |
|---|---|---|
| `PurchasableGiftDrop` | `0x9555EA0` | calls the base hook, then the nested one if `GiftDrop != null` |
| `PurchasableItem` | `0x9556A00` | defaults a null `SubscriberPrices` to an empty list |
| `StorefrontGiftDrop` | `0x9558520` (bounds `0x9558520..0x955867E` via `fstart.py`) | derives `Content`, normalizes `ItemSetId` |

### ✅ `SubscriberPrices: null` is safe — `Prices: null` is NOT

`PurchasableItem.EMSIIQRWASQ` is exactly:

```
if (this.SubscriberPrices /* +0x20 */ == null)
    this.SubscriberPrices = new List<PurchasablePrice>();     ; 0x9556A31 cmp qword [rdi+0x20], 0
```

It touches **only `+0x20`**. Per `py fields2025.py PurchasableItem`: `+0x18` = `Prices`,
`+0x20` = `SubscriberPrices`. So a null `SubscriberPrices` is repaired to an empty list, while a null
**`Prices` is left null** and NREs in whatever enumerates it. **Always send `Prices` as an array**
(`[]` at worst); `SubscriberPrices` may be omitted.

### ✅ A null `GiftDrop` does not throw in the hook

`PurchasableGiftDrop.EMSIIQRWASQ` is `base.Hook(); if (GiftDrop /* +0x68 */ != null) GiftDrop.Hook();`
— `test rcx,rcx / je 0x9555EC5` at `0x9555EB4`, so null skips rather than throwing. But
`get_Id()`, `get_FriendlyName()`, `get_Rarity()`, `get_ConsumableItemDesc()` and the rest all read
through it, so the store UI NREs later instead. Send the object.

### Why `Content` is not a wire key — it is computed from the other keys

`StorefrontGiftDrop.EMSIIQRWASQ` writes `Content` (`+0xC8`) on every path. First match wins:

| # | condition | `Content` |
|---|---|---|
| 1 | `AvatarItemDesc` non-empty, **or** `CustomAvatarItemId` set | `AvatarItemType == 1` ? **`HairDye` 6** : **`OutfitItem` 1** |
| 2 | else `ConsumableItemDesc` non-empty | **`Consumable` 4** |
| 3 | else `EquipmentPrefabName` non-empty | **`Equipment` 2** |
| 4 | else `IsQuery == true` | **`Query` 5** |
| 5 | else `CurrencyType != 0` **and** `Currency > 0` | **`Currency` 3** |
| 6 | else | **`Unspecified` -1** |

Branch 1's selector is `test al, cl / mov eax,6 / mov ecx,1 / cmove eax, ecx` at `0x9558663` — i.e.
it tests only the **low bit** of `AvatarItemType`, so `Outfit 0` and `CustomOutfit 2` both yield
`OutfitItem 1`, and only `HairDye 1` yields `6`.

**So for a consumable you must set `ConsumableItemDesc` and leave `AvatarItemDesc` /
`CustomAvatarItemId` / `EquipmentPrefabName` empty**, or the item is classified as outfit or
equipment and lands in the wrong tab. This is the mechanism behind "the item shows up under the
wrong category" with an otherwise-valid payload.

⚠️ **`PurchasableXpBoostId` is not consulted**, so this hook can never produce
`PurchasableXpBoost 8`. An XP-boost item reached through this route is classified by rules 2–6.

### ⚠️ `ItemSetId` is normalized, and the check reads only one byte

The hook opens with, at `0x9558575`:

```
if (((byte*)&this.ItemSetId /* +0xD4 */)[0] == 0)
    this.ItemSetId = new int?(0);          ; writes value=0, HasValue=true
```

Practical effect: **`ItemSetId: null` comes back as `0` with `HasValue == true`, never null.** Do not
expect the client to distinguish "no item set" from set 0.

⚠️ It compares only the **low byte** of the value, not `HasValue` (which sits at `+0xD8`;
`Nullable<T>` is laid out value-then-`has_value`, as the `rax >> 32` read of `AvatarItemType`'s flag
at `0x9558659` confirms). So an `ItemSetId` that is a **non-zero multiple of 256** (256, 512, …) has
a zero low byte and is **silently reset to 0**. Keep item-set ids away from multiples of 256. This
one is read off optimized code rather than from a source-level predicate — treat the byte-level
detail as such, but the reset itself is unambiguous in the instruction stream.

### Enum tables (2026, `py enumvals.py`)

```
PurchasableItemType : GiftDrop 0, SeasonTier 1, SeasonEliteUpgrade 2
GiftRarity          : None -1, Common 0, Uncommon 10, Rare 20, Epic 30, Legendary 50
CurrencyType        : Invalid 0, LaserTagTickets 1, RecCenterTokens 2, LostSkullsGold 100,
                      DraculaSilver 101, RecRoyale_Season1 200, RoomCurrency 300,
                      RoomInventoryItem 301, ProgressionEvent 400, RoomieCredits 500,
                      PaintballPaint 600
GiftBoxContents     : Unspecified -1, XP 0, OutfitItem 1, Equipment 2, Currency 3, Consumable 4,
                      Query 5, HairDye 6, Rectober_Trick 7, PurchasableXpBoost 8
AvatarItemType      : Outfit 0, HairDye 1, CustomOutfit 2
GiftContext         : None -1, Default 0, First_Activity 1, Game_Drop 2,
                      All_Daily_Challenges_Complete 3, All_Weekly_Challenge_Complete 4,
                      Daily_Challenge_Complete 5, Weekly_Challenge_Complete 6,
                      Unassigned_Equipment 10, Unassigned_Avatar 11, Unassigned_Consumable 12
```

All numeric on the wire.

## Minimal working body

One consumable, for a request of `{"PurchasableItemIds":[8311],"GiftDropIds":[]}`:

```json
[
  {
    "GiftDrop": {
      "GiftDropId": 8311,
      "FriendlyName": "Confetti Cannon",
      "Tooltip": "Pop!",
      "TagList": "",
      "ConsumableItemDesc": "consumable.confetti_cannon",
      "AvatarItemDesc": null,
      "CustomAvatarItemId": null,
      "PurchasableXpBoostId": null,
      "AvatarItemType": null,
      "EquipmentPrefabName": null,
      "EquipmentModificationGuid": null,
      "IsQuery": false,
      "Unique": false,
      "SubscribersOnly": false,
      "Rarity": 0,
      "CurrencyType": 2,
      "Currency": 0,
      "Context": 0,
      "ItemCount": 1,
      "ItemSetId": null,
      "ItemSetFriendlyName": null,
      "AvatarItemId": null,
      "EquipmentItemId": null,
      "ThumbnailImageName": "confetti_cannon.png"
    },
    "PurchasableItemId": 8311,
    "Type": 0,
    "Prices": [ { "CurrencyType": 2, "Price": 100, "StorefrontSaleData": null } ],
    "SubscriberPrices": [],
    "IsFeatured": false,
    "AvailableAt": null,
    "AvailableUntil": null,
    "NewUntil": null,
    "CanBeGifted": false,
    "OnlyAvailableThroughCv2": false
  }
]
```

`Rarity`, `CurrencyType`, `Context`, `Type`, `GiftDropId`, `Currency`, `ItemCount` and the bools are
non-nullable — a JSON `null` on any of them throws. Omit the key instead.

## Where the ids come from

The ids posted here are the `PurchasableItemId`s the store page already collected —
`api/storefronts/v3/giftdropstore/{N}` ([giftdropstore-v3](giftdropstore-v3-wire-shape.md),
[giftdropstore-storefront-type](giftdropstore-storefront-type.md)) and `algorithmiclists/{name}?type=5` unified ids
`0.<int>` ([algorithmiclists-type5-unified-id](algorithmiclists-type5-unified-id.md)). **So this route must agree with
those**: every `PurchasableItemId` the catalogue hands out has to resolve here, or the tab that lists
it fails wholesale rather than dropping that one row.
