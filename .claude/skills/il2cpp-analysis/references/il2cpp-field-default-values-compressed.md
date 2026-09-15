# IL2CPP field default values compressed

> Enum member values live in fieldDefaultValues as il2cpp COMPRESSED (zigzag) ints, not raw LE — plus il2cpp-2025/enumvals.py and ginst.py, which close the two long-standing gaps in the toolkit.

Written **2026-08-24** while deriving [avatar-lockeditems-bulk-wire-shape](../../wire-shapes/references/endpoints/avatar-lockeditems-bulk-wire-shape.md). Fills the
"need a `fieldDefaultValues` walker" and "cannot resolve generic instantiations" gaps in
[recflare-2025-metadata-carve](recflare-2025-metadata-carve.md).

**The trap:** `Il2CppFieldDefaultValue.dataIndex` entries for an enum step by **1–5 bytes, not by the
enum's declared width**, because the value is stored as an il2cpp *compressed* integer — and for
signed underlying types it is **zigzag**-encoded on top. Reading 4 raw LE bytes for an `int` enum
yields plausible-looking garbage (`Public = 33555458`), which is worse than an error.

```
uint: b<0x80 -> b | (b&0xC0)==0x80 -> ((b&0x3F)<<8)|b1 | (b&0xE0)==0xC0 -> 4-byte
      0xF0 -> u32 LE at +1 | 0xFE,0xFF -> sentinels
int : e = uint; if e==0xFFFFFFFF -> INT_MIN; neg = e&1; e >>= 1; return neg ? -(e+1) : e
```

**Second trap, found 2026-08-24:** **byte/sbyte-backed enums store a RAW byte, not a compressed
int.** `ChatMessage.ModerationState.MarkedForDelete` is stored as `0xFF` = **255**, which the
compressed reader decodes as the `0xFFFFFFFF` sentinel. `enumvals.py` now special-cases 1-byte
underlying types. Values below 128 are identical either way, which is why this hid for so long.

Verified against two independently known enums: `KJMOLELGPPF` (byte, Accounts 0 … 8, see
[algorithmiclists-wire-shape](../../wire-shapes/references/endpoints/algorithmiclists-wire-shape.md)) and `KLKIFENPGNG` (int, Private 0 / Public 1 / Unlisted 2, see
[outfits-me-saved-wire-shape](../../wire-shapes/references/endpoints/outfits-me-saved-wire-shape.md)), plus `System.Net.HttpStatusCode` (`OK` decodes to 200).

**New tools in `il2cpp-2025/`:**
- `py enumvals.py <TypeName> …` — enum members with real values; reads the underlying type from
  `value__` and picks signed/unsigned decoding accordingly.
- `py ginst.py inst <N>` / `py ginst.py spec <N>` — resolves the `<generic inst class=… method=…>`
  numbers that `slots2025.py` prints. **`method=N` is a genericInst index, not a methodSpec index** —
  use `inst`, not `spec`. This is what turns `MGPBDIAGCFD::HPBKMCLEANE <generic inst method=91389>`
  into `HPBKMCLEANE<List<BGJHOEKDNED>>`, i.e. it names the response DTO directly.

- `py msig.py <TypeName>` — every method of a type with its **full signature** (return type + param
  types and names), resolved through the same generic-instantiation walker. This is how you pick the
  right interface slot out of a `call <helper>` with `ecx = <slot>`: dump the interface, count from 0.
- `py iface.py <InterfaceName>` — the typedefs that implement an interface (walks `interfaces[]` and
  matches on the interface's `byvalTypeIndex`).

Metadata header (v31) offsets used: `0x58` parameters, `0x88` interfaces, `0x18` string, `0x30` methods, `0x40` fieldDefaultValues,
`0x48` fieldAndParameterDefaultValueData, `0x60` fields, `0xA0` typeDefinitions.

**Compiler-generated names survive obfuscation, and async state machines are full of them.** A
`<Method>d__N` capture-field dump (`fields2025.py`) often names the whole algorithm for free —
`unifiedItemIds`, `watchStorefrontTask`, `storeItemsInInitialOrder` — when every surrounding type and
method is an 11-char scramble.

**Also note:** `whatis2025.py` indexes the **2025-04-29** dump, which is the *wrong build* — it will
happily name any RVA. `methods.pkl` (live capture, `20250718.01`) is the authority; ignore
`whatis2025.py` output for this client.
