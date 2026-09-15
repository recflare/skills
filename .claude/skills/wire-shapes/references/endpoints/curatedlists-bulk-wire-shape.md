# Curatedlists bulk wire shape

> Wire shape of GET curatedlists/bulk?id= on the Lists service (svc 13) for recflare-2025 — a bare array of 8-key curated-list objects, no envelope.

Derived **2026-08-17** from `C:\Games\recflare-2025` (build `20250718.01`) via
[recflare-2025-metadata-carve](../../../il2cpp-analysis/references/recflare-2025-metadata-carve.md).

`GET https://lists.<host>/curatedlists/bulk?id=<long>` — `id` repeats, one per requested list.
Service enum 13 (Lists). Client batches ids; at **100 or more** ids it switches to the other
`HttpMethod` static (the `cmp eax, 0x64` branch in `OBENNBMFBDA$$MoveNext`, RVA `0x7E3A940`).

Response is a **bare JSON array** — *no* `{success, error, value}` envelope. Proof: RecNet's list
envelope `GJAFHDAFBNE<T>` has a generated Utf8Json formatter for 12 other DTOs but **none** for the
curated-list DTO, and the client deserialises straight to `List<OOCDKDLBGOI>`.

Element keys, in `____stringByteKeys` order, with the field offset that confirms each pairing:

| key | CLR | offset |
|---|---|---|
| `ListId` | long | 0x10 |
| `CreatorAccountId` | int | 0x18 |
| `Name` | string | 0x20 |
| `Description` | string (nullable) | 0x28 |
| `ImageName` | string | 0x30 |
| `Type` | byte enum | 0x38 |
| `ItemIds` | IReadOnlyList\<string\> | 0x40 |
| `CreatedAt` | DateTime | 0x48 |

`Type` enum `KJMOLELGPPF : byte` — Accounts 0, Rooms 1, Inventions 2, CustomAvatarItems 3,
PurchasableItems 4, Generic 5, ChipAndPort 6, DiscoverySection 7, DiscoverySectionSubType 8. It is
emitted **numerically** — settled 2026-08-17: no by-name enum formatter exists on this build, see
[recflare-2025-metadata-carve](../../../il2cpp-analysis/references/recflare-2025-metadata-carve.md).

Utf8Json accepts three casings per key (`ListId`/`listId`/`listid`). The post-deserialize hook is
RVA `0xA60520`, the shared no-op stub (4,877 methods fold onto it) — **no validation**, so a wrong
body fails silently as nulls rather than throwing.

Results are re-keyed to the requested ids through a `Func<TResult, TId>` selector on the batcher
`IMAGJAIKIPF<long, OOCDKDLBGOI>`, so **order does not matter** but each object's `ListId` must equal
a requested id; an id with no object simply resolves to absent.

**Why:** the obfuscated property names (`OFDEDCPAMLM`, …) are NOT the wire names and this DTO carries
no `[DataMember]`, so the keys exist only as literals inside the generated formatter — recoverable
only after the carve.

**How to apply:** the same technique reads any other DTO on this build — find the formatter's `.ctor`
RVA, then decode its kind-5 usage slots; the trailing run of one-per-member keys is
`____stringByteKeys` in declaration order.
