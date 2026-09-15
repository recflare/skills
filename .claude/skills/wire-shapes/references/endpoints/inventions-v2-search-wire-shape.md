# Inventions v2 search wire shape

> GET api/inventions/v2/search?value=&ugcVersion=&skip=&take= (svc 2 API) returns a BARE ARRAY of the 28-key Invention DTO (KKBFDGFLMMA); search text key is `value`, not searchQuery; Obscured* fields are plain numbers/bools on the wire.

Derived **2026-08-27** from build `20250718.01` via [recflare-2025-metadata-carve](../../../il2cpp-analysis/references/recflare-2025-metadata-carve.md).

`GET api/inventions/v2/search` — **GET** (`HttpMethod` statics `+0x08`), service **2 = API**.
Client entry `GLAKFFIIDPF.LHIMANBJGHA(string searchQuery, int? ugcVersion, int skip, int take)`
`0x7CED9F0`. Send `HPBKMCLEANE<List<KKBFDGFLMMA>>` — **required response, BARE ARRAY**
(`{}` or empty body throws `IONCMJIACFI`; serve `[]`). Belongs on [nonobject-response-routes](../conventions/nonobject-response-routes.md).

**Query params: `value`, `ugcVersion`, `skip`, `take`.** ⚠️ The search text key is **`value`**, not
`searchQuery` (unlike `customAvatarItems/v1/search`, [customavataritems-routes-wire-shapes](customavataritems-routes-wire-shapes.md)).
Not paged — no `{Results, TotalResults}`; the client infers "end" from a short array.

## `KKBFDGFLMMA` = Invention, 28 keys (formatter `FFIJPCECJME` `.ctor 0x79B06C0`)

28 declared fields -> 28 keys, 1:1 in declaration order.

| key | CLR | wire |
|---|---|---|
| `InventionId` | ObscuredLong | plain number |
| `ReplicationId` | string | |
| `CreatorPlayerId` | ObscuredInt | plain number |
| `Name`, `Description`, `LongDescription`, `ImageName` | string | |
| `UgcVersion` | **byte** | |
| `CurrentVersionNumber`, `LatestVersionNumber` | int | |
| `Accessibility` | `KLKIFENPGNG` | `Private 0`, `Public 1`, `Unlisted 2` |
| `ForceCannotPublish` | bool | |
| `ModifiedAt`, `CreatedAt` | DateTime | note ModifiedAt comes FIRST |
| `FirstPublishedAt` | DateTime? | |
| `CreationRoomId` | long? | |
| `NumPlayersHaveUsedInRoom`, `NumDownloads`, `CheerCount` | int | |
| `CreatorPermission`, `GeneralPermission` | `KGCKBAIOBNL` | see below |
| `IsAGInvention`, `IsCertifiedInvention`, `IsRecRoomApproved`, `AllowTrial` | ObscuredBool | plain true/false |
| `Price` | int? | |
| `HideFromPlayer` | bool | |
| `DisplayMetadataJson` | string | nested JSON as an escaped STRING |

`KGCKBAIOBNL` permission enum: `Unassigned 0`, `LimitedOneUseOnly 10`, `DisallowKeyLock 15`,
`UseOnly 20`, `EditAndSave 40`, `Publish 60`, `Charge 80`, `Unlimited 100`.

**No validation:** `KKBFDGFLMMA.CPOBHIECLEN` `0x7D0B550` only re-encrypts the Obscured* fields
(`ObscuredLong/Int/Bool.ADACFEEMPHN`) — no literals, no throws. That re-encryption is also the
independent proof the Obscured types arrive as **plain JSON numbers/bools**, matching
[rooms-contributedby-wire-shape](rooms-contributedby-wire-shape.md).

Sibling routes on the same facade `GLAKFFIIDPF`: `/v2/mine`, `/v2/batch`, `/v2/metadata`,
`/v2/accessibility`, `/v2/cheer`, `/v2/delete`, `/v2/unpublish`, `/v2/update`, `/v2/updateprice`.
