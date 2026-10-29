# `GET api/roomconsumables/v1/roomConsumable/room/{roomId}/me`

> **GET** (svc **28 Econ**), **no params, no body** → a **bare JSON array** of the 6-key
> `RecNet.RoomConsumableInventoryItem`, i.e. `List<RoomConsumableInventoryItem>`. No envelope.
> This is *the local player's owned counts* for one room — not the room's catalogue. The sibling
> without `/me` returns `List<RoomConsumable>` instead
> ([roomconsumables-by-room](roomconsumables-by-room-wire-shape.md)); **the two routes return
> different element types**, so do not share a handler.
> ⚠️ **Return `[]`, never `null`.** The send is the plain, non-nullable
> `ZWUODKCINOA<List<RoomConsumableInventoryItem>>`, so a `null` body **resolves successfully** and
> the list is then captured and enumerated with no null guard.
> ⚠️ Note the casing: `roomConsumable` is **camelCase** here, unlike the `/purchase/*` routes which
> use all-lowercase `roomconsumable`.

Derived **2026-10-22** from build `20260323.14`.

## Route

Facade **`RecNet.RoomConsumables.CWSWHCSFHUG(long roomId, CancellationToken)`** **`0x95722A0`** →
`Task<List<RecNet.RoomConsumableInventoryItem>>`. The compiler-generated state machine name survives
obfuscation and gives the original method name: **`<GetConsumableInventoryForRoomServiceCall>d__19`**
`0x957C0F0` (nested typedef #23102 under `RecNet.RoomConsumables` #23104).

| what | value | evidence |
|---|---|---|
| path | `"api/roomconsumables"` + `"{0}/v1/roomConsumable/room/{1}/me"` | literals **`0xFCD3A70`** (2 refs, both here) + the `api/roomconsumables` prefix; `String.Format` at `0x957C25A` |
| service | **28 = Econ** | `mov r8d, 0x1C` at `0x957C279`, into the request `.ctor` `0x8BBF9E0` at `0x957C285` |
| verb | **GET** | `[klass+0x20]` → **`[statics+0x08]`** at `0x957C21E`–`0x957C222` |
| params | **none** | only 4 literals in the method: the two path pieces, twice each |
| body | **none** | no `FZNGWUAGAIN`/`YHPVSAVMRFS` call |
| response | `List<RoomConsumableInventoryItem>` | `<>t__builder` is `AsyncTaskMethodBuilder<List<RecNet.RoomConsumableInventoryItem>>` |

⚠️ **The path is assembled from two literals** — grep `roomConsumable/room` or the
`{0}/v1/...` fragment, not the full URL.

`{roomId}` is the only variable; **`me` is literal** — the account comes from the bearer token.

### It is client-cached per roomId

The promise-style entry point is
**`RecNet.RoomConsumables.WOPATOEZJNN(long roomId)`** `0x9573510` →
`MPVTAJGPRUT<IReadOnlyList<RoomConsumableInventoryItem>>`, which routes through a memoising helper
(`0x67B88B0`, keyed on `roomId`) before tail-jumping to the `Task`→promise adapter. `CWSWHCSFHUG`
has **0 direct call sites** — its stub is inlined into that wrapper.

➡️ **Relaunch (or change room) between server-side attempts**, as with `club/home/me` and
`roomkeys/v1/mine`. The NRE at `0x95735A7` inside `WOPATOEZJNN` guards the *static cache service*
being null — a client-side init failure, **not** server-driven.

Call chain into the manager:
`RoomConsumablesManager` closure `UBKCIYMGHYX.JOVLJLBTDMV` `0xFE1440` (takes a `RoomDTO`, skips
`IsRoomV2` rooms at `0xFE14D3`) → `WOPATOEZJNN` → continuation `UBKCIYMGHYX.JOQEMEHVUBM` `0xFE1330`
→ **`RoomConsumablesManager.BLYPTTUMSQG(IEnumerable<RoomConsumableInventoryItem>)`** `0xFB1F50`.

## Response

```json
[
  {
    "RoomConsumableId": "772888d0-db9c-46f0-8a29-1b4c98b60693",
    "AccountId": 1,
    "Count": 3,
    "ConcurrencyCode": "9f1d4c22-7a08-4e51-b6c3-2d5e8a71f004",
    "ModifiedAt": "2026-10-22T00:00:00Z",
    "Consumable": {
      "RoomConsumableId": "772888d0-db9c-46f0-8a29-1b4c98b60693",
      "RoomId": 1162,
      "Name": "Health Potion",
      "Description": "",
      "ImageName": "",
      "Price": 100,
      "PurchaseCurrencyId": null,
      "ModifiedAt": "2026-10-22T00:00:00Z",
      "MaximumCountPerPurchase": 10,
      "IsGiftable": false,
      "Visibility": 0
    }
  }
]
```

`[]` is the correct "owns nothing in this room" answer.

### `RecNet.RoomConsumableInventoryItem` (typedef #23089) — 6 keys

Formatter **`Utf8Json.Formatters.RecNet.TULDIQEAQLB`** `.ctor` **`0x8E68410`** (confirmed by `msig`),
`____stringByteKeys` `0x8E6878E`…`0x8E6885A`, declaration order, **no renames**:

| # | key | CLR | off | notes |
|---|---|---|---|---|
| 1 | `RoomConsumableId` | `System.Guid` | 0x10 | |
| 2 | `AccountId` | int | 0x20 | |
| 3 | `Count` | int | 0x24 | the owned count |
| 4 | `ConcurrencyCode` | `System.Guid` | 0x28 | the client feeds this back as `CurrentConcurrencyCode` on a purchase — see [roomconsumables-purchase-currency](roomconsumables-purchase-currency-wire-shape.md) |
| 5 | `ModifiedAt` | `DateTime` | 0x38 | |
| 6 | `Consumable` | `RecNet.RoomConsumable` | 0x40 | **nested object, the full definition** |

This is the **same element type** that the two `/purchase/*` routes return inside
`OperationResult.InventoryItem`, so one serializer covers all three.

### Nested `Consumable` — `RecNet.RoomConsumable` (typedef #23082) — **11** keys

Formatter **`Utf8Json.Formatters.RecNet.PWYCNUHPKDA`** `.ctor` **`0x8E642A0`**, keys
`0x8E64874`…`0x8E64A08`, declaration order, no renames:

| # | key | CLR | off |
|---|---|---|---|
| 1 | `RoomConsumableId` | `Guid` | 0x10 |
| 2 | `RoomId` | long | 0x20 |
| 3 | `Name` | string | 0x28 |
| 4 | `Description` | string | 0x30 |
| 5 | `ImageName` | string | 0x38 |
| 6 | `Price` | **long** | 0x40 |
| 7 | `PurchaseCurrencyId` | `Guid?` | 0x48 |
| 8 | `ModifiedAt` | `DateTime` | 0x60 |
| 9 | `MaximumCountPerPurchase` | int | 0x68 |
| 10 | **`IsGiftable`** | bool | 0x6C |
| 11 | **`Visibility`** | `RecRoom.DataLayer.UgcPurchasableItemVisibility` | 0x70 |

⚠️ **11 keys on 2026, not the 9** the 2025 note records for `.JHLGLLIJGKM`
([roomconsumables-by-room](roomconsumables-by-room-wire-shape.md)) — 2026 added `IsGiftable` and
`Visibility`, the same pair it added to `RecNet.RoomKey`
([roomkeys-v1-mine](roomkeys-v1-mine-wire-shape.md)).

`Visibility` is **numeric**: `AlwaysVisible = 0`, `HiddenInWatchStore = 1` — no member name exists
as a string literal, so there is no by-name formatter.

The four `MIN_NAME_LENGTH` / `MAX_NAME_LENGTH` / `MIN_DESCRIPTION_LENGTH` /
`MAX_DESCRIPTION_LENGTH` entries on this type are **static consts** and carry no wire key — that is
why `fields2025.py` shows 15 fields against 11 keys.

## No validation; `null` is not handled

Neither `RoomConsumableInventoryItem` nor `RoomConsumable` declares an `EMSIIQRWASQ` (sync) or
`IULRMJBAHPG` (async) post-deserialize hook — checked individually. **Zero** validation or
normalization: a partial element parses and every omitted number becomes `0` (including `Count`).

The send at `0x957C2A1` is the plain **`ZWUODKCINOA<List<RoomConsumableInventoryItem>>(ct)`**
(`rdx` = the state machine's `cancellationToken` at `+0x28`), **not** `LIRIDCJIGGA(bool, ct)` — so
there is no allow-null flag and nothing rejects a null value
([2026-send-helper-tiers](../conventions/2026-send-helper-tiers.md)). A `null` body therefore
resolves the promise **successfully**, and `JOQEMEHVUBM` `0xFE1330` passes the value straight to
`BLYPTTUMSQG` `0xFB1F50`, which captures it into a closure at `[closure+0x10]` (`0xFB2072`)
**without a null check** and enumerates it from there.

⚠️ **Not pinned**: the exact instruction that throws on the null enumeration — the consumption
happens inside generic-shared LINQ reached through the `XJFOINZDIYK` nested closure, which
`callxref` cannot follow (the skill's standing caveat). `BLYPTTUMSQG` does contain **7** separate
`0xC403A0` NRE throw sites. What *is* established: nothing on the path handles a null list, and the
sibling `/room/{roomId}` route is already documented as NRE-ing on one.

➡️ **`200 []`**. Never `null`, never `{}` (which raises `IONCMJIACFI` "Malformed Response" since `T`
is a `List`), never 204.

## `RecNet.RoomConsumables` facade (17 methods) — the neighbouring routes

| facade | returns | route |
|---|---|---|
| `CWSWHCSFHUG(long, ct)` `0x95722A0` | `Task<List<RoomConsumableInventoryItem>>` | **this note** |
| `WOPATOEZJNN(long)` `0x9573510` | `MPVTAJGPRUT<IReadOnlyList<…>>` | cached wrapper over the above |
| `SPKXOJIQHMX(long, ct)` | `Task<List<RoomConsumable>>` | `…/roomConsumable/room/{roomId}` ([note](roomconsumables-by-room-wire-shape.md)) |
| `JLKJKBCJHLG(long)` | `MPVTAJGPRUT<IReadOnlyList<RoomConsumable>>` | cached wrapper over the above |
| `DNFZQDRNSGQ(...)` / `HETWSYTAWSA(...)` | `MPVTAJGPRUT<RoomConsumableOperationResult>` | create / update — **not derived** |
| `QGVGHSTNZZV(Guid)` | `MPVTAJGPRUT<RoomConsumableResult>` | delete — **not derived** |
| `LDPVJWWJOCC(Guid, Guid?)` | `MPVTAJGPRUT<RoomConsumableInventoryItemOperationResult>` | `…/{id}/consume` — ✅ **now derived**: [roomconsumables-consume](roomconsumables-consume-wire-shape.md) |
| `BKHHIYEPBWQ(Guid)` | `MPVTAJGPRUT<bool>` | `…/{id}/isOwned` — **not derived** |
| `NICGJJXYEZM(Guid, int)` | `MPVTAJGPRUT<Guid?>` | `…/{id}/player/{accountId}/concurrencyCode` — **not derived** |
| `QOGFSFOQKUZ(Dictionary<Guid, AwardRoomConsumableRequest>, ct)` | `Task<Dictionary<Guid, RoomConsumableInventoryItemOperationResult>>` | `…/awardBulk` — **not derived**; note the response is a **map**, not an array |
