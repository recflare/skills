# UGC purchasables room items wire shape

> GET api/ugcPurchasables/v1/items/room/{roomId} (svc 28 Econ) takes NO params and returns a BARE ARRAY of the 10-key FNEMLMEJDAI; Price is a LONG and ItemId is a bare Guid (not the lowercase {itemType,itemId} struct).

Derived **2026-09-22** from build `20250718.01`.
`ItemType` shares the `NJHJPFMKGEE` enum with [econ-items-purchaseinfos](econ-items-purchaseinfos-wire-shape.md)'s `ItemId.itemType`.

`GET https://econ.<host>/api/ugcPurchasables/v1/items/room/{roomId}` — service **28 = Econ**
(`mov r8d, 0x1c` at `0x7DC9011`), verb **GET** (`HttpMethod` statics `[rcx+8]` at `0x7DC8FB1`).

**The path is `String.Format`-built**, not a single literal:
`Format("{0}/v1/items/room/{1}", "api/ugcPurchasables", roomId)`. Only `'api/ugcPurchasables'` and
`'api/ugcPurchasables/v1/items/bulk'` exist as whole-route literals, so grepping for the full path
finds nothing — the same trap as [roomkeys-v1-room](roomkeys-v1-room-wire-shape.md).

State machine `HBADNMCECOK$$MoveNext` `0x7DC8E70` (+0x440), error literal
`'Unable to fetch UGC purchasable items for room'`. **No query params and no body** — no
`ELHKHFJEHLM`, no `ELKIBCPINAP`; the room id is baked into the path.

## Response — BARE ARRAY, no envelope

`MGPBDIAGCFD::HPBKMCLEANE<T>` generic inst **#2715** = **`List<FNEMLMEJDAI>`** — the `List`
directly. `{}` or an empty body throws `IONCMJIACFI`; serve `[]`.

Element `.FNEMLMEJDAI`, formatter **`MLFFNMKOBJI`** `.ctor 0x76FEF30` (+0xcf0), key run
`0x76FF83F..0x76FFAEE` — **10 keys, 1:1 with the 10 declared fields** and with the 10-arg ctor, so
the pairing is confirmed three ways:

| # | key | CLR | off |
|---|---|---|---|
| 1 | `ItemType` | enum `NJHJPFMKGEE` | 0x10 |
| 2 | `ItemId` | **`System.Guid`** | 0x14 |
| 3 | `Name` | string | 0x28 |
| 4 | `Description` | string | 0x30 |
| 5 | `ImageName` | string | 0x38 |
| 6 | `RoomId` | **`long?`** | 0x40 |
| 7 | `Price` | **`long`** | 0x50 |
| 8 | `PurchaseCurrencyId` | `Guid?` | 0x58 |
| 9 | `CreatedAt` | DateTime | 0x70 |
| 10 | `ModifiedAt` | DateTime | 0x78 |

```json
[ { "ItemType": 0, "ItemId": "6da89ddf-f2e5-4c32-8b22-feb687683e36",
    "Name": "VIP Key", "Description": "", "ImageName": null,
    "RoomId": 78, "Price": 250, "PurchaseCurrencyId": null,
    "CreatedAt": "2026-09-22T00:00:00Z", "ModifiedAt": "2026-09-22T00:00:00Z" } ]
```

`NJHJPFMKGEE : int` — `RoomKey 0`, `RoomConsumable 1`, `RoomCurrencyPurchaseOffer 2`,
`CustomAvatarItem 3`, `StoreUGCAvatarItem 4`, `UNDEFINED 5`. Numeric on the wire.

⚠️ **Two easy type mistakes:**
- **`Price` is a `long` here**, not the `int` it is on `GICBMFJFHLI` ([customavataritems-routes](customavataritems-routes-wire-shapes.md)).
- **`ItemId` is a bare `Guid`**, *not* the lowercase-keyed `{itemType, itemId}` unified-id struct
  (`GOOKEEENOCO`) used by `api/items/purchaseInfos`. The discriminator rides beside it as the
  separate `ItemType` key.

## No validation

`FNEMLMEJDAI.CPOBHIECLEN` is the shared no-op stub `0xA60520` (4877 names fold onto that RVA), so
every key is omittable and nothing throws on partial data. The only hard requirement is the array.

## Purpose

Consumer side is unobfuscated: `RecRoom.Systems.UGCPurchasableItemsManager`, whose
`ConvertCustomAvatarItemToPurchasableItem` `0xF14250` builds one of these from a
`GICBMFJFHLI` — so the DTO is the room-scoped catalog of player-purchasable UGC (room keys,
room consumables, currency offers, custom avatar items).
