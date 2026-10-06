# Storefronts v1 buyRoomKey wire shape

> GET api/storefronts/v1/buyRoomKey?RoomKeyId=&RequestedPrice= (svc 28 Econ) returns the UNOBFUSCATED RoomKeyPurchaseResponseDTO: {RoomKeyResponse: {Status, RoomKey}, BalanceUpdateResponse: {BalanceUpdates, Balance, CurrencyType, Platform}}. `Platform` is a [DataMember] rename of BalanceType whose 0 is SteamPurchased — an omitted Platform claims a Steam purchase.

Derived **2026-10-01** from build `20250718.01`.
`RoomKeyResponse` is the **same `.AMNEJJIFIBM`** that [roomkeys-v1-create](roomkeys-v1-create-wire-shape.md) returns; `RoomKey` and
`Data` are both the 10-key `JODGFDKLMBO` from [roomkeys-v1-room](roomkeys-v1-room-wire-shape.md).

`GET https://econ.<host>/api/storefronts/v1/buyRoomKey` — service **28 = Econ**
(`mov dword ptr [rdi+0x18], 0x1c` at `0x7D86D51`), verb **GET** (`HttpMethod` statics `[rcx+8]` at
`0x7D86D10`). Whole-route literal, slot `0xD153E20`.

Client entry **`AKDHOHEPFBH.CEEPAGMBONL`** `0x7D86C00`. Two `ELHKHFJEHLM` params, **PascalCase** and —
because the verb is GET — in the **query string**: `RoomKeyId` (`0x7D86D8A`) then `RequestedPrice`
(`0x7D86DC1`). No body.

## Response — bare, two nested objects

`MGPBDIAGCFD.HPBKMCLEANE<T>`, generic inst **#1375** = **`.RoomKeyPurchaseResponseDTO`** (typedef
#22725) — **unobfuscated**, as are its two property names. Formatter `EPJDLBJDGNK` `.ctor`, keys
`RoomKeyResponse` / `BalanceUpdateResponse`.

```json
{ "RoomKeyResponse": {
    "Status": 0,
    "RoomKey": { "RoomKeyId": 43, "ReplicationId": "0f8c...", "RoomId": 12, "Name": "VIP Key",
                 "Description": "...", "Price": 0, "PurchaseCurrencyId": null,
                 "CreatedAt": "2026-01-01T00:00:00Z", "ImageName": null, "Type": 0 } },
  "BalanceUpdateResponse": {
    "BalanceUpdates": [ { "UpdateResponse": 0,
                          "Data": { "RoomKeyId": 43, "RoomId": 12, "Name": "VIP Key" } } ],
    "Balance": 1000, "CurrencyType": 2, "Platform": -1 } }
```

(`Data` carries the full 10-key room key, abbreviated above.)

### `BalanceUpdateResponse` is a SUBCLASS — derived-first key order

`.EPLDBKEAKJF : RecNet.BalanceResponseDTO`. It declares **one** field (`BalanceUpdates` at `0x20`);
the base supplies the other three. Derived-first ordering puts the subclass member first, which the
formatter `KPJCFOFCAIH` `.ctor 0x7698C80` confirms — run is `BalanceUpdates`, `Balance`,
`CurrencyType`, `Platform`:

| # | key | CLR | off | declared on |
|---|---|---|---|---|
| 1 | `BalanceUpdates` | `List<FDNDPCACJCK>` (inst #25641) | 0x20 | `EPLDBKEAKJF` |
| 2 | `Balance` | long | 0x10 | `BalanceResponseDTO` |
| 3 | `CurrencyType` | enum `PJBEJGJLLLM` | 0x18 | `BalanceResponseDTO` |
| 4 | **`Platform`** | enum `GNCGGEBPLKF`, field name **`BalanceType`** | 0x1C | `BalanceResponseDTO` |

**`Platform` is the `[DataMember]` rename of `BalanceType`.** This is the concrete instance of the
rename rule in `SKILL.md` — the C# name never appears on the wire.

### `BalanceUpdates[]` element — `.FDNDPCACJCK`

Formatter `NAFIJOHONNM` `.ctor 0x769D230`, 2 keys:

| # | key | CLR | off |
|---|---|---|---|
| 1 | `UpdateResponse` | enum `IIFPJCBKPKN` | 0x10 |
| 2 | `Data` | `.JODGFDKLMBO` (the room key) | 0x18 |

A generic "purchase update" wrapper — `AJIPDCKPHHJ` (typedef #22719) is the same generated shape over
a different `Data` type, so do not assume `Data` is always a room key on sibling storefront routes.

## Enums — three of them have a dangerous `0`

| enum | members |
|---|---|
| `IIFPJCBKPKN` **UpdateResponse** | `OK 0`, `TooManyRequests 1`, `NotEnoughCredit 2`, `AlreadyOwned 3`, `NoItemAvailable 4`, `CouponNotApplicable 5`, **`RequestedPriceDoesNotMatch 6`**, `RequestedAmountNotAllowed 7`, `PlayerNotEligible 8`, `RequestCannotBeRefunded 9`, `PlayerNotApproved 10` |
| `PJBEJGJLLLM` **CurrencyType** | `Invalid 0`, `LaserTagTickets 1`, `RecCenterTokens 2`, `LostSkullsGold 100`, `DraculaSilver 101`, `RecRoyale_Season1 200`, `RoomCurrency 300`, `RoomInventoryItem 301`, `ProgressionEvent 400`, `RoomieCredits 500`, `NonPurchasedEarnedByP2P 1000`, `NonPurchasedEarnedByP2Pv2 1001`, `RoomieEnergyPack 1101` |
| `GNCGGEBPLKF` **BalanceType, wire `Platform`** | `NonPurchasedNotUsableInP2P -2`, `NonPurchasedDefault -1`, **`SteamPurchased 0`**, `OculusPurchased 1`, `PlayStationPurchased 2`, `MicrosoftPurchased 3`, `RecNetPurchased 4`, `IOSPurchased 5`, `GooglePlayPurchased 6`, `PicoPurchased 8`, `SwitchPurchased 9` |

⚠️ **Three zero-value traps stack on this one route.** An omitted key reads as the `0` member:

- `RoomKeyResponse.Status` → `RoomKeyResult.Success` ([roomkeys-v1-create](roomkeys-v1-create-wire-shape.md))
- `BalanceUpdates[].UpdateResponse` → `OK`
- **`Platform` → `SteamPurchased`** — the worst of the three, because it is not merely permissive but
  *wrong*: omitting it tells the client the balance was bought on Steam. For currency the player
  earned, send **`-1` (`NonPurchasedDefault`)**.

`CurrencyType`'s `0` is `Invalid`, so that one is safe to omit. `GNCGGEBPLKF` has **no `7`**.

⚠️ `RequestedPriceDoesNotMatch (6)` is the rejection for the `RequestedPrice` query param — the server
is expected to compare it against the key's real price, so a `RequestedPrice=0` on a priced key should
come back as `6`, not `OK`.

## Validation — all hooks null-tolerant

| type | `CPOBHIECLEN` | behaviour |
|---|---|---|
| `RoomKeyPurchaseResponseDTO` | **`0x7DC02B0`** real | `if (RoomKeyResponse != null)` then its no-op hook; `if (BalanceUpdateResponse != null)` then tail-jump to its virtual hook (`vtable+0x1A0`) |
| `EPLDBKEAKJF` | **`0x7DAA9B0`** real | base's no-op, then `EADLCOCJAGD.IANBCAFGFNL(BalanceUpdates, 0)` `0x7623250` |
| `FDNDPCACJCK`, `AMNEJJIFIBM`, `JODGFDKLMBO` | `0xA60520` no-op | — |

Every dereference is guarded, and the list walker returns early on null
([playerevents-v1-all](playerevents-v1-all-wire-shape.md) proves `0x762345C` is `xor al,al ; ret`). So both nested objects and
`BalanceUpdates` may be `null` without throwing at deserialize. Prefer `[]` and real objects anyway —
downstream consumers were not traced.

## Siblings

`api/storefronts/v1/PurchaseRoomKeyWithCurrency` is now derived and is the **mirror image** of this
route — POST not GET, a room-currency `Balance` object not a token `BalanceUpdateResponse`, and the
reversed key order: [storefronts-v1-purchaseroomkeywithcurrency](storefronts-v1-purchaseroomkeywithcurrency-wire-shape.md).

Same facade/prefix, not yet derived: `/buyForFreeGiftButton`, `/buyProgressionEventXpBoost`,
`/buyPurchaseReminder`, `/adcarouselitems`, `/objectives`, `/toptoday`,
`/trialInvention/duration`.
