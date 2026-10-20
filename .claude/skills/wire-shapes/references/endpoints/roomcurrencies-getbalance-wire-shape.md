# Roomcurrencies getBalance wire shape

> GET api/roomcurrencies/v1/getBalance?currencyId=&accountId= (svc 28 Econ) returns a BARE 4-key CurrencyBalance {AccountId, CurrencyId, Balance, ModifiedAt} — no envelope, no renames, no validation hook. Identical on 20250718.01 and 20260323.14.

Derived **2026-10-15** from both builds. Siblings on the same facade:
[roomcurrencies-createcurrency](roomcurrencies-createcurrency-wire-shape.md),
[roomcurrencies-awardcurrency-bulk](roomcurrencies-awardcurrency-bulk-wire-shape.md),
[roomcurrencies-purchaseoffersbatch](roomcurrencies-purchaseoffersbatch-wire-shape.md),
[roomcurrencies-v2-purchase](roomcurrencies-v2-purchase-wire-shape.md).

`GET https://econ.<host>/api/roomcurrencies/v1/getBalance?currencyId=<guid>&accountId=<int>`

| | 20260323.14 | 20250718.01 |
|---|---|---|
| facade | `RecNet.RoomCurrencies.ECUEIWFWFFY(Guid, int, bool)` `0x9574350` | `APMOEDPLHMM.LIOPOMENALJ(Guid, int, bool)` `0x7DA7A60` |
| returns | `MPVTAJGPRUT<RecNet.CurrencyBalance>` | `KPIPLFECKNC<PDBNFODGBLL>` |
| literal | `0xFC6A3B0` | `0xD14DD30` |
| service | `mov r8d, 0x1c` (28 Econ) at `0x95744C0` | `0x1c` at the `AKJEAMCCEOH..ctor` site `0x7DA7BB3` |
| verb | `HttpMethod` statics `+0x08` = **GET** (`0x95744A9`) | GET |
| send | `RGBOOBRDHEB.ZWUODKCINOA<T>` (plain, not the allow-null `LIRIDCJIGGA`) | `MGPBDIAGCFD.HPBKMCLEANE<T>` (response required) |
| formatter | `Utf8Json.Formatters.RecNet.MXOEHTIKACB` `.ctor 0x924C880` | `PLLOODIHMEP` `.ctor 0x7E89050` |

## Request

Two params via `NJPEKLKCVCG` (2026) / `ELHKHFJEHLM` (2025), in this order: `currencyId` (Guid),
`accountId` (int). The verb is GET, so they go in the **query string**
([elhkhfjehlm-verb-dependent-params](../conventions/elhkhfjehlm-verb-dependent-params.md)). No body.

The facade's `bool` third argument is passed to `ORUUDATDRUN` (the response-cache setter, 2026), so
it controls client-side caching. Nothing about it reaches the server.

## Response: bare object, no envelope

2026 chain: `ZWUODKCINOA<T>` → `Task<T>` → `SAXZOKINUQZ.CTZMMSFIPBH(Task<T>) → MPVTAJGPRUT<T>` →
`KGLKSSUUEOH.JCYQMVCDGYK(MPVTAJGPRUT<T>, Log, string) → MPVTAJGPRUT<T>`. That last step only
annotates the error ('Failed to get balance for player'), so T = `CurrencyBalance` and nothing unwraps
it. 2025: `HPBKMCLEANE<T>` → `DCEKGPHGICM.MLJHEDNMIEE` (annotator), with no `DHFGOBPNOJB` unwrap.

`RecNet.CurrencyBalance`: 4 fields, 4 keys, no `[DataMember]` renames:

| # | key | CLR |
|---|---|---|
| 1 | `AccountId` | int |
| 2 | `CurrencyId` | `System.Guid` |
| 3 | `Balance` | long |
| 4 | `ModifiedAt` | DateTime |

```json
{ "AccountId": 2, "CurrencyId": "71a9abea-cb3f-485d-b5d9-8888866debff",
  "Balance": 0, "ModifiedAt": "2026-10-15T00:00:00Z" }
```

The type declares only getters, setters and two ctors, so it has no post-deserialize hook. Any
omitted key deserializes to its default. This is the same DTO as `CurrencyBalanceResponse` inside
[roomcurrencies-v2-purchase](roomcurrencies-v2-purchase-wire-shape.md)'s `Value`.

For a player who holds none of the currency, return a real object with `Balance: 0`. Both builds use
the response-required sender, and this note does not establish that a `null` body is accepted. A
`[]` or envelope body will not deserialize into this object.
