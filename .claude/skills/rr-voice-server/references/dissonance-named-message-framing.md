# Dissonance named message framing

> How Dissonance rides recflare-2025's forked NGO — NamedMessage.Hash is a ushort NamedMessageType (1 = DissonanceToServer, 2 = DissonanceToClient), then an int length, then a STOCK Dissonance packet with magic 0x8bc7.

Read **2026-08-22** from build `20250718.01`, after the client reached a stable plaintext NGO
session. Follows [ngo-fork-batch-and-approval](ngo-fork-batch-and-approval.md) and [voice-roster-account-id](voice-roster-account-id.md).

## NamedMessage is NOT stock

`Unity.Netcode.NamedMessage` fields: **`Hash` is a `ushort`** @struct 0, `SendData` @8,
`m_ReceiveData` @0x10. Stock NGO uses a `ulong` name hash — **anyone parsing 8 bytes here eats 6
bytes of payload.** `NamedMessage.Deserialize` (`0x9735E00`) is literally
`reader.ReadBytesSafe(&this.Hash, 2)` then `m_ReceiveData = reader`. No length, no 64-bit hash.

The fork replaced the hash with an enum, `Unity.Netcode.NamedMessageType : ushort`, members in
declaration order: `ReservedDoNotUse`, **`DissonanceToServer`**, **`DissonanceToClient`**,
`RRClientToServerProxied`, `RRServerToClientProxied`, `RRClientToServer`, `RRServerToClient`,
`AIManagement`, `AIData`.

Verified from the call sites, not from the enum order:
- `NfgoCommsNetwork.IDPOCNBEHOE` (`0x3134810`) sends with `edx = 1`, clientId 0 -> **client→server = 1**
- `NfgoCommsNetwork.MHANLGJOHAB` (`0x3134AD0`) sends with `edx = 2` -> **server→client = 2**
- `OJNKHPPBHMF` (= NfgoServer) registers handler for **1**; `DBAAJJACPCL` (= NfgoClient) for **2**

**A server replies on hash 2.**

`NfgoCommsNetwork.MHOMAMOENOO` (`0x3134E50`) packs the Dissonance byte[] with
`FastBufferWriter.WriteValueSafe(byte[])`, which prefixes an **int32 length**.

So: `u16 NamedMessageType | i32 length | <Dissonance packet>`.

## The Dissonance packet is STOCK

Magic **`0x8bc7`** confirmed as an immediate at 10 sites. `FPIFOKCNKJE` = **PacketWriter** (9 header
writers + `Write` overloads `KENBDFDJMJH`, byte writer `PBFCHHMDOMN` `0x3149FB0`);
`AJLLGKJMHIO` = **PacketReader** (`BKJPKJLIHFE` `0x3136430` does the magic check).

Message-type bytes **read as immediates** from the writers: 1, 2, 3, 4, 6, 9, 0x0A, 0x0B — which
line up exactly with stock Dissonance `MessageTypes` (RemoveClient 0, ClientState 1, VoiceData 2,
TextData 3, HandshakeRequest 4, HandshakeResponse 5, ErrorWrongSession 6, ServerRelayReliable 7,
ServerRelayUnreliable 8, DeltaChannelState 9, HandshakeP2P 10, HeartbeatP2P 11, RemoveClientP2P 12).
Stock is further corroborated by verbatim asset log strings ("Discarding packet - incorrect magic
number.", "Received handshake response from server, joined session '{0}'", "Kicked from session -
wrong session ID. Mine:{0} Theirs:{1}").

**So use the Placeholder Software Dissonance source as the protocol reference** — it is not forked.

## Tooling gap worth remembering

Dissonance's networking core lives at ~`0x48F0000`, `0x4EBD000`, `0x6434000` — regions
**`methods.pkl` does not index**, so `callxref`/`mxref` attribute those hits to absurd names
(SmtpFailedRecipientsException, JsonException…). The *addresses* are right; the *names* are the
previous indexed method. Do not trust a name whose ref offset is tens of KB past the method start.
