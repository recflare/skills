# Rooms subrooms/{id}/data wire shape (room save commit)

> POST rooms/{roomId}/subrooms/{subRoomId}/data is the room-save COMMIT — the call that follows the Storage blob uploads. It carries the `friendlyActionDescription` `'save room'`, so it is **ENVELOPED**: `{Value: {Room, SubRoomDataSave}, Success, Error, error_id}`. A bare body or a 204 here fails the save, and the client's only symptom is that the save never completes.

Derived **2026-10-03** from build `20250718.01`, from a live capture of the save sequence.
Upstream half: [storage-upload](storage-upload-wire-shape.md) (the `FileType=1` / `FileType=6` blob uploads).
The GET on this same path is a different tier — see **Both verbs** below.

`POST https://rooms.<host>/rooms/{roomId}/subrooms/{subRoomId}/data` — service **16 = Rooms**
(facade `OALMDGJKBJH`). Path is `String.Format("rooms/{0}/subrooms/{1}/data", roomId, subRoomId)`,
literal slot **`0xD1A6900`**.

Client entry **`OALMDGJKBJH.KIMKMJBHHJB`** `0x7DFBD20` (+0x610). It carries the literal
**`'save room'`** at `0x7DFBE26` — a `friendlyActionDescription`, which is the reliable tell for an
**enveloped** helper on this facade ([rooms-isbanned](rooms-isbanned-wire-shape.md)).

## Request body — 12 keys, `.EHOIFCLDCGI`

Formatter `EHOIFCLDCGI` `.ctor 0x7793320` (+0x1030), key run `0x7793EC7`..`0x779420C`:

```json
{ "UnityAssetId": null, "ReferencedUnityAssetIds": [],
  "RoomData":    { "Filename": "2026-10-04/008e8a3d-…", "Hash": null, "OwnershipProof": null },
  "SubRoomData": { "Filename": "2026-10-04/c63e2467-…", "Hash": null, "OwnershipProof": null },
  "InventionUsage": "CAESBgil2gEQARIFCIECEAE=",
  "PersistenceVersion": 227, "OMVersion": 0, "Description": "test1",
  "AutoPublish": true, "ShouldStageSave": false,
  "RoomAssetOriginIds": [], "UgcSubVersion": 227 }
```

`RoomData` and `SubRoomData` are each the **upload response object** —
`{Filename, Hash, OwnershipProof}` (`.AOEMIBONGBD`), echoed straight back from
[storage-upload](storage-upload-wire-shape.md). `RoomData` is the `FileType=6` **RoomMetadata** blob (cloud-variable
definitions, room-level config); `SubRoomData` is the `FileType=1` **SubRoomSave** geometry blob.

A near-identical 7-key DTO `PEALNJLMGOB` `.ctor 0x771CDD0`
(`{SessionId, RoomId, SubRoomId, UnityAssetId, RoomData, SubRoomData, SavedByAccountId}`) exists for
the Studio path — do not confuse it with this one.

## Response — ENVELOPED, two nested objects

Send helper **`OALMDGJKBJH.PJPLCMBOAFB<T>`** (methodref `0x7DFBE1A`) — one of the facade's
**enveloped** helpers — generic inst **#1229** = **`.KHGKBALDIBN`**, a 2-key wrapper. Formatter
`DIEEPNKODOL` `.ctor 0x776E400`, keys `Room` / `SubRoomDataSave`:

```json
{ "Value": {
    "Room": { … },
    "SubRoomDataSave": {
      "SubRoomDataSaveId": 90001, "SubRoomId": 1307, "UnityAssetId": null,
      "ReferencedUnityAssetIds": [], "DataBlob": "2026-10-04/c63e2467-…",
      "DataBlobHash": null, "PersistenceVersion": 227, "OMVersion": 0,
      "SavedByAccountId": 205, "SavedOnPlatform": 0, "SavedOnDeviceClass": 0,
      "Description": "test1", "ModerationState": 0,
      "CreatedAt": "2026-10-04T00:00:00Z", "UgcSubVersion": 227 } },
  "Success": true, "Error": null, "error_id": null }
```

⚠️ **This is the most likely place to get the save wrong.** `Success: false` or a null body raises
**`LLCLDPPAGIJ`**, not `IONCMJIACFI` ([llcldppagij-envelope-failure-exception](../conventions/llcldppagij-envelope-failure-exception.md)). A **bare**
`{Room, SubRoomDataSave}` with no envelope, or a `204`, fails the same way — and because the failure
is an exception on the save path rather than a parse error, the visible symptom is simply that the
save never completes.

### `Value.SubRoomDataSave` — `.GCLKKDPHAON`, 15 keys

Formatter `NINGOINGMNB` `.ctor 0x77332C0` (+0x1440), run `0x7734152`..`0x7734584` — 15 keys, 1:1 with
the 15 declared fields:

| # | key | CLR | off |
|---|---|---|---|
| 1 | `SubRoomDataSaveId` | long | 0x10 |
| 2 | `SubRoomId` | long | 0x18 |
| 3 | `UnityAssetId` | `Guid?` | 0x20 |
| 4 | `ReferencedUnityAssetIds` | list | 0x38 |
| 5 | **`DataBlob`** | string | 0x40 |
| 6 | **`DataBlobHash`** | string | 0x48 |
| 7 | `PersistenceVersion` | int | 0x50 |
| 8 | `OMVersion` | int | 0x54 |
| 9 | `SavedByAccountId` | nullable | 0x58 |
| 10 | `SavedOnPlatform` | nullable | 0x60 |
| 11 | `SavedOnDeviceClass` | nullable | 0x68 |
| 12 | `Description` | string | 0x70 |
| 13 | `ModerationState` | enum `CCJNDAADAJO` (**byte**) | 0x78 |
| 14 | `CreatedAt` | DateTime | 0x80 |
| 15 | `UgcSubVersion` | nullable | 0x88 |

### ⚠️ `OMVersion == 0` can BLOCK the room load outright

Found **2026-10-07** while chasing the literal *"Rooms that were built with older versions of the
experimental feature preview of Hierarchical Building are no longer supported."* (`0xD127CB8`).

`LPFBNFALMGH.NFCHBPHJCMA(Google.Protobuf.ByteString saveBlob, out string message) -> bool`
`0x12F9D70` (+0x240) runs at room load and returns **true with a message to refuse the load**. Three
messages live in it:

| message | literal |
|---|---|
| `"…built with the experimental feature preview of Hierarchical Building…"` | `0xD128050` |
| `"…built with **older versions of** the experimental feature preview…"` | `0xD127CB8` |
| `"Could not join room: Incorrect room model was initialized."` | — |

The blob is first parsed as the **Hierarchical Building** experimental object-model protobuf
(interface call on `[this+0x20]`, slot 7, at `0x12F9E56`). If it does **not** parse as that model,
neither HB message can fire — the only possible refusal is *"Incorrect room model was
initialized."* If it does, the check consults the live SubRoom:

```
RecNet.Matchmaking.FINBJKEJMJL()      -> .PNAGCNAKDLL   (the current SubRoom)   0x12F9F46
  .[+0x40]  = <FDNAHKJMNKA>           -> .GCLKKDPHAON   (CurrentSave, this DTO)
    .[+0x54] = <CDMENHHBDEC>          -> int            = OMVersion  (key #8 above)
```

| condition | outcome |
|---|---|
| `CurrentSave == null` (`0x12F9F2D`) | **allowed**, no message |
| `CurrentSave.OMVersion != 0` (`0x12F9F5D`) | **allowed**, no message |
| **`CurrentSave.OMVersion == 0`** | **load refused** with the *"older versions"* message |

So **`OMVersion` is the one gate here a server owns.** Because `GCLKKDPHAON` has no
post-deserialize validation (`CPOBHIECLEN` is the shared no-op), **omitting `OMVersion` lands it as
`0`** — indistinguishable from deliberately sending `0`. On a room whose save blob is an HB model
that silently turns into a hard "this room is no longer supported" refusal, which reads like a
server-side ban rather than a missing integer.

Serve the `OMVersion` the client sent on the save commit (it is key #9 of the request body above),
and never default it to 0.

⚠️ **It has to be the `OMVersion` inside `SubRooms[].CurrentSave` of
`GET rooms/{id}?include=`.** That is the only wire path by which a `.PNAGCNAKDLL` reaches the client
— no route returns a bare SubRoom — and `FINBJKEJMJL()` hands that object to the check. The same
`OMVersion` key also appears on `GET .../saves/{saveId}` and `GET .../saves/no_unity_assets`
(identical DTO, identical key name), and **setting it there has no effect on this gate.** See
[rooms-room-by-id](rooms-room-by-id-wire-shape.md).

### Full branch decode — and why `OMVersion` is only ONE of the two HB messages

Re-read from the true method entry **2026-10-07** (the first pass started mid-instruction;
the stream from `0x12F9DE5` is identical either way). `LPFBNFALMGH`'s two relevant fields are

```
[this+0x10] = .ONIHMLNNEEF EFJNGOKNPIL      (call it B)
[this+0x20] = .DDOPFJHAODP JFOFGGINHNP      (call it A — the object-model loader)
```

and the method is:

```
loaded = A.<interface slot 7>(blob)   # 0x12F9E56 — load the save blob into the object model
bIsGck = <test on B vs .GCKIEPKGGOK>  # 0x12F9E72, TypeInfo slot 0x1D53000
aIsCab = <test on A vs .CABPMMMMPBM>  # 0x12F9E90, TypeInfo slot 0x1D4A6F8

if (loaded) {
    if (!aIsCab)  -> "…built with the experimental feature preview…"        # PLAIN
    else          -> OMVersion check above -> "…older versions of…" iff 0   # OLDER
} else {
    if (!bIsGck || aIsCab) -> allowed, no message
    else -> "Could not join room: Incorrect room model was initialized."
}
```

The two `rdx` operands resolve to the **`.CABPMMMMPBM` and `.GCKIEPKGGOK` TypeInfo slots** — the only
two type slots the method loads — so both are type tests on the model objects, not reads of a server
field. (`call 0x2f50` is a shared thunk; the exact helper was not resolved, so "type test" is the
reading of `rdx = TypeInfo, r8 = object`, not a byte-confirmed call.)

⚠️ **Consequence: `OMVersion` only gates the *"older versions of"* variant.** The plain
*"built with the experimental feature preview"* message fires when the blob **loads** but the
initialized object model is the wrong type — nothing in any HTTP payload changes that directly.
Observed on a live server 2026-10-07 with `SubRooms[0].CurrentSave.OMVersion = 138` (non-zero, so
the OLDER branch was impossible) still refusing the load. **Read the full string before chasing
`OMVersion`:** the presence or absence of the words *"older versions of"* decides which half of this
method you are in.

### The blob envelope — `.EINLNHFFMJL` and the `.DGBKKKBIBEO` version enum

The `loaded` test resolves all the way down, and the version enum survived obfuscation. Slot 7 of
interface `.CABPMMMMPBM` is **`bool GGKKJOPELBA(Google.Protobuf.ByteString)`** — the signature
matches the call site exactly. `ELEBFNLECEJ.GGKKJOPELBA` `0x8395AB0` is a 0x50-byte forwarder onto
**`static bool NCADFHACNLC.GGKKJOPELBA(ByteString)`** `0x839E7F0` (+0x100), which is:

```csharp
if (blob == null || blob.Length == 0) return false;              // 0x839E82B
var msg = MessageParser<.EINLNHFFMJL>.ParseFrom(blob);           // 0x839E894
if (msg.Payload == null || msg.Payload.Length <= 0) return false; // 0x839E8B6
return (int)msg.Version >= 3;                                     // 0x839E8BF  cmp [rbx+0x18], 3 / setge
```

So the save blob is a **two-field protobuf envelope**, `.EINLNHFFMJL` (typedef #57711):

| field | off | type | accessors |
|---|---|---|---|
| Version | 0x18 | enum `.DGBKKKBIBEO` | `ABOGEKBDALP()` / `NNJCNMKHDFO()` |
| Payload | 0x20 | `Google.Protobuf.ByteString` | `EFFADAHELHC()` / `AMEFEMCONAN()` |

and **`.DGBKKKBIBEO`** (typedef #57708, `int`) is fully readable:

| val | name |
|---|---|
| 0 | `V0PreObjectModel` |
| 1 | `V1ObjectModelHierarchy` |
| 2 | `V2ObjectModelHierarchy` |
| 3 | `V3Entities050` |
| 4 | `V4Entities050Compressed` |
| 5 | `V5BumpObjectModelVersionMay2024` |
| 3 | `OldestCompatibleVersion` (alias of V3) |
| 5 | `LatestVersion` (alias of V5) |

**`GGKKJOPELBA` is therefore "is this blob at least `OldestCompatibleVersion`, with a payload".**
V0/V1/V2 — the three pre-/early-object-model versions, i.e. the actual *experimental Hierarchical
Building* era — return `false`.

### ⚠️ Which means the two HB messages fire on MODERN blobs, not old ones

Re-reading the branch table with that in hand:

| `loaded` | meaning | outcome |
|---|---|---|
| `false` | blob is V0/V1/V2, or empty payload | `!bIsGck \|\| aIsCab` → allowed; else *"Incorrect room model was initialized."* |
| `true` | blob is **V3+ with a payload** | `!aIsCab` → **PLAIN HB message**; else → `OMVersion == 0` → OLDER HB message |

So if you are seeing an **HB message at all, your blob is already V3+ and fine** — an old
experimental blob would produce *"Incorrect room model was initialized."* instead. The failing test
is `aIsCab`: a parameterless bool on `.CABPMMMMPBM` (one of `MKALDDDJCLL`, `JCFDBGGLLMA`,
`HJIMAHOJABK`, `PGBFPNFKHOJ`, `BLOJBNMAJKJ`), i.e. **the client initialized the non-object-model room
model while the save is an object-model save.**

**Prime server-side suspect: the Room DTO's `UgcVersion` / `UgcSubVersion` / `MinUgcSubVersion`.**
Observed live 2026-10-07 on a room that refused to load with the HB message while serving
`UgcVersion: 1`, `UgcSubVersion: null`, `MinUgcSubVersion: null` at the Room level and
`CurrentSave.UgcSubVersion: 314` + `OMVersion: 138` on the save — i.e. a modern object-model save
advertised as a `UgcVersion 1` room. `PersistenceVersion` was ruled out by experiment (setting it to
176 everywhere changed nothing).

### ✅ RESOLVED: the predicate is `Room.UgcVersion == 2`

`0x2F50` is the **interface-slot invoke helper** — `invoke(uint16 slot /*rcx*/, Il2CppClass* iface
/*rdx*/, void* obj /*r8*/)`: it reads the slot from `cx`, then walks `obj->klass->interfaceOffsets`
(`[klass+0xB8]`, count at `[klass+0x146]`) looking for `rdx`. Both call sites in the gate do
`xor ecx, ecx`, so **slot 0**. That unlocks the chain:

```
al = A.<.CABPMMMMPBM slot 0>()                         # slot 0 = bool MKALDDDJCLL()
   = ELEBFNLECEJ.MKALDDDJCLL()                         0x8395DB0
   = this.IEHKKLCADNA                                  (field +0x28, .LDGOHEECGAG)
       .ALIBKKBONKO()                                  (.LDGOHEECGAG slot 6 -> .IJEHOPDKOAG)
       .MKALDDDJCLL()                                  (.IJEHOPDKOAG slot 0, sole method)
   = HAEFPIAJIBP.MKALDDDJCLL()                         0x12CF7E0
   = MIBODHPEFHP.BOFHONAMHDC( RecNet.Matchmaking.MLNNAKHOFCA() )
```

`MLNNAKHOFCA()` returns **`.HGMJJMJDHLJ`, the current Room DTO**, and
`MIBODHPEFHP.BOFHONAMHDC` `0x7E1A1C0` is **three instructions**:

```asm
cmp  byte ptr [rcx + 0xe5], 2
sete al
ret
```

`.HGMJJMJDHLJ` **extends `.MIBODHPEFHP`** (parentIndex 103828), and its derived fields start at
`0x108` — so `+0xE5` is a base-class field: `byte <EFBECMIPHHP>k__BackingField`, the only `byte`
in a run of `bool`s. Aligning the base layout tail against base keys 56–63 pins it 8-for-8:

| off | type | key |
|---|---|---|
| **0xE5** | **byte** | **`UgcVersion`** (#56) |
| 0xE6 | bool | `IsDeveloperOwned` (#57) |
| 0xE7 | bool | `IsJuniorCreated` (#58) |
| 0xE8 | `int?` | `CCU` (#59) |
| 0xF0 | bool | `IsRecRoomApproved` (#60) |
| 0xF1 | bool | `ExcludeFromLists` (#61) |
| 0xF4 | `int?` | `UgcSubVersion` (#62) |
| 0xFC | `int?` | `MinUgcSubVersion` (#63) |

**So the whole gate is:**

```csharp
if (blobVersion >= V3Entities050 && blobPayload.Length > 0) {
    if (room.UgcVersion != 2)                 -> "built with the experimental feature preview"
    else if (currentSave.OMVersion == 0)      -> "built with older versions of the ... preview"
    else                                      -> load proceeds
}
```

⚠️ **`Room.UgcVersion` must be `2` for an object-model room to load at all.** A V3+ save blob
served under `UgcVersion: 1` is refused with the plain HB message, every time, with no other
symptom. Confirmed live 2026-10-07.

⚠️ **Do not confuse this with the Invention DTO's `UgcVersion`**, which must be **1**
([inventions-v2-mine](inventions-v2-mine-wire-shape.md)). Same key name, different DTO, opposite required value.

### ✅ Gate confirmed from Player.log, and `UgcVersion` is a 72-call-site switch

Validated against a live `Player.log` **2026-10-08**, same room (21536/29208), two attempts:

| time | `Room.UgcVersion` | result |
|---|---|---|
| 14:16:37 | `1` | `Booting player to dorm: Cannot load room. Rooms that were built with **the experimental feature preview** of Hierarchical Building are no longer supported.` — the PLAIN variant, exactly as derived |
| 14:30:54 | `2` | **no HB message anywhere in the log**; the client proceeded further and hard-crashed |

So the `UgcVersion == 2` requirement is real and the plain/older split is as derived.

⚠️ **But `UgcVersion == 2` is not a one-field toggle.** `callxref` on the predicate
`MIBODHPEFHP.BOFHONAMHDC` `0x7E1A1C0` reports **72 call sites** — it is the global *"is this a
Rooms 2.0 room"* switch, read by `RRUI.Data.SubroomModel.get_CanMoveSubroom`,
`PlayerGameRoleManager.get_SupportedInCurrentRoom`, `RoomConsumablesManager.CreateRoomConsumableAsync`,
`RoomKeysManager`, `ScalabilityManagerBehaviour`, `ClothingCustomizerTool.Awake`,
`PublishInventionConditionalButton`, `EditRoomRoleSettingsWatchUIFlow.Awake` and ~60 more. Flipping
it switches a whole subsystem on, so expect second-order failures rather than one missing field.

### The crash that follows (`ObjectId = Invalid`)

```
[Error] ObjectId = Invalid
[Error] Lifetime = LoadInstance
  OHLFAAEBMBG:.ctor(GameObject, EOEFLGKDFOB, POOLCNKIBAH&)      0x83D7860 (+0x330)
  DCBAJFGNKCB:CLCLMIBBLAJ(RigidbodyEx, POOLCNKIBAH, LAPLJDMFFDB)
  NPGJFDBIBIL:CLCLMIBBLAJ(RigidbodyEx, POOLCNKIBAH, LAPLJDMFFDB)
  JGCOFFOABHP:CLCLMIBBLAJ(RigidbodyEx)
  RecRoom.RigidbodyEx:Awake()
Crash!!!                                  (native, GameAssembly -> UnityPlayer)
```

Both `[Error]` lines are the ctor **dumping its own state** — its only literals are
`'ObjectId = '` (`0x83D7A35`) and `'Lifetime = '` (`0x83D7A8E`), via `Debug.LogError`. They appear
**exactly once each** in a 26,081-line log, so they are novel to the change.
`.OHLFAAEBMBG` is an object-model handle wrapper
(`{.ONIHMLNNEEF, .CMKBJNKNGNP, .GOLADBGGMAB, .EOEFLGKDFOB}`).

⚠️ **Timing says this is EARLIER than the HB gate, so "the gate passed" is not proven.** The
crash lands `0.08 s` after `START: LoadScene.SafeLoadSceneAsync(Basement)` (902.6499 → 902.7279),
whereas on the `UgcVersion: 1` attempt the HB message fired ~2.4 s *after* that scene finished
loading. All that is established is that the client got further and died in base-scene object
registration — a `RigidbodyEx` in the scene being registered into the object model with no valid
object id.

**How to apply:** treat `UgcVersion` as a room-wide capability flag, not a loader hint. If a room does
not genuinely need Rooms 2.0, re-saving it from this client as a `UgcVersion: 1` room avoids the
entire surface; `OMVersion: 138` / `UgcSubVersion: 314` / `RankedEntityId` on the failing room all
suggest its save came from a much newer Rec Room build than `20250718.01`.

`LPFBNFALMGH.COJPPCIBOJB` `0x12F9700` (+0x670) is the only caller. It carries the literal
**`'InitObjectModel'`** — confirming OM = **Object Model** — and a hardcoded GUID
**`4c222ae4-bbce-4cfd-a8a6-cf7de1955161`** referenced twice (`0x12F996A`, `0x12F9C18`), which is a
candidate marker for the HB object model. What selects which model gets initialized was **not
derived**; `PersistenceVersion` is the obvious suspect and is worth making consistent first.

`CCJNDAADAJO : byte` — `None 0`, `Pending 1`, `Approved 2`, `Denied 3`, `ModeratorPending 4`,
`ModeratorApproved 5`, `ModeratorDenied 6`.

**`DataBlob`/`DataBlobHash` is the echo of `SubRoomData.Filename`/`Hash`** from the request — i.e. the
server is expected to return the subroom blob reference it just recorded.

The three `nullable` members (9/10/11) and `UgcSubVersion` were read from field layout, not from a
traced consumer; their inner types are not pinned beyond "Nullable".

### `Value.Room` — `.HGMJJMJDHLJ`, not derived

Generic inst **#1188 = `.HGMJJMJDHLJ`** — **now derived**: the bare 63-key Room DTO, whose first two
keys are `DataBlob` / `DataBlobHash`. See [rooms-room-by-id](rooms-room-by-id-wire-shape.md).

## ⚠️ There is no read-back path for `RoomData`

This matters for "a cloud variable will not commit". Checked explicitly:

- `SubRoomDataSave` echoes only the **subroom** blob (`DataBlob`/`DataBlobHash`). There is **no
  RoomData/metadata counterpart** among its 15 keys.
- `RoomDataFilename` / `RoomDataHash` are real wire keys (slot `0xD0CD9D8`) but appear in **exactly
  one** formatter in the whole build — `HEPHPFJFFDP` `.ctor 0x7712800` → `.CMPBBIDGFAK`, which belongs
  to the **Studio remote-run** routes `remote-run/session` and `remote-run/push-to-studio`
  (`EKKJPDGOAHE.FILEDFKGAGD` `0x7DC7080`, `.AGHPEBDCGLG` `0x7DC6D60`). Not the in-game save.
- There are **no** `RoomMetadata`, `MetadataFilename`, `RoomDataSave` or `CloudVariables` wire keys at
  all.

**RESOLVED 2026-10-03:** the reference comes back under a *different name* — `GET rooms/{id}?include=`
returns it as the Room DTO's **key #1 `DataBlob`** (and #2 `DataBlobHash`). The chain renames the value
at every hop: upload `Filename` -> commit `RoomData.Filename` -> read `DataBlob`. That is why searching
for `RoomDataFilename` only ever found the Studio DTO. See
[rooms-room-by-id](rooms-room-by-id-wire-shape.md).

Practical consequence: before hunting a read route, make this POST return the **enveloped** shape with
`Success: true` and a fully populated `SubRoomDataSave` whose `DataBlob` echoes the request's
`SubRoomData.Filename`. A failed commit and a missing read path look identical from the UI.

## Both verbs, two tiers

| verb | helper | tier |
|---|---|---|
| **POST** (this note) | `PJPLCMBOAFB<T>` — carries `'save room'` | **enveloped** `{Value:{Room, SubRoomDataSave}, …}` |
| GET | not derived | — |

Same path, different helper, so do not share a handler shape. Compare
[rooms-playerdata-me](rooms-playerdata-me-wire-shape.md), where GET is bare and PUT is enveloped on one path.
