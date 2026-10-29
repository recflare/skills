# `PUT thread/{threadId}/favorite` wire shape (2026 build)

> `PUT chat.<host>/thread/{threadId}/favorite` (svc **9 Chat**) takes **`favorite` as a
> form-urlencoded BODY field** and returns a **BARE 2-key `RecNet.FavoriteChatResponse`**:
> `{"ChatResult": 0, "IsFavorited": true}`.
> ⚠️ **`IsFavorited` is authoritative, not an echo** — the client writes whatever you return into its
> cached `ChatThread`, so returning the wrong value flips the heart back.
> ⚠️ **`200 {}` reads as "Success, not favorited"** and silently un-favorites the thread.
> ⚠️ `ChatResult != 0` makes the client **ignore `IsFavorited` entirely** — no cache write, no
> thread-updated event.

Derived **2026-10-20** from build `20260323.14`.

Route literal `'thread/{0}/favorite'` **`0xFCDB730`** (`mxref` → exactly 2 refs, both in the one
method). Facade:

```csharp
static RecRoom.Async.MPVTAJGPRUT<RecNet.ChatResults>
    RecNet.MGJPJSBRWJJ.WYTTCQBUCAG(long threadId, bool favorite)     // 0x944DAC0
```

Returns `MPVTAJGPRUT<T>` — a value-or-error promise, **not** a `Task` — so a `404` is a handled,
non-fatal outcome, same as [clubs-club-by-id](clubs-club-by-id-wire-shape.md).

## Verb and service

From the request construction at `0x944DCA4`:

```
0x944dca4: mov  rax, <HttpMethod klass>
0x944dcb0: mov  rcx, qword ptr [rax + 0x20]   ; static fields  (2026 offset)
0x944dcb4: mov  rsi, qword ptr [rcx + 0x28]   ; +0x28 = PUT
0x944dcd6: call System.String$$Format          ; 'thread/{0}/favorite'
0x944dcef: mov  r8d, 9                         ; service 9 = Chat
0x944dd03: call Entry$$.ctor
```

**PUT**, service **9 Chat**. (Confirms `[klass+0x20]` as the 2026 static-fields pointer with the
inner offsets unchanged — `0x28` is still Put.)

## Request — `favorite` is a FORM field, not a query param

```
0x944dd19: call <box bool>                     ; boxes the `favorite` argument
0x944dd27: mov  rdx, <StringLiteral 'favorite'>
0x944dd37: call RecNet.RGBOOBRDHEB$$NJPEKLKCVCG
```

`NJPEKLKCVCG` is the **verb-dependent** adder (see
[elhkhfjehlm-verb-dependent-params](../conventions/elhkhfjehlm-verb-dependent-params.md)), and the verb is PUT, so:

```
PUT /thread/890/favorite
Content-Type: application/x-www-form-urlencoded

favorite=true
```

There is **no query string and no JSON body** — no `ELKIBCPINAP`/`FZNGWUAGAIN` call exists in the
method. Bind `favorite` from the body.

## Response — bare 2-key object

Send is **`RGBOOBRDHEB.ZWUODKCINOA<T>`** with generic inst **#23065 = `RecNet.FavoriteChatResponse`**
— the plain tier, so **no envelope** (see [2026-send-helper-tiers](../conventions/2026-send-helper-tiers.md)).

`RecNet.FavoriteChatResponse` (typedef **#21963**) — 2 fields, **2 wire keys**
(14 literal refs = 6 unique casings × 2 + 2 ✓). Formatter
`Utf8Json.Formatters.RecNet.OCTULJHSRLH` `.ctor` **`0x924D6F0`** (bounds `..0x924D914`),
`____stringByteKeys` run at `0x924D89E` / `0x924D8CA`:

| # | key | CLR | offset |
|---|---|---|---|
| 1 | `ChatResult` | `RecNet.ChatResults` (int enum, **numeric on the wire**) | `0x10` |
| 2 | `IsFavorited` | bool | `0x14` |

```json
{"ChatResult": 0, "IsFavorited": true}
```

No `[DataMember]` renames, no `[IgnoreDataMember]` members, and **no post-deserialize hook** —
`FavoriteChatResponse`'s only methods are the four accessors and `.ctor`.

`ChatResult` is numeric: `ThreadNotFound` and the other member names appear **zero** times in
`stringliteral.json`, so there is no by-name formatter.

### `RecNet.ChatResults` (typedef #21950, int)

```
Success 0 · InvalidArguments 1 · ThreadNotFound 2 · MembershipNotFound 3 ·
PlayerAlreadyOnThread 4 · CannotMessagePlayer 5 · InvalidCharacters 6 · RecentlyLeftThread 7 ·
ThreadTooLarge 8 · InsufficientPermission 9 · TooManyAffiliationThreads 10 · UnderModeration 11 ·
MessageNotFound 12 · InvalidThreadJoinType 13 · PlayerBanned 14 ·
CannotMessagePlayerDueToLocalPrivacySetting 15 · CannotMessagePlayerDueToRemotePrivacySetting 16 ·
SuccessWithPartialPlayersAddedToThreadDueToPrivacySetting 17 ·
CannotAddPlayersToThreadDueToPrivacySetting 18 ·
CannotConvertDirectMessageChatToGroupChatDueToPrivacySetting 19
```

## ⚠️ What the client does with the response

`MPVTAJGPRUT<FavoriteChatResponse>.Transform` runs the closure
**`ZKRDDIOPABO.IQJXECWNATC`** `0x947BEB0`:

```csharp
ChatResults Transform(FavoriteChatResponse resp) {
    if (resp.ChatResult == ChatResults.Success) {       // 0x947bee1  cmp [rbx+0x10], 0
        cachedThread.IsFavorited = resp.IsFavorited;    // 0x947bef4  ChatThread + 0x68
        MGJPJSBRWJJ.UBXOULIRSKY(cachedThread);          // 0x947bf15  thread-updated event
    }
    return resp.ChatResult;                             // 0x947bf1a
}
```

Three consequences, in order of how easily they bite:

1. **`IsFavorited` is read back, not assumed.** The client never applies the value it asked for —
   it applies yours. Echo `favorite` from the request.
2. **`200 {}` is a silent un-favorite.** A missing `ChatResult` deserializes to `0` (Success) and a
   missing `IsFavorited` to `false`, so an empty object is indistinguishable from
   "succeeded, now not favorited". The heart turns off and nothing is logged.
3. **A non-zero `ChatResult` is a no-op, not an error.** The cache write and the
   `UBXOULIRSKY` event are both inside the `== Success` branch, so the UI keeps its old state and
   the promise still *resolves* with the code. Only the caller's own handling distinguishes it.

An empty or `null` body does **not** reach the transform — the plain `ZWUODKCINOA` send raises
`RecNetMalformedResponseException: Response was empty` first.

## ⚠️ Two client-side short-circuits send NO request at all

`WYTTCQBUCAG` consults the client's own `Dictionary<long, RecNet.ChatThread>` thread cache
(generic inst **#5858 = `['long','RecNet.ChatThread']`**) before building the request:

| condition | result | HTTP |
|---|---|---|
| `!threadCache.TryGetValue(threadId, out thread)` | `ChatResults.ThreadNotFound` (**2**) — `mov ecx, 2` at `0x944DC26` | **none** |
| `thread.IsFavorited == favorite` already | `ChatResults.Success` (**0**) — `xor ecx, ecx` at `0x944DE94` | **none** |

Both return an already-resolved `MPVTAJGPRUT` via `MRDAKWBRKMV.RUJXWRYSKXH<ChatResults>(value)`.

**So if your server never sees the `PUT`, it is not a routing problem** — the thread is not in the
client's cache (fix the route that populates it, e.g. the thread list / `POST thread/party`
([chat-thread-party](chat-thread-party-wire-shape.md))), or the client already believes the thread is
in the requested state because an earlier response said so.

`RecNet.ChatThread` (typedef #21956) carries `<IsFavorited>k__BackingField` at **`+0x68`** — the only
field this route mutates.
