# A remote avatar's eyes/blink are a LOCAL Animator idle, woken by MOVEMENT (2026)

> **RESOLVED 2026-11-12 (live, confirmed by the bot):** a bot avatar that renders asleep (eyes
> closed, no blink) from spawn **wakes the instant it moves** — a brief position change over event-28
> is enough, permanently, and it is NOT the 212→450 spawn handshake. This confirms candidate (1) of
> update #3: eyes-open is the observer-LOCAL social-idle face state (`SetIdleHappy`→`Animator.SetBoolID`,
> fired from the gaze update `LSYDFFHRWLA` 0x159e9d0), and a **stationary** avatar is never entered
> into the observer's live/gaze-able player set that drives it. Any real movement registers the avatar
> there → the local idle/gaze face runs → eyes open and stay open. **Bot fix (shipped): emit a brief
> movement right after spawn.** The whole 212/450 investigation below was orthogonal to the eyes; keep
> it for the spawn-point/master mechanics, not the face. See the detail chain in updates #1–#3.

> A remote player rendered from an **instantiate + event-28 pose stream alone** appears as a body
> that poses/moves correctly but with **eyes closed and no idle blink** — "placed but not awake."
> The eyes/blink are **not** on any wire: they are a **local Unity Animator idle state** each
> observer plays for an avatar it considers a *spawned, alive* player. The thing that flips an
> avatar from "placed" to "embodied/awake" is the **spawn handshake**
> `RpcMasterRequestPlayerSpawn` (212, `RpcSpawnNewPlayer` on the wire) → master `RpcSpawnNewPlayer`
> (450, 0x260ccf0), which runs player **dynamic-state initialization**. Build `20260323.14`.
> Derived **2026-11-11** from a bot (account 16) that rendered a stable standing body via verbatim
> event-28 frames but with closed eyes, having skipped 212/450.

## The face/eyes are Animator-driven and local, NOT in event-28

- `RecRoom.Avatars.PlayerFacialAnimatorBase.SetIdleHappy` (0x97ef570) ends in
  `UnityEngine.Animator.SetBoolID` — the "living" idle face (open eyes + periodic blink + happy
  idle) is an **Animator state**, set locally on each observer. It is never serialized into the
  event-28 pose blob (which is transforms only; see
  [avatar-movement-stream-event-28-2026](avatar-movement-stream-event-28-2026.md)).
- The face DOES have its own **separate low-rate networked sync** — `PlayerFacialAnimator`
  (`WriteSyncData` 0x159fd50 / `ReadSyncData` 0x159f430 / `HasSyncDataToWrite` 0x159e940, all
  virtual/0-direct-callers; registered via `RecRoom.Networking.PEJBWBFHLBI` + a `Timer` in
  `PlayerFacialAnimatorBase.Start` 0x18ad300). But `ReadSyncData` carries only **two small Vector3
  feature offsets** (gaze/jitter, read off sync object `KLPEYQQZALU`) and toggles a face GameObject
  active — it is live-expression nuance, **not** the eye-open gate. Copying a face packet is not the
  fix.
- Avatar Animator parameters exist as string literals: **`Alive`, `Awake`, `Spawned`, `Sleeping`,
  `Idle`, `Wave`**. The idle-alive state (eyes open, blink) is reached only when the avatar is driven
  as a live/spawned player; the default/dormant Animator state is eyes-closed.

## The remote avatar = LivePlayerPuppet, driven by a spawned Player

- Remote avatar is `RecRoom.Players.Puppet.LivePlayerPuppet` (Start 0x1538030, `get/set_TargetPlayer`
  0x1538160/0x1538180), hierarchy `PlayerPuppet` ← `AnimatedPlayerPuppet` (menu/render-texture
  previews, `PlayEmote`/`PlayAnimationFidget`/`Update` 0x1532550) ← `LivePlayerPuppet` (in-room).
- It animates idle from its `TargetPlayer` (the networked `RecRoom.Players.Player`). `Player` exposes
  the spawned/alive gates: `get_IsInitialized` 0x19fdd50, `get_IsInitialLoadFinished` 0x19fdd00,
  `get_IsSpawning` 0x19fdef0, `get_PlayerSpawnEvent` 0x19ff0b0, `get_LocalPlayerIsSpawnedAndNotFading`
  0x19fe320, and `RpcBroadcastSpawnPlayer` 0x19f52f0. `PlayerAvatarDisplayBase.get_IsInitialized`
  0x24de7f0 is the display-side gate.

## The spawn handshake does the embodiment, not just placement

`RecRoomSceneManager.RpcSpawnNewPlayer` (450, 0x260ccf0) fires **player dynamic-state
initialization**, not just a position: `OnDynamicStateDidInitializeDelegate`,
`ObjectModelManager.LNBMIMWOHXE` 0x9bbfa20, and the embodiment system `RecRoom.Core.WBRILOCITGX`
(`ZKDQMQBVNIA` 0x a49b5f0 / `IMHQWMFNHLG` 0xa49af40), plus `PlayerSpawnEvent`/spawn broadcast. This
is the transition from *instantiated object* to *embodied/spawned/alive*. Request side:
`RpcMasterRequestPlayerSpawn(requestId,RPCInfo)` 0x260cb10.

So: instantiate creates the puppet, event-28 moves its bones (body poses correctly) — but without
212/450 the `Player` never enters the spawned state, so `LivePlayerPuppet`'s Animator never leaves
its dormant default: **eyes closed, no idle blink, probably no idle breathing/sway**.

## Ruled out (do not re-chase)
- **Voice/mic activity** is NOT the eye driver. `Player.UserIsPresent` (get 0x19ff810 / set
  0x1a00740, matches string `"UserIsPresent"`) is read only by `PlayerVoice`, mic toggles
  (`UtilityExpressoUIFlow`), and `PlayerSpecificVoiceIndicator` — a mic/AFK presence flag.
- **`BlinkingRenderer`** (StartBlinking 0x20d7390 / StopBlinking 0x1b06060) is a quest-explosive
  blinking *light* (callers: ExplosiveTrap, QuestExplosiveEnemy, QuestSciFiChargeShotEnemy), NOT
  avatar eyes.
- **XR `leftEyeOpenAmount`/`rightEyeOpenAmount`** are `UnityEngine.InputSystem.XR.Eyes` VR
  eye-tracking input, not the avatar face sprites.
- **Avatar-data load** sets the model/outfit/`IsInitialized` (a prerequisite) but the blink itself is
  the Animator idle.

## Minimum fix + confirming test
- **Minimum to open eyes + idle-blink**: make the avatar count as a *spawned/alive* player, not send
  more pose or face data. Drive the spawn path for the bot's actor.
- **Decisive test** (emit-and-verify): have the master send `RpcSpawnNewPlayer`/`RpcBroadcastSpawnPlayer`
  for the bot's actor (or bot sends 212 and the real master answers 450), observe a throwaway client:
  eyes open + blink ⇒ confirmed. If still closed, next suspect is the Animator `Alive`/`Awake` param
  not being driven off the spawned `Player` — trace what `LivePlayerPuppet` reads.

## NOT byte-proven
The architecture is confirmed; the single `if(spawned) SetBool("Alive"/"Awake")` branch inside the
puppet was not traced to one instruction. The confirming test above closes it.

## There is NO polled "isSpawned" network field (added 2026-11-12)
Reverse-xref'd every spawn/visibility string literal to its referencing code — **none is a networked
avatar field**: `PlayerSpawned` → `RecRoom.Analytics.GANKGKUAXGZ` (analytics event name);
`WAS_PLAYER_SPAWNED`/`player_spawned` → `AppExitDetector` (crash-detection PlayerPrefs, local);
`PlayerStatusVisibility` → `RecRoom.Settings.XIBHKUUXBTM` (settings key); `PlayerInitSpawn` →
`Player..ctor` (construction tag). So there is **no op-103 key or player NetworkVariable a spawned
player writes that observers poll to open the eyes**, and 450 is requester-targeted so observers never
see it either.

**The eyes-open condition is a LOCAL face-Animator bool, not a field.** `PlayerFacialAnimator` has NO
`Update`/`LateUpdate`/`Blink` loop — only `OnEnable`/`ReadSyncData`/`WriteSyncData`/`SetIdleHappy`
0x97ef570/`LocalPlayEmote`/`UpdateFaceDisplays`. A remote face is driven by (1) the **owner's
networked face-sync stream** — a separate per-component sync channel (`WriteSyncData` 0x159fd50 →
wire → `ReadSyncData` 0x159f430, live face-feature offset vectors; NOT op-103, NOT a named
NetworkVariable), and (2) a one-shot `SetIdleHappy` → `Animator.SetBoolID` that puts the face Unity
Animator into its idle/alive state (hash from a face-config asset, no wire name); until set, the
Animator default = eyes closed. `SetIdleHappy` is reached from the gaze update `LSYDFFHRWLA`
(0x159e9d0), which runs only when the avatar is driven as a live/present player.

**Bot levers (no field to set):** emit the embodiment event `RpcBroadcastSpawnPlayer` on the bot's
own view (see [player-spawn-handshake-212-450-2026]); and/or produce a `PlayerFacialAnimator`
face-sync packet. Test order: emit the broadcast first (eyes open ⇒ done); if still closed, add a
face-sync packet (eyes open ⇒ it's the owner face-sync stream — trace that packet's layout next).
Static analysis cannot fully separate which of the two gates `LSYDFFHRWLA`; the emit test decides.

## UPDATE 2026-11-12 — capture resolves it: NOT a face channel, broadcast is a CUE not state
A capture of everything a SCREEN player (acct 205) emits while idle = movement(28), object/room
state, counters, instantiate(29) — **no face-sync channel at all**, yet 205's eyes are open. So for a
screen avatar the eyes-open is purely embodiment (confirms Q16: `SetIdleHappy` needs no face packet).
Bot emitted `RpcBroadcastSpawnPlayer(firstSpawn=true,pos,suppress=false)` on its own view → eyes
STILL shut. Conclusion: **`RpcBroadcastSpawnPlayer` is the spawn-in ANIMATION CUE, not the awake/alive
state transition.** The persistent awake state is set when the requester PROCESSES 450 (dynamic-state
init) and lives on the networked object; a bare cue with no underlying state no-ops. The handler
0x19f52f0 is a 6-byte dispatch stub in BOTH disk and mem images (body behind the RPC invoker), so it
can't be byte-read — but the emit test is decisive.
- RPC index note: indexes **0–471 are STABLE** (case-insensitive sort of `[RPCMethod]` names), only
  472–512 vary per session (see [rpc-shortcut-index-and-sender-gates-2026]); `RpcBroadcastSpawnPlayer`
  = 77 is in the stable block, so the index is not the bug.
- `RpcBroadcastSpawnPlayer(bool firstSpawn, Vector3 spawnPosition, bool suppressAnimation)` on event
  36; args type-tagged via `RYVCIIOUZLU`: bool `[0x04][u8]`, Vector3 `[0x12][3×f32 LE]`, bool
  `[0x04][u8]`.
- Event code **33 = `RR_BulkDestroy`** (NOT expression state); 31 BulkInstantiate / 32 Destroy / 34
  TransferOwnership nearby.
- **Highest-yield next step:** diff the bot's player instantiate(29) payload vs the real screen
  player's — the instantiate dict is the persistent, all-observer (and late-joiner) embodiment source
  (body-world pose key 6, display mode, avatar config, spawn markers). The one skipped write most
  likely lives there, or in the dynamic-state that processing 450 initializes.

## UPDATE 2026-11-12 #2 — the eyes are a LOCAL per-frame face state; the gate is op-103 ControllerDisplayMode
Capture facts: bot's instantiate is BYTE-IDENTICAL to a real player's (so the missing write is not in
29); driving the real 212→450 failed (master never replied). Decisive finding: **the face is driven
LOCALLY every frame for every avatar** — `Player.LateUpdate` 0x19e20d0 → `get_FacialAnimator` →
`PlayerFacialAnimatorBase.UpdateFaceDisplays` 0x97f0840. So eyes-open is NOT gated on 450 / the
broadcast / the face-sync stream / instantiate — it is a per-frame facial state reading a
**continuously-synced property**. **212→450 is NOT the eyes gate.**

Eye source depends on PRESENTATION MODE: **VR** avatars get eye-open from networked eye-TRACKING
(`leftEyeOpenAmount`/`rightEyeOpenAmount`/`CenterEyeAnchor`, perm `com.oculus.permission.EYE_TRACKING`)
→ no tracking data = eyes closed; **SCREEN** avatars get eyes from a LOCAL idle (open+blink, no
tracking). The switch is **`ControllerDisplayMode` (VR=1/SCREEN=2)**, an op-103 player property
(`Player.get/set_ControllerDisplayMode` 0x19fcc10/0x19ff990) that `PlayerAvatarNetworkSynchronization.
UpdateInterpolation` 0x1b418c0 and the puppet `RMWKDYSYBHS.FRSDIKGUWJW` already branch on (the
"SCREEN arms are receiver-derived" path). **Prime suspect for closed eyes: the bot streams VR-style
poses but never sets `ControllerDisplayMode=SCREEN(2)`, so observers treat it as VR and wait for
eye-tracking data that never comes.** Fix/test = set the op-103 `ControllerDisplayMode` property to 2;
confirm by diffing the bot's op-103 writes vs a real screen player's (acct 205). NOT byte-proven that
the facial eye branch reads ControllerDisplayMode specifically (carve's facial FSM unreadable) — the
op-103 diff or a breakpoint on `UpdateFaceDisplays` settles it cheaply.

## UPDATE 2026-11-12 #3 — CORRECTION: the face driver is LOCAL, eyes-open is a local idle state
The bot writes `ControllerDisplayMode=2` byte-identical to a real screen player (205) and still shows
closed eyes, so ControllerDisplayMode is NOT the gate (update #2 was wrong). **Reading
`UpdateFaceDisplays` 0x97f0840 fully: it runs on `Time.realtimeSinceStartup` + `System.Math` (local
blink/jitter phase) + null checks — it does NOT read any per-frame networked value.** So there is NO
"continuously-synced eye field"; the eyes are driven LOCALLY. (Earlier "continuously-synced value
switched by ControllerDisplayMode" was wrong.)

Mechanism: eyes-open = the face Animator's idle/alive state, set LOCALLY by `SetIdleHappy` 0x97ef570 →
`Animator.SetBoolID`, fired from `LSYDFFHRWLA` 0x159e9d0 — a SOCIAL-GAZE update that iterates a list
of nearby players and reads `PlayerHead.transform`. The face Animator's default/entry state is
eyes-CLOSED; it opens only when this local idle/gaze runs on the avatar. `Player.LateUpdate` 0x19e20d0
drives `UpdateFaceDisplays` for any avatar whose `get_FacialAnimator != null` (no IsLocal gate).

So closed-vs-open is NOT on the wire (confirmed: event-28 is transforms only, no face/eye field;
`IsSleeping` is a transform-rest bit that 205's own observers also get while seeing open eyes; the
blink is local). It's that the bot's avatar never reaches the live social-idle face state on the
observer. Two LOCAL candidates: (1) the bot's avatar isn't in the observer's live/gaze-able player set
→ `LSYDFFHRWLA` never fires → face stays at default closed; (2) the bot's avatar's face style didn't
build (`BuildFaceStyleAsyncIfChanged`→`SetFaceSettings(eyeSelection,…)`) so the eye feature has no
open texture (body/outfit render on a separate pipeline). **Static analysis of the carve is exhausted
here** (face FSM is dispatch stubs). Runtime decides: breakpoint `SetIdleHappy` 0x97ef570 +
`LSYDFFHRWLA` 0x159e9d0 on the OBSERVER, filtered to the bot — never fires = (1) presence/registration;
fires but eyes shut = (2) face build. Quick visual triage: whole face wrong/blank = (2); face correct
but only eyes shut = (1).

Q19 (master ignores a delivered 212): `RpcMasterRequestPlayerSpawn` 0x260cb10 → `SceneSpawnManager.
MWGUQHEKJXD` 0x277a5b0 gates the 450 on SPAWN-POINT ACQUISITION — queries `RecNet.Matchmaking.
GUDYYSHFFKE`, reads requester props `prev_room`/`prev_subroom`/`prev_room_tags`, picks via
`QUAMSNFSSVT`/`SpawnPoint.MasterUse`/`GetFirstAvailableSpawnTransformLocalToParentView`; null → logs
"Could not spawn player because a spawn point could not be acquired", no 450. Handler ALSO defers on
`OnDynamicStateDidInitialize` (ObjectModelManager), so the master needs the requester's object+dynamic
state initialized on ITS side first — **sending 212 before instantiate can never get a reply**. Likely
block = bot's dynamic state never initializes on the master and/or recflare matchmaking returns
nothing for the bot (server variable). Q20: SpawnManager view = `RecRoomSceneManager`'s scene-baked
RRNetworkView (not a fixed const); view 11 was delivered so it's right FOR THIS ROOM; read it live
from the scene singleton per room.
