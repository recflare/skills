# Matchmaking `GET player?id=` — presence lookup

> `GET match.<host>/player?id=<playerId>` (svc 4 Matchmaking) returns a **BARE ARRAY** of the
> 10-key `RecNet.PlayerPresence`, even for one id. The client takes `FirstOrDefault()`: one element
> updates that player's cached presence, an **empty array `[]` removes it** from the cache, and
> `{}` fails with `Malformed Response: '{}'`.

Derived **2026-11-09** on `C:\Games\recflare-2026`, build **20260323.14**. RVAs are 2026-specific.

## Request

Literal `'player'` `0xFC20AC0`. Two callers on `RecNet.Matchmaking` share it:

| caller | RVA | verb | id param |
|---|---|---|---|
| `UUFDWYIGRPW` (one player) | `0x94FF050` | GET (statics `+0x08` at `0x94FF1F6`), `r8d=4` | one `id` in the query string |
| `QQTEJRKKSLE` (several) | `0x94FC310` | POST (statics `+0x20` at `0x94FC610`), `r8d=4` | `id` repeated in a form body (`id=1&id=2`) |

Both log `'Failed to refresh player presence'` on error. Both read into methodSpec inst #26234 =
`List<RecNet.PlayerPresence>` via the response-required helper `ZWUODKCINOA`. So the single-id GET
and the bulk POST return the **same array shape**; a server wiring only one verb 405s the other.

## Response element — `RecNet.PlayerPresence`

Formatter `Utf8Json.Formatters.RecNet.YYUOWSHQAKK` (`Deserialize` confirmed via `msig`), key run
`0x8E0ECC0`. 10 keys, declaration order, with three `[DataMember]` renames flagged:

| key (wire) | C# field | type | notes |
|---|---|---|---|
| `PlayerId` | PlayerId | int | |
| `StatusVisibility` | StatusVisibility | enum | Public 0, FriendsOnly 1, FavoriteFriendsOnly 2, Offline 3 |
| `Platform` | **PlatformType** | enum | rename. All -1, Steam 0, Oculus 1, PlayStation 2, Xbox 3, RecNet 4, IOS 5, GooglePlay 6, Standalone 7, Pico 8, Switch 9 |
| `DeviceClass` | DeviceClass | enum | Unknown 0, VR 1, Screen 2, Mobile 3, VRLow 4, Quest2 5 |
| `VrMovementMode` | **VRMovementMode** | enum | rename. TELEPORT 0, WALK 1 |
| `RoomInstance` | RoomInstance | DTO | the Matchmaking `RoomInstance` (same as matchmake/v2/room, heartbeat); `null` if not in a room |
| `CorrelationId` | CorrelationId | Guid? | |
| `IsOnline` | IsOnline | bool | |
| `AppVersion` | AppVersion | string | |
| `ClientJoinData` | **ClientJoinDataJson** | string | rename; embedded JSON text |

Three fields have **no key** (filled by the post-deserialize hook, do not emit):
`ClientJoinData` (the parsed `ClientJoinDataDTO`, distinct from the `ClientJoinDataJson` string),
`ParsedAppVersion`, `AppearsOnlineToMe`.

## What the client does with it

Single-id path: continuation `XGWZLUNCZMP$$OZPOVSJVWRU` `0x9510680` →
`Enumerable.FirstOrDefault(list)` (inst #18262 = one `PlayerPresence`):

- element present → `Matchmaking$$KTWVWDBDEBA` `0x94F9750` upserts it into the presence cache;
- `FirstOrDefault` of `[]` is null → falls to `Dictionary.Remove` (`0x951073A`) + `XQEMDIRMNOC`, so
  **`[]` evicts the player from the cache** — the correct "offline / not found" answer.

So for `?id=2`, return `[ { …one PlayerPresence… } ]` with `RoomInstance` either the full DTO or
`null`. Never `{}` (that is `Malformed Response`). The 10 keys match 2025's presence record; only the
three rename spellings above and the obfuscated type names changed on 2026.
