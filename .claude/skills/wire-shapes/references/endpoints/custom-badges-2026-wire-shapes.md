# Custom badges (2026) — wire shapes

> A "badge" is **not its own resource**. It is a `CustomAvatarItem` whose `OutfitType` is
> **`CustomBadge = 1000`**, with the room link and text colour carried in a **nested JSON string**
> (`CustomAvatarItemSaveDTO.AdditionalConfiguration`). There are only **two** badge-relevant HTTP
> routes: the owned-items list, filtered by `outfitType`, and one POST that grants a badge.

Derived **2026-10-16** from build `20260323.14` (`C:\games\recflare-2026`), index
`C:\Games\recnet-patcher\il2cpp-2026`. This build keeps **real names** for all of these DTOs, so the
shapes are read straight from metadata rather than from formatter key runs.

## 1. `POST circuitsRoomRewards/grantRoomBadge` — service 28 Econ

Client entry `RecNet.CustomAvatarItems$$UFCWWWBITAQ` `0x9407e30` (bounds `0x9407e30..0x9407f63`):

```
Task<CircuitsGrantRoomBadgeResponseDTO> UFCWWWBITAQ(CircuitsGrantRoomBadgeRequestDTO a,
                                                    CancellationToken b)
```

- service **28 = Econ** (`mov r8d, 0x1c` at `0x9407efe`) → `https://econ.<host>/circuitsRoomRewards/grantRoomBadge`
- verb **POST** — `HttpMethod` statics `[rcx+0x20]` at `0x9407ee7` (see the ⚠️ offset box below)
- the route is **one whole literal** (`0xFCFB308`), not assembled from fragments
- body is **JSON**, not form-urlencoded: the builder call is the generic
  `RGBOOBRDHEB.FZNGWUAGAIN<T>(!!T a)` (`0x9407f20`). The `ELHKHFJEHLM`-style form-param path is
  not used here at all.
- `Task<SomeDTO>` → **bare DTO, no envelope** (per [2026-send-helper-tiers](../conventions/2026-send-helper-tiers.md))

### Request body — `RecNet.CircuitsGrantRoomBadgeRequestDTO` (typedef #21731)

Formatter `Utf8Json.Formatters.RecNet.TQQMKFKSGTC` `.ctor 0x9000c60` (bounds `..0x9000fec`),
`____stringByteKeys` run `0x9000f26..0x9000fa2` — **4 keys, PascalCase, no `[DataMember]` renames**:

| # | key | CLR |
|---|---|---|
| 1 | `TargetAccountId` | `int` |
| 2 | `BadgeCustomAvatarItemId` | `System.Guid` |
| 3 | `RoomInstanceId` | `long` |
| 4 | `GrantMessage` | `string` |

```json
{ "TargetAccountId": 0, "BadgeCustomAvatarItemId": "00000000-0000-0000-0000-000000000000",
  "RoomInstanceId": 0, "GrantMessage": "" }
```

### Response — `RecNet.CircuitsGrantRoomBadgeResponseDTO` (typedef #21733)

Formatter `Utf8Json.Formatters.RecNet.WGVKDTTHSJA` `.ctor 0x9003450` (bounds `..0x9003674`),
key run `0x90035fe..0x900362a` — **2 keys**:

| # | key | CLR |
|---|---|---|
| 1 | `ResponseCode` | `CircuitsGrantRoomBadgeResponseCode` — **numeric** |
| 2 | `ErrorMessage` | `string` |

`RecNet.CircuitsGrantRoomBadgeResponseCode` (typedef #21732), int:

| value | name |
|---|---|
| 0 | `Success` |
| 1 | `PlayerAlreadyHadBadge` |
| 2 | `Error` |

```json
{ "ResponseCode": 0, "ErrorMessage": null }
```

**Bare — do not envelope it.** The facade returns `Task<CircuitsGrantRoomBadgeResponseDTO>`, so a
`{Value, Success, …}` wrapper deserializes into a DTO with `ResponseCode = 0` (`Success`) and a null
`ErrorMessage`, i.e. it **silently reads as success** rather than raising. That is the dangerous
failure mode here: no exception, a false positive.

### Who calls it

The CircuitsV2 nodes `AwardRoomBadge` / `AwardRoomBadgeNode`
(`<<AwardRoomBadge>g__DoAsyncWork|0>d` typedef #12628) and `PlayerHasRoomBadge` /
`PlayerHasRoomBadgeNode` (#12630). Room-side error strings worth grepping when a grant fails:
`'Couldn't award badge. Error: '`, `'Couldn't check if player has badge. Error: '`,
`'Player Already Had Badge'`, `'Invalid badge for this room.'`, `'Badge does not have room link.'`.

## 2. The badge **list** is the owned-items route — `GET econ/customAvatarItems/v1/ownedby/{accountId}`

There is no `badges` endpoint. `ICustomBadgesDataService.TrackBadgesEarnedByAccount` resolves through
`<GetBadgesEarnedByAccountAndUpdateTrackingEntryIfNeeded>d__20$$MoveNext` `0x23b0860` to
`RecNet.CustomAvatarItems$$GetCustomAvatarItemsOwnedByAccount` `0x9402b70`
(bounds `..0x94030ec`), which is the ordinary paged owned-items route:

```
Task<ODFPVNYWDAJ<CustomAvatarItem>> GetCustomAvatarItemsOwnedByAccount(
        int accountId, int skip, int take, int? outfitType, CancellationToken cancellation)
```

- path assembled from **two** literals — `'econ/customAvatarItems'` (`0x9402c5e`) +
  `'{0}/v1/ownedby/{1}'` (`0x9402c6a`) → `econ/customAvatarItems/v1/ownedby/{accountId}`
- service **28 = Econ** (`mov r8d, 0x1c` at `0x9402e69`), verb **GET**
  (`mov rsi, [rcx+8]` at `0x9402e1e`)
- query params, in literal order: `unityAssetVersion`, `unityAssetTarget`, `take`, `skip`,
  **`outfitType`**
- response is the same bare paged `{Results, TotalResults}` as the `/v1/owned` sibling —
  see [econ-customavataritems-owned](econ-customavataritems-owned-wire-shape.md)

**To serve the badge list, honour `outfitType=1000`.** The client then filters again client-side
(`'Filtered {0:N0} avatar items down to {1:N0} badges for local account.'`), discarding any item
whose `OutfitTypeData` is not a `CustomBadgeData`
(`'had OutfitTypeData that wasn't a CustomBadgeData. It may be a corrupt item or perhaps a new type
of badge this client doesn't understand, yet. Skipping it.'`). So a wrong `outfitType` filter
server-side yields an **empty badge list with no error**.

## 3. What makes an item a badge — `CustomBadgeData` inside a JSON **string**

`RecRoom.Avatars.OutfitType.CustomBadge = **1000**` (typedef #58099). The rest lives in
`CustomAvatarItemSaveDTO.AdditionalConfiguration`, which is a **`string`** (typedef #46374) holding
serialized `RecRoom.Avatars.Data.Shared.SerializedAvatarItemData` (#59795). Its `OutfitTypeData`
member must be:

`RecRoom.Avatars.Data.Shared.CustomBadgeData` (typedef #58116)

| member | CLR | note |
|---|---|---|
| `RoomId` | `long` | `IsLinkedToRoom` is a computed getter over this — **no backing field, no key** |
| `TextColor` | `UnityEngine.Color` | r/g/b/a floats |

Client-side validation strings, in the order they bite:
`'Missing AdditionalConfiguration on badge save.'` → `'Missing badge configuration ItemData.'` →
`'Invalid badge configuration OutfitTypeData.'` → `'Outfit type should always be custom badge.'`.

⚠️ `RecRoom.AppUI.CustomBadge` (#58484 — `Id, Name, Description, ImageRecNetFileName, TextColor,
RoomId, IsFirstPartyBadge`) is **not a wire DTO**. It is built client-side by translating owned
avatar items (`'Got {0:N0} custom badge avatar items owned by account {1}. Translating them into
badge data…'`). Do not try to serve it. Same for `BadgeListEntry` (#41202),
`CustomBadgeListViewModel` (#41204), `CustomBadgeViewModel` (#41206) and `CustomBadgeUIType` (#58485).

## 4. The one other badge field on the wire — `StorefrontConfig.LatestStoreBadgeDateTime`

Unrelated feature: the "NEW" flag on store rows. `RecNet.StorefrontConfig` (typedef #22120) has
exactly two members — `MinPlayerLevelForGifting` and `LatestStoreBadgeDateTime` — and ships as a
section of `GET api/config/v2`. See
[gameconfig-v2-roomkeyconfig](gameconfig-v2-roomkeyconfig.md). Wire keys
`latestStoreBadgeDateTime` / `lateststorebadgedatetime` are the usual Utf8Json casing variants.

## 5. Everything else matching /badg/ is NOT wire

Checked all **84** typedefs whose name or namespace contains `badg`, plus every `badg` string
literal. Beyond §1–§4 there is nothing server-visible:

| thing | what it actually is |
|---|---|
| `RecRoom.AppUI.AccountBadgeIconType` (#41097) | nametag icon enum — **client-local**, see below |
| ~50 `*BadgeImpl` / `Hide*Badge*` typedefs | AppUI data-binding impls (0 fields) |
| `ScreenHUDBadge`, `ScreenHUDBadgeManager` | in-world HUD prefab plumbing |
| `BoostBadgeController`, `BoostLevelBadgeConfig`, `RoomBoosterBadgeImpl` | room-boost UI |
| `CheersBadgeImageMapping`, `CheerBadge*Impl` | cheers UI |
| `ApplicationBadgeCountResetEvent` (#61472), `PushNotification[… Badge={1} …]` | OS app-icon badge count (APNs), not an endpoint |
| `CV2SetConstantRoomBadgePayload` (#24536 — `Node`, `RoomBadgeId`) | **CircuitsV2 persistence payload**, room-state save data, not HTTP |
| `badgeId`, `badgeCount`, `custom_badge*`, `show_popular_badge` | **analytics** param names — `badgeId` `0xFD8A808` refs only `RRUI.CustomBadgesDataService$$NavigateToLinkedRoom` `0x23a3c20` |
| `Discovery.PopularBadgeCCUThreshold` | a remote-config key |
| `limited_badge_details`, `limited_badge_enabled`, `limited_badge_threshold_days` | gate-config keys |

### ⚠️ `AccountBadgeIconType` grew in 2026 — the 2025 note is stale for this build

[nametag-badge-icons](nametag-badge-icons-wire-shape.md) records a 4-member priority chain
(`Party(1) > Influencer(3) > RRPlus(2) > None(0)`) derived on `20250718.01`. On `20260323.14` the
enum has **11** members:

| value | name |
|---|---|
| 0 | `None` |
| 1 | `Party` |
| 2 | `RRPlus` |
| 3 | `Influencer` |
| 4 | `Developer` |
| 5 | `Cheer_Helpful` |
| 6 | `Cheer_General` |
| 7 | `Cheer_Sportsmanship` |
| 8 | `Cheer_GreatHost` |
| 9 | `Cheer_Creative` |
| 10 | `League` |

The 2025 note's **values 0–3 are unchanged**, so its `influencerpartnerprogram` finding still holds;
what is **not** re-derived is whether 2026's priority chain still ranks only those four. There is
also a `RoleBadgeIconType` string literal (`0xFCB6560`) with **no typedef** — a data-item name, not
an enum to serve.

## ⚠️ Tooling: the `HttpMethod` static-fields offset moved on 2026

[SKILL.md](../../SKILL.md) says the verb comes from `[klass+0x90]` (static fields) at a fixed offset.
**That `0x90` is a 2025 constant.** On `20260323.14` the static-fields pointer is **`[klass+0x20]`**:

```
mov rax, qword [rip + …]      ; TypeInfo System.Net.Http.HttpMethod
mov rcx, qword [rax + 0x20]   ; -> static fields      (2025: [klass+0x90])
mov rsi, qword [rcx + 8]      ; -> the HttpMethod     (offset table UNCHANGED)
```

The **field offsets inside** static fields are the same on both builds —
`0x00` Delete · `0x08` Get · `0x10` Head · `0x18` Options · `0x20` Post · `0x28` Put · `0x30` Trace.
Controlled against the already-derived `/v1/owned` (GET on 2025 via `[rcx+8]`): the 2026 `ownedby`
sibling reads `[rcx+8]` too.

Also: `slots2025.py` annotates the `lea`/`mov` **TypeInfo** slots but not the subsequent
double-deref, so it will tell you `HttpMethod` is involved without telling you which verb — read the
two `mov`s with `rangedis.py`. And `rangedis.py` **desyncs** if you start it mid-function; sweep from
the `fstart.py` lower bound and `awk` out the window instead.

## Tools that do not work on this build

`findm.py` is Tier B — it reads `out/script.json`, which a carved build has no equivalent of. Use a
`methods.pkl` name search instead. `enumvals.py` returns nothing for a name with no typedef
(e.g. `RoleBadgeIconType`), which is **not** the same as "the enum has no members".

Related: [econ-customavataritems-owned](econ-customavataritems-owned-wire-shape.md),
[customavataritems-routes](customavataritems-routes-wire-shapes.md),
[nametag-badge-icons](nametag-badge-icons-wire-shape.md),
[2026-send-helper-tiers](../conventions/2026-send-helper-tiers.md),
[recnet-service-enum](../conventions/recnet-service-enum.md)
