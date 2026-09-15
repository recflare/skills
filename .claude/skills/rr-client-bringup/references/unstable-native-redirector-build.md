# Unstable native redirector build

> How to build the native redirector.dll in ../recnet-patcher-unstable (x64, vcvars-in-same-call gotcha)

`C:\Games\recnet-patcher-unstable` is a **novel native (C/Win32) approach** replacing the abandoned
BepInEx/MelonLoader managed patchers (both crash in il2cpp_init / need a working loader). It's a DLL
that hooks winsock (`getaddrinfo`/`connect`/`gethostbyname` in ws2_32) to redirect Rec Room's traffic
to a self-hosted server, sidestepping the managed loader entirely. Builds to `build\redirector.dll`.

**Build (must target x64 — Rec Room/GameAssembly.dll is 64-bit):**
- Toolchain: VS 2022 Community. `cmake`/`ninja` ship with VS; default dev shell is **x86**.
- PowerShell tool **does not persist env vars between calls**, so the amd64 env import and the
  cmake/build must run in the SAME PowerShell call, else you silently get an x86 DLL (0x014C):

```powershell
$vcvars = "C:\Program Files\Microsoft Visual Studio\2022\Community\VC\Auxiliary\Build\vcvarsall.bat"
cmd /c "`"$vcvars`" amd64 >nul 2>&1 && set" | ForEach-Object { if ($_ -match '^([^=]+)=(.*)$') { Set-Item -Path "Env:$($matches[1])" -Value $matches[2] } }
Set-Location "C:\Games\recnet-patcher-unstable"
cmake -S . -B build -G Ninja -DCMAKE_BUILD_TYPE=Release
cmake --build build
```

- Verify arch from PE header: machine word at (PE offset @0x3C)+4 must be **0x8664**, not 0x014C.
- Installed Windows SDK is **10.0.19041.0**; the VS-generator MSBuild probe fails to find it without
  the VC env, which is another reason to use Ninja inside the imported amd64 env.

**Status as of 2026-07-30 (all builds clean x64, none runtime-verified):**
- **Loading vector — DONE (self-contained, no version_orig.dll as of 2026-07-30).** `src/proxy/version_proxy.c`
  implements all 17 version.dll exports as `my_`-prefixed runtime wrappers that lazily `LoadLibraryW` the
  real System32\version.dll BY FULL PATH (GetSystemDirectoryW + "\version.dll" — full path avoids recursion
  into our own app-dir version.dll) and call through; exported under real names via `#pragma comment(linker,
  "/export:RealName=my_RealName")` aliases (NOT forwarders). Can't name them the same as the Win32 APIs
  (SDK headers mark them dllimport → clashes with dllexport), hence my_ + alias. Lazy-load on first CALL not
  in DllMain (LoadLibrary in DllMain = loader-lock deadlock). Only UnityPlayer.dll imports version.dll here
  and only 3 fns (GetFileVersionInfoA/SizeA, VerQueryValueA) but we export all 17. CMake: OUTPUT_NAME version,
  PREFIX "", `-DGAME_DIR=...` deploys just version.dll. **Earlier design shipped version_orig.dll (a renamed
  System32 copy) with static PE forwarders — replaced because the extra file confused users.** RecRoom.exe/
  UnityPlayer import VERSION.dll so our DLL loads before UnityPlayer; DllMain starts the hook thread.
- **TLS pinning bypass — DONE (implemented+wired, UNVERIFIED).** `src/unity/ssl_patch.c` waits for
  il2cpp init (`il2cpp_domain_get` non-null), sweeps assemblies via `il2cpp_class_from_name` to find
  concrete `Org.BouncyCastle.Crypto.Tls.LegacyTlsAuthentication`, gets `NotifyServerCertificate`
  (argc=1), reads the compiled entry from `MethodInfo` offset 0 (`methodPointer` — there is NO
  `il2cpp_method_get_pointer` export), and detours it to an accept-all no-op. Wired into HookThread on
  its own thread. Never calls original → trampoline corruption is moot.
- **connect/gethostbyname — intentionally NOT installed.** connect hook blindly redirects ALL :443
  (breaks Photon/CDN); getaddrinfo covers the il2cpp DNS path surgically. gethostbyname pass-through
  has a latent self-recursion bug if ever installed (calls `real_gethostbyname` not a trampoline).
- **detour.c length-aware trampoline — FIXED 2026-07-30 (was the real crash).** The blind 14-byte
  copy tore an instruction: ws2_32!getaddrinfo prologue is `48 8B C4 / 48 89 58 08 / 48 89 68 10 /
  48 89 70 18 / ...` — instruction boundaries at 3,7,11,15, so a 14-byte copy splits the 4th `mov`.
  The trampoline (`original_getaddrinfo`) then ran `48 89 70` fused with the FF25 jump bytes = garbage
  → the thread calling it died. Symptom: game booted fine (the first `getaddrinfo`, cdp.cloud.unity3d.com,
  ran on Unity's Cloud-Diagnostics *background* thread — it died silently, main thread kept going), but
  RecRoom's later `ns.rec.net` lookup hit the same broken trampoline and its thread died → request never
  sent → nothing in mitmproxy, only ONE DNS line ever logged. Fix: `insn_len`/`steal_len` in detour.c
  copy whole instructions (>=14) and NOP-pad the remainder; `steal_len` returns 0 (refuse hook, no crash)
  on rip-relative/branch/unknown. Two modes: `outTrampoline != NULL` = length-aware call-through
  (getaddrinfo); `NULL` = blind 14-byte replace-only (SSL, which never calls original). `backup_getaddrinfo`
  bumped to [32]. Confirmed decoder yields 15 for getaddrinfo.

**RUNTIME-VERIFIED 2026-07-30 (deployed to C:\Games\recflare-client-unstable):** proxy loads, getaddrinfo
detoured, il2cpp comes up, `NotifyServerCertificate` resolved+detoured, and the getaddrinfo hook sees the
game's DNS lookups — so il2cpp DNS DOES go through ws2_32 getaddrinfo. Client did NOT get kicked in the
first ~2s of logs (anti-cheat scan not yet confirmed either way over a full session).

**Mechanism pivot (user request):** DNS redirect is now **host rewrite, not static-IP synthesis** — on an
exact-match lookup we swap the hostname (ns.rec.net → ns.recflare.net) and delegate to real getaddrinfo, so
the client reaches the target's current (dynamic) IP. Config `redirector.json` now uses
`"rewrite": [ { "from": "ns.rec.net", "to": "ns.recflare.net" } ]` (EXACT match only — user rejected
subdomain matching). Parsed by flat key-scan in `src/core/config.c` (`RewriteHost` in strings.c). The old
ip/port/redirect[] fields + `ShouldRedirect` remain only for the disabled connect hook (dead for DNS). Note:
host rewrite keeps SNI/Host = ns.rec.net, so the recflare server must serve that host on 443.
README.md documents build/install.

**HTTP-layer host rewrite added 2026-07-30 (`src/unity/http_rewrite.c`) — the real fix for the requirement.**
User clarified recflare serves `ns.recflare.net` as its OWN vhost/cert, so requests must carry that host in
URL+SNI+Host header; DNS-name rewrite can't (Host is inside TLS; SNI/Host stay ns.rec.net). Replicates the
managed `SendRequestPatch` natively: call-through hook on static `BestHTTP.HTTPManager.SendRequest(HTTPRequest)`
(resolve argc=1), read `req.get_Uri().get_AbsoluteUri()`, exact host-swap via `RewriteHost`, `new System.Uri(url)`,
`req.set_Uri(newUri)`, then forward. Uses il2cpp exports runtime_invoke/object_new/string_new/string_chars/
string_length (all present). Cecil facts: Uri interop name is `Il2CppSystem.Uri` but runtime namespace is
`System`/`Uri`; ctor(String)=argc1; HTTPRequest auto-prop backing field is mangled `<Uri>k__BackingField` so we
use get_Uri/set_Uri methods. Once Uri=ns.recflare.net the getaddrinfo rewrite rule stops matching (harmless).
**This hook CALLS THROUGH so it needs a working trampoline.** Wired into HookThread own thread.

**Relocating trampoline — DONE 2026-07-30 (version.dll ~29KB).** First live run REFUSED the SendRequest hook:
its il2cpp prologue is `40 53 / 48 83 EC 50 / 48 8B D9 / 80 3D <disp32> 00` (push rbx; sub rsp,50; mov rbx,rcx;
`cmp byte[rip+0x04770393],0` — the il2cpp class-init check), steal_len=16 which includes the rip-relative cmp.
detour.c now: `decode()` classifies each insn (RK_NONE/RIPREL/REL32/UNSUPPORTED); `RelocateInto()` copies stolen
bytes and fixes rip-rel disp32 + rel32 fields; `AllocNear()` VirtualAllocs the trampoline within ±1.87GB of the
target so fixed-up 32-bit offsets stay in range. **Critical correctness point: rip is relative to the END OF THE
WHOLE INSTRUCTION (past any trailing imm8), so the fixup uses `insn.len`, NOT disp_off+4** — the cmp has an imm8
after the disp32. rel8 branches (Jcc/JMP rel8/LOOP) in a stolen prologue are still REFUSED (would need rel8→rel32
re-encode; none seen so far). SSL/DNS unaffected (SSL replace-only=blind 14B; getaddrinfo prologue is
position-independent). **CONFIRMED WORKING 2026-07-30: HTTP host rewrite fires end-to-end — mitmproxy shows a
valid request to ns.recflare.net returning the correct nameserver doc.** SendRequest prologue that needed reloc:
`40 53 / 48 83 EC 50 / 48 8B D9 / 80 3D <disp32> 00` (steal_len=16, one rip-rel cmp fixed up).

**Memory-integrity scan neutralizer added 2026-07-30 (`src/unity/memcheck_patch.c`) — for "Launch validation
failed".** After HTTP rewrite worked, boot hit the native memory-integrity scan (hashes GameAssembly code, our
inline hooks perturb it → mismatch → boot dies). This is the SAME failure the managed build's MemoryIntegrityPatch
fixed by skipping the scan-start method. NAMES ROTATE PER BUILD and the running 175MB build's global-metadata is
HEADER-SCRAMBLED (magic 0x00000100 not 0xFAB11BAF) so Il2CppDumper fails ("encrypted") — can't static-dump it.
(The 156MB recflare-client build IS clean/dumpable, but it's a different build.) So the neutralizer resolves
EVERYTHING by signature at runtime via il2cpp reflection exports (all present: image_get_class(_count),
class_get_fields/methods, field/method/type inspectors, runtime_invoke): (1) in Assembly-CSharp, find the class
with BOTH a System.Threading.Thread field AND a CancellationTokenSource field = the scanner; (2) its public
instance 0-param non-void method = scan-start, whose return type = the promise interface; (3) find that promise
type's static special-name (property getter) 0-param method returning it, excluding `_k__BackingField` = the
`Resolved` singleton getter (recipe from managed AmplitudePatch.ResolvedPromise, retrieved from git commit
6acdec8); (4) detour scan-start REPLACE-ONLY to return `il2cpp_runtime_invoke(ResolvedGetter)`. Started FIRST
among il2cpp patch threads (boot awaits the scan early — race). Heavily logs `[MEMCHECK]` candidates so an
ambiguous match is diagnosable on first launch. RUNTIME-UNVERIFIED. Il2CppDumper v6.7.46 net?-win is in
scratchpad/Il2CppDumper (RequireAnyKey set false) if a static dump of a clean build is ever needed.
User reported memcheck bypass "worked" (boot past Launch validation) 2026-07-30.

**EAC neutralizer added 2026-07-30 (`src/unity/eac_patch.c`) — ports managed EACPatches (from git 6acdec8).**
Two replace-only hooks on `RecRoom.AntiCheat.EACManager` (type name UNOBFUSCATED — resolve via
il2cpp_class_from_name sweep): (1) readiness check → force true: the sole static, 0-param, bool-returning,
NON-special-name (not a property getter) method (its obfuscated name rotates: EJDEKGFDNMB/MCFIOBHCFBB/
IMMGELPFGCK/FJLMLEPOKGE across builds — resolve by that signature); (2) `GenerateChallengeResponse` (argc=1,
unobfuscated) → return base64(UTF8(challenge)), empty/null→base64("nothing"). Native GcrHook reads RCX,RDX,R8
and picks challenge by the static flag (static: RCX=challenge; instance: RDX=challenge); has its own base64 +
UTF16→UTF8. Both use il2cpp string exports (string_new/chars/length). Started on its own thread after HTTP.
Safe to patch EACManager code now that memcheck is neutralized. Logs `[EAC]`. RUNTIME-UNVERIFIED. version.dll ~37KB.
Full il2cpp patch order on threads: memcheck (first) → ssl → http → eac.

**Multi-process log-stomping gotcha (found 2026-07-30).** version.dll loads into SEVERAL processes (the
game, the EasyAntiCheat launcher/bootstrap, the crash handler). They all opened `redirector.log` with "w"
and truncated each other — the EAC-launcher process (stuck forever in WaitForUnity because UnityPlayer never
loads there) kept re-dumping the module list and clobbered the GAME process's [DETOUR]/[SSL]/[HTTP] lines,
making it look like the HTTP hook never ran. Diagnosis tell: the surviving log had only [THREAD]+[UNITY]
"Waiting for UnityPlayer.dll..." from one TID plus endless [MODULE] dumps, and the game's DNS lines were on a
different TID entirely. Fixes: (1) logger writes per-PID `redirector_<pid>.log`; (2) WaitForUnity is now
bounded (60s) and HookThread bails in non-game processes; (3) module watcher dumps once then only announces
GameAssembly/UnityPlayer load and stops; (4) LogProcessInfo() logs the exe name at startup. **To read the
game's log, pick the `redirector_<pid>.log` containing `[STATUS] DNS REDIRECT ACTIVE`.** RUNTIME-UNVERIFIED
whether the HTTP host rewrite actually fires (need the clean per-PID game log next). Note: early ns.rec.net
requests that fire before the HTTP hook installs (during il2cpp init) get DNS-rewritten to recflare's IP but
still carry Host=ns.rec.net → recflare would reject those; the HTTP hook must be up before the first API call.
