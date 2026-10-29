# `GET rooms/hot` — paged `{Results, TotalResults}` of the 44-key `RoomDTO`

> **`rooms/hot`** (svc **16 Rooms**) returns the **paged wrapper**
> `RecNet.Common.ODFPVNYWDAJ<RecNet.Rooms.RoomDTO>` = **`{"Results": [...], "TotalResults": <long>}`**
> — **not** a bare array. The element is the flat **44-key `RoomDTO`**, which is a *different, smaller*
> type than the 63-key DTO that `GET rooms/{id}?include=` returns.
> ⚠️ `RoomDTO` has **no `SubRooms`, `Roles`, `DataBlob`, `DataBlobHash`, `Tags` or `Scenes` keys.**
> If the server reuses the room-by-id serializer here, every one of those is parsed and **silently
> discarded** — pure wasted bandwidth.
> ⚠️ **`TotalResults` is a `long`** on this wrapper, not the `int` the 2025 econ note records.

Derived **2026-10-23** from build `20260323.14`.

## Route

Facade **`RecNet.Rooms.DFMBMRNABHU.DVEQVZCPJON`** **`0x95ABA80`** (spans to `0x95ABC10`):

```
Task<RecNet.Common.ODFPVNYWDAJ<RecNet.Rooms.RoomDTO>> DVEQVZCPJON(
    IReadOnlyList<string> a,        // tag filter
    int b, int c,                   // skip / take
    Nullable<Guid> d,
    CancellationToken e)
```

| what | value | evidence |
|---|---|---|
| path | `rooms/hot` | literal **`0xFD5DAC8`**, `mxref` = exactly **2** refs, both in this method (`0x95ABAEB` init `lea`, `0x95ABBD0` use `mov`) |
| service | **16 = Rooms** | consistent with the `rooms.<host>` subdomain; **not** re-read off the request `.ctor` — see caveat |
| response | `ODFPVNYWDAJ<RoomDTO>` | the `AsyncTaskMethodBuilder<T>` on the state machine, confirmed by `msig` |

⚠️ **The verb and the query-parameter names are not pinned.** The method's only literals are the two
`rooms/hot` refs — it builds a closure (`[+0x10]` = the tag list, `[+0x18]` / `[+0x1c]` = the two
ints, `[+0x20]`..`[+0x30]` = the `Guid?`) and hands a delegate to the send builder, so the request
`.ctor` and the param adds happen in a compiler-generated class that `callxref` cannot reach
(`DVEQVZCPJON` itself has **0 direct call sites** — its stub is inlined into an interface-dispatched
wrapper). GET is the safe assumption from the URL form, but if it is not a GET then
[elhkhfjehlm-verb-dependent-params](../conventions/elhkhfjehlm-verb-dependent-params.md) applies and
`skip`/`take`/tags ride a form body instead of the query string.

## Response

```json
{
  "Results": [
    {
      "RoomId": 1162, "Name": "RawName", "FriendlyName": "Sanitized Name",
      "Description": "", "ImageName": "", "WarningMask": 0, "CustomWarning": null,
      "CreatorAccountId": 1, "State": 0, "Accessibility": 1, "PublishState": 0,
      "SupportsLevelVoting": false, "IsRRO": false,
      "SupportsScreens": true, "SupportsWalkVR": true, "SupportsTeleportVR": true,
      "SupportsVRLow": true, "SupportsQuest2": true, "SupportsMobile": true,
      "SupportsJuniors": true,
      "AgeRating": 0, "MinLevel": 0,
      "CreatedAt": "2026-10-23T00:00:00Z", "PublishedAt": null,
      "Stats": { "CheerCount": 0, "FavoriteCount": 0, "VisitorCount": 0, "VisitCount": 0 },
      "RankingContext": null, "IsDorm": false,
      "MaxPlayerCalculationMode": 0, "MaxPlayers": 20, "PersistenceVersion": 0,
      "CloningAllowed": false, "DisableMicAutoMute": false, "DisableRoomComments": false,
      "EncryptVoiceChat": false, "LoadScreenLocked": false,
      "UgcVersion": 2, "IsDeveloperOwned": false, "IsJuniorCreated": false,
      "CCU": null, "IsRecRoomApproved": false, "ExcludeFromLists": false,
      "UgcSubVersion": null, "MinUgcSubVersion": null, "BoostCount": 0
    }
  ],
  "TotalResults": 1
}
```

### `RecNet.Common.ODFPVNYWDAJ<T>` (typedef #46720) — the paged wrapper

| # | key | CLR | field |
|---|---|---|---|
| 1 | `Results` | `IReadOnlyList<T>` | `YBUVFRPZVHC` |
| 2 | `TotalResults` | **long** | `TQQRUZIYSIW` |

The key names come from the already-derived sibling routes that use the same generic
([econ-customavataritems-owned](econ-customavataritems-owned-wire-shape.md),
[custom-badges-2026](custom-badges-2026-wire-shapes.md)); the **`long`** width is read off
`ftypes.py` on 2026.

⚠️ **This wrapper declares an `IULRMJBAHPG` async post-deserialize hook**, which is
**not derived** — it is generic-shared and has no metadata-usage slot, so whether it rejects
`Results: null` is unknown. **Send `[]`, never `null`.**

### `RecNet.Rooms.RoomDTO` (typedef #23494) — 44 wire keys

Formatter **`Utf8Json.Formatters.RecNet.Rooms.PDOBGOIZODY`** `.ctor` **`0x8F04FE0`**, confirmed by
`msig` (`Serialize(JsonWriter, RecNet.Rooms.RoomDTO, …)`). `____stringByteKeys` is the trailing
single-casing run `0x8F06750`…`0x8F06ECA`, in declaration order.

**44 keys against 45 instance fields** (47 total minus the two statics `DefaultImageName` and
`INVALID_ROOM_ID`). The pairing is 1:1 by position and type with exactly one gap: **`UPYHLYAVEUS`
(string, between `CCU` and `IsRecRoomApproved`) carries no wire key** — it is
`[IgnoreDataMember]`'d or computed, and `fields2025.py` confirms it with **offset `0x0000`** while
its neighbours run `0xe8` → `0xf0`.

Three `Obscured*` fields are plain JSON scalars on the wire (no formatter exists for them):
`DLARUBZJWEL` (`ObscuredLong`) = **`RoomId`**, `LMJQJTTKKNR` (`ObscuredInt`) =
**`CreatorAccountId`**, `CNXXPRECRMO` (`ObscuredBool`) = **`IsRRO`**, `LRZCCSZAVOX` (`ObscuredBool`)
= **`CloningAllowed`**.

Note the two name keys are **swapped relative to intuition**: wire `Name` ← field `RawName`, wire
`FriendlyName` ← field `SanitizedFriendlyName`.

Nullable → **optional**: `PublishedAt` (`DateTime?`), `CCU` (`int?`), `UgcSubVersion` (`int?`),
`MinUgcSubVersion` (`int?`). Everything else is non-nullable and takes its CLR default when omitted.

`Stats` is the nested 4-int **`RecNet.Rooms.UserInteractionStatisticsDTO`**:
`CheerCount`, `FavoriteCount`, `VisitorCount`, `VisitCount`.

Enums are **numeric**: `WarningMask`, `ModerationState`, `Accessibility`, `RoomPublishState`,
`UgcAgeRating`, `MaxPlayerCalculationMode`. `UgcVersion` is a plain **byte**.

## Is this "too much data"?

44 keys is roughly **800–1000 bytes of JSON per room** in Original casing (the key names alone are
~700 bytes of overhead before values), so a 20-room page is ~16–20 KB. That is not the problem. The
two things actually worth checking:

1. **Keys the client does not have.** Utf8Json **drops unknown members silently**, so anything from
   the richer room-by-id DTO — `SubRooms`, `Roles`, `DataBlob`, `DataBlobHash`, `Tags`, `Scenes`,
   `CreatorPlayerId` — is parsed and thrown away. If the server shares one room serializer across
   both routes, this is free bandwidth to reclaim with **zero** client-visible effect.
2. **`Description`**, which is unbounded and is the only large free-text field in the element. A
   hot-list card does not need it.

### Trimming is risky, because an omitted key is indistinguishable from a false one

**Safe to omit** (nullable, and `null` is the benign value):
`PublishedAt`, `UgcSubVersion`, `MinUgcSubVersion`, `CustomWarning`, `RankingContext`.
`CCU` is also nullable but it is the live-player count the card renders, so omitting it blanks the
badge.

**`MinUgcSubVersion` is specifically proven safe.** `RRUI.Data.RoomModel.get_HasSufficientVersion`
`0x283CFF0`:

```
0x283d0fb  movzx esi, byte ptr [rax+0xe4]   ; UgcVersion
0x283d146  call  r9                          ; -> client's supported sub-version for that UgcVersion
0x283d160  mov   rcx, qword ptr [rcx+0xfc]  ; MinUgcSubVersion (Nullable<int>)
0x283d178  call  ...                         ; Nullable<int>.GetValueOrDefault()
0x283d17d  cmp   edi, eax                    ; supported >= required ?
```

`GetValueOrDefault()` turns `null` into **0**, which always passes. This feeds
`HideIfRoomIsPlayableInCurrentVersionUpdateToPlayImpl.ShouldHide` `0x2864270`, so a wrong value here
**hides the room from the list** with no error — but `null` or `0` never does.

**Not safe to omit** — each defaults to `false`/`0` and silently changes behaviour:

| key | omitting it means |
|---|---|
| `UgcVersion` | **0**, the wrong version lane. This is the field that caused the silent-render bug in [inventions-v2-mine](inventions-v2-mine-wire-shape.md); it pairs with `MinUgcSubVersion` in the gate above |
| the 7 `Supports*` flags | the room claims it supports **no** platform, so it reads as unplayable on the player's device |
| `SupportsJuniors` | junior accounts cannot see it |
| `Accessibility`, `State`, `PublishState` | moderation/visibility lane 0 |
| `MaxPlayers` | a 0-capacity room |
| `ImageName`, `Name`, `FriendlyName`, `RoomId` | blank card |
| `AgeRating`, `MaxPlayerCalculationMode`, `MinLevel` | 0 |

`ExcludeFromLists` and `IsRecRoomApproved` are server-side filters by intent — the server should be
*applying* them, not relying on the client to.

➡️ **Verdict: send all 44 keys, drop anything that is not one of them, and shorten or omit
`Description`.** The element is already the lean DTO; the win is in not over-serving it and in
honouring `take`.
