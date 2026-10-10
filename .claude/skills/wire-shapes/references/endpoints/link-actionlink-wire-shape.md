# Link actionlink/{code} wire shape (short links / Video Partner codes)

> GET actionlink/{code} on the **LINK service (svc 12)** — `link.<host>`, not `api.<host>` — returns
> a **BARE 3-key object** `{CreatorPlayerId: int, Data: string, IsValid: bool}`.
> It is the **nullable-response** tier (`CJBFDPLCIEJ`), so a null body is tolerated at parse time.
> An action link whose type is `Influencer (6)` **is** what the UI calls a **"Video Partner Code"** —
> this route is how a scanned code resolves to the partner's account id.

Derived **2026-10-08** from build `20250718.01`.
Facade **`.CGBLJMGEBOF`** (7 methods). Service **12 = Link**
(`mov r8d, 0xC` at `0x7D06E2E`, [recnet-service-enum](../conventions/recnet-service-enum.md)).

`GET https://link.<host>/actionlink/{code}` — verb **GET** (`HttpMethod` statics `[rcx+8]` at
`0x7D06DD2`). Client entry **`CGBLJMGEBOF.KHEGPNHJDFL(string code)`** `0x7D06CF0` (+0x1D0).

Path is built by concatenation, **not** `String.Format`:

```csharp
"actionlink/" + System.Net.WebUtility.UrlEncode(code)      // literal 0xD0BF1F8, UrlEncode 0x7D06DF0
```

so the code is **URL-encoded** — grep `actionlink/` rather than a full path. Error literal
`'Failed to CheckActionLink'`. No `ELHKHFJEHLM`, no `ELKIBCPINAP`: the code is the only input.

## Response — BARE 3 keys

Send helper **`MGPBDIAGCFD.CJBFDPLCIEJ<T>`** (methodref `0x7D06E3F`) — the **nullable-response**
tier — generic inst **#14753 = `.FFMOCGDFIOC`** (typedef #22156). No envelope.

Formatter **`CMBKCBDHIBK` `.ctor 0x79ABC00`** (+0x470), `____stringByteKeys` run
`0x79ABF17`..`0x79ABFB9` — 3 keys, 1:1 with the 3 declared fields:

| # | key | CLR | off |
|---|---|---|---|
| 1 | `CreatorPlayerId` | int | 0x10 |
| 2 | `Data` | string | 0x18 |
| 3 | `IsValid` | bool | 0x20 |

```json
{ "CreatorPlayerId": 205, "Data": "…", "IsValid": true }
```

`FFMOCGDFIOC.CPOBHIECLEN` is the shared no-op `0xA60520`, so **no key is required** — every omission
lands as `0` / `null` / `false`. Note that means a `{}` response reads as **`IsValid: false`**, which
is the safe default for an unknown code, but also means a server that forgets `IsValid` silently
rejects every valid link.

⚠️ **The response carries no `Type`.** `CreatorPlayerId` is the account that created the link and
`Data` is the opaque payload; the link's *kind* is not on this route's wire shape. The client passes
the expected kind **in** on the consume call instead (below).

## The rest of the facade

```
static KPIPLFECKNC<.MBMBLLCJCAP> ECNLKOBJMEE()
static KPIPLFECKNC<.ShortLinkData> KNOKFJPFNNO(string code)
static KPIPLFECKNC<string>        JEODFELAKDI(.ShortLinkData data)
static KPIPLFECKNC<.FFMOCGDFIOC>  KHEGPNHJDFL(string code)                        # CHECK - this note
static KPIPLFECKNC<string>        LDMPGBHNMNO(string data, int, int?, .KPKPPPNJNMD, long?)   # CREATE
static KPIPLFECKNC<.FFMOCGDFIOC>  GKALGCCIEEA(string code, int?, .KPKPPPNJNMD, bool, bool)   # CONSUME
```

Error literals pin the three verbs: `'Failed to CheckActionLink'` (`KHEGPNHJDFL`),
`'Failed to ConsumeActionLink'` (`GKALGCCIEEA` `0x7D06740`), `'Failed to CreateActionLink'`
(`LDMPGBHNMNO` `0x7D07210`). **Check and Consume share the same response DTO**; Create returns a bare
string (the new code).

Two more DTOs, both with unobfuscated-ish shapes:

| type | formatter | keys |
|---|---|---|
| **`.ShortLinkData`** (name survived) | `KMAJGCGANEI` `.ctor 0x79B6D30` | `FullLink`, `ReferrerId`, `Type` |
| `.MBMBLLCJCAP` | `EKPHGHFDAJM` `.ctor 0x79AE920` | `FreshnessSeconds`, `Url` |

## `.KPKPPPNJNMD` — the action-link type enum

typedef #22155, `int`:

| val | name | val | name |
|---|---|---|---|
| -1 | `Unknown` | 3 | `Club` |
| 0 | `Friend` | 4 | `PlayerEvent` |
| 1 | `Referral` | 5 | `Room` |
| 2 | `Meetup` | **6** | **`Influencer`** |
| | | 7 | `Photo` |

This is the `Type` of `.ShortLinkData` and the type argument of Create/Consume. **`Influencer 6` is
the Video Partner code type** — see below.

## ⚠️ "Influencer" in code == "Video Partner" in the UI

The partner program is the **influencer** partner program; the player-facing wording is *Video
Partner*. The user-visible strings make the mapping unambiguous:

| literal | addr |
|---|---|
| `'the Video Partner Program'` | `0xD0DDEF0` |
| `'Select Video Partner'` | `0xD24F568` |
| `"You're already supporting this Video Partner!"` | `0xD258228` |
| `'Please select a Video Partner to support first.'` | — |
| **`'This is a {0} Code, not a Video Partner Code!'`** | `0xD1E7C18` |
| `'video_partner_code'` (analytics key) | `0xD1F0830` |
| `'https://recroom.com/partners'` | — |

**`RRUI.Data.SupportInfluencerDialogModel.KJIKLILMPOK`** `0x26DAA00` (+0x210) is the validator. It
loads the **`.KPKPPPNJNMD` TypeInfo** (`0x26DAA2D`/`0x26DAB59`) and emits one of three refusals:

```
'This is a {0} Code, not a Video Partner Code!'   # wrong KPKPPPNJNMD type - {0} is the actual type
"You're already supporting this Video Partner!"
"You can't support yourself!"                     # compares against the local account
```

So the flow a short code drives is:

1. `GET link.<host>/actionlink/{code}` → `{CreatorPlayerId, Data, IsValid}`.
2. The dialog checks the link's type is `Influencer (6)` and that `CreatorPlayerId` is neither the
   local account nor the already-supported one.
3. `POST api/influencerpartnerprogram/support` with form field `influencerAccountId =
   CreatorPlayerId` → valueless envelope ([influencerpartnerprogram](influencerpartnerprogram-wire-shape.md)).

**For a self-hosted server:** a Video Partner code lookup must return the partner's account id as
`CreatorPlayerId` with `IsValid: true`. Getting `IsValid` wrong, or returning `0` for
`CreatorPlayerId`, produces the "not a Video Partner Code" / "can't support yourself" refusals rather
than any network error.

## There is no "partner" flag on the account

Checked explicitly ([account-dto](account-dto-wire-shape.md)): the 13-key Account DTO has **no**
influencer/partner/verified field. Partner status is carried in two other places:

- the **JWT `role` claim** containing `influencer` — `PCGJFHLIGAC.DIFENANFJCD("influencer")` at
  `0x7D176CC` ([jwt-role-privilege-claims](../conventions/jwt-role-privilege-claims.md));
- server-side membership, exposed by `GET api/influencerpartnerprogram/influencers` as
  `{InfluencerIds, ContinuationToken}`.

Who a player *supports* is `GET api/influencerpartnerprogram/myinfluencer` → a **bare integer**, with
`0` as the "supporting nobody" sentinel. Changes arrive by the `InfluencerSupportedUpdate` push
(payload `.JKBAKBGEGFI`, facade `ONDILCNHMJD`).

Also in this family but unrelated to partners: `ActionLinkImpl`, and the handler-dispatch log lines
`'HandleActionLink: '` / `'HandleActionLink: No handler for ActionType: {0}'` — the latter names the
`.KPKPPPNJNMD` value when a link type has no registered client handler, which is the log line to grep
if a code resolves but nothing happens.
