# Photon vs gameserver backend switch

> The client picks Photon vs the NGO/dedicated 'GameServer' room backend from Experiments.ShouldUseGameServerNetworking in GET player/connection-info — OBNIPMNHCIE.IDPELGOBGIG requires HasValue && Value, so anything missing/null/false means Photon.

Derived **2026-09-01** from build `20250718.01` via [recflare-2025-metadata-carve](../../il2cpp-analysis/references/recflare-2025-metadata-carve.md), answering
"why is the client still calling Photon when I have a Tachyon/NGO room server". Companion to
[rr-named-message-room-protocol](rr-named-message-room-protocol.md) and [player-connection-info-wire-shape](../../wire-shapes/references/endpoints/player-connection-info-wire-shape.md).

## The switch is server-driven — there is nothing to disable client-side

`.HOGEJEIPPPD : int` = **`Photon = 0`, `GameServer = 1`**.

`.OBNIPMNHCIE` is a static holder with paired backends and two int statics:
`+0x00` = **desired**, `+0x04` = **active**; then `+0x08`/`+0x10` the two `GDDFOMHBNHP` room-network
services, plus paired `PKLFDEMCFPI` and `FPALJLNJIEN`.

- **`OBNIPMNHCIE.IDPELGOBGIG(.KOGGADGCBLL experiments)` `0x8264F30`** — sets *desired*:
  ```
  ebx = 0                                   ; Photon
  if (experiments != null) {
      ax = word [experiments + 0x2c]        ; Nullable<bool> ShouldUseGameServerNetworking
      cl = (ah == 1)                        ; HasValue
      if (al & cl) ebx = 1                  ; GameServer
  }
  statics[+0x00] = ebx
  ```
  **Both `HasValue` and `Value` are required.** Null `Experiments`, missing key, `null`, or `false`
  all land on **Photon**.
- `OBNIPMNHCIE.INBJOPOHCLE(.HOGEJEIPPPD)` `0x8264FD0` — commits to *active* (`statics[+0x04]`) and
  raises the `Action<GDDFOMHBNHP, GDDFOMHBNHP>` changed event if the resolved impl differs.
- `OBNIPMNHCIE.IPLEMLLPEGL()` `0x8265080` — returns the **GameServer** service iff
  `statics[+0x04] != 0`, else the Photon one.
- `OBNIPMNHCIE.FMOCEBEBIGN()` `0x8264DA0` — `desired != active`, i.e. "switch pending"; driven by
  `LANHDGEKFKP.MoveNext` `0x8282AE0`, which tears the old backend down then calls `LBFFCGFIOFK()`.

`KCGBOHDOJEH.IPLEMLLPEGL()` `0x82626E0` is the per-instance facade that just tail-jumps to the
static one — everything routes through it.

## What to send

`Experiments` is the 9th key of **`GET player/connection-info`** (svc 4 Matchmaking,
[player-connection-info-wire-shape](../../wire-shapes/references/endpoints/player-connection-info-wire-shape.md)); type `.KOGGADGCBLL`, formatter `EGCILJEEEOK` `.ctor
0x7AB9D60`, 8 keys, `ShouldUseGameServerNetworking` **last** (field `+0x2c`):

```json
"Experiments": { "ShouldUseGameServerNetworking": true }
```

## The three `GDDFOMHBNHP` implementors

`.NOOJNOPBIDK` (Photon), **`.OBMHNGEHIBL`** (GameServer — its `.ctor` `0x82735F0` is the *only*
constructor of `.FOMDMHNNNKP`, the NGO session that speaks the `RR_JoinRequest`/`RR_JoinResponse`
protocol in [rr-named-message-room-protocol](rr-named-message-room-protocol.md)), and `.KCGBOHDOJEH` (the routing facade).

## Why the room-load step names mislead

`RoomManagerInitialRoomLoad.ConnectToPhoton()` (`MFGDEGACJIJ.MoveNext` `0x8A19E60`) and
`JoinRoomLoadWithPhoton()` (`ILBDJKIIACC.MoveNext` `0x8A10D50`) are **stale names** — there is no
GameServer-named step. `ConnectToPhoton()` builds a `.JPPIHLEDPEB` connect-args record from the
connection-info DTO (`PGJPCIACLPG.CPGAKPHLDCA` `0x89FDEE0`, a straight 8-field copy) and then makes
an **interface** call on `.ALHBKIJJAOM` (`0x8A1A161: call r10`), whose `GPBEKHFFAAD` is
`ConnectToRoomInstance`. Implementors include the Photon client (`.AHBLEMDIPAN` behind
`.JFNFEPCDGIJ`) and **`.BAOFAOBLAMJ` = TachyonClient** (log literal
`'TachyonClient.ConnectToRoomInstance: {0} - {1}'` `0xD075B60`, in `GPBEKHFFAAD` `0x82781E0`).
Note TachyonClient ships inside the assembly `RecRoom.Networking.PhotonImpl.Runtime`, so "Photon" in
a name proves nothing about which backend runs.

**How to apply:** flipping this flag only moves the **room networking service**. Photon Chat / Photon
Voice app-ids are separate keys in the same DTO and are not governed by it — expect some Photon
traffic to remain, and judge success by whether `RR_JoinRequest` (`NamedMessageType 5`, op 100)
arrives, not by Photon going silent.
