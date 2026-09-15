# LiteNetLib fork encrypt layer

> recflare-2025's bundled LiteNetLib is stock for ConnectAccept/ProcessConnectAccept — the fork is a PacketLayerBase called RecRoomClientEncryptLayer with ExtraPacketSizeForLayer = 9 on EVERY datagram.

Answered **2026-08-21** for a third-party NGO/LiteNetLib server whose stock `ConnectAccept` was
being silently ignored. Carve: [recflare-2025-metadata-carve](../../il2cpp-analysis/references/recflare-2025-metadata-carve.md); context
[voice-handshake-key-exchange](voice-handshake-key-exchange.md).

**LiteNetLib's internals are obfuscated in this build** — only
`Netcode.Transports.LiteNetLib.LiteNetLibTransport` kept its name. Types must be found by shape.
Map: `EPGOLFIPCGO` = NetConnectAcceptPacket, `PCPCKKAAELA` = NetPacket, `EDHDDFDJJPM` =
FastBitConverter, `JAOBJOHMHKI` = NetManager (75 fields/62 methods), `MOLHAOHJIGG` = NetPeer,
`GDIPEMDOCEO` = NetStatistics, `MGHAOMEMAHF` = **RecRoomClientEncryptLayer**.

**ConnectAccept matches stock exactly.** `FromData` (`0x734FF00`): `cmp dword [pkt+0x18], 0xF; jne
-> null` (Size **15**); `ToInt64(raw,1)`; `raw[9]` connectionNumber with `>= 4 -> null`
(MaxConnectionNumber **4**); `raw[10]` isReused `> 1 -> null`; `ToInt32(raw,11)` peerId `< 0 ->
null`. Fields: 0x10 long ConnectionTime, 0x18 byte ConnectionNumber, 0x1c int PeerId, 0x20 bool
PeerNetworkChanged. `Make` (`0x734FE10`): `new NetPacket(property=6, 0)`, time at offset 1,
`raw[9]=connectNum`, peerId LE at 11..14, does **not** write `raw[10]`.

**ProcessConnectAccept matches stock** (inlined in `JAOBJOHMHKI$$DBGKGFFJCCP` at `0x7355ADE`):
FromData != null → `peer.ConnectionState == 2` (Outgoing) → `accept.ConnectionTime ==
peer.ConnectTime` (peer field 0xD8) → set connectNum, `RemoteId` (0x12C), zero timeSinceLastPacket
(0x40), state = **4** (Connected), raise Connect event.

## The actual fork

`LiteNetLibTransport.Initialize` (`0x735C1E0`) logs **`"Adding RecRoomClientEncryptLayer"`**, news up
`MGHAOMEMAHF`, sets its **`ExtraPacketSizeForLayer` (base field 0x10) = 9**, and passes it as
NetManager's **third ctor argument** (`new NetManager(listener, layer)`). There is exactly one
NetManager ctor and one call site.

`MGHAOMEMAHF`: `byte[]` key at 0x18 — **same field slug `DAKIIEIEKNI` as the `byte[]` parameter of
`LiteNetLibTransport.RecRoom_SetEncryptionInfo(ulong, byte[])`** — plus a static
`RandomNumberGenerator`. `ProcessInboundPacket` = `GKKBCNBDNNF` (`0x735DF90`, 3 args);
`ProcessOutBoundPacket` = `FMHFAJOCCHG` (`0x735D760`, the largest).

**Consequence:** every datagram — handshake included — goes through the layer, which reserves 9
extra bytes. A stock 15-byte ConnectAccept has no layer framing, so it is dropped before
`FromData` ever runs. That is the silent-ignore-and-retry, and it is why a synthetic stock client
(no layer) connects to the same server fine.

**Not established:** `NetConstants.ProtocolId` from the image (const ints live in
`fieldDefaultValues`, not walked yet) and the layer's exact 9-byte format.
