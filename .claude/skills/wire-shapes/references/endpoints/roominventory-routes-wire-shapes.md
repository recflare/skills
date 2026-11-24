# econ/roomInventory* routes — Room Inventory Items (2026)

> Build `20260323.14`. Derived **2026-11-12** while debugging a maker room where Circuits reports a
> missing inventory item. All on **svc 28 Econ** (`econ.` host), class `RecNet.SBIATKLCDRY`. The list
> routes return **BARE ARRAYS**; the create route is **ENVELOPED**. Base literals: `econ/roomInventory`
> 0xFD8A6F0, `econ/roomInventoryItemTags` 0xFD8AD88.

## Routes

| Verb | Path | Facade (RVA) | Response |
|---|---|---|---|
| GET  | `econ/roomInventory/room/{roomId}` | `HMDVOEDYWYZ` 0x9576ae0 (gen #23351) | **BARE** `List<RoomInventoryItemDTO>` |
| POST | `econ/roomInventory/room/{roomId}` | `<CreateRoomInventoryItem>d__3` 0x957a5f0 (gen #22948) | **ENVELOPED** `RecNetResultObject<RoomInventoryItemDTO>` — the created item; **request body** set via `FZNGWUAGAIN` |
| GET  | `econ/roomInventory/room/{roomId}/player` | `PTGCCVTVLHQ` 0x9576fa0 (gen #23350) | **BARE** `List<PlayerRoomInventoryItemDTO>` |
| GET  | `econ/roomInventoryItemTags/room/{roomId}` | `<GetRoomInventoryItemTagsForRoom>d__5` 0x957f010 (gen #2978) | **BARE** `List<RoomInventoryItemTagDTO>` |
| PUT  | `econ/roomInventory/items/{roomId}/{originId}` | `<UpdateRoomInventoryItem>d__4` 0x9583940 (gen #22948) | **ENVELOPED** `RecNetResultObject<RoomInventoryItemDTO>` — the updated item; **request body** via `FZNGWUAGAIN`. `{originId}` echoes back as `Value.OriginId`. Same response type as POST create. |
| DELETE | `econ/roomInventory/items/{roomId}/{originId}` | `<DeleteRoomInventoryItem>d__5` 0x957b660 (gen #3201) | **VALUELESS ENVELOPE** `RecNet.RecNetResult` = `{Success, Error, error_id}` — NO `Value`, no request body. Serve `{"Success":true,"Error":null,"error_id":null}`. |
| POST | `econ/roomInventory/v2/award` | `HMDVOEDYWYZ` 0x9576ae0 (gen #2948) | **BARE ARRAY** `List<AddOrRemovePlayerRoomInventoryItemCountResponseDTO>` — bulk grant/deduct of player item counts; **request body** via `FZNGWUAGAIN`. Each element 2 keys: `Result` (enum `PlayerRoomInventoryOperationResult`, numeric) + `PlayerRoomInventoryItem` (the 6-key `PlayerRoomInventoryItemDTO`, updated). Serve `[]` not null/`{}`; echo a fresh `ConcurrencyCode` per item. |

**`PlayerRoomInventoryOperationResult`** (int enum #46541, numeric on wire): `Unknown=-1`, `Success=0`,
`RoomInventoryItemDoesNotExist=1`, `PlayerDoesNotExist=2`, `RoomDoesNotExist=3`,
`RequestQuantityTooLarge=4`, `PlayerHasReachedTheMinimumOwnedAmount=5` (deduct floor),
`ConcurrencyCodeMismatch=6`, `InvalidConcurrencyCode=7`.

Sibling builders on the same class, NOT fully derived: `UpdateRoomInventoryItemTags` (d__3),
`DeleteRoomInventoryItemTag` (d__4) — `{0}/room/{1}` / `{0}/{1}` shapes.

**Verb note:** the list/tags/player sends are plain response-required (`ZWUODKCINOA`, no body) ⇒ GET;
create sets a body and returns the enveloped single ⇒ POST. The `HttpMethod` static offset was not
byte-pinned (these facades load it indirectly), but the GET/POST split matches a live probe.

**Send tier:** all sends are `ZWUODKCINOA` (response-required). The list routes deserialize straight
into `List<T>`, so a `null` body RESOLVES then NREs on the consumer, and `{}` throws Malformed
Response — **serve `[]` for empty, never null or `{}`.** The POST deserializes into
`RecNetResultObject<RoomInventoryItemDTO>` (2026 envelope: `Success` bool +0x10, `Error` string +0x18,
`error_id` +0x20, `Value` +0x28), so serve `{"Value":{…},"Success":true,"Error":null,"error_id":null}`.

## DTOs (field order from the ctor/getters; wire keys are camelCase, Utf8Json accepts all 3 casings)

### RoomInventoryItemDTO — 12 keys (the room's item DEFINITIONS)
`OriginId` Guid(→string) · `RoomId` long · `Name` string · `Description` string · `ImageName` string ·
`CreatedAt` DateTime(→ISO string) · `ModifiedAt` DateTime · `Properties` string ·
`TagIds` `List<long>` · `NewTags` `List<RoomInventoryItemTagDTO>` · `IconShape` byte(→number) ·
`IconColor` int.

### PlayerRoomInventoryItemDTO — 6 keys (per-player owned counts)
`RoomId` long · `RoomInventoryItemOriginId` Guid(→string, = a RoomInventoryItemDTO.OriginId) ·
`Count` long · `ConcurrencyCode` Guid(→string) · `CreatedAt` DateTime · `ModifiedAt` DateTime.

### RoomInventoryItemTagDTO — 3 keys
`TagId` long · `Name` string · `Properties` string.

## ⚠️ Diagnostic link — "Unknown Inventory Item" in Circuits
The client holds the literal `RoomInventory: PlayerRoomInventoryItem has none existent
roomInventoryItemId {0}` (0xFC... slot, string #152199). A `PlayerRoomInventoryItemDTO` whose
`RoomInventoryItemOriginId` has **no matching `RoomInventoryItemDTO.OriginId`** in the room's
definition list is unresolvable, and `RoomInventoryItemModelBase.RefreshInternal` 0x21e57d0 then
renders the item as the literal **"Unknown Inventory Item"** (string #29003) — which surfaces in
Circuits as a missing inventory item. So if recflare serves `/room/{id}/player` rows (counts) but
`GET econ/roomInventory/room/{id}` returns `[]`/null (no definitions), every referenced item reads as
missing. The definitions endpoint `GET econ/roomInventory/room/{id}` is the one to verify first.
