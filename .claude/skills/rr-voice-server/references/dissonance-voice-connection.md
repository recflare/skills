# Dissonance voice connection

> Voice in recflare-2025 is Dissonance, gated on a VoiceConnectionInfo from POST voiceconnection/{id} on the CHAT service (svc 9) — without it the client silently skips voice entirely.

Investigated **2026-08-21** on `C:\Games\recflare-2025` (build `20250718.01`) via
[recflare-2025-metadata-carve](../../il2cpp-analysis/references/recflare-2025-metadata-carve.md), from "voice not working + Dissonance in the logs".

The build ships **both** stacks: Photon Voice (`PhotonVoiceNetwork`, `PhotonVoiceAppId`, `[PV]`
logging) **and** Dissonance (48 literals, `AudioPluginDissonanceNative`, `DissonanceComms`,
`Dissonance_Audio_*` settings). The active path needs a **`VoiceConnectionInfo`**; the dev audio
overlay prints **"Voice: No VoiceConnectionInfo, not using Dissonance"** when it is absent — that
line is the diagnostic for this exact failure (`RRUI.Data.DevDebugAudioModel`, `0x2654D00`).

## The endpoints — all on the CHAT service (svc 9), not a voice host

| call | method | verb | returns |
| --- | --- | --- | --- |
| `voiceconnection/{id}` | `PNAHAINBHAH.GKIIBOHJNFO(long)` `0x7CB8170` | **POST** | `DJBHKNJMNON` |
| `voiceconnection/presences/{a}/{b}` | `KIJPEHNHGEP(long,long)` `0x7CB9DE0` | **GET** | `HLNHDNNENAH` |
| `voiceconnection/connectionerror/{a}/{b}` | `HBFIPCIBONG(long,long,string)` `0x7CB8950` | **POST** | void promise |

Matching error literals: "Failed to GetOrCreateVoiceConnection",
"Failed to GetVoiceConnectionPresences", "Failed to ReportVoiceConnectionError".

**`DJBHKNJMNON` (the VoiceConnectionInfo)** — formatter `MMPLEDGJHDO` ctor `0x7653770`, bare, 9 keys:
`VoiceConnectionId` long 0x10, `AccountId` int 0x18, `ChatThreadId` long 0x20, `AuthToken` string
0x28, `Address` string 0x30, `ServerName` string 0x38, `Cluster` string 0x40, `Version` string 0x48,
`CreatedAt` DateTime 0x50.

**`HLNHDNNENAH` (presences)** — formatter `HNCLGFLNKPP` ctor `0x764CE90`, 2 keys:
`VoiceConnectionId` long 0x10, `AccountIds` list 0x18.

## What it implies

- The id is a **chat-thread id**, not a room instance — the DTO carries `ChatThreadId`, the calls sit
  on the Chat service, and the only caller (`JCIFDIFBKDP.NFOKLONLGEP`, `0x186DCC0`) is the **party
  voice call** path ("Can not start a new voice call while an existing call is on", "This room does
  not support Party Voice calls").
- `Address` / `ServerName` / `Cluster` / `AuthToken` describe a **dedicated voice server you must
  run** — unlike Photon Voice, which is cloud-hosted via `PhotonVoiceAppId` from
  `player/connection-info` ([photon-connection-info-endpoint](../../wire-shapes/references/endpoints/photon-connection-info-endpoint.md)). The client validates the address:
  "Invalid connection address info", then "Failed to start Voice Chat Client"
  (`GHJODKALAPK.HBJNEGCPIBD`, `0x827ED70`, in `RecRoom.Networking.PhotonImpl.Runtime`).
- `Version` almost certainly pairs with the `VoiceServerVersion` field the client already sends in
  the matchmaking body ([matchmake-v2-room-wire-shape](../../wire-shapes/references/endpoints/matchmake-v2-room-wire-shape.md)).
- Dissonance tuning keys are built from the prefixes `Voice.Dissonance.` and
  `Voice.Dissonance.global.` (`KPLAILPNMHO`, `0x1413AD0`/`0x1413B40`) — they come from the config
  service, so `api/config/v2` can carry them.

**Not derivable from the client:** what wire protocol that voice server speaks. That lives inside
Dissonance's comms layer / the native plugin, not in RecNet DTOs.

## In-room proximity voice: it comes from `player/connection-info`, and it is NOT Photon

Traced **2026-08-21** after the user reported Photon realtime + Photon chat working but in-room
voice dead ("worked in 20230414").

`player/connection-info` (Matchmaking, svc 4) returns `Matchmaking.OHDFEFMFJLJ` — formatter
`EPKMPBCGLGG` ctor `0x7ABAFF0`, **9 keys**, 8 strings plus an object:

`PhotonAuthToken` 0x10, `PhotonRealtimeAppId` 0x18, `PhotonVoiceAppId` 0x20, `PhotonChatAppId` 0x28,
`PhotonRegion` 0x30, `PhotonRoomId` 0x38, **`VoiceConnectionInfo` string 0x40**,
**`VoiceServerId` string 0x48**, `Experiments` (`KOGGADGCBLL`) 0x50.

**`VoiceConnectionInfo` is a plain `"<ip>:<port>"` string**, not an object and not a Photon id. The
voice client `GHJODKALAPK.HBJNEGCPIBD` (`0x827ED70`, in `RecRoom.Networking.PhotonImpl.Runtime`
despite the name) does exactly:

```
String.Split  ->  IPAddress.Parse(part0)  ->  UInt16.Parse(part1)
   -> configure Netcode.Transports.LiteNetLib.LiteNetLibTransport
   -> Unity.Netcode.NetworkManager.StartClient()
```

Failure to parse throws `Exception("Invalid connection address info")`; a failed connect logs
"Failed to start Voice Chat Client".

**So proximity voice is Dissonance over Unity Netcode for GameObjects on a LiteNetLib UDP
transport — a server you host yourself.** `PhotonVoiceAppId` is vestigial on this build; that is why
a server written for the 20230414 shape keeps realtime and chat working (their app ids are still
read) while voice silently no-ops: `VoiceConnectionInfo` comes back null and the client logs
"Voice: No VoiceConnectionInfo, not using Dissonance".

The `voiceconnection/*` endpoints on the Chat service are the **party-voice** equivalent; proximity
voice does not use them.

## No flag re-enables Photon Voice (checked 2026-08-21)

- The voice-client abstraction `FMMPBLPGMMH` (`RecRoom.Networking.PhotonImpl.Runtime`, line 1224) is
  an **interface with exactly one implementation**, `GHJODKALAPK`. There is no Photon-Voice
  implementation to switch to; it is resolved by DI (`LMKONLJOAEP<FMMPBLPGMMH>`) with a single
  candidate.
- `GHJODKALAPK.HBJNEGCPIBD` has **no conditional** — it goes straight from `VoiceConnectionInfo` to
  Split → `IPAddress.Parse` → `UInt16.Parse` → `LiteNetLibTransport` → `NetworkManager.StartClient()`.
- **No voice-backend config key exists.** The only `Voice.*` prefixes are `Voice.Dissonance.` and
  `Voice.Dissonance.global.`; there is no `Voice.Backend` / `Voice.UsePhoton`.
- The Photon Voice PUN package is still compiled in (33 methods on `PhotonVoiceNetwork`, plus Rec
  Room's own glue inside `Photon.Voice.Unity.VoiceConnection` — the "RecNetID" log line), but
  `ConnectAndJoinRoom` and `ConnectUsingSettings` have **zero call sites**. (Caveat: a call scan
  cannot see virtual or Unity-lifecycle dispatch, so this is strong evidence, not proof.)
- `PhotonVoiceAppId` survives as a field on `player/connection-info` but nothing selects it for room
  voice — it is vestigial on this build.

**Only untested lever:** the `Experiments` object on connection-info carries
`ShouldUseGameServerNetworking` (bool?, `KOGGADGCBLL.KLOMDPFBAIP`, getter `0xF0BE10`). Its getter has
no direct callers (inlined), so its effect could not be confirmed statically — but it is free to
try, since the server controls it. Full Experiments key set: `NetworkTransformSyncInterval`,
`ShouldUseUnreliableOnChange`, `R2RuntimeStaticBaking`, `R2AutoEmbodiment`,
`R2RuntimeStaticBakingMinShapeThreshold`, `ShouldAvoidDiscontinuityRPCs`,
`ShouldAvoidRedundantDiscontinuity`, `ShouldUseGameServerNetworking`.

## Confirmed live (2026-08-21): the client really does dial LiteNetLib, and the transport is ENCRYPTED

With a dummy IP in `VoiceConnectionInfo` the client reached
`FailedToConnectToVoice / COADIPLNFKJ: Client has already disconnected`, which confirms the whole
chain:

- **Room load has a dedicated voice stage.** Enum `IPDOKLDLFDN`: Success 0,
  FailedToConnectToRegion 1, FailedToConnectToRoom 2, FailedToSpawnPlayer 3, Cancelled 4,
  **FailedToConnectToVoice 5**, ForceDisconnected 6. Reaching 5 means Photon region + room already
  succeeded.
- **The address parsed.** A bad format would raise "Invalid connection address info" instead.
- `COADIPLNFKJ : DMAEGBDNIKG : Exception` is declared immediately above `GHJODKALAPK` in
  `RecRoom.Networking.PhotonImpl.Runtime`, and is thrown by `BAOFAOBLAMJ.FJDKONPENFO` (`0x8278070`)
  via `TaskCompletionSource.TrySetException` — a connect that was in flight when the transport
  reported disconnect.
- **`BAOFAOBLAMJ` is the NGO voice session wrapper**: it references
  `Netcode.Transports.LiteNetLib.LiteNetLibTransport` and calls
  **`LiteNetLibTransport.RecRoom_SetEncryptionInfo(ulong, byte[])`** — a Rec Room-added method on
  the transport (note the `RecRoom_` prefix, `Netcode.Transports.LiteNetLib.cs:178`).

**So the LiteNetLib transport is Rec Room-modified and encrypts voice traffic** — a stock
NGO + LiteNetLib server will not interoperate. Alongside it, `DMIBBCKIGCG.EAIDKGJNAPP()` builds an
`AesCryptoServiceProvider` from **hardcoded** base64 constants (32-byte key
`QJwT58FheuEIXNlbnvEGlcC6n7Ury+BYFid4LNWLEJ4=`, 16-byte IV `GTLFaIAoniLKqHEJFIhcGw==`) plus a
1024-bit RSA **public** key literal, all at `0x827A800`-ish in the same class. Ties in with
`EncryptVoiceChat` on the room DTO / `RoomInstance`.

**Next unknowns:** where the per-connection key passed to `RecRoom_SetEncryptionInfo` comes from
(likely decrypted/verified with those constants), and whether `VoiceServerId` feeds it.

## Not P2P — the client can never be the voice server (checked 2026-08-21)

Asked whether the IP from `player/connection-info` might be another player's machine. **No.**

- `Unity.Netcode.NetworkManager$$StartHost` (`0x973CDA0`) and `$$StartServer` (`0x973CF80`) have
  **zero call sites**. `$$StartClient` (`0x973CBB0`) has two: `BAOFAOBLAMJ$$GPBEKHFFAAD`
  (`0x82781E0`) and `GHJODKALAPK$$HBJNEGCPIBD` (`0x827ED70`). (Direct `E8`/`E9` scan; these are
  non-virtual, so there is no vtable path.)
- `LiteNetLibTransport$$StartServer` (`0x735D150`) is implemented but only reachable through those,
  so it is dead code.
- `LiteNetLibTransport$$StartClient` (`0x735CE30`) calls `NetManager.Start(0, 0)` — **ephemeral
  port, no listen bind** — then `NetManager.Connect(address=[transport+0x30], port=u16
  [transport+0x28], connectData)` (`JAOBJOHMHKI$$EHPNKKJDIMD` @ `0x73560A0`). Purely outbound.
- `NfgoCommsNetwork$$Update` (`0x3135110`) does read `IsClient` / `IsConnectedClient` / `IsServer` —
  that is stock Dissonance NFGO deciding Host vs Client — but `get_IsServer` (`0x973DC50`) reads
  `[[nm+0x98]+0x48]+0x10`, a flag only set on the StartServer/StartHost path. Always false here.

NGO is star topology (server relays), so Dissonance-over-NGO is client-server regardless of what
Dissonance supports elsewhere.

**`BAOFAOBLAMJ` is `TachyonClient`** — its literals are `"TachyonClient.ConnectToRoomInstance: {0}
- {1}"`, `"Invalid connection address info"`, `"Payload serialized {0}"`, and
**`"TachyonClient.SetDedicatedServerConnectionRequestPayload"`** — the client's own string says
*DedicatedServer*. Fields: `0x10` NetworkManager, `0x40`/`0x48` `RSACryptoServiceProvider`, `0x50`
`AesCryptoServiceProvider`, `0x58` byte[] — the handshake state from
[voice-handshake-key-exchange](voice-handshake-key-exchange.md).

So the voice address is **operator infrastructure you must host**, consistent with `VoiceServerId` +
`VoiceServerVersion` being negotiated through matchmaking. See
[litenetlib-fork-encrypt-layer](litenetlib-fork-encrypt-layer.md) for what that server has to speak on the wire.
