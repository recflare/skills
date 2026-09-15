# Econ items purchaseinfos wire shape

> POST api/items/purchaseInfos (svc 28 Econ) body {Ids:[{itemType,itemId}]}, response is a BARE ARRAY of the 10-key PurchaseInfo (ODENGGBLDCP); no validation hook on either side.

Derived **2026-08-27** from build `20250718.01` via [recflare-2025-metadata-carve](../../../il2cpp-analysis/references/recflare-2025-metadata-carve.md).

`POST api/items/purchaseInfos` — **POST** (`HttpMethod` statics `+0x20`), service **28 Econ**
([recnet-service-enum](../conventions/recnet-service-enum.md)). Client entry
`AKDHOHEPFBH.GHNNDNMJHBN(IReadOnlyList<Guid> ids, CancellationToken)` `0x7D88880`.
Send `HPBKMCLEANE<List<ODENGGBLDCP>>` — **required response, BARE ARRAY** (so it belongs on
[nonobject-response-routes](../conventions/nonobject-response-routes.md); `{}` or an empty body throws `IONCMJIACFI`, `[]` is fine).

## Request body `ILKICDHNJMN` - 1 key (formatter `DINHACKIPMD` `.ctor 0x76D82A0`)

```json
{ "Ids": [ {"itemType": 3, "itemId": "6da89ddf-f2e5-4c32-8b22-feb687683e36"} ] }
```

`Ids` is `IReadOnlyList<GOOKEEENOCO>` - the same **lowercase-keyed** unified item id struct used by
`ugcPurchasables/v1/items/bulk` ([avatar-lockeditems-bulk-wire-shape](avatar-lockeditems-bulk-wire-shape.md) neighbours) and as
`PurchaseInfo.ItemId`. The client method takes plain `Guid`s, so `itemType` is normally
`CustomAvatarItem = 3`. `itemType` enum `NJHJPFMKGEE`: `RoomKey 0`, `RoomConsumable 1`,
`RoomCurrencyPurchaseOffer 2`, `CustomAvatarItem 3`, `StoreUGCAvatarItem 4`, `UNDEFINED 5`.

## Response: bare array of `ODENGGBLDCP` - 10 keys

Same DTO that appears as `CustomAvatarItem.PurchaseInfo` (see the `POST api/customAvatarItems/v1`
derivation):

| key | offset | type |
|---|---|---|
| `ItemId` | 0x10 | `GOOKEEENOCO` `{itemType, itemId}` - **lowercase keys** |
| `PurchaseMethodId` | 0x18 | `IPFLNKMNPMP` `{Type, NumberId, Guid}`; Type `PurchasableItem 0` / `CustomAvatarItem 1` |
| `Prices` | 0x20 | `List<BNOLJGINMNE>` `{CurrencyType, Price, StorefrontSaleData}` |
| `NewUntil` | 0x28 | `DateTime?` |
| `AvailableAt` | 0x38 | `DateTime?` |
| `AvailableUntil` | 0x48 | `DateTime?` |
| `CanBeGifted` | 0x58 | bool |
| `CanApplySubscriberDiscount` | 0x59 | bool |
| `SubscribersOnly` | 0x5A | bool |
| `IsFeatured` | 0x5B | bool |

`CurrencyType` (`PJBEJGJLLLM`): `Invalid 0`, `LaserTagTickets 1`, `RecCenterTokens 2`,
`LostSkullsGold 100`, `DraculaSilver 101`, `RecRoyale_Season1 200`, `RoomCurrency 300`,
`RoomInventoryItem 301`, `ProgressionEvent 400`, `RoomieCredits 500`.
`StorefrontSaleData` (`IKOJIDAIAIN`): `{SalePercent int, SaleStartDate DateTime?, SaleEndDate DateTime?}`.

**No validation:** both `ODENGGBLDCP.CPOBHIECLEN` and `ILKICDHNJMN.CPOBHIECLEN` fold onto the shared
no-op stub `0xA60520`, so nothing throws on partial data - a wrong shape just yields defaults.
