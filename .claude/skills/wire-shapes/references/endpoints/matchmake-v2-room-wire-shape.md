# Matchmake v2 room wire shape

> Wire shape of POST matchmake/v2/room/{roomId} on the Matchmaking service (svc 4) for recflare-2025 — JSON request DTO in, {ErrorCode, RoomInstance, CorrelationId} out.

Derived **2026-08-17** from `C:\Games\recflare-2025` (build `20250718.01`) via
[recflare-2025-metadata-carve](../../../il2cpp-analysis/references/recflare-2025-metadata-carve.md). Same method as [curatedlists-bulk-wire-shape](curatedlists-bulk-wire-shape.md).

`POST https://match.<host>/matchmake/v2/room/{roomId}` — service enum `NNPMGHNBFMD` = **4**
(Matchmaking; Lists = 13, confirming the enum). **POST**, no query string. Client entry is
`RecNet.Matchmaking.DILDMHLGACC` (RVA `0x7D3AD40`) → generic `HMNDOJGENAA<TRequestDTO>`
(`0x3DDB720`, state machine MoveNext `0x4F2C2A0`) → `OPHMGAOHKNI` (`0x7D45110`).

**Request body** = `GBEFLPPCJKJ`, 13 keys in `____stringByteKeys` order (formatter `ACAPOHENPAM`
ctor `0x7AB6660`): `AdditionalPlayerIds` List\<int\> 0x10, `BypassMovementModeRestriction` bool 0x18,
`MaxPersistenceVersion` int? 0x1c, `Ugc1SubVersion` int? 0x24, `Ugc2SubVersion` int? 0x2c,
`VoiceServerVersion` string 0x38, `LoginLock` Guid 0x40, `ClientJoinData` string 0x50,
`CorrelationId` Guid 0x58, `JoinMode` enum 0x68, `InviteMode` enum 0x6c,
`ShouldKeepPlayerWithParty` bool 0x70, `PlayerScores` List\<KHLNILAPPFC\> 0x78.

**Response** = `PLIIKGCAIOM`, bare object, no envelope: `ErrorCode` (`JILFDCOLLLA`, Success=0,
UnknownError=-1), `RoomInstance` (`GGCLDGNBNLI`|null), `CorrelationId` (Guid). Formatter
`CAFAMOMOBBO` ctor `0x7AB7DC0`.

`RoomInstance` = 15 keys (formatter `KPJAFKABLFC` ctor `0x7AC7040`): `RoomInstanceId` long,
`RoomId` long, `SubRoomId` long, `Location` string, `EventId` long, `ClubId` long, `RoomCode` string,
`Name` string, `MaxCapacity` int, `IsFull`/`IsPrivate`/`IsInProgress`/`EncryptVoiceChat` bool,
`RoomInstanceType` enum, `MatchmakingPolicy` enum. Two `[IgnoreDataMember]` backing fields sit at
0x30 and 0x58 and are **not** on the wire — that is why 17 fields map to 15 keys.

Two real post-deserialize hooks here (unlike the curated-list DTO, which folds onto the
`0xA60520` no-op):

- `PLIIKGCAIOM.CPOBHIECLEN` (`0x7D48130`): **throws `NullReferenceException("Matchmaking response
  has no RoomInstance field")` when `ErrorCode == 0` and `RoomInstance` is null.** Null RoomInstance
  is only legal on a non-zero ErrorCode.
- `GGCLDGNBNLI.CPOBHIECLEN` (`0x7D2ED90`): parses `Location` through a GUID→enum dictionary
  (`IMKBHICHFMI.BOIPBPENDNC`, table built in `.cctor` `0x89B6FD0`). **`Location` is a scene-location
  GUID string, not a name.** Unknown value only logs "RecNet game session contains unknown scene
  location ID" and leaves the parsed enum 0 (DORM_ROOM). Common ones: REC_CENTER
  `cbad71af-0831-44d8-b8ef-69edafa841f6`, DORM_ROOM `76d98498-60a1-430c-ab76-b54a29b7a163`,
  CUSTOM_DORM_ROOM `1c92f780-baf1-4bd8-aa15-27cca0aa7396`; the other 47 come out of that `.cctor` in
  enum order.

**Why:** a matchmaking response that omits `RoomInstance` on success throws inside the client's
deserialize path rather than surfacing an error, so it looks like a hang, not a bad response.

**How to apply:** re-derive with `names.py <formatter ctor>` + `fields2025.py <TypeName>`; the
GUID table with `rangedis.py 89b7290 89b7b90` (key literal then `mov r8d, <enum value>`).

**Added 2026-09-01** (from [matchmake-v2-player-wire-shape](matchmake-v2-player-wire-shape.md)): the shared sender
`LPDCMOMJHCA.MoveNext` `0x7D32FB0` also **requires the response `CorrelationId` to equal the one the
client sent** — `Guid.op_Inequality` at `0x7D336E8`, else
`InvalidOperationException("Invalid correlation ID returned in HTTP Response. Expected {0} but was
{1}")` at `0x7D33D6C`. That applies to this route as well; echo the key back.
