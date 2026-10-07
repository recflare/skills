# Econ api/consumables routes wire shapes (+ why a potion lasts seconds)

> **`POST api/consumables/v1/updateActive` IGNORES ITS RESPONSE ENTIRELY** (`CNDMDLNHDLI`) — any 2xx
> is equivalent, so it can never be the cause of a consumable expiring early. So does
> `POST api/consumables/v1/consume`.
> The consumable's duration and active state live in **`GET api/consumables/v2/getUnlocked`**, whose
> wire DTO `.FDPNJHFIICP` is a **grouped** row: `{Ids:[long], CreatedAts:[date], ConsumableItemDesc,
> Count, InitialCount, IsActive, ActiveDurationMinutes, IsTransferable, ThumbnailImageName,
> FriendlyName}`. `ActiveDurationMinutes` (`int?`) is the **only** duration anywhere in the
> consumable wire model.

Derived **2026-10-06** from build `20250718.01`, while diagnosing a potion that activated and then
deactivated a few seconds later.
Facade **`.PEEKIHPGAGG`** (17 methods). All routes are service **28 = Econ** (`mov r8d, 0x1c`).

| route | verb | entry | request | response |
|---|---|---|---|---|
| `api/consumables/v2/getUnlocked` | **GET** | `OCHNJOJPMOM` `0x7CDA700` | none | `HPBKMCLEANE<T>`, inst #85895 = **`List<.FDPNJHFIICP>`** — bare array |
| `api/consumables/v1/updateActive` | **POST** | `PKAJDAFOBHK` `0x7CDAC50` | JSON `.ActivateConsumableItemRequest` (inst #15022) | **`CNDMDLNHDLI` — IGNORED** |
| `api/consumables/v1/consume` | **POST** | `LEHLNOEOOAI` `0x7CDA1A0` | JSON `.ConsumableItemRequest` (inst #15023) | **`CNDMDLNHDLI` — IGNORED** |
| `{0}v1/getTransferable/{1}` | — | `AJCOHHFAIOI` `0x7CD95B0` | none | `HPBKMCLEANE<T>`, inst #85895 = `List<.FDPNJHFIICP>` |
| `api/consumables/v1/transfer` | — | — | — | not derived |

`getTransferable` is assembled from the shared prefix `'api/consumables/'` (`0xD126C28`) plus
`'{0}v1/getTransferable/{1}'`, so grepping for `api/consumables/v1/getTransferable` finds nothing.
Its verb was not pinned.

## ⚠️ `updateActive` cannot be the cause of an early expiry

Send helper is **`MGPBDIAGCFD.CNDMDLNHDLI`** at `0x7CDADD6` — the **no-response** tier. There is no
`T`, no formatter, and no shape to match.

- Return **any 2xx**; `{}`, `204` and a full object are identical to the client.
- `IONCMJIACFI` cannot fire (nothing parses the body).
- `LLCLDPPAGIJ` cannot fire (no envelope — `{"Success": false}` with a 200 reads as **success**).
- A rejection has to be a **non-2xx status code**, and even then the only observable is the status.

Same tier and same consequences as [api-images-v1-report](api-images-v1-report-wire-shape.md) and
[rooms-v1-verifyrole](rooms-v1-verifyrole-wire-shape.md).

### Request — `.ActivateConsumableItemRequest` (unobfuscated), 3 keys

JSON body via `ELKIBCPINAP`; no `ELHKHFJEHLM`, so nothing is in the query string.

| key | CLR |
|---|---|
| `Id` | **long** |
| `IsActive` | bool |
| `ActivatedByRoomie` | bool |

```json
{ "Id": 90210, "IsActive": true, "ActivatedByRoomie": false }
```

⚠️ **`Id` is the `long` inventory-row id, not the item descriptor.** A value like
`VQSgL2pTLkWx4B3kwYG7UA` is a base64-packed GUID and belongs in `ConsumableItemDesc`; it can never
appear in this body. The `long` the client sends comes from an element of the **`Ids` array** of the
`getUnlocked` row — so if the server cannot map that long back to the inventory row it handed out, it
will accept the POST, return 200, and flip nothing. The client cannot tell, because it never reads
the response.

## `POST api/consumables/v1/consume` — same ignored tier (re-verified 2026-10-06)

Re-derived from a **full** slot dump of `PEEKIHPGAGG.LEHLNOEOOAI` `0x7CDA1A0` (+0x350), not a
filtered one. The method contains **exactly one** send call —
`MGPBDIAGCFD.CNDMDLNHDLI` at **`0x7CDA3CB`** — and no `HPBKMCLEANE`, `CJBFDPLCIEJ` or
`KBIHOFDDIMI` anywhere. **The response body is ignored; there is no response shape.** Return any
2xx.

Verb **POST**, read properly this time from the `HttpMethod` statics load
`mov rsi, qword ptr [rcx+0x20]` at `0x7CDA330` (where `rcx` is `[statics+0x90]`), feeding
`AKJEAMCCEOH..ctor` at `0x7CDA366`; service **28** (`mov r8d, 0x1c` at `0x7CDA355`). Whole-route
literal `'api/consumables/v1/consume'`. **Zero `ELHKHFJEHLM`** — nothing in the query string.

### Request body — `.ConsumableItemRequest`, 2 keys

One `ELKIBCPINAP` at `0x7CDA3B5`, generic inst **#15023 = `.ConsumableItemRequest`** (typedef
#21948). Formatter **`EJDNDKOKKND` `.ctor 0x78822C0`** (+0x330); the `____stringByteKeys` run is
`0x78824FF`..`0x7882556` — 2 keys, 1:1 with the 2 declared fields:

| # | key | CLR | off |
|---|---|---|---|
| 1 | `Id` | **long** | 0x10 |
| 2 | `DeltaCount` | int | 0x18 |

```json
{ "Id": 90210, "DeltaCount": 1 }
```

`Id` is read as `consumable.Id` (`[[rdi+0x10]+0x10]` → `[rsi+0x10]` at `0x7CDA3A1`) — again the
**long inventory-row id** from the `getUnlocked` `Ids` array, not the `ConsumableItemDesc`.

### ⚠️ `DeltaCount` is the raw argument; the LOCAL decrement is `Math.Abs`

Two different values, and this is the part worth knowing:

- **Local:** `consumable.Count -= Math.Abs(count)` — `neg eax` / `cmovs eax, ebp` / `sub esi, eax`
  at `0x7CDA2D0`..`0x7CDA2D9`, written straight back into the cached DTO's `Count` field
  (`[rbx+0x20]`). This is the `System.Math` TypeInfo at `0x7CDA2B8`.
- **Wire:** `DeltaCount = count` **unmodified** (`mov ecx, [rdi+0x18]` → `[rsi+0x18]` at
  `0x7CDA3A5`) — *not* absolute-valued.

So treat `DeltaCount` as "how many were consumed" and subtract **`|DeltaCount|`**, which is what the
client has already done to its own copy. Do **not** read it as a signed delta to add: a negative
`DeltaCount` would still have decremented the client's cache.

And because the response is ignored, **the client's `Count` and the server's can drift permanently**.
Nothing corrects it until the next `GET api/consumables/v2/getUnlocked` — and that resync is fed
straight into the `INIGJDDNEOE` reconcile below, which is what deactivates an active consumable. A
server that decrements differently from `|DeltaCount|` therefore shows up as a potion switching
itself off, not as a wrong count.

### The only thing the reply can do is roll back the local count

There is **no success continuation** on this route. The single callback attached after
`CNDMDLNHDLI` (via `JMNHOAIMFBC.AOCLNBFKPEP` at `0x7CDA3D5`) is the **error** handler
`.FEJFKDGBBOK.JKMMINMNNDK(string error)` `0x7CD1820` (+0x80), whose closure is
`{APFHNDMEABH consumable, int deltaCount}`. Its entire body is the inverse of the pre-send
decrement:

```
consumable.Count += Math.Abs(deltaCount)      # neg/cmovs = abs, add, store [rbx+0x20]
```

(`0x7CD1872`..`0x7CD1880`). That is **all** it does: it does not remove the row, does not touch
`IsActive` or `ActiveDurationMinutes`, and raises no event.

⚠️ **So neither the body nor the status code of this response can deactivate a consumable.** A
non-2xx only restores the cached `Count`; a 2xx does nothing at all. If an effect dies shortly after
this response is delivered, the response is **not** the cause — see below.

### ⚠️ Holding this response stalls everything behind it — the "delivering it deactivated the potion" trap

Observed while debugging: pausing the `consume` response at a proxy kept the potion alive, and
releasing it deactivated the potion "shortly after". That is **not** causation by this response. The
2025 client dispatches **every** HTTP request through one serial FIFO pump `CBACIMLIBPF`
([serialized-request-queue-stall](../../../rr-client-bringup/references/serialized-request-queue-stall.md)), so holding any one response
blocks every request queued behind it. Releasing it drains the queue, and the **next** request — not
this one — carries the real trigger.

Prime suspect once the type-71 push is ruled out: a `GET api/consumables/v2/getUnlocked` that comes
back with the row **absent** or **`IsActive: false`** (because the server deleted/zeroed it on
consume), feeding the `INIGJDDNEOE` reconcile described below.

The websocket push channel is a **separate socket** and is *not* on this HTTP pump, so a push is not
delayed by a held HTTP response — which is how the two causes can be told apart: if pausing an HTTP
response delays the deactivation, the trigger is HTTP, not a push.

**How to find it:** the `[Pump]` / `[Send]` log hooks in `recnet-plugin-unstable` print the queue's
dispatch order. Release the held response and read the next few `[Send]` lines; that names the
request directly. Do not infer it from the consume response.

### Client-side preconditions — it may not send at all

Before building the request, `LEHLNOEOOAI` tests the **cached** `consumable.Count`
(`cmp dword ptr [rax+0x20], 0` / `jle` at `0x7CDA2AB`). If it is `<= 0` the client:

1. calls `PEEKIHPGAGG.PAFLIBIKCNN(consumable.Id)` at `0x7CDA4B8` — dropping the row from its local
   cache, and
2. throws via `JFNOOGODOOA.FPEGBJHGPDL` with **`'Count is 0'`** at `0x7CDA4DB`,

**without issuing any HTTP request.** So a missing `consume` call in a capture can mean the client
believed the stack was empty — i.e. a `Count` your `getUnlocked` under-reported — rather than a
client bug. `.FEJFKDGBBOK::JKMMINMNNDK` is the continuation closure; `.JCFICNGFDLA` is the valueless
task the method returns.

## `GET api/consumables/v2/getUnlocked` — the authoritative state

Response is a **bare array** of `.FDPNJHFIICP` (typedef #21944). Formatter
**`PNBBCKBJLFL` `.ctor 0x7891EB0`** (+0xD40), `____stringByteKeys` run `0x7892815`..`0x7892AC4` —
10 keys, 1:1 with the 10 declared fields in offset order:

| # | key | CLR | off |
|---|---|---|---|
| 1 | `Ids` | `List<long>` | 0x10 |
| 2 | `CreatedAts` | `List<DateTime>` | 0x18 |
| 3 | `ConsumableItemDesc` | string | 0x20 |
| 4 | `Count` | int | 0x28 |
| 5 | `InitialCount` | int | 0x2c |
| 6 | **`IsActive`** | bool | 0x30 |
| 7 | **`ActiveDurationMinutes`** | **`int?`** | 0x34 |
| 8 | `IsTransferable` | bool | 0x3c |
| 9 | `ThumbnailImageName` | string | 0x40 |
| 10 | `FriendlyName` | string | 0x48 |

```json
[ { "Ids": [90210, 90211], "CreatedAts": ["2026-10-06T00:00:00Z", "2026-10-06T00:01:00Z"],
    "ConsumableItemDesc": "VQSgL2pTLkWx4B3kwYG7UA",
    "Count": 2, "InitialCount": 5, "IsActive": true,
    "ActiveDurationMinutes": 30, "IsTransferable": false,
    "ThumbnailImageName": "…", "FriendlyName": "Speed Potion" } ]
```

⚠️ **This row is GROUPED, and the grouping is load-bearing.** One element covers every copy of one
`ConsumableItemDesc` the player owns: `Ids` and `CreatedAts` are **parallel arrays**, and
`PEEKIHPGAGG.HIBDIFCAANK` `0x7CD9EA0` expands them into one in-memory `.APFHNDMEABH` per
`(Ids[i], CreatedAts[i])` pair. So:

- `Ids.Length` must equal `CreatedAts.Length`, index-aligned.
- `Count` should match that length; `InitialCount` is the pre-consumption total.
- Returning one element per copy (un-grouped, each with a 1-element `Ids`) also works, but emitting a
  `null` or short `CreatedAts` will mis-pair the expansion.

**`IsActive` and `ActiveDurationMinutes` are per-group, not per-copy.** There is no `IsActive` on the
individual copies — the client's per-copy model `.APFHNDMEABH` gets its `IsActive` from the group.
`ActiveDurationMinutes` being `Nullable<int>` means `null` is representable and is **not** the same as
`0`.

`.FDPNJHFIICP` and `.APFHNDMEABH` are adjacent typedefs (#21944 / #21945) with eight overlapping
field names, and `APFHNDMEABH` has its own 11-key formatter `ALDOAELPEMB` `.ctor 0x787D290` keyed
`Id` / `CreatedAt` / `ActivatedByRoomie` (singular). **That formatter is not this route's shape** —
`APFHNDMEABH` is the client-side model. Pinning the type from the send's generic inst (#85895) rather
than from the plausible nearby formatter is what separates them.

## Diagnosing "Potion activated" then "Potion deactivated" a few seconds later

The two toasts come from
`RecRoom.Consumable.AvatarItemEffects.AvatarItemConsumableEffect.HLFFPCOMEJD` `0xFB3FC0`
(`'Potion activated'`) and `.JDIKLBMOFAN` `0xFB43F0` (`'Potion deactivated'`), which delegate to
`RecRoom.Consumable.ConsumableEffect` `0xF9A7D0` / `0xF9A8E0`. Subclasses:
`HandPotionConsumableEffect`, `HeadPotionConsumableEffect`, `CameraFilterConsumableEffect`,
`RoomieConversationalStatusEffectConsumableEffect`.

**Useful negative result: the client does not expire a consumable on a local timer.** A disassembly
sweep of the whole `ConsumableEffect` + `ConsumableManager` range (`0xF9A150`–`0xFA0950`) finds **no**
`TimeSpan.FromMinutes`/`FromSeconds`, no `DateTime` arithmetic, no `AddMinutes`, no `UtcNow` —
nothing that could turn `CreatedAt + ActiveDurationMinutes` into a countdown. So an early
deactivation is **data-driven**, not a client clock bug, and it is not worth looking for a
client-side duration constant.

The only path to `ConsumableEffect.LocalDeactivateConsumable` `0xF9AD80` is:

| caller | trigger |
|---|---|
| `ConsumableManager.DeactivateConsumableOfCategory` `0xF9C940` | explicit: the UI toggle (`BackpackScreen.Button_ToggleActiveState`, `RRUI.Data.ConsumableModel.Use`), or `ActivateConsumable` swapping out the previous consumable in the same category |
| **`ConsumableManager.INIGJDDNEOE` `0xF9E6C0`** | **a reconcile against a freshly downloaded list** |

`INIGJDDNEOE` is the one to care about. It is registered as a delegate in `ConsumableManager.Awake`
(MethodDef slot at `0xF9C31E`, used at `0xF9C529`) — hence `callxref` reports zero call sites — and it
walks the consumable list comparing entries with `APFHNDMEABH.PHGIAKEDBEK` / `.BDCEBPMLGHE`
(`op_Inequality` / `op_Equality`), then calls `LocalDeactivateConsumable`, `ActivateConsumable` and
`PEEKIHPGAGG.PKAJDAFOBHK` (`updateActive`, at `0xF9ECA9`) to make the local state match.

So the shape of the bug is: the client activates locally, POSTs `updateActive` (and ignores the
reply), then the next `getUnlocked` — fed into `DownloadPurchasedConsumables` `0xF9CE40` →
`MEAENBGALJN` `0xF9F3C0` — comes back saying the consumable is **not** active, and the reconcile
dutifully deactivates it.

**Checklist, in the order worth testing:**

1. Does `GET api/consumables/v2/getUnlocked` return **`IsActive: true`** for that
   `ConsumableItemDesc` *after* the `updateActive` POST? If it still says `false`, the POST was not
   persisted — most likely because the posted `long Id` did not match a row (see the `Id` warning
   above). **This is the single most likely cause.**
2. Is **`ActiveDurationMinutes`** non-`null` and the real duration? `null` and `0` are distinct on
   the wire and neither is a safe default.
3. Are `Ids` and `CreatedAts` the **same length and index-aligned**? A mismatch mis-pairs the
   expansion in `HIBDIFCAANK`, so the client may be tracking a different copy than the one it
   activated.
4. Does `Count` match `Ids.Length`?

**RESOLVED 2026-10-06 — the trigger is the `ConsumableMappingRemoved` websocket push.** See the
section below. `getUnlocked` carries **no** `DIDJOECFJII` response cache, so the delay was never a
cache TTL — unlike [itemwishlists-v1-routes](itemwishlists-v1-routes-wire-shapes.md), which has a 5s one; it is the
round-trip of the server's own push after `consume`.

## ⚠️ `ConsumableMappingRemoved` (push type 71) is what deactivates the effect

Empirically confirmed by blocking `POST api/consumables/v1/consume` at the proxy: the potion then
**never deactivated**. The deactivation is driven by the push the server sends in response to that
consume, not by anything in the HTTP reply (which is ignored — see above).

`PEEKIHPGAGG.OCOPJMCPGIB` `0x7CDAA10` registers three handlers through
`LMBGGGGNBOB.KOOMBBKFAEP<T>`, with the notification type id in `ecx`:

| id | enum member | handler | payload `T` |
|---|---|---|---|
| **70** (`0x46` at `0x7CDAAC8`) | `ConsumableMappingAdded` | `PEEKIHPGAGG.GHBJMIDPOCD` `0x7CD9DF0` | inst #1093 = **`.APFHNDMEABH`** |
| **71** (`0x47` at `0x7CDAB07`) | `ConsumableMappingRemoved` | `PEEKIHPGAGG.IEKFCNNGEHI` `0x7CDA020` | inst #1093 = **`.APFHNDMEABH`** |
| 110 (`0x6E` at `0x7CDAB42`) | `FreeGiftButtonItemsAdded` | `PEEKIHPGAGG.NFHKGCAAKDO` `0x7CDA5E0` | plain `System.Action` — **no payload** |

The ids come from **`.EMNAKPGIHDN`** (typedef #22327), the 39-member **numeric** RecNet notification
enum (`RelationshipChanged 1`, `MessageReceived 2`, `PresenceHeartbeatResponse 4`, `RefreshLogin 5`,
… `StorefrontBalanceUpdate 61`, `ConsumableMappingAdded 70`, `ConsumableMappingRemoved 71`,
`PlayerEventCreated 80`, `InventionModerationStateChanged 100`, `LocalRoomKeyCreated 120`).

⚠️ **These two do not appear in `il2cpp-2025/notifications-2025.txt`.** That generated table is
built from *string* literals, and `ConsumableMappingAdded`/`Removed` exist **only as metadata enum
member names** — they are dispatched by integer, never by name. `grep` over
`out/stringliteral.json` finds nothing; `py fieldfind.py ConsumableMappingRemoved` finds the enum.
Any numerically-dispatched notification is invisible to that table.

### The chain, hop by hop

1. Server pushes **type 71** with an `.APFHNDMEABH` payload.
2. `IEKFCNNGEHI` `0x7CDA020` null-checks it (`APFHNDMEABH.BDCEBPMLGHE`, `op_Equality`, at
   `0x7CDA051`) and calls `PEEKIHPGAGG.PAFLIBIKCNN(payload.Id)` at `0x7CDA078`.
3. `PAFLIBIKCNN` `0x7CDAB60` (+0xF0) removes that row from the owned-consumables list and
   **tail-jumps to the change-event delegate** at `0x7CDAC2F`, passing the removed item
   (`rcx = [statics+0x90]`, `rdx = item`).
4. `ConsumableManager.INIGJDDNEOE` `0xF9E6C0` — registered as a delegate in
   `ConsumableManager.Awake` (MethodDef slot `0xF9C31E`, used at `0xF9C529`) — reconciles, finds the
   active consumable is no longer owned, and calls `ConsumableEffect.LocalDeactivateConsumable`
   `0xF9AD80`.
5. `AvatarItemConsumableEffect.JDIKLBMOFAN` `0xFB43F0` prints **`'Potion deactivated'`**.

Hop 4's event wiring is **inferred**, not traced — the raiser at `0x7CDAC2F` and
`ConsumableManager`'s `add_` are both linker-folded, so the delegate edge cannot be read statically.
Hops 1–3 and 5 are read directly from the binary, and the proxy experiment closes the loop.

### Payload — `.APFHNDMEABH`, 11 keys (the PER-COPY DTO, not the grouped one)

Formatter **`ALDOAELPEMB` `.ctor 0x787D290`** (+0xE90), run `0x787DCEE`..`0x787DFE8`:

| # | key | CLR | off |
|---|---|---|---|
| 1 | `Id` | long | 0x10 |
| 2 | `ConsumableItemDesc` | string | 0x18 |
| 3 | `Count` | int | 0x20 |
| 4 | `InitialCount` | int | 0x24 |
| 5 | `CreatedAt` | DateTime | 0x28 |
| 6 | `ActiveDurationMinutes` | `int?` | 0x30 |
| 7 | `IsActive` | bool | 0x38 |
| 8 | `IsTransferable` | bool | 0x39 |
| 9 | `ActivatedByRoomie` | bool | 0x3a |
| 10 | `ThumbnailImageName` | string | 0x40 |
| 11 | `FriendlyName` | string | 0x48 |

```json
{ "Id": 90210, "ConsumableItemDesc": "VQSgL2pTLkWx4B3kwYG7UA",
  "Count": 1, "InitialCount": 5, "CreatedAt": "2026-10-06T00:00:00Z",
  "ActiveDurationMinutes": 30, "IsActive": true, "IsTransferable": false,
  "ActivatedByRoomie": false, "ThumbnailImageName": "…", "FriendlyName": "Speed Potion" }
```

Note the **singular** `Id` / `CreatedAt` and the extra `ActivatedByRoomie`: this is the per-copy
sibling of the grouped `getUnlocked` DTO `.FDPNJHFIICP`, and the two are adjacent typedefs
(#21945 / #21944) with eight shared field names. The push uses **this** one. Only `Id` is actually
read by `IEKFCNNGEHI`, but the whole object must deserialize or the handler never runs.

### What the server should do instead

The client **already does its own bookkeeping** on consume — `Count -= |DeltaCount|` locally, and it
calls `PAFLIBIKCNN(Id)` itself when the cached `Count` reaches 0 (see above). So a type-71 push for
the row the player just consumed is **redundant at best**, and fatal when that row is the one
carrying the active effect.

Options, cheapest first:

1. **Do not send `ConsumableMappingRemoved` for the row that is currently active.** Activating a
   potion consumes a copy *and* keeps an active mapping; those must not be the same `Id` from the
   client's point of view.
2. If the consumed copy genuinely disappears, follow the removal with a
   **`ConsumableMappingAdded` (70)** carrying the surviving active mapping — `IsActive: true` and
   `ActiveDurationMinutes` set — so the reconcile finds the consumable still owned.
3. Simplest test to confirm the diagnosis: **stop sending type 71 on consume entirely** and let the
   next `getUnlocked` resync the count. If the potion then runs its full duration, this is the bug.

Either way the push's `Id` has to be the **long inventory-row id** the client knows from the
`getUnlocked` `Ids` array. A type-71 push with an `Id` the client has never seen is a silent no-op;
one with the *active* row's `Id` kills the effect.

`ConsumableManager` raises `OnActiveConsumableChanged` / `OnPurchasedConsumableChanged` (error
literals `'Error raising OnActiveConsumableChanged: '` / `'…OnPurchasedConsumableChanged: '`) from
`NIPIBHINHJA` `0xF9F730` and `OEDOMBJBKKB` `0xF9F880`; the facade's cache mutators
`GHBJMIDPOCD` `0x7CD9DF0`, `IEKFCNNGEHI` `0x7CDA020`, `LLLFJAFMAFN` `0x7CDA4F0` and
`PAFLIBIKCNN` `0x7CDAB60` are the likely publishers — not confirmed.

## Not the same thing: `api/roomconsumables/v1/*`

The creator-side room-consumable CRUD lives on a **different facade** `.PLDJEBOENBJ` with
`Guid`-keyed ids (`api/roomconsumables/v1/roomConsumable`, `.../awardBulk`,
`.../roomconsumable/{0}/purchase/currency`, `.../purchase/tokens`), and is **enveloped-tier with real
response types** (`HPBKMCLEANE<.JMHPDGFLBDG>` etc). Its `'Unable to update consumable'` literal
(`0xD162E60`) is easy to mistake for the player-inventory path. See
[roomconsumables-by-room](roomconsumables-by-room-wire-shape.md). Nothing on that facade affects a potion's duration.
