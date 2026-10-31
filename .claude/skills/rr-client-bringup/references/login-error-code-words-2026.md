# The `Unable to login (code: <word>)` codes — what each word actually means

> The word codes are `RecNet.Error` enum members, and each one is raised from **exactly one** place
> in the client. `timber` = `LOGIN_CODE_TIMBER = 25`, raised only in
> `<AddDeviceTokenToLoginRequest>d__96` when the **platform device-token fetch throws** — i.e.
> before the login request is even sent, so **no server response can cause or fix it**.
> The real cause is always logged immediately before the throw. Full code → raise-site map below.

Derived **2026-10-29** from build `20260323.14`. The literals and the enum are **identical on
`20250718.01`**, so this map applies to both builds.

## The table that turns a word into a method

`RecNet.Error` (typedef #22207, `int`) holds every user-facing error, and
**`RecNet.MLREETGNUXI`** is the message table. Its API:

```csharp
static Dictionary<RecNet.Error, string> BUWJZLVSPNV          // Error -> message
static Dictionary<string, RecNet.Error> QVJALHJWVWK          // message key -> Error (reverse)
static string    ZJGJQVSXQPY(RecNet.Error)   0x94B0E10        // <-- the lookup; 47 call sites
static string    Get(RecNet.Error key)       0x94B0760
static Exception NOQAHTURUAW(RecNet.Error)   0x94B07E0
static Exception NOQAHTURUAW(RecNet.Error, Exception)  0x94B0860
static RecNet.Error VJZIQYMNHMN(string)      0x94B0C00
static IEnumerable<(RecNet.Error, string)> BGPBCGHJLHK(string, char)  0x94B06D0   // parses an override blob
```

The `.cctor` **`0x94B0E60`** builds both dictionaries with the default English strings — that is
where all 15 `Unable to login (code: …)` literals live, and why `mxref` on one of them only ever
reaches the `.cctor`.

The 15 word/number login literals on this build:

```
code: 3   code: 4   code: 5          (LOGIN_CODE_3/4/5           = 15/16/17)
code: plot        = LOGIN_CODE_PLOT       18      code: block   = LOGIN_CODE_BLOCK      19
code: challenge   = LOGIN_CODE_CHALLENGE  20      code: doll    = LOGIN_CODE_DOLL       21
code: note        = LOGIN_CODE_NOTE       22      code: spinner = LOGIN_CODE_SPINNER    23
code: wrapper     = LOGIN_CODE_WRAPPER    24      code: timber  = LOGIN_CODE_TIMBER     25
code: book        = LOGIN_CODE_BOOK       26      code: water 1 = LOGIN_CODE_WATER_1    27
code: water 2     = LOGIN_CODE_WATER_2    28      code: water 3 = LOGIN_CODE_WATER_3    29
```

Sibling families with the same opaque style: `FAILED_TO_CONNECT_CODE_{LOCKER 4, NAME 5, PENCIL 6,
STUDENT 7, SUMMER 8, LIST 41}` and `STEAM_LOGIN_CODE_{1 33, 2 34, 3 35}`.

⚠️ **The enum values are not the numbers in the message.** `code: 3` is `LOGIN_CODE_3` = **15**,
not 3. `Error = 3` is `ERROR_OCCURRED_TRY_AGAIN`.

## Code → raise site (complete `ZJGJQVSXQPY` map)

Produced by pairing each call site's preceding `mov ecx, imm` with its owning method
(`scratchpad/errmap.py`, 40 of 47 sites carry a literal constant; the rest pass a variable):

| `Error` | member | raised in |
|---|---|---|
| 1 | `ACCOUNT_ALREADY_LOGGED_IN` | `<ShowLaunchGameScreen>d__146` `0x1135F4A` |
| 2 | `CANNOT_CHANGE_BIRTHDAY` | `RecNet.Accounts$$TRDTPWBDPRP` `0x942277E` |
| 4 | `FAILED_TO_CONNECT_CODE_LOCKER` | `<ProcessNameServerResponse>d__144` `0x9496650` |
| 5 | `FAILED_TO_CONNECT_CODE_NAME` | `RecNetNameServerResponseChangedException..ctor` `0x9432195` |
| 7 | `FAILED_TO_CONNECT_CODE_STUDENT` | `<>c$$PSBDDKRFAOD` `0x95673E2` |
| 8 | `FAILED_TO_CONNECT_CODE_SUMMER` | `<ConnectToRecNet>d__142` `0x948D610` |
| 9 | `FAILED_TO_REMOVE_CACHED_LOGIN` | `<>c$$RLUDVNIXOPO` `0x94EB2E0` |
| 13 | `INVALID_SYSTEM_TIME` | `RecNet.Login$$AWUFMYCEVDB` `0x94DB07D` |
| 14 | `LAUNCH_VALIDATION_FAILED` | `<Initialize>d__11` `0x13F8E8B`, `Login$$AWUFMYCEVDB` `0x94DB1BC` |
| **15** | **`LOGIN_CODE_3`** | `<ParseLoginResponse>d__98` ×3 (`0x950C58C`, `0x950C65E`, `0x950C7F3`), `<SendLoginRequest>d__97` `0x950DE07` |
| **18** | **`LOGIN_CODE_PLOT`** | `<AddPlatformAuthToLoginRequest>d__94` `0x950497C`; also `TIFHMBHOZCV$$EVABSPFEOGI` `0xEB3AEF` |
| **19** | **`LOGIN_CODE_BLOCK`** | `<DownloadDefaultAvatarItems>d__243` `0xFE948C`, `<GetModerationBlockDetailAsync>d__22` `0x20613E6` |
| **25** | **`LOGIN_CODE_TIMBER`** | **`<AddDeviceTokenToLoginRequest>d__96` `0x94E688D` — the only site** |
| **26** | **`LOGIN_CODE_BOOK`** | `<LoginToAccountNo2FA>d__217` `0xFEFAD2`, `<RunManualLoginState>d__128` `0x113207C` |
| **27** | **`LOGIN_CODE_WATER_1`** | `RecNet.Login$$AWUFMYCEVDB` `0x94DB174` |
| **28** | **`LOGIN_CODE_WATER_2`** | `<GenerateChallengeResponse>d__108` `0x9506E8D` |
| **29** | **`LOGIN_CODE_WATER_3`** | `<GenerateChallengeResponse>d__108` `0x9507023` |
| 31 | `LOGIN_FAILED_TRY_AGAIN` | `<RunManualLoginState>d__128` `0x1131B03`, `Login$$AWUFMYCEVDB` `0x94DB248` |
| 36 | `UNABLE_TO_LOAD_ACCOUNT` | `<HandleLoginResponse>d__99` `0x950A3A6` |
| 37 | `USERNAME_AND_PASSWORD_MISMATCH` | `RecNet.Login$$AWUFMYCEVDB` `0x94DB124` |
| 40 | `ACCOUNT_PERMALOCKED` | `RecNet.Login$$AWUFMYCEVDB` `0x94DB0CD` |
| 41 | `FAILED_TO_CONNECT_CODE_LIST` | `<ConnectToRecNet>d__142` `0x948D6DE`, `<…RefreshGameConfigsInternal|111_1>d` `0xFF8342`, `<>c$$PSBDDKRFAOD` `0x95673A1`, `XJAFUXFVGPU$$RBSYDGDRRZM` `0x9569CCA` |
| 42 | `PLATFORM_USER_COMMUNICATION_RESTRICTED` | `<InitializePlatform>d__112` `0xFEB085`, `Login$$AWUFMYCEVDB` `0x94DB007` |
| 43 | `TLS_FATAL_ERROR` | `<ConnectToRecNet>d__142` `0x948D54E` |

➡️ **`RecNet.Login$$AWUFMYCEVDB` `0x94DB000`-ish is the server-driven translator** — it is the one
method that maps several codes (13, 14, 27, 31, 37, 40, 42), i.e. it turns a login *response* field
into a user-facing error. **Anything it does not emit cannot be selected by the server.**

A second, smaller family goes through `NOQAHTURUAW(Error, Exception)`, called only from
`<<InitializationParallelSteps>g__TransformException|0>d` `0xFF84D0`, which wraps four parallel boot
steps. The `Error` is baked into each call in `<InitializationParallelSteps>d__223$$MoveNext`
`0xFE99D0`:

| site | `r8d` | member |
|---|---|---|
| `0xFE9B80` | `0x13` | `LOGIN_CODE_BLOCK` 19 |
| `0xFE9BCD` | `0x16` | `LOGIN_CODE_NOTE` 22 |
| `0xFE9C8A` | `0x17` | `LOGIN_CODE_SPINNER` 23 |
| `0xFE9CBF` | `0x15` | `LOGIN_CODE_DOLL` 21 |

## `timber` in detail

`<AddDeviceTokenToLoginRequest>d__96$$MoveNext` **`0x94E63F0`–`0x94E68E0`** does exactly one thing:

```
0x94e6506  RecNet.Core statics -> [statics+0x28]           ; the AQWHEEVHLXV platform service
0x94e6558  mov r8d, 5 ; resolve interface slot 5           ; AQWHEEVHLXV::YPGSXDJTCDM()
0x94e6576  call rax                                        ;   -> Task<string>  (the device token)
0x94e6594  BDTRWDYNBFK::VZKXYSMBGFF<string>(task, ct)      ; WithCancellation wrapper
0x94e65d5  await
0x94e65fe  String.IsNullOrWhiteSpace(token)
0x94e6605  jne 0x94e6630                                   ; empty token -> skip, SetResult, NO error
0x94e662a  RGBOOBRDHEB::NJPEKLKCVCG("device_token", token) ; otherwise add the login param
```

`RecNet.AQWHEEVHLXV` is the platform-services interface (24 methods; slot 19/20 are
`SanitizeDisplayText`/`SanitizeDisplayTextAsync`). **Slot 5 `YPGSXDJTCDM()` → `Task<string>` is the
device token.**

The catch block `0x94E6748`–`0x94E68DE`:

```
0x94e6748  catch (…) -> r14 = exception          ; NO exception-type filter
0x94e686d  RecRoom.Log$$PKNBDRXBUHB(logger, r14, <>c::QFECBIQGNRR)   ; logs the REAL cause
0x94e6888  mov ecx, 0x19
0x94e688d  call MLREETGNUXI$$ZJGJQVSXQPY         ; "Unable to login (code: timber)"
0x94e68b8  throw new RecNet.RecNetWebException(message, inner: r14)
```

Three consequences worth knowing:

1. ⚠️ **The catch is unfiltered**, so *any* failure of the device-token task becomes `timber`,
   including an `OperationCanceledException` from the `VZKXYSMBGFF` cancellation wrapper. A login
   the user aborted and a genuinely broken platform SDK produce the identical message.
2. ✅ **The inner exception is logged first** (`Log.PKNBDRXBUHB` at `0x94E686D`). In `Player.log`,
   the lines immediately **before** the timber message are the actual diagnosis. Never debug
   `timber` itself — read what precedes it.
3. ⚠️ **It is thrown while *building* the login request**, before `<SendLoginRequest>d__97` runs.
   So no HTTP status, body or header from the server can produce it or prevent it, and it is not in
   `Login$$AWUFMYCEVDB`'s server-driven set. It is a genuine **client/platform-side** failure —
   one of the few login symptoms where
   [the usual "the server is the variable" rule does not apply](recflare-2025-working-client.md).
   An **empty** token is explicitly fine (`IsNullOrWhiteSpace` → skip the param), so a platform
   stub that returns `""` is a legitimate workaround; one that throws is not.

`RecNetWebException` is the thrown type despite nothing having been sent — do not read it as
evidence of a network round trip.

## Technique note

The whole map came from one pattern, reusable for any obfuscated error-code table:

1. Grep `out/stringliteral.json` for the user-visible message → get its address.
2. `mxref.py` it → lands in a `.cctor` (a static message table), which names the table class.
3. `enumvals.py` the enum the table is keyed by → member names and values survive obfuscation.
4. `callxref.py` the table's lookup method, then for each site read the immediate loaded into the
   argument register just before the `call`, and attribute it with `fstart.py`.

⚠️ `rangedis.py` windows overrun into the next method, so the same call site appears under several
"owners" if you pair by window. **`fstart.py <rva>` gives the true `(start, end)`** — attribute by
containment, not by window.
