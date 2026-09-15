# Subroom data save endpoint

> Wire shape the client expects from POST rooms/{id}/subrooms/{id}/data (the room-save endpoint) — envelope + room + subRoomDataSave; and why 'Failed to save room' names nothing useful

Build installed 2026-07-28 at `C:\Games\recflare-client`. Recovered statically from a fresh
Il2CppDumper dump (see [launch-validation-boot-failure](../../../rr-client-bringup/references/launch-validation-boot-failure.md) for the xref/`names.py` procedure).

## The call chain

`RoomPersistenceManager.AttemptRoomSaveIfGameNotRunning` (unobfuscated) is the ONLY thrower of
`IONCKFICKKG("Failed to save room")` — it wraps the whole save chain, so that message identifies
**nothing** about which step failed. The chain is
`IFMKBNCAMNG.EACCIOALNHB` → closure `<UploadRoomDataBlobAndSyncReload>b__0` (name survives
obfuscation) which awaits, in order: a `bool`, `PAMGELIFHKC → Task<OBBHEEKAPFJ>` (blob upload),
`OFOEAHKNLMP → Task<DGIDKKNDMIP>` (**this POST**), then a protobuf reload message `LFEPDAHLEPH`.
`IFMKBNCAMNG` lives in `RecRoom.RoomLoading.Runtime.dll`, `IONCKFICKKG` in
`RecRoom.Promises.Runtime.dll`.

The rejection funnel in the Player.log stack is `PHLHFLLLDLK<T>.LEFPGJEKFGF(string)` — the RecRoom
promise's `Reject(string)`, i.e. the API layer turned a **string** error into the exception.

## Response shape (Utf8Json, three casings per key: camel / Pascal / all-lower)

Envelope is `GEMGLHHAKOD<T>` : `JNGDGCDCOJN<T>` : `FOKGKPOPJPF` — `success` (bool), `error`
(string), `value` (T). Same envelope family as [photon-connection-info-endpoint](photon-connection-info-endpoint.md).

```json
{ "success": true, "error": null, "value": {
    "room": { /* full standard Room object */ },
    "subRoomDataSave": {
      "subRoomDataSaveId": 0,        // long
      "subRoomId": 0,                // long
      "unityAssetId": null,          // string
      "unityAsset": null,            // string
      "unityAssetHash": null,        // string
      "dataBlob": "",                // string
      "dataBlobHash": "",            // string
      "savedByAccountId": 0,         // int?
      "savedOnPlatform": 0,          // enum? Steam=0 Oculus=1 PlayStation=2 Xbox=3 RecNet=4 IOS=5 GooglePlay=6 Standalone=7 Pico=8 (All=-1)
      "savedOnDeviceClass": 2,       // enum? Unknown=0 VR=1 Screen=2 Mobile=3 VRLow=4 Quest2=5
      "description": null,           // string
      "createdAt": "..."             // DateTime (non-nullable)
    } } }
```

`room` is the ordinary Room DTO (`LCEKCFEIEGJ`), keys in declaration order: `DataBlob`,
`DataBlobHash`, `SubRooms`, `Roles`, `Tags`, `LoadScreens`, `PromoImages`, `PromoExternalContent`,
`RoomId`, `IsDorm`, `MaxPlayerCalculationMode`, `MaxPlayers`, `PersistenceVersion`,
`CloningAllowed`, `DisableMicAutoMute`, `DisableRoomComments`, `EncryptVoiceChat`, `ToxmodEnabled`,
`LoadScreenLocked`, `IsDeveloperOwned`, `Name`, `Description`, `ImageName`, `WarningMask`,
`CustomWarning`, `CreatorAccountId`, `State`, `Accessibility`, `SupportsLevelVoting`, `IsRRO`,
`SupportsScreens`, `SupportsWalkVR`, `SupportsTeleportVR`, `SupportsVRLow`, `SupportsQuest2`,
`SupportsMobile`, `SupportsJuniors`, `MinLevel`, `CreatedAt`, `Stats`, `RankingContext`.

Formatter ctor RVAs used: envelope `0x4CB21E0`, `subRoomDataSave` `0x3435180`, `room` `0x259F470`.
The **trailing `mov` run** in `names.py` output is `____stringByteKeys` = declaration order; the
earlier `lea` run is hash-table build order and is NOT the field order.

## Confirming which step actually fails

The exception is generic, so read the wire: `[Advanced] Debug = true` makes `SendRequestPatch` log
`[HTTP] ->` / `[HTTP] <-` with bodies for every request, including the blob upload that precedes
this POST. BestHTTP ignores the Windows proxy, so mitmproxy sees nothing.
