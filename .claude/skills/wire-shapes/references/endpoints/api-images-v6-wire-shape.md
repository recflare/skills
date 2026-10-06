# Api images v6 wire shape

> GET api/images/v6/{imageId} AND GET api/images/v6?name= (svc 2 API) both return the SAME bare 13-key record .FFPCBIOBBNH, keyed `Id` (not `SavedImageId`). ⚠️ CORRECTED 2026-10-02 — the earlier version of this note described the adjacent typedef `GBJHBCMJBNP` and had the wrong key names, a nonexistent `ClubId`, and a missing `TaggedPlayerIds`.

Derived **2026-08-18**, **substantially corrected 2026-10-02** from build `20250718.01`.

## Two routes, one response type

| route | entry | path built from |
|---|---|---|
| `api/images/v6/{imageId}` | `HPJKKCCECLH.HDIOFDAGCPF` **`0x7CF53A0`** | `String.Format("{0}v6/{1}", "api/images/", id)` |
| `api/images/v6?name={name}` | `HPJKKCCECLH.MDCEPFFCKAA` **`0x7CF72C0`** | the whole-route literal `api/images/v6` + query param `name` |

Both are **GET** (`HttpMethod` statics `[rcx+8]`, e.g. `0x7CF5533` on the by-id route), service
**2 = API** (`mov r8d, 2` at `0x7CF5584`), and both send
**`MGPBDIAGCFD.HPBKMCLEANE<T>`** with generic inst **#1396 = `.FFPCBIOBBNH`** — a **bare object**, no
envelope. The by-id route takes **no query params** (no `ELHKHFJEHLM`); its only extra builder call is
`MGPBDIAGCFD.DIDJOECFJII` `0x7CF55C7`, the response-cache TTL.

⚠️ **The by-id path is `String.Format`-built from the shared prefix `api/images/`**, so grepping for
`api/images/v6/` finds nothing — the prefix literal (`0xD12D0B8`) is shared with
`{0}v5/player/{1}` and `{0}v1/{1}/report`. Only the `?name=` variant has a whole-route literal.

## Response — 13 keys

Formatter **`ENPHHCHIBOM`** `.ctor 0x7883230`, `____stringByteKeys` run `0x7883DDA`..`0x788416A` —
13 keys, 1:1 with the 13 declared fields of typedef **#22013**:

| # | key | CLR | off |
|---|---|---|---|
| 1 | **`Id`** | long | 0x10 |
| 2 | `ImageName` | string | 0x18 |
| 3 | `Description` | string | 0x20 |
| 4 | `PlayerId` | **int** | 0x28 |
| 5 | `RoomId` | `long?` | 0x30 |
| 6 | `PlayerEventId` | `long?` | 0x40 |
| 7 | `Accessibility` | enum `OKEAJPFBMGI` | 0x50 |
| 8 | `AccessibilityLocked` | bool | 0x54 |
| 9 | **`Type`** | enum `BJFECDCCOPG` | 0x58 |
| 10 | `CreatedAt` | DateTime | 0x60 |
| 11 | **`TaggedPlayerIds`** | `IReadOnlyList<int>` (inst #16662) | 0x68 |
| 12 | `CheerCount` | int | 0x70 |
| 13 | `CommentCount` | int | 0x74 |

```json
{ "Id": 89, "ImageName": "image/2026-10-02/....jpg", "Description": null,
  "PlayerId": 205, "RoomId": null, "PlayerEventId": null,
  "Accessibility": 1, "AccessibilityLocked": false, "Type": 1,
  "CreatedAt": "2026-10-02T00:00:00Z", "TaggedPlayerIds": [],
  "CheerCount": 0, "CommentCount": 0 }
```

`OKEAJPFBMGI` **Accessibility**: `Private 0`, `Public 1`, `FriendsOnly 2`.
`BJFECDCCOPG` **Type**: `None 0`, `ShareCamera 1`, `OutfitThumbnail 2`, `RoomThumbnail 3`,
`ProfileThumbnail 4`, `InventionThumbnail 5`, `PlayerEventThumbnail 6`, `RoomLoadScreen 7`.

`{}` deserializes (every key omittable) but an **empty body** throws `IONCMJIACFI`.

## The hook is a normalizer, not a validator

`FFPCBIOBBNH.CPOBHIECLEN` **`0x7CE6720`** is *not* the shared `0xA60520` stub, but it does not throw.
It tests `HasValue` on exactly **two** nullables and replaces a missing one with `0`:

```
cmp byte [rbx+0x30], 0   ; RoomId.HasValue        -> if false, RoomId        = 0   (0x7CE6751)
cmp byte [rbx+0x40], 0   ; PlayerEventId.HasValue -> if false, PlayerEventId = 0   (0x7CE677F)
ret                                                                               (0x7CE67AA)
```

So omitting `RoomId`/`PlayerEventId` is safe and they arrive as `0`, not `null`. This remains the
concrete counter-example to "any RVA other than the shared stub means real validation" — always
disassemble the hook. (`MIBODHPEFHP.CPOBHIECLEN` at `0xFEA4F0` is the other kind: its own `nop; ret`.)

**Why `[obj+0x30]` is the HasValue test:** `Nullable<T>` in IL2CPP is laid out
`{bool hasValue; T value}` — hasValue **first**. `cmp byte [obj+0x30], 0` on a `long?` field at 0x30
tests HasValue, not the low byte of the value. Getting this backwards inverts every nullable check.

## ⚠️ What the 2026-08-18 version got wrong, and why

| claim then | actually |
|---|---|
| type `GBJHBCMJBNP` | **`FFPCBIOBBNH`** — `GBJHBCMJBNP` is typedef **#22012**, the adjacent type used by `RecRoom.Sharing.PhotoCode.Create` |
| first key `SavedImageId` | **`Id`** |
| keys included `ClubId` and `SavedImageType` | **neither exists**; key 9 is `Type` and there is no `ClubId` |
| no `TaggedPlayerIds` | key 11 is `TaggedPlayerIds`, an `IReadOnlyList<int>` |
| `Description` after `PlayerEventId` | `Description` is key **3**, before `PlayerId` |
| formatter `BODPFLOJAIK` `0x78808B0` | `BODPFLOJAIK`'s own run is the 2-key `{SavedImageId, Cheer}`; the real formatter is `ENPHHCHIBOM` `0x7883230` |
| hook normalizes **3** nullables | it normalizes **2** |

Both mistakes have the same cause and are worth guarding against generally:

1. **Adjacent typedefs with near-identical shapes.** #22012 and #22013 are both 13-field image-ish
   records. Confirm the type from the **send's generic inst** (`ginst.py inst <n>`), never from a
   plausible nearby name.
2. **`names.py` run with a length that overruns the method.** Formatter `.ctor`s sit back to back, so
   an over-long window silently splices the next formatter's keys onto the end of the run. Get the
   method length from `methods.pkl` first (here `ENPHHCHIBOM..ctor` is `0x10A0`) and pass it.

## Related, but not this JSON

The content-signature check that stalls mirrored images
([image-content-signature-bypass](../../../rr-client-bringup/references/image-content-signature-bypass.md), `HPJKKCCECLH.BLDFMLMAFLH` at `0x7CF32F0`) lives on this
same class but is on the **image fetch**, not this metadata response.

Siblings on the `api/images/` prefix: `{0}v5/player/{1}` (`BOBMJOCPBBK.MFOKICBLFKO` `0x7CDFC00` and
`HPJKKCCECLH.FAEGHDFDLNM` `0x7CF45E0`, both with a `sort` param) and `{0}v1/{1}/report`
(`HPJKKCCECLH.HGFICBPHMLD` `0x7CF5790`). Whole-route literals: `api/images/v1/cheer`,
`/v1/deletesaved`, `/v1/listsaved`, `/v1/modifydescription`, `/v1/sendlink`, `/v1/slideshow`,
`/v2/modifyaccessibility`, `/v2/named`, `/v4/uploadsaved`, `/v5/bulk`, `/v5/cheered/bulk`.
