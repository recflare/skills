# RoomCurrencies v2 purchase wire shape

> POST api/roomCurrencies/v2/purchase (svc 28 Econ) sends 3 FORM fields and is ENVELOPED: {Value: {CurrencyBalanceResponse, TokenBalanceResponse}, Success, Error, error_id}. TokenBalanceResponse is the shared RecNet.BalanceResponseDTO, so the `Platform` zero-value trap applies here too.

Derived **2026-10-01** from build `20250718.01`.
`TokenBalanceResponse` is the **same `RecNet.BalanceResponseDTO`** that
[storefronts-v1-buyroomkey](storefronts-v1-buyroomkey-wire-shape.md) embeds — read that note for the `Platform` rename and its
enums. Siblings already derived: [roomcurrencies-awardcurrency-bulk](roomcurrencies-awardcurrency-bulk-wire-shape.md),
[roomcurrencies-createcurrency](roomcurrencies-createcurrency-wire-shape.md), [roomcurrencies-purchaseoffersbatch](roomcurrencies-purchaseoffersbatch-wire-shape.md).

`POST https://econ.<host>/api/roomCurrencies/v2/purchase` — service **28 = Econ**
(`mov dword ptr [rdi+0x18], 0x1c` at `0x7D8A072`), verb **POST** (`HttpMethod` statics `[rcx+0x20]` at
`0x7D8A031`). Whole-route literal, slot `0xD14A750`.

⚠️ **The path is mixed-case `roomCurrencies`** on this v2 route, while every v1 sibling literal is
lowercase `api/roomcurrencies/v1/...`. If the server routes case-sensitively, v2 needs its own entry.

Client entry **`AKDHOHEPFBH.HPDGNHPPENF`** `0x7D89ED0`. Error literal
`'Failed to purchase currency offer'`.

## Request — 3 form fields

Three `MGPBDIAGCFD.ELHKHFJEHLM` calls, in order. The verb is POST, so these are an
**`application/x-www-form-urlencoded` body**, not query params
([elhkhfjehlm-verb-dependent-params](../conventions/elhkhfjehlm-verb-dependent-params.md)):

| # | field | RVA of the add |
|---|---|---|
| 1 | `PurchaseOfferId` | `0x7D8A0AF` |
| 2 | `RequestedAmount` | `0x7D8A0E6` |
| 3 | `RequestedPrice` | `0x7D8A11D` |

All three PascalCase. `RequestedPrice`/`RequestedAmount` mirror the
`RequestedPriceDoesNotMatch (6)` / `RequestedAmountNotAllowed (7)` rejections on
[storefronts-v1-buyroomkey](storefronts-v1-buyroomkey-wire-shape.md) — this route is expected to validate them the same way, but
its own failure channel is the envelope's `Success`/`Error`, not an enum.

## Response — ENVELOPED, single value

`MGPBDIAGCFD.HPBKMCLEANE<T>` (response required), generic inst **#14528** =
**`KGOJLHJNIOD<LDLHPJHGONI>`** — the single-value envelope. Derived-first ordering puts `Value` before
the base members:

```json
{ "Value": {
    "CurrencyBalanceResponse": { "AccountId": 205,
                                 "CurrencyId": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
                                 "Balance": 500,
                                 "ModifiedAt": "2026-10-01T00:00:00Z" },
    "TokenBalanceResponse":    { "Balance": 1000, "CurrencyType": 2, "Platform": -1 } },
  "Success": true, "Error": null, "error_id": null }
```

`Success: false` or a null body raises **`LLCLDPPAGIJ`**, not `IONCMJIACFI`
([llcldppagij-envelope-failure-exception](../conventions/llcldppagij-envelope-failure-exception.md)).

### `Value` — `.LDLHPJHGONI`, 2 keys

Formatter `EDCAMJGFKEB` `.ctor 0x7E77CE0`, key run `0x7E77F5D` / `0x7E77FB4`:

| # | key | CLR | off |
|---|---|---|---|
| 1 | `CurrencyBalanceResponse` | `.PDBNFODGBLL` | 0x10 |
| 2 | `TokenBalanceResponse` | `RecNet.BalanceResponseDTO` | 0x18 |

Two *different* balance shapes in one response: the room's own currency, and the global token
balance.

### `CurrencyBalanceResponse` — `.PDBNFODGBLL`, 4 keys

Formatter **`PLLOODIHMEP`** `.ctor 0x7E89050`, key run `0x7E8944B`..`0x7E89535` — 4 keys, 1:1 with the
4 declared fields:

| # | key | CLR | off |
|---|---|---|---|
| 1 | `AccountId` | **int** | 0x10 |
| 2 | `CurrencyId` | **`System.Guid`** | 0x14 |
| 3 | `Balance` | long | 0x28 |
| 4 | `ModifiedAt` | DateTime | 0x30 |

`CurrencyId` is a bare Guid string, and the `0x14`→`0x28` gap is the 16-byte Guid plus alignment.
Formatter identified by key-literal intersection (`Balance` × `AccountId` leaves only two ctors) and
confirmed from `PLLOODIHMEP$$LABNBGADOBH` `0x7E88D60`, which references `.PDBNFODGBLL`'s TypeInfo at
`0x7E88FAF`.

### `TokenBalanceResponse` — the shared `RecNet.BalanceResponseDTO`

3 keys: `Balance` (long), `CurrencyType` (enum `PJBEJGJLLLM`), **`Platform`** (enum `GNCGGEBPLKF`,
field name `BalanceType`).

⚠️ **The `Platform` trap carries over.** Its `0` is `SteamPurchased`, so omitting the key tells the
client this balance was bought on Steam. Send **`-1` (`NonPurchasedDefault`)** for earned currency.
Full enums are in [storefronts-v1-buyroomkey](storefronts-v1-buyroomkey-wire-shape.md).

## Validation

| type | `CPOBHIECLEN` | behaviour |
|---|---|---|
| `LDLHPJHGONI` | **`0x7DB69B0`** real | `if (TokenBalanceResponse != null)` then tail-jump to its virtual hook; **`CurrencyBalanceResponse` is never validated** |
| `PDBNFODGBLL` | `0xA60520` no-op | — |
| `BalanceResponseDTO` | `0xA60520` no-op | — |

Null-tolerant throughout, so a missing `CurrencyBalanceResponse` or `TokenBalanceResponse` will not
throw at deserialize — but the envelope check still fires first, so `Success` must be `true` for the
client to reach `Value` at all.

## Siblings not yet derived

`api/roomcurrencies/v1/createPurchaseOffer`, `/deletePurchaseOffer`, `/updatePurchaseOffer`,
`/currencies`, `/getAllBalances`, `/getBalance`, `/updateCurrency`, and the bare `api/roomcurrencies`.
