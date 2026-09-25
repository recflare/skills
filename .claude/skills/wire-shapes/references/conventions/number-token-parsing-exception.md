# `expected:'Number Token'` — the two `long?` routes

> NKJABNHBPCA "expected:'Number Token', actual:'[', at offset:0" means the response T is a BARE NULLABLE NUMBER and the server sent an array. In build 20250718.01 exactly two routes deserialize to `long?`: `GET dormroom/me` (Rooms) and `GET api/progressionEvents/active` (API). Serve a bare integer or `null`.

Derived **2026-09-24** from build `20250718.01`.

## The exception

```
NKJABNHBPCA: expected:'Number Token', actual:'[', at offset:0
  at ANAMOLLPKLG.CDMENBIFAFK ()
  at PBJNFCLHOCO.LABNBGADOBH (ANAMOLLPKLG& , COIBJKJDIKH )
  at INIGPFNLHFL.LABNBGADOBH[T] (ReadOnlySequence`1[Byte]& )
  at MPDMKDOGMGF.BLPCCACIGAE[T] (...)
  at MGPBDIAGCFD.KKEIDMPEHAL[T] (DPEENGNNEEB )
  ...
  at CBACIMLIBPF.IBJKIAMJCDN (...)
  at CBACIMLIBPF.KOMEOKGFOBP (Queue`1[T], CancellationToken)
```

`NKJABNHBPCA` is Utf8Json's `JsonParsingException`. It is **not** `IONCMJIACFI`
([ioncmjiacfi-malformed-response](ioncmjiacfi-malformed-response.md)) — the parse blew up *inside* the formatter, so the
send helper never got to wrap it. Same root cause, different exception type.

The two obfuscated frames that pin the type:

| frame | what it is | evidence |
|---|---|---|
| `ANAMOLLPKLG.CDMENBIFAFK` `0x8D3AF50` | `JsonReader.ReadInt64()` | calls `ANAMOLLPKLG.CFKFDIJCABG` (ReadNumberSegment) then `EPAAKDFEPAF.NPGAGFPCHKI(seg, &qword, 0)` and returns the **qword** at `0x8D3AF7D` |
| `PBJNFCLHOCO.LABNBGADOBH` `0x8D5EFC0` | `NullableInt64Formatter.Deserialize` | `ReadIsNull` first (`ANAMOLLPKLG.GLHCEJIDNDJ` `0x8D3BDE0`), then `ReadInt64`, then builds a **16-byte** struct returned in `xmm0` — `Nullable<long>`, not `Nullable<int>` (8 bytes) |

`PBJNFCLHOCO.FBGBLPHHDGN` (Serialize) confirms the layout: `cmp byte ptr [rbx], 0` — **`hasValue`
sits at offset 0**, value at +8. Same Mono nullable layout as everywhere else in this build.

So **T is `long?`**, the body must be a bare JSON number or literal `null`, and `[` at offset 0 means
the server returned an array.

## Which route

Scanning all 911,853 methodSpecs for a send helper instantiated over `long`/`long?`/`int`/`int?`
leaves exactly **two** entry helpers taking `Nullable<long>`:

| route | service | verb | entry | helper |
|---|---|---|---|---|
| `dormroom/me` | **16 Rooms** | GET (`[rcx+8]` at `0x7DFEC17`) | `OALMDGJKBJH.OGNJABFICGG` `0x7DFEB60` | `OALMDGJKBJH.NDBMFFLDBBK<long?>` (spec 832151, slot `0xD2A0E20`) — **bare**, no envelope |
| `api/progressionEvents/active` | **2 API** | GET (`[rcx+8]` at `0x7D62400`, `r8d=2` at `0x7D62423`) | `MPJLPOEEGIF.MLFAMKJMNOD` `0x7D62330` | `MGPBDIAGCFD.CJBFDPLCIEJ<long?>` (spec 827983, slot `0xD16C4B0`) — nullable send |

Both take **no params and no body**. Neither is enveloped. Correct responses:

```
1162          # a dorm room id / an active progression event id
null          # nothing set
```

Full derivation of the API one: [progressionevents-active](../endpoints/progressionevents-active-wire-shape.md) — `-1` is the client's own
"no active event" sentinel there, so serve `-1` rather than `null`.

`dormroom/me` is the usual culprit — the name reads like "give me my dorm room", so a server
naturally returns a room object or a list of rooms. The client wants the **id alone**.

`OALMDGJKBJH.OGNJABFICGG` has **0 direct call sites** (it is a thin forwarder that gets inlined), so
do not try to find its callers with `callxref` — see the inlining caveat in
[nonobject-response-routes](nonobject-response-routes.md).

## Why the generated table misses both

Neither appears in `il2cpp-2025/nonobject-responses.txt`. That scan keeps sends whose `T` is a
primitive, a string or a `List`; `Nullable<long>` is a **genericinst over a value type**, so it falls
through the filter. Combined with the `String.Format` blind spot already recorded in
[nonobject-response-routes](nonobject-response-routes.md), treat that file as a lower bound twice over.

To redo the scan on a new build: iterate `MetadataRegistration.methodSpecs`, resolve each spec's
method generic inst with the helpers in `ginst.py`, keep the one-arg scalar ones whose owning method
is a known send helper, then map spec index → `.data` slot (kind 6) → `mxref.py` → owning method →
`names.py` for the route literal.
