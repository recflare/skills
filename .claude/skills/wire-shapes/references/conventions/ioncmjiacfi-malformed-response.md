# Ioncmjiacfi malformed response

> IONCMJIACFI 'Malformed Response' in recflare-2025 is thrown by MGPBDIAGCFD.KKEIDMPEHAL<T> when the body is empty or fails to deserialize into T — a '{}' body means the endpoint expects an ARRAY or a scalar, not an object.

Identified **2026-08-20** on `C:\Games\recflare-2025` (build `20250718.01`) via
[recflare-2025-metadata-carve](../../../il2cpp-analysis/references/recflare-2025-metadata-carve.md).

`IONCMJIACFI : MELLIJAOIBB : Exception` is thrown by the generic deserialize step
`MGPBDIAGCFD.KKEIDMPEHAL<T>(DPEENGNNEEB response)` (`0x3D89D70`, state machine
`NBEFLKHMAFJ<T>`; the gshared bodies land in `0x574F9C0`, which `methods.pkl` mislabels as
`FLMDJANAGJA$$PBFKIPJJGLD`). Six instantiations, each with the same structure — the literals give
the logic away:

- `"Response was empty"` — body null/empty
- `"Deserialization returned null"` — Utf8Json returned null for `T` (only in the 3 reference-type
  instantiations)
- `"Malformed Response: '<body>'"` — the rethrow wrapper, with the raw body inlined

Call chain in the stack: `CBACIMLIBPF.KOMEOKGFOBP` (queue drain) → `CBACIMLIBPF.IBJKIAMJCDN`
(the pump, whose args include `NNPMGHNBFMD service` and `string path` — **the trace never shows
their values**) → `MGPBDIAGCFD.ECHPAADCNOI<TResponse>` → `<>c__44<TResponse>.GLCPIAEHOMD` (the
`HPBKMCLEANE<T>` "response required" lambda) → `KKEIDMPEHAL<T>`.

## `Malformed Response: '{}'` is a strong signal

`{}` is valid JSON, so it only fails when `T` cannot be built from a JSON **object**:

- `List<T>` / arrays — Utf8Json's list formatter wants `[`, throws on `{`
- `string` — wants a string token
- value types (enum / int / bool)

**If `T` were a plain DTO class, `{}` would deserialize fine** (all members default) and you would
get [llcldppagij-envelope-failure-exception](llcldppagij-envelope-failure-exception.md) instead, or silent nulls. So a `Malformed Response:
'{}'` means **the endpoint should be returning an array or a scalar and the server returned an empty
object** — almost always an unimplemented route falling through to a default `{}`.

Correct empty responses for the array endpoints derived so far: `[]`, not `{}`. See
[curatedlists-bulk-wire-shape](../endpoints/curatedlists-bulk-wire-shape.md), [rooms-contributedby-wire-shape](../endpoints/rooms-contributedby-wire-shape.md),
[privileges-me-restrictions-wire-shape](../endpoints/privileges-me-restrictions-wire-shape.md), [discovery-sections-pagesource-wire-shape](../endpoints/discovery-sections-pagesource-wire-shape.md),
[rooms-autocomplete-search-wire-shape](../endpoints/rooms-autocomplete-search-wire-shape.md) (array of plain strings),
[platformnotifications-wire-shapes](../endpoints/platformnotifications-wire-shapes.md) (`config/categories`), and
[chat-cansenddm-wire-shape](../endpoints/chat-cansenddm-wire-shape.md) (bare integer).

**How to apply:** the exception names no endpoint. Correlate with the server access log for the
request immediately preceding it, then check whether that route's shape is an array/scalar.

# ✅ 2026 (`20260323.14`): same rule, new names — and the inner exception tells you the direction

Re-confirmed **2026-10-30** from a live `Player.log`. On 2026 the exception type is spelled out:
**`RecNet.RecNetMalformedResponseException`**, and the deserialize step is
**`RecNet.RGBOOBRDHEB.AIYNPFIEYFY<T>(RecNet.XJAFUXFVGPU response)`** — generic-shared, the
reference-type body spanning `0x6c6ce10`–`0x6c6d30a` (`methods.pkl` mislabels it
`UnityEngine.Localization.Tables.AssetTableEntry$$set_PreloadAsyncOperation`; attribute with
`fstart.py`, not by window):

```
0x6c6d135  deserialize the body into T
0x6c6d239  'Deserialization returned null'   literal 0xFDDD6E0
0x6c6d24e  new System.Exception(msg)                      ; the INNER exception
0x6c6d28f  XJAFUXFVGPU$$AFXLACYVZDU                       ; re-read the body as a string
0x6c6d2bb  new RecNetMalformedResponseException("Malformed Response: '" + body + "'")
```

`'Malformed Response: <body>'` is only the wrapper — **read the inner exception to learn which way
the mismatch runs**:

| body | inner exception | what `T` is |
|---|---|---|
| `{}` | `Exception: Deserialization returned null` | a **list / array / scalar** — serve `[]` (or the scalar) |
| `[]` | `JsonParsingException: expected:'{', actual:'[', at offset:0` | an **object** — serve `{…}`, or the envelope |

Both forms appeared 90 s apart in one session, so a log with several of these can carry both
directions at once; do not assume every `Malformed Response` in a session is the same route.

2026 send-helper names for the frames above the deserialize (on `RecNet.RGBOOBRDHEB`):
`ZWUODKCINOA<T>(ct)` response required (2025 `HPBKMCLEANE`), **`LIRIDCJIGGA<T>(bool, ct)` nullable
response** (2025 `CJBFDPLCIEJ`), `JEYAQXBXMRA(ct)` no response, with
`YGADVOMHRVJ<T>` / `TZATELUBAOF<T>.MUKIUKVCLOC` as the retry/await plumbing beneath them.

⚠️ **If the task was fire-and-forget the stack has no application frame at all** — it ends at
`LIRIDCJIGGA<TResponse>` and is surfaced by `RecRoom.Async.XKMSFCDUWSV<T>.IQQWXDIHGCW(Task<T>)` →
`SAXZOKINUQZ.KSNTDCQPEQA`. There is then nothing in the log to identify the route, so derive the
candidate routes from the UI action instead; worked example in
[avatar-trial-item-pricing-chain-2026](../endpoints/avatar-trial-item-pricing-chain-2026.md).

⚠️ **`Player.log`'s bracketed clock ran 3 h behind UTC** on this machine — the Dissonance lines
carry a parallel UTC stamp, so use those when matching a server access log.
