# `PUT api/roomconsumables/v1/roomConsumable/{id}/consume` — the 2-key `Status` + `InventoryItem` object

> **`PUT api/roomconsumables/v1/roomConsumable/{roomConsumableId}/consume`** (svc **28 Econ**) returns
> a **BARE 2-key** object — `RecNet.RoomConsumableInventoryItemOperationResult` =
> **`{"Status": <int>, "InventoryItem": {…}}`** — in that key order.
> ⚠️ **`InventoryItem` must be present even on a FAILURE response.** The client resolves the
> inventory item *before* it looks at `Status`, and a null `InventoryItem` makes it return early, so
> **every failure status is silently discarded** and the consumable is never deactivated.
> ⚠️ `Status` is `RoomConsumableResult` where **`Success = 0`**, so an omitted `Status` reads as
> success.
> ⚠️ A **null or empty body is an NRE**, not a graceful failure.

Derived **2026-10-26** from build `20260323.14`. Closes the "not derived" row in
[roomconsumables-inventory-me](roomconsumables-inventory-me-wire-shape.md).

## Route

Facade **`RecNet.RoomConsumables.LDPVJWWJOCC`** **`0x9572B00`** (spans to `0x9572DA0`):

```
static RecRoom.Async.MPVTAJGPRUT`1<RecNet.RoomConsumableInventoryItemOperationResult>
    LDPVJWWJOCC(System.Guid roomConsumableId, System.Nullable`1<System.Guid> currentConcurrencyCode)
```

| what | value | evidence |
|---|---|---|
| path | `api/roomconsumables` + `{0}/v1/roomConsumable/{1}/consume` | literal **`0xFCD4110`**, `mxref` = exactly **2** refs, both in this method (`0x9572B93` init `lea`, `0x9572CB8` use `mov`); joined by `String.Format` at `0x9572CC2` |
| verb | **PUT** | `0x9572C95 mov rcx,[rax+0x20]` → `0x9572C99 mov rdi,[rcx+0x28]` — **`+0x28` = `Put`** |
| service | **28 = Econ** | `0x9572CE2 mov r8d, 0x1c` into the request `.ctor` at `0x9572CF1` |
| response | `RoomConsumableInventoryItemOperationResult` | the facade's generic return, `msig`-confirmed |

Note the casing: **`roomConsumable` camelCase**, like the `/room/{roomId}` list routes and *unlike* the
all-lowercase `roomconsumable` in the `/purchase/currency` and `/purchase/tokens` routes
([roomconsumables-purchase-currency](roomconsumables-purchase-currency-wire-shape.md)). The 2026
build genuinely ships both spellings; match them exactly.

## Request body — `RecNet.RoomConsumableConcurrencyCodes` (a compare-and-set)

The method allocates a body object and fills two fields before formatting the route:

```
0x9572c0d  movups xmm0, [rbx]            ; the Guid? param (16-byte Guid + 4-byte hasValue)
0x9572c13  movups [rsi+0x10], xmm0       ; -> CurrentConcurrencyCode
0x9572c17  mov    [rsi+0x20], eax
0x9572c33  call   System.Guid$$NewGuid   ; CLIENT-GENERATED
0x9572c3b  movups [rsi+0x24], xmm0       ; -> NewConcurrencyCode
0x9572d06  mov    rdx, rsi               ; body attached to the request
```

The layout pins the type unambiguously — **`RecNet.RoomConsumableConcurrencyCodes`** (typedef #23083)
is the only type with `Nullable<Guid>` at `0x10` and `Guid` at `0x24`:

| # | key | CLR | field |
|---|---|---|---|
| 1 | `CurrentConcurrencyCode` | **`Guid?`** | `<CurrentConcurrencyCode>k__BackingField` `0x10` |
| 2 | `NewConcurrencyCode` | **`Guid`** | `<NewConcurrencyCode>k__BackingField` `0x24` |

Formatter **`Utf8Json.Formatters.RecNet.ICYDRYWRQVR`** `.ctor 0x8E48590` (msig-confirmed), key run
`0x8E4873E`/`0x8E4876A`.

```json
{ "CurrentConcurrencyCode": "772888d0-db9c-46f0-8a29-1b4c98b60693", "NewConcurrencyCode": "…" }
```

➡️ **This is optimistic concurrency, and the client picks the next token.** The server should compare
`CurrentConcurrencyCode` against the stored code for `(roomConsumableId, accountId)`, and on a match
store **`NewConcurrencyCode`** as the new code and echo it back in `InventoryItem.ConcurrencyCode`.
On a mismatch, answer `Status: 32` (`ConcurrencyCodeMismatch`) — **and still send `InventoryItem`**,
see the trap below. `CurrentConcurrencyCode` is nullable, so a first-ever consume legitimately sends
`null`.

⚠️ **Do not confuse the body type with `RecNet.ConcurrencyCodePairDTO`**, which declares the *same two
key names* (formatter `UIOPHCOHOYL` `.ctor 0x9136950`) and shares all six key literals. The `mxref` on
`CurrentConcurrencyCode` returns both formatters; `msig` is what separates them.

## Response

```json
{ "Status": 0,
  "InventoryItem": {
    "RoomConsumableId": "772888d0-db9c-46f0-8a29-1b4c98b60693",
    "AccountId": 1,
    "Count": 2,
    "ConcurrencyCode": "<the NewConcurrencyCode the client just sent>",
    "ModifiedAt": "2026-10-26T00:00:00Z",
    "Consumable": { "RoomConsumableId": "…", "RoomId": 1162, "Name": "…", "Description": "…",
                    "ImageName": "…", "Price": 0, "PurchaseCurrencyId": null,
                    "ModifiedAt": "2026-10-26T00:00:00Z", "MaximumCountPerPurchase": 1,
                    "IsGiftable": false, "Visibility": 0 } } }
```

### `RecNet.RoomConsumableInventoryItemOperationResult` (typedef #23090) — 2 keys

Formatter **`Utf8Json.Formatters.RecNet.BHTAIQHOGFX`** `.ctor 0x8E591A0`, msig-confirmed
(`Serialize(JsonWriter, RecNet.RoomConsumableInventoryItemOperationResult, …)`).
`____stringByteKeys` is the trailing run `0x8E59323` → `0x8E5934F`:

| # | key | CLR | field off |
|---|---|---|---|
| 1 | `Status` | `RecNet.RoomConsumableResult` (int enum) | `0x10` |
| 2 | `InventoryItem` | `RecNet.RoomConsumableInventoryItem` | `0x18` |

**2 keys against 2 instance fields**, 1:1, and the first field sits at `0x10` — so **no inheritance
here**, unlike the `/purchase/*` responses whose derived-before-base ordering is the documented trap
in that note. Key order is declaration order: `Status` first.

**No post-deserialize hook** — `msig` shows only the four accessors plus `.ctor` on this type, and
likewise on `RoomConsumableInventoryItem`.

### Nested `RecNet.RoomConsumableInventoryItem` — 6 keys

Unchanged from [roomconsumables-inventory-me](roomconsumables-inventory-me-wire-shape.md):
`RoomConsumableId` (Guid), `AccountId` (int), `Count` (int), `ConcurrencyCode` (Guid),
`ModifiedAt` (DateTime), `Consumable` (the **11-key** `RecNet.RoomConsumable`).

`RoomConsumable` is 15 fields minus **4 statics** (`MIN_NAME_LENGTH`, `MAX_NAME_LENGTH`,
`MIN_DESCRIPTION_LENGTH`, `MAX_DESCRIPTION_LENGTH`, all at offset `0x0000`) = 11 wire keys, with
`PurchaseCurrencyId` a **`Guid?`** at `0x48`.

### Envelope tier — **bare**

Every `MPVTAJGPRUT<T>`-returning route on this facade carries one "Unable to …" literal, and it is a
**`RecRoom.Async` failure message, not a `friendlyActionDescription`**:

| method | literal |
|---|---|
| `LDPVJWWJOCC` (this route) | `'Unable to consume consumable'` `0x9572B9F` |
| `QGVGHSTNZZV` (delete) | `'Unable to delete consumable'` `0x9573038` |
| `NICGJJXYEZM` (concurrencyCode) | `'Unable to get concurrency code for player'` `0x9572E2E` |

The pattern across three siblings is what settles it — an envelope description names the *action*
("change subroom permissions"), not the *failure*. Consistent with the rest of this facade being
documented bare.

⚠️ **Not pinned**: the send helper's own name. The route tail-calls a generic-shared helper at
`0x9572D6F` that `methods.pkl` resolves only to a wrong nearest-match
(`System.Text.Json.Utf8JsonReader$$get_TokenType+0x1b570`), so the tier here rests on the
sibling-literal pattern plus the facade's existing notes, not on reading the helper signature.

## 🔴 The trap: `InventoryItem` is resolved BEFORE `Status`, so a null one discards the failure

This is the whole reason to read this note. The result flows
`RoomConsumablesManager.LDPVJWWJOCC` `0xFB5990` → continuation
**`MEFUQXVKMNJ(RoomConsumableInventoryItemOperationResult)` `0xFB5C40`**, which begins:

```
0xfb5c92  call  RoomConsumablesManager$$FSRZFLYBWSN   ; (result) -> .ALAFJEDKZCD
0xfb5c9a  test  rax, rax
0xfb5c9d  je    0xfb5d35                              ; -> plain return, Status NEVER read
0xfb5ca3  test  rbx, rbx                              ; result itself
0xfb5ca6  je    0xfb5d42                              ; -> 0xc403a0  NRE THROW
0xfb5cac  cmp   dword [rbx+0x10], 2                   ; Status == ConsumableUnderModeration
0xfb5cb2  cmp   dword [rbx+0x10], 1                   ;        == FeatureDisabled
0xfb5cb8  cmp   dword [rbx+0x10], 0x21                ;        == PlayerDoesNotOwnConsumable (33)
0xfb5cbe  cmp   dword [rbx+0x10], 4                   ;        == RoomConsumableNotFound
0xfb5cc2  jne   0xfb5d35                              ; anything else -> return
0xfb5d30  call  RoomConsumablesManager$$KCHITLCSWXS   ; the deactivate path
```

and the gate it calls first, **`FSRZFLYBWSN` `0xFB3770`**, is where the two null decisions happen:

```
0xfb37b1  test rbx, rbx            ; result == null
0xfb37b4  je   0xfb3854            ; -> 0xc403a0   NullReferenceException
0xfb37ba  cmp  qword [rbx+0x18], 0 ; result.InventoryItem == null
0xfb37bf  je   0xfb3847            ; -> xor eax,eax; ret   RETURNS NULL, no log, no error
0xfb37d2  mov  rdx, [rbx+0x18]     ; otherwise look the item up in the manager's table
0xfb37de  call XJFOINZDIYK$$AYNAQSXARIG
```

So the two failure modes are:

| response | what the client does |
|---|---|
| body `null` / empty / `204` | **`NullReferenceException`** at `0xFB3854` |
| `{"Status": 33}` with **no `InventoryItem`** | `FSRZFLYBWSN` returns null → `MEFUQXVKMNJ` returns at `0xFB5D35` → **`Status` is never examined**. No log, no toast, no deactivation. |
| `{"Status": 33, "InventoryItem": {…}}` | `KCHITLCSWXS` runs and the consumable is deactivated |

➡️ **Always send `InventoryItem`, including on every failure.** Serve the player's *current* row —
unchanged `Count` and the **old** `ConcurrencyCode` when the operation was refused. Returning
`Status` alone is the silent-failure shape: the player's consumable stays live in their hand and the
only symptom is that nothing happens.

Only **four** statuses do anything client-side:

| value | name | meaning here |
|---|---|---|
| 1 | `FeatureDisabled` | deactivate |
| 2 | `ConsumableUnderModeration` | deactivate |
| 4 | `RoomConsumableNotFound` | deactivate |
| 33 | `PlayerDoesNotOwnConsumable` | deactivate |

Every other value — **including `0 Success`** — falls through `0xFB5CC2` and triggers no handling in
this continuation. So a rejection you want the player to *see* must use one of those four;
`ConcurrencyCodeMismatch` (32) and the rest are inert on this path.

### `Status` omitted reads as success

`RecNet.RoomConsumableResult` (typedef #23098, `int`) has **55 members, `Unknown = -1` and
`Success = 0`**. Utf8Json gives an absent key the CLR default **`0`**, so **omitting `Status` claims
the consume succeeded.** Always emit it explicitly. Values relevant to this route:

| val | name | val | name |
|---|---|---|---|
| -1 | `Unknown` | 32 | `ConcurrencyCodeMismatch` |
| 0 | **`Success`** | 33 | `PlayerDoesNotOwnConsumable` |
| 1 | `FeatureDisabled` | 34 | `OwnershipLimitExceeded` |
| 2 | `ConsumableUnderModeration` | 36 | `RoomNotFound` |
| 3 | `RoomConsumableIdMismatch` | 37 | `RoomUnderModeration` |
| 4 | `RoomConsumableNotFound` | 6 | `AccountIdInvalid` |
| 7 | `PlayerDoesntHavePermission` | 11 | `PlayerIsJuniorAccount` |
| 12 | `PlayerUnderModeration` | 14 | `RoomIdMismatch` |

Full 55-member table is in
[roomconsumables-purchase-currency](roomconsumables-purchase-currency-wire-shape.md).

## Related

Siblings on the same facade, from the table in
[roomconsumables-inventory-me](roomconsumables-inventory-me-wire-shape.md) — still **not derived**:
`DNFZQDRNSGQ`/`HETWSYTAWSA` (create/update → `RoomConsumableOperationResult`), `QGVGHSTNZZV` (delete →
`RoomConsumableResult`, route `{0}/v1/roomConsumable/{1}` `0xFCD3DC0`), `BKHHIYEPBWQ`
(`…/{id}/isOwned` → `bool`), `NICGJJXYEZM` (`…/{id}/player/{accountId}/concurrencyCode` → `Guid?`),
`QOGFSFOQKUZ` (`…/awardBulk` → a **map** `Dictionary<Guid, RoomConsumableInventoryItemOperationResult>`
keyed by Guid, body `Dictionary<Guid, AwardRoomConsumableRequest>` where
`AwardRoomConsumableRequest` = `{Quantity: int, ConcurrencyCodes: RoomConsumableConcurrencyCodes}`).

`awardBulk` reuses **this note's** element type as its map *value*, so the `InventoryItem`-before-
`Status` trap above likely applies per entry there too — **unverified**, the award path was not read.
