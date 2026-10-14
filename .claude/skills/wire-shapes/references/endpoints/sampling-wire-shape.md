# `GET sampling?sessionId=` wire shape (2026 build only)

> `GET datacollection.<host>/sampling?sessionId=<id>` (svc **19 DataCollection**) returns a
> **BARE ARRAY** of the 2-key `EventDTO` — `{EventType: string, ShouldBeSampled: bool}`.
> ⚠️ **`{}` throws `Malformed Response: '{}'`.** Serve **`[]`** to sample nothing.
> ⚠️ **2026 build `20260323.14` only.**

Derived **2026-10-13** from build `20260323.14`, after a live `Player.log` showed
`Malformed Response: '{}'` on this route. Found via the `# Formatted Async Stack Trace` block, which
named `RecNet.Data.FRNWCURICAL.IIRTTUTGNFO` — see
[cv1-mappings-join-nre-2026](../../../rr-client-bringup/references/cv1-mappings-join-nre-2026.md).

Service **19 = DataCollection** (`mov r8d, 0x13` at `0x95D8705`), verb **GET**
(`[HttpMethod statics + 0x08]` at `0x95D86E6`). Path is the bare literal `sampling` (`0xFC...`), and
the single query parameter is **`sessionId`** — a GET, so `NJPEKLKCVCG` puts it in the query string
([elhkhfjehlm-verb-dependent-params](../conventions/elhkhfjehlm-verb-dependent-params.md)).

Facade `RecNet.Data.FRNWCURICAL.IIRTTUTGNFO(...)` `0x95CB2A0`, state machine
**`<GetSamplingEvents>d__24$$MoveNext`** `0x95D8540` (+0x4A0).

⚠️ **This is an `async void`.** The method's builder is `AsyncVoidMethodBuilder`, not
`AsyncTaskMethodBuilder` — so nothing awaits it and the exception surfaces as an unhandled
`[Exception]` in the log rather than failing a caller. That is why a wrong body here is noisy but
otherwise harmless: it does **not** feed `[Platform.BootSequence]` and cannot cause the
"glitch in the matrix" join failure.

## Response — bare array

Send is `RGBOOBRDHEB::ZWUODKCINOA<T>` with generic inst **#23356 = `List<.EventDTO>`**. No envelope.

`.EventDTO` — formatter `Utf8Json.Formatters.RecNet.Data.PMFFDWNUODD` `.ctor` **`0x8F50F80`**
(+0x230), key run 1:1 with the field list:

| # | key | CLR |
|---|---|---|
| 1 | `EventType` | string |
| 2 | `ShouldBeSampled` | bool |

```json
[ { "EventType": "player_join", "ShouldBeSampled": true },
  { "EventType": "room_load",   "ShouldBeSampled": false } ]
```

**`[]` is the correct "sample nothing" answer** and is what a server with no telemetry pipeline
should return. `{}` hard-fails — this is an ordinary member of the
[nonobject-response-routes](../conventions/nonobject-response-routes.md) class.

`ShouldBeSampled` is a non-nullable bool, so `null` throws; omit the key to mean `false`.

## ✅ Duplicate `EventType` values are safe here

After the await, the state machine clears and refills a **`Dictionary<string,bool>`** (generic inst
#1685) keyed by `EventType`:

```
dict.Clear();                                  // 0x1895D8571
foreach (var e in list) dict[e.EventType] = e.ShouldBeSampled;   // set_Item, 0x1895D857D
```

It uses **`set_Item`**, not `Add` — so a repeated `EventType` simply overwrites (last one wins) and
does **not** throw. ⚠️ Contrast `api/consumables/v1/all`, which uses `Dictionary.Add` and therefore
**does** throw on a duplicate key, taking the whole catalogue load down
([consumables-v1-v2-routes](consumables-v1-v2-routes-wire-shapes.md)). Same data structure, opposite tolerance — always read
which method the loop calls before telling a server its keys may repeat.

A `null` *element* inside the array would NRE on `e.EventType`; a `null` array would NRE on
`GetEnumerator`. Serve `[]`, never `null`, and no null entries.
