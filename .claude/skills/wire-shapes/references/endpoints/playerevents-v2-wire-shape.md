# Playerevents v2 wire shape

> Wire shape of POST api/playerevents/v2 (create) and the whole v2 edit family for recflare-2025 — response is {PlayerEvent, Result, TagModifyResult}, and edits are per-field PUTs that need PlayerEvent echoed back.

Derived **2026-08-19** from `C:\Games\recflare-2025` (build `20250718.01`) via
[recflare-2025-metadata-carve](../../../il2cpp-analysis/references/recflare-2025-metadata-carve.md). All on `BPHIJNEOCMK`, service **2 = API**.

**`POST api/playerevents/v2`** (`MEJDANGEEJA`, `0x7E441B0`) — **POST**, JSON body via
`ELKIBCPINAP`, no query params. Body `HKFACONKBBO` (formatter `LMGCGJFACOA` ctor `0x772F770`),
14 keys: `RoomId` long, `SubRoomId` long?, `ClubId` long?, `Name`, `Description`,
`Tags` List\<string\>, `ImageName`, `StartTime` DateTime, `EndTime` DateTime, `Accessibility` enum,
`IsMultiInstance` bool, `SupportMultiInstanceRoomChat` bool, `DefaultBroadcastPermissions` enum,
`CanRequestBroadcastPermissions` enum.

Re-verified **2026-08-25** the proper way (read `T` off the send generic, not the method's return
type): create uses `LMKONLJOAEP<ALNFIGPAIBK>` — the facade's **bare**, description-less helper — so
the response really is unenveloped. Body keys re-read from the `LMGCGJFACOA` trailing
`____stringByteKeys` run at `0x7730410` and matched 1:1 against the 14 declared fields.
Both request enums are numeric, values in [playerevents-v1-room-wire-shape](playerevents-v1-room-wire-shape.md):
`Accessibility` = `Private 0 / Public 1 / Unlisted 2`; the two broadcast fields =
`None 0 / RoomOwners 256 / All 2147483647` (**not** 0/1/2).

**Response `ALNFIGPAIBK`** (formatter `HICOHMHIJAP` ctor `0x7722CA0`) — bare, 3 keys:
`PlayerEvent`, `Result`, `TagModifyResult`. **Every v2 create/edit call returns this same envelope.**

`PlayerEvent` = `EAAICKJKHED : NEMBNIGCMFK` (formatter `KACECPHFCNP` ctor `0x77276E0`), 18 keys —
derived member first, per Utf8Json inheritance order: `Tags`, then `PlayerEventId` long,
`CreatorPlayerId` int, `RoomId` long, `SubRoomId` long?, `ClubId` long?, `Name`, `Description`,
`ImageName`, `StartTime`, `EndTime`, `AttendeeCount` int, `Accessibility`, `IsMultiInstance`,
`SupportMultiInstanceRoomChat`, `DefaultBroadcastPermissions`, `CanRequestBroadcastPermissions`,
`BroadcastingRoomInstanceId` long?.

`TagModifyResult` = `EKDKFKMDIIO` `{Result, Tags}`, where **`Tags` is `List<string>`** (unlike
`PlayerEvent.Tags`, which is `List<{Tag,Type}>` on BOTH builds — see
[playerevent-tags-build-difference](playerevent-tags-build-difference.md)).

⚠️ **CORRECTED 2026-09-23: `TagModifyResult.Result` is its OWN enum `CJJEIGDCFGB`, not the event
`CPIAPAGENIK`** — 11 members, tag-specific: `Success 0`, `TooManyTags 1`, `TagUseRestricted 2`,
`InvalidTag 3`, `InappropriateTag 4`, `TagTooLong 5`, `TagNotFound 6`, `TagAlreadyExists 7`,
`NoChange 8`, `TagRepeated 9`, `LacksPermission 10`.

The **event-level** `Result` is `CPIAPAGENIK`, 36 members, 0-based: Success 0,
HasModeratorClosedEvent 1, DoesNotExist 2, PlayerDoesNotExist 3, RoomDoesNotExist 4,
StatusUnchanged 5, PrivateEvent 6, SomethingWentWrong 7, DoesNotOwnRoom 8, ResponseDoesNotExist 9,
PlayerAlreadyInvited 10, EventDatesInvalid 11, EventTooLong 12, EventTooShort 13,
InappropriateName 14, InappropriateDescription 15, SomeInvitesFailed 16, CannotInviteJunior 17,
EventCountLimitReached 18, DoesNotOwnEvent 19, UnregisteredOrJuniorNotAllowed 20,
InvalidClubPermissions 21, ImageDoesNotExist 22, SubRoomDoesNotExist 23, DoesNotOwnSubRoom 24,
ModifyTagsFailed 25, RoomCapacityTooLow 26, BroadcastEventNotMultiInstance 27,
PlayerNotAllowedToCreateMultiInstanceEvents 28, PlayerBannedFromEventCreation 29,
EventIsModerationClosed 30, EventIsModerationPendingReview 31, InvalidRecurringEventSchedule 32,
EventIsInModerationBlockedRoom 33, JuniorsCannotCreateEvents 34.

## Why editing breaks even when create "works"

**Every edit method takes the existing event object as its first parameter**
(`NEMBNIGCMFK CJOEGPGHFJH`) and builds the URL from *its* `PlayerEventId`. The client gets that
object from `response.PlayerEvent`. So a create that returns `Result: 0` but a null/blank
`PlayerEvent` looks like success and then leaves nothing to edit — no request is ever attempted.
Nothing throws: `ALNFIGPAIBK.CPOBHIECLEN` (`0x7E40310`) null-guards each child, and
`EAAICKJKHED.CPOBHIECLEN` (`0x7E48350`) tail-jumps `Tags` into the list validator, which returns
false on null. **Echo the full created PlayerEvent, with a real `PlayerEventId` and
`CreatorPlayerId`.**

Edits are **per-field PUTs**, not one update call — `api/playerevents/v2/{id}/` + `name`,
`description`, `time`, `tags`, `image`, `room`, `club`, `accessibility`, `multiinstance`
(`JNLGFFDBCOK`, `JOMHFDEMNAC`, `PLGNAJGPDEF`, `AELPCLCDPBL`, …; verb read from `HttpMethod` statics
`+0x28`). There is also a **full update: `POST api/playerevents/v2/{id}`** (`JIOCEHKLMDC`,
`0x7E436E0`, 12 params, verb `+0x20`), and `api/playerevents/v2/delete/{id}`.
All of them answer with the same `{PlayerEvent, Result, TagModifyResult}`.

## `POST api/playerevents/v2/delete/{id}` specifically (derived 2026-08-25)

`BPHIJNEOCMK.KHLEKGMOAEF(long playerEventId, CancellationToken)` `0x7E44090` — **POST**
(`HttpMethod` statics `+0x20`), service **2 = API**, path
`String.Format("api/playerevents/v2/delete/{0}", id)`, **no query params, no body**. Send is
`LMKONLJOAEP<ALNFIGPAIBK>` — the facade's **bare** (description-less) helper, so the response is the
plain `{PlayerEvent, Result, TagModifyResult}` object with no envelope
([playerevents-v1-room-wire-shape](playerevents-v1-room-wire-shape.md) has the bare-vs-enveloped rule).

**Unlike create/edit, `PlayerEvent` is not needed here.** `ALNFIGPAIBK.CPOBHIECLEN` (`0x7E40310`)
null-guards both child objects (`if (PlayerEvent != null) …; if (TagModifyResult != null) …`), and
the success continuation `RRUI.Data.EventModel.CHFGCBOLHDF` (`0x268A0C0`) **never reads `Result`** —
it just toasts `"Successfully deleted event."`, calls `BrowserModel.RemoveFromHistory` and refreshes.
So any deserializable body reports success; even `{}` works (it is an object DTO, so every member
takes its default). Prefer `{"PlayerEvent":null,"Result":0,"TagModifyResult":null}` for clarity.

Failure has to be signalled by a **non-2xx status**, not by `Result` — nothing on this path inspects
the enum. Callers: `EventModel.LBMBCMPLIEA` (`0x268DC90`, toasts `'Deleting event...'` first) and
`EventDetailsScreen.Awake`.

**How to apply:** if create succeeds but edit silently does nothing, check the create response's
`PlayerEvent` before suspecting the edit routes. If edits 404, it is the nine per-field PUTs that
are missing, not a single PUT.

## v1 is read-only — there is no `POST api/playerevents/v1`

Checked **2026-08-19**. The bare literal `api/playerevents/v1` (`0xD13DA98`) has exactly two
rip-relative refs, both inside `BPHIJNEOCMK.KFGMFCLHDFN()` (`0x7E43FC0`), which is a **GET**
(`HttpMethod` statics `+0x08`) taking no arguments and returning `List<NEMBNIGCMFK>` — the caller's
event list. There is no composed form of the path either (no `api/playerevents/` fragment literal),
so nothing else can be building it.

`api/playerevents/v1/{0}` (`0xD141078`) has four referencing methods — `IDMGLIJDECO(long)`,
`JPIPIIFCCFB(long,long)`, `MKPIFABOJCN(long)`, `GJBDGHKHMAO$$MoveNext` — and **all four are GET**.

The only v1 POSTs are response/invite/moderation traffic, not event CRUD:
`v1/respond`, `v1/bulkInvite`, `v1/deleteResponse`, `v1/report`, `v1/broadcast`, `v1/bulk`.

**So implementing `POST api/playerevents/v1` as a create cannot fix editing — the client never calls
it.** Creation is `POST api/playerevents/v2` and every edit is a v2 route.

The v1 GET returns the **base** `NEMBNIGCMFK` (formatter `CLAPAFCIEHB` ctor `0x7709A30`), 17 keys —
the v2 `PlayerEvent` list minus `Tags`: `PlayerEventId`, `CreatorPlayerId`, `RoomId`, `SubRoomId`,
`ClubId`, `Name`, `Description`, `ImageName`, `StartTime`, `EndTime`, `AttendeeCount`,
`Accessibility`, `IsMultiInstance`, `SupportMultiInstanceRoomChat`, `DefaultBroadcastPermissions`,
`CanRequestBroadcastPermissions`, `BroadcastingRoomInstanceId`. Bare array, no envelope.

⚠️ **CORRECTION 2026-09-02:** where this note says the parameters are **query params**, they
are actually an **`application/x-www-form-urlencoded` request body** — `ELHKHFJEHLM` routes params
to the query string only for GET. See [elhkhfjehlm-verb-dependent-params](../conventions/elhkhfjehlm-verb-dependent-params.md). Response shape
unaffected.


## ⚠️ Two corrections to this note (2026-09-23)

1. **`TagModifyResult.Result` is `CJJEIGDCFGB`**, an 11-member tag-specific enum — not the 36-member
   event `CPIAPAGENIK`. Both start `Success = 0`, which is why the mix-up survived: the success path
   looks identical and only error codes diverge.
2. **`PlayerEvent.Tags` is `List<{Tag,Type}>` on the 2025 build too**, not `List<string>` — see
   [playerevent-tags-build-difference](playerevent-tags-build-difference.md). A response that is otherwise byte-perfect and
   returns **200** is still rejected wholesale by the client if this field carries bare strings, so
   the event is created server-side while the client reports failure.

The user-facing message for an event `Result` is produced by
`LAEMBKPAEHH.JOGBEKHJAFI(CPIAPAGENIK) -> string` `0x7C68140` — 24 distinct strings, `Result 0` maps
to `"Success!"`. Useful in reverse: an on-screen message names the code the client believes it got.
