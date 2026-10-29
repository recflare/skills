# `announcements/club/*` — the five club-announcement routes (svc 15 Clubs)

> **`DELETE announcements/club/{clubId}/{announcementId}`** returns the **valueless envelope**
> `RecNet.RecNetResult` — exactly **three** keys, `{"Success":true,"Error":null,"error_id":null}`.
> No `Value`, no array, no bare body.
> ⚠️ **`{}` is a failure**, not a success: `Success` is a `bool` and defaults to `false`, which
> rejects the promise. **Always send `"Success": true` explicitly, and send the object — not a 204.**
> The request itself carries **no query params, no form params and no body** — both ids are in the
> path and that is all the client sends.

Derived **2026-10-22** from build `20260323.14`. The whole family lives on the obfuscation-era
**promise** facade `RecNet.Clubs` (125 methods), not the `Task` facades, so the
[2026-send-helper-tiers](../conventions/2026-send-helper-tiers.md) table reads one level in:

| promise return type | meaning |
|---|---|
| `RecRoom.Async.NXPIPFBMDQY` | **no value** — but the body is still parsed, see below |
| `RecRoom.Async.MPVTAJGPRUT<T>` | value `T` |

## The five routes

All five are **svc 15 = Clubs** (`mov r8d, 0xf` into the request `.ctor` `0x8BBF9E0`). Verbs read
from `[klass+0x20]` → the `HttpMethod` static slot (`0x00` Delete · `0x08` Get · `0x20` Post ·
`0x28` Put):

| verb | path | facade method | RVA | returns | params |
|---|---|---|---|---|---|
| GET | `announcements/club/{clubId}` | `WSTCYXVGHEQ(long clubId)` | `0x946D440` | `MPVTAJGPRUT<RecNet.ClubAnnouncementList>` | none |
| POST | `announcements/club/{clubId}` | `WDXRANKDILR(.ZIPZCPYJSWM)` | `0x946CAB0` | `MPVTAJGPRUT<long>` — the new announcement id | `title`, `body`, `imageName` |
| PUT | `announcements/club/{clubId}/{announcementId}` | `YOIPKVBIINH(.NPLBGRXTVFQ)` | `0x946E890` | `NXPIPFBMDQY` | `announcementId`, `title`, `body`, `imageName` |
| **DELETE** | **`announcements/club/{clubId}/{announcementId}`** | **`PFXAQIAXDSU(long clubId, long announcementId)`** | **`0x94676E0`** | `NXPIPFBMDQY` | **none** |
| POST | `announcements/club/{clubId}/{announcementId}/read` | `ILKGGBTAZKO(long clubId, long announcementId)` | `0x9463CA0` | `NXPIPFBMDQY` | none |

Verb evidence, in order: `[statics+0x08]` at `0x946D626` (GET) · `[statics+0x20]` at `0x946CC80`
(POST) · `[statics+0x28]` at `0x946EA3C` (PUT) · **`[statics+0x00]` at `0x94677DF`–`0x94677F3`
(DELETE)** · `[statics+0x20]` at `0x9463EC5` (POST).

⚠️ **There is NO `GET` on `announcements/club/{clubId}/{announcementId}`.** `mxref` on the literal
`announcements/club/{0}/{1}` (**`0xFC34680`**) gives exactly **4** refs = 2 methods × 2 (the
one-time-init `lea` plus the use `mov`), and those two methods are the **PUT** and the **DELETE**.
A single announcement is never fetched by id — the client only ever gets the whole list from
`announcements/club/{clubId}`. If a GET on the two-segment path shows up in server logs it is not
this client.

Route literals: `announcements/club/{0}` `0xFC34330` · `announcements/club/{0}/{1}` `0xFC34680` ·
`announcements/club/{0}/{1}/read` `0xFC349D0`. `{0}` is the **clubId**, `{1}` the **announcementId**
(`PFXAQIAXDSU` stores arg 1 at closure `+0x10` → `{0}` and arg 2 at `+0x18` → `{1}`,
`String.Format` at `0x9467834`).

## The DELETE response: `RecNet.RecNetResult`, three keys

`NXPIPFBMDQY` means *the facade exposes no value* — it does **not** mean the body is ignored. The
tail of `PFXAQIAXDSU` is:

```
0x9467863  Entry$$.ctor(request, HttpMethod.Delete, svc 15, "announcements/club/{0}/{1}", null)
0x9467879  <send>                       ; xor edx,edx = default(CancellationToken)
0x9467892  call 0x942d310               ; RecNet.KGLKSSUUEOH::FQWUEPYTLAQ
                                        ;   (MPVTAJGPRUT<RecNet.RecNetResult>) -> NXPIPFBMDQY
```

➡️ **`T` is `RecNet.RecNetResult`** — the collapse helper's parameter type *is* the deserialize
target. `FQWUEPYTLAQ` `0x942D310` reads the envelope and settles the value-less promise from it, so
`Success:false` surfaces as a rejection carrying `Error`/`error_id`.

The **same collapse** is used by the PUT (`0x946EBE1`) and the `/read` POST (`0x9463F6F`) — so all
three value-less routes on this family share this body. (`callxref` on `0x942D310` gives 36 call
sites across `RecNet.Clubs` and friends; it is the standard value-less envelope path.)

`RecNet.RecNetResult` (typedef #46515) — 3 fields, 3 wire keys, formatter
**`Utf8Json.Formatters.RecNet.VTLMXGUPIAK`** `.ctor` **`0x8E55120`** (confirmed by `msig`:
`Serialize(JsonWriter, RecNet.RecNetResult, …)`). `____stringByteKeys` runs
`0x8E552D1`…`0x8E55321`:

| # | key | CLR | off |
|---|---|---|---|
| 1 | `Success` | bool | 0x10 |
| 2 | `Error` | string | 0x18 |
| 3 | **`error_id`** | string | 0x20 — `[DataMember]` rename of `ErrorId` |

Accepted casings from `____keyMapping` (`0x8E5515A`…`0x8E55196`): `Success`/`success`,
`Error`/`error`, `error_id`/**`Error_id`**. ⚠️ **`ErrorId` (no underscore) is NOT accepted** — it
does not exist as a literal anywhere in the build. Serialize as `error_id`.

```json
{"Success": true, "Error": null, "error_id": null}
```

Failure:

```json
{"Success": false, "Error": "Announcement not found.", "error_id": "not_found"}
```

The static factories confirm the contract: `RecNetResult.Ok()` and
`RecNetResult.Fail(string error, string errorId)` — nothing else is ever set.

## Request bodies on the siblings

The PUT and the create-POST add their fields through the shared parameter adder, so per
[elhkhfjehlm-verb-dependent-params](../conventions/elhkhfjehlm-verb-dependent-params.md) they land
in an **`application/x-www-form-urlencoded` body**, not a query string (both are non-GET):

- **POST** `announcements/club/{clubId}` — `title`, `body`, `imageName`. Carrier DTO `.ZIPZCPYJSWM`
  has 5 fields (`long`, 3× `string`, `.MetaData`), so a 4th value exists client-side; only the three
  named literals reach the wire from `0x946CB7B`–`0x946CB9F`.
- **PUT** `announcements/club/{clubId}/{announcementId}` — `announcementId`, `title`, `body`,
  `imageName`. Note `announcementId` is sent **both** in the path and in the form body.

⚠️ **Not derived here**: `RecNet.ClubAnnouncementList` (the GET list's response) and the
`ClubAnnouncementType` enum — the build carries
`"Unknown ClubAnnouncementType, {0}. Falling back to Generic."` (so an unknown value degrades rather
than throwing) plus `announcementType`/`announcement_type` key literals, and the related
`announcements/mine`, `announcements/subscription/mine`,
`announcements/v2/mine/unread[?sendAnnouncements=true]`,
`announcements/v2/subscription/mine/unread[?sendAnnouncements=true]` and `api/announcement/v1/get`
routes. The `lastAnnouncementId` / `lastReadAnnouncementId` keys belong to the club/subscription
DTOs, not to these routes.
