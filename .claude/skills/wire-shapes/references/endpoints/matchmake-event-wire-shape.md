# `POST matchmake/event/{playerEventId}` wire shape (2026 build)

> `POST match.<host>/matchmake/event/{playerEventId}` (svc **4 Matchmaking**) returns a **BARE
> 3-key `RecNet.MatchmakingResponse`** — `{ErrorCode, RoomInstance, CorrelationId}`. No envelope.
> **Identical shape to `matchmake/v2/room`, `matchmake/v2/player` and `matchmake/invite/{id}`** —
> every matchmake route converges on one sender.
> ⚠️ Two hard client-side gates: **`CorrelationId` must echo the request's**, and
> **`ErrorCode: 0` requires a non-null `RoomInstance`**.

Derived **2026-10-13** from build `20260323.14`. The `{0}` is **`PlayerEvent.PlayerEventId`**, so a
path of `matchmake/event/317` means `PlayerEventId == 317` — not a room or instance id.

Route literal `'matchmake/event/{0}'` **`0xFCB3CA0`** (2025: `0xD117918` — same route both builds).

## Call chain

| step | method | note |
|---|---|---|
| facade | `RecNet.Matchmaking.QRIAQWMDXNP(Events.PlayerEvent, int[] expectedPlayerIds, bool bypassMovementModeRestriction, RoomJoinMode, JoinRoomInviteMode)` `0x94FC830` | formats the path from `PlayerEvent` field `+0x10` = `PlayerEventId` |
| | `RecNet.DIPTQBEVHLM.QRIAQWMDXNP` `0x94F1470` | the instance-flavoured twin; same literal, same path |
| build | `RecNet.Matchmaking.AIJKPSZWFDR` = **`GoToHelper`** `0x94F3AF0`, state machine `<GoToHelper>d__131$$MoveNext` `0x9508CB0` | builds the `RGBOOBRDHEB` request and all the params |
| send | `<SendMatchmakingRequestHelper>d__133$$MoveNext` `0x950DED0` | `RGBOOBRDHEB.NJDMOZYSDOQ(ct)` → `XJAFUXFVGPU.RBSYDGDRRZM(bool)` → `XJAFUXFVGPU.DAOUNAUWTPW<T>()` |

**Verb POST, service 4 Matchmaking** — read at `0x9508EDD`: `[HttpMethod statics + 0x20]` = Post,
and `mov r8d, 4` at `0x9508EF4` into `RGBOOBRDHEB..ctor(HttpMethod, Service, string)`.

Send tier is `Task<T>` with `T` = generic inst **#1283 = `RecNet.MatchmakingResponse`** → **bare**,
no envelope ([2026-send-helper-tiers](../conventions/2026-send-helper-tiers.md)).

## Request — form-urlencoded body, 10 params

POST, and every parameter goes through `RGBOOBRDHEB.NJPEKLKCVCG` → **`application/x-www-form-urlencoded`
body, not a query string** ([elhkhfjehlm-verb-dependent-params](../conventions/elhkhfjehlm-verb-dependent-params.md)). ⚠️ **This differs from
`matchmake/v2/room`, which posts a JSON `GoToRoomRequestDTO`.** Same response, different request
encoding.

From `<GoToHelper>d__131`: `BypassMovementModeRestriction`, `LoginLock`, `AdditionalPlayerIds`
(repeated once per id, the `IReadOnlyList<int>` overload), `VoiceServerVersion`, `CorrelationId`,
`MaxPersistenceVersion`, `Ugc1SubVersion`, `Ugc2SubVersion`.

Plus two added by the closure **`HNNYTJCFZKE.GMDASHUMDCJ`** `0x94F36E0` (the `Action<RGBOOBRDHEB>`
the facade passes in): **`JoinMode`** (field `+0x10`, `RecNet.RoomJoinMode`) and **`InviteMode`**
(field `+0x14`, `RecNet.JoinRoomInviteMode`). Reading only the state machine misses these two.

## Response — bare `RecNet.MatchmakingResponse`, 3 keys

Field layout (`py ftypes.py MatchmakingResponse`): `ErrorCode` `+0x10`, `RoomInstance` `+0x18`,
`CorrelationId` `+0x20`.

| # | key | CLR |
|---|---|---|
| 1 | `ErrorCode` | `RecNet.MatchmakingErrorCode` (int enum) |
| 2 | `RoomInstance` | `RecNet.RoomInstance` or `null` |
| 3 | `CorrelationId` | `Guid` |

```json
{
  "ErrorCode": 0,
  "CorrelationId": "<echo the CorrelationId the client sent>",
  "RoomInstance": {
    "RoomInstanceId": 9001,
    "RoomId": 1234,
    "SubRoomId": 0,
    "Location": "cbad71af-0831-44d8-b8ef-69edafa841f6",
    "EventId": 317,
    "ClubId": 0,
    "RoomCode": "ABCD",
    "Name": "My Event Room",
    "MaxCapacity": 40,
    "IsFull": false,
    "IsPrivate": false,
    "IsInProgress": true,
    "EncryptVoiceChat": false,
    "RoomInstanceType": 0,
    "MatchmakingPolicy": 0
  }
}
```

`EventId` should be the `317` that was requested — it is how the client ties the instance back to the
`PlayerEvent`.

## The three ways this response kills the client

1. ⚠️ **`CorrelationId` must equal the one the client sent.** `Guid.op_Inequality` at `0x950E701`
   in `<SendMatchmakingRequestHelper>d__133`, else
   `InvalidOperationException("Invalid correlation ID returned in HTTP Response. Expected {0} but was {1}")`
   (literal site `0x950ED16`). Echo the request's `CorrelationId` verbatim.
2. ⚠️ **`ErrorCode: 0` with a null or absent `RoomInstance` throws.**
   `MatchmakingResponse.IULRMJBAHPG` = **`OnDeserializedAsync`** `0x95118E0`, state machine
   `<OnDeserializedAsync>d__14$$MoveNext` `0x9524E00`:
   ```
   if (response == null)                       -> NRE (throw helper, 0x9524FE2)
   if (ErrorCode != 0 && RoomInstance == null) -> return      ; 0x9524E85 je 0x9524ED3 — legal
   if (ErrorCode == 0 && RoomInstance == null) -> throw NullReferenceException(
                                                    "Matchmaking response has no RoomInstance field")
                                                              ; 0x9524E78 je 0x9524F95
   else await RoomInstance.OnDeserializedAsync()
   ```
   **A null `RoomInstance` is legal only with a non-zero `ErrorCode`.** To refuse a join, pick a real
   code from the table below — never `ErrorCode: 0` with no instance.
3. **Non-2xx throws before deserialization.** `XJAFUXFVGPU.RBSYDGDRRZM(bool)` runs at `0x950E628`,
   ahead of `DAOUNAUWTPW<T>()` at `0x950E642`. And `DAOUNAUWTPW<T>()` takes **no** `allowNull`
   argument, so an empty body or a literal `null` is refused too (`SWGLEDQGUUP` — see
   [club-home-me](club-home-me-wire-shape.md)). Answer **200 with a real object**, always.

## `RecNet.RoomInstance` — 15 keys, unchanged from 2025

Formatter **`Utf8Json.Formatters.RecNet.XUDZRULFMPM`** `.ctor` **`0x8E6E420`** (confirmed with
`py msig.py XUDZRULFMPM`: `Serialize(JsonWriter, RecNet.RoomInstance, …)`). The trailing
`____stringByteKeys` run, in order:

`RoomInstanceId` long · `RoomId` long · `SubRoomId` long · `Location` string · `EventId` long ·
`ClubId` long · `RoomCode` string · `Name` string · `MaxCapacity` int ·
`IsFull`/`IsPrivate`/`IsInProgress`/`EncryptVoiceChat` bool · `RoomInstanceType` enum ·
`MatchmakingPolicy` enum.

✅ **Same 15 keys as build `20250718.01`** ([matchmake-v2-room](matchmake-v2-room-wire-shape.md)), so one payload serves
both builds. 2026 just de-obfuscates the names — which finally settles the two renames the 2025 note
could only describe as "two `[IgnoreDataMember]` backing fields":

- **17 instance fields, 15 keys.** The two with no wire key are **`Location`** (the
  `.RoomSceneLocations` *enum*, filled in by the post-deserialize hook) and **`SanitizedName`**.
- ⚠️ **wire `Location` is the C# `SceneLocationId` (string)** — a scene-location **GUID**, not a name
  and not the enum.
- ⚠️ **wire `Name` is the C# `RawName`.** `SanitizedName` is computed client-side; emitting it is
  silently dropped.

`RoomInstance.OnDeserializedAsync` → `<OnDeserializedAsync>d__86$$MoveNext` `0x950BB60` parses
`Location` and, on an unrecognised GUID, only **logs** via `RecRoom.Log.LIBCEQYQFAM` with
`'RecNet game session contains unknown scene location ID'` (literal `0xFDCBDA8`, site `0x950BE1C`) —
**log-only on 2026 too, no throw**, leaving the enum at 0 (`DORM_ROOM`). Common GUIDs: REC_CENTER
`cbad71af-0831-44d8-b8ef-69edafa841f6`, DORM_ROOM `76d98498-60a1-430c-ab76-b54a29b7a163`,
CUSTOM_DORM_ROOM `1c92f780-baf1-4bd8-aa15-27cca0aa7396`. `SCENES.md` has the full table.

## `RecNet.MatchmakingErrorCode` (2026) — the event-specific codes

`py enumvals.py MatchmakingErrorCode` — typedef #22492, `int`. **46 members, identical values to
2025**, so the 2025 table transfers. The ones this route can actually need:

| value | name |
|---|---|
| -1 | `UnknownError` |
| **0** | **`Success`** — requires a `RoomInstance` |
| 1 | `NoSuchGame` |
| 3 | `InsufficientSpace` |
| **4** | **`EventNotStarted`** |
| **5** | **`EventAlreadyFinished`** |
| 11 | `JuniorNotAllowed` |
| 13 | `AlreadyInBestInstance` |
| 17 | `AlreadyInTargetInstance` |
| 20 | `NoSuchRoom` |
| 22 | `RoomIsNotActive` |
| **35** | **`EventIsPrivate`** |
| **36** | **`EventIsFull`** |
| 77 | `LevelTooLow` |
| 86 | `RoomInstanceBlockedByMatchmakingPolicy` |

Full 46-member list via `enumvals.py`; the rest are tabulated in
[matchmake-v2-player](matchmake-v2-player-wire-shape.md).

## Siblings — this shape covers all of them

`RecNet.Matchmaking` has 132 methods on 2026 and **11** return `MPVTAJGPRUT<MatchmakingResponse>`:
`GoToRoom`, `QRIAQWMDXNP` (this one, by event), `OJMAFIRNNBB(Club, …)` (by club),
`SSQBTAXEWUG(int, …)` (by player), `ROISCYWVXNF`, `GNVJPACEDBM`, `WMGPPJEXPWX`, `KHGBUZLHBDH`,
`WINDVXCMCKJ`, `OGHXCNYUBNS`, `EFYSFFTWXDS`. **All of them funnel through `GoToHelper` →
`SendMatchmakingRequestHelper`, so all of them return exactly this shape and obey the same three
gates.** Getting this one right gets the whole family right.
