# The junior-account / `birthday` throw

**Symptom:** `Nullable object must have a value.` — aborts the SpawnInvention creation op, and also
fires at boot from unrelated code paths.

```
[Error] Error: Unhandled error for Creation Op: SpawnInvention
Nullable object must have a value.
[Error] Received response with bad result: Failure_Generic
```

**Cause:** the account response omitted `birthday`.

**Fix:** return `birthday` on the account/me response. Fixed server-side 2026-08-03; **no client patch
ships for this.** Don't go looking for one.

---

## Why it happens

`OGFMIPLEJAK.JJLDHBGHIIP()` (RecNet.Runtime.dll) is the **"is this account a junior (under 13)"**
check. It reads the local account object and dereferences its birthday **with no `HasValue` guard**:

```asm
call ObscuredBool.GJGPFJHFLAE      ; override flag; if set -> return true
call <get account>                 ; null -> NullReferenceException
movups xmm0, [rax + 0x98]          ; the Nullable<DateTime> = birthday
call Nullable<DateTime>.get_Value  ; <-- THROWS when birthday is absent
call PHBHEFBDHJF.MLPHMGJALDG       ; -> age
cmp eax, 0xd ; jl -> return true   ; 13 == MKKJLGPDDKJ.HLMJAHGECNE
```

The account object is `IKCIDEMLEIA`, held by `MKKJLGPDDKJ.ELLPBOAKGMN`. Its `Nullable<DateTime>` lives
at field offset `0x98` — the exact offset the throwing instruction loads.

The client exposes a `hasBirthday` property that this path **never checks**. The missing guard is a
genuine client bug, so there is nothing to configure around it: supply the field.

**Why it kills invention spawning specifically:** the caller is
`ACFFPNIEHJE.HDIJFJFDNON(tool)` — the SpawnableTools per-tool predicate. Junior accounts get a
restricted tool set, so the spawn path asks "is this player a junior?" and the getter throws instead
of answering. The call chain is:

```
NNALMOBMGNE.BMAIOBNEEHB            (Photon event pump)
  HGDLKGAFGLC.CHBKOAFLLLN          (SpawnInvention handler; SM = OEDFILCDGIO)
    HGDLKGAFGLC.MBPCIGODAME        (SM = AOICKKIJCGA)
      ACFFPNIEHJE.HDIJFJFDNON      (SpawnableTools predicate)
        OGFMIPLEJAK.JJLDHBGHIIP    <-- throws
```

## The account DTO the server must satisfy

`IKCIDEMLEIA`, Utf8Json formatter `GPAFKEPAJOG`. Utf8Json accepts **three casings** of each key
(`birthday` / `Birthday` / `BIRTHDAY`), and silently drops unknown members.

```
accountId  username  displayName  displayEmoji  profileImage  bannerImage
email  phone  birthday  isJunior  hasBirthday  juniorState  treatAsJunior
parentAccountId  identityFlags  personalPronouns  availableUsernameChanges  createdAt
```

`birthday` is the **only** `DateTime?` in the DTO. Serve it as an ISO-8601 datetime; an adult DOB
makes the gate return false legitimately. Serving `juniorState` / `isJunior` / `hasBirthday` alongside
it keeps the account coherent.

---

## If the names have re-rolled (they will)

Everything obfuscated above is valid for the **20230414 build** (`GameAssembly.dll` mtime
2026-07-23). Type and method names change every game build; **enum members, compiler-generated names
and the Utf8Json key strings survive.** Re-derive rather than trusting the names:

1. `OGFMIPLEJAK` — the signature that identifies it: a class of ~17 **static 0-param `bool`** methods
   in `RecNet.Runtime.dll`, one of which contains a `Nullable<DateTime>.get_Value` and a `cmp eax,0xd`.
2. The account DTO — find the Utf8Json formatter whose `.ctor` emits the literal `"birthday"`; the
   formatter's generic argument is the DTO type.
3. The `13` is a named constant on the config registry class (`HLMJAHGECNE` here), alongside
   `1 / 15 / 50 / 255`.

### Tooling (session scratchpad `il2cpp/`)

Il2CppDumper output + `methods.pkl` (a sorted `(rva, name)` table) plus:

| Script | What it does |
| --- | --- |
| `smcalls.py <name>` | lists a method's direct callees **in call order**, marking RecRoom code |
| `nullscan.py <regex>` | reports which methods call `Nullable<T>.get_Value` |
| `rangedis.py <a> <b>` | disassembles an RVA range with call targets resolved |
| `disfn.py <rva> <len>` | disassembles a method, resolving **string literals** (how the DTO keys were read) |

`nullscan.py` over the whole spawn tree narrowed ~1450 methods to 3 candidates in seconds. That
beats a call-graph BFS, which saturates at depth 3–5 because most of this path dispatches through
interfaces (`call qword ptr [rax]`) that a `call rel32` scan cannot follow.

> ⚠️ These scans only see **direct** calls. `OGFMIPLEJAK.JJLDHBGHIIP` was reached via a chain the
> direct-call sweep did surface, but a virtual-dispatch hop would have been invisible.

## Harmony lessons that cost real test cycles here

These are runtime-verified on this client, and they are why the bug took several launches:

- **Async `MoveNext` bodies patch with NO error and NEVER fire.** `OEDFILCDGIO.MoveNext`,
  `FPJOIIJLKHM.MoveNext` and the async stub `NODLNKPKPBO` all stayed silent while ordinary methods
  around them logged normally. Verified the types were correct via Cecil first — it is not a
  targeting mistake.
- **Constructors are the same silent no-op.** Hooking
  `Il2CppSystem.InvalidOperationException..ctor(string)` to dump `Il2CppSystem.Environment.StackTrace`
  armed and never fired, not even on unrelated exceptions.
- **`[HarmonyFinalizer]` on an async method is useless** — the compiler's own try/catch calls
  `SetException`, so `__exception` is always null.
- **Only ordinary non-async instance/static methods hook reliably.** The winning technique was
  bracket logging (prefix + postfix) *around* the async bodies: a postfix does not run when the
  method throws, so the culprit is the innermost `>>` with no matching `<<`.
- **Patch breadth is not free.** ~70 hooks hard-crashed the client with no dump and no fatal log
  line; ~14 ran clean. Keep diagnostic patch sets small.
