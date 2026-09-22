---
name: rr-voice-server
description: Implement or debug a self-hosted Rec Room voice server - the Tachyon/NGO connect handshake and RSA/AES key exchange, the RecRoomClientEncryptLayer datagram format, the forked NGO batch header and approval message, and how Dissonance packets are relayed. Use when voice will not connect, the roster is empty, or you are writing the voice server itself.
---

# Rec Room voice server

Voice is a **separate server you must host**. It is not Photon and not the room server. The client
will silently run with no voice at all if anything upstream is missing, so the first question is
always *which* of the four layers failed.

## The four layers, outermost first

1. **Gate.** The client only starts voice if `POST voiceconnection/{chatThreadId}` on the **Chat
   service (svc 9)** returns a `VoiceConnectionInfo`. No info, no voice, and the only evidence is the
   log line `No VoiceConnectionInfo, not using Dissonance`.
2. **Transport.** LiteNetLib, stock except for a `PacketLayerBase` called
   `RecRoomClientEncryptLayer` that wraps **every datagram including the handshake**.
3. **Session.** A forked Netcode for GameObjects - non-standard batch header, and a
   `ConnectionApprovedMessage` carrying an extra `Payload` string.
4. **Voice.** Stock Dissonance packets relayed inside NGO named messages.

Work down that list. A failure at layer 1 looks exactly like a failure at layer 4 from the client's
UI, and only the log line distinguishes them.

## Start here

- **Writing the server from scratch:** read `voice-handshake-key-exchange`, then
  `recroom-encrypt-layer-format`, then `ngo-fork-batch-and-approval`, then
  `dissonance-named-message-framing`. That is the full stack bottom-up.
- **Nobody hears anybody, roster empty:** `voice-roster-account-id` - identity is the account id as
  a decimal string, and the server's own session roster is the roster.
- **Two rooms hearing each other:** `voice-instance-routing` - the connect payload carries no room
  or instance id, so you must map account to instance yourself.
- **You cannot read the client's handshake fields:** `voice-rsa-key-swap` - one static-field write
  swaps the hardcoded public key for yours, with a built-in self-test.
- **A departed player keeps logging "Failed to find player for voice playback":**
  `voice-stale-playback-on-leave` - the voice server never removed them from the Dissonance
  session; broadcast RemoveClient (type 0). The client cannot clean the playback up itself.

## Traps

- `ExtraPacketSizeForLayer = 9` is a **reservation, not the framed size** - a plaintext packet grows
  by 1 byte, not 9.
- The NGO batch hash **is** enforced, and `BatchCount` is not where stock NGO puts it.
- Package versions cannot be read from assembly metadata (all stripped to 0.0.0.0); fingerprint by
  API surface instead.

## References

| Reference | What it settles |
|---|---|
| [dissonance-named-message-framing](references/dissonance-named-message-framing.md) | How Dissonance rides recflare-2025's forked NGO — NamedMessage.Hash is a ushort NamedMessageType (1 = DissonanceToServer, 2 = DissonanceToClient), then an int length, then a STOCK Dissonance packet with magic 0x8bc7. |
| [dissonance-voice-connection](references/dissonance-voice-connection.md) | Voice in recflare-2025 is Dissonance, gated on a VoiceConnectionInfo from POST voiceconnection/{id} on the CHAT service (svc 9) — without it the client silently skips voice entirely. |
| [litenetlib-fork-encrypt-layer](references/litenetlib-fork-encrypt-layer.md) | recflare-2025's bundled LiteNetLib is stock for ConnectAccept/ProcessConnectAccept — the fork is a PacketLayerBase called RecRoomClientEncryptLayer with ExtraPacketSizeForLayer = 9 on EVERY datagram. |
| [ngo-fork-batch-and-approval](references/ngo-fork-batch-and-approval.md) | recflare-2025's forked NGO wire format — NetworkBatchHeader is 24 bytes with BatchCount MOVED to offset 16, and ConnectionApprovedMessage gained a `Payload` string that carries the Tachyon Carrot JSON into NetworkManager.RecRoom_ConnectionInfo. |
| [recroom-encrypt-layer-format](references/recroom-encrypt-layer-format.md) | The RecRoomClientEncryptLayer wire format in recflare-2025 — a TRAILING marker byte, 0x11 plaintext (+1 byte) or 0x2A encrypted (+9 = 8 nonce + marker); inbound is strip-only for 0x11. |
| [voice-handshake-key-exchange](references/voice-handshake-key-exchange.md) | The full recflare-2025 voice (Tachyon/NGO) connection handshake and AES key exchange — JSON payloads PAFCNOLGBNM in / PMFAAFNFMAL out, gated on an RSA keypair whose PUBLIC half is hardcoded in the client. |
| [voice-instance-routing](references/voice-instance-routing.md) | The Tachyon voice connect payload carries NO room/instance id — only AI (account id, plaintext). Route voice by mapping account->instance at VoiceConnectionInfo issuance, or by giving each instance its own endpoint. |
| [voice-roster-account-id](references/voice-roster-account-id.md) | How recflare-2025 knows who is in voice — the Dissonance SESSION roster from the voice server, keyed by the ACCOUNT ID as a decimal string. VoiceServerId plays no part. |
| [voice-rsa-key-swap](references/voice-rsa-key-swap.md) | How to swap the hardcoded Tachyon RSA public key for your own so the server can decrypt CKA/CIA and read AT — single static-field write at BAOFAOBLAMJ..ctor 0x82795E0, plus the decrypt recipe and a free self-test via VB. |
| [voice-stack-package-versions](references/voice-stack-package-versions.md) | Dissonance/NGO/LiteNetLib package fingerprint for recflare-2025 voice — assembly versions are stripped, so fingerprint by API surface; NGO is trimmed to messaging only (7 message types). |
| [voice-stale-playback-on-leave](references/voice-stale-playback-on-leave.md) | A repeating "RecRoomVoicePlayback: Failed to find player for voice playback: {id} after {n} updates" after someone leaves means the VOICE server never removed them from the Dissonance session — fix is to broadcast RemoveClient (type 0); the client cannot clean up the playback object itself. |
