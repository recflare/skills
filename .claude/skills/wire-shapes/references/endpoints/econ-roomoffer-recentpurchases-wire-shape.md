# `GET econ/roomOffer/room/{roomId}/recentPurchases` — why the **Report Room** button does nothing

> ⚠️ **This route 404ing is what makes the in-game "Report Room" button dead.**
> `RRUI.Data.RoomModel.ShowReportRoomDialogPopUp` **awaits** it before building any UI, so a
> non-2xx throws `RecNetWebException: HTTP Error 404` inside the dialog's state machine and the
> popup is never shown. No toast, no error UI — just a button that does nothing.
> **GET**, svc **28 Econ**, no query params, no body.
> Response is **ENVELOPED LIST**: `{"Value":[…],"Success":true,"Error":null,"error_id":null}`.
> Element is the 5-key `RecNet.RoomOfferLastPurchaseDTO`. **`Value: []` is fine** — an empty list
> just hides the "Is this about an offer?" picker. The only hard requirement is **2xx + `Success:
> true`**.

Derived **2026-10-29** from build `20260323.14`, starting from a live `Player.log` repro.

## The symptom and how the log names the route

`Player.log` shows five identical `HTTP Error 404` blocks, one per click of the report button, each
rethrown as a `FormattedAsyncException` whose formatted stack is:

```
RecNetWebException: HTTP Error 404
  at RecNet.XJAFUXFVGPU.RBSYDGDRRZM (System.Boolean a)          ; ensure-success, throws on non-2xx
  at RecNet.RGBOOBRDHEB+<>c__44`1[TResponse].WDXTMYIEGJT
  …
  at RecNet.Cache.Get[TResponse] (service, requestUri, maxCacheAge, forceRefreshCache, callback, ct)
  at RecNet.RGBOOBRDHEB.ZWUODKCINOA[TResponse]
  at RecNet.LEMLPUGKWSA.LHAFODXTBPA (System.Int64 a, CancellationToken b)
  at RecRoom.RoomEconomy.RoomOffer.KQPMJKEWIZA.WQDTRTKHEPO (System.Int64 a, CancellationToken b)
  at RRUI.Data.RoomModel.ShowReportRoomDialogPopUp ()
```

The two obfuscated middle frames resolve by the state machine they start, because
compiler-generated nested names survive obfuscation while the outer method names do not:

| log frame | RVA | `AsyncTaskMethodBuilder::Start` methodSpec | real name |
|---|---|---|---|
| `KQPMJKEWIZA.WQDTRTKHEPO` | `0xA1A8AF0` | inst **#66609** = `<GetRecentPurchasedRoomOffersForRoom>d__47` | **`GetRecentPurchasedRoomOffersForRoom(long roomId, ct)`** |
| `LEMLPUGKWSA.LHAFODXTBPA` | `0x956F310` | inst **#66628** = `<GetRecentRoomOfferPurchasesForRoom>d__19` | **`GetRecentRoomOfferPurchasesForRoom(long roomId, ct)`** |

➡️ **Generalisable:** for any obfuscated async frame in a stack trace, `slots2025.py` the method and
read the `Start` methodSpec's generic instantiation — `ginst.py --method <n>` prints the
`<RealName>d__N` state machine. That is a two-command de-obfuscation for anything that appears in a
log, and it does not need `callxref` or a literal to anchor on.

`RecNet.LEMLPUGKWSA` (typedef #23157) is the **RoomOffers facade**; `RecRoom.RoomEconomy.RoomOffer.KQPMJKEWIZA`
(typedef #59095) is `RoomOfferManager`, the in-room layer above it.

## Route

State machine `<GetRecentRoomOfferPurchasesForRoom>d__19$$MoveNext` **`0x957DE00`**:

| what | value | evidence |
|---|---|---|
| path | **`econ/roomOffer/room/{roomId}/recentPurchases`** | `String.Format("{0}/room/{1}/recentPurchases", "econ/roomOffer", roomId)` — literals `0x957DE98` + `0x957DEA4`, formatted at `0x957DF73` |
| verb | **GET** | `0x957DF37 mov rcx,[rax+0x20]` (HttpMethod statics) → `0x957DF3B mov r15,[rcx+8]` = **`+0x08`** |
| service | **28 = Econ** | `0x957DF96 mov r8d, 0x1c` into the request `.ctor` `0x8BBF9E0` at `0x957DFA2` |
| params | **none** | the builder-action slot is `mov qword [rsp+0x20], 0` at `0x957DF8A` |
| body | **none** | GET, no `FZNGWUAGAIN`/`NJPEKLKCVCG` call in the method |

`roomId` is a **path segment**, not a query param. Nothing else is sent — the server must resolve
the caller from the bearer token.

### It is response-cached, so a 404 is not re-requested on every click

`0x957DFEE call 0x9538790` = **`RGBOOBRDHEB.ORUUDATDRUN(TimeSpan maxCacheAge, bool forceRefresh)`**
→ `RecNet.Cache.Get<TResponse>` (visible in the log frame). The `TimeSpan` comes from a facade
static, `forceRefresh` from a static byte.

⚠️ **This is why it can look like the button "doesn't even make a request".** Within the cache
window a repeat click replays the cached outcome instead of hitting the network, so a packet capture
taken after the first click shows nothing. In the captured log the request *was* made — five times,
once per click, spread over ~2 minutes. **Relaunch the client (or wait out the window) between
server-side attempts**, the same trap already recorded for
[makerai-checkfreetrialeligibility](makerai-checkfreetrialeligibility-wire-shape.md).

## Response — ENVELOPED LIST

```json
{ "Value": [ { "RoomOfferOriginId": "2f1c9e4a-0000-4000-8000-000000000001",
               "Name": "Blue Hat",
               "PurchasePrice": 25,
               "PurchaseDate": "2026-10-29T11:00:00Z",
               "Version": 1 } ],
  "Success": true,
  "Error": null,
  "error_id": null }
```

`TResponse` is **`RecNet.RecNetResultListObject<RecNet.RoomOfferLastPurchaseDTO>`** — methodSpec
generic inst **#22898** on the `ZWUODKCINOA` call at `0x957DFFC`. Both checks agree it is enveloped:

- **Envelope oracle** ([2026-send-helper-tiers](../conventions/2026-send-helper-tiers.md)):
  `RecNet.RecNetResultListObject_RoomOfferLastPurchaseDTO$$.ctor` **`0x9539760`** exists as a
  concrete typedef. (There are only 12 `RecNetResultListObject_*` types on this build; the sibling
  `…_RoomOfferPurchaseCountDTO` `0x95397A0` is one of them.)
- The facade's own builder is `AsyncTaskMethodBuilder<RecNetResult<List<RoomOfferLastPurchaseDTO>>>`
  (inst **#3008**), and `SetResult` at `0x957E0CE` is handed the **deserialized envelope unchanged**
  — ⚠️ **there is no `FQWUEPYTLAQ` collapse in this facade.** `RecNetResultListObject<T>` derives
  `RecNetResult<List<T>>`, so the envelope is the facade's return value and the *caller* unwraps it.

### The 2026 envelope layout — formatter-confirmed, not assumed

The envelope has its own generated formatter per concrete type. For this route it is
**`Utf8Json.Formatters.RecNet.PDYQSWVXISV`** `.ctor` **`0x8E206B0`** (`msig`: `Serialize(…,
RecNet.RecNetResultListObject`1<RecNet.RoomOfferLastPurchaseDTO>, …)`). Its `____stringByteKeys` run
(`0x8E208C1`…`0x8E2093D`) gives the **declaration order and canonical casing**:

| # | key | CLR | off | accepted casings |
|---|---|---|---|---|
| 1 | `Value` | `List<RoomOfferLastPurchaseDTO>` | 0x28 | `Value`, `value` |
| 2 | `Success` | **bool** | 0x10 | `Success`, `success` |
| 3 | `Error` | **string** | 0x18 | `Error`, `error` |
| 4 | **`error_id`** | string | 0x20 | **`error_id`, `Error_id`** |

So `Value` comes **first** on the wire, not last, and the CLR field order (`Success`, `Error`,
`ErrorId` on the base `RecNet.RecNetResult`, then `Value` added by `RecNetResult<T>`) is the reverse
— derived-class members are emitted before base members, the usual rule. Order does not matter for
*deserialization*, but it is what the client emits.

⚠️ Two things worth having right:

- **`Error` is a string on 2026**, not the numeric code older notes imply (`ftypes` on
  `RecNet.RecNetResult`: `Success` bool, `Error` string, `ErrorId` string). The consumer confirms the
  offsets — `+0x10` tested as a byte, `+0x18` concatenated into a message string, `+0x28` taken as
  the list.
- The `ErrorId` key has only **two** accepted casings instead of the usual three, and `Error_id` is
  one of them. `error_id` is the canonical form the client writes, so keep serving that.

`RecNet.RecNetResultListObject_RoomOfferLastPurchaseDTO` declares **0 fields of its own** (`ftypes`)
— it is purely `RecNetResultListObject<T>` pinned to this element type, so nothing extra rides
along.

### Element DTO — `RecNet.RoomOfferLastPurchaseDTO`, 5 keys

Formatter **`Utf8Json.Formatters.RecNet.WOOORFYRPIF`** `.ctor` **`0x8E810F0`** (`msig`-confirmed;
the near-identical `SVZGOXEDADM` `0x8E7F5B0` is `RoomOfferPurchaseCountDTO` — do not mix them up,
they share the `RoomOfferOriginId` key literal `0xFD20BA0`). Key run `0x8E813E4`…`0x8E81488`:

| # | key | CLR | off |
|---|---|---|---|
| 1 | `RoomOfferOriginId` | **`System.Guid`** | 0x10 |
| 2 | `Name` | string | 0x20 |
| 3 | `PurchasePrice` | int | 0x28 |
| 4 | `PurchaseDate` | `System.DateTime` | 0x30 |
| 5 | `Version` | int | 0x38 |

Three casings each (`RoomOfferOriginId` / `roomOfferOriginId` / `roomofferoriginid`, etc.) — 13
distinct casings in `____keyMapping` + 5 `____stringByteKeys` ✓. `RoomOfferOriginId` is a **GUID
string**, not a long id. `msig` on the DTO shows only accessors and two `.ctor`s — **no
post-deserialize hook** (`IULRMJBAHPG`/`EMSIIQRWASQ` both absent), so no sanitisation round trip and
no null-tolerance question on `Name`.

## What the client does with it — only 2xx is load-bearing

`<GetRecentPurchasedRoomOffersForRoom>d__47$$MoveNext` **`0xA1AB0E0`**:

```
0xa1ab2ce  test rax, rax                 ; the envelope
0xa1ab2d1  je   0xa1ab4ac                ; null envelope -> NRE helper
0xa1ab2d7  cmp  byte ptr [rax + 0x10], 0 ; Success
0xa1ab2db  jne  0xa1ab3a3                ; true  -> success path
0xa1ab2e1  …    [rax + 0x18]             ; false -> Concat("Error loading recent Room Offer
0xa1ab2ef  call System.String$$Concat    ;          Purchases: ", Error) and log
0xa1ab3a3  mov  rbx, qword ptr [rax+0x28]; Value
0xa1ab3d0  call AsyncTaskMethodBuilder::SetResult
```

So on this route:

- **`Success: false` does NOT throw.** It logs `Error loading recent Room Offer Purchases: <Error>`
  and completes. The dialog still opens.
- **`Value: null` does not throw here either** — it is handed to `SetResult` as-is. Serve `[]`
  anyway; the picker consumer was not followed further.
- **A non-2xx status is the only fatal case**, because `XJAFUXFVGPU.RBSYDGDRRZM(bool)` throws
  `RecNetWebException` far below any of this.

➡️ **Minimum viable fix:** return `200` with
`{"Value":[],"Success":true,"Error":null,"error_id":null}`. The report dialog then opens with the
"Is this about an offer?" row empty, which is correct behaviour for a player who has bought nothing
in the room.

## Why a *report* dialog reads room-offer purchases

`<ShowReportRoomDialogPopUp>d__349$$MoveNext` **`0x28506A0`** — `names.py` gives the dialog's whole
string inventory, which explains the dependency:

```
"Report {0}"                      "Choose your reason"        "Report Details"
"Is this about a key?"            "Select a key to report..."
"Is this about an offer?"         "Select an offer to report..."
"Enter report details here..."    "Take Photo" / "Remove Photo" / "Submit"
"(Optional) Take a photo of the violating content to include in your report."
"Leave feedback for the room owner instead"
"Players who send false reports or abuse the reporting system will be penalized."
```

The **offer picker is populated from this route** — you can only report an offer you actually
purchased, so "recent purchases" *is* the offer list. Every literal above sits **after** the awaits
in the state machine, so the fetch gates the entire dialog, not just that one row.

⚠️ The dialog also has a **key** picker (`"Is this about a key?"`), which implies a second
prerequisite fetch on the `roomkeys` facade ([roomkeys-v1-mine](roomkeys-v1-mine-wire-shape.md)).
It did not appear in this repro's stack — all five 404s were this one route — so either it is served
already or it is reached after the throw. **Expect it to surface as the next blocker** once
`recentPurchases` returns 2xx.

## The rest of the `econ/roomOffer` family (leads, verbs underived)

All six siblings live on `RecNet.LEMLPUGKWSA` and build their path from the same `econ/roomOffer`
base literal `'econ/roomOffer'` **`0xFD8B0D0`** + a per-route format string. Only `recentPurchases` is derived here:

| state machine | RVA | path format | likely name |
|---|---|---|---|
| `<CreateRoomOffer>d__14` | `0x957AD60` | `{0}/room/{1}` | create |
| `<UpdateRoomOffer>d__15` | `0x95840A0` | `{0}/{1}/{2}` | update |
| `<DeleteRoomOffer>d__16` | `0x957B9F0` | `{0}/{1}/{2}` | delete |
| `<GetRoomOfferPurchaseCountsForRoom>d__18` | `0x957F360` | `{0}/room/{1}/purchaseCounts` | → `RecNetResultListObject<RoomOfferPurchaseCountDTO>` |
| **`<GetRecentRoomOfferPurchasesForRoom>d__19`** | **`0x957DE00`** | **`{0}/room/{1}/recentPurchases`** | **this note** |
| `<GetInventoryItemsConcurrencyCodesMapForPlayer>d__20` | `0x957D3B0` | `{0}/player/{1}/concurrencyCode` | + `roomInventoryIds` param |
| `<PurchaseRoomOffer>d__21` | `0x9580D10` | `{0}/{1}/{2}/purchase` | purchase |

⚠️ `d__16`, `d__18`, `d__20` and `d__21` each hold **a second route from an unrelated facade**
(`api/recipesEvents`, `api/timedRewardTracks`, `api/timedRewardTrees`) because IL2CPP packed
neighbouring method bodies adjacently — `names.py` with a wide window crosses into them. Attribute
literals to the state machine they start inside, not to the window.

## Also in this log, unrelated

- `[LiveOps.TLA.Recipes.Ingredients] RecNet.RecNetWebException: HTTP Error 404` at 09:24 and 10:19 —
  the `api/recipesEvents` family, a different gap.
- `[10:57:51] [Warning] Missing prefab to load` — the room-load prefab gap, covered by
  `rr-client-bringup/references/room-load-unknown-prefab-studio-bundle-2026.md`; not investigated
  here, and not related to the report button.
