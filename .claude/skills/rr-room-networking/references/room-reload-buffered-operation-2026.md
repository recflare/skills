# Making every client in a room reload: the `Reload` buffered room operation (2026)

> There is **no push notification that reloads a room or moves a player**. A room reload is a
> **`RoomOperationRequest` protobuf inside `RRBufferedRoomEvent` (op `22`)** on the room server —
> master-only, proxied to every client on `NamedMessageType 4`, and **buffered**, so late joiners
> replay it. The payload's kind is **`MessageKind.Reload = 4`**.
> ⚠️ Two different enums have a `Reload` member and only one of them is on this wire.

Derived **2026-11-05** on build `20260323.14`, from a live `Player.log` plus the client's own
serializer. Builds on [buffered-room-event-echo-stall-2026](buffered-room-event-echo-stall-2026.md)
(the op-22 loopback) and [room-opcode-permissions-and-master-election-2026](room-opcode-permissions-and-master-election-2026.md)
(who may send op 22).

## The log line that names everything

```
[BufferedEventHelper] Waiting to receive buffered message
[RoomLoad.RoomManager] START: RoomManagerRequestHandler.ProcessBufferedRoomEvent()
[RoomLoad.RoomManager] RoomOperationRequestSerialization.Deserialize(
                           Google.Protobuf.ByteString, Reload, Invalid, 0, (Request Payload …))
[RoomLoad.RoomManager] END: RoomManagerRequestHandler.ProcessBufferedRoomEvent()
```

The format string is **`'RoomOperationRequestSerialization.{0}({1}, {2}, {3}, {4}, {5})'`**
(`0xFD218F0`), emitted by `ESCTXDLDNMB$$WTTMKJLPUNW` **`0xA2007C0`**, whose `slots` give the
argument types outright:

| slot | meaning | type |
|---|---|---|
| `{0}` | `Serialize` / `Deserialize` | — |
| `{1}` | the buffer | `Google.Protobuf.ByteString` |
| **`{2}`** | **message kind** | **`RecRoom.RoomLoad.Protobuf.MessageKind`** |
| **`{3}`** | **operation type** | **`RecRoom.RoomLoad.Protobuf.RoomOperationType`** |
| `{4}` | an `int` (0 in every capture) | |
| `{5}` | the request payload, or the literal `'Null'` (`0xFD218…`) | |

## ⚠️ THE TRAP: three enums, two of them with a `Reload`

```
RecRoom.RoomLoad.Protobuf.MessageKind        (typedef #29660, int)   <- field {2}, ON THE WIRE
   Error 0 · OperationStart 1 · PhaseChange 2 · CompletionMark 3 · Reload 4 · Finished 100

RecRoom.RoomLoad.Protobuf.RoomOperationType  (typedef #29662, int)   <- field {3}, ON THE WIRE
   Invalid 0 · LoadRoom 1 · SaveRoom 2 · ReloadRoom 3

RecRoom.RoomLoading.RequestOperationType     (typedef #45887, int)   <- NOT on this wire
   InitialRoomLoad 0 · AutoSave 1 · SaveToDisk 2 · SaveToRecNet 3 · RestoreAutoSave 4 · Reload 5
```

`RequestOperationType.Reload` is the **client-internal** operation label (it names the slice/operation
in logs, alongside the literal `'RequestReloadRoom'` `0xFC4A7B0`). The `Reload` in the log line above
is **`MessageKind.Reload = 4`**, a different enum with a different value. Reading the log's second
field as `RequestOperationType` gives `5` and a wrong wire byte — a mistake that is easy to make
because both enums live one namespace apart and the log prints only the member name.

Observed pairing: `MessageKind.Reload` arrives with `RoomOperationType = Invalid (0)` and a non-null
payload — the operation type is **not** redundantly restated for a reload. Phase traffic during a
normal load is `MessageKind.PhaseChange` + `RoomOperationType.Invalid` + `(Null)`.

The phase names in that traffic are `RecRoom.Persistence.RoomOperationState` (21 members,
`NOT_STARTED 0` … `DESERIALIZE_OBJECTS 14` … `COMPLETE 19`; note **`POST_DESTROY_OLD_OBJECTS` and
`DESERIALIZE_SETTINGS` are both 10**).

## The wire path

| | |
|---|---|
| op code | **`22` `RRBufferedRoomEvent`** on the `NILCDNBAPNO` enum ([rr-event-codes-and-rpc-dispatch](rr-event-codes-and-rpc-dispatch.md)) |
| client → server | `NamedMessageType 5` (`RRClientToServer`) |
| server → clients | `NamedMessageType 4` — the **proxied data plane**, not the direct server→client path (which only accepts `7/101/102/103/104/105`) |
| who may send | **master only**, and op 22 is the *one* data-plane code with a client-side sender check ([room-opcode-permissions-and-master-election-2026](room-opcode-permissions-and-master-election-2026.md)) |
| buffering | the server caches it and replays to joiners — that is what makes a reload reach players who arrive mid-operation |
| receiver | `RoomManagerRequestHandler.ProcessBufferedRoomEvent()` → `RoomOperationRequestSerialization.Deserialize` |
| client teardown | `<CleanupBeforeRoomReload>d__388` `0x124BF30` |

So the shape of "everyone reloads" is: **one `MessageKind.Reload` buffered event, proxied to all.**
It is not N messages and not an HTTP fan-out.

⚠️ **Not yet tested: originating op 22 from the server.** The documented flow is master→server→all,
and the client's *direct* server→client handler would reject a synthetic op 22. But op 22 rides the
**proxied** plane (nType 3/4), which the client does accept, so emitting one server-side with the
master as the nominal sender is the obvious lever for a server-driven reload. Confirm against a real
client before relying on it — and note the sender check is **client-side**, so a server that
originates one is not fighting a server-side gate.

## The client can refuse — `RoomReloadValidation`

`'RoomReloadValidation.CanPlayerReload('` (`0xFD23038`, logged by `EYKCAZOIXTX$$HYXKLYRSZZS`
`0xA200B00`) gates the reload. Results are `RecRoom.RoomLoad.Protobuf.BYMJGVKDRDM`, built and
rendered by `RecRoom.RoomLoading.WIIVPBSPAEV`:

```
static bool    HUENRYGZCQX(BYMJGVKDRDM)                        // succeeded?
static BYMJGVKDRDM XXRUBTYDRAY(ValidationReason)               // single reason
static BYMJGVKDRDM AIFREGWXNSP(IEnumerable<BYMJGVKDRDM>)       // -> Aggregate
static BYMJGVKDRDM ZWBCQRPPAJW()                               // success
static string  LRGXCKUTBIS(BYMJGVKDRDM)                        // the logged text
```

`RecRoom.RoomLoad.Protobuf.ValidationReason` (typedef #29656) — **grep the log for these names when a
reload silently does nothing**:

| val | reason | | val | reason |
|---|---|---|---|---|
| 0 | `UnknownFailure` | | 10 | `UgcRestrictedForLocation` |
| 1 | `Success` | | 11 | `Permissions` |
| 2 | `NullPlayer` | | 12 | `Aggregate` |
| 3 | **`OperationAlreadyInProgress`** | | 13 | `NotInRoom` |
| 4 | `JuniorRestriction` | | 14 | `MultiInstanceEventActive` |
| 5 | `PlatformRestriction` | | 15 | `WaitingForPlayerToFinishOperation` |
| 6 | `Moderation` | | 16 | `KeepsakeRoomWithActiveEvent` |
| 7 | `ServerForbidsSaving` | | 17 | **`RoomContentIsBaked`** |
| 8 | `ServerForbidsSavingItem` | | 18 | `CircuitsCorruption` |
| 9 | `GameRunning` | | 200 | `Cancelled` |

`OperationAlreadyInProgress` and `WaitingForPlayerToFinishOperation` are the two that will bite a
broadcast reload: the operation is **master-locked** (`MasterLockedCodeBlock` in the log), so a second
reload issued while one is running is dropped, not queued. `Permissions` maps to the room-role
permission set ([rooms-subrooms-permissions](../../wire-shapes/references/endpoints/rooms-subrooms-permissions-wire-shape.md),
`CAN_SAVE_ROOM` / `CAN_EDIT_SUBROOM_SETTINGS` family).

The sibling request on the same family is
`RoomManagerAutosaves.RequestRestoreAutosave(WOXARZYVFKQ) -> Task<BYMJGVKDRDM>` `0xA2066A0`, which
returns the same validation type — a useful cross-check that the whole operation family shares this
gate.

## ❌ Why no push notification can do this

Asked and answered 2026-11-05, so it does not get re-investigated. The 2026 client's matchmaking
subscriptions, registered in **`RecNet.Matchmaking$$Initialize` `0x94F8720`** through
`RecNet.Notifications::ENCROASZHDJ<T>`:

| channel | payload | handler |
|---|---|---|
| `RoomInstanceUpdate` | `RecNet.RoomInstance` | `HVKTDWRMJFH` |
| `PresenceUpdate` | `RecNet.PlayerPresence` (13 fields, incl. a nested `RoomInstance`) | `PHDJHDHRYIE` |
| `GoToFailure` | `RecNet.AutoFollowFailedMessage` | `YZHWXKQKCYO` |

- **Nothing commands a join.** `AutoFollowFailedMessage` has exactly **one** field,
  `ErrorCode: MatchmakingErrorCode` — it is the *failure* leg of auto-follow and cannot carry a
  destination. The join is always client-initiated:
  `Matchmaking.GoToRoom(long roomId, RoomJoinMode, int[] expectedPlayerIds,
  bool bypassMovementModeRestriction, RoomLoad.Protobuf.LIPBHKKNIRA customRoomLoadPayload,
  JoinRoomInviteMode)`.
- **The only indirect lever is auto-follow**: `PlayerPresence` carries a full `RoomInstance`, so a
  `PresenceUpdate` for someone the local player follows is what *leads* the client to call
  `GoToRoom` itself. It needs follow state and cannot be aimed at an arbitrary player.
- **`SubscriptionUpdateGameSession` does not exist.** The only `*Subscription*` channels are
  `CommerceSubscriptionUpdate` and `CreatorClubSubscriptionUpdate` (RR+/creator-club billing).
  There is no `GameSession` channel at all — `gameSessionId` / `GameSessionId` appear only as field
  names. Do not go looking for it again.
### ✅ What `RoomInstanceUpdate` *does* do — a per-client HTTP re-fetch, not a reload

Worth knowing precisely, because it is the one push that provokes real client work.
`HVKTDWRMJFH(RoomInstance)` `0x94F7B60` is a 140-byte shim that tail-calls
**`QZQNRBXPWCL(RoomInstance)` `0x94FC9C0`**, and that does three things:

1. **Field-by-field equality check** against the cached instance — `rbx` = cached, `rsi` = pushed,
   with every field from `Location` (`+0x30`) onward compared and any difference jumping to the
   changed-path at `0x94FCB5B`: `EventId +0x38`, `ClubId +0x40`,
   **`RoomCode +0x48`** and **`RawName +0x50`** (the two `String.op_Inequality` calls at `0x94FCB0F`
   / `0x94FCB23`), `MaxCapacity +0x60`, `IsFull +0x64`, `IsPrivate +0x65`, `IsInProgress +0x66`,
   `EncryptVoiceChat +0x67`, `RoomInstanceType +0x68`, `MatchmakingPolicy +0x6C`.
   ⚠️ **Pushing an identical `RoomInstance` is a complete no-op** — it never reaches the cache write.
2. On a change: `Dictionary<long, RoomInstance>.set_Item`, then
   **`XQEMDIRMNOC` `0x95004B0`** — invokes a `RecRoom.DQCNOGDGYBL<T>` delegate (the change event)
   **and** `TaskCompletionSource<T>.TrySetResult`, so anything awaiting an instance update unblocks.
3. If the changed instance is the **local** one (compared against `HBIPLOLFBGY()`),
   **`JVKFLBTKGRJ(RoomInstance roomInstance)` `0x94F8C20`** fires an **HTTP re-fetch of the room
   details** through `RecNet.Rooms.Client` + `KGLKSSUUEOH::XXATRYZHEBX<inst #1359>` — and
   **inst #1359 is `RecNet.Rooms.RoomDetailsDTO`**, the same 63-key DTO derived in
   [rooms-subrooms-default-matchmaking-policy](../../wire-shapes/references/endpoints/rooms-subrooms-default-matchmaking-policy-wire-shape.md).
   Failure literal: **`'Failed to retrieve room details for local room instance!'`**.

So `RoomInstanceUpdate` is a usable **"everyone re-read the room DTO"** lever: change one field (e.g.
`RawName`) and every client in that instance re-GETs `rooms/{id}`. It refreshes room *metadata* only
— it does not re-bake the scene, re-run migrations or re-deserialize objects. For that you still need
the op-22 `MessageKind.Reload` above.

- Moving *other* players is also in-room, not backend:
  `GameManager.SendPlayerChangeSceneWithAutoFollowRequest` `0x24B6520` /
  `RpcOnChangeSceneWithAutoFollowRequest` `0x24B5AD0`, plus
  `RecNet.GoToSubRoomRequestDTO { AdditionalPlayersAutoFollow: bool }`.
- `rrs.pushtodevice` (`RecNet.Studio.Client$$Initialize` `0x958E920`) is the Studio
  "push to device" channel — the one push that does send a client somewhere, and it is Studio-scoped.

**How to apply:** to reload every client in a room, emit **one** `RRBufferedRoomEvent` (op 22) whose
`RoomOperationRequest` has `MessageKind = Reload (4)`, on the proxied plane, and let the server's
buffering fan it out. Do not build an HTTP fan-out and do not wait for a notification channel that
is not there. If it no-ops, grep the clients' logs for `RoomReloadValidation.CanPlayerReload(` and
read the `ValidationReason`.
