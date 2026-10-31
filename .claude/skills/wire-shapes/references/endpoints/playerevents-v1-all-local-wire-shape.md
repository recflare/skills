# `GET api/playerevents/v1/all` (no id) — the LOCAL player's events, bare `{Created, Responses}`

> ⚠️ **This is a different route from [`api/playerevents/v1/all/{accountId}`](playerevents-v1-all-wire-shape.md).**
> Both literals ship on `20260323.14` and both deserialize into the **same** DTO, but the bare one
> takes **no id** — it is `GetLocalPlayerEventInfo`, scoped to the bearer token.
> **GET**, svc **2 API**, **no query params, no body, no request-builder action.**
> Response is a **BARE OBJECT** `{"Created": [...], "Responses": [...]}` — no envelope.
> ⚠️ **`"Responses": null` throws** on 2026 (it is fed to `Enumerable.Select` unguarded in the
> cache-insert step); `"Created": null` and a wholly `null` body are tolerated. **Send `[]`.**

Derived **2026-10-29** from build `20260323.14`. The `{accountId}` sibling was derived on
`20250718.01` in [playerevents-v1-all](playerevents-v1-all-wire-shape.md); the shape still holds,
with the 2026 differences recorded below.

## Which literal is which

`grep` for `playerevents/v1/all` matches **two** distinct string literals on 2026:

| literal | addr | facade | original name |
|---|---|---|---|
| `api/playerevents/v1/all` | **`0xFC5AB40`** | `BFKPNJRKYIX.ZSDEJDRDPAO(CancellationToken)` **`0x96185C0`** | **`GetLocalPlayerEventInfo`** |
| `api/playerevents/v1/all/{0}` | `0xFC5AE90` | `BFKPNJRKYIX.QKCOTUSXWUB(int accountId, CancellationToken)` `0x9616F40` | `GetRemotePlayerEventList` |

Both return `Task<RecNet.Events.LocalPlayerEventInfo>`, so the **response body is byte-identical in
shape** — the only difference is the scope of the data and the absent path segment. ⚠️ The remote
one takes an **`int`** accountId, not a long.

Each literal has 4 refs: the facade method, plus the `RecNet.Events.Client` wrapper's closure
(`<<GetLocalPlayerEventInfo>b__59_0>d$$MoveNext` `0x962F7E0` /
`<<GetRemotePlayerEventList>b__0>d$$MoveNext` `0x9631110`), which **builds the request itself**
rather than calling the facade method — which is why both appear twice.

## Route

| what | value | evidence |
|---|---|---|
| path | `api/playerevents/v1/all` | whole-path literal, **no `String.Format`** |
| verb | **GET** | `0x961864A`: `mov rcx,[rax+0x20]` (HttpMethod statics) → `0x9618674 mov rdx,[rcx+8]` = **`+0x08`** |
| service | **2 = API** | `mov r8d, 2` at `0x9616C8D` inside `NJDXKMQCUTD` (see below) |
| params | **none** | the `Action<RGBOOBRDHEB> requestBuilderAction` arg is `mov qword [rsp+0x20], 0` at `0x961866B` — **null** |
| body | **none** | same — the builder action is the only way this facade adds params or a body |

### How the 2026 Events facade builds requests

`RecNet.Events.BFKPNJRKYIX` is a **rewrite**: every route goes through one generic helper instead of
per-route send calls.

```csharp
Task<T> Get<T>(HttpMethod method, string route, CancellationToken ct, Action<RGBOOBRDHEB> requestBuilderAction)
RGBOOBRDHEB NJDXKMQCUTD(HttpMethod, string route, Action<RGBOOBRDHEB>)   // 0x9616C70
```

`NJDXKMQCUTD` invokes the `.Factory` delegate handed to the facade's `.ctor` with
**`r8d = 2` (API)** hard-coded (`0x9616C8D`), then applies `requestBuilderAction` to the request
**only if non-null** (`0x9616CA7 test rbx,rbx; je`). So on this facade:

➡️ **`requestBuilderAction == null` ⇒ the route has no params, no body, no headers, full stop.**
That is one `rangedis` instead of hunting for `NJPEKLKCVCG`/`FZNGWUAGAIN` call sites, and it is the
fastest way to triage any of the facade's 30-odd routes. A null `.Factory` NREs at `0x9616C80`.

## Response — bare object

```json
{ "Created": [ { …PlayerEvent… } ],
  "Responses": [ { "PlayerEvent": { …PlayerEvent… },
                   "PlayerEventResponse": { "PlayerEventResponseId": 900001,
                                            "PlayerEventId": 134, "PlayerId": 205,
                                            "CreatedAt": "2026-10-29T00:00:00Z", "Type": 0 } } ] }
```

`T` is `RecNet.Events.LocalPlayerEventInfo` — methodSpec generic inst **#3171**, confirmed with
`ginst`. Formatter **`Utf8Json.Formatters.RecNet.Events.ZFZVCHUZLUI`** `.ctor` **`0x8F41340`**
(`msig`-confirmed), key run `0x8F41495` / `0x8F414C1`:

| # | key | CLR |
|---|---|---|
| 1 | `Created` | `List<RecNet.Events.PlayerEvent>` |
| 2 | `Responses` | `List<RecNet.Events.PlayerEventInformation>` |

Only **two** casings exist per key (`Created`/`created`, `Responses`/`responses`) — for a
single-word key Utf8Json's camelCase and all-lowercase forms coincide.

**Bare, not enveloped**, on two independent checks:

- The **envelope oracle** ([2026-send-helper-tiers](../conventions/2026-send-helper-tiers.md)):
  `RecNetResultObject_LocalPlayerEventInfo` does not exist — and in fact **not one** of the 74
  `RecNetResultObject_*` instantiations on this build names any `RecNet.Events` type, so the whole
  facade is bare.
- Structurally: `ZSDEJDRDPAO` routes through `Get<T>`, which carries **no leading
  `friendlyActionDescription` string**. The facade's two helpers that *do* take one
  (`QCRHMYXCMAX(string, HttpMethod, …)` `0x9616CD0`, `MSBYXMTYOOH(string, HttpMethod, …)`
  `0x9616B10`) are the enveloped pair — the same tell as the 2025 facades. Even `CreateEvent`
  `0x96158C0` uses plain `Get<T>`.

An **empty body** still fails (`T` is a reference type the continuation dereferences); `{}`
deserializes fine, since both keys are omittable.

### ⚠️ `"Responses": null` throws — this is new on 2026

The 2025 build validated this tree in four null-tolerant `CPOBHIECLEN` hooks. On 2026 **none of the
three types has a post-deserialize hook at all** (`msig` on `LocalPlayerEventInfo`,
`PlayerEventInformation` and `PlayerEventResponse` shows only `.ctor` plus accessors — no
`IULRMJBAHPG`, no `EMSIIQRWASQ`). That work moved into the `Client` cache-insert step, which is
**not** uniformly null-tolerant:

**`RecNet.Events.Client.AYOUXIIIMLG(LocalPlayerEventInfo)` `0x9618FE0`** — called from the wrapper
closure at `0x962F9C0` on the raw deserialized object, with no null check at the call site:

```
0x961906e  test rbx, rbx ; je 0x96192f2      ; whole DTO null  -> clean skip  ✔
0x9619077  mov  rdi,[rbx+0x10]               ; Created
0x9619095  call 0x9619300                    ; AYOUXIIIMLG(IReadOnlyList<PlayerEvent>)
             └─ 0x9619351 test rdi,rdi ; je 0x9619487   ; Created null -> clean skip  ✔
0x961909a  mov  rsi,[rbx+0x18]               ; Responses
0x961913f  mov  rcx, rsi                     ; ...straight in as the LINQ source
0x9619142  call 0x3a91870                    ; System.Linq.Enumerable::Select (methodSpec #10405,
                                             ;   selector <>c::BXOUKCFDQJL)  -- NO null guard  ✘
```

`Enumerable.Select(null, selector)` raises **`ArgumentNullException`**; the `test rax,rax` right
after is IL2CPP's routine check on the returned iterator, not tolerance for a null source. The
throw lands in the async continuation **after** a fully successful parse, so it presents as a
stackless exception with no HTTP error and no deserialize error — the classic "the route 200s and
the events page is empty" signature.

➡️ **Serve `[]` for both lists.** `Created` is genuinely safe as `null` and the whole object is
safe as `null`, but there is no reason to rely on that asymmetry.

## The element DTOs — unchanged from 2025, now unobfuscated

| 2025 | 2026 |
|---|---|
| `.CPHNJLLFJEB` (wrapper) | **`RecNet.Events.LocalPlayerEventInfo`** |
| `.NEMBNIGCMFK` (event) | **`RecNet.Events.PlayerEvent`** |
| `.HALOCGHCLFE` (pair) | **`RecNet.Events.PlayerEventInformation`** |
| `.DHOECFANGJN` (RSVP) | **`RecNet.Events.PlayerEventResponse`** |
| `KOMDDCCKBID` | `RecNet.Events.PlayerEventAccessibility` |
| `GAHAEEIJGGE` | `RecNet.Events.PlayerEventBroadcastPermissionsMode` |
| facade `BPHIJNEOCMK` | `RecNet.Events.BFKPNJRKYIX` (+ a `RecNet.Events.Client` cache layer above it) |

**`PlayerEvent` — 17 keys, formatter `Utf8Json.Formatters.RecNet.Events.GKOPOASIIMX` `.ctor`
`0x8F2D900`**, key run `0x8F2E23E`…`0x8F2E4DE`. Names, order and types are **identical** to the
2025 note, so that table stands verbatim: `PlayerEventId` (long), `CreatorPlayerId` (**int**),
`RoomId` (long), `SubRoomId` (long?), `ClubId` (long?), `Name`, `Description`, `ImageName`,
`StartTime`, `EndTime` (DateTime), `AttendeeCount` (int), `Accessibility`, `IsMultiInstance`,
`SupportMultiInstanceRoomChat` (bool), `DefaultBroadcastPermissions`,
`CanRequestBroadcastPermissions`, `BroadcastingRoomInstanceId` (long?).

**There is still no `Tags` key** — `ftypes` gives exactly 17 fields. The v2 Tags requirement
([playerevent-tags-build-difference](playerevent-tags-build-difference.md)) does not reach this
route; a `Tags` key here is silently dropped.

**`PlayerEventInformation`** — formatter `YXBDKSPDTQX` `.ctor` `0x8F40C00`, 2 keys **`PlayerEvent`**
/ **`PlayerEventResponse`**. **`PlayerEventResponse`** — formatter `FAUZTBBOLVY` `.ctor` `0x8F2B960`,
the 5 keys above.

Enums re-checked on 2026 and **identical**:

| enum | members |
|---|---|
| `PlayerEventAccessibility` | `Private 0`, `Public 1`, `Unlisted 2` |
| `PlayerEventBroadcastPermissionsMode` | `None 0`, `RoomOwners 256`, `All 2147483647` — sparse, never `1`/`2` |
| `PlayerEventResponseType` | `None -1`, **`Yes 0`**, `Interested 1`, `No 2`, `Pending 3` |

⚠️ `PlayerEventResponseType` keeps its trap: **`Yes` is `0`**, so an omitted `Type` reads as an
accepted RSVP.

## Consumers

`RecNet.Events.Client` (typedef #23743) mirrors the facade's method names one layer up and is where
caching happens. `Client.ZSDEJDRDPAO()` is `GetLocalPlayerEventInfo` (state machine
`<GetLocalPlayerEventInfo>d__59$$MoveNext` `0x9629800`), and it returns
`MPVTAJGPRUT<List<PlayerEvent>>` — i.e. the client layer **discards `Responses`** for its own
callers after feeding both lists to the cache. `Client.QKCOTUSXWUB(int, Predicate<PlayerEvent>)` is
the remote equivalent and additionally filters.

So `Responses` exists on the wire purely to populate the RSVP cache in `AYOUXIIIMLG` — which is
exactly the step that throws on `null`.
