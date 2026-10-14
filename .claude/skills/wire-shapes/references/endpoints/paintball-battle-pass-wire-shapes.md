# `paintball-battle-pass/*` wire shapes (2026 build only)

> `GET econ.<host>/paintball-battle-pass/config` returns a **BARE `BattlePassDTO`** — no envelope.
> 13 PascalCase keys: `BattlePassId, Name, ValidRoomIds, StartTime, EndTime, Levels, EventXP,
> BoostConfig, DailyParticipationBonusLimit, MinimumParticipationTimeInSeconds, PurchasableSkus,
> PermanentBoostTokenPrice, LimitedTimeReward`.
> **Returning JSON `null` is the supported "no pass running" answer** — the client then throws
> `RecNetWebException('No Paintball Battle Pass available')` out of progress/purchase instead of
> NREing.
> ⚠️ The response is **cached client-side for 1 hour**, so config edits are not picked up promptly.
> ⚠️ **2026 build `20260323.14` only** — the whole feature is absent from `20250718.01`.

Derived **2026-10-13** from build `20260323.14` via the 2026 carve
([[recflare-2026-static-index]] → `C:\Games\recnet-patcher\il2cpp-2026\`). Everything else in this
catalog is 20250718.01 unless it says otherwise. Service **28 Econ**
(`mov r8d, 0x1c` at `0x95C7CF1`), hence `econ.<host>`.

## ⚠️ How 2026 marks an envelope — read the facade's `T`, not the friendly string

The 2025 tell ("a leading `friendlyActionDescription` on the send helper means enveloped") **does not
work on this build**: *every* 2026 send takes one. `paintball-battle-pass/config` passes
`'retrieve battle pass configuration'` and is still bare.

2026 instead expresses the envelope **in `T` itself** — the send helper never unwraps anything, so the
facade's declared return type is the literal wire type:

| 2026 type | shape | 2025 equivalent |
|---|---|---|
| `RecNet.ZBIGKCZRHCL` (interface) | `{ Success: bool, Error: string, error_id: string }` | `JFNAKFCGDAO` |
| `RecNet.IAHBKPCLGPS<T>` (interface) | adds `Value: T` | `KGOJLHJNIOD<T>` |

⚠️ **CORRECTED 2026-10-13: the wire key is `error_id`**, lowercase with an underscore, same as
2025 — an earlier revision of this note read the C# property name (`ErrorId`) and wrongly called it
PascalCase. `ErrorId` is not a string literal anywhere in the binary; `error_id` has 278 formatter
references. See [2026-send-helper-tiers](../conventions/2026-send-helper-tiers.md).

So one `py msig.py <facade>` settles bare-vs-enveloped for a whole service at once:

```
=== .BVOZXUGXNCX (8 methods)                                     # the Econ BattlePass facade
  Task<BattlePassDTO>                              KPIELWZFOCV(ct)                      <- BARE
  Task<BattlePassAccountProgressDTO>               IROFUMYRGNC(long, ct)                <- BARE
  Task<ZBIGKCZRHCL>                                DASJEVKWECM(long, BattlePassSkuType, int?, int?, ct)
  Task<ZBIGKCZRHCL>                                MFVNUJQNDZE(long, int, int?, ct)
  Task<IAHBKPCLGPS<ReportBattlePassSessionResponseDTO>> PAYYQWLLJKY(long, long, DateTime, IReadOnlyDictionary<BattlePassEvent,int>, IReadOnlyList<int>, ct)
  static Task<!!T> XNYOJFPCXJH(string a, HttpMethod b, string c, ct, Action<RGBOOBRDHEB> requestBuilderAction)
  static Task<!!T> Get(string friendlyActionDescription, HttpMethod method, string route, ct, Action<RGBOOBRDHEB> requestBuilderAction)
  static RGBOOBRDHEB NJDXKMQCUTD(HttpMethod a, string b, Action<RGBOOBRDHEB> requestBuilderAction)
```

`NJDXKMQCUTD` is the per-service request factory — **it is where the service enum is baked in**
(`XNYOJFPCXJH` has no service parameter). Sibling facades: `RecNet.Rooms.DFMBMRNABHU`,
`RecNet.Lists.PZONXXKUWMN`, `RecNet.Events.BFKPNJRKYIX`, `RecNet.DataAPI.VGVSUOPUMYE`,
`RecNet.Discovery.ZRRRWQIKCQM`.

## `GET paintball-battle-pass/config`

Route literal `0xFE0F168`, state machine `<GetBattlePassConfig>d__0$$MoveNext` **`0x95D6A70`**,
facade `BVOZXUGXNCX.KPIELWZFOCV` `0x95C7A70`, send `XNYOJFPCXJH` with generic inst
**#3122 = `RecNet.Econ.BattlePass.BattlePassDTO`**. Verb **GET** — `[HttpMethod statics + 0x08]`
= `get_method`, read at `0x95D6BB3`. No path or query parameters at all.

Formatter `Utf8Json.Formatters.RecNet.Econ.BattlePass.TMSQOMSSDZA`, `.ctor` **`0x8F3CFD0`** (+0x980);
the trailing `____stringByteKeys` run is 13 keys and matches `ftypes.py` field-for-field, so there
are **no `[DataMember]` renames and no ignored members**.

| # | key | CLR | notes |
|---|---|---|---|
| 1 | `BattlePassId` | `long` | the `{0}` in every sibling route |
| 2 | `Name` | string | |
| 3 | `ValidRoomIds` | `IReadOnlyList<long>` | |
| 4 | `StartTime` | `DateTime` | **not nullable** |
| 5 | `EndTime` | `DateTime` | **not nullable** |
| 6 | `Levels` | `IReadOnlyList<BattlePassLevelDTO>` | ordered, level 1 first |
| 7 | `EventXP` | `IReadOnlyDictionary<BattlePassEvent,int>` | **integer keys as strings** — see below |
| 8 | `BoostConfig` | `BattlePassBoostConfigDTO` | |
| 9 | `DailyParticipationBonusLimit` | `int` | |
| 10 | `MinimumParticipationTimeInSeconds` | `int` | |
| 11 | `PurchasableSkus` | `IReadOnlyList<BattlePassSkuDTO>` | |
| 12 | `PermanentBoostTokenPrice` | `int` | |
| 13 | `LimitedTimeReward` | `BattlePassLimitedTimeRewardDTO` | reference type, `null` is legal |

### Nested DTOs (each its own generated formatter, keys = property names, same order)

**`BattlePassLevelDTO`** (`FMOPNPCUAFE`): `XpRequired` (int), `RewardGiftDropIds`
(`IReadOnlyList<int>`).

**`BattlePassBoostConfigDTO`** (`EAWBKAZRMBH`), all `int`:
`TemporaryBoostDurationInMinutes`, `TemporaryBoostXpMultiplierPercentage`,
`PermanentBoostXpMultiplierPercentage`, `SocialBoostXpMultiplierPercentage`,
`MaxBoostXpMultiplierPercentage`.

**`BattlePassSkuDTO`** (`SPXHXZJEJZP`): `Type` (`BattlePassSkuType`, **numeric**), `TokenPrice`
(int), `BonusLevels` (int), `PermanentBoost` (bool).

**`BattlePassLimitedTimeRewardDTO`** (`IIEHKIQHSHK`): `CompletionDeadline` (`DateTime`),
`GiftDropIds` (`IReadOnlyList<int>`).

### The two enums are numeric

`RecNet.Econ.BattlePass.BattlePassEvent : int` — `Unknown 0`, `Paintball_KO 1`,
`Paintball_FlagCapture 2`, `Paintball_FinishGame 3`, `Paintball_WinGame 4`.

`RecNet.Econ.BattlePass.BattlePassSkuType : byte` — `Invalid 0`, `StandardPass 1`,
`AcceleratedPass 2`, `UltimatePass 3`, `Permaboost 4`.

Neither enum's member names appear in `stringliteral.json`, and the 10 generated formatters in
`Utf8Json.Formatters.RecNet.Econ.BattlePass` are all for DTOs — **no enum formatter exists**, so both
go on the wire as **numbers**, not names.

⚠️ **`EventXP` is a dictionary keyed by an enum**, so its keys are the integer values *as JSON
strings* (`"1"`, `"2"`): a JSON object key must be quoted, and with no name table there is nothing to
quote but the number. `"Paintball_KO"` will not bind.

### Example

```json
{
  "BattlePassId": 1,
  "Name": "Season 1",
  "ValidRoomIds": [112],
  "StartTime": "2026-10-01T00:00:00Z",
  "EndTime": "2026-12-01T00:00:00Z",
  "Levels": [
    { "XpRequired": 100,  "RewardGiftDropIds": [1] },
    { "XpRequired": 250,  "RewardGiftDropIds": [2, 3] }
  ],
  "EventXP": { "1": 10, "2": 25, "3": 50, "4": 100 },
  "BoostConfig": {
    "TemporaryBoostDurationInMinutes": 60,
    "TemporaryBoostXpMultiplierPercentage": 50,
    "PermanentBoostXpMultiplierPercentage": 25,
    "SocialBoostXpMultiplierPercentage": 10,
    "MaxBoostXpMultiplierPercentage": 100
  },
  "DailyParticipationBonusLimit": 5,
  "MinimumParticipationTimeInSeconds": 120,
  "PurchasableSkus": [
    { "Type": 1, "TokenPrice": 1000, "BonusLevels": 0,  "PermanentBoost": false },
    { "Type": 2, "TokenPrice": 2000, "BonusLevels": 10, "PermanentBoost": false },
    { "Type": 3, "TokenPrice": 3000, "BonusLevels": 25, "PermanentBoost": true  },
    { "Type": 4, "TokenPrice": 500,  "BonusLevels": 0,  "PermanentBoost": true  }
  ],
  "PermanentBoostTokenPrice": 500,
  "LimitedTimeReward": { "CompletionDeadline": "2026-11-01T00:00:00Z", "GiftDropIds": [9] }
}
```

### ✅ `null` is the correct "no battle pass" response

`<GetBattlePassProgress>d__6$$MoveNext` `0x95D7460` awaits the config first and branches on it at
`0x95D75EF` (`test rax, rax / je 0x95D784D`). The null path at **`0x95D784D`** builds a
**`RecNet.RecNetWebException`** with the message `'No Paintball Battle Pass available'`
(literal `0xFD3BF88`) and throws it. The same branch exists in `<PurchaseBattlePass>d__7` and
`<PurchasePermanentBoost>d__8`.

So `config` is the gate for the entire feature, and a bare `null` body turns it off cleanly. The
non-null path immediately reads `BattlePassId` (`[rax+0x10]`, the first field) and uses it as the
`{0}` of every sibling route.

⚠️ **`StartTime`/`EndTime` are non-nullable `DateTime`** — a JSON `null` on either throws inside the
Utf8Json DateTime formatter. Emit a real ISO-8601 instant. Same for every `int`/`long`/`bool` key.
Only `LimitedTimeReward`, `BoostConfig` and the four collections are reference-typed, and an empty
array is safer than `null` for the collections (the UI iterates them).

### ⚠️ 1-hour client-side response cache

The `requestBuilderAction` is `<>c::SMABEBQJMKG` **`0x95DE7D0`** — 0x64 bytes, **no literals, no
query parameters**. All it does is

```
RGBOOBRDHEB::ORUUDATDRUN(RecNet.Cache.ZQATVLASZAW /*[statics+0x18]*/, false)
```

`ORUUDATDRUN(TimeSpan, bool)` is the response-cache TTL (2025's `DIDJOECFJII`), and
`RecNet.Cache..cctor` `0x9444C20` sets the five shared TTLs:

| field | value |
|---|---|
| `SHPGMRRTKIA` +0x00 | `TimeSpan.FromMinutes(1)` |
| `USKWFSNTBQQ` +0x08 | `FromMinutes(5)` |
| `TFHWOVMEPKB` +0x10 | `FromMinutes(10)` |
| **`ZQATVLASZAW` +0x18** | **`FromHours(1)`** ← used here |
| `TSIQXQURCHS` +0x20 | `FromHours(24)` |

So a config change is invisible to a running client for **up to an hour**. Restart the client when
testing rather than assuming the server is wrong.

## The rest of the family

Verbs read from `[HttpMethod statics + N]` (`0x08` get, `0x20` post) at each state machine's
request-factory call.

| route | verb | state machine | wire `T` |
|---|---|---|---|
| `paintball-battle-pass/config` | **GET** | `<GetBattlePassConfig>d__0` `0x95D6A70` | `BattlePassDTO` (bare) |
| `paintball-battle-pass/{0}/progress/me` | **GET** | `<GetBattlePassProgress>d__1` `0x95D7150` | `BattlePassAccountProgressDTO` (bare) |
| `paintball-battle-pass/{0}/purchase` | **POST** | `<PurchaseBattlePass>d__2` `0x95DC2E0` | `ZBIGKCZRHCL` = `{Success, Error, ErrorId}` |
| `paintball-battle-pass/{0}/permanent-boost/purchase` | **POST** | `<PurchasePermanentBoost>d__3` `0x95DCC30` | `ZBIGKCZRHCL` |
| `paintball-battle-pass/{0}/report-session` | **POST** | `<ReportGameSession>d__4` `0x95DD660` | `IAHBKPCLGPS<ReportBattlePassSessionResponseDTO>` = `{Value, Success, Error, ErrorId}` |

`{0}` is `BattlePassId` from the config in every case.

**`BattlePassAccountProgressDTO`** (formatter `LDENLWOPOUQ`) — 8 keys: `BattlePassId` (long),
`AccountId` (int), `Xp` (int), `IsPurchased` (bool), `DailyParticipationBonusCount` (int),
`DailyParticipationBonusResetTime` (`DateTime`), `BoostedUntil` (**`DateTime?`**), `CompletionDate`
(**`DateTime?`**). The last two are the only nullables in the family.

**`ReportBattlePassSessionResponseDTO`** (`UNAHFHQNKQR`) — 6 keys: `Progress`
(`BattlePassAccountProgressDTO`), `EventXpEarned` (int), `ParticipationBonusXpEarned` (int),
`WasParticipationBonusCountIncremented` (bool), `BoostPercent` (int), `TeamBonusPercent` (int).

Request bodies for the three POSTs (generated formatters exist for all three, so they are JSON
bodies, not form-encoded):

**`PurchaseBattlePassRequestDTO`** (`GJAOEENPMDG`) — `Type` (`BattlePassSkuType`, numeric),
`ToAccountId` (`int?` — gifting), `RequestedPrice` (`int?`).
**`PurchaseBattlePassPermanentBoostRequestDTO`** (`YWPMUWSXXMH`) — `RequestedPrice` (int),
`ToAccountId` (`int?`).
**`ReportBattlePassSessionRequestDTO`** (`URRDAQHQNNH`) — `RoomInstanceId` (long),
`SessionStartTime` (`DateTime`), `Events` (`IReadOnlyDictionary<BattlePassEvent,int>`),
`TeammateAccountIds` (`IReadOnlyList<int>`).

### Not derived

- **How `ValidRoomIds` is enforced.** `BattlePassDTO.get_ValidRoomIds` compiles to a shared trivial
  field getter (`0xD0CCB0`, 117 call sites across unrelated types), so `callxref` cannot attribute
  it. Whether the client hides the pass UI outside those rooms is unknown — list the room you are
  testing in.
- The client-side manager `RecNet.Econ.BattlePass.EKOCDKRMDGN` re-exposes the same five calls with
  the `battlePassId` argument dropped (it supplies it from the cached config);
  `<GetBattlePassConfig>d__5` `0x95D6E30` is a bare pass-through with no extra validation.
- Other battle-pass surface not chased: `RRUI.BattlePassConfigContent` (addressables, client-side
  art), `'PaintballPassManager not initialized'`, `'Failed to load BattlePassConfigContent from
  addressables: '`, `NavigateToBattlePassStore`, `BATTLE_PASS_SKU_TYPE_KEY`.
