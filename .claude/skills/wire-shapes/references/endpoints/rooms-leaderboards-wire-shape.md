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
