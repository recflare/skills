# POST unity_assets/baked/bulk — response wire shape (2026)

> Build `20260323.14`. Derived **2026-11-12**. `POST https://rooms.recflare.net/unity_assets/baked/bulk`
> returns a **BARE JSON ARRAY** of `RecNet.Rooms.BakedUnityAssetDTO` — no envelope. Serve `[]` for
> the empty case, never `{}`.

## Route facts
- **Service = Rooms (svc 16)** → `rooms.` host. ✓ matches `rooms.recflare.net`.
- **Verb = POST** — confirmed from the `System.Net.Http.HttpMethod` statics read in the builder:
  `mov rax,[HttpMethod klass]` → `[rax+0x20]` (the 2026 static-fields pointer) → **`[+0x20]` = Post**
  (0x08 Get / 0x20 Post / 0x28 Put). Not inferred from the method name.
- Builder: `RecNet.Rooms.DFMBMRNABHU$$KXVCEXPNCFP` 0x95af0c0 (a merged facade; this route is the first
  block). Path literal `'unity_assets/baked/bulk'` slot 0xFD86978. It is a **bulk POST with a request
  body** (body built before the send; request DTO not pinned here — out of scope for the response).

## Response = bare `List<BakedUnityAssetDTO>` (NO envelope)
The send is `RecNet.Rooms.DFMBMRNABHU::Get<T>` with the generic inst (methodSpec #23345) resolving to
**`System.Collections.Generic.List<RecNet.Rooms.BakedUnityAssetDTO>` directly** — the HTTP body
deserializes straight into the list, so there is **no `RecNetResultObject`/`Value` wrapper**. (The
helper is named `Get` but the verb comes from the `HttpMethod` arg, not the name.)

- Empty result = **`[]`**. A `{}` body fails (the list formatter wants `[`, sees `{`) → `Malformed
  Response`. Serve an empty array, not an empty object and not `null`.

## Element: `RecNet.Rooms.BakedUnityAssetDTO` (typedef #23435, 5 keys)
Formatter `Utf8Json.Formatters.RecNet.Rooms.YQYUPMFVDQF` .ctor 0x8eccf90. Serialize order (trailing
`____stringByteKeys` run) and field offsets from `fields2025`:

| # | wire key | field off | CLR type | wire form |
|---|---|---|---|---|
| 1 | `UnityAssetId` | 0x10 | `System.Guid` | JSON **string**, 36-char hyphenated GUID (Utf8Json GuidFormatter) |
| 2 | `Target`       | 0x20 | `byte`        | JSON **number** (0–255; stored as plain byte, no by-name enum formatter) |
| 3 | `Version`      | 0x24 | `int`         | JSON number |
| 4 | `Filename`     | 0x28 | `string`      | JSON string |
| 5 | `Hash`         | 0x30 | `string`      | JSON string |

- ctor: `.ctor(System.Guid unityAssetId, byte target, int version, string filename, string hash)`.
- Utf8Json accepts all three casings per key (Original / camelCase / all-lower); emit the Original
  (PascalCase) names above. No `[DataMember]` renames (keys == property names). No `Nullable<T>`
  fields, so none are optional-by-type — but a missing number deserializes to 0, so send all five.
- Post-deserialize hook not inspected; none expected (sibling Rooms DTOs use the shared no-op).

Example element:
```json
{"UnityAssetId":"3f2504e0-4f89-41d3-9a0c-0305e82c3301","Target":2,"Version":1,
 "Filename":"abc123.unity3d","Hash":"d41d8cd98f00b204e9800998ecf8427e"}
```

## NOT pinned (out of scope / confirm if needed)
- Request body shape (the bulk POST input — likely a list of UnityAssetId GUIDs or a filter DTO).
- Whether `Get<T>` is response-REQUIRED vs null-tolerant; either way the safe empty response is `[]`.
- `Target` byte semantics (platform/target enum vs raw) — it is a number on the wire regardless.
- Related DTO `BakedUnitySubAssetDTO` (formatter `ZJWOTHGNGMD`) is a DIFFERENT type, not nested here.
