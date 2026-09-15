# Two client builds name check

> TWO client builds are in play — recflare-2025 (20250718.01, MGPBDIAGCFD/IONCMJIACFI) and recflare-client (2026-07-23, BGBHKBJEMPI/HEBOAMGAJAG). Check which one a stack trace belongs to BEFORE resolving any obfuscated name.

Learned **2026-08-25** after answering a trace against the wrong carve's name table.

| build | version literal | request builder | malformed-response ex | dump |
|---|---|---|---|---|
| `recflare-2025` | **`20250718.01`** | `MGPBDIAGCFD` | `IONCMJIACFI` | `il2cpp-2025/` + `tools/metadump/out/` |
| `recflare-client` | **`20230414`** | `BGBHKBJEMPI` | `HEBOAMGAJAG` | `il2cpp-tools/` (`out/dump.cs`, `script.json`, `out/DummyDll/`) |

**`recflare-client` is the 2023-04-14 build** — confirmed by the sole `20[0-9]{6}` literal in its
string table (`"20230414"`); `recflare-2025`'s is `"20250718.01"`. So "recflare-client" is the
**older** of the two despite its newer file mtime (that is just when it was copied). Getting this
backwards inverts every per-build branch — see [playerevent-tags-build-difference](../../wire-shapes/references/endpoints/playerevent-tags-build-difference.md).

The server can branch on the JWT `ver` claim, which carries exactly these strings. `20250718.01` is
**not parseable as an int** — compare the leading 8 characters as a date/integer.

**One-line test on any pasted trace:** if it names `BGBHKBJEMPI` / `HEBOAMGAJAG` / `KIIINOPMMME` /
`FJBJEDDGNAB`, it is `recflare-client` → use `il2cpp-tools/`. If it names `MGPBDIAGCFD` /
`IONCMJIACFI` / `CBACIMLIBPF` / `KKEIDMPEHAL`, it is `recflare-2025` → use `il2cpp-2025/`.
Cheap check: `py -c "import pickle; ..."` over each `methods.pkl` — a name present in one is absent
in the other. Every obfuscated type/method name and every RVA re-rolls between them.

**What survives across both:** route literals, JSON wire keys, enum member names *and values*,
compiler-generated names (`<SendWithNullableResponseAsync>b__0`, `<Method>d__N`). So **wire-shape
answers transfer; names and RVAs do not.** `il2cpp-2025/nonobject-responses.txt`
([nonobject-response-routes](../../wire-shapes/references/conventions/nonobject-response-routes.md)) is a `recflare-2025` artifact — the routes are probably the same on
`recflare-client` but the T resolution was not re-derived there.

`il2cpp-tools/` is the better toolkit for `recflare-client` because it has a real Il2CppDumper run:
**`out/dump.cs` carries full declarations with return types**, so `grep -nE "PROMISE<(Nullable<)?int>"`
enumerates every number-returning endpoint directly — no slot/generic-instantiation work needed.
On that build the promise type is `NCOKFFGPIJM<T>` and `BGBHKBJEMPI.DDKPNIIFDNB<T>` is
SendWithNullableResponse.

⚠️ `C:/Games/recflare-client/GameAssembly.dll` **no longer exists**, so the binary-reading scripts
(`fxref.py`, `rangedis.py`, `slots.py`) fail there — only the `out/` dump artifacts are usable.
