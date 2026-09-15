# Roomconsumables by room wire shape

> GET api/roomconsumables/v1/roomConsumable/room/{roomId} (svc 28 Econ) returns a BARE ARRAY of the 9-key JHLGLLIJGKM; cached whole-list by roomId (no per-element key matching, unlike getPurchaseOffersBatch), no validation, [] is fine.

Derived **2026-09-14** from build `20250718.01` via [recflare-2025-metadata-carve](../../../il2cpp-analysis/references/recflare-2025-metadata-carve.md).
Econ facade `PLDJEBOENBJ` (room consumables), sibling of the currency facade `APMOEDPLHMM`
([roomcurrencies-createcurrency-wire-shape](roomcurrencies-createcurrency-wire-shape.md)).

`GET https://econ.<host>/api/roomconsumables/v1/roomConsumable/room/{roomId}` — service
**28 = Econ** (`mov r8d, 0x1c` at `0x7DB3C61`), verb **GET**: the state machine has exactly **one**
`HttpMethod` static read, `[statics+0x08] = get_method` at `0x7DB3C01`. (Worth checking that count —
[roomcurrencies-purchaseoffersbatch-wire-shape](roomcurrencies-purchaseoffersbatch-wire-shape.md) has *two* and picks by id count.)

Path is `String.Format("{0}/v1/roomConsumable/room/{1}", "api/roomconsumables", roomId)`
(`0xD094028` + `0xD14B218`), so `roomId` is baked into the path. **No query params, no body** — no
`ELHKHFJEHLM` / `ELKIBCPINAP` anywhere in the method.

Entry `PLDJEBOENBJ.IEFPPIFNGAM(long roomId, CancellationToken)` → `Task<List<JHLGLLIJGKM>>`, state
machine `IPGHMKBFGLJ.MoveNext` **`0x7DB3AC0`** (fields unobfuscated: `long roomId`). Send generic
`HPBKMCLEANE<List<JHLGLLIJGKM>>` (generic inst **2725**) — **bare array, no envelope**.

## Response element `.JHLGLLIJGKM` — 9 keys

Formatter `KGPBPNGHMCC` `.ctor 0x76B1C30`. The type lists 13 "fields", but **four are static consts**
(`DONAIGDOFJE`, `PGCAHPHFKPH`, `FOLFJNMLNDK`, `LJLCPBCKOLE` — all at offset `0x0000`, i.e. not
instance data). The 9 instance fields map 1:1 to the 9 keys:

| # | key | CLR | offset |
|---|---|---|---|
| 1 | `RoomConsumableId` | `System.Guid` | 0x10 |
| 2 | `RoomId` | long | 0x20 |
| 3 | `Name` | string | 0x28 |
| 4 | `Description` | string | 0x30 |
| 5 | `ImageName` | string | 0x38 |
| 6 | `Price` | **long** | 0x40 |
| 7 | `PurchaseCurrencyId` | **`Guid?`** | 0x48 |
| 8 | `ModifiedAt` | DateTime | 0x60 |
| 9 | `MaximumCountPerPurchase` | int | 0x68 |

```json
[ { "RoomConsumableId": "<guid>", "RoomId": 1162, "Name": "Health Potion",
    "Description": "…", "ImageName": null, "Price": 25,
    "PurchaseCurrencyId": "<room-currency guid or null>",
    "ModifiedAt": "2026-09-14T12:00:00Z", "MaximumCountPerPurchase": 10 } ]
```

`PurchaseCurrencyId` is the room currency from
[roomcurrencies-createcurrency-wire-shape](roomcurrencies-createcurrency-wire-shape.md)'s `CurrencyId`; `null` means it is not bought with a
room currency (token purchase — see the sibling routes `…/purchase/currency` vs `…/purchase/tokens`).

## Cached by roomId, not per element

`PLDJEBOENBJ..cctor` `0x7DBF290` registers `IEFPPIFNGAM` as the loader of a
**`.FDBJDINACHP\`2<long, List<JHLGLLIJGKM>>`** cache — the key is the **roomId** and the value is the
**whole list**. The public accessor is
`PLDJEBOENBJ.KMCHHMDAFDD(long roomId) -> KPIPLFECKNC<IReadOnlyList<JHLGLLIJGKM>>` `0x7DBE740`.

⇒ Unlike [roomcurrencies-purchaseoffersbatch-wire-shape](roomcurrencies-purchaseoffersbatch-wire-shape.md) (whose `IMAGJAIKIPF<Guid, …>` cache keys
*each element* by `CurrencyId` and so needs one element per requested id), **this route has no
per-element key matching**. `[]` is a completely valid answer for a room with no consumables.

## No validation

`JHLGLLIJGKM.CPOBHIECLEN` is the `0xA60520` **no-op** — every key omittable, nothing throws.
A `{}` body is the only hard failure ([ioncmjiacfi-malformed-response](../conventions/ioncmjiacfi-malformed-response.md), T is a `List`).

## Sibling routes on `PLDJEBOENBJ`

`{0}/v1/roomConsumable/room/{1}/me` `0xD0943C8`, `{0}/v1/roomConsumable/{1}` `0xD094760`,
`…/{1}/consume` `0xD094B00`, `…/{1}/isOwned` `0xD094E98`,
`api/roomconsumables/v1/roomConsumable` `0xD14B5B0`, `…/roomConsumable/awardBulk` `0xD14B948`,
`…/roomconsumable/{0}/purchase/currency` `0xD14BCE0`, `…/roomconsumable/{0}/purchase/tokens`
`0xD14C078`.
