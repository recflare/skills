# Room opcode permissions and master election (2026)

> The full `NetworkEventCode` space on `20260323.14`, split into the **control plane** (nType 5/6,
> ops 7 + 100–112) and the **proxied data plane** (nType 3/4, ops 4–36), with who may legitimately
> send each.
> ⚠️ **`102` with flag `09` is not an attack — it is `SetMasterClient`**, a compare-and-set whose
> second u64 is the *expected* current master. Rejecting it as a "protected room field" is what makes
> a client resend it.
> ⚠️ **There is no kick/ban/mute opcode.** All moderation is HTTP (`api/PlayerReporting/*`), even the
> master's own "disconnect that player", which is a `RecNet.Matchmaking` call.
> ⚠️ The client's server→client handler accepts a **closed set of six** codes: `7, 101, 102, 103,
> 104, 105`. Anything else is logged and dropped — including the new 107–112.

Derived **2026-10-23** from build `20260323.14`. Supersedes nothing; extends
[rr-named-message-room-protocol](rr-named-message-room-protocol.md) and
[rr-event-codes-and-rpc-dispatch](rr-event-codes-and-rpc-dispatch.md), both of which were derived on
`20250718.01`.

**Type names in `RecRoom.Networking` are no longer obfuscated on 2026.** `NILCDNBAPNO` is now
`RecRoom.Networking.NetworkEventCode`, `OCKHMGFANHD` is `NetworkedRoomData`, `EECOLELLELP` is
`NetworkedPlayerData`, `JIHACJLNFKE` is `RoomDataFields`, `FMEPBLGLEHD` is `PlayerDataFields`.
Enum *values* are unchanged from 2025, so every capture-derived number still holds.

## The two planes

The channel is decided by the sender, not the opcode, and the split is exact:

| plane | `NamedMessageType` | ops | carries |
|---|---|---|---|
| **control** | **5** `RRClientToServer` / **6** `RRServerToClient` | `7`, `100`–`112` | join, leave, room/player state, master changes |
| **proxied data** | **3** `RRClientToServerProxied` / **4** `RRServerToClientProxied` | `4`–`6`, `10`, `11`, `20`–`36` | every gameplay event, all cache flags |

Evidence: the op-102 sender `HVFCFCFDHNM.KDMLUGQZJVK` `0x9A96BF0` has `mov r9d, 5` at `0x9A96D61`;
the generic raise-event sender `HVFCFCFDHNM.WDVHFRRPINS` `0x9A98E50` has `mov r9d, 3` at
`0x9A990A9`. Control-plane sends are hardcoded `NetworkDelivery = 4`
(ReliableFragmentedSequenced, `0x9A96D67`); data-plane delivery is computed per event from
`NRBCKYXWUJK.IJFCIWIRFZH`.

## `RecRoom.Networking.NetworkEventCode : byte` (typedef #60560) — 36 members

`enumvals.py` on the carved metadata. **Six are new on 2026**: 107–112.

| op | name | dir | may send |
|---|---|---|---|
| 4 | `OMSendPacket` | c↔s | object owner |
| 5 | `RR_OutOfBandMessage` | c↔s | anyone |
| 6 | `RR_FastForwardMarker` | c↔s | master |
| **7** | `RR_SelfJoinMarker` | **s→c** | **server only** |
| 10 | `RR_DebugOp` | c↔s | — (see note) |
| 11 | `RR_CachedEvent` | s→c | server only |
| 20 | `RRRoomRequestEvent` | c→m | anyone (a *request* to the master) |
| 21 | `RRRoomRequestFailedResponseEvent` | m→c | **master only** |
| 22 | `RRBufferedRoomEvent` | c↔s | **master only** (validated client-side, below) |
| 23 | `RRClearBufferedRoomEvent` | c↔s | master only |
| 24 | `RR_CreationOp` | c→m | anyone (a request) |
| 25 | `RR_CreationOpResponse` | m→c | master only |
| 26 | `RR_CreationOp_Unchecked` | c↔s | master only — *"Unchecked" means the master skips revalidation* |
| 27 | `RR_MasterLockBlockComplete` | m→c | master only |
| 28 | `RR_NetworkSynchronization` | c↔s | master only |
| 29 | `RR_NetworkInstantiate` | c↔s | object creator; **master only for room objects** |
| 30 | `DO_NOT_USE` | — | nobody — reject unconditionally |
| 31 | `RR_BulkInstantiate` | c↔s | **master only** |
| 32 | `RR_Destroy` | c↔s | **owner, or master covering an owner who left** |
| 33 | `RR_BulkDestroy` | c↔s | master only |
| 34 | `RR_TransferOwnership` | c↔s | current owner, or master |
| 35 | `RR_OwnershipUpdate` | c↔s | master only |
| 36 | `RR_RPC` | c↔s | anyone (per-RPC; see *RPC gating* below) |
| **100** | `RR_JoinRequest` | **c→s** | anyone, pre-join |
| **101** | `RR_JoinResponse` | **s→c** | **server only** |
| **102** | `RR_RoomUpdate` | **c↔s** | mask-dependent — see below |
| **103** | `RR_PlayerUpdate` | **c↔s** | **self only** from a client |
| **104** | `RR_RemotePlayerJoined` | **s→c** | **server only** |
| **105** | `RR_RemotePlayerLeft` | **s→c** | **server only** |
| **106** | `RR_Leave` | **c→s** | self only |
| 107 | `RR_StartBroadcast` | new 2026 | unconfirmed |
| 108 | `RR_StopBroadcast` | new 2026 | unconfirmed |
| 109 | `RR_ScreenShareData` | new 2026 | unconfirmed |
| 110 | `RR_BroadcastVoiceData` | new 2026 | unconfirmed |
| 111 | `RR_BroadcastChatData` | new 2026 | unconfirmed |
| 112 | `RR_GameServerDebug` | new 2026 | unconfirmed |

The `dir` and `may send` columns are **inferred from the client-side gates listed below plus the
request/response naming**, except where an explicit gate is cited. They are the right default for a
server policy, not a decoded wire fact for every row.

⚠️ **107–112 are not accepted server→client.** The dispatcher's switch (below) has no arm for them,
so if the server sends one the client logs *"Received unknown server message code {0}"* and drops it.
They are therefore client→server on nType 5, or proxied on 3/4. The pairing with
`PlayerDataFields.IsBroadcasted = 16` (new on 2026) and the `screenshare` JWT role
([jwt-role-privilege-claims](../../wire-shapes/references/conventions/jwt-role-privilege-claims.md))
says this is the streamer/screenshare feature. **Not yet derived** — no sender was located.

### The server→client accepted set is closed

`RecRoom.Networking.HVFCFCFDHNM.UTXSJFMIQSN(ulong senderClientId, FastBufferReader)` `0x9A98870`
(2025: `FOMDMHNNNKP.AGMAPFJIFMH`):

```
0x9a98909  test rsi, rsi          ; senderClientId
0x9a9890c  jne  0x9a98a4f         ; -> LogError "Received a message from client {0} instead of the server"
0x9a9895b  cmp  dl, 7             ; RR_SelfJoinMarker -> RVUFECEGSGI(code, 0, null)
0x9a98989  sub  ecx, 0x65         ; 101 RR_JoinResponse
0x9a98992  sub  ecx, 1            ; 102 RR_RoomUpdate
0x9a98997  sub  ecx, 1            ; 103 RR_PlayerUpdate  --+ same handler
0x9a9899c  sub  ecx, 1            ; 104 RemotePlayerJoined +
0x9a989a1  cmp  ecx, 1            ; 105 RR_RemotePlayerLeft
0x9a989a6  ...                    ; else LogError "Received unknown server message code {0}"
```

`senderClientId` **must be 0**. 103 and 104 share one handler (both carry `NetworkedPlayerData`).
Unchanged from 2025 apart from the re-rolled names.

## Q2 — the flag byte is a field mask, and bit 8 is a compare-and-set

The byte after the op on 102/103 is the struct's first field, `dataFields`. It is a **field-presence
bitmask**: only the named fields are serialized, which is why the master-change message is 20 bytes
and not the size of a full room update.

### `RoomDataFields : byte` (#60570) — used by op 102

| bit | name | selects |
|---|---|---|
| 0 | `None` | — |
| 1 | `MasterClient` | `ulong masterClientId` |
| 2 | `Players` | `NetworkedPlayerData[] players` |
| 4 | `Properties` | `SerializableDictionary roomProperties` |
| 8 | `PreviousMasterClient` | `ulong previousMasterClientId` |
| 7 | `All` | `MasterClient｜Players｜Properties` — **deliberately excludes bit 8** |
| 9 | `MasterClientChange` | `MasterClient｜PreviousMasterClient` |

### `RoomData` body — `RecRoom.Networking.NetworkedRoomData`, declaration order

`dataFields` (byte) · `masterClientId` (u64) · `previousMasterClientId` (u64) ·
`players` (`NetworkedPlayerData[]`) · `roomProperties` (`SerializableDictionary`)

### `PlayerDataFields : byte` (#60572) — used by ops 103/104

`None 0`, `Name 1`, `AccountId 2`, `PlatformId 4`, `Properties 8`, **`IsBroadcasted 16` (new 2026)**,
`All 15`.

### `PlayerData` body — `RecRoom.Networking.NetworkedPlayerData`

`dataFields` (byte) · `clientId` (u64) · `name` (string) · `accountId` (int) · `platformId` (string)
· `playerProperties` (`SerializableDictionary`)

➡️ **`IsBroadcasted` has no matching field in the struct** (6 fields, 6 named bits minus one). Bit 16
is a **mask-only boolean** — it carries no body bytes. `All = 15` excludes it, exactly as `All = 7`
excludes `PreviousMasterClient`, i.e. both enums use "excluded from `All`" to mean "not an ordinary
field".

### This settles the 2025 note's open question

[rr-named-message-room-protocol](rr-named-message-room-protocol.md) flagged conditional
serialization as ⚠️ *"not yet proven"* because `NetworkSerialize` is RGCTX-resolved and statically
unreachable. **A 20-byte `102`/`09` capture proves it**: `2` (nType) + `1` (op) + `1` (mask) +
`8` + `8` = 20, with `players` and `roomProperties` **absent** because bits 2 and 4 are clear. The
mask gates serialization field by field.

**No bit means "broadcast".** Direction is the channel, not a flag. The only compare-and-set is
bit 8.

## Q3 — master election

### What the client sends

`HVFCFCFDHNM.EKOJRVGZPFD(JNIVCIZIPSX player) -> bool` `0x9A95A70` is `SetMasterClient`:

```
0x9a95a9c  cmp  byte ptr [rbx+0x50], 0   ; must not be the server
0x9a95aa6  cmp  dword ptr [rbx+0x18], 9  ; ClientState must == Joined (9)
0x9a95ac5  mov  esi, [rax+0x50]          ; esi = the master the client believes is current
0x9a95ae2  cmp  esi, eax                 ; target == current master?
0x9a95ae4  je   0x9a95b5a                ;   -> no-op, send nothing
0x9a95b32  mov  byte ptr [rsp+0x20], 9   ; dataFields = MasterClientChange
0x9a95b2a  ...  [rsp+0x28] = target      ; masterClientId        = who should become master
0x9a95b25  ...  [rsp+0x30] = current     ; previousMasterClientId = who it thinks master is NOW
           call 0x9a96bf0                ; -> op 102 on nType 5
```

So `previousMasterClientId` is **not** informational and **not** "another member's id" — it is the
**expected value**. This is Photon's `SetMasterClient`, which sets room property
`GamePropertyKey.MasterClientId = 248` with `expectedProperties[248] = currentMaster`, ported to the
NGO path. A server that honours it should apply the change **only if its own master equals
`previousMasterClientId`**, and otherwise reply with the authoritative master.

### When the client claims mastership

`PUNNetworkManager.MasterSwitchToBestCandidatePlayer()` `0x15DDE20`, called from five places:

| caller | trigger |
|---|---|
| `SessionManager.MasterTryForceSwitchToNewBestMaster` | master is leaving or unhealthy |
| **`SessionManager.SetLocalPlayerBackgrounded`** | **the local player backgrounded the app / headset slept** |
| `GameManager.SPINVHXIRXQ` | session lifecycle |
| `CircuitsV2Manager.RpcRequestMasterRecalculateMaster` | **an RPC — any peer can ask for a recalculation** |
| `HJKFMYJZGWR.RecalculateRoomAuthorityStatic` | CV2 room-authority recalculation |

`SetLocalPlayerBackgrounded` is the operationally important one: a player alt-tabbing or putting a
headset down hands off mastership, so spontaneous `102`/`09` with no one leaving is **normal**.

Candidate selection is `PUNNetworkManager.LQVIUHRNORB` `0x15DD7E0`, weighing **ping, network type and
a hardware score** (`"\tNew Ping: {0}, Old Ping: {1}"`, `"\tNew Network: {0}, Old Network: {1}"`,
`"\tNew HW: {0}, Old PW: {1}"`) against the game-config threshold
**`MasterClientSelection.CostDiffThreshold`** (read in `ACHRERAWTPM.AMOOSREVRCC` `0x15C9050`).
Candidates still loading are skipped — *"Couldn't find a valid master client candidate (all
candidates are still loading)"*. **This is not "lowest client id"**; a server that picks lowest-id
will routinely disagree with every client's own choice.

### How it learns the result, and what it does on disagreement

Only from a server→client `102` whose mask includes `MasterClient`, which drives
`PUNNetworkManager.OnMasterClientSwitched(JNIVCIZIPSX)` `0x15DF0A0`. That method is a **recovery
path, not an assert** — *"Trying to recover a viable master client."*, *"Trying to recover master
client. Current client is best candidate."*, *"Unable to determine a better candidate, this room is
now in an indeterminate state"*, *"Trying to recover from master client forced switch."* It accepts
whatever the server says and re-derives from there. **The server's answer wins, if it sends one.**

### Does it loop by design?

**No.** `EKOJRVGZPFD` has no retry, no timer and no backoff — it sends once per external trigger, and
it self-suppresses when the target already equals its believed master. A repeated `102`/`09` means
the client's believed master **never changed**, so every subsequent trigger re-fires with the same
payload. 500 in one session is the expected consequence of a server that silently drops the message,
not evidence of a modified client. The one amplifier available to a peer is
`RpcRequestMasterRecalculateMaster`, which is an ordinary RPC inside op 36 and can be spammed by a
modified client — so rate-limit *that RPC*, not op 102.

## Q4 — event codes, senders and cache flags

The codes the capture shows are all `NetworkEventCode` members; identification is exact:

| seen | name | what it is |
|---|---|---|
| 22 | `RRBufferedRoomEvent` | the room-load loopback ([buffered-room-event-echo-stall-2026](buffered-room-event-echo-stall-2026.md)) |
| 24 | `RR_CreationOp` | a client's *request* to the master to mutate the room |
| 26 | `RR_CreationOp_Unchecked` | the same, master-authored, revalidation skipped |
| 27 | `RR_MasterLockBlockComplete` | master signals a locked phase-change block finished |
| 29 | `RR_NetworkInstantiate` | **one** runtime-spawned networked object |
| 31 | `RR_BulkInstantiate` | many scene objects at once |
| 32 | `RR_Destroy` | one object |
| 33 | `RR_BulkDestroy` | many objects |
| 36 | `RR_RPC` | ViewId + method-name string + boxed args |

### Cache flags

Two enums, and the difference matters:

- **`RecRoom.Networking.RpcCacheOption : byte`** (#60587) — the full space:
  `DoNotCache 0`, `AddToRoomCache 4`, `AddToRoomCacheGlobal 5`, `RemoveFromRoomCache 6`,
  `RemoveFromRoomCacheForActorsLeft 7`. Photon's values exactly; 1/2/3 (Merge/Replace) do **not**
  exist.
- **`RecRoom.Networking.RPC.BufferedEventCaching : int`** (#62771) — `DoNotCache 0`,
  `AddToRoomCache 4`, `AddToRoomCacheGlobal 5` only.

➡️ **The buffered-event API cannot remove.** A `6` or `7` therefore never originates from RR's
buffered-event helper — it comes from the lower `RpcCacheOption` path, i.e. cache maintenance.
Photon semantics: `4` is scoped to the sending actor and is purged when they leave; `5` is global and
survives them; `7` purges entries for departed actors and is **master-only**.

`GamePropertyKey.CleanupCacheOnLeave = 249` is the room property governing the automatic purge, so
whether the server or the master is expected to do the cleanup is itself room-configurable.

### Code 29, cache 4, 91 bytes

`RR_NetworkInstantiate` carries `RecRoom.Networking.InstantiateParameters` (10 fields):
`viewIDs int[]` · `objLevelPrefix byte` · `data object[]` · `group byte` · `scale Vector3` ·
`rotation Quaternion` · `position Vector3` · `prefabName string` · `creator` · `timestamp int`.
91 bytes is one such record (12 + 16 + 12 = 40 bytes of transform alone, plus a prefab name and a
small view-id array), so a constant 91 means **one prefab name repeated** — the same object spawned
over and over.

Cache `4` is correct for a player-spawned object: it must reach late joiners, and it must vanish when
the spawner leaves. **2007 in four minutes into a three-player room is ~8/s of a single prefab.** That
is the shape of a held trigger or a thrown/consumable item spawner, not of room building. Whether it
is legitimate depends on the prefab, which is in the payload — ⚠️ **not derived**: `prefabName` is
readable server-side and is the field worth logging, since it distinguishes a paintball from an
exploit far better than the rate does.

### The master's 1000+ bursts

Code 33 `RR_BulkDestroy` and code 36 `RR_RPC` with cache `6` from a master on a large room are
**cache maintenance**, not gameplay: the master clearing buffered instantiate/RPC entries for objects
that no longer exist. This is the mirror image of the room-load burst — a room that bulk-instantiates
at load bulk-destroys and un-buffers at reset. ⚠️ **Inferred** from the cache-flag semantics and the
master-only gate; not traced to a specific caller.

### The one receive-side sender check the client makes

`RecRoom.Networking.Events.OMPLTMRHXHL.NQNFUQKKGRF(VZZVUJOFUEN)` `0x9AAC2F0`, the buffered-event
(slice) receive path:

```
0x9aac5a1  mov  ebx, eax            ; ebx = event sender id      (interface slot 1)
0x9aac5b0  mov  ecx, 4              ; master client id           (interface slot 4)
0x9aac5c1  cmp  ebx, eax
0x9aac5c3  je   0x9aac670           ; sender == master -> accept
           ...                      ; else LogWarning + discard
           "Received buffered message from non-master client [{0}] Current Master is [{1}]. Discarding..."
```

**Op 22 is the only code with a client-side sender check.** Everything else on the data plane is
trusted, which is precisely why the gate has to live in the server.

## Q5 — privileged and administrative operations

**There is no kick, ban, mute, room-settings or teleport-others opcode.** Every moderation action is
an HTTP call authorized by the backend against the JWT, not a room message:

`api/PlayerReporting/v1/instantKick` · `v1/modKick` · `v1/roomModKick` · `v3/voteToKick` ·
`v1/voteToKickReasons` · `ModerationUnkick`, with payload fields `kicker`, `kickerRole`,
`playerIdKicker` and reasons `kicked_by_host`, `kicked_by_room_mod`.

Even the master's own disconnect primitive is HTTP. `PUNNetworkManager.MasterSendRemotePlayerRecNetDisconnect(player)`
`0x15DDDA0` tail-jumps straight to `RecNet.Matchmaking.RFWLFXRXQKX` `0x94FCDC0` — a REST call, with
no room message emitted at all:

```
0x15dde0a  jmp  0x94fcdc0   ; -> RecNet.Matchmaking$$RFWLFXRXQKX
```

➡️ **The room server never has to recognise a kick, and must never accept one.** If a kind-5 or
event opcode ever appears to kick someone, it is forged. The consequence of a real kick arrives as an
ordinary `106 RR_Leave` or a transport disconnect.

`RecRoom.ObjectModel.NetworkEventType` (#51395) does expose Photon's reserved **200–255** range,
including `CloseConnection 203`, `DestroyPlayer 207`, `RemoveCachedRPCs 205`, `OwnershipRequest 209`,
`OwnershipTransfer 210`, `VacantViewIds 211`, `PropertiesChanged 253`, `Leave 254`, `Join 255`. These
belong to the **Photon backend**, which brokers them itself. On the dedicated path they must be
**rejected outright** — `NetworkEventCode` stops at 112 and leaves 200–255 unused, so nothing
legitimate on a dedicated room server ever carries one.

### The protected room properties

`RecRoom.ObjectModel.GamePropertyKey : byte` (#51390) — the well-known room-property keys, all
server-authoritative:

`MaxPlayers 255`, `IsVisible 254`, `IsOpen 253`, `PlayerCount 252`, `Removed 251`,
`PropsListedInLobby 250`, `CleanupCacheOnLeave 249`, **`MasterClientId 248`**, `ExpectedUsers 247`,
`PlayerTtl 246`, `EmptyRoomTtl 245`, and one RR addition **`HasDedicatedMaster 87`**.

➡️ A client `102` with `Properties (4)` touching any of 245–255 is the real "protected room fields"
case — that is what the existing rejection was presumably written for. `MasterClientId 248` is the
one that must be handled rather than rejected, via the mask-9 path above.

### RPC gating

Op 36 dispatches PUN-style by **ViewId + method-name string** (unobfuscated), so per-RPC policy is
possible server-side without any symbol work. The naming convention is load-bearing:
`RpcMaster*` = a client→master *request*, plain `Rpc*` = a master→all *broadcast*. **A plain `Rpc*`
arriving from a non-master is the signature to gate**, and `grep methods.pkl` for `Rpc` is the whole
registry — see [rr-event-codes-and-rpc-dispatch](rr-event-codes-and-rpc-dispatch.md).

## Q6 — what the client does with a silently dropped operation

**Nothing.** The control-plane senders are fire-and-forget: `KDMLUGQZJVK` (102) and `KEPRVKUVTGC`
(103) return a `bool` that reports only whether the local `SendNamedMessage` succeeded. There is no
sequence number, no ack, no timeout and no retry anywhere on the path. A dropped `102` therefore
produces a **silent, permanent divergence** — the client keeps its stale belief until some unrelated
trigger re-fires the same send.

There is no generic negative acknowledgement the server can use. The request/response pairs that
exist — `21 RRRoomRequestFailedResponseEvent` and `25 RR_CreationOpResponse` — are **master→client**
(`RoomManagerRequestHandler.SendMasterFailRequest()` / `TrySendMasterFailRequest()`,
`RoomManagerReceiveOperation.MasterTryStartOperationFromRequest`), and they are not in the
server→client accepted set, so the server cannot use them to reject without impersonating the master.

➡️ **The clean rejection is a state correction, not an error.** Reply on nType 6 with
`102 RR_RoomUpdate`, mask `MasterClient (1)`, carrying the authoritative `masterClientId`. The client
feeds it to `OnMasterClientSwitched`, which is written to accept and recover from exactly that.
A well-behaved client then stops, because the no-op guard at `0x9A95AE4` suppresses the next send
once its belief matches. Dropping the message instead is what produces the resend loop.

## How to apply, server side

In `src/game_dispatch.cpp` / `src/rr_game.cpp`:

1. **Split on `NamedMessageType` first.** Accept `100/102/103/106` only on **5**, gameplay codes only
   on **3**. A control op on 3, or a gameplay op on 5, is already anomalous.
2. **Handle `102` mask `9`** as compare-and-set `SetMasterClient`: apply iff
   `previousMasterClientId == server's current master`, then broadcast `102` mask `1`. On mismatch,
   reply `102` mask `1` with the authoritative master. **Stop rejecting it.**
3. **Reject `102` mask `4`** only for keys **245–255** (`GamePropertyKey`), not wholesale.
4. **Pin `103` to the sender**: `clientId` must equal the sending connection, else drop.
5. **Never accept** `7`, `11`, `101`, `104`, `105` from a client, nor any code `200`–`255`, nor `30`.
6. **Master-only**: `6`, `21`, `22`, `23`, `25`, `26`, `27`, `28`, `31`, `33`, `35`, and any cache
   flag `6`/`7`. **Owner-only**: `4`, `32`, `34`. Codes `20` and `24` are requests and stay open.
7. **Log `prefabName` on `29`**, not just the rate — it is the field that separates a projectile from
   an exploit.
8. **Rate-limit `RpcRequestMasterRecalculateMaster` inside op 36**, which is the only peer-reachable
   master-election amplifier.
