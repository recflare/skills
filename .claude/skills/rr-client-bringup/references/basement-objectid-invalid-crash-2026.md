# `ObjectId = Invalid` native crash on a Rooms-2.0 Maker Room (2026 build)

> A **hard native crash** — not an exception, not a boot-sequence failure — while loading a room
> whose scene is `Basement` (`MAKER_ROOM`). The last three log lines are always:
> ```
> [Error] ObjectId = Invalid
> [Error] Lifetime = LoadInstance
> Crash!!!
> ```
> ⚠️ **The crash is a `Debugger.Break()` compiled to a raw `int3`.** The managed failure underneath it
> is an ordinary `NullReferenceException` that the client *catches* — the catch block logs those two
> lines and then breaks into the debugger. With no debugger attached, `int3` raises
> `EXCEPTION_BREAKPOINT` and Unity's handler kills the process. **This is an assert firing, so the
> client is telling you its input was bad; it is not a random memory fault.**

Resolved **2026-10-14** on build `20260323.14`. Same crash was first seen on `20250718.01` and
recorded, obfuscated and unexplained, in
[rooms-subrooms-data](../../wire-shapes/references/endpoints/rooms-subrooms-data-wire-shape.md) ("The crash that follows
(`ObjectId = Invalid`)"). The 2026 metadata de-obfuscates the whole chain.

## Reading a native crash frame — resolve the RVAs

`Player.log` prints the module base and the raw return addresses:

```
C:\...\GameAssembly.dll:GameAssembly.dll (00007FFF13950000), size: 291041280
...
========== OUTPUTTING STACK TRACE ==================
0x00007FFF1D52D47E (GameAssembly) (function-name not available)
```

**RVA = address − module base.** Feed each RVA through `methods.pkl` (bisect on the sorted start
addresses) and the stack becomes readable. ⚠️ **Only the innermost frame is a faulting address; every
other frame is a RETURN address**, so the interesting instruction is the `call` immediately *before*
it.

| # | RVA | method |
|---|---|---|
| 1 | `0x9bdd47e` | `RecRoom.ObjectModel.EmbodiedRigidbodyExImpl..ctor` **+0x30e — the `int3`** |
| 2 | `0xa15e471` | `RecRoom.Rbex.ObjectModel.BFGEMMXLWSZ.YXLXPOFLABM` (ret addr of the ctor call) |
| 3 | `0xb34ec1` | IL2CPP generic-shared invoke thunk |
| 4 | `0xa17488f` | `RecRoom.Rbex.ObjectModel.VBEFKBTLOCQ.YXLXPOFLABM` |
| 6 | `0xa16c800` | `RecRoom.RigidbodyExManager.YXLXPOFLABM` |
| 7 | `0xa16d3c7` | `RecRoom.RigidbodyEx.Awake` +0x157 |

2025 → 2026 name map, for reading the older note:

| `20250718.01` | `20260323.14` |
|---|---|
| `OHLFAAEBMBG..ctor(GameObject, EOEFLGKDFOB, POOLCNKIBAH&)` `0x83D7860` | `ObjectModel.EmbodiedRigidbodyExImpl..ctor(GameObject, KMOQKJRUHKT, RigidbodyExData)` `0x9bdd170` |
| `DCBAJFGNKCB.CLCLMIBBLAJ` | `Rbex.ObjectModel.BFGEMMXLWSZ.YXLXPOFLABM` `0xa15e400` |
| `NPGJFDBIBIL.CLCLMIBBLAJ` | `Rbex.ObjectModel.VBEFKBTLOCQ.YXLXPOFLABM` `0xa1747d0` |
| `JGCOFFOABHP.CLCLMIBBLAJ` | `RigidbodyExManager.YXLXPOFLABM` `0xa16c710` |

## The ctor, and why `Debugger.Break()` is reached

`EmbodiedRigidbodyExImpl..ctor(GameObject gameObject, KMOQKJRUHKT rigidbodyEx, RigidbodyExData data)`
`0x9bdd170`, real bounds `0x9bdd170..0x9bdd492` (`fstart.py`). Body:

```
gameObject.GetComponent<ObjectModel.MFRBGNAGTXA>()   0x9bdd20f   ; iface: ObjectLocalId get_ObjectId()
  .get_ObjectId()                                    0x9bdd229   -> this[+0x18]  (ObjectLocalId, a struct)
this[+0x20] = rigidbodyEx
ObjectLocalId.ANUNEWMBPCH(ref this[+0x18])           0x9bdd258   -> ObjectModel.NJEOPPRLVYV   ; resolve owning object system
  .<slot 0>() -> service provider                    0x9bdd272
  NQBLFOUZQEF.DODVAYLOFEX<RbexEmbodimentService>()   0x9bdd281   -> this[+0x10]
RbexEmbodimentService.ZIUYDORKAML(...)               0x9bdd2b4
RbexEmbodimentService.GRJZBWFENLC(...)               0x9bdd2ca
data.<slot 4>(this)                                  0x9bdd2e6
ret                                                  0x9bdd300
```

Five inlined null checks (`0x9bdd1ff`, `0x9bdd217`, `0x9bdd260`, `0x9bdd2a1`, `0x9bdd2d2`) all branch
to `call 0xc403a0` = the IL2CPP *raise NullReferenceException* helper. **The whole body is inside a
try/catch**, and the catch funclet is the block at `0x9bdd31c..0x9bdd492` — it shares the parent's
frame, which is why it reads `this` back out of the home slot `[rsp+0x90]`:

```
0x9bdd31c  this.IQKJCATCPVR()            ; -> ObjectLocalId  (field +0x18)
0x9bdd33d  ObjectLocalId.ToString()
0x9bdd345  "ObjectId = "  -> Debug.LogError          <-- log line 1
0x9bdd396  ObjectModelManager.SFIFYIOFSRD()          ; -> Foundation.Service.GZOGVDISCYD (current scope)
0x9bdd3d1    .XSNPGPPHUMG()                          ; -> ObjectModel.Lifetime
0x9bdd39e  "Lifetime = " -> Debug.LogError           <-- log line 2
0x9bdd46a  System.Diagnostics.Debugger
0x9bdd47e  int3                                      <-- THE CRASH
0x9bdd47f  rethrow
```

Both literals (`'ObjectId = '` `0xFE1F238`, `'Lifetime = '` `0xFC89F78`) have **exactly one xref each
in the entire binary**, both inside this ctor — so those two log lines are a unique fingerprint for
this crash.

## What the two values mean

**`ObjectId = Invalid`** — `this[+0x18]` is the default `ObjectLocalId`. Two ways to get there, and the
log cannot distinguish them because in the first case the field is never written at all:

1. `GetComponent<MFRBGNAGTXA>()` returned **null** — the `RigidbodyEx`'s GameObject carries no
   object-model entity view. Implementers of `MFRBGNAGTXA`:
   `ObjectModel.EmbodiedEntity`, `ObjectModel.DisembodiedEntityView`, `ObjectModel.TYCGBKIHXGP`,
   `ObjectModel.BVAQGUDMNAD`.
2. The component existed but `get_ObjectId()` returned the invalid id, so
   `ObjectLocalId.ANUNEWMBPCH()` (resolve the owning `ObjectModel.NJEOPPRLVYV`, sole implementer
   `RecRoom.ObjectModel.ObjectModel`) returned null.

✅ **`gameObject` itself is never null** — frame 2 obtains it from
`Component.get_gameObject()` at `0xa15e440` immediately before the `new`.

**`Lifetime = LoadInstance`** — `RecRoom.ObjectModel.Lifetime`:
`Uninitialized -1`, `Application 0`, `LoginSession 1`, `PhotonRoom 2`, `OMRoom 3`,
**`LoadInstance 4`**, `COUNT 5`. This value is *normal* for a room load; it is not the anomaly. Its
only diagnostic use is proving that an object-model scope **was** active — because
`RigidbodyEx.Awake` has a clean bail-out when there is none:

```
0xa16d33b  ObjectModelManager.ANUNEWMBPCH()   ; current scope
0xa16d343  je 0xa16d424                       ; null -> skip registration entirely, no crash
```

So the scene's `Awake` pass ran *with* a live object-model scope but *before* the objects had ids.

## ⚠️ The real switch: Legacy vs ObjectModel Rbex provider

`RecRoom.Rbex.IQECWWRWFGM` has **three** implementers — the dispatcher plus one provider per room
version:

| type | role |
|---|---|
| `RecRoom.Rbex.ObjectModel.VBEFKBTLOCQ` | the dispatcher |
| `RecRoom.Rbex.Legacy.BFGEMMXLWSZ` | **RoomV1 path** — held at dispatcher `+0x10` (allocated first in `.ctor` `0xa1748b0`) |
| `RecRoom.Rbex.ObjectModel.BFGEMMXLWSZ` | **RoomV2 path** — held at `+0x18`; **this is the one that crashed** |

`VBEFKBTLOCQ.YXLXPOFLABM` `0xa1747d0` picks between them on one bool:

```
0xa174828  r8 = this[+0x20]                  ; the ObjectModel instance
0xa17483a  BIHWTDLPPPA.ZUHPPKCGGXY()         ; bool, iface slot 0
0xa174841  je  0xa174849
0xa174843  r8 = this[+0x18]                  ; TRUE  -> ObjectModel provider  (needs an OM entity)
0xa174849  r8 = this[+0x10]                  ; FALSE -> Legacy provider
0xa17488a  call provider.YXLXPOFLABM(rigidbodyEx, data, ctx)
```

`RecRoom.ObjectModel.ObjectModel.ZUHPPKCGGXY` `0x1add350` is a one-instruction getter —
`return this[+0x32]` (a plain bool field, `movzx eax, byte [rcx+0x32]; ret`).

**So the crash means that flag was `true` for this room.** `RecRoom.ObjectModel.ObjectModel`'s fields
include **`RecRoom.ObjectModel.RoomVersionService XWZNDFWBIRO`**, whose only mutator is
`Set(RecRoom.Foundation.RoomVersionType)` `0x9bc3690`, and that enum is:

```
RecRoom.Foundation.RoomVersionType : int   None = 0, RoomV1 = 1, RoomV2 = 2
```

### ✅ The flag and the room version are one unit — proven from the reset path

`RecRoom.ObjectModel.ObjectModel.RNXVLANKMCO()` `0x9bc08a0` clears **both** in the same four
instructions:

```
0x9bc08aa  rbx = this[+0x28]                       ; the RoomVersionService
0x9bc08bc  Ownership.GJOMTMVABDK(&rbx[+0x10], 0)
0x9bc08ce  Ownership.NXPWHZJBIYZ(&rbx[+0x10], 0, 0)  ; RoomVersionType = None
0x9bc08d8  this[+0x32] = 0                          ; OM Rbex provider = off
```

`RoomVersionService.Set(RoomVersionType)` `0x9bc3690` touches the identical `Ownership` struct at
`+0x10` of the service, which is how `ObjectModel[+0x28]` is pinned as the service (it is also
`ObjectModel`'s only `RoomVersionService` field, `XWZNDFWBIRO`). **So "room version" and "use the
object-model Rbex provider" are set and cleared together** — being routed to the crashing provider
*is* the room being treated as `RoomV2`.

⚠️ **Not pinned:** the *enable* site. Both `VLNAMSJFHHY(bool)` `0x1b66aa0` (the one-instruction
`[rcx+0x32] = dl` setter) and `RoomVersionService.Set` report **0 call sites** — they are inlined or
reached by interface dispatch, exactly the case `callxref` cannot see. A byte-pattern scan for inlined
`mov byte [reg+0x32], 1` across the whole image finds only false positives on other types
(`MClusterManagerBehaviour.RoomLoad` writes offset `0x32` on
`Core.Creation.Shapes.MHHNPBBWPTS`, not on `ObjectModel`). So *what* reads the room metadata to decide
V1 vs V2 is still open; the 2025 note's candidates (`UgcVersion`, `OMVersion`, `UgcSubVersion`,
`PersistenceVersion`) remain the suspects.

## ✅ ROOT CAUSE (2026-10-14): the subroom's `UnitySceneId` is the V1 Maker Room

> ✅ **Fix applied and confirmed 2026-10-14: the crash is gone.** The scene now loads as `ugcr2` and
> the room-load pipeline runs to completion. It then fails differently, with
> `FailedToSpawnPlayer (Code 8700)` from a Studio asset bundle whose scripts do not bind —
> [studio-asset-bundle-script-bind-failure-2026](studio-asset-bundle-script-bind-failure-2026.md).

Settled by diffing the server's `GET rooms/21536?include=` against a **reference export of the same
room from real Rec Room**. One field differs that matters:

| field | recflare | real Rec Room |
|---|---|---|
| `SubRooms[0].UnitySceneId` | **`a75f7547-79eb-47c6-8986-6767abcb4f92`** = `MAKER_ROOM` | **`5d4e40d8-f289-4295-a6e1-4f907835007d`** = `MAKER_ROOM_2` |
| `SubRooms[0].Name` | `Home` | `TheBlock` |
| `CurrentSave.DataBlobHash` | `8LZXL0pWGEQ8cL6tTPobJ8EZ8ktBfNDv3ULvzXfHYlk=` | **identical** |
| `CurrentSave.PersistenceVersion` / `OMVersion` / `UgcSubVersion` | `251` / `198` / `449` | **identical** |

**The save is byte-for-byte the real `RunTheBlock` save. The base scene it is being applied to is the
wrong one.** `MAKER_ROOM` is the legacy V1 maker room (Unity scene `Basement`); `MAKER_ROOM_2` is its
Rooms-2.0 counterpart. So with `UgcVersion: 2` the client enables the object-model Rbex provider and
then loads a **V1** scene whose `RigidbodyEx` objects are not object-model entities — which is exactly
the assert.

✅ The 2026 client **does** know `5d4e40d8-f289-4295-a6e1-4f907835007d` (literal `0xFDAA360`), so this
is a one-field server fix, not a missing-scene problem.

⚠️ **The scene-location enum renumbered between builds.** On `20260323.14` the registration `.cctor` is
`LWWSBHUHPZM..cctor` `0xa18be80`, and pairing each `mov r8d, N` with the `mov rdx, <guid literal>`
immediately after it (rule anchored on `MAKER_ROOM` → `0x18` = 24, matching `SCENES.md`) gives
**`MAKER_ROOM_2` = 41 on 2026**, where `SCENES.md` records 40 for `20250718.01`. Only those two entries
were checked, so all that is established is that something was inserted between 25 and 40. **Re-read
the enum per build; the GUIDs are stable, the integers are not.**

### The row is a default Maker Room scaffold carrying someone else's save

Every other difference points the same way — the room row was created as a **fresh blank Maker Room**
and then had the real save attached, without the scene, name or version fields being updated:

| field | recflare | real |
|---|---|---|
| `Description` | `This room is a blank canvas. Make it into whatever you like!` | — |
| `ImageName` | `MakerRoom.jpg` | `cv8vjhunbytzazzzwwz23yrlq.png` |
| `SubRooms[0].MaxPlayers` | 12 | 10 |
| `SubRooms[0].Accessibility` | 2 | 1 |
| room `PersistenceVersion` | **0** | (save says 251) |
| room `UgcSubVersion` / `MinUgcSubVersion` | **314 / 314** | (save says 449) |

The room-level `PersistenceVersion: 0` and `UgcSubVersion: 314` against a save at `251` / `449` are a
second, independent inconsistency: **the save-commit path is not propagating the save's versions back
onto the room row.** Not proven to contribute to this crash — the crash is upstream of the save
download — but fix it in the same pass.

## How to act on it

The room is being treated as **RoomV2 / Rooms 2.0**, so its base scene objects are routed through the
object-model Rbex provider, which requires every `RigidbodyEx` GameObject to already be an object-model
entity. For a `Basement` / `MAKER_ROOM` base scene they are not, so the first one to `Awake` asserts.

⚠️ **The two builds fail this room in opposite directions, which is the whole diagnosis.** On
`20250718.01`: served `UgcVersion: 1` the client *refused* it outright —
`Cannot load room. Rooms that were built with the experimental feature preview of Hierarchical
Building are no longer supported.` — and served `UgcVersion: 2` it got further and hard-crashed here.
So the room's save genuinely carries Hierarchical-Building / Rooms-2.0 markers, while its base scene
is a legacy `MAKER_ROOM`. **One side of that pair is wrong in the server's data, and the client has no
third option.**

1. ✅ **Set `SubRooms[].UnitySceneId` to `5d4e40d8-f289-4295-a6e1-4f907835007d` (`MAKER_ROOM_2`)** for
   subroom 29208. The room is correctly `UgcVersion: 2`; what was wrong is the base scene. **Do not
   "fix" this by dropping to `UgcVersion: 1`** — on `20250718.01` that produced an outright refusal
   (*"Rooms that were built with the experimental feature preview of Hierarchical Building are no
   longer supported"*), and `UgcVersion` is a 72-call-site capability switch rather than a loader hint
   ([rooms-subrooms-data](../../wire-shapes/references/endpoints/rooms-subrooms-data-wire-shape.md)).
2. **Audit every room row for a V1 scene GUID with `UgcVersion: 2`.** Any room created from a default
   Maker Room template and then given a Rooms-2.0 save has the same latent crash. The pairing to
   enforce is `MAKER_ROOM` ⇔ V1 and `MAKER_ROOM_2` ⇔ V2 (likewise `CUSTOM_DORM_ROOM` /
   `CUSTOM_DORM_ROOM_2`).
3. **Propagate the save's `PersistenceVersion` / `UgcSubVersion` onto the room row on commit.**
4. **Diff this room's metadata against a room that loads.** ⚠️ **Confirmed 2026-10-14: every other
   room on this server joins fine — only `21536/29208` crashes.** So neither the build nor the
   `Basement` scene is the trigger; something in *this room's* `GET rooms/{id}` + subroom metadata
   flips it to `RoomV2`. Capture the response for a working room and for this one and diff the version
   fields first. The crash happens **before** the subroom save downloads, so only the metadata
   fetched at `Fetch room details completed` can be responsible — the save blob is off the hook.

✅ **`Basement` is not a fallback** — it is `MAKER_ROOM`, scene-location 24, so the server deliberately
reported `a75f7547-79eb-47c6-8986-6767abcb4f92`. See `SCENES.md`. A *wrong* scene would be
`dormroom2` plus the warning `RecNet game session contains unknown scene location ID`, which this log
does not contain.

## Recognising the log shape

This crash leaves a **succeeded** join above it, which is what distinguishes it from the 404 cascade in
[cv1-mappings-join-nre-2026](cv1-mappings-join-nre-2026.md):

| | 404 cascade | this crash |
|---|---|---|
| `[Platform.BootSequence] ErroredPromiseException` | present | **absent** |
| `DestroyOldObjectsTask.BulkDestroy(N)` | `(0)` | **`(24)`** |
| `Login screen scene was loaded while not in the pre-game controller state` | present | absent |
| ending | "glitch in the matrix", process alive | `Crash!!!`, process gone |

Observed timeline in the 2026-10-14 capture (5,322 lines, process dies at `t=37.93`):

```
18.95  leaving to go to room: 78/98 instance:1426882     ; @djdevin's Dorm
20.46  LoadScene.SafeLoadSceneAsync(dormroom2)
26.58  Room load complete                               ; <-- clean join, BulkDestroy(24)
35.95  leaving to go to room: 21536/29208 instance:1426892
36.26  Fetch room details completed in 299.417ms
37.24  TachyonClient.ConnectToRoomInstance: 104.234.6.145:7777
37.75  LoadScene.SafeLoadSceneAsync(Basement)
37.93  ObjectId = Invalid / Lifetime = LoadInstance / Crash!!!
```

⚠️ **The crash is 0.19 s into the scene load, before the new room's `DOWNLOADING_DATA` phase.** No
subroom save has been applied yet, so nothing in the room's *content* can be blamed — only the room
**metadata** fetched at `36.26` and whatever it switched on.

`ObjectModel running with additional DOTS debug information.` appears at line 34 of this log. This is a
dev-configured object model, which is why the assert is compiled in at all; a stock retail client
would likely take the `rethrow` without the `int3`.

## Also in that capture, all non-fatal

Everything else matches [post-join-residual-log-items-2026](post-join-residual-log-items-2026.md):
`giftdropstore` 404 at 12.56 s (`[LiveOps.TLA.Recipes.Ingredients]`) and 26.73 s
(`OutfitManager.GetStorefront`, plus `RecNet.FSCENWUOSRW.KPGTZNEXCEY(CurrencyType)` as a second
consumer); `objectives/v1/cleargroup` still answering `'[]'`; the room-list 404 at 29.26 s with its
consequent NRE in `RoomQueryManager.QueryStaticListSource`, and a third NRE at 37.25 s in
`RoomListViewModel.FetchData` from the same faulted list; `makerai/checkfreetrialeligibility`
answering `'false'` at 32.98 s; the fire-and-forget `TrickstersTLAManager.VKRUFYNKGCE` NRE at 9.70 s.

**New in this capture, not previously recorded:**

```
[Error] Error deserializing SpawnableTool (Marker)(Clone) (UnityEngine.GameObject):
        Serialized GUID 0848fb3e-2c8b-43eb-b9ef-4b0a1264a652
        does not match prefab value e469ee80-1c71-4b95-8add-9fe0cb797987
```

**8 times at 25.88 s**, during the *successful* dorm load (room 78/98, `SubRoomDataSaveId: 45`). The
subroom save holds a `Marker` spawnable whose recorded prefab GUID is not this build's prefab GUID, so
those 8 objects deserialize with default state. Non-fatal and unrelated to the crash, but it is the
same class of problem — **saved room data carrying identifiers from a different client build** — and
worth fixing before chasing the version flags above.
