# Rooms isbanned wire shape

> GET rooms/{roomId}/bans/{accountId}/isBanned (svc 16 Rooms) is ENVELOPED — {Value:bool, Success, Error, error_id}, not a bare true; every send helper on the OALMDGJKBJH room facade envelopes.

Derived **2026-08-24** from build `20250718.01` via [recflare-2025-metadata-carve](../../../il2cpp-analysis/references/recflare-2025-metadata-carve.md).

`GET https://rooms.<host>/rooms/{roomId}/bans/{accountId}/isBanned` — service **16 = Rooms**
([recnet-service-enum](../conventions/recnet-service-enum.md)), verb **GET** (`HttpMethod` statics `+0x08`), **no query params, no body**.
Client entry `OALMDGJKBJH.PEDECJGKFHP(long roomId, int accountId, CancellationToken)` `0x7DFF350`
returning `Task<bool>`; route is `String.Format("rooms/{0}/bans/{1}/isBanned", roomId, accountId)`
(literal `0xD19F000`), friendly description literal `'check room ban'` (surfaces as
`"Failed to check room ban"`).

## Response is ENVELOPED — not a bare `true`

```json
{ "Value": true, "Success": true, "Error": null, "error_id": null }
```

`Value` is the boolean. `Success`/`Error` PascalCase, **`error_id` lowercase**
(`[DataMember(Name = "error_id")]`); all keys accept the three Utf8Json casings.
`Success: false` or a null body → the client throws `LLCLDPPAGIJ`
([llcldppagij-envelope-failure-exception](../conventions/llcldppagij-envelope-failure-exception.md)) with no endpoint name in the message.

**Why: envelope status is a property of the send helper, not the service.** This route uses
`IFGOMFPLGHC<T>`, one of the room facade's **enveloped** helpers. ⚠️ **Corrected 2026-08-24:** an
earlier version of this note claimed *every* helper on `OALMDGJKBJH` is enveloped — it is not; the
facade also has two description-less **bare** helpers (`NDBMFFLDBBK<T>`, `LMKONLJOAEP<T>`), used by
e.g. [rooms-showcase-wire-shape](rooms-showcase-wire-shape.md). Read which helper the entry method calls, every time.
The enveloped helpers here:

| helper | returns | awaits |
|---|---|---|
| `IFGOMFPLGHC<T>` / `PJPLCMBOAFB<T>` (SMs `MAIFFNFOJDL\`1`, `GJPJGPKPHDF\`1`) | `Task<T>` | `KGOJLHJNIOD<T>` / `OOJPCAPFGCP<T>` |
| `NNKPBFNIDFI<T>` (SM `POGDDGGCJOK\`1`) | `Task<List<T>>` | `GJAFHDAFBNE<T>` |
| `PJPLCMBOAFB` non-generic (SM `BAGDEGGEONJ` `0x7DE77F0`) | `Task` | `JFNAKFCGDAO` (valueless) |

All of those take a leading `friendlyActionDescription`; the bare helpers do not — that parameter is
the reliable tell ([playerevents-v1-room-wire-shape](playerevents-v1-room-wire-shape.md)). `rooms/{id}/experience`
([rooms-experience-wire-shape](rooms-experience-wire-shape.md)) and `rooms/contributedby/me`
([rooms-contributedby-wire-shape](rooms-contributedby-wire-shape.md)) are bare, and so is `showcase/{id}` on this very facade.

## Envelope hierarchy (corrects the tier list in [outfits-me-put-wire-shape](outfits-me-put-wire-shape.md))

```
JFNAKFCGDAO                       { Success, Error, error_id }        valueless
  FFOENOGPGNH`1<T> : JFNAKFCGDAO  { Value, Success, Error, error_id } Value first (derived-first)
    KGOJLHJNIOD`1<T>              single value
    OOJPCAPFGCP`1<T>              single value
    GJAFHDAFBNE`1<T> : FFOENOGPGNH`1<List<T>>   list value
FABLLDLBLBB`1<T> : ValueType      { Success, Error, error_id, Value }  struct variant
```
All implement the marker `MPKGNLKJDEG`, which is exactly what `POCKEGKCADF.AIHPPAPDEBL` asserts on.

**Not pinned:** which of `KGOJLHJNIOD<bool>` / `OOJPCAPFGCP<bool>` `IFGOMFPLGHC` uses — the helper is
shared generic code reached via rgctx, and both have an identical wire shape, so it does not matter.

**Siblings on the same facade** (same literal block): `rooms/{0}/bans`, `rooms/{0}/bans/bulk`,
`rooms/{0}/bans/history`, `rooms/{0}/bans/import`, `rooms/{0}/bans/{1}`, `rooms/{0}/automute`.
