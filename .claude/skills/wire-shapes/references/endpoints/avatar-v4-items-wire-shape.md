# Avatar v4 items wire shape

> GET api/avatar/v4/items (svc 28 Econ) takes NO params and returns a BARE ARRAY of the 10-key BGJHOEKDNED — the player's OWNED/unlocked avatar items. Cross-build diff: `ThumbnailImage` and `CreatedAt` are NEW in the 2025 build; the other 8 keys and both enums are unchanged.

Derived **2026-09-15** from build `20250718.01`, diffed against the pre-2025 client.
Shares its element DTO with [avatar-lockeditems-bulk](avatar-lockeditems-bulk-wire-shape.md) (which has the same
table); this note pins the `v4/items` route itself and the **cross-build delta**.

`GET https://econ.<host>/api/avatar/v4/items` — service **28 = Econ** (`mov r8d, 0x1c` at
`0x7D00085`), verb **GET** (`HttpMethod` statics `[rcx+8]` at `0x7D00062`). Client entry
`OGAEDNMDDLF.GKPNEOBMMGN` `0x7CFFF80` (+0x1b0).

**No parameters, no body** — no `ELHKHFJEHLM` and no `ELKIBCPINAP` call; the bearer token identifies
the player.

⚠️ **Two existing notes contradict each other on what this route means** (flagged 2026-09-15).
[avatar-lockeditems-bulk](avatar-lockeditems-bulk-wire-shape.md) calls it "the full baked-in avatar-item catalogue",
with ownership decided separately by `api/playeritems/v1/isavataritemowned/bulk`;
[giftdropstore-storefront-type](giftdropstore-storefront-type.md) calls it "the player's owned/unlocked avatar items".
**The structural evidence favours the catalogue reading**: the same facade `OGAEDNMDDLF` also serves
`api/avatar/v1/defaultbaseavataritems`, `/defaultunlocked`, `/lockeditems` and `/lockeditems/bulk`,
all returning the *same* `List<BGJHOEKDNED>` — a `defaultunlocked` and a `lockeditems` route only
make sense if `v4/items` is the full set, and ownership has its own `isavataritemowned` route. That
is inference from the route family, **not** a consumer-side proof; it has not been confirmed by
reading what the client does with the result, so treat it as unresolved.

## Response — BARE ARRAY, no envelope

`HPBKMCLEANE<T>` generic inst `#91389` = **`List<BGJHOEKDNED>`** — the `List` directly. `{}` or an
empty body throws `IONCMJIACFI`; serve `[]`
([nonobject-response-routes](../conventions/nonobject-response-routes.md)).

Element `BGJHOEKDNED` (10 declared fields, 10 keys), formatter **`KLBAEFOPOFB`** `.ctor 0x76CA880`
(+0xd40), `____stringByteKeys` run `0x76CB1E2..0x76CB491`:

| # | key | CLR | off | |
|---|---|---|---|---|
| 1 | `AvatarItemType` | `NHKFIOBDEOB` enum | 0x10 | `Outfit 0`, `HairDye 1`, `CustomOutfit 2` |
| 2 | `AvatarItemDesc` | string | 0x18 | the payload |
| 3 | `FriendlyName` | string | 0x20 | |
| 4 | `Tooltip` | string | 0x28 | |
| 5 | `Rarity` | `LCEGHIAIKNO` enum | 0x30 | `None -1`, `Common 0`, `Uncommon 10`, `Rare 20`, `Epic 30`, `Legendary 50` |
| 6 | `TagList` | string | 0x38 | **a STRING, not an array** |
| 7 | `AvatarItemId` | int | 0x40 | |
| 8 | `IsBaseAvatarItem` | bool | 0x44 | |
| 9 | **`ThumbnailImage`** | string | 0x48 | **NEW in 2025** |
| 10 | **`CreatedAt`** | DateTime | 0x50 | **NEW in 2025** — Utf8Json ISO-8601 |

## Cross-build diff — what is actually new in 2025

The same DTO in the **pre-2025** client (`recflare/GameAssembly.dll`, 156,069,888 bytes) is
`EDDPDJCKOBH.JBANAMGBBAP`, formatter `PKMKMONGFID` `.ctor 0x33CC7D0` (+0x7f0), whose key run holds
**8 keys** and stops at `IsBaseAvatarItem`:

```
AvatarItemType AvatarItemDesc FriendlyName Tooltip Rarity TagList AvatarItemId IsBaseAvatarItem
```

So 2025 **appends exactly two keys — `ThumbnailImage` and `CreatedAt`** — and changes nothing else.
The DTO mapping is unambiguous in both directions: `IsBaseAvatarItem` is referenced by exactly one
formatter `.ctor` in each build (3 refs in `PKMKMONGFID` at `0x88868F0`, 3 in `KLBAEFOPOFB` at
`0xD1DC940`), so there is only one avatar-item DTO per build to compare.

**Both enums are unchanged.** The pre-2025 `EDDPDJCKOBH.NIEKOAENMLL` is `Outfit 0 / HairDye 1 /
CustomOutfit 2` and `DOOBOJIHNDF` is `None -1 / Common 0 / Uncommon 10 / Rare 20 / Epic 30 /
Legendary 50` — identical member names *and* values to the 2025 enums. No enum member was added.

> **Method note: diff the formatter's key run, not the string-literal pool.** `"CreatedAt"` *does*
> occur in the pre-2025 literal pool (other DTOs use it), so a pool grep would have wrongly called it
> old. Conversely `"ThumbnailImage"` is absent from the pool, and the `"thumbnailImage"` camelCase
> literal that *is* present belongs to the `customAvatarItems` POST multipart part name
> ([customavataritems-routes](customavataritems-routes-wire-shapes.md)), not to a key — a real Utf8Json key emits every
> casing, and `"thumbnailimage"` is absent. Only the `____stringByteKeys` run settles it.

## No validation

Nothing throws on partial data — omit either new key and it defaults (`null` / `default(DateTime)`).
Serving the pre-2025 8-key shape to the 2025 client is therefore **safe**: the two new keys simply
read as empty.
