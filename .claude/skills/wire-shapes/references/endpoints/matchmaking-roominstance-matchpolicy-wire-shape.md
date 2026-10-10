# Matchmaking roominstance/{id}/matchpolicy wire shape

> PUT roominstance/{roomInstanceId}/matchpolicy (svc 4 Matchmaking) has **NO response shape** — the
> send helper is `CNDMDLNHDLI`, so the body is ignored entirely. Any 2xx works.
> It carries exactly one param, `policy`, the 3-member enum `.FDLHIHKECMA`
> (`Default 0`, `Avoid 1`, `Ignore 2`) — and because the verb is PUT, that param is an
> **`application/x-www-form-urlencoded` body**, not a query string.

Derived **2026-10-07** from build `20250718.01`.

`PUT https://match.<host>/roominstance/{roomInstanceId}/matchpolicy` — service **4 = Matchmaking**
(`mov r8d, 4` at `0x7D39D31`), verb **PUT** (`HttpMethod` statics `[rcx+0x28]` at `0x7D39CAB`).

Path is `String.Format("roominstance/{0}/matchpolicy", roomInstanceId)`, whole-path template literal
**`0xD18FA68`**.

Client entry **`RecNet.Matchmaking.CJFJLLFPIPB(.FDLHIHKECMA policy)`** `0x7D39BA0` (+0x290):

```
static .JCFICNGFDLA CJFJLLFPIPB(.FDLHIHKECMA policy)
```

⚠️ **The room-instance id is not a parameter.** The method takes only the policy; the id comes from
`RecNet.Matchmaking.HOGBJEEMMIP()` (the current game session, called twice at `0x7D39C3B` and
`0x7D39CD0`). So the client can only ever set the policy for the instance it is **currently in** —
there is no way for it to target another instance, and a server can safely validate that the path id
matches the caller's live session.

Callers: `LPPOIOFEDHM.MoveNext` `0x11A7D00` and the tail-jump wrapper
`MCGKBPKCGMB.CJFJLLFPIPB` `0x7D34910`. Error literal:
**`"Failed to modify current room's matchmaking policy state"`**.

## Response — IGNORED

Send helper is **`MGPBDIAGCFD.CNDMDLNHDLI`** at `0x7D39D7D` — the **no-response** tier. There is no
`T`, no formatter and no shape to match.

Return **any 2xx**; `{}`, `204` and a full object are all equivalent to the client.

- **`IONCMJIACFI` cannot fire** — nothing parses the body, so an empty body is safe.
- **`LLCLDPPAGIJ` cannot fire** — no envelope, so `Success`/`Error` are not read. A rejection has to
  be a **non-2xx status code**; `{"Success": false}` with a 200 reads as success.
- The declared return `.JCFICNGFDLA` is the valueless task type, so the caller has no value to
  inspect either.

Same tier and same consequences as [api-images-v1-report](api-images-v1-report-wire-shape.md),
[rooms-v1-verifyrole](rooms-v1-verifyrole-wire-shape.md) and
[consumables-v1-v2-routes](consumables-v1-v2-routes-wire-shapes.md)'s `updateActive` / `consume`.

## Request — one param, in a FORM BODY

`slots2025.py` over the whole method shows exactly **one** `MGPBDIAGCFD.ELHKHFJEHLM` (at
`0x7D39D67`) and **zero** `ELKIBCPINAP`. The param name is the literal **`'policy'`**
(`0x7D39D57`).

Because the verb is **PUT**, `ELHKHFJEHLM` puts it in an `application/x-www-form-urlencoded`
**body**, not the query string — see
[elhkhfjehlm-verb-dependent-params](../conventions/elhkhfjehlm-verb-dependent-params.md). Bind it with `[FromForm]`.

```
PUT /roominstance/1319580/matchpolicy
Content-Type: application/x-www-form-urlencoded

policy=Avoid
```

The overload taken is `ELHKHFJEHLM(string name, object value)` — the enum is **boxed** (the
`TypeInfo 0x8` loaded at `0x7D39D42`, immediately before the `'policy'` literal) and then
stringified. For an `int`-backed enum that is `Enum.ToString()`, i.e. the **member name**
(`Default` / `Avoid` / `Ignore`), the same way `OAANAMJCIDA.Permission` carries a name rather than a
number ([rooms-subrooms-permissions](rooms-subrooms-permissions-wire-shape.md)).

⚠️ **Not byte-confirmed.** The stringification happens behind a virtual dispatch inside
`MGPBDIAGCFD.ELHKHFJEHLM` `0x7D9B420` that could not be resolved statically, so the numeric form
(`policy=1`) is not ruled out. **Accept both** — parse the value case-insensitively as an enum name
*or* as an integer. That is cheap and removes the question; a live capture settles it definitively.

## `.FDLHIHKECMA` — the policy enum (typedef #22249, `int`)

| val | name | meaning |
|---|---|---|
| 0 | `Default` | normal matchmaking — the instance accepts new players |
| 1 | `Avoid` | deprioritise this instance; matchmaking sends players elsewhere when it can |
| 2 | `Ignore` | exclude this instance from matchmaking entirely |

On the wire this enum is spelled **`MatchmakingPolicy`** — it is key #15 of the 15-key
`RoomInstance` DTO (`GGCLDGNBNLI`) that every matchmake route returns
([matchmake-v2-room](matchmake-v2-room-wire-shape.md)). **No typedef is named `MatchmakingPolicy`**; grepping the
metadata for that name finds only the wire key and the unrelated
`JILFDCOLLLA.RoomInstanceBlockedByMatchmakingPolicy = 86`, which is the join-result code the
matchmaker returns when this policy refuses a join (full table in
[matchmake-v2-player](matchmake-v2-player-wire-shape.md)).

This is how a room instance takes itself out of rotation — the "don't send me more people" control —
and it is a **state change on the instance**, not a per-player preference. The enum is also the type
of `.PNAGCNAKDLL`'s `NFDNCCOLDCM` field (the SubRoom DTO's default matchmaking policy, served by
`rooms/{0}/subrooms/{1}/default_matchmaking_policy`), so the same three values appear in the Rooms
service's subroom shape as the persisted default; this route overrides it for one live instance.

Since the response is ignored, **the client cannot tell whether the change took effect.** If the
policy must be enforced, enforce it in the matchmaker — the client will keep believing it succeeded
either way.

## Siblings on the same `roominstance/{0}/` family

All whole-path templates, none derived here:

| literal |
|---|
| `roominstance/{0}/inprogress` |
| `roominstance/{0}/markprivate` |
| **`roominstance/{0}/matchpolicy`** (this note) |
| `roominstance/{0}/refresh` |
| `roominstance/{0}/reportjoinresult` |
| `roominstance/{0}/roomCode` |

They are adjacent literals in `out/stringliteral.json`, so one grep for `roominstance/` finds the
whole set. Do not assume they share a tier — `CNDMDLNHDLI` here says nothing about the others.
