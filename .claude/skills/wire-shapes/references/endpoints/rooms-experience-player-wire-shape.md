# Rooms experience/player wire shape (room XP, per player)

> GET rooms/{roomId}/experience/player (svc 16 Rooms) returns a **BARE 3-key object**
> `{RoomExperienceEnabled: bool, Experience: int?, ConcurrencyCode: Guid?}` — **not** the
> `{Enabled, DailyLimit}` config that `rooms/{id}/experience` one level up returns.
> The POST on this same path is **ENVELOPED** around the same DTO.
> `ConcurrencyCode` is the optimistic-concurrency token the XP-award POST echoes back; omit it and
> the client logs *"Room Experience Concurrency Code for Room {0} is not cached"*.

Derived **2026-10-07** from build `20250718.01`. Facade **`.JOOBKACKLJE`** (9 methods) — the whole
`/experience` family lives here, and [rooms-experience](rooms-experience-wire-shape.md) covers the
`{Enabled, DailyLimit}` config route it is easy to confuse this with.

`GET https://rooms.<host>/rooms/{roomId}/experience/player` — service **16 = Rooms**
(`mov r8d, 0x10` at `0x7DB4EAC`), verb **GET** (`HttpMethod` statics `[rcx+8]` at `0x7DB4E5B`).

Path is `String.Format("{0}/{1}/experience/player", "rooms", roomId)` — assembled from a hardcoded
`'rooms'` literal plus the template, so **grepping for `rooms/{0}/experience/player` finds nothing**;
grep `/experience/player`.

Client entry **`JOOBKACKLJE.BPMPLEMPMHF(long roomId, CancellationToken)`** `0x7DB4D90` (+0x160);
`JOOBKACKLJE.JGDCPDEBPPO` `0x7DB5350` is a 0x70 literal-free tail-jump wrapper onto it, not a second
route.

**No params, no body** — `slots2025.py` over the whole method shows **zero** `ELHKHFJEHLM` and zero
`ELKIBCPINAP`. The room id is the only input and it is a path segment.

## Response — BARE 3-key object

Send helper `MGPBDIAGCFD.HPBKMCLEANE<T>` (**response required**), generic inst **#2859 =
`.KBOCGEMKEOL`** (typedef #22844) — no envelope. Formatter **`DADFCOIDFIB` `.ctor 0x765DE70`**
(+0x470), `____stringByteKeys` run `0x765E187`..`0x765E229` — 3 keys, 1:1 with the 3 declared fields
in offset order:

| # | key | CLR | off |
|---|---|---|---|
| 1 | `RoomExperienceEnabled` | bool | 0x10 |
| 2 | `Experience` | **`int?`** | 0x14 |
| 3 | `ConcurrencyCode` | **`Guid?`** | 0x1c |

```json
{ "RoomExperienceEnabled": true,
  "Experience": 1250,
  "ConcurrencyCode": "a16bfd31-ffb9-46ac-a199-362c163130c0" }
```

`KBOCGEMKEOL.CPOBHIECLEN` is the shared no-op `0xA60520`, so **every key is omittable** and there is
no post-deserialize validation. `{}` parses — but see the caveats below for what that costs.

`Experience` and `ConcurrencyCode` are **nullable**, so `null` is a legal value for both and is
distinct from `0` / an empty Guid. Utf8Json wants the plain 36-char dashed form for the Guid.

## ⚠️ Two routes called `experience`, three different shapes

| route | verb | entry | wire `T` |
|---|---|---|---|
| `rooms/{id}/experience` | GET | `OPOLMNDLBND` `0x7DB5630` | `.PBOOAFNIPBL` — bare `{Enabled, DailyLimit}` |
| `rooms/{id}/experience` | POST | `FIOCOBOOIAA` `0x7DB4F60` | `JFNAKFCGDAO` — valueless envelope |
| **`rooms/{id}/experience/player`** | **GET** | `BPMPLEMPMHF` `0x7DB4D90` | **`.KBOCGEMKEOL` — bare, this note** |
| `rooms/{id}/experience/player` | POST | `GBMHNIPLKGF` `0x7DB5150` | **`KGOJLHJNIOD<.KBOCGEMKEOL>` — enveloped** |
| `rooms/{id}/experience/coOwner` | POST | `KMLGJHNBELM` `0x7DB53C0` | `KGOJLHJNIOD<.KBOCGEMKEOL>` — enveloped |

Both POSTs are **POST** (`[rcx+0x20]` at `0x7DB524C` / `0x7DB54BC`), and both carry params through
`ELHKHFJEHLM`, which on a non-GET means an **`application/x-www-form-urlencoded` body**, not a query
string ([elhkhfjehlm-verb-dependent-params](../conventions/elhkhfjehlm-verb-dependent-params.md)):

| route | params |
|---|---|
| POST `.../experience/player` | `increment` (int), `concurrencyCode` (`Guid?`) |
| POST `.../experience/coOwner` | `targetExperience` (`int?`), `concurrencyCode` (`Guid?`) |

So the same path serves a **bare** DTO on GET and the **enveloped** one on POST. The envelope
formatter is `LMMNJHAPMNA` `.ctor 0x766C930`, run `0x766CC4A`..`0x766CD37` — `Value`, `Success`,
`Error`, lowercase `error_id`, in that order:

```json
{ "Value": { "RoomExperienceEnabled": true, "Experience": 1255,
             "ConcurrencyCode": "…" },
  "Success": true, "Error": null, "error_id": null }
```

Returning the bare object from the POST raises `LLCLDPPAGIJ`
([llcldppagij-envelope-failure-exception](../conventions/llcldppagij-envelope-failure-exception.md)); returning the envelope from the GET
fails in the formatter instead, because `Value`/`Success` are not keys of `.KBOCGEMKEOL`. Do not
share one handler across the two verbs.

## What the fields are for

- **`RoomExperienceEnabled`** mirrors the room-level `Enabled` from
  [rooms-experience](rooms-experience-wire-shape.md). `false` turns room XP off for this player in this room.
- **`Experience`** is the player's XP in this room. The POST's `increment` is a delta, and the
  enveloped response carries the post-award total — so the server, not the client, owns the sum.
  Contrast `targetExperience` on the coOwner route, which is **absolute**, not a delta.
- **`ConcurrencyCode`** is an optimistic-concurrency token. The client caches whatever the GET
  returns and sends it back as `concurrencyCode` on the award POST; the log line *"Room Experience
  Concurrency Code for Room {0} is not cached"* fires when it has none. Both the param and the field
  are `Guid?`, so **`null` is wire-legal** — a server that does not implement concurrency can return
  `null` and ignore the inbound value. If you *do* return one, return a fresh one from each POST or
  the client will keep replaying a stale token.

Because `CPOBHIECLEN` is the no-op stub, a `{}` response does not throw — it reads as
`RoomExperienceEnabled: false` with null XP, which silently disables room XP and leaves the
concurrency code uncached. That is the most likely way to get "room XP does nothing" with no error
anywhere.
