# il2cpp-tools — wire-shape toolkit

Scripts for recovering endpoint and DTO wire shapes from an obfuscated IL2CPP Rec Room client.
Companion to `SHAPES.md`. Refreshed **2026-08-18** against `recflare-2025` (build `20250718.01`).

> **Read this first if you last used the 2026-08-04 bundle.** That bundle assumed Il2CppDumper
> output (`out/script.json`, `out/dump.cs`, `out/stringliteral.json`) exists. **On the 2025 build it
> cannot be produced** — the shipped `global-metadata.dat` is a 47,962,260-byte decoy of repeated
> `0x52`, `.text`/`il2cpp` are encrypted at rest, `Il2CppCodeRegistration` is field-permuted, and
> Il2CppDumper's PE-loader fallback dies because `GameAssembly.dll` imports Referee. Everything the
> tools need is now produced by the carve pipeline in `carve/` instead. `SHAPES.md` §0/§4/§6 still
> describe the old Il2CppDumper flow and are stale for this build; the technique in §1
> (Utf8Json generated formatters) is unchanged and still the core trick.

## Layout

- **root** — analysis scripts, split into two tiers below.
- **`carve/`** — the pipeline that produces the inputs. Run this first on a new build.

## What is not here — and why

The **generated indexes are not committed**: `methods.pkl` (16 MB), `rva2025.pkl` (19 MB) and
`out/stringliteral.json` (7 MB), along with the carved `GameAssembly.dll` and `global-metadata.dat`.
They are derived from the game binary, they are large, and they are **specific to one build** — a
copy from the wrong build resolves every address to a confident wrong name rather than failing.
`.gitignore` keeps them out.

Produce them yourself with `carve/` below; it takes a few minutes against a running client. Then
verify before trusting anything:

```sh
python -c "import pickle;t=pickle.load(open('methods.pkl','rb'));print(len(t))"   # ~346,938
```

and the anchor: on `20250718.01`, RVA `0x77E0950` must resolve to
`BestHTTP.HTTPManager$$SendRequest`. If it does not, your index and your client disagree — stop and
re-carve.

## carve/ — produce the inputs (once per build)

`metadump.exe` is a passive reader (`OpenProcess` + `ReadProcessMemory`); it never writes to the
game or calls into it. Start it **before** launching, then play to the title screen.

```sh
carve/metadump.exe               # -> out/{ga_image.bin, metadata.bin, manifest.txt}
python carve/solve_header.py     # recover the shuffled metadata header
python carve/idtables.py         # identify regions by content ...
python carve/idtables2.py        # ... by cross-referenced counts ...
python carve/idtables3.py        # ... and the remainder
python carve/rebuild_metadata.py # -> out/global-metadata.dat
python carve/rebuild_binary.py   # -> out/GameAssembly.dll  (decrypted code spliced into disk PE)
python carve/mkindex2025.py      # -> methods.pkl + out/stringliteral.json
```

`carve/CARVE.md` has the per-stage findings and why each step is shaped the way it is.
Rebuild `metadump.exe` from `metadump.c` with `cl /O2 metadump.c` in an **amd64** VS shell if you'd
rather not trust the prebuilt binary.

**Build-specific constants are baked into `slots2025.py`, `fields2025.py` and
`carve/mkindex2025.py`** — metadata table offsets, `METADATA_REGISTRATION_RAW`,
`CODEGEN_MODULES_RAW`, `TD_N`, `LOAD_BASE`. A new client changes all of them. `idtables*.py` and
`rebuild_metadata.py` print the new values; copy them across before using the tier-A scripts.

## Configuration

**Set all three.** The in-script defaults are absolute paths on the machine the toolkit was written
on (`C:\Games\recnet-patcher\tools\metadump\out\...`). On any other machine they are simply
wrong, and if something *is* at that path — an older build, a half-finished carve — the scripts read
it without complaint. Export them explicitly every session:

```sh
export GAMEASSEMBLY=/path/to/carve/out/GameAssembly.dll
export GA_IMAGE=/path/to/carve/out/ga_image.bin
export GA_METADATA=/path/to/carve/out/global-metadata.dat
```

Scripts read these, falling back to those hardcoded paths:

| var | file |
| --- | --- |
| `GAMEASSEMBLY` | rebuilt `GameAssembly.dll` |
| `GA_IMAGE` | `ga_image.bin` (decrypted memory image) |
| `GA_METADATA` | rebuilt `global-metadata.dat` |

`methods.pkl` and `out/stringliteral.json` are read from the **working directory**, not from
alongside the script. So keep your carved index wherever you like and invoke the toolkit by path:

```sh
cd /path/to/my-build-index          # holds methods.pkl + out/stringliteral.json
python /path/to/skills/tools/il2cpp/rangedis.py 0x77E0950 0x77E0A00
```

Scripts that need only metadata (`msig.py`, `fields2025.py`, `ftypes.py`, `enumvals.py`, `iface.py`)
read the three env vars alone and run from anywhere. The rest fail with a bare
`FileNotFoundError: methods.pkl` if the working directory is wrong — that is the symptom, not a bug.

## Tier A — works on a carved build (no Il2CppDumper)

| script | purpose |
| --- | --- |
| `names.py <ctor_rva> [len]` | **wire names from a Utf8Json formatter `.ctor`** — the main one |
| `fields2025.py <TypeName>...` | a type's fields with runtime offsets, straight from metadata |
| `slots2025.py <rva> [len]` | all six metadata-usage kinds resolved (types, methods, literals) |
| `mxref.py <slot_rva>...` | who *references* a literal/type slot (rip-relative) |
| `callxref.py <rva>...` | who *calls* a method (direct `E8`/`E9`) |
| `fxref.py <rva>...` | older rip-relative xref; `mxref.py` supersedes it |
| `rangedis.py <a> <b>` | disassemble an RVA range, call targets resolved |
| `callsites.py`, `smcalls.py <name>` | call sites / a method's callees |
| `nullscan.py <regex>` | methods calling `Nullable<T>.get_Value` |
| `cg.py` | call graph — **run `nullscan.py` first**, it consumes `nullable_xref.txt` |
| `whatis2025.py <rva> [--dump <dir>]` | RVA -> name from an RVA-annotated Cpp2IL dump |

`whatis2025.py` defaults to the **2025-04-29** dump. Pass `--dump` for any other build and check the
printed anchor line — `HTTPManager.SendRequest` must be `0x77E0950` on `20250718.01`.

### Added since the 2026-08-18 refresh

All tier A — they work on a carved build.

| script | purpose |
| --- | --- |
| `msig.py <TypeName>` | every method on a type with full signatures — the fastest way to find a facade's route helpers |
| `ftypes.py <TypeName>` | fields with declared CLR types (pair with `fields2025.py` for offsets) |
| `typeslots.py <TypeName>` | the metadata-usage slots naming a type; feed them to `mxref.py` to find its consumers |
| `iface.py <TypeName>` | base class + implemented interfaces — how a Utf8Json formatter is matched to its DTO (`IHCMHKGLBEA`1<T>`) |
| `ginst.py inst <N>` / `spec <N>` | resolve a generic instantiation or methodSpec index to real type arguments |
| `ginstscan.py` | search generic instantiations by shape |
| `enumvals.py <EnumType>` | enum member names **with values** — they are zigzag-compressed in `fieldDefaultValues`, so a raw read returns garbage |
| `fieldfind.py <offset>` | which types have a field at a given offset |
| `imgtypes.py <Assembly>` | types in one image — used to fingerprint bundled package versions (all stripped to 0.0.0.0) |
| `sendscan.py` / `sendscan2.py` / `sendreport.py` | sweep every HTTP send call site and its response `T`; produced `nonobject-responses.txt` |
| `notifall.py` / `notifreport.py` | sweep websocket notification registrations; produced `notifications-2025.txt` |
| `bundlescan.py <dir> <terms> [limit]` | decompress and grep Unity addressable bundles (2745 of them in ~85 s) |
| `lz4b.py` | pure-Python LZ4 block decompressor `bundlescan.py` depends on |
| `aacatalog.py <aa-dir> <key...>` | Addressables catalog.json lookup: asset GUID -> asset path -> owning .bundle (first listed) + its deps |
| `bundlepeek.py <dir> <bundles> <needles>` | decompress named bundles and say which one actually contains a string — the confirmation step after `aacatalog.py` |
| `caiexport.py build\|verify` | build or verify a CustomAvatarItem export folder byte-identically (SHA-256 hashes, System.Text.Json default encoder, duplicated `N_save.json`) |
| `descresolve.py <data-dir> <desc>` | AvatarItemDesc -> registry -> asset guid -> catalog -> `Assets/.../(Name).prefab` + owning bundle; prints the **system name**. No item name needed. Tries both desc spellings and multi-token keys. |
| `caiids.py <desc>` | deterministic, v4-shaped `CustomAvatarItemId` / `UnityAssetId` derived from the DESC (the unique key -- the system name is not, several descs share one). Canonicalises spelling/commas first, so a re-export never mints a duplicate. |

`enumvals.py` raises on a type that is not an enum — that is the check, not a bug.

### Generated tables kept here

`nonobject-responses.txt` — the routes whose response `T` is a List/array/scalar, i.e. every endpoint
that hard-fails on a `{}` body. It is a **lower bound**: it misses facade helpers and
`String.Format`-built paths, and treats enum `T` as an object. `notifications-2025.txt` — the 49
websocket channel ids with their payload DTOs. Both are for `20250718.01`; regenerate with the
`sendscan`/`notifall` scripts on a new build.

## Tier B — legacy, needs Il2CppDumper `out/`

`callers.py`, `disasm.py`, `disfn.py`, `dtoshape.py`, `findm.py`, `gateconfigs.py`, `mkmethods.py`,
`regall.py`, `regmap.py`, `slots.py`, `whatis.py`, `xref.py`, `xref2.py`.

These read `out/script.json` or `out/dump.cs` and only work on builds Il2CppDumper can process.
`dtoshape.py` is the old one-shot DTO dumper — on a carved build use `names.py` + `fields2025.py`.

## Gotchas that cost real time

- **This client strips `IMAGE_SCN_MEM_EXECUTE`** (code sections are `0xC0000020`; exec is granted at
  runtime). Any tool filtering sections on `MEM_EXECUTE` matches nothing and reports **0 refs for
  every target, silently**. `fxref.py` had exactly this bug — fixed here to filter on `CNT_CODE`.
- **Metadata-usage slots live in `.data` on disk only.** Generated code reaches literals through
  globals initialised to `(kind << 29) | (index * 2 + 1)`; the runtime overwrites them with real
  pointers. Read `.data`/`.rdata` from the **disk** PE, code from `ga_image.bin`.
- **Only `.text` and `il2cpp` may be spliced from memory.** `il2cpp_init` rewrites `.data` in place.
- **Pair formatter keys to members by position and type, not by name.** The obfuscator does not keep
  the `<prop>k__BackingField` convention, so Cpp2IL property names and metadata backing-field names
  disagree. `[DataMember(Name=…)]` attributes landing on the expected index are the cross-check.
- **Enums go on the wire as numbers** unless a by-name formatter exists — and if one did, every
  member name would appear in `stringliteral.json`. Checking a few distinctive member names against
  the literal table settles it in seconds.
- **Resolve a generic call's real type argument from the methodSpec's generic inst**
  (`MetadataRegistration` `_mr[2]/_mr[3]`), not from a nearby `TypeInfo` slot — they can differ.
- **Jump tables hide switch cases.** Grepping for a `cmp reg, <imm>` immediate gives a false negative
  when the dispatch compiled to a jump table. Always run a positive control with a value you know is
  handled before concluding a case does not exist.
- **`rangedis.py` desyncs in padded regions.** A linear sweep that walks into alignment padding
  decodes garbage that still looks like instructions. Bound the window by the next method start.
- **A window that overruns attributes the *next* method's calls to yours.** `names.py <rva> 1000`
  reads 0x1000 bytes and will cross the boundary — check the length against the next entry in
  `methods.pkl`.
- **Shared generic bodies are not in `methods.pkl`.** One RVA serves every instantiation of a shape,
  so some methods (the Dissonance networking regions, `IMAGJAIKIPF`'s completion logic) have no
  entry at all. An empty lookup there means "not indexed", not "does not exist".
