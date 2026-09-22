# Roomcoowner message data payload

> RoomCoOwnerInvited (Message Type 62) and its siblings 60/61 carry Data as a BARE DECIMAL ROLE NUMBER (Byte.TryParse -> PHBPGMMKBJJ), not JSON; the room comes from the Message's RoomId. Also: the DTO parse switch NOT handling a type does not mean Data is unused.

Derived **2026-09-14** from build `20250718.01` via [recflare-2025-metadata-carve](../../../il2cpp-analysis/references/recflare-2025-metadata-carve.md).
Refines [messages-v2-message-type-payloads](messages-v2-message-type-payloads.md).

## ⚠️ Correction to the parse-table reading

[messages-v2-message-type-payloads](messages-v2-message-type-payloads.md) maps `PNAFJFAEEEE.CPOBHIECLEN` `0x7D48280` and concludes that
a type with no case in that switch has `Data` "never parsed". **True at the DTO layer, false
overall** — the switch only does *eager* parsing into the `[IgnoreDataMember]` details object at
`+0x58`. Several types instead parse `Data` **lazily in their notification handler**, and
RoomCoOwnerInvited is one. Absence from that switch means "no eager parse / no throw", not
"Data is ignored".

## The per-type handler factory

`PFFCBNBJIFG.BCIOENDEHAE(PDMHJMEKAGD msg) -> AMBNCBOBOHH` **`0x22E30C0`** is a switch on
`msg.Type` that `new`s one handler class per message type. **It uses jump tables**, so scanning for
a `cmp reg, 0x3e` immediate gives a FALSE NEGATIVE — the 60–70 block is
`add ebx,-0x3c; cmp ebx,0xa; ja default` + table at RVA **`0x22E3BDC`** (`lea rcx,[rip-…]` makes the
base 0, so entries are absolute RVAs). Same trick in the watch-category mapper.

| Type | handler class |
|---|---|
| 60 `RoomCoOwnerAdded` | `.CGAOEJNIMEE` (`0x22E3801`) |
| 61 `RoomCoOwnerRemoved` | `.NMOKONFCNPO` (`0x22E382C`) |
| **62 `RoomCoOwnerInvited`** | **`.EAFCPFOCMFN`** (`0x22E3857`) |
| 63 `RoomTranslationCompleted` | `.HELJLDDFAOJ` |
| 64 `RoomModerationCompleted` | `.ENMFPAFEFGO` |
| 65–69 | default → unhandled |
| 70 `CreatorPublishedNewRoom` | `.ENOKGLMMLDD` |

## `Data` = the ROLE, as a decimal string

`.EAFCPFOCMFN : .NDKKDAFFKCM`. The base holds `PHBPGMMKBJJ DBLPKPJAPHN` (+0x70, cached role) and
`string DEEDCGPPKKH` (+0x78, cached display name); the message is at +0x58.

`NDKKDAFFKCM.ALIMPIHCCFN()` **`0xCFF1C0`**:

```
if (this[+0x70] != 0) return this[+0x70];     // cached
msg = this[+0x58];  if (msg == null) throw NRE
s   = msg.<interface slot 8>()                 // PDMHJMEKAGD.LAGKPBIDKEG = Data (string)
if (System.Byte.TryParse(s, out b)) this[+0x70] = b
return this[+0x70]
```

So **`Data` is a bare decimal number**, `Byte.TryParse`d into `PHBPGMMKBJJ`
([rooms-roles-wire-shape](rooms-roles-wire-shape.md)): `None 0`, `Banned 1`, `Host 10`, `Moderator 20`, `Contributor 25`,
**`CoOwner 30`**, `TemporaryCoOwner 31`, `Creator 255`. It mirrors the `InvitedRole` key on
`GET rooms/{id}/roles`. **Not JSON, not an object, no quotes-in-quotes** — unlike
`ChatMessage.Contents` ([chat-sendmessage-wire-shape](chat-sendmessage-wire-shape.md)).

`NDKKDAFFKCM.JALDNHNBPDH()` `0xCFF250`: if the cached name string is empty, call `ALIMPIHCCFN()` and
map the role through `LKLHHAKEHGI.LMIGDHDFDJI(role)` to the display name.

`EAFCPFOCMFN.NAALCJNAPMC()` **`0xD0C4E0`** builds the notification text:

```
"You are invited to be a " + <role name> + " of " + <room name> + "!"
```

Room name via `AMBNCBOBOHH.EKBJOAAACIF` `0xD04850`, resolved from the Message's **`RoomId`** (the
top-level key), with `'<room name loading...>'` / `'Loading...'` placeholders. So **`RoomId` must be
set** — it is not in `Data`.

## Failure mode is silent, not fatal

`Byte.TryParse` failing (null / empty / non-numeric `Data`) leaves the cached byte at **0 = None**,
so the message renders as "You are invited to be a <None-name> of …". No throw. The only NRE in the
getter is on a null *message*, which cannot happen over the wire.

## Watch category IS configured

`PFFCBNBJIFG.CMHPFBLIDGN` `0x22E4140` maps type → `NLHKHJNLGGH` (`Transient 0`, `General 1`,
`Friends 2`, `Official 4`, `Deprecated -1`) via the jump table at RVA **`0x22E4498`** for the 60–70
block. **60, 61, 62, 64 and 70 all → `General (1)`**; 65–69 fall to the default arm which logs
`"Message type {0} has no configured watch category"` and returns `-1`. So a type-62 message will be
categorised and shown.

## The client never sends type 62

`EGCFIPALFLN`'s senders (`DCJDOJEHBAO(long accountId, KHAAMCHNGDI type, string data, long? roomId)`
`0x7D28AF0`) only emit types **1, 2, 10, 11, 30, 41**. 60/61/62 are server-originated only.
Note that send signature: `data` and `roomId` are separate arguments — the room is never inside
`Data` for any type.

## Payload

```json
{ "Id": 9001, "FromPlayerId": 220, "SentTime": "2026-09-14T12:00:00Z",
  "Type": 62, "Data": "30", "RoomId": 1162, "PlayerEventId": null }
```

(`"30"` = CoOwner; use `"31"` for TemporaryCoOwner. Wrapped in the notification envelope
`{"Msg": {...}, "Id": "<string>"}` when pushed — see [messages-v2-message-type-payloads](messages-v2-message-type-payloads.md).)

## The 0–20 block of the same factory (resolved 2026-09-15)

Same method `PFFCBNBJIFG.BCIOENDEHAE` `0x22E30C0`. Low types are reached by a binary-search chain
(`cmp ebx,0x64 / 0x29 / 0x1e` …) ending at `cmp ebx,0x14; ja default` and a dense jump table at
RVA **`0x22E3C08`** (base 0, entries are absolute RVAs).

| Type | handler class | case |
|---|---|---|
| 0 `DEPRECATED_GameInvite` | `.IGMGEFIPJAH` | `0x22E3A34` |
| 1 `GameInviteDeclined` | `.EMJAJEHOENC` | `0x22E3988` |
| 2 `GameJoinFailed` | `.BIPDDNGOOKK` | `0x22E39B3` |
| 3 `DEPRECATED_PartyActivitySwitch` | `.DGBDBAMAKNI` | `0x22E3A5F` |
| **4 `FriendInvite`** | **`.OKDMMKBAJHB`** | `0x22E39DE` |
| 5 `VoteToKick` | `.DHALBKMDJDB` | `0x22E3A09` |
| 6 `GameInviteV2` | `.IGMGEFIPJAH` (same as 0) | `0x22E3A34` |
| 7 `PartyActivitySwitchV2` | `.DGBDBAMAKNI` (same as 3) | `0x22E3A5F` |
| 8 `PartyInvite` | `.GJFHFAPOLDO` | `0x22E3A8A` |
| 10 `RequestGameInvite` | `.MOMBPGGGLOG` | `0x22E3AB5` |
| 11 `RequestGameInviteDeclined` | `.DHLCEGHPPDO` | `0x22E3AE0` |
| 20 `FriendStatusOnline` | `.NEKFABILFEF` | `0x22E3B0B` |
| 9, 12–19 | **default → `throw NotImplementedException`** | `0x22E3B62` |

⚠️ **The default arm throws `System.NotImplementedException`**, it does not return null. Those gap
values are not `KHAAMCHNGDI` members, so `Enum.IsDefined` filters them before the factory sees them
— but a *new* type value that passes the filter with no handler would throw here.

### `FriendInvite (4)` does not use `Data`

Checked both mechanisms the correction above demands:
- **No eager parse** — 4 has no case in `PNAFJFAEEEE.CPOBHIECLEN`, so it falls to the default arm.
- **No lazy parse** — `OKDMMKBAJHB`'s 15 methods never dereference the Message's `Data` at `+0x30`
  (they read the handler's own `+0x10`/`+0x18`/`+0x20` and the message at `+0x58`), and neither does
  `AMAMAAGEIPI.PECGJFLFANL` `0x7D4DF30`, the one helper they hand the whole message to.

So `Data` may be `null`, `""` or anything; `FromPlayerId` carries the inviting player.
*Scope of that check: the handler's own methods plus its one delegated helper — not an exhaustive
proof that nothing anywhere keys on `Type == 4`.*

### Refinement: `VoteToKick (5)` does have a handler

[messages-v2-message-type-payloads](messages-v2-message-type-payloads.md) says "No consumer keyed to `Type == 5` turned up." The
factory **does** construct `.DHALBKMDJDB` for type 5, so a consumer class exists. Whether it reads
`Data` is not yet checked — that note's conclusion that `Data` is schema-free for VoteToKick rests
on the eager switch only, and should be re-verified against `DHALBKMDJDB` before being relied on.

### `FriendRequestAccepted (40)` and `FriendCodeUsed (41)`

Reached by the same binary-search chain (`cmp ebx,0x1e` → `cmp ebx,0x28` / `cmp ebx,0x29`), not the
`0x22E3C08` jump table:

| Type | handler class | case |
|---|---|---|
| **40 `FriendRequestAccepted`** | **`.PELLKEDEKNE`** | `0x22E390D` |
| 41 `FriendCodeUsed` | `.BCHLLDGNEON` | `0x22E3941` |

**`FriendRequestAccepted` does not use `Data`** — same two checks as type 4:
- **No eager parse** — 40 has no case in `PNAFJFAEEEE.CPOBHIECLEN`.
- **No lazy parse** — `PELLKEDEKNE` has only 7 methods (4 with real bodies) and dereferences nothing
  but the message pointer at `+0x58`; no `+0x30`. Following the chain two levels further —
  `AMBNCBOBOHH.OOOMEICMMML` `0xD05C00` → `IHCAGKGKJLH.FPKACMLMJPI` `0xCFB640` — turns up no `+0x30`
  either (the second reads no message field at all). Contrast the Data-using pattern at the top of
  this note: `RoomCoOwnerInvited` has a cached-parse field on its base *and* a dedicated parse
  method; `PELLKEDEKNE` has neither.

So `Data` may be `null`, `""` or anything; `FromPlayerId` carries the player who accepted.

**Behaviour:** `PELLKEDEKNE.IDCLNJODFPP` `0xD015B0` calls `RecRoom.Core.WatchUI.get_Local` then
**`RecRoom.Core.WatchUI.ShowIntroduceFriendsDialog`** `0x18848B0` — acting on this notification opens
the Introduce-Friends dialog. Text comes from `NAALCJNAPMC` `0xD016C0` via the base helper plus
`String.Concat`, not from `Data`.

Both 4 and 40 map to watch category `FriendRequests (2)` ([party-invite-accept-gate](party-invite-accept-gate.md)).
