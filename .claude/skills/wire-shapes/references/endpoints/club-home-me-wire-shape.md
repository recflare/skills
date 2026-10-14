# Clubs `club/home/me` wire shape

> `GET clubs.<host>/club/home/me` (svc 15 Clubs) takes NO params and returns **ONE bare Club object**
> — the *same* 16-key DTO as [clubs-account-clubs](clubs-account-clubs-wire-shape.md), but a single object, **not** an array.
> ⚠️⚠️ **CORRECTED 2026-10-13 (third pass): `null` is REJECTED. This route requires a real Club
> object.** Two earlier revisions of this note said `null` was the intended "no home club" answer,
> on the strength of the send helper being the "nullable" tier. **A live mitmproxy capture disproved
> it** — see the section below.
> ⚠️ Cached client-side for **1 hour**.

Derived **2026-10-13** from build `20250718.01`, cross-checked against `20260323.14`. Both builds
agree on the shape; see the build-delta section at the bottom.

Fourth Clubs route derived; siblings [clubs-account-clubs](clubs-account-clubs-wire-shape.md),
[clubs-account-created](clubs-account-created-wire-shape.md), [clubs-subscription-mine-member](clubs-subscription-mine-member-wire-shape.md),
[clubs-subscription-id](clubs-subscription-id-wire-shape.md).

Service **15 = Clubs** (`mov r8d, 0xF` at `0x7CA6D79`), verb **GET** (`HttpMethod` statics
`[rcx+8]`, read at `0x7CA6D4F`/`0x7CA6D56`). Path is the whole literal `club/home/me`
(**`0xD1ED070`**) — no `String.Format`, no path segment, **no params and no body** (no
`ELHKHFJEHLM`, no `ELKIBCPINAP`).

Client entry **`LNJNCFHNBOM.GJFKIFIJOHA()`** `0x7CA6C60` (+0x250), which also carries the literal
`'Failed to GetMyHomeClub'` — that error string is what names the method.

## Response — a SINGLE bare Club, nullable

Send is **`MGPBDIAGCFD.CJBFDPLCIEJ<T>(bool)`** — the **nullable-response** tier — with generic inst
**#1269 = `.NBOMJFLBIGC`** (the Club DTO), *not* `List<NBOMJFLBIGC>`. So:

- **a JSON object** = the player's home club
- ⚠️ **`null` is NOT legal** — see below. It throws `Response was empty`.
- **`[]` or `{}` are wrong.** `[]` fails to deserialize into an object (`IONCMJIACFI`
  `Malformed Response`); `{}` parses into a Club with every field defaulted, which is worse than
  `null` because `ClubId` reads as `0` and `State` reads as `Active`.

### ⚠️⚠️ CORRECTED: `null` is rejected too — the route needs a real object

**Disproved by capture, 2026-10-13.** The server returned exactly what the previous revision of this
note asked for:

```http
HTTP/1.1 200 OK
Content-Type: application/json
Content-Length: 4

null
```

and the client still threw **`RecNetMalformedResponseException: Response was empty`** out of
`RGBOOBRDHEB.AIYNPFIEYFY<T>`. So `Response was empty` does not mean "zero-length body" — it means
**"the response produced no value"**, and a body of `null` produces no value just as a body of
length 0 does.

**The send helper's `bool` is an explicit allow-null flag, and this route passes `false`.**
`RGBOOBRDHEB.LIRIDCJIGGA<TResponse>(bool a, CancellationToken b)` is called from
`RecNet.Clubs.BNKQVMIFOKZ` `0x945EB30` at **`0x945ECDE`** with `xor edx, edx` immediately before —
`rcx` = the request, **`dl` (parameter `a`) = 0**, `r8d` = default token. The 2025 build does the
same thing: `LNJNCFHNBOM.GJFKIFIJOHA` `0x7CA6C60` calls `CJBFDPLCIEJ<T>(bool)` at **`0x7CA6E14`**,
also with `xor edx, edx`.

⚠️ **So "the nullable tier" is a property of the helper, not of the route.** Seeing
`CJBFDPLCIEJ` / `LIRIDCJIGGA` on a call site tells you nothing about whether `null` is accepted —
**read the `bool` argument at that call site.** `0` means the response must produce a value. This
invalidates the "nullable response ⇒ `null` is safe" reading wherever it appears; see the send-tier
tables in `SKILL.md` and [2026-send-helper-tiers](../conventions/2026-send-helper-tiers.md).

(The `a = false` ⇒ reject-null reading is the one consistent with the capture; `LIRIDCJIGGA` itself
is generic-shared and has no own entry in `methods.pkl`, so its body was not read. What is
*certain* is the observed behaviour and the argument value.)

### The mechanism, traced: `null` IS "empty" to this client

`RecNet.XJAFUXFVGPU.SWGLEDQGUUP()` **`0x9569D10`** is the "response has no value" predicate, and it
treats a literal `null` body as empty:

```csharp
bool SWGLEDQGUUP() {                      // on the raw response, BEFORE any deserialization
    var data = this.<body>;               // field +0x20, DisposableMemorySequence<byte>
    if (data == null)   return true;                                  // 0x9569D6C
    if (data.IsEmpty()) return true;                                  // SNLYTXZQIHA, 0x9569D82
    return SequenceEqual(data.AsSpan(), XJAFUXFVGPU.<static byte[4]>); // 0x9569DFF
}
```

That static is allocated in `XJAFUXFVGPU..cctor` `0x9569EA0` as **`mov edx, 4`** — a **4-byte**
array initialised from an RVA blob, i.e. `null`. So *null*, *empty* and *zero-length* are one
condition.

And the gate in the deserializing helper (real bounds `0x6C6C510..0x6C6C98C`, found with
`fstart.py` — it is generic-shared and has **no entry in `methods.pkl`**, which is why `mxref` on
the message literal misattributes it):

```
0x6C6C574: test esi, esi                 ; esi = throwIfEmpty
0x6C6C576: je   0x6C6C594                ;   0 -> skip the check entirely
0x6C6C587: call XJAFUXFVGPU.SWGLEDQGUUP
0x6C6C58E: jne  0x6C6C89E                ;   -> new RecNetWebException("Response was empty")
```

`throwIfEmpty` is `!allowNull` from the send call, and `club/home/me` passes `allowNull = false`.
**So on this route there is no in-body encoding for "none" at all** — not `null`, not `{}` (that
parses into a bogus club), not an empty body.

⚠️ `RecNet.Clubs.UTPEXSLGHXC(Club a)` `0x946B300` *does* null-guard its argument
(`test rdi, rdi / je 0x946B88E` at `0x946B397`), which looks like null tolerance but is unreachable
from this path — the helper throws before the continuation runs.

### ⚠️ One bad answer poisons the whole session

A proxy capture of a full sign-in + room join (2026-10-13) contains **exactly one** request to
`club/home/me`, at ~1.4 s, answered `null` — and the same session's `Player.log` then shows **six**
`Response was empty` exceptions spread over 30-95 s, all with `RecNet.Clubs.BNKQVMIFOKZ` in the
trace. So the failed/empty result is **served from `RecNet.Cache` for the full 1-hour TTL**: the
client does not retry, and every later consumer re-throws off the cached body.

Consequences worth planning around:

- the **first** answer of the session is the only one that matters;
- re-clicking the UI will not produce a new request, so **relaunch the client** between server-side
  attempts or you are testing the cache, not the fix;
- in that capture the first failure at 30.66 s was followed 0.095 s later by
  `[Platform.BootSequence] ErroredPromiseException`, i.e. this route had become the
  **boot-sequence killer** now that the consumables 404s are fixed. The boot sequence fails on its
  *first* unmet dependency, so fixing one reveals the next
  ([cv1-mappings-join-nre-2026](../../../rr-client-bringup/references/cv1-mappings-join-nre-2026.md)).

The consumers seen reaching it: `RRUI.Data.AccountModelController+AccountToCreatorClubImpl.OnModelChanged`
(so this route backs the **Creator Club** on an account), `RRUI.Data.ClubModel.RefreshInternal`,
`RRUI.Data.SessionModel.RefreshInternal` and `BrowserModelController+BrowserRouterImpl`.

### What to serve instead

"No home club" has to be signalled **out of band, with a non-2xx status.** Two options, in the
order worth trying:

**1. `404 Not Found` — try this first.** It is the idiomatic REST answer and, more to the point, it
produces a **different exception class**: `RecNetWebException` rather than
`RecNetMalformedResponseException`. `RRUI.Data.ClubModel.RefreshInternal` runs its promise through
`CWUHNXNCXSC<T>.ZISSNPREGJX(Func, Func transformErrorFunc)` — it has an explicit **error transform**
— and `RecNet.Clubs.BNKQVMIFOKZ` wraps the whole thing in
`KGLKSSUUEOH.XXATRYZHEBX<Club>(promise, log, "Failed to GetMyHomeClub")`, a log-and-continue
wrapper. So a 404 is expected to be logged as `Failed to GetMyHomeClub` and handled.
⚠️ **Not traced:** whether that `transformErrorFunc` actually recovers the UI, or only reshapes the
error. This is the strong hypothesis, not a verified path — it is a one-minute experiment, so test
it before building on it.

**2. A real 16-key Club object** — guaranteed not to throw, at the cost of inventing a club. Serve
whatever club the player is in, or a stub with a valid `ClubId`, leaving `ClubhouseRoomId` null when
there is no clubhouse:

```json
{ "ClubId": 207, "Name": "Home", "Description": null, "MainImageName": null,
  "State": 0, "CreatorAccountId": 205, "Category": null, "Visibility": 1,
  "Joinability": 0, "AllowJuniors": true, "MinLevel": 0, "MemberCount": 1,
  "IsRRO": false, "ClubChatEnabled": true, "ClubhouseRoomId": null, "ClubType": 0 }
```

⚠️ When testing this, remember the **1-hour response cache** below: a failed or empty answer can be
re-served from cache, so relaunch the client rather than re-clicking.

### ⚠️⚠️ An EMPTY BODY is not `null` — it throws, and it takes the boot sequence down

**Confirmed on a live server 2026-10-13.** A zero-length body (or a `204`) on this route throws the
2026 exception **`Response was empty`** — a *different* exception from `Malformed Response`, raised
before any formatter runs. `null` means the four ASCII bytes `null`:

```http
HTTP/1.1 200 OK
Content-Type: application/json

null
```

This matters far more than it looks. `club/home/me` is awaited by **`[Platform.BootSequence]`**, so
the throw rejects the boot promise, which makes the client **load the login screen scene on top of
the room scene** and destroy every `NetworkedSingletonMonoBehaviour` in it — ending in the
`CreateCV1MappingsTask` NRE and *"Failed to load room due to a glitch in the matrix."* See
[cv1-mappings-join-nre-2026](../../../rr-client-bringup/references/cv1-mappings-join-nre-2026.md). Whether the join actually dies is
pure timing: harmless if the rejection lands during the initial boot (the login screen is legal
there), fatal if it lands after the room scene is up.

### ✅ Observed again 2026-10-13 — it also breaks the Badges UI

A second capture, on clicking **Badges**, shows the same empty body taking out the RRUI router. The
formatted async trace gives the whole chain, caller-last:

```
RRUI.Data.RRUIEventQueue+<DelayedProcessQueueRoutine>d__17.MoveNext
  RecNet.Clubs.PWEJSUIDXZI(long clubId, bool)         -> club details, succeeds
  RecNet.Clubs.PVMWUFLLOKA(ClubDetails)
  RRUI.Data.ClubModel.OnClubDetailsUpdated(long clubId)
  RRUI.Data.ClubModel.RefreshInternal(RecNetRefreshType)
  RRUI.Data.ClubModel+<>c__DisplayClass110_0.<RefreshInternal>b__1(RecNet.ClubDetails clubDetails)
  RecNet.Clubs.BNKQVMIFOKZ()                          <- GET club/home/me
  RGBOOBRDHEB.LIRIDCJIGGA<T>(bool, ct)                <- the NULLABLE tier
  RecNet.Cache.Get<T>(service, requestUri, maxCacheAge, forceRefreshCache, callback, ct)
  -> RecNetMalformedResponseException: Response was empty
```

and the UI damage that follows ~0.1 s later:

```
[Warning] Failed to get account id to initialize model
[Error]   Unable to find AssetReference for Route: <NULL>/<NULL>
[Error]   URI load failed: Failed to get prefab reference for route <NULL>/<NULL>
[Exception] PromiseException: … NullReferenceException
             at RRUI.Data.Router+UriLoadOperation.Dispose ()
```

So an empty body here does **not** degrade gracefully: `ClubModel.RefreshInternal`'s promise
rejects, the model never initializes, `RRUI.Data.Router` resolves the page to `<NULL>/<NULL>`, and
`UriLoadOperation.Dispose()` NREs on a half-built operation. The user-visible symptom is *"clicking
Badges throws a bunch of NREs"* with no mention of clubs anywhere.

⚠️ **`LIRIDCJIGGA<T>(bool, ct)` is the nullable-response helper, and it is still not empty-tolerant.**
"Nullable `T`" means the JSON value `null` is accepted; it does not mean a zero-length body is. Those
are two different things on this build, and only one of them works.

So on this route the three "empty" answers are **not** interchangeable:
`null` ✅ · empty body ❌ throws · `204` ❌ throws · `{}` ⚠️ parses as a bogus club.

Note the contrast with its sibling: `account/{id}/clubs` is the **required-response** tier
(`HPBKMCLEANE<List<T>>`) and must serve `[]`. Envelope tier is per-helper, not per-service.

### The 16 keys

Identical to [clubs-account-clubs](clubs-account-clubs-wire-shape.md) — same formatter `MLDOEFKMDHN` `.ctor 0x7651380`,
same order, same casing. Repeated here only as a payload:

```json
{ "ClubId": 207, "Name": "My Club", "Description": "…", "MainImageName": null,
  "State": 0, "CreatorAccountId": 205, "Category": null, "Visibility": 1,
  "Joinability": 0, "AllowJuniors": true, "MinLevel": 0, "MemberCount": 12,
  "IsRRO": false, "ClubChatEnabled": true, "ClubhouseRoomId": null, "ClubType": 0 }
```

Order: `ClubId, Name, Description, MainImageName, State, CreatorAccountId, Category, Visibility,
Joinability, AllowJuniors, MinLevel, MemberCount, IsRRO, ClubChatEnabled, ClubhouseRoomId, ClubType`.
`ClubId`/`CreatorAccountId`/`IsRRO`/`ClubChatEnabled` are CodeStage `Obscured*` types but plain
numbers/bools on the wire; `State`/`Visibility`/`Joinability`/`ClubType` are numeric enums (tables in
that note); `ClubhouseRoomId` is `long?`.

For a *home* club specifically, `ClubhouseRoomId` is the field that actually matters downstream —
it is what the client resolves into a room to send the player to.

## ⚠️ Cached for 1 hour

The only extra builder call is **`MGPBDIAGCFD.DIDJOECFJII`** `0x7D9ADB0` (the response-cache TTL),
called at `0x7CA6DF7` with `.NNMGBLLLIAH` static **`+0x18`**. `NNMGBLLLIAH..cctor` `0x7CB48D0` is the
shared TTL table — `+0x00`/`+0x08`/`+0x10` are `TimeSpan.FromMinutes(…)` and **`+0x18` is
`TimeSpan.FromHours(1)`** (the constant `1.0` at image offset `0x9DDBFE0`, loaded at `0x7CB498E`).

So changing a player's home club server-side will not show up for up to an hour. Relaunch the client
when testing. (This is the same table and the same slot that 2026 calls `RecNet.Cache.ZQATVLASZAW` —
see [paintball-battle-pass](paintball-battle-pass-wire-shapes.md).)

## Three other methods reference the same literal

`mxref` on `0xD1ED070` returns four methods, only one of which is the GET:

| method | role |
|---|---|
| `LNJNCFHNBOM.GJFKIFIJOHA` `0x7CA6C60` | **the GET** derived here |
| `LNJNCFHNBOM.IHCKEIDDJEL` `0x7CA9000` | the companion **setter** (2026: `GKZUQBRIXCZ(long?)`, a valueless promise — so it writes and returns no body) |
| `<>c.IFPNNCNEKFD` `0x7CBDF00` | a lambda, 0xC0 bytes |
| `IAGLONIBNFB.CAINDKPDMMN` `0x7CD1CE0` | 0xD0 bytes — cache invalidation by URL key |

The last one matters practically: the 1-hour TTL **is** explicitly bustable from inside the client,
so a home-club change made *through the client* refreshes immediately while one made directly in the
database does not.

## Build delta — `20260323.14`

Unchanged in substance. On 2026 the facade is **`RecNet.Clubs`** and the DTO keeps its real name:

```
static Task<RecNet.Club>  BNKQVMIFOKZ()            # GET club/home/me
static NXPIPFBMDQY        GKZUQBRIXCZ(long? a)     # the setter, no response body
```

`RecNet.Club` has the same 16 fields in the same order, and formatter
`Utf8Json.Formatters.RecNet.WFUFAZXIHKO` `.ctor 0x9139D20` (+0xAF0) emits the same 16 keys ending in
`ClubType`.

⚠️ **One naming trap.** On 2026 the seventh property is renamed **`PrimaryTag`**, but the **wire key
is still `Category`** — `PrimaryTag` does not exist as a string literal anywhere in the 2026 binary,
while `Category`/`category` do, and the formatter's key run has `Category` in slot 7. (`primaryTag`
*is* a literal, but it belongs to an unrelated method, `OFYRLOBOYPO.YJDMGQMDBME` `0x28D9550`.) So it
is a `[DataMember]` rename: **do not start emitting `PrimaryTag` for the 2026 client.** This is the
formatter-is-the-authority rule paying off.
