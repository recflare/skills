# Voice roster account id

> How recflare-2025 knows who is in voice — the Dissonance SESSION roster from the voice server, keyed by the ACCOUNT ID as a decimal string. VoiceServerId plays no part.

Traced **2026-08-21** on build `20250718.01`, after the voice server reached a stable connection.
Follows [ngo-fork-batch-and-approval](ngo-fork-batch-and-approval.md) / [dissonance-voice-connection](dissonance-voice-connection.md).

**`VoiceServerId` is not involved.** The roster is Dissonance's own session membership, which the
**voice server** owns and broadcasts.

## Identity: account id as a decimal string

`DissonancePlayerVoiceInput.Awake` (`0xAB4D30`) reads an `ObscuredInt` off the local account object
(`PHCHGFEEEMG.EBADLLKHNNM`, `0x7C97500`, backing field `<MLFGMOGIIBB>`), calls `Int32.ToString`, and
passes it to `DissonanceComms.set_LocalPlayerName` (`0x31422F0`) — the **only** call site.

So `DissonanceComms.LocalPlayerName == accountId.ToString()`. Each client announces its own name in
the Dissonance handshake; the server never assigns it.

## Roster: standard Dissonance session events

`DissonanceComms` keeps `Players` / `FindPlayer` and the events `OnPlayerJoinedSession`,
`OnPlayerLeftSession`, `OnPlayerEnteredRoom`, `OnPlayerExitedRoom` (`0x31415xx`-`0x31419xx`). All
server-driven. Dissonance instantiates one `PlaybackPrefab` — `RecRoomVoicePlayback` — per remote
session player.

## Binding back to the in-room avatar

`RecRoomVoicePlayback.GBJLCHBJMEK` (`0xC34130`):
`BaseVoicePlayback.get_PlayerName()` -> **`Int32.TryParse`** -> **`Player.GetFromAccountId`**
(`0x2098150`) -> `CrossRoomVoiceChatManager.GetOrCreateDissonanceVoiceOutput` (`0x140C990`) ->
`DissonancePlayerVoiceOutput.InitFromVoicePlayback` (`0xAB6490`). It retries across several frames,
then logs **`"RecRoomVoicePlayback: Failed to find player for voice playback: {0} after {1}
updates."`** — the diagnostic for "voice arrived for someone the game doesn't have". A second
literal, `"You should never get a voice playback for your own local account..."`, confirms the name
is the local account id.

## Positions do NOT come from the voice server

**`DissonanceComms.TrackPlayerPosition` (`0x3140970`) has ZERO callers.** Rec Room does not use
Dissonance positional tracking; the AudioSource is attached to the avatar and Unity 3D audio does
the spatialisation. So the voice server needs no position data — the game (Photon/Luxon) already
places every avatar, and voice is joined to it purely by account id.

**Not established:** the Dissonance **room** names used by `VoiceBroadcastTrigger` /
`VoiceProximityBroadcastTrigger` / `VoiceReceiptTrigger`. Those are Unity-serialized component
fields, so they live in prefab/scene assets, not `GameAssembly.dll` — same limitation as the
`DiscoverySectionPrefabMapping[]` table in [discovery-sections-pagesource-wire-shape](../../wire-shapes/references/endpoints/discovery-sections-pagesource-wire-shape.md). A server
must still implement Dissonance's room/channel routing.
