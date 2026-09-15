# Referee protected build 23191908

> Rec Room build 23191908 (depot 471711, downloaded 2026-08-11) ships Themida-packed Referee.dll; strips ALL il2cpp exports + VERSION.dll import + real global-metadata, breaking the native redirector's loader and all four il2cpp patches

Steam depot 471711 build **23191908** at `C:\Games\depots\471711\23191908` (GameAssembly.dll 287 MB,
2026-08-11 18:11) replaces EasyAntiCheat-era protection with **Referee** and invalidates the whole
foundation of the native redirector at `C:\Games\recnet-patcher` — this is *not* an obfuscated-name
reroll ([build-20230414-obfuscation](build-20230414-obfuscation.md) rules don't apply; there is nothing to re-derive from).

Verified statically with `pefile` (contrast against the two older clients):

| | recflare-client | -unstable | **23191908** |
| --- | --- | --- | --- |
| GameAssembly exports | 243 | 388 | **0 (no EXPORT data dir at all)** |
| GameAssembly import DLLs | 9 | 10 | **1 — `referee.dll`** |

- **`RecRoom.exe`, `UnityPlayer.dll`, `GameAssembly.dll` each import exactly one symbol:
  `Referee.dll!jjiEVn`.** Referee itself imports only 4 symbols (kernel32/user32/shell32/crypt32) and
  resolves everything else dynamically. So **the `version.dll` proxy loader vector is dead** — nothing
  imports VERSION.dll by name any more, so our DLL is never mapped.
- **All `il2cpp_*` exports are gone**, so every `GetProcAddress(ga, "il2cpp_...")` returns NULL. That
  kills `ResolveApi` in all four il2cpp patches (`ssl_patch.c`, `http_rewrite.c`, `eac_patch.c`,
  `memcheck_patch.c`) at the first line. Whether Referee *rebuilds* the export table in memory after
  unpacking is **UNVERIFIED and the single highest-value unknown** — test at runtime with
  `GetProcAddress(GetModuleHandleA("GameAssembly.dll"), "il2cpp_domain_get")`.
- **`GameAssembly.dll` is encrypted at rest**: `.text` (13.6 MB) and `il2cpp` (181 MB) sections both
  measure **entropy 8.00** and are marked writable (`C0000020`) — Referee decrypts them in memory.
- **`RecRoom_Data/il2cpp_data/Metadata/global-metadata.dat` is a 52 MB decoy: every single byte is
  `0x52` ('R')**, start to end. The sibling `global-metadata-bak.dat` (31 MB, magic `0xFAB11BAF`,
  v27) is clean but belongs to an *older* build, so it can't name anything in this one.
  → **Il2CppDumper and everything in `il2cpp-tools/` cannot run on this build from disk.** Static
  analysis requires dumping the unpacked image out of a live process first.
- `Referee.dll` (60.6 MB) and `RefereeClientApp.exe` are **Themida-packed** — `.themida` + `.boot`
  sections, nameless high-entropy sections. `RefereeClientInstaller.exe -install` (run via
  `installscript.vdf` at Steam install time) registers a **Windows service** running
  `RefereeClientApp.exe`; PDB path `C:\a1\_work\2\s\Referee\Src\Bin\Release\`. EasyAntiCheat/ still
  ships but is vestigial.

**Reference bypass — `C:\Games\Rec-Room-2025-Patch`** (targets the 2025-07-19 build, so its constants
are stale, but the *technique* is the map):
- Plain `DllMain` DLL with **no loader vector — it must be manually injected** after GameAssembly.dll
  and Referee.dll are already mapped.
- Neutralizes Referee by **nop-ing 4 functions at hardcoded `Referee.dll` RVAs**: `0x76E850`,
  `0x2E6F670`, `0x2E6F680`, `0x2E6F6E0` (three clustered — likely one check family).
- Calls into il2cpp through **return-address spoofing** (`spoof_call` + `RetSpoof.hpp`), using a
  `jmp qword ptr [rbx]` gadget found by `PatternScan("FF 23", GA, SizeOfImage)`, so Referee's
  stack walks see a return address inside GameAssembly instead of the injected module. Assume Referee
  detects hooks *and* walks stacks.
- Hooks the same unobfuscated targets we do (`HTTPManager.SendRequest`,
  `LegacyTlsAuthentication.NotifyServerCertificate`) but by **hardcoded RVA from a dump**, not
  reflection — and it still used `GetProcAddress` for `il2cpp_string_new`/`object_new`/
  `object_get_class`, which implies exports *did* exist on the 2025 build.

Stale-evidence trap: `redirector_*.log` in the depot folder are timestamped 18:04–18:09 but
`GameAssembly.dll` landed at 18:11, so they describe the *previous* contents of that folder, not this
build. Confirmed by Devin. Don't read them as evidence about Referee.

## Session 2 findings (2026-08-11 evening) — vectors tested + Referee dumped

**Delivery vectors — three tested, all detected, all funnel to `__fastfail` 0xC0000409 at
`Referee.dll+0x26f3179`:**
- Manual injection (`CreateRemoteThread`+`LoadLibraryW`): remote thread dies 0xC0000409 immediately.
- **On-disk plugin modification IS hash-checked.** Proved by A/B + control: genuine boot (Player.log,
  clean, runs to ~25 s, self-exits at RecNet "error code: summer") vs a *modified* `RecRoom_Data/
  Plugins/x86_64/DXGIDisplays.dll` proxy → Referee `__fastfail` at load, at the same +0x26f3179, even
  when the proxy is PASSIVE (zero il2cpp calls, no log written before death). So it's the file bytes,
  not runtime behaviour.
- **External observation is also detected** but slower (~5 s): an external EXE doing
  `OpenProcess(VM_READ)`+`ReadProcessMemory` on the genuine game got the process `__fastfail`-killed at
  t≈5 s (vs 25 s un-observed). Referee has a foreign-handle/debug watchdog.

**But external RPM WORKS long enough to dump.** `tools/refdump/refdump.c` (external x64 EXE: polls for
RecRoom.exe, finds Referee base=`0x180000000`, `ReadProcessMemory`-dumps section #1) captured the FULL
40 MB decrypted Referee code section (RVA 0x1000, 0 holes) at t=5 s before the kill. Themida does NOT
block cross-process reads here. This is the way to get a static, disassemblable Referee for THIS build
(runtime in-proc dump is impossible — process dies first). Dump lived at scratchpad `refdump_out/
refdump_sec1_23028_5s.bin`. Magicmida64 (in Downloads, bundles ScyllaHide) is a fallback for a *rebuilt*
PE but can't host a DLL standalone and fights anti-debug — the external RPM dump is simpler/lower-risk.

**Kill-site analysis (capstone over the dump):** `+0x26f3179` is `int 0x29` = the **generic UCRT
`abort()`/`__fastfail(FAST_FAIL_FATAL_APP_EXIT=7)` funnel** (`abort()` entry at `+0x26f3144`, 37 direct
callers; 20 `int 0x29` + 18 `int 0x2c` sites total across the image — standard `/GS`+`/guard`
hardening). `+0x69839d` (`mov eax,[r8]` AV, 0xC0000005) is downstream teardown noise. **So the fault
offset is NOT a bespoke check** — nopping abort is not a clean single lever. The real detection
functions (2025Patch's `Check1-4` equivalents) live upstream and still need locating in the dump (find
the specific caller that hashes modules then calls abort). The 2025Patch RVAs are for a different build;
do not reuse.

**Referee.dll proxy vector — TESTED, foothold works but Referee still aborts.** Referee exports exactly
ONE symbol `jjiEVn`, statically imported by RecRoom.exe + UnityPlayer.dll + GameAssembly.dll +
baselib.dll (loads very early). Built a NULL-effect proxy `Referee.dll` (renamed real →
`Referee_orig.dll`, export `jjiEVn` as PE forwarder `Referee_orig.jjiEVn`, minimal DllMain). Result:
- **Our proxy DllMain RAN** (`referee_proxy_<pid>.log` written at load) and the forwarder resolved, so
  the foothold + real Referee both loaded. Both modules coexist: proxy at high addr (e.g.
  `0x7fffd40e0000`), genuine `Referee_orig.DLL` at its preferred base `0x180000000`.
- **~3–4 s later the genuine Referee `__fastfail`ed anyway** (DllMain t=+0.0s; AV `0xC0000005` at
  `Referee_orig+0x69839d` t=+3s; abort `0xC0000409` at `+0x26f3179` t=+4s). So the proxy is a viable
  *early in-proc foothold with a multi-second head start*, but real Referee's scanner detects the
  tampered module set (extra/renamed module) and kills the process. Foothold alone ≠ enough.

**Crash minidumps are at `%LOCALAPPDATA%\CrashDumps\RecRoom.exe.<pid>.dmp` (~77 MB, WithFullMemory).**
Walk with the pip `minidump` lib (installed): thread `ContextObject.Rip/Rsp`; stack at file offset
`th.Stack.Rva`, len `th.Stack.DataSize`; module map from `mf.modules`. The faulting-thread call chain
(most-recent first, all in `Referee_orig`, RVAs): `+0x26f1829 → +0x26f15da → +0x26f0cb2 → +0x26ecfa0`
(these ~0x26exxxx/0x26fxxxx are the CRT/abort region, abort funnel at `+0x26f3144`) then the detection
body `+0x69839d`(AV site, fn starts `+0x698340`/`+0x698390`) `+0x698492 +0x69828c +0x699d40 +0x6a198b`,
outer `+0x217exxx +0x1dbxxxx +0x2254xxx +0x2184xxx`, back to Themida entry `+0x7385058`. The
`+0x698390` fn is a container/list-walk (`mov r10,[rcx+8]; cmp r10,[rcx+0x10]; mov eax,[r8]`←AV) —
consistent with Referee enumerating loaded modules and choking on our extra module. Many of these
(0x698xxx especially) may be Themida-VM handlers, so nopping a single "check" may be hard.

**abort()-defang TESTED externally (2026-08-11 ~22:08) — keeps the process ALIVE but WEDGED, does not
boot.** `tools/refpatch/refpatch.c` (external EXE: OpenProcess VM_WRITE, spin-read `Referee.dll+0x26f3144`
until its decrypted prologue `48 83 EC 28` appears, WriteProcessMemory it to `31 C0 C3` = xor eax,eax;
ret). Findings:
- **abort()'s page only decrypts at ~+3094 ms** — exactly when the scanner reaches it — so external
  patch lands right at the kill moment (tied race, but it DID apply).
- **With abort defanged the process did NOT die** (survived 2+ min, same pid, 136 MB) — so abort() is
  indeed the terminal kill. BUT abort() is compiled *noreturn*, so every `call abort` is followed by a
  trailing `int3`. Making abort `ret` returns into that `int3` → **STATUS_BREAKPOINT (0x80000003) storm
  at `+0x26e7aac`, ~1/sec**, all caught/non-fatal. Player.log stayed STALE → **Unity never initialised**:
  the engine waits on Referee's `jjiEVn` init to pass cleanly, which never happens, so the game never
  boots. Surviving ≠ booting.
- The storm site decodes as a textbook checked-call: `call 0x26e7ab0` (returns bool) `test rax,rax`
  `je → call abort()` `int3`. i.e. Referee re-runs a check every second; on fail it aborts. Defanging
  abort only defers death into the trailing int3. To BOOT you must make the CHECK pass (or stop the scan
  loop) — not defang the terminal. Better abort patch would be `EB FE` (jmp $) or a clean thread-exit,
  not `ret`, but that still won't boot (main thread blocked on Referee init).

**Verdict on the in-proc fight:** it is LAYERED Themida-2.1.1.1 anti-tamper — defeat the fatal abort and
it falls back to an int3 loop; the engine won't boot until Referee's detection *passes cleanly*, and any
memory/module/file/handle change we make is exactly what it detects (module-walk AV at +0x69839d is
common to proxy/plugin/external-read). Neutralising the detection CORE (`0x217e6b0`: KUSER_SHARED_DATA
timing, TEB/PEB, spinlocks; likely partly VM-virtualised) is research-grade. For the archival goal the
tractable path is **external-only redirect**, which never touches Referee: hosts-file/DNS
`ns.rec.net → recflare` + local reverse-proxy + a custom root CA — **viable IFF** the client's
BestHTTP/BouncyCastle TLS trusts a store/root we can satisfy rather than hard-pinning. Verify statically
from a GameAssembly dump (`LegacyTlsAuthentication.NotifyServerCertificate` + the cert-validation path) —
no launch needed. Genuine game boots to ~25 s and dies only at RecNet ("error code: summer"), so the
redirect is functionally all that's needed; Referee does not block boot, only our tampering does.

**Refinement (static analysis bottomed out):** the wedged pid-12704 dump has only **4 threads** — main
(tid 8656, 54 Referee frames, stuck in ntdll exception dispatch) + 3 idle threadpool waiters. So
Referee's init runs **synchronously on the main thread via `jjiEVn`** *before* Unity's threads exist;
the engine cannot proceed until it returns cleanly. The `int3`-storm site `0x26e7aac` is **CRT plumbing,
not the tamper verdict**: its "check" `0x26e7ab0` is `__acrt_getptd`-style per-thread-data
(`_Init_thread` once-guard `cmp [rip+0x34bef7a],-1`, `GetCurrentThreadId` import pair, returns ptr in
rax), and the caller aborts if the ptr is null. Because `abort()` is *noreturn* with a trailing `int3`
at every call, the `ret`-defang made CRT getptd fall through into `int3` and loop → the main thread
wedged on **broken CRT state**, not on an unfinished scan. So abort-defang is doubly wrong (can't pass
the check AND breaks CRT). The real pass/fail compare is in the **VM-dispatched** code and is NOT
statically reachable — everything reachable is CRT/EH plumbing or Themida VM stubs. **Cracking it
requires DYNAMIC tracing** (x64dbg + ScyllaHide; ScyllaHide ships inside `Downloads\Magicmida64.zip`).
Trace plan written to `C:\Games\recnet-patcher\tools\REFEREE_TRACE_PLAN.md`. Alternative first step:
Magicmida-unpack Referee to recover the check statically (GUI, user-run).

**The 2025Patch "referee disable" (`C:\Games\Referee`) does NOT transfer to this build.** It is a
MinHook DLL that nops 4 Referee integrity functions by hardcoded RVA (`Referee+0x76E850, 0x2E6F670,
0x2E6F680, 0x2E6F6E0`) + spoof_call, built for build **19/07/25** (Referee ver may differ from our
2.1.1.1). Confirmed those RVAs are wrong for us: `0x76E850` disassembles mid-function in our dump (an
FNV-1a hasher — `movabs rax,0xcbf29ce484222325`), and `0x2E6Fxxx` is beyond section#1 entirely. The repo
ships no injector and no per-build notes; its DllMain assumes it is already injected (which our build
rejects). The technique (proxy foothold at t=0 + nop the checks before they fire at ~+3s) is sound in
principle, but needs THIS build's check RVAs, which are NOT statically recoverable: the check gate
`0x611580` is Themida byte-mutation, and FNV-1a hash constants appear **56,586 times, evenly spaced from
RVA 0x1190 onward** — Themida saturates the section with them, so they can't mark the real hasher. Every
static angle (gate, FNV markers, 2025Patch RVAs, orchestrator `0x217e6b0` which is actually call_once
init machinery) is defeated by the mutation. Getting the check RVAs requires DYNAMIC tracing
(x64dbg+ScyllaHide, `tools/REFEREE_TRACE_PLAN.md`). This is the singular remaining blocker for the
disable approach.

Reusable tooling built this session (all under `C:\Games\recnet-patcher\tools\`): `refdump/` (external
Referee memory dumper), `refpatch/` (external abort patcher), `referee_proxy/` (jjiEVn forwarder proxy +
defang variant), `plugin_proxy/` (DXGI/RRTexture proxies), `probe/`+`inject/`. Crash dumps auto-saved to
`%LOCALAPPDATA%\CrashDumps\RecRoom.exe.<pid>.dmp`; walk with pip `minidump` (see script patterns in the
session scratchpad). Analysis scripts (capstone over `refdump_sec1_*.bin`, minidump stack-walkers) in the
session scratchpad `.../scratchpad/`.
