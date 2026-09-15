# Customavataritems routes wire shapes

> The CustomAvatarItem DTO (GICBMFJFHLI, 20 keys) and every api/customAvatarItems/v1 route: /search /featured /bulk return a BARE ARRAY, POST /v1 is ENVELOPED, /design is a bare 4-key object.

Derived **2026-08-26/27** from build `20250718.01` via [recflare-2025-metadata-carve](../../../il2cpp-analysis/references/recflare-2025-metadata-carve.md).
All on service **2 = API** (`api.<host>`) except the `econ/customAvatarItems/*` siblings.

## The shared element: `GICBMFJFHLI` = CustomAvatarItem, 20 keys

Formatter `DKABGCCAAEB` `.ctor 0x7D703D0`. 21 declared fields -> 20 keys (`BIECGDFEFCF` is a plain
field, not an auto-property, so it never serializes). **No post-deserialize hook** - the deserializer
sets fields and returns, so nothing throws on partial data.

`CustomAvatarItemId` Guid, `CreatorAccountId` int, `Name`, `Description`, `Price` int,
`Accessibility` enum (`Private 0`, `Public 1`, `Unlisted 2`), `ForceCannotPublish`, `IsFeatured`,
`IsRecRoomApproved` bool, `BaseAvatarItemId` int?, `BaseAvatarItemColor`, `DesignFilename`,
`ThumbnailImageFilename` string, `CreatedAt`, `ModifiedAt` DateTime,
`PreviewOrientation` enum (`Front 0`, `Back 1`), `RankingContext` string, `OutfitType` int,
`CurrentSaves` array, `PurchaseInfo` object|null.

- `CurrentSaves[]` = 12 keys: `CustomAvatarItemSaveId` long, `CustomAvatarItemId` Guid,
  `UnityAssetId` Guid, `CreatedAt`, `ThumbnailFileName`, `AdditionalConfiguration`, `BodyType` int,
  `UnityAsset`, `UnityAssetHash`, `UnityAsset2`, `UnityAsset2Hash`, `OutfitType` int.
  Send `[]`, not null - callers iterate it.
- `PurchaseInfo` = the 10-key `ODENGGBLDCP`, see [econ-items-purchaseinfos-wire-shape](econ-items-purchaseinfos-wire-shape.md).

## Routes

| route | verb | send | response |
|---|---|---|---|
| `/v1/search?...` | GET | `HPBKMCLEANE<List<GICBMFJFHLI>>` | **bare array** |
| `/v1/featured` | GET | same | **bare array** |
| `/v1/bulk?customAvatarItemIds=...` | GET | same | **bare array** |
| `/v1` | POST | `HPBKMCLEANE<KGOJLHJNIOD<GICBMFJFHLI>>` | **ENVELOPED** `{Value, Success, Error, error_id}` |
| `/v1/design` | GET | `CJBFDPLCIEJ<MCEHDHECECM>` (nullable) | bare `{CreatorAccountId, BaseAvatarItemId, DesignFilename, BaseAvatarItemColor}` |
| `/v1/design` | PUT / DELETE | `CNDMDLNHDLI` | body ignored, any 2xx |

All the array routes are **required responses** - `{}` or an empty body throws `IONCMJIACFI`; serve
`[]`. Only `POST /v1` is enveloped, and its `KGOJLHJNIOD<T>.CPOBHIECLEN` raises `LLCLDPPAGIJ` on a
null envelope or `Success == false` ([llcldppagij-envelope-failure-exception](../conventions/llcldppagij-envelope-failure-exception.md)).

## `/v1/search` query params

`LINCNKPIJDN.PAOFLDLGHFK` `0x7C6F680`, error literal `'Unable to get searched Custom Avatar Items'`.
Keys (all via the query-param adder `ELHKHFJEHLM`):
`searchQuery`, `skip`, `take`, `creatorUsername`, `creatorAccountId`, `itemTypes`, `outfitTypes`,
`minPrice`, `maxPrice`, `isOwned`, `isFeatured`, `includeCoachItems`, `includePurchaseInfos`,
`ordering`, `unityAssetTarget`, `unityAssetVersion`.

`ordering` enum `PBFFECJMOHO`: `SearchScoreDescending 0`, `HotScoreDescending 1`, `Newest 2`,
`Oldest 3`, `PriceAscending 4`, `PriceDescending 5`, `FeaturedFirst 6`.
`itemTypes` enum `NEJIBLDMMMK`: `All -1`, `None 0`, `Shirt 1`.

**Search is NOT paged** - it returns a bare array, not `{Results, TotalResults}`. `skip`/`take` are
inputs only; the client infers "no more" from a short array.

## `POST /v1` (create) request

Not a JSON body: `metadata` is a **query param** carrying the serialized `KKOJBEFNMCA`
(`{Name, Description, Price, BaseAvatarItemId, BaseAvatarItemColor, Accessibility,
PreviewOrientation}`), plus two multipart file parts `thumbnailImage` then `design`, both with the
literal filename `file.bin`.
