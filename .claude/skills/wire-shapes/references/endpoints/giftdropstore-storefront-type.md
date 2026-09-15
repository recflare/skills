# Giftdropstore storefront type

> api/storefronts/v3/giftdropstore/{N} IS THE CATALOG OF REGULAR PURCHASABLE ITEMS. N is a PNOBDCBDLNP StorefrontType enum value (1704 = PopUpShop_5), not a db id. Returns {StorefrontName,...,StoreItems[]} where each StoreItem carries PurchasableItemId (the int that '0.<int>' unified ids resolve against) and a 22-key GiftDrop.

Derived **2026-08-27** from build `20250718.01` via [recflare-2025-metadata-carve](../../../il2cpp-analysis/references/recflare-2025-metadata-carve.md).

URL is built in `<<GetStorefrontAsTask>b__0>d$$MoveNext` `0x7DC0310` as
`String.Format("{0}v3/giftdropstore/{1}", "api/storefronts/", storefrontType)` — service **28 Econ**.
Send `HPBKMCLEANE<FMHJCKFGDPI>` (required response); `FMHJCKFGDPI` is the GiftDropStorefront DTO,
also seen as `RecRoom.AppUI.Data.StoreItemListQueryData.out_GiftDropStorefront`.

## `{N}` is a StorefrontType enum value

`PNOBDCBDLNP`: `None 0`, `LaserTag 1`, `RecCenter 2`, `Watch 3`, `Quest_LostSkulls 100`,
`Quest_Dracula 101`, `Quest_GoldenTrophy 102`, `Quest_CrimsonCauldron 103`, `RecRoyale 200`,
`Cafe 300`, `Paintball 400` (+`_River 401` `_Homestead 402` `_Quarry 403` `_ClearCut 404`
`_Spillway 405` `_SunsetDriveIn 406`), `Bowling 500`, `StuntRunner 600`, `DormMirror 700`,
`InventionStore 800`, `RoomKeys 900`, `Player_Profile 1000`, `Room_Save 1100`,
`RoomCurrencies 1200`, `Wishlist 1300`, `Friendotron 1400`, `RoomConsumables 1500`, `RecRally 1600`,
**`PopUpShop_1..PopUpShop_20 = 1700..1719`**, `CustomAvatarItems 1800`,
`ProgressionEventPurchasableXpBoosts 1900`, `PopUpShop_ProgressionEvent_1..5 = 2000..2004`,
`RoomOffers 2100`, `MyLittleMonsters 2200`, `Destiny 2201`, `RunTheBlock 2202`.

**So `/giftdropstore/1704` = `PopUpShop_5`.** There is no database lookup — the client asks for a
fixed storefront *kind*, one request per pop-up-shop kiosk configured in the room.

## Who calls it

Public entry `RecRoom.Avatars.Outfit.OutfitManager.GetStorefront(PNOBDCBDLNP, bool)` `0x1493CA0`
-> `Task<FMHJCKFGDPI>`; sibling `GetStorefrontGiftDrops(PNOBDCBDLNP)` `0x1493BA0` ->
`Task<List<GBEBEEFLKJP>>`.

It is on the **room-load critical path**:
- `CPFHIBCIIJI$$MoveNext` `0xF3BEF0` logs `Downloading Room GiftDrop Shops` ->
  `Completed Downloading Room GiftDrop Shops`
- `JLADONGMCPP$$MoveNext` `0xF42590` does the bounded wait via `Task.WhenAny`, logging
  `Waiting on Download of Room GiftDrop Shops` and, on expiry,
  `Room GiftDrop Shops failed to download in the specified amount of time`

⚠️ Because it sits behind the single FIFO request pump ([serialized-request-queue-stall](../../../rr-client-bringup/references/serialized-request-queue-stall.md)) **and**
has its own timeout, a slow or hanging response here delays every room load. Answer promptly with an
empty storefront rather than 404-ing or stalling.

Other gift-drop literals worth grepping when debugging:
`AppActionsManager: Could not find PurchasableGiftDrop with ID {0}`,
`{0} cost not set for PurchasableGiftDrop id {1}`,
`Orientation store only supports PurchasableGiftDrop items!`.


## This IS the regular-purchasable-item catalog

Established **2026-08-27**. There is **no separate "browse all purchasable items" route** - the
storefront payload is the catalog, and the client caches it by `PurchasableItemId`.

`FMHJCKFGDPI` (GiftDropStorefront), formatter `MFJFPALAFOH` `.ctor 0x7684AD0`, **6 keys**:
`StorefrontName`, `SubscriberDiscountPercent`, `StorefrontType`, `NextUpdate`, `NewUntil`,
**`StoreItems`**.

`StoreItems[]` = `GBEBEEFLKJP` (PurchasableGiftDrop), formatter `OBNJPHDJPPM` `.ctor 0x7E85EC0`,
**11 keys**: **`GiftDrop`**, **`PurchasableItemId`** (int), `Type`, `Prices`, `SubscriberPrices`,
`IsFeatured`, `AvailableAt`, `AvailableUntil`, `NewUntil`, `CanBeGifted`, `OnlyAvailableThroughCv2`.

`GiftDrop` = `FLMDJANAGJA`, formatter `DPABMEPLIFA` `.ctor 0x7754A10`, **22 keys**:
`GiftDropId`, `FriendlyName`, `Tooltip`, `TagList`, `ConsumableItemDesc`, **`AvatarItemDesc`**,
**`CustomAvatarItemId`**, **`AvatarItemType`**, `EquipmentPrefabName`, `EquipmentModificationGuid`,
`IsQuery`, `Unique`, `SubscribersOnly`, `Rarity`, `CurrencyType`, `Currency`, `Context`, `ItemSetId`,
`ItemSetFriendlyName`, **`AvatarItemId`**, **`EquipmentItemId`**, `ThumbnailImageName`.

`GiftDrop` is a **discriminated union** - one drop points at a baked-in avatar item
(`AvatarItemId` / `AvatarItemDesc` / `AvatarItemType`), a custom avatar item (`CustomAvatarItemId`),
equipment (`EquipmentItemId` / `EquipmentPrefabName`), or a consumable (`ConsumableItemDesc`). That
is how one store row mixes Unity-shipped clothing with player-made items.

**`PurchasableItemId` is the int that `"0.<int>"` unified-algorithmic-list ids resolve against**
([algorithmiclists-type5-unified-id](algorithmiclists-type5-unified-id.md)): `MBNLJPBLFAF.DAHPAENLOOP` does a `Dictionary<int,...>`
lookup on the loaded storefront cache and returns null on a miss. **So a store row can only show a
regular item that some giftdropstore response already delivered** - populate the storefront first,
then reference its ids from discovery sections.

⚠️ Do NOT confuse with `api/avatar/v4/items` - that is the player's **owned/unlocked** avatar items
(`List<BGJHOEKDNED>`, [avatar-lockeditems-bulk-wire-shape](avatar-lockeditems-bulk-wire-shape.md)). Returning the whole catalog there
makes every item read as already owned.
