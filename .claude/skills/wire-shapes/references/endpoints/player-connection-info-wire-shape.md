# Player connection info wire shape

> GET player/connection-info?roomInstanceId= (Matchmaking, svc 4) for recflare-2025 — bare 9-key DTO carrying the Photon ids plus VoiceConnectionInfo and VoiceServerId.

Derived **2026-08-21** from `C:\Games\recflare-2025` (build `20250718.01`) via
[recflare-2025-metadata-carve](../../../il2cpp-analysis/references/recflare-2025-metadata-carve.md). Supersedes the older [photon-connection-info-endpoint](photon-connection-info-endpoint.md) note for
this build.

`GET https://match.<host>/player/connection-info?roomInstanceId={long}` — **GET** (`HttpMethod`
statics `+0x08`), service **4 = Matchmaking**, one optional query param. Client entry
`LGHENDGDHBM(long? roomInstanceId, CancellationToken)`, state machine `INLCHIIPELK$$MoveNext`
(`0x7D31440`).

Response is a **bare** `Matchmaking.OHDFEFMFJLJ` (formatter `EPKMPBCGLGG` ctor `0x7ABAFF0`), 9 keys:

| key | type | offset |
| --- | --- | --- |
| `PhotonAuthToken` | string | 0x10 |
| `PhotonRealtimeAppId` | string | 0x18 |
| `PhotonVoiceAppId` | string | 0x20 |
| `PhotonChatAppId` | string | 0x28 |
| `PhotonRegion` | string | 0x30 |
| `PhotonRoomId` | string | 0x38 |
| `VoiceConnectionInfo` | string `"<ip>:<port>"` | 0x40 |
| `VoiceServerId` | string | 0x48 |
| `Experiments` | object (`KOGGADGCBLL`) | 0x50 |

`Experiments`: `NetworkTransformSyncInterval` float?, `ShouldUseUnreliableOnChange` bool?,
`R2RuntimeStaticBaking` bool?, `R2AutoEmbodiment` bool?,
`R2RuntimeStaticBakingMinShapeThreshold` int?, `ShouldAvoidDiscontinuityRPCs` bool?,
`ShouldAvoidRedundantDiscontinuity` bool?, `ShouldUseGameServerNetworking` bool?.

## `VoiceServerId`

- Pairs with **`VoiceServerVersion`**, which the client *sends* in the `matchmake/v2/room` body
  ([matchmake-v2-room-wire-shape](matchmake-v2-room-wire-shape.md)): client advertises the version it supports, server allocates a
  voice server and returns its **id** here alongside the **address** in `VoiceConnectionInfo`.
- The client's own offline factory `OHDFEFMFJLJ.LOONDNAGBFO()` (`0x7D47590`) sets the Photon app-ids
  to the literal `"offline"` but sets **both `VoiceConnectionInfo` and `VoiceServerId` to `""`** —
  so empty string is the canonical "no voice" value and is definitely accepted.
- The voice client entry is `FMMPBLPGMMH.HBJNEGCPIBD(string, string, string)` — **three** strings —
  and its log line is `"VoiceChatClient.voiceConnectionInfo: {0} - {1}"` printing the first two, so
  `VoiceServerId` is carried into the voice client next to the address.

**Not pinned:** what the voice client actually does with `VoiceServerId` (session key to the voice
server vs telemetry only), and what the third string parameter is. Its property getter is a
**shared stub** (`mov rax,[rcx+0x48]; ret`, 21 unrelated callers across Protobuf/CSharp-binder code)
and the voice client is invoked through a DI-resolved interface, so neither getter-xref nor
call-scan resolves it. Determining it needs a runtime probe.

**How to apply:** `il2cpp-2025/typeslots.py <TypeName>` (added 2026-08-21) finds the metadata-usage
slots for a type so `mxref.py` can list every method that touches it — that is how this DTO was
narrowed to just three methods (resolver `.cctor`, formatter Deserialize, offline factory).
