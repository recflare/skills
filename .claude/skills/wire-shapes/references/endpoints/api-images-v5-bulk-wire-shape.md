# `api/images/v5/bulk` — a BARE ARRAY of 13-key `SavedImageDTO`, keyed `SavedImageId`

> `GET api/images/v5/bulk?ids=<id>[&…]` (svc **2 API**) deserializes into
> **`List<SavedImageDTO>`** — a **bare JSON array**, no envelope, no wrapper object.
> ⚠️ **This is NOT the `images/v6` DTO.** `v6` returns a *different* 13-key type keyed **`Id`**
> ([api-images-v6](api-images-v6-wire-shape.md)); `v5/bulk` is keyed **`SavedImageId`** and
> carries `ClubId`, which `v6` does not. Reusing one shape for the other silently yields rows of
> zeros.
> ⚠️ **The verb depends on the id count** — `< 100` ids ⇒ **GET** with a query string, `>= 100` ids
> ⇒ **POST** with the ids in a form body.

Derived **2026-10-22** from build `20260323.14`.

## Route

Client entry is the state machine **`<GetSavedImagesById>d__71$$MoveNext`** `0x94B4450` — the
compiler-generated name survives obfuscation, so the original method is
`GetSavedImagesById(IReadOnlyList<long> imageIds, CancellationToken)`.

| what | value | evidence |
|---|---|---|
| path | `api/images/v5/bulk` | literal **`0xFC4D3F0`**, `mxref` = exactly **2** refs, both in this method (`0x94B4516`, `0x94B45E6`) |
| service | **2 = API** | `mov r8d, 2` at `0x94B45EB`, into the request `.ctor` at `0x94B45F7` |
| verb | **GET** or **POST**, count-dependent | see below |
| params | **`ids`** only | literal at `0x94B4610`, added at `0x94B461A` |
| response | **`List<SavedImageDTO>`** | `<>t__builder` is `AsyncTaskMethodBuilder<List<SavedImageDTO>>` (and `<>u__1` is `TaskAwaiter<List<SavedImageDTO>>`) |

### The verb is chosen from the number of ids

```
0x94b4550  r8 = [rbx+0x20]          ; imageIds  (struct offset; class offset 0x30)
0x94b4566  call <iface>             ; -> eax ; test eax,eax / je 0x94b46cd  -- EMPTY LIST: no request at all
0x94b4589  call <iface>             ; -> eax = id count
0x94b4595  cmp eax, 0x64            ; 100
0x94b4598  jge 0x94b45b4
0x94b45aa  call 0x2026e60           ; [HttpMethod statics + 0x08] = GET     (count < 100)
0x94b45c4  call 0x2026eb0           ; [HttpMethod statics + 0x20] = POST    (count >= 100)
```

Both getters read `[klass+0x20]` then the fixed `HttpMethod` static slot — `+0x08` Get, `+0x20` Post
(the standard offset table). The path, the `ids` parameter and the response type are **identical**
on both branches; only the verb changes. Per
[elhkhfjehlm-verb-dependent-params](../conventions/elhkhfjehlm-verb-dependent-params.md) the shared
parameter-adder puts `ids` in the **query string on GET** and in an
**`application/x-www-form-urlencoded` body on POST**, so a server that only reads the query string
will see zero ids once a caller asks for 100+ images.

⚠️ **An empty `imageIds` short-circuits before the request is built** (`je 0x94b46cd` above), so an
absent HTTP request is not evidence the route is broken.

## Response: bare `List<SavedImageDTO>`

`Task<List<SavedImageDTO>>` is the **plain tier** — bare value, no envelope
([2026-send-helper-tiers](../conventions/2026-send-helper-tiers.md)). The top-level body is a JSON
**array**:

```json
[{"SavedImageId":29466,"ImageName":"…","PlayerId":1,"RoomId":null,"PlayerEventId":null,
  "ClubId":null,"Description":"","Accessibility":1,"AccessibilityLocked":false,
  "SavedImageType":1,"CreatedAt":"2026-10-14T12:00:00Z","CheerCount":0,"CommentCount":0}]
```

⚠️ **`{}` or `{"Value":[…]}` throws** `IONCMJIACFI` "Malformed Response" — this is one of the
non-object routes ([ioncmjiacfi-malformed-response](../conventions/ioncmjiacfi-malformed-response.md)).
`[]` is valid and safe.

### `SavedImageDTO` (typedef #22227) — 13 fields, 13 wire keys, no renames

Formatter **`Utf8Json.Formatters.RecNet.HPHNIEJFNMW`** `.ctor` **`0x9373240`**, confirmed by
`msig` (`Serialize(JsonWriter, .SavedImageDTO, …)`). `____stringByteKeys` runs `0x9373984`…`0x9373B68`
in exactly declaration order:

| # | key | CLR | off | notes |
|---|---|---|---|---|
| 1 | `SavedImageId` | long | 0x10 | **not** `Id` — that is the v6 DTO |
| 2 | `ImageName` | string | 0x18 | the CDN object name |
| 3 | `PlayerId` | **int** | 0x20 | int, not long |
| 4 | `RoomId` | `long?` | 0x28 | nullable → **optional** |
| 5 | `PlayerEventId` | `long?` | 0x38 | nullable → **optional** |
| 6 | `ClubId` | `long?` | 0x48 | nullable → **optional**; **absent from the v6 DTO** |
| 7 | `Description` | string | 0x58 | |
| 8 | `Accessibility` | `.SavedImageAccessibility` | 0x60 | enum, **numeric** |
| 9 | `AccessibilityLocked` | bool | 0x64 | |
| 10 | `SavedImageType` | `.SavedImageType` | 0x68 | enum, **numeric** |
| 11 | `CreatedAt` | `DateTime` | 0x70 | non-nullable; omit ⇒ `DateTime.MinValue` |
| 12 | `CheerCount` | int | 0x80 | |
| 13 | `CommentCount` | int | 0x84 | |

No `[DataMember]` renames and no key-less members — 13 backing fields, 13 keys. Every key accepts
the usual three Utf8Json casings (e.g. `SavedImageId` / `savedImageId` / `savedimageid`).

Enums are **numbers on the wire**: no member name of either enum exists as a string literal in the
build, so there is no by-name formatter.

```
.SavedImageAccessibility (typedef #22240) : int    Private 0 · Public 1 · FriendsOnly 2
.SavedImageType          (typedef #22241) : int    None 0 · ShareCamera 1 · OutfitThumbnail 2 ·
                                                   RoomThumbnail 3 · ProfileThumbnail 4 ·
                                                   InventionThumbnail 5 · PlayerEventThumbnail 6 ·
                                                   RoomLoadScreen 7
```

## Post-deserialize hook: normalizes the three nullables to 0, and nothing else

`SavedImageDTO.EMSIIQRWASQ` **`0x94B31F0`** is the **sync** hook (`RTSPZODLERY.EMSIIQRWASQ` runner —
see [featuredrooms-current](featuredrooms-current-wire-shape.md) for the 2026 sync/async hook split).
It is 0xB4 bytes, has **no throw and no validation**, and does exactly three identical things:

```
if (!RoomId.HasValue)        RoomId        = 0;   ; byte test [this+0x28] -> write 16B
if (!PlayerEventId.HasValue) PlayerEventId = 0;   ; byte test [this+0x38]
if (!ClubId.HasValue)        ClubId        = 0;   ; byte test [this+0x48]
```

(IL2CPP `Nullable<T>` puts `hasValue` **first**, hence the byte test at the field's own offset.)

➡️ **There is no hard requirement on this route.** Omitting `RoomId`/`PlayerEventId`/`ClubId` is
identical to sending `0`, and a row with only the four non-nullable scalars parses. Still send all
13 keys: an omitted number is indistinguishable from a wrong one, and the client filters on these
values downstream.

## Sibling routes sharing these types

- `api/images/v5/cheered/bulk` (literal `0xFC4D4F8`) — separate route, **not** derived here.
- `api/images/v6` / `?name=` — **different DTO**, see [api-images-v6](api-images-v6-wire-shape.md).
- `SavedImageCheerDTO` (formatter `TNWUPWSIEGF` `0x937D760`), `SlideshowImageDTO` (`SZJFJETHHAP`
  `0x937CF00`) and `ImageCheerRequestDTO` (`NZGTLPTHOAL` `0x937BFD0`) all also reference the
  `SavedImageId` key literal — that is why key-literal intersection alone cannot pick the formatter
  here, and `msig` on the candidate class is what settles it.
