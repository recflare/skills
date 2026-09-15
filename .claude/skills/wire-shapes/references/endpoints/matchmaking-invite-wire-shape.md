# Matchmaking invite wire shape

> POST invite (svc 4 Matchmaking, match.recflare.net) returns a BARE 4-key {RoomInviteId, FromPlayerId, ToPlayerId, RoomId}; player ids are int32, invite/room ids int64

Build 20250718.01 (`il2cpp-2025` carve). Request builder is `RecNet.Matchmaking$$BBIEMMAIDFK`
@ RVA `0x7D39050` (size 0x220), path literal `'invite'` @ `0xD23E938`.

**Request** — `POST` (HttpMethod static-field offset `0x20`; `Get`=0x08, `Post`=0x20, `Put`=0x28,
`Delete`=0x00), service enum `r8d = 4` (Matchmaking) in the `AKJEAMCCEOH$$.ctor` call, 5th ctor arg
`0` = no body. Three **query** params added via `MGPBDIAGCFD$$ELHKHFJEHLM`, in this order:
`playerId`, `roomInstanceId`, `joinRoomInviteMode` (enum `.EKFPOCGIIEF`).

**Response** — send generic `.MGPBDIAGCFD::HPBKMCLEANE<KGOJLHJNIOD`1<NOJAKOKCKCF>>`
(methodSpec generic inst **14536**). `KGOJLHJNIOD`1` is the fieldless send-result interface, so the
wire type is the **bare** DTO `.NOJAKOKCKCF` — no `{success,error,value}` envelope. Its parent is
`object`, so there is **no post-deserialize validation hook** (no nested-object NRE trap).

Formatter `PLAAFJJJCKB` (.ctor `0x7ACB940`, Deserialize `0x7ACB710`). `____stringByteKeys` tail run:

| key | CLR |
| --- | --- |
| `RoomInviteId` | long |
| `FromPlayerId` | int |
| `ToPlayerId` | int |
| `RoomId` | long |

Types confirmed twice over: field offsets `0x10 long / 0x18 int / 0x1c int / 0x20 long` line up with
the key order, and the deserialize switch reads `CDMENBIFAFK` (64-bit) / `JCHINMCLLNP` (32-bit) /
`JCHINMCLLNP` / `CDMENBIFAFK`. **RecNet player/account ids are `int` in this build** (cross-checked
against `CheerRequest.PlayerId`); only room/invite ids are `long`. Utf8Json accepts all three casings.

Sibling routes on the same service, not derived here: `invite/{0}` (`RecNet.Matchmaking$$IJFAPAPCENM`,
`0x7D3E6C0`) and `invite/bulk` (`RecNet.Matchmaking$$AOIBEJPLJEI`, `0x7D38E30`).

Method used: calibrated the send-generic → DTO mapping against the already-confirmed
[player-connection-info-wire-shape](player-connection-info-wire-shape.md) before trusting it. See [recflare-2025-metadata-carve](../../../il2cpp-analysis/references/recflare-2025-metadata-carve.md) for the
toolchain — this build has **no `dump.cs`**, so `dtoshape.py` cannot run; use `slots2025.py` /
`fields2025.py` / `mxref.py` plus a genericInst resolver over `MetadataRegistration` pair 1.

⚠️ **CORRECTION 2026-09-02:** where this note says the parameters are **query params**, they
are actually an **`application/x-www-form-urlencoded` request body** — `ELHKHFJEHLM` routes params
to the query string only for GET. See [elhkhfjehlm-verb-dependent-params](../conventions/elhkhfjehlm-verb-dependent-params.md). Response shape
unaffected.
