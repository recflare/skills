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

## Newer-server variant: `AvatarItemInfo` and 4 other keys (2026-09-15)

A capture may show a **27-key** `GiftDrop`. That is a **newer Rec Room version than `20250718.01`**,
not an error in this note. Reference data in `Vanadium-2023-2025-Leak-Server/Data/Storefronts/`
(files named by `StorefrontType`, which independently confirms the enum) contains three vintages
that nest **strictly**:

| vintage | GiftDrop keys | sample |
|---|---|---|
| older than this build | 17 | `1.json` (LaserTag), `3.json` (Watch) |
| **`20250718.01` (this note)** | **22** | — |
| newer | 27 | `2.json` (RecCenter) |

`17 ⊂ 22 ⊂ 27` with no key ever removed, which is what fixes the ordering. The 17-key vintage lacks
`TagList`, `CustomAvatarItemId`, `AvatarItemId`, `EquipmentItemId`, `ThumbnailImageName`; the 27-key
vintage adds **`AvatarItemInfo`, `ItemCount`, `QueryRedirectContext`, `QueryRedirectTag`,
`QueryRedirectRarity`**.

**None of the five exists in `20250718.01`.** `"AvatarItemInfo"` has **0 occurrences** in
`out/stringliteral.json` in any casing — decisive, because Utf8Json keys are emitted as string
literals (positive control: `ThumbnailImageName`, `ItemSetFriendlyName`, `AvatarItemDesc`,
`AvatarItemId`, `AvatarItemType` each return 1). Sending them to this client is **silently dropped**,
per the usual unknown-key rule.

`AvatarItemInfo` is a v2 wrapper that supersedes the legacy avatar-item triple; the newer server
sends **both**, so the payload stays backward compatible:

```json
"AvatarItemInfo": { "Version": 2,
  "LegacyAvatarItemDesc": "6b337a35-95d9-4b3a-9891-d9fbb06262aa",
  "DownloadableAvatarItemId": "5f00002b-8092-438c-8763-cc8ebd7eaf4d",
  "AvatarItemType": 0, "LegacyAvatarItemRowId": 360 }
```

Correlation across all 9 populated instances in `2.json` is exact:

| `AvatarItemInfo` field | legacy equivalent this client reads |
|---|---|
| `LegacyAvatarItemDesc` | `AvatarItemDesc` **with the trailing commas stripped** (`"<guid>,,,"` → `"<guid>"`) |
| `LegacyAvatarItemRowId` | `AvatarItemId` |
| `AvatarItemType` | `AvatarItemType` |
| `DownloadableAvatarItemId` | **no equivalent** — the new downloadable-avatar-item system, which this build has no concept of |
| `Version` | always `2` |

It is `null` when the drop carries no avatar item (`AvatarItemDesc: ""`, `AvatarItemId: 0`).

**So for `20250718.01`: keep populating the legacy fields and ignore `AvatarItemInfo`.** Relaying a
newer capture verbatim is safe — the legacy keys are still present and are what this client reads.
The one thing that cannot be carried back is `DownloadableAvatarItemId`.
