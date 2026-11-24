# Player spawn handshake 212→450 and the observer embodiment broadcast (2026)

> The player-spawn handshake is a **master-targeted request/reply on the `RecRoomSceneManager`
> SCENE view**, NOT a broadcast: client → **212** `RpcMasterRequestPlayerSpawn(byte requestId)` to
> the **master player**, master → **450** `RpcSpawnNewPlayer(byte requestId, Vector3 pos, Quaternion
> rot, RRNetworkView spawnParent)` back to the **requester only**. Observers never see 450. The frame
> that embodies the avatar for OTHERS is a separate broadcast on the player's own view:
> **`Player.RpcBroadcastSpawnPlayer(bool firstSpawn, Vector3 spawnPosition, bool suppressAnimation)`**.
> Build `20260323.14`. Derived **2026-11-12** tracing the 212→450 handshake for a server-side bot.

## RPC send primitive (2026)
RPCs are sent via typed `RRNetworkView` methods, addressed by **ViewId + the Rpc MethodDef** (becomes
the u16 rpc index on the wire — see [rpc-shortcut-index-and-sender-gates-2026]):
- `RRNetworkView.RPC(string methodName, RpcTarget target, object[] params)` and overload
  `RPC(string, JNIVCIZIPSX targetPlayer, object[])` — the two wire forms.
- Typed families `RpcAll(RPCAction,args…)`, `RpcPlayer(targetPlayer,…)`, etc.
- Low-level send `PEJBWBFHLBI.GBHIYWZYOMP(ViewId, methodName, RpcTarget, RpcCacheOption, params[])`.
- **`RpcTarget`** (int): `All=0, Others=1, MasterClient=2, AllBuffered=3, OthersBuffered=4,
  AllViaServer=5, AllBufferedViaServer=6`. **`RpcCacheOption`** (byte): `DoNotCache=0, AddToRoomCache=4,
  AddToRoomCacheGlobal=5, RemoveFromRoomCache=6, RemoveFromRoomCacheForActorsLeft=7`.

## 212 — RpcMasterRequestPlayerSpawn (client → master)
- `RecRoomSceneManager.RpcMasterRequestPlayerSpawn(byte requestId, RPCInfo messageInfo)` 0x260cb10.
  **On the wire = one byte `requestId`**; `RPCInfo` is receiver-injected (sender identity), NOT sent.
  No pos/rot/team/account/spawn-index.
- **View = the `RecRoomSceneManager` SCENE view** — a scene-baked `RRNetworkView`, **fixed low id, NOT
  `actor*100000+N`**. Client learns it from the loaded room's scene objects. (Numeric id = capture per
  room.)
- **Target = the master player** via `RpcPlayer(...)`, target ref = `PEJBWBFHLBI.VJZKYKLEVCC()`
  (master-client). Reliable, not cached.
- Sender = async `<RequestSpawnFromMasterClient>d__30.MoveNext` 0x2784e20: sends 212, **awaits** a
  correlated reply (`ConfiguredTaskAwaiter` + response event `ODDUZQOLIWT`), retries with backoff,
  throws **`FailedToSpawnPlayerException`** ("Unable to spawn player!" / "Failed to spawn player on
  attempt {0} after {1}s. Retrying…") on timeout.

## 450 — RpcSpawnNewPlayer (master → requester ONLY)
- `RecRoomSceneManager.RpcSpawnNewPlayer(byte requestId, Vector3 spawnPosition, Quaternion
  spawnRotation, RRNetworkView spawnParent)` 0x260ccf0. `requestId` echoes 212. **pos/rot are LOCAL to
  `spawnParent`** (chosen spawn point's parent view; null = scene/world). **No instantiate arg — it
  positions an object that must already exist.**
- View = same `RecRoomSceneManager` scene view. **Target = the requester only** via `RpcPlayer(...)` —
  **NOT broadcast; observers never receive it.**
- Master side: `RpcMasterRequestPlayerSpawn` → `SceneSpawnManager.MWGUQHEKJXD` 0x277a5b0 picks the
  point (`QUAMSNFSSVT` filter, `SpawnPoint.MasterUse`, `GetFirstAvailableSpawnTransformLocalToParentView`
  0x277d6d0) → sends 450. On failure logs "Could not spawn player because a spawn point could not be
  acquired."
- Requester side: 450 runs **dynamic-state / embodiment init** (`OnDynamicStateDidInitializeDelegate`,
  `ObjectModelManager.LNBMIMWOHXE` 0x9bbfa20, `WBRILOCITGX` 0xa49b5f0/0xa49af40) on itself.

## The observer-facing embodiment frame (what others consume)
Because 450 is requester-only, observers embody via a **broadcast on the player's OWN view**:
- **`Player.RpcBroadcastSpawnPlayer(bool firstSpawn, Vector3 spawnPosition, bool suppressAnimation)`**
  0x19f52f0 — on view `actor*100000+1`, broadcast to others (Others/All — confirm by capture; handler
  is a dispatch thunk). `firstSpawn` = initial vs respawn; `suppressAnimation=false` plays spawn-in.
  Counterpart `RpcBroadcastDespawnPlayer(bool suppressAnimation)` 0x19f5250.
- This is the frame that transitions an observer from "object placed, body posed, eyes closed"
  (instantiate + event-28 only) to embodied. See
  [avatar-embodiment-eyes-and-spawn-handshake-2026].

## Ordering (Q14)
1. **Instantiate the `(Player)` networked object FIRST** — 450 positions an existing object (no
   instantiate arg).
2. Then **212 → await → 450**; the spawn position comes from the master in 450, not pre-chosen by the
   client.
3. **Observers embody on `RpcBroadcastSpawnPlayer` (broadcast), not on the instantiate and not on 450.**

## For a server-side bot
The 212/450 master dance exists so a REAL requester gets an authoritative spawn point and registers
with the master (teams, spawn-point occupancy). For pure appearance the bot can **skip it** and
directly emit **`RpcBroadcastSpawnPlayer(true, botPos, false)`** on its own view (actor*100000+1,
event 36) to others — the observer-facing embodiment frame. Recommended order:
**instantiate (Player) → stream event-28 poses → emit `RpcBroadcastSpawnPlayer`.**

## UPDATE 2026-11-12 — a malformed 212 is REJECTED at dispatch (log-confirmed)
The `requestId` arg is `byte` and MUST be sent type-tagged as **`SerializedType.Byte` (0x05)**, not
Int32 (0x0A). If sent as Int32, the master's PUN dispatcher finds the method on the scene view but
rejects the call — the handler never runs, so there is NO spawn-point attempt and NO 450. The
telltale master-side log (seen live, build 20260323.14):
`RPC method 'RpcMasterRequestPlayerSpawn' found on object with networkView 11 but has wrong
parameters. Implement as 'RpcMasterRequestPlayerSpawn(Int32)'. PhotonMessageInfo is optional as final
parameter.` ⇒ the received arg deserialized to Int32, method wants byte, mismatch → dropped. So "the
master never replies 450" is FIRST a param-type bug, not spawn-point acquisition / matchmaking /
`prev_room`. Fix the arg to a byte and the handler runs. (This is also why a server-side bot's 212
silently fails even with correct view/ordering/dynamic-state.) The same PUN type-match applies to any
RR RPC: args are type-tagged on the wire and matched against the method signature; a wrong tag is
rejected with this exact error naming the received type.

## NOT byte-proven (confirm by capture/test)
- `RpcBroadcastSpawnPlayer` exact target enum (Others vs All) and that its handler flips the
  alive/eyes state for observers (handler is a dispatch thunk).
- The numeric scene view id of `RecRoomSceneManager` per room.
- Whether observer eyes are gated on the broadcast vs. the requester's synced dynamic-state from 450
  — emit the broadcast and watch a throwaway observer to decide.
