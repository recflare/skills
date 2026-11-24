# RR typed-value codec (`SerializedType`) and the forwarded-malformed-frame crash (2026)

> RR serializes polymorphic values (event payloads, the instantiate dict, join req/resp, broadcast
> voice/chat) with a **type-tagged codec** `RecRoom.Networking.RYVCIIOUZLU`, keyed by the **`SerializedType`
> byte enum (valid range 0–61)**. Each value on the wire = `[SerializedType : u8][payload]`; containers
> carry a count and each element is itself type-tagged. A **wrong inner length/count desyncs the
> `FastBufferReader`**: it finishes a value at the wrong offset, reads the next byte as a `SerializedType`,
> and throws `Cannot deserialize {id}. There is no corresponding registered type` for any id > 61. Because
> the relay **forwards a client's event payload verbatim to every other client**, one malformed frame from
> one client throws in *every* receiver's NGO inbound handler — a flood + abandoned temp buffers hangs the
> main thread (~29 s ANR) and the process dies. Build `20260323.14`. Derived **2026-11-11** from a live
> crash (bot account 16 replaying event-28 frames captured in another instance crashed a real player's
> client).

## The codec

`RecRoom.Networking.RYVCIIOUZLU` (static registry):
- `Deserialize(FastBufferReader) → object` **0x9ad48b0** — reads `SerializedType` byte, `TryGetValue` in a
  `Dictionary<SerializedType,…>`, dispatches; miss → `String.Format("Cannot deserialize unregistered type {0}")`.
- `XQIXCNAGDPI(object, FastBufferWriter)` **0x9ad8ec0** / `DIJQDPKNCFT(object, Type, FastBufferWriter)` — writers.
- `ELLIMRVBZIG(reader, Func<Type,int,IList>)` **0x9ad4c60** — the container (Array/List) reader; throws
  `"Cannot deserialize {0}. There is no corresponding registered type"` — **the crash string**.
- `.cctor` **0x9ad9680** registers each `(Type, SerializedType, SerializeMethod, DeserializeMethod)` via
  `FDJJCSKQNEJ`.

### `SerializedType : byte` — valid 0–61 (the wire type tags)
```
0 Null · 1 Object · 2 Array · 3 List · 4 Bool · 5 Byte · 6 SByte · 7 Char · 8 Short · 9 UShort ·
10 Int · 11 UInt · 12 Long · 13 ULong · 14 Float · 15 Double · 16 String · 17 Vector2 · 18 Vector3 ·
19 Vector3Int · 20 Vector4 · 21 Quaternion · 22 Color · 23 Color32 · 24 ByteArray · 25 SByteArray ·
26 CharArray · 27 ShortArray · 28 UShortArray · … · 42 Guid · 43 ViewId · 44 ObjectNetworkId ·
45 UncompressedQauternion · 46 QuadControlPoint · 47 ToolHolderInfo · 48 LegacyToolCleanupImplSettingOverrides ·
49 StringIndexedMapPair · 50 ByteReadOnlyMemory · 51 ManagedUGCStorefrontData · 52 Dictionary ·
53 RoomJoinRequest · 54 RoomJoinResponse · 55 IntDictionary · 56 StringDictionary · 57 CircuitsVec3 ·
58 CircuitsQuat · 59 CV2RecNetImageWrapper · 60 BroadcastVoiceData · 61 BroadcastChatData
```
Any inbound tag > 61 is garbage from a desynced reader, never a real message. (`SerializedType.Byte = 5`
is the common first byte — it is NOT the event-28 discriminator; see below.)

## The crash signature
Inbound NGO named message → `CustomMessagingManager.InvokeNamedMessage` →
`RecRoom.Networking.HVFCFCFDHNM.VRFMZCRQJYV(ulong sender, FastBufferReader)` **0x9a98b00** →
`RYVCIIOUZLU.Deserialize`. A 2 s flood of `Cannot deserialize <id>` with **ids far past 61** (observed:
66,75,88,110,119,132,141,154,176,185,198,207,221,233,242 — effectively random) then a native crash
(`UnityPlayer!UnityMain`, no PDB). Per-read bounds checks (`ReadValueSafe`/`ReadBytesSafe`) throw cleanly,
so the kill is the **volume**, not a single OOB read.

**Cause:** a forwarded frame whose inner length/count prefix does not match its payload. Replaying bytes
captured in another instance is one trigger (instance-specific view-ids/lengths), and the relay rewriting
the sender/actor without recomputing the length prefix is another. **This is also the likely mechanism of
the "crash everyone in the room" griefing reports** (the 8172+9444 "crash everyone but u" keybind): a
deliberately length-mismatched typed value, forwarded verbatim, desyncs every receiver.

## Server-side mitigation (relay)
The relay must **length-validate a forwarded named/typed message against the datagram and drop it** rather
than proxy it. Recompute/verify every length and count prefix after any actor/view rewrite. A single
client must never be able to emit a frame that desyncs other receivers.

## Not this codec: event 28
`RR_NetworkSynchronization` (event 28) movement is **bit-packed** (`BitPacker`, see
[avatar-movement-stream-event-28-2026](avatar-movement-stream-event-28-2026.md)), NOT `RYVCIIOUZLU`. The
`[i32 N][u8 05]…` header's `05` is a sync-format discriminator, not a `SerializedType`. A malformed event-28
frame crashes others only indirectly — by carrying a wrong **entry length** in the proxied batch, so the
batch reader advances wrong and reads the *next* entry's content through `RYVCIIOUZLU` on a bad offset.
