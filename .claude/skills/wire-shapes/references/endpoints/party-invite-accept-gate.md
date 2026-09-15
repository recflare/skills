# Party invite accept gate

> CONFIRMED FIXED 2026-08-26: a game invite needs Type=GameInviteV2(6) AND Data = escaped JSON RoomInviteDetails {InviteId,Name,InviteMode}; a bad Data THROWS in the post-deserialize hook -> registrar logs 'Deserialization returned null' -> total silence. Also maps every gate on the watch-notification and chat-invite paths.

Derived **2026-08-26** from build `20250718.01` via [recflare-2025-metadata-carve](../../../il2cpp-analysis/references/recflare-2025-metadata-carve.md), diagnosing
"invite renders correctly, click deletes the message and then nothing happens".


## The WATCH notification path is a DIFFERENT DTO (not RecNet.ChatMessage)

A "X invited you to join them in room ^Y!" popup with a **"Go now"** button is NOT the chat
`PartyInviteChatMessageModel` path above. It is `RecRoom.Core.WatchUI.HandleIncomingRecNetMessage`
`0x187ED70` over `PDMHJMEKAGD` / concrete `PNAFJFAEEEE`, formatter `CLOPDDHBAHI` `.ctor 0x7AB8A90`,
**7 wire keys**:

| key | offset | type |
|---|---|---|
| `Id` | 0x10 | long |
| `FromPlayerId` | 0x18 | int |
| **`SentTime`** | 0x20 | DateTime |
| `Type` | 0x28 | `KHAAMCHNGDI` |
| `Data` | 0x30 | string |
| `RoomId` | 0x38 | **Nullable\<long\>** |
| `PlayerEventId` | 0x48 | **Nullable\<long\>** |

⚠️ **This DTO really does use `SentTime`** — the `TimeSent` rule above is only for
`RecNet.ChatMessage`. `ToPlayerId` and `CreatedAt` are not keys and are dropped silently.

### Type must be `GameInviteV2 = 6`

`KHAAMCHNGDI`: `DEPRECATED_GameInvite 0`, `GameInviteDeclined 1`, `GameJoinFailed 2`,
`FriendInvite 4`, `VoteToKick 5`, **`GameInviteV2 6`**, `PartyActivitySwitchV2 7`, `PartyInvite 8`,
`RequestGameInvite 10`, `TextMessage 30`, `CoachMessage 100`, `VirtualClubAnnouncement* 100000+`.

`HandleIncomingRecNetMessage` does `dec eax; cmp eax,0x13; ja <no popup>` then a 20-entry jump table
(RVA `0x187F5F4`) for types **1..20** — so **type 0 renders no popup at all**. Type 6 → `0x187F423`
→ the "Go now" branch; type 8 → "Accept"; type 10 → "Invite".

The **"Go now" label itself** only appears when `Matchmaking.GJLHHMPLFEB(FromPlayerId)` returns a
cached presence AND `ADEDKDNDABF.HPEJNCLLLFE()` is true — that reads `[presence+0x60]`, the parsed
`AppVersion` object. **Seeing "Go now" proves `GET player?id=` is being consumed correctly.**

### Button chain

`PlayWatchNotification(..., Action = GBKOPKHHKPC.ODBGMNFCPIE, label, ...)`
→ `WatchUI.EFBDCBEDMBC(notif).Then(OHLNKLKDMEI)`
→ `OHLNKLKDMEI` → `WatchUI.HFPIODKELGL(notif, true)` `0x187E490`
→ `PFFCBNBJIFG.PKOPIGAOJNA(Type)` → `PFFCBNBJIFG.BCIOENDEHAE(Type)` `0x22E30C0` = type→action registry.

- `EFBDCBEDMBC` `0x187C790` carries `'Invalid message. This message will now be deleted'` but is
  **gated on `Type == 100001`** (invention announcement) — for every other type it returns an
  already-resolved promise. **Do not read that literal as a general invite failure.**
- Registry table RVA `0x22E3C08` (types 0..20): **types 0 and 6 share handler `0x22E3A34` =
  `new IGMGEFIPJAH()`**. Types **9, 12, 13, 14, 15, 16, 17, 18, 19 have NO handler** (`0x22E3B62`
  returns null) — for those the button is a no-op with zero logging.
- `IGMGEFIPJAH.NAALCJNAPMC()` `0xCF97F0` builds the text with `'<room name loading...>'` /
  `'<account name loading...>'`, so the action resolves a room from **`RoomId`** — a null/absent
  `RoomId` leaves it nothing to go to.

## The chat-message path (a different flow)

## The gate chain

`RRUI.Data.PartyInviteChatMessageModel.CanAcceptPartyInvite()` `0x259E6F0`:

```
if (HasPartyInviteExpired()) return false;
if (senderAccountModel == null) return false;            // this+0x150
if (senderAccountModel.presence == null) return false;   // +0x120
return presence.IsOnline;                                // ADEDKDNDABF+0x44
```

`HasPartyInviteExpired()` `0x259E7C0`:

```
(DateTime.UtcNow - chatMessage.TimeSent.ToUniversalTime()).TotalMinutes
    > PNAHAINBHAH.NBDAFCHJCGM()
```

- `chatMessage` = `ChatMessageModel` field `0x00D0`, type **`RecNet.ChatMessage`**; the DateTime is
  `+0x28` = wire key **`TimeSent`** ([chat-sendmessage-wire-shape](chat-sendmessage-wire-shape.md) has the full 6-key list).
  It is the **only** DateTime field on the type and `TimeSent` the only DateTime key, so the
  pairing is unambiguous.
- `NBDAFCHJCGM()` `0x7CBAC90` = cached `settings/partyinvite` value (svc 9 Chat, literal
  `'Failed to get party invite settings'`, see [chat-settings-partyinvite-wire-shape](chat-settings-partyinvite-wire-shape.md)).
  Returns **30** (`mov eax, 0x1e`) only while the static cache is the `-1` sentinel; once the
  server answers, that value is cached for the process lifetime.

## The trap

The property is *named* something else in C# but **the wire key is `TimeSent`**. `SentTime` and
`CreatedAt` are both wrong and both dropped silently by Utf8Json → the field stays
`default(DateTime)` = `0001-01-01` → elapsed ≈ 2 million minutes → **every invite expired forever**.

Same DTO is the payload for the `ChatMessageReceived` websocket channel
([notification-types-2025](notification-types-2025.md)) — the notification frame and the REST body share one formatter, so
there is exactly one spelling to get right, in both places.


## Upstream of all of the above: the packager lookup (Type, Version)

The invite only *becomes* a `PartyInviteChatMessageModel` if a packager matches. `MOJCAIGCBGC`
`.BPNJMIEMGCK(MessageJson, bool)` `0x803EC90`:

```
if (MessageJson == null) bail          ; ChatMessage.CPOBHIECLEN already logged 'Error parsing message!'
packager = NCCKGGLACOH(msg.Version, msg.Type)   ; 0x803F7C0, key = (Version @+0x10, Type @+0x14)
if (packager == null) log 'No packager registered for the supplied message type ({0}) and version({1}).'
```

`MessageJson` fields are UNOBFUSCATED: `Type` 0x10, `Version` 0x14, `Data` 0x18.

Registered packagers (`ABOGEKBDALP()` = Version, `DJNDAKOFMMJ()` = Type):

| packager | Type | Version | details type |
|---|---|---|---|
| `BHGIEPAFNCB` | Text 0 | **2** | `TextMessageDetails` |
| `LEBAAGCKMEM` | **PartyInvite 1** | **1** | (via `OEPPGJEODLM<T>`) |
| `FHOMAKIPFAI` | Photo 2 | 1 | `PhotoMessageDetails` |
| `HFAGDNBKGCP` | from field +0x28 | 1 | `TextMessageDetails` |

Only **Type 3 (VoiceChatConnectionInfo)** is version-agnostic — `NCCKGGLACOH` zeroes the key's
version for it (`cmp edi,3 / mov dword [rbx+0x14],0`). Every other type must match Version exactly.

So a party invite REQUIRES:

```json
"Contents": "{\"Type\":1,\"Version\":1,\"Data\":\"<inviter display name>\"}"
```

`PartyInviteMessageDetails..ctor(string)` `0x8040C10` = `String.Concat(Data, " sent a party invite!")`
— `Data` is the inviter's NAME and becomes the visible body text. Null `Data` leaves `MessageJson`
null ([chat-sendmessage-wire-shape](chat-sendmessage-wire-shape.md)).

**Wrong Version = no model = no Join action at all**, and then `HasPartyInviteExpired` /
`CanAcceptPartyInvite` / `AcceptPartyInvite` never run. Distinguishing the three failures:

| symptom | meaning |
|---|---|
| log `Error parsing message!` | `Contents` unparseable or `Data` null |
| log `No packager registered ... type (X) and version(Y)` | wrong `Version` (or `Type`) |
| no `settings/partyinvite` request on click | model never built — one of the two above |
| `settings/partyinvite` fetched, still nothing | expiry gate → `TimeSent` |
| room-by-id request fires, then stalls | past the gate; problem is in the join |

## How to tell this apart from a join failure

`SessionManager.TryJoinPlayer(int, account, presence, mode)` `0x2177A50` **always** fetches the room:

```
presence == null || presence.RoomInstance == null  -> NullReferenceException (0x2177CA1)
else KCHDMOJGHJD.AFKPOMIFDFD(RoomInstance.RoomId, false)   ; logs 'No such room' on miss
     -> continuation FNOBGMPMCPH.OKMNIJOFNEN(HGMJJMJDHLJ targetRoom)  0x2180020
```

So **if the click produced no room-by-id request, `TryJoinPlayer` never ran** and the failure is in
`CanAcceptPartyInvite`, not the join. A room fetch that happens and then stalls is the other half.

**Why:** none of these gates log anything, so a bad timestamp key and a healthy join path are
indistinguishable from the UI — the request trace is the only signal.

## NotificationGroupPreference gates every watch popup

`HandleIncomingRecNetMessage` calls `PNAFJFAEEEE.POGPOELEPGM(Type, settings)` `0x7D48820`
**before** the type switch; **false = no popup at all, silently**.

It ANDs a bitmask against a per-type bit. Mask comes from `EGCFIPALFLN.FDNPHKBNONJ()` `0x7D29940`,
which reads the player setting key **`'NotificationGroupPreference'`** (throws if the settings
provider is null). Flags `GHMAAFKIGII`: `ALL -1`, `NONE 0`, **`Games 1`**, `FriendRequests 2`,
`FriendStatusOnline 4`, `Cheers 8`, `Rooms 16`, `Subscriptions 32`, `PlayerEvents 64`, `Clubs 128`,
`CreatorFeedback 256`, `RoomNotifications 512`, `Gifting 1024`.

Per-type bit (byte table RVA `0x7D48B58` -> jump table `0x7D48B48`, types 0..20):

| types | requires |
|---|---|
| 0, 1, 2, **6 (GameInviteV2)**, 8, 10, 11 | **`Games` (1)** |
| 4 (FriendInvite), 40 (FriendRequestAccepted) | `FriendRequests` (2) |
| 20 (FriendStatusOnline) | `FriendStatusOnline` (4) |
| 50, 51 (PlayerCheer*) | `Cheers` (8) |
| 60-63 (RoomCoOwner*, RoomTranslation) | `Rooms` (16) |
| 81 (PlayerEventInvitation) | `PlayerEvents` (64) |
| 3, 5, 7, 9, 12-19, and anything unmapped | **none - returns TRUE** (`0x7D489AE`: `mov al,1`) |
| 80, 90, 91 | always FALSE (`0x7D48A17`: `xor al,al`) |

**The filter is permissive by default** - unmapped types pass unconditionally. That is why a mask
missing `Games` looks like "every other notification works, just not game invites".

**Serve `NotificationGroupPreference = -1` (ALL) or at least bit 1.** A missing/0 value suppresses
every watch notification with no log — and it only becomes visible once `Type` is a value the
switch actually handles, which is why fixing `Type 0 -> 6` can look like a regression.

## Two popup builders - only one needs the sender's ACCOUNT

`HandleIncomingRecNetMessage`'s type switch ends in one of two calls:

- `0x187F123` / `0x187F126` -> **`WatchUI.KILKNBECPEH(notif, text, ...)` directly**. No account
  needed. Used by types 3, 20, 81, 100, ... These keep working even when accounts are broken.
- **`WatchUI.AIFGBBIFIFO(notif, format, category, buttonLabel)` `0x187A9D0`** -> reads iface slot 3
  (`FromPlayerId`), calls **`LPNHLJBDCLH.CHGEEFABLNL(FromPlayerId)` `0x7C85D60` = GetAccountById**,
  and only builds the popup in the `.Then` continuation `DBLOHDNOMAL.GEAJAFMIIHL(senderAccount)`
  `0x188C930`, which formats the text via `PHCHGFEEEMG.OJKBJPNAJOE()` (display name) before calling
  `KILKNBECPEH`. **`GameInviteV2` (6) uses THIS path.**

So a broken/missing account lookup kills exactly the sender-name notifications (game invites, friend
invites, cheers-from-X) and leaves every other type working - which reads as
"other notifications work, just not this one".

Grep the client log for `Failed to GetAccountById: No such account {0}` or
`Failed to GetAccountById: Invalid accountId {0}` (`0x7C85DC5` / `0x7C85DD1`).

Ruled out as gates on this path: `KBHICAJBFCL.EKIKNPHMBBK` `0x7C82510` (returns true except types
81 and 200-202), `WatchUI.HOKKGHPMHBB` `0x187EB30` (only special-cases categories Club 7 / Event 12),
and the type-6 branch itself `0x187F423` (no bail - the presence lookup only decides the "Go now"
label).

## ROOT CAUSE: `Data` is parsed per-Type by the post-deserialize hook

`PNAFJFAEEEE.CPOBHIECLEN` `0x7D48280` switches on `Type` (`this+0x28`) and parses `Data`
(`this+0x30`) into `this+0x58` = interface slot 7 `HPDBADMOOJM()`:

| Type | `Data` must be |
|---|---|
| **6 `GameInviteV2`, 7** | **JSON object -> `AOMBKFDJLHO` (RoomInviteDetails)** |
| 2, 50, 51, 130 | a plain integer (`Int32.Parse`) |
| 20 | (own branch `0x7D48409`) |
| 8, 200, 201, 202 | (own branch `0x7D483E8`) |
| 120 | `GiftReceivedDetails` |
| 220 | `CustomAvatarItemModerationFlaggedDetails` |
| **0 and anything unlisted** | **not parsed at all** |

**On failure it THROWS** (`0x7D485D6`: `new System.Exception("RoomInviteDetails deserialization "
+ "failed: '" + Data + "'")` -> `il2cpp_raise_exception` at `0x7D48651`), which aborts
deserialization of the whole frame. The websocket registrar `LMBGGGGNBOB.ENONAEIPKDD` `0x7D5DD10`
then reports **`Deserialization returned null`** and the notification object is never constructed -
so NOTHING downstream runs: no watch row, no `player?id=`, no `GetAccountById`, no popup.
That total silence is the signature of a bad `Data` on a Type that parses it.

**`AOMBKFDJLHO`** (formatter `JFBLJCLFMKK` `.ctor 0x7C17270`), 3 keys:

```json
"Data": "{\"InviteId\":12345,\"Name\":\"^GoldenTrophy\",\"InviteMode\":22}"
```

`InviteId` long (= `RoomInviteId` from POST invite, [matchmaking-invite-wire-shape](matchmaking-invite-wire-shape.md)),
`Name` string, `InviteMode` enum `EKFPOCGIIEF`: `None 0`, `LeaveParty 1`, `InviteParty 2`,
`PartyAutoFollow 3`, `EveryoneAutoFollow 4`, `InviteOnlineFriends 20`, `FullInstanceReinvite 21`,
`PlayTogether 22`.

Slot 7 is what `IGMGEFIPJAH.NAALCJNAPMC()` `0xCF97F0` reads (`mov ecx, 7`) to build the
"... invited you to join them in room ^X!" text - **the room name comes from `Data.Name`, not
`RoomId`**. A bare id string like `"1000202"` fails the parse, so switching Type 0 -> 6 turns a
half-working card into total silence: type 0 never parsed `Data`, type 6 requires it.
