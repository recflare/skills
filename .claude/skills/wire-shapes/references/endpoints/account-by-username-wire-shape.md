# `GET account?username=` — account lookup by username

> `GET accounts.<host>/account?username=<name>` (svc 11 Accounts) is Rec Room's
> **GetAccountByUsername**. It returns a **bare single `RecNet.Account`** (no envelope, not an
> array), the send is **response-required**, and the result is **cached**. Return a non-2xx (404) for
> an unknown username — never an empty/null/`{}` body, which the client reads as `Malformed Response`.

Derived **2026-11-09** on `C:\Games\recflare-2026`, build **20260323.14**. RVAs are 2026-specific.
Service enum per [recnet-service-enum](../conventions/recnet-service-enum.md): **Accounts = 11**
(`mov r8d, 0xB`), which picks the `accounts.` subdomain. Shape companion:
[account-dto](account-dto-wire-shape.md) (the `RecNet.Account` record itself).

## Route — `RecNet.Accounts$$XPTBOAVVOMW` `0x9423EB0`

- Route literal `'account'` `0xFE06BE8`; one query param **`username`** `0xFDC8E88`, added by
  `RGBOOBRDHEB$$NJPEKLKCVCG` `0x9537F80` (verb-dependent adder → **query string on GET**).
- Request built via `Entry$$.ctor` `0x8BBF9E0` with service `0xB`. **GET**, no body.
- **Response-cached**: wrapped in `RGBOOBRDHEB$$ORUUDATDRUN` `0x9538790` (`RecNet.Cache`) — repeat
  lookups of the same username replay the cached result and fire **no** request, so a capture after
  the first lookup shows nothing. Relaunch between server-side attempts.
- Failure log literal `'Failed to GetAccountByUsername'` `0xFC64498` (passed to the **log decorator**
  `KGLKSSUUEOH::XXATRYZHEBX`, `T→T` — **not** the envelope collapse `FQWUEPYTLAQ`, so the route is
  BARE).

## Response — bare single `RecNet.Account`

Send helper is `RGBOOBRDHEB$$ZWUODKCINOA` (**response-required**, generic inst #1144 =
`RecNet.Account`), so a null / empty / `{}` body is a hard `Malformed Response` on this build
(every 2026 object formatter returns null for `{}` —
[empty-json-object-deserializes-to-null](../conventions/empty-json-object-deserializes-to-null.md)).

Formatter `Utf8Json.Formatters.RecNet.AYTPNVJBFUD` `0x8EE6390` (`Deserialize` confirmed via `msig`).
Wire keys in serialize order — **13, unchanged from the 2025 Account DTO** (re-confirmed on 2026):

| # | key (wire) | type | notes |
|---|---|---|---|
| 1 | `AccountId` | long | |
| 2 | `UserName` | string | serialized from the `RawUsername` field |
| 3 | `DisplayName` | string | |
| 4 | `DisplayEmoji` | string | |
| 5 | `ProfileImage` | string | serialized from `RawProfileImage`; the computed `ProfileImage`/`Username` props carry no key |
| 6 | `BannerImage` | string | |
| 7 | `TreatAsJunior` | bool | |
| 8 | `HasBirthday` | bool | |
| 9 | `PersonalPronouns` | int | identity **bitmask** |
| 10 | `IdentityFlags` | int | identity **bitmask** |
| 11 | `createdAt` | string (date) | **lowercase** `[DataMember]` rename — not `CreatedAt` |
| 12 | `IsMetaPlatformBlocked` | bool | |
| 13 | `IsJunior` | bool? | back-filled by the post-deserialize hook `IULRMJBAHPG` when omitted |

Each key accepts three casings (Original / camel / lower). There is **no** `IsVerified`/badge field;
see [account-dto](account-dto-wire-shape.md) for why every "Verified" string is a different feature.

## Not-found behaviour

Because the response is required, an unknown username must be a **non-2xx (404)**, not an empty body.
The client has an `"Account does not exist"` path keyed off the HTTP failure; a 200 with `{}` or
`null` instead throws `Malformed Response` and surfaces as a boot/lookup error rather than a clean
"no such account". The 11-key `createdAt`-lowercase rename is the one easy-to-miss trap when
hand-building the body.

Related: `account/bulk` (POST, repeated `id`), `account/{accountId}` (by id) share the same
`RecNet.Account` element.
