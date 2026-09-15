# Reproducible patcher plan

> The MelonLoader-based reproducible client patcher — architecture, status, and how names are resolved

Goal (user, 2026-07-21): a **reproducible, open-source, configurable** Rec Room client patcher.
Workflow is "download clean build from Steam, then inject patches (MelonLoader etc.)", so the game
folder is disposable and the patcher is the injection step.

**Loader decision: MelonLoader, not BepInEx.** BepInEx 6 crashes in `il2cpp_init` on current builds
(see [bepinex-crashes-new-build](bepinex-crashes-new-build.md)). MelonLoader 0.7.3 loads fine and — once the correct
`global-metadata.dat` is in place — its generator produces `MelonLoader/Il2CppAssemblies/` for the
exact build (`Assembly Generation Successful!`). The earlier crash was a **patched/mismatched
metadata** file (user restored it); that mismatch also caused the "stripped code registration"
Cpp2IL failures — NOT real anti-tamper.

**Implemented:** MelonLoader mod at `melon/` in the repo (`RecNetMelon.csproj`, `RecNetMod.cs`,
`Patches/RecNetPatches.cs`, `README.md`). Builds clean, deploys to `<game>\Mods\RecNetMelon.dll` via
post-build. References `<game>\MelonLoader\net6` + `MelonLoader\Il2CppAssemblies`. Config via
MelonPreferences category `[RecNet]` in `UserData/MelonPreferences.cfg`.

**Key design — resolve obfuscated targets by SIGNATURE, not name** (Rec Room re-obfuscates every
build with Beebyte; hard-coded names are why patches kept breaking):
- Photon: patch every method returning `Photon.Realtime.AppSettings` that isn't a `get_` getter,
  in `Assembly-CSharp` + `Il2CppRecRoom.Networking.PhotonImpl.Runtime` (postfix overwrites from config).
  In the 07-21 build these are `LEALBOODIEE.GBNKOFMAJPA`, `PUNNetworkManager.OIMACPCFIKN(string,bool)`,
  `HDEJKABEHLO.GBNKOFMAJPA`, `PMGKJFMNAGJ.DPPLANLNNAN(string)` — but we never name them.
- EAC readiness: the one private `static bool` parameterless method on `EACManager` (was `FJLMLEPOKGE`
  in depot, `IMMGELPFGCK` in 07-21).
- Stable names (patched directly): `EACManager.GenerateChallengeResponse`,
  `HTTPManager.SendRequest(HTTPRequest)`, `LegacyTlsAuthentication.NotifyServerCertificate`,
  `CheatManager.CheckForDUIDMismatch`.

**Runtime findings (2026-07-21 launches):**
- MelonLoader loads + patches apply (v2 log showed all sections patching, incl. `PUNNetworkManager.OIMACPCFIKN`
  and `LEALBOODIEE.GBNKOFMAJPA`). But the client **exits cleanly during OnInitializeMelon** (no native
  crash dump, Player.log ends at MelonLoader "MODIFIED" banner). ML alone (no mod) reached the menu, so
  it's OUR patching that quits it.
- Native EAC is NOT the cause: `steam_appid.txt`=480 (Spacewar spoof), EasyAntiCheat not in the loaded
  module list. Suspect Rec Room's **managed tamper check** (Rranticheat `EACManager` / `CheatManager`)
  calling Application.Quit when its own code is Harmony-patched.
- Two bugs fixed: EAC-readiness lookup used `BindingFlags.NonPublic` but Il2CppInterop emits proxies as
  **public** (must scan Public|NonPublic); DUID prefix skipped the `out string` param (now sets it).

**CONFIRMED WORKING end-to-end as of 2026-07-21** (user: "everything works"). Working config: TLS + HTTP
+ 2 Assembly-CSharp Photon providers; `DeactivateManagers`, `EnableEacChallenge`, `EnableEacReady`,
`EnableDuid` all OFF. User's takeaway: deactivating CheatManager/EACManager (and other anti-cheat-touching
patches) was what destabilized it — KEEP THOSE OFF unless a specific need arises. Note: in the pre-toggle
builds (v1/v2) the manager deactivation ran unconditionally in OnSceneWasLoaded; it's now gated OFF.

**Critical il2cpp gotcha (cost many launches):** patching/reflecting certain interop methods
hard-faults il2cpp *natively* and kills the client with NO managed exception and NO crash dump. The
confirmed faulter is patching the PhotonImpl providers `HDEJKABEHLO.GBNKOFMAJPA` /
`PMGKJFMNAGJ.DPPLANLNNAN` (GetMethods/h.Patch on those types). **Correction (verified 2026-07-21 via a
diagnostic probe):** `AccessTools.TypeByName` does NOT hard-fault — it survives, just spamming catchable
`ReflectionTypeLoadException` warnings for malformed generic proxies (`InjectedSingletonMonoBehaviour\`2`).
So the earlier "TypeByName hard-faults" belief was wrong; the real killer was the PhotonImpl method patch,
fixed by omitting those two providers (the two Assembly-CSharp providers redirect Photon fully).

**Final design (refactored):** split into one-file-per-concern under `melon/Patches/`
(PatchUtil, Patcher, TlsPatch, HttpPatch, PhotonPatch, EacPatch, DuidPatch, SceneManagers). All targets
referenced by compile-time `typeof(...)` + `AccessTools.Method` (BepInEx/Vanadium style) — compiles
against the generated Il2CppAssemblies so an obfuscated-name rotation breaks the BUILD loudly instead of
silently no-op'ing. Removed the ResolveType/ResolveMethod helpers (unnecessary — typeof avoids scan+spam).
Refresh obfuscated Photon names in PhotonPatch.cs per build via offline Cecil scan.

**Photon providers** (obfuscated, in `PhotonProviders` array, regenerate per build via offline Cecil scan
for methods returning AppSettings): working = `Assembly-CSharp` `PUNNetworkManager.OIMACPCFIKN` +
`LEALBOODIEE.GBNKOFMAJPA`. DISABLED = the two in `RecRoom.Networking.PhotonImpl.Runtime`
(`HDEJKABEHLO.GBNKOFMAJPA`, `PMGKJFMNAGJ.DPPLANLNNAN`) — reflecting over those types faults even with the
safe lookup. **Confirmed NOT needed:** Photon redirect works end-to-end with just the two Assembly-CSharp
providers (user confirmed 2026-07-21). Leave the PhotonImpl ones disabled.

**Per-patch toggles** in config (`EnableTls/EnableHttp/EnablePhoton/EnableEacChallenge/EnableEacReady/
EnableDuid/DeactivateManagers`); anti-cheat-touching ones default OFF (can trip Rec Room's managed tamper
check → Application.Quit). **Next:** verify redirect actually works with recflare config (ServerHost,
Photon app IDs, EacChallengeResponse — server-specific, user must supply), then decide if PhotonImpl
providers / EAC challenge are needed.

Tools in `scratchpad/tools`: Cpp2IL pre.21 + StrippedCodeRegSupport, MelonLoader 0.7.3. `ilspycmd`
for decompiling; Mono.Cecil (from `MelonLoader/net6`) for fast signature scans.
