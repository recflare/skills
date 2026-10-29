# `PUT api/roomconsumables/v1/roomconsumable/{id}/purchase/currency`

> **PUT** (svc **28 Econ**) with a **JSON body**, returning a **bare 3-key object** —
> `RecNet.RoomConsumablePurchaseWithCurrencyResponse`. No envelope.
> ⚠️ **It has 3 keys, not the 2 its own type declares.** The type **inherits** from
> `RoomConsumablePurchaseResponse`, so the wire is `BalanceUpdateResult`,
> `CurrencyBalanceResponse`, **then the inherited `OperationResult`** — derived-before-base.
> Reading the 2 declared fields and stopping is the trap here: `OperationResult` is where the
> success/deny status actually lives.
> ⚠️ **Note the casing.** The route literal is **all-lowercase `roomconsumable`**, unlike the
> sibling list route which is `roomConsumable`. Both spellings exist in the build.

Derived **2026-10-22** from build `20260323.14`.

## Route

Facade **`RecNet.Storefronts.UQSIWWZUABW`** **`0x955E6B0`** — note it is on **`Storefronts`**, not a
`RoomConsumables` facade:

```csharp
static RecRoom.Async.MPVTAJGPRUT<RecNet.RoomConsumablePurchaseWithCurrencyResponse>
UQSIWWZUABW(Guid roomConsumableId, long price, Guid currencyId,
            Guid? currentConcurrencyCode, int quantity, int? giftRecipientAccountId)
```

| what | value | evidence |
|---|---|---|
| path | `api/roomconsumables/v1/roomconsumable/{0}/purchase/currency` | literal **`0xFC685E0`**, `mxref` = 2 refs, both here; `String.Format` at `0x955E952` with `{0}` = the `Guid` |
| service | **28 = Econ** | `mov r8d, 0x1C` at `0x955E96B`, into the request `.ctor` `0x8BBF9E0` at `0x955E97F` |
| verb | **PUT** | `[klass+0x20]` → **`[statics+0x28]`** at `0x955E92C`–`0x955E930` |
| params | **none** | only 4 literals in the whole method: the route ×2 and the failure message ×2 |
| body | **JSON** | `RGBOOBRDHEB.FZNGWUAGAIN<T>(T)` at `0x955E99A` — the JSON-body setter |
| response | `RoomConsumablePurchaseWithCurrencyResponse` | the promise's `T` |

Sole caller: `RecRoom.Systems.Economy.Consumables.RoomConsumablesManager.JACRRMLUHLQ` `0xFB51D0`,
which pre-validates locally with `"Purchase quantity cannot be less than 1"` — so a quantity < 1
never reaches the server.

The returned promise is decorated with the failure message **`"Failed to purchase room consumable"`**
(use site `0x955E9F7`, into a `RecNet.KGLKSSUUEOH` error-mapping helper), so a rejected request
surfaces as that user-visible error rather than a crash. ⚠️ **Not pinned**: which of the
`KGLKSSUUEOH` overloads — the target `0x3C09910` falls in a `methods.pkl` gap and the arg layout
(`rcx` promise, `edx` an int from statics, `r8` the string) matches none of the three documented
`(promise, Log, string)` forms exactly.

## Request body — `RecNet.RoomConsumablePurchaseRequest`

Formatter **`Utf8Json.Formatters.RecNet.XSVPCNUQZXQ`** `.ctor` **`0x8E6D2D0`** (confirmed by `msig`),
`____stringByteKeys` `0x8E6D568`…`0x8E6D5E4` — **4 keys in declaration order**:

```json
{
  "ConcurrencyCodes":        {"CurrentConcurrencyCode": "…guid or null", "NewConcurrencyCode": "…guid"},
  "ExpectedPriceAndCurrency":{"Price": 100, "CurrencyId": "…guid or null"},
  "Quantity":                1,
  "GiftRecipientAccountId":  null
}
```

| key | CLR | notes |
|---|---|---|
| `ConcurrencyCodes` | `RecNet.RoomConsumableConcurrencyCodes` | `{CurrentConcurrencyCode: Guid?, NewConcurrencyCode: Guid}` — optimistic-concurrency pair |
| `ExpectedPriceAndCurrency` | `RecNet.RoomConsumablePriceAndCurrency` | `{Price: long, CurrencyId: Guid?}` — **`Price` is a `long`** here, unlike `RoomKey.Price` (int) |
| `Quantity` | int | ≥ 1, enforced client-side |
| `GiftRecipientAccountId` | `int?` | present ⇒ this is a gift purchase |

The server is expected to reject a stale `CurrentConcurrencyCode` with
`ConcurrencyCodeMismatch = 32`, and a price/currency mismatch with
`RequestedPriceDoesNotMatch = 38` / `RequestedCurrencyDoesNotMatch = 39` (see the enum below).

## Response — bare, **3 keys**

Formatter **`Utf8Json.Formatters.RecNet.HGRMQBJTYOH`** `.ctor` **`0x8E5DDE0`** (confirmed by `msig`:
`Serialize(JsonWriter, RecNet.RoomConsumablePurchaseWithCurrencyResponse, …)`),
`____stringByteKeys` `0x8E5E01C`…`0x8E5E06C`:

| # | key | CLR | off | notes |
|---|---|---|---|---|
| 1 | `BalanceUpdateResult` | `RecNet.CurrencyBalanceUpdateResult?` | 0x18 | **nullable enum**, numeric |
| 2 | `CurrencyBalanceResponse` | `RecNet.CurrencyBalance` | 0x20 | object |
| 3 | **`OperationResult`** | `RecNet.RoomConsumableInventoryItemOperationResult` | **0x10** | **inherited** from `RoomConsumablePurchaseResponse` |

> 🔑 **How the inheritance was caught**: `fields2025.py` reports the type's own first field at
> **`0x18`**, not `0x10` — the gap at `0x10` is the base class's `OperationResult`. The formatter
> then confirms three keys with the base member **last**. Any time a 2026 DTO's lowest declared
> offset is above `0x10`, look for a base class before trusting the key count.

```json
{
  "BalanceUpdateResult": 0,
  "CurrencyBalanceResponse": {
    "AccountId": 1, "CurrencyId": "…guid", "Balance": 900, "ModifiedAt": "2026-10-22T00:00:00Z"
  },
  "OperationResult": {
    "Status": 0,
    "InventoryItem": {
      "RoomConsumableId": "65ac0fdf-3ed9-4e78-9709-59d0b7f3e26f",
      "AccountId": 1, "Count": 1, "ConcurrencyCode": "…guid",
      "ModifiedAt": "2026-10-22T00:00:00Z",
      "Consumable": { … }
    }
  }
}
```

### `BalanceUpdateResult` — `RecNet.CurrencyBalanceUpdateResult?` (#23099)

```
Success = 0 · NotEnoughCredit = 1
```

Numeric on the wire. It is **`Nullable`**, so omitting it is meaningful (`null` = "no balance update
attempted") and distinct from `0`. ⚠️ Do not leave it out on a success — `0` is `Success`, and
`null` is not.

### `CurrencyBalanceResponse` — `RecNet.CurrencyBalance` (#23118), 4 keys

| key | CLR | off |
|---|---|---|
| `AccountId` | **int** | 0x10 |
| `CurrencyId` | `System.Guid` | 0x14 |
| `Balance` | **long** | 0x28 |
| `ModifiedAt` | `DateTime` | 0x30 |

Same four members as the room-currency balance on
[storefronts-v1-purchaseroomkeywithcurrency](storefronts-v1-purchaseroomkeywithcurrency-wire-shape.md).
⚠️ There is **no `BalanceType`/`Platform`** on this type, so the "omitting Platform claims a Steam
purchase" trap from [storefronts-v1-buyroomkey](storefronts-v1-buyroomkey-wire-shape.md) does **not**
apply here.

### `OperationResult` — `RecNet.RoomConsumableInventoryItemOperationResult` (#23090), 2 keys

| key | CLR |
|---|---|
| `Status` | `RecNet.RoomConsumableResult` — enum, numeric |
| `InventoryItem` | `RecNet.RoomConsumableInventoryItem` |

`RecNet.RoomConsumableInventoryItem` (#23089), 6 keys:

| key | CLR | off |
|---|---|---|
| `RoomConsumableId` | `Guid` | 0x10 |
| `AccountId` | int | 0x20 |
| `Count` | int | 0x24 — the post-purchase owned count |
| `ConcurrencyCode` | `Guid` | 0x28 — feed this back as `CurrentConcurrencyCode` next time |
| `ModifiedAt` | `DateTime` | 0x38 |
| `Consumable` | `RecNet.RoomConsumable` | 0x40 |

`RecNet.RoomConsumable` (#23082) — **11 instance members on 2026**, not the 9 the 2025 note records
for `.JHLGLLIJGKM` ([roomconsumables-by-room](roomconsumables-by-room-wire-shape.md)). The four
`MIN_/MAX_NAME_LENGTH`, `MIN_/MAX_DESCRIPTION_LENGTH` entries are **static consts** and carry no key:

| key | CLR | off |
|---|---|---|
| `RoomConsumableId` | `Guid` | 0x10 |
| `RoomId` | long | 0x20 |
| `Name` | string | 0x28 |
| `Description` | string | 0x30 |
| `ImageName` | string | 0x38 |
| `Price` | **long** | 0x40 |
| `PurchaseCurrencyId` | `Guid?` | 0x48 |
| `ModifiedAt` | `DateTime` | 0x60 |
| `MaximumCountPerPurchase` | int | 0x68 |
| **`IsGiftable`** | bool | 0x6C | **new on 2026** |
| **`Visibility`** | `RecRoom.DataLayer.UgcPurchasableItemVisibility` | 0x70 | **new on 2026** |

Same two additions as `RecNet.RoomKey` ([roomkeys-v1-mine](roomkeys-v1-mine-wire-shape.md)) —
2026 added `IsGiftable` + `Visibility` to the UGC purchasable types as a set.

### `Status` — `RecNet.RoomConsumableResult` (#23098): the deny vocabulary

Numeric on the wire. This is the full server-side reason code set, so it is worth having in one
place:

```
-1 Unknown                               27 DescriptionTooLong
 0 Success                               28 DescriptionHasInvalidCharacters
 1 FeatureDisabled                       29 DuplicateName
 2 ConsumableUnderModeration             30 InappropriateName
 3 RoomConsumableIdMismatch              31 InappropriateDescription
 4 RoomConsumableNotFound                32 ConcurrencyCodeMismatch
 5 ImageDoesNotExist                     33 PlayerDoesNotOwnConsumable
 6 AccountIdInvalid                      34 OwnershipLimitExceeded
 7 PlayerDoesntHavePermission            35 PurchaseFailed
 8 PlayerIsNotBetaMember                 36 RoomNotFound
 9 PlayerIsNotRRPMember                  37 RoomUnderModeration
10 PlayerIsP2PSellingRestricted          38 RequestedPriceDoesNotMatch
11 PlayerIsJuniorAccount                 39 RequestedCurrencyDoesNotMatch
12 PlayerUnderModeration                 40 ConsumableCannotBePurchasedWithRoomCurrency
13 MaxConsumablesInRoom                  41 ConsumableCannotBePurchasedWithTokens
14 RoomIdMismatch                        42 PlayerIsP2PBuyingRestricted
15 RoomIdMissing                         43 AwardAmountIsInvalid
16 RoomIdInvalid                         44 ConsumableCannotBeAwarded
17 PriceOrCurrencyMissing                45 PlayerHasReachedAwardLimit
18 CurrencyNotFound                      46 AwardLimitIsInvalid
19 PriceTooLowCurrency                   47 InvalidRelationship
20 PriceTooHighCurrency                  48 PlayerIsUgcGiftingRestricted
21 PriceTooLowTokens                     49 PlayerIsUgcGiftReceivingRestricted
22 PriceTooHighTokens                    50 CannotGiftFreeConsumable
23 NameTooShort                          51 RoomConsumableNotGiftable
24 NameTooLong                           52 GiftingRateLimited
25 NameHasInvalidCharacters              53 CannotUpdateToTokenPrice
26 DescriptionTooShort
```

⚠️ **`Unknown` is `-1`, so `0` is `Success`** — an omitted `Status` reads as a successful purchase.
Never leave it out on a deny.

## No validation anywhere in the chain

**None** of `RoomConsumablePurchaseWithCurrencyResponse`, `RoomConsumablePurchaseResponse`,
`RoomConsumableInventoryItemOperationResult`, `RoomConsumableInventoryItem`, `CurrencyBalance` or
`RoomConsumable` declares an `EMSIIQRWASQ` (sync) or `IULRMJBAHPG` (async) post-deserialize hook —
checked individually. So there is **zero** server-side-payload validation or null normalization: a
partial object parses, and every omitted number silently becomes `0`.

The send is the plain **`ZWUODKCINOA<RoomConsumablePurchaseWithCurrencyResponse>(ct)`** at
`0x955E9B4` (`xor edx, edx` = `default(CancellationToken)`), **not** `LIRIDCJIGGA(bool, ct)` — so
there is no allow-null flag and nothing rejects a null body
([2026-send-helper-tiers](../conventions/2026-send-helper-tiers.md)). A `null` body therefore
**resolves the promise successfully** with a null response object, and the deny path never fires.

➡️ **Always return the full 3-key object.** For a deny, send
`{"BalanceUpdateResult":1,"CurrencyBalanceResponse":{…},"OperationResult":{"Status":<code>,"InventoryItem":null}}`
rather than a 4xx with no body — that is the shape the client's error path is built to read.

# The `/purchase/tokens` sibling

Derived **2026-10-22**, same session. `PUT api/roomconsumables/v1/roomconsumable/{id}/purchase/tokens`
— literal **`0xFC68930`**, **`RecNet.Storefronts.MJPEAUCRNMF(Guid roomConsumableId, long price,
Guid? currentConcurrencyCode, int quantity, int? giftRecipientAccountId)`** **`0x955C520`** →
`MPVTAJGPRUT<RecNet.RoomConsumablePurchaseWithTokenResponse>`.

**Structurally identical to the currency route** — PUT (`[statics+0x28]` at `0x955C74A`), svc **28
Econ** (`mov r8d, 0x1C` at `0x955C785`), JSON body via `FZNGWUAGAIN<T>` at `0x955C7B4`, plain
`ZWUODKCINOA` send at `0x955C7CE`, same 4 literals (route ×2 + `"Failed to purchase room
consumable"` ×2), so **no query or form params**. The facade drops the `Guid currencyId` argument —
that is the only signature difference.

**Request body is the same `RecNet.RoomConsumablePurchaseRequest`** (it is the only
`RoomConsumablePurchase*Request` typedef in the build), with
`ExpectedPriceAndCurrency.CurrencyId` left `null`:

```json
{"ConcurrencyCodes":{"CurrentConcurrencyCode":null,"NewConcurrencyCode":"…guid"},
 "ExpectedPriceAndCurrency":{"Price":100,"CurrencyId":null},
 "Quantity":1,"GiftRecipientAccountId":null}
```

## Token response — also **3 keys**, also inherited

`RecNet.RoomConsumablePurchaseWithTokenResponse` (typedef #23096) declares 2 fields, first at
**`0x18`** — so it inherits the same `OperationResult` at `0x10`. Formatter
**`Utf8Json.Formatters.RecNet.EONQFLRPPMP`** `.ctor` **`0x8E5B080`**, `____stringByteKeys`
`0x8E5B2BC`…`0x8E5B30C`:

| # | key | CLR | off |
|---|---|---|---|
| 1 | `BalanceUpdateResult` | **`RecNet.UpdateResponseTypes?`** | 0x18 |
| 2 | `TokenBalanceResponse` | **`RecNet.BalanceResponseDTO`** | 0x20 |
| 3 | `OperationResult` | `RoomConsumableInventoryItemOperationResult` | 0x10 (inherited) |

⚠️ **Keys 1 and 2 are NOT the currency route's types.** Only `OperationResult` is shared — it is
byte-for-byte the same `{Status, InventoryItem}` with the same `RoomConsumableResult` enum.

### `BalanceUpdateResult` — `RecNet.UpdateResponseTypes?` (#46529), a different enum

```
OK = 0 · TooManyRequests = 1 · NotEnoughCredit = 2 · AlreadyOwned = 3 · NoItemAvailable = 4
CouponNotApplicable = 5 · RequestedPriceDoesNotMatch = 6 · RequestedAmountNotAllowed = 7
PlayerNotEligible = 8 · RequestCannotBeRefunded = 9 · PlayerNotApproved = 10
```

Note the clash: **`NotEnoughCredit` is `2` here, but `1` in the currency route's
`CurrencyBalanceUpdateResult`** (`Success 0 · NotEnoughCredit 1`). The success member is also named
differently (`OK` vs `Success`), though both are `0`. Numeric on the wire; `Nullable`, so `null` is
distinct from `0`.

### `TokenBalanceResponse` — `RecNet.BalanceResponseDTO` (#46530), 3 keys — ⚠️ one is RENAMED

Formatter **`Utf8Json.Formatters.RecNet.QEBKDCYWYRE`** `.ctor` **`0x8FFD500`**, keys at
`0x8FFD6DF`…`0x8FFD72F`:

| # | wire key | CLR member | type | off |
|---|---|---|---|---|
| 1 | `Balance` | `Balance` | **long** | 0x10 |
| 2 | `CurrencyType` | `CurrencyType` | `RecNet.CurrencyType` | 0x18 |
| 3 | **`Platform`** | **`BalanceType`** | `RecNet.StorefrontBalanceType` | 0x1C |

> 🔑 **`BalanceType` goes on the wire as `Platform`** — the same `[DataMember]` rename already
> recorded for [storefronts-v1-buyroomkey](storefronts-v1-buyroomkey-wire-shape.md). The formatter
> is the authority; sending `BalanceType` is silently dropped. This is *why* the type's own
> `BalanceType` key literal does not resolve to this formatter.

⚠️ **Two zero-value traps, both of which make an omitted key mean something wrong:**

```
RecNet.StorefrontBalanceType (#46526)                RecNet.CurrencyType (#46525)
  NonPurchasedNotUsableInP2P = -2                      Invalid            = 0   <-- default!
  NonPurchasedDefault        = -1                      LaserTagTickets    = 1
  SteamPurchased             =  0   <-- default!       RecCenterTokens    = 2
  OculusPurchased            =  1                      LostSkullsGold     = 100
  PlayStationPurchased       =  2                      DraculaSilver      = 101
  MicrosoftPurchased         =  3                      RecRoyale_Season1  = 200
  RecNetPurchased            =  4                      RoomCurrency       = 300
  IOSPurchased               =  5                      RoomInventoryItem  = 301
  GooglePlayPurchased        =  6                      ProgressionEvent   = 400
  PicoPurchased              =  8                      RoomieCredits      = 500
  SwitchPurchased            =  9                      PaintballPaint     = 600
```

- Omitting **`Platform`** claims a **Steam purchase** (`0`). Send **`-1`**
  (`NonPurchasedDefault`) for earned/non-purchased token balances, or **`-2`** to additionally bar
  the balance from P2P spending.
- Omitting **`CurrencyType`** yields **`Invalid` (0)**, not "tokens". Send the real currency.

(There is no `7` in `StorefrontBalanceType` — the enum is sparse, so do not infer values.)

## Both routes at a glance

| | `/purchase/currency` | `/purchase/tokens` |
|---|---|---|
| facade | `UQSIWWZUABW` `0x955E6B0` | `MJPEAUCRNMF` `0x955C520` |
| route literal | `0xFC685E0` | `0xFC68930` |
| verb · svc | PUT · 28 Econ | PUT · 28 Econ |
| extra arg | `Guid currencyId` | — |
| request body | `RoomConsumablePurchaseRequest` | same, `CurrencyId: null` |
| response formatter | `HGRMQBJTYOH` `0x8E5DDE0` | `EONQFLRPPMP` `0x8E5B080` |
| key 1 | `BalanceUpdateResult` : `CurrencyBalanceUpdateResult?` | `BalanceUpdateResult` : `UpdateResponseTypes?` |
| key 2 | `CurrencyBalanceResponse` : `CurrencyBalance` (4 keys) | `TokenBalanceResponse` : `BalanceResponseDTO` (3 keys, `Platform` rename) |
| key 3 | `OperationResult` (inherited) | `OperationResult` (inherited) — **identical** |
| hooks | none | none |

Everything in **No validation anywhere in the chain** above applies unchanged to the tokens route:
no post-deserialize hook on `RoomConsumablePurchaseWithTokenResponse`, `BalanceResponseDTO` or
anything below them, and the plain `ZWUODKCINOA` send means a `null` body resolves successfully and
the deny path never fires. **Return the full 3-key object for denies too.**
