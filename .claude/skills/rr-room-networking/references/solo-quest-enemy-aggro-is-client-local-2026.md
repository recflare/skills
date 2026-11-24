# Solo quest enemy aggro is client-local (2026)

> On a **solo** quest instance the owner is the sole authority/master, and the entire enemy
> detection→aggro→combat decision runs **locally on that client** off `UnityEngine.Time.time` and
> live `Transform.position`. **No inbound server→client message is in the aggro path.** The server's
> only coupling to quest-enemy behaviour is the initial room-story-state **room property** (`RSS`/`SS`)
> that a new-instance join reply may seed — which recflare omits (join flag 3 = no property dict).
> Build `20260323.14`.

Derived **2026-11-11** answering "are enemies engaging on solo spawn because the server (Tachyon)
sends an event/RPC that triggers aggro?" — **No.** See reasoning below.

## The engagement path (all local, authority-gated)

| step | method | RVA | note |
|---|---|---|---|
| combat start | `RecRoom.Core.AI.Enemy.AuthorityStartCombat` | 0x1f22a30 | gated on `RRNetworkBehavior.get_HasAuthority`; authority = owner when solo |
| forwarder | `QuestAIController.StartCombatBehavior` | 0x1d4cd60 | thin jmp to AuthorityStartCombat; invoked via CV2/Encounter delegate (0 direct callers) |
| target pick | `Enemy.HVVJXTFPONI` | 0x1f281b0 | → `EnemyManager.GetClosestOpponent` 0x1f1d950 / `GetOpponentsInVisionCone` 0x1f1e190 |
| opponent gather | `EnemyManager.JGIFRAKUITU` | 0x1f1f2b0 | iterates `RecRoom.Core.Combat.Combatant`, reads each `Transform.position` (LIVE, not replicated) |
| per-frame tick | `Enemy.Update` / `QuestAIController.Update` | 0x1f326f0 / 0x1d4d150 | both read `UnityEngine.Time.get_time` (LOCAL clock) + a `Timer` class |
| auto-aggro suppression | `Enemy.AddPreventAutoAggro` / config `QuestAiConfig_EnemyCommon.PreventAutoAggro` | 0x1f22310 / 0x1d51310 | ref-counted tokens + baked config; `get_CanAggroEnemies` hardcoded `return true` |

### `Enemy+0x280` is the enemy's OWN local AI FSM, not story state
`get_IsAggrod` (0x1f35100) and `get_CanStartCombat` (0x1f34d60) both read `[Enemy+0x280]` then
`word [+0x28]` (the FSM state enum): `==3` → aggro'd; `∈{2,5,7}` → may start combat. Set locally by
the `Authority*` combat/patrol methods. **No networked field, no server write.** (The field tools
`fields2025`/`md.py` give no offsets on this carve — read from disassembly.)

## WHEN enemies spawn/aggro: Encounters system, polled locally by the master

`RecRoom.Core.Encounters.*` — start-trigger → step graph, evaluated by the GameEncounter manager's
local tick loop (triggers' `IsTriggered` and `Enemy.get_CanStartCombat` have **0 direct callers** =
virtual dispatch from that loop, never pushed by a message):

- `RoomLoadEncounterStartTrigger.IsTriggered` = **0xd24d80, the shared `mov al,1;ret` stub → always
  true** (fires on room load).
- `PlayerSpawnedEncounterStartTrigger.IsTriggered` 0xf4ad20 (fires when the local player spawns).
- `StoryStateEncounterStartTrigger.IsTriggered` 0x1b13d50 → reads
  `QuestManager.get_CurrentRoomStoryState` + `get_CurrentCampaignStoryState`.
- Steps: `SpawnEnemyEncounterStep.OnStartRunning` 0x1b12d10, `TriggerEnemyBehaviourEncounterStep.OnStartRunning` 0x1b159f0.

So a quest of `[RoomLoad or StoryState(RSS==X) → SpawnEnemy + TriggerEnemyBehaviour]` spawns and
engages enemies on load/spawn **by content design**, locally, with no server event.

## The one server variable: the room-story-state PROPERTIES (`RSS`/`SS`/`DSS`)

`QuestManager.AwakeInternal` (0x18ab700) registers SynchronizedFields keyed by room-property names
**`RSS`** (`CurrentRoomStoryState`, backing field `QuestManager+0x1a0`, get 0x18b49a0 / set 0x18b4e30),
**`SS`**, **`DSS`**, **`DRI`** (DefaultRoomIndex), **`QUEST_TIMER`**. These are room properties synced
via op-102/103 and carried in the join-reply property dictionary.

- `RSS` is **written only by `ChangeStoryStateEncounterStep.OnStartRunning`** (0x1afe2d0) — the quest's
  own graph. There is NO generic "master sets starting RSS"; it starts at the SynchronizedField
  default and advances locally. (`QuestTestingTable.RpcMasterSetStartingStoryState` 0xda4200 is a
  debug table and sets the *campaign* state, not RSS.)
- recflare's solo join reply is **flag 3 = no property dictionary**, so `RSS`/`SS` are absent → default
  (`STATE_0`). **But for a solo master the client owns `RSS`**, so it defaults to the same value the
  real service's master would — this only differs if the **real matchmaking seeds an initial room
  property server-side** for a new quest instance (a quest-phase / start-state). That is a
  real-service capture question, NOT answerable from the client binary.

## Why no inbound message can be the trigger

1. Server→client traffic is ConnectionApproved / join-101 / TimeSync / Dissonance — none is a
   room-property write (102/103), an RPC (event 36), a buffered room event (op 22), or a cache replay.
2. The NGO client accepts only server→client opcodes `7/101/102/103/104/105`
   ([rr-named-message-room-protocol](rr-named-message-room-protocol.md)); recflare sends none of the
   data-plane ones to a solo client.
3. NGO network time (`NetworkTick` ≈ uptime×30 ≈ 6.8M) feeds **no** AI timer — the AI path is
   `Time.time`-only. The huge tick base is a red herring for aggro.

## To resolve the services difference
- **Exclude injection:** confirm the outbound trace sends the solo client zero op-102/103, event-36,
  op-22, cache-replay, nType-4 proxied frames. (Already essentially confirmed by the capture.)
- **Capture a real-service join** and diff its room-property dictionary against the flag-3 reply — if
  it seeds `RSS`/`SS`/a quest-phase, recflare must replicate it (send flag 7 + the dict).
- **Localize on the owner:** breakpoint 0x1b13d50 / 0x1b12d10 / 0x1b159f0 / 0x1f22a30 logging `RSS`/`SS`
  + timestamp. `AuthorityStartCombat` with no preceding Spawn/Trigger encounter ⇒ built-in auto-aggro
  (enemy spawned inside its vision cone of the spawn point = content/layout, identical on both
  services).
