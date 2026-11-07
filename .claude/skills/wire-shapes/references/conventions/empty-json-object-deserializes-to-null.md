# `{}` deserializes to NULL for every object DTO (2026)

> On build `20260323.14` every generated Utf8Json object formatter begins
> `if (ReadIsNull()) return null; ReadIsBeginObjectWithVerify(); if (ReadIsEndObject()) return null;`
> — so an **empty JSON object is parsed as `null`**, the RecNet send helper then throws
> `Exception: Deserialization returned null`, and it surfaces as
> `RecNetMalformedResponseException: Malformed Response: '{}'`. `{}` is never a valid response body
> for an object DTO on this client. The minimum is one key.

Derived **2026-11-06** from `C:\games\recflare-2026` (build `20260323.14`) plus a live `Player.log`,
via [recflare-2026-static-index]. This **corrects** the rule in
[ioncmjiacfi-malformed-response](ioncmjiacfi-malformed-response.md), which said a `{}` body means
`T` is a list or a scalar.

## The formatter prologue

`Utf8Json.Formatters.RecNet.LGXRWCKQVEY$$Deserialize` (`SubscriptionInfoDTO`) `0x912D650`:

```
0x912D6CC  call Utf8Json.JsonReader$$KKLKLRLWGGJ   ; ReadIsNull()
0x912D6D3  jne  0x912D8B0                          ; -> xor eax,eax ; ret     (return null)
0x912D6DE  call Utf8Json.JsonReader$$IDIIQOMHLBZ   ; ReadIsBeginObjectWithVerify()   (mov dl,0x7b)
0x912D6E8  call Utf8Json.JsonReader$$KMTQGEAVNZE   ; ReadIsEndObject()               (mov dl,0x7d)
0x912D6EF  jne  0x912D8B0                          ; -> return null            *** '{}' LANDS HERE
0x912D721  call Utf8Json.JsonReader$$PEPQTDIXVGN   ; ReadIsEndObjectWithSkipValueSeparator(ref n)
```

The four `JsonReader` primitives, identified from their literal bytes:

| 2026 name | RVA | what it is |
|---|---|---|
| `KKLKLRLWGGJ` | `0xA513620` | `ReadIsNull()` |
| `IDIIQOMHLBZ` | `0xA5132C0` | `ReadIsBeginObjectWithVerify()` — `mov dl, 0x7b` (`{`) |
| `KMTQGEAVNZE` | `0xA5136E0` | `ReadIsEndObject()` — `mov dl, 0x7d`, **no `ref int`** |
| `PEPQTDIXVGN` | `0xA514290` | `ReadIsEndObjectWithSkipValueSeparator(ref int)` — `0x7d` **plus** the counter |

The `ReadIsEndObject()` early return is **not** stock Utf8Json behaviour (stock returns
`new T()` with every member defaulted). It is universal in this build.

### Scale of the check

Scanned all **910** `Utf8Json.Formatters.*$$Deserialize` methods in the image for
`call KMTQGEAVNZE ; test al,al ; jne <target>` and followed the branch:

| result | count |
|---|---|
| branch lands on a `return null` epilogue (`xor eax,eax` / `33 c0`, possibly after register restores) | **850** |
| no `ReadIsEndObject` call at all — the `Utf8Json.Formatters.*` types with no namespace, i.e. **struct** DTOs, which cannot return null | 60 |

So every reference-type DTO in the build behaves this way. Verified end to end on two
(`LGXRWCKQVEY` `0x912D650`, `BXBVOGOAEGA` `0x91237B0`) and prologue-matched on six more at random.

⚠️ **`xor eax, eax` assembles here as `33 C0`, not `31 C0`.** The first pass of this scan
matched only `31 C0`, scored **0 of 910**, and read as "the pattern does not exist" — it was the
scanner that was wrong, not the hypothesis. Allow both encodings, and allow a register-restore
preamble (`48 8b 9c 24…` / `4c 8d 5c 24…`) before the `33 C0`: 748 formatters branch straight to it,
102 restore registers first.

⚠️ **Whether this was ever true on `20250718.01` is UNVERIFIED.** The old rule held for every 2025
route anyone checked, but those routes genuinely were array/scalar ones, so the inference was never
tested against a 2025 object DTO. Re-run the 910-formatter scan against the 2025 image before
trusting either rule there.

## What it looks like in the log

Two exceptions, inner then wrapper, from `RecNet.RGBOOBRDHEB.AIYNPFIEYFY<T>`:

```
Exception: Deserialization returned null
  at RecNet.RGBOOBRDHEB.AIYNPFIEYFY[T] (RecNet.XJAFUXFVGPU a)
  at RecNet.RGBOOBRDHEB+TZATELUBAOF`1[a].MUKIUKVCLOC (RecNet.XJAFUXFVGPU a)
  at RecNet.RGBOOBRDHEB.YGADVOMHRVJ[TResponse] (System.Func`2[T,TResult] a, CancellationToken b)
  at RecNet.Core.OOLFEOLDQTG (HttpMethod a, RecNet.Service b, String c, …)
Rethrow as RecNetMalformedResponseException: Malformed Response: '{}'
```

The two throw sites, both generic-shared (`methods.pkl` mislabels the region
`UnityEngine.Localization.Tables.AssetTableEntry$$set_PreloadAsyncOperation` — bound with
`fstart.py`, never by window):

```
0x6C6F280 .. 0x6C6FAF1
  0x6C6F95C 'Received blank response when we expected data'  -> Log$$LIBCEQYQFAM
  0x6C6F9A5 new RecNetWebException("Malformed Response")
  0x6C6F9E7 new RecNetWebException("Deserialization returned null")   <- reached from
            0x6C6F69E call 0xC40570 (is-not-null on the shared T) ; 0x6C6F6AC je 0x6C6F9D0
0x6C6C510 .. 0x6C6C98C
  0x6C6C8B5 new RecNetMalformedResponseException("Response was empty")
  0x6C6C8EB <catch funclet>  -> XJAFUXFVGPU$$AFXLACYVZDU(0) (body as string)
  0x6C6C928 "Malformed Response: '" + body + "'"  -> RecNetMalformedResponseException
```

## How to read a `Malformed Response` on 2026

The **inner** exception, not the wrapper, tells you what is wrong:

| body | inner exception | meaning |
|---|---|---|
| `{}` | `Exception: Deserialization returned null` | **the formatter rejected the empty object.** Serve the DTO with at least one key — `T` being a list/scalar is NOT implied |
| *(empty / zero bytes)* | `Received blank response when we expected data` → `RecNetWebException("Malformed Response")`, or `RecNetMalformedResponseException("Response was empty")` | no body at all; 204 and an empty 200 both land here |
| `[]` | `JsonParsingException: expected:'{', actual:'[', at offset:0` | `T` is an object, you sent an array |
| `{...}` | `JsonParsingException: expected:'Number Token', actual:'null'` | a non-nullable numeric member arrived as `null` |

**How to apply:** never emit a bare `{}` from a 2026 handler. For a "nothing here" object response
emit every key the formatter declares with `null`/`0` values, e.g.
`{"Subscription":null,"PlatformAccountSubscribedPlayerId":null}` — one key is enough to get past
`ReadIsEndObject`, but sending the full key set also avoids the `'Number Token'` trap. `[]` remains
correct for list responses and is unaffected: the empty-array case is a *different* code path and was
**not** checked here.

Worked example:
[econ-campuscard-updateandgetsubscription](../endpoints/econ-campuscard-updateandgetsubscription-wire-shape.md)
— `{}` for a non-subscriber broke `Platform.BootSequence` with
`ErroredPromiseException: Failed to get subscription: An error occurred`.
