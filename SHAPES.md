# Recovering DTO and endpoint wire shapes

How to find out what JSON the client actually expects, when the code is obfuscated IL2CPP and there
is no API documentation. This is the procedure that produced the invention, account, subroom and
Photon connection-info shapes.

> **All obfuscated names in this file are examples from the 20230414 build** (`GameAssembly.dll`
> mtime 2026-07-23). They re-roll every game build. The *signatures* and the procedure are what
> survive — always re-resolve names, never copy them forward. See CLAUDE.md.

---

## 0. Why you can't just read it

The DLLs under `BepInEx/interop` are Il2CppInterop **stubs** — method bodies only marshal into
`GameAssembly.dll`. Decompiling them shows no logic. Two sources actually carry information:

| Source | Gives you | Caveat |
| --- | --- | --- |
| **Il2CppDumper** output (`dump.cs`, `script.json`, `stringliteral.json`) | field order, field **offsets**, RVAs, string literals | a snapshot — must match the installed binary |
| **Live interop via Mono.Cecil** | what you actually compile and patch against | no offsets, no bodies |

**Use both and cross-check.** A dump from a different build silently produces a plausible, wrong
answer — that has cost real time here. Confirm the dump's `GameAssembly.dll` mtime/size matches the
installed one before trusting any RVA.

---

## 1. The core trick: Utf8Json generated formatters

The client serializes with Utf8Json, and its **generated formatters hold the wire names as plain
string literals**. This is the single highest-value technique in this document — the field names are
*not* the obfuscated property names, they are real, and they are recoverable exactly.

Find the formatter for a DTO by its signature (in `dump.cs`):

```csharp
public sealed class GPAFKEPAJOG : MJFBLDENKJM<IKCIDEMLEIA>, CMMCGLEIHLB
{
    private readonly KIDNBPBMGMO NDPCKELFFEM;   // AutomataDictionary  ____keyMapping
    private readonly byte[][]    DLPJHHIHOLN;   // byte[][]            ____stringByteKeys

    public void .ctor() { }                                              // <-- the literals live here
    public void         IIADKJHBOIN(ref …, IKCIDEMLEIA, …) { }   // Slot 4 = Serialize
    public IKCIDEMLEIA  BBCFAILGGHN(ref …, …)              { }   // Slot 5 = Deserialize
}
```

The identifying shape, independent of names: **`sealed class … : <formatter-base><TDto>, <marker>`
with a `byte[][]` field, a `.ctor`, and exactly two virtual methods at consecutive slots** — one
taking `TDto` (serialize), one returning it (deserialize). Grep `dump.cs` for `<TDto>` to find it:

```sh
grep -n "IKCIDEMLEIA" dump.cs | grep "class "
```

Then dump the literals from the `.ctor` in order:

```sh
py names.py <ctor_rva_hex> [len_hex]      # e.g. py names.py 387BD30 700
```

`names.py` disassembles the ctor and resolves every RIP-relative reference against
`stringliteral.json`. Prefer it over `disfn.py` for this: `disfn.py` streams the 312 MB
`script.json` and takes minutes; `names.py` reads the 4 MB literal map and is instant.

### What you get, and how to read it

- **Three casings per field** (`birthday` / `Birthday` / `BIRTHDAY`, `inventionId` / `InventionId` /
  `INVENTIONID`). Utf8Json accepts any of them, so pick whichever your server already emits.
- The literals come out in **hash-bucket order, not declaration order.** Don't infer field order from
  this list — get order from the `dump.cs` class block (§2).
- **Unknown members are dropped silently.** Sending extra fields is harmless; the client simply
  ignores them. This is why a payload can look wrong and still work.

---

## 2. Field order, offsets, and what they're for

The `dump.cs` class block gives declaration order *and* byte offsets:

```csharp
public class IKCIDEMLEIA : DFDECAEJBIO
{
    private ObscuredString      <PIMPMNOPEFF>k__BackingField; // 0x88
    private ObscuredString      <BHIDBDJBJHB>k__BackingField; // 0x90
    private Nullable<DateTime>  <NHPCMCBLJFO>k__BackingField; // 0x98
    …
}
```

Two uses:

1. **Pair names to types.** Match the `names.py` literal list against the field list by type — one
   `DateTime?`, two strings, one enum, etc. Usually unambiguous.
2. **Pin a field from a disassembly.** When an instruction reads `[rax + 0x98]`, the offset names the
   field exactly. This is how the junior-account bug was tied to `birthday` (see JUNIOR.md).

Nested/derived DTOs: fields below the base class's size are the derived ones. A DTO base with a
`Slot: 4` virtual (a post-deserialize hook) is common — here `GHAILDIJJJO`, with ~293 subclasses.

### Type tells

| Type in dump | Means |
| --- | --- |
| `Nullable<T>` | **optional** — the server controls whether it's present. These are where "Nullable object must have a value." bugs come from. |
| `ObscuredString` / `ObscuredInt` / `ObscuredBool` | CodeStage AntiCheat wrappers. Wire format is the plain underlying value; the obfuscation is in-memory only. |
| `Il2CppStructArray<byte>` | protobuf payload, not JSON — stop looking for a shape and go find the `.proto` message. |

**Enumerate the nullables first.** They are the smallest, highest-yield list: exactly the fields whose
absence changes client behaviour. For the invention details DTO that was `firstPublishedAt`,
`creationRoomId`, `price`; for the account DTO, `birthday`.

---

## 3. Envelope or bare?

Some endpoints return a bare object, others wrap it. Both exist in this client:

- **bare** — invention details/version, account: the DTO is the whole body.
- **enveloped** — subroom data save: `{success, error, value:{…}}`.

Tell them apart by looking at what the call site deserializes into. If the formatter's `TDto` has
`success` / `error` / `value` members, it's an envelope and `value` holds the real DTO — recurse into
*that* type's formatter. If not, the body is bare.

Do not guess from a sibling endpoint; it is not consistent across the API.

---

## 4. Finding the endpoint itself

URLs and path templates are string literals:

```sh
# in the dump
grep -n "inventions/v1" out/stringliteral.json

# or straight from metadata, no dump needed
grep -a -o -E '[ -~]{4,}' RecRoom_Data/il2cpp_data/Metadata/global-metadata.dat | grep -i invention
```

Then `xref.py` maps a literal address to the method that references it, and `smcalls.py` /
`callers.py` walk outward from there to the handler.

If the refs land in a `.cctor`, the string is a **table entry**, not the logic — find the enum key and
x-ref the enum→value converters instead.

---

## 5. Confirming at runtime (do this — static reading is not proof)

Static analysis gets the shape; only a launch proves it. Several confident static readings in this
repo turned out wrong.

- **`[Advanced] Debug = true`** logs request and response bodies from inside BestHTTP. This is the
  primary tool. (It also logs auth tokens and passwords — don't paste logs around.)
- **A system-level mitmproxy sees nothing.** BestHTTP does not use the Windows system proxy. Don't
  conclude "no calls are being made" from an empty proxy.
- For "did the client accept it?", find the method that only runs on success and prefix-log it — a
  bracket probe (prefix + postfix) shows both entry and completion. See JUNIOR.md for which method
  shapes can actually be hooked; async `MoveNext` bodies and constructors **cannot**.

---

## 6. Order of operations

1. Confirm the dump matches the installed `GameAssembly.dll` (mtime + size).
2. Find the DTO type — from the handler, or by grepping a field name you already know.
3. Find its formatter (`grep "class " dump.cs | grep <TDto>`), note the `.ctor` RVA.
4. `py names.py <rva>` → the wire names.
5. Read the `dump.cs` class block → declaration order, offsets, and the **nullable list**.
6. Check for an envelope; recurse if present.
7. Re-verify the type still exists in the **live interop** with Cecil before acting on it.
8. Launch with `Debug = true` and diff the real traffic against what you derived.

## Tooling

Scripts live in the session scratchpad `il2cpp/`; copy them somewhere permanent if you want them to
survive. All expect `out/` (Il2CppDumper output) alongside them and a `methods.pkl` — a pickled,
sorted `(rva, name)` table built from `script.json`.

| Script | Purpose |
| --- | --- |
| `names.py <rva> [len]` | **wire names from a Utf8Json formatter `.ctor`** — the main one |
| `smcalls.py <name>` | a method's direct callees, in call order, RecRoom code flagged |
| `nullscan.py <regex>` | which methods call `Nullable<T>.get_Value` |
| `rangedis.py <a> <b>` | disassemble an arbitrary RVA range, call targets resolved |
| `disfn.py <rva> <len>` | disassemble a method with string literals resolved (slow) |
| `xref.py`, `callers.py` | literal/method cross-references |

> `disfn.py` has a known bug: it tests `operands[0].type == 1` for call targets, but Capstone's
> `X86_OP_IMM == 2`, so call annotations never print. Use `smcalls.py` or `rangedis.py` for calls.
