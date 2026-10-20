---
name: rr-room-networking
description: Understand how the Rec Room client joins and talks to a room/session server - choosing Photon vs the dedicated NGO GameServer backend, the shared RR event-code enum, the named-message room protocol and its join handshake, PUN-style RPC dispatch, and Photon peer timeout behaviour. Use when a client will not join a room, drops after N seconds, or you are implementing the room server.
---

# Rec Room room networking

The client supports **two** room backends and picks between them from a server-controlled flag.
Decide which one you are on before debugging anything else - the packet formats have nothing in
common.

## Which backend

`Experiments.ShouldUseGameServerNetworking` inside `GET player/connection-info` selects it. The
reader requires `HasValue && Value`, so **missing, null or false all mean Photon**. See
`photon-vs-gameserver-backend-switch`.

## The dedicated (NGO) path

`rr-named-message-room-protocol` has the frame layout and the join handshake
(`RR_JoinRequest 100` -> `RR_JoinResponse 101`). The server->client direction accepts a **closed set**
of op codes; anything else is dropped without a log, which is the usual reason a hand-written server
"connects" but nothing happens.

`rr-event-codes-and-rpc-dispatch` covers the op byte itself. The same enum serves both backends, so
an event code learned from a Photon capture is valid on the NGO path and vice versa. RPC **method
names are unobfuscated strings** on the wire - the single most useful fact here, because it means you
can read a capture without any symbol work.

## The Photon path

`photon-peer-timeout-config` explains the disconnects. The short version: the timeout that fires is
the **resend-count** branch, not the wall-clock one, because `timeoutTime` is rebased on every
resend. Consequence - **making the server retransmit faster does not help**, and on timeout the
client sends no Disconnect command at all, so the server sees only silence.

## References

| Reference | What it settles |
|---|---|
| [photon-peer-timeout-config](references/photon-peer-timeout-config.md) | Rec Room's Photon peer settings and the exact TimeoutDisconnect trigger — DisconnectTimeout 10000 ms and SentCountAllowance 7 are ctor defaults never overridden; the trigger is (sentCount > allowance) OR (now > cmd.timeoutTime), and timeoutTime RESETS on every resend so the COUNT branch is what fires. |
| [photon-vs-gameserver-backend-switch](references/photon-vs-gameserver-backend-switch.md) | The client picks Photon vs the NGO/dedicated 'GameServer' room backend from Experiments.ShouldUseGameServerNetworking in GET player/connection-info — OBNIPMNHCIE.IDPELGOBGIG requires HasValue && Value, so anything missing/null/false means Photon. |
| [rr-event-codes-and-rpc-dispatch](references/rr-event-codes-and-rpc-dispatch.md) | NILCDNBAPNO is the shared RR event-code enum for BOTH Photon RaiseEvent and the NGO named-message op byte (RR_RPC = 36); RPCs inside it are dispatched PUN-style by ViewId + method-name STRING, and RPC method names are unobfuscated. |
| [rr-named-message-room-protocol](references/rr-named-message-room-protocol.md) | The RR room protocol riding NGO named messages: NamedMessageType 5/6 (RRClientToServer/RRServerToClient) wrap a 1-byte NILCDNBAPNO op code; join = RR_JoinRequest 100 -> RR_JoinResponse 101; the client's direct server->client handler accepts only codes 7/101/102/103/104/105. |
| [buffered-room-event-echo-stall-2026](references/buffered-room-event-echo-stall-2026.md) | A room load is 32 loopback round trips through the room server (RRBufferedRoomEvent op 22 out on nType 5, relayed back on nType 4) with NO client retransmit and a 180 s wait, so losing any one relay fails the whole load as FailedToSpawnPlayer 8702. CORRECTED: loss is NOT uniform - it concentrates on the single hop out of DESERIALIZE_OBJECTS, whose latency scales with the deserialized-object count (57 ms at 28 objects, 358 ms median at 352, 22% never arriving). Also records a second, separate episodic connection-wide 1-23 s stall. |
