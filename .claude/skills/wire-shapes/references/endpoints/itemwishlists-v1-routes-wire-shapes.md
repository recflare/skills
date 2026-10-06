# Econ api/itemWishlists/v1 routes wire shapes

> All four itemWishlists routes are svc 28 Econ and share ONE 5-key DTO `AMJGGOKLEGL`
> (`{WishlistItemId:Guid, AccountId, PurchasableItemId, CustomAvatarItemId:Guid?, CreatedAt}`).
> `GET .../wishlist/{me|id}?True|?False` is a **bare array**; `POST .../wishlist/add` and
> `.../wishlist/remove` are **enveloped** `{Value:<one entry>, Success, Error, error_id}`;
> `POST .../isonwishlist/bulk` is a **bare array of booleans**.
> The `?True`/`?False` is a **keyless query string** — a raw `bool.ToString()` appended after `?` —
> so the server cannot bind it and the two variants are indistinguishable on the wire.

Derived **2026-10-05** from build `20250718.01`.
Facade **`.MOCMPLCDBHE`** — 7 methods, all four routes plus one cache-invalidation helper.
Service **28 = Econ** on every one (`mov r8d, 0x1c`), so the host is `econ.<host>`, not `api.<host>`.

## The facade, from carved metadata

`py msig.py MOCMPLCDBHE` gives the signatures outright — worth doing before any disassembly on a
facade this small:

```
static void                             JFFFKOLLOLJ()    # cache invalidate
static KPIPLFECKNC<AMJGGOKLEGL>         DAFHDJLKDED(int? purchasableItemId, Guid? customAvatarItemId)
static JCFICNGFDLA                      HNGHJAGCFBI(int? purchasableItemId, Guid? customAvatarItemId)
static KPIPLFECKNC<List<AMJGGOKLEGL>>   EIMEGHPANAC(int accountId, bool flag)
static KPIPLFECKNC<List<bool>>          JONNEINHLHE(List<int> accountIds, int? purchasableItemId, Guid? customAvatarItemId)
```

| route | verb | entry | wire `T` |
|---|---|---|---|
| `api/itemWishlists/v1/wishlist/{me\|id}?{bool}` | **GET** | `EIMEGHPANAC` `0x7C90FF0` | inst #16679 = **`List<AMJGGOKLEGL>`** — bare |
| `api/itemWishlists/v1/wishlist/add` | **POST** | `DAFHDJLKDED` `0x7C90C60` | inst #1000 = **`KGOJLHJNIOD<AMJGGOKLEGL>`** — enveloped |
| `api/itemWishlists/v1/wishlist/remove` | **POST** | `HNGHJAGCFBI` `0x7C91410` | inst #1000 = **`KGOJLHJNIOD<AMJGGOKLEGL>`** — enveloped |
| `api/itemWishlists/v1/isonwishlist/bulk` | **POST** | `JONNEINHLHE` `0x7C91820` | inst #2705 = **`List<bool>`** — bare |

Every one sends with `MGPBDIAGCFD.HPBKMCLEANE<T>` — **response required**, no nullable tier, no
fire-and-forget. Verbs read from the `HttpMethod` static offset loaded before `AKJEAMCCEOH..ctor`:
`[rcx+8]` = GET on the read, `[rcx+0x20]` = POST on all three writes. **`remove` is a POST, not a
DELETE.**

## The DTO — `.AMJGGOKLEGL`, 5 keys

Formatter **`CAOPMHJOOCP` `.ctor 0x7E73710`** (+0x760). The trailing `____stringByteKeys` run is
`0x7E73C5C`..`0x7E73D94` — 5 keys, 1:1 with the 5 declared fields in offset order:

| # | key | CLR | off |
|---|---|---|---|
| 1 | `WishlistItemId` | **`System.Guid`** | 0x10 |
| 2 | `AccountId` | int | 0x20 |
| 3 | `PurchasableItemId` | int | 0x24 |
| 4 | `CustomAvatarItemId` | **`Guid?`** | 0x28 |
| 5 | `CreatedAt` | DateTime | 0x40 |

```json
{ "WishlistItemId": "8f0c1e4a-2b77-4b16-9a3e-5dbcfd7f2865",
  "AccountId": 205, "PurchasableItemId": 1534,
  "CustomAvatarItemId": null, "CreatedAt": "2026-10-05T00:00:00Z" }
```

An avatar-item row is the mirror image — `PurchasableItemId: 0` and a real `CustomAvatarItemId`:

```json
{ "WishlistItemId": "…", "AccountId": 205, "PurchasableItemId": 0,
  "CustomAvatarItemId": "c3ed9841-1b4a-40a6-b266-5dbcfd7f2865",
  "CreatedAt": "2026-10-05T00:00:00Z" }
```

⚠️ **`WishlistItemId` is a Guid, not an int.** The row's primary key has to be a GUID server-side.
Utf8Json's Guid formatter wants the plain 36-char dashed form — no braces, no `N` format — and
throws `NKJABNHBPCA` on anything else, *inside* the formatter, so the send helper never wraps it as
`IONCMJIACFI` (compare [number-token-parsing-exception](../conventions/number-token-parsing-exception.md)).

⚠️ **`PurchasableItemId` is a plain `int`, not `int?`** — there is no null to send for an avatar-item
row. `AMJGGOKLEGL.CPOBHIECLEN` is the shared no-op `0xA60520`, so every key is omittable and a
missing `PurchasableItemId` lands as `0`. `CustomAvatarItemId` *is* nullable, so `null` is correct
there.

`WishlistAccountId` (slot `0xD106CC8`) looks like a sixth key but is **not one** — its only
references are `RRUI.Data.StoreItemListModel.AIIBEEHNMPD` and
`LMHBMKDLJKC.GetLegacySourceMetadataStringFromQueryData`, i.e. a UI/analytics field name. Confirm a
candidate key by xrefing it into the formatter `.ctor`, not by its plausible spelling.

## `GET wishlist/{me|accountId}?{True|False}` — bare array

Path is built in one `String.Format`, not from a baked route literal:

```
String.Format("{0}/v1/wishlist/{1}?{2}", "api/itemWishlists", "me"|accountId.ToString(), flag.ToString())
```

literals `'api/itemWishlists'` `0xD137990`, `'{0}/v1/wishlist/{1}?{2}'` and `'me'`; `String.Format`
at `0x7C912CD`. The account id is an `ObscuredInt` (`ObscuredInt$$MJOOONLKLLN` at `0x7C911BD`)
decoded to a plain int before `Int32.ToString`.

**No `ELHKHFJEHLM`, no `ELKIBCPINAP`** — no query params and no body. The only other builder call is
`MGPBDIAGCFD.DIDJOECFJII` at `0x7C91312`, the **response-cache TTL = `TimeSpan.FromSeconds(5.0)`**
(the constant at `0x9DDBFD0`), not a parameter.

Serve a **bare JSON array**; `{}` throws `IONCMJIACFI`
([ioncmjiacfi-malformed-response](../conventions/ioncmjiacfi-malformed-response.md)). An empty wishlist is `[]`.

### ⚠️ `?True` / `?False` is a keyless query string

The bool is appended straight after `?` with no parameter name, so the request line is literally

```
GET /api/itemWishlists/v1/wishlist/me?True
GET /api/itemWishlists/v1/wishlist/me?False
```

ASP.NET parses that as a single valueless key, so **no model binder can recover the bool** — the two
variants are indistinguishable to a server that reads query parameters by name. Implement **one
handler** for `GET /api/itemWishlists/v1/wishlist/{accountId}` plus the `me` alias and ignore the
query string entirely. Do not route on `?True`/`?False`, and do not 400 on the nameless key.

The bool's *meaning* was **not determined**. Three of the four call sites pass `false`
(`RRUI.Data.StoreItemModel.JELCJOLCBKI`, `RRUI.Data.CustomAvatarItemModel.JELCJOLCBKI`,
`RecRoom.AppUI.Data.StoreItemQueryManager.<GetStoreItemsFromWishlist>d__24`) and one passes `true`
(`HLCDLKHPMFJ.MoveNext` `0xB9B030`, `mov dl, 1` at `0xB9B2BD`). Since the server cannot read it
anyway, this only matters if a future build starts naming the parameter.

### The two baked `me?True` / `me?False` literals are CACHE KEYS

`api/itemWishlists/v1/wishlist/me?False` (`0xD138458`) and `...me?True` (`0xD1387F0`) exist as
**whole-route literals**, which makes them look like the request paths. They are not — their only
reference is `MOCMPLCDBHE.JFFFKOLLOLJ` `0x7C917A0`, which calls
`NNMGBLLLIAH.BMICOFMDHAB(0x1c, <literal>, 0)` once per literal: a **cache invalidation** of the two
TTL'd entries, keyed by full path. It is reached from `<>c.ILNEOEFNPBA` `0x7C99DC0` — the add route's
success continuation — and from `<>c.EDOOIDCBPLG` `0x7C99330`.

Generalisable: a whole-route literal referenced only by a method that also references *sibling*
route literals and calls into a cache class is an invalidation list, not a request. Find the real
path by looking for the `String.Format` that reproduces it.

## `POST wishlist/add` and `POST wishlist/remove` — enveloped

Whole-route literals `'api/itemWishlists/v1/wishlist/add'` `0xD1380C0` and
`'.../wishlist/remove'` `0xD138B88` — these two *are* the request paths (each is referenced twice
inside its own entry method, once for the `lea` init and once as the `AKJEAMCCEOH..ctor` path
argument at `0x7C90E1A` / `0x7C915CA`).

### Request — form body, both params always sent

Both methods add exactly two parameters via `MGPBDIAGCFD.ELHKHFJEHLM`:

| param | CLR |
|---|---|
| `purchasableItemId` | `int?` |
| `customAvatarItemId` | `Guid?` |

Because the verb is **POST**, `ELHKHFJEHLM` puts these in an
`application/x-www-form-urlencoded` **body**, not the query string — see
[elhkhfjehlm-verb-dependent-params](../conventions/elhkhfjehlm-verb-dependent-params.md). Reading it as a query param
mis-specifies both routes.

⚠️ **Neither add is guarded by `get_HasValue`.** The two `ELHKHFJEHLM` calls at `0x7C90E4A` and
`0x7C90E8B` are unconditional; the `Nullable<T>` is boxed first (`call 0x9CBDE0` at `0x7C90E35` and
`0x7C90E6D`), and IL2CPP boxing a `Nullable<T>` with `HasValue == false` yields a **null reference**.
So the empty one reaches the adder as a null value. The server must accept **either** field missing
**or** present-and-empty, and must not require both:

```
POST /api/itemWishlists/v1/wishlist/add
Content-Type: application/x-www-form-urlencoded

purchasableItemId=1534&customAvatarItemId=
```

The caller supplies whichever one applies: `RRUI.Data.StoreItemModel.ToggleIsWishlisted` passes the
`purchasableItemId`, `RRUI.Data.CustomAvatarItemModel.ToggleIsWishlisted` the
`customAvatarItemId` Guid. Both call `add` and `remove` from the same method, picking by current
state.

### Response — `KGOJLHJNIOD<AMJGGOKLEGL>`

```json
{ "Value": { "WishlistItemId": "8f0c1e4a-2b77-4b16-9a3e-5dbcfd7f2865", "AccountId": 205,
             "PurchasableItemId": 1534, "CustomAvatarItemId": null,
             "CreatedAt": "2026-10-05T00:00:00Z" },
  "Success": true, "Error": null, "error_id": null }
```

`Value` first, then `Success` / `Error` / lowercase `error_id`. A **bare** entry object with no
envelope, or a `204`, raises `LLCLDPPAGIJ`
([llcldppagij-envelope-failure-exception](../conventions/llcldppagij-envelope-failure-exception.md)) — the same failure as
`Success: false`.

`remove` deserializes the **same** instantiation (`inst #1000`) even though its declared return type
`.JCFICNGFDLA` carries no value: the body is parsed as `KGOJLHJNIOD<AMJGGOKLEGL>` and the `Value`
discarded. **Return the removed entry anyway.** `{"Value": null, "Success": true}` parses too, but
the full entry is what the formatter is built for and costs nothing.

On success the add route runs `JFFFKOLLOLJ`, dropping both `wishlist/me?True` and `?False` cache
entries, so the next `GET` is a real request rather than a 5-second-cached one. A server that 200s
the add but does not persist the row therefore shows the item un-wishlisted again **immediately**,
not after a delay — so a flicker-back is a persistence bug, never a cache one.

### `'Wishlist full!'` is client-side

The literal `0xD106930` is used only inside `RRUI.Data.StoreItemModel.ToggleIsWishlisted` and
`CustomAvatarItemModel.ToggleIsWishlisted`, shown through `RRUI.Data.ToastListModel.AddMessageToast`
(`0xB71114`) off bit tests on the model (`test byte ptr [rsi+0x1a0], 4` at `0xB710C8`). It is **not**
read from the envelope's `Error`, and the cap is enforced *before* the request is made — a
server-side limit cannot produce that message. `'Wishlist error: '` (`0xD106588`) is the string that
renders `Error` verbatim, so keep `Error` user-presentable.

## `POST isonwishlist/bulk` — bare array of booleans

`JONNEINHLHE` `0x7C91820`, literal `'api/itemWishlists/v1/isonwishlist/bulk'` `0xD137D28`. Params,
all in the **form body** (POST):

| param | CLR |
|---|---|
| `accountIds` | `List<int>` — added through the generic `ELHKHFJEHLM` (inst #42 = `int`) |
| `purchasableItemId` | `int?` |
| `customAvatarItemId` | `Guid?` |

Response is inst #2705 = **`List<bool>`** — a bare positional array, one element per entry of
`accountIds`, in the same order:

```json
[true, false, true]
```

`{}` throws `IONCMJIACFI`; `[]` parses but silently means "nobody has it", and a short array means
the tail of `accountIds` reads as unset. Error literals
`'Failed to check wishlist for players'` and `'Attempted to get wishlist with invalid Account ID'`
(the non-`{0}` variant — the `{0}` one belongs to the GET route).

## Consumers

| route | callers |
|---|---|
| GET `wishlist/{id}?{bool}` | `RRUI.Data.StoreItemModel.JELCJOLCBKI` `0xB6C930`, `RRUI.Data.CustomAvatarItemModel.JELCJOLCBKI` `0x264C370`, `HLCDLKHPMFJ.MoveNext` `0xB9B030`, `StoreItemQueryManager.<GetStoreItemsFromWishlist>d__24` `0x7EFD960` |
| add / remove | `RRUI.Data.StoreItemModel.ToggleIsWishlisted` `0xB70FC0`, `RRUI.Data.CustomAvatarItemModel.ToggleIsWishlisted` `0x264EBC0` |

`RRUI.Data.WishlistModel` (`get_WishlistItems` `0xAD9F30`, `get_IsLocalWishlist` `0xBAE560`,
`get_OwnerAccountId` `0xBAE600`, `GetEmptyWishlistMessage` `0xBADE80`, `TryGetPreviewWishlistItem`
`0xBAE3A0`) is the view model over the GET's array — unobfuscated names, useful for reading the UI's
expectations directly.

## How the methodSpec operands were read

`slots2025.py` prints `<generic inst class=-1 method=N>` on a kind-6 MethodRef slot, where **`N` is a
genericInst index**, resolved with `ginst.py inst N` — *not* a methodSpec index for `ginst.py spec`.
`spec 1000` here resolves to an unrelated `<>c` lambda, which is how a wrong envelope conclusion
would have been reached. The same `N` repeating across several MethodRefs in one method
(`DCEKGPHGICM::MLJHEDNMIEE`, `JMNHOAIMFBC::AOCLNBFKPEP`, `MGPBDIAGCFD::HPBKMCLEANE` all at
`method=1000`) is expected, not a tool failure — they are the task-continuation chain over the same
`T`.
