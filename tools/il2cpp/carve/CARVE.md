# metadump — live carve for recflare-2025 (build 20250718.01)

Static analysis of this client is impossible from disk: `global-metadata.dat` is a 47,962,260-byte
decoy of repeated `0x52`, and `.text` + `il2cpp` are encrypted at rest (entropy 8.000). Both are
decrypted during `il2cpp_init`, so the only source is a running process. This is DUMPING.md stages
1–3 implemented for that build.

The Cpp2IL dump at `RecRoom_Info/Code/2025-07-19_02-45-25` matches this client (verify:
`BestHTTP.HTTPManager.SendRequest` = RVA `0x77E0950`) but is **signature-only** — no method bodies
for formatters, no string literals. That is what this pipeline replaces.

## Run order

```sh
metadump.exe                  # start FIRST; polls for Recroom_Release.exe, then captures
                              #   out/ga_image.bin   GameAssembly flattened by RVA (decrypted)
                              #   out/metadata.bin   the private allocation holding real metadata
                              #   out/manifest.txt   bases, region table, decryption sanity check
python solve_header.py        # recover the table layout from the permuted header
python idtables.py            # identify regions by content (string blob, literals, ...)
python idtables2.py           # pin tables by counts cross-referenced from typeDefinitions/methods
python idtables3.py           # pin the remainder (generic containers, default values, ...)
python rebuild_metadata.py    # -> out/global-metadata.dat  (canonical header, <Module> repaired)
python rebuild_binary.py      # -> out/GameAssembly.dll     (decrypted code spliced into disk PE)
python mkindex2025.py         # -> ../../il2cpp-2025/{methods.pkl, out/stringliteral.json}
```

`metadump.exe` is a pure reader (`OpenProcess` + `ReadProcessMemory`); it never writes to the game
or calls into it, so it does not disturb the `2025Patch.dll` injection.

## What each stage learned

- **Header.** 64 ints at `0x00`; magic/version overwritten and the 31 `{offset, size}` slots
  shuffled. The tables tile the file end to end from `0x100`, and here the tiling is **unique**,
  ending at `0x2DBD894` (47,962,260) — the decoy was made exactly file-sized. Two leftover slots
  (`499489`, `302531`) are the old sanity/version fields.
- **Layout is shuffled too.** File-order region 0 is the *string blob*, not `stringLiteral`, so
  every table has to be identified by contents, not position. Anchors: `mscorlib.dll` for the string
  blob, `curatedlists/bulk` for `stringLiteralData`, the only 8-byte region that exactly tiles that
  blob for `stringLiteral`; then `typeDefinitions` (88-byte stride) and `methods` (36-byte stride)
  give exact counts for fields/events/properties/nestedTypes/interfaces/vtable/interfaceOffsets/
  parameters, each of which matches exactly one region.
- **`<Module>` repair.** 404 type definitions carry a junk `genericContainerIndex` (`nameIndex` was
  intact on this build). Il2CppDumper accepts the result: `Metadata Version: 31`.
- **Binary.** Only `.text` and `il2cpp` are spliced from memory; `.rdata`/`.data` must come from
  disk because `il2cpp_init` rewrites `.data` in place. x64 code is position-independent, so **zero**
  relocations land inside the spliced ranges (all 2,335,754 are in the data sections).

## Why Il2CppDumper still can't finish, and why it doesn't matter

`Il2CppCodeRegistration`'s fields are permuted and `codeGenModules` is shuffled out of image order,
so the auto-search fails; the PE-loader fallback then dies trying to `LoadLibrary` a DLL that imports
Referee. `mkindex2025.py` skips it and produces what the tools actually consume:

- `methods.pkl` — 346,938 `(rva, "Class$$Method")` pairs, built from image → type → method tokens
  indexed into each module's `methodPointers` (modules matched to images **by name**, since the array
  is alphabetical rather than in image order). 14 of the pointer arrays live in the `.data` BSS tail
  and are read from the memory image with runtime pointers rebased.
- `out/stringliteral.json` — 78,079 usage slots. Generated code reaches literals through globals
  statically initialised with `(kind << 29) | (index * 2 + 1)`; the runtime overwrites them with real
  pointers, which is the other reason `.data` has to come from disk. Kinds: 1 TypeInfo, 2 Il2CppType,
  3 MethodDef, 4 FieldInfo, 5 StringLiteral, 6 MethodRef.

`MetadataRegistration` is **not** permuted — found at raw `0xC1A5770` by its
`fieldOffsetsCount == typeDefinitionsSizesCount == 59728` signature. `codeGenModules` is at raw
`0xCD16D00`, 405 entries.

Verification (all EXACT): `0x77E0950` → `BestHTTP.HTTPManager$$SendRequest`,
`0x7CF32F0` → `HPJKKCCECLH$$BLDFMLMAFLH` (the image content-signature verifier the plugin hooks).

## Using it

`../../il2cpp-2025/` holds the il2cpp-tools scripts pointed at this build:

```sh
export GAMEASSEMBLY="C:\Games\recnet-patcher\tools\metadump\out\GameAssembly.dll"
python names.py <rva> <len>       # string literals a method references, in order
python fxref.py <slot_rva>        # who references a literal slot
python slots2025.py <rva> <len>   # metadata usages resolved WITHOUT script.json (slots.py needs it)
```

`slots2025.py` replaces `slots.py`/`whatis.py` here, since those parse Il2CppDumper's `script.json`.
Member CLR types still come from the Cpp2IL dump at `RecRoom_Info/Code/2025-07-19_02-45-25`.

## Caveat

The capture was taken with `2025Patch.dll` injected, so the handful of functions it detours carry a
MinHook `E9` at their entry in `ga_image.bin` (visible at `0x77E0950`). Harmless for metadata and
literal work; recapture without the plugin if a hooked prologue itself matters.
