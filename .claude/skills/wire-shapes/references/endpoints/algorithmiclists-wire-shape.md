# Algorithmiclists wire shape

> Wire shape of GET algorithmiclists/{name}?type= on the Lists service (svc 13) for recflare-2025 — a bare {Type, Entities:[{Id, Context}]} object.

Derived **2026-08-17** from `C:\Games\recflare-2025` (build `20250718.01`) via
[recflare-2025-metadata-carve](../../../il2cpp-analysis/references/recflare-2025-metadata-carve.md). Sibling of [curatedlists-bulk-wire-shape](curatedlists-bulk-wire-shape.md) on the same service.

`GET https://lists.<host>/algorithmiclists/{servingEndpoint}?type={int}` — **GET**
(`HttpMethod` statics `+0x08`). The path is `String.Concat("algorithmiclists/", servingEndpoint)`, so
the trailing segment is a free-form serving-endpoint name (`HotList`, and elsewhere
`UnifiedAlgorithmicList` / `AlgorithmicList` / `CAIAlgorithmicList`); sibling fixed paths are
`algorithmiclists/search`, `/recommendednext`, `/similarentities`, `/crosstypesimilarentities`.
Client entry `FCKNCPNDBBM.FOHODDJAAMP(string servingEndpoint, KJMOLELGPPF type, CancellationToken)`
(`0x7E223F0`), state machine `JDAKDHGKCAD$$MoveNext` (`0x7E2B690`).

`type` is added as a **query param** by the closure `NJBEJIGCNOP.DAHBOJJEDEO` (`0x7E39890`), boxed as
an I4 → numeric. Enum `KJMOLELGPPF : byte` — Accounts 0, Rooms 1, Inventions 2, CustomAvatarItems 3,
PurchasableItems 4, Generic 5, ChipAndPort 6, DiscoverySection 7, DiscoverySectionSubType 8. Same
enum as the curated-list `Type`.

Response `FCDCBEOPIPH` — **bare object, no envelope** (no formatter exists for any
`*<FCDCBEOPIPH>` envelope instantiation). Formatter `GCJFLBJIEPD` ctor `0x76F49C0`, keys
`Type` (the enum, echoed) and `Entities` (list). Each entity is `KMJIFOJIEHC` (formatter
`NABBKPCLNNA` ctor `0x7701E40`): `Id` string, `Context` string (nullable).

No required-field throw: `KMJIFOJIEHC.CPOBHIECLEN` is the `0xA60520` no-op, and
`FCDCBEOPIPH.CPOBHIECLEN` (`0x7CF92D0`) tail-jumps into the list-validate helper
`EADLCOCJAGD.IANBCAFGFNL`, which **returns false on a null list** rather than throwing.

**Why:** `Id` is a *string* even for room lists (type=1), matching curated lists' `ItemIds`
`IReadOnlyList<string>` — the whole Lists service keys entities as strings regardless of type.

**How to apply:** this endpoint is what definitively pinned `MGPBDIAGCFD.ELHKHFJEHLM` as the
**query-param** adder (it is the call that produces the `?type=` visible in the real URL);
`ODAJIJCEFDF` and `NLDEIEKIMEK` are its form/header siblings.
