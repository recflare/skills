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

## A bare trailing `?` is normal and carries nothing

Added **2026-10-07**, after a capture of `GET rooms/112/experience/player?` — a route with **zero**
`ELHKHFJEHLM` calls — raised "is there a query param I'm missing?".

The query string is assembled by **`MGPBDIAGCFD.ADJPJGNMMLM() -> string`** `0x7D9A9B0` (+0x1A0):

```
joined = String.Join("&", params)                 # 0x7D9AAEE, the '&' literal in rsi
if (path.Contains('?'))                           # 0x7D9AAFF: mov edx, 0x3F ; String.Contains
    return String.Concat(path, "&", joined)       # 0x7D9AB1A
else
    return String.Concat(path, "?", joined)       # 0x7D9AB40
```

Two things follow:

- **The concat is unconditional** — there is no "params is empty" guard in this method. With an empty
  collection, `String.Join` returns `""` and the result is literally `path + "?"`. So a trailing `?`
  with nothing after it means **the param list was empty**, not that a parameter was dropped.
- **The separator is chosen by `path.Contains('?')`, not by position.** A path that already carries a
  `?` from its own `String.Format` template gets `&` for the first real param. That is why
  [itemwishlists-v1-routes](../endpoints/itemwishlists-v1-routes-wire-shapes.md) can produce `...?True` from a format string and
  still append params correctly — the two mechanisms compose.

**How to apply:** server-side, treat a trailing `?` as an empty query string and do not 400 on it.
When auditing a capture, a bare `?` is not evidence of a parameter — count the `ELHKHFJEHLM` calls in
the entry method instead.

## The same mechanism on the 2026 build: `RGBOOBRDHEB.NJPEKLKCVCG`

Confirmed **2026-10-13** on build `20260323.14`. The request builder is now
**`RecNet.RGBOOBRDHEB`** (2025's `MGPBDIAGCFD`), and the parameter adder is
**`NJPEKLKCVCG`** `0x9537F80`, which does the identical verb test:

```
r14 = this.<HttpMethod>  ; field +0x10, same offset as 2025
al  = HttpMethod.op_Equality(r14, HttpMethod.get_method)   ; statics +0x08, at 0x9538022
r9  = &this[+0x28]                                         ; 0x9538030
test al, al                                                ; then pick the other list
```

So the rule carries over unchanged: **GET → query string, every other verb → form-urlencoded body.**

Two differences worth knowing:

- **There are three adders, not one.** `msig.py RGBOOBRDHEB` shows `NJPEKLKCVCG`, `ZTKGODPCQRW` and
  `KTGGWMNSEXK` with identical `(string name, <value>)` overload sets (string / `DateTime` /
  `IReadOnlyList<T>` / `object`). Only `NJPEKLKCVCG` has been read; **which of the other two is the
  query-only or header variant is not established**, so do not assume a route's params are
  verb-dependent just because *an* adder was called — disassemble the one at the call site.
- **The response-cache TTL setter is `ORUUDATDRUN(TimeSpan, bool)`** (2025's `DIDJOECFJII`), and the
  shared TTL constants live on `RecNet.Cache` — `.cctor` `0x9444C20` sets `+0x00` 1 min, `+0x08`
  5 min, `+0x10` 10 min, `+0x18` **1 hour**, `+0x20` 24 hours. A route that sets one caches its
  response client-side for that long; see [paintball-battle-pass](../endpoints/paintball-battle-pass-wire-shapes.md).

**How to apply:** unchanged for GET-vs-other. When reading a 2026 route, get the verb from
`[HttpMethod statics + N]` at the `RGBOOBRDHEB..ctor` call site (`0x00` delete, `0x08` get, `0x10`
head, `0x18` options, `0x20` post, `0x28` put, `0x30` trace) — the service enum is the `r8d`
immediate on that same call, because the per-service factory `NJDXKMQCUTD` bakes it in.

---

## ⚠️ 2026: there are THREE param families, not one — two of them IGNORE the verb

Established **2026-10-13** from build `20260323.14`, after a live request to
`POST api/consumables/v1/query/bulk` showed **`?configurationVersion=2` in the URL** while
`descriptors` sat in the form body — i.e. two params on the **same POST** went to **different
places**. ([consumables-v1-query-bulk](../endpoints/consumables-v1-query-bulk-wire-shape.md))

`RecNet.RGBOOBRDHEB` (2026's `MGPBDIAGCFD`) keeps the same two collections —
`GXDEVTXLNLF` **`+0x28`** and `ODWNBEXQFEH` **`+0x30`** — and **which collection is which is now
proven**, from the verb branch in the bare `NJPEKLKCVCG` `0x9537F80`:

```
rdx = [[HttpMethod TypeInfo + 0x20] + 8]     ; HttpMethod.Get  (statics +0x08)
al  = HttpMethod.op_Equality(this.Method, Get)        ; 0x9538022
r9  = &this[+0x28]                                    ; 0x9538030  default
test al, al                                           ; 0x9538034
jne  0x9538053                                        ; 0x953804D  IS GET -> keep +0x28
r9  = &this[+0x30]                                    ; 0x953804F  NOT GET -> switch
call NJPEKLKCVCG(name, value, parameters, bool, bool) ; 0x9538053  explicit-list overload
```

GET's destination is `+0x28`, so:

| `+0x28` `GXDEVTXLNLF` | **QUERY STRING** |
|---|---|
| `+0x30` `ODWNBEXQFEH` | **FORM-URLENCODED BODY** |

And the three families are all thin wrappers over the same explicit-list overload
`NJPEKLKCVCG(name, value, List<KeyValuePair<string,string>> parameters, …)`, differing **only** in
which list they hand it:

| family | passes | behaviour |
|---|---|---|
| **`NJPEKLKCVCG`** (bare, `0x9537F80`) | branches on the verb | **verb-dependent** — GET→query, else→body. The rule at the top of this file. |
| **`ZTKGODPCQRW`** (`0x9539050`, `0x9539080`, `0x95390D0`) | `lea r9, [rcx + 0x28]` | ⚠️ **ALWAYS QUERY STRING**, even on POST/PUT |
| **`KTGGWMNSEXK`** (`0x9537D70`, `0x9537D90`, `0x9537DC0`) | `lea r9, [rcx + 0x30]` | ⚠️ **ALWAYS FORM BODY**, even on GET |

Each family has the same three overloads — `(string, string)`, `(string, DateTime)`,
`(string, IReadOnlyList<T>)`, `(string, object)` — so they are easy to mistake for one another in a
slot dump. **Read the method name, not just the param literal.**


### The two trailing `bool`s on the string overload are *skip-if-blank* gates

Added **2026-10-26** from
[account-recoverpassword](../endpoints/account-recoverpassword-wire-shape.md). All three families'
`(string name, string value, …)` overloads forward to the explicit-list overload
**`NJPEKLKCVCG`** **`0x9538080`**, whose head is:

```
0x95380f1  test rdi, rdi                  ; value == null        -> skipped UNCONDITIONALLY
0x95380f4  je   0x95381d0
0x95380fa  cmp  byte [rsp+0x70], 0        ; arg4 (bool)          -> if set, skip when
0x9538106  call System.String$$IsNullOrEmpty                     ;   IsNullOrEmpty(value)
0x9538113  cmp  byte [rsp+0x78], 0        ; arg5 (bool)          -> if set, skip when
0x953811f  call System.String$$IsNullOrWhiteSpace                ;   IsNullOrWhiteSpace(value)
```

So the signature reads `NJPEKLKCVCG(string name, string value, bool skipIfNullOrEmpty,
bool skipIfNullOrWhiteSpace)`.

**How to apply:** read the two immediates at the call site. With **both `false`** — the common case,
e.g. `ResetPassword` at `0x94E1484` — an **empty or whitespace string is still transmitted**, so the
server receives a present-but-empty field (`email=`) rather than a missing one, and must validate it
itself. A `null` value is dropped either way, so a param that is absent from a live capture does not
prove the client never adds it.

### How to avoid the mistake this note exists for

In a `slots2025.py` dump the adder appears either as a resolved `call -> RecNet.RGBOOBRDHEB$$<NAME>`
or as a `MethodRef RecNet.RGBOOBRDHEB::<NAME>` (for the generic `IReadOnlyList<T>` overloads, which
are generic-shared). **Grepping only for `NJPEKLKCVCG` and finding nothing does not mean the params
are verb-dependent — it means you have not found the adder yet.** That is exactly how this note's
subject route was first mis-specified as all-form-body.

### Blast radius — small, and enumerated

`callxref` on all six force-a-side RVAs:

- **`ZTKGODPCQRW`** — 13 direct sites, all in: `RecNet.HKIQYNCZHCQ.QSUKOMULOOV` (6),
  the Game AI routes `<DescribeImage_GameAI>d__65`/`d__66`, `<EditImage_GameAI>d__67`,
  `<GenerateImage_GameAI>d__69`, `<GenerateMeshRequestFromImage>d__61`,
  `<GetConsumableDefinitions>d__35`, `<QuerySuperStageIngredient>d__10`.
- **`KTGGWMNSEXK`** — 1 direct site, `<SuperStageIngredient>d__11`.
- **`NJPEKLKCVCG`** bare — **237** sites.

So the verb-dependent rule still covers the overwhelming majority, and **no other route currently in
[CATALOG.md](../CATALOG.md) is among the force-a-side callers** — the existing notes stand.

⚠️ **The `KTGGWMNSEXK` count is an undercount.** The `IReadOnlyList<T>` overloads are generic-shared,
so a call reached through a methodSpec (as `descriptors` is in `d__35`, via inst #862) is invisible
to `callxref`, which scans direct `call rel32` only. Treat 1 as a floor, not the total.

## The generic `IReadOnlyList<T>` overload — verb-dependent too, and it REPEATS the key

Read **2026-10-28** from [inventions-v2-batch](../endpoints/inventions-v2-batch-wire-shape.md).
`NJPEKLKCVCG<T>(string name, IReadOnlyList<T> values)` **`0x3E51520`** was previously only known to
exist. It is not a side-forcing overload — it makes the same verb test as the bare one:

```
0x3e515b2  mov rax,<HttpMethod statics> ; mov rdx,[rax+0x20] ; mov rdx,[rdx+8]   ; HttpMethod.Get
0x3e515bc  mov rcx,r14                  ; r14 = request->JLFBPBGZQJS (verb field, +0x10)
0x3e515c7  call HttpMethod::op_Equality
0x3e515dc  lea r9,[rdi+0x28]            ; GXDEVTXLNLF = query-string list
0x3e515e8  jne 0x3e515ee                ; verb == GET -> keep +0x28
0x3e515ea  lea r9,[rdi+0x30]            ; otherwise   -> ODWNBEXQFEH = form-urlencoded body list
```

then hands the chosen list to the explicit-list overload **`0x3E51350`**, which is a plain
`for (i = 0; i < values.Count; i++)` that **boxes each element and calls the single-value
`NJPEKLKCVCG(string, object, List<KVP>)` `0x9538350` once per element** (`0x3E514AE`, back-edge
`0x3E514B9`).

➡️ **A list parameter goes on the wire as the key repeated**, `id=1&id=2&id=3` — never
`id=1,2,3`, never a JSON array, never `ids=`. A null list adds nothing at all
(`0x3E51382 test rbx,rbx; je`), so the parameter is simply absent rather than empty.

## Batch routes choose GET or POST from the item count — so BOTH verbs are live

Same source. The batch/bulk service calls do not have a fixed verb. They call

```
RecNet.HBEADHYKUCU.GCPOFRCEWMT(int count, int threshold) -> HttpMethod   0x9551FC0
  0x9551ff1  cmp edi, ebx ; jge …                  ; count >= threshold ?
  0x955203b  [statics+0x20]+0x08 -> HttpMethod.Get   ; count <  threshold
  0x9552099  [statics+0x20]+0x20 -> HttpMethod.Post  ; count >= threshold
```

with `count` read off the id collection (interface slot 0 = `get_Count`) and `threshold` a literal
`mov edx, 0x64` = **100** at the only site read so far. Combined with the rule above, that means one
route serves **two different request encodings**:

| count | request |
|---|---|
| 1 … 99 | `GET <path>?id=1&id=2…` |
| ≥ 100 | `POST <path>` · `application/x-www-form-urlencoded` · `id=1&id=2…` |

⚠️ Two consequences for the server. **Route both verbs to the same handler and read the ids from
query *or* form**, or the rare large batch breaks in a way no amount of small-batch testing shows.
And **do not take a captured POST as the route's verb** — a packet capture taken while a big batch
flushed is what makes a route look POST-only.

The batch family is enumerable: `callxref` on `RGBOOBRDHEB.NUIBPXHZBHT()` **`0x9538730`** (which
every one of them calls, to set the `Nullable<int>` `SITKKODGYPP` at `+0x58` to 2) gives **26** sites
on `20260323.14`, and their state-machine names are unobfuscated — `GetAccountsBulkServiceCall`,
`GetInventionsBulkServiceCall`, `GetCurrentOutfitsBulkServiceCall`, `GetSavedOutfitsServiceCall`,
`GetUGCPurchasableItemsByIdsServiceCall`, `GetPurchaseOffersForCurrencyBatchAsync`,
`GetSimpleSummariesOfInstancesOfRooms`, and so on. Assume the pattern for all of them; confirm
before writing any one of them down.
