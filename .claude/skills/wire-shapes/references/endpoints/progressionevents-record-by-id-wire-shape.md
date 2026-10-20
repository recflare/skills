# progressionEvents record/{id} wire shape

> GET api/progressionEvents/record/{eventId} (svc 2 API) returns a BARE ProgressionEventRecordDTO. 2026 (20260323.14) has 9 keys, 2025 (20250718.01) has 7 (no ProgressionEventId, no LimitedRewardCollectionState). Send all 9 for both builds. A null body NREs, and on 2026 the client caches the record under the RESPONSE's ProgressionEventId, so echo the requested id.

Derived **2026-10-15** from both builds. Sibling routes:
[progressionevents-event-by-id](progressionevents-event-by-id-wire-shape.md),
[progressionevents-active](progressionevents-active-wire-shape.md).

`GET https://api.<host>/api/progressionEvents/record/{eventId}`. The path is
`String.Format("{0}/record/{1}", "api/progressionEvents", eventId)`. It has no query params, no body
and no request-builder lambda.

| | 20260323.14 | 20250718.01 |
|---|---|---|
| facade | `RecNet.TJASXPRZXFT.NJFEQKSQKZM(long eventId, bool)` `0x9548C50` | `MPJLPOEEGIF.HLCHIABMCOM(long, bool)` `0x7D61990` |
| returns | `MPVTAJGPRUT<RecNet.ProgressionEventRecordDTO>` | `KPIPLFECKNC<RecNet.ProgressionEventRecordDTO>` |
| request | **inlined ctor**: `[+0x10]` = HttpMethod statics `+0x08` (**GET**), `mov dword [rdi+0x18], 2` (**API**) at `0x9548F5F` | `AKJEAMCCEOH..ctor`, `r8d = 2` at `0x7D61C57`, statics `[+0x90]` then `+0x08` = GET |
| send | `RGBOOBRDHEB.ZWUODKCINOA<T>` → `CTZMMSFIPBH` (no envelope unwrap) | `MGPBDIAGCFD.HPBKMCLEANE<T>` (response required) |
| formatter | `Utf8Json.Formatters.RecNet.CRPVBJLRSJT` `.ctor 0x8DFC790` | `NEPBDPINDMD` `.ctor 0x7D82630` |

## Response: bare object, 9 keys on 2026

No `[DataMember]` renames. The order follows the key run and matches the field offsets:

| # | key | CLR | 2026 offset | in 2025? |
|---|---|---|---|---|
| 1 | `AccountId` | int | 0x10 | yes |
| 2 | `ProgressionEventId` | long | 0x18 | **no** |
| 3 | `Xp` | int | 0x20 | yes |
| 4 | `GameMinutesToday` | int | 0x24 | yes |
| 5 | `RewardsCollected` | int | 0x28 | yes |
| 6 | `BonusRewardsCollected` | int | 0x2C | yes |
| 7 | `XpBoostLastPurchasedAt` | `DateTime?` | 0x30 | yes |
| 8 | `PremiumRewardsCollected` | int | 0x40 | yes |
| 9 | `LimitedRewardCollectionState` | enum int | 0x44 | **no** |

`ProgressionEventLimitedRewardCollectionState`: `NotEarned 0`, `Earned 1`, `Collected 2`,
`CannotEarn 3`. It goes on the wire as a number, because none of the member names exist as string
literals.

```json
{ "AccountId": 2, "ProgressionEventId": 18, "Xp": 0, "GameMinutesToday": 0,
  "RewardsCollected": 0, "BonusRewardsCollected": 0, "XpBoostLastPurchasedAt": null,
  "PremiumRewardsCollected": 0, "LimitedRewardCollectionState": 0 }
```

The 2025 formatter drops the two extra keys silently, so this one payload serves both builds.
`XpBoostLastPurchasedAt` is the only nullable field.

## Client-side behaviour (2026)

From `NJFEQKSQKZM`:
- **Cache.** If the `bool` is false and the `Dictionary<long, DTO>` at `this+0x18` already holds
  `eventId`, the cached record is returned and **no request is sent**. Passing true forces a refetch.
- **The `-1` sentinel.** If `this+0x20` is set and `eventId == -1`, the client builds a placeholder
  record locally (`ProgressionEventId = -1`, everything else 0/null) and sends nothing. -1 is the same
  "no event" value that [progressionevents-active](progressionevents-active-wire-shape.md) returns.

The continuation is `TJASXPRZXFT.NFIUSLBHVGK(DTO)` at `0x9548BD0`:

```
if (dto == null) -> NRE (0x9548C3F)
cache[dto.ProgressionEventId] = dto       // key read from the RESPONSE (+0x18)
recordChanged?.Invoke(dto)                // Action<ProgressionEventRecordDTO> at this+0x10
```

So:
- **A `null` body throws.** For a player with no progress, return a zeroed record, not `null`.
- **Echo the requested id in `ProgressionEventId`.** If you omit it, it deserializes to 0. The record
  is then cached under key 0, every later non-forced call for event 18 misses the cache and refetches,
  and any consumer that looks the record up by event id finds nothing.
- `AccountId` is not read on this path.

On 2025 the DTO has no event-id field, so the cache cannot be keyed from the response there.
