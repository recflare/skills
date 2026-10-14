# `GET api/timeLimitedEvents/{id}` wire shape (2026 build only)

> `GET econ.<host>/api/timeLimitedEvents/{guid}` returns a **BARE 7-key `TimeLimitedEventDTO`** —
> no envelope, no array.
> ⚠️ **`Config` is NOT a wire key.** The event's whole configuration arrives as a **JSON string** in
> **`ConfigJson`**, which the client parses into the `Config` object itself. Send a string, not an
> object.
> ⚠️ **2026 build `20260323.14` only** — `api/timeLimitedEvents` does not exist in `20250718.01`.

Derived **2026-10-13** from build `20260323.14` via the 2026 carve
([[recflare-2026-static-index]] → `C:\Games\recnet-patcher\il2cpp-2026\`). Everything else in this
catalog is 20250718.01 unless it says otherwise.

Service **28 Econ** (`mov r8d, 0x1c` at `0x959E45D`), verb **GET** (`[HttpMethod statics + 0x08]`,
read at `0x959E414`), hence `econ.<host>`. Path is
`String.Format("{0}/{1}", "api/timeLimitedEvents", id)` — base literal `0xFC72EC8`, template
`{0}/{1}`. The id is a **path segment**, no query params.

**Both an `int64` id and a `Guid` hit the same route and the same shape** — the facade declares two
overloads that compile to two near-identical methods:

```
RecNet.IFTDOIEBBWL (12 methods)
  Task<List<TimeLimitedEventDTO>>          LSCHCBIHUGO(ct)                 # GET api/timeLimitedEvents  (all)
  Task<TimeLimitedEventDTO>                JZQTLNGETOL(long, ct)           # 0x959E2F0
  Task<TimeLimitedEventDTO>                JZQTLNGETOL(Guid, ct)           # 0x959E510   <- the GUID form
  Task<TimeLimitedEventTeamConfigDTO>      QIQFIDMVQDO(long, ct)
  Task<List<int>>                          QUUILVGKFCU(Guid, ct)
  Task<RecNetResult>                       UBYGKOAHZNY(Guid, int, ct)
  Task<RecNetResult>                       NITRPVAMPEE(Guid, int, ct)
  Task<RecNetResult>                       XHDMOCZBMFA(Guid, int, ct)
```

A `Guid` in the path means the server is being asked by **`ReplicationId`**, which is key #2 of the
DTO — so `.../cbe9582c-6314-4ba3-ad0e-57d220b79aff` is a lookup by `ReplicationId`, while the `long`
overload looks up by `TimeLimitedEventId`. Both must return the same object.

## Response — bare, 7 keys

Formatter `Utf8Json.Formatters.RecNet.Interfaces.TimeLimitedEvents.QFNVXEGBHHM`, `.ctor`
**`0x8F39FF0`** (+0x550). Keys = property names, declaration order, no renames:

| # | key | CLR | notes |
|---|---|---|---|
| 1 | `TimeLimitedEventId` | `long` | |
| 2 | `ReplicationId` | **`Guid`** | the id in the URL above |
| 3 | `Name` | string | |
| 4 | `StartTime` | `DateTime` | **not nullable** |
| 5 | `EndTime` | `DateTime` | **not nullable** |
| 6 | **`ConfigJson`** | **string** | the entire `Config`, as JSON **text** |
| 7 | `Metadata` | string | also free-form text |

```json
{ "TimeLimitedEventId": 1,
  "ReplicationId": "cbe9582c-6314-4ba3-ad0e-57d220b79aff",
  "Name": "Autumn Cook-Off",
  "StartTime": "2026-10-01T00:00:00Z",
  "EndTime": "2026-11-01T00:00:00Z",
  "ConfigJson": "{\"CurrencyGrant\":null,\"XpSinks\":[],\"TeamConfig\":null}",
  "Metadata": null }
```

### ⚠️ `Config` has a field but no key — it is parsed from `ConfigJson`

`ftypes.py` shows **8** fields on `TimeLimitedEventDTO`; the formatter emits **7** keys. The missing
one is `Config` (`TimeLimitedEventConfigDTO`), which is populated client-side by deserializing the
`ConfigJson` **string**. The matching failure literal is
**`'TimeLimitedEvent Metadata parsing failed'`** (`0xFC6E818`).

So:

- **`"ConfigJson": "{...}"`** — a string containing JSON. Correct.
- **`"ConfigJson": { ... }`** — an object. **Wrong**; the formatter reads a string token.
- **`"Config": { ... }`** — silently ignored (unknown key), and `Config` stays null.

`TimeLimitedEventConfigDTO` (formatter `UVGESPSHMQI` `.ctor 0x8F3E0C0`) is **3 keys** —
`CurrencyGrant`, `XpSinks`, `TeamConfig` — and that is the shape that belongs *inside* the
`ConfigJson` string.

This string-carrying-JSON pattern is the same one `api/consumables/v1/all` uses for
`ConfigurationData` ([consumables-v1-v2-routes](consumables-v1-v2-routes-wire-shapes.md)); on this build, treat any
`*Json` / `*Data` / `Metadata` key as **text until proven otherwise**.

⚠️ `StartTime`/`EndTime` are non-nullable `DateTime` — a JSON `null` throws in the Utf8Json DateTime
formatter. Emit an ISO-8601 instant or omit the key. `ReplicationId` is a non-nullable `Guid`, so
`null` throws there too; emit a real GUID string.

## The surrounding feature (not derived)

42 generated formatters live under `Utf8Json.Formatters.RecNet.Interfaces.TimeLimitedEvents` — this
is the TLA / "Recipes" live-ops system (`LiveOps.TLA.Recipes.Ingredients` and `LiveOps.TLA.Tricksters`
are two of the subsystems that 404 during the 2026 join failure,
[cv1-mappings-join-nre-2026](../../../rr-client-bringup/references/cv1-mappings-join-nre-2026.md)). Their DTOs keep real names, so one
`msig.py` per formatter maps the whole surface cheaply:

`IngredientDTO`, `IngredientRewardDTO`, `IngredientRecordDTO`, `RecipeDTO`, `RecipeIngredientDTO`,
`RecipeRecordDTO`, `RecipeChallengeTypeDTO`, `CookRecipeResultDTO`,
`CookRecipeFromIngredientsRequestDTO`, `IncrementalCookRecordDTO`, `StageIngredientsRequestDTO`,
`SuperStageResultDTO`, `RecipesEventChallengesDTO`, `RecipesEventChallengeLaneDTO`,
`RecipesEventChallengeLaneConfigDTO`, `RecipesEventRewardsDTO`, `RecipesEventRecordDTO`,
`RecipesEventXpSourceDTO`, `CompleteChallengeResponseDTO`, `TimedRewardTreeDTO`,
`TimedRewardTreeNodeDTO`, `TimedRewardTreeNodeCollectedDTO`, `TimedRewardTreeRecordDTO`,
`TimedRewardTreeXpSinkDTO`, `TimedRewardTreeXpEarnedDTO`, `TimedRewardTrackXpSinkDTO`,
`TimedEventXpSinkDTO`, `TimedEventXpMultiplierDTO`, `TimedEventCurrencyGrantDTO`,
`ActiveConsumableXpMultiplierDTO`, `ActiveRoomBoostCountXpMultiplierDTO`,
`OwnsAvatarItemXpMultiplierDTO`, `OwnsCustomAvatarItemXpMultiplierDTO`,
`InRoomWithTagXpMultiplierDTO`, `DistanceMovedXpSourceDTO`, `GiftingXpSourceDTO`, `GiftingXpReward`,
`ClientAuthoritativeCounterRateLimiterConfigDTO`, `TimeLimitedEventTeamConfigDTO`,
`TimeLimitedEventTeamConfigStorageDTO`, plus the two derived above.

`ActiveRoomBoostCountXpMultiplierDTO` ties this system to
[rooms-boosts-count](rooms-boosts-count-wire-shapes.md) — the room-boost count feeds a TLA XP multiplier.
