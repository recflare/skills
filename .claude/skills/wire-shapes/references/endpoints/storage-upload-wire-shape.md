# Storage upload wire shape (multipart)

> POST upload on the STORAGE service (svc 8) is the generic multipart blob upload — the `FileType` form field is the 19-member enum NJNHMGCEENL, and **`FileType=6` is `RoomMetadata`** (cloud-variable definitions and room-level config, NOT the room geometry save, which is `SubRoomSave=1`). It returns a REQUIRED bare `{Filename, Hash, OwnershipProof}`; if that response is wrong the client has nothing to attach to the room.

Derived **2026-10-03** from build `20250718.01`, from a live room-save multipart capture.

`POST https://storage.<host>/upload` — service **8 = Storage**
(`mov dword ptr [rsi+0x18], 8` at `0x7D94F7B`), verb **POST** (`HttpMethod` statics `[rcx+0x20]` at
`0x7D94F3A`). Whole-route literal `'upload'`, written to the request's path field at `0x7D94F85`.

⚠️ **It is not on `api.<host>`, `rooms.<host>` or `econ.<host>`.** A room save fans out across
services, and the blob half lands on Storage. Sibling literal on the same service:
`upload/roomReportScreenshot`.

Client entry **`JPDBADBNOEB.GOOEEFGKCNI`** `0x7D94DE0` (+0x260). The thin forwarder
`AACANGGGMOL.GOOEEFGKCNI` `0xFD8480` passes `FileType` straight through in `r8d`, so the value is
chosen by the (inlined) caller — there is no constant to find in the facade.

## Request — multipart, four possible parts

| part name | notes |
|---|---|
| `File` | the blob; `Content-Type: application/octet-stream`, filename **`file.bin`** |
| `FileType` | the `NJNHMGCEENL` enum, **as a decimal string** |
| `FilenameOverride` | optional |
| `References` | optional; joined with `','` (the `","` literal at `0x7D94E77`) |

A captured room-metadata save sends only `FileType` and `File`.

## `NJNHMGCEENL` — the FileType enum

| val | name | val | name |
|---|---|---|---|
| 0 | `Unknown` | 10 | `UnityAsset` |
| 1 | `SubRoomSave` | 11 | `HLSPlaylist` |
| 2 | `Holotar` | 12 | `HLSSegment` |
| 3 | `Image` | 13 | `AvatarItemUnityAssetBaked` |
| 4 | `Video` | 14 | `AvatarItemUnityAssetSource` |
| 5 | `Invention` | 15 | `SubRoomCircuitGraph` |
| **6** | **`RoomMetadata`** | 16 | `RoomAssetSave` |
| 7 | `SubRoomUnityAssetZip` | 17 | `RefereeFile` |
| 8 | `SubRoomUnityAssetBaked` | 18 | `RoomAssetPackage` |
| 9 | `SubRoomUnityAssetSource` | | |

So a payload whose protobuf body contains cloud-variable names plus room-level config
(`Room Level`, `XP`, `Room Levels`, `XP Needed`) and arrives with `FileType=6` is the
**room metadata** blob. The geometry save is a *separate* upload with `FileType=1`
(`SubRoomSave`), and circuit graphs are `15`.

## Response — REQUIRED bare 3-key object

Send helper is `MGPBDIAGCFD.HPBKMCLEANE<T>` — **response required** — generic inst **#15001** =
**`.AOEMIBONGBD`** (typedef #22687). Formatter `PFAFNBKEINJ` `.ctor 0x768A2C0`, key run 3 keys 1:1
with its 3 declared string fields:

| # | key | CLR | off |
|---|---|---|---|
| 1 | `Filename` | string | 0x10 |
| 2 | `Hash` | string | 0x18 |
| 3 | `OwnershipProof` | string | 0x20 |

```json
{ "Filename": "2026-10-03/0f8c….bin",
  "Hash": "R0SVMvrAW4n1TIF2lxaOAQZ5XXVJh7prEP6GpiLCrQo=",
  "OwnershipProof": "…" }
```

Because the helper is `HPBKMCLEANE` and not `CNDMDLNHDLI`, **the body is parsed** — `{}` or an empty
body throws `IONCMJIACFI`. A `204` is not acceptable here, unlike the fire-and-forget routes.

## ⚠️ Why a bad upload response reads as "Save your room to commit this variable"

The client's only product from this call is `Filename` + `Hash`. Those are what get attached to the
room so the blob can be fetched back on the next load. If the upload 200s but returns no usable
`Filename`/`Hash`, the metadata is uploaded and then **orphaned**: nothing references it, so the
cloud-variable list never materialises and the pending-variable prompt persists. The client reports
no error, because from its point of view the POST succeeded.

So when a variable will not commit, check the **upload response** before looking at any read route.

## Where the filename is meant to land — partially traced

`RoomDataFilename` / `RoomDataHash` is a real wire key pair (three casings, slot `0xD0CD9D8`),
distinct from the per-subroom `SubRoomDataFilename` / `SubRoomDataHash`. Both appear together on
**`.CMPBBIDGFAK`** (typedef #22905, 8 keys: `SessionId`, `RoomId`, `SubRoomId`, `UnityAssetId`,
`RoomDataFilename`, `RoomDataHash`, `SubRoomDataFilename`, `SubRoomDataHash`), formatter
`HEPHPFJFFDP` `.ctor 0x7712800`.

⚠️ **But that DTO belongs to the Rec Room Studio remote-run routes**, not the in-game save:
`EKKJPDGOAHE.FILEDFKGAGD` `0x7DC7080` (`remote-run/session`) and `EKKJPDGOAHE.AGHPEBDCGLG`
`0x7DC6D60` (`remote-run/push-to-studio`). It is the right *shape* for "here are my blob filenames",
and it is evidence the room-level and subroom-level blobs are tracked as separate
filename/hash pairs — but it is **not** the route an in-game save uses.

**Not found: the route that commits the room-metadata filename, and the route the committed
cloud-variable list is read back from.** `rooms/{id}/playerdata/me` is **not** it — that is
`{"Data": "<string>"}`, per-player room data on the Rooms service
([rooms-playerdata-me](rooms-playerdata-me-wire-shape.md)), a different concept from room-scoped cloud-variable
definitions.

To close that gap, capture the requests that follow the `FileType=6` upload in the same save — the
commit call will carry the `Filename` the upload returned, which makes it unmistakable in a log. That
is far cheaper than more static tracing: the save path fans out across several services and the
relevant call sites are inlined.
