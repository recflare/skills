# Unstable build identity rvas

> recflare-client-unstable is Rec Room build 2025-04-29 (dump at RecRoom_Info/Code/2025-04-29_02-57-34); GameAssembly is on-disk-ENCRYPTED with stripped exports, so hook by hardcoded RVA at runtime

`C:\Games\recflare-client-unstable` (see [unstable-build-proxy-vector-wintrust](unstable-build-proxy-vector-wintrust.md) for the injection
vector) is Rec Room build **2025-04-29** (user-confirmed: 2025-04-29T06:57:34Z). The matching
RVA-annotated Cpp2IL dump is **`C:\Games\RecRoom_Info\Code\2025-04-29_02-57-34\`** (`RecNet.Runtime.cs`
= BestHTTP + BouncyCastle + RecNet). Unity 2021.3.41f1.

**This GameAssembly.dll is HARDENED on disk (same family as the all-R Referee builds, but NO
Referee.dll loads in-process):**
- **`.text` and `il2cpp` sections are ENCRYPTED on disk** (entropy 7.999) - decrypted at runtime by a
  packer. So the dump's `Offset` (file offset) is USELESS against our on-disk file (reading it gives
  ciphertext), and other builds' RVAs won't verify statically. The dump's **RVA is a RUNTIME RVA** -
  valid only against the decrypted in-memory image. **Hook at runtime: VA = GameAssembly_base + RVA.**
- **Export table fully stripped** (Export DataDirectory VA=0/size=0). `GetProcAddress(GameAssembly,
  "il2cpp_*")` returns NULL at runtime -> the redirector's four reflection-based il2cpp patches all
  abort with "missing il2cpp exports". This is THE blocker for the HTTP/TLS patches on this build.
- **`global-metadata.dat` is all-'R' (0x52) decoy** on disk (magic 0x52525252, not 0xFAB11BAF) ->
  static Il2CppDumper fails "Metadata encrypted". Runtime metadata is decrypted in memory.

**Concrete RVAs (build 2025-04-29, VA = 0x180000000 + RVA; at runtime GameAssembly_base + RVA):**
- `BestHTTP.HTTPManager.SendRequest(HTTPRequest)` = **RVA 0x71D7BE0** (single-arg static; host-rewrite
  hook point, call-through).
- `LegacyTlsAuthentication.NotifyServerCertificate(Certificate)` = **RVA 0x71CFD00** (vtable Slot 6;
  TLS accept-all hook point, replace-only).

**SOLVED — il2cpp runtime API recovered by SIGNATURE SCAN from a same-il2cpp-version reference.**
Exports are stripped, but **Pistol Whip** (Steam, `2021.3.7`, metadata **v29 == ours**) is a clean
reference: its GameAssembly exports the il2cpp API and its libil2cpp code is byte-stable across 2021.3.x.
Method: extract `String::New`/`Object::New` (targets of the exported il2cpp_string_new/object_new
thunks) prologues from Pistol Whip, mask rel32/disp32, scan our decrypted `.text` in memory. **Both
matched EXACTLY ONCE** (scanner: `scratchpad/sigscan.py`):
- **il2cpp_string_new = GA + RVA 0x8D9EA0** — ABI `(rcx=const char* utf8) -> Il2CppString*`. Verified by
  the inline-strlen prologue `40 53 48 83 EC 40 48 C7 C0 FF..FF 48 FF C0 80 3C 01 00 75 F7`.
- **il2cpp_object_new = GA + RVA 0x8E1460** — ABI `(rcx=Il2CppClass*) -> obj`. NOTE the sig matched at
  +0xA (the `mov rbx,rcx`); the function ENTRY is 0x8E1460 (back up over the `mov [rsp+10],rbx;push
  rdi;sub rsp,20` prologue). (Framework methods like System.Uri..ctor/get_AbsoluteUri do NOT
  signature-scan — bodies changed across patch versions / prologues too generic.)

**Struct offsets (il2cpp v29, from Pistol Whip `il2cpp.h`) — for resolving methods by walking the class
at runtime instead of the stripped API:** `Il2CppClass.name`@0x10, `.namespaze`@0x18, `.methods`(MethodInfo**)@0x98,
`.method_count`(u16)@0x11C. `MethodInfo.methodPointer`@0x0, `.name`(char*)@0x18, `.parameters`(Il2CppType**)@0x30,
`.parameters_count`(u8)@0x52. `Il2CppType.bits`@0x8 → type enum=`(bits>>16)&0xFF` (STRING=0x0E).
`Il2CppString`: length(i32)@0x10, chars(utf16)@0x14. `System.Uri` (Mono corelib): `m_String`@0x10,
`m_Syntax`@0x20, `m_Flags`(u64)@0x30, `m_Info`@0x38. **HTTPRequest.Uri FIELD @ 0x168** (build-specific;
r6hookmethod's 0x10 is a different build). il2cpp obj header: klass@0x0, monitor@0x8.

**SOLVED — full redirect works. The client boots, logs in, fetches avatar (confirmed via user's
mitmproxy showing ns.recflare.net traffic).** The winning host-rewrite (`src/unity/http_rewrite.c`,
`PatchHttpHostRewriteRVA`): detour SendRequest(HTTPRequest) [RVA 0x71D7BE0, call-through]; get uri via
HTTPRequest.get_Uri [RVA 0x9C9460, call it — auto-property, MethodInfo arg ignored]; read uri.m_String
(+0x10, reliable instance offset); if host matches config, build a FRESH `new Uri(newUrl)` and set it
back via set_Uri [RVA 0x9C91D0]. In-place Uri mutation does NOT work (canonical-cache corruption /
host-length truncation); a fresh ctor is required.

**THE KEY UNLOCK — MethodInfo.methodPointer is XOR-obfuscated with a GLOBAL key, recoverable at
runtime.** This build shuffles Il2CppClass + MethodInfo AND encrypts the method entry pointer, so you
can't call framework methods (Uri..ctor) directly. But: `real_VA = *(u64*)(mi+0x10) ^ key`, and the key
is constant across all methods in a process (changes per launch w/ ASLR). Recover it from a method whose
RVA you know: `key = enc_methodptr(get_Uri) ^ (GA_base + 0x9C9460)`. Verified identical key from two
known methods. Then decrypt Uri..ctor and call it. **Shuffled runtime offsets (this build):**
Il2CppClass.methods@0x60 (MethodInfo* array, NUL-terminated walk), MethodInfo.methodPointer@0x10
(==virtualMethodPointer@0x48 for non-virtual), MethodInfo.name@0x30, MethodInfo.parameters_count@0x51.
Uri(string) is the sole 1-param `.ctor`. il2cpp obj header: klass@0x0. il2cpp_object_new @ GA+0x8E1460.

**DONE (all confirmed at runtime):** injection (launcher.exe, +forcemode:screen), DNS hook, TLS bypass
(NotifyServerCertificate RVA 0x71CFD00 replace-only), and the SendRequest fresh-Uri host rewrite. The
memcheck/EAC patches still abort (no exports) but are NOT needed — no integrity kill occurs.

**REMAINING BLOCKER = PHOTON, needs a CLIENT-SIDE app-id injection (not just server config).** The game
runs ~31s then exits CLEANLY (telemetry `app_exit_state=ReadyForExit`, `crash_detected=false`,
`logged_in=true` — NOT an integrity/crash kill). Ground truth from OUR redirector log (authoritative,
not the stale batched Player.log telemetry): the client makes exactly ONE rewritten call (ns.rec.net ->
ns.recflare.net), then DNS-resolves every other service as `<svc>.recflare.net` directly (accounts, api,
auth, cdn, chat, clubs, commerce, econ, match, notify, playersettings, rooms) — **service discovery is
DNS-based; there is NO `connection-info` HTTP call at this stage.** Fatal sequence (current session,
Player.log): at **7.6s** `GetRegions failed. ReturnCode: -2: Empty application id` -> NullReference in
Photon.LoadBalancingClient -> `OnDisconnected cause=InvalidAuthentication` -> `[Platform.BootSequence]
AHIOPBGELAM: An error occurred`. This is Photon init at STARTUP (before any room-join connection-info),
so it needs `AppSettings.AppIdRealtime` populated at boot. A self-hosted server CANNOT supply real
Photon Cloud app IDs (account secrets), so we inject the user's OWN Photon Cloud app IDs CLIENT-SIDE.

**PHOTON APP-ID INJECTION — DONE & WORKING (`src/unity/photon_patch.c`, `PatchPhotonAppId`).** Detour
the concrete `IMJEOJBJIMB(AppSettings)` [RVA **0x7BECE70**, call-through — a ConnectUsingSettings-style
method] and overwrite the app-id string fields on the passed `Photon.Realtime.AppSettings` object before
the original runs. AppSettings isn't in the dump; its **runtime instance-field offsets (pre-Fusion
layout, discovered live):** `AppIdRealtime@0x10`, `AppIdChat@0x18`, `AppIdVoice@0x20`,
`AppVersion@0x28` ("20250424_prod"), `UseNameServer(bool)@0x30`. New strings via il2cpp_string_new
(GA+0x8D9EA0). App IDs come from `redirector.json` keys `photonRealtimeAppId`/`photonChatAppId`/
`photonVoiceAppId` (parsed in config.c; user supplied their own Photon Cloud GUIDs). **Result: the
"Empty application id"/GetRegions/InvalidAuthentication errors are GONE and the player now SPAWNS into a
room** (`player_spawned:true`).

**STILL exits cleanly ~33s (was 31s) — next layer, NO logged error.** Boot completes, player spawns,
then `PhotonNetwork.Disconnect() called!` at ~13s, and the process exits ~33s with `ReadyForExit` and
NO further app-level log lines after ~21s. Not integrity (no "validation failed"), not a crash. Likely
candidates (unconfirmed): the client can't fully join the specific room INSTANCE (room 92 / instance
1000054) on the user's empty Photon Cloud (rooms were on Rec Room's Photon); missing DNS for
`datacollection.recflare.net` / `platformnotifications.recflare.net` (the ns response advertises hosts
that don't resolve — non-fatal telemetry/notifications but noisy); or an idle/focus artifact of the
non-interactive scripted launch (`OnApplicationFocus False@17s`). NEXT: user should test INTERACTIVELY
(real window, click around) and watch what happens at ~33s; and inspect the match/rooms.recflare.net
responses for the room-join flow. Client-side redirector is otherwise COMPLETE (redirect + TLS + Photon
auth + player spawn all working).

**ANTI-TAMPER FUNNEL SUPPRESSION — DONE & WORKING (`src/unity/antitamper_patch.c`).** The `/hile` call
seen last before the exit is the anti-tamper report: POST `api/PlayerReporting/v1/hile` with
`Type=6` (=ImageSignature) `Message="Signature verification failed (profile/.../x.jpg?width=256&sig=p1)"`.
recflare stamps CDN image URLs with a PLACEHOLDER `sig=p1` the client's signature check rejects (it
verifies against a baked-in key it can't forge). All tamper detections funnel through one static method
`BBFGNPPNKOG(GDMJABNKMGN kind, string detail, int? code, bool)` [RVA **0x774F610**, RecNet.Runtime] —
the build's equivalent of the documented AAKMENFOFEI.GIOHEBODOAC funnel (see
[launch-validation-boot-failure](launch-validation-boot-failure.md); violation enum `GDMJABNKMGN`: Obscured=0 Time=1 Inject=2 GiftCount=3
Engine=4 UnknownDll=5 ImageSignature=6 AvatarHack=7 …Memory_Hash_Mismatch=500 Native_Memory_Hash_Mismatch=700).
We detour it replace-only -> return null. Confirmed at runtime: it fires (`[ANTITAMPER] suppressed report
kind=6 detail="Signature verification failed (...sig=p1)"`, many) and the `/hile` POST no longer goes out.
Player.log still logs `Image signature verification failed` / `Cached image handle promise failed` (the
images themselves are rejected -> missing profile pics, cosmetic; the OLD managed patcher also only
suppressed the funnel and shipped, so this is not the blocker).

**STILL exits cleanly ~36s (31->33->36 as each fix lands).** app_exit_state=ReadyForExit,
seconds_since_main_thread_active=2. NOT attributable to /hile anymore. PRIME REMAINING SUSPECT: the
native **memory-integrity scan** — we now have FOUR inline .text detours (SendRequest 0x71D7BE0,
NotifyServerCertificate 0x71CFD00, Photon-connect 0x7BECE70, antitamper-funnel 0x774F610) and our
memcheck neutralizer ABORTS (no il2cpp exports). The scanner is the Thread+CancellationTokenSource class
**`CHPCJHMCKMA`** (Assembly-CSharp; found by shape — its closure `ECHAILPJHKD`/`<>4__this`); a background
re-scan (`CheckHashesInBackground`) detecting our hooks likely drives the quit. Next: port memcheck to
hardcoded RVAs for CHPCJHMCKMA's scan-start (needs the resolved-promise too), OR make hooks invisible.
Should confirm via interactive user test first (scripted launch ~= headless; user should watch what the
UI does at ~36s and whether avatars render).

**UPDATE — root cause of the ~30s exit is a FREEZE from the ANTI-CHEAT subsystem, NOT memcheck/account.**
Ruled out along the way (all confirmed): (a) memcheck — the antitamper funnel logs EVERY tamper kind and
NO Memory_Hash_Mismatch=500/Native=700 ever appears; (b) account/junior — user's /account/me HAS
`birthday` (placeholder 1904-01-01) and `isJunior:false`, so the [invention-spawn-endpoints](../../wire-shapes/references/endpoints/invention-spawn-endpoints.md)
birthday-null throw is not it; the "meta junior account creation error" `Application.Quit(878787)` path
(`POONLBAMBLG` @0xA26BF0/0xCFF920/0x101AEB0/0x12E76E0) is NOT what fires. **The real exit is a CRASH:
process exit code -1073741819 = 0xC0000005 ACCESS_VIOLATION**, or (with the antitamper hook removed) a
FREEZE that lingers then closes. A vectored AV logger (`src/debug/crash_handler.c`,
`InstallCrashHandler`, logs faults as GA+RVA) shows RECURRING first-chance AVs, all in GAME code (not our
DLL): **reading `0x186700B90` = preferred-base `0x180000000+0x6700B90` (an un-rebased/ASLR-broken
pointer, every ~20s) and `0xFFFFFFFF52520000` (`0x52`='R' poison/uninitialized memory, every ~10s)**,
plus managed-exception raises via the runtime helper at GA+0x99427C ("below first method"). These
correlate with the periodic `api/PlayerReporting/v1/referee` anti-cheat report (~29s). Interpretation:
the Referee/EAC anti-cheat subsystem is not initialized in this environment, so its periodic (~10s) scan
dereferences uninitialized/un-rebased structures, eventually hanging the main thread → freeze/close.
**The antitamper funnel hook (return null) is currently DISABLED (`#if 0` in hook_manager.c) because its
null return turned the freeze into a faster 0xC0000005 crash** — a caller derefs the null DKABIBJEBOC.
NEXT: neutralize the anti-cheat periodic scan / its init (the thing reading 0x52-poison + the
0x180000000-based pointer every ~10s) — likely an EACManager/Referee init or a periodic tick to hook;
find the method whose scan reads those addresses. The redirect + login + avatar + Photon-spawn all work;
this anti-cheat freeze is the last blocker.

**UPDATE 2026-08-13 — root cause is very likely STEAMWORKS ISteamHTMLSurface, not EAC/Referee.**
`RecRoom.exe.dll` (imported by name from the thin `RecRoom.exe` stub) turned out to be
Themida-protected (`.themida`/`.boot` sections; ~56MB) — corrects the earlier "no Themida on this
build" assumption. Live x64dbg attach (headless.exe, `-cf` scripts, TlsCallbacks=0, SafeAttach=1, and
ScyllaHide w/ Themida profile) was tried to catch the fault live but is a dead end: attaching, with or
without ScyllaHide, reproducibly crashes with `EXCEPTION_ACCESS_VIOLATION`/DEP at `baselib.dll`'s own
declared entry point before any script command runs. **This turned out NOT to be debugger-specific** —
the identical baselib-EP fault also appears once, early, in normal undebugged runs (see below) — so it's
not an anti-debug trip-wire, just an early/benign self-recovering race, and x64dbg live-attach adds no
value here; don't retry it for this bug.

Instead, `src/debug/crash_handler.c`'s `VehCrash` was extended: it now logs full GP registers and walks
**the faulting thread's actual stack from `ep->ContextRecord->Rsp`** (via SEH-guarded `SafeReadPtr`),
not `CaptureStackBackTrace()` (which only walked the VEH's own dispatch stack — a bug; always showed
empty/wrong frames for these faults). Confirmed: for every recurring poison fault, `ExceptionAddress ==
ExceptionInformation[1]` (fault RIP itself equals the bad pointer) and `ExceptionInformation[0]==8`
(DEP/EXECUTE) — these are **calls through a corrupt/null function pointer**, not bad data reads.

With real stack context, `il2cpp-tools/whatis.py` (run from `il2cpp-tools/`, needs `out/script.json`)
resolved the return addresses on `[rsp+0]` at the two recurring fault sites:
- `FFFFFFFF52520000/10/20` (every ~10s, thread persists across the run) → callers
  `GA+0x7FAC63`/`0x7FACE2`/`0x7FACEE` all land inside **`Steamworks.NativeMethods$$ISteamHTMLSurface_Init`**
  (@GA+0x7fac10) and **`...ISteamHTMLSurface_JSDialogResponse`** (@GA+0x7fac90) — tight offsets (+0x52..0x5e),
  high confidence these are real hits, not "closest preceding symbol from a big gap" noise (Steamworks.NET
  codegen emits hundreds of tiny P/Invoke wrappers contiguously, which is exactly the density seen here).
- `0x186700B90` (once per run, different thread each time) is **not** an un-rebased GA pointer as first
  assumed — `RecRoom.exe.dll` itself loads at exactly `0000000180000000`, so this is RVA `0x6700B90`
  *inside* `RecRoom.exe.dll`'s own (Themida-encrypted-on-disk) code, landing in the section that has real
  file backing (not the pure-virtual `.themida` stub section) — i.e. a stale cached pointer into
  Themida-protected code that's no longer valid/mapped when called again. `rbx`/`rdx` at that fault spell
  ASCII `"Authenti"` (`"Auth"`+`"enti"`), suggesting this is on a Steam-auth-ticket-adjacent path. Separate
  from the ISteamHTMLSurface issue; not yet chased further.

Checked and ruled out as *the* fix: the game folder's `steam_appid.txt` had the wrong AppID (`480`,
Valve's public Spacewar test id) instead of Rec Room's real one. Real AppID is **471710** (inferred from
`.DepotDownloader/471711_*.manifest` — Steam depot = appid+1 by convention; not yet independently
confirmed). **Changing `steam_appid.txt` to 471710 and relaunching made zero difference** — byte-identical
crash addresses/timing to before the change. Confirmed via live `Get-Process -Module` mid-boot that
`steam_api64.dll` **and** `steamclient64.dll` (from `C:\Program Files (x86)\Steam`) both load into the
process — so `SteamAPI_Init()` is reaching a running Steam client at some level; `EasyAntiCheat.dll`
(present on disk at `RecRoom_Data/Plugins/x86_64/EasyAntiCheat.dll`, contradicting the launcher.c comment
"no anti-cheat ever loads") was NOT seen loaded at the ~12s checkpoint. Leading theory: Steam's **Overlay**
subsystem (which `ISteamHTMLSurface` depends on) may only fully activate for processes actually launched
*through* Steam (steam.exe → child exe), and our suspended-CreateProcess+inject launch path (see
[unstable-build-proxy-vector-wintrust](unstable-build-proxy-vector-wintrust.md)) bypasses that, leaving HTMLSurface partially initialized with a
bad/null function pointer that later gets called and faults.

**2026-08-13 — LAUNCH-PATH / EVASION AVENUE EXHAUSTED (all negative). The Themida ~35s assert is invariant.**
Chasing "make the launch look legitimate so Themida doesn't assert" — every variant lands at 35-40s,
same as baseline:
- **EAC is NOT in the launch chain.** `Recroom_Release.exe` is Rec Room's own launcher `LaunchRecRoom`
  (PDB `C:\ClientSecurity\LaunchRecRoom\...`); it only imports KERNEL32+CRT and just
  `CreateProcessW(".\RecRoom.exe")` (+`IsDebuggerPresent`). No EAC bootstrap. EasyAntiCheat_x64.dll
  never loads in-process. So the assertion is pure Themida, not EAC.
- **Suspended vs running launch: no difference.** Added `--running`/`RECFLARE_RUNNING=1` mode to
  `tools/launcher/launcher.c` (creates the process NON-suspended, Themida inits normally, inject at
  T+600ms). 40s. So `CREATE_SUSPENDED` is not the tell.
- **PEB module hiding: no difference.** New `src/memory/module_hide.c` + `include/module_hide.h`
  (`HideModuleFromPeb`, config `hideModule`/`hide_module` default 1) unlinks redirector.dll from all
  three PEB loader lists (verified "unlinked"). Still 35-40s — Themida is not finding us by walking the
  loader module list.
- **Real launcher parent lineage: no difference.** Built `inject.exe` (from `tools/inject/inject.c`,
  Sleep after detect trimmed 2000->500ms) and launched `Recroom_Release.exe` -> `RecRoom.exe` (genuine
  parent, exactly what Steam would produce), injecting into the child. 40s. Parent PID doesn't matter.
Combined with the earlier proofs (zero code patches via HWBP+dns-off, and all diagnostics off), the
assertion is invariant to launch method, injection method, code patching, module visibility, parent
lineage, and our diagnostics. It fires on a consistent ~35s cadence regardless. This is a periodic
Themida protection check we cannot cheaply evade; remaining detection vectors (our worker threads'
start addresses in an unlinked-but-mapped region, a memory scan for unknown executable pages, or timing
anomalies from our hooks) are all below the level these experiments reach. **Verdict: incremental
evasion does not crack this; only a real Themida unpack/neutralise would, which is a large separate
effort of uncertain payoff.** Toggles left in place (`useHwbp`, `enableDns`, `enableDiag`, `hideModule`,
launcher `--running`) for any future attempt. Clean shipping default unchanged: inline detours, diag
off, Referee poison-slot fix on, hideModule on (harmless hygiene).

**★★★ 2026-08-13 — TWO SEPARATE CRASHES; ONE FIXED, THE SESSION-KILLER IS THEMIDA ITSELF.**
After neutralising the Referee P/Invokes (below), the client still dies ~35-40s in. Full exception
logging (crash_handler.c now logs EVERY exception code, not just AVs) split the problem cleanly:
1. **Referee P/Invokes (FIXED).** The `0xFFFFFFFF525200xx` junk-pointer calls. Fixed two ways in
   `src/unity/filesig_patch.c`: (a) replace-only detours on 11 named Referee externs, and — more
   completely — (b) `PatchPoisonSlots`, a scan of GameAssembly's mapped image (byte-granular, only
   MEM_COMMIT readable regions via VirtualQuery) that finds every qword matching
   `0xFFFFFFFF525200xx` and overwrites it with a stub returning 0. That repaired 4 slots
   (GA+0x7FAC59/0x7FACD8/0x7FACE4/0x7FAD36) and **eliminated ALL 0x52520000-family faults**, including
   ones we never saw fault. ~141 ms per scan; repeated ~10x because P/Invoke resolution is lazy.
   This is the correct, general fix for that class.
2. **The actual session-killer (NOT fixed — Themida's own anti-tamper).** WER blames
   `RecRoom.exe.dll+0x34D7E14`; our first-chance VEH never sees THAT one (Themida's own SEH takes it),
   but we DO catch, on the SAME thread microseconds earlier: `C0000420` = **STATUS_ASSERTION_FAILURE**
   at `RR+0x2FE315C`, immediately followed by an AV executing `RR+0x6700B90`. Registers at that fault:
   `rcx=0x80000000`, `rbx="Auth"`, `rdx="enti"` — i.e. the thread just ran `cpuid` leaf 0x80000000 and
   read back "AuthenticAMD", then tried to `call` into an address inside RecRoom.exe.dll's own
   encrypted section that isn't executable/decrypted. **This is Themida's VM / anti-tamper doing CPU
   fingerprinting, asserting, and jumping into a VM handler that faults.** It is inside the packer, not
   game logic, and fires on a ~35s timer regardless of what we do. Proven independent of us: dies at
   35-40s with (a) zero inline patches (all hooks on HWBP + DNS off), and (b) all diagnostics off
   (`enableDiag:false` — no VEH, no hang probe, no self-test), so it is not our detours, not our VEH,
   not our thread-suspension. The hang probe also shows the main thread parked in an ntdll wait
   (`rip=7FFD36BC0ED4`) for the last ~15s — it stops getting work ~34s in, consistent with a Themida
   watchdog thread tearing things down rather than a main-thread fault.
   This is the Themida wall the older notes ([referee-protected-build-23191908](referee-protected-build-23191908.md)) warned about, just
   on the 2025-04-29 build. Defeating it = actually unpacking/neutralising Themida (the OEP-redirect
   `RecRoom.exe.dllMM.exe` is NOT a real unpack — encrypted sections unchanged). Big, separate effort;
   may not be worth it. NEXT IDEAS IF PURSUED: (a) this build ships EasyAntiCheat + Referee and Themida
   may expect to run under EAC's launcher — try launching via the EAC bootstrap or Steam instead of our
   suspended-CreateProcess; (b) find what `RR+0x2FE315C` asserts on; (c) accept ~35s as the ceiling.

**★★ 2026-08-13 — ROOT CAUSE OF THE PERIODIC CRASHES: UNRESOLVED *REFEREE* P/INVOKES.**
The recurring first-chance AVs are `EXECUTE` faults where RIP *is* the bad address
(`0xFFFFFFFF52520000` / `...10` / `...20`) — i.e. calls through junk function pointers, on an exact
10.000 s timer, survivable several times until one kills the process. Chain (all resolved with the
CORRECT dump via the new `il2cpp-tools/whatis2025.py`): return addresses `GA+0x7FAC63 / 0x7FACE2 /
0x7FACEE` are *below the first managed method*, i.e. inside **libil2cpp's own P/Invoke glue**; the
managed frames above land in class **`BEDNFMIFJNG`**, whose async state machine `JBMCKPKFHLD` carries
the literal string **"Unable to initialize Referee telemetry. Is the game protected by Referee?"**.
So `BEDNFMIFJNG` is the **Referee anti-cheat integration layer**; its `extern` methods are Referee
native P/Invokes, Referee's native side does not exist in this build (`RecRoom.exe.dll` exports
exactly ONE Themida-mangled symbol, `qxPzOD`), so il2cpp resolves those imports to junk. The
`0x52520000` base with `+0`/`+0x10`/`+0x20` is consecutive slots of that one unresolved import table.
(`0x52 0x52` = "RR".) Nearby code calls `AmplitudeAnalyticsClient.Event("file_sig_check")`.

Fix shipped: `src/unity/filesig_patch.c` + `include/filesig_patch.h` (`PatchFileSigCheck`, tag
`[REFEREE]`, own thread from hook_manager) replace-only detours **11 Referee P/Invokes**, all
returning 0. RVAs (class `BEDNFMIFJNG` + nested `DIMHKPJGDLP`, 2025-04-29 dump): `0x1119690`,
`0x1119710`, `0x11197D0`, `0x1119890`, `0x1119970`, `0x1119A50`, `0x111A590`, `0x111A5B0`
(`FGIGMCJGLCJ`, the file-sig check), `0x111A5E0`, `0x111A8C0`, `0x112A1E0`. **0, not 1**, because the
"Is the game protected by Referee?" message proves the client has a designed "Referee unavailable"
path; returning 1 hands callers garbage handles/uninitialised `[Out]`s instead. Prologue check
confirmed the RVAs are real entries (`0x111A5B0` = `48 83 EC 38`, `sub rsp,0x38`).
RESULT: the `0x52520000` fault is gone and **uptime went from a very consistent 35 s to 40-60 s**
(measured 60, 55, 40 — genuinely improved but variable). NOT a complete fix.
**Measured and rejected:** also stubbing `JBMCKPKFHLD.MoveNext` @`0x1127670` DOES remove the last two
faults (`...10`/`...20`) but is a NET LOSS — uptime fell to ~40 s, presumably because the async task
it drives then never completes. Do not re-add without re-measuring uptime.
STILL OPEN: `RR+0x6700B90` (inside Themida-wrapped RecRoom.exe.dll, caller `RR+0x2FDF51A`, ~20 s
period; registers at that fault spell CPUID vendor `"AuthenticAMD"`, so it is Themida CPU
fingerprinting) and the two remaining `0x52520000+0x10/+0x20` calls from `MoveNext+0x166`.

**★ 2026-08-13 — OUR PATCHING IS *NOT* WHAT KILLS THE SESSION. Stop trying to hide the hooks.**
Ran the client with **ZERO inline byte patches anywhere in the process**: all three GameAssembly hooks
via hardware breakpoints (`"useHwbp": true`) *and* the ws2_32!getaddrinfo detour disabled
(`"enableDns": false` — safe because once the SendRequest rewrite is live the client asks for real
*.recflare.net names that resolve natively). Result: **71 requests still rewritten, client still boots
fully, and it STILL dies at ~35s with the same crash** (that run: `ucrtbase.dll+0xED3D7`). Therefore:
- The memory-integrity / anti-tamper-detects-our-detours hypothesis is **DEAD**. Inline detours are
  fine; there is no need to hide them, no need to port a memcheck neutralizer, and **no need to
  neutralize Themida** — that whole line of work is unnecessary.
- HWBP vs inline makes no behavioural difference (35s either way), so keep inline detours as the
  default (`use_hwbp = 0`) since they're simpler and cheaper than suspending ~135 threads every 200ms.
Crash modules/offsets VARY across runs -- `RecRoom.exe.dll+0x34D7E14` (most common), `+0x34F2AE8`,
`+0x35FB437`, and `ucrtbase.dll+0xED3D7` (repeatedly; almost certainly `abort()`). Varying fault sites
plus a CRT abort is the signature of **heap corruption / an unhandled native exception**, not a
protector's deliberate kill. Combined with Player.log stopping dead at `PhotonNetwork.Disconnect()`
(~11s game time) and the process then lingering ~20s before dying, the picture is: **the main thread
hangs ~11s in, then the process aborts.** NEXT HYPOTHESIS TO TEST: recflare's response payloads differ
from what the real servers sent, and some native deserialization path corrupts the heap on the odd
data. Best tool: enable **PageHeap** for RecRoom.exe (Image File Execution Options registry key
`GlobalFlag=0x02000000` + `PageHeapFlags=0x3`; gflags.exe is not installed on this machine) so the
corrupting write faults at its source instead of ~20s later.

**2026-08-13 — HARDWARE-BREAKPOINT HOOKS: BUILT AND WORKING (earlier "dead end" call was WRONG).**
Self-test (arming a function inside our own DLL, slot 3) **PASSES**, and with the engine started early
(from `HwbpSelfTest()` right after `InstallCrashHandler()`, not lazily at first hook) all ~135 threads
stay armed and the hooks fire: 176 single-step traps, 77 URL rewrites. The earlier zero-hit runs were
an init-ordering problem, not the protector faking registers. Retained details:
`src/memory/hwbp.c` + `include/hwbp.h` now exist (DR0-3 + VEH on EXCEPTION_SINGLE_STEP; redirect
`ctx->Rip` to the hook; call-through hooks use a thread-local one-shot `HwbpSkipOnce` + `EFlags.RF` to
call the original without re-trapping; per-thread applier thread). `HWBP_SLOT_SSL/HTTP/PHOTON` = 0/1/2,
slot 3 free; ws2_32!getaddrinfo deliberately stays an inline detour. Toggle = `use_hwbp` /
`"useHwbp"` in redirector.json, **defaulted to 0 because it breaks the client**. Findings:
- Arming works: Dr0 reads back as the target VA, Dr7 = `0x415` across ~27 threads (0x415 = our 0x15
  plus bit 10, which always reads 1 — not a bug).
- **The protector zeroes Dr0-Dr3 a few seconds in** (Dr0 -> 0, Dr7 left at 0x415). A one-shot arm is
  silently disarmed before the hooks are ever called. Re-arming EVERY thread EVERY 200ms defeats that
  and the registers then verifiably persist.
- **Even with registers confirmed present, the breakpoints never fire.** SendRequest is definitely
  reached (DNS hook shows recflare lookups) but the hook is never entered → no URL rewrite → the client
  degrades to vanilla behaviour and dies at ~15s instead of ~35s. Likely Themida hooks
  NtGetContextThread/NtSetContextThread and fakes the debug-register view, so our readback is just the
  value we wrote while the real CPU registers stay clear (ScyllaHide has dedicated options for exactly
  this). NEXT TEST IF RESUMED: log whether the VEH sees ANY EXCEPTION_SINGLE_STEP; if never, hardware
  breakpoints are a dead end on this target and inline detours are the only interception that works.
Confirmed-good baseline to return to: `useHwbp` off → 72 requests rewritten, full boot, ~35s session.

**⚠️ 2026-08-13 — `il2cpp-tools/out/` IS THE WRONG BUILD. Check this BEFORE trusting any RVA/name.**
`il2cpp-tools/out/{dump.cs,script.json,methods.pkl,meta.pkl,il2cpp.h,stringliteral.json}` are from a
DIFFERENT client build than recflare-client-unstable. Proof: that dump puts BestHTTP `SendRequest` at
RVA `0x3161AF0` and `NotifyServerCertificate` at `0x3F447C0`, whereas the RVAs that demonstrably work at
runtime here are `0x71D7BE0` / `0x71CFD00`. **The CORRECT dump is
`C:\Games\RecRoom_Info\Code\2025-04-29_02-57-34`** (plain `*.cs` with `[Cpp2IlInjected.Address(RVA=...)]`
attributes; `RecNet.Runtime.cs` lists SendRequest at `0x71D7BE0` — match). Always sanity-check a dump by
looking up SendRequest before using it. Consequences of having used the wrong one:
- `whatis.py`/`findm.py`/`fxref.py` (which read `out/script.json`) return **bogus names** for this client.
  The "`Steamworks.NativeMethods$$ISteamHTMLSurface_Init`" attribution below came from there and is void.
- A memcheck scan-entry RVA (`0x133B720`, class `BLGELNMKAKM`, `verification.sig`,
  `CheckHashesInBackground`) was read from the wrong dump and hooked; at runtime that address is
  mid-instruction (prologue `DF C7 47 10`) and nothing calls it. Hook is now DISABLED in
  `src/unity/memcheck_patch.c` (`PatchMemcheckByRVA`) with a warning — do not re-enable without
  re-deriving from the correct dump.
- **`CheckHashesInBackground`, `verification.sig`, and class `BLGELNMKAKM` do NOT exist in the correct
  dump**, so the managed file-hash scanner is not in this build at all. Neither is `CHPCJHMCKMA` (that
  name was from yet another build). The integrity check that matters here is therefore very likely
  **native, inside the Themida-wrapped `RecRoom.exe.dll`** — the same module the fatal crash lands in.
To re-point the tooling: `il2cpp-tools` scripts take `GAMEASSEMBLY` env var and read `out/script.json`;
a matching `script.json` for 2025-04-29 would have to be regenerated, or grep the correct dump's `.cs`
files directly for `Cpp2IlInjected.Address(RVA = "0x...")` (that's how SendRequest was verified).

**CORRECTION 2026-08-13 (later) — the Steamworks theory above is WRONG; ignore its "NEXT" steps.**
The `ISteamHTMLSurface` AVs are FIRST-CHANCE and handled: they recur on an exact 10.000 s timer and the
process keeps running through many of them. They're il2cpp's normal hardware-null-deref →
NullReferenceException mechanism (a Steam feature we don't need), NOT the crash. Same for the early
`baselib`-entry-point AV: it appears in ordinary undebugged runs too, so the x64dbg attach failure was
never anti-debug — just that same benign early fault.

**The definitive tool is the Windows Application Error event log, not address archaeology:**
`Get-WinEvent -FilterHashtable @{LogName='Application'; ProviderName='Application Error'}` names the
faulting module + offset directly. Use it FIRST on any future crash here. It shows the fatal fault is
**`0xC0000005` inside `RecRoom.exe.dll`** (the Themida-protected bootstrap, base `0x180000000`), at a
*repeating* offset **`+0x34D7E14`** (5/8 recent runs), sometimes `+0x35FB437`, and sometimes instead
**`ucrtbase.dll+0xED3D7`** (3/8). Mixed-but-repeating fault sites in the protector module = a deliberate
protector/anti-tamper reaction or heap corruption, not a game logic bug.

Also ruled out with hooks that were installed and NEVER fired (so these paths are not used at all):
`UnityEngine.Application$$Quit` @GA+0x3EA5FA0 and `Quit(int)` @GA+0x3EA5FE0, and
`kernel32!TerminateProcess` on self. (`kernel32!ExitProcess` could NOT be hooked — the detour engine
refuses its prologue, gotcha 2.) So nothing calls a managed or explicit process-exit path; it is a hard
crash. Tracer lives in `src/unity/quit_trace.c` + `include/quit_trace.h`, wired in hook_manager.c, with a
`"blockQuit"` config toggle (`block_quit` in config.c/h) that is currently pointless since Quit never
fires — keep it only as a witness.

Timeline that kills the "referee report causes the quit" idea: Photon disconnect (Player.log's last line)
happens ~3 s BEFORE the `api/PlayerReporting/v1/referee` POST, so that POST is a shutdown-flush artifact,
not the trigger. Player.log lives at `%USERPROFILE%\AppData\LocalLow\Against Gravity\Rec Room\Player.log`
(internal clock runs 3 h behind local) and is very useful; `Player.slog`, `anrTime`, `appstate.raw`,
`backtrace/` sit beside it.

Fixed along the way (real bug, keep): `datacollection.recflare.net` and `platformnotifications.recflare.net`
had NO DNS records, throwing `SocketException 11001` and an unobserved-task AggregateException. Added
`{"from":"datacollection.recflare.net","to":"api.recflare.net"}` and the same for platformnotifications to
`redirector.json`'s `rewrite` list (the DNS hook and HTTP rewrite share that table, so no rebuild needed).
Player.log "Could not resolve host" count went 2 → 0 and the exit moved 25-30 s → 35 s, but the crash
remains, so this was NOT the root cause. A wildcard `*.recflare.net` DNS record server-side would be the
cleaner fix. Also tried and REVERTED (zero effect): `steam_appid.txt` 480 → 471710 (real Rec Room AppID,
per `.DepotDownloader/471711_*.manifest`; restored to the original 480). `steam_api64.dll` and
`steamclient64.dll` both DO load and reach the running Steam client.

Control test: vanilla (no injection at all) exits **cleanly at 15 s with NO crash event** — but it never
logs in (dead `ns.rec.net`), so it never reaches the code where we crash; it is NOT a valid control for the
35 s crash. Need a better isolation test.

**LEADING HYPOTHESIS + NEXT STEP:** the native **memory-integrity scan was never ported to this build** —
`[MEMCHECK] missing il2cpp exports -- aborting` in every log, so it is UNPATCHED here while we run four
inline .text detours (SendRequest 0x71D7BE0, NotifyServerCertificate 0x71CFD00, Photon-connect 0x7BECE70,
plus ws2_32!getaddrinfo). On older builds that scan produced "Launch validation failed"; on this
Themida-wrapped build it plausibly just crashes inside `RecRoom.exe.dll` instead. Two ways forward:
(a) port the memcheck neutralizer to hardcoded RVAs for build 2025-04-29 (needs the scanner class
`CHPCJHMCKMA`'s scan-start RVA *and* a resolved-promise to return); or (b) **make the hooks invisible** by
converting the inline detours to hardware breakpoints (debug registers DR0-3 + VEH), which leave code bytes
untouched so no integrity scan can see them — note `src/memory/hwbp.c` / `include/hwbp.h` do NOT exist
(an earlier git status listed them; they are gone), so (b) means writing it from scratch, and DR0-3 caps
us at 4 hooks (exactly the number we have). A cheap isolation test first: bisect with the existing
`enableSsl`/`enableHttp`/`enablePhoton` config toggles to see which hook (if any) the crash depends on.

SUPERSEDED (kept only to avoid re-deriving): either (a) detour/neutralize the concrete `Steamworks.NativeMethods` entry points at
GA+0x7fac10 (`ISteamHTMLSurface_Init`) and GA+0x7fac90 (`ISteamHTMLSurface_JSDialogResponse`) to safe
no-ops, matching this codebase's existing hardcoded-RVA detour pattern (ssl_patch.c/eac_patch.c) — fast
but possibly whack-a-mole if other `ISteamHTMLSurface_*`/Steamworks entry points also get called with the
same bad pointer; or (b) find the single C# choke point that acquires/caches the HTMLSurface interface
pointer and fix it there (one patch, more investigation). Also worth trying: launching via `steam.exe
-applaunch 471710` instead of our own suspended-launcher, to see if overlay activation differs (bigger
rework of the injection strategy, since Steam's launcher spawns the real game exe itself).
