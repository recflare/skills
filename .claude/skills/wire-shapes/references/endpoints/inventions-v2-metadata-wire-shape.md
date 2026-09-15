# Inventions v2 metadata wire shape

> PUT api/inventions/v2/metadata (svc 2 API) returns the SAME enveloped {Value:{Status,Invention,InventionVersion,TagsResponse},Success,Error,error_id} as v9/save, but is STRICTER: on Success=true both Value AND Value.Invention must be non-null or the client NREs.

Derived **2026-08-29** from build `20250718.01` via [recflare-2025-metadata-carve](../../../il2cpp-analysis/references/recflare-2025-metadata-carve.md).
Companion to [inventions-v9-save-wire-shape](inventions-v9-save-wire-shape.md) — **identical response type**, different strictness.

`PUT https://api.<host>/api/inventions/v2/metadata` — service **2 = API**
([recnet-service-enum](../conventions/recnet-service-enum.md)), verb **PUT** (`HttpMethod` statics `+0x28`; the send site reads
`[statics+0x28]` at `0x7CEC883`). Literal `0xD135938`. No query params.

Client entry `GLAKFFIIDPF.JBJNDLNCILI(long inventionId, string name, string description,
string longDescription, string imageName, List<string> autoTags, List<string> customTags)`
**`0x7CEC540`** → `KPIPLFECKNC<FFOENOGPGNH<GCLKCLFIPED>>`.

Three thin wrappers post the same route with one field set: `IPEPBIPMECB(id, name)` `0x7CEBE00`,
`LIMKCLBAJGJ(id, description)` `0x7CEDE30`, `DHPIKLGJAOM(id, imageName)` `0x7CE8FC0`.

**Request body** = `RecNet.UpdateInventionMetadataRequest` (unobfuscated, 6 keys) via
`MGPBDIAGCFD.ELKIBCPINAP` (inst 14956): `InventionId` long, `Name`, `Description`,
`LongDescription`, `ImageName` strings, `TagsRequest` = `RecNet.ModifyTagsRequest`
`{AutoTags: [string], CustomTags: [string]}`.

## Response — same envelope and Value as v9/save

Send generic `MGPBDIAGCFD.HPBKMCLEANE<KGOJLHJNIOD<GCLKCLFIPED>>` — **generic inst 1001, the exact
same instantiation as [inventions-v9-save-wire-shape](inventions-v9-save-wire-shape.md)**. So every key, type, formatter and enum in
that note applies verbatim: envelope `{Value, Success, Error, error_id}` (`+0x10 Success`,
`+0x18 Error`, `+0x20 error_id`, `+0x28 Value`) wrapping `GCLKCLFIPED`
`{Status, Invention, InventionVersion, TagsResponse}`.

```json
{"Value":{"Status":0,"Invention":{ …28 keys… },"InventionVersion":null,"TagsResponse":null},
 "Success":true,"Error":null,"error_id":null}
```

## Stricter than v9/save — `Invention` is mandatory on success

Consumers:

1. `ACDIFEDIGIO.CNDLLDHCBGF(envelope)` **`0x7D04CC0`** (the `.Then` registered inside
   `JBJNDLNCILI`; the display class holds `long inventionId`):
   - envelope null → **NRE** (`0x7D04D13`)
   - `Success == false` → returns quietly, nothing else happens
   - `Success == true`: `NNMGBLLLIAH.BMICOFMDHAB(2, …)` cache-invalidate, then
     `Value` null → **NRE** (`0x7D04D83`), then
     `GLAKFFIIDPF.MOMMBDIHDCI(Value.Invention)` `0x7CEEEC0`, which **null-checks its arg and throws
     NRE** (`0x7CEEEE8`) before reading `InventionId` — so **`Value.Invention` is mandatory**.
     Then `LLMDAMLHLGB(this.inventionId)` and a static event fire.
2. `MKIILBHCHHO.MoveNext` `0x1ADA140` (await at `0x1ADA275`):
   - result null → NRE; `Success == false` → takes `Error` (`[rax+0x18]`) into a failure result
   - `Success == true` → `Value` null → NRE (`0x1ADA387`), `Value.Invention` null → NRE
     (`0x1ADA394`), then reads `Invention.InventionId` and `DBNNIBCEIJE.LIPDJEFPIMJ(Invention)`.
3. `NOKJPNELNDB.MoveNext` `0x7D14A10` awaits and **discards the result entirely** — inspects nothing.

**`Status` is never read on this route either** (same as v9/save) — `Success` + `Error` is the
failure channel. `InventionVersion` and `TagsResponse` are deserialised and unused, so `null` is
fine for both.

**How to apply:** on success echo the full updated invention —
`{"Success":true,"Value":{"Status":0,"Invention":{…}}}`. Returning `Success:true` with a null
`Value` *or* a null `Value.Invention` is a hard NRE here (v9/save tolerated a null `Invention`;
this route does not). On failure `{"Success":false,"Error":"<message>","Value":null}` is safe.
