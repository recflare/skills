# PUT curatedlists/{listName}/items/{itemId}/createlistifneeded — the Saved-for-Later toggle

> This is the **add half of "Save for Later"**. It returns a **bare `RecNet.Lists.CuratedListDTO`** —
> the same 8-key object as `curatedlists/bulk`, no envelope. The request is a **form-urlencoded body**
> `accessibility=<int>&type=<int>` (PUT, so `NJPEKLKCVCG` puts params in the body, not the query).
> **`ItemIds` in the response must contain the item id as a decimal string**, because the client
> caches the returned DTO and the next toggle decides saved-vs-not with
> `ItemIds.Contains(roomId.ToString())`. A `null`/`204` answer **throws a NullReferenceException**
> inside the client's own wrapper.

Derived **2026-10-16** from build `20260323.14`, answering "what's the response shape of
`PUT https://lists.recflare.net/curatedlists/__SavedForLater_Rooms/items/2576/createlistifneeded`".

## The route

Service **13 Lists**, facade `RecNet.Lists.PZONXXKUWMN`. The path is **not** a format string — it is
`String.Concat` of five pieces, which is why grepping the full path finds nothing:

```
"curatedlists/" + listName + "/items/" + itemId + "/createlistifneeded"
   0xFDD79B0                   0xFC7BBE0            0xFC78A38
```

⚠️ The sibling literal `"curatedlists/{0}/items/{1}"` (`0xFDD9758`) belongs to the **plain** add
(`<AddItemToCuratedList>d__19`) and the remove (`<RemoveItemFromCuratedList>d__21`) — a different
route with no `/createlistifneeded` suffix.

```
RecNet.Lists.PZONXXKUWMN.VXGQEWWPUDD(string listName, string itemId,
                                     RecNet.Lists.EntityType type,
                                     RecRoom.DataLayer.UgcAccessibility accessibility,
                                     CancellationToken ct)
        -> Task<RecNet.Lists.CuratedListDTO>
state machine  <AddItemToCuratedList>d__20$$MoveNext      0x95ec200 .. 0x95ec623
```

- **Verb PUT** — `HttpMethod` statics `[+0x28]`, read at `0x95ec393`
  (`mov rcx,[rax+0x20]` = static_fields, `mov r13,[rcx+0x28]`).
- Send is `MSBYXMTYOOH<T>(string friendlyActionDescription, HttpMethod, route, ct, Action<RGBOOBRDHEB>)`
  with the generic method inst **#3137 = `RecNet.Lists.CuratedListDTO`** — so **bare `T`**, per
  [2026-send-helper-tiers](../conventions/2026-send-helper-tiers.md). The description literal is
  `'add item to list'` (`0x95ec4a9`) and, on 2026, carries no information.
- Both path segments are **strings** on the wire side: the state machine stores them as object refs
  at `+0x30` / `+0x38` and concatenates them with no `ToString` call, so the item id arrives already
  stringified by the caller.

### Request — a form-urlencoded body, two fields

The `Action<RGBOOBRDHEB>` is the display-class lambda `.JSKXOTRANKO::LIUYXOZUUDH`
`0x95e7ba0 .. 0x95e7c51`:

```
0x95e7c05  RGBOOBRDHEB::NJPEKLKCVCG("accessibility", <int>)
0x95e7c3b  RGBOOBRDHEB::NJPEKLKCVCG("type",          <byte>)
```

`NJPEKLKCVCG` is the **verb-dependent** adder — GET puts params in the query, every other verb puts
them in an `application/x-www-form-urlencoded` body
([elhkhfjehlm-verb-dependent-params](../conventions/elhkhfjehlm-verb-dependent-params.md)). The verb
here is PUT, so:

```
Content-Type: application/x-www-form-urlencoded

accessibility=0&type=1
```

| field | CLR type | values |
|---|---|---|
| `accessibility` | `RecRoom.DataLayer.UgcAccessibility : int` | **Private 0**, Public 1, Unlisted 2 |
| `type` | `RecNet.Lists.EntityType : byte` | Accounts 0, **Rooms 1**, Inventions 2, CustomAvatarItems 3, PurchasableItems 4, Generic 5, ChipAndPort 6, DiscoverySection 7, DiscoverySectionSubType 8 |

Both are **numeric** on the wire (no by-name enum formatter). For the Saved-for-Later call site the
constants are baked in at `0x196bb82`/`0x196bb85`: **`accessibility=0` (Private), `type=1` (Rooms)**.

The two values exist only so the server can *create* the list when it is missing — that is the whole
point of the `/createlistifneeded` suffix. The server must therefore:

1. find the caller's curated list named `{listName}` (`__SavedForLater_Rooms`),
2. create it with the given `type` + `accessibility` if absent,
3. add `{itemId}` to its `ItemIds`,
4. return the resulting list.

## Response — bare `RecNet.Lists.CuratedListDTO`, 8 keys

Formatter `Utf8Json.Formatters.RecNet.Lists.YOMLWJVCRKH` (msig-confirmed),
`.ctor 0x8f26350 .. 0x8f2691a`. `____stringByteKeys` order, with the field offset confirming each
pairing (`ftypes.py`/`fields2025.py` both resolve — this DTO is **completely unobfuscated** on 2026,
property names and `k__BackingField` names intact):

| # | key | CLR | offset |
|---|---|---|---|
| 1 | `ListId` | long | `0x10` |
| 2 | `CreatorAccountId` | int | `0x18` |
| 3 | `Name` | string | `0x20` |
| 4 | `Description` | string (nullable) | `0x28` |
| 5 | `ImageName` | string (nullable) | `0x30` |
| 6 | `Type` | `RecNet.Lists.EntityType` (byte enum, numeric) | `0x38` |
| 7 | `ItemIds` | `IReadOnlyList<string>` | `0x40` |
| 8 | `CreatedAt` | DateTime | `0x48` |

Three casings accepted per key (`ListId`/`listId`/`listid`, …). Identical key set, order and offsets
to the 2025 build ([curatedlists-bulk](curatedlists-bulk-wire-shape.md)) — this DTO did not move.

**`RecNet.Lists.CuratedListDTO` has 17 methods: 8 property pairs plus `.ctor`, and nothing else.**
There is **no post-deserialize hook at all**, so nothing validates the body. Every wrong or omitted
key fails silently as `0` / `null`.

For the question as asked:

```json
{
  "ListId": 90210,
  "CreatorAccountId": 12345,
  "Name": "__SavedForLater_Rooms",
  "Description": null,
  "ImageName": null,
  "Type": 1,
  "ItemIds": ["2576"],
  "CreatedAt": "2026-10-16T18:04:11.482Z"
}
```

`CreatorAccountId` is the **calling player's** account id; `2576` is the room id and belongs in
`ItemIds`, as a **decimal string**.

## ⚠️ The two things that actually matter

### 1. `ItemIds` must contain the item id, or the toggle breaks

The caller is
`<SetRoomSavedForLaterStateAsync>d__142$$MoveNext` `0x196b7b0 .. 0x196beb2`, and it is a **state
toggle that reads its own cached copy of this response**:

```
0x196ba38  r15 = roomId.ToString()
0x196ba49  rcx = this.<cachedList>        ; manager field +0xc8
0x196ba50  if (rcx == null) isSaved = false
0x196ba5f  else isSaved = Contains(rcx->[+0x40] /* ItemIds */, r15)
0x196ba6c  if (isSaved == desiredState) -> log and return          ; 0x196bc8e
...
0x196bb92  call RecNet.Lists.Client$$VXGQEWWPUDD                    ; the add
0x196bbec  this.<cachedList> = <the returned CuratedListDTO>        ; +0xc8, write barrier
```

So the returned DTO **becomes the client's truth** for whether the room is saved. If the response
omits `2576` from `ItemIds`:

- the heart/bookmark re-reads as **not saved** immediately,
- the "already in that state" guard at `0x196ba6c` never fires, and
- the next tap issues the same PUT again instead of the DELETE.

The guard's log literals are worth grepping for in `Player.log`:
`"Attempt to set a room, "` + `", to the same state in player's Saved for Later playlist (Id: "`.

### 2. `null` / `204` throws an NRE in the client's own wrapper

`RecNet.Lists.Client.VXGQEWWPUDD(...)` (`<AddItemToCuratedList>d__24` `0x95ecac0 .. 0x95ecf57`) is
the layer the UI actually calls. After awaiting the facade it does:

```
0x95ecd8e  test rbx, rbx ; je 0x95ecdba      ; IF (dto != null)
0x95ecd93    rsi = dto->ListId               ;   cache key
0x95ecdb5    RecNet.Lists.Client$$VUNVZAUYLFI(rsi, dto)   ; cache insert — GUARDED
0x95ece04  test rbx, rbx ; je 0x95ecf46      ; ...and then dereferences it again
0x95ece0d    r14 = dto->ListId               ; UNGUARDED
```

`0x95ecf46` is the IL2CPP null-throw helper `0xc403a0` → **`NullReferenceException`**. The author
guarded the cache insert and then dereferenced the same reference one block later, so the `!= null`
check buys nothing. Whether the send helper itself would have rejected the null first
(`ZWUODKCINOA` vs `LIRIDCJIGGA(bool)`) could not be read — `MSBYXMTYOOH<T>` is generic-shared over a
reference `T` and its body is absent from `methods.pkl` — but it does not matter: **both paths are
fatal, so always return the object.**

Non-2xx behaves as everywhere else: `RecNet.RecNetWebException: HTTP Error {0}` from
`MLREETGNUXI.VEIQCOEFCVM`. There is no in-band failure encoding on this route.

## The rest of the Saved-for-Later flow

`__SavedForLater_Rooms` is a client literal (`0xFD1BF58`, 10 refs). The list name is **not**
server-chosen — the client hardcodes it:

| step | method | route |
|---|---|---|
| feature gate | `<InitRoomSavedForLaterAsync>d__140` `0x1966000` | flag literal **`can_save_for_later`** (`0x196612c`) — false ⇒ the log line `Attempt to use Saved for Later playlist when not enabled for user` |
| find the list | `Client.VYRHNUPWUTE(name, EntityType, ct)` `0x1966206` | `GET curatedlists?creatorAccountId=&type=&name=__SavedForLater_Rooms` ([curatedlists-lookup-and-pagesource-names](curatedlists-lookup-and-pagesource-names.md)) |
| load it | `Client.QIBNREYRSLU(listId, EntityType, ct)` `0x19662e9` | `GET curatedlists/{listId}` |
| save | `Client.VXGQEWWPUDD(name, itemId, 1, 0, ct)` `0x196bb92` | **this route** |
| unsave | `Client.PFKOTQAEFBZ(listId, itemId, ct)` `0x196bab6` | `curatedlists/{listId}/items/{itemId}` — takes the **list id**, not the name, and also returns a bare `CuratedListDTO` |

⚠️ **Asymmetry worth knowing:** the add is keyed by **list name** and the remove by **list id**. The
remove therefore only works after the GET has populated the cache, which is why a broken
`curatedlists?name=` lookup shows up as "saving works, unsaving does nothing".

The same literal also reaches `RRUI.Data.RoomListModel.get_SourceLabelText` `0x280ebe0`,
`<GetCuratedPlaylistAsync>d__199` `0x2811c90` and
**`<QueryStaticListSource>d__24` `0x96db460`** — the last of which is the method NRE-ing in the
post-join residual items
([post-join-residual-log-items-2026](../../../rr-client-bringup/references/post-join-residual-log-items-2026.md)),
so `__SavedForLater_Rooms` is one of the static list sources that room-list query path asks for.

## Sibling tiers on this facade

Free from one `py msig.py PZONXXKUWMN` — **every curated-list route on svc 13 returns a bare
`CuratedListDTO`**, there is no envelope anywhere on this facade:

```
QIBNREYRSLU(long, ct)                                   -> Task<CuratedListDTO>
QIBNREYRSLU(int, EntityType, string, ct)                -> Task<CuratedListDTO>
KKACSDZQEBJ(IReadOnlyList<long>, ct)                    -> Task<List<CuratedListDTO>>   # bulk
UUJNXVPWCHM(EntityType?, ct)                            -> Task<List<CuratedListDTO>>
IPKDDKDFVQG(string, EntityType, UgcAccessibility, ct)   -> Task<CuratedListDTO>         # create
KKGFJHRBHNA(long, UgcAccessibility, ct)                 -> Task<CuratedListDTO>
TNGBJUOFLFJ(long, ct)                                   -> Task                         # delete, no body
QFENNHQPHTL / LWUAALNWJCY / QYAHSJGWGHF(long, string)   -> Task<CuratedListDTO>         # rename/describe/image
IUYAFODTPKS(long, IEnumerable<string>, ct)              -> Task<CuratedListDTO>         # set all items
VXGQEWWPUDD(long, string, ct)                           -> Task<CuratedListDTO>         # add by list id
VXGQEWWPUDD(string, string, EntityType, UgcAccessibility, ct) -> Task<CuratedListDTO>   # THIS ROUTE
PFKOTQAEFBZ(long, string, ct)                           -> Task<CuratedListDTO>         # remove
SetContextualFeatures(Dictionary<string,object>, ct)    -> Task<RecNet.RecNetResult>    # the one envelope
```

`RecNet.Lists.Client` mirrors each of these as a `static` with typed overloads
(`RoomDTO`/`Account`/`Invention` instead of a string id) that stringify the entity's id for you, then
call `Client.VUNVZAUYLFI(listId, dto)` to update the client cache.

## ⚠️ On `20250718.01` the SAME route is ENVELOPED (corrected 2026-10-16)

The response **body differs between builds**. 2025 wraps it; 2026 does not.

```
state machine  IMCOMMPAEDL$$MoveNext                      0x7E2B090
send           .FCKNCPNDBBM::PJPLCMBOAFB  <generic inst method=2891>   <- description-carrying tier
inst#2891      .OOCDKDLBGOI               = CuratedListDTO, the same 8 keys
description    'add item to list'
path           "curatedlists/" 0xD0489F0 + "/items/" 0xD250728 + "/createlistifneeded" 0xD24DC38
```

`PJPLCMBOAFB<T>` deserializes `{Value, Success, Error, error_id}`, asserts `Success`, and returns
`Value` — so on 2025 the server must send:

```json
{ "Value": { "ListId": 3437, "CreatorAccountId": 205, "Name": "__SavedForLater_Rooms",
             "Description": null, "ImageName": "DefaultRoomImage.jpg", "Type": 1,
             "ItemIds": ["2576"], "CreatedAt": "2026-10-16T18:30:35.198Z" },
  "Success": true, "Error": null, "error_id": null }
```

Answering the **bare** object on 2025 throws **`LLCLDPPAGIJ`** (`Success` absent ⇒ `false`) — observed
live, twice, on both this route and its `DELETE` sibling. The key set inside `Value` is identical on
both builds; only the wrapper differs. Full tier table:
[2025-facade-helper-tiers](../conventions/2025-facade-helper-tiers.md).

**The same applies to every curated-list write**, including the unsave
`DELETE curatedlists/{listId}/items/{itemId}` (`FONPJGBLNHE$$MoveNext` `0x7E260D0`,
`'remove item from list'`) — which sends **no request body** and still expects the envelope back.
The three GET routes stay bare on 2025.

## The rule

| answer | what the client does |
|---|---|
| **the 8-key object with `ItemIds` containing the item id** ✅ | cache updated, toggle consistent |
| the object with `ItemIds` missing the item id ❌ | silent — UI re-reads as *not saved*, next tap re-adds |
| `{}` ❌ | silent — `ListId 0`, `ItemIds null`, and `Contains` on a null list NREs on the next toggle |
| `200 null` / `204` ❌ | **NullReferenceException** in `<AddItemToCuratedList>d__24` at `0x95ece0d` |
| any non-2xx | `RecNetWebException: HTTP Error {0}`, no soft-failure channel |

**How to apply:** treat this as read-modify-write on the server and return the list *after* the add,
with `ItemIds` reflecting it. Echoing the request back as a stub is not enough here — unlike most
write routes, the response feeds a client-side cache that gates the next request.
