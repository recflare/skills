# PlayerEvent.Tags shape

> ⚠️ CORRECTED 2026-09-23 — PlayerEvent.Tags is `List<{Tag, Type}>` on BOTH clients. This note previously claimed recflare-2025 wanted bare strings; it does not, and sending strings makes the 2025 client reject an otherwise-perfect 200 response. Only TagModifyResult.Tags is `List<string>`, on both builds.

Original note **2026-08-25** (diagnosing a `HEBOAMGAJAG: Malformed Response` on `recflare-client`);
**corrected 2026-09-23** after the same symptom appeared on `recflare-2025`.

## The shape (both builds)

```json
"PlayerEvent":     { …, "Tags": [ { "Tag": "class", "Type": 0 } ], … }
"TagModifyResult": { "Result": 0, "Tags": [ "class" ] }
```

**`PlayerEvent.Tags` is a list of objects. `TagModifyResult.Tags` is a list of bare strings.**
That asymmetry is real on both builds — do not "fix" both.

| build | JWT `ver` | `PlayerEvent.Tags` element | evidence |
|---|---|---|---|
| `recflare-client` | `20230414` | `ALGBCBHPICC` `{string @0x10, IHJBBBIJIDH @0x18}` | `NCBAEFEDLMK : IMIJPHJKLIM` has `List<ALGBCBHPICC> <EAHDAGAJEAA>k__BackingField` @0x98 (dump.cs 1260809) |
| `recflare-2025` | `20250718.01` | `EOPJHDOGHKN` `{string @0x10, EEHJEEHMEFC @0x18}` | `EAAICKJKHED` has `List<EOPJHDOGHKN>` @0x98 (`msig.py`/`fields2025.py`) |

Wire keys **`Tag`** then **`Type`** — read from the 2025 formatter `LBOEDPPEOJI` `.ctor 0x772D820`,
trailing `____stringByteKeys` run `0x772DA0D..0x772DA64`. Both literals are present in the 2023
string table too.

`Type` enum, **identical on both builds** (`IHJBBBIJIDH` on 2023, `EEHJEEHMEFC` on 2025):
**`General 0`, `Auto 1`, `AGOnly 2`, `Banned 3`**.

## No build branch is needed for this field

The original note told you to branch on the JWT `ver` claim. **That is unnecessary** — both builds
take the same object form. (The `ver` branch is still right for genuinely divergent fields; this just
is not one of them.)

## The failure it causes

Utf8Json hits `"` where it expects `{`, the deserialize throws, and the **entire response is
discarded** — after the server has already done the work and returned **200**. So the symptom is:
the event really is created or renamed server-side, HTTP 200, and the client still shows an error.
The same single field breaks `POST api/playerevents/v2` and every one of the nine per-field PUTs
identically.

Exception name identifies the client ([two-client-builds-name-check](../../../il2cpp-analysis/references/two-client-builds-name-check.md)):
`HEBOAMGAJAG` = `recflare-client`, `IONCMJIACFI` = `recflare-2025`.

## How the original error happened

The 2023 side was derived properly, from `il2cpp-tools/out/DummyDll/RecNet.Runtime.dll` via
Mono.Cecil. The 2025 side was **inferred, not read** — the note even sourced the `Tag`/`Type` key
names *from* 2025's `EOPJHDOGHKN`, the very type that proves 2025 uses objects, while its table
claimed 2025 used strings. The evidence and the conclusion contradicted each other inside one note.

**Lesson: read the field on each build you are claiming about.** A per-build table is exactly where
one side gets assumed from the other.

## Still valid: the DummyDll technique

`recflare-client`'s `GameAssembly.dll` was missing when this note was written, and a Mono.Cecil pass
over `il2cpp-tools/out/DummyDll/` answered the shape question from type and field signatures alone.
That build's binary is available again at `C:\Games\recflare-2023` (156,069,888 bytes), and
`il2cpp-tools/out/dump.cs` indexes it — so either route works now.
