# Rooms autocomplete search wire shape

> Wire shape of GET rooms/autocomplete_search on the Rooms service for recflare-2025 — a bare JSON array of plain strings, no objects.

Derived **2026-08-18** from `C:\Games\recflare-2025` (build `20250718.01`) via
[recflare-2025-metadata-carve](../../../il2cpp-analysis/references/recflare-2025-metadata-carve.md).

`GET https://rooms.<host>/rooms/autocomplete_search?query={string}&take={int}&searchSessionId={guid}`
— **GET** (`HttpMethod` statics `+0x08`), no body. Client entry
`OALMDGJKBJH.FGCECPJGIEN(string query, int take, Guid? searchSessionId, CancellationToken)` at
`0x7DF8CD0`; the three query params are added by the closure `HIEGPENPILD.PBKCFHCKEJG`
(`0x7DEC4E0`) via `MGPBDIAGCFD.ELHKHFJEHLM`. `searchSessionId` is `Guid?` — omitted entirely when
null, not sent empty.

**Response is a bare JSON array of plain strings** — `TResponse = List<string>` (confirmed from the
`LMKONLJOAEP` methodSpec inst 1028 and the Cpp2IL signature `Task<List<string>>`). Not objects, not
an envelope:

```json
["rec room", "rec royale", "recording studio", "rec center"]
```

At most `take` entries. There is no DTO, so there is **no post-deserialize hook and no validation
at all** — the array elements are the suggestion text used directly.

An alternate wrapper `KCHDMOJGHJD.PAGLCJMNHHP(string query, int take = 5, Guid? searchSessionId)`
(`0x7DDCB00`) returns `IReadOnlyList<string>` and uses the path-template literal
`"autocomplete_search/{0}&take={1}"` — note the `&` with no `?`, which looks malformed but is just
a builder string; same bare-string-array shape either way.

**Why:** every other Rooms endpoint returns room objects, so the instinct is to return
`MIBODHPEFHP` records here (see [rooms-contributedby-wire-shape](rooms-contributedby-wire-shape.md)). This one is query-suggestion
*text* only — the client re-searches with the chosen string.

**How to apply:** the related telemetry literals `autoCompleteQueryId`, `autoCompleteRank`,
`autocomplete_impression` are client-side analytics fields, not part of this response.
