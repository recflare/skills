# Avatar movement stream — event 28 `RR_NetworkSynchronization` (2026)

> The per-frame avatar pose stream (Photon 201 → wire **event code 28 =
> `RecRoom.Networking.NetworkEventCode.RR_NetworkSynchronization`**, delivery 0 / cache 0 / receiver 2,
> unreliable-**Sequenced**) is produced per player view by **`PlayerAvatarNetworkSynchronization`**. Its
> body is a **bit-packed `BitPacker` stream** (NOT byte-aligned, NOT a Photon dictionary), carrying 4
> avatar `NetworkTransform` sub-poses each gated by a presence bit. The avatar's visibility is tied to
> the **network object** (instantiate 29 / destroy 32 / ownership), not to this stream — a view that
> never sends event 28 stays rendered at its last/instantiate pose. Build `20260323.14`. Derived
> **2026-11-11** for the "Claude AI" server-side walk-and-wave bot (Request #19).

## Producer / consumer — `PlayerAvatarNetworkSynchronization`

Virtual `RRNetworkBehavior` serialize override; **0 direct callers** = driven by the RR serialization
scheduler, which wraps the per-view frame (`[len][05][client ms][sequence][view id]`) and raises event
28. The inner bit-stream is what these methods write/read.

| method | RVA | role |
|---|---|---|
| `Awake` | 0x1b3ebb0 | registers the 4 avatar `NetworkTransform`s |
| `Serialize(BitPacker)` | 0x1b41340 | **sender**: `isLocal` gate → `Time.realtimeSinceStartup` stamp → for each of 4 transforms: `BitPacker.GGSROABXXOX(bool)` presence bit then the packet (`WPKEZFPWWUN` 0x1b41c80 → `NetworkTransform.PrepareSyncDataPacket` + `DDJNDNDEEZV.XQIXCNAGDPI`). Branches on `Player.get_ControllerDisplayMode` 0x19fcc10. |
| `Deserialize(BitPacker)` | 0x1b3edd0 | **receiver**: reads 4 presence bits (`BitPacker.ZXDPKDWUMOM`) + 4 packets (`XTQAQJUPBJQ`) |
| `UpdateInterpolation` | 0x1b418c0 | per-frame receiver smoothing: `NetworkTransform.SmoothMove` (interpolate) + `SimpleSmoothMove(extrapolationWeight)` (extrapolate from Velocity/AngularVelocity) + `PerformFrameUpdate` on each transform |

The **4 transforms = head-local, left hand, right hand, body-world** — the same 4 `Vector3/Quaternion`
pairs carried in the instantiate (event 29) payload key `6` `object[8]`. `HasSyncDataToWrite` on the
avatar components is the shared `mov al,1;ret` stub 0xd24d80.

Only **4 classes** implement `WriteSyncData(BitPacker)` at all: `RecRoom.Core.Locomotion.PlayerMovement`
(0x1a6afe0), `PlayerHand` (0x1cc22a0, ×2), `RecRoom.Avatars.Face.PlayerFacialAnimator` (0x159fd50),
`LaserTeleporter` — the layered per-component state on top of the 4 transforms. (Many other gameplay
types — RCCar, GroundVehicle, NetworkEnemyHeadRotation, FullBodyPuppetTool … — have their own
`Serialize/Deserialize(BitPacker)` and ride event 28 under their own view.)

## BitPacker is LSB-first (confirmed from the core writer)

`BitPacker.BDXJXHHKLMT(value, count)` **0x9853fc0** (write-bool `GGSROABXXOX` 0x9854840 calls it with
count=1): masks `value` to `count` bits, **shifts it left by the current bit-position** (`bitpos & 63`)
and **ORs** it into a 64-bit accumulator flushed little-endian. So the **first bit written is bit 0 (LSB)
of byte 0**; a decoder/encoder must consume/emit bits LSB-first, byte 0 first. Read-bool = `ZXDPKDWUMOM`
0x98549... (mirror). Quaternion quantizer `CRKSUBUDQSX(bp, quat, bits)` 0x9856fe0 is smallest-three
(compares the 4 comps via `Single.Equals`, drops the largest, writes the rest through `BDXJXHHKLMT`); the
bit count is a **call-site parameter**, not baked in the quantizer. Position quantizer `APDFIIJECNW(bp,
val, min, max, bits)` 0x98568c0 likewise takes range+bits from the caller.

## Captured frame anatomy (relay-forwarded, account 205 VR avatar, 2026-11-11)

Four real frames (2 standing, 2 walking), **84 bytes each**, byte-diffed:
- **Header bytes 0–4 `00 01 50 00 09`** (const). Best read: `00 01` = constant 2-byte tag; **bytes 2–3 LE
  u16 `0x0050` = 80 = the bit-packed payload length** (= bytes 4–83); `09` = first payload byte.
  (Unconfirmed vs size — all frames are 84 B here; capture a different-size avatar to prove byte 2 tracks
  length.)
- **Trailer bytes 77–83 `00 f8 01 f0 0d 20 03`** (const); `ff 15 00` at 67–69.
- **Both standing and both walking frames are the same 84 B with the same const skeleton** ⇒ the layout is
  **fixed, all 4 poses always present** (no change-delta omission; presence bits set).
- Byte-diff separates the poses: bytes that are **const-within-a-state but differ standing↔walking**
  (≈5–8,10–14,18–24,33–40,48,55,58,70,73,75–76) = the **body transform/velocity** (steady when still,
  steady-but-different when walking forward); bytes that **vary between two same-state captures**
  (≈25–31,42–49,60–66) = the **head + two hand transforms** (VR tracking jitter even when "standing").

## Measured frame layout (15 standing frames, account 205 VR, LSB-first)

**`header[0:5] + 4 × pose[18] + trailer[7] = 84 bytes`**, proven by bit-variance diff:
- `header` bytes 0–4 `00 01 50 00 09` (const; bytes 2–3 LE = `0x0050` = 80 = payload length byte 4→83).
- **Pose 0 = bytes 5–22** — **perfectly constant across all standing frames = the stationary BODY-world
  pose.** Its first 4 bytes `0c 00 e8 01` are the body position/velocity (→ `1c 80 37 00` when walking).
- **Poses 1–3 = bytes 23–40, 41–58, 59–76** — jitter every frame = HEAD + two HANDS (VR tracking).
- `trailer` bytes 77–83 `00 f8 01 f0 0d 20 03` (const footer for this avatar).

**Per-pose 18-byte internal layout** (same in all three jittering poses; offsets are within the pose):
- **offset 0–4**: quantized **position** (moderate jitter).
- **offset 5–8**: **rotation** — smallest-three quaternion, ~30 heavy-varying bits (the 3 clusters land at
  frame bytes 28–31 / 46–49 / 64–67, exactly 18 apart). 2-bit largest-component index + 3 components.
- **offset 9–17**: velocity / angular-velocity + per-pose structural constants (the sub-view-id reference
  for this transform, constant per avatar; e.g. the `49 e0`, `05 00`, `81` anchors at pose boundaries).

So to synthesise: write the 5-byte header, then 4 poses (body first), each = position(0–4) + rotation
smallest-three(5–8) + velocity/flags/subview(9–17), then the 7-byte footer. Recompute, never replay.

**Quantization — AUTHORITATIVE from the encoder `PlayerAvatarNetworkSynchronization.YDPMBBSFGSN`
0x1b42170** (the ONLY caller of the avatar position quantizer `HCORMQGTURS.APDFIIJECNW` 0x98568c0):
- Per-pose write order: `LGHGQYEUQKP` (sub-view/context) → bool flag → `RIIXDBJEBSX` (full-float vec3) →
  bool flag → **`APDFIIJECNW` (11-bit/component range-quant vec3** — `mov [rsp+0x20],0xb` = bits=11) →
  bool flag → `RLLXSUEOJXE` (full-float vec3). The flags select full-vs-compressed per vector.
- **Position is RELATIVE, not absolute**: `NetworkTransform.PrepareSyncDataPacket` 0x15d6350 uses
  **`DiffFromSync`** + `get_hasParent`, so event-28 carries a **delta / parent-relative** position, NOT
  world coords. ⇒ a body that hasn't moved since instantiate encodes ~zero-delta, which is why the known
  world pos (-5.4996,..) does **not** appear in the bits, and why ground-truth-to-bits matching is a dead
  end. **The absolute spawn pose lives in the instantiate (event 29); event-28 is incremental motion.**
- The 11-bit range `[min,max]` is a `Vector3` pair read from a config object (`[rax+0x10..0x1c]`), i.e.
  **delta bounds**, not a world box — not an immediate; trace its init (or read the decoder) to get values.
- **Rotation**: smallest-three (`CRKSUBUDQSX`/`ZVNHLQMPUIV`), width is a call-site param (not yet read).

**Consequence for a bot:** it does NOT need an absolute world↔bits map. Stand = emit zero-delta frames;
walk = emit bounded deltas.

### Decoder-derived per-pose read order (AUTHORITATIVE, `DDJNDNDEEZV.Deserialize` 0x9ab92b0)

Each of the 4 poses is decoded by `DDJNDNDEEZV.Deserialize` (mirror of encoder `XQIXCNAGDPI`), via
`PlayerAvatarNetworkSynchronization.XTQAQJUPBJQ` 0x1b41f60 (flag → `DDJNDNDEEZV.Deserialize` →
`NetworkTransform.QueueSyncDataPacket`). Read order, LSB-first:
1. context/header (`IMOJIOTDQGW`)
2. bool flag (`BitPacker.ZXDPKDWUMOM`)
3. int `ContinuousMovementID` (`LXJDHDZHOBZ.KKWIXLPGYLT`)
4. **`ViewId` ParentView** (`ViewId.MXIECNUYXCY`/`PartialViewId`) — the frame the position is relative to
5. **position** — conditional: full **float32×3** (`JMIYNCETVWK`/`RIIXDBJEBSX`, `mov r8d,0x20` ×3 = 32-bit
   each) OR a compressed path (the 18-byte frames take the compressed branch; `HOBNVIWPZTK` float reads)
6. 3× bool flags
7. **rotation = smallest-three, 10 bits/component** (`HCORMQGTURS.WIIDOYABLEE` 0x9857e00, `mov r8d,0xa`),
   reconstruct largest `= sqrt(1 − a²−b²−c²)` (the `sqrtss`), range ≈ 1/√2, + 2-bit index ⇒ 32 bits total
8. bool flag + **velocity** single floats (`HCORMQGTURS.XESMAFFZWLM`)

So: **rotation = 10-bit smallest-three (32 b); position = 11-bit relative delta (APDFIIJECNW) or float32×3;
position is ParentView-relative.** The exact compressed-position branch offsets are config-flag-gated and
best finalized by the **emit-and-self-verify loop** (below), since relative coding makes foreign-capture
offset-matching unreliable.

### The ParentView anchor is RELATIVE — the payload is actor-agnostic
The per-pose ViewId is read as a **`PartialViewId`** (`{isPartial, viewId, offset, destroyOnLeave}`) via
`ViewId.MXIECNUYXCY` 0x99c2bf0 → `PartialViewId.IBFWBVCANUI` 0x9938a80, which reconstructs the id by
applying `offset` to a base (`MRAOAUAYYFN`=`id/100000`, `From`, `ObjectNetworkId`). The **raw view-id value
(e.g. 800001) does NOT appear anywhere in the 84-byte payload** (verified: no 800001–800028 at any width).
ViewId internally is `actor<<20 | sub`-style (`shr 0x14`). ⇒ **The event-28 pose payload carries no
absolute actor/view id; the sender's identity comes from the NGO message sender, and the ParentView offsets
are self-relative.** So a bot does **NOT** write `actor*100000+n` into the pose anchors — it copies them
unchanged regardless of its actor. (Confirm empirically by the verbatim-standing test below; if a foreign
standing payload renders a standing bot without crashing, the payload is actor-agnostic.)

### Safe path to a moving bot (no desync risk)
A **zero-motion frame** — deltas = 0, rotation = the bot's spawn quaternion (10-bit smallest-three), the
bot's OWN ParentView/sub-view anchors, correct 84-byte framing (header len = 80) — reconstructs on the
receiver as `instantiate baseline + 0` = standing. Zero-delta encodes identically regardless of the delta
range, so the bot needs the range ONLY for motion. Correct framing (own view ids, right length) cannot
desync — so unlike a replayed foreign frame, a self-authored zero-motion frame is safe to test live.

## The transform packet — `RecRoom.DataLayer.NetworkTransformSyncData` (13 fields)

```
Context (QRNHLOZQKVX) · ContinuousMovementID int · IsSleeping bool · CompressedRotation bool ·
CompressedPosition bool · Position Vector3 · Rotation Quaternion · HasDeformationScale bool ·
Scale Vector3 · Velocity Vector3 · AngularVelocity Vector3 · SyncIsRedundantResend bool · ParentView ViewId
```

The `bool` fields are **presence/mode bits written before the payload** they gate: `IsSleeping` (skip
dynamics), `CompressedPosition` / `CompressedRotation` (choose quantized vs full), `HasDeformationScale`
(Scale present), `SyncIsRedundantResend`. `ParentView` lets a transform be relative (head-local to body).

### Encoding — `RecRoom.Networking.HCORMQGTURS` (static BitPacker codecs)

| write / read | encoding |
|---|---|
| `RLLXSUEOJXE` / `CPPBCXRONBB` | **full Vector3 = 3× float32** |
| `RIIXDBJEBSX` / `JMIYNCETVWK` | full Vector3 (second variant) |
| `APDFIIJECNW(bp,val,min,max[,bits])` / `CRWXKCNRMXN` | **range-quantized Vector3** into `[min,max]` at `bits` → the compressed-position path |
| `CRKSUBUDQSX(bp,quat,bits)` / `WIIDOYABLEE` | **smallest-three compressed quaternion** at `bits` |
| `ZVNHLQMPUIV(bp,quat,bool,bits)` / `YECUUPOYMVM` | compressed quaternion (presence variant) |
| `RUSMODTTIAD` / `XESMAFFZWLM` | single **float32** |

So **position** = 3×float32 when `CompressedPosition=0`, else quantized in a min/max range at N bits;
**rotation** = full when `CompressedRotation=0`, else smallest-three at N bits. Compression is toggled by
`NetworkTransform.UseCompressedPosition` / `UseCompressedRotation` / `AllowCompression` /
`CanCompressRotationForSize(maxSize)`. **The exact bit widths and the position min/max range are
call-site int constants — read them from a capture or deeper disasm; not pinned here.** Production traces
keep only 48 bytes so the blob tail was never captured; breakpoint `DDJNDNDEEZV.XQIXCNAGDPI` 0x9ab9cd0
(encode) / `0x9ab92b0` (decode) and `PlayerAvatarNetworkSynchronization.Serialize` 0x1b41340 to dump it.

## No-event-28 behavior (does a standing bot still render?)

**Yes.** Lifetime = the network object: instantiate (29) + ownership create it, `RR_Destroy` (32) /
owner-leave remove it. There is **no sync-timeout despawn or hide** keyed on event 28. A view that stops
sending holds its last pose (receiver keeps `SmoothMove`-ing toward the last target). A **solo** player
sends no movement only because receiver=2 (others) has nobody to replicate to — a visibility non-issue.

## The wave (and gestures)

- **A greeting wave is NOT an RPC and NOT a flag.** There is no `Rpc*Wave*` in the image. A VR player's
  wave is just their **right-hand `NetworkTransform` moving in the event-28 stream**; observers'
  `RecRoom.CircuitsV1.WaveNode` (a circuit detector, has a `WaveMode`) recognizes it **locally** from the
  streamed hand motion. → To make the bot wave, oscillate the right-hand transform; send nothing else.
- **Interactive two-hand gestures DO use an RPC** (event 36):
  `RecRoom.Core.Gestures.PlayerHandGestures.RpcHandGestureDetected(PlayerHand otherHand, Gesture gesture,
  int serverTimeMiliseconds, bool pauseOthers)` @ **0x1a11380** (no `RPCInfo` param → handler never
  learns caller; gate in the relay). Driven by `AuthorityTriggerGesture(Gesture, PlayerHand, bool)`.
  Enum **`.Gesture` (typedef #16267)**: None=-1, Highfive=0, Fistbump=1, HandshakeStart/Cancel/Success,
  StopGesture*, CheerGesture*, GameReviveHandshake*, GiveTakeSuccess. These need a second hand/player and
  are the "hands touch" interactions, not a solo wave.
- Head gestures (nod/shake/tilt) are a **separate** `.Gesture` enum (typedef #1268).

## Screen vs VR arm pose

`ControllerDisplayMode` = enum **`RecRoom.LocalPlayerControllerDisplayMode`** (UNINITIALIZED=0, **VR=1,
SCREEN=2**) is a **SynchronizedField on `Player`** (`VPEHBKURMFI<…>` field `DNJOYRNUVNM`) — it rides a
**player property (op-103)**, NOT the event-28 blob, but `Serialize`/`UpdateInterpolation` read it. For a
SCREEN player the hands are not tracked devices, so other clients **derive** the arm/hand pose
(procedural/animation) rather than from raw streamed hand transforms. Bot implication: set the display
property; VR mode ⇒ you must feed believable hand transforms, SCREEN mode ⇒ receiver animates arms from
locomotion.

## Spawn choreography

`RecRoomSceneManager.RpcMasterRequestPlayerSpawn(byte requestId, RPCInfo)` @0x260cb10 → master
`RpcSpawnNewPlayer(byte requestId, Vector3 spawnPosition, Quaternion spawnRotation, RRNetworkView
spawnParent)` @0x260ccf0 (also `RpcMasterRequestPlayerRespawn`/`RpcRespawnPlayer`). A client that
instantiates `(Player)` at a self-chosen position **will render on others** (avatar is driven by the
instantiate + event 28, independent of the spawn exchange). But the **master owns the spawn record** —
teams, spawn points, the player-list — so skipping the handshake risks wrong/no team and the master not
registering the bot. For pure "walk + wave" visibility the instantiate + `rrPnr` + event 28 suffice; for
correct integration do the spawn handshake.

## What a remote avatar needs besides the instantiate

Networked body = `rrPnr` player property (room index, op-103) + the `(Player)` instantiate (29).
**Name and outfit come from an account/avatar API lookup by account id, NOT the join string.** The avatar
is built via `RecRoom.Avatars.PlayerAvatarDisplayBase.SetOutfitSelections(IList<AvatarItemSelection>, …)`
from avatar data downloaded for that account (`…DownloadLocalAvatarForExistingAccount` etc.); the name
resolves from the account likewise. `R1TagManager.RemoteSetRuntimeTags` (RPC) syncs gameplay tags (not
required to render). Without valid account/avatar data the remote shows a **default/potato** outfit —
default, not invisible. So bot account 16 needs a real account id the API resolves to a name + avatar;
the body shows regardless.
