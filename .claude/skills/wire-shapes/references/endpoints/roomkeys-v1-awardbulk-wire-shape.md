# Roomkeys v1 awardbulk wire shape

> POST api/roomkeys/v1/awardbulk (svc 28 Econ) is the only roomkeys route with a JSON BODY rather than form fields, and its response is an ARRAY OF PER-ITEM ENVELOPES — List<KGOJLHJNIOD<{RoomKeyId, AccountId}>>, one envelope per request item. Driven by a client-side request BATCHER, so N is whatever accumulated in the debounce window.

Derived **2026-10-01** from build `20250718.01`.
Siblings: [roomkeys-v1-create](roomkeys-v1-create-wire-shape.md) (form fields), [roomkeys-v1-room](roomkeys-v1-room-wire-shape.md) (bare array).

`POST https://econ.<host>/api/roomkeys/v1/awardbulk` — service **28 = Econ**
(`mov dword ptr [rsi+0x18], 0x1c` at `0x7D98511`), verb **POST** (`HttpMethod` statics `[rcx+0x20]`
at `0x7D984CB`). Whole-route literal, slot `0xD14F2C0`.

Client entry `LHMONGGMNAI.IJKGAGPAFAL` **`0x7D98410`**, reached by tail-jump from
**`RecRoom.Systems.Economy.RoomKeys.RoomKeysManager.IJKGAGPAFAL`** `0xF591F0` — unobfuscated, which
names the route.

## Request — a JSON body, not form fields

This is the **only** roomkeys route that uses `MGPBDIAGCFD.ELKIBCPINAP` (the body setter) instead of
`ELHKHFJEHLM` form/query fields. Generic inst **#13405** = **`.KCEHJFDIHLH`**, whose two fields are
`long` at `0x10` and `int` at `0x18` — the same layout *and the same obfuscated backing-field names*
(`BPMDDMBIACG`, `GIMCDKIBOHE`) as the response value type, so the item shape is:

```json
[ { "RoomKeyId": 900001, "AccountId": 205 } ]
```

Key names confirmed by key-literal intersection: only five formatter ctors reference both `RoomKeyId`
and `AccountId`, and the two-key ones are `0x76A60C0` / `0x76B2A90` / `0x7E7A410` (the third being the
response value's). Utf8Json accepts any key order, so the server need not care that the
[owns/bulk](roomkeys-v1-owns-bulk-wire-shape.md) sibling emits `AccountId` first.

**Confirmed 2026-10-01 that the body really is an array**, not inferred from the route name: the
Utf8Json serializer is instantiated over **`IEnumerable<KCEHJFDIHLH>`** (methodSpec 904517,
`GEMFFEGOJPC::MDKDDHDGDJK`).

## Response — ARRAY of PER-ITEM ENVELOPES

`MGPBDIAGCFD.HPBKMCLEANE<T>` (response required), generic inst **#22037** =
**`List<KGOJLHJNIOD<EDDNPLOOPIA>>`**. That is an array whose **every element is a single-value
envelope** — not a bare array, and not one envelope wrapping an array:

```json
[ { "Value": { "RoomKeyId": 900001, "AccountId": 205 },
    "Success": true, "Error": null, "error_id": null } ]
```

`EDDNPLOOPIA` (typedef #22866), formatter `FIMPJMMHADL` `.ctor 0x7E7A410`, 2 keys:

| # | key | CLR | off |
|---|---|---|---|
| 1 | `RoomKeyId` | long | 0x10 |
| 2 | `AccountId` | **int** | 0x18 |

Envelope member order is derived-first — `Value`, then `Success`, `Error`, `error_id` (lowercase) —
see the hierarchy in [rooms-isbanned](rooms-isbanned-wire-shape.md). `{}` or an empty body throws
`IONCMJIACFI`; serve `[]` for "nothing awarded".

**Echo `Value` back.** Each element identifies which `(RoomKeyId, AccountId)` pair it reports on, so
`Value` is how a result is attributable at all. Returning envelopes with a null `Value` leaves the
client unable to tell which award succeeded.

## It is fed by a client-side batcher

The call site is generic over **`HBDOGOHIEDF<KCEHJFDIHLH, KGOJLHJNIOD<EDDNPLOOPIA>>`** (generic inst
#11205) — a request **batcher/debouncer**, not a plain send. Its 12 fields include two
`List<MDKGLKBMHFH<TReq,TResp>>` pending queues, two `CancellationTokenSource`s, a `Task` and two
`float` delays. So individual "award this key to this player" calls accumulate and flush as one
array.

Consequences for the server:

- **N is unpredictable.** The same user action can produce a 1-item or a 20-item body depending on
  timing. Do not assume one.
- **Return one envelope per request item.** The batcher has to fan results back out to the individual
  awaiting callers.

⚠️ **Not pinned: how results are matched to pending requests, and whether a `Success: false` element
throws.** The matching lives in `HBDOGOHIEDF`/`MDKGLKBMHFH` generic-shared code with **no concrete
entries in `methods.pkl`**, so neither ordering nor per-item failure handling could be read out.
`LLCLDPPAGIJ` is raised by the explicit extension `POCKEGKCADF.AIHPPAPDEBL`
([llcldppagij-envelope-failure-exception](../conventions/llcldppagij-envelope-failure-exception.md)), not by the deserialize hook, so whether it
fires here depends on that unresolved code. **Serve `Success: true` per item**, return them in request
order, and treat a partial failure as untested.

## Siblings on this facade

`api/roomkeys/v1/owns/bulk` returns the **3-key** `{doesPlayerOwnRoomKey, AccountId, RoomKeyId}`
(formatter `0x76B5AB0`) — same id pair plus a bool, so do not reuse this route's 2-key shape for it.
`/revoke` and `/mine` are not yet derived.
