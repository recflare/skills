# Playerevents v1 room wire shape

> GET api/playerevents/v1/room/{roomId} (svc 2 API) returns a BARE ARRAY of the 17-key NEMBNIGCMFK — identical to GET api/playerevents/v1, filtered to a room; includes the two broadcast-permission enum values (None 0 / RoomOwners 256 / All int.MaxValue).

Derived **2026-08-24** from build `20250718.01` via [recflare-2025-metadata-carve](../../../il2cpp-analysis/references/recflare-2025-metadata-carve.md).
Companion to [playerevents-v2-wire-shape](playerevents-v2-wire-shape.md), which has the v2 create/edit family.

`GET https://api.<host>/api/playerevents/v1/room/{roomId}` — service **2 = API**
([recnet-service-enum](../conventions/recnet-service-enum.md)), verb **GET** (`HttpMethod` statics `+0x08`), **no query params, no body**.
Client entry `BPHIJNEOCMK.NDIDOEGFGDJ(long roomId, CancellationToken)` `0x7E44780` →
`Task<List<NEMBNIGCMFK>>`; literal `'api/playerevents/v1/room/{0}'` `0xD140218`.

**Response is a BARE JSON ARRAY — no envelope.** It uses `LMKONLJOAEP<List<NEMBNIGCMFK>>`
(generic inst 2737) — the **exact same helper and T** as `GET api/playerevents/v1`
(`BPHIJNEOCMK.KFGMFCLHDFN()` `0x7E43FC0`), so the two routes are shape-identical and this one is
just filtered to a room. Serve `[]` when empty.

Element `NEMBNIGCMFK` — formatter `CLAPAFCIEHB` `.ctor 0x7709A30`, trailing `____stringByteKeys` run
at `0x770AA0E..`, verified 1:1 against the 17 declared fields:

| # | key | CLR |
|---|---|---|
| 1 | `PlayerEventId` | long |
| 2 | `CreatorPlayerId` | int |
| 3 | `RoomId` | long |
| 4 | `SubRoomId` | long? |
| 5 | `ClubId` | long? |
| 6 | `Name` | string |
| 7 | `Description` | string |
| 8 | `ImageName` | string |
| 9 | `StartTime` | DateTime (ISO-8601) |
| 10 | `EndTime` | DateTime |
| 11 | `AttendeeCount` | int |
| 12 | `Accessibility` | enum `KOMDDCCKBID` |
| 13 | `IsMultiInstance` | bool |
| 14 | `SupportMultiInstanceRoomChat` | bool |
| 15 | `DefaultBroadcastPermissions` | enum `GAHAEEIJGGE` |
| 16 | `CanRequestBroadcastPermissions` | enum `GAHAEEIJGGE` |
| 17 | `BroadcastingRoomInstanceId` | long? |

**Enum values (new — not in [playerevents-v2-wire-shape](playerevents-v2-wire-shape.md)), numeric on the wire:**
- `KOMDDCCKBID`: `Private 0`, `Public 1`, `Unlisted 2`.
- `GAHAEEIJGGE`: `None 0`, **`RoomOwners 256`**, **`All 2147483647`**. Not 0/1/2 — guessing these
  wrong is the obvious way to break broadcast permissions.

**No post-deserialize validation** — `NEMBNIGCMFK.CPOBHIECLEN` is the `0xA60520` no-op. (The v2
derived `EAAICKJKHED` *does* have a real hook for `Tags`; this base type does not.)

## Rule: the `friendlyActionDescription` parameter tells you if a route is enveloped

Every RecNet client facade exposes several send helpers over `MGPBDIAGCFD`, and on both facades
examined the split is exact:

| helper signature | state machine awaits | wire |
|---|---|---|
| `(HttpMethod, string route, CT, Action<MGPBDIAGCFD>)` | `T` | **bare** |
| `(string friendlyActionDescription, HttpMethod, string route, CT, Action<MGPBDIAGCFD>)` | `KGOJLHJNIOD<T>` / `GJAFHDAFBNE<T>` / `JFNAKFCGDAO` | **enveloped** |

On `BPHIJNEOCMK`: `NDBMFFLDBBK<T>` / `LMKONLJOAEP<T>` (SMs `JBBBPLHOFDI\`1`, `JMEHLCFICCI\`1`,
8 fields, `<>u__1 = TaskAwaiter<!T>`) are **bare**; `PJPLCMBOAFB<T>` (SM `NIJHJMMNMIC\`1`, 9 fields,
`<>u__1 = TaskAwaiter<KGOJLHJNIOD<!T>>`) is **enveloped**. On `OALMDGJKBJH` *every* helper carries
the description, which is why all of it is enveloped ([rooms-isbanned-wire-shape](rooms-isbanned-wire-shape.md)).

**How to apply:** to classify a new route fast, dump the facade with `msig.py`, find which helper the
entry method calls, and check for the leading description string — no disassembly of shared generic
code needed.
