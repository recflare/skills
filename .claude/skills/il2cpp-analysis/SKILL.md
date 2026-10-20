---
name: il2cpp-analysis
description: Statically analyse an obfuscated IL2CPP Rec Room build - carving real metadata and decrypted code out of a live process when Il2CppDumper cannot run, driving the il2cpp-2025 toolkit (methods.pkl, slots2025, fields2025, enumvals, ginst), decompressing Unity addressable bundles to grep them, telling two client builds apart from a stack trace, and reading Rec Room's log facade frames. Use before resolving any obfuscated name, RVA or enum value.
---

# Analysing an obfuscated IL2CPP build

The tooling and technique layer under every other skill here. If you are about to trust an
obfuscated name, an RVA or an enum value, this is what establishes it.

## Do this first, every time

1. **Identify the build.** Two are in play and their obfuscated names are completely different -
   `two-client-builds-name-check`. A name resolved against the wrong build is silently plausible and
   wrong.
2. **Verify the index is not stale.** A stale `methods.pkl` resolves every address to a confident
   wrong name. The anchor check is in `recflare-2025-metadata-carve`.
3. **Only then** resolve names.

## Getting an index at all

For builds where Il2CppDumper works, use it. For **build 20250718.01 it cannot** - the shipped
`global-metadata.dat` is a multi-megabyte decoy of repeated `0x52`, the code sections are encrypted
at rest, and the PE-loader fallback dies on the Referee import. `recflare-2025-metadata-carve` has
the live-process carve pipeline that produces a real `global-metadata.dat`, a decrypted
`GameAssembly.dll`, `methods.pkl` and `out/stringliteral.json`.

The pipeline and every analysis script are in **`tools/il2cpp/`** in this repo; its README has the
run order, the per-script table and the build-specific constants you must copy across for a new
client. The indexes themselves are deliberately not committed — regenerate and verify the anchor
(`0x77E0950` -> `BestHTTP.HTTPManager$$SendRequest` on `20250718.01`) before trusting a name.

## Reading values, not just names

- **Enum member values** are zigzag-compressed ints in `fieldDefaultValues`; a raw little-endian read
  returns garbage that looks like data. `il2cpp-field-default-values-compressed`.
- **Generic instantiations** must come from the methodSpec at the call site, never from a nearby
  `TypeInfo` slot. Same note, plus `ginst.py`.

## Searching assets

`unity-bundle-text-scanning` - addressable bundles are LZ4-compressed, so a raw byte scan of
`StreamingAssets/aa` finds nothing **including your control**, which reads as a confident negative.
Decompress first, and always run a positive control before believing an absence.

## Reading a crash

`unity-log-facade-frames` - the top five frames of any Rec Room Unity stack trace are the logging
facade and carry no information. Start at the sixth.

## What survives a client upgrade

Enum member names and values, compiler-generated names (`<Method>b__0`), Utf8Json key literals,
`[DataMember]` renames, and named string channels. **Everything else re-rolls** - every obfuscated
type/method name, every RVA, every metadata table offset. Re-derive from signatures and literals;
never carry an obfuscated name across a build.

## References

| Reference | What it settles |
|---|---|
| [il2cpp-field-default-values-compressed](references/il2cpp-field-default-values-compressed.md) | Enum member values live in fieldDefaultValues as il2cpp COMPRESSED (zigzag) ints, not raw LE — plus il2cpp-2025/enumvals.py and ginst.py, which close the two long-standing gaps in the toolkit. |
| [recflare-2025-metadata-carve](references/recflare-2025-metadata-carve.md) | recflare-2025 (build 20250718.01) is now fully statically analysable — live carve pipeline in tools/metadump plus a working il2cpp-tools index in il2cpp-2025. |
| [protobuf-descriptor-recovery](references/protobuf-descriptor-recovery.md) | Rec Room's protobuf types keep their REAL names: protoc embeds the whole FileDescriptorProto as 60-char base64 literals that the generated <File>Reflection..cctor passes to string.Concat. Take the `mov` run from names.py on that cctor (literal-table order is NOT concat order) and you recover exact message/field/enum names - the protobuf analogue of msig.py. |
| [two-client-builds-name-check](references/two-client-builds-name-check.md) | TWO client builds are in play — recflare-2025 (20250718.01, MGPBDIAGCFD/IONCMJIACFI) and recflare-client (2026-07-23, BGBHKBJEMPI/HEBOAMGAJAG). Check which one a stack trace belongs to BEFORE resolving any obfuscated name. |
| [unity-bundle-text-scanning](references/unity-bundle-text-scanning.md) | bundlescan.py + lz4b.py decompress Rec Room's LZ4 addressable bundles in pure Python and grep them for text — 2745 (2025, UnityFS v8) in ~85 s, 6499 (2023, v7) in ~168 s. CORRECTED 2026-09-23: align on version>=7, NOT flags&0x200, or every v7 bundle decodes empty and the scan reports a clean hits=0. |
| [unity-log-facade-frames](references/unity-log-facade-frames.md) | In Rec Room Unity-side stack traces the top 5 frames are always the logging facade (DFFFAEKJJHP / CFGDDKLPHOL`1 / HDOEMDBOEDB) — noise. The first real frame is the one below them; room-gameplay components keep their real names. |
