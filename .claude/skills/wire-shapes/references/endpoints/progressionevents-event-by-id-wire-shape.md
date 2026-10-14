# `GET api/progressionEvents/event/{id}` wire shape

> `GET api.<host>/api/progressionEvents/event/{eventId}` (svc **2 API**) returns a **BARE
> `ProgressionEventDTO`** — no envelope, no array.
> **15 keys on `20250718.01`, 16 on `20260323.14`**; the one addition is `EventLeaderboardId`
> (`long?`), so a single payload carrying all 16 works for both builds.
> Not to be confused with its sibling [progressionevents-active](progressionevents-active-wire-shape.md), which returns a
> **bare nullable number**, not an object.

Derived **2026-10-13** from build `20260323.14`, cross-checked against `20250718.01` (the route
exists in both).

Path is `String.Format("{0}/event/{1}", "api/progressionEvents", eventId)` — base literal
`0xFC62C70` + template `{0}/event/{1}`, so `/event/18` is **two path segments**, no query params.
Verb **GET** (`[HttpMethod statics + 0x08]` at `0x95490D3`).

Service **2 = API**, hence `api.<host>`. ⚠️ **The service is not an `r8d` immediate here** — this
call site has the request constructor inlined, so it appears as a direct field store
`mov dword ptr [rsi + 0x18], 2` at `0x9549131`. Request-object layout at that site: `+0x10`
HttpMethod, **`+0x18` service enum**, `+0x20` path string. Worth knowing: grepping only for
`mov r8d, <imm>` misses these.

Facades: **`RecNet.TJASXPRZXFT.PDHJHUWHRJA(long)`** `0x9548FE0` on 2026, and on 2025
`.MPJLPOEEGIF.ODNHILEBKCB(long)` (plus a second entry `DNBMGEGLONI(long)` with the same return type —
an interface/impl pair). Both declare `ProgressionEventDTO` directly, so the response is **bare**.

## Response — bare object

Formatter `Utf8Json.Formatters.RecNet.SLMXEFSRIUE`, `.ctor` **`0x8E09B90`** (+0xBB0) on 2026. Keys =
property names, declaration order, no `[DataMember]` renames.

| # | key | CLR | notes |
|---|---|---|---|
| 1 | `ProgressionEventId` | `long` | |
| 2 | `Name` | string | |
| 3 | `Rewards` | `List<ProgressionEventRewardDTO>` | |
| 4 | `KeepsakeRoomLists` | `List<KeepsakeRoomListDTO>` | |
| 5 | `StartTime` | `DateTime` | **not nullable** |
| 6 | `EndTime` | `DateTime` | **not nullable** |
| 7 | `CollectionEndTime` | `DateTime` | **not nullable** — rewards claimable until here |
| 8 | `UsesBoost` | bool | |
| 9 | `BoostDailyGameplayMinutesLimit` | int | |
| 10 | `BoostXpMultiplier` | **float** | |
| 11 | `PurchasableXpBoostId` | **`Guid?`** | nullable |
| 12 | `ActiveExperiment` | string | |
| 13 | `ChallengesIconImageName` | string | |
| 14 | `RewardsPipImageName` | string | |
| 15 | `EventInfoImageName` | string | |
| 16 | `EventLeaderboardId` | **`long?`** | **2026 only** — see below |

```json
{ "ProgressionEventId": 18,
  "Name": "Autumn Event",
  "Rewards": [ { "ProgressionEventRewardId": 1, "ImageName": null, "Xp": 500,
                 "RewardIndex": 0, "IsBonus": false, "IsRRPlusExclusive": false,
                 "MaxGlobalCollections": null } ],
  "KeepsakeRoomLists": [],
  "StartTime": "2026-10-01T00:00:00Z",
  "EndTime": "2026-11-01T00:00:00Z",
  "CollectionEndTime": "2026-11-08T00:00:00Z",
  "UsesBoost": true,
  "BoostDailyGameplayMinutesLimit": 60,
  "BoostXpMultiplier": 1.5,
  "PurchasableXpBoostId": null,
  "ActiveExperiment": null,
  "ChallengesIconImageName": null,
  "RewardsPipImageName": null,
  "EventInfoImageName": null,
  "EventLeaderboardId": null }
```

### Build delta — `EventLeaderboardId` is the only difference

`ftypes.py ProgressionEventDTO` gives **15** fields on 20250718.01 and **16** on 20260323.14, with
the first 15 identical in order and type. Confirming it is purely additive: all 15 key names exist as
string literals in the 2025 binary, and **`EventLeaderboardId` exists in 2026 only** (0 hits in the
2025 string table).

It is `Nullable<long>`, so emitting `"EventLeaderboardId": null` — or omitting it — is safe for both
builds. On 2025 it is an unknown key and silently dropped.

On 2025 every property name on this DTO is obfuscated in metadata (`<CDJHDIAHBGE>k__BackingField` …)
while the **wire keys are not** — the key literals are all present and unobfuscated. That is the
usual split, and the reason the key table above transfers to 2025 unchanged.

### Nested DTOs

**`ProgressionEventRewardDTO`** — 7 fields: `ProgressionEventRewardId` (long), `ImageName` (string),
`Xp` (int), `RewardIndex` (int), `IsBonus` (bool), `IsRRPlusExclusive` (bool),
`MaxGlobalCollections` (**`int?`**). Present on both builds.

**`KeepsakeRoomListDTO`** — 10 fields: `KeepsakeRoomListId` (long), `ProgressionEventId` (long),
`UnlockItemAvatarItemId` (**`int?`**), `UnlockItemGiftDropId` (**`int?`**),
`UnlockItemLockDurationTicks` (**`long?`**), `RoomUnlockStartOffsetTicks` (long),
`RoomUnlockIntervalTicks` (long), `RoomUnlockBatchSize` (int), `RoomType`
(`RecNet.KeepsakeRoomType`, numeric enum), `KeepsakeRooms` (`List<KeepsakeRoomDTO>`).

The three `*Ticks` fields are **.NET ticks** (100 ns units), not seconds or milliseconds.

⚠️ The three `DateTime`s and every `int`/`long`/`float`/`bool` are **non-nullable** — a JSON `null`
throws. Only `PurchasableXpBoostId`, `EventLeaderboardId`, `MaxGlobalCollections` and the
`UnlockItem*` fields accept `null`. Serve `[]` rather than `null` for `Rewards` and
`KeepsakeRoomLists`; the client iterates both.

## The rest of the facade

One `msig.py` on the facade covers the family. 2026 names, with the 2025 equivalents in the same
order:

| 2026 (`RecNet.TJASXPRZXFT`) | returns | route |
|---|---|---|
| `SWSDCUOSKOW()` | `long?` | `api/progressionEvents/active` — [progressionevents-active](progressionevents-active-wire-shape.md) |
| **`PDHJHUWHRJA(long)`** | **`ProgressionEventDTO`** | **`/event/{id}` — this note** |
| `NJFEQKSQKZM(long, bool)` | `ProgressionEventRecordDTO` | the caller's own progress |
| `PQQHVOPRIWZ(long)` | `List<ProgressionEventPurchasableXpBoostDTO>` | |
| `IVKLKWXXEKO(long, Guid)` | `int` | bare scalar |
| `RPPOWCPWJFU(long, long)` | `int?` | bare nullable scalar |
| `EXWYSAVTEEJ(long, int)` | *(no value)* | a write |
| `KFYOGTILLDR(int)` | *(no value)* | a write |

⚠️ Four of these return **scalars** (`long?`, `int`, `int?`), so they are in the
[nonobject-response-routes](../conventions/nonobject-response-routes.md) class — `{}` hard-fails on them. `SWSDCUOSKOW`/`active`
is one of exactly two routes in 20250718.01 that deserialize into a bare `long?`
([number-token-parsing-exception](../conventions/number-token-parsing-exception.md)).
