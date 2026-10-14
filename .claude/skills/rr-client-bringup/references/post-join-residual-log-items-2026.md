# Residual Player.log items after a clean room join (2026 build)

> Triage of what is left in `Player.log` once the join actually succeeds — i.e. no
> `ErroredPromiseException`, no `[Platform.BootSequence]` failure, no
> `EconRPCForwarder is not initialized`, `BulkDestroy(24)` not `(0)`. See
> [cv1-mappings-join-nre-2026](cv1-mappings-join-nre-2026.md) for the join failure itself.
> **None of the items below can fail a join.** They are feature-level and cosmetic, in priority
> order.
> ⚠️ A log that ends in `Crash!!!` after `ObjectId = Invalid` / `Lifetime = LoadInstance` is a third
> failure mode, neither of these — see
> [basement-objectid-invalid-crash-2026](basement-objectid-invalid-crash-2026.md).

Captured **2026-10-13**, build `20260323.14`, a clean join: 5,218 lines, **8 `[Exception]`,
2 `[Error]`, 18 `[Warning]`** — down from a 923 KB log full of boot-sequence damage.

## How to triage this log shape fast

```bash
grep -nE '^\[[0-9:]+\] \[[0-9]+\] \[[0-9.]+\] \[(Exception|Error|Warning)\]' Player.log
```

That one line is the whole inventory — every real problem has a header in that form, and the
thousands of `[Log]` lines never need reading. Then, for each hit, take the
`# Formatted Async Stack Trace` block and drop the frames matching
`System.Threading*`, `System.Runtime.CompilerServices*`, `AsyncMethodBuilder*`, `Task\`1*`,
`RecNet.RGBOOBRDHEB`, `RecNet.FOIOSBRLQPI`, `RecNet.KYWGTEMIXKR`, `RecNet.Core.*`,
`RecNet.XJAFUXFVGPU`, `RecNet.HBEADHYKUCU`, `RecRoom.Async.*`, `BestHTTP.*`, `UnityEngine.*`.
**What survives names the owning subsystem**, which is the only identification step that matters.

⚠️ **This log records no request URLs** — grepping for `https?://` finds only a Backtrace docs link.
The subsystem frame is the only in-log route evidence; cross-check against the server's own 404 log
by timestamp.

## 1. `giftdropstore` 404 — two consumers, one missing route

| line | t | owner |
|---|---|---|
| 400 | 11.60 s | `[LiveOps.TLA.Recipes.Ingredients] RecNetWebException: HTTP Error 404` |
| 1655 | 24.17 s | `RecRoom.Avatars.Outfit.OutfitManager.GetStorefront` |
| 2119 | 24.23 s | `An error occurred` — same chain, the wrapped rethrow |

All three pass through **`RecNet.Storefronts+TNUQJOJQLAU.TBDRLIDREPP`** `0x9560E50`, whose state
machine is generic inst **#67146 = `<GetStorefrontAsTask>b__0>d`** returning
inst **#3158 = `RecNet.GiftDropStorefront`**. That is
**`GET api/storefronts/v3/giftdropstore/{storefrontType}`** — **already derived**, see
[giftdropstore-v3](../../wire-shapes/references/endpoints/giftdropstore-v3-wire-shape.md) and
[giftdropstore-storefront-type](../../wire-shapes/references/endpoints/giftdropstore-storefront-type.md).

**Two different storefront types are being requested** (a Tricksters/Rectober recipe-ingredient
storefront and the outfit storefront) and both 404. The `{N}` is a `StorefrontType` enum value, not a
row id — the server's 404 log gives the exact ones. Note the earlier capture showed type `453`.

The `OutfitManager` failure is the one with visible cost: no outfit storefront means the avatar
clothing shop is empty.

## 2. `api/makerai/checkfreetrialeligibility` — 404, then `false`

| line | t | message |
|---|---|---|
| 3827 | 60.65 s | `HTTP Error 404` |
| 4622 | 75.15 s | `Malformed Response: 'false'` |

Same route both times — `RecNet.BVIXCNIZYIX.DRECUPUEDKL` with formatter
`Utf8Json.Formatters.RecNet.VTLMXGUPIAK`. It wants the **valueless envelope**
`{Success, Error, error_id}`, not a boolean. Derived in
[makerai-checkfreetrialeligibility](../../wire-shapes/references/endpoints/makerai-checkfreetrialeligibility-wire-shape.md).
⚠️ **1-hour response cache — relaunch between attempts.**

## 3. Room-list 404 → NRE in the same method

| line | t | message |
|---|---|---|
| 3317 | 26.82 s | `HTTP Error 404` |
| 3573 | 27.35 s | `Object reference not set to an instance of an object.` |

Both in **`RecRoom.AppUI.Data.RoomQueryManager.QueryStaticListSource(RoomListQueryData, ct)
-> Task<List<RoomDTO>>`** `0x96BC8A0`, state machine `<QueryStaticListSource>d__24` `0x96DB460`
(real bounds `0x96DB460..0x96DCEBC`). The NRE is the **consequence** of the 404, one second later —
the faulted list is dereferenced — so fixing the 404 fixes both.

**Which route is not pinned from the log.** The method branches over five network sources:

| call site | method | route |
|---|---|---|
| `0x96DB985` | `RecNet.Rooms.Client.MBPCDCVJQUL() -> IReadOnlyList<RoomDTO>` | **`rooms/base`** (`RecNet.Rooms.DFMBMRNABHU.MBPCDCVJQUL` `0x95AF810`) — ⚠️ **not in the catalog** |
| `0x96DBBB3` | `RecNet.Lists.Client.VYRHNUPWUTE(string, EntityType, ct)` | curated list by name |
| `0x96DC05E` | `RecNet.Lists.Client.GGMAMLSGFKC(string, EntityType, ct)` | curated list by name |
| `0x96DC46A` | `RecNet.Lists.Client.QIBNREYRSLU(long, EntityType, ct)` | curated list by id |
| `0x96DC850` | `RecNet.Rooms.Client.WJTOCIAXDUR() -> FeaturedRoomGroupDTO` | `featuredrooms/current` |

✅ **`featuredrooms/current` can be ruled out as the thrower**: its branch checks
`Task.get_IsCompletedSuccessfully` at `0x96DC8D2` before use, so a failure there is swallowed. The
other four are unguarded.

`rooms/base` is the only one of the four with no catalog entry, which makes it the leading candidate.
Confirm from the server's 404 log at the matching timestamp before deriving anything.

The literal `'__SavedForLater_Rooms'` (`0x96DB6ED`) is the only string in the method — a reserved
list name, useful for recognising which page is querying.

## 4. `Malformed Response: '[]'` on objectives — already derived, not yet applied

| line | t | message |
|---|---|---|
| 2728 | 25.71 s | `Malformed Response: '[]'`, formatter `Utf8Json.Formatters.RecNet.VGCBANXFZSJ` |
| 3032 | 25.81 s | `[RecNet.Features.Objectives] Error on server call: … Local objective state will not be reflected in server!` |

`POST api/objectives/v1/cleargroup` is still answering `[]`. It wants a **single**
`{Group, IsCompleted, ClearedAt}` object —
[objectives-v1-cleargroup](../../wire-shapes/references/endpoints/objectives-v1-cleargroup-wire-shape.md). The feature-level
`[RecNet.Features.Objectives]` line is the cheapest signal for this class, because the subsystem
logs it itself rather than leaving it to the generic sender.

## 5. `TrickstersTLAManager` NRE at boot — fire-and-forget, no 404 behind it

Line 236, **9.45 s**, `Object reference not set to an instance of an object.`, frames
`TrickstersTLAManager.VKRUFYNKGCE ← .SAVGDXVMHSP ← .REEVPVXDANZ ← .ctor` under UJect DI.

`VKRUFYNKGCE` is **`UpdateProgressionEvent`** (builder generic inst **#96229 =
`<UpdateProgressionEvent>d__80`**, state machine `0x20B39A0`, bounds `..0x20B4611`). It does
`DateTime.UtcNow >= …` twice and calls `RecRoom.BattlePass.Data.BattlePassWrapper.New` — so it is
reading dates off a progression-event/battle-pass object that came back null.

⚠️ **This is not caused by a 404** — there is no progressionEvents 404 anywhere in this log, so a
route is answering `200` with something the TLA then dereferences (a null or empty event). The
Tricksters/Rectober seasonal activity is enabled client-side and has no backing data here.

✅ **Harmless.** `REEVPVXDANZ()` is `void` and calls `SAVGDXVMHSP()` which returns `Task` — nothing
awaits it, so this is an unobserved exception that is logged and dropped. It cannot fail boot and
cannot fail a join. Chase it only if you want the seasonal activity working.

Related: [progressionevents-event-by-id](../../wire-shapes/references/endpoints/progressionevents-event-by-id-wire-shape.md),
[paintball-battle-pass](../../wire-shapes/references/endpoints/paintball-battle-pass-wire-shapes.md).

## 6. Avatar item ids the client's catalog does not have — server data gap

**10 occurrences** of
`Unable to find base avatar item for id {0}. Falling back to default base avatar item`, for exactly
two ids: **2498** and **2896** (lines 362-366 at 10.45 s, 868-872 at 14.92 s).

Literal `0xFDEAD38`, both sites in
**`RecRoom.Avatars.Data.Runtime.AvatarItem.FITGPMRAPRR(int id, AvatarItem out) -> bool`**
`0x15EB170` — a lookup against a **client-side registry** read from a static field, i.e. shipped in
the asset bundles, not fetched.

So the server is handing out avatar item ids **2498** and **2896** that this client build's catalog
does not contain. Cosmetic — the avatar falls back to the default base item rather than failing — but
visible as a wrong-looking avatar. Fix by only serving ids the shipped catalog knows. Same family as
[avatar-item-desc-registry](avatar-item-desc-registry.md).

## 7. Confirmed-benign noise — do not chase

| item | count | why it is fine |
|---|---|---|
| `Your project uses a scriptable render pipeline. You can use Camera.stereoTargetEye only with the built-in renderer.` | 4 | stock Unity URP warning |
| `[Backtrace]::Reponse code: 0, Response text: Cannot resolve destination host` | 1 | their crash reporter cannot reach `backtrace.io`, which is correct for a self-hosted setup; silence it with the telemetry kill switches if it bothers you |
| `No Transform with name 'tryon' was found. Skipping sorting for this Transform.` | 1 | stock UI layout |
| `AvatarFullBodySystem: Tried to get bone , but no bone by that name was found.` | 1 | empty bone name, stock |

## Priority

1. **`giftdropstore/{type}`** — two consumers, and it empties the outfit shop. Already derived.
2. **`objectives/v1/cleargroup`** — derived, just needs the single-object fix applied.
3. **`makerai/checkfreetrialeligibility`** — derived; remember the 1-hour cache.
4. **the room-list 404** — identify from the server log first; likely `rooms/base`, which would be a
   genuinely new derivation.
5. avatar ids 2498/2896 — cosmetic.
6. Tricksters TLA — cosmetic, fire-and-forget.
