# Notification types 2025

> The 49 websocket notification channel ids on build 20250718.01 with their payload DTOs — 15 are NEW since 20230414. ReputationUpdate's payload is the 9-key reputation object KBMCBHICFPL.

Enumerated **2026-08-25** on build `20250718.01`. Table:
`C:\Games\recnet-patcher\il2cpp-2025\notifications-2025.txt` (`id | payload DTO | owner`).

The registrar is the generic **`LMBGGGGNBOB.KOOMBBKFAEP<TPayload>(string id, handler)`**. Rebuild with
`il2cpp-2025/notifall.py` (collects its per-instantiation `.data` slots, recovering `T`), then
`mxref.py` on those slots, then `notifreport.py` (disassembles each owner and pairs each register
call with the string literal beside it).

⚠️ `il2cpp-tools/regall.py` — the equivalent for `20230414` — **no longer finds anything** (1 bogus
hit); its hardcoded registrar no longer matches. Don't trust a zero/near-zero result from it.

⚠️ The **owner** column can be off by one where a method registers several channels in a row; the
`id -> payload` pairing is what to rely on. `ReputationUpdate` is listed against `LINCNKPIJDN` but the
real subscriber is `HGDMAPNBDOA` (see below).

## 15 ids that are NEW since `20230414`

`DataCollectionEventDisabled`, `MakerAITimeBalanceStatusUpdate`, `MakerAIUsageBalanceStatusUpdate`,
`MeshGenStatusUpdated`, `OtherPlayerVoiceViolationIntervened`, `PlayerVoiceViolationDetected`,
`RoomBanned`, `RoomModKick`, `RoomOfferCreated`, `RoomOfferDeleted`, `RoomOfferModified`,
`RoomUnbanned`, `VoiceCallStarted`, `cards.iam`, `cards.iamdeleted`

(Tested by presence of each id literal in the `20230414` string table. The reverse direction —
ids *removed* since 2023 — was not computed, because `regall.py` is broken on that build.)

## `PlayerProgressionLevelUpdate`

Derived **2026-10-07**. Subscriber is **`LBKMGPMDOGK`** (the player-progression facade). Registration
at `0x7D5CD56`/`0x7D5CD60` inside `LBKMGPMDOGK.OCOPJMCPGIB` `0x7D5CC20`:
`KOOMBBKFAEP<inst 1144 = .DPBJAGGKHDJ>('PlayerProgressionLevelUpdate', HIAHOADEAFB)`, and the handler
signature `static void HIAHOADEAFB(.DPBJAGGKHDJ)` confirms the payload independently.

**Payload = `.DPBJAGGKHDJ`** (typedef #45685), formatter **`LFHEPCILADM` `.ctor 0x7D7F160`** (+0x470),
`____stringByteKeys` run `0x7D7F477`..`0x7D7F519` — **3 keys, all `int`**, 1:1 with the 3 declared
fields in offset order:

| # | key | CLR | off |
|---|---|---|---|
| 1 | `PlayerId` | int | 0x10 |
| 2 | `Level` | int | 0x14 |
| 3 | `XP` | int | 0x18 |

Wrapped in the standard `MDCEJFPDCEL<T>` frame — **`Msg` then `Id`, `Id` a string**
([avatar-gifts-v2](avatar-gifts-v2-wire-shape.md)):

```json
{ "Msg": { "PlayerId": 205, "Level": 42, "XP": 125000 }, "Id": "…" }
```

All three are plain non-nullable `int` — there is no `null` to send, and `DPBJAGGKHDJ.CPOBHIECLEN` is
the shared no-op `0xA60520`, so a missing key lands as `0`. **A push that omits `Level` reads as
level 0**, which is a visible regression rather than an error.

`XP` is an **absolute total**, not a delta — the three HTTP reads on the same facade return the same
DTO, so the push and the fetch have to agree:

| facade method | meaning |
|---|---|
| `LBKMGPMDOGK.OOKDPMCFBMO() -> .DPBJAGGKHDJ` | the cached local value the UI reads |
| `LBKMGPMDOGK.GNHIAGJMPLA() -> KPIPLFECKNC<.DPBJAGGKHDJ>` | fetch own progression |
| `LBKMGPMDOGK.HNBDPFINOJD(List<int>) -> KPIPLFECKNC<List<.DPBJAGGKHDJ>>` | bulk fetch by account ids |

Consumers are unobfuscated and say what breaks if the push is wrong:
`AGUI.StackedUI.PlayerLevelText` (`BCFHGPNNPCF`, `NALOEJHPOOO`),
`AGUI.StackedUI.ProgressionController.CPGCGMNGIBM`, `PlayerInfoUIControl.BECGHKONOPB`. So this is the
level number above a player's name and on their card — send it for **other** players too, not only
the local one, which is what `PlayerId` is for.

## `ReputationUpdate`

Subscriber is **`HGDMAPNBDOA`** (the reputation manager: `OBNIKGABDBN()` get-local,
`CEEPICOKNOA()`/`ENJBCALBOPP(int)` the HTTP fetches). Registration at `0x7D934CF`:
`KOOMBBKFAEP<KBMCBHICFPL>('ReputationUpdate', NJNKLPAKMKK)`, and the handler signature
`NJNKLPAKMKK(KBMCBHICFPL)` confirms the payload independently.

**Payload = the reputation object itself** — no wrapper, no list. Formatter `ENBICLAHGEO`
`.ctor 0x7D756C0`, trailing run at `0x7D75FCF`, **9 keys** (the 10th field `OFCOIOEJENL` is a plain
field, not an auto-property, so it never serializes):

| key | CLR |
|---|---|
| `AccountId` | int |
| `IsCheerful` | bool |
| `SelectedCheer` | `Nullable<CheerCategory>` |
| `CheerCredit` | int |
| `CheerGeneral` | int |
| `CheerHelpful` | int |
| `CheerCreative` | int |
| `CheerGreatHost` | int |
| `CheerSportsman` | int |

`SelectedCheer` uses the same enum as [playercheer-create-wire-shape](playercheer-create-wire-shape.md): `General 0`, `Helpful 10`,
`Sportmanship 20`, `GreatHost 30`, `Creative 40`, `RecRoomDeveloper 9000`. **Note the spelling
mismatch**: the enum member is `Sportmanship`, the wire key is `Cheer***Sportsman***`.

`HGDMAPNBDOA` also registers a *second*, non-websocket subscription in the same method —
`FHLIAIDPCMK<List<int>>.EHAFMEMPAKB(HIHACOICDMH)`, a local event bus with no channel id. Don't
mistake it for a second `ReputationUpdate` shape.
