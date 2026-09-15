# Launch validation boot failure

> SOLVED + runtime-confirmed: \"Launch validation failed. Is Rec Room installed correctly?\" = the client's NATIVE MEMORY INTEGRITY SCAN (OHEPLIHINHC) detecting BepInEx's own inline hooks. Fix = skip OHLMLHJNBAL

Boot failure `Launch validation failed. Is Rec Room installed correctly?` on build 20230616
(`C:\Games\recflare-client`). **Still open** as of 2026-07-27.

## ✅ Root cause (CONFIRMED at runtime 2026-07-27 — boot proceeds to account login)

### The native memory integrity scan (`OHEPLIHINHC`, Assembly-CSharp)

**It is BepInEx's own hooks that trip it. Nothing server-side is involved.** HarmonyX installs hooks
by overwriting the first bytes of native functions with jump trampolines, so a hash over
`GameAssembly.dll`'s executable memory can never match. ANY BepInEx-loaded client fails this,
pointed at any server.

`OHEPLIHINHC` is identified by its private static Win32 toolkit — the signatures, never the names:

```
IntPtr GAGFPALJNKJ(string)                 GetModuleHandle / LoadLibrary
IntPtr EFNDMBILAKK(IntPtr, string)         GetProcAddress
IntPtr GPIIOCAPDLN()                       GetCurrentProcess
Int32  DJCBBKNHHDJ(IntPtr, IntPtr, Int32)  memory read / compare
void   LKMJGILNHCG(DAFGDOMLDFF, byte[], List<IntPtr>)   hash buffer over pointer list
Thread PKCINLGIHPE  +  CancellationTokenSource LKKPLEEDIPO   background scan
OOPPNGPPPLE OHLMLHJNBAL()                  public instance 0-param entry point  <-- HOOK THIS
```

Maps to `ACBODHFEDLF.Memory_Hash_Mismatch=500` / `Native_Memory_Hash_Mismatch=700`.

**Fix:** `Patches/MemoryIntegrityPatch.cs` prefixes `OHLMLHJNBAL` and substitutes an already-resolved
promise (`AmplitudePatch.ResolvedPromise()`), skipping the scan. Knob
`[Advanced] Disable Memory Integrity Check`, default true, logs `[MEMCHECK]`.

## Ruled out — the "eac challenge failed" theory was a RED HERRING

The message is the display text for error code `FKEHJLEGOKO.LAUNCH_VALIDATION_FAILED = 15`. An xref
found `FPJKNNCGJKI.AMJBCANMGEP` — an OAuth token-error mapper selecting 15 on the server string
`"eac challenge failed"` — and it looked conclusive:

```
0x3bb30d8  STR "eac challenge failed"
0x3bb30ec  je  <next check>      ; no match
0x3bb310c  mov ecx, 0xf          ; 15 = LAUNCH_VALIDATION_FAILED
0x3bb3113  call LGGFADNNINO      ; -> the message
```

Sibling branches: `invalid_grant`, `invalid_username_or_password`, `invalid time`,
`account locked indefinitely`, `platform verification failed`.

**A runtime probe demolished this.** `ErrorCodeProbePatch` showed the converter reached is
`MEINKDCJHDP`, that `AMJBCANMGEP` **never runs**, and that `GenerateChallengeResponse` is **never
even called**. `MEINKDCJHDP` has exactly ONE caller — `OHEPLIHINHC.NIJCGIEBIHJ.MFFCMMCDMLB`, a
closure rejecting unconditionally.

**Why the xref missed it:** the 15 IS a constant, materialised as
`xor edx,edx; lea ecx,[rdx+0xf]`. An immediate-operand scan cannot see that. It then cost a second
wrong turn — concluding "so the code must arrive as a variable." **Decode lea-form constants.**

`GenerateChallengeResponse` is **never called** during the failing boot, so nothing about the EAC
challenge response is involved. `EACPatches.cs` keeps its original base64(challenge) behaviour.

## Hard-won process lessons (this cost ~8 wasted launches)

**Seven client-side patches were tried and ALL failed, because there was never a client check to
bypass.** Do not repeat: KnownDlls module whitelist (`CheatManager.HEMFMDDNMJA`), Steam app-id
override, forcing the boot step to resolve, file-hash checks, CodeStage `InjectionDetector`. Also
ruled out empirically: setting `steam_appid.txt` to 471710 changes nothing.

- `SteamPlatformManager.IGFPNGDCJMP()` returns **False** and that is NORMAL — it is
  `RestartAppIfNecessary`-shaped (Packsize/DllCheck + app 471710). `Initialize` does
  `call IGFPNGDCJMP; test al,al; jne <restart path>`. Forcing it true sends boot down the
  quit branch. Do not "fix" it.
- `SteamUtils.GetAppID` is **inlined away** by IL2CPP — hooking it never fires.
- **Go to the string-xref FIRST** when a generic error message has no obvious owner. Pattern-matching
  levers against other mods was the expensive path.

## The xref procedure (works, ~15 min)

Il2CppDumper net6-win → `dump.cs`, `script.json`, `stringliteral.json`. Scripts in
`scratchpad/il2cpp/` (`xref.py`, `callers.py`, `disfn.py`, plus `find15b/c.py` arg-decoders).

1. `stringliteral.json` maps text → literal address (far smaller than script.json; grep it, not script).
2. `xref.py` finds RIP-relative refs to that address → owning method via ScriptMethod bisect.
3. If the refs land in a `.cctor`, the string is a **table entry**, not the logic — find the enum key
   and x-ref the enum→message converters instead.
4. Decode the constant passed at each call site by disassembling backwards.

**Two traps that cost time here:** (a) there were TWO enum→message converters (`LGGFADNNINO` AND
`MEINKDCJHDP`) — x-ref both; (b) constants are materialised as `lea edx,[r8+N]`, not just
`mov edx,N`, so byte-pattern scans miss them — decode properly.

**Enum member names survive obfuscation** (`LAUNCH_VALIDATION_FAILED`, `STEAM_LOGIN_CODE_1`), as do
state-machine locals and display-class fields (`hashCheckStartTime`, `warningKey`, `reportCategory`).
These are the most durable handles in an obfuscated build.

**Compiler-generated lambda names do NOT survive into this build's interop.** Other projects patch
`<CreateHileWarning>b__0`, `<OnUnknownDLLDetected>b__0`, `<CheckHashesInBackground>b__0` by name; a
scan for those in build 20230616 returns **nothing**, and a predicate-based patcher keyed on them
silently no-ops. Find the owning type by its display-class *field* instead.

## The anti-tamper report funnel (`AAKMENFOFEI`, RecNet.Runtime.dll)

Every tamper detection funnels through one **static, concrete** method — hook this rather than
individual callbacks:

```
AAKMENFOFEI.GIOHEBODOAC(ACBODHFEDLF kind, string detail, Nullable<int> code) -> OOPPNGPPPLE
```

`ACBODHFEDLF` is the violation taxonomy and reads in full (enum names survive):
`Obscured=0 Time=1 Inject=2 GiftCount=3 Engine=4 UnknownDll=5 ImageSignature=6 AvatarHack=7`,
`NetworkCertificate*=100-103`, `Autosave*=150-152`, `Photon_*=200-204,400`,
`AppData_Runtime_*=300-302`, `AppData_Boot_*=310,311`, `Config_*=320,321`,
`Memory_Hash_Mismatch=500`, `Driver_Invalid_Signature=600`, `Native_Memory_Hash_Mismatch=700`.

`Inject` and `UnknownDll` are the BepInEx-relevant ones (it injects via winhttp.dll). Covered by
`Patches/AntiTamperPatch.cs` / `[Advanced] Suppress AntiTamper Reports`, which logs `[ANTITAMPER]`
before suppressing so a launch reveals whether the path fires at all.

## Note on mitmproxy

BestHTTP does **not** use the Windows system proxy, so a system-level mitmproxy sees no client
traffic. Use the plugin's `[Advanced] Debug` knob (logs request/response bodies from inside BestHTTP)
instead of concluding "no calls are being made".
