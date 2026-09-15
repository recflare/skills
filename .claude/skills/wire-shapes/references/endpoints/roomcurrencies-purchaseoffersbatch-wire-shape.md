# Roomcurrencies purchaseoffersbatch wire shape

> getPurchaseOffersBatch (svc 28 Econ) is a POST with `ids` as a FORM field — not a GET query string — and returns a BARE ARRAY of {CurrencyId, PurchaseOffers:[7-key offer]}; the list hook is non-throwing.

Derived **2026-09-14** from build `20250718.01` via [recflare-2025-metadata-carve](../../../il2cpp-analysis/references/recflare-2025-metadata-carve.md).
Sibling of [roomcurrencies-createcurrency-wire-shape](roomcurrencies-createcurrency-wire-shape.md).

## The verb is CONDITIONAL on the id count — <100 = GET

`BLEKKMENCDA.MoveNext` **`0x7DAA5A0`** (fields unobfuscated: `IReadOnlyList<System.Guid>
currencyIds`, builder `AsyncTaskMethodBuilder<List<CKDHKOMKGFL>>`):

```
0x7DAA688  r8  = currencyIds            ; null -> NRE
0x7DAA69E  edi = currencyIds.Count      ; interface get_Count
0x7DAA6DD  cmp edi, 0x64                ; 100
0x7DAA6E0  jge  -> 0x7DAA735            ; >=100 : rsi = statics[+0x20] = post_method
           else -> 0x7DAA721            ; < 100 : rsi = statics[+0x08] = get_method
0x7DAA7AE  mov r8d, 0x1c                ; service 28 = Econ
```

Both verb loads are in the same method; an earlier pass that read only the second one concluded
"POST" and was **wrong for the normal case**. Offsets checked against the metadata field order
`delete 0x00 / get 0x08 / head 0x10 / options 0x18 / post 0x20 / put 0x28 / trace 0x30`.

`ids` is added with the 2-arg `ELHKHFJEHLM(string, IReadOnlyList<T>)` (generic inst **322** =
`System.Guid`), so by [elhkhfjehlm-verb-dependent-params](../conventions/elhkhfjehlm-verb-dependent-params.md) it follows the verb:

```
GET  /api/roomcurrencies/v1/getPurchaseOffersBatch?ids=<guid>&ids=<guid>     (<100 ids)
POST /api/roomcurrencies/v1/getPurchaseOffersBatch                           (>=100 ids)
     Content-Type: application/x-www-form-urlencoded
     ids=<guid>&ids=<guid>…
```

**A server must handle both**, keyed off the verb, not the path.

`MGPBDIAGCFD.HHKCCEIBOOH()` `0x7D9C2C0` is also called on the builder; it only writes the
`Nullable<int>` at `+0x58` from a config value — unrelated to query-vs-body.

## Response — BARE ARRAY, no envelope

`HPBKMCLEANE<List<CKDHKOMKGFL>>` (generic inst **2708**).

`.CKDHKOMKGFL` — formatter `PIEEPAEDDHO` `.ctor 0x76BD890`, **2 keys**:

| key | CLR | offset |
|---|---|---|
| `CurrencyId` | `System.Guid` | 0x10 |
| `PurchaseOffers` | `List<ODEGNHKCDGA>` | 0x20 |

`.ODEGNHKCDGA` — formatter `FNOIOCKEIJF` `.ctor 0x7E7AF20`, **7 keys**, 1:1 with its 7 fields:

| # | key | CLR | offset |
|---|---|---|---|
| 1 | `CurrencyPurchaseOfferId` | `System.Guid` | 0x10 |
| 2 | `CurrencyId` | `System.Guid` | 0x20 |
| 3 | `Order` | int | 0x30 |
| 4 | `Name` | string | 0x38 |
| 5 | `CurrencyAmount` | long | 0x40 |
| 6 | `Price` | long | 0x48 |
| 7 | `ModifiedAt` | DateTime | 0x50 |

```json
[ { "CurrencyId": "b9f41a7c-32f1-4456-b84f-fdb94b240955",
    "PurchaseOffers": [
      { "CurrencyPurchaseOfferId": "…", "CurrencyId": "b9f41a7c-…",
        "Order": 0, "Name": "Small pile", "CurrencyAmount": 100,
        "Price": 25, "ModifiedAt": "2026-09-14T12:00:00Z" } ] } ]
```

## Nothing throws

`CKDHKOMKGFL.CPOBHIECLEN` `0x7DABD00` is a 3-instruction tail-jump: it takes `PurchaseOffers`
(`this+0x20`) into the list validator `EADLCOCJAGD.IANBCAFGFNL`, which **returns false on null rather
than throwing** ([platformnotifications-wire-shapes](platformnotifications-wire-shapes.md)). `ODEGNHKCDGA` has no hook of its own.
So `"PurchaseOffers": null` and `[]` are both safe, and `[]` is the right answer for an id with no
offers. The only hard failure is a `{}` body — T is a `List`, so that is
[ioncmjiacfi-malformed-response](../conventions/ioncmjiacfi-malformed-response.md).

## ⚠️ Results feed a KEYED BATCH CACHE — CurrencyId must match exactly

`APMOEDPLHMM..cctor` `0x7DA8D40` registers the route method
`APMOEDPLHMM.PPKLIPKHFBL(IReadOnlyList<Guid>, CancellationToken)` `0x7DA8C30` as the **batch loader**
of an **`.IMAGJAIKIPF\`2<System.Guid, .CKDHKOMKGFL>`** keyed cache, with the key selector
`Func<CKDHKOMKGFL, Guid>` = `<>c.JADCIPCKNNL(set) -> set.CurrencyId`.

That type holds `Dictionary<TKey, TaskCompletionSource<TValue>>` pending maps
(`LOPNMCNEBKA`, `MLMCNPLLJNA`) and exposes `LMKONLJOAEP(key, …) -> Task<T>` /
`LMKONLJOAEP(IEnumerable<key>, …) -> Task<List<T>>`. So each requested id has a pending TCS that is
satisfied by finding an element **whose `CurrencyId` equals that id**.

⇒ **Every element's `CurrencyId` must be the exact guid that was requested**, and an id that is
absent from the array has nothing to resolve its TCS. Returning an element with an empty
`PurchaseOffers` list is therefore strictly safer than omitting the id.

⚠️ **Unverified:** whether a missing key completes with `default` or leaves the task pending
(a hang). The completion logic lives in `IPEEBFBGDKD` / `AALJCHFPKPC`, which are **shared generic
bodies not indexed by `methods.pkl`** — same tooling gap as [dissonance-named-message-framing](../../../rr-voice-server/references/dissonance-named-message-framing.md).
If a stub of this route "hangs" rather than errors, that is the first thing to test.
