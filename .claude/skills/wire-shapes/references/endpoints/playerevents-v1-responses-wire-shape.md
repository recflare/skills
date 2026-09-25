# Playerevents v1 responses wire shape

> GET api/playerevents/v1/{eventId}/responses (svc 2 API) takes NO params and returns a BARE ARRAY of the 5-key DHOECFANGJN RSVP record; Type is an enum whose `Yes` is 0, so an omitted Type reads as an affirmative RSVP.

Derived **2026-09-23** from build `20250718.01`.
Sibling of [playerevents-v1-room](playerevents-v1-room-wire-shape.md) and [playerevents-v2](playerevents-v2-wire-shape.md); confirms that note's
"v1 is read-only" finding — this is another v1 GET.

`GET https://api.<host>/api/playerevents/v1/{playerEventId}/responses` — service **2 = API**
(facade `BPHIJNEOCMK`), verb **GET** (`HttpMethod` statics `[rcx+8]` at `0x7E424D6`).

Path is `String.Format("api/playerevents/v1/{0}/responses", id)` — the event id is a **path
segment**. **No query params, no body** (no `ELHKHFJEHLM`, no `ELKIBCPINAP`).

Client entry `BPHIJNEOCMK.AECJHFJKJNN(long playerEventId, CancellationToken)` **`0x7E42420`**
(+0x120) → `Task<List<DHOECFANGJN>>`. The literal is also referenced by
`<<GetAllPlayerEventResponses>b__0>d.MoveNext` `0x7E55180` — a compiler-generated wrapper whose
**unobfuscated** name confirms the route's purpose.

## Response — BARE ARRAY, no envelope

Send helper is **`BPHIJNEOCMK.LMKONLJOAEP<T>`** — the facade's description-less (bare) helper, so
there is no envelope ([playerevents-v1-room](playerevents-v1-room-wire-shape.md) has the bare-vs-enveloped rule). Generic inst
**#2712** = **`List<DHOECFANGJN>`**. `{}` or an empty body throws `IONCMJIACFI`; serve `[]`.

Element `.DHOECFANGJN`, formatter **`KFHAJAIAKNB`** `.ctor 0x772BC30` (+0x710), key run
`0x772C12F..0x772C267` — **5 keys, 1:1 with the 5 declared fields**:

| # | key | CLR | off |
|---|---|---|---|
| 1 | `PlayerEventResponseId` | long | 0x10 |
| 2 | `PlayerEventId` | long | 0x18 |
| 3 | `PlayerId` | **int** | 0x20 |
| 4 | `CreatedAt` | DateTime | 0x28 |
| 5 | `Type` | enum `DNNJHDCDDFO` | 0x30 |

```json
[ { "PlayerEventResponseId": 900001, "PlayerEventId": 134, "PlayerId": 205,
    "CreatedAt": "2026-09-23T00:00:00Z", "Type": 0 } ]
```

`DNNJHDCDDFO : int` — **`None -1`, `Yes 0`, `Interested 1`, `No 2`, `Pending 3`**. Numeric on the
wire.

⚠️ **`Yes` is `0`, so an omitted or defaulted `Type` reads as an affirmative RSVP**, not as unset.
Send **`-1` (`None`)** if you mean "no response". Same shape of trap as `GiftContext`, where the
absent value is `Default (0)` rather than `None (-1)`.

⚠️ `PlayerId` is an **int** while both event ids are **long** — easy to widen the wrong one.

## No validation

`DHOECFANGJN.CPOBHIECLEN` is the shared no-op stub `0xA60520` (4877 names fold onto that RVA), so
every key is omittable and nothing throws on partial data. The only hard requirement is the array.

## Table gap

This route is **absent from the generated `nonobject-responses.txt`** because its path is
`String.Format`-built and the scanner only picks up whole-route literals — the same blind spot as
[roomkeys-v1-room](roomkeys-v1-room-wire-shape.md) and [ugcpurchasables-room-items](ugcpurchasables-room-items-wire-shape.md). Treat that table as a lower
bound, never a census.

Other v1 routes carrying a `{0}` path segment, for reference: `api/playerevents/v1/{0}`,
`/all/{0}`, `/club/{0}`, `/room/{0}`.
