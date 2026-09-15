# Photon connection info endpoint

> Shape of the client's `player/connection-info` API (Utf8Json), which supplies per-join Photon config; and how PhotonPatches clobbers it

Build 20230616. Room join calls **`player/connection-info`**; on failure the client throws
`LCAMIKNEHDP`, which `RoomManager` reports as `FailedToSpawnPlayer / (Code 8700)`.

## Response shape

Envelope is generic `BICLOIGIJHA<T>`; its `success` bool is the field the client tests
(`cmp byte ptr [rdi+0x10], 0` in `RecNet.Matchmaking.IHBBLOLGDOM$$MoveNext`).

```json
{ "success": true, "error": null, "value": {
    "photonAuthToken": "", "photonRealtimeAppId": "", "photonVoiceAppId": "",
    "photonChatAppId": "", "photonRegion": "us", "photonRoomId": "",
    "voiceServerId": "", "voiceConnectionInfo": "" } }
```

All eight `value` fields are `string`. **No host field** — the Photon host can only come from
`AppSettings.Server`, never from this endpoint.

Each name is registered in **three casings** (`photonAuthToken` / `PhotonAuthToken` /
`photonauthtoken`), same for `success`/`value`/`error`. Nothing else matches — no snake_case.

## ⚠️ `PhotonPatches` clobbers most of this

`PAAJLJEEAKL.PKPMKAKCJLO(LFCEINHHKOK)` is the seam converting connection-info → `AppSettings`
(`LFCEINHHKOK` holds four readonly strings whose obfuscated names are IDENTICAL to four of the DTO's
properties). Our postfix runs **after** and unconditionally overwrites:

- `AppIdRealtime` / `AppIdVoice` / `AppIdChat` ← `[Photon]` config
- `FixedRegion = "us"`, `UseNameServer = true`, `Protocol = Udp`

So server-returned app ids and region are **discarded**. Blanking the config does NOT opt out — the
postfix would assign empty strings. Letting the endpoint drive requires making the override
conditional on the config value being non-empty.

`Server`/`Port` are only touched when `[Advanced] Enabled Advanced Settings = true`; with it false
the host is left alone entirely.

## How the shape was recovered

Serializer is **Utf8Json** — identified by generated-formatter field shape, not namespace
(obfuscation strips it): `AutomataDictionary`-like `IEnumerable<KeyValuePair<string,int>>` +
`byte[][]` = `____keyMapping` + `____stringByteKeys`. Those tables are built from plain **string
literals** in the formatter's `.ctor`, so disassembling it and resolving rip-relative refs against
`stringliteral.json` yields the wire names. Script: `scratchpad/il2cpp/names.py <ctor_rva>`.

Formatters: `FMNOLOJAMLI` (payload, ctor RVA `0x3BAE1B0`), `LOBOLJAOGGN` (envelope, `0x427ACA0`).
DTO `Matchmaking.NBDPJBOGNGD`; see [launch-validation-boot-failure](../../../rr-client-bringup/references/launch-validation-boot-failure.md) for the xref tooling.
