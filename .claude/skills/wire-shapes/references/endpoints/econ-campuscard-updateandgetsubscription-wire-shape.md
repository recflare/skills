# `POST api/CampusCard/v1/UpdateAndGetSubscription` — Rec Room Plus subscription (2026)

> svc 28 Econ, **POST**, one form param `accessToken`. Response is a **BARE** 2-key
> `SubscriptionInfoDTO` — **`{}` is NOT a valid "no subscription" answer**: every generated object
> formatter in this build returns `null` for an empty JSON object, so `{}` throws
> `Deserialization returned null` → `Malformed Response: '{}'` → `Failed to get subscription: An
> error occurred` and the **boot sequence fails**. Serve at least one key:
> `{"Subscription":null,"PlatformAccountSubscribedPlayerId":null}`.

Derived **2026-11-06** on `C:\games\recflare-2026` (build `20260323.14`), cross-checked against a
live `Player.log` from a non-subscriber account.

## Request

```
POST /api/CampusCard/v1/UpdateAndGetSubscription
Host: econ.<domain>
Content-Type: application/x-www-form-urlencoded

accessToken=
```

| fact | value |
|---|---|
| method | `RecNet.Commerce$$EANKREABZWE(string accessToken, CancellationToken)` **0x93FC070** (bounds `0x93FC070`–`0x93FC307`) |
| path literal | `'api/CampusCard/v1/UpdateAndGetSubscription'` @ `0xFC3CAF8` (2 refs, both in this method) |
| verb | **POST** — `0x93FC155 mov rax,[HttpMethod statics]` → `mov rcx,[rax+0x20]` → `[rcx+0x20]`, i.e. statics **+0x20** |
| service | `mov r8d, 0x1c` at `0x93FC179` = **28 Econ** |
| params | one `NJPEKLKCVCG` at `0x93FC1B4`, literal `'accessToken'` @ `0xFC3*` — POST ⇒ **form body**, not query string (see [elhkhfjehlm-verb-dependent-params](../conventions/elhkhfjehlm-verb-dependent-params.md)) |
| send helper | `RecNet.RGBOOBRDHEB.LIRIDCJIGGA<SubscriptionInfoDTO>(bool, CancellationToken)` with `dl = 1`; methodSpec **method inst #1441 → `.SubscriptionInfoDTO`** |
| continuation | `.<>c::WMRUUXRUNRI` **0x941A750** via `RecRoom.Async.SAXZOKINUQZ::CTZMMSFIPBH<T>` |

### The caller does two attempts

`RecNet.Commerce$$GLPBILBMXNL(bool force)` **0x93FCDB0**:

1. `force == false` **and** the cached DTO (`Commerce` statics **+0x18**) is non-null ⇒ returns the
   cache, **no request** (`0x93FCF17 cmp qword [rax+0x18], 0 ; jbe <fetch>`). Relaunch the client
   between server-side attempts.
2. a platform check fails ⇒ errors the promise with `'Needs access token'`, no request.
3. otherwise `EANKREABZWE("")` — **the first attempt sends an EMPTY `accessToken`**.
4. if that fails: logs `'GetSubscription attempt without access token failed (will try again with
   access token)'` and retries through `RecNet.KGLKSSUUEOH::BOOMBAMSRGA<SubscriptionInfoDTO>` with a
   real platform token. On a self-hosted server that retry has no platform token to get, so **both
   attempts hit this same route** and you see the failure twice per cycle.

Callers of `GLPBILBMXNL`: `<RunBackgroundOperationsDuringRoomLoad>d__181$$MoveNext` 0x112E0B0,
`<OnPurchaseCompletedSuccessfully>d__1` 0x23985A0, `RRUI.Data.SkuModel$$SetSkuButton` 0x28F5E50,
`<TryPurchaseSku>g__OnRRPlusMembershipPurchaseSuccess|11` 0x2916E80, `Commerce$$YBDKRMGBAND`
0x93FF740, `<GetRecRoomPlusSubscriptionSnapshot>d__17` 0x957DA90.

## Response — bare `SubscriptionInfoDTO`, 2 keys

No `RecNetResultObject_SubscriptionInfoDTO` typedef exists (the build pre-generates 92 of those and
this is not one of them) ⇒ **not enveloped**. Formatter
`Utf8Json.Formatters.RecNet.LGXRWCKQVEY` `.ctor` **0x912DB00**, `Deserialize` **0x912D650**;
trailing `____stringByteKeys` run = `Subscription`, `PlatformAccountSubscribedPlayerId` — matches
`ftypes` exactly, no `[DataMember]` renames, nothing keyless.

```json
{
  "Subscription": {
    "SubscriptionId": 1,
    "RecNetPlayerId": 12345,
    "PlatformType": null,
    "PlatformId": null,
    "PlatformPurchaseId": null,
    "Level": 0,
    "Period": 0,
    "ExpirationDate": "2026-12-06T00:00:00Z",
    "IsAutoRenewing": true,
    "CreatedAt": "2026-11-06T00:00:00Z",
    "ModifiedAt": "2026-11-06T00:00:00Z"
  },
  "PlatformAccountSubscribedPlayerId": null
}
```

`Subscription` = 11-key `SubscriptionDTO`, formatter `Utf8Json.Formatters.RecNet.BXBVOGOAEGA`
`.ctor` **0x9124500** / `Deserialize` **0x91237B0**, keys in declaration order with no renames:

| key | type | field offset | notes |
|---|---|---|---|
| `SubscriptionId` | long | +0x10 | |
| `RecNetPlayerId` | int | +0x18 | |
| `PlatformType` | `RecNet.PlatformType?` | +0x1C | numeric |
| `PlatformId` | string | +0x28 | |
| `PlatformPurchaseId` | string | +0x30 | |
| `Level` | `RecNet.Store.SubscriptionLevel` | +0x38 | **Gold 0 · Platinum 1** (typedef #46739) |
| `Period` | `RecNet.Store.SubscriptionPeriod` | +0x3C | **Month 0 · Year 1 · ThreeMonth 2 · SixMonth 3** (typedef #46740) |
| `ExpirationDate` | DateTime | +0x40 | **the only thing `IsActive` reads** |
| `IsAutoRenewing` | bool | +0x48 | |
| `CreatedAt` | DateTime | +0x50 | |
| `ModifiedAt` | DateTime | +0x58 | |

Computed properties (no key, no backing field):

- `SubscriptionDTO.get_IsActive` **0x9413BE0** = `DateTime.UtcNow < ExpirationDate`. Nothing else.
  A past `ExpirationDate` is how you express "lapsed".
- `SubscriptionInfoDTO.get_CanBuySubscription` **0x9413CA0** =
  `!PlatformAccountSubscribedPlayerId.HasValue` (`cmp byte [rbx+0x18], 0 ; sete al` — `hasValue` is
  the **first** byte of the IL2CPP `Nullable<int>`). **Send `null` / omit it or the store refuses to
  sell.** Set it to a player id only when that platform account already holds the subscription.

## ✅ The non-subscriber answer

```json
{"Subscription": null, "PlatformAccountSubscribedPlayerId": null}
```

`Subscription: null` is safe everywhere. The only accessor is
`RecNet.Commerce$$GXLRRHSAEWC` **0x93FD420** = `CurrentSubscriptionInfo?.Subscription`, which
null-checks the DTO (`0x93FD495 test rax,rax ; je`) and returns `[rax+0x10]`; **all 17 call sites
null-check the result again** before touching it — `LocalPlayerGetRRPlusStatus` 0x11D0730,
`RecRoomPlusDataManager.get_HasRecRoomPlusSubscription` 0x96BA330,
`RecRoomAIConversationModel.get_IsRRPlusSubscriber` 0x2739E00, the five `HideIf…RRPlus` /
`ClaimReward…` `OnModelChanged` impls, `RewardSelectionModel.CanShowRecRoomPlusUpsell` 0x27479F0,
`<CheckFreeItemSignOnBonusEligibility>d__7` 0x96BE740, `ProgressionEvents.DVOQLGSEJKF$$GLCURHQNOUG`
0x9D9FE90. There is **no unguarded dereference**, so a null subscription cannot NRE anything.

## ❌ Why `{}` breaks boot

Observed in `Player.log` (build 20260323.14, non-subscriber, server returning `{}`):

```
Exception: Deserialization returned null
  at RecNet.RGBOOBRDHEB.AIYNPFIEYFY[T] (RecNet.XJAFUXFVGPU a)
  at RecNet.RGBOOBRDHEB+TZATELUBAOF`1[a].MUKIUKVCLOC (RecNet.XJAFUXFVGPU a)
  at RecNet.RGBOOBRDHEB.YGADVOMHRVJ[TResponse] (System.Func`2[T,TResult] a, CancellationToken b)
Rethrow as RecNetMalformedResponseException: Malformed Response: '{}'
  ...
  at RecNet.RGBOOBRDHEB.LIRIDCJIGGA[TResponse] (System.Boolean a, CancellationToken b)
[Platform.BootSequence] RecRoom.Async.ErroredPromiseException: Failed to get subscription: An error occurred
```

`'Failed to get subscription: '` @ `0xFCB8F40` is produced by `.<>c$$QBPZKSTWPBX` **0x941A430**;
`'An error occurred'` @ `0xFCD5C68` is the generic promise-error text, so the message tells you
nothing about the body — **read the inner exception**.

The cause is **not** this route being an array or a scalar. It is a property of every generated
object formatter in this build: see
[empty-json-object-deserializes-to-null](../conventions/empty-json-object-deserializes-to-null.md).
`{}` → `ReadIsNull()` false → `ReadIsBeginObjectWithVerify()` ok → `ReadIsEndObject()` **true** →
`return null`, and `AIYNPFIEYFY<T>` rejects a null result.

Four `Malformed Response: '{}'` log entries per cycle = two attempts × (inner + formatted rethrow).

## What a successful response actually does

Continuation `.<>c$$WMRUUXRUNRI` **0x941A750** (140 bytes):

```
0x941A7C9  mov [Commerce_statics + 0x18], result     ; cache CurrentSubscriptionInfo
0x941A7DC  write barrier
0x941A7EC  mov rcx, [Commerce_statics + 0x28]        ; the changed delegate (RecRoom.BQUYOYJDJCS)
0x941A7FC  jmp RecRoom.BQUYOYJDJCS$$Invoke           ; fire it if non-null
```

`RecNet.Commerce` static layout (the 6 `const string` fields carry no storage, which is why the
offsets do not match `ftypes` declaration order): `+0x00` Log, `+0x08`/`+0x10` TimeSpans,
**`+0x18` `SubscriptionInfoDTO <NYYTIQPDTYF>`**, `+0x20`
`DQCNOGDGYBL<SubscriptionEventDTO>`, **`+0x28` the changed delegate**, …

Related pushes that exist in this build and are **not** this route:
`RecNet.NotificationDto_SubscriptionUpdate`, `RecNet.NotificationDto_SubscriptionEventDTO`.

## Siblings on the same facade, underived

- `api/CampusCard/v1/SignUpBonus` (cached in `Commerce` statics as
  `ValueTuple<SignUpBonusCacheStates, RRPlusSignUpBonusDTO>`)
- `api/CampusCard/PS5RecRoomPlusEnabledForAllPlayers`
