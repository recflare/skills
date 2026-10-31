# `PUT dormroom/me` — set active dorm

> PUT dormroom/me (svc Rooms) takes a form-body `roomId` and returns the dorm room id **ENVELOPED on
> both builds**: `{"Value":1162,"Success":true,"Error":null,"error_id":null}`. A bare `1162` fails.

Derived **2026-10-30**. **Confirmed live on 20260323.14 the same day**: the enveloped body fixed dorm creation. Friendly description on both builds: `'set dorm room as active dorm'`.
The GET sibling on the same path returns `long?`, bare on both builds. See
[number-token-parsing-exception](../conventions/number-token-parsing-exception.md).

## ⚠️ Corrected the same day — the first version said "bare on 2026"

That claim came from the `RecNetResultObject_*` envelope oracle, which returned 0 hits for `long`.
**The oracle is incomplete:** primitives use a separate family, `RecNet.RecNetResultPrimitive<T>`,
with concrete types `…PrimitiveBoolean / Guid / Int / Long / String`. A live capture disproved the
"bare" answer:

```
JsonParsingException: expected:'{', actual:'35278', at offset:0
  at Utf8Json.Formatters.RecNet.RAWAXOIPGST.Deserialize
  ...
Rethrow as RecNetMalformedResponseException: Malformed Response: '35278'
Rethrow as RecNetUserFriendlyException: Failed to set dorm room as active dorm
  at RecNet.Rooms.DFMBMRNABHU.LKVNIZZZQYH[c]
```

`RAWAXOIPGST` is `Deserialize(...) -> RecNet.RecNetResultPrimitive<long>` (`msig`). The user-visible
symptom is `[Experience.CustomDorm] Failed to create new dorm: Failed to set dorm room as active dorm`.

## Request (both builds)

- Verb **PUT**: `[HttpMethod statics + 0x28]`.
- No JSON body. One parameter, `roomId` (long), added by the closure lambda through the param adder.
  Because the verb is not GET, it goes in an **`application/x-www-form-urlencoded` body**:
  `roomId=1162`. See [elhkhfjehlm-verb-dependent-params](../conventions/elhkhfjehlm-verb-dependent-params.md).

## Response

| build | facade method | send | deserialize target |
|---|---|---|---|
| `20260323.14` | `RecNet.Rooms.DFMBMRNABHU.XTOHTDVTMAB(long, ct)` `0x95B45C0` → `Task<long>` | `DFMBMRNABHU.LKVNIZZZQYH<long>` (ginst #59) | `RecNetResultPrimitive<long>`, formatter `RAWAXOIPGST` (`.ctor` `0x8E4FBB0`) |
| `20250718.01` | `OALMDGJKBJH.NPKNGCEDKOH(long, ct)` `0x7DFE6E0` → `Task<long>` | `OALMDGJKBJH.IFGOMFPLGHC<long>` (ginst #704) | `OOJPCAPFGCP<long>` (see [rooms-showcase](rooms-showcase-wire-shape.md)) |

The 2026 formatter's serialized keys, in order: **`Value`, `Success`, `Error`, `error_id`**. These
are the same four as every other envelope, so one response works on both builds:

```json
{"Value": 1162, "Success": true, "Error": null, "error_id": null}
```

- `Value` is a non-nullable `long`. Echo the `roomId` that was set.
- `Success` must be `true`. `{}` deserializes to `Success=false`, and the call fails.

`LKVNIZZZQYH<T>` is the 2026 Rooms facade's description-carrying helper. It deserializes
`RecNetResultPrimitive<T>` itself and returns `Value`, which is why the facade declares a plain
`Task<long>`, and why `msig` cannot tell this route apart from a bare one.

Closure lambdas holding the `roomId` literal: `LEFGRLARUPB.ZSODIEUMKRD` `0x95B67E0` (2026),
`BEFDDBGCAEG.BBDHJFONHMF` (2025).
