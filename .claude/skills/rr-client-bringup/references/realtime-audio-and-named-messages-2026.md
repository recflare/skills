# In-world audio and oversized NamedMessages (2026 build)

> **In-world audio ships a BLOB NAME, not audio bytes** — `AudioPlayer.RpcPlaySample(string
> blobName, float audioLength, string audioName)`. So audio playback is **not** the source of the
> 50–180 KB `NamedMessage`s.
> **No clock is involved in audio playback.** Nothing in the audio path transmits a timestamp;
> position is a replicated `float PlaybackPosition` plus an argument-less
> `RpcInvokeOnChangePlaybackPosition()`. The LiteNetLib pong epoch (1970 vs 0001) is therefore
> irrelevant to audio.
> ⚠️ Which op carries the oversized messages is **NOT established** — see the open question at the
> bottom and the one byte-level datum that would settle it.

Investigated **2026-10-13** against build `20260323.14`
([[recflare-2026-static-index]] → `C:\Games\recnet-patcher\il2cpp-2026\`).

## `Unity.Netcode.NamedMessageType : ushort` — the inner named kinds

```
0 ReservedDoNotUse        3 RRClientToServerProxied   6 RRServerToClient
1 DissonanceToServer      4 RRServerToClientProxied   7 AIManagement
2 DissonanceToClient      5 RRClientToServer          8 AIData
```

## `RecRoom.Networking.NetworkEventCode : byte` — the full event code table

```
  4 OMSendPacket                 25 RR_CreationOpResponse        103 RR_PlayerUpdate
  5 RR_OutOfBandMessage          26 RR_CreationOp_Unchecked      104 RR_RemotePlayerJoined
  6 RR_FastForwardMarker         27 RR_MasterLockBlockComplete   105 RR_RemotePlayerLeft
  7 RR_SelfJoinMarker            28 RR_NetworkSynchronization    106 RR_Leave
 10 RR_DebugOp                   29 RR_NetworkInstantiate        107 RR_StartBroadcast
 11 RR_CachedEvent               30 DO_NOT_USE                   108 RR_StopBroadcast
 20 RRRoomRequestEvent           31 RR_BulkInstantiate           109 RR_ScreenShareData
 21 RRRoomRequestFailedResponseEvent 32 RR_Destroy                110 RR_BroadcastVoiceData
 22 RRBufferedRoomEvent          33 RR_BulkDestroy               111 RR_BroadcastChatData
 23 RRClearBufferedRoomEvent     34 RR_TransferOwnership         112 RR_GameServerDebug
 24 RR_CreationOp                35 RR_OwnershipUpdate
                                 36 RR_RPC
```

⚠️ **There is no in-world-audio event code.** The only audio-ish codes are `RR_ScreenShareData 109`
and `RR_BroadcastVoiceData 110` (Dissonance voice / screenshare). In-world audio rides `RR_RPC 36`
and the persistence path.

## In-world audio: `RecRoom.Core.Creation.SandboxGizmos.AudioPlayer`

`py msig.py AudioPlayer` — 91 methods. The entire networked surface:

| member | note |
|---|---|
| `RpcPlaySample(string blobName, float audioLength, string audioName)` | **a blob name + length, no samples** |
| `RpcPlaySFX(Guid guid, float volume, float playbackSpeedShift)` | built-in SFX by guid |
| `RpcPlayGenAIAudio(string blobName)` | likewise a blob name |
| `RpcStop()` / `RpcPause()` | no arguments |
| `RpcInvokeOnChangePlaybackPosition()` | **no arguments** — a bare "position changed" notify |
| `float PlaybackPosition` (+ `PlaybackPosition_Get/_Set`) | replicated scalar |
| `float ClipSpeed`, `float SpeedModifier`, `bool IsPlaying` | replicated scalars |
| `OnPhotonPlayerConnected(PlayerId)` | **late-joiner push** — the owner re-sends state on connect |
| `SerializeTo(...)` / `DeserializeFrom(...)` | room-save persistence |

**So playback synchronisation is: a replicated position float, re-pushed on change and on late
join. No timestamp, no clock, no interpolation.** A receiver seeks to whatever position it is told,
when it is told. That predicts **choppy, not silent** — jitter in RPC delivery becomes audible
stutter, and a dropped position update leaves a receiver running free until the next one.

⚠️ The audio bytes themselves are fetched out-of-band by `blobName` (storage/CDN), not pushed
through the game socket. Confirm with a proxy capture: a `RpcPlaySample` should be followed by an
HTTP blob fetch, not by a large NamedMessage.

## Where raw audio *does* get serialised — the Holotar sampler

`RecRoom.Protobuf.AudioStreamData` carries **raw PCM**: a `.Format` enum
(**`Uncompressed = 0`, `Opus = 1`**), sample-rate/frame-size ints, and a
**`RepeatedField<float>`** with a `FieldCodec<float>` — i.e. one protobuf `float` per sample. At
4 bytes/sample that is ~176 KB per second of mono 44.1 kHz uncompressed, which is the right order of
magnitude for the 52–178 KB messages.

Its container is `RecRoom.Protobuf.AudioSamplerPersistenceData`, and the code around it is
`RecRoom.Core.Creation.Holotars.AudioSampler.SerializeTo` `0x1DC5D30` /
`DeserializeFrom` `0x1DC4370` (error literals `'Error serializing Audio Sampler {0}: Data already
specified.'`, `'Error deserializing Audio Sampler {0}: data empty.'`). **This is the
persistence/creation path, not a stream** — a recorded clip being saved or shipped once.

**Strong candidate, not proven:** the oversized messages are an `AudioSampler` recording travelling
as `RR_CreationOp 24` / `RRBufferedRoomEvent 22`, or a CircuitsV2 snapshot (see below).

## Client-side size knobs (remote config, defaults NOT in the binary)

`RecRoom.CircuitsV2.Config.GameConfig.IXMQGHUAZTK` `0x12DFF60` reads these string configs and
`Int32.TryParse`s them into `Nullable<int>` overrides:

```
UGC.CircuitsV2.RpcMessageSplitSizeBytes          <- client-side RPC chunking
UGC.CircuitsV2.SnapshotThresholdBytes
UGC.CircuitsV2.ActionCompressionThresholdBytes
UGC.CircuitsV2.InvisibleChipLimitBytes
UGC.CircuitsV2.StopEventExecutionAfterSingleFailure
UGC.CircuitsV2.ImmediateDynamicInitialization
```

**So CircuitsV2 RPCs *are* chunked, and the split size is server-configurable** — which means a
too-large CircuitsV2 RPC is a config problem, not a protocol one. Setting
`UGC.CircuitsV2.RpcMessageSplitSizeBytes` below the 16384/16390 server cap is worth trying.

⚠️ **The defaults are not readable from the binary.** `get_RpcMessageSplitSizeBytes` `0x12E05D0` is
`return override.HasValue ? override.Value : <field +0x38>`, and `+0x38` is a **serialized
ScriptableObject field** — i.e. it lives in a Unity asset, not in code. Pull it from the game's
asset bundles, or just set the remote config explicitly and stop depending on it.

Related literal: `'Failed to compress the serialized world payload'` — the world payload has a
compression path, consistent with `ActionCompressionThresholdBytes`.

## ⚠️ What this investigation could NOT establish

**Whether anything reads NGO network time.** `NetcodeImpl.GZVDHGCUOFA` does wrap it —
`double GetLocalTime()`, `double GetServerTime()`, `int GetRoundTripTime()`,
`NetworkConfig GetNetworkConfig()` — but `GetLocalTime` and `GetServerTime` **share one RVA**
(`0x9A946A0`), and `GetRoundTripTime`/`SendCustomMessage` resolve to the shared trivial-stub RVAs
`0xD0A4D0`/`0xD0A4C0`. Folded stubs make both `callxref` and name lookup useless here, and
`NetworkManager.get_ServerTime` `0xB043FB0` reporting **0 call sites** is explained by inlining
rather than by disuse. **Do not read "0 call sites" as "unused" for a trivial getter on this build.**

By the same token, **the LiteNetLib pong clock could not be ruled out globally**: all 36
`LiteNetLib.*` types are obfuscated (`LiteNetLib.CQOVEHYRLVH`, `.MLEQXSNXGHS`, …), so searching for
`RemoteTimeDelta` / `RemoteUtcTime` by name proves nothing. *For audio specifically* it does not
matter — no timestamp is transmitted on that path at all — but a claim about the rest of the game
would need the obfuscated `NetPeer` equivalent read field-by-field.

`NetworkConfig.TickRate`'s configured value was **not** recovered; it is set on a
`NetworkConfig` asset/instance, not as a code immediate. `GZVDHGCUOFA.GetNetworkConfig()` is the
accessor to chase if it matters.

## The one datum that would close Q1

The server rejects before reading the inner kind, so the journal cannot name the op. **Log the first
~16 bytes of one rejected payload.** The layout after the NGO `NamedMessage` header is the
`NamedMessageType` (ushort, so `03 00` or `05 00`) followed by the Rec Room framing whose next byte
is the `NetworkEventCode` from the table above. One hex prefix from the 178 KB message identifies the
op outright and turns every "strong candidate" here into a fact.
