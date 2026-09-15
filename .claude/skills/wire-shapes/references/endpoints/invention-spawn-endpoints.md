# Invention spawn endpoints

> SOLVED: the 'Nullable object must have a value' that kills SpawnInvention is OGFMIPLEJAK.JJLDHBGHIIP, an unguarded Nullable<DateTime> in a date-gated feature flag. Plus the invention DTO wire shapes and which Harmony patch shapes work in IL2CPP.

Build installed 2026-07-28 at `C:\Games\recflare-client`. Same dump/`names.py` procedure as
[subroom-data-save-endpoint](subroom-data-save-endpoint.md).

## Where SpawnInvention lives

Creation ops dispatch through `NNALMOBMGNE` (enum `JNEOCDDOFAO`: `Invalid=0 SpawnInvention=1
SpawnObject=2 Paste=3 Clone=4 DeleteAll=5 BuiltInTooling=6 BuiltInTooling_SkipCheck=7`).
`CreationManager.Awake` registers ops 2–7; **op 1 is registered separately** in
`CreationManager.HGDLKGAFGLC.IHEKMEOIBOI` → handler `HGDLKGAFGLC.CHBKOAFLLLN(int, byte[],
CancellationToken)`, state machine `HGDLKGAFGLC.OEDFILCDGIO.MoveNext` @ RVA `0xC351C0`.

Its locals (compiler-generated names **survive** obfuscation and are the best handle here):
`requestingPlayer, requestData, inventionId, versionNum, dataBlobName, dataBlobHash,
inventionDataBlob`.

`Error: Unhandled error for Creation Op: {0}\n{1}` logs only `ex.Message`, and the async rethrow
drops the throwing frames — **the Player.log stack is useless for locating the throw.**

## Response shapes (Utf8Json, three casings each, **no `{success,value}` envelope** — bare object)

`api/inventions/v1/version?inventionId={id}&version={n}` → `PJGPNHMNHPH`, declaration order:

```
inventionId(long) replicationId(string) versionNumber(int) instantiationCost(int)
lightsCost(int) chipsCost(int) cloudVariablesCost(int) blobName(string) blobHash(string)
```

`blobName`/`blobHash` become the handler's `dataBlobName`/`dataBlobHash` and are fed to
`KHPMKANLOIJ(name, hash)` to fetch the creation blob. **No nullable fields at all.**

`api/inventions/v1/details` (and `v2/batch`, `v2/mine`, …) → `OEBAEGDPBLA`, declaration order:

```
inventionId(ObscuredLong) replicationId(string) creatorPlayerId(ObscuredInt) name description
imageName currentVersionNumber(int) accessibility(Private=0 Public=1 Unlisted=2)
modifiedAt(DateTime) createdAt(DateTime) firstPublishedAt(DateTime?) creationRoomId(long?)
numPlayersHaveUsedInRoom(int) numDownloads(int) cheerCount(int)
creatorPermission generalPermission        // DNCOGHGDMAF: Unassigned=0 LimitedOneUseOnly=10
                                           // DisallowKeyLock=15 UseOnly=20 EditAndSave=40
                                           // Publish=60 Charge=80 Unlimited=100
isAGInvention(ObscuredBool) isCertifiedInvention(ObscuredBool) allowTrial(ObscuredBool)
price(int?) hideFromPlayer(bool)
```

**Exactly three nullables the server controls: `firstPublishedAt`, `creationRoomId`, `price`.**

Re-verified against the installed interop 2026-08-03 — both DTOs unchanged. Note the details DTO has
**no `currentVersion`, `isPublished`, `isFeatured`, `referencedInventions` or `tags`**: real Rec Room
sends a nested `CurrentVersion` object and the client parses it and throws it away, taking blob info
from the separate `v1/version` call instead. So a server can omit all of that, and extra members are
dropped silently by Utf8Json — a details payload is *not* where a missing-nullable throw comes from.

## ✅ SOLVED 2026-08-03 — `OGFMIPLEJAK.JJLDHBGHIIP()`

**Root cause: the account response has no `birthday`.** `OGFMIPLEJAK.JJLDHBGHIIP()` is the
**"is this account a JUNIOR (under 13)"** check. It reads the local account object `IKCIDEMLEIA`
(held by `MKKJLGPDDKJ.ELLPBOAKGMN`), loads the `Nullable<DateTime>` at **field offset 0x98**, and
calls `.Value` with **no `HasValue` guard**, then compares the age against 13:

```
call ObscuredBool.GJGPFJHFLAE      ; override flag; if set -> return true
call <get account>                 ; null -> NullReferenceException
movups xmm0, [rax + 0x98]          ; the Nullable<DateTime> = birthday
call Nullable<DateTime>.get_Value  ; <-- THROWS when birthday is absent
call PHBHEFBDHJF.MLPHMGJALDG       ; -> age
cmp eax, 0xd ; jl -> return true   ; 13 == MKKJLGPDDKJ.HLMJAHGECNE
```

**Nothing to do with the invention payload, and NOT a `/api/gameconfigs/v1/all` gate.** The caller
fits exactly: `ACFFPNIEHJE.HDIJFJFDNON` gates the SpawnableTools set — what juniors have restricted.

### Account DTO `IKCIDEMLEIA` (Utf8Json formatter `GPAFKEPAJOG` @0x387BD30, 3 casings each)

```
accountId username displayName displayEmoji profileImage bannerImage email phone
birthday isJunior hasBirthday juniorState treatAsJunior parentAccountId
identityFlags personalPronouns availableUsernameChanges createdAt
```

`birthday` is the only `DateTime?` → **serve it as ISO-8601 and the throw disappears.** The DTO even
exposes `hasBirthday`, which this path neglects to check — the missing guard is a client bug.

Chain (probe + dump, each step verified):
`HGDLKGAFGLC.MBPCIGODAME` → SM `AOICKKIJCGA` → `ACFFPNIEHJE.HDIJFJFDNON` (SpawnableTools per-tool
predicate) → `OGFMIPLEJAK.JJLDHBGHIIP()` → `Nullable<DateTime>.get_Value` @0x2f98b3b (the method's
ONLY get_Value site). The bracket probe bounded it: spawn reaches `MBPCIGODAME`, and `CKOCGDBOCLK`
(the next marker downstream inside `AOICKKIJCGA`) never runs.

**Independent confirmation:** the boot-time Player.log stack for the same message reads
`Nullable\`1.get_Value <- OGFMIPLEJAK.JJLDHBGHIIP()` from an unrelated caller
(`JAPACNBJJNH.FOJAMFPCNHC`). Same throw site, two paths — so it breaks things beyond spawning.

**FIXED SERVER-SIDE 2026-08-03 — confirmed by the user.** The account endpoint now returns `birthday`;
spawning works. **No client patch ships for this** — a `FeatureGatePatch.cs` was written and then
reverted along with the whole probe scaffold, so the repo is back to its 10 original patches. Don't go
looking for it. If the throw ever returns, the fix is the server field, not a patch.

## (historical) ⚠️ the throwing nullable was NOT identified by static hunting

Static hunting ruled out the obvious candidates; each `.Value` found on the path is properly guarded:

- `LOBKKNOBPKI.LAOGFDLKHIM(mgr, out GNPJIJFFLAA)` — guarded by `MIHKOOKKBLF` then `HasValue`, else
  assigns from `CreationManager.CanAffordResourceCost` first.
- `LOBKKNOBPKI.IIADKJHBOIN()` — both `Nullable<JFOADMEPNEL>` (spawn transform) derefs are
  `HasValue`-guarded.
- `HGDLKGAFGLC.BACIDFINIBL.MoveNext` (`CKOCGDBOCLK(viewData, long? parentInventionId)`, a trophy-type
  check) — reached only when `HasValue` or after the `Nullable<long>` ctor assigns it.

**Why static search stalls: a direct-call BFS saturates at depth 3–5** because most of this path
dispatches through interfaces/virtuals (`call qword ptr [rax]`), which a `call rel32` scan can't
follow. Don't repeat the BFS — go to runtime.

**A Harmony `[HarmonyFinalizer]` on `MoveNext` does NOT work** — `MoveNext` is an async state
machine, so the compiler's own try/catch swallows the exception and calls `SetException`. The
finalizer sees `__exception == null`. Same reason a finalizer on the op dispatcher is useless.

## Bracket probe (`Patches/SpawnInventionProbePatch.cs`, `[Advanced] Probe Invention Spawn`)

Prefix/postfix on every target; a postfix does not run when the method throws, so the culprit is the
innermost `>>` with no matching `<<`.

**Rooted on `NNALMOBMGNE.BMAIOBNEEHB(byte, int, object)`** — the plain non-async Photon event entry
point. Rooting on the SpawnInvention handler's state machine instead produced ZERO output, which was
ambiguous (handler never runs? or Harmony can't patch it?); the plain root makes silence meaningful.

- ✅ **CONFIRMED 2026-08-03: Harmony patching works here.** The root fired 290× in 90s of ordinary
  play. So "no output" from a patched method now means the method genuinely did not run.
- 🚨 **ASYNC `MoveNext` PATCHES SILENTLY AND NEVER FIRES.** `OEDFILCDGIO.MoveNext`,
  `FPJOIIJLKHM.MoveNext` and `NODLNKPKPBO` all patched with no error and stayed silent while the
  ordinary class methods around them (`BMAIOBNEEHB`, `CHBKOAFLLLN`, `HAPIECNKEEF`) logged normally.
  `OEDFILCDGIO` is definitely the right type — Cecil shows it holds `messagePayload`,
  `cancellationToken`, `_inventionDataBlob_5__8`. **Do not instrument async bodies by patching them
  here.** Use `NullableThrowProbePatch` instead (below).
- ⚠️ **70 hooks hard-crashes the client** (~90s in, no crash dump, no fatal log line, no spawn
  attempt). That revision wildcarded all of `HGDLKGAFGLC` (~48 methods) + `LOBKKNOBPKI` + converters.
  Unresolved whether the cause is hook *volume* tripping the native memory integrity scan
  ([launch-validation-boot-failure](../../../rr-client-bringup/references/launch-validation-boot-failure.md) — this branch ships no `MemoryIntegrityPatch`) or one specific
  unsafe target. Cut to ~14 hooks; if that still crashes, it's the integrity scan.
- The root fires on every Photon event, so its bracket is buffered and only emitted when something
  nests inside; the first 3 always print as the self-test.
- Types in generic context (`BCFOBDJJIEL`, `KHIEAIOACFF`, `CDIEMOJJKEC`, `NCFNGOFOIBA`, `FNNGLHGOPBK`)
  resolve to nothing — their methods report `ContainsGenericParameters`. Probe limitation, not a
  rename. None are on the inbound path.

Inbound topology (Cecil-verified, 20230414): `LNEBHFBKIFI.OnEvent` → `OADCBCKNPID.Invoke` →
`NNALMOBMGNE.BMAIOBNEEHB` → `NNALMOBMGNE.NODLNKPKPBO(int senderId, IDictionary eventData,
CancellationToken)` (state machine `NNALMOBMGNE.FPJOIIJLKHM`, parses the op enum + request id out of
`eventData`, then dispatches) → `HGDLKGAFGLC.CHBKOAFLLLN` (state machine `OEDFILCDGIO`).
`BCFOBDJJIEL` is the *outbound* sender `PCGGFIGLKOH`'s state machine — it logs `Received response with
bad result`, and holds the `Nullable<TimeSpan> requestTimeout` field.

Since the error text already names the op as `SpawnInvention`, the op-enum parse in `FPJOIIJLKHM`
succeeded — so a dispatcher-side throw is after that, in the request-id read or the handler invoke.

### 2026-08-03 runtime trace — the throw is SYNCHRONOUS inside the handler

```
>>[0] NNALMOBMGNE.BMAIOBNEEHB/3
  >>[1] HGDLKGAFGLC.CHBKOAFLLLN/3
  <<[1] HGDLKGAFGLC.CHBKOAFLLLN/3
[Error] Unhandled error for Creation Op: SpawnInvention / Nullable object must have a value.
  >>[1] NNALMOBMGNE.HAPIECNKEEF/4          <- sends the failure response
<<[0] NNALMOBMGNE.BMAIOBNEEHB/3
```

The handler **is** reached (earlier doubt resolved). The whole sequence sits inside ONE synchronous
`BMAIOBNEEHB` call, so `CHBKOAFLLLN` returned an already-faulted Task and the awaiting dispatcher
resumed inline. Either the throw precedes the first await, or every await completed synchronously
(cached blob). **So "the throw is after the blob load" is NOT established** — the invention rendering
on screen and the CDN `.inv` fetch succeeding are consistent with a different code path.

## 🚨 Harmony cannot patch IL2CPP CONSTRUCTORS either — silent no-op

Tried `Il2CppSystem.InvalidOperationException..ctor(string)` + dump `Il2CppSystem.Environment
.StackTrace` (static concrete, returns the IL2CPP frame list — would have seen through the async
bodies). It **armed and never fired, not even the self-test on unrelated exceptions.** Patch deleted.
Same silent-no-op class as async `MoveNext`. **Only ordinary non-async instance/static methods are
reliably hookable here.**

## ✅ THE SUSPECT LIST IS DOWN TO 3 (2026-08-03)

Il2CppDumper + a capstone sweep of every direct `call rel32` in the spawn call tree
(`scratchpad/il2cpp/smcalls.py` lists a method's callees in order; `nullscan.py` reports which
methods call `Nullable<T>.get_Value`). Across ~1450 methods scanned, get_Value appears in **exactly
three**:

| Method | Sites | T |
| --- | --- | --- |
| `LOBKKNOBPKI.IIADKJHBOIN` | 2 | `JFOADMEPNEL` (spawn transform) |
| `LOBKKNOBPKI.LAOGFDLKHIM` | 2 | `OILDLLGEMKP.BKOPGEEODIK.KLPCNGCAKOA` |
| `HGDLKGAFGLC.BACIDFINIBL.MoveNext` | 1 | `long` (= `CKOCGDBOCLK`'s `parentInventionId`) |

The earlier static reading called all three "properly guarded" — **one of those readings is wrong.**
First two are ordinary methods and patch fine; the third is async, so bracket its caller
`CKOCGDBOCLK` (static, patchable) instead. `FHGNGDBHOCA`/`NLOGLNAFFOA`/`BEAGLGEBILJ`/the protobuf
converters/`CreationManager`/`NNALMOBMGNE` contain **zero** get_Value sites.

⚠️ The sweep only sees direct calls — virtual/interface dispatch (`call qword ptr [rax]`) is
invisible. If all three log matched pairs, a 4th site is hiding behind a virtual call: go native.

### `OEDFILCDGIO.MoveNext` @0xC351C0 call order (134 calls, dump matches installed GameAssembly.dll,
mtime 2026-07-23)

Sync prologue: `NOIGDGIHCIC.MCCPMJGBPBO` → `CHILKDJABBF.HHCPOGCCGNF` → `OJCLFOJBCNJ.BKEOJJEEMFI` →
`MessageParser.ParseFrom` → `NOEJICCJIPP.FDBPJOGIGGK` ×2 → **first await: `OKANDNFCNBK`** (its SM is
`ILJMIDJNFJJ`, which awaits `KHOBPBLFGEN`). Then `KJIMPHBHBOB` (blob fetch, returns `GAMIBKOFAAE`) →
`GANJODBFNNA` → `MBPCIGODAME` → `CreationManager.EHLDIPNLCME` → `Guid.NewGuid` → `NCMMJPBKOBJ` →
`BEAGLGEBILJ.BBCFAILGGHN` → converters → `LOBKKNOBPKI..ctor/IFAGMFNEPBO/NJDMOMPGEJO/JPHIJLMGPKC/
HEEABPICHNG/JLNPLIHNBII` → `FHGNGDBHOCA.LHNLMHFIFJM` → `NLOGLNAFFOA.LGFPMPKGMLE` →
`FHGNGDBHOCA.OOOHABDPHEC` → `NCFNGOFOIBA..ctor`. **MoveNext itself contains no get_Value call.**

**Decisive next step is a native breakpoint.** Every IL2CPP managed throw funnels through two fixed
addresses (build-specific RVAs, 20230414 build):

- `GameAssembly.dll+0x40A05E0` = `System.InvalidOperationException..ctor` — `rdx` is the Il2CppString
  message (length at `+0x10`, UTF-16 chars at `+0x14`).
- `GameAssembly.dll+0x6C0360` = native `il2cpp_codegen_raise_exception` (below the first managed
  method, so `whatis.py` reports "<below first method>" — that's the tell for a runtime helper).

The 134 `Nullable<T>.get_Value` stubs are contiguous in two blocks, `0x26708D0–0x26735E0` and
`0x2A1A2C0–0x2A1B5E0`; each is `sub rsp,0x28` + `cmp byte ptr [rdx+0x10],0`, so at a breakpoint on
either helper `[rsp]` = which stub (identifies T) and `[rsp+0x30]` = **the method that dereferenced
the empty Nullable**. Filter noise with a condition on `[rsp]-mod.base(rip)` falling in those blocks.

`MoveNext` @ `0xC351C0` contains **no** `get_Value` call itself — every candidate is a callee. The
RecRoom-code callees after the blob await are `LOBKKNOBPKI` (`.ctor`, `IFAGMFNEPBO`, `NJDMOMPGEJO`,
`HEEABPICHNG`, `JLNPLIHNBII`, `JPHIJLMGPKC`), `CreationManager.FHGNGDBHOCA.{LHNLMHFIFJM,OOOHABDPHEC}`,
`NLOGLNAFFOA.LGFPMPKGMLE`, `IPGNGHAADEJ.JEFGHAKNIEM`, `CreationManager.EHLDIPNLCME`, plus an
enumeration of `List<TrialInventionManager.AMIIGCHDJEK.OIPPHAKOBLB>` — note **TrialInventionManager**,
suggestive given the DTO's `allowTrial`/`price`.

Reusable tooling in session scratchpad `il2cpp/`: `disfn.py` (disassemble by RVA), `whatis.py`
(addr→method name), `xref.py`, `nullable_xref.txt`. **`disfn.py` has a bug**: it tests
`operands[0].type==1` for call targets, but Capstone x86 `X86_OP_IMM==2`, so call annotations never
print — extract targets with grep and resolve via `whatis.py`.
