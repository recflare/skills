# Subroom saves list wire shape

> Wire shape of GET rooms/{id}/subrooms/{id}/saves/no_unity_assets on the Rooms service for recflare-2025 — a bare paged {Results, TotalResults} of 15-key save records.

Derived **2026-08-17** from `C:\Games\recflare-2025` (build `20250718.01`) via
[recflare-2025-metadata-carve](../../../il2cpp-analysis/references/recflare-2025-metadata-carve.md). Companion to [subroom-data-save-endpoint](subroom-data-save-endpoint.md), which is the *write*
side; this is the listing.

`GET https://rooms.<host>/rooms/{roomId}/subrooms/{subRoomId}/saves/no_unity_assets` — **GET**
(`HttpMethod` statics `+0x08`). Client entry
`OALMDGJKBJH.NAEEPIPAACO(long roomId, long subRoomId, byte? unityAssetTarget, int? unityAssetVersion,
int skip, int take, bool isDescendingCreatedAt, CancellationToken)` (`0x7DFDE60`), state machine
`DBCJPDNBJIJ$$MoveNext` (`0x7DE8B30`). All five query params are added by the closure
`PLAHGGGJCLC.MHDPGCFPIGN` (`0x7E01F50`) via `MGPBDIAGCFD.ELHKHFJEHLM`; `isDescendingCreatedAt` is a
boxed bool, so it goes on the wire as .NET `True`/`False`, not `true`/`false`.

**Response is a bare paged wrapper, no `{success,error,value}` envelope** —
`LKDBFCMHAED : FGLBCGIODIE<GCLKKDPHAON>`. Formatter `PMACIGFKMLB` ctor `0x77B3AA0`, keys
`Results` (list) and `TotalResults` (long, the unpaged total).

Each result is `GCLKKDPHAON` (formatter `NINGOINGMNB` ctor `0x77332C0`), 15 keys in declaration
order — `SubRoomDataSaveId` long 0x10, `SubRoomId` long 0x18, `UnityAssetId` Guid? 0x20,
`ReferencedUnityAssetIds` IReadOnlyCollection\<Guid\> 0x38, `DataBlob` string 0x40,
`DataBlobHash` string 0x48, `PersistenceVersion` int 0x50, `OMVersion` int 0x54,
`SavedByAccountId` int? 0x58, `SavedOnPlatform` enum? 0x60, `SavedOnDeviceClass` enum? 0x68,
`Description` string 0x70, `ModerationState` byte enum 0x78, `CreatedAt` DateTime 0x80,
`UgcSubVersion` int? 0x88. Two more declared properties are computed (no backing field, not on the
wire), which is why 17 properties give 15 keys.

Enums: `SavedOnPlatform` `NLJFAOJNHDJ` — All -1, Steam 0, Oculus 1, PlayStation 2, Xbox 3, RecNet 4,
IOS 5, GooglePlay 6, Standalone 7, Pico 8, Switch 9. `SavedOnDeviceClass` `KPOJCHHIMDA` — Unknown 0,
VR 1, Screen 2, Mobile 3, VRLow 4, Quest2 5. `ModerationState` `CCJNDAADAJO : byte` — None 0,
Pending 1, Approved 2, Denied 3, ModeratorPending 4, ModeratorApproved 5, ModeratorDenied 6.

No required-field throw: `GCLKKDPHAON.CPOBHIECLEN` is the `0xA60520` no-op and
`LKDBFCMHAED.CPOBHIECLEN` (`0x7E18C70`) tail-jumps into the list-validate helper, which returns
false on a null list.

**Why:** `no_unity_assets` refers to the *element type*, not to omitted fields — there is a subclass
`OOIBOPOFICP : GCLKKDPHAON` that a different endpoint returns. This one
returns the plain base, so emitting those extra keys is pointless (Utf8Json drops unknown keys).

**That endpoint is now derived: `GET .../saves/{saveId}`** — see
[subroom-save-by-id](subroom-save-by-id-wire-shape.md). Correction to the line above: `OOIBOPOFICP` adds **four**
keys, not two — `UnitySubAssets`, `ReferencedUnityAssets`, `UnityAsset`, `UnityAssetHash` — and
because Utf8Json emits derived members first, they lead the run, so that route's shape is a 19-key
object whose **first four** keys are the new ones, not a 15-key object with four appended.

**How to apply:** `FGLBCGIODIE<T>` is the generic paged base — any endpoint returning it has the same
`{Results, TotalResults}` outer shape, so only the element formatter needs re-deriving.
