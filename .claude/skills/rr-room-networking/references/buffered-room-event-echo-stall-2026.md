# Buffered room event echo stall → 180 s hang at ~90% → FailedToSpawnPlayer 8702

> Every room-load phase change is a **loopback round trip** through the room server:
> client sends `RRBufferedRoomEvent` (op **22**) on `NamedMessageType 5` and blocks until the server
> relays it back on `NamedMessageType 4`. A room load is **32 of these hops**, the client has **no
> retransmit**, and the wait is **180 s**, so losing any one relay costs the whole load and reports
> **`FailedToSpawnPlayer (Code 8702)`**. The loss is **not uniform**: it concentrates on the single
> hop out of `DESERIALIZE_OBJECTS`, whose relay latency scales with the room's deserialized-object
> count — ~57 ms at 28 objects, 358 ms median at 352, where **22 % never arrive at all**.

Observed **2026-10-15** on build `20260323.14` joining `^Guess_The_ColorRR` (room 4017.4747,
instance 1438905) against the dedicated NGO/Tachyon backend at `104.234.6.145:7777 - rollout-1`.

## The signature in Player.log

The healthy pattern, repeated once per phase (~30–170 ms each):

```
[BufferedEventHelper] Waiting to receive buffered message
[RoomLoad.RoomManager] START: RoomManagerRequestHandler.ProcessBufferedRoomEvent()
[RoomLoad.RoomManager] RoomOperationRequestSerialization.Deserialize(ByteString, PhaseChange, Invalid, 0, (Null))
[RoomLoad.RoomManager] END: RoomManagerRequestHandler.ProcessBufferedRoomEvent()
[BufferedEventHelper] Send receive took 61.532ms / 2frames
[RoomLoad.RoomManager] Moving to phase <NEXT>...
```

The stall is a `Waiting to receive buffered message` with **no `ProcessBufferedRoomEvent` after it**,
closed 180 s later by:

```
[BufferedEventHelper] Send receive took 180028.0796ms / 5744frames
[RoomLoad.RoomManager] END: MasterLockedCodeBlock
[RoomLoad.RoomManager] Exception during operation InitialRoomLoad-<guid>:
BufferedEventReceiveTimeoutException::Timed out after 3.0m: Timed out waiting for buffered message
[RoomLoad.InitialRoomLoad] JoinRoomLoadWithPhoton threw exception: Room Load faulted / Faulted Faulted
[RoomLoad.RoomManager] Reporting result FailedToSpawnPlayer / (Code 8702) to RecNet Matchmaking
```

`Send receive took` is logged on **receipt**, so a 180028 ms figure is the timeout, not a slow link.
**`Waiting to receive buffered message` with no matching `Send receive took` within a second is the
only thing to grep for** — one line, and it pins the phase.

Owning frames (filter the `# Formatted Async Stack Trace` block per
[the log-facade rule](../../il2cpp-analysis/SKILL.md)):

```
RecRoom.Networking.Events.OMPLTMRHXHL+XQGMJSCIVMW.SMVOJIXHKGW(CancellationToken, TimeSpan)   ← the timeout
RecRoom.Networking.Events.OMPLTMRHXHL.{FJMFHDYGNCW,QRYKRGRBTYT,PIBEMJVHKKD}
RecRoom.RoomLoading.RoomOperation.BCVCERTHUJS.{AYBOJUMAUVA,BIGYIQBQYAQ}
RecRoom.RoomLoading.RoomOperation.MoveToPhaseTask.{SBKZTLVLWPM,MoveTo}
RecRoom.RoomLoading.RoomOperation.DIZANNKBGBB.{GOADOHIDIEH,DeserializeAllObjects}  ← names the phase
```

`RecRoom.Networking.Events.BufferedEventReceiveTimeoutException` is **unobfuscated**, so it greps.

## 8702 ≠ 8700

Both surface as "room won't load", and both are reported through the same
`Reporting result FailedToSpawnPlayer` line, but they are different failures:

| code | cause | note |
|---|---|---|
| **8700** | the Studio asset bundle's prefab registry came up empty | [studio-asset-bundle-script-bind-failure-2026](../../rr-client-bringup/references/studio-asset-bundle-script-bind-failure-2026.md) |
| **8702** | a buffered room event was never echoed back | this note |

Read the code, not the label.

## ⚠️ CORRECTED 2026-10-15 (second pass): it IS size-dependent

> **An earlier revision of this note said "payload size and content are out." That was wrong.**
> It rested on one retry of the room succeeding, where I read the critical hop's latency off the
> **load-wide median (61 ms)** instead of measuring that hop. Measured properly, the hop ran at
> **312 ms** in that very "fast" load — it was the load's slowest hop, not its median one. Never read
> a single hop's timing off an aggregate.

A 283k-line session with **13 load attempts, 490 relay round trips and 2 fatal losses** separates the
hops cleanly. Grouping every round trip by the `[RoomLoad.RoomManager]` marker that preceded its
`Waiting to receive buffered message`:

| n | hop (phase / preceding marker) | min | median | max | >1 s | lost |
|---|---|---|---|---|---|---|
| 16 | **`DESERIALIZE_OBJECTS` / `END:DeserializeObjects`** | 49.8 | **188.1** | **180028** | 2 | **2** |
| 16 | `STUDIO_ASSET_BUNDLE_PROCESSED` | 28.6 | 59.9 | 16998 | 2 | 0 |
| 16 | `RUN_MIGRATIONS` / `START:MasterLockedCodeBlock` | 31.3 | 62.1 | 22655 | 1 | 0 |
| 16 | `SETUP_ROOM_OBJECTS` | 54.8 | 59.6 | 8185 | 1 | 0 |
| … | every other hop (≈28 distinct) | ~30 | **~60** | ≤1.4 s | ≤1 | **0** |

**Both fatal losses in the whole log are at that one hop, and its median is 3× every other hop's.**

### The variable is the deserialized object count

`RegisterInstantiatedObjectsTask.Run(N)` is logged during each load, before `DESERIALIZE_OBJECTS`.
Pairing it with that hop's relay time:

| objects | n | median (delivered) | range | **lost** |
|---|---|---|---|---|
| 25 | 1 | 63 ms | — | 0 |
| 28 | 5 | 57 ms | 50–118 ms | 0 |
| 64 | 1 | 154 ms | — | 0 |
| **352** | **9** | **358 ms** | **117–787 ms** | **2 (22 %)** |

Monotone in object count, and **only the 352-object room ever loses the relay.** Per room:
`@djdevin's Dorm` 28 objects, 5/5 delivered at ~57 ms; `^Guess_The_ColorRR` 352 objects, 7/9
delivered at 117–787 ms, **2/9 never**.

`END:DeserializeObjects` duration does **not** predict loss (178 ms and 275 ms for the two losses;
338 ms and 363 ms for successes), and the client held a steady **32 fps through every stall**, so this
is not a client hitch or a focus stall — the client is running and waiting on the network.

**Leading hypothesis, not proven:** the payload at this hop scales with object count, so at 352
objects it must fragment (the NGO path MTU settles at **1419 bytes**), and the server's relay drops or
fails to reassemble large/fragmented named messages. The competing explanation is queue pressure — a
352-object room carries far more concurrent sync traffic, so the relay may simply be queued behind it.
**Both are size-dependent; separating them needs the byte length server-side.**

### Second, separate phenomenon: episodic connection-wide delay

Eleven round trips took 1.1–22.7 s and still arrived. They cluster: six consecutive hops at
t=1787–1793 all delayed ~1.2 s then one at 17 s, and four more at t=2792–2828. Both clusters sit in
loads that **completed**, at hops unrelated to object count, while the client ran at 32 fps. That is a
connection-wide stall episode, **not** the size effect above, and it is non-fatal only because the
client's patience is 3 minutes.

## It is NOT specific to one instance, room or room version

- Instance **1439503 failed at t=2984 and then succeeded at t=3204 — the same instance id.** That
  kills "the instance was in a bad state", and resolves the confound in the earlier revision, which
  could not separate "retry worked" from "fresh instance worked".
- `^Guess_The_ColorRR` loaded successfully **7 times** in this session across 5 instance ids.
- The room's data never changed across either session.

## Which message, and what it is on the wire

The stalled hop was the phase change **out of `DESERIALIZE_OBJECTS`** — in a healthy load the very
next line is `Moving to phase DESERIALIZE_CONNECTABLES`. It sits inside the second
`MasterLockedCodeBlock` (slice type `MasterBlock`), which is why `END: MasterLockedCodeBlock` is the
first line to appear after the timeout.

Wire format, from [rr-named-message-room-protocol](rr-named-message-room-protocol.md):

- client → server: `u16 NamedMessageType = 5` (`RRClientToServer`), `u8 op = 22`
  (`RRBufferedRoomEvent`), `NetworkDelivery = 4` (ReliableFragmentedSequenced).
- server → client: op 22 is **not** in the direct `AGMAPFJIFMH` switch (that accepts only
  7/101/102/103/104/105), so the relay must come back on **`NamedMessageType 4`**
  (`RRServerToClientProxied` → `POBPNHBKBDN`, which enqueues any code without switching).

The sender is also a recipient: with `playerCount 1` the master is the only client in the room, so
the server has to relay the event **back to the client that sent it**. An implementation that
broadcasts "to everyone except the sender" hangs every single-player room load here.

### The server sent nothing at all — it did not mis-channel it

If op 22 had come back on `NamedMessageType 6` instead of 4, `AGMAPFJIFMH` would have logged
*"Received unknown server message code 22"*. That string appears **0 times** in the log, as does
*"instead of the server"*. So the relay was not mis-channelled: **look for a dropped or thrown
relay, not a wrong channel.**

⚠️ **Do not read the 180 s log silence as "the connection delivered nothing."** An idle client logs
almost nothing: 500 s parked in the dorm (t=3895–4395) produced only HTTP errors and
`OnApplicationFocus` lines. The silence proves no *buffered room event* arrived (one would have
logged `ProcessBufferedRoomEvent`); it says nothing about other traffic on the connection.

The `Setting MTU for transport 0 to N` lines are **not** a heartbeat either — they are a one-shot
5-step path-MTU probe per connection (1151 → 1379 → 1391 → 1411 → 1419 over ~4 s) that then stops
for the life of the connection, including connections that stay up for 8 minutes. Their absence
during the stall means nothing.

## What is ruled out

| hypothesis | refutation |
|---|---|
| connection died | no `OnClientStopped`/`Disconnect` in the window; the client keeps sending (clear-slice notifies go out at timeout) |
| count/connection cap on buffered events | the stalled load managed **20** round trips before the 21st hung; the **dorm does 32** on the same server and completes |
| slow link / MTU | the 20 prior trips ran 30–170 ms; the NGO path-MTU ramp (1151 → 1379 → 1391 → 1411 → 1419) is identical in loads that succeed |
| the concurrent HTTP 404s | see below — they are warnings on separate tasks, and the buffered send had already been issued |
| alt-tab / focus loss | `OnApplicationFocus False` lands at t=3699.98, **after** the send stalled at t=3694.96 |

| **payload size / content of that event** | the retry relayed the *same* event at 61 ms — see above |
| room-specific server state | same room, same save, next instance, clean 32/32 |

Not yet established: what actually dropped it. With content, size, count and channel all out, the
remaining candidates are an unreliable/unsequenced delivery mode for op 22, or a race in the
server's relay path. Both are server-side measurements.

## Concurrent, unrelated: 404s on room-object blobs

Seven `HTTP Error 404` fire 60–430 ms after the stalled send, which makes them look causal. They are
not — three are blob fetches through `RecNet.Core.GZSWPIITLPJ` → `ILKPXFFCVHR(name, expectedHash, …)`
and `RecNet.NUXLUAFCYMM.CCPMLEEZFAL`, and the client downgrades them to warnings itself:

```
[Warning] Error downloading Audio Sampler data: An error occurred
[Warning] Error downloading Holotar data: An error occurred
```

The other four go through `RGBOOBRDHEB.YGADVOMHRVJ` with no surviving subsystem frame (fire and
forget). None of them can block a phase change. They do mean the room's per-object data blobs are
missing server-side and should be mirrored, but that is a separate job.

## Checking it from the client side only

1. Grep `Waiting to receive buffered message` and pair each one with the next
   `Send receive took` — the unpaired one names the phase.
2. Join the same room again. ✅ **Done 2026-10-15: it succeeded, 32/32.** That is what moved this
   from "that event is malformed" to "the relay is lossy".
3. A room that loads (the dorm) exercises the identical 32-hop sequence against the same server, so
   it is a clean control for "is the relay working at all".
