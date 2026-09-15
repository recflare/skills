# Inventions v4 publish wire shape

> POST api/inventions/v4/publish (svc 2 API) returns the same enveloped {Value:{Status,Invention,InventionVersion,TagsResponse},Success,Error,error_id} as v9/save; Value AND Value.Invention are mandatory when Success=true, Status is never read, and Error is shown to the user verbatim.

Derived **2026-08-29** from build `20250718.01` via [recflare-2025-metadata-carve](../../../il2cpp-analysis/references/recflare-2025-metadata-carve.md).
Third member of the family with [inventions-v9-save-wire-shape](inventions-v9-save-wire-shape.md) and
[inventions-v2-metadata-wire-shape](inventions-v2-metadata-wire-shape.md) — **all three return the identical response type**.

`POST https://api.<host>/api/inventions/v4/publish` — service **2 = API**
([recnet-service-enum](../conventions/recnet-service-enum.md)), verb **POST** (`HttpMethod` statics `+0x20`, read at `0x7CED846`).
Literal `0xD136EC8`. No query params.

Client entry `GLAKFFIIDPF.LEDGNKMCBBO(long inventionId, KGCKBAIOBNL permission,
KLKIFENPGNG accessibility, int? price)` **`0x7CED710`** → `KPIPLFECKNC<FFOENOGPGNH<GCLKCLFIPED>>`.

**Request body** = `RecNet.PublishInventionRequest` (unobfuscated, 4 keys) via
`MGPBDIAGCFD.ELKIBCPINAP` (inst 14946):
`{"InventionId": long, "Permission": KGCKBAIOBNL, "Accessibility": KLKIFENPGNG, "Price": int|null}`.

## Response — same envelope and Value as v9/save

Send generic `MGPBDIAGCFD.HPBKMCLEANE<KGOJLHJNIOD<GCLKCLFIPED>>` — **generic inst 1001 again**, so
every key, type, formatter and enum from [inventions-v9-save-wire-shape](inventions-v9-save-wire-shape.md) applies verbatim.

```json
{"Value":{"Status":0,"Invention":{ …28 keys… },"InventionVersion":null,"TagsResponse":null},
 "Success":true,"Error":null,"error_id":null}
```

## Consumers

1. `AKNHCOMGAFA.HKBHOBODOHP(envelope)` **`0x7D051E0`** — the `.Then` registered inside
   `LEDGNKMCBBO`; display class holds `long inventionId`:
   - envelope null → **NRE** (`0x7D0523F`)
   - `Success == false` → returns quietly
   - `Success == true`: `Value` null → **NRE** (`0x7D05256`); then
     `GLAKFFIIDPF.MOMMBDIHDCI(Value.Invention)` `0x7CEEEC0`, which **NREs on a null argument**
     (`0x7CEEEE8`) — so **`Value.Invention` is mandatory**, exactly as in
     [inventions-v2-metadata-wire-shape](inventions-v2-metadata-wire-shape.md). Then `List<long>.Remove(inventionId)` off an unpublished
     cache, `NNMGBLLLIAH.BMICOFMDHAB(2, …)` invalidate, and an event fires.
2. `MakerPenPaletteInventionPublishingScreen.CDEKKFEMBDD(result)` **`0xE42720`** (paired with the
   catch `HNBMOECBNIE(string)`; both `GJKIPJJGEON` `0xE42ED0` and `LEDGNKMCBBO` `0xE43540` on the
   screen register the same pair, after setting the "Publishing..." label):
   - `Success == false` → **`"Unable to publish invention: " + Error`** shown on the screen
     (`0xE42999`). **`Error` is user-visible text on this route**, not just a log line.
   - `Success == true` → reads the screen's OWN cached invention (`this+0x118`), never the response
     `Value`; shows `"Invention published!"`, then optionally the subscriber-announcement prompt
     (`"New Invention now Available"` / `" is now available in the invention store!"`).
3. `RRUI.Data.InventionDetailsModel.KHKDBICENCB` `0x26CC4B0` → `PCDBKBMDFLM` `0x26CCCC0` →
   `PLBOBKOMNJL(result, verb)` `0x26CCD10`: null → NRE; `Success == false` → toast
   `"Error: " + Error`; `Success == true` → toast `"Invention " + verb`. Never touches `Value`.

**`Status` is never read on this route either** — same as the other two. `Success` decides, `Error`
is the message. `InventionVersion` and `TagsResponse` may be `null`.

**How to apply:** `{"Success":true,"Value":{"Status":0,"Invention":{…updated invention…}}}` — the
`Invention` must be non-null or the inner `.Then` NREs before any UI runs. On failure
`{"Success":false,"Error":"<player-facing reason>","Value":null}`; that string is concatenated
straight into the publishing screen, so write it for a player, not a developer.
