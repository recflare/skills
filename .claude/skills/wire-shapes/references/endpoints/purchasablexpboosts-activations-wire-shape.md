# purchasableXpBoosts/activations wire shape

> GET api/purchasableXpBoosts/activations (svc 2 API, build 20260323.14 ONLY) takes no params and returns a BARE paged wrapper {Results: [5-key PurchasableXpBoostActivationDTO], TotalResults: long}, not a bare array and not the RecNet envelope. A `[]` body will not deserialize.

Derived **2026-10-15** from build `20260323.14`. **The route does not exist on `20250718.01`**:
neither `api/purchasableXpBoosts` nor `.../activations` is a string literal there.

`GET https://api.<host>/api/purchasableXpBoosts/activations`

| | |
|---|---|
| state machine | `<GetActivations>d__9$$MoveNext` `0x954A1A0` (the original name leaks through the compiler-generated type) |
| facade | `RecNet.SAFJZXKVOFB.XHWZDCZPXQF(CancellationToken)` `0x9547770` → `Task<RecNet.Common.ODFPVNYWDAJ<PurchasableXpBoostActivationDTO>>` |
| literal | `0xFC63660` |
| request | **inlined ctor**: `[+0x10]` = HttpMethod statics `+0x08` (**GET**, `0x954A2C7`), `mov dword [rdi+0x18], 2` (**API**, `0x954A2FB`), `[+0x20]` = path |
| params | none: no `NJPEKLKCVCG` call, no body |
| caching | `ORUUDATDRUN(req, RecNet.Cache static, 0, 0)` at `0x954A342`, so the response is cached client-side |
| send | `RGBOOBRDHEB.ZWUODKCINOA<T>`, T = generic inst **3002** = `ODFPVNYWDAJ<PurchasableXpBoostActivationDTO>` |

The `AsyncTaskMethodBuilder<T>` and `TaskAwaiter<T>` in the state machine use the same inst 3002, so
T is the deserialize target and nothing unwraps it.

## Response

### Wrapper: `RecNet.Common.ODFPVNYWDAJ<T>`, 2 keys

A generic paged-result type: `IReadOnlyList<T>` plus a `long`. Utf8Json generates one formatter per
instantiation. This route uses **`Utf8Json.Formatters.RecNet.Common.DZDJJXVHQFQ`** (`.ctor
0x8F43F70`). Siblings with the same two keys wrap `RoomDTO` (`BCDUKKYQCTP`),
`PlatformNotificationCategoryConfigDTO` (`BVXOITRFJDK`), `KeepsakeCategoryConfigDTO` (`LTAVEKHPGRX`),
`CustomAvatarItem` (`QAZWCDUNNRS`) and `SubRoomDataSaveDTO` (`RKOUHUVDAAE`).

| # | key | CLR |
|---|---|---|
| 1 | `Results` | `IReadOnlyList<T>` |
| 2 | `TotalResults` | long |

### Element: `RecNet.PurchasableXpBoostActivationDTO`, 5 keys

Formatter `Utf8Json.Formatters.RecNet.FYPQTINZIVY` `.ctor 0x8DFFC60`. No renames.

| # | key | CLR |
|---|---|---|
| 1 | `PurchasableXpBoostLedgerEntryId` | long |
| 2 | `PurchasableXpBoostId` | `System.Guid` |
| 3 | `XpMultiplier` | float |
| 4 | `StartTime` | DateTime |
| 5 | `EndTime` | DateTime |

```json
{ "Results": [], "TotalResults": 0 }
```

```json
{ "Results": [ { "PurchasableXpBoostLedgerEntryId": 1,
                 "PurchasableXpBoostId": "<guid>",
                 "XpMultiplier": 2.0,
                 "StartTime": "2026-10-15T12:00:00Z",
                 "EndTime":   "2026-10-15T13:00:00Z" } ],
  "TotalResults": 1 }
```

`PurchasableXpBoostId` presumably refers to the boost catalog served by
`api/progressionEvents/{id}/xpboosts` (`ProgressionEventPurchasableXpBoostDTO`). That link was not
traced.

## Related client-side behaviour

- `SAFJZXKVOFB.DXAWWIEKHLE` `0x95474E0` and `.HRKYDOZFSEV(PurchasableXpBoostActivationDTO)`
  `0x9547610` both pass the prefix `'api/purchasableXpBoosts'`. `HRKYDOZFSEV` also invokes a
  `DQCNOGDGYBL<PurchasableXpBoostActivationDTO>` event. This looks like cache invalidation plus a
  "boost activated" event, presumably fed by the `PurchasableXpBoostActivated` notification
  (literal `0xFCBF5E8`). Not verified.
- `XHWZDCZPXQF` has **no direct call sites**, so it is reached through interface dispatch. The
  consumer of `Results` (null handling, any `EndTime` filtering) was **not traced**. Send `[]` rather
  than `null` for `Results`, and send all 5 element keys. A missing `EndTime` deserializes to
  `DateTime.MinValue`, which would make the boost look long expired.
