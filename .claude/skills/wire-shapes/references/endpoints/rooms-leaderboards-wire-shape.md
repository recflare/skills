# Rooms leaderboards wire shape

> POST and DELETE rooms/{roomId}/leaderboards/{index} (svc 16 Rooms) both return the VALUELESS envelope {Success, Error, error_id}; the POST's leaderboardTitle/statFormat/sortAscending are QUERY params, not a body, and Success!=true throws LLCLDPPAGIJ.

Derived **2026-09-02** from build `20250718.01` via [recflare-2025-metadata-carve](../../../il2cpp-analysis/references/recflare-2025-metadata-carve.md).
Route literal `'rooms/{0}/leaderboards/{1}'` `0xD1A1E30`, Rooms facade `OALMDGJKBJH`, **svc 16**
([recnet-service-enum](../conventions/recnet-service-enum.md)). `{1}` is the leaderboard **index** (int), not an id.

| verb | client entry | RVA | `HttpMethod` statics | friendlyActionDescription |
|---|---|---|---|---|
| **POST** | `HICNNOMNBPK(long roomId, int index, string leaderboardTitle, int statFormat, bool sortAscending, CT)` | `0x7DFA460` | `+0x20` post | `'create or update room leaderboard metadata'` |
| **DELETE** | `LFCHKAABMCH(long roomId, int index, CT)` | `0x7DFCF00` | `+0x00` delete | `'delete room leaderboard metadata'` |

## The POST parameters are QUERY params, not a body

`IPDNJJNGLCB.PNLHEEEGOGE(MGPBDIAGCFD r)` `0x7DEFE00` — a display class whose fields are
**unobfuscated**: `leaderboardTitle` (string), `statFormat` (int), `sortAscending` (bool). All three
are added with **`MGPBDIAGCFD.ELHKHFJEHLM`**, the query-param adder
([algorithmiclists-wire-shape](algorithmiclists-wire-shape.md)) — there is **no `ELKIBCPINAP` call, so no request body at all**.
`sortAscending` serialises via `object.ToString()`, hence the .NET-style `False`/`True` casing.
DELETE adds nothing — bare path.

## Response — the VALUELESS envelope, for both verbs

Both call the **non-generic** `OALMDGJKBJH.PJPLCMBOAFB(string friendlyActionDescription,
HttpMethod, string route, CancellationToken, Action<MGPBDIAGCFD>)` `0x7DFF7C0` → plain `Task`.
Its state machine `.BAGDEGGEONJ` (`MoveNext` `0x7DE77F0`) has **unobfuscated fields** — `method`,
`route`, `requestBuilderAction`, `cancellationToken`, `friendlyActionDescription` — and
`<>u__1 = TaskAwaiter<`**`JFNAKFCGDAO`**`>`.

`JFNAKFCGDAO` is the **valueless envelope** ([outfits-me-put-wire-shape](outfits-me-put-wire-shape.md)) — formatter
`OGMMAAFJCJG` `.ctor 0x76887E0`, exactly three keys, re-verified here:

```json
{ "Success": true, "Error": null, "error_id": null }
```

(case variants accepted: `success`, `error`, `Error_id`.) **No `Value` key is read** — the helper is
non-generic, so nothing else in the body is looked at.

`BAGDEGGEONJ.MoveNext`:
- awaited envelope **null → NullReferenceException** (`0x7DE797A`)
- `Success != true` → **`LLCLDPPAGIJ`** ([llcldppagij-envelope-failure-exception](../conventions/llcldppagij-envelope-failure-exception.md)) with the message
  **`"Failed to " + friendlyActionDescription`** — i.e. *"Failed to create or update room leaderboard
  metadata"* / *"Failed to delete room leaderboard metadata"* (`0x7DE7B8E` concat, `0x7DE7B4B` ctor)
- otherwise `SetResult()` — the `Task` completes and nothing is returned to the caller.

So `{"Success":true}` alone is a complete, valid response for both verbs; `Error`/`error_id` are only
read into the envelope object and never surfaced (the exception text uses the *client's* description,
not your `Error` string).

## Rule confirmation

This is another clean instance of the [playerevents-v1-room-wire-shape](playerevents-v1-room-wire-shape.md) rule: the helper carries a
leading `friendlyActionDescription`, therefore the route is **enveloped**. The non-generic overload
of that helper maps to the `JFNAKFCGDAO` tier specifically.

Related but different service: the leaderboard *stat* routes (`leaderboard/GetPlayerRank`,
`leaderboard/CheckAndSetStat`, `leaderboard/GetRanks`, `leaderboard/GetNearbyScores`) live on
**svc 10** and are bare — see [leaderboard-wire-shapes](leaderboard-wire-shapes.md).

⚠️ **CORRECTION 2026-09-02:** where this note says the parameters are **query params**, they
are actually an **`application/x-www-form-urlencoded` request body** — `ELHKHFJEHLM` routes params
to the query string only for GET. See [elhkhfjehlm-verb-dependent-params](../conventions/elhkhfjehlm-verb-dependent-params.md). Response shape
unaffected.

# ⚠️ 2026 (`20260323.14`): the ENVELOPE IS GONE — the body is no longer parsed

Derived **2026-10-22**. Verbs, path and parameters are unchanged; **the response tier changed.**

Facade is now **`RecNet.Rooms.DFMBMRNABHU`**:

```csharp
Task HAGCWUSHAAP(long roomId, int index, string title, int statFormat, bool sortAscending, ct)  // 0x95ADC90
Task JJUTAZWMGZY(long roomId, int index, ct)                                                    // 0x95AE820
```

| | 2025 | 2026 |
|---|---|---|
| path | `rooms/{0}/leaderboards/{1}` | same, literal **`0xFD66620`** (exactly 4 refs = 2 methods × 2) |
| verbs | POST · DELETE | same — `[statics+0x20]` at `0x95ADDA9` (POST), `[statics+0x00]` at `0x95AE8C5` (DELETE) |
| params | `leaderboardTitle`, `statFormat`, `sortAscending` in a **form-urlencoded body** | **same three**, all referenced from the closure **`XKLIFIKKMWF.HOBGDNEBDWH`** (`0xFC393D8`, `0xFC45CC0`, `0xFC10CE0`) |
| response | **valueless envelope** `{Success, Error, error_id}`, `Success != true` throws `LLCLDPPAGIJ` | **nothing is parsed** |

Both methods return a **non-generic `Task`**, and both go through the **non-generic** overload of the
class-bound send helper:

```csharp
Task         DFMBMRNABHU.MSBYXMTYOOH(string friendlyActionDescription, HttpMethod, string route, ct, Action<RGBOOBRDHEB>)
Task<!!T>    DFMBMRNABHU.MSBYXMTYOOH(...)   // the generic sibling — NOT used here
```

Call sites `0x95ADE43` (POST, description `'create or update room leaderboard metadata'`) and
`0x95AE92A` (DELETE, `'delete room leaderboard metadata'`).

Per [2026-send-helper-tiers](../conventions/2026-send-helper-tiers.md), **a non-generic `Task` means
no response value at all** — the body is never deserialized.

➡️ **Consequences for the server:**
- `{"Success":true,...}` is still *accepted*, but only because it is ignored. An **empty body is
  equally fine**.
- ⚠️ **`{"Success":false}` no longer fails the call.** On 2025 that threw `LLCLDPPAGIJ` and the UI
  reported the error; on 2026 it is silently discarded and the client treats the operation as having
  succeeded. **Denials must be a non-2xx HTTP status**, exactly like
  [api-images-v1-report](api-images-v1-report-wire-shape.md).
- The 2025 rule quoted above — "the helper carries a leading `friendlyActionDescription`, therefore
  the route is enveloped" — **does not hold on 2026**: every 2026 send takes a description, so it
  carries no information. That is the documented 2026 retirement of the heuristic, not a
  contradiction of the 2025 finding.
