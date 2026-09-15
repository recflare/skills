# RR named message room protocol

> The RR room protocol riding NGO named messages: NamedMessageType 5/6 (RRClientToServer/RRServerToClient) wrap a 1-byte NILCDNBAPNO op code; join = RR_JoinRequest 100 -> RR_JoinResponse 101; the client's direct server->client handler accepts only codes 7/101/102/103/104/105.

Derived **2026-09-01** from build `20250718.01` via [recflare-2025-metadata-carve](../../il2cpp-analysis/references/recflare-2025-metadata-carve.md), answering the
Tachyon server agent's "client sends nType=5 and blocks" question. Extends
[dissonance-named-message-framing](../../rr-voice-server/references/dissonance-named-message-framing.md) (which covered only types 1/2) and
[ngo-fork-batch-and-approval](../../rr-voice-server/references/ngo-fork-batch-and-approval.md).

## `Unity.Netcode.NamedMessageType : ushort` — full space

`ReservedDoNotUse 0`, `DissonanceToServer 1`, `DissonanceToClient 2`, `RRClientToServerProxied 3`,
`RRServerToClientProxied 4`, **`RRClientToServer 5`**, **`RRServerToClient 6`**, `AIManagement 7`,
`AIData 8`.

Registrations actually present in the client:
- `DBAAJJACPCL` (NfgoClient) → **2**; `OJNKHPPBHMF` (NfgoServer) → **1** (Dissonance).
- `CLEIAIFNJOC` → **7** and **8** (OpenAI realtime / `MOHJDANJFLI`).
- **`FOMDMHNNNKP`** (the RR NGO session, holds `INetworkManager` + `LiteNetLibTransport`) →
  **4 → `POBPNHBKBDN(ulong, FastBufferReader)` `0x8270280`** and
  **6 → `AGMAPFJIFMH(ulong, FastBufferReader)` `0x826B110`**.
  Both registered in `FOOAOOLIEBB` `0x826CFE0` and `NLGAHIHDCPE` `0x826F5B0`.
- Nothing registers 3 or 5 client-side — those are **client→server only**.

## Framing: `u16 NamedMessageType | u8 NILCDNBAPNO op | INetworkSerializable body`

The op byte is a **raw single byte** (`AGMAPFJIFMH` MemCpy's 1 byte then `reader.Position++`), NOT
bitpacked. `.NILCDNBAPNO : byte`:

`OMSendPacket 4`, `RR_OutOfBandMessage 5`, `RR_FastForwardMarker 6`, **`RR_SelfJoinMarker 7`**,
`RR_DebugOp 10`, `RR_CachedEvent 11`, `RRRoomRequestEvent 20`, `RRRoomRequestFailedResponseEvent 21`,
`RRBufferedRoomEvent 22`, `RRClearBufferedRoomEvent 23`, `RR_CreationOp 24`,
`RR_CreationOpResponse 25`, `RR_CreationOp_Unchecked 26`, `RR_MasterLockBlockComplete 27`,
`RR_NetworkSynchronization 28`, `RR_NetworkInstantiate 29`, `DO_NOT_USE 30`, `RR_BulkInstantiate 31`,
`RR_Destroy 32`, `RR_BulkDestroy 33`, `RR_TransferOwnership 34`, `RR_OwnershipUpdate 35`, `RR_RPC 36`,
**`RR_JoinRequest 100`**, **`RR_JoinResponse 101`**, **`RR_RoomUpdate 102`**,
**`RR_PlayerUpdate 103`**, **`RR_RemotePlayerJoined 104`**, **`RR_RemotePlayerLeft 105`**,
`RR_Leave 106`.

## The join handshake

**Client → server**, `FOMDMHNNNKP.NLGAHIHDCPE` `0x826F5B0` (tail at `0x826F8F0`):
`new FastBufferWriter(0x100)`; `WriteValueSafe<NILCDNBAPNO>(100)`;
`WriteValueSafe<FHJNNGKCIPB>(body)`; send with **`namedMessageType = 5`** (`mov r9d,5` `0x826F9F9`),
clientId 0, **`NetworkDelivery = 4`** (ReliableFragmentedSequenced) (`0x826F9FF`).

`.FHJNNGKCIPB` = **RoomJoinRequest** (the name is confirmed by `LLOHCFOAIOA.RoomJoinRequest = 54`).
Its `NetworkSerialize` was read directly out of `WriteValueSafe<FHJNNGKCIPB>` `0x3C4BB40` — **three
unconditional `SerializeValue` calls, in declaration order, no mask, no version byte**:
1. `string Name` — `SerializeValue(ref string, oneByteChars = false)` (`r8d = 0`) ⇒
   **`u32 charCount` + 2 bytes/char UTF-16LE**
2. `string PlatformId` — same encoding
3. `LGIGIHLJAPI Properties`

That decodes the captured 68 bytes exactly:
`05 00 | 64 | 09 00 00 00 | "A\0l\0s\0o\0D\0e\0v\0i\0n\0" | <u32 len + UTF-16 SteamID64> | <5 bytes props>`.

**Server → client**: `AGMAPFJIFMH` `0x826B110` requires `senderClientId == 0` (else LogError
*"Received a message from client {0} instead of the server"*), reads the op byte, and switches:

| op | body type | handler |
|---|---|---|
| 7 `RR_SelfJoinMarker` | **none** (enqueued with a null payload) | inline `0x826B1F5` |
| 101 `RR_JoinResponse` | `.OPGKNONENAJ` | `DNLJNAMGFNH<OPGKNONENAJ>` `0x3C46990` |
| 102 `RR_RoomUpdate` | `.OCKHMGFANHD` | `0x3C468C0` |
| 103 `RR_PlayerUpdate` | `.EECOLELLELP` | `0x3C467F0` |
| 104 `RR_RemotePlayerJoined` | `.EECOLELLELP` | `0x3C467F0` |
| 105 `RR_RemotePlayerLeft` | `.EAKJGHCMEFB` | `0x3C46720` |
| anything else | — | LogError *"Received unknown server message code {0}"* |

**Every other op code must arrive on the PROXIED channel (`NamedMessageType 4`)**, whose handler
`POBPNHBKBDN` `0x8270280` does not switch — it just enqueues whatever code it reads.

All handlers only `EHECDIEOHBA(code, int, object)` `0x826C540`, which boxes into `.CIOJAGADNJA`
`{byte Code, int, object Payload}` and appends to a locked list at `FOMDMHNNNKP+0x30`, drained on
the main thread.

## Body layouts (field order = declaration order, verified for the request)

- `.OPGKNONENAJ` **RoomJoinResponse**: `bool Accepted`, `.OCKHMGFANHD Room`.
- `.OCKHMGFANHD` **RoomUpdate**: `.JIHACJLNFKE Mask` (byte), `ulong MasterClient`,
  `ulong PreviousMasterClient`, `.EECOLELLELP[] Players`, `.LGIGIHLJAPI Properties`.
- `.EECOLELLELP` **PlayerUpdate**: `.FMEPBLGLEHD Mask` (byte), `ulong ClientId`, `string Name`,
  `int AccountId`, `string PlatformId`, `.LGIGIHLJAPI Properties`.
- `.EAKJGHCMEFB` **RemotePlayerLeft**: `ulong ClientId`, `.OCKHMGFANHD Room`.

Both `Mask` fields are **bit flags**, which strongly implies the two update structs serialize
*conditionally* on the mask (the request struct has no mask and is unconditional):
- `.JIHACJLNFKE : byte` — `None 0`, `MasterClient 1`, `Players 2`, `Properties 4`,
  `PreviousMasterClient 8`, **`All 7`** (deliberately excludes PreviousMasterClient),
  `MasterClientChange 9`.
- `.FMEPBLGLEHD : byte` — `None 0`, `Name 1`, `AccountId 2`, `PlatformId 4`, `Properties 8`,
  `All 15`.

⚠️ **Not yet proven:** the conditional-serialization hypothesis and the `LGIGIHLJAPI` encoding.
`NetworkSerialize` for these structs is generic over `BufferSerializer<T>` and resolved through the
RGCTX, so its code address is not statically reachable with the current tooling (`methods.pkl` does
not index it, and `.OPGKNONENAJ::NetworkSerialize` has 3 methodSpecs but **no metadata-usage slot**).
Settle it from a capture instead.

## `LGIGIHLJAPI` — the property bag

A struct wrapping `Dictionary<object, object>`. Values are variant-tagged with
`.LLOHCFOAIOA : byte` (60 members): `Null 0, Object 1, Array 2, List 3, Bool 4, Byte 5, SByte 6,
Char 7, Short 8, UShort 9, Int 10, UInt 11, Long 12, ULong 13, Float 14, Double 15, String 16,
Vector2 17, Vector3 18, Vector3Int 19, Vector4 20, Quaternion 21, Color 22, Color32 23,
ByteArray 24 … Color32Array 41, Guid 42, ViewId 43, ObjectNetworkId 44, UncompressedQauternion 45,
QuadControlPoint 46, ToolHolderInfo 47, LegacyToolCleanupImplSettingOverrides 48,
StringIndexedMapPair 49, ByteReadOnlyMemory 50, ManagedUGCStorefrontData 51, Dictionary 52,
PhotonHashtable 53, **RoomJoinRequest 54**, **RoomJoinResponse 55**, IntDictionary 56,
StringDictionary 57, CircuitsVec3 58, CircuitsQuat 59`.
Read/write delegates: `.EFJIOMPEFOO (object, FastBufferWriter)` / `.PCEKNCHNDEJ (FastBufferReader) -> object`.
In the captured JoinRequest an empty bag is **5 bytes** — consistent with a 1-byte flag plus an
`i32 count = 0` (order unconfirmed).
