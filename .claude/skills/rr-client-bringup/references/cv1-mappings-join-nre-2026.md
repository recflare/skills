# "Glitch in the matrix" join failure — CreateCV1MappingsTask NRE (2026 build)

> On build **20260323.14**, joining a room that has **CircuitsV1** data can fault the room load with
> `FailedToSpawnPlayer (Code 8718)` and the user-facing *"Failed to load room due to a glitch in the
> matrix."* It is **not a process crash** — the app stays up. The NRE is in
> `RoomManagerCallbacks.DETHYNTNMDU` `0x10A2CC0`, reached from
> `RoomOperation.CreateCV1MappingsTask.Run()`, because
> **`NetworkedSingletonMonoBehaviour<CircuitsV1Manager>.Instance` is null**.
> ✅ **ROOT CAUSE (2026-10-13, second pass): a server-side 404 on
> `GET api/consumables/v1/all?supportedVersion=2`** (a 2026-only route) rejects the
> `[Platform.BootSequence]` promise ~100 ms later, which loads the **login screen scene** on top of
> the room scene, destroying every networked singleton in it. The CV1 NRE is the last link in that
> chain, not the bug. Implement the consumables routes and the join succeeds.
> **✅ CONFIRMED FIXED 2026-10-13** on the live server. ⚠️ The user implemented several missing
> routes in one pass, so **which single 404 was the boot killer was never isolated** — the
> 404→BootSequence pairing below proves *a* single route was responsible and points at consumables,
> but treat "it was `api/consumables/v1/all`" as the leading hypothesis, not a verified fact.

Diagnosed **2026-10-13** from `Player.log` / `Player-prev.log` plus the 2026 carve
([[recflare-2026-static-index]] → `C:\Games\recnet-patcher\il2cpp-2026\`).

## Log signature

There is **no `Crash!!!` marker and no crash dump** — Unity's handler never fires. Grep for this
instead:

```
[RoomLoad.RoomManager] START: Create CV1 Mappings
[RoomLoad.RoomManager] END: Create CV1 Mappings          <- logged even on failure (LogRangeScope dispose)
[RoomLoad.RoomManager] Exception during operation InitialRoomLoad-<guid>:
[RoomLoad.InitialRoomLoad] JoinRoomLoadWithPhoton threw exception: Room Load faulted / Faulted Faulted
[RoomLoad.RoomManager] Reporting result FailedToSpawnPlayer / (Code 8718) to RecNet Matchmaking
                       for exception System.NullReferenceException
Failed to load room due to a glitch in the matrix. Please let us know with a bug report!
[RoomLoad.InitialRoomLoad] Error during initial room join for <instanceId>
```

with the top stack frames

```
at RecRoom.RoomLoading.RoomManagerCallbacks.DETHYNTNMDU (RecRoom.Protobuf.PersistedRoomData a,
                                                         RecRoom.Protobuf.DEPRECATED_RoomPersistenceVersion b)
at RecRoom.RoomLoading.RoomOperation.CreateCV1MappingsTask.Run ()
```

⚠️ **`END: Create CV1 Mappings` is not success.** `'Create CV1 Mappings'` is a
`RecRoom.Logging.LogRangeScope` name (literal at `0xA218735`), and the scope disposes on the
exception path too — so START/END appear even when the task throws.

⚠️ **Every `[Exception]` in this log is followed by `Uploading Crash Report`.** That is Backtrace
uploading each *managed* exception; it is **not** evidence of a process crash. Both sessions here
ended with a clean `Application.quit`.

## The failing method, decoded

`RecRoom.RoomLoading.RoomManagerCallbacks.DETHYNTNMDU` **`0x10A2CC0`** (+0x260):

```csharp
void DETHYNTNMDU(PersistedRoomData a, DEPRECATED_RoomPersistenceVersion b)
{
    if (a == null) throw NRE;                                   // 0x10A2D38
    var blob = a.<ByteString @ +0x58>;                          // CircuitNodeGraphCollectionData
    if (blob == null)   return;                                 // ByteString.op_Equality, 0x10A2D5F
    if (blob.IsEmpty)   return;                                 // 0x10A2D7B
    if (FSGRHONWUQJ_parser == null) throw NRE;                  // 0x10A2DDF
    var graph = MessageParser<RecRoom.CircuitsV1.Protobuf.FSGRHONWUQJ>.ParseFrom(blob);
    RoomManagerCallbacks.NDZEKQWJBZV(graph);                    // 0x10A2E12
    CircuitPreInitializeMigration.BIEGNHFDYYA(b, graph);        // 0x10A2E34
    if (NetworkedSingletonMonoBehaviour<CircuitsV1Manager>.Instance == null) throw NRE;  // 0x10A2E7B
    CircuitsV1Manager.Reinitialize(graph);                      // 0x10A2E83
}
// catch -> log 'Error parsing CircuitNodeGraphCollectionData!'  (literal 0x10A2EB1)
```

Four candidate throw sites, narrowed:

| site | excluded? |
|---|---|
| `blob == null` / `blob.IsEmpty` | **Not a throw** — clean early return. A room with no CV1 data can never fail here. |
| parse failure | **Excluded** — `'Error parsing CircuitNodeGraphCollectionData!'` appears **0 times** in either log. |
| `FSGRHONWUQJ` parser static null | **Excluded** — the class-init call (`sub_c40430`) runs immediately before. |
| `a == null` | Possible in principle, but see below. |
| **`CircuitsV1Manager.Instance == null`** | **The remaining explanation.** |

## ✅ ROOT CAUSE FOUND 2026-10-13 (second pass): a 404 on a `RecNet.Consumables` boot call

The NRE mechanism below is correct and the "cascade from a failed boot sequence" framing is correct.
A second log pass **identified the trigger**, and it is entirely server-side:

```
HTTP 404 on a RecNet.Consumables boot request
  -> [Platform.BootSequence] RecRoom.Async.ErroredPromiseException   (~100 ms later, 3/3 exact)
  -> the LOGIN SCREEN SCENE is loaded on top of the room scene
       'Login screen scene was loaded while not in the pre-game controller state.'
  -> every NetworkedSingletonMonoBehaviour in that scene is destroyed:
       8x '[Economy.UGC] RPC Forwarder - Trying to set <X> but EconRPCForwarder is not initialized'
       and NetworkedSingletonMonoBehaviour<CircuitsV1Manager>.Instance becomes null
  -> DestroyOldObjectsTask.BulkDestroy(0)   instead of (24) - the scene is already gone
  -> CreateCV1MappingsTask -> NRE in DETHYNTNMDU -> FailedToSpawnPlayer (8718)
  -> 'Failed to load room due to a glitch in the matrix.'
```

### The correlation table that settles it

One session, five `Reload` operations of the **same** payload
(`RoomId:112 SubRoomId:137 SubRoomDataSaveId:23472`) - so the room data is **not** the variable:

| # | uptime | fetch | BootSequence error? | login screen? | `BulkDestroy` | result |
|---|---|---|---|---|---|---|
| 1 | 20.26 | 1.37 s | 17.92 (**during initial boot**) | no | 24 | **OK** |
| 2 | 195.99 | 1.33 s | **195.62** | **YES** 196.30 | **0** | **FAIL** |
| 3 | 502.44 | 0.001 s (cache) | no | no | 24 | OK |
| 4 | 512.33 | 0.001 s (cache) | no | no | 24 | OK |
| 5 | 2372.58 | 1.73 s | **2372.20** | **YES** 2372.96 | **0** | **FAIL** |

⚠️ **Network-vs-cached fetch is a red herring** - load 1 was a full 1.37 s network fetch and
succeeded. The only perfect discriminator is **the login screen scene loading mid-join**, and that is
driven by the BootSequence rejection.

Load 1's BootSequence error is the same 404, but it lands **during the initial boot**, while the
client legitimately *is* in the pre-game controller state and the room scene is not up yet - so
loading the login screen is legal there, no error is logged, and the join survives. The same failure
during a join is fatal.

And the 404 -> BootSequence pairing is exact, to 100 ms, three times out of three:

| 404 (`[Exception] HTTP Error 404`) | `[Platform.BootSequence]` |
|---|---|
| 17.8198 | 17.9206 |
| 195.5228 | 195.6215 |
| 2372.1008 | 2372.2032 |

**Only these three of the session's 38 404s do this.** One route, requested once per room join.

### ⚠️ CORRECTION: the log *can* name the failing subsystem - use the FORMATTED trace

An earlier revision said "the log cannot name the 404'd routes; the stack only reaches
`RecNet.Core.OOLFEOLDQTG`". That is true of the **plain** stack trace. It is **not** true of the
`Rethrow as FormattedAsyncException` / `. # Formatted Async Stack Trace` block that Rec Room appends
to the same exception - that one walks the **async** chain and names the originating methods.

For the boot-killing 404 it contains:

```
at RecNet.RGBOOBRDHEB.ZWUODKCINOA[TResponse] (CancellationToken a)      x3   <- the deserializing send
at RecNet.Consumables.QDHFBWAJOUK (System.Boolean a)                    x2
at RecNet.Consumables.TTFUICYEDRZ ()                                    x1
```

Resolved statically against build `20260323.14`:

| frame | state machine (`AsyncTaskMethodBuilder.Start` generic inst) | route |
|---|---|---|
| `RecNet.Consumables.QDHFBWAJOUK(bool)` `0x947F810` | **`<GetAllBuiltInConsumablesAsync>d__36`** (inst #66476) | **`GET api/consumables/v1/all?supportedVersion=2`** |
| `RecNet.Consumables.TTFUICYEDRZ()` `0x947FE20` | **`<DownloadUnlockedConsumables>d__37`** (inst #66475) | `GET api/consumables/v2/getUnlocked` |

So: **implement both consumables routes.** `api/consumables/v1/all?supportedVersion=2` is the prime
suspect because it is **2026-only** - the literal does not exist in `20250718.01` at all, so a
server built against the 2025 client will not have it. Wire shapes for both are in
`wire-shapes/references/endpoints/consumables-v1-v2-routes-wire-shapes.md` (the `v1/all` section is
the 2026 addendum): a **bare array** of the 8-key `RecNet.Consumable`, `[]` is a valid empty answer,
and `ConsumableItemDesc` must be unique and non-null because the client re-keys the array into a
`Dictionary<string,_>`.

**Technique worth keeping:** on an exception with both traces, read the
`# Formatted Async Stack Trace` block, filter out `System.Threading.*` / `AsyncMethodBuilder*` /
`Task`1*`, and whatever `RecNet.<Feature>.<Method>` frames remain name the caller. Then
`ginst.py inst <N>` on that method's `AsyncTaskMethodBuilder.Start` inst gives the
`<OriginalName>d__N` state machine, and `mxref` on the route literal confirms the pairing.

### Not a bug: the 409 on `player/verifylock` in this log was deliberate testing

```
[07:25:09] [1589] [151.3692] [Error] [Unity | Error] [RecNet.Core.HTTP] POST Matchmaking player/verifylock
HTTP STATUS: 409
DURATION: 10374 ms
[07:25:09] [1600] [151.6853] [Log] [Unity] [Network.TachyonClient] TachyonClient.Disconnect
```

**A 409 on that route force-logs-out the client.** `RecNet.Matchmaking.WJITRSFCKUU` `0x94FFDA0` is
`if (response.StatusCode != 409) return;` and otherwise fires the forced-logout event with the reason
`'Conflict (409)'` - see `wire-shapes/references/endpoints/player-verifylock-wire-shape.md`. The
`TachyonClient.Disconnect` 0.3 s later is that logout.

⚠️ **The user confirmed this 409 was their own deliberate test, not a server defect** — so do not
read it as a finding. It also did not cause the two failures here (it fires once, at 151 s, and joins
3 and 4 succeeded afterwards). It is recorded only as a live confirmation that **409 on this route
really does end the session**, which is what the static derivation predicted.

**Settled contract for this server: always return 2xx.** The real function of `verifylock` is
single-session enforcement — 409 means "another client has claimed your login lock" — which is
irrelevant on a single-user self-hosted server. `200` is fine (the body is never read; `204` is
marginally tidier). Never return 409 unless you actually want the client kicked.

### Remaining failures in the same session, by subsystem tag

| tag | count | note |
|---|---|---|
| bare `HTTP Error 404` | 17 | three of them are the boot killer above |
| `[Economy.UGC]` | 16 | the 8x2 EconRPCForwarder messages - **symptom, not cause** |
| bare `NullReferenceException` | 15 | includes the two CV1 ones and `PlayerPuppet.TNZHDHHZQGJ` |
| `Malformed Response: '{}'` | 7 | **wire-shape mismatches** - server sent an object where `T` is a list/scalar |
| `[LiveOps.TLA.Recipes.Ingredients]` | 4 | 404 |
| `Malformed Response: '[]'` | 2 | server sent an array where `T` is an object |
| `[RecNet.Features.Objectives]` | 2 | `Error on server call` |
| `[RecNet.Features.Matchmaking]` | 1 | `RecNet presence heartbeat response indicates local presence is out-of-sync!` |

The 9 `Malformed Response` exceptions are the next cheapest wins - each is one route whose body shape
is inverted. See the `ioncmjiacfi-malformed-response` and `nonobject-response-routes` conventions.

## ⚠️ CORRECTED 2026-10-13: this is a CASCADE from a failed boot sequence, not a client bug

An earlier revision of this note concluded "the first room load per process works and every later one
fails — a stock client lifecycle bug". **That was wrong**, and the objection that caught it is the
right one: Rec Room ships this client to millions, so "every room re-load fails" would never survive
QA. The NRE mechanism below is real and traced; the *attribution* was not supported.

### What is actually different on the failing load

Both loads of the same room/instance walk an identical phase sequence and both fetch room data
successfully (`FetchDeserializationDataTask.Run('112.137')`, ~1.15 s, no error, on **both**) — so the
`PersistedRoomData` is not the variable. What load 2 has that load 1 does not:

```
[Economy.UGC] RPC Forwarder - Trying to set RoomCurrencyManager      but EconRPCForwarder is not initialized
[Economy.UGC] RPC Forwarder - Trying to set RoomExperienceManager    but EconRPCForwarder is not initialized
[Economy.UGC] RPC Forwarder - Trying to set RoomGiftDropShopsManager but EconRPCForwarder is not initialized
[Economy.UGC] RPC Forwarder - Trying to set NetworkedStorefront      but EconRPCForwarder is not initialized
[Economy.UGC] RPC Forwarder - Trying to set RoomInventoryManager     but EconRPCForwarder is not initialized
[Economy.UGC] RPC Forwarder - Trying to set RoomOfferManager         but EconRPCForwarder is not initialized
[Economy.UGC] RPC Forwarder - Trying to set RoomConsumablesManager   but EconRPCForwarder is not initialized
[Economy.UGC] RPC Forwarder - Trying to set RoomKeysManager          but EconRPCForwarder is not initialized
[Error] Login screen scene was loaded while not in the pre-game controller state.
```

**Eight networked room managers fail to initialize on the second load** — exactly the same class of
failure as `NetworkedSingletonMonoBehaviour<CircuitsV1Manager>.Instance` being null. And the client
even re-loads the **login screen scene** mid-join, i.e. it is partially re-running its boot sequence.

Upstream of all of it, on **both** loads:

```
[RecNet.Features.InAppMessages] RecNet.RecNetWebException: HTTP Error 404
[Platform.BootSequence] RecRoom.Async.ErroredPromiseException: An error occurred
```

**`[Platform.BootSequence]` throws on an HTTP 404 on every load.** A stock client against real
RecNet never gets there, which is exactly why this does not ship broken. The null
`CircuitsV1Manager` is a **symptom of a half-initialized client**, not an independent defect.

### 46 HTTP 404s in one session — fix these first

Subsystems that name themselves in the log:

| tag | errors |
|---|---|
| `RecNet.Features.InAppMessages` | 404 |
| `LiveOps.TLA.Recipes.Ingredients` | 404 |
| `LiveOps.TLA.Tricksters` | error |
| `Economy.Player.AvatarEffectConfigService` | error |
| `RecNet.Features.Objectives` | error |
| `Economy.UGC` | 8× EconRPCForwarder-not-initialized (load 2 only) |

⚠️ **The log cannot name the 404'd routes.** The stack only reaches the generic sender
`RecNet.Core.OOLFEOLDQTG(HttpMethod, RecNet.Service, string path, …)`, which takes the path as a
**string argument**, so it never appears in the trace. Use an HTTP proxy capture; do not try to infer
routes from the log.

### Still-useful observation: the lost room-load handler

Room-load handler `0a18d495-c261-47e0-86de-2dc9bfc56e7f` runs 8 times, **all inside load 1**
(`PRE_DESTROY_OLD_OBJECTS`, `POST_DESTROY_OLD_OBJECTS` and two later phases) and never again. On
load 2 `PRE_DESTROY_OLD_OBJECTS` goes straight to "All handlers complete" and
`POST_DESTROY_OLD_OBJECTS` runs only `0951cdad-…`. `DestroyOldObjectsTask.BulkDestroy(24)` on load 1
versus **`BulkDestroy(0)`** on load 2.

**Which component owns that handler was never established** — attributing it to the CV1 manager was
the unsupported step. Treat the handler diff as a *symptom pointer*, and the generalisable technique
as: **diff the `RunFor.All handler <guid>` lines between a working and a failing load; a GUID present
in one and absent in the other names a component that failed to initialize.**

## Separate noise in the same logs (not this bug)

- **`HTTP Error 404` ×many during join.** The stack only reaches the generic sender
  `RecNet.Core.OOLFEOLDQTG(HttpMethod, RecNet.Service, string path, …)`, which takes the path as a
  **string argument**, so the log cannot name the route. A proxy capture is required to identify
  them — do not try to guess from the log.
- **`Malformed Response: '{}'`** via `RecNet.RGBOOBRDHEB.AIYNPFIEYFY<T>` — the 2026 equivalent of
  2025's `IONCMJIACFI`. Same meaning: the body would not deserialize into `T`, and a `{}` body
  against a list/scalar `T` is the classic case. See the wire-shapes convention
  `ioncmjiacfi-malformed-response`.

## Build note: 2026 stack traces are worth reading

Unlike 20250718.01, this build **keeps real names for much of the room-load pipeline** —
`RoomLoading.RoomManagerCallbacks`, `RoomOperation.CreateCV1MappingsTask`, `MoveToPhaseTask`,
`RecRoom.Protobuf.PersistedRoomData`, `CircuitPreInitializeMigration`, `CircuitsV1Manager`,
`ObjectModelManager`, `RecRoom.Logging.LogRangeScope`. Only the methods are obfuscated
(`DETHYNTNMDU`-style). A managed stack trace therefore names the task and the DTO for free, and
`slots2025.py` on the method RVA fills in the rest — far cheaper than the 2025 workflow.
