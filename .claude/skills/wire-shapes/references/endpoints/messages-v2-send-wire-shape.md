# `POST api/messages/v2/send` — yes, the client calls it; body is ignored

> **The client does send messages.** `RecNet.Messages.SendMessage` **`0x9515B30`** is live, with
> **6 direct callers** (all thin typed wrappers in `RecNet.Messages`), **3 of which are reachable
> from gameplay/UI**.
> **POST** (svc **2 API**), request is **`application/x-www-form-urlencoded`** with up to four
> fields — **`ToPlayerId`**, **`Type`**, **`Data`**, **`RoomId`** — and **no JSON body, no query
> string**.
> ✅ **The response body is NEVER parsed.** The send is `RGBOOBRDHEB::JEYAQXBXMRA(ct)` `0x9537A00`
> → non-generic `Task` ⇒ status code only. **Any 2xx works, with any body or none.** Reject with a
> non-2xx.
> ⚠️ But the premise is half-right: the client only ever sends **5 of the 25 `MessageType` values**.
> Everything a player actually *sees* in their inbox — `GameInviteV2 6`, `PartyInvite 8`,
> `PlayerCheer 50`, `FriendRequestAccepted 40`, the `RoomCoOwner*` family, `CreatorPublishedNewRoom
> 70` — is **backend-originated** and never passes through this route. See the table below.

Derived **2026-10-27** from build `20260323.14`.

## Route

**`RecNet.Messages.SendMessage(long playerId, MessageType messageType, string data,
Nullable<long> roomId)`** **`0x9515B30`** (spans to `0x9515D60`) → `RecRoom.Async.NXPIPFBMDQY`.
The facade method name survives obfuscation.

| what | value | evidence |
|---|---|---|
| path | `api/messages/v2/send` | literal **`0xFC58A20`**, `mxref` = exactly **2** refs, both in this method (`0x9515BB1` init `lea`, `0x9515C25` use `mov`) — no `String.Format` |
| verb | **POST** | `0x9515C0A mov rax,[TypeInfo]` → `0x9515C11 mov rcx,[rax+0x20]` (statics) → `0x9515C15 mov rdi,[rcx+0x20]` — **`+0x20` = `HttpMethod.Post`** |
| service | **2 = API** | `mov r8d, 2` at `0x9515C2C`, into `RGBOOBRDHEB..ctor` `0x8BBF9E0` at `0x9515C44` |
| params | 4, **form body** | see below |
| JSON body | **none** | no `FZNGWUAGAIN` / `YHPVSAVMRFS` / `WOGHBITUUOI` call |
| response | **ignored** | `0x9515D23 call 0x9537A00` = `RGBOOBRDHEB::JEYAQXBXMRA(ct)` → non-generic `Task`; then `0x9515D2D` `RecRoom.Async.SAXZOKINUQZ::CTZMMSFIPBH` adapts it to `NXPIPFBMDQY` |
| client cache | **none** | no `ORUUDATDRUN` call |

### The four form fields

All four go through verb-dependent adders, and the verb is POST, so they land in `ODWNBEXQFEH`
`+0x30` = **`application/x-www-form-urlencoded`**
([elhkhfjehlm-verb-dependent-params](../conventions/elhkhfjehlm-verb-dependent-params.md)):

| order | field | adder at | overload | CLR |
|---|---|---|---|---|
| 1 | `ToPlayerId` | `0x9515C78` | `NJPEKLKCVCG(string, object)` `0x9538270` | boxed long |
| 2 | `Type` | `0x9515CAE` | `NJPEKLKCVCG(string, object)` `0x9538270` | boxed int (`MessageType`) |
| 3 | `Data` | `0x9515CDA` | `NJPEKLKCVCG(string, string, bool, bool)` `0x9537F80` | string |
| 4 | `RoomId` | `0x9515D11` | `NJPEKLKCVCG(string, object)` `0x9538270` | boxed `Nullable<long>` |

Casing is **PascalCase** on all four — same spellings as the response DTO on
[`GET api/messages/v2/get`](messages-v2-message-type-payloads.md).

**`Data` carries both skip-if-blank bools as `false`** (`r9d` xor-zeroed at `0x9515CC3`,
`[rsp+0x20] = 0` at `0x9515CD5`), so an **empty string is still transmitted** — only a literal
`null` is dropped.

**`RoomId` disappears when the `Nullable<long>` is empty.** Boxing a `Nullable<T>` with
`HasValue == false` yields `null`, and the object adder's explicit-list overload drops nulls:

```
0x95383ca  test rbx, rbx          ; rbx = the boxed value
0x95383cd  je   0x95385b0         ; -> skipped, nothing appended
```

➡️ So the three live wrappers all produce exactly:

```
POST /api/messages/v2/send
Content-Type: application/x-www-form-urlencoded

ToPlayerId=12345&Type=10&Data=
```

`RoomId` absent, `Data` present but empty. **Treat a missing `RoomId` and an empty `Data` as
normal**, not as a malformed request.

## Which `MessageType`s the client actually sends

Six wrappers call `SendMessage`; each hardcodes its `MessageType` immediate. `callxref` on
`0x9515B30` gives all six, and on each wrapper gives its own reachability:

| wrapper | `MessageType` | `data` / `roomId` | reachable from |
|---|---|---|---|
| `VOYZZHWLDUM(long)` `0x95165E0` | **10 `RequestGameInvite`** (`mov edx,0xa` `0x951663A`) | `""` / `null` | ✅ `SessionManager$$RequestGameInvite` `0x205C000`, `<SendRequestForInviteAfterRoomLoad>d__207` `0x1134680` |
| `IKMUEPFEGIC(long)` `0x9513AA0` | **11 `RequestGameInviteDeclined`** (`mov edx,0xb` `0x9513AFA`) | `""` / `null` | ✅ `RequestGameInviteNotificationController$$NotificationSlotOnDismiss` `0xD879F0`, `<>c__DisplayClass0_0$$<Show>g__RejectInvite\|3` `0x25F3CA0` |
| `DVPVDTOIQVC(long)` `0x95122E0` | **1 `GameInviteDeclined`** (`mov edx,1` `0x951233A`) | `""` / `null` | ✅ `RecRoom.MQPAYDMTBJO$$JDXJZALHZMS` `0xE3C9E0` |
| `EOZKGITVADX(long, int)` `0x9512370` | **2 `GameJoinFailed`** (`mov edx,2` `0x95123E0`) | `int.ToString()` `0x95123A9` / — | ⚠️ **0 direct call sites** |
| `FHPMFRADYXM(long)` `0x95124C0` | **41 `FriendCodeUsed`** (`mov edx,0x29` `0x951251A`) | — | ⚠️ **0 direct call sites** |
| `RUWOBXQLMUY(long, string)` `0x9515950` | **30 `TextMessage`** (`mov edx,0x1e` `0x95159B0`) | caller-supplied | ⚠️ **0 direct call sites** |

⚠️ **"0 direct call sites" is not proof of death** — `callxref` scans `call`/`jmp rel32` only, and a
wrapper whose stub was inlined into an async state machine or reached through a delegate is
invisible (the skill's standing caveat). `TextMessage 30` in particular looks **legacy**: player DMs
on 2026 are on the **Chat** service (`thread/*`), not here. Implement all six server-side; only the
top three are confirmed live.

### Everything else in the inbox is yours to originate

`.MessageType` (typedef #22510, int) — **25 members**, of which the client sends the 5 above:

```
DEPRECATED_GameInvite 0 · GameInviteDeclined 1* · GameJoinFailed 2* ·
DEPRECATED_PartyActivitySwitch 3 · FriendInvite 4 · VoteToKick 5 · GameInviteV2 6 ·
PartyActivitySwitchV2 7 · PartyInvite 8 · RequestGameInvite 10* ·
RequestGameInviteDeclined 11* · FriendStatusOnline 20 · TextMessage 30* ·
FriendRequestAccepted 40 · FriendCodeUsed 41* · PlayerCheer 50 · PlayerCheerAnonymous 51 ·
RoomCoOwnerAdded 60 · RoomCoOwnerRemoved 61 · RoomCoOwnerInvited 62 ·
RoomTranslationCompleted 63 · RoomModerationCompleted 64 · CreatorPublishedNewRoom 70 ·
PlayerAttendingEvent 80
```

`*` = client-sent. The other 20 must be **written by the server** into whatever
`GET api/messages/v2/get` reads, or pushed over the websocket.

⚠️ Do not confuse this with `RecRoom.Core.UI.RoomChat.MessageType` (typedef #16960, 4 members
`Default/Canned/System/Reaction`) — unrelated, in-room chat only.

### The modern invite path does **not** use this route

The player-facing "invite to game" action goes through two *other* facade methods that have their
own routes and **do** read a response:

```
static MPVTAJGPRUT<RecNetResult<RoomInviteDTO>> UGZQVQQCGMR(long, long, JoinRoomInviteMode)  0x95164D0
                                        <- SessionManager$$InvitePlayerToGame 0x2058900
static MPVTAJGPRUT<RecNetResult>              SSXIYLQOVVA(int[], long, JoinRoomInviteMode)  0x9515AC0
                                        <- <InvitePlayersToGame>d__175$$MoveNext 0x207BE80
```

Both have **0 literal references** — the route lives in a compiler-generated closure, so they are
**not derived**. ➡️ That is why `GameInviteV2 6` / `PartyInvite 8` never appear on `v2/send`: the
client posts an *invite*, and the backend fans out the message rows. **This is the part of the
premise that is correct.**

## The rest of `RecNet.Messages` (53 methods)

| facade | route literal | callers |
|---|---|---|
| `SendMessage` `0x9515B30` | `api/messages/v2/send` `0xFC58A20` | **this note** |
| `WVKZAPYEHQB(List<long>, MessageType, string, long?)` `0x9516790` | `api/messages/v1/sendMultiple` `0xFC58380` | ⚠️ **0** — the multi-recipient send appears unused |
| `FVTZXXJJFEW()` `0x9512DD0` | `api/messages/v2/get` `0xFC586D0` | [messages-v2-message-type-payloads](messages-v2-message-type-payloads.md) |
| `JWNOQQBBEPZ(IEnumerable<long>)` `0x9513FE0` | `api/messages/v3/delete` `0xFC58D70` | [messages-v3-delete](messages-v3-delete-wire-shape.md) |
| `SendOnlineStatusToFriends()` `0x9515D60` | `api/messages/v1/friendOnlineStatus` `0xFC58030` | 1 — `JQANEOELTUC$$MoveNext` `0x206DF80`; returns `MPVTAJGPRUT<SendOnlineStatusToFriendsResultDTO>` — **not derived** |

`FriendStatusOnline 20` therefore has its own route (`v1/friendOnlineStatus`) rather than riding
`v2/send`, and that one *does* read a DTO back.
