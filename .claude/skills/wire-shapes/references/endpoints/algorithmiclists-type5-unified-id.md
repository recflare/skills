# Algorithmiclists type5 unified id

> algorithmiclists/{name}?type=5 (Generic) is the UNIFIED store path — each Entities[].Id must be a unified item id '0.<int>' (PurchasableItem) or '1.<guid>' (CustomAvatarItem); an unparseable Id is silently skipped.

Derived **2026-08-24** from build `20250718.01` via [recflare-2025-metadata-carve](../../../il2cpp-analysis/references/recflare-2025-metadata-carve.md).
Extends [algorithmiclists-wire-shape](algorithmiclists-wire-shape.md) (which has the envelope-free `{Type, Entities:[{Id, Context}]}`
body and the `KJMOLELGPPF` type enum).

**The `type` query param, not the path segment, decides what `Id` means.** The serving-endpoint
segment (`newitems`, `HotList`, …) is a free-form string parameter — `'newitems'` is **not** a literal
in `GameAssembly.dll`, so it comes from a discovery-section config, and the client has no opinion
about it. What the client *does* branch on is which caller issued the request:

| caller | `mov dl,` | `type` |
|---|---|---|
| `StoreItemQueryManager.GetUnifiedItemIdsFromUnifiedAlgorithmicList` `0x7EF7210` | `5` | Generic |
| `…FromPurchasableAlgorithmicList` `0x7EFF710` | `4` | PurchasableItems |
| `…FromCustomAvatarItemAlgorithmicList` `0x7EFEA80` | `3` | CustomAvatarItems |
| `RoomQueryManager.GetRoomsFromAlgorithmicListDto` `0x7EE4120` | | Rooms (1) |

So **`type=5` is only ever the unified store path**, and each `Id` is fed to
`DFKJCABFMCH.AGIMFBCEFJB` `0x7621920` (`TryParse` for the unified item id struct):

```
s.Split('.')                      -> must yield EXACTLY 2 parts (one dot)
Int32.TryParse(parts[0])          -> a NUMBER, and Enum.IsDefined(NNIJHHALHAM, n)
                                     NNIJHHALHAM: PurchasableItem = 0, CustomAvatarItem = 1
n == 0 -> Int32.TryParse(parts[1])
n == 1 -> Guid.TryParse(parts[1])
```

```json
{ "Type": 5, "Entities": [
  { "Id": "0.1234", "Context": null },
  { "Id": "1.6da89ddf-f2e5-4c32-8b22-feb687683e36", "Context": null } ] }
```

**Trap:** `DFKJCABFMCH.ToString()` `0x7622690` formats `"{0}.{1}"` with the enum **name**
(`"PurchasableItem.1234"`), which the parser **rejects** — it requires the numeric form. Do not
mirror the ToString shape onto the wire.

**Failure modes in the consumer** (`<GetUnifiedItemIdsFromUnifiedAlgorithmicList>d__34$$MoveNext`
`0x7EFFD00`):
- **An unparseable `Id` is silently skipped** — `0x7F0004F: test al, al ; je <loop top>`. No log, no
  error; the section just renders short or empty. This is the failure to suspect when a store row
  comes back 200 OK and shows nothing.
- **A null response body or a null `Entities` throws** (`je 0x7F00271` / `je 0x7F0026C`).
- An **empty** `Entities` array is fine — the count check short-circuits to an empty result.
- No branch on the echoed `Type` was found in this consumer.
- `Context` is an optional string, consumed by `StoreItemQueryManager.PopulateRankingContextDictionary`
  `0x7EF7530` for ranking telemetry only.

## Hydration: there is NO second endpoint

`GetStoreItemsFromUnifiedAlgorithmicList` `0x7EF6910` just awaits the id list above and then calls
interface `NDFKHFMKMJC` **slot 4** = `MBNLJPBLFAF.MGGJKDCNBFB(IReadOnlyList<DFKJCABFMCH>, bool)`
`0x89E0D10` (dispatch at `0x7EFD28B`, `ecx=4`, bool arg `0`). Its state machine `CNHPBNPPIPD$$MoveNext`
`0x89D9BE0` contains **zero string literals** — no URL. Its capture fields keep their
compiler-generated (unobfuscated) names and tell the whole story:

```
unifiedItemIds / convertCustomAvatarItemsToPurchasableGiftDrops
<watchStorefrontTask>5__2 / <customAvatarItems>5__3 / <storeItemsInInitialOrder>5__4
```

It awaits the **already-loaded storefront**, fetches the custom-avatar items, then combines via
`FOCMOPJCIFH(ids, IReadOnlyList<GBEBEEFLKJP> storefrontItems, IReadOnlyList<HCJBFOICEDA> customAvatarStoreItems)`.
`storeItemsInInitialOrder` = **the order you return in `Entities` is preserved**.

Single-id resolution `MBNLJPBLFAF.DAHPAENLOOP(DFKJCABFMCH)` `0x89DEBA0`:
- `itemType == 1` → `NEFFDKAPOGB()` (Guid) → `BPOHJCLPKAF(Guid)` lookup
- `itemType == 0` → `EDHFOJHBHFL()` (int) → **Dictionary<int, …> lookup on the storefront cache**
- anything else → **returns null**

So a `"0.<int>"` only resolves if that int is **already in the storefront the client loaded**.
Nothing 404s or errors — the item is just missing from the row.

## Two parsers, two accepted formats

| method | format | callers |
|---|---|---|
| `AGIMFBCEFJB` `0x7621920` | **prefixed** `0.<int>` / `1.<guid>` | `GetUnifiedItemIdsFromUnifiedAlgorithmicList`, `…FromUnifiedCuratedList`, `…ForCrossTypeSimilarEntities`, `<SearchItems>d__29`, +2 |
| `CLPJEPLGGMP` `0x7621DB0` | **bare** `<int>` or `<guid>`, type inferred from shape | one caller (`JKOBMGINHDJ.NIGEDCJADML`) |

So the prefixed form also governs **curated-list `ItemIds`** ([curatedlists-bulk-wire-shape](curatedlists-bulk-wire-shape.md)) and
`algorithmiclists/crosstypesimilarentities` — not just this route.

Other `DFKJCABFMCH` members: `NEFFDKAPOGB() -> Guid`, `EDHFOJHBHFL() -> int`,
`GLPKCDEEOPA(string, out NNIJHHALHAM)`, factories `FMBMEMANPCJ(int)` / `EACHPKJGNBC(Guid)`,
`.ctor(NNIJHHALHAM, int?, Guid?)`.
