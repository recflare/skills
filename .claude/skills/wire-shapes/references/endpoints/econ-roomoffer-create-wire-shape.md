# `POST econ/roomOffer/room/{roomId}` — create a Room Offer (2026)

> Build `20260323.14`. Derived **2026-11-13**. svc **28 Econ** (`econ.` host). Facade
> `RecNet.LEMLPUGKWSA` (the low-level RoomOffer HTTP facade; the manager
> `RecRoom.RoomEconomy.RoomOffer.KQPMJKEWIZA` sits above it). This is the **create** sibling the
> [recentPurchases note](econ-roomoffer-recentpurchases-wire-shape.md) left underived.

## Route
- **Verb: POST.** `[HttpMethod klass + 0x20]` (2026 statics ptr) then `[statics + 0x20]` = Post,
  disassembled at `0x957b09d`.
- **Path:** `String.Format("{0}/room/{1}", "econ/roomOffer", roomId)` → `econ/roomOffer/room/{roomId}`.
  `roomId` is the path segment (facade arg `b`, a long); it is **not** in the body.
- Async state machine `<CreateRoomOffer>d__14$$MoveNext` **0x957ad60**; facade
  `RecNet.LEMLPUGKWSA$$NNAHOQXCHHV` 0x956f440 (`Nullable<Guid> originId` first arg ⇒ create; the
  `Guid`-required sibling `THECMLYFYCQ` / `<UpdateRoomOffer>d__15` 0x95840a0 is the PUT update).
- Body set via `FZNGWUAGAIN` (request-body setter); send tier `ZWUODKCINOA` (response-required).
- ⚠️ The create path fires a **second** request to `econ/roomInventoryItemTags/{0}/{1}` after the
  create (tag upsert), send inst #3201 — a distinct route, not part of this response.

## Response — **ENVELOPED single object**
Send inst #22951 = **`RecNet.RecNetResultObject`1<RecNet.RoomOffer>`**. 2026 envelope layout:
`Success` bool +0x10, `Error` string +0x18, `error_id` +0x20 (lowercase `[DataMember]`), `Value` +0x28.

```json
{"Value": { …RoomOffer… }, "Success": true, "Error": null, "error_id": null}
```

`Value` is the created offer. ⚠️ Plain `ZWUODKCINOA` ⇒ a null/`{}` body **deserializes to null**
and then NREs the caller — return the full envelope with a populated `Value`, never a bodyless 2xx.

### `Value` = `RecNet.RoomOffer` — 18 keys
Formatter `Utf8Json.Formatters.RecNet.NXODCJEERGH` `.ctor 0x8e7b3f0` (one of three formatters that
ref the `HasDynamicPrice` literal 0xFD44B40; this is the one with `RoomId`/`Version`/`CreatedAt` and
**no** `RoomOfferId`/`PriceUnitId` — those belong to the sibling `RoomOfferDTO` formatter 0x8e774d0).
Order = backing-field order from `fields2025.py RoomOffer` (typedef #46549):

| # | key | CLR | notes |
|---|---|---|---|
| 1 | `OriginId` | Guid(→string) | server-assigned on create |
| 2 | `RoomId` | long | |
| 3 | `Name` | string | |
| 4 | `Description` | string | |
| 5 | `ImageName` | string | |
| 6 | `Price` | int | |
| 7 | `IsGiftable` | bool | |
| 8 | `Visibility` | `UgcPurchasableItemVisibility` enum(int) | 0 AlwaysVisible, 1 HiddenInWatchStore |
| 9 | `HasDynamicPrice` | bool | |
| 10 | `MinimumDynamicPrice` | `int?` | backing `<EFMBVXADKYQ>`; public `MinDynamicPrice` int is COMPUTED, not on wire |
| 11 | `MaximumDynamicPrice` | `int?` | backing `<NNZIINITTJM>`; public `MaxDynamicPrice` int is COMPUTED |
| 12 | `PriceUnitOriginId` | `Guid?` | |
| 13 | `Version` | int | |
| 14 | `MaxNumPurchasesPerPlayer` | `int?` | |
| 15 | `MaxCountPerPurchase` | `int?` | |
| 16 | `ItemMappings` | `List<RoomOfferItemMappingDTO>` | |
| 17 | `CreatedAt` | DateTime(→ISO) | |
| 18 | `ModifiedAt` | DateTime | |

**NOT on the wire** (no string literal / computed, confirmed): `RoomOfferType` (computed),
`InventoryItemMappings` (field `XOBPSHYWISM`, derived), `MinDynamicPrice`/`MaxDynamicPrice` (computed
ints), and the client-local `LocalOverrideImageName` / `LocalOverrideDescription` /
`LocalOverrideName` / `LocalOverridePrice` + their `HasLocalOverride*` flags — `LocalOverrideImageName`
has **no** string literal in the image, proving these are `[IgnoreDataMember]` client-side overrides.

## Request body — `RecNet.RoomOfferCreateOrUpdateRequestDTO` — 15 keys
Formatter `Utf8Json.Formatters.RecNet.DYHUEFRFMLT` `.ctor 0x8e72b60` (the one with `AllowRename` +
`PriceUnitId`, no RoomId/Version). The server must accept:

`OriginId` Guid? (**null on create** — server mints it; set on update) · `Name` string ·
`Description` string · `ImageName` string · `Price` int · `HasDynamicPrice` bool ·
`MinimumDynamicPrice` int? · `MaximumDynamicPrice` int? · `MaxNumPurchasesPerPlayer` int? ·
`MaxCountPerPurchase` int? · `ItemMappings` `List<RoomOfferItemMappingDTO>` · `PriceUnitId` Guid? ·
`AllowRename` bool · `Visibility` enum(int) · `IsGiftable` bool.

The facade takes a `Dictionary<Guid,int>` of item→count and converts it to the `ItemMappings` list
(`PETEHTEDMHP` + the loop in NNAHOQXCHHV). `RoomOfferType` is a facade arg but is **not** a wire key.

### Nested `RecNet.RoomOfferItemMappingDTO` — 3 keys
`ItemType` `RoomOfferItemType` enum(byte) (0 Unset, 1 RoomInventoryItem) · `ItemOriginId` Guid ·
`Count` int. ⚠️ This is the link to room inventory: `ItemOriginId` is a **Room Inventory Item
OriginId** (see [roominventory-routes](roominventory-routes-wire-shapes.md)) with
`ItemType=RoomInventoryItem` — an offer grants those items on purchase.

## `GET econ/roomOffer/room/{roomId}` — list a room's offers (same file)
Facade `LEMLPUGKWSA.UGPKWIPGCWQ` 0x956fb40 (inline, no d__). **GET** (`[statics+0x08]`, disasm
`0x956fbf8`→`[rcx+8]`), same `{0}/room/{1}` path, no body. **BARE ARRAY** `List<RoomOffer>`
(send inst #23352 = `List<RecNet.RoomOffer>`, `ZWUODKCINOA`, no `FZNGWUAGAIN`). Element is the
same 18-key `RoomOffer` above. Serve `[]` for empty, never null/`{}`.

## `GET econ/roomOffer/room/{roomId}/purchaseCounts` (same file)
Facade `LEMLPUGKWSA.WHUZUGWXAHW`, `<GetRoomOfferPurchaseCountsForRoom>d__18` 0x957f360. **GET**
(`[statics+0x08]`, disasm `0x957f483`→`[rcx+8]`), path `String.Format("{0}/room/{1}/purchaseCounts",
"econ/roomOffer", roomId)`, no body. **ENVELOPED LIST** `RecNetResultListObject<RoomOfferPurchaseCountDTO>`
(send inst #22899). Element `RoomOfferPurchaseCountDTO` = **2 keys**: `RoomOfferOriginId` Guid(→string,
= a `RoomOffer.OriginId`) · `NumOffersPurchased` int (aggregate room-wide purchase count). Serve
`{"Value":[],"Success":true,"Error":null,"error_id":null}` for empty.

## `POST econ/roomOffer/{roomId}/{offerId}/purchase` — buy an offer (same file)
Facade `LEMLPUGKWSA.CEUJYXEZKOS` 0x956ee80 → `Task<RoomOfferPurchaseResponseDTO>` (**BARE**, not
enveloped). SM `<PurchaseRoomOffer>d__21` 0x9580d10. **POST** (`[statics+0x20]`→`[rcx+0x20]` at
`0x9580f1d`), **svc 28 Econ** (descriptor ctor `r8d=0x1c` at `0x9580f96`). Path
`String.Format("{0}/{1}/{2}/purchase", "econ/roomOffer", roomId, offerOriginId)` (literal 0xFCDC8E0).
Body set from a `RoomOfferPurchaseRequestDTO` built at `0x9580ec7`.

### Request body — `RecNet.RoomOfferPurchaseRequestDTO` — 7 keys (no renames)
Declaration order, all Original-casing literals present (no `[DataMember]`): `NumOffersPurchased` int ·
`TransactionId` Guid (client idempotency key) · `ExpectedTotalPrice` int (mismatch ⇒ result 6) ·
`ExpectedPriceUnitOriginId` Guid? (optional) · `ExpectedRoomOfferVersion` int (must equal the offer's
`Version`; mismatch ⇒ result 7) · `ConcurrencyCodeByItemOriginIdMap` `Dictionary<Guid,Guid?>`
(itemOriginId→code) · `GiftRecipientAccountId` int? (null = self, set = gift).

### Response — `RecNet.RoomOfferPurchaseResponseDTO` — 4 keys, **BARE** (typedef #46557)
⚠️ bare DTO ⇒ 2026 `{}`→null NRE; always return the object with `OperationResult`.
- `OperationResult` — enum `RoomOfferPurchaseOperationResult` **byte, NUMERIC** (only 1 of 3 sampled
  member names has a literal, so not by-name). `0 Success`; failures incl. `1 ConcurrencyCodeMismatch`,
  `2 RoomOfferDoesNotExist`, `6 ExpectedOfferTotalPriceMismatch`, `7 ExpectedOfferVersionMismatch`,
  `8 InsufficientBalance`, `12 CannotPurchaseMoreThanPerPlayerLimit`, `14 InsufficientInventoryItems`,
  `100 NoConcurrencyCodesForInventoryItem`, `101 UnexpectedOfferItemType`, `254 FeatureDisabled`,
  `255 UnknownError`.
- `BalanceUpdateResult` — `Nullable<UpdateResponseTypes>` (int enum, `0 OK`), optional.
- `TokenBalanceResponse` — `BalanceResponseDTO` 3 keys: `Balance` long · `CurrencyType` int enum
  (2 RecCenterTokens, 300 RoomCurrency, 301 RoomInventoryItem) · ⚠️ **`Platform`** = `BalanceType`
  `[DataMember]`-renamed (int enum `StorefrontBalanceType`, 4 RecNetPurchased). Emit `Platform`, not
  `BalanceType`.
- `PlayerRoomInventoryItems` — `List<RecNet.PlayerRoomInventoryItemDTO>` (the items this offer granted;
  these drive the backpack/getUnlocked). Element 6 keys: `RoomId` long · `RoomInventoryItemOriginId`
  Guid (= the offer's `ItemMappings[].ItemOriginId`) · `Count` **long** · `ConcurrencyCode` Guid ·
  `CreatedAt` · `ModifiedAt`. Serve `[]` if none, never null.

## Underived siblings on this facade
`BVWEYEQUOVE` delete (`RecNetResult`), `UVPYFNKGZHR` concurrencyCode map,
`LHAFODXTBPA` recent purchases (`RecNetResultListObject<RoomOfferLastPurchaseDTO>`).
