# The 2026 send-helper tiers — read `T`, not the friendly string

> On build `20260323.14` the 2025 heuristics for "is it enveloped?" and "is the body ignored?" both
> stop working. 2026 encodes **everything in the facade method's return type**:
> `Task<T>` deserializes into `T`; `Task<IAHBKPCLGPS<T>>` / `Task<ZBIGKCZRHCL>` means the envelope
> **is** `T`; `Task<XJAFUXFVGPU>` means **status code only, body never parsed**; and a **non-generic
> `Task`** means **no response value at all**.
> One `py msig.py <facade>` therefore settles every route on a service at once.

Established **2026-10-13** across five derivations:
[paintball-battle-pass](../endpoints/paintball-battle-pass-wire-shapes.md), [rooms-boosts-count](../endpoints/rooms-boosts-count-wire-shapes.md),
[player-verifylock](../endpoints/player-verifylock-wire-shape.md), [timelimitedevents-by-id](../endpoints/timelimitedevents-by-id-wire-shape.md),
[distancemoved-timedcurrencygrants-posts](../endpoints/distancemoved-timedcurrencygrants-posts-wire-shapes.md).

## ⚠️ What stopped working

**2025:** "a leading `friendlyActionDescription` on the send helper means enveloped"
(`MGPBDIAGCFD.HPBKMCLEANE` vs `CJBFDPLCIEJ`), and `CNDMDLNHDLI` means the body is ignored.

**2026:** *every* send takes a `friendlyActionDescription` — the generic senders are declared

```
static Task<!!T> Get(string friendlyActionDescription, HttpMethod method, string route,
                     CancellationToken cancellationToken, Action<RGBOOBRDHEB> requestBuilderAction)
```

so its presence carries no information. `paintball-battle-pass/config` passes
`'retrieve battle pass configuration'` and is a **bare** DTO.

## The four tiers

| facade/send returns | meaning | example |
|---|---|---|
| `Task<SomeDTO>` / `Task<List<T>>` / `Task<int>` | deserialize the body into exactly that — **bare** | `club/home/me`, `rooms/{id}/boosts/{aid}/count` |
| `Task<IAHBKPCLGPS<T>>` | **enveloped**, `{Value, Success, Error, error_id}` | `paintball-battle-pass/{id}/report-session` |
| `Task<ZBIGKCZRHCL>` | **valueless envelope**, `{Success, Error, error_id}` | `paintball-battle-pass/{id}/purchase` |
| `Task<XJAFUXFVGPU>` | **raw response — body NEVER parsed**, only the status code | `player/verifylock` |
| **non-generic `Task`** | **no response value at all** | `api/timedCurrencyGrants/update` |

The helper **never unwraps anything**, which is why the envelope types appear in `T` itself. Both
envelopes are **interfaces**:

```
RecNet.ZBIGKCZRHCL      { bool Success; string Error; string ErrorId }     # 2025: JFNAKFCGDAO
RecNet.IAHBKPCLGPS<T>   { T Value }  (+ the above)                          # 2025: KGOJLHJNIOD<T>
```

⚠️ **CORRECTED 2026-10-13: the wire key is `error_id`, lowercase with an underscore, exactly as on
2025.** An earlier revision of this note said 2026 had switched to PascalCase `ErrorId` — that was
read off the **C# property name** and is wrong. The `[DataMember]` rename survives: `ErrorId` does
**not** exist as a string literal anywhere in the 2026 binary, while `error_id` (`0xFDD6A48`) has
**278 references** across ~90 generated formatters. The envelope serializer **is** shareable between
the two builds.

The interfaces above are what the facades declare; the **concrete wire types** are
`RecNet.RecNetResult` (valueless), **`RecNet.RecNetResultObject<T>`** (single `Value`) and
**`RecNet.RecNetResultListObject<T>`** (list `Value`). 2026 generates a Utf8Json formatter **per
concrete instantiation** — e.g. `Utf8Json.Formatters.RecNet.ATOVKGPMENG` is
`RecNetResultObject<ClubDetails>` — and every one of them emits the same four keys in this order:

| # | key |
|---|---|
| 1 | `Value` |
| 2 | `Success` |
| 3 | `Error` |
| 4 | **`error_id`** |

(`Value` first, then the base-class members — the usual "derived before base" ordering.)

There is also `RecNet.RecNetResult`, which appears directly as `T` on some facades
(`IFTDOIEBBWL.UBYGKOAHZNY` etc.) — a concrete result type rather than the interface.

## ⚠️ `Task<T>` does NOT mean a `null` body is accepted

Added **2026-10-13** after a capture disproved the opposite assumption.

The deserializing helpers come in two flavours and the difference is an **explicit `bool` argument**,
not the type:

| helper | signature |
|---|---|
| `RGBOOBRDHEB.ZWUODKCINOA<TResponse>(ct)` | plain send |
| `RGBOOBRDHEB.LIRIDCJIGGA<TResponse>(bool a, ct)` | send with the allow-null flag |

**Seeing `LIRIDCJIGGA` tells you nothing on its own — read `a` at the call site.** `a` is `dl`
immediately before the call, so `xor edx, edx` means `false`. With `false`, a response that
deserializes to `null` throws **`RecNetMalformedResponseException: Response was empty`** from
`AIYNPFIEYFY<T>`.

⚠️ **`Response was empty` does not mean "zero-length body".** It means *the response produced no
value*. A body of `null` (4 bytes, `application/json`) triggers it exactly as a 0-byte body does.
Confirmed on `GET club/home/me`, which passes `false` on both builds
(`0x945ECDE` on 20260323.14, `0x7CA6E14` on 20250718.01) and rejects `null`
([club-home-me](../endpoints/club-home-me-wire-shape.md)).

The 2025 equivalent is `MGPBDIAGCFD.CJBFDPLCIEJ<TResponse>(bool)`, and the same rule applies — the
"nullable response" label in `SKILL.md`'s tier table describes the helper's *capability*, not the
route's contract.

**How to apply:** before telling a server that `null` is a valid empty answer, disassemble the
facade method and read the byte in `dl` at the send call. If it is 0, the route needs a real value
and there is no "none" encoding available.

## The two "no body read" tiers are different

Both ignore the payload, but they are reached by different helpers and are distinguishable:

**`Task<XJAFUXFVGPU>`** — `RGBOOBRDHEB::NJDMOZYSDOQ(ct)`. `XJAFUXFVGPU` is the HTTP response wrapper
(`.ctor(int statusCode, string, DisposableMemorySequence<byte> data, string, string, bool, bool,
HTTPCacheFileInfo)`; status at field `+0x10`). The caller reads the status itself — e.g.
`player/verifylock` compares it to `409` and does nothing otherwise.

**non-generic `Task`** — `RGBOOBRDHEB::JEYAQXBXMRA(ct)` `0x9537A00`. It only starts
**`<SendWithNoResponseAsync>d__43`** (the name comes free from the `AsyncTaskMethodBuilder.Start`
generic inst, #95959), which calls `YGADVOMHRVJ<bool>(lambda, ct)`. The caller sees nothing but
completion-or-throw, and the state machine's builder is the **non-generic** `AsyncTaskMethodBuilder`
whose `SetResult` takes no argument — a second, independent confirmation.

### Status still matters on every tier

A non-2xx raises **`RecNet.RecNetWebException`** with the message built by
`RecNet.MLREETGNUXI.VEIQCOEFCVM(int statusCode)` `0x94B0BA0` from the literal
**`'HTTP Error {0}'`** (`0xFD1BF38`). This is confirmed at runtime, not just statically: the 2026
`Player.log` carries `RecNet.RecNetWebException: HTTP Error 404` out of the generic sender
([cv1-mappings-join-nre-2026](../../../rr-client-bringup/references/cv1-mappings-join-nre-2026.md)).

So for a non-generic-`Task` route the server contract is just: **any 2xx (prefer `204 No Content`)
to accept, any non-2xx to reject.** The body is discarded either way, so there is nothing to get
wrong in it — and nothing you can put in it to signal a soft failure.

## How to read a 2026 route, in order

1. `grep` the route in `out/stringliteral.json`, then `py mxref.py <addr>`.
2. The hit is usually a **`<OriginalName>d__N$$MoveNext`** — 2026 leaks the original method name
   through compiler-generated state-machine types even when the declaring method is renamed. That
   name alone often answers "what is this route for".
3. `py msig.py <facade>` on the declaring class. **This is the step that replaces most of the 2025
   workflow**: it prints the real DTO names and the tier for every route on that service at once.
4. Verb from `[HttpMethod statics + N]` at the request-ctor call site — `0x00` delete, **`0x08` get**,
   `0x10` head, `0x18` options, **`0x20` post**, `0x28` put, `0x30` trace.
5. Service from the `r8d` immediate on that same call (the per-service factory `NJDXKMQCUTD` bakes it
   in). ⚠️ **If the constructor is inlined there is no `r8d` immediate** — the service appears as a
   direct field store instead, e.g. `mov dword ptr [rsi + 0x18], 2` for
   `api/progressionEvents/event/{id}` ([progressionevents-event-by-id](../endpoints/progressionevents-event-by-id-wire-shape.md)).
   Request-object layout at those sites: `+0x10` HttpMethod, `+0x18` service, `+0x20` path.
6. Params from `NJPEKLKCVCG` — still **verb-dependent**, see
   [elhkhfjehlm-verb-dependent-params](elhkhfjehlm-verb-dependent-params.md).
7. The `requestBuilderAction` lambda is where `ORUUDATDRUN` (response-cache TTL) lives. A `null`
   fourth argument to the ctor means no params, no body, no caching.

**How to apply:** on a 2026 route, never guess the envelope from the path, a sibling, or the presence
of a friendly string — `msig` the facade and read `T`. A non-generic `Task` or a `Task<XJAFUXFVGPU>`
means stop looking for a response shape; there isn't one.
