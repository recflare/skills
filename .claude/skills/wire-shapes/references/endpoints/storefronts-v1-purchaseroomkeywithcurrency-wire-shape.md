# Storefronts v1 PurchaseRoomKeyWithCurrency wire shape

> POST api/storefronts/v1/PurchaseRoomKeyWithCurrency (svc 28 Econ) sends 3 FORM fields and returns the UNOBFUSCATED, BARE RoomKeyPurchaseWithCurrencyResponseDTO = {Balance, RoomKeyResponse}. `Balance` is an OBJECT (the 4-key room-currency balance) that itself contains a numeric `Balance` — and the key order is the mirror image of buyRoomKey's.

Derived **2026-10-01** from build `20250718.01`.
Pairs with [storefronts-v1-buyroomkey](storefronts-v1-buyroomkey-wire-shape.md) (the token-currency variant) and reuses
`.PDBNFODGBLL` from [roomcurrencies-v2-purchase](roomcurrencies-v2-purchase-wire-shape.md) and `.AMNEJJIFIBM` from
[roomkeys-v1-create](roomkeys-v1-create-wire-shape.md).

`POST https://econ.<host>/api/storefronts/v1/PurchaseRoomKeyWithCurrency` — service **28 = Econ**
(`mov dword ptr [rdi+0x18], 0x1c` at `0x7D8B912`), verb **POST** (`HttpMethod` statics `[rcx+0x20]` at
`0x7D8B8D1`). Whole-route literal, slot `0xD152C40`. Note the route is **PascalCase in the path**.

Client entry **`AKDHOHEPFBH.LBMFNJLJHJM`** `0x7D8B7A0` — same facade as `buyRoomKey`
(`CEEPAGMBONL` `0x7D86C00`).

## Request — 3 form fields

Three `MGPBDIAGCFD.ELHKHFJEHLM` calls. The verb is POST, so this is an
**`application/x-www-form-urlencoded` body**, *not* a query string — unlike `buyRoomKey`, which is a
GET with the same first two params in the URL
([elhkhfjehlm-verb-dependent-params](../conventions/elhkhfjehlm-verb-dependent-params.md)):

| # | field | RVA of the add |
|---|---|---|
| 1 | `RoomKeyId` | `0x7D8B94B` |
| 2 | `RequestedPrice` | `0x7D8B982` |
| 3 | `RequestedPurchaseCurrencyId` | `0x7D8B9BD` |

The third field is what distinguishes this route: the purchase is paid in a **room currency**
identified by Guid, rather than the global token balance.

## Response — BARE object, no envelope

`MGPBDIAGCFD.HPBKMCLEANE<T>` (response required), generic inst **#1376** =
**`.RoomKeyPurchaseWithCurrencyResponseDTO`** (typedef #22726) — **unobfuscated**, as are both of its
property names. No envelope. Formatter `NBLDLHHNPNM` `.ctor 0x769D9E0`, key run `0x769DC1F` /
`0x769DC76` — 2 keys, 1:1 with the 2 fields:

| # | key | CLR | off |
|---|---|---|---|
| 1 | `Balance` | **`.PDBNFODGBLL`** (an object) | 0x10 |
| 2 | `RoomKeyResponse` | `.AMNEJJIFIBM` | 0x18 |

```json
{ "Balance": { "AccountId": 205,
               "CurrencyId": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
               "Balance": 500,
               "ModifiedAt": "2026-10-01T00:00:00Z" },
  "RoomKeyResponse": {
    "Status": 0,
    "RoomKey": { "RoomKeyId": 43, "ReplicationId": "0f8c...", "RoomId": 12, "Name": "VIP Key",
                 "Description": "...", "Price": 250, "PurchaseCurrencyId": "3fa85f64-...",
                 "CreatedAt": "2026-01-01T00:00:00Z", "ImageName": null, "Type": 0 } } }
```

`{}` or an empty body throws `IONCMJIACFI`.

⚠️ **The outer `Balance` is an OBJECT, and it contains a numeric `Balance`.** Emitting
`"Balance": 500` at the top level is the obvious mistake here — it will not deserialize into
`.PDBNFODGBLL`. The nested 4 keys are `AccountId` (int), `CurrencyId` (`System.Guid`), `Balance`
(long), `ModifiedAt` (DateTime); see [roomcurrencies-v2-purchase](roomcurrencies-v2-purchase-wire-shape.md) for the formatter
(`PLLOODIHMEP` `0x7E89050`).

`RoomKeyResponse` is `{Status, RoomKey}` with `Status` the `RecRoom.DataLayer.RoomKeyResult` enum —
full member list on [roomkeys-v1-create](roomkeys-v1-create-wire-shape.md), and the **`Success == 0`** trap applies, so an
omitted `Status` reads as success.

## ⚠️ Mirror image of `buyRoomKey` — do not share server code

The two room-key purchase routes look interchangeable and are not:

| | `buyRoomKey` | `PurchaseRoomKeyWithCurrency` |
|---|---|---|
| verb | **GET**, params in the query string | **POST**, params in a form body |
| params | `RoomKeyId`, `RequestedPrice` | `RoomKeyId`, `RequestedPrice`, **`RequestedPurchaseCurrencyId`** |
| response DTO | `RoomKeyPurchaseResponseDTO` | `RoomKeyPurchaseWithCurrencyResponseDTO` |
| key order | `RoomKeyResponse`, **`BalanceUpdateResponse`** | **`Balance`**, `RoomKeyResponse` |
| balance type | `EPLDBKEAKJF : BalanceResponseDTO` — token balance, 4 keys incl. `BalanceUpdates` and the `Platform` enum | `.PDBNFODGBLL` — **room-currency** balance, 4 keys incl. `CurrencyId` |

So the balance half is a **different type with different keys**, and the key order is reversed. The
`Platform`/`BalanceType` zero-value trap does **not** apply to this route — there is no `Platform` key
here at all.

## Validation

`RoomKeyPurchaseWithCurrencyResponseDTO.CPOBHIECLEN` **`0x7DC02F0`** is real but trivial and
null-tolerant:

```
if (this.RoomKeyResponse != null) tail-jump to its hook   // which is the 0xA60520 no-op
return
```

`Balance` is **never validated**. `PDBNFODGBLL` and `AMNEJJIFIBM` both have the shared no-op hook, so
nothing in this tree throws on partial data. Send both objects fully populated anyway — consumers were
not traced.
