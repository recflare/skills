# Roomkeys v1 owns/bulk wire shape

> POST api/roomkeys/v1/owns/bulk (svc 28 Econ) takes a JSON ARRAY of {AccountId, RoomKeyId} and returns a BARE ARRAY of {AccountId, RoomKeyId, DoesPlayerOwnRoomKey} — no envelopes, unlike its awardbulk sibling. Note AccountId comes FIRST here and RoomKeyId first on awardbulk.

Derived **2026-10-01** from build `20250718.01`.
Siblings: [roomkeys-v1-awardbulk](roomkeys-v1-awardbulk-wire-shape.md), [roomkeys-v1-create](roomkeys-v1-create-wire-shape.md),
[roomkeys-v1-room](roomkeys-v1-room-wire-shape.md).

`POST https://econ.<host>/api/roomkeys/v1/owns/bulk` — service **28 = Econ**
(`mov dword ptr [rdi+0x18], 0x1c` at `0x7D9CE97`), verb **POST** (`HttpMethod` statics `[rcx+0x20]`
at `0x7D9CE5A`). Whole-route literal, slot `0xD150120`.

The route lives in the async state machine `MLBGAFDPMNL$$MoveNext` **`0x7D9CD30`**; the request-item
adapter is `LHMONGGMNAI.AMIFCGCJLOP` `0x7D95DF0` (0 direct call sites — inlined, so do not try to
reach it with `callxref`).

## Request — JSON array of 2-key items

Body via `MGPBDIAGCFD.ELKIBCPINAP`, generic inst **#14082** = `.LBOPEMMJOCA`. That the body is an
**array** is direct evidence, not inference: the Utf8Json serializer is instantiated over
**`IReadOnlyList<LBOPEMMJOCA>`** (methodSpec 904545, `GEMFFEGOJPC::MDKDDHDGDJK`).

Formatter `BKKLJDLPGMM` `.ctor 0x76A6700`, key run `0x76A697D` / `0x76A69D4` — 2 keys, 1:1 with the 2
fields:

| # | key | CLR | off |
|---|---|---|---|
| 1 | `AccountId` | **int** | 0x10 |
| 2 | `RoomKeyId` | long | 0x18 |

```json
[ { "AccountId": 205, "RoomKeyId": 900001 } ]
```

## Response — BARE ARRAY, no envelopes

`MGPBDIAGCFD.HPBKMCLEANE<T>`, generic inst **#2720** = **`List<HGENLKNBPFI>`**. A plain array —
**no per-item envelope**, which is the opposite of [roomkeys-v1-awardbulk](roomkeys-v1-awardbulk-wire-shape.md)'s
`List<KGOJLHJNIOD<…>>`. Two bulk routes on one facade, two different response tiers.

Element `.HGENLKNBPFI` (typedef #22869), formatter `MJDCNBKEFHE` `.ctor 0x76B5AB0`, key run
`0x76B5E12` / `0x76B5E69` / `0x76B5EB4` — 3 keys, 1:1 with the 3 fields:

| # | key | CLR | off |
|---|---|---|---|
| 1 | `AccountId` | **int** | 0x10 |
| 2 | `RoomKeyId` | long | 0x18 |
| 3 | `DoesPlayerOwnRoomKey` | bool | 0x20 |

```json
[ { "AccountId": 205, "RoomKeyId": 900001, "DoesPlayerOwnRoomKey": true } ]
```

`{}` or an empty body throws `IONCMJIACFI`; serve `[]`. Echo `AccountId`/`RoomKeyId` back on every
element — they are what attributes each answer to a request item.

⚠️ **`DoesPlayerOwnRoomKey` is a bool and defaults to `false` when omitted**, which is the safe
direction (no false grant), unlike the enums elsewhere in this facade whose `0` is permissive.

## ⚠️ Key ORDER differs from awardbulk

Both bulk routes carry the same id pair, in the opposite order, and under different field names
internally:

| route | item keys | field names |
|---|---|---|
| `/v1/awardbulk` | `RoomKeyId` (long), `AccountId` (int) | `<BPMDDMBIACG>k__BackingField`, `<GIMCDKIBOHE>k__BackingField` — auto-properties |
| `/v1/owns/bulk` | `AccountId` (int), `RoomKeyId` (long) | `PMFGNEEOBOM`, `FGIKEPFFAFO` — **plain public fields**, no backing-field wrapper |

Utf8Json accepts keys in any order, so a server reading these does not have to care — but the two
DTOs are genuinely distinct types and **their shapes must not be shared in server code**: `owns/bulk`
adds the bool, `awardbulk` wraps each result in an envelope.

## Validation

Both `LBOPEMMJOCA.CPOBHIECLEN` and `HGENLKNBPFI.CPOBHIECLEN` are the shared no-op `0xA60520` — no
post-deserialize validation, every key omittable. There is **no batcher** on this route (no
`HBDOGOHIEDF` instantiation over either type), so unlike awardbulk the item count is whatever the
caller passed, not a debounce artefact.
