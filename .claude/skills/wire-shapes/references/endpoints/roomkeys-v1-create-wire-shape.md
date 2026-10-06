# Roomkeys v1 create wire shape

> POST api/roomkeys/v1/create (svc 28 Econ) sends 7 FORM fields and returns a BARE 2-key object {Status, RoomKey} — Status is the UNOBFUSCATED enum RecRoom.DataLayer.RoomKeyResult (Success 0), RoomKey is the same 10-key JODGFDKLMBO the /v1/room route returns.

Derived **2026-09-25** from build `20250718.01`.
Sibling of [roomkeys-v1-room](roomkeys-v1-room-wire-shape.md), which documents the `JODGFDKLMBO` element in full.

`POST https://econ.<host>/api/roomkeys/v1/create` — service **28 = Econ**
(`mov dword ptr [rsi+0x18], 0x1c` at `0x7D961E9`), verb **POST** (`HttpMethod` statics
`[rcx+0x20]` at `0x7D961A8`). Whole-route literal, slot `0xD14F658`.

Client entry `LHMONGGMNAI.AMMILKOFFCC` **`0x7D95F10`** (+0x680); the thin overload at `0x7D95E60`
shares the name. Sole UI caller **`RRUI.Data.RoomKeyModel.CreateRoomKey`** `0x2818970` —
unobfuscated, which confirms the route's purpose.

## Request — 7 form fields

Seven `MGPBDIAGCFD.ELHKHFJEHLM` calls. The verb is POST, so these are an
**`application/x-www-form-urlencoded` body**, not query params
([elhkhfjehlm-verb-dependent-params](../conventions/elhkhfjehlm-verb-dependent-params.md)) — reading them as query params
mis-specifies the whole route.

| # | field | RVA of the add |
|---|---|---|
| 1 | `Type` | `0x7D96228` |
| 2 | `RoomId` | `0x7D9629E` |
| 3 | `Name` | `0x7D962C5` |
| 4 | `Description` | `0x7D962EC` |
| 5 | `Price` | `0x7D96323` |
| 6 | `ImageName` | `0x7D9634F` |
| 7 | `PurchaseCurrencyId` | `0x7D96391` |

`Type` is the `CAIBPLFEHJI` enum — `Key 0`, `CircuitEventKey 1`. The method also carries the client
-side literals `'Room key creation error'` and **`'Keys are not allowed in Rooms2'`**, so the client
refuses before sending for a Rooms2 room.

## Response — BARE object, no envelope

`MGPBDIAGCFD.HPBKMCLEANE<T>` (response required), generic inst **#1091** = **`.AMNEJJIFIBM`** — the
DTO itself, not an envelope. Formatter `HEILOGJJLPB` `.ctor 0x767D200`, key run at `0x767D43F` /
`0x767D496` — **2 keys, 1:1 with the 2 declared fields**:

| # | key | CLR | off |
|---|---|---|---|
| 1 | `Status` | enum **`RecRoom.DataLayer.RoomKeyResult`** (unobfuscated) | 0x10 |
| 2 | `RoomKey` | `.JODGFDKLMBO` | 0x18 |

```json
{ "Status": 0,
  "RoomKey": { "RoomKeyId": 900001, "ReplicationId": "0f8c…", "RoomId": 12,
               "Name": "VIP Key", "Description": "…", "Price": 250,
               "PurchaseCurrencyId": null, "CreatedAt": "2026-01-01T00:00:00Z",
               "ImageName": null, "Type": 0 } }
```

`{}` or an empty body throws `IONCMJIACFI`. `AMNEJJIFIBM.CPOBHIECLEN` is the shared no-op
`0xA60520`, so there is **no post-deserialize validation** — both keys are omittable at parse time.

⚠️ **Not pinned: whether `RoomKey: null` is safe on a non-Success status.** The result is consumed
through a Task continuation off `RoomKeyModel.CreateRoomKey` that I did not follow to the field read,
and the sibling route's consumer *does* NRE on a null ([roomkeys-v1-room](roomkeys-v1-room-wire-shape.md)). Always send the
full object on `Success`; treat `null` on an error status as untested.

## `RecRoom.DataLayer.RoomKeyResult : int` (typedef #58420, unobfuscated, 19 members)

| val | name | val | name |
|---|---|---|---|
| 0 | `Success` | 10 | `PriceIsInvalid` |
| 1 | `InvalidParameters` | 12 | `PermissionDenied` |
| 2 | `DoesNotExist` | 13 | `PlayerHasRoomUnderModerationReview` |
| 3 | `NameTooShort` | 14 | `JuniorStatusFail` |
| 4 | `NameTooLong` | 15 | `PlayerIsNotCoOwner` |
| 5 | `DuplicateName` | 16 | **`RoomKeyLimitReached`** |
| 6 | `InappropriateName` | 17 | `PlayerAlreadyOwns` |
| 7 | `DescriptionTooShort` | 18 | `RoomUnderModerationReview` |
| 8 | `DescriptionTooLong` | 19 | `PurchaseFailed` |
| 9 | `InappropriateDescription` | | |

**There is no `11`.** Numeric on the wire, and `Success` is `0`, so an omitted `Status` reads as
success — the same trap as `PlayerEventResponse.Type`
([playerevents-v1-responses](playerevents-v1-responses-wire-shape.md)).

`RoomKeyLimitReached (16)` pairs with the `RoomKeyConfig.MaxKeysPerRoom` game-config value the
client reads locally before it even offers the button — see
[gameconfig-v2-roomkeyconfig](gameconfig-v2-roomkeyconfig.md).

## Siblings

Other whole-route literals on this facade: `api/roomkeys/v1/awardbulk`, `/v1/mine`, `/v1/owns`,
`/v1/owns/bulk`, `/v1/revoke`, plus the `String.Format`-built `/v1/room?roomId=`.
`/v1/owns` and `api/roomkeys/` return a **bare `bool`**.
