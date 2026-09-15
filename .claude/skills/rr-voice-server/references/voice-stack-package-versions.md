# Voice stack package versions

> Dissonance/NGO/LiteNetLib package fingerprint for recflare-2025 voice — assembly versions are stripped, so fingerprint by API surface; NGO is trimmed to messaging only (7 message types).

Determined **2026-08-21** on `C:\Games\recflare-2025` (build `20250718.01`) via
[recflare-2025-metadata-carve](../../il2cpp-analysis/references/recflare-2025-metadata-carve.md). Companion to [dissonance-voice-connection](dissonance-voice-connection.md).

**Assembly versions are useless here** — the metadata assembly table (offset `0x2D87A24`, stride 64,
405 entries; version ints at `+0x28..+0x34`) reports **0.0.0.0** for every one of these, which is
what Unity emits for asmdef/UPM-compiled assemblies. Also no PE version resource on
`AudioPluginDissonance.dll`. Fingerprinting must be done from API surface — see
`il2cpp-2025/imgtypes.py` (added 2026-08-21), which lists an image's types from the carved metadata.

The six voice assemblies: `DissonanceVoip.dll` (266 types), `DissonanceNFGO.dll` (10),
`Unity.Netcode.Runtime.dll` (105), `Netcode.Transports.LiteNetLib.dll` (116, LiteNetLib itself
bundled inside), plus `RecRoom.Networking.NetcodeImpl.Runtime.dll` and
`RecRoom.Foundation.Netcode.Runtime.dll` glue.

**Dissonance ≈ 8.x.** Floor markers: `Dissonance_Audio_BgDenoise_Enabled`/`_Amount` and
`Dissonance_RnnoiseProcessFrame returned false` → the RNNoise background denoiser, **added in
Dissonance 8.0**; `Packages/com.placeholder-software.dissonance/Plugins/Dissonance/Resources` → UPM
layout; `Dissonance.Integrations.Unity_NFGO.NfgoCommsNetwork` → the NFGO integration. Native side:
`AudioPluginDissonance.dll` + `fvad.dll` (WebRTC VAD).

**NGO = 1.x, at least 1.6.0, definitely not 2.x.** Present: `NetworkConnectionManager`,
`NetworkMessageManager`, `ComponentFactory`, `IRealTimeProvider`/`RealTimeProvider`,
`NetworkManagerHooks`, `DeferredMessageManager`, `MessageVersionData` — the 1.6.0 internal refactor.
Absent: `RpcTarget`, `AnticipatedNetworkVariable`, distributed-authority/`SessionOwner` types (2.x).

## The big structural finding

**NGO is trimmed to connection + messaging + serialization + transport.** There is **no
`NetworkObject`, `NetworkBehaviour`, `NetworkVariable`, spawning, or scene management** in the image.
The complete message set is only **seven** types:

`ConnectionRequestMessage`, `ConnectionApprovedMessage`, `DisconnectReasonMessage`, `NamedMessage`,
`UnnamedMessage`, `ServerLogMessage`, `TimeSyncMessage`

plus `CustomMessagingManager` / `NamedMessageType`. So Rec Room appears to have rewired Dissonance's
NFGO integration off `NetworkBehaviour` RPCs onto raw named/unnamed messages.

**Why this matters:** a compatible voice server does **not** need NGO object replication — only the
connection handshake, time sync, and a named-message relay over LiteNetLib UDP. That is a far
smaller target than "reimplement NGO".

**Limit:** exact patch versions (8.4.2 vs 8.7.1, 1.6.0 vs 1.8.1) are not recoverable from a
name-obfuscated build offline — only the family and the floor.
