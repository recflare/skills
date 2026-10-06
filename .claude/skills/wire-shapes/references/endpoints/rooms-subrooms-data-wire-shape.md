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
