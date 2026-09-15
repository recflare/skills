# Discovery sections pagesource wire shape

> Wire shape of GET sections/pagesource/{id} on the Discovery service for recflare-2025 — a bare array of 5-key section DTOs whose DisplayMetadata is a nested JsonUtility JSON string.

Derived **2026-08-17** from `C:\Games\recflare-2025` (build `20250718.01`) via
[recflare-2025-metadata-carve](../../../il2cpp-analysis/references/recflare-2025-metadata-carve.md).

`GET https://discovery.<host>/sections/pagesource/{pagesourceId}` — **GET**, no query params
(path is `String.Concat("sections/pagesource/", id)`; no configure closure). Client entry
`GHPCLEPIJGF.DNLDAOPCOHJ(string pagesourceId, CancellationToken)` (`0x7E4A690`), state machine
`DAEDGNJHFEF$$MoveNext` (`0x7E46EA0`). Known page-source ids: `StoreCategories`, `PlayCategories`.

Response is a **bare array**, `List<LCDOCLAIDFN>` — no envelope (no formatter exists for any
envelope instantiation of it). Element formatter `ICJKMFKKBCH` ctor `0x76F7590`; the DTO's property
names are **unobfuscated**, so keys == members: `Id` string 0x10, `SectionType` enum 0x18,
`Source` string? 0x20, `SourceMetadata` string? 0x28, `DisplayMetadata` string? 0x30.
`CPOBHIECLEN` is the `0xA60520` no-op — no validation.

`SectionType` `JBCDFKPPEML`: RoomsSection 0, AccountsSection 1, InventionsSection 2, ClubsSection 3,
StoreItemsSection 4, EventsSection 5, RoomBanner 6, Top5Section 7, CustomAvatarItemsSection 8,
AdsSection 9, SkusSection 10, RoomCategorySection 11, RoomCategoryListSection 12,
DiscoverySection 13.

**The consumer is stricter than the DTO** — `RRUI.Data.CategorizedStoreModel`
`TryGetStoreCategoryFromSectionDTO` (`0xB0AD40`) drops a section unless all of:

- `DisplayMetadata` is non-empty (an `IsNullOrEmpty` guard) **and** parses **and** its
  `IsSupported` returns true (platform / junior / account-age gating);
- `SectionType` is **4 (StoreItemsSection)** → handled by
  `StoreCarouselListModel.TryGetCarouselInfoFromSectionDTO`, or **13 (DiscoverySection)** → the
  `Source` branch. Anything else logs "Unhandled SectionType {0}, skipping.";
- for DiscoverySection, `Source` is exactly `"CuratedList"` or `"PageSource"` (`SourceMetadata`
  carries the argument — a curated-list id, or another page-source name to recurse into). Anything
  else logs "Unhandled Source {0} for SectionType.DiscoverySection, skipping."

**`DisplayMetadata` is a JSON string parsed by `UnityEngine.JsonUtility`, not Utf8Json** — public
fields, **exact case, no casing variants, no envelope**. Target here is
`RRUI.Data.StorePageDiscoveryDisplayMetadata : DiscoveryDisplayMetadata : BaseDiscoveryDisplayMetadata`
(resolved from the `FromJson` methodSpec generic inst, not guessed). Fields:

- base: `unsupportedPlatforms` string[], `unsupportedInteractionCategories` string[],
  `excludeJuniors` bool, `excludeJuniorsWithoutCreatePermissions` bool, `accountAgeMinDays` int,
  `accountAgeMaxDays` int
- `DiscoveryDisplayMetadata`: `DisplayTitle` (capital D), `supportsDedupe`, `numRows`,
  `sizePerPlatform`, `backgroundColor`, `horizontalScrollEnabled`, `itemCount`, `cardStyle`,
  `minItemsToShowSection`, `imageName`, `textColor`, `showNewThisSessionForSection`,
  `sessionSectionIdOverride`, `descriptionText`
- store page: `itemsToContributeToDeduping`, `itemsToDedupe`, `tagList`, `categoryDepth`,
  `categoryIconSprite`, `categoryUriNames`, `HideSkuInfoOnCards`

`categoryUriNames` is **comma-separated** (`String.Split(',')` on field 0xE0 in the parsed object).

**Why:** the wire DTO is trivially permissive but the page renders nothing unless `DisplayMetadata`
carries valid JsonUtility JSON — a section with a null/blank `DisplayMetadata` is dropped with no
error anywhere the user can see.

**How to apply:** resolve a `FromJson<T>`/generic call's real type argument from the methodSpec's
generic inst (`MetadataRegistration` `_mr[2]/_mr[3]`) rather than trusting a nearby `TypeInfo` slot —
the nearby one here was a different type.

## Per-page-source consumers (checked 2026-08-19)

The wire shape is identical for every page source; what differs is the consumer, and specifically
which `BaseDiscoveryDisplayMetadata` subclass parses `DisplayMetadata`. **Only two subclasses exist
in the entire client** — everything else uses plain `DiscoveryDisplayMetadata`:

| page source | consumer | DisplayMetadata type |
| --- | --- | --- |
| `StoreCategories` | `RRUI.Data.CategorizedStoreModel` | `StorePageDiscoveryDisplayMetadata` (+ `itemsToContributeToDeduping`, `itemsToDedupe`, `tagList`, `categoryDepth`, `categoryIconSprite`, `categoryUriNames`, `HideSkuInfoOnCards`) |
| `PlayMenuTabs` | `RRUI.Data.PlayMenuTabsModel` + `PlayMenuTabsModelController` | `TabsDiscoveryDisplayMetadata` (+ `HideIfEmpty` bool, `SearchType` enum) |
| everything else | generic discovery-section models | plain `DiscoveryDisplayMetadata` |

`SearchType`: None 0, Button 1, BarWithChips 2, BarWithoutChips 3.

**`PlayMenuTabs` has a second, harder gate.**
`PlayMenuTabsModelController.TabDiscoverySectionSpawnerImpl` holds a Unity-serialized
`DiscoverySectionPrefabMapping[]` whose entries are
`{ JBCDFKPPEML DiscoveryEntityType; string Source; PlayMenuTabView Prefab; Route DestinationRoute; }`.
Each returned section is matched on the **`(SectionType, Source)` pair**; a pair with no mapping
renders **no tab, silently**. That table is serialized asset data, not code, so the valid pairs live
in the prefabs under `Recroom_Release_Data`, not in `GameAssembly.dll` — extracting it needs an asset
dump, not the carve.

**`PlayHighlight` (enum value 1) has no consumer in code at all.** It is declared in `GAEJAGAGEHB`
and never referenced outside the enum. Since page sources can also be selected by a serialized
`discoveryPageSource` field, a prefab could still request it — but nothing in the binary handles it
specially, so it would fall through to the generic path with plain `DiscoveryDisplayMetadata`.

## `SourceMetadata` has no enum — and PlayMenuTabs never reads it

Checked **2026-08-20**. `SourceMetadata` is a plain `string?` (field 0x28) and **nothing parses it as
an enum** anywhere. The enum-like field is **`Source`**: it carries a fixed vocabulary of string
literals (`"CuratedList"`, `"PageSource"` in the store path), and `SourceMetadata` is just the
*argument* whose meaning depends on which `Source` was named — a curated-list id for `CuratedList`,
a page-source name for `PageSource`.

For **PlayMenuTabs**, tab selection ignores `SourceMetadata` entirely. The two predicates in
`PlayMenuTabsModelController.TabDiscoverySectionSpawnerImpl` are:

- `AKFJBEGHMON` (`0x28451B0`) — exact: `dto.SectionType == mapping.DiscoveryEntityType &&`
  `String.op_Equality(mapping.Source, dto.Source)` (reads DTO fields 0x18 and **0x20**)
- `IJHIENBFHME` (`0x2845200`) — **wildcard fallback**: `dto.SectionType == mapping.DiscoveryEntityType &&`
  `String.IsNullOrEmpty(mapping.Source)`, i.e. a mapping with a blank `Source` matches any section of
  that type

Neither touches 0x28. The spawner `NCAKMAAMIIH` (`0x285FD30`) reads `Source` (0x20) and
`DisplayMetadata` (0x30) but never 0x28 either.

Consequence: for tabs, both the accepted `SectionType` values **and** the accepted `Source` strings
live in the serialized `DiscoverySectionPrefabMapping[]` asset, not in code — they cannot be
enumerated from the carve.

## `Source` does have an enum — `{None, PageSource, CuratedList}`

Found **2026-08-20** by scanning metadata typeDefinitions for enums containing a member named
`CuratedList`/`PageSource`. Two mirrored declarations, identical members, values 0/1/2:

- `RoomCategoriesListModel.GGHOOPIIGFD` (Assembly-CSharp; `Set(GGHOOPIIGFD source, string, string, string)`)
- `RoomCategoryListViewModel.Sources` (RecRoom.AppUI.Runtime) — **unobfuscated**

The wire value is the member **name as a string**, which is why `CategorizedStoreModel` compares
`dto.Source` against the literals `"CuratedList"` and `"PageSource"` rather than parsing an int.

**Do not mix this up with the other `Source` vocabularies** — several unrelated enums also contain
`CuratedList`, and they belong to different systems:

| enum | context | members |
| --- | --- | --- |
| `GGHOOPIIGFD` / `Sources` | **discovery sections** | None, PageSource, CuratedList |
| `LMHEAJIDAJJ` | algorithmic lists | None, AlgorithmicList, CuratedList |
| `EPJOCKOBIJM` | portfolio | Portfolio, Featured, Search, AlgorithmicList, CuratedList |
| `DAMKPLKFBHC` | store item lists | Store, AdCarousel, Wishlist, TopToday, AlgorithmicList, Storefront, ServerSearch, CAIAlgorithmicList, CuratedList, UnifiedAlgorithmicList, UnifiedCuratedList, UnifiedCrossTypeSimilarEntities, None, CustomAvatarItemCuratedList, CustomAvatarItemPortfolio, CustomAvatarItemFeatured, Roomie |
| `AccountListQueryType` | account lists | 14 members incl. CuratedList |
| `ILKEIEBOKBL` | inventions | 13 members incl. CuratedList |

The store-item-list set is stringified by `LMHBMKDLJKC.GetLegacySourceStringFromQueryData`
(`0x2471460`), which emits 12 of those names — useful if you are serving store list telemetry, but
**not** the `Source` field of a discovery section.

Caveat for **PlayMenuTabs**: its matcher compares `dto.Source` against a string authored in the
serialized `DiscoverySectionPrefabMapping[]`, so its accepted values are asset-defined and not
necessarily limited to the three above.


## StoreItemsSection (4): `Source` is a `DAMKPLKFBHC` member NAME, `SourceMetadata` is the endpoint

Derived **2026-08-27**. For `SectionType == 4` the store path calls
`StoreCarouselListModel.TryGetCarouselInfoFromSectionDTO` `0xB46DE0`, which:

1. maps `SectionType` -> carousel kind through a serialized
   `Dictionary<JBCDFKPPEML, FNOEBGCAGPO>` on the model (`FNOEBGCAGPO`: `StoreItemCarousel 0`,
   `CustomAvatarItemCarousel 1`, `AdCarousel 2`, `SkuCarousel 3`, `InventionCarousel 4`,
   `DataBoundStoreItemCarousel 5`, `DataBoundCustomAvatarItemCarousel 6`);
2. calls `NMFAELCJNAO(carouselKind, dto.Source, out NFNBPBNALAD)` `0xB465E0`, which is a
   **`System.Enum.TryParse` switched on carousel kind** over five enums -
   `DAMKPLKFBHC` (store items), `DIPFIKKHLOK`, `EPJOCKOBIJM` (portfolio), `ILKEIEBOKBL` (inventions),
   `KOHBBGBFHLE`. So **`Source` is the enum member name as a string**, not a free-form value;
3. copies `dto.SourceMetadata` (0x28) into the carousel info, which becomes
   `RecRoom.AppUI.Data.StoreItemListQueryData.endpoint` (field names there are unobfuscated:
   `source`, `staticSource`, `dynamicSource`, `searchQuery`, `accountId`, `storefrontType`,
   `adCarouselItemId`, **`endpoint`**, `crossTypeSimilarEntitySeedId/Type`, `displayName`,
   `maxItemsToDisplay`, `includeRankingContext`).

`DAMKPLKFBHC` (the store-item `Source` vocabulary): `Store 0`, `AdCarousel 1`, `Wishlist 2`,
`TopToday 3`, **`AlgorithmicList 4`**, `Storefront 5`, `ServerSearch 6`, **`CAIAlgorithmicList 7`**,
`CuratedList 8`, **`UnifiedAlgorithmicList 9`**, `UnifiedCuratedList 10`,
`UnifiedCrossTypeSimilarEntities 11`, `None 12`, `CustomAvatarItemCuratedList 13`,
`CustomAvatarItemPortfolio 14`, `CustomAvatarItemFeatured 15`, `Roomie 16`.

**The algorithmic `Source` values and the `type=` they send** ([algorithmiclists-type5-unified-id](algorithmiclists-type5-unified-id.md)):

| `Source` | client calls | ids in `Entities[].Id` |
|---|---|---|
| `UnifiedAlgorithmicList` | `algorithmiclists/{SourceMetadata}?type=5` | `"0.<int>"` / `"1.<guid>"` |
| `AlgorithmicList` | `?type=4` (PurchasableItems) | plain int |
| `CAIAlgorithmicList` | `?type=3` (CustomAvatarItems) | plain guid |

So `SourceMetadata` is exactly the free-form serving-endpoint segment (e.g. `accessoriesitems`,
`newitems`) that `algorithmiclists/{name}` uses. Related runtime enums:
`StoreItemListQuerySources` (`None 0, Search 1, Wishlist 2, StaticSource 3, DynamicSource 4, Roomie 5`),
`StaticSources` (`None 0, Storefront 1, AdCarousel 2, CustomAvatarPortfolio 3, CustomAvatarFeatured 4`),
`DynamicSources` (`None 0, AlgorithmicList 1, CustomAvatarItemAlgorithmicList 2,
UnifiedAlgorithmicList 3, UnifiedCuratedList 4, CustomAvatarItemCuratedList 5,
UnifiedCrossTypeSimilarEntities 6`).

## `IsSupported()` defaults are all permissive - omit the gating fields

`BaseDiscoveryDisplayMetadata.get_IsSupported` `0x7ED9320`: both age checks are `jle`-guarded
(`0x7ED96FC` on `accountAgeMinDays` 0x3C, `0x7ED971B` on `accountAgeMaxDays` 0x40), so **0 disables
them**; `excludeJuniors` (0x38) and `excludeJuniorsWithoutCreatePermissions` (0x39) are only
evaluated when true. A `DisplayMetadata` that omits all six base fields passes.

## Page sources: `StoreCategories` vs the rest

`GAEJAGAGEHB` (page-source enum, used via `Enum.ToString()`): `WatchHome 0`, `PlayHighlight 1`,
`CommunityBoard 2`, `MobileHome 3`, `StoreFeatured 4`, `StoreClothing 5`, `StoreConsumables 6`,
`PlayCategories 7`, `StoreInventions 8`, `TitleScreen 9`, `PlayMenuTabs 10`,
`OrientationStoreFeatured 11`, `AppNavPortalPanel 12`, `WWPanelList 13`, `RecRoomPlusBenefits 14`,
`RecCenterStorefront 15`, `RecCenterCommunityContent 16`, `None 999`.

`StoreCategories` is a raw string id (not in the enum) consumed by `CategorizedStoreModel`;
`StoreFeatured` / `StoreClothing` / `StoreConsumables` / `StoreInventions` bind to
`StoreCarouselListModel` via its serialized `DiscoveryPageSourceName`. Both paths funnel into
`TryGetCarouselInfoFromSectionDTO` and therefore both parse `DisplayMetadata` as
`StorePageDiscoveryDisplayMetadata` - **the wire shape and DisplayMetadata type are the same for all
four**; only `StoreCategories` additionally accepts `SectionType 13`.
