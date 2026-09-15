# Giftdropstore v3 wire shape

> GET api/storefronts/v3/giftdropstore/{id} (svc 28 Econ) and the nested GiftDrop DTO (FLMDJANAGJA) — 22 wire keys; AvatarItemDesc is the STRING at 0x70, and the parsed NPHONPGHNPF struct at 0x38 plus the item-kind enum at 0xb8 are client-derived and NOT on the wire.

Derived **2026-09-09** from build `20250718.01` via [recflare-2025-metadata-carve](../../../il2cpp-analysis/references/recflare-2025-metadata-carve.md).
Ties directly to [avatar-item-desc-registry](../../../rr-client-bringup/references/avatar-item-desc-registry.md) — this is the payload whose `AvatarItemDesc` feeds
the wardrobe lookup that silently drops unknown descs.

`GET https://econ.<host>/api/storefronts/v3/giftdropstore/{storefrontId}` — service **28 = Econ**
(`mov r8d, 0x1c` at `0x7DC053C`). Route is `Format("{0}v3/giftdropstore/{1}", "api/storefronts/",
id)`, literals `0xD0B6610` + `0xD1528A8`. State machine `<GetStorefrontAsTask>b__0>d.MoveNext`
`0x7DC0310`; send generic `HPBKMCLEANE<.FMHJCKFGDPI>` (inst 2826) — **bare, no envelope**.

## Nesting

`FMHJCKFGDPI` (storefront, formatter `MFJFPALAFOH` `.ctor 0x7684AD0`) — trailing keys
`StorefrontName`, `SubscriberDiscountPercent`, `StorefrontType`, `NextUpdate`, `NewUntil`,
**`StoreItems`** (`List<GBEBEEFLKJP>` @0x38). The client `OrderBy`s the items by a `string` key
(generic inst 9618 = `<GBEBEEFLKJP, string>`) before use.

`GBEBEEFLKJP` (store item, formatter `OBNJPHDJPPM` `.ctor 0x7E85EC0`, base `AKOFCOCBAIC`) — 11 keys,
**derived member first**: **`GiftDrop`** (`.FLMDJANAGJA` @0x68), then `PurchasableItemId`, `Type`,
`Prices`, `SubscriberPrices`, `IsFeatured`, `AvailableAt`, `AvailableUntil`, `NewUntil`,
`CanBeGifted`, `OnlyAvailableThroughCv2`.

## `GiftDrop` = `.FLMDJANAGJA` — 22 wire keys

Formatter `DPABMEPLIFA` `.ctor 0x7754A10`. The type declares **24** fields; the mapping below was
taken from the **Serialize** method `DPABMEPLIFA.FBGBLPHHDGN` `0x7753870`, reading the field offsets
it touches in order — the only reliable way here, because pairing keys against the declaration list
mis-aligns at `AvatarItemDesc`.

| # | key | CLR | offset |
|---|---|---|---|
| 1 | `GiftDropId` | int | 0x10 |
| 2 | `FriendlyName` | string | 0x18 |
| 3 | `Tooltip` | string | 0x20 |
| 4 | `TagList` | string | 0x28 |
| 5 | `ConsumableItemDesc` | string | 0x30 |
| 6 | **`AvatarItemDesc`** | **string** | **0x70** |
| 7 | `CustomAvatarItemId` | `Guid?` | 0x78 |
| 8 | `AvatarItemType` | `NHKFIOBDEOB?` | 0x8c |
| 9 | `EquipmentPrefabName` | string | 0x98 |
| 10 | `EquipmentModificationGuid` | string | 0xa0 |
| 11 | `IsQuery` | bool | 0xa8 |
| 12 | `Unique` | bool | 0xa9 |
| 13 | `SubscribersOnly` | bool | 0xaa |
| 14 | `Rarity` | `LCEGHIAIKNO` | 0xac |
| 15 | `CurrencyType` | `PJBEJGJLLLM` | 0xb0 |
| 16 | `Currency` | int | 0xb4 |
| 17 | `Context` | `EHFKNLKDDIE` | 0xbc |
| 18 | `ItemSetId` | `int?` | 0xc0 |
| 19 | `ItemSetFriendlyName` | string | 0xc8 |
| 20 | `AvatarItemId` | `int?` | 0xd0 |
| 21 | `EquipmentItemId` | `int?` | 0xd8 |
| 22 | `ThumbnailImageName` | string | 0xe0 |

**Two fields are `[IgnoreDataMember]` and must NOT be sent:**
- **`0x38  Nullable<.NPHONPGHNPF>`** — the *parsed* `AvatarItemDesc` (the 48-byte three-guid struct
  from [avatar-item-desc-registry](../../../rr-client-bringup/references/avatar-item-desc-registry.md)). The wire carries the **string** form at 0x70; this is its
  client-side parse target. Failure literal:
  `"Error when parsing giftDrop={0} for outfit using customAvatarItemId='{1}'"` `0xD0433D8`.
- **`0xb8  .FCEOMOKNMBM`** — the item-kind enum (`Unspecified -1, XP 0, OutfitItem 1, Equipment 2,
  Currency 3, Consumable 4, Query 5, HairDye 6`), **derived** by the post-deserialize hook.

## The hook derives, it does not validate

`FLMDJANAGJA.CPOBHIECLEN` `0x7D906C0` runs three `String.IsNullOrEmpty` checks over the id/desc
fields and writes the kind into `+0xb8` (3 Currency, 5 Query, 2 Equipment, −1 Unspecified …). It also
composes a `" Star Unique Box"` display name. **No throw helper anywhere in its range** — every key
is omittable.

## Enums

- `AvatarItemType` `NHKFIOBDEOB`: `Outfit 0`, `HairDye 1`, `CustomOutfit 2` (confirmed by the
  literals `'PurchasableGiftDrop.AvatarItemType is CustomOutfit'` / `'… is HairDye'`).
- `Rarity` `LCEGHIAIKNO`: `None -1`, `Common 0`, `Uncommon 10`, `Rare 20`, `Epic 30`,
  `Legendary 50`.
- `CurrencyType` `PJBEJGJLLLM`: `Invalid 0`, `LaserTagTickets 1`, `RecCenterTokens 2`,
  `LostSkullsGold 100`, `DraculaSilver 101`, `RecRoyale_Season1 200`, `RoomCurrency 300`,
  `RoomInventoryItem 301`, `ProgressionEvent 400`, `RoomieCredits 500`
  (same enum as [storefronts-v3-buyinvention-wire-shape](storefronts-v3-buyinvention-wire-shape.md)).
- `Context` `EHFKNLKDDIE`: `None -1`, `Default 0`, `First_Activity 1`, `Game_Drop 2`,
  `All_Daily_Challenges_Complete 3`, `All_Weekly_Challenge_Complete 4`,
  `Daily_Challenge_Complete 5`, `Weekly_Challenge_Complete 6`, `Unassigned_Equipment 10`,
  `Unassigned_Avatar 11`, `Unassigned_Consumable 12`, `Reacquisition 20`, `Membership 21`,
  `NUX_TokensAndDressUp 30`.

**How to apply:** for an avatar item, set `AvatarItemDesc` (the comma-separated guid string) **and**
`AvatarItemType`; leave `0x38`/`0xb8` alone — they have no keys. Serving a desc the client's baked
`descToCaidMapping` does not contain still yields a silent drop with no log
([avatar-item-desc-registry](../../../rr-client-bringup/references/avatar-item-desc-registry.md)) — that failure is downstream of this payload, not caused by it.
