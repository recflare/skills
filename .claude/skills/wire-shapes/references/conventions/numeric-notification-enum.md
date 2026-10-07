# `.EMNAKPGIHDN` — the numeric RecNet notification enum

> Some websocket pushes are dispatched by **integer type id**, not by a string name — and those are
> **absent from `il2cpp-2025/notifications-2025.txt`**, which is generated from string literals.
> The ids live in `.EMNAKPGIHDN` (typedef #22327, `int`, 39 members). If a push you expect the client
> to handle cannot be found by grepping `out/stringliteral.json`, it is in here.

Recorded **2026-10-06** from build `20250718.01`, after `ConsumableMappingRemoved` turned out to be
the cause of a consumable effect ending early
([consumables-v1-v2-routes](../endpoints/consumables-v1-v2-routes-wire-shapes.md)).

## Why the generated table misses them

`notifications-2025.txt` (51 rows, `name | payload T | owner$$OCOPJMCPGIB`) is built by matching
**string literals** against the notification registrar. A numerically-dispatched push has no string
anywhere in the binary: `grep -in "ConsumableMappingRemoved" out/stringliteral.json` returns nothing,
while

```
py fieldfind.py ConsumableMappingRemoved     ->  22327 .EMNAKPGIHDN
py enumvals.py EMNAKPGIHDN                   ->  ConsumableMappingRemoved = 71
```

finds it immediately. **So a miss in `notifications-2025.txt` is not evidence that the client ignores
a push.** Check this enum before concluding that.

## Finding the handler and payload for an id

Registration is `LMBGGGGNBOB.KOOMBBKFAEP<T>(int typeId, Delegate handler, …)` with the id as an
**immediate in `ecx`**, called from each facade's `OCOPJMCPGIB` method. So:

1. `py enumvals.py EMNAKPGIHDN` → the id.
2. Disassemble the candidate facades' `OCOPJMCPGIB` and look for `mov ecx, <id>` immediately before
   a `KOOMBBKFAEP` call (or tail-`jmp`).
3. The handler is the `MethodDef` slot loaded for that call; the payload `T` is the call's generic
   inst, resolved with `ginst.py inst <n>` — **not** from a nearby `TypeInfo`.

Worked example — `PEEKIHPGAGG.OCOPJMCPGIB` `0x7CDAA10`:

| `mov ecx,` | id | member | handler | payload |
|---|---|---|---|---|
| `0x46` @ `0x7CDAAC8` | 70 | `ConsumableMappingAdded` | `PEEKIHPGAGG.GHBJMIDPOCD` `0x7CD9DF0` | inst #1093 = `.APFHNDMEABH` |
| `0x47` @ `0x7CDAB07` | 71 | `ConsumableMappingRemoved` | `PEEKIHPGAGG.IEKFCNNGEHI` `0x7CDA020` | inst #1093 = `.APFHNDMEABH` |
| `0x6E` @ `0x7CDAB42` | 110 | `FreeGiftButtonItemsAdded` | `PEEKIHPGAGG.NFHKGCAAKDO` `0x7CDA5E0` | plain `System.Action` — **no payload** |

A handler registered with a plain `System.Action` takes **no payload**, so for that id the body is
not deserialized at all.

## The enum

```
RelationshipChanged                 1     ConsumableMappingAdded              70
MessageReceived                     2     ConsumableMappingRemoved            71
MessageDeleted                      3     PlayerEventCreated                  80
PresenceHeartbeatResponse           4     PlayerEventUpdated                  81
RefreshLogin                        5     PlayerEventDeleted                  82
Logout                              6     PlayerEventResponseChanged          83
SubscriptionUpdateProfile          11     PlayerEventResponseDeleted          84
SubscriptionUpdatePresence         12     PlayerEventStateChanged             85
SubscriptionUpdateGameSession      13     ChatMessageReceived                 90
SubscriptionUpdateRoom             15     CommunityBoardUpdate                95
ModerationQuitGame                 20     CommunityBoardAnnouncementUpdate    96
ModerationUpdateRequired           21     InventionModerationStateChanged    100
ModerationKick                     22     FreeGiftButtonItemsAdded           110
ModerationKickAttemptFailed        23     LocalRoomKeyCreated                120
ModerationRoomBan                  24     LocalRoomKeyDeleted                121
ServerMaintenance                  25
GiftPackageReceived                30
GiftPackageReceivedImmediate       31
GiftPackageRewardSelectionReceived 32
ProfileJuniorStatusUpdate          40
RelationshipsInvalid               50
StorefrontBalanceAdd               60
StorefrontBalanceUpdate            61
StorefrontBalancePurchase          62
```

**The numbering is sparse** — 7–10, 14, 16–19, 26–29, 33–39, 41–49, 51–59, 63–69, 72–79, 86–89,
91–94, 97–99, 101–109, 111–119 are unassigned. An id the client does not recognise is dropped
silently, so a typo'd id and a correct one look identical from the server side.

Several names here duplicate rows that *are* in `notifications-2025.txt`
(`ChatMessageReceived`, `CommunityBoardUpdate`, …). Those pushes exist in both forms; do not assume
the numeric id and the string name share a handler or a payload type — resolve each separately.

## A push can be as destructive as a bad response

The lesson from the consumable case: a push handler mutates client state directly, with **no
response for the client to reject and no error path**. `ConsumableMappingRemoved` deletes an
inventory row by `Id` and raises a change event, which cascades into deactivating an active
consumable effect. The HTTP route the server was answering at the time
(`POST api/consumables/v1/consume`) ignores its own response body entirely, so **every observable
consequence came from the push** — and chasing the HTTP wire shape could not have found it.

Generalisable: when a route's response is `CNDMDLNHDLI` (ignored) and the client still visibly
reacts, the reaction came from somewhere else. Check this enum and the facade's `OCOPJMCPGIB`.
