# Playerreporting moderationblockdetails wire shape

> POST api/PlayerReporting/v1/moderationBlockDetails (svc 2 API) sends deviceToken as a form field and returns a BARE 16-key moderation-block DTO (EGCLKLJADBL); no validation, no throws — the same DTO the RoomModKick/ModerationUnkick notifications carry.

Derived **2026-09-03** from build `20250718.01` via [recflare-2025-metadata-carve](../../../il2cpp-analysis/references/recflare-2025-metadata-carve.md).

`POST https://api.<host>/api/PlayerReporting/v1/moderationBlockDetails` — service **2 = API**
(`mov dword ptr [rdi+0x18], 2` at `0x7D9FA4C`), verb **POST** (`HttpMethod` statics `+0x20`, read at
`0x7D9FA0B`). Literal `0xD11F928`.

Client entry `NDIGFGBCINJ.FDCFKAFLFLI(string deviceToken)` **`0x7D9F8F0`** →
`KPIPLFECKNC<EGCLKLJADBL>`.

**Request: one `deviceToken` field, added with `ELHKHFJEHLM` and guarded by
`String.IsNullOrEmpty`** — and because the verb is POST that lands in an
**`application/x-www-form-urlencoded` body**, not the query string
([elhkhfjehlm-verb-dependent-params](../conventions/elhkhfjehlm-verb-dependent-params.md)). No JSON body (no `ELKIBCPINAP`).

## Response — BARE object, no envelope

Send generic `HPBKMCLEANE<.EGCLKLJADBL>` (inst **1155**). Formatter `LAMFGNJKEBF` `.ctor 0x7C1A800`,
**16 wire keys**; the type declares 17 fields — the `float` at `+0x78` is `[IgnoreDataMember]`.

| # | key | CLR | offset |
|---|---|---|---|
| 1 | `ReportCategory` | enum `DGJGKHDFDCN` | 0x10 |
| 2 | `Duration` | int | 0x14 |
| 3 | `GameSessionId` | long | 0x18 |
| 4 | `IsHostKick` | bool | 0x20 |
| 5 | `Message` | string | 0x28 |
| 6 | `PlayerIdReporter` | `int?` | 0x30 |
| 7 | `IsBan` | bool | 0x38 |
| 8 | `IsVoiceModAutoban` | bool | 0x39 |
| 9 | `IsDeviceBan` | bool | 0x3a |
| 10 | `IsWarning` | bool | 0x3b |
| 11 | `VoteKickReason` | string | 0x40 |
| 12 | `TimeoutStartedAt` | `DateTime?` | 0x48 |
| 13 | `AssociatedAccountUsername` | string | 0x58 |
| 14 | `ShowCreatorCodeOfConduct` | bool | 0x60 |
| 15 | `TopMessageOverride` | string | 0x68 |
| 16 | `BottomMessageOverride` | string | 0x70 |
| — | *(skipped)* | float | 0x78 |

`Duration` is a plain `int` (not nullable) and pairs with `TimeoutStartedAt`.

## `DGJGKHDFDCN` (ReportCategory)

`Moderator -1`, `Unknown 0`, `DEPRECATED_MicrophoneAbuse 1`, `Harassment 2`, `Cheating 3`,
`DEPRECATED_ImmatureBehavior 4`, `AFK 5`, `Misc 6`, `Underage 7`, `VoteKick 10`,
`MisleadingPurchases 11`, `CoC_Underage 100`, `CoC_Sexual 101`, `CoC_Discrimination 102`,
`CoC_Trolling 103`, `CoC_NameOrProfile 104`, `InappropriateClothing 200`,
`IssuingInaccurateReports 1000`, `RoomInventoryItems 1100`, `InappropriateRooms 1101`.

## No validation, no throws

`EGCLKLJADBL.CPOBHIECLEN` `0x7D8FFF0` **normalises, it does not validate**: it stamps
`ABJOPACFCAG.HGPIGKDMGNO()` (realtime-since-startup) into the ignored `+0x78` float, and if
`PlayerIdReporter` has no value it zeroes the 8 bytes at `+0x30`. Same pattern as
[api-images-v6-wire-shape](api-images-v6-wire-shape.md). No throw helper anywhere in its range.

Consumer `<>c.HLABHJLNNIK(EGCLKLJADBL)` `0x7DA5700` just tail-jumps to the static setter
`NDIGFGBCINJ.NDLHICADFMD` `0x7DA23E0` — a plain cache store with **no null check**, read back via
`NDIGFGBCINJ.ENBHADKHJOG()`. So `null` is tolerated at this step; any risk is in downstream readers,
which were not surveyed.

## Cross-reference

`.EGCLKLJADBL` is the **same DTO** the `RoomModKick` and `ModerationUnkick` websocket notifications
carry ([notification-types-2025](notification-types-2025.md), both dispatched by `NDIGFGBCINJ.OCOPJMCPGIB`) — so a push and
this poll deliver identical content, and a server can share one serialiser.

Sibling routes on `NDIGFGBCINJ`: `api/PlayerReporting/v1/deviceId`, `/hile`, `/instantKick`,
`/modKick`, `/referee`, `/roomModKick`, `/voteToKickReasons`, `api/PlayerReporting/v3/create`,
`api/PlayerReporting/v3/voteToKick`.
