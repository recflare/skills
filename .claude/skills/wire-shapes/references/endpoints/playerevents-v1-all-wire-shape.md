# Playerevents v1 all/{accountId} wire shape

> GET api/playerevents/v1/all/{accountId} (svc 2 API) takes NO params and returns a BARE OBJECT {Created, Responses} — Created is a list of the 17-key v1 PlayerEvent, Responses is a list of {PlayerEvent, PlayerEventResponse} PAIRS. Every post-deserialize hook in the tree is null-tolerant.

Derived **2026-09-30** from build `20250718.01`.

> ⚠️ **There is a second, id-less route with almost the same path.** `api/playerevents/v1/all` (no
> trailing segment) is a **separate literal and separate facade method** — the local player's own
> events, `GetLocalPlayerEventInfo` — documented in
> [playerevents-v1-all-local](playerevents-v1-all-local-wire-shape.md). Same response DTO, no id.
> That note also records the **2026** differences that apply to *this* route too: the facade was
> rewritten (`RecNet.Events.BFKPNJRKYIX` + a `RecNet.Events.Client` cache layer), the DTOs are now
> unobfuscated, **the four null-tolerant hooks below are gone on 2026**, and `Responses: null`
> therefore **throws** there. Treat the "all four hooks are null-tolerant" section as 2025-only.
Siblings: [playerevents-v1-room](playerevents-v1-room-wire-shape.md), [playerevents-v1-responses](playerevents-v1-responses-wire-shape.md),
[playerevents-v2](playerevents-v2-wire-shape.md), [playerevent-tags-build-difference](playerevent-tags-build-difference.md).

`GET https://api.<host>/api/playerevents/v1/all/{accountId}` — service **2 = API** (facade
`BPHIJNEOCMK`), verb **GET** (`HttpMethod` statics `[rcx+8]` at `0x7E423B5`).

Path is `String.Format("api/playerevents/v1/all/{0}", accountId)` — literal slot **`0xD13E1C8`**; the
id is a **path segment**. **No params, no body.**

Client entry **`BPHIJNEOCMK.ADNCCKFNPOB`** `0x7E42300`. The literal is also referenced by
**`<<GetRemotePlayerEventList>b__0>d.MoveNext`** `0x7E563E0` — a compiler-generated wrapper whose
**unobfuscated** name confirms the route's purpose.

## Response — BARE OBJECT, no envelope

Send helper is **`BPHIJNEOCMK.LMKONLJOAEP<T>`** — the facade's description-less (bare) helper, so no
envelope ([playerevents-v1-room](playerevents-v1-room-wire-shape.md) has the bare-vs-enveloped rule). Generic inst
**#2811** = **`.CPHNJLLFJEB`**, a 2-key wrapper; formatter `IOBJLKGGGFH` `.ctor 0x7724D60`:

| # | key | CLR |
|---|---|---|
| 1 | `Created` | `List<NEMBNIGCMFK>` (generic inst #2737) |
| 2 | `Responses` | `List<HALOCGHCLFE>` (generic inst #25608) |

```json
{ "Created":   [ { …PlayerEvent… } ],
  "Responses": [ { "PlayerEvent": { …PlayerEvent… },
                   "PlayerEventResponse": { "PlayerEventResponseId": 900001, "PlayerEventId": 134,
                                            "PlayerId": 205, "CreatedAt": "2026-01-01T00:00:00Z",
                                            "Type": 0 } } ] }
```

`{}` deserializes fine (both keys omittable), but an **empty body** throws `IONCMJIACFI`.

`HALOCGHCLFE` is the pair type, formatter `HAJFBEJGGLM` `.ctor`, 2 keys **`PlayerEvent`** /
**`PlayerEventResponse`** — the second is the 5-key `DHOECFANGJN` RSVP record documented in
[playerevents-v1-responses](playerevents-v1-responses-wire-shape.md), ⚠️ including its `Type` trap where **`Yes` is `0`**.

## The v1 PlayerEvent — `.NEMBNIGCMFK`, 17 keys

Formatter **`CLAPAFCIEHB`** `.ctor 0x7709A30`, key run ending `0x770AEE2` — 17 keys, 1:1 with the 17
declared fields:

| # | key | CLR | off |
|---|---|---|---|
| 1 | `PlayerEventId` | long | 0x10 |
| 2 | `CreatorPlayerId` | **int** | 0x18 |
| 3 | `RoomId` | long | 0x20 |
| 4 | `SubRoomId` | `long?` | 0x28 |
| 5 | `ClubId` | `long?` | 0x38 |
| 6 | `Name` | string | 0x48 |
| 7 | `Description` | string | 0x50 |
| 8 | `ImageName` | string | 0x58 |
| 9 | `StartTime` | DateTime | 0x60 |
| 10 | `EndTime` | DateTime | 0x68 |
| 11 | `AttendeeCount` | int | 0x70 |
| 12 | `Accessibility` | enum `KOMDDCCKBID` | 0x74 |
| 13 | `IsMultiInstance` | bool | 0x78 |
| 14 | `SupportMultiInstanceRoomChat` | bool | 0x79 |
| 15 | `DefaultBroadcastPermissions` | enum `GAHAEEIJGGE` | 0x7C |
| 16 | `CanRequestBroadcastPermissions` | enum `GAHAEEIJGGE` | 0x80 |
| 17 | `BroadcastingRoomInstanceId` | `long?` | 0x88 |

All three `Nullable` members are **16-byte** `Nullable<long>` — stride-confirmed (0x28→0x38→0x48, and
0x88→0x98 by the subclass below).

| enum | members |
|---|---|
| `KOMDDCCKBID` **Accessibility** | `Private 0`, `Public 1`, `Unlisted 2` |
| `GAHAEEIJGGE` **broadcast permissions** | `None 0`, `RoomOwners 256`, `All 2147483647` |

⚠️ `GAHAEEIJGGE` is a **flags-style sparse enum** — `0`, `256`, `int.MaxValue`. Do not send `1`/`2`.

## `EAAICKJKHED : NEMBNIGCMFK` — the v2 event is a SUBCLASS

`.EAAICKJKHED` (the type [playerevent-tags-build-difference](playerevent-tags-build-difference.md) covers) declares **exactly one**
field — a genericinst at **`0x98`**, i.e. immediately after `NEMBNIGCMFK` ends. So the v2 PlayerEvent
is the v1 one **plus `Tags`**, and derived-first ordering means `Tags` is emitted **before** all 17
keys above when serializing an `EAAICKJKHED`.

Corollary: **this route's `NEMBNIGCMFK` has no `Tags` key at all.** Sending `Tags` here is silently
dropped, and the v2 `Tags` requirement (`[{"Tag":"class","Type":0}]`) does not apply.

## Validation — all four hooks are null-tolerant

Unusually for this codebase, two of the four types have **real** hooks rather than the shared no-op:

| type | `CPOBHIECLEN` | behaviour |
|---|---|---|
| `CPHNJLLFJEB` | **`0x7D5AFC0`** real | calls `EADLCOCJAGD.IANBCAFGFNL(list, 0)` `0x7623250` on `Created` then tail-jumps for `Responses` |
| `HALOCGHCLFE` | **`0x7E4B0F0`** real | `if (PlayerEvent != null)` → virtual call to its hook (`vtable+0x1A0`); `PlayerEventResponse` is **never** validated |
| `NEMBNIGCMFK` | `0xA60520` no-op | — |
| `DHOECFANGJN` | `0xA60520` no-op | — |

`EADLCOCJAGD.IANBCAFGFNL` opens with `test rbx,rbx ; je 0x762345C`, and `0x762345C` is
`xor al,al ; ret` — a **clean early return, not a throw**. So `"Created": null` and
`"Responses": null` are both tolerated at deserialize time, as is a `null` `PlayerEvent` inside a
pair. Nothing in this tree throws on partial data.

Still prefer `[]` over `null`: the hooks are safe but downstream consumers on sibling routes are not
([playerevents-v1-responses](playerevents-v1-responses-wire-shape.md), [roomkeys-v1-room](roomkeys-v1-room-wire-shape.md)), and I did not
follow this route's consumer past `GetRemotePlayerEventList`.

## Table gap

Absent from the generated `nonobject-responses.txt` on two counts: the path is `String.Format`-built
**and** the response T is an object rather than a List/scalar. Lower bound, never a census.
