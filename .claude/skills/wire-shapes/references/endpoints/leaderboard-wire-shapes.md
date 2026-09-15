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
