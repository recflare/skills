# Outfits bulk wire shape

> POST api/outfits/bulk (svc 2 API) — body {AccountIds, UnityAssetTarget, UnityAssetVersion}; response is a BARE object with ONE key OutfitsByAccountId, a MAP of accountId -> the 8-key outfit DTO (not an array).

Derived **2026-08-24** from build `20250718.01` via [recflare-2025-metadata-carve](../../../il2cpp-analysis/references/recflare-2025-metadata-carve.md).
Shares its element DTO with [outfits-me-saved-wire-shape](outfits-me-saved-wire-shape.md) and [outfits-me-put-wire-shape](outfits-me-put-wire-shape.md).

`POST https://api.<host>/outfits/bulk` — service **2 = API** (`mov r8d, 2`), verb **POST**
(`HttpMethod` statics `+0x20`), **no query params**. State machine `NIPKIBBDAFD$$MoveNext`
`0x7D63890`; literal `'outfits/bulk'` `0xD25AD20`.

**Request body** (JSON, via `ELKIBCPINAP<CONLNOOBMMD>`) — formatter `NNNFCELHPJI` `.ctor 0x76CE450`,
3 keys in declaration order:

| key | CLR |
|---|---|
| `AccountIds` | `List<int>` |
| `UnityAssetTarget` | `byte?` |
| `UnityAssetVersion` | `int?` |

**Response — a BARE object with exactly one key, and its value is a MAP, not an array.**
`HPBKMCLEANE<PMKLGLGAELO>`; formatter `BKBCFCDMOII` `.ctor 0x76BEA60`, single key
`OutfitsByAccountId` = `Dictionary<int, KPPNBDELPNB>` (Utf8Json writes int keys as JSON strings):

```json
{ "OutfitsByAccountId": {
    "220": { "DataVersion": 0, "LegacyData": {…}, "CustomizationSettings": "…",
             "Selections": [], "Slot": 0, "Name": "", "Accessibility": 1,
             "ThumbnailFileName": null } } }
```

`KPPNBDELPNB` is the **same 8-key outfit DTO** as `GET/PUT outfits/me` and `outfits/me/saved` — see
[outfits-me-saved-wire-shape](outfits-me-saved-wire-shape.md) for its keys and the `Accessibility` enum.

**No validation** — `PMKLGLGAELO.CPOBHIECLEN` and `CONLNOOBMMD.CPOBHIECLEN` are both the `0xA60520`
no-op.

**The client iterates the requested `AccountIds`, not the map.** The result is built by
`Select(accountIds, id => new KJNCFCMCNHA(id, response.OutfitsByAccountId[id]))`
(`MGKMLGFMMGB.JLPNDNEBFHL` `0x7D60660`) → `List<KJNCFCMCNHA>` where `KJNCFCMCNHA = {int, KPPNBDELPNB}`.
So the output always has one entry per **requested** id regardless of what the map contains.
The lookup pre-zeroes its out slot and has no throw path after the call, so a **missing key yields a
null outfit rather than an exception** — but `response` itself being null *does* throw
(`0x7D606AB`). Safest: return an entry for every requested id.

**Trap:** the client method's return type is `Task<List<KJNCFCMCNHA>>`, which reads like an array
endpoint. It is not the wire type — see the rule in [platformnotifications-wire-shapes](platformnotifications-wire-shapes.md): always
resolve `T` from the `HPBKMCLEANE<T>` generic instantiation.
