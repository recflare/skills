# Elhkhfjehlm verb dependent params

> CORRECTION: MGPBDIAGCFD.ELHKHFJEHLM is NOT a query-param adder — it branches on the verb. GET puts params in the query string; every other verb puts them in an application/x-www-form-urlencoded BODY.

Established **2026-09-02** from build `20250718.01`, after a mitmproxy capture of
`POST rooms/{id}/leaderboards/{i}` showed `leaderboardTitle` / `statFormat` / `sortAscending` in the
**request body**, contradicting notes that called them query params.

## The mechanism

`MGPBDIAGCFD` carries **two** `List<KeyValuePair<string,string>>`:
`IDNLIFPDFPI` **`+0x28`** and `GMOFOGHJJJA` **`+0x30`**.

`MGPBDIAGCFD.ELHKHFJEHLM(string name, object value)` **`0x7D9B820`**:

```
rbp = this.OKLBFBBPMPB                       ; the request's HttpMethod, field +0x10
al  = HttpMethod.op_Equality(rbp, HttpMethod.get_method)   ; statics +0x08
r9  = &this[+0x28]                           ; default
if (!al) r9 = &this[+0x30]                   ; 0x7D9B8DA
tail-call ELHKHFJEHLM(this, name, value, r9) ; 0x7D9B420, the 4-arg core
```

- **GET → `+0x28`**, which `MGPBDIAGCFD.HGLJADFEDMH` `0x7D9BAE0` splices into the URL with `'?'` and
  `'&'` (`0x7D9BC88`/`0x7D9BC94`) — a real query string.
- **POST / PUT / DELETE → `+0x30`**, which the request pump `CBACIMLIBPF`
  ([serialized-request-queue-stall](../../../rr-client-bringup/references/serialized-request-queue-stall.md)) emits as an
  **`application/x-www-form-urlencoded`** body (`0xD165C98`, referenced from
  `CBACIMLIBPF.EEJPCKJEKKL` `0x7CC42B0`).

Values are stringified with `object.ToString()`, which is why booleans appear as .NET-cased
`True`/`False`.

## What this invalidates

Every note that says "takes X as **query params**, no body" for a **non-GET** route is wrong on that
one point: those params are a **form-urlencoded body**. The *response* shapes in those notes are
unaffected — the send helper and `T` were derived separately.

Known affected (all say query, all non-GET): [rooms-leaderboards-wire-shape](../endpoints/rooms-leaderboards-wire-shape.md),
[matchmake-v2-player-wire-shape](../endpoints/matchmake-v2-player-wire-shape.md), [player-heartbeat-wire-shape](../endpoints/player-heartbeat-wire-shape.md), [rooms-tags-put-wire-shape](../endpoints/rooms-tags-put-wire-shape.md),
[playercheer-create-wire-shape](../endpoints/playercheer-create-wire-shape.md), [roomcomments-wire-shapes](../endpoints/roomcomments-wire-shapes.md),
[matchmaking-invite-wire-shape](../endpoints/matchmaking-invite-wire-shape.md), [matchmaking-vrmovementmode-wire-shape](../endpoints/matchmaking-vrmovementmode-wire-shape.md),
[rooms-experience-wire-shape](../endpoints/rooms-experience-wire-shape.md) (its POST half), [playerevents-v2-wire-shape](../endpoints/playerevents-v2-wire-shape.md) (the per-field PUTs).
GET-only notes ([algorithmiclists-wire-shape](../endpoints/algorithmiclists-wire-shape.md), which first pinned `ELHKHFJEHLM`, and the rest)
remain correct as written.

**A route that builds params with `String.Format` into the path** — e.g.
[roomkeys-v1-room-wire-shape](../endpoints/roomkeys-v1-room-wire-shape.md)'s `?roomId=` — is a genuine query string regardless of verb, because
it never touches `ELHKHFJEHLM`.

**How to apply:** when reading a route, check the verb first. `ELHKHFJEHLM` on a GET = query;
on anything else = form body. A server binding these should accept `[FromForm]` for non-GET routes.
