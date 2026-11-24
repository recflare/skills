# `GET api/ugcPurchasables/v1/items/room/{roomId}` — unified room purchasables (2026)

> svc **28 Econ** (`econ.` host). **GET**, no body. Returns a **BARE JSON ARRAY** of the unified
> `RecNet.UGCPurchasableItem` (send tier `ZWUODKCINOA`, deserialize type class 2987 =
> `List<UGCPurchasableItem>` — NOT enveloped). One flat list of everything buyable in the room, each
> element tagged by `ItemType`. A **room offer** is an element with `ItemType = 5`.

Derived **2026-11-23** from build `20260323.14`.

## Route
- Path `String.Format("{0}/v1/items/room/{1}", "api/ugcPurchasables", roomId)` (base literal 0xFC73F58,
  template `{0}/v1/items/room/{1}` 0x...). Consumer `<GetUGCPurchasableItemsForRoomServiceCall>d__5`
  **0x95a1440** (manager `RecRoom.Systems.UGCPurchasableItemsManager`; failure literal
  `'Unable to fetch UGC purchasable items for room'`). Sibling: `POST api/ugcPurchasables/v1/items/bulk`
  (`<GetUGCPurchasableItemsByIdsServiceCall>d__7` 0x95a0f10) → same element shape.
- **BARE** — serve `[]` for empty, never null/`{}`.

## Element — `RecNet.UGCPurchasableItem` — 10 keys (same shape for every ItemType)
No `[DataMember]` renames (all Original-casing literals present). Order = field order:

| # | key | CLR | notes |
|---|---|---|---|
| 1 | `ItemType` | `UGCPurchasableItemType` enum (numeric) | **5 = RoomOffer** |
| 2 | `ItemId` | Guid | for a room offer = the `RoomOffer.OriginId` |
| 3 | `Name` | string | |
| 4 | `Description` | string | |
| 5 | `ImageName` | string | |
| 6 | `RoomId` | long? | the owning room |
| 7 | `Price` | long | |
| 8 | `PurchaseCurrencyId` | Guid? | null = default currency; set = a room-currency item id |
| 9 | `CreatedAt` | DateTime | |
| 10 | `ModifiedAt` | DateTime | |

### `UGCPurchasableItemType` (int enum)
`RoomKey=0, RoomConsumable=1, RoomCurrencyPurchaseOffer=2, CustomAvatarItem=3, StoreUGCAvatarItem=4,
**RoomOffer=5**, UNDEFINED=6`.

### A room offer as it appears here
```json
{
  "ItemType": 5,
  "ItemId": "5a3c4b24-2970-54d6-9548-ae35a77ffb11",
  "Name": "My Offer",
  "Description": "",
  "ImageName": "",
  "RoomId": 21536,
  "Price": 100,
  "PurchaseCurrencyId": null,
  "CreatedAt": "2026-11-23T00:00:00Z",
  "ModifiedAt": "2026-11-23T00:00:00Z"
}
```

## ⚠️ This is a FLATTENED projection, not the full `RoomOffer`
It has **no** `Version`, `Visibility`, `ItemMappings`, `IsGiftable`, dynamic-price fields, or per-player
limits — those live only on the `RoomOffer` DTO from
[`econ/roomOffer/room/{roomId}`](econ-roomoffer-create-wire-shape.md). `ItemId` here is the join key
back to `RoomOffer.OriginId`. Use this endpoint for the lightweight "what's buyable in this room"
catalog; use the `roomOffer` routes when you need offer version/mappings (e.g. the purchase path, which
sends `ExpectedRoomOfferVersion` + `ConcurrencyCodeByItemOriginIdMap`).
