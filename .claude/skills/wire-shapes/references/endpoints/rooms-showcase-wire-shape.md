# Rooms showcase wire shape

> GET rooms/showcase/{roomId} (svc 16 Rooms) returns a BARE JSON ARRAY of numbers (List<long>) — it uses the room facade's description-less bare helper, not the enveloped one.

Derived **2026-08-24** from build `20250718.01` via [recflare-2025-metadata-carve](../../../il2cpp-analysis/references/recflare-2025-metadata-carve.md).

`GET https://rooms.<host>/showcase/{roomId}` — service **16 = Rooms** ([recnet-service-enum](../conventions/recnet-service-enum.md)),
verb **GET** (`HttpMethod` statics `+0x08`), **no query params, no body**. Client entry
`OALMDGJKBJH.HDJJEEDJPHI(int roomId, CancellationToken)` `0x7DFA270` → `Task<List<long>>`;
path is `String.Format("showcase/{0}", roomId)`, literal `0xD259C78`.

**Response is a BARE JSON ARRAY of numbers** — `LMKONLJOAEP<List<long>>`, T is the `List<long>`
itself:

```json
[ 5512, 5513 ]
```

Serve `[]` for a room with no showcase. (The `long` values are ids the caller resolves elsewhere;
what they point at was not traced.)

**The same `showcase/{0}` literal is used by two other facades** — `BDPKDKOCHBC.BGDMOPEEECB`
`0x7DC4EA0` and `KCHDMOJGHJD.HDJJEEDJPHI` `0x7DD4290` — on different services. Match the host before
assuming this shape; only the `OALMDGJKBJH` one is `rooms.<host>`.

## Corrects an overreach in [rooms-isbanned-wire-shape](rooms-isbanned-wire-shape.md)

That note says "on `OALMDGJKBJH` *every* helper carries the description, which is why all of it is
enveloped." **Wrong** — the room facade also has two description-less bare helpers, and this endpoint
uses one. The earlier search only enumerated state machines that *had* a `friendlyActionDescription`
field, so the bare ones were invisible to it. Full table:

| helper | SM | description? | awaits | wire |
|---|---|---|---|---|
| `NDBMFFLDBBK<T>` / `LMKONLJOAEP<T>` | `DDDGNNGFOEK\`1`, `MLIDEJOJDDP\`1` | no | `T` | **bare** |
| `PJPLCMBOAFB<T>` | `MAIFFNFOJDL\`1` | yes | `KGOJLHJNIOD<T>` | enveloped |
| `IFGOMFPLGHC<T>` | `GJPJGPKPHDF\`1` | yes | `OOJPCAPFGCP<T>` | enveloped |
| `NNKPBFNIDFI<T>` | `POGDDGGCJOK\`1` | yes | `GJAFHDAFBNE<T>` | enveloped (list) |
| `PJPLCMBOAFB` / `ONEPMGPMHNC` | `BAGDEGGEONJ`, `NCJCHOMKLOB` | yes | `JFNAKFCGDAO` / void | enveloped / none |

The **`friendlyActionDescription` rule itself still holds exactly** (and `isBanned` really is
enveloped — it uses `IFGOMFPLGHC`). What does not hold is "this facade is uniformly enveloped":
envelope status is **per helper, per endpoint**, on every facade. Always read which helper the entry
method calls.
