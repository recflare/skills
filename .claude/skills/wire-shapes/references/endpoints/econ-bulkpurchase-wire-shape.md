# Econ bulkpurchase wire shape

> Wire shape of POST api/items/bulkpurchase on the Econ service (svc 28) for recflare-2025 — enveloped {Success, Error, error_id, Value} with a balance + per-item BalanceUpdates list.

Derived **2026-08-17** from `C:\Games\recflare-2025` (build `20250718.01`) via
[recflare-2025-metadata-carve](../../../il2cpp-analysis/references/recflare-2025-metadata-carve.md). Same method as [curatedlists-bulk-wire-shape](curatedlists-bulk-wire-shape.md) and
[matchmake-v2-room-wire-shape](matchmake-v2-room-wire-shape.md).

`POST https://econ.<host>/api/items/bulkpurchase` — service enum `NNPMGHNBFMD` = **28** (Econ; the
`mov r8d, 0x1c` before `AKJEAMCCEOH..ctor`). Client entry `AKDHOHEPFBH.KDOHPDDFIBB` (`0x7D8B330`),
state machine `KMEFLHDDNLH$$MoveNext` (`0x7DB62C0`). JSON body via `MGPBDIAGCFD.ELKIBCPINAP`.

**Request** `IHGONHNDFKA` (formatter `KHGDNEHGMOD` ctor `0x76FB700`): `PurchaseItemRequests`,
`StorefrontType`, `CurrencyType`, `BypassGiftPackages`, `AllowPartialSuccess`, `ShoppingBagId`.
Each item is `EHLBPHGFCOI` (`HOHFJBCFIIG` ctor `0x76E1530`): `ItemPurchaseMethodId`,
`RequestedPrice`, `Gift`, `CouponConsumablePlayerMappingId`, `DuplicateItemCount`.

**Response** `KGOJLHJNIOD<BalanceUpdateResponseDTO<MHKNNBHBKJI>>` — this one **is** enveloped, unlike
curated lists. Envelope keys (formatter `JNPEIEHDBLM` ctor `0x7E81D10`): `Value`, `Success`, `Error`,
**`error_id`** (lowercase — it carries `[DataMember(Name = "error_id")]`; the other three are
PascalCase).

`Value` = `BalanceUpdateResponseDTO<T>` (`OCCEFKLJDPE` ctor `0x77036C0`): `BalanceUpdates` (list),
plus the `BalanceResponseDTO` base (`LHBFHLKDIEF` ctor `0x7C1C1C0`) `Balance` long, `CurrencyType`,
**`Platform`** — that last key is the property `BalanceType` renamed by
`[DataMember(Name = "Platform")]`.

Each `BalanceUpdates[]` entry is the nested `OGAOPBELHMN` (`ADKLPEDMBCO` ctor `0x76EDEE0`):
`UpdateResponse` (enum `IIFPJCBKPKN`: OK 0, TooManyRequests, NotEnoughCredit, AlreadyOwned,
NoItemAvailable, CouponNotApplicable, RequestedPriceDoesNotMatch, RequestedAmountNotAllowed,
PlayerNotEligible, RequestCannotBeRefunded, PlayerNotApproved 10) and `Data` = `MHKNNBHBKJI`
(`KNKNINCHGFF` ctor `0x76FCCC0`): `GiftPackage`, `PurchasableItemId` (int?), `CustomAvatarItem`.

`CurrencyType` `PJBEJGJLLLM`: Invalid 0, LaserTagTickets 1, RecCenterTokens 2, LostSkullsGold 100,
DraculaSilver 101, RecRoyale_Season1 200, RoomCurrency 300, RoomInventoryItem 301,
ProgressionEvent 400, RoomieCredits 500. `Platform` `GNCGGEBPLKF`: NonPurchasedNotUsableInP2P -2,
NonPurchasedDefault -1, SteamPurchased 0, OculusPurchased 1, PlayStationPurchased 2,
MicrosoftPurchased 3, RecNetPurchased 4, IOSPurchased 5, GooglePlayPurchased 6, PicoPurchased 8,
SwitchPurchased 9, NonPurchasedEarnedByP2P 1000/1001, RoomieEnergyPack 1101.

**No required-field throw here.** `KGOJLHJNIOD<T>.CPOBHIECLEN` (`0x53B42D0`) only cascades —
`base.Validate()` (the `0xA60520` no-op) then `Value?.Validate()` — so a null `Value` is tolerated.
Contrast [matchmake-v2-room-wire-shape](matchmake-v2-room-wire-shape.md), where a null `RoomInstance` on success throws.

**Why:** the envelope key set here (`Value`/`Success`/`Error`/`error_id`) is the RecNet standard, but
whether a given endpoint is enveloped at all varies per endpoint — curated lists is bare, this is
enveloped. Never assume; check for a generated formatter on the concrete envelope instantiation.
