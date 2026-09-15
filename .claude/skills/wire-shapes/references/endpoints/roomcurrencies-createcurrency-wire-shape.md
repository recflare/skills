# Roomcurrencies createcurrency wire shape

> POST api/roomcurrencies/v1/createCurrency (svc 28 Econ) sends 7 form fields and returns the ENVELOPED {Value: 11-key NKPAKKPNADD, Success, Error, error_id}; no validation hook, but Success=false rejects with Error and 'Failed to create currency'.

Derived **2026-09-14** from build `20250718.01` via [recflare-2025-metadata-carve](../../../il2cpp-analysis/references/recflare-2025-metadata-carve.md).

`POST https://econ.<host>/api/roomcurrencies/v1/createCurrency` — service **28 = Econ**
(`mov r8d, 0x1c` at `0x7DA662B`), verb **POST** (`HttpMethod` statics `+0x20`, read at `0x7DA6606`).
Literal `0xD14CB40`. Client entry
`APMOEDPLHMM.ALPDIBGHEGE(long roomId, string name, string description, long limit, byte shape,
int color, string imageName)` **`0x7DA6490`**.

## Request — 7 form fields, no JSON body

All added with `ELHKHFJEHLM`; POST ⇒ **`application/x-www-form-urlencoded` body**
([elhkhfjehlm-verb-dependent-params](../conventions/elhkhfjehlm-verb-dependent-params.md)). Emission order:

```
RoomId & Name & Description & Limit & Shape & Color & ImageName
```

**`CurrencyType` is NOT sent** — the server assigns it (expect `RoomCurrency 300`).

## Response — ENVELOPED

Send generic `HPBKMCLEANE<KGOJLHJNIOD<NKPAKKPNADD>>` (inst **14534**); a dedicated formatter exists
for that instantiation (`.LOLJEFHBAFF : IHCMHKGLBEA<KGOJLHJNIOD<NKPAKKPNADD>>`), confirming the
envelope is on the wire. The promise chain is
`MLJHEDNMIEE(…, 'Failed to create currency')` → **`DCEKGPHGICM.DHFGOBPNOJB<NKPAKKPNADD>`**
(inst **4028**), the generic envelope unwrapper
`KPIPLFECKNC<FFOENOGPGNH<T>> -> KPIPLFECKNC<T>` — so callers receive `Value`, not the envelope.

```json
{ "Value": { "CurrencyId": "0f8c…", "RoomId": 1162, "Name": "Coins",
             "Description": "…", "CurrencyType": 300, "Limit": 1000000,
             "Shape": 0, "Color": -1, "ImageName": null,
             "CreatedAt": "2026-09-14T12:00:00Z", "ModifiedAt": "2026-09-14T12:00:00Z" },
  "Success": true, "Error": null, "error_id": null }
```

`Value` = `.NKPAKKPNADD`, formatter `KJLMCONIIJK` `.ctor 0x7C18F20`, **11 keys, 1:1 with the 11
declared fields** (nothing `[IgnoreDataMember]`):

| # | key | CLR | offset |
|---|---|---|---|
| 1 | `CurrencyId` | `System.Guid` | 0x10 |
| 2 | `RoomId` | `long?` | 0x20 |
| 3 | `Name` | string | 0x30 |
| 4 | `Description` | string | 0x38 |
| 5 | `CurrencyType` | enum `PJBEJGJLLLM` | 0x40 |
| 6 | `Limit` | long | 0x48 |
| 7 | `Shape` | **byte** | 0x50 |
| 8 | `Color` | **int** | 0x54 |
| 9 | `ImageName` | string | 0x58 |
| 10 | `CreatedAt` | DateTime | 0x60 |
| 11 | `ModifiedAt` | DateTime | 0x68 |

`PJBEJGJLLLM` (same enum as [storefronts-v3-buyinvention-wire-shape](storefronts-v3-buyinvention-wire-shape.md) / [giftdropstore-v3-wire-shape](giftdropstore-v3-wire-shape.md)):
`Invalid 0`, `LaserTagTickets 1`, `RecCenterTokens 2`, `LostSkullsGold 100`, `DraculaSilver 101`,
`RecRoyale_Season1 200`, **`RoomCurrency 300`**, `RoomInventoryItem 301`, `ProgressionEvent 400`,
`RoomieCredits 500`.

## Failure behaviour

`NKPAKKPNADD.CPOBHIECLEN` is the `0xA60520` **no-op** — no per-field validation, every key omittable.

The envelope is the only gate. Read directly from the non-generic sibling's lambda
`<>c.FBKGHAJPODL` `0x7C75C20`: **null envelope → NRE**; **`Success == false` → the promise is
rejected with the `Error` string** (`JFNOOGODOOA.FPEGBJHGPDL`), which is where
`'Failed to create currency'` `0xD1670A0` surfaces. ⚠️ That lambda belongs to the *valueless*
overload; the `T = NKPAKKPNADD` generic instantiation is shared-generic code I did not isolate, so
treat "null `Value` with `Success: true`" as unverified — populate `Value` on success.

## Sibling routes on `APMOEDPLHMM`

`api/roomcurrencies/v1/currencies`, `/updateCurrency`, `/getBalance`, `/getAllBalances`,
`/awardCurrency/bulk`, `/createPurchaseOffer`, `/updatePurchaseOffer`, `/deletePurchaseOffer`,
`/getPurchaseOffersBatch`, and **`api/roomCurrencies/v2/purchase`** (note the capital C — a distinct
literal `0xD14A750`).
