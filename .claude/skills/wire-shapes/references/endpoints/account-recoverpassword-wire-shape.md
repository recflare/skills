# `POST account/recoverpassword` — valueless envelope, form body `email=`

> **POST** (svc **1 Auth**), request is **`application/x-www-form-urlencoded`** with the single field
> **`email`** — there is **no JSON request body and no query string**.
> Response is the **valueless envelope** `RecNet.RecNetResult` =
> **`{"Success": true, "Error": null, "error_id": null}`** — exactly three keys, no `Value`.
> ⚠️ **The body IS parsed** even though the facade exposes no value. The facade returns the
> non-generic promise `NXPIPFBMDQY`, which here is **not** the "body ignored" tier — the collapse
> helper `KGLKSSUUEOH::FQWUEPYTLAQ(MPVTAJGPRUT<RecNet.RecNetResult>)` types `T` as the envelope and
> **rejects the promise when `Success == false`**.
> ⚠️ **`{}` means `Success: false`** (bool default) and therefore a rejection. **Never 204, never an
> empty body, never `null`.**
> ⚠️ The wire key is **`error_id`**, lowercase with an underscore. **`ErrorId` is not accepted.**

Derived **2026-10-26** from build `20260323.14`.

## Route

**`RecNet.Login.ResetPassword(string email)`** **`0x94E1340`** (spans to `0x94E1530`) →
`RecRoom.Async.NXPIPFBMDQY`. The method name survives obfuscation — the whole `RecNet.Login`
facade carries plain names for this one method.

| what | value | evidence |
|---|---|---|
| path | `account/recoverpassword` | literal **`0xFE09688`**, `mxref` = exactly **2** refs, both in this method (`0x94E13CC` init `lea`, `0x94E1440` use `mov`) — **no `String.Format`, the path is the literal** |
| verb | **POST** | `0x94E1425 mov rax,[TypeInfo]` → `0x94E142C mov rcx,[rax+0x20]` (statics) → `0x94E1430 mov rdi,[rcx+0x20]` — **`+0x20` = `HttpMethod.Post`** |
| service | **1 = Auth** | `mov r8d, 1` at `0x94E1449`, into `RGBOOBRDHEB..ctor` `0x8BBF9E0` at `0x94E145D`; `RecNet.Service` (typedef #46523) `Auth = 1` — matches the `auth.<host>` subdomain |
| params | **`email`** only | `0x94E146B` loads the literal, `0x94E1484 call 0x9537F80` = `RGBOOBRDHEB::NJPEKLKCVCG(string, string, bool, bool)` |
| JSON body | **none** | no `FZNGWUAGAIN` / `YHPVSAVMRFS` / `WOGHBITUUOI` call anywhere in the method |
| response | **`RecNet.RecNetResult`** | tail `jmp 0x942D310` = the non-generic `KGLKSSUUEOH::FQWUEPYTLAQ(MPVTAJGPRUT<RecNet.RecNetResult>) -> NXPIPFBMDQY` |
| client cache | **none** | no `ORUUDATDRUN(TimeSpan, bool)` call — the request is sent every time |

### `email` rides the **form body**, not the query string

`0x9537F80` is the **bare, verb-dependent** adder (see
[elhkhfjehlm-verb-dependent-params](../conventions/elhkhfjehlm-verb-dependent-params.md)), not the
always-query `ZTKGODPCQRW` or the always-body `KTGGWMNSEXK`. The verb is POST, so the parameter goes
into `ODWNBEXQFEH` `+0x30` = **`application/x-www-form-urlencoded`**:

```
POST /account/recoverpassword
Content-Type: application/x-www-form-urlencoded

email=player%40example.com
```

#### The two trailing bools are *skip-if-blank* gates, and both are **false** here

New on 2026-10-26 — read off the explicit-list overload `NJPEKLKCVCG` **`0x9538080`**:

```
0x95380f1  test rdi, rdi                  ; value == null       -> skipped unconditionally
0x95380f4  je   0x95381d0
0x95380fa  cmp  byte [rsp+0x70], 0        ; arg4 (bool)         -> if set, String.IsNullOrEmpty -> skip
0x9538106  call System.String$$IsNullOrEmpty
0x9538113  cmp  byte [rsp+0x78], 0        ; arg5 (bool)         -> if set, IsNullOrWhiteSpace -> skip
0x953811f  call System.String$$IsNullOrWhiteSpace
```

`ResetPassword` passes **`false, false`** (`r9d` xor-zeroed at `0x94E1472`, `[rsp+0x20] = bl = 0` at
`0x94E1480`). So an **empty or whitespace email is still transmitted** as `email=` — only a literal
`null` would be dropped. ➡️ The server must validate `email` itself; a blank value reaches it as a
present-but-empty field, not as a missing one.

## Response

```json
{"Success": true, "Error": null, "error_id": null}
```

Failure:

```json
{"Success": false, "Error": "No account with that email address.", "error_id": "not_found"}
```

### Why the non-generic promise does **not** mean "body ignored"

[2026-send-helper-tiers](../conventions/2026-send-helper-tiers.md) lists a **non-generic `Task`**
tier that never parses the body — that is `RGBOOBRDHEB::JEYAQXBXMRA(ct)` `0x9537A00`, and this route
does **not** use it. The tail of `ResetPassword` is:

```
0x94e145d  RGBOOBRDHEB..ctor(req, HttpMethod.Post, svc 1, "account/recoverpassword", null)
0x94e1484  RGBOOBRDHEB::NJPEKLKCVCG("email", email, false, false)
0x94e149e  <send>                       ; edx = 0 = default(CancellationToken), generic-shared
0x94e14ad  <Task<T> -> MPVTAJGPRUT<T>>  ; generic-shared adapter
0x94e14eb  <log-on-error>(promise, RecRoom.Log, "ResetPassword failed")
0x94e14ff  <...>(promise, 3)
0x94e151d  jmp 0x942d310                ; KGLKSSUUEOH::FQWUEPYTLAQ
                                        ;   (MPVTAJGPRUT<RecNet.RecNetResult>) -> NXPIPFBMDQY
```

`msig.py RecNet.KGLKSSUUEOH` gives **two** `FQWUEPYTLAQ` overloads:

```
static NXPIPFBMDQY       FQWUEPYTLAQ(MPVTAJGPRUT<RecNet.RecNetResult>)
static MPVTAJGPRUT<!!T>  FQWUEPYTLAQ(MPVTAJGPRUT<RecNet.RecNetResult`1<!!T>>)
```

The method returns `NXPIPFBMDQY`, so it is the **first** one — and `methods.pkl` has exactly **one**
named `FQWUEPYTLAQ` entry, `0x942D310`, the non-generic (the `xor edx, edx` for the `MethodInfo*`
argument is the other tell; a generic-shared call needs a real one). ➡️ **`T` is
`RecNet.RecNetResult`.** Identical collapse to the three valueless Clubs routes
([clubs-announcements-routes](clubs-announcements-routes-wire-shapes.md)) and to
`POST rooms/{id}/experience` ([rooms-experience](rooms-experience-wire-shape.md)).

### `RecNet.RecNetResult` (typedef #46515) — 3 fields, 3 keys

Formatter **`Utf8Json.Formatters.RecNet.VTLMXGUPIAK`** `.ctor` **`0x8E55120`** (confirmed by `msig`:
`Serialize(JsonWriter, RecNet.RecNetResult, …)`), `____stringByteKeys` `0x8E552D1`…`0x8E55321`:

| # | key | CLR | off |
|---|---|---|---|
| 1 | `Success` | bool | 0x10 |
| 2 | `Error` | string | 0x18 |
| 3 | **`error_id`** | string | 0x20 — `[DataMember]` rename of `ErrorId` |

Accepted casings (`____keyMapping` `0x8E5515A`…`0x8E55196`): `Success`/`success`, `Error`/`error`,
`error_id`/**`Error_id`**. ⚠️ **`ErrorId` (no underscore) is NOT accepted** — it does not exist as a
literal anywhere in the build.

**No post-deserialize hook.** `msig.py RecNet.RecNetResult` lists only the six accessors, `.ctor`,
and the two static factories `Ok()` and `Fail(string error, string errorId)` — nothing else is ever
set, so those three keys are the whole contract.

## What the client does with it

Only caller: **`<RunResetPasswordState>d__133.MoveNext`** `0x1133180` (spans `0x1133700`) — a state
in the title-screen flow. `callxref` on `0x94E1340` gives exactly **1** site, `0x11333C1`.

```
0x11332ae  RecRoom.Log::DPMSSQUUFGW("Entering ResetPasswordState")
0x113332f  RRUI.Data.TitleScreenFlowModel$$ShowResetPasswordScreen      ; awaited — user types the email
0x11333a2  RRUI.Data.TitleScreenFlowModel$$GoToTitleInterstitialPage    ; BEFORE the request
0x11333c1  RecNet.Login$$ResetPassword(email)
0x11333d3  RecRoom.Async.SAXZOKINUQZ$$TTKEXAOXQYZ                       ; promise -> awaiter
           <await>  -> builds the next-state value -> builder.SetResult
```

Two consequences for the server:

1. **The UI leaves the reset screen before the request is sent.** `GoToTitleInterstitialPage` runs at
   `0x11333A2`, one instruction block *ahead* of the call. The player is already on the interstitial
   while the POST is in flight, so a slow response reads as a hung title screen, not as a spinner on
   the form.
2. **A rejection is not handled in `MoveNext`.** There is no local recovery branch — the only
   `AsyncTaskMethodBuilder` terminators are the `SetResult` at `0x1133467` and a `SetException` at
   `0x113368B` in the compiler-generated catch. `Success: false` therefore **faults the title-screen
   flow task** rather than showing a field-level "unknown email" message, and the only artefact is
   the greppable client log line **`ResetPassword failed`** (literal `0xFC5FCE8`, attached at
   `0x94E14E2`).

➡️ **Answer `200 {"Success": true, "Error": null, "error_id": null}` for every email you are willing
to accept**, including addresses you do not recognise — that is the usual account-enumeration
defence *and* the only shape that keeps the flow intact. Reserve `Success: false` for requests you
genuinely want to break (rate-limited, malformed), and put a human-readable sentence in `Error`
because nothing else surfaces.

## Siblings on `RecNet.Login` / the Auth service

`msig.py RecNet.Login` (65 methods) — the password-adjacent literals are
`account/me/changepassword` (`0x306935` in `stringliteral.json`) and `account/me/haspassword`
(`0x307171`); **neither is derived**. The structurally identical neighbour is
**`RecNet.Login.STVWCTVGOHS(string code)`** `0x94E1630` → `NXPIPFBMDQY`: route
`account/me/remoteauth`, one form param **`code`**, failure literal `Failed to authorize login`,
same `FQWUEPYTLAQ` collapse ⇒ **same `RecNet.RecNetResult` body**. Derive it from this note if the
remote-device login flow needs it.

⚠️ `RecNet.Login` also exposes `MZWNSKIAHLD(string, string, string)` and `NSVRFNPUVIB(string,
string)` returning `NXPIPFBMDQY` — do **not** assume they share this body without reading their own
tail jump; the generic `FQWUEPYTLAQ<T>` overload collapses `RecNetResult<T>` instead and looks
nearly identical at the call site.
