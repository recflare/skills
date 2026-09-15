# Recflare 2025 metadata carve

> recflare-2025 (build 20250718.01) is now fully statically analysable — live carve pipeline in tools/metadump plus a working il2cpp-tools index in il2cpp-2025.

As of **2026-08-17**, `C:\Games\recflare-2025` (build `20250718.01`) can be analysed statically. It
ships a decoy `global-metadata.dat` (47,962,260 bytes of `0x52`) and encrypted `.text`/`il2cpp`, so
the Cpp2IL dump `RecRoom_Info/Code/2025-07-19_02-45-25` — which matches this client, verify
`SendRequest = 0x77E0950` — is signature-only: **no formatter bodies and no string literals**. That
is why "read the Utf8Json keys out of dump.cs" never works here.

The carve lives in `C:\Games\recnet-patcher\tools\metadump` (see its README for the run order and
the per-stage findings). `metadump.exe` is a pure reader and needs the game running; everything after
it is offline. Output index is `C:\Games\recnet-patcher\il2cpp-2025\` — `methods.pkl` (346,938
methods, verified EXACT on `0x77E0950` and `0x7CF32F0`) and `out/stringliteral.json` (78,079 slots).

Two facts worth keeping even if the pipeline is rewritten:

- **Il2CppDumper cannot finish on this build** — `Il2CppCodeRegistration` is field-permuted and its
  PE-loader fallback dies on `LoadLibrary` (GameAssembly imports Referee). `mkindex2025.py` bypasses
  it entirely. `MetadataRegistration` is *not* permuted.
- **String literals are recoverable without `script.json`.** Generated code reaches them through
  globals statically initialised in `.data` with `(kind << 29) | (index * 2 + 1)` (kind 5 =
  StringLiteral); the runtime overwrites them with pointers, so `.data` must come from **disk**, not
  from the memory image. `slots2025.py` resolves all six usage kinds this way.

**Getting wire keys without `dump.cs`.** `dtoshape.py` cannot run here (it opens `out/dump.cs`, which
this build has no way to produce). Use `names.py` on the **formatter's .ctor** instead — find
`XXXX : IHCMHKGLBEA<Dto>` in the Cpp2IL dump, take its ctor RVA, then
`$env:GAMEASSEMBLY="C:\Games\recnet-patcher\tools\metadump\out\GameAssembly.dll"; py names.py <ctor> 1200`.
Output is two blocks: `lea` = `____keyMapping` (all three casings, interleaved/unordered) and a
trailing `mov` block = `____stringByteKeys`, **one entry per member in declaration order** — that
second block is the shape. Pair it with the property list from the Cpp2IL dump and offsets fall out
as `0x10 + 8*i` (backing fields exist even for `[IgnoreDataMember]` members, so count those too).
Worked end-to-end on `api/config/v2` 2026-08-17.

**`fxref.py` silently returns 0 refs on this build.** It filters sections by
`IMAGE_SCN_MEM_EXECUTE`, and this client ships `.text`/`il2cpp` as `0xC0000020` — exec is granted at
runtime, so the filter matches nothing and every query reports "0 rip-relative ref(s)" instead of
failing. Use `il2cpp-2025/mxref.py <slot_rva>` instead: same scan over `ga_image.bin`, filtered on
`IMAGE_SCN_CNT_CODE`, chunked so the 154 MB `il2cpp` section fits in memory. This is what made
literal→method lookup work at all.

`il2cpp-2025/fields2025.py <TypeName>` lists a type's fields with runtime offsets straight from the
carved metadata (`MetadataRegistration.fieldOffsets`, `_mr[10]/_mr[11]`). Cpp2IL only annotates
`FieldOffset` on real fields, so auto-property backing fields — which is all a RecNet DTO has — have
no offsets in the dump. Pairing the offsets against a formatter's `____stringByteKeys` run is the
independent check that key order really matches declaration order, and it exposes
`[IgnoreDataMember]` members as backing fields with no key.

**Enums go on the wire as numbers.** Utf8Json only writes an enum by name if a by-name formatter was
generated, and that bakes every member name in as a string literal. On this build the distinctive
member names are simply absent from `out/stringliteral.json` (checked for RoomInstanceType,
MatchmakingPolicy, the matchmaking error enum, and the curated-list Type) — so no by-name formatter
exists and the value is numeric. Checking a few distinctive member names against the literal table is
the cheap way to settle this for any enum.

`whatis2025.py` defaults to the **2025-04-29** dump — always pass
`--dump C:\Games\RecRoom_Info\Code\2025-07-19_02-45-25` for this client. Its self-check used to
hardcode a single build's `SendRequest` RVA and shouted "WRONG DUMP" at the *correct* dump; fixed
2026-08-17 to look the anchor up by name and list all overloads.

Use `il2cpp-2025/` (not `il2cpp-tools/`) for anything targeting this client — `il2cpp-tools/out` is a
different, much older build with no curated lists at all (verified: zero hits for this build's type
names, none of its anchor RVAs). See [recflare-2025-working-client](../../rr-client-bringup/references/recflare-2025-working-client.md) and
[curatedlists-bulk-wire-shape](../../wire-shapes/references/endpoints/curatedlists-bulk-wire-shape.md).

**Why:** without this, any "what does the client expect for X" question on the 2025 client dead-ends,
because both the on-disk binary and the archived Cpp2IL dump are unusable for wire shapes.

**How to apply:** before answering a wire-shape question on recflare-2025, check that
`il2cpp-2025/methods.pkl` still resolves `0x77E0950` to `BestHTTP.HTTPManager$$SendRequest`; if the
client is ever re-downloaded, re-run the whole pipeline (the RVAs and region offsets are build-specific).
