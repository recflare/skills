# Outfits me put wire shape

> Wire shape of PUT api/outfits/me — responds with the BARE 3-key envelope {Success, Error, error_id}, no Value key.

Derived **2026-08-17** from `C:\Games\recflare-2025` (build `20250718.01`) via
[recflare-2025-metadata-carve](../../../il2cpp-analysis/references/recflare-2025-metadata-carve.md).

`PUT https://api.<host>/outfits/me` — **PUT** (`HttpMethod` statics `+0x28` = `put_method`;
`+0x08` GET, `+0x20` POST), service **2 = API** (`mov r8d, 2`). Client entry
`IADEBGHMJIG.DBDHNNFDFBO(KPPNBDELPNB outfit)` (`0x7D58800`), state machine `AHOLFKMFPIA$$MoveNext`
(`0x7D4A4C0`). JSON body via `MGPBDIAGCFD.ELKIBCPINAP`. Note the same `outfits/me` literal is also
used by a **GET** state machine `NCBLEPFFJBE$$MoveNext` (`0x7D62F60`) — check the HttpMethod static
offset, not the path, to tell them apart.

**Response is `JFNAKFCGDAO` — the base envelope with NO `Value`**: exactly three keys in
`____stringByteKeys` order, `Success`, `Error`, `error_id` (formatter `OGMMAAFJCJG` ctor
`0x76887E0`). `error_id` is lowercase (`[DataMember(Name = "error_id")]`); `Success`/`Error` are
PascalCase; all accept their casing variants. So `{"Success":true,"Error":null,"error_id":null}`
is a complete valid response — adding a `Value` key is harmless but ignored.

`JFNAKFCGDAO.CPOBHIECLEN` is the `0xA60520` no-op — no validation. Neither call site
(`BOKCGGFPDGN$$MoveNext` `0x7D502B0`, `<<SetMySavedOutfit>b__0>d$$MoveNext` `0x7D68F10`) inspects
`Success` immediately after the await; the envelope object is just handed onward.

Request body `KPPNBDELPNB` (formatter `GAHMAGAAONJ` ctor `0x76C4C50`), 8 keys: `DataVersion` long
0x10, `LegacyData` object 0x18, `CustomizationSettings` string 0x20, `Selections` list 0x28,
`Slot` int 0x30, `Name` string 0x38, `Accessibility` enum 0x40, `ThumbnailFileName` string 0x48.

**Why:** RecNet has three envelope tiers — `JFNAKFCGDAO` (no value, used by write endpoints like
this), `KGOJLHJNIOD<T>` (single value, see [econ-bulkpurchase-wire-shape](econ-bulkpurchase-wire-shape.md)), and
`GJAFHDAFBNE<T>` (list) — and plenty of endpoints use no envelope at all
([curatedlists-bulk-wire-shape](curatedlists-bulk-wire-shape.md), [rooms-contributedby-wire-shape](rooms-contributedby-wire-shape.md)). Which tier applies is
per-endpoint; read it off the state machine's `AsyncTaskMethodBuilder<T>`.

# ✅ 2026 (`20260323.14`): `Success` IS read — but `Error` is unreachable, and a refusal never reaches the player

Re-derived **2026-11-06** on `C:\games\recflare-2026` to answer "what can the server tell the
client when it refuses an outfit save?". Short answer: **`Success` gates the client's local state,
`Error` is dead, and no refusal can produce a message, a revert, or a re-fetch.**

## The route, 2026 names

| | |
|---|---|
| verb / service | **PUT**, svc **2 = API** (`HttpMethod` statics `+0x28`) |
| request body | **JSON** `RecNet.OutfitDTO` via `RGBOOBRDHEB::FZNGWUAGAIN<OutfitDTO>` (methodSpec inst **#3184**) — not form params |
| response `T` | **`RecNet.RecNetResult`** (methodSpec inst **#3201**) = the valueless envelope `{Success, Error, error_id}` |
| send helper | `RGBOOBRDHEB::ZWUODKCINOA<RecNetResult>` — **response required** |
| state machine | `<SetSavedOutfitInternal>d__31$$MoveNext` **0x9527BB0**–0x9527FE7 |
| facade | `RecNet.OAIKZUPWURV` (13 fields; the saved-slot cache is `Dictionary<int, OutfitDTO> JSCJMQHVYTM`) |
| public wrapper | `<SetMySavedOutfit>d__29$$MoveNext` **0x9527770** → `OAIKZUPWURV$$MWHCVPKGNUN` 0x951B870, serialized through `RecRoom.NoEngine.Common.PNTGWOQNAMQ<RecNetResult>::TRJHBUMIJOH` |
| GET sibling | `<GetMyCurrentOutfit>d__22$$MoveNext` **0x9523500**, returns a **bare `OutfitDTO`** (no envelope, no cache in the state machine) |

Same `'outfits/me'` literal (`0xFDF1268`) serves both verbs — 4 refs, 2 per state machine. Tell them
apart by the `HttpMethod` static offset, never the path.

## What the client reads — exactly

```
0x9527DD3  TaskAwaiter<RecNetResult>.GetResult()      -> r14 = envelope
0x9527DDB  test rax,rax ; je 0x9527FCC                -> null envelope = NullReferenceException
0x9527DE4  cmp byte ptr [rax + 0x10], 0               <-- Success
0x9527DE8  je  0x9527EC6                              -> !Success: skip EVERYTHING below
0x9527E1E  Dictionary<int,OutfitDTO>.set_Item(outfit.Slot, outfit)   ; caches what it SENT
0x9527E71  OutfitEvent.Invoke(...)                    ; facade +0x20
0x9527EC2  OutfitEvent.Invoke(...)                    ; facade +0x18
0x9527EC6  common tail
0x9527EE8  AsyncTaskMethodBuilder<RecNetResult>.SetResult(r14)       ; envelope handed back as-is
```

Envelope field layout (matches [econ-roomoffer-recentpurchases](econ-roomoffer-recentpurchases-wire-shape.md)):
**`Success` bool `+0x10`, `Error` string `+0x18`, `error_id` `+0x20`** (`Value` would be `+0x28`).

- **`Success` is read.** HTTP status is not inspected here at all — a non-2xx is turned into a thrown
  `RecNetWebException` by `ZWUODKCINOA` long before this point.
- **`Error` (+0x18) is never loaded** anywhere on the outfit path.
- `Success:false` ⇒ the slot cache is **not** updated and **neither** change event fires, so the
  saved-looks list does not refresh. The avatar in the scene is untouched.
- `Success:true` ⇒ the client caches **the `OutfitDTO` it sent**, never anything from the response.
  So if the server stores a *modified* outfit (perk stripped) and answers `Success:true`, the
  client's own slot cache keeps the unmodified version until it next re-reads `outfits/me`.

## Why a server refusal can never reach the player

The UI layer is `RRUI.Data.SavedOutfitsModel.<SaveOutfitAsync>d__61$$MoveNext` **0x28AEB80**,
returning `Result<RecRoom.Avatars.AvatarSaveResult, RecRoom.Avatars.SYTHVIOUNET>`:

```
0x28AEDA6  interface call (slot 0x2A) -> true  => SYTHVIOUNET error      ; pre-flight #1
0x28AEDC2  interface call (slot 0x1A) -> true  => SYTHVIOUNET error      ; pre-flight #2
0x28AEE35  interface call on the avatar = the real save (awaited)
0x28AF05B  Result.IsError ; jne 0x28AF119
   -- ok --   0x28AF0B7  ToastListModel.AddMessageToast(toastSuccessMessage)
              0x28AF0F3  PlayerEvents.SavedOutfitSlot(...)
   -- err -- 0x28AF137  Result.GetError -> SYTHVIOUNET
              0x28AF148  switch on [err+0x18] = .ErrorCode   (-2,-1,-1,-1 chain)
              0x28AF1A7  ToastListModel.AddMessageToast(<client-side literal>)
```

The toast text is chosen from a **client-side literal** keyed by the **client-side** enum
`.ErrorCode` (typedef **#14252**):

| value | member | toast |
|---|---|---|
| 0 | `None` | — |
| 1 | `InvalidData` | `'Failed to save outfit'` (default arm) |
| 2 | `WearingLockedOrTrialItems` | `"You are wearing trial items which you don't own."` |
| 3 | `WearingUnknownOrLockedItems` | `'Update your game to save this outfit.'` |
| 4 | `InvalidSlot` | `'Failed to save outfit'` |
| 5 | `ThumbnailRenderingFailed` | `'Failed to save outfit image'` |
| 6 | `ThumbnailUploadFailed` | `'Failed to save outfit image'` |

**There is no member meaning "the server refused,"** and nothing builds a `SYTHVIOUNET` from a
`RecNetResult`, an HTTP status or an `Error` string — so the server's `Error` text has no renderer.
`CanAvatarOutfitBeSaved` checks **item ownership only**; there is no RRPlus check at save time.

> ⚠️ **Do not enumerate the error sites with `callxref` on `SYTHVIOUNET$$.ctor` (0x15827C0).** It
> reports only 3 direct `call rel32` sites (`CanAvatarOutfitBeSaved` 0x28A4248 — which passes
> `edx=3`/`edx=2` — and the two pre-flight arms of `<SaveOutfitAsync>d__61` at 0x28AEFCB `edx=3` /
> 0x28AEFFE `edx=2`). The avatar layer allocates the object and writes the code **straight into the
> field** instead (`call 0xC40350` on the TypeInfo, then the *shared* ctor 0x9AF74F0, then
> `mov dword ptr [rdi+0x18], <code>`), so those sites are invisible to `callxref`. **Enumerate by
> `mxref` on the `SYTHVIOUNET` TypeInfo slot `0xFD2B258` instead** — 16 refs across 5 methods:
> `<CaptureAndUploadThumbnailImageAsync>d__18` 0x1583250, `<TrySaveOutfitInternal>d__19` 0x1585240,
> `<TrySaveToSlotAsync>d__17` 0x1585810, `CanAvatarOutfitBeSaved`, `<SaveOutfitAsync>d__61`. The
> `0x18` offset is confirmed by the shared getter `OSBDXJNGMZS` 0xD0C6A0 = `mov eax,[rcx+0x18]; ret`.

## The avatar-layer chain, and the one place the server *can* raise a visible error

`RecRoom.Avatars.BALXQSAJJOJ` is the avatar implementation behind the `YDWQRULJIUO` interface:

```
<TrySaveToSlotAsync>d__17        0x1585810   orchestrator
  0x15859B0  if (String.IsNullOrEmpty(previewImageName))
  0x15859CB    await BALXQSAJJOJ$$OZPYVIAQBCJ 0x155D850      -> <CaptureAndUploadThumbnailImageAsync>d__18  (builder inst 3064)
  0x1585A51    Result.IsError(thumbnailResult)
  0x1585A58    jne 0x1585BEC                                  -> SHORT-CIRCUIT: the PUT never happens
  0x1585AA2  await BALXQSAJJOJ$$CZLZNMHLYQC 0x155B360         -> <TrySaveOutfitInternal>d__19               (builder inst 3056)
```

`<TrySaveOutfitInternal>d__19` 0x1585240 is the method that awaits the PUT
(`TaskAwaiter<RecNetResult>`, inst **#3201**) — and **it discards the envelope**:

```
0x1585562  TaskAwaiter<RecNetResult>.GetResult()
0x1585573  Result<AvatarSaveResult>.Ok(...)        <-- unconditional; Success is never read here
```

Its three error arms (`mov dword ptr [rdi+0x18], 3` at 0x1585631, `…, 2` at 0x1585676, and one more
at 0x15856A1) are all **pre-PUT** validation, not response handling. So the `Success` test inside
`SetSavedOutfitInternal` is genuinely the only consumer, and it only affects the facade's own cache.

### ✅ `POST api/images/v4/uploadsaved` — the server-reachable generic error

`<CaptureAndUploadThumbnailImageAsync>d__18` **0x1583250** is the pre-PUT step, and it talks to the
server:

```
0x15834F7/0x15835AB  BALXQSAJJOJ$$HWCYJFAHELI + ManagedTexture$$HEGUFCUTURV/JFQBOWYYPOC   ; render
0x1583A3F  mov dword ptr [rbx+0x18], 5    ; ThumbnailRenderingFailed
           log 'Couldn''t render avatar pose for saved outfit: '        (0x15839E2)
0x1583649  RecNet.Images$$GMHYOGKRBOZ 0x949D5C0                          ; UPLOAD
0x15836A2  String.IsNullOrEmpty(result.ImageName)
0x15836D6  mov dword ptr [rdi+0x18], 6    ; ThumbnailUploadFailed   <-- empty name
0x15838D0  mov dword ptr [rbx+0x18], 6    ; ThumbnailUploadFailed   <-- threw
           log 'Failed to upload thumbnail image for saved outfit: '    (0x1583873)
```

The upload route, from `RecNet.Images$$GMHYOGKRBOZ` **0x949D5C0** (the 0x949D2F0 overload carries no
literals):

| | |
|---|---|
| route | **`POST api/images/v4/uploadsaved`** (literal 0xFDF…, `mov r8d, 2` = svc **2 API**, `HttpMethod` statics **+0x20** = POST) |
| file part | `'image'`, filename `'file.bin'`, added by `RGBOOBRDHEB$$WOGHBITUUOI` 0x9538BD0 (multipart) |
| meta part | `'imgMeta'` = JSON of `.SavedImageMetaDTO`, added by `NJPEKLKCVCG` 0x9537F80 (methodSpec inst **#23230**) |
| response | **`.SavedImageAccessibilityDTO`** (inst **#19162**) via **response-required** `ZWUODKCINOA` — 2 keys `{ImageName, Accessibility}` |

`.SavedImageMetaDTO` (6 keys, all **camelCase** on the wire):
`playerIds List<int>`, `savedImageType`, `roomId long`, `playerEventId long`, `accessibility`,
`description`.

`.SavedImageType` **#22241**: `None 0, ShareCamera 1, **OutfitThumbnail 2**, RoomThumbnail 3,
ProfileThumbnail 4, InventionThumbnail 5, PlayerEventThumbnail 6, RoomLoadScreen 7`.
`.SavedImageAccessibility` **#22240**: `Private 0, Public 1, FriendsOnly 2`.

**So the server can identify an outfit-save thumbnail (`imgMeta.savedImageType == 2`) and make the
client show a real toast:**

| server answer to `uploadsaved` | client |
|---|---|
| `200 {"ImageName":"","Accessibility":0}` | `IsNullOrEmpty` → `ErrorCode 6` → toast **"Failed to save outfit image"**. No exception. **Clean.** |
| any non-2xx | `ZWUODKCINOA` throws → caught → log `'Failed to upload thumbnail image for saved outfit: <ex>'` → `ErrorCode 6` → same toast, plus a logged exception |
| `200 {}` | `Malformed Response: '{}'` — see [empty-json-object-deserializes-to-null](../conventions/empty-json-object-deserializes-to-null.md). Never. |

⚠️ **This aborts the whole save** (0x1585A58 short-circuits before `TrySaveOutfitInternal`), so it is
an *indication plus a full refusal* — it cannot be combined with "store a stripped outfit and
accept". Pick one.
⚠️ The wording is about the image, not the outfit, and **codes 1 `InvalidData` and 4 `InvalidSlot`
are never produced anywhere**, so the better-worded generic `'Failed to save outfit'` (the default
arm) is dead code — unreachable from the server.
⚠️ The thumbnail step only runs when the caller passed an empty `previewImageName`
(`IsNullOrEmpty` at 0x15859B0). A save that reuses an existing thumbnail skips the upload entirely
and therefore skips this lever.

Consequences for a server that wants to refuse:

| server answer | client behaviour |
|---|---|
| `403` (or any non-2xx) | `ZWUODKCINOA` throws `RecNetWebException: HTTP Error 403` → the promise errors → `RecRoom.Async.XKMSFCDUWSV<T>.IQQWXDIHGCW` → `SAXZOKINUQZ.KSNTDCQPEQA` logs it. **No UI at all**, local avatar keeps everything, slot cache untouched, events do not fire. |
| `200 {"Success":false,"Error":"…"}` | No exception. Slot cache not updated, events do not fire, `Error` discarded. Still no message, still no revert. |
| `200 {"Success":true,…}` | Slot cache takes **the body the client sent**; both events fire; success toast shows. |
| `200 {}` | `Malformed Response: '{}'` — see [empty-json-object-deserializes-to-null](../conventions/empty-json-object-deserializes-to-null.md). Never do this. |

So **strip-the-perk + `Success:true` is the only answer that leaves the client in a consistent
state**, and the local divergence until reload is unavoidable on this build.

## No push can make the client re-read its own outfit

2026 exposes its push payloads as generated `RecNet.NotificationDto_<T>` wrappers — enumerate them
with `{n.split('$$')[0] for … if 'NotificationDto_' in n}` over `methods.pkl`. **70 of them**, and
**none is outfit- or avatar-related**:

```
Account AnnouncementDTO AnnouncementIdDTO AppVersionUpdate AutoFollowFailedMessage
BalanceResponseDTO BalanceUpdateResponseDTO_RewardBalanceModificationDTO ChatMessage
ClubMembershipUpdate CommunityBoardAnnouncementDTO CommunityBoardDTO Consumable
ConsumableInstanceDto Currency CurrencyIdDTO CustomAvatarItem DataCollection_EventDTO DebugCommand
GenerateMeshResponseDTO GiftPackage GiftPackageIdDTO InAppMessageDTO InAppMessageIdDTO
InventionPurchaseResponseDTO KeepsakeInstanceDTO LeaderboardStatChangedDTO LogoutNotificationDTO
MakerAITimeBalanceStatusUpdatePushNotification MakerAIUsageBalanceStatusUpdatePushNotification
Message MessageIdDTO ModerationBlockDetail ModerationKickFail NotifyVoiceViolationDTO
PhotonAccessTokenAndPermissionsDTO PlayerEvent PlayerEventDetails PlayerEventIdDTO
PlayerEventInformation PlayerPresence PlayerReferral Progression ProgressionEventRecordDTO
PurchasableXpBoostActivationDTO PurchaseBalanceModificationDTO Relationship RemoteRunDTO Reputation
RewardSelection RoomBanNotificationDTO RoomBoostConsumedNotificationDTO RoomBoostNotificationDTO
RoomComment RoomDetailsDTO RoomInstance RoomKey RoomKeyIdDTO RoomModKickDetail RoomOffer
RoomOfferIdDTO SelfAccount ServerMaintenanceDTO SubscriptionEventDTO SubscriptionUpdate
SupportedInfluencerDto TimedRewardTrackRecordDTO TimedRewardTrackXpEarnedDTO
TimedRewardTreeNodeCollectedDTO TimedRewardTreeXpEarnedDTO VoiceConnectionDTO
```

`CustomAvatarItem` is the existing `PlayerCustomAvatarItemModerated` channel (a single moderated UGC
item), not an outfit reload. This list is also the fast way to answer "is there a push for X?" on
2026 — it replaces `regall.py`, which needs Tier-B `script.json` and cannot run on a carved build.

In-room appearance does **not** come from `outfits/me` or `outfits/bulk`: it is replicated per-player
over the room protocol as the 68-field protobuf `AvatarSystemUpdateData` (registered in
`RecRoom.Protobuf.KQWWEWEILWC$$.cctor` 0x9E62560, literals `'AvatarSystemUpdate'` 0xFDDD6D8 /
`'AvatarSystemUpdateData'`), driven by `RecRoom.Avatars.AvatarSystemUpdateState` and
`RecRoom.Players.Puppet.PlayerPuppet`. So a server-side edit to the stored outfit is invisible to
everyone **in the room** until the owning client re-sends its avatar state; `outfits/bulk` only
feeds out-of-room views. Player-level RRPlus status rides a separate player property keyed
**`"HasRecRoomPlus"`** (0xFD497C8, registered in `Player$$Awake` 0x19CF440, read by
`RecRoom.AppUI.LocalPlayerWidgetViewModel$$InitializeDataItems` 0x9706330).

## The message channel that does exist: `cards.iam`

The only server-driven arbitrary-text surface is the in-app-message push, still present in 2026 as
`cards.iam` (0x96503 in `stringliteral.json`) / `cards.iamdeleted`, payload
**`RecNet.InAppMessageDTO`** (15 fields), rendered by
`RRUI.Data.Notifications.MessageNotificationController_InAppMessageDTO$$Initialize` **0xD801B0**:

```
MessageId · SenderMessageId · IsBroadcast · Platform (PlatformType) · PlatformTypeMask (PlatformMask)
Priority int · SentAt DateTime · <WKDCHMJMBKF> bool · IsClientRead bool
Channel  (RecNet.InAppMessageChannel   #46402: None 0, Announcements 1, JustInTimeTutorials 2)
ContentType (RecNet.InAppMessageContentType #46401: Unknown 0, ContentBlock 1, JustInTimeTutorialTrigger 2)
<UNETSPILNQP> string · ContentObject (RecNet.NPEFNKEXJEN)
```

With `Channel = Announcements (1)` and `ContentType = ContentBlock (1)`, `ContentObject` is a
`RecNet.ContentBlock`:

```
TrackingCategory · Layout (ContentBlockLayout #46392: Default 0, Vertical 1, Horizontal 2)
TextSize (ContentBlockTextSize) · TitleTextPlacement (ContentBlockTitlePlacement)
HeaderOverride · Title · Body · ImageNames List<string> · Buttons List<ContentBlockButton>
```

`ContentBlockButton { LinkType, LinkName, LinkUriOrParameter, LinkButtonLabel }` with
`RecNet.ContentBlockLinkType` **#46391**: `Url 0, AccountId 1, EventId 2, RoomName 3,
Storefront 4, ActionCode 5, Item 6, CustomAvatarItem 7, AuthorizedRecNetUrl 8, Close 9`.

So a titled card with body text, images and buttons — and `Storefront 4` deep-links to the store
(the RRPlus signup) while `Close 9` is a plain dismiss. It is **not** correlated with the save: it
arrives as a notification whenever the server sends it.

⚠️ `'RRPlusMessageTitle'` / `'RRPlusMessageBody'` (0xFD5BB98 / 0xFD5B848) look like server-settable
copy for a restriction dialog but are **not** — both are referenced only by
`<>c__DisplayClass13_0$$<TryPurchaseSku>g__OnRRPlusMembershipPurchaseSuccess|11` 0x2916E80, i.e. the
*purchase succeeded* message.

## The native path: let the client enforce the Plus gate

The client already owns the whole "non-subscriber touched a Plus-only avatar feature" flow, and it
is driven entirely by local subscription state:

| method | RVA |
|---|---|
| `RRUI.Data.AvatarCustomizationModel$$get_IsLocalPlayerRRPlusSubscriber` | 0x249C5E0 |
| `…$$AddRRPlusRestriction` | 0x248E6D0 |
| `…$$RemoveRRPlusRestriction` | 0x2495540 |
| `…$$LiftRRPlusRestrictions` | 0x24933F0 |
| `…$$AdjustRRPlusRestrictionOnUndoOrRedo` | 0xD0A4C0 (shared stub) |
| `…$$ShowRRPlusUpsellDialog` | 0x2497CC0 |
| `…$$SetClonedAvatarDataToLocalAvatarAndLiftRestrictions` | 0x24961E0 |
| `RRUI.Data.RRPlusExclusiveBodyPaintUpsellDialogModel$$DismissRRPlusDialogAndRemoveRRPFeatures` | 0x249E540 |
| `…$$OnSubscriptionUpdated` | 0x249E850 |
| `…$$TryPurchaseRRPlus` / `$$ShowRRPlusDetails` | 0x249EA40 / 0x249E9F0 |

`DismissRRPlusDialogAndRemoveRRPFeatures` calls `RemoveRRPlusRestriction` **twice** (body paint and
aura), pushes an `AddUndoStack` entry and fires a change delegate — i.e. the client itself strips
the perks and tells the player why. Log line: `'Player dismissed RRPlus restriction dialog.'`

`get_IsLocalPlayerRRPlusSubscriber` resolves through the injected interface `RecNet.AWWNSFRHFFK` via
the extension `RecNet.HMQHCVODEZA$$MDRXJSKOFYA` **0x8DB0F80** — **48 call sites**, which is every
RRPlus gate in the client (storefronts, nametag toggle, `<RoomRestrictionsGate>d__210`,
`WatchUI.ShowRecRoomPlusPage`, the avatar customizer). Separately,
`RecRoom.AppUI.Data.RecRoomPlusDataManager$$get_HasRecRoomPlusSubscription` **0x96BA330** and
`RRUI.Data.RecRoomAIConversationModel$$get_IsRRPlusSubscriber` **0x2739E00** read
`RecNet.Commerce$$GXLRRHSAEWC` 0x93FD420 — i.e. `Commerce.CurrentSubscriptionInfo?.Subscription`,
which is populated **only** by
[econ-campuscard-updateandgetsubscription](econ-campuscard-updateandgetsubscription-wire-shape.md).

⚠️ **So a broken `UpdateAndGetSubscription` leaves every RRPlus gate reading from a null cache.**
Fix that route first: with correct subscription state the client blocks the Plus-only save itself,
with real UI, and the server never has to refuse. `AvatarAuraModel$$LocalPlayerCanEquipAura`
(0xD24D80) is the shared `return true` stub, so **auras are not gated at equip time** — only body
paint has the dedicated upsell dialog.

## Trap: `call 0x2350` is interface dispatch, not a helper

Several methods above show `mov ecx, <N>; mov rdx, <MethodInfo>; mov r8, <this>; call 0x2350`.
`0x2350` is the **interface-dispatch thunk** on this build and `ecx` is the interface slot index —
not `String.Equals`, not `Enum.Parse`. Mis-reading it as a string/enum helper makes `cmp eax, 2`
after it look like an enum comparison when it is a boolean interface result. Examples:
`CanAvatarOutfitBeSaved` 0x28A41DC / 0x28A41F4, `<SaveOutfitAsync>d__61` 0x28AEDB5 (slot 0x2A) and
0x28AEDD1 (slot 0x1A).
