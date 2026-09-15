# Matchmake invite accept wire shape

> POST matchmake/invite/{roomInviteId} (svc 4) is the ACCEPT for a game invite; params are QUERY not body; returns the same bare {ErrorCode, RoomInstance, CorrelationId} as matchmake/v2/room, with the same required-RoomInstance throw.

Derived **2026-08-26** from build `20250718.01` via [recflare-2025-metadata-carve](../../../il2cpp-analysis/references/recflare-2025-metadata-carve.md).

`POST matchmake/invite/{0}` — **POST** (`HttpMethod` statics `+0x20`), service **4 Matchmaking**
([recnet-service-enum](../conventions/recnet-service-enum.md)). Client entry
`RecNet.Matchmaking.GBJOLDHEOAC(long roomInviteId, long roomId, int, int[] additionalPlayerIds, bool)`
`0x7D3C3F0` -> shared sender `GABPLBPIMLP` `0x7D3C1E0`, state machine `FFAPNJIPFOE$$MoveNext`
`0x7D2D8F0`. Called from `<AcceptRoomInvite>b__0>d$$MoveNext` `0x18615A0`.

The `{0}` is the **RoomInviteId** — the same value the invite notification carried as
`Data.InviteId` ([party-invite-accept-gate](party-invite-accept-gate.md)) and that `POST invite` returned as `RoomInviteId`
([matchmaking-invite-wire-shape](matchmaking-invite-wire-shape.md)).

## Request: QUERY params, no body

Unlike `matchmake/v2/room/{id}` ([matchmake-v2-room-wire-shape](matchmake-v2-room-wire-shape.md)) which posts a JSON DTO, this
route adds everything via `MGPBDIAGCFD.ELHKHFJEHLM` (the query-param adder):
`AdditionalPlayerIds`, `BypassMovementModeRestriction`, `MaxPersistenceVersion`, `Ugc1SubVersion`,
`Ugc2SubVersion`, `VoiceServerVersion`, `LoginLock`, `CorrelationId`.

## Response: identical DTO to matchmake/v2/room

`PLIIKGCAIOM`, **bare object, no envelope**, formatter `CAFAMOMOBBO` `.ctor 0x7AB7DC0`, 3 keys:
`ErrorCode` (enum `JILFDCOLLLA`), `RoomInstance` (`GGCLDGNBNLI` 15 keys, or null),
`CorrelationId` (Guid).

`PLIIKGCAIOM.CPOBHIECLEN` `0x7D48130` re-verified:

```
if (RoomInstance != null) GGCLDGNBNLI.CPOBHIECLEN()   ; parses Location as a scene GUID
if (ErrorCode != 0) return                            ; null RoomInstance is LEGAL on an error
if (RoomInstance == null) throw NullReferenceException("Matchmaking response has no RoomInstance field")
```

**So: `ErrorCode == 0` REQUIRES a full `RoomInstance`; any non-zero code may omit it.**

`JILFDCOLLLA` codes most relevant here: `Success 0`, `UnknownError -1`, `PlayerNotOnline 2`,
`InsufficientSpace 3`, `AlreadyInTargetInstance 17`, `NoSuchRoom 20`, `RoomIsPrivate 25`,
`RoomInstanceIsPrivate 26`, **`RoomInviteExpired 40`**, `BannedFromRoom 55`,
`InstanceJoinNotPermitted 76`, **`ChatPartyInviteNotFound 78`**, `ChatPartyInviteModerated 79`,
**`ChatMessageNotAnInvite 80`**, `RoomInstanceBlockedByMatchmakingPolicy 86`.
(Full 47-member table in the binary; `AlreadyInBestInstance 13`, `UpdateRequired 16`,
`DeviceClassNotSupported 30`, `MovementModeNotSupportedByRoomOwner 32`, `NotorietyTooPoor 50`,
`LevelTooLow 77`, `RRPlusRequired 82`, `AccountDoesNotExist 85`, `PlatformNotSupported 87` …)
