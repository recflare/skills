# Storefronts v3 buyinvention wire shape

> POST api/storefronts/v3/buyInvention (svc 28 Econ) returns a BARE 2-key {InventionResponse, BalanceUpdateResponse}; InventionResponse is the SAME KGOJLHJNIOD<GCLKCLFIPED> envelope as v9/save and NREs if Success=true with a null Value.

Derived **2026-09-02** from build `20250718.01` via [recflare-2025-metadata-carve](../../../il2cpp-analysis/references/recflare-2025-metadata-carve.md).
Shares its inner payload with [inventions-v9-save-wire-shape](inventions-v9-save-wire-shape.md) and its balance half with
[econ-bulkpurchase-wire-shape](econ-bulkpurchase-wire-shape.md).

`POST https://econ.<host>/api/storefronts/v3/buyInvention` — service **28 = Econ**
(`mov dword ptr [rdi+0x18], 0x1c` at `0x7D8C30C`), verb **POST** (`HttpMethod` statics `+0x20`, read
at `0x7D8C2CB`). Literal `0xD155AE0`. Client entry
`AKDHOHEPFBH.MNJGAGIDMCP(long inventionId, int requestedPrice)` **`0x7D8C1C0`**.

**Request: a JSON body** (via `MGPBDIAGCFD.ELKIBCPINAP`, inst 14962), not form params —
`RecNet.PurchaseInventionRequestDTO`, **unobfuscated**, 2 keys:
`{"InventionId": long, "RequestedPrice": int}`.

## Response — BARE object, 2 keys

Send generic `HPBKMCLEANE<.InventionPurchaseResponseV2DTO>` (inst **1374**) — no outer envelope.
Formatter `GDDDJFIJNKK` `.ctor 0x7694F70`.

```json
{ "InventionResponse":     { …KGOJLHJNIOD<GCLKCLFIPED>… },
  "BalanceUpdateResponse": { …BODFFHLDIPO… } }
```

**`InventionResponse` is `KGOJLHJNIOD<GCLKCLFIPED>` — the exact envelope from
[inventions-v9-save-wire-shape](inventions-v9-save-wire-shape.md)** (`{Value:{Status,Invention,InventionVersion,TagsResponse},
Success, Error, error_id}`), nested one level down.

**`BalanceUpdateResponse`** = `.BODFFHLDIPO : RecNet.BalanceResponseDTO`, formatter `MDKJCLJCGCF`
`.ctor 0x7E69A70`, 4 keys — derived first, then base:

| # | key | CLR | note |
|---|---|---|---|
| 1 | `BalanceUpdates` | `List<AJIPDCKPHHJ>` | derived |
| 2 | `Balance` | long | base |
| 3 | `CurrencyType` | enum `PJBEJGJLLLM` | base |
| 4 | `Platform` | enum `GNCGGEBPLKF` | base — **the CLR field is `BalanceType`; the wire key is `Platform`** |

`AJIPDCKPHHJ` (formatter `DOHMPLPHMOH` `.ctor 0x7E5D610`) = **`{"UpdateResponse": enum, "Data": Invention}`**
where `Data` is the 28-key `KKBFDGFLMMA` invention DTO.

## Enums

- `UpdateResponse` `.IIFPJCBKPKN`: `OK 0`, `TooManyRequests 1`, `NotEnoughCredit 2`,
  `AlreadyOwned 3`, `NoItemAvailable 4`, `CouponNotApplicable 5`,
  `RequestedPriceDoesNotMatch 6`, `RequestedAmountNotAllowed 7`, `PlayerNotEligible 8`,
  `RequestCannotBeRefunded 9`, `PlayerNotApproved 10`.
- `CurrencyType` `.PJBEJGJLLLM`: `Invalid 0`, `LaserTagTickets 1`, `RecCenterTokens 2`,
  `LostSkullsGold 100`, `DraculaSilver 101`, `RecRoyale_Season1 200`, `RoomCurrency 300`,
  `RoomInventoryItem 301`, `ProgressionEvent 400`, `RoomieCredits 500`.
- `Platform` `.GNCGGEBPLKF`: `NonPurchasedNotUsableInP2P -2`, `NonPurchasedDefault -1`,
  `SteamPurchased 0`, `OculusPurchased 1`, `PlayStationPurchased 2`, `MicrosoftPurchased 3`,
  `RecNetPurchased 4`, `IOSPurchased 5`, `GooglePlayPurchased 6`, `PicoPurchased 8`,
  `SwitchPurchased 9`, `PlayStationNonPurchasedP2P 100`, `NonPlayStationNonPurchasedP2P 101`,
  `NonPurchasedEarnedByP2P 1000`, `NonPurchasedEarnedByP2Pv2 1001`, `RoomieEnergyPack 1101`.

## No deserialisation throws — but the consumer has two

`InventionPurchaseResponseV2DTO.CPOBHIECLEN` `0x7DB3FB0` null-guards both members and forwards to
their hooks; its whole range contains **zero** throw-helper calls.

`<>c.CHMHDEEIMOM(InventionPurchaseResponseV2DTO)` **`0x7DC0D20`** (the `.Then`):
- `response` null → **quiet return**
- `response.InventionResponse` null → **NRE** (`0x7DC0D69` → `0x7DC0DE5`)
- `InventionResponse.Success == false` → **quiet return; the balance is NOT applied**
- `BalanceUpdateResponse` non-null → `AKDHOHEPFBH.ADDMHLHKNCB(RecNet.BalanceResponseDTO)` `0x7D85B10`
  — note the **base** type, so only `Balance` / `CurrencyType` / `Platform` are consumed;
  **`BalanceUpdates` is never read on this path**. `null` is fine (skipped).
- `InventionResponse.Value` null → **NRE** (`0x7DC0DB5`)
- `Value.Invention` → `GLAKFFIIDPF.EKKDIPMBHJN` `0x7CE9F80`, which **returns quietly on null** — so
  unlike [inventions-v2-metadata-wire-shape](inventions-v2-metadata-wire-shape.md) and [inventions-v4-publish-wire-shape](inventions-v4-publish-wire-shape.md), a null
  `Invention` is tolerated here.

`Status` inside `Value` is, once again, never read.

**How to apply:** on success return
`{"InventionResponse":{"Success":true,"Value":{"Status":0,"Invention":{…}}},
"BalanceUpdateResponse":{"Balance":<new>,"CurrencyType":2,"Platform":0,"BalanceUpdates":[]}}`.
To refuse, `{"InventionResponse":{"Success":false,"Error":"…","Value":null},
"BalanceUpdateResponse":null}` is safe — but note nothing surfaces that `Error` to the player on
this path, and the client's own balance simply stays stale. Never `Success:true` with a null `Value`.
