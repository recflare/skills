# `GET api/roomEarningsDistributions/v1/earningsDistribution/{roomId}` — ENVELOPED 5-key DTO

> **GET** (svc **28 Econ**), **no query params, no body**.
> Response is **ENVELOPED**:
> `{"Value": {…5 keys…}, "Success": true, "Error": null, "error_id": null}`
> — even though the facade's declared `T` is the bare DTO, because the generic collapse helper
> unwraps it. **Do not serve the bare DTO.**
> The `Value` payload is the 5-key **`RecNet.RoomEarningsDistributionDTO`**:
> `RoomId`, `EarningsDistributionMapping`, `EarningsDistributionMethod`,
> `ShouldDistributeToRoomBalance`, `RoomBalanceTokenLimit`.
> ⚠️ `EarningsDistributionMapping` is a **`Dictionary<int, byte>`** — a JSON **object** keyed by
> **accountId as a string**, value = percent. Not an array.
> ⚠️ `EarningsDistributionMethod` is a **byte enum**, `Equal = 0` / `Custom = 1` — numeric on the wire.

Derived **2026-10-28** from build `20260323.14`.

## Route

Facade **`RecNet.VTWUJFMTUKP.AZIJDJCSHIV(long roomId)`** **`0x943CA20`** →
`RecRoom.Async.MPVTAJGPRUT<RecNet.RoomEarningsDistributionDTO>`. The facade has only two route
methods (plus `.ctor`/`.cctor`).

| what | value | evidence |
|---|---|---|
| path | `api/roomEarningsDistributions` + `{0}/v1/earningsDistribution/{1}` | literals **`0xFC67550`** + **`0xFCD29E0`**, `String.Format` at `0x943CB5F`; `mxref` = 2 refs each, both in this method |
| verb | **GET** | `0x943CB32 mov rcx,[rax+0x20]` (statics) → `0x943CB36 mov rdi,[rcx+8]` — **`+0x08` = `HttpMethod.Get`** |
| service | **28 = Econ** | `mov r8d, 0x1c` at `0x943CB7F`, into `RGBOOBRDHEB..ctor` `0x8BBF9E0` at `0x943CB8E` |
| params | **none** | no `NJPEKLKCVCG` / `ZTKGODPCQRW` / `KTGGWMNSEXK` anywhere in the method |
| body | **none** | no `FZNGWUAGAIN` / `YHPVSAVMRFS` |
| client cache | **none** | no `ORUUDATDRUN` |

⚠️ **The path is assembled from two literals** — grep `v1/earningsDistribution`, not the full URL.

### A client-side guard fires before the request

```
0x943cacd  test rbx, rbx            ; roomId
0x943cad0  js   0x943cc20           ; negative -> log and bail, NO request is sent
```

The bail branch formats **`"Attempted to get room earnings distribution with invalid RoomID: {0}"`**
(literal at `0x943CAAE`) and returns a rejected promise. So a negative `roomId` never reaches the
server, and that string in a client log means the *caller* passed garbage, not that the route 404'd.

## Response — enveloped

```json
{ "Value": {
    "RoomId": 34443,
    "EarningsDistributionMapping": { "1": 60, "205": 40 },
    "EarningsDistributionMethod": 1,
    "ShouldDistributeToRoomBalance": false,
    "RoomBalanceTokenLimit": 0 },
  "Success": true, "Error": null, "error_id": null }
```

### `RecNet.RoomEarningsDistributionDTO` — 5 keys

Formatter **`Utf8Json.Formatters.RecNet.DHHLWESJSOD`** `.ctor` **`0x8E5A5C0`** (confirmed by `msig`:
`Serialize(JsonWriter, RecNet.RoomEarningsDistributionDTO, …)`), found by xrefing the key literal
`EarningsDistributionMapping` **`0xFCA60B8`** (3 refs, all in this `.ctor`).
`____stringByteKeys` is the trailing single-casing run `0x8E5A910`…`0x8E5A9B4`:

| # | key | CLR | notes |
|---|---|---|---|
| 1 | `RoomId` | long | |
| 2 | `EarningsDistributionMapping` | **`Dictionary<int, byte>`** | accountId → percent |
| 3 | `EarningsDistributionMethod` | `RecNet.EarningsDistributionMethod` (**byte**) | `Equal = 0`, `Custom = 1` |
| 4 | `ShouldDistributeToRoomBalance` | bool | |
| 5 | `RoomBalanceTokenLimit` | long | |

All three Utf8Json casings are present for every key (`RoomId`/`roomId`/`roomid`, …), so the
`____keyMapping` block is the 15 interleaved entries at `0x8E5A5FE`…`0x8E5A6A6`.

**No post-deserialize hook** — `msig` lists exactly 11 methods (5 getter/setter pairs + `.ctor`),
no `EMSIIQRWASQ` and no `IULRMJBAHPG`. Nothing validates the payload.

➡️ `EarningsDistributionMapping` should be `{}` rather than `null` for "nothing configured"
(`Dictionary` consumers downstream of a clean parse are the usual NRE source — see
[circuitchiplists](circuitchiplists-wire-shape.md)). `EarningsDistributionMethod: 0` (`Equal`) with
an empty mapping is the sane default, and matches the UI's `ToggleEqualDistribution`.

### Why enveloped, when the facade says `MPVTAJGPRUT<RoomEarningsDistributionDTO>`

The tail is:

```
0x943cbad  <send>                  ; ZWUODKCINOA<T>(default(ct)), generic-shared
0x943cbbc  <Task<T> -> MPVTAJGPRUT<T>>
0x943cc01  <log-on-error>(promise, Log, <static message string>)
0x943cc10  call 0x3c092f0          ; ONE arg + methodInfo -> the GENERIC collapse
                                   ;   FQWUEPYTLAQ<T>(MPVTAJGPRUT<RecNetResult<T>>) -> MPVTAJGPRUT<T>
```

`0x3C092F0` is **not** the non-generic `FQWUEPYTLAQ` `0x942D310` used by the value-less routes
([clubs-announcements-routes](clubs-announcements-routes-wire-shapes.md),
[account-recoverpassword](account-recoverpassword-wire-shape.md)); it takes one parameter, which is
the arity of the **generic** overload. It unwraps `Value`, which is why the facade's declared `T` is
already the bare DTO.

Confirmed independently by the **envelope oracle** (see
[2026-send-helper-tiers](../conventions/2026-send-helper-tiers.md)):
**`RecNet.RecNetResultObject_RoomEarningsDistributionDTO`** exists as a concrete typedef
(`.ctor` `0x953A620`), which only happens if something instantiates
`RecNetResultObject<RoomEarningsDistributionDTO>` — and this DTO appears on no other route.

## The write sibling — `POST`, JSON body, same 5 fields

**`RecNet.VTWUJFMTUKP.AMNEAPLCJHO(long roomId, EarningsDistributionMethod method,
Dictionary<int,byte> mapping, bool shouldDistributeToRoomBalance, long roomBalanceTokenLimit)`**
**`0x943C7E0`** → `RecRoom.Async.NXPIPFBMDQY`.

| what | value | evidence |
|---|---|---|
| path | `api/roomEarningsDistributions/v1/earningsDistribution` | literal **`0xFC678A0`** — **whole path, no `{roomId}` segment** |
| verb | **POST** | `0x943C923 mov rcx,[rax+0x20]` → `0x943C927 mov rbx,[rcx+0x20]` = **`+0x20`** |
| service | **28 Econ** | `mov r8d, 0x1c` at `0x943C93E` |
| body | **JSON** | `0x943C971 call 0x3E50380` with one object arg = `FZNGWUAGAIN<T>(T)`; no param adders, only 2 literals in the whole method |
| response | value-less promise | `NXPIPFBMDQY` |

The five parameters map **1:1, in order and by type**, onto the five DTO keys, so the body is
almost certainly the same `RoomEarningsDistributionDTO` (`roomId` travels in the body, which is why
the POST path has no id segment). ⚠️ **The body's methodSpec was not read** — `0x3E50380` is
generic-shared and `methods.pkl` mis-resolves it — so the request type is an inference from arity
and types, not a confirmed generic instantiation.

Its response tier is **not** settled here either: it ends in the same `0x3C08C10` log helper but the
final collapse was not read, and a value-less `NXPIPFBMDQY` is reached both by `JEYAQXBXMRA` (body
ignored) and by the non-generic `FQWUEPYTLAQ` (value-less envelope). Serving
`{"Success": true, "Error": null, "error_id": null}` satisfies both.

## Consumers

`callxref` on `0x943CA20` gives exactly **2** sites:

- **`EarningsDistributionModel.AZIJDJCSHIV()`** `0x21D91D0` — the room-settings screen. Its siblings
  name the feature plainly: `ToggleEqualDistribution`, `GetTotalPercentageText`,
  `GetEarningsDistributionReminderText`, `SaveSettings`, `RevertSettings`,
  `get_ShouldEqualDistributionToggleBeInteractable`. So the mapping's values are **percentages the
  UI expects to total 100**.
- **`RRUI.Data.RoomModel.GetEarningsDistribution`** `0x281BEC0`.

Three websocket-side notification controllers exist for this feature and are **not derived**:
`RoomEarningsDistributionCoOwnerAddedNotificationController`,
`…CoOwnerRemovedNotificationController`, `…PercentageUpdatedNotificationController` (all deriving
`BaseRoomEarningsDistributionNotificationController` `.ctor` `0xD756B0`). The literal
`RoomEarningsDistribution` `0xFCF7F08` is the likely channel key.
