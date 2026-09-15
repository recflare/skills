# Photon peer timeout config

> Rec Room's Photon peer settings and the exact TimeoutDisconnect trigger — DisconnectTimeout 10000 ms and SentCountAllowance 7 are ctor defaults never overridden; the trigger is (sentCount > allowance) OR (now > cmd.timeoutTime), and timeoutTime RESETS on every resend so the COUNT branch is what fires.

Derived **2026-09-02** from build `20250718.01` via [recflare-2025-metadata-carve](../../il2cpp-analysis/references/recflare-2025-metadata-carve.md), for the
server-side agent debugging Photon client timeouts. Photon SDK types are **unobfuscated**
(`ExitGames.Client.Photon.*`), so this layer reads easily. Related:
[photon-vs-gameserver-backend-switch](photon-vs-gameserver-backend-switch.md).

## Peer defaults — all from `PhotonPeer..ctor` `0x75356A0`, none overridden

| field | offset | value | site |
|---|---|---|---|
| `SentCountAllowance` | +0x78 | **7** | `0x7535752` |
| `disconnectTimeout` | +0x88 | **10000 ms** | `0x7535771` |
| `InitialResendTimeMax` | +0x7C | 400 ms | `0x7535759` |
| `TimePingInterval` | +0x80 | 1000 ms | `0x7535760` |
| `mtu` | +0x90 | 1200 | `0x753577B` |
| `ChannelCount` | +0x72 | 2 | `0x753574C` |
| `SequenceDeltaLimitResends` | +0x5C | 100 | `0x753573E` |
| `SequenceDeltaLimitSends` | +0x60 | 75 | `0x7535745` |
| `quickResendAttempts` | +0x71 | **0** (never written) | — |
| `CommandBufferSize` / `LimitOfUnreliableCommands` | +0x10 / +0x14 | **never written → 0** | — |

A scan of PhotonPeer's entire code range (`0xA62800`–`0x75363D0`) finds **no other write** to +0x78
or +0x88. `disconnectTimeout` is private with only `get_DisconnectTimeout` `0x7535DB0`, so it cannot
be changed from outside at all. `SentCountAllowance` is a public field, so RR *could* write it from
elsewhere, but no such write was found.

## The exact TimeoutDisconnect trigger — `EnetPeer.SendOutgoingCommands` `0x75246F0`

Per outstanding reliable command, and **only once it is already due for resend**
(`now > cmd.commandSentTime + cmd.roundTripTimeout`, `0x7524AA6`):

```
0x7524AE8  eax = cmd.commandSentCount            ; NCommand +0x40 (byte)
0x7524AED  cmp eax, photonPeer.SentCountAllowance ; PhotonPeer +0x78
0x7524AF0  jle -> time check ; else cl = 1        ; COUNT branch => timeout
0x7524B0B  eax = watch.ElapsedMilliseconds
0x7524B10  cmp eax, cmd.timeoutTime               ; NCommand +0x48
0x7524B14  setg cl                                ; TIME branch => timeout
0x7524B25  if (cl) -> 0x7524F94  "Timeout-disconnect! Command: ..."
```

So it is **`sentCount > SentCountAllowance` OR `now > cmd.timeoutTime`** — an OR, per command.
It is **not** "time since the last ack of any kind".

**The decisive detail** — `EnetPeer.QueueSentCommand` `0x7522300` runs on *every* send **and resend**:

```
cmd.commandSentTime = now                                   ; +0x3C  0x752236F
if (cmd.roundTripTimeout == 0) rto = Min(rtt + 4*rttVar, InitialResendTimeMax=400)
else if (sentCount > QuickResendAttempts && …) rto *= 2      ; 0x75223B7 (add eax,eax)
cmd.timeoutTime = now + photonPeer.DisconnectTimeout         ; +0x48  0x752242D
cmd.commandSentCount++                                       ; +0x40  0x7522430
```

**`timeoutTime` is rebased to `now + 10 s` on each retransmit.** The wall-clock branch therefore
only fires if a *single* backed-off resend interval exceeds 10 s (RTO doubles 400 → 800 → … →
12800). In practice the **count branch fires first: the 8th send of one reliable command kills the
connection.**

⇒ **A server-side retransmit floor does not help.** What matters is that the ack reaches the client
within 8 total sends of that command; slowing the client's resends only delays the same outcome.

## On timeout the client sends NOTHING — `0x75251F7`

```
peerConnectionState = 6 (Zombie)          ; ConnectionStateValue: Disconnected 0, Connecting 1,
EnqueueStatusCallback(0x410 TimeoutDisconnect)   ;  Connected 3, Disconnecting 4,
<vtable +0x1D0>()   // StopConnection             ;  AcknowledgingDisconnect 5, Zombie 6
NCommandPool.Release(cmd)
```

**No `CT_DISCONNECT` command is queued.** `EnetPeer.Disconnect` `0x751F1C0` is a separate path used
for a graceful leave. A client-side timeout looks like silence on the wire, so production drops that
*did* arrive as a Disconnect command are **not** client timeouts.

`StatusCode`: `TimeoutDisconnect 1040`, `DisconnectByServerTimeout 1041`,
`DisconnectByServerUserLimit 1042`, `DisconnectByServerLogic 1043`,
`DisconnectByServerReasonUnknown 1044`, `Disconnect 1025`, `SendError 1030`,
`ExceptionOnReceive 1039`.

## Socket and receive loop

`SocketUdp.Connect` `0x75534E0`: `new Thread(DnsAndConnect)` → `IsBackground = true` → `Start()` —
the receive loop is on its **own dedicated background thread**, never the main thread.

`SocketUdp.DnsAndConnect` `0x7553820`: `new Socket(...)`, `set_Blocking`, `Connect`. **It never calls
`Socket.ReceiveBufferSize`** — SO_RCVBUF is left at the OS default.

`SocketUdp.ReceiveLoop` `0x7553F80`: user buffer is `new byte[IPhotonSocket.MTU]` = **1200 bytes**;
loop is `Socket.Poll(5000 µs)` → `Socket.Receive(buf)` → `IPhotonSocket.HandleReceivedDatagram`.
Dispatch to game code still happens on the main thread via `DispatchIncomingCommands`.

## `"RaiseEvent(N) failed. Your event is not being sent!"`

Literal `0xD19E650` (long form, ends `…and the eventCode must be less than 200 (0..199).`) is
referenced **only** by `OEOMKFKDCCG.JHAEBMBAEHB(byte eventCode, object content, BPKHPBMNOFA
raiseEventOptions, SendOptions)` `0x759C060` — the forked `LoadBalancingClient.OpRaiseEvent`. The
success path tail-calls the peer's `OpRaiseEvent` through vtable slot `+0x210` (`0x759C1C2`).
An event code of 36 is < 200, so the code is not what fails; stock Photon's guard here is
`CurrentRoom == null`. ⚠️ **Partially verified only** — that method's prologue desyncs the length
decoder (interleaved padding), so the guard's operand was not read directly. The message text is
verbatim stock Photon including the `"your are"` typo, which is why the stock condition is the
working assumption.

## Not established

- The PUN send-pass cadence. `Photon.Pun.PhotonHandler` `Awake 0x75A6810` exists with
  `MaxDatagrams`, `SendAsap`, `SendReceiveAtEndOfFrame` and four ints at +0x38/+0x3C/+0x40/+0x44
  (PUN's `UpdateInterval` / `UpdateIntervalOnSerialize` / next-tick counters), but the interval
  computation was not isolated — and RR may drive the pump from its own backend rather than
  PhotonHandler.
- What produces a ~45 kB burst and with which `ReceiverGroup`.
- Whether anything caps the incoming reliable queue (`CommandBufferSize` is 0 here, which reads as
  "no limit", but that was inferred from the absence of a ctor write, not from a bounds check).
