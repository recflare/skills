# `POST api/distanceMovedRewardTracks/distance` and `POST api/timedCurrencyGrants/update` — no response shape (2026 only)

> **Neither route has a response shape.** Both are sent with the **non-generic `Task`** helper
> (`RGBOOBRDHEB::JEYAQXBXMRA`), so the client reads **no value at all** from the response — not an
> object, not a status code, nothing. The body is discarded unparsed.
> **Return `204 No Content`.** Any 2xx is accepted identically; any non-2xx throws
> `RecNet.RecNetWebException: HTTP Error <code>` into the caller.
> ⚠️ **2026 build `20260323.14` only** — both routes are absent from `20250718.01`.

Derived **2026-10-13** from build `20260323.14` via the 2026 carve
([[recflare-2026-static-index]] → `C:\Games\recnet-patcher\il2cpp-2026\`). Everything else in this
catalog is 20250718.01 unless it says otherwise. See
[2026-send-helper-tiers](../conventions/2026-send-helper-tiers.md) for why the non-generic `Task` is the tell.

Both are service **28 Econ** and both are **POST** (`[HttpMethod statics + 0x20]` = `post_method`),
hence `econ.<host>`.

## `POST api/distanceMovedRewardTracks/distance`

Route literal `0xFC48B10`, state machine **`<RecordDistanceTraveled>d__3$$MoveNext`** `0x95815D0`
(+0x270). Verb read at `0x95816B1`, service `mov r8d, 0x1c` at `0x95816D4`.

**One parameter, one float:**

```
distanceMeters=<float>
```

`movss xmm0, dword ptr [rbx + 0x20]` at `0x95816E5` pulls a **`float`** out of the state machine,
boxes it at `0x95816FC`, and hands it to
`RGBOOBRDHEB.NJPEKLKCVCG("distanceMeters", (object)value)` at `0x958171A`.

Because the verb is **POST**, that parameter is an **`application/x-www-form-urlencoded` body**, not
a query string — the verb branch in `NJPEKLKCVCG` is unchanged from 2025's `ELHKHFJEHLM`
([elhkhfjehlm-verb-dependent-params](../conventions/elhkhfjehlm-verb-dependent-params.md)). Values are stringified with
`object.ToString()`, so expect .NET formatting (`12.5`, and `True`/`False` for bools elsewhere).

Nothing else is on the request: no cache TTL, no JSON body, no second parameter.

Send is `RGBOOBRDHEB::JEYAQXBXMRA(ct) -> Task` ⇒ **no response value**.

This is the write half of the TLA "distance moved" XP source; the config side is
`RecNet.Interfaces.TimeLimitedEvents.DistanceMovedXpSourceDTO` (`XpPerMeter`), which arrives inside
`TimeLimitedEventDTO.ConfigJson` ([timelimitedevents-by-id](timelimitedevents-by-id-wire-shape.md)). So the server multiplies
the posted metres by the configured `XpPerMeter` — the client never sees the awarded XP from this
call.

## `POST api/timedCurrencyGrants/update`

Route literal `0xFC73568`, state machine **`<UpdateGrants>d__10$$MoveNext`** `0x9583160` (+0x400).
Facade `RecNet.RecNetTimedCurrencyGrants.IBHEUMIYCFQ(ct) -> Task`. Verb read at `0x95833F0`, service
`mov r8d, 0x1c` at `0x9583413`.

**No parameters and no body whatsoever.** The request-ctor's `requestBuilderAction` argument is
**`null`** — `mov qword ptr [rsp + 0x20], 0` at `0x9583403` — and there is no `NJPEKLKCVCG` and no
body setter anywhere in the method. It is a bare `POST` with an empty body whose only information is
"this player is here; recompute their accrued grants".

Send is `JEYAQXBXMRA` ⇒ **no response value**. To read the result back, the client uses the separate
GET (below).

### ⚠️ Client-side throttle: at most once per minute

Before building the request the state machine does:

```csharp
var now = KAVZNQFQHAV.LHIGTOQPEMU();                       // the clock, 0x9583299
TimeSpan? elapsed = lastUpdate.HasValue                     // 0x95832AE
                  ? now - lastUpdate.Value                  // DateTime.op_Subtraction, 0x95832D2
                  : (TimeSpan?)null;
if (elapsed.HasValue && elapsed.Value <= RecNetTimedCurrencyGrants.RXNPXIEAIXM)
    return;                                                 // 0x9583350 / jmp 0x958347A
```

`RXNPXIEAIXM` is set in `RecNetTimedCurrencyGrants..cctor` `0x9571000` to
**`TimeSpan.FromMinutes(1)`** (the constant `1.0` at image offset `0xB9D4FA8`, loaded at
`0x9571041`).

So the client posts **at most once per minute**, and because the "last update" is a `Nullable` the
**first** call after start-up always goes through. If you see this route arriving more often than
once a minute, the manager is being re-created, not looping.

### The sibling read — `GET api/timedCurrencyGrants/{id}`

`SNVJKLFYGNG(long id, ct) -> Task<TimedCurrencyGrantDTO>` (state machine
`<GetGrantByIdInternal>d__11` `0x957CDA0`, base literal `api/timedCurrencyGrants` `0xFC73218`).
**Bare**, 8 keys — formatter `Utf8Json.Formatters.RecNet.GCOCSHASVHN` `.ctor 0x8EA7D50` (+0x630),
key run verified against the field list 1:1, no renames:

| # | key | CLR |
|---|---|---|
| 1 | `TimedCurrencyGrantId` | `long` |
| 2 | `Name` | string |
| 3 | `StartTime` | `DateTime` |
| 4 | `EndTime` | `DateTime` |
| 5 | `CurrencyType` | `RecNet.CurrencyType` (numeric enum) |
| 6 | `OfflineRatePerHour` | **float** |
| 7 | `OnlineRatePerHour` | **float** |
| 8 | `ActiveExperiment` | string |

```json
{ "TimedCurrencyGrantId": 1, "Name": "Daily Tokens",
  "StartTime": "2026-10-01T00:00:00Z", "EndTime": "2026-12-01T00:00:00Z",
  "CurrencyType": 0, "OfflineRatePerHour": 1.0, "OnlineRatePerHour": 5.0,
  "ActiveExperiment": null }
```

`StartTime`/`EndTime` are non-nullable `DateTime` and the two rates are non-nullable `float` — a JSON
`null` on any of them throws in the Utf8Json formatter. Omit the key instead.

## What the server must do with both POSTs

| response | client behaviour |
|---|---|
| **`204 No Content`** | accepted. **Recommended.** |
| `200` with any body | identical — the body is never read |
| any other 2xx | identical |
| any non-2xx | **throws** `RecNetWebException("HTTP Error <code>")` into the awaiting caller |

The message comes from `RecNet.MLREETGNUXI.VEIQCOEFCVM(int)` `0x94B0BA0` formatting
`'HTTP Error {0}'` (`0xFD1BF38`).

⚠️ **There is no way to signal a soft failure.** Because no value is read, a `200` carrying
`{"Success": false, …}` is indistinguishable from success — the rejection has to be the status code.
This is the same rule as 2025's `CNDMDLNHDLI` tier.

⚠️ Conversely, **a 404 here is not silent.** Unlike `player/verifylock` (where a 404 reads as
"lock valid" and costs nothing, [player-verifylock](player-verifylock-wire-shape.md)), an unimplemented route on either of
these throws. If they are in the 404 pile during the 2026 join failure
([cv1-mappings-join-nre-2026](../../../rr-client-bringup/references/cv1-mappings-join-nre-2026.md)), they are contributing real exceptions —
stubbing both to `204` is a one-line fix that removes them.
