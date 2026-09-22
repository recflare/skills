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
| `/v1/bulk` | **POST** (see correction below) | same | **bare array** |
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

`outfitTypes` is **`IEnumerable<int>`, not a typed enum parameter** (method signature:
`IEnumerable<int> AIBHDDKBJGE`), so it is repeatable — `outfitTypes=101&outfitTypes=105` — and the
server must accept a *list*, not one value. The ints are **`RecRoom.Avatars.OutfitType`** (typedef
#56729, **unobfuscated**, 19 members), banded by body region:

| band | members |
|---|---|
| head | `None -1`, `Hat 0`, `Hair 2`, `Ear 3`, `Eye 10`, `Beard 20` |
| torso | `Shoulder 100`, `Shirt 101`, `Waist 102`, `Neck 103`, `TeamJersey 104`, **`CustomShirt 105`** |
| arms | `Wrist 200`, `TeamWrist 203` |
| legs | `Legs 300`, `Feet 301` |
| Roomie | `Roomie_Hat 500`, `Roomie_Waist 501`, `Roomie_Eye 502` |

Do not confuse it with `itemTypes` above — that is the 3-member `NEJIBLDMMMK` whose `Shirt` is `1`,
whereas an `OutfitType` shirt is `101` and a *custom* shirt is `105`. The two `Shirt`s are different
numbers in different enums, and a typical custom-item search sends `itemTypes=-1` (All) together
with `outfitTypes=105` (CustomShirt).

**Search is NOT paged** - it returns a bare array, not `{Results, TotalResults}`. `skip`/`take` are
inputs only; the client infers "no more" from a short array.

## `POST /v1` (create) request

Not a JSON body: `metadata` is a **query param** carrying the serialized `KKOJBEFNMCA`
(`{Name, Description, Price, BaseAvatarItemId, BaseAvatarItemColor, Accessibility,
PreviewOrientation}`), plus two multipart file parts `thumbnailImage` then `design`, both with the
literal filename `file.bin`.


## ⚠️ CORRECTION 2026-09-16 — `/v1/bulk` is POST with a FORM BODY, not GET with query params

The routes table above previously read `/v1/bulk?customAvatarItemIds=... | GET`. **Both halves were
wrong.** Verified on `FBPHDFLFDFN$$MoveNext` `0x7C5B9A0` (+0x8a0), the `api/customAvatarItems/v1/bulk`
state machine:

```
0x7C5BCE3  mov rax, [rip+…]      ; TypeInfo = System.Net.Http.HttpMethod
0x7C5BCEA  mov rcx, [rax + 0x90] ; static fields
0x7C5BCF1  mov r14, [rcx + 0x20] ; +0x20 = POST      <-- not +0x08 (Get)
0x7C5BD1D  mov r8d, 2            ; service 2 = API
0x7C5BD23  mov rdx, r14          ; -> AKJEAMCCEOH..ctor(HttpMethod, service, path)
```

Because the verb is POST, its **five `ELHKHFJEHLM` calls put the parameters in an
`application/x-www-form-urlencoded` BODY**, not the query string
([elhkhfjehlm-verb-dependent-params](../conventions/elhkhfjehlm-verb-dependent-params.md)) — there is **no `ELKIBCPINAP` call**, so the body is
form-encoded, not JSON.

```
POST https://api.<host>/api/customAvatarItems/v1/bulk
Content-Type: application/x-www-form-urlencoded

customAvatarItemIds=<guid>&customAvatarItemIds=<guid>&includePurchaseInfos=True&unityAssetTarget=0&unityAssetVersion=3
```

`customAvatarItemIds` values are **`System.Guid`** (param generic inst #322) and the key is
**repeated once per id**. Response is unchanged: `HPBKMCLEANE<List<GICBMFJFHLI>>` (inst #2718) —
a **bare array** of the 20-key DTO, so `{}` throws `IONCMJIACFI`; serve `[]`.

**`/v1/search` really is GET** (`[rcx+8]` at `0x7C6F8E2`), so its params are genuine query params.
The two sibling routes differ in verb, and therefore in where their parameters live — a server that
routes `GET /api/customAvatarItems/v1/bulk` will never be called.
