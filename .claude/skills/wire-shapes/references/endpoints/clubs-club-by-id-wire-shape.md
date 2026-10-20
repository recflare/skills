# GET club/{clubId} wire shape — and why a missing club must be a 404

> `GET club/{clubId}` (svc **15 Clubs**) returns a **BARE `RecNet.Club`** (the same 16-key DTO as
> `account/{id}/clubs`). For a club that does not exist, **return `404`, never `200` with an empty
> payload.** `200 {}` deserializes into a perfectly valid `Club` with `ClubId = 0` and `Name = null`
> and the client's promise **resolves successfully** — nothing validates it, so the UI renders a
> club that isn't there. A `404` is a first-class handled outcome on this route.

Derived **2026-10-15** from build `20260323.14`, answering "404 or 200 with an empty payload?".

## The route

`GET https://clubs.<host>/club/{clubId}` — service **15 = Clubs**, facade `RecNet.Clubs`.
Path is `String.Format("club/{0}", clubId)`, literal slot **`0xFD1DF70`**.

```
static RecRoom.Async.MPVTAJGPRUT`1<RecNet.Club> RecNet.Clubs.ROIHLCPPLIA(long clubId, bool b)
                                                                            0x946a110
```

- **Verb GET** — `HttpMethod` statics `[+0x08]`, read at `0x946a3a9`.
- Send is **`RGBOOBRDHEB.ZWUODKCINOA<RecNet.Club>`** (generic inst **#1181 = `RecNet.Club`**) — the
  **plain** send, *not* the nullable `LIRIDCJIGGA<T>(bool)` tier. There is no allow-null option on
  this route at all, so `null` is not a representable answer
  ([2026-send-helper-tiers](../conventions/2026-send-helper-tiers.md)).
- The other method holding the same literal is `Clubs.BNBADEJNTFJ(long, string) -> NXPIPFBMDQY`
  `0x945e8d0` (the valueless promise), i.e. the write on the same path.

### It checks two client caches first

`ROIHLCPPLIA` calls `RecRoom.NoEngine.DataStructures.Caching.TCLCQNCIIAT<K,V>::TryGetValue` **twice**,
with instantiations **#22693 = `<long, RecNet.Club>`** and **#22695 = `<long, RecNet.ClubDetails>`**.
So a club already fetched through `club/{id}/details` satisfies a `club/{id}` request without any
HTTP. The `bool b` parameter sits next to that logic (cache bypass / force refresh); its exact
polarity is **not** derived.

## Response — bare `RecNet.Club`

`RecNet.Club` is **unobfuscated** on 2026, and so are all its accessors. 16 wire members:

```
ClubId(long)  Name  Description  MainImageName  State(ClubState)  CreatorAccountId(int)
PrimaryTag  Visibility(ClubVisibility)  Joinability(ClubJoinability)  AllowJuniors(bool)
MinLevel(int)  MemberCount(int)  IsRRO(bool)  ClubChatEnabled(bool)
ClubhouseRoomId(long?)  ClubType(ClubType)
```

Same DTO and key set as [clubs-account-clubs](clubs-account-clubs-wire-shape.md) — which also records
that four members are CodeStage `Obscured*` types that are plain numbers/bools on the wire, and that
`State` is a sparse enum whose omitted value reads as `Active`. ⚠️ 2026 renames the **property**
behind key #7 to `PrimaryTag` while the **wire key stays `Category`** — see
[club-home-me](club-home-me-wire-shape.md).

## ⚠️ `200 {}` is the dangerous answer: nothing validates it

`RecNet.Club` *does* have a post-deserialize hook, `ARMIVRDLSVE` `0x945dab0`, and it is **not** the
shared no-op stub — it has a unique address and a real body. **It is still not a validator.** The
whole method re-encrypts the CodeStage fields after deserialization:

```
0x945db0c  call ObscuredLong$$OOBOIWNJMNP   ; ClubId   at +0x10
0x945db2c  call ObscuredInt$$OOBOIWNJMNP    ;          at +0x54
0x945db52  call ObscuredBool$$OOBOIWNJMNP   ;          at +0x84
0x945db57  lea  rcx, [rbx + 0x90]           ; …and so on
```

No comparison, no throw, no literal. This is exactly the trap the skill warns about: **a non-stub
hook RVA is not proof of validation — disassemble it.**

Consequence: `200 {}` yields a non-null `Club` with `ClubId = 0`, `Name = null`, `MemberCount = 0`,
`State` = `Active` (the sparse-enum default), and the promise **resolves**. `.Then(...)` fires and the
UI shows a club that does not exist, with a null name. No error, no log line, nothing to grep.

`200 null` is also wrong but at least loud: the plain `ZWUODKCINOA` send produces no value, which
raises **`RecNetMalformedResponseException: Response was empty`** (literal at `out/stringliteral.json`
line 67147) — an error that reads like a serialization bug rather than "no such club".

## ✅ `404` is a handled, non-fatal outcome

The facade does **not** return a `Task`. It returns **`RecRoom.Async.MPVTAJGPRUT<RecNet.Club>`** —
Rec Room's own promise type, whose surface (`RecRoom.Async.MRDAKWBRKMV`, 24 methods) is:

```
Then(Action)                      Error(Action<string> errorFunc)
Transform(Func<T>)                GUDOJFUBTFE(string)   // = FromError
RUJXWRYSKXH(T)                    // = FromResult
ZISSNPREGJX(Func<…>, Func<string, …> transformErrorFunc)
```

A value **or an error string** — never an unhandled throw. The bridge is

```
RecRoom.Async.SAXZOKINUQZ.CTZMMSFIPBH(Task<T>) -> MPVTAJGPRUT<T>     0x9da3a10
RecRoom.Async.SAXZOKINUQZ.KSNTDCQPEQA(Exception) -> string           0x9da3bd0
```

and `KSNTDCQPEQA`'s single literal is **`"An error occurred"`** (`0x9da3c22`) — the generic error
string the promise carries.

**Confirmed at runtime, not only statically.** The 2026 `Player.log` shows this exact chain for other
promise-backed routes:

```
RecRoom.Debugging.MHEJTCPVNYP:LogException(Exception, Object)
UnityEngine.Debug:LogException(Exception)
RecRoom.Async.SAXZOKINUQZ:KSNTDCQPEQA(Exception)
RecRoom.Async.XKMSFCDUWSV`1:IQQWXDIHGCW(Task`1)
```

with the visible messages `An error occurred` and `Error refreshing store items from source Store: An
error occurred`. So a `404` on `club/{id}` produces:

1. one `[Exception] [Unity | Error] HTTP Error 404` line (noisy, harmless — `RecNetWebException` from
   `MLREETGNUXI.VEIQCOEFCVM`),
2. the promise completing **as an error** with `"An error occurred"`,
3. any `.Error(...)` handler running; a caller that only attached `.Then(...)` simply never fires.

No crash, no NRE, no poisoned cache — a failure does not populate either `TCLCQNCIIAT`, so a later
request retries.

## Who calls it

23 call sites, all UI, so a bad club id reaches this route from a stale reference rather than from
boot: `RecRoom.ClubLinkButtonTypeController` (4 sites incl. `OnLinkTargetIdChanged`),
`RecRoom.Sharing.ClubCode.Handle`, `InviteFriendsDialog.ShowDialog`,
`AGUI.StackedUI.ClubSpecificUIBehaviour.SetClubId`, `ClubAnnouncementConditionalButton`,
`ClubAnnouncementSpecificUIBehaviour`, `EventDetailsScreen`, `RRUI.Data.ClubAnnouncementModel`
(`GetCanPerformAnnouncementAction`, `GetAnnouncementSummaryLabel`), `ClubAnnouncementCreationModel`.

## The rule

| answer | what the client does |
|---|---|
| **`404`** ✅ | promise completes as an error (`"An error occurred"`), one log line, caller's `Error` path runs |
| `200 {}` ❌ | **resolves successfully** with `ClubId = 0`, `Name = null` — silent, renders a ghost club |
| `200 null` ❌ | `RecNetMalformedResponseException: Response was empty` — an error, but a misleading one |
| `204` ❌ | same as `200 null` |

**Return `404`.** This generalises: on any route whose send is the plain `ZWUODKCINOA<T>` and whose
DTO has no validating hook, "absent" has no in-band encoding, so absence must be a status code.
