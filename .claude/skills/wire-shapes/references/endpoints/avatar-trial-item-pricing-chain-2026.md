# Swapping to a Full Body Avatar prices "trial items" — the chain that shows `$0` and then fails

> Switching avatar body type (classic -> **FBA**) turns the newly-required avatar items into
> **trial items**, and the avatar editor immediately prices them. The pricing call is
> `GetStoreItemsByIdsAsync`, which issues **two bulk POSTs in sequence** —
> `api/customAvatarItems/v1/bulk` then `api/storefronts/v1/purchasableitems` — and both expect a
> **BARE ARRAY**. A `{}` body from either one faults the whole chain with
> `RecNetMalformedResponseException: Malformed Response: '{}'`, the store-item list stays empty, the
> checkout dialog therefore totals **0**, and the purchase (and so the body-type swap) fails.
> The call is **fire-and-forget**, so the log carries no application stack frame — only HTTP plumbing.

Derived **2026-10-30** from build `20260323.14`, from a live `Player.log` failure.

# ✅ RESOLVED — the root cause was the DEFAULT AVATAR ITEMS, not this chain

Confirmed on the live server **2026-10-30**: fixing the bulk-pricing routes did **not** fix the FBA
swap. **Adding the missing FBA items to the default avatar-item list did.**

So read everything below as the *downstream* symptom, correctly mapped but not the cause:

```
default avatar-item list has no FBA entries
  -> the FBA-only slots (legs, shoes) and the FBA torso have nothing UNLOCKED to fall back on
  -> the editor fills them from browsable (unowned) items -> OutfitManager.IsTrialItem == true
  -> trial items get priced -> the two bulk POSTs below -> empty/`{}` -> total renders 0 -> fail
```

The two routes that seed that list are **`GET api/avatar/v1/defaultunlocked`** and
**`GET api/avatar/v1/defaultbaseavataritems`** (both svc **28 Econ**, bare arrays of the 10-key item
DTO) — shapes in [avatar-lockeditems-bulk](avatar-lockeditems-bulk-wire-shape.md). The body-type
fallbacks that consume them:

| accessor | RVA | note |
|---|---|---|
| `OutfitManager$$TryGetDefaultTorsoItem(out AvatarItem, RecRoom.Protobuf.AvatarBodyType, bool useDefaultCostumeTorsoItem)` | `0x1599130` | **takes the body type** — per-body-type default |
| `OutfitManager$$TryGetDefaultLegsItem(out AvatarItem)` | `0x1598CD0` | **FBA-only slot** |
| `OutfitManager$$TryGetDefaultShoesItem(out AvatarItem)` | `0x1598F00` | **FBA-only slot** |

All three read the **shipped** `AvatarItemWardrobeRuntimeConfig.Config` →
`ConvertToAvatarItemList`, then pick via `OutfitManager$$TryGetRandomItem` and
`OutfitManager$$TryGetRandomUnlockedItem`. The candidate list is baked into the client; **only the
"unlocked" filter is server-side**, which is exactly why a defaults list missing the FBA entries
leaves those slots unfillable while the classic body type keeps working.

➡️ **Diagnostic lesson:** legs and shoes do not exist on the classic body, so a defaults list that
is complete for classic can still be missing everything FBA needs. If an FBA swap prices items the
player should already own, **check the defaults list before touching any pricing route**.

⚠️ Related but distinct: a *hard failure* of this download is a login blocker, not an FBA bug —
`<DownloadDefaultAvatarItems>d__243` `0xFE91D0` raises `LOGIN_CODE_BLOCK` (19) at `0xFE948C`, i.e.
`Unable to login (code: block)` (see
[login-error-code-words-2026](../../../rr-client-bringup/references/login-error-code-words-2026.md)).
A list that is present but *incomplete* boots fine and only breaks the FBA swap.

## The symptom in the log

```
[13:31:35] [5412] [180.8986] [Exception] [Unity | Error] Malformed Response: '{}'
Exception: Deserialization returned null
  at RecNet.RGBOOBRDHEB.AIYNPFIEYFY[T] (RecNet.XJAFUXFVGPU a)
  at RecNet.RGBOOBRDHEB+TZATELUBAOF`1[a].MUKIUKVCLOC (RecNet.XJAFUXFVGPU a)
  at RecNet.RGBOOBRDHEB.YGADVOMHRVJ[TResponse] (System.Func`2[T,TResult] a, …)
  …
  at RecNet.RGBOOBRDHEB.LIRIDCJIGGA[TResponse] (System.Boolean a, …)   <- nullable-response send
Rethrow as RecNetMalformedResponseException: Malformed Response: '{}'
…
RecRoom.Async.SAXZOKINUQZ:KSNTDCQPEQA(Exception)
RecRoom.Async.XKMSFCDUWSV`1:IQQWXDIHGCW(Task`1)                        <- fire-and-forget sink
```

⚠️ **No `<…>d__N` frame appears**, unlike the Report-Room 404 — the task is not awaited by UI code,
it is handed to `XKMSFCDUWSV<T>.IQQWXDIHGCW` and logged by `SAXZOKINUQZ.KSNTDCQPEQA`. So the stack
alone cannot name the route; the chain below is how it was recovered.

Also note the clock: `Player.log`'s bracketed time runs **3 h behind** the UTC stamps the Dissonance
lines carry, so `[13:31:35]` here is **20:31:35 UTC** — use the UTC value when grepping a server log.

### Reading `AIYNPFIEYFY<T>`'s two failure messages apart

`RGBOOBRDHEB.AIYNPFIEYFY<T>` (generic-shared; the reference-type body contains
`0x6c6ce10`–`0x6c6d30a`, misattributed by `methods.pkl` to
`UnityEngine.Localization.Tables.AssetTableEntry$$set_PreloadAsyncOperation`) is:

```
0x6c6d135  deserialize body into T                      ; may throw JsonParsingException
0x6c6d239  'Deserialization returned null'              ; literal 0xFDDD6E0
0x6c6d24e  new System.Exception(msg)                    ; plain Exception, inner
0x6c6d28f  XJAFUXFVGPU$$AFXLACYVZDU                     ; re-read body as string
0x6c6d2bb  new RecNetMalformedResponseException("Malformed Response: '" + body + "'")
```

Both paths end as `Malformed Response: '<body>'`; the **inner** exception says which happened:

| body | inner exception | what it means |
|---|---|---|
| `[]` | `JsonParsingException: expected:'{', actual:'['` | T **is** an object — the verify-ing object formatter threw |
| `{}` | `Exception: Deserialization returned null` | the collection formatter accepted the token and yielded null — T is a **list/array/scalar** |

That is consistent with the pre-existing rule in
[ioncmjiacfi-malformed-response](../conventions/ioncmjiacfi-malformed-response.md): a `{}` body means
the route wants an **array or a scalar**. The same `Player.log` shows the mirror case 90 s earlier
(`Malformed Response: '[]'` at `[13:30:01]`, an object route fed an array).

## The chain, UI down to the wire

| step | method | RVA |
|---|---|---|
| body-type button | `RRUI.Data.AvatarTypeCustomizationModel$$SetAvatarBodyType` | `0x24CFBF0` |
| → applies it | `RRUI.Data.AvatarCustomizationModel$$SetAvatarBodyType` | — |
| → re-prices | `RRUI.Data.AvatarCustomizationModel$$UpdateTrialItemCost` | `0x249B6C0` (tiny — only `Model<T>.Broadcast`) |
| the fetch | `AvatarCustomizationModel$$RefreshTrialItemPurchaseInfo` / `<…>d__367$$MoveNext` | `0x2495350` / `0x24A0780` |
| → | `RecRoom.Storefronts.EJGLZIQDEVD$$LQEQRPAKIBB()` and `$$UILGGXLYOIC(ct)` = **`GetStoreItemsInternal`** | `0x10218E0`, `0x1021B70`; SM `<GetStoreItemsInternal>d__19$$MoveNext` `0x10316E0` |
| → | `RoomEconomy.Store.PRJHEOOIRTF.ITTHUHMXWEE(IReadOnlyList<UnifiedItemId>, bool)` → impl `ANIDAXYBRZA$$ITTHUHMXWEE` = **`GetStoreItemsByIdsAsync`** | `0xA1B07B0`; SM `<GetStoreItemsByIdsAsync>d__36$$MoveNext` `0xA1B7450` |

Both facade hops return `Task<List<RecNet.BRRULFGEELR>>` — generic inst **#1089**.
**`RecNet.BRRULFGEELR` is an INTERFACE**, not a DTO (`msig` shows 11 getters, `fields2025` shows 0
fields: `ItemType`, `Id`, `FriendlyName`, `ThumbnailImageFilename`, `IsFeatured`, `SubscribersOnly`,
`Rarity`, `ConsumableItemDesc`, `AvatarItemType`, `GiftBoxContent`, `IsQueryGiftDrop`). It is the
unified store-item view over **both** wire types below — do not look for a `BRRULFGEELR` formatter.

### Inside `<GetStoreItemsByIdsAsync>d__36$$MoveNext` `0xA1B7450`

```
0xa1b76f4 / 0xa1b772c   LINQ: filter the UnifiedItemIds to the '1.<guid>' (CustomAvatarItem) ones
0xa1b7834               interface dispatch -> the CustomAvatarItems bulk fetch
0xa1b7861  await #1  -> List<RecNet.CustomAvatarItem>
0xa1b79e1               ANIDAXYBRZA$$HOOESMUIYHW(List<CustomAvatarItem>)   ; enrich
0xa1b7a15  await #2
0xa1b7a59               ANIDAXYBRZA$$DSPKTLJTKQT(IEnumerable<BRRULFGEELR>) ; cache into the store
0xa1b7b15 / 0xa1b7b4d   LINQ: filter to the '0.<int>' (PurchasableItem) ids
0xa1b7c71  await #3  -> List<RecNet.PurchasableGiftDrop>
0xa1b7cc1               ANIDAXYBRZA$$REPOOSPDQUL(ids, giftDrops, items)    ; ZIPS back in id order
0xa1b7cf9               ANIDAXYBRZA$$VRQJENOVOCX(List<BRRULFGEELR>)
```

| await | wire call | route | literal |
|---|---|---|---|
| #1 | `RecNet.CustomAvatarItems.GetCustomAvatarItemsByIdsServiceCallInternal(IReadOnlyList<Guid> customAvatarItemIds, int assetVersion, ct)` `0x9402A20`, SM `<…>d__76$$MoveNext` `0x94355C0` (batched variant `<GetCustomAvatarItemsByIdsServiceCall>d__71` `0x9435FA0`) | **POST `api/customAvatarItems/v1/bulk`** | `0xFC469F0` |
| #3 | `<GetPurchasableGiftDropsByPurchasableItemIdsAsTaskInternal>d__34$$MoveNext` `0x95631A0` (sibling `…ByGiftDropIds…d__33` `0x9562D20`) | **POST `api/storefronts/v1/purchasableitems`** | `0xFC703C0` |

Shapes for both are already derived:
[customavataritems-routes](customavataritems-routes-wire-shapes.md) and
[storefronts-v1-purchasableitems](storefronts-v1-purchasableitems-wire-shape.md). **Both are bare
arrays** — which is why `{}` is fatal and `[]` is the safe empty answer.

⚠️ **Await #1 has no count guard.** `0xA1B76B4`–`0xA1B7851` contains only null checks (`test r14,r14`,
`test r15,r15`, `test rax,rax`) — no `Count == 0` comparison — so the **CustomAvatarItems bulk POST
goes out even when the filtered guid list is empty**. A server that answers `{}` (or 404s) on an
empty-id request breaks the FBA swap for a player who has no custom items involved at all. Serve `[]`.

⚠️ **The awaits are sequential in one state machine**, so the first `{}` aborts before #3 is sent.
Fix `api/customAvatarItems/v1/bulk` first, then re-test — `api/storefronts/v1/purchasableitems` may
be broken too and will only surface afterwards.

## Why the dialog says you must pay `0`

The checkout total is not a wire field. `List<BRRULFGEELR>` is handed to
`RecRoom.Storefronts.WVVAPDZFLEA.Set(List<PurchaseSourceItem>, StorefrontTypes, CurrencyType)` —
a **local aggregator** (`msig` shows 14 methods, no wire keys) — via
`AvatarCustomizationModel.SetPurchasePromotionDiscountForItems(WVVAPDZFLEA costInfo)` inside
`HandleTrialItemsInternal` → `ShowTrialItemsCheckoutDialog` → `ShowPurchaseItemsPrompt`.

So **an empty store-item list sums to 0** and the prompt renders a 0 cost with no error of its own.
`$0` in the UI is therefore a *downstream symptom* of the failed fetch, not a separate pricing bug —
there is no "price" route to fix. ⚠️ Do not chase
`api/customAvatarItems/v1/pricingconfig`; it is not in this chain.

The purchase that follows goes through
`PRJHEOOIRTF.MBHBOMXYABC(StorefrontTypes, CurrencyType, IReadOnlyList<UnifiedItemId>, IReadOnlyList<long>, long?, GiftItemDTO, Guid?)`
→ `MPVTAJGPRUT<BalanceUpdateResponseDTO<BulkPurchaseItemsBalanceUpdateResponseDataDTO>>`, so it
submits the unified ids it never managed to price. Underived.

## Related client-side state

`AvatarTypeCustomizationModel` keeps three preference flags that gate the FBA nags and are **purely
local** (`RecRoom.Preferences.STAKPLUPOSH`, key e.g.
`'AvatarCustomization_PlayerHasTriedFullBodyAvatar'`): `PlayerHasTriedFullBodyAvatar`,
`PlayerHasDismissedFBACallToActionToast`, `PlayerHasDismissedAddNoseAndBrowsDialog`. No route backs
them, so they are not a server concern.

`RRUI.Data.AvatarTypeCustomizationModel$$ShowSwapAvatarTypeDialog` `0x24D0580`
(`"Some of your avatar items are incompatible with this avatar type and will be removed. Swap
anyways?"` `0xFDACE60`) and the store-side `RRUI.Data.StoreItemModelBase$$ShowSwapAvatarTypeDialog`
`0x295EDE0` (`"Swap body type?"` `0xFC86738`) are both pure UI — neither issues a request.
