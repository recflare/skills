# `api/inventions/v2/batch` — BARE ARRAY of Invention, and the verb is **GET below 100 ids**

> svc **2 API**. ⚠️ **The verb is computed at runtime from `ids.Count`**: `< 100` → **GET** with a
> repeated query param, `>= 100` → **POST** with a repeated **form-urlencoded** body. There is
> **no JSON body on either path** — the ids always travel as a repeated `id` parameter.
> Response is a **BARE JSON ARRAY** of the 28-key `RecNet.Invention` (no envelope).
> ⚠️ **2026 key drift: 2025's `IsAGInvention` is now `IsAgInvention`.**
> ⚠️ `UgcVersion` must be **1** or every row silently vanishes — see
> [inventions-v2-mine](inventions-v2-mine-wire-shape.md).

Derived **2026-10-28** from build `20260323.14`. The DTO itself was first derived on `20250718.01`
in [inventions-v2-search](inventions-v2-search-wire-shape.md); that shape still holds, with the one
casing change noted below.

## Route

Facade **`RecNet.Inventions.DOEFRIAWEWS(IReadOnlyList<long> ids, CancellationToken ct)`**
**`0x94A5DA0`** → `Task<List<RecNet.Invention>>`. Its state machine keeps the original name:
**`<GetInventionsBulkServiceCall>d__44$$MoveNext`** **`0x94E76C0`** (owner typedef #22322
`RecNet.Inventions`, found via the nested-type table — `mfind` cannot see the outer name because
the method itself is obfuscated while the compiler-generated state machine is not).

| what | value | evidence |
|---|---|---|
| path | `api/inventions/v2/batch` | literal **`0xFC526C0`**, 2 refs, both in `0x94E76C0`; no `String.Format` |
| verb | **GET or POST, decided by `ids.Count`** | `0x94E77E4 call 0x9551FC0` = `RecNet.HBEADHYKUCU.GCPOFRCEWMT(count, 100)` — see below |
| service | **2 = API** | `mov r8d, 2` at `0x94E780B`, into `RGBOOBRDHEB..ctor(HttpMethod, Service, string)` `0x8BBF9E0` at `0x94E7817` |
| params | **one repeated `id`** | literal `id` **`0xFC526C8`** at `0x94E7830`, into generic `NJPEKLKCVCG<long>` `0x3E51520` |
| JSON body | **none** | no `FZNGWUAGAIN` / `YHPVSAVMRFS` in the method |
| client cache | none in the request | the *caller* caches — see **The batching coalescer** |

A null `ids` throws before the request (`0x94E77AC test r8,r8; je` → NRE helper `0xC403A0`).

### The verb is chosen by the number of ids

```
0x94e77b5  xor ecx,ecx ; mov rdx,<IReadOnlyCollection`1<long>> ; call 0x2350
                                      ; interface-slot-0 invoker = ids.Count  -> eax
0x94e77da  xor r8d,r8d ; mov edx,0x64 ; mov ecx,eax
0x94e77e4  call 0x9551fc0              ; HBEADHYKUCU.GCPOFRCEWMT(count, 100) -> HttpMethod
```

`GCPOFRCEWMT(int a, int b)` `0x9551FC0` is a two-line picker:

```
0x9551ff1  cmp edi, ebx ; jge 0x955204e   ; count >= threshold ?
0x955203b  mov rax,[rax+0x20] ; mov rax,[rax+8]    ; count <  100 -> HttpMethod.Get  (+0x08)
0x9552099  mov rax,[rax+0x20] ; mov rax,[rax+0x20] ; count >= 100 -> HttpMethod.Post (+0x20)
```

➡️ **`POST api/inventions/v2/batch` is the ≥100-ids case only.** In normal play the client sends
**GET**, because the batching coalescer in front of this route flushes small batches. A server that
only routes POST will 404/405 every ordinary invention fetch. Route **both verbs to the same
handler**, and read the ids from the query string *or* the form body.

### The ids are a repeated parameter, never a list literal

`NJPEKLKCVCG<T>(string name, IReadOnlyList<T> values)` `0x3E51520` is the generic member of the
verb-dependent parameter family ([elhkhfjehlm-verb-dependent-params](../conventions/elhkhfjehlm-verb-dependent-params.md)):

```
0x3e515b2  mov rax,<HttpMethod statics> ; mov rdx,[rax+0x20] ; mov rdx,[rdx+8]   ; HttpMethod.Get
0x3e515bc  mov rcx,r14                  ; r14 = request->JLFBPBGZQJS (verb, +0x10)
0x3e515c7  call HttpMethod::op_Equality
0x3e515dc  lea r9,[rdi+0x28]            ; GXDEVTXLNLF = query-string list
0x3e515e8  jne 0x3e515ee                ; verb == GET -> keep +0x28
0x3e515ea  lea r9,[rdi+0x30]            ; otherwise   -> ODWNBEXQFEH = form-urlencoded body list
```

and the explicit-list overload `0x3E51350` is a plain `for (i = 0; i < values.Count; i++)` that
**boxes each element and calls the single-value `NJPEKLKCVCG(string, object, List<KVP>)` `0x9538350`
once per id** (`0x3E514AE`, loop back-edge `0x3E514B9`).

| ids.Count | wire |
|---|---|
| 1 … 99 | `GET api/inventions/v2/batch?id=1&id=2&id=3` |
| ≥ 100 | `POST api/inventions/v2/batch` · `application/x-www-form-urlencoded` · `id=1&id=2&…` |

⚠️ **Not** `ids=`, **not** `id=1,2,3`, **not** a JSON array. A null list adds nothing
(`0x3E51382 test rbx,rbx; je`), so an empty batch sends the bare path with no `id` at all — answer
`[]`, not an error.

### One batch-only knob

`0x94E784D call 0x9538730` = `RGBOOBRDHEB.NUIBPXHZBHT()`, which sets the `Nullable<int>` field
`SITKKODGYPP` (`+0x58`, the one paired with `DOUWIZVKIPW` = `Nullable<TimeSpan>`) to **2** and
returns `this`. All **26** of its call sites are bulk/batch service calls
(`<GetAccountsBulkServiceCall>d__120`, `<GetCurrentOutfitsBulkServiceCall>d__32`,
`<GetSavedOutfitsServiceCall>d__33`, `<GetUGCPurchasableItemsByIdsServiceCall>d__7`,
`<GetPurchaseOffersForCurrencyBatchAsync>d__34`, `<GetSimpleSummariesOfInstancesOfRooms>d__169`, …),
so it is a retry/timeout-class setting specific to batch requests. ⚠️ **Its consumer was not read** —
the value 2 is confirmed, the meaning is inference.

## Response — bare array

```json
[ { "InventionId": 7, "ReplicationId": "…", "CreatorPlayerId": 205, "Name": "Thing",
    "Description": "", "LongDescription": "", "ImageName": null, "UgcVersion": 1,
    "CurrentVersionNumber": 1, "LatestVersionNumber": 1, "Accessibility": 1,
    "ForceCannotPublish": false, "ModifiedAt": "2026-10-28T00:00:00Z",
    "CreatedAt": "2026-10-28T00:00:00Z", "FirstPublishedAt": null, "CreationRoomId": null,
    "NumPlayersHaveUsedInRoom": 0, "NumDownloads": 0, "CheerCount": 0,
    "CreatorPermission": 100, "GeneralPermission": 20, "IsAgInvention": false,
    "IsCertifiedInvention": false, "IsRecRoomApproved": false, "AllowTrial": false,
    "Price": null, "HideFromPlayer": false, "DisplayMetadataJson": "{\"0\":47,\"99\":0}" } ]
```

Two independent checks agree it is **bare**:

- The send is `ZWUODKCINOA<List<RecNet.Invention>>(ct)` (`0x94E785B`, methodSpec generic inst
  **#1096 = `List<RecNet.Invention>`**), and the awaited result goes **straight into
  `AsyncTaskMethodBuilder<T>.SetResult`** at `0x94E78DD`. There is **no `FQWUEPYTLAQ` collapse at
  all** — neither the value-less `0x942D310` nor the generic `0x3C092F0`.
- The **envelope oracle** ([2026-send-helper-tiers](../conventions/2026-send-helper-tiers.md)):
  `RecNetResultObject_Invention` does **not** exist. The only near hit is
  `RecNet.RecNetResultObject_InventionResponse` (`.ctor 0x953A020`), which belongs to
  [v9/save](inventions-v9-save-wire-shape.md) / [v4/publish](inventions-v4-publish-wire-shape.md) /
  [v2/metadata](inventions-v2-metadata-wire-shape.md) — different DTO, different routes.

Belongs on [nonobject-response-routes](../conventions/nonobject-response-routes.md): `{}` cannot
deserialize into a `List`. **Serve `[]` for "nothing", never `{}`, `null` or an empty body.**

### `RecNet.Invention` — 28 keys, formatter `Utf8Json.Formatters.RecNet.PTEUMTQNOBK`

`.ctor` **`0x94C8EE0`** (confirmed by `msig`:
`Deserialize(JsonReader, …) -> RecNet.Invention`). `____stringByteKeys` is the trailing
single-casing run starting **`0x94C9DDE`**; `ftypes` gives 28 fields, so 28 keys 1:1 in declaration
order:

`InventionId`, `ReplicationId`, `CreatorPlayerId`, `Name`, `Description`, `LongDescription`,
`ImageName`, **`UgcVersion`**, `CurrentVersionNumber`, `LatestVersionNumber`, `Accessibility`,
`ForceCannotPublish`, `ModifiedAt`, `CreatedAt`, `FirstPublishedAt`, `CreationRoomId`,
`NumPlayersHaveUsedInRoom`, `NumDownloads`, `CheerCount`, `CreatorPermission`, `GeneralPermission`,
**`IsAgInvention`**, `IsCertifiedInvention`, `IsRecRoomApproved`, `AllowTrial`, `Price`,
`HideFromPlayer`, `DisplayMetadataJson`.

Types, obscured fields, the `DisplayMetadataJson` nested-JSON-as-string trap and the permission enum
are all unchanged from [inventions-v2-search](inventions-v2-search-wire-shape.md). Enums re-checked
on 2026 and **identical**: `RecRoom.DataLayer.UgcAccessibility` = `Private 0` / `Public 1` /
`Unlisted 2`; `RecRoom.DataLayer.InventionPermission` = `Unassigned 0`, `LimitedOneUseOnly 10`,
`DisallowKeyLock 15`, `UseOnly 20`, `EditAndSave 40`, `Publish 60`, `Charge 80`, `Unlimited 100`.

#### ⚠️ Key drift: `IsAGInvention` → `IsAgInvention`

| build | Original | camelCase | lowercase |
|---|---|---|---|
| `20250718.01` | `IsAGInvention` | `isAGInvention` | `isaginvention` |
| `20260323.14` | **`IsAgInvention`** | `isAgInvention` | `isaginvention` |

Utf8Json matches keys **exactly**, so a server still emitting `IsAGInvention` has that field
**silently dropped** by the 2026 client and the bool reads `false`. `UgcVersion` also moved from the
end of the declaration order to position 8 — that only affects client→server serialization order,
not what the client accepts.

➡️ The portable fix if you serve both builds: emit the **all-lowercase** `isaginvention`, which is
accepted by *both* (it is the only casing the two spellings share).

### The post-deserialize hook is real on this DTO

**`RecNet.Invention.IULRMJBAHPG()` `0x94D2FC0` is `OnDeserializedAsync`** — the nested type is
literally `<OnDeserializedAsync>d__122` (`MoveNext` **`0x94E7E30`**), which settles what the
`IULRMJBAHPG` virtual is across every DTO on this build. It does two things:

1. Re-encrypts the Obscured fields — six `Obscured{Long,Int,Bool}.OOBOIWNJMNP` calls at
   `0x94E7F37`…`0x94E7FB0` (1 long, 1 int, 4 bool). This is the independent proof that the
   `Obscured*` members arrive as **plain JSON numbers/bools**.
2. **Awaits three text-sanitization calls**, interface slot **20** on `RecNet.AQWHEEVHLXV` =
   **`SanitizeDisplayTextAsync(string displayText, SanitizeMode sanitizeMode, bool isChat)`**,
   invoked with `sanitizeMode = 3`, `isChat = false` (`0x94E8013`…`0x94E8030`, repeated at
   `0x94E809A` and `0x94E8118`) — i.e. once each for `Name`, `Description`, `LongDescription`.

So every row costs three awaited sanitizer round-trips before the array resolves. The hook itself
has no literals and no throw of its own; the only `je` into the NRE helper (`0x94E8484`) guards the
**sanitizer service** from `RecNet.Core` statics `+0x20/+0x28`, not the strings. Still: serve
`""` rather than `null` for `Name` / `Description` / `LongDescription`, since all three are fed
straight into that call.

## The batching coalescer in front of the route

`DOEFRIAWEWS` has **0 direct call sites** — it is installed as the `ServiceCall<long, Invention>`
delegate of a **`RecNet.MNLGCORXIOE<long, RecNet.Invention>`** (generic inst **#5865**) held in
`RecNet.Inventions` statics at **`+0x88`**. Public entry:

**`RecNet.Inventions.FRLWKCUJDZH(IEnumerable<long> ids)`** **`0x94A6A40`** →
`MPVTAJGPRUT<List<Invention>>`, which calls
`MNLGCORXIOE<long,Invention>.Get(ids, shouldOverrideCachedResult: null, ct: default)` **`0x7077CA0`**
and converts the task with `SAXZOKINUQZ::CTZMMSFIPBH<List<Invention>>`.

`MNLGCORXIOE`'s own method names survive in its nested state machines, which is what the class
actually is: `Get`, `GetWithCachedIdList`, `GetCachedIdList`, `GetAndSortResults`,
`InvokeServiceCall`, `ProcessPendingRequestsImmediate`, `ScheduleBatchProcess`,
`DelayUntilReadyToProcessPendingRequests`. Fields `NQTIDHQQSDY` / `RQLHBBSXTST` are
`Dictionary<long, TaskCompletionSource<Invention>>` — one pending promise **per requested id** — plus
an `IDictionary<long,Invention>` cache, an `IEqualityComparer<long>` and a `getBatchDelay` func.

⚠️ **Unverified, and it matters:** because the coalescer completes one `TaskCompletionSource` per
*requested* id, an id the server omits from the array may leave its promise **pending forever**
rather than resolving to null. The distribution body (`GetAndSortResults` / `LGYOWDVMORG`) is
generic-shared and reached through RGCTX indirection (`[rax+0xb8]+0x170`), so it could not be read
with `callxref`/`rangedis` here. Until that is settled, **return exactly one row for every requested
`id`** and never silently drop unknown ones.

Consumers of `FRLWKCUJDZH` (`callxref`, 5 sites):

- `RecRoom.Core.Creation.ASFWGVAMISZ$$ZAUCKQNGYZB` `0x1C4DB70`
- `RRUI.Data.InventionListModel$$GetInventionsInOriginalOrder` `0x266D1F0`
- `RecNet.Clubs$$IFOOYQECSAC` `0x9463930`
- `RecNet.Inventions$$ETNUQLSJKPV` `0x94A65D0`
- `RecNet.Inventions$$WHOLKVZHULR` `0x94AC250`

## Leads

The 26 `NUIBPXHZBHT` call sites are the full list of batch routes on this build, and several are
underived: `GetAccountsBulkServiceCall` `0x9434A70`, `GetCurrentOutfitsBulkServiceCall` `0x9522DA0`,
`GetSavedOutfitsServiceCall` `0x95246E0`, `GetUGCPurchasableItemsByIdsServiceCall` `0x95A0F10`,
`GetPurchaseOffersForCurrencyBatchAsync` `0x957D740`,
`GetSimpleSummariesOfInstancesOfRooms` `0x9508910`, `<GetInventionsByCreators>b__0` `0x94E9E40`.
Each is a candidate for the same **GET-under-100 / POST-at-100 + repeated-param** pattern, which is
worth assuming and then confirming before writing any of them down.
