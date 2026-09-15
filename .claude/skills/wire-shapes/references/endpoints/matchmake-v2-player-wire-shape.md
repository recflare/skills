# Matchmake v2 player wire shape

> POST matchmake/v2/player/{playerId} (svc 4) sends NO body — 8 QUERY params — and returns the same bare {ErrorCode, RoomInstance, CorrelationId} as matchmake/v2/room; the response CorrelationId must echo the request's or the client throws.

Derived **2026-09-01** from build `20250718.01` via [recflare-2025-metadata-carve](../../../il2cpp-analysis/references/recflare-2025-metadata-carve.md).
"Join this player" (follow-a-friend). Sibling of [matchmake-v2-room-wire-shape](matchmake-v2-room-wire-shape.md) — **same response
type, different request style**.

`POST https://match.<host>/matchmake/v2/player/{playerId}` — service **4 = Matchmaking**
(`mov r8d, 4` at `0x7D2DB5B`), verb **POST** (`HttpMethod` statics `+0x20`, read at `0x7D2DB33`).
Literal `'matchmake/v2/player/{0}'` `0xD118780`.

Client entry `RecNet.Matchmaking.FHBNIGAKHJE(int playerId, int[] additionalPlayerIds,
bool bypassMovementModeRestriction, bool)` **`0x7D3BCE0`** → `KPIPLFECKNC<PLIIKGCAIOM>`, via the
shared `Matchmaking.GABPLBPIMLP(string requestUri, int[] expectedPlayerIds,
bool bypassMovementModeRestriction, OAPOJMIFJHN customRoomLoadPayload,
Action<MGPBDIAGCFD> configureRequest)` `0x7D3C1E0` (state machine `FFAPNJIPFOE.MoveNext`
`0x7D2D8F0` — **its fields are unobfuscated**, which is where those parameter names come from).

## Request — NO JSON body, 8 query params

Unlike the room route (which posts a `GBEFLPPCJKJ` body), this one adds everything as query string
via `MGPBDIAGCFD.ELHKHFJEHLM` ([algorithmiclists-wire-shape](algorithmiclists-wire-shape.md) pins that as the query-param adder).
There is **no `ELKIBCPINAP` call anywhere in the state machine** — nothing is serialized into a body.

`BypassMovementModeRestriction` (bool), `LoginLock` (Guid), `AdditionalPlayerIds`
(`IReadOnlyList<int>` overload, generic inst 42 = `int`), `VoiceServerVersion` (string),
`CorrelationId` (Guid, `Guid.NewGuid()` per call), `MaxPersistenceVersion` (int?),
`Ugc1SubVersion` (int?), `Ugc2SubVersion` (int?).

Same key *names* as the room body's first 8 keys — so a server can share the binding model, but must
read them from the query string here.

Before sending, the client throws `Exception("Not logged in to matchmaking service")`
(`0xD…` literal at `0x7D2E0FA`) if the matchmaking session isn't established — a client-side gate,
never reaches the server.

## Response — bare `PLIIKGCAIOM`, identical to matchmake/v2/room

Both routes converge on `Matchmaking.OPHMGAOHKNI(string requestUri, Guid correlationId,
MGPBDIAGCFD request, OAPOJMIFJHN customRoomLoadPayload)` → `Task<PLIIKGCAIOM>`, state machine
`LPDCMOMJHCA.MoveNext` **`0x7D32FB0`** (inlined into `FFAPNJIPFOE.MoveNext`). It sends with
`MGPBDIAGCFD.KBIHOFDDIMI` (raw `DPEENGNNEEB` BestHTTP response) and reads the body as
`PLIIKGCAIOM` — **bare object, no envelope**.

```json
{ "ErrorCode": 0,
  "RoomInstance": { …15 keys… },
  "CorrelationId": "<echo of the request's CorrelationId>" }
```

`PLIIKGCAIOM`: `ErrorCode` enum `JILFDCOLLLA` +0x10, `RoomInstance` `GGCLDGNBNLI` +0x18,
`CorrelationId` Guid +0x20. Formatter `CAFAMOMOBBO` ctor `0x7AB7DC0`. `RoomInstance` is the same
15-key DTO documented in [matchmake-v2-room-wire-shape](matchmake-v2-room-wire-shape.md) (Location is a scene GUID).

## Two hard failures — both shared with the room route

1. **`CorrelationId` must be echoed exactly.** `LPDCMOMJHCA.MoveNext` compares the sent Guid
   (SM `+0x30`) against `response.CorrelationId` (`+0x20`) with `Guid.op_Inequality` at `0x7D336E8`
   and throws `InvalidOperationException("Invalid correlation ID returned in HTTP Response.
   Expected {0} but was {1}")` (`0x7D33D6C`) on mismatch. **This check is in the shared sender, so it
   applies to `matchmake/v2/room/{id}` too** — it was missing from that note. Omitting the key
   (all-zero Guid) fails it just as surely as a wrong one.
2. `PLIIKGCAIOM.CPOBHIECLEN` `0x7D48130` throws `NullReferenceException("Matchmaking response has no
   RoomInstance field")` when `ErrorCode == 0` and `RoomInstance` is null.

## `ErrorCode` (`JILFDCOLLLA`), full table

`UnknownError -1`, `Success 0`, `NoSuchGame 1`, `PlayerNotOnline 2`, `InsufficientSpace 3`,
`EventNotStarted 4`, `EventAlreadyFinished 5`, `BlockedFromRoom 7`, `JuniorNotAllowed 11`,
`Banned 12`, `AlreadyInBestInstance 13`, `InsufficientRelationship 14`, `UpdateRequired 16`,
`AlreadyInTargetInstance 17`, `UGCNotAllowed 19`, `NoSuchRoom 20`, `RoomIsNotActive 22`,
`RoomBlockedByCreator 23`, `RoomIsPrivate 25`, `RoomInstanceIsPrivate 26`,
`DeviceClassNotSupported 30`, `DeviceClassNotSupportedByRoomOwner 31`,
`MovementModeNotSupportedByRoomOwner 32`, `EventIsPrivate 35`, `EventIsFull 36`,
`RoomInviteExpired 40`, `NoAvailableRegion 45`, `NotorietyTooPoor 50`, `BannedFromRoom 55`,
`NoSuchClub 70`, `ClubHasNoClubhouse 71`, `ClubIsNotActive 73`, `NotAMemberOfClub 74`,
`BannedFromClub 75`, `InstanceJoinNotPermitted 76`, `LevelTooLow 77`, `ChatPartyInviteNotFound 78`,
`ChatPartyInviteModerated 79`, `ChatMessageNotAnInvite 80`, `DeveloperOnly 81`, `RRPlusRequired 82`,
`MetaJuniorAccountRestriction 83`, `NotExclusivelyLoggedIn 84`, `AccountDoesNotExist 85`,
`RoomInstanceBlockedByMatchmakingPolicy 86`, `PlatformNotSupported 87`.

The ones a *player*-target route will actually want: `PlayerNotOnline 2`, `AccountDoesNotExist 85`,
`InsufficientRelationship 14`, `AlreadyInTargetInstance 17`, `AlreadyInBestInstance 13`,
`InstanceJoinNotPermitted 76`, `NotExclusivelyLoggedIn 84`.

**How to apply:** always echo `CorrelationId` from the query string, and return
`{"ErrorCode": <nonzero>, "RoomInstance": null, "CorrelationId": "<echo>"}` to refuse a join —
never `ErrorCode 0` with a null `RoomInstance`.

⚠️ **CORRECTION 2026-09-02:** where this note says the parameters are **query params**, they
are actually an **`application/x-www-form-urlencoded` request body** — `ELHKHFJEHLM` routes params
to the query string only for GET. See [elhkhfjehlm-verb-dependent-params](../conventions/elhkhfjehlm-verb-dependent-params.md). Response shape
unaffected.
