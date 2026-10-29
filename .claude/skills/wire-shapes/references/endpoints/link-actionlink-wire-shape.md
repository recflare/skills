# Link actionlink/{code} wire shape (short links / Video Partner codes)

> GET actionlink/{code} on the **LINK service (svc 12)** — `link.<host>`, not `api.<host>` — returns
> a **BARE 3-key object** `{CreatorPlayerId: int, Data: string, IsValid: bool}`.
> It is the **nullable-response** tier (`CJBFDPLCIEJ`), so a null body is tolerated at parse time.
> An action link whose type is `Influencer (6)` **is** what the UI calls a **"Video Partner Code"** —
> this route is how a scanned code resolves to the partner's account id.

> ⚠️ **Everything above the "2026" heading at the bottom is from build `20250718.01`.** On
> `20260323.14` the facade and three of the four DTOs have **real names** and the RVAs all re-rolled —
> see [the 2026 section](#-2026-20260323141-post-actionlink-create-and-the-renamed-facade) for the
> mapping and for `POST actionlink`. The **wire shapes and the enum values are unchanged**.

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

# ⚠️ 2026 (`20260323.14`): `POST actionlink` (create) and the renamed facade

Derived **2026-10-20**. The 2025 facade `.CGBLJMGEBOF` is now **`RecNet.Link`**, and the DTOs are
de-obfuscated:

| 2025 | 2026 |
|---|---|
| `.CGBLJMGEBOF` | **`RecNet.Link`** |
| `.FFMOCGDFIOC` | **`RecNet.ActionLinkDTO`** (typedef #22376) |
| `.KPKPPPNJNMD` | **`RecNet.ActionLinkCodeType`** (typedef #22375) |
| `.MBMBLLCJCAP` | **`RecNet.PageViewDTO`** |
| `.ShortLinkData` | `.ShortLinkData` (unchanged) |

`ActionLinkDTO` is still the same 3 fields at the same offsets (`CreatorPlayerId` 0x10,
`Data` 0x18, `IsValid` 0x20), and `ActionLinkCodeType` still
`Unknown -1 · Friend 0 · Referral 1 · Meetup 2 · Club 3 · PlayerEvent 4 · Room 5 · Influencer 6 · Photo 7`.

```csharp
static MPVTAJGPRUT<RecNet.PageViewDTO>   Link.PCFSUMOMNAY()
static MPVTAJGPRUT<.ShortLinkData>       Link.XFCMAHWWEAE(string)
static MPVTAJGPRUT<string>               Link.OKKOSSBNMKW(.ShortLinkData)
static MPVTAJGPRUT<RecNet.ActionLinkDTO> Link.EOOPELZINEK(string code)                 # CHECK  0x94D91B0
static MPVTAJGPRUT<string>               Link.ZIMIYJQSFBE(string data, int validHours,
                                             int? maxCount, ActionLinkCodeType codeType,
                                             long? extraDataId)                        # CREATE 0x94D9DB0
static MPVTAJGPRUT<RecNet.ActionLinkDTO> Link.TFGIBUBGQKL(string id, int? setValidHours,
                                             ActionLinkCodeType codeType, bool newPlayer,
                                             bool newInstall)                          # CONSUME 0x94D96F0
```

## The COMPLETE 2026 Link (svc 12) surface — 6 routes, nothing else

Enumerated **2026-10-20** from all 7 `RecNet.Link` methods (`.cctor` plus the six senders).
`RecNet.Link` is the only facade on service 12.

| facade | verb | path | error literal | send helper → T |
|---|---|---|---|---|
| `ZIMIYJQSFBE` `0x94D9DB0` | **POST** (`+0x20`) | `actionlink` | `Failed to CreateActionLink` | `ZWUODKCINOA` → **`string`** (#862) |
| `EOOPELZINEK` `0x94D91B0` | **GET** (`+0x08` @ `0x94D928F`) | `actionlink/` + `UrlEncode(code)` | `Failed to CheckActionLink` | **`LIRIDCJIGGA(bool, ct)`** → `ActionLinkDTO` (#19124) |
| `TFGIBUBGQKL` `0x94D96F0` | **POST** (`+0x20` @ `0x94D9856`) | `actionlink/` + `UrlEncode(id)` + **`/consume`** (3-arg `Concat` `0x94D988D`) | `Failed to ConsumeActionLink` | `LIRIDCJIGGA(bool, ct)` → `ActionLinkDTO` (#19124) |
| `OKKOSSBNMKW` `0x94D9370` | — | `datalink`, param `data` | `Failed to GetOrCreateDataLinkId` | `ZWUODKCINOA` → `string` |
| `XFCMAHWWEAE` `0x94D9A80` | — | `datalink/` + id | `Failed to CheckDataLink` | `LIRIDCJIGGA(bool, ct)` → **`RecNet.DataLinkDTO`** (#23053) |
| `PCFSUMOMNAY` `0x94D9570` | — | `pageview/consume` | `Failed to ConsumePageView` | `LIRIDCJIGGA(bool, ct)` → **`RecNet.PageViewDTO`** (#19144) |

Two corrections to earlier revisions of this note:

1. ⚠️ **CHECK and CONSUME are the NULLABLE tier**, `RGBOOBRDHEB.LIRIDCJIGGA(bool, CancellationToken)`
   — *not* the plain `ZWUODKCINOA` that CREATE uses. Only CREATE and the datalink create are plain.
   So an empty/`null` body is tolerated at parse time on CHECK, but **not** on CREATE.
2. ⚠️ **CONSUME is `POST actionlink/{id}/consume`**, not `actionlink/{id}`, and it sends **`id`
   again as a form field** alongside `validHours`, `codeType`, `newPlayer`, `newInstall`
   (`NJPEKLKCVCG` sites `0x94D98E1`, `0x94D9933`, `0x94D996A`, `0x94D99A1`, `0x94D99DF`).

### ⚠️ `actionlink/<anything>` is always CHECK — the segment is the CODE, not a sub-resource

`EOOPELZINEK` builds its path as plain concatenation, **not** `String.Format`:

```
0x94d92ad: call System.Net.WebUtility$$UrlEncode
0x94d92bf: call System.String$$Concat          ; "actionlink/" + UrlEncode(code)
```

There is **no** other literal beginning `actionlink` in the build — `grep` over
`out/stringliteral.json` returns exactly two (`'actionlink'` `0xFE13400`, `'actionlink/'`
`0xFE13748`). So any `GET actionlink/<segment>` your server sees is a **code lookup** whose code is
`<segment>`, however route-like the segment looks. If the segment is not a code your server issued,
the string was handed to the client from somewhere outside the binary (a deep link, a pasted URL via
`ActionCode.ActionUrlToCode` `0xF4D5E0`, or a server/config value) — **check it against the raw
literal set before assuming a missing endpoint.**

## `POST actionlink` — verb, service, params

Route literal **`'actionlink'`** `0xFE13400` (no `String.Format`, no trailing slash — the
`'actionlink/'` literal `0xFE13748` belongs to CHECK and CONSUME only).

```
0x94d9f9a: mov  rax, <HttpMethod klass>
0x94d9fa1: mov  rcx, qword ptr [rax + 0x20]   ; static fields (2026 offset)
0x94d9fa5: mov  rsi, qword ptr [rcx + 0x20]   ; +0x20 = POST
0x94d9fbc: mov  r8d, 0xc                      ; service 12 = Link
0x94d9fd0: call Entry$$.ctor
```

Five params, all through **`NJPEKLKCVCG(string, object)`** `0x9538270` — the **verb-dependent**
adder ([elhkhfjehlm-verb-dependent-params](../conventions/elhkhfjehlm-verb-dependent-params.md)) — so on POST they all land in a
**form-urlencoded body**, in this call order:

| # | field | CLR | site |
|---|---|---|---|
| 1 | `data` | string | `0x94D9FF7` |
| 2 | `validHours` | int | `0x94DA02C` |
| 3 | `maxCount` | `int?` | `0x94DA061` |
| 4 | `codeType` | `ActionLinkCodeType` (numeric) | `0x94DA096` |
| 5 | `extraDataId` | `long?` | `0x94DA0D2` |

```
POST /actionlink
Content-Type: application/x-www-form-urlencoded

data=<opaque>&validHours=168&codeType=5
```

⚠️ **The two nullable fields are absent, not empty, when null.** Boxing a `Nullable<T>` with
`HasValue == false` yields `null`, and `NJPEKLKCVCG` `0x9538350` bails on a null value
(`test rbx, rbx / je 0x95385B0 → mov rax, rsi; ret`) without adding the parameter. There is no
`HasValue` branch at the call site — all five are boxed and passed unconditionally — so
`maxCount` / `extraDataId` simply do not appear in the body. **Treat both as optional.**

## Response — a BARE JSON STRING

Send is **`RGBOOBRDHEB.ZWUODKCINOA<T>`** with generic inst **#862 = `string`** — the plain tier, so
**no envelope** ([2026-send-helper-tiers](../conventions/2026-send-helper-tiers.md)). The whole body is the new code as a
JSON string:

```json
"ABC123"
```

**The quotes are required** — Utf8Json's `string` formatter wants a String token, so a bare
unquoted `ABC123` fails to parse. An empty body raises
`RecNetMalformedResponseException: Response was empty` before any caller sees it.

**Return the code only, not a URL.** Callers wrap it into `.CodeAndUrl` (typedef #11173:
`Code`, `Url`, `ChatMessage`, `DeepLink`, `Context`) and build `Url`/`DeepLink` themselves from
`StorefrontConfig`-sibling `ShareBaseUrl` on `GET api/config/v2`
([gameconfig-v2-roomkeyconfig](gameconfig-v2-roomkeyconfig.md), field at `0x50`). Returning a full URL here yields a
double-prefixed link.

Re-verified **2026-10-20**: `ZWUODKCINOA<T>(CancellationToken) → Task<T>` (`msig RGBOOBRDHEB`), and
**every** wrapper in the chain is instantiated over `string` — `SAXZOKINUQZ::CTZMMSFIPBH` `0x94DA0F2`,
`KGLKSSUUEOH::XXATRYZHEBX` `0x94DA12A`, all `method=862`. Nothing in the facade turns it into an
object or an envelope. Control case: **`POST api/sanitize/v1`**
([sanitize-v1](sanitize-v1-wire-shape.md)) is the same bare-string tier and is already working in production.

## 🔍 If the client "does nothing" after a correct `"CODE"`

A wrong body shape **is not silent on this route.** The facade wraps the promise in
`KGLKSSUUEOH.XXATRYZHEBX(promise, RecRoom.Log, "Failed to CreateActionLink")`, and the rejection
closure `NECAAMUHRKL.AMKBCLLJLUR` `0x942F5E0` calls **`RecRoom.Log::LIBCEQYQFAM`** (`0x942F702`).

**So grep `Player.log` for `Failed to CreateActionLink` first.** That one line splits the problem:

| | meaning | next step |
|---|---|---|
| line **present** | the body was rejected (malformed, `204`, empty, non-200) | the logged exception names which |
| line **absent** | the request never left the client, **or** it parsed fine and the failure is downstream | check whether the server even logged the `POST` |

**If the server never saw the POST, it is the promise cache.** `TCLCQNCIIAT` `TryGetValue` at
`0x94D9F22` caches the **promise object**, rejected ones included, keyed by
`.CreateActionLinkData{data, maxCount, validHours}` — all three identical across retries of the same
share. One failed attempt therefore poisons every later press **in that process**, with no HTTP and
no log. **Restart the client between server-side fixes on this route.**

⚠️ **Watch for a double-encoded body.** The correct body is the six bytes `"ABC123"` — one JSON
string. If the server JSON-serialises a string that *already* contains its quotes it emits
`"\"ABC123\""`, which parses **successfully** into a code containing literal `"` characters: the
request 200s, nothing logs, and the share URL is garbage. A stray leading quote (`""ABC123"`) is
instead invalid JSON and throws. Check the raw response bytes, not the framework's view of them.

There is **no `MPVTAJGPRUT.Transform` inside the facade** (unlike CHECK/CONSUME) — the raw string is
what `ZIMIYJQSFBE` resolves with. The *callers* then chain two transforms of their own, e.g.
`RoomCode.Create` `0xF64F50`:

```
Link.ZIMIYJQSFBE(...)                              // MPVTAJGPRUT<string>
  .Transform<.CodeAndUrl>(.CodeAndUrl::EBESUVQFPGF)      // 0xF651F5 — string -> .CodeAndUrl
  .Transform<.CodeAndUrl>(.VBVXDSOHTWJ::LZVNVSUGUSS)     // 0xF65236
```

`.CodeAndUrl` is a **struct** (typedef #11173; unboxed `Code` 0x00, `Url` 0x08, `ChatMessage` 0x10,
`DeepLink` 0x18, `Context` 0x20). `Url` comes from `ActionCode.ActionCodeToUrl(code)` `0xF4D560` →
`LinkManager.GetAbsoluteShareUrl()` `0xF59ED0`, which reads `RecNet.Config` but **falls back to the
hardcoded literal `'https://rec.net/{0}'`** — so a missing `ShareBaseUrl` cannot null this out, and
is *not* a candidate cause.

## ⚠️ The create result is cached client-side, and the key omits `codeType`

`ZIMIYJQSFBE` consults `RecRoom.NoEngine.DataStructures.Caching.TCLCQNCIIAT<K,V>` with generic inst
**#22700 = `['.CreateActionLinkData', 'MPVTAJGPRUT<string>']`** — `TryGetValue` at `0x94D9F22`,
`set_Item` at `0x94DA15E`. It caches the **promise**, so a repeat create is served locally with no
HTTP at all.

`.CreateActionLinkData` (typedef #22384) has only **three** fields:

```
0x10  string            data
0x18  Nullable<int>     maxCount
0x20  int               validHours
```

**`codeType` and `extraDataId` are not part of the cache key.** Two creates that differ only in
`codeType` return the first one's code. In practice `data` carries the subject id so collisions are
unlikely, but it also means **a bad code you return once is reused for the rest of the process** —
restart the client when testing this route, don't just retry.

## Callers

`RecRoom.Sharing.{ClubCode, FriendCode, MeetupCode, PlayerEventCode, ReferralCode, RoomCode}` —
`Create(object args)` → `MPVTAJGPRUT<.CodeAndUrl>`, plus `FriendCode.TRZWDJBCDYA` and
`MeetupCode.VPVLNXSDKZN`. Each passes its own `ActionLinkCodeType`, which is how one route serves
every share-code kind.

## The `data` form field is itself a DTO — `.Data`, DOUBLE-serialized

`data` is **not opaque to the client**, only to the server. It is built by
**`RecRoom.Sharing.ActionCode.GetActionLinkData(object extraJsonObject)`** `0xF4DCB0`
(bounds `..0xF4DDDE`):

```csharp
string GetActionLinkData(object extraJsonObject) {
    var d = new Data {
        ExtraJson = UnityEngine.JsonUtility.ToJson(extraJsonObject),   // 0xF4DD8E
        Platform  = PlatformManager.Instance.RTDNZHEUQME(),            // 0xF4DD64
        Type      = <this handler's ActionLinkCodeType>,
    };
    return System.Text.Json.JsonSerializer.Serialize<Data>(d);          // 0xF4DDB8
}
```

**Two different serializers.** The inner payload goes through **`UnityEngine.JsonUtility`** (plain
public fields, no `[DataMember]` renames); the outer `.Data` through **`System.Text.Json`**, whose
default encoder escapes `"` as `"`. That is why a live capture looks like:

```
data: '{"ExtraJson":"{"RoomId":1162}","Platform":0,"Type":5}'
```

`.Data` (typedef **#22380**), formatter `Utf8Json.Formatters.RecNet.PPUGPDCRKQG` `.ctor`
**`0x9609CC0`** (bounds `..0x9609F36`) — **3 keys**, 17 literal refs = 7 unique casings × 2 + 3 ✓:

| # | key | CLR | off |
|---|---|---|---|
| 1 | `ExtraJson` | string holding **Unity-JSON** | 0x10 |
| 2 | `Platform` | `RecNet.PlatformType` | 0x18 |
| 3 | `Type` | `RecNet.ActionLinkCodeType` — **duplicates the `codeType` form field** | 0x1c |

`RecNet.PlatformType` (typedef #46495, int):
`All -1 · Steam 0 · Oculus 1 · PlayStation 2 · Xbox 3 · RecNet 4 · IOS 5 · GooglePlay 6 ·
Standalone 7 · Pico 8 · Switch 9`.

### `ExtraJson` payload per `codeType`

From the `ActionCode.ParseExtraJson<T>` generic instantiation in each `*Code.Handle`:

| codeType | handler | `ExtraJson` DTO | fields |
|---|---|---|---|
| 0 `Friend` | `FriendCode` `0xF52F10` | *(none — no `ParseExtraJson`)* | |
| 1 `Referral` | `ReferralCode` `0xF64A70` | *(none)* | |
| 2 `Meetup` | `MeetupCode` `0xF5EF00` | `.MeetupData` #11200 | `RoomId` long, `SubRoomId` long |
| 3 `Club` | `ClubCode` `0xF4FDC0` | `.ClubData` #11180 | `ClubId` long, `Joinability` `ClubJoinability`, `Visibility` `ClubVisibility` |
| 4 `PlayerEvent` | `PlayerEventCode` `0xF632A0` | `.CodeData` **#11215** | `PlayerEventId` long |
| 5 `Room` | `RoomCode` `0xF65420` | `.RoomCodeData` #11224 | `RoomId` long |
| 6 `Influencer` | `InfluencerCode` `0xF54EF0` | *(none)* | |
| 7 `Photo` | `PhotoCode` `0xF626F0` | `.CodeData` **#11211** | `ImageId` long |

⚠️ **`.CodeData` is two different nested types with the same name** (#11211 `ImageId`, #11215
`PlayerEventId`). `ginst.py` prints only the name — resolve the typedef, not the string.

### The other three form fields

`RoomCode.Create` `0xF64F50` is the worked example; the call lands at `0xF651E1`:

| arg | source | note |
|---|---|---|
| `data` | `GetActionLinkData(boxed .RoomCodeData{RoomId})` `0xF65151` | |
| `validHours` | `.Configuration.validHours` (typedef **#11174**, `+0x24`; `maxUses` `+0x20`) read at `0xF65166` | a client-side per-kind config — `8760` is 365 days |
| `maxCount` | `Configuration.get_MaxUses()` `0xF5086F` → `int?` | **absent from the body** when null = unlimited |
| `codeType` | `mov r9d, 5` `0xF651C7` — same constant as `LinkManager.GetHandler(5)` `0xF65109` | |
| `extraDataId` | **`RoomDTO.get_RoomId()` a second time** `0xF65183` → `long?` → `[rsp+0x20]` `0xF651D9` | the subject id, duplicating `ExtraJson.RoomId` — the server-indexable copy |

## ⚠️ Server contract: store `data` VERBATIM and echo it back

The consume/check response's `Data` is deserialized in **`TNBERNAISKS..ctor`** `0x94E6180`:

```
0x94e623e: call System.String$$IsNullOrEmpty          ; guard
0x94e6260: call RecNet.HBEADHYKUCU::Deserialize<.Data>
```

giving `.TNBERNAISKS` (typedef #22381) — the client's parsed holder: `ANQXTWODGKJ` string (the
code), `JYCRAKAJMKS` int (the creator), two bools, and **`PNXCZCZCKQD` : `.Data`** at `+0x20`.

Then the inbound pump **`LinkManager.IFJRBXUUUMQ`** `0xF5B0A0` dispatches on the `Type` *inside that
blob* — not on anything else on the wire:

```
0xf5b18d: mov rdx, qword ptr [rax + 0x20]    ; TNBERNAISKS.PNXCZCZCKQD -> .Data
0xf5b194: je  0xf5b433                       ; null -> NRE thrower 0xc403a0
0xf5b19a: cmp dword ptr [rdx + 0x1c], -1     ; .Data.Type == Unknown?
0xf5b19e: je  0xf5b227                       ; bail: 'HandleActionLink: No handler for ActionType: {0}'
0xf5b1e2: mov eax, dword ptr [rcx + 0x1c]    ; .Data.Type -> LinkManager.GetHandler
```

So on `GET actionlink/{code}` and the consume call, **`ActionLinkDTO.Data` must be the exact string
the client POSTed**:

- **`Data: null` or `""`** → `IsNullOrEmpty` skips the deserialize, `PNXCZCZCKQD` stays null, and the
  pump **NREs** at `0xF5B194`.
- **`Data: "{}"`** → parses, but `Type` defaults to **`0` = `Friend`** (not `Unknown`), so the link
  is silently handed to `FriendCode` whatever it really was. The `No handler` log only appears if you
  store `-1`.
- **Re-serializing the blob server-side is risky** — `ExtraJson` is a *string* containing JSON, so a
  JSON library that pretty-prints, re-escapes or normalises it still round-trips, but one that
  re-parses `ExtraJson` into an object and re-emits it changes the field to an object and breaks
  `JsonUtility.FromJson<T>` on the client. Treat it as an opaque blob.

Suggested columns:

| column | source |
|---|---|
| `code` (PK) | what you return from `POST actionlink` |
| `data` text | the `data` form field, **verbatim** → `ActionLinkDTO.Data` |
| `creator_account_id` int | the authenticated caller → `ActionLinkDTO.CreatorPlayerId` |
| `code_type` int | the `codeType` form field — for your own indexing and consume validation |
| `extra_data_id` bigint null | the `extraDataId` form field — the subject id |
| `expires_at` | `now() + validHours` |
| `max_count` int null / `use_count` int | the `maxCount` form field; drives `IsValid` |
| `is_valid` bool | → `ActionLinkDTO.IsValid` (omitting it reads as **false** — see above) |

`code_type` and `extra_data_id` are **redundant with the blob** (`.Data.Type` and
`ExtraJson.<subject>Id`); keep them as columns anyway, because the blob is the only thing the client
reads and you do not want to parse it to answer "every link for room N".
