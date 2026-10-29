# Leaderboard wire shapes

> POST leaderboard/GetPlayerRank -> bare {PlayerId,Score,Rank}; POST leaderboard/CheckAndSetStat -> a BARE JSON NUMBER (enum Success 0/InvalidStat 1/RedisConnectionError 2). Both svc 10, both POST, and both IDENTICAL on the two client builds.

Derived **2026-08-25** from build `20250718.01`, cross-checked against `20230414`.
Facade `MOALPPFOCMH` (2025) / `POCFIEIKIDJ` (20230414). Service **10 = Leaderboard**
([recnet-service-enum](../conventions/recnet-service-enum.md)). **Both routes are POST** (`HttpMethod` statics `+0x20`) despite the
`Get`-prefixed name — no query params, JSON body.

## `POST leaderboard/GetPlayerRank`

Client `MOALPPFOCMH.FOIFKCJLFJC(int playerId, int statChannel, LBCJAIFOLFO filterType, bool sortAscending)`
`0x7D11C60`. Body `RecNet.GetRankRequestDTO` (**unobfuscated field names**), formatter
`AIFJHKJMLBJ` `.ctor 0x79A6F90`, 5 keys:

```json
{ "PlayerId": 205, "StatChannel": 3, "RoomId": 1159, "FilterType": 0, "SortAscending": false }
```

`FilterType` enum (`LBCJAIFOLFO`): **`Global 0`, `Friends 1`**.

Response `EKDLDNELLAG` — **bare object**, formatter `MPBNFLOPNEL` `.ctor 0x79BA250`, 3 keys, all int:

```json
{ "PlayerId": 205, "Score": 4200, "Rank": 17 }
```

Send is `CJBFDPLCIEJ<EKDLDNELLAG>` — the **nullable** variant, so an absent body is tolerated
(the client gets null). The method also carries an `'InvalidStat'` literal on its error path.

## `POST leaderboard/CheckAndSetStat`

Client `MOALPPFOCMH.MPEIEIEFDMM(RecNet.SetStatRequestDTO)` `0x7D12A90`. Body formatter
`OLHOIMKMBAH` `.ctor 0x79BB200`, 4 keys:

```json
{ "StatChannel": 3, "RoomId": 1159, "StatValue": 4200, "CurrentStatValue": 4100 }
```

`CurrentStatValue` is `Nullable<int>` — it is the **compare** half of a compare-and-set; `null`
means unconditional.

**Response is a BARE JSON NUMBER.** Send is `HPBKMCLEANE<IJNBNEIDPAK>` and `IJNBNEIDPAK` is an
**enum**: **`Success 0`, `InvalidStat 1`, `RedisConnectionError 2`**. So the entire body is e.g. `0`.
`{}` or `[]` raises the malformed-response throw.

⚠️ **This route is MISSING from `il2cpp-2025/nonobject-responses.txt`**
([nonobject-response-routes](../conventions/nonobject-response-routes.md)). That scan classified `T` by il2cpp type kind and only kept
list/array/**primitive** — an enum is kind `0x11` (valuetype) and fell into the "class" bucket. So
**the table under-reports scalar routes: any enum-typed `T` is a bare number and is absent from it.**
Re-run `sendscan.py` with kind `0x11` treated as scalar to close that gap.

## Cross-build: identical, no `ver` branch

On `20230414` (`POCFIEIKIDJ`, via Mono.Cecil over `il2cpp-tools/out/DummyDll/`):
`JHCFBEFNKOM(int,int,LHJOAPKMPKC,bool) -> KLCPLGECDIH` (3 × Int32) and
`DPKCFAJMPEA(SetStatRequestDTO) -> NGALGIAEELG` (enum `Success 0 / InvalidStat 1 /
RedisConnectionError 2`). `RecNet.SetStatRequestDTO` and `RecNet.GetRankRequestDTO` are
**field-for-field identical**, and `LHJOAPKMPKC` is `Global 0 / Friends 1`. Only the obfuscated type
names differ. **One response body serves both clients.**

That build additionally has an `api/Leaderboard/` prefix with three `Task<int>` methods
(`AHCDLEANPOC`, `DFEKJBALCHJ`, `AKCADDBBLEM`) and a `DOCCJKCCKGJ` enum (`Always 0 / IfGreater 1 /
IfLess 2`) — an older stat-setting API that coexists; `api/Leaderboard/` does **not** exist on 2025.

# ⚠️ 2026 (`20260323.14`): the request body CHANGED and two routes were ADDED

Derived **2026-10-22**. The "identical on the two client builds" claim above means
`20250718.01` vs `20230414` — **2026 was never checked until now, and it is not identical.**

Facade is now **`RecNet.Leaderboards`** (35 methods, unobfuscated class name; the route-bearing
members and the nested enums are unobfuscated too). Still **svc 10 Leaderboard** (`mov r8d, 0xA`,
e.g. `0x94D8CF0`) and still **all POST** (`[statics+0x20]`), all with a **JSON body**
(`RGBOOBRDHEB.FZNGWUAGAIN<T>`, `0x3E50380`).

| route | facade | holder RVA | request | response |
|---|---|---|---|---|
| `leaderboard/GetPlayerRank` | `ZVMLDUGKOIZ(int, int, FilterType, bool)` | `0x94D8B80` | `GetRankRequestDTO` **(6 keys — CHANGED)** | `LeaderboardEntry` (unchanged) |
| `leaderboard/CheckAndSetStat` | `ZAXSPZTZQLX(SetStatRequestDTO)` | `0x94D81D0` | `SetStatRequestDTO` (4 keys, unchanged) | bare number, `.RequestResult` (unchanged) |
| `leaderboard/GetRanks` | — (closure `LIHWWNNFXBM.HHFRFPDAYUY`) | `0x94D41B0` | `GetRanksRequestDTO` **(8 keys — NEW ROUTE)** | `SingleLeaderboard` |
| `leaderboard/GetNearbyScores` | — (closure `TNUQJOJQLAU.WFLMGUYLZGC`) | `0x94E62A0` | `GetNearbyScoresRequestDTO` **(7 keys — NEW ROUTE)** | `SingleLeaderboard` |

Route literals: `GetPlayerRank` `0xFC38698` · `CheckAndSetStat` `0xFC37FF8` · `GetRanks` `0xFC389E8`
· `GetNearbyScores` `0xFC38348`.

## 1. `GetRankRequestDTO` — 5 keys → **6**, with two RENAMES

Formatter **`Utf8Json.Formatters.RecNet.YASANOVXAMC`** `.ctor` **`0x9380630`**,
`____stringByteKeys` `0x9380A0A`…`0x9380AD6`:

| 2025 key | 2026 key | 2026 CLR | off | |
|---|---|---|---|---|
| `PlayerId` | `PlayerId` | int | 0x10 | same |
| `RoomId` | **`PrimaryKey`** | **`long?`** | 0x18 | **renamed + now nullable** |
| `StatChannel` | **`SecondaryKey`** | **`int?`** | 0x28 | **renamed + now nullable** |
| `FilterType` | `FilterType` | `.FilterType` | 0x30 | same |
| `SortAscending` | `SortAscending` | bool | 0x34 | same |
| — | **`LeaderboardType`** | `.LeaderboardType` | 0x38 | **NEW** |

⚠️ **The renames are real wire keys, not `[DataMember]` aliases.** `PrimaryKey` (`0xFC69E18`) is
referenced by this formatter and by the two new ones; `RoomId`/`StatChannel` are **not** keys on this
DTO any more. A 2025-shaped body deserializes with `PrimaryKey`/`SecondaryKey` **null** and
`LeaderboardType` **0**.

`.LeaderboardType` (typedef #22353, nested on `RecNet.Leaderboards`): **`Room = 0`, `Event = 1`** —
numeric. `.FilterType` (#22352) is unchanged: `Global = 0`, `Friends = 1`.
⚠️ Do not confuse `.FilterType` with `Hjg.Pngcs.FilterType` (#59452), a PNG enum.

```json
{"PlayerId":205,"PrimaryKey":1159,"SecondaryKey":3,"FilterType":0,
 "SortAscending":false,"LeaderboardType":0}
```

## 2. `GetPlayerRank` response: unchanged — but `null` is no longer tolerated

`RecNet.LeaderboardEntry` (#22346) is still **3 int keys**, formatter
**`VZRQYVMBRER`** `.ctor` **`0x94CED50`**, keys `0x94CEF2C`…`0x94CEF7C`:

```json
{"PlayerId":205,"Score":4200,"Rank":17}
```

⚠️ **Behaviour change.** 2025 sent this through the *nullable* helper `CJBFDPLCIEJ`, so an absent
body was tolerated and the client got `null`. 2026 sends it through
**`RGBOOBRDHEB.LIRIDCJIGGA<LeaderboardEntry>(bool a, ct)` `0x3E50970` with `a = false`**
(`xor edx, edx` at `0x94D8DDE`), which **throws
`RecNetMalformedResponseException: Response was empty`** on a null or empty body
([2026-send-helper-tiers](../conventions/2026-send-helper-tiers.md)). Both new routes use the same
helper with `false` (`0x94D42C6`, `0x94E63B6`).

➡️ **Always return a body on all three Get* routes.** For "no rank", return
`{"PlayerId":<id>,"Score":0,"Rank":0}`, not `null` and not an empty body.

## 3. `CheckAndSetStat` — fully unchanged

Request `RecNet.SetStatRequestDTO`, formatter **`RISPGSVHPAO`** `.ctor` **`0x8E7DF50`**, keys
`0x8E7E216`…`0x8E7E292` — **the same 4**: `StatChannel`, `RoomId`, `StatValue`,
`CurrentStatValue` (`int?`, the compare half).

Response is still a **bare JSON number**: `.RequestResult` (typedef #22351, nested) with the
**same three values** `Success = 0`, `InvalidStat = 1`, `RedisConnectionError = 2`. Send is
`ZWUODKCINOA<RequestResult>` `0x3E528A0` (`xor edx, edx` = default ct).

⚠️ Note this route keeps `RoomId`/`StatChannel` while `GetPlayerRank` renamed them — **the two
bodies no longer share a vocabulary.** Do not refactor them onto one model.

## 4. NEW: `POST leaderboard/GetRanks` → `SingleLeaderboard`

Request **`RecNet.GetRanksRequestDTO`** (#22349) **inherits `GetRankRequestDTO`** — its own fields
start at **`0x40`**, and the formatter **`ZNJVTWZXOHH`** `.ctor` **`0x93824F0`** emits **8** keys,
derived-before-base (`0x93829DE`…`0x9382AFA`):

```json
{"RankStart":1,"RankEnd":50,
 "PlayerId":205,"PrimaryKey":1159,"SecondaryKey":3,"FilterType":0,
 "SortAscending":false,"LeaderboardType":0}
```

## 5. NEW: `POST leaderboard/GetNearbyScores` → `SingleLeaderboard`

Request **`RecNet.GetNearbyScoresRequestDTO`** (#22348), same inheritance (own field at `0x40`),
formatter **`EUGTZQKGMHC`** `.ctor` **`0x9243480`**, **7** keys (`0x92438E4`…`0x92439D8`):

```json
{"WindowSize":5,
 "PlayerId":205,"PrimaryKey":1159,"SecondaryKey":3,"FilterType":0,
 "SortAscending":false,"LeaderboardType":0}
```

## `SingleLeaderboard` — ONE key wrapping the array

**Not a bare array.** `RecNet.SingleLeaderboard` (#22350), formatter **`CZUCCJZHSWH`** `.ctor`
**`0x8E87850`**, `____stringByteKeys` = **`Rows`** only (`0x8E87949`):

```json
{"Rows":[{"PlayerId":205,"Score":4200,"Rank":17},
         {"PlayerId":206,"Score":4100,"Rank":18}]}
```

⚠️ Returning a bare `[...]` raises `IONCMJIACFI` "Malformed Response"; and because these use
`LIRIDCJIGGA(false)`, `null` raises `Response was empty`. `{"Rows":[]}` is the empty answer.
⚠️ **Not verified**: whether a null `Rows` is dereferenced unguarded by the consumer — send `[]`.

## Also on the 2026 facade, not yet located to a route

`RecNet.Leaderboards` exposes more than these four routes. **Not derived** — no route literal was
matched to them, so they may ride one of the four above or a path assembled elsewhere:

- `SHTTXYOJNOB(int,int)`, `NIVKYVBQDCE(int,int)`, **`UIXQNJWQZKM(int, int, .SetMode)`** → `MPVTAJGPRUT<int>`.
  ⚠️ `.SetMode` (#22357) is **`Always 0 / IfGreater 1 / IfLess 2`** — the enum this note previously
  recorded as existing *only* on `20230414` under the retired `api/Leaderboard/` prefix. It is
  **back on 2026**, but `api/Leaderboard/` is still absent from the literal table.
- `ZOBYJDNNTNN(int, long, int, int?)` → `MPVTAJGPRUT<.RequestResult>` — a positional
  `CheckAndSetStat` variant.
- `YCSKJTDPPTM(int, long, int, .FilterType, bool, bool)` → `LeaderboardEntry` — a 6-arg
  `GetPlayerRank` variant.
- `CPTDHVLUWPO` / `FGHQWSELEUB` / `XAOBPWNDLVI` → `SingleLeaderboard` — three more entry points into
  `GetRanks`/`GetNearbyScores`.
- `XKWZTPOIWBV(int,int)` → `MPVTAJGPRUT<.IZFMEPITZST>`; `LYFJKRUHAQT(long, bool)` → `int?`.
- `BDEGXQWPFHC(long, bool, ct)` → `Task<RecNet.SquadAverageScoreDTO>` = **`{SquadId:int, AverageScore:int}`**.
- `DEFPAQKJSII(int, int, Guid, Guid, List<int>)` → `Task<RecNet.RecNetResult>`.
- `WXDVEMTGZAP(RecNet.LeaderboardStatChangedDTO)` is a **push handler**, not a route:
  `{PlayerId:int, StatValue:int, PrimaryKey:long, SecondaryKey:int, LeaderboardType}` — note it uses
  the same `PrimaryKey`/`SecondaryKey`/`LeaderboardType` vocabulary as the new request DTOs.
