# Clubs subscription/{id} wire shape

> POST subscription/{id} (svc 15 Clubs) is ENVELOPED with a scalar: {"Value": <long>, "Success", "Error", "error_id"}. Its DELETE sibling on the same literal is the VALUELESS envelope (no Value). The POST also sends a form-encoded `roomId` body — but only when the player is in a room.

Derived **2026-09-24** from build `20250718.01`.
Envelope hierarchy comes from [rooms-isbanned](rooms-isbanned-wire-shape.md); the verb→param rule from
[elhkhfjehlm-verb-dependent-params](../conventions/elhkhfjehlm-verb-dependent-params.md).

`POST https://clubs.<host>/subscription/{id}` — service **15 = Clubs** (`r8d = 0xF` at the
`AKJEAMCCEOH..ctor` call `0x7CAA99C`), verb **POST** (`HttpMethod` statics `[rcx+0x20]` at
`0x7CAA940`).

Path is `String.Format("subscription/{0}", id)` — literal slot **`0xD08B968`**. The `{0}` is an
**int** — the UI caller loads it with `mov edi, dword ptr [rbx+0x10]` / `mov ecx, edi` at
`0xDB2C52`, so `207` is an int id, not a long.

Client entry **`LNJNCFHNBOM.JCFEAEHPCAO(int id, CancellationToken)`** `0x7CAA7C0`. Callers:
`GPPGDNOODMO.JCFEAEHPCAO` `0xDAA2B0`, `MJKKHMHMCMB.OHOJELMFKMO` `0xDB2B90` (a `Button3D` handler —
this fires from a UI subscribe button), and the tail-jump wrapper `MAOFOGLKCFP.JCFEAEHPCAO`
`0x7C71DA0`.

## Request — conditional form body

One `ELHKHFJEHLM("roomId", <ObscuredLong>)` at `0x7CAAAB1`. The verb is POST, so this is an
**`application/x-www-form-urlencoded` body**, not a query param.

It is **guarded**: the client reads the current room from `RecNet.Matchmaking.MLNNAKHOFCA` (falling
back to `ObscuredLong(-1)` when there is no room) and skips the parameter entirely on
`cmp rax, -1; je 0x7CAAAB6` (`0x7CAAA67`). So:

| client state | request body |
|---|---|
| in a room | `roomId=<roomId>` |
| not in a room | **no body at all** |

A server that requires `roomId` will 400 for anyone subscribing from a menu outside a room. There is
no `ELKIBCPINAP`, so nothing else is ever sent.

## Response — ENVELOPED, scalar Value

Send helper is **`MGPBDIAGCFD.HPBKMCLEANE<T>`** (response required), methodref at `0x7CAAAB6`,
generic inst **#14629** = **`OOJPCAPFGCP<long>`** — one of the two single-value envelopes in the
`FFOENOGPGNH<T>` family. Derived-first ordering puts `Value` before the base members:

| # | key | CLR |
|---|---|---|
| 1 | `Value` | **long** |
| 2 | `Success` | bool |
| 3 | `Error` | string |
| 4 | `error_id` | string — **lowercase**, it is a `[DataMember]` rename |

```json
{ "Value": 0, "Success": true, "Error": null, "error_id": null }
```

`Success: false` (or a null body) throws **`LLCLDPPAGIJ`**, not `IONCMJIACFI` — the envelope check
runs before the value is read.

⚠️ **What the `long` means is not pinned.** The client threads it out through
`MKNAIKDDNEO`'s continuation to the caller; neither UI consumer stores it anywhere I could follow.
`Value` is a plain `long` (not `Nullable`), so an omitted key deserializes to `0` and nothing
throws. The sibling route `subscription/subscriberCount/{0}` is a *separate* endpoint
(`LNJNCFHNBOM.CJCAAJNIIMO` `0x7CA2500`, `LNJNCFHNBOM.KDFFFEPFAII` `0x7CAB670`), so the returned
long is **not** the client's only source of subscriber count.

## DELETE on the same path is a different envelope

`LNJNCFHNBOM.LFHHMLBDIOE` `0x7CAD710` uses the same `subscription/{0}` literal with
`HttpMethod` statics **`[rcx+0x00]` = Delete** (`0x7CAD86F`) and `HPBKMCLEANE<T>` generic inst
**#2849** = **`JFNAKFCGDAO`** — the **valueless** envelope. It takes **no params and no body**.

```json
{ "Success": true, "Error": null, "error_id": null }
```

Returning a `Value` key there is harmless (unknown keys are dropped), but returning the *valueless*
shape for the POST leaves `Value` at `0`.

## Siblings

Other `subscription/*` literals in this build, with the class that references each — note they are
**not all on `LNJNCFHNBOM`**:

| literal | class |
|---|---|
| `subscription/{0}` | `LNJNCFHNBOM` (POST `JCFEAEHPCAO`, DELETE `LFHHMLBDIOE`) |
| `subscription/subscriberCount/{0}` | `LNJNCFHNBOM` (`CJCAAJNIIMO`, `KDFFFEPFAII`) |
| `subscription/top/creators/today` | `LNJNCFHNBOM` (`KPNMJEKMDGL`) |
| `subscription/details/{0}` | `DFGEAKEHCIP` (`NPNJDPBKEOH`) |
| `subscription/mine/member` | `MIAEIIPKLEI` (`DLDEEKKJNKF`) |
| `subscription/v1/cancel` | `CMHGCGFFLAM` (`KOBBLPBLPFP`) |

None of them are in the generated `nonobject-responses.txt` — every one is `String.Format`-built, the
same blind spot as [playerevents-v1-responses](playerevents-v1-responses-wire-shape.md). Treat that table as a lower bound.

## Tooling note

`names.py` / `slots2025.py` need **`GAMEASSEMBLY=…/tools/metadump/out/GameAssembly.dll`** (the carved,
decrypted PE). Pointing them at the shipped `recflare/GameAssembly.dll` is not an error — the
`il2cpp` section is encrypted at rest, so they return **`0 literal reference(s)`** and plausible-looking
garbage instead. `mxref.py` reads `GA_IMAGE` and keeps working, which makes the mismatch easy to miss.
