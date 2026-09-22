# Econ customAvatarItems owned wire shape

> GET econ/customAvatarItems/v1/owned (svc 28 Econ — NOT the API host) is PAGED: it returns a bare {Results, TotalResults} wrapper around the same 20-key CustomAvatarItem (GICBMFJFHLI), unlike /v1/search which is a bare unpaged array.

Derived **2026-09-15** from build `20250718.01`.
Element DTO and the sibling API-host routes are in [customavataritems-routes](customavataritems-routes-wire-shapes.md);
this note covers the `econ/` family member it named but did not derive.

`GET https://econ.<host>/econ/customAvatarItems/v1/owned` — service **28 = Econ**
(`mov r8d, 0x1c` at `0x7C6B451`), verb **GET** (`HttpMethod` statics `[rcx+8]` at `0x7C6B42E`).
Client entry `LINCNKPIJDN.DOHIKHFAAMD(int skip, int take)` `0x7C6B2C0` (+0x420), error literal
`'Unable to get Custom Avatar Items owned by the for local player'` (sic).

⚠️ **Different host from its siblings.** `/v1/search`, `/v1/featured`, `/v1/bulk` and `POST /v1` are
service **2 = API** (`api.<host>`); the `econ/customAvatarItems/*` routes are service **28 = Econ**.
Same facade class `LINCNKPIJDN`, two different subdomains.

## Query params

Four, all via `ELHKHFJEHLM` and therefore (verb is GET) in the **query string**:
`skip`, `take`, `unityAssetTarget`, `unityAssetVersion`. The method signature takes only
`(skip, take)`; the two `unityAsset*` values come from client state.

## Response — BARE PAGED object

`HPBKMCLEANE<T>` generic inst `#14694` = **`.CGGCCPFAOHI`** — a bare object, no envelope.
`CGGCCPFAOHI` is the closed generic `FGLBCGIODIE<GICBMFJFHLI>`; **it declares no fields of its own**
(`fields2025` reports 0 — the members live on the generic base), so read the shape from the
formatter, not the field list. Formatter **`IJJHJOFBLLJ`** `.ctor 0x7E7F770` (+0x330), key run
`0x7E7F9AF..0x7E7FA06` — **2 keys**:

| # | key | CLR | off |
|---|---|---|---|
| 1 | `Results` | `IReadOnlyList<GICBMFJFHLI>` (generic inst #2667) | 0x10 |
| 2 | `TotalResults` | int | 0x18 |

```json
{ "Results": [ /* 20-key CustomAvatarItem, see customavataritems-routes */ ], "TotalResults": 0 }
```

`Results` elements are **the same `GICBMFJFHLI`** that `/v1/search` returns (class generic inst
`#2832`), so the 20-key table and its `CurrentSaves` / `PurchaseInfo` nesting carry over unchanged.

## This route IS paged — `/v1/search` is not

The contrast is worth stating because the two are otherwise interchangeable-looking:

| route | host | response |
|---|---|---|
| `/v1/search`, `/v1/featured`, `/v1/bulk` | API (svc 2) | **bare array**, no `TotalResults` |
| `econ/customAvatarItems/v1/owned` | **Econ (svc 28)** | **`{Results, TotalResults}`** |

So a server that reuses its `/search` handler here will return a bare array, the client will fail to
deserialize it into `CGGCCPFAOHI`, and the owned list reads as empty.

## Validation: send `Results: []`, never null

`CGGCCPFAOHI.CPOBHIECLEN` `0x7C56610` is **not** the shared no-op stub — it is a dedicated 0x40-byte
hook that loads `Results` (`[rbx+0x10]`) and tail-jumps to the list-validate helper
`EADLCOCJAGD.IANBCAFGFNL` `0x7623250`. That helper **returns false on a null list rather than
throwing** (same helper and behaviour as `FCDCBEOPIPH` in
[algorithmiclists](algorithmiclists-wire-shape.md)), so a null `Results` does not crash — it fails validation and the
response is treated as unusable. `[]` is the correct empty value.
