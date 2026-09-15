# Roomkeys v1 room wire shape

> GET api/roomkeys/v1/room?roomId= (svc 28 Econ) returns a BARE ARRAY of the 10-key JODGFDKLMBO room-key DTO; no validation hook, but RoomKeysManager NREs on a null list — return [] never null.

Derived **2026-09-01** from build `20250718.01` via [recflare-2025-metadata-carve](../../../il2cpp-analysis/references/recflare-2025-metadata-carve.md).

`GET https://econ.<host>/api/roomkeys/v1/room?roomId={roomId}` — service **28 = Econ**
(`mov dword ptr [rbx+0x18], 0x1c` at `0x7D97B0A`, [recnet-service-enum](../conventions/recnet-service-enum.md)), verb **GET**
(`HttpMethod` statics `+0x08`, read at `0x7D97AAE`).

The path is **String.Format-built, not a literal**: `LHMONGGMNAI.EKELNHDEELI(long roomId)`
`0x7D97630` = `Format("{0}v1/room?roomId={1}", "api/roomkeys/", roomId)` (`0xD14EB90` +
`'{0}v1/room?roomId={1}'`). So `roomId` is baked into the path and there is **no separate
query-param adder and no other parameter** — the only other builder call is
`MGPBDIAGCFD.DIDJOECFJII(TimeSpan, bool)` `0x7D9ADB0`, which is a **response-cache TTL** (taken from
an `NNMGBLLLIAH` static), not a param.

Client entry `LHMONGGMNAI.GEHCFBLIBMJ(long roomId)` **`0x7D979F0`** →
`KPIPLFECKNC<List<JODGFDKLMBO>>` via `MGPBDIAGCFD.HPBKMCLEANE<List<JODGFDKLMBO>>` (generic inst
**16692**). Sole caller: `RecRoom.Systems.Economy.RoomKeys.RoomKeysManager.GetRoomKeysForRoom(long)`
`0xF58AB0` — **unobfuscated**, which confirms the route's purpose.

## Response — BARE JSON ARRAY

Element `.JODGFDKLMBO`, formatter `GHMIKIMLDCC` `.ctor 0x7D77420`, `____stringByteKeys` = 10 keys,
1:1 with the 10 declared fields:

| # | key | CLR | offset |
|---|---|---|---|
| 1 | `RoomKeyId` | long | 0x10 |
| 2 | `ReplicationId` | **`System.Guid`** | 0x18 |
| 3 | `RoomId` | long | 0x28 |
| 4 | `Name` | string | 0x30 |
| 5 | `Description` | string | 0x38 |
| 6 | `Price` | int | 0x40 |
| 7 | `PurchaseCurrencyId` | `Guid?` | 0x44 |
| 8 | `CreatedAt` | DateTime | 0x58 |
| 9 | `ImageName` | string | 0x60 |
| 10 | `Type` | enum `CAIBPLFEHJI` | 0x68 |

```json
[ {"RoomKeyId": 900001, "ReplicationId": "0f8c…", "RoomId": 12, "Name": "VIP Key",
   "Description": "…", "Price": 250, "PurchaseCurrencyId": null,
   "CreatedAt": "2026-01-01T00:00:00Z", "ImageName": null, "Type": 0} ]
```

⚠️ `ReplicationId` is a **Guid** here, unlike the invention DTOs where the same key name is a
**string** ([inventions-v9-save-wire-shape](inventions-v9-save-wire-shape.md)).

`CAIBPLFEHJI : int` — **`Key = 0`, `CircuitEventKey = 1`**.

## Validation

`JODGFDKLMBO.CPOBHIECLEN` is the `0xA60520` **no-op** — no per-element validation, every key
omittable.

**But the list itself must not be null.** `RoomKeysManager.GetRoomKeysForRoom` chains
`LEDLAPGJELB` `0xF59A70` → `APKOMBEMFEP(IList<JODGFDKLMBO>, bool)` `0xF56840`, which does
`test rbx,rbx; je 0xF569F5` → the **NRE throw helper** at its very first use. So `[]` is required for
"no keys"; `null` throws. A `{}` body fails earlier as
[ioncmjiacfi-malformed-response](../conventions/ioncmjiacfi-malformed-response.md) (T is a `List`).

## Table gap (extends [rooms-roles-wire-shape](rooms-roles-wire-shape.md)'s correction)

`nonobject-responses.txt` line 83 lists `api/roomkeys/v1/mine` with the **same** `List<JODGFDKLMBO>`
T, but this route is absent — its path is built with `String.Format`, and the scanner only picks up
literal routes. Two independent reasons now to treat that table as a lower bound, not a census:
non-literal paths, and facade helpers ([nonobject-response-routes](../conventions/nonobject-response-routes.md)).

Sibling routes on `LHMONGGMNAI`: `api/roomkeys/v1/mine` `HEEJPFMLAGG` `0x7D981F0`,
`api/roomkeys/v1/owns` `CELCBCEPAGE` (bool), `api/roomkeys/v1/owns/bulk` (`List<HGENLKNBPFI>`),
`api/roomkeys/v1/create`, `/awardbulk`, `/revoke`.
