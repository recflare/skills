# Player heartbeat wire shape

> POST player/heartbeat (svc 4 Matchmaking) sends no body, 2 query params, and returns a BARE 11-key presence record {ServerTime + the 10 ADEDKDNDABF presence keys}; the client ADOPTS it — a mismatched RoomInstance forces a resync, a null body NREs.

Derived **2026-09-01** from build `20250718.01` via [recflare-2025-metadata-carve](../../../il2cpp-analysis/references/recflare-2025-metadata-carve.md).

`POST https://match.<host>/player/heartbeat` — service **4 = Matchmaking** (`mov r8d, 4` at
`0x7D31FFA`), verb **POST** (`HttpMethod` statics `+0x20`, read at `0x7D31FD2`). Literal `0xD05FD60`.

State machine `JKHPBPACKPH.MoveNext` **`0x7D31B10`**; entry `RecNet.Matchmaking.ADNCOJENLMA()`
`0x7D38750`. **No body** — two query params via `ELHKHFJEHLM`: **`LoginLock`** and
**`VoiceServerVersion`**. Sent with `MGPBDIAGCFD.KBIHOFDDIMI` (raw `DPEENGNNEEB`), body deserialised
into the SM's `<response>5__3`.

## Response — BARE object, no envelope

Type `.LHJNFIEBDOJ`, which **derives from `.ADEDKDNDABF`** (the presence record that
`Matchmaking.GJLHHMPLFEB(playerId)` `0x7D3C8D0` returns locally). Formatter `GJCMKKENKDJ`
`.ctor 0x7ABE630`, 11 keys — derived first, then base:

| # | key | CLR | offset |
|---|---|---|---|
| 1 | `ServerTime` | `DateTime?` | 0x70 *(on `LHJNFIEBDOJ`)* |
| 2 | `PlayerId` | int | 0x10 |
| 3 | `StatusVisibility` | enum `FPDHAFIJOCE` | 0x14 |
| 4 | `Platform` | enum `NLJFAOJNHDJ` | 0x18 |
| 5 | `DeviceClass` | enum `KPOJCHHIMDA` | 0x1C |
| 6 | `VrMovementMode` | enum `OIHHPHPLPGP` | 0x20 |
| 7 | `RoomInstance` | `GGCLDGNBNLI` (15 keys) | 0x28 |
| 8 | `CorrelationId` | `Guid?` | 0x30 |
| 9 | `IsOnline` | bool | 0x44 |
| 10 | `AppVersion` | string | 0x48 |
| 11 | `ClientJoinData` | string (embedded JSON) | 0x50 |

`ADEDKDNDABF` declares 13 fields; the last three (`0x58` `FHLOGOIDOBC`, `0x60` `JMHHOKPEFKH`,
`0x68` bool) are `[IgnoreDataMember]` — they are *outputs* of the post-deserialize hook. Mapping
double-checked against [matchmake-v2-player-wire-shape](matchmake-v2-player-wire-shape.md): `IFPNKLBHOOM`/`BLFKLCKALCO` are the same
backing-field names `PLIIKGCAIOM` uses for `RoomInstance`/`CorrelationId`.

`RoomInstance` is the identical 15-key DTO from [matchmake-v2-room-wire-shape](matchmake-v2-room-wire-shape.md) (`Location` is a
scene GUID).

## Post-deserialize hook `ADEDKDNDABF.CPOBHIECLEN` `0x7D243C0` — no throws, but it rewrites

1. `RoomInstance` non-null → `GGCLDGNBNLI.CPOBHIECLEN` (Location GUID→enum; unknown only logs).
2. **If `DeviceClass` is not VR(1) / VRLow(4) / Quest2(5), `VrMovementMode` is forced to 0
   (TELEPORT)** — `0x7D2440D..0x7D2441F`. Whatever you send for a Screen/Mobile client is discarded.
3. `AppVersion` non-empty → parsed into a version object (ignored field `0x60`).
4. `ClientJoinData` → `Utf8Json Deserialize<FHLOGOIDOBC>(string)` into ignored field `0x58`. That
   helper null/empty-guards at `0x3D95C2C`/`0x3D95C31`, so `null` and `""` are both safe.

## The response is AUTHORITATIVE — `Matchmaking.LIKJHJLPJNN` `0x7D40F30`

- **null response → NRE** (`0x7D40F94` → `0x7D4118F`).
- `ServerTime` → `EKKLOHCJKIG.IJNHKKEHNAN(DateTime?)`, which sets the client's server-clock offset
  (stored at Matchmaking statics `+0xF8`). This is how the client learns server time.
- It then compares `response.RoomInstance` against the **local** presence's RoomInstance
  (`GJLHHMPLFEB(myPlayerId)` → `GGCLDGNBNLI.DBDBPBIBHHA`). If they differ and `HMMGLKLELGK()` is
  true it logs **"RecNet presence heartbeat response indicates local presence is out-of-sync!"**
  (`0xD1CDF60`) and calls `HFMGPEPGBCN(response, true)` — **it adopts the server's record**, forcing
  a client-side resync.

So this is not a fire-and-forget ping: **echo the player's actual current presence, RoomInstance
included**, or every heartbeat drags the client out of the instance it thinks it is in. Both sides
being `null` counts as agreeing.

Related literals: `'RecNet presence heartbeat failed: {0}'` `0xD1CDBD0` (`PFGPBOLNLDE.MAJILNPGOFA`
`0x7D47F60`), `'Timed out trying to send presence heartbeats.'` `0xD226920` (in the SM),
`'Heartbeat failed after being in the background. Logging out. '` `0xD212888`.

## Enums (numeric on the wire)

- `StatusVisibility` `FPDHAFIJOCE`: `Public 0`, `FriendsOnly 1`, `FavoriteFriendsOnly 2`, `Offline 3`.
- `Platform` `NLJFAOJNHDJ`: `All -1`, `Steam 0`, `Oculus 1`, `PlayStation 2`, `Xbox 3`, `RecNet 4`,
  `IOS 5`, `GooglePlay 6`, `Standalone 7`, `Pico 8`, `Switch 9`.
- `DeviceClass` `KPOJCHHIMDA`: `Unknown 0`, `VR 1`, `Screen 2`, `Mobile 3`, `VRLow 4`, `Quest2 5`.
- `VrMovementMode` `OIHHPHPLPGP`: `TELEPORT 0`, `WALK 1` — matches
  [matchmaking-vrmovementmode-wire-shape](matchmaking-vrmovementmode-wire-shape.md).

⚠️ **CORRECTION 2026-09-02:** where this note says the parameters are **query params**, they
are actually an **`application/x-www-form-urlencoded` request body** — `ELHKHFJEHLM` routes params
to the query string only for GET. See [elhkhfjehlm-verb-dependent-params](../conventions/elhkhfjehlm-verb-dependent-params.md). Response shape
unaffected.
