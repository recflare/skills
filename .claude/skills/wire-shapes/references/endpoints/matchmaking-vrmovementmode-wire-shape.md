# Matchmaking vrmovementmode wire shape

> PUT player/vrmovementmode on the Matchmaking service (svc 4) for recflare-2025 — the response body is IGNORED entirely (SendWithNoResponse); it takes one numeric query param.

Derived **2026-08-21** from `C:\Games\recflare-2025` (build `20250718.01`) via
[recflare-2025-metadata-carve](../../../il2cpp-analysis/references/recflare-2025-metadata-carve.md).

`PUT https://match.<host>/player/vrmovementmode?vrMovementMode={0|1}` — **PUT** (`HttpMethod`
statics `+0x28`), service **4 = Matchmaking** (`mov r8d, 4`), **no request body**, one query param
added via `ELHKHFJEHLM` as an I4. Client entry
`RecNet.Matchmaking.MIPJJMHEFAH(OIHHPHPLPGP vrMovementMode)` at `0x7D426C0`, non-async; failure logs
**"Failed to set VR movement mode"**.

**There is no response shape.** The send call is `MGPBDIAGCFD.CNDMDLNHDLI` — the
*SendWithNoResponse* variant (returns a non-generic `Task`), and the method's own return type is the
non-generic promise `JCFICNGFDLA`. **Nothing is deserialized**, so any 2xx works; `204 No Content` is
the natural answer and an empty body cannot trigger
[ioncmjiacfi-malformed-response](../conventions/ioncmjiacfi-malformed-response.md).

`vrMovementMode` = `OIHHPHPLPGP`: **TELEPORT 0, WALK 1** (numeric on the wire).

**Why:** it is a matchmaking-side profile flag, not a settings write — matchmaking uses it for the
`MovementModeNotSupportedByRoomOwner` / `BypassMovementModeRestriction` logic seen in
[matchmake-v2-room-wire-shape](matchmake-v2-room-wire-shape.md).

**How to apply:** identify these write-only endpoints by the send method, not the path — a
`CNDMDLNHDLI` call means the body is discarded, `HPBKMCLEANE<T>` means it is required, and
`CJBFDPLCIEJ<T>` means it is optional.

## There is no GET on `player/vrmovementmode`

Verified **2026-08-21**. The literal `player/vrmovementmode` (`0xD0616A8`) has **exactly two**
rip-relative references, both inside the PUT method `MIPJJMHEFAH` (`0x7D426C0`), and there is no
composed form (no bare `player/` prefix literal exists — only complete `player/...` paths). So a GET
on that path is never called by this client and its shape cannot be derived.

**The read equivalent is `GET player?id={accountId}`** — `Matchmaking.OFPKFPHIHFI(int accountId)`
(`0x7D44900`), service 4, one query param `id`, logs "Failed to refresh player presence" on failure.
It returns the **player-presence DTO `ADEDKDNDABF`** (formatter `FIPBEDGIIKG` ctor `0x7ABCCB0`),
10 keys, which is where `VrMovementMode` is actually read back:

`PlayerId` int 0x10, `StatusVisibility` enum 0x14, `Platform` enum 0x18, `DeviceClass` enum 0x1c,
**`VrMovementMode` enum 0x20**, `RoomInstance` (`GGCLDGNBNLI`, the same object as
[matchmake-v2-room-wire-shape](matchmake-v2-room-wire-shape.md)) 0x28, `CorrelationId` Guid? 0x30, `IsOnline` bool 0x44,
`AppVersion` string 0x48, `ClientJoinData` string 0x50. Three further fields carry no key.

`VrMovementMode` is also a key on `LHJNFIEBDOJ` (formatter `GJCMKKENKDJ`), the sibling presence
payload that adds `WelcomeMatName`.

⚠️ **CORRECTION 2026-09-02:** where this note says the parameters are **query params**, they
are actually an **`application/x-www-form-urlencoded` request body** — `ELHKHFJEHLM` routes params
to the query string only for GET. See [elhkhfjehlm-verb-dependent-params](../conventions/elhkhfjehlm-verb-dependent-params.md). Response shape
unaffected.
