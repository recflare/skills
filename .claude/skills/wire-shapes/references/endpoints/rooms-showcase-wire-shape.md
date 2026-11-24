# Rooms showcase wire shape

> **BARE JSON ARRAY of numbers (`List<long>`) on BOTH builds** — the room-id ints of the rooms the
> showcase features. The client fetches this id list, then **bulk-resolves** the ids into full rooms
> via a *separate* call. Do **NOT** serve `RoomDTO` objects here — the client deserializes each element
> as a `long`, so an array of objects breaks the showcase screen (empty / broken). Serve `[]` for empty.

## 2026 (`20260323.14`) — bare `List<long>` (VERIFIED, corrects an earlier mis-derivation)

Verified **2026-11-22**. `GET https://rooms.<host>/showcase/{roomId}` — svc **16 Rooms**, **GET**, no body, no query params.

```json
[ 1162, 5512, 5513 ]
```

- **The HTTP response deserializes to `List<long>`.** Proven via the deobfuscated showcase consumer
  `<GetRoomsShowcase>b__0>d$$MoveNext` `0x95c3ad0`, whose awaits are, in order: ① `TaskAwaiter<List<long>>`
  (ginst class 2959) = the showcase body, then ② `TaskAwaiter<List<RoomDTO>>` (class 1105) = the
  bulk id→DTO resolve (`Client.IGHFPJOWRQB` 0x95c3fc6 / `CUXYYVUNGOZ.URNDYZGXOOU(IReadOnlyList<long>,bool,ct)`),
  returning `IReadOnlyList<RoomDTO>` (class 2926).
- **Low-level HTTP facade:** `RecNet.Rooms.DFMBMRNABHU$$EXXDRWGZSNL(int,CancellationToken)` `0x95ac090`
  → `Task<List<long>>`, path `String.Format("showcase/{0}", roomId)` (literal `0xFE1FC30`). Bare list,
  no envelope. (0 direct call sites because it is interface-dispatched — NOT orphaned.)
- ⚠️ **TRAP that caused a wrong derivation on 2026-11-22:** `RecNet.Rooms.Client$$EXXDRWGZSNL(int)` `0x95892a0`
  and `RoomsClientStaticProxy$$EXXDRWGZSNL` (jmp `0x95d20b2`, callers `RoomListModel.RefreshCacheInternal`,
  `<QueryPlayerSource>d__23`) return `MPVTAJGPRUT<IReadOnlyList<RoomDTO>>` — but that is the **RESOLVED**
  result (ids already looked up), **not the wire body**. Reading a facade's *return* type as the wire
  shape fails whenever the facade resolves ids to DTOs client-side. Always confirm the wire type from the
  first `await`/deserialize in the async consumer, not the method's return type.
- The third sharer of the `showcase/{0}` literal, `HWJSABCRIGB$$LSHBWNNMUQJ(int)→string`, is just a Rooms
  route-string builder, not an HTTP caller.

## 2025 (`20250718.01`) — bare array of numbers (`List<long>`)

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
