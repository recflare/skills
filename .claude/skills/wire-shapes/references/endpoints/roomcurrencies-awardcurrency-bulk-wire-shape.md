# Roomcurrencies awardcurrency bulk wire shape

> POST api/roomcurrencies/v1/awardCurrency/bulk (svc 28 Econ) takes a JSON ARRAY body and returns a BARE ARRAY of per-award results {AccountId, CurrencyId, Success, Error, Response}; when Success=true the nested Response is MANDATORY — a null one NREs in the balance-update consumer.

Derived **2026-09-14** from build `20250718.01` via [recflare-2025-metadata-carve](../../../il2cpp-analysis/references/recflare-2025-metadata-carve.md).
Sibling of [roomcurrencies-createcurrency-wire-shape](roomcurrencies-createcurrency-wire-shape.md) and
[roomcurrencies-purchaseoffersbatch-wire-shape](roomcurrencies-purchaseoffersbatch-wire-shape.md) on the same facade `APMOEDPLHMM`.

`POST https://econ.<host>/api/roomcurrencies/v1/awardCurrency/bulk` — service **28 = Econ**
(`mov r8d, 0x1c` at `0x7DA7170`), verb **POST** (`HttpMethod` statics `+0x20`, read at `0x7DA714B`).
Literal `0xD14C7A8`. Client entry
`APMOEDPLHMM.DFDEHGHMJFN(List<MGNCPLFLDOM> awards)` **`0x7DA7030`**.

## Request — a real JSON ARRAY body

Sent with **`MGPBDIAGCFD.ELKIBCPINAP`** (generic inst **14884** = `.MGNCPLFLDOM`), the
`IEnumerable<T>` overload — so this one is a genuine JSON body, **not** form fields
([elhkhfjehlm-verb-dependent-params](../conventions/elhkhfjehlm-verb-dependent-params.md) does not apply). Element `MGNCPLFLDOM`, formatter
`IJFJINIHEAM` `.ctor 0x76AEF30`, 4 keys 1:1 with its 4 fields:

```json
[ { "CurrencyId": "<guid>", "RecipientId": 220, "Amount": 100, "TransactionId": "<guid>" } ]
```

`RecipientId` is an **int** (account id); `Amount` is a **long**; `TransactionId` is a client-minted
`Guid` (idempotency key).

## Response — BARE ARRAY, no envelope

`HPBKMCLEANE<List<LIGIHFDPEEL>>` (generic inst **1018**). The extra
`DCEKGPHGICM.BBHOKCAHEAD<List<LIGIHFDPEEL>>(promise, logger, 'Award Currency Bulk')` in the chain is
only the **error-description annotator** — signature `KPIPLFECKNC<T> -> KPIPLFECKNC<T>`, T unchanged,
so it is *not* an envelope unwrapper (that is `DHFGOBPNOJB`, which maps `FFOENOGPGNH<T> -> T`).

`.LIGIHFDPEEL` — formatter `JEFDEMLJBCI` `.ctor 0x76B0560`, **5 keys**:

| # | key | CLR | offset |
|---|---|---|---|
| 1 | `AccountId` | int | 0x10 |
| 2 | `CurrencyId` | `System.Guid` | 0x14 |
| 3 | `Success` | bool | 0x24 |
| 4 | `Error` | string | 0x28 |
| 5 | `Response` | `.LCNEPHPLOAB` | 0x30 |

`.LCNEPHPLOAB` — formatter `GHNCCNOMLNO` `.ctor 0x7E7C410`, **5 keys**:

| # | key | CLR | offset |
|---|---|---|---|
| 1 | `AccountId` | int | 0x10 |
| 2 | `CurrencyId` | `System.Guid` | 0x14 |
| 3 | `Balance` | long | 0x28 |
| 4 | `AmountAwarded` | long | 0x30 |
| 5 | `AwardedAt` | DateTime | 0x38 |

```json
[ { "AccountId": 220, "CurrencyId": "<guid>", "Success": true, "Error": null,
    "Response": { "AccountId": 220, "CurrencyId": "<guid>",
                  "Balance": 1100, "AmountAwarded": 100,
                  "AwardedAt": "2026-09-14T12:00:00Z" } } ]
```

Note this is a **per-item** `Success`/`Error` pair inside a bare array — not the RecNet envelope.
(The backing-field names `MGEMHOPKHMI` / `PEHOIKIFKKI` are the same ones `JFNAKFCGDAO` uses for
`Success`/`Error`, but the type is unrelated.)

## `Response` is mandatory when `Success` is true

No deserialize-time validation exists — all three DTO hooks are no-ops (`MGNCPLFLDOM` and
`LCNEPHPLOAB` on `0xA60520`; `LIGIHFDPEEL` on its own `nop; ret` at `0xFEA4F0`). The requirement is
in the consumer.

`<>c.KICEEIOMIIF(List<LIGIHFDPEEL>)` `0x7DC1830` tail-jumps to
**`APMOEDPLHMM.KJJNHBABAOA`** `0x7DA7890`:

```
if (results == null) return;                 // quiet, 0x7DA7908
foreach (r in results) {
    if (r == null)        -> NRE (0x7DA7A4C)
    if (!r.Success)       -> continue        // 0x7DA797B; Error is NEVER read
    acct = r.AccountId; cur = r.CurrencyId
    resp = r.Response;  if (resp == null) -> NRE (0x7DA7A47)   // ⚠️
    raise balance-changed { acct, cur, resp.Balance, resp.AmountAwarded }
      via APMOEDPLHMM.EKLDPKKNDKL 0x7DA7340
}
```

So:
- **null list → quiet return** (nothing updates, no throw).
- **a null element → NRE.**
- **`Success: false` → the whole entry is skipped and `Error` is never surfaced**; use it to refuse
  individual awards, but don't expect the player to see the reason.
- **`Success: true` with a null/missing `Response` → NRE**, and the balance never refreshes.
- `Response.AwardedAt` is deserialised but unused on this path — only `Balance` and `AmountAwarded`
  are read. `Response.AccountId`/`CurrencyId` are also ignored (the outer ones win), so they need
  not agree, though echoing them is harmless.

`[]` is a valid response. A `{}` body fails as [ioncmjiacfi-malformed-response](../conventions/ioncmjiacfi-malformed-response.md) since T is a
`List`.
