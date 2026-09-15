# Messages v2 message type payloads

> The Message DTO (PNAFJFAEEEE, 7 wire keys) from GET api/messages/v2/get and the per-Type Data parse table — VoteToKick=5 has NO case in the switch, so its Data is never parsed; also which Types throw on bad Data.

Derived **2026-09-02** from build `20250718.01` via [recflare-2025-metadata-carve](../../../il2cpp-analysis/references/recflare-2025-metadata-carve.md).
Distinct from the *chat* message-content enum in [chat-sendmessage-wire-shape](chat-sendmessage-wire-shape.md) (that one is
`EDNOJBKNKKD`, only Text 0 / PartyInvite 1 / Photo 2 / VoiceChatConnectionInfo 3) and from the
websocket channels in [notification-types-2025](notification-types-2025.md) — this is the **inbox/notification Message**.

## Carrier

`GET api/messages/v2/get` — service **2 = API**, verb **GET** (`HttpMethod` statics `+0x08`), entry
`EGCFIPALFLN.MFANIOIDHEE()` `0x7D2B190`, error literal `'Failed to initialize message list'`.
Send generic `HPBKMCLEANE<List<PNAFJFAEEEE>>` (inst **1025**) — **bare array, no envelope**.
Siblings: `api/messages/v2/send`, `api/messages/v1/sendMultiple`,
`api/messages/v1/friendOnlineStatus`, `api/messages/v3/delete`
([messages-v3-delete-wire-shape](messages-v3-delete-wire-shape.md)).

## The Message DTO `.PNAFJFAEEEE`

Formatter `CLOPDDHBAHI` `.ctor 0x7AB8A90` — **7 wire keys**. The type declares 9 fields; the
`object` @`0x58` (parsed details) and `DateTime` @`0x60` (received-at) are **client-side only**,
both produced by the post-deserialize hook.

| # | key | CLR | offset |
|---|---|---|---|
| 1 | `Id` | long | 0x10 |
| 2 | `FromPlayerId` | int | 0x18 |
| 3 | `SentTime` | DateTime | 0x20 |
| 4 | `Type` | enum `KHAAMCHNGDI` | 0x28 |
| 5 | `Data` | string | 0x30 |
| 6 | `RoomId` | `long?` | 0x38 |
| 7 | `PlayerEventId` | `long?` | 0x48 |

`PNAFJFAEEEE.EMKFPBNAECK(msg)` `0x7D486B0` is literally
**`Enum.IsDefined(typeof(KHAAMCHNGDI), msg.Type)`** — a message with an undefined `Type` is filtered
out, so only values in the enum below are usable.

## `Data` is parsed per `Type` — `PNAFJFAEEEE.CPOBHIECLEN` `0x7D48280`

| `Type` values | what happens to `Data` | throws? |
|---|---|---|
| 2, 50, 51, 130 | `Int32.Parse(Data)`, boxed into `+0x58` | **FormatException** if non-numeric |
| 8, 200, 201, 202 | `Int64.Parse(Data)`, boxed | **FormatException** if non-numeric |
| 6, 7 | `Deserialize<BBJHHFGLGNF>` = **RoomInviteDetails** `{Guid, string}` | null result → `Exception("RoomInviteDetails deserialization failed: '<data>'")` |
| 20 | `IsNullOrEmpty(Data)` guard, then `Deserialize<GFBKIOJFDFB>` `{bool}` | no — empty `Data` skips to default |
| 120 | `Deserialize<OCNKEMFMECC>` = **GiftReceivedDetails** `{Guid, string}` | null → `"GiftReceivedDetails deserialization failed"` |
| 220 | `Deserialize<AOMBKFDJLHO>` = **CustomAvatarItemModerationFlaggedDetails** `{long, string, EKFPOCGIIEF}` | null → `"CustomAvatarItemModerationFlaggedDetails deserialization failed"` |
| **everything else** | **nothing** — falls to the default `0x7D484A9`, which only stamps `+0x60 = DateTime.Now` | never |

All parsing branches converge at `0x7D48499`: `this[+0x58] = <parsed>`.

## **VoteToKick = 5 has no case**

It lands in the default arm. **`Data` is never read, never parsed, and the parsed-details field
stays null** — so there is no payload schema to satisfy: `Data` can be `null`, `""`, or arbitrary
text and nothing throws. It only has to survive the `Enum.IsDefined` filter, which `5` does.

It sits in the legacy block (`DEPRECATED_GameInvite 0`, `DEPRECATED_PartyActivitySwitch 3`), and the
live vote-kick flow is the route `api/PlayerReporting/v3/voteToKick` `0xD120B20` plus in-room UI
(`'You are being vote kicked for '` `0xD217C10` in `LGMACPMCMNJ.PHEPNEEFDJP` `0x2186000`), not this
message type. No consumer keyed to `Type == 5` turned up.

## `.KHAAMCHNGDI : int` — full table

`DEPRECATED_GameInvite 0`, `GameInviteDeclined 1`, `GameJoinFailed 2`,
`DEPRECATED_PartyActivitySwitch 3`, `FriendInvite 4`, **`VoteToKick 5`**, `GameInviteV2 6`,
`PartyActivitySwitchV2 7`, `PartyInvite 8`, `RequestGameInvite 10`, `RequestGameInviteDeclined 11`,
`FriendStatusOnline 20`, `TextMessage 30`, `FriendRequestAccepted 40`, `FriendCodeUsed 41`,
`PlayerCheer 50`, `PlayerCheerAnonymous 51`, `RoomCoOwnerAdded 60`, `RoomCoOwnerRemoved 61`,
`RoomCoOwnerInvited 62`, `RoomTranslationCompleted 63`, `RoomModerationCompleted 64`,
`CreatorPublishedNewRoom 70`, `PlayerAttendingEvent 80`, `PlayerEventInvitation 81`,
`DEPRECATED_GroupInvitation 90`, `DEPRECATED_PlayerJoinedGroup 91`, `CoachMessage 100`,
`CoachDebugCommand 101`, `CoachMessageReportActioned 102`, `NewRoomComments 110`,
`GiftReceived 120`, `FriendIntroduction 130`, `ClubMemberInvited 200`, `ClubModeratorInvited 201`,
`ClubCoownerInvited 202`, `RoomEarningsDistributionCoOwnerAdded 210`,
`RoomEarningsDistributionCoOwnerRemoved 211`, `RoomEarningsDistributionPercentageUpdated 212`,
`CustomAvatarItemModerationFlagged 220`, and the `Virtual*` block `100000`–`100011`
(`VirtualClubAnnouncementRoomPublished` … `VirtualPartyUpRequest`).

## The websocket notification envelope `MDCEJFPDCEL<T>`

Confirmed **2026-09-02** from a live client stack. A pushed Message arrives wrapped:

```
INIGPFNLHFL.LABNBGADOBH<T>(ReadOnlyMemory<byte>)      Utf8Json entry
  OMIHNNODDCJ.LABNBGADOBH                             formatter for MDCEJFPDCEL<PNAFJFAEEEE>
    CLOPDDHBAHI.LABNBGADOBH                           formatter for PNAFJFAEEEE (the Message)
      ANAMOLLPKLG.HFLENAAHPHN / .KPBPEBLCJLL          JsonReader string primitives
```

`MDCEJFPDCEL<T> : BAKBIAOEPNB`, formatter `OMIHNNODDCJ` `.ctor 0x7C24F80`, **2 keys, derived
first**: **`Msg`** (the `T`) then **`Id`** — and the envelope's `Id` is a **`string`**
(`BAKBIAOEPNB.CMGKJAEFCGA` @0x10), whereas `Msg.Id` is a **`long`**. Swapping those is easy and silent.

```json
{ "Msg": { "Id": 1, "FromPlayerId": 220, "SentTime": "2026-09-02T11:39:30Z",
           "Type": 5, "Data": null, "RoomId": null, "PlayerEventId": null },
  "Id": "some-string" }
```

## Diagnosing `NKJABNHBPCA: expected:'String Begin Token', actual:'{'`

That is Utf8Json's `ANAMOLLPKLG` reader refusing an object where a quoted token belongs. Read the
frame **below** the reader frames to locate the DTO: `CLOPDDHBAHI` on the stack means the bad field
is on the **Message**, not the envelope. `PNAFJFAEEEE` has exactly **two** quoted-token readers —
**`SentTime`** (DateTime) and **`Data`** (string); `Id`/`FromPlayerId`/`Type`/`RoomId`/
`PlayerEventId` are all numeric. So an `actual:'{'` there is a `Data` (or `SentTime`) sent as a
nested **object** instead of a string. The `at offset:N` is a byte index into the raw frame, so
`frame[N]` is the offending `{`.

Same trap as `ChatMessage.Contents` ([chat-sendmessage-wire-shape](chat-sendmessage-wire-shape.md)): **`Data` is an escaped JSON
string, never a nested object** — and for the Types with no parse case (VoteToKick 5 among them)
`null` or `""` is equally fine.

## ⚠️ CORRECTION 2026-09-14 — "no case in the switch" does NOT mean `Data` is unused

The switch above is only the **eager** parse into the `[IgnoreDataMember]` details object at `+0x58`.
Several types instead parse `Data` **lazily in their per-type notification handler**, built by the
factory `PFFCBNBJIFG.BCIOENDEHAE(msg)` `0x22E30C0`. Example: **`RoomCoOwnerInvited (62)` reads `Data`
as a bare decimal role number** — see [roomcoowner-message-data-payload](roomcoowner-message-data-payload.md).

So the correct reading of the table is "no eager parse, and no `FormatException`/deserialize throw",
not "Data is ignored". To decide whether a given type uses `Data`, look up its handler class in that
factory's jump tables. ⚠️ `BCIOENDEHAE` and the watch-category mapper both dispatch via **jump
tables**, so grepping for a `cmp reg, <type>` immediate gives false negatives.
