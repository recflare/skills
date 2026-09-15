# BepInEx crashes new build

> Why BepInEx stopped working after the 2026-07 Rec Room upgrade and how the diagnosis was reached

After the 2026-07-21 Rec Room build (install at `C:\Games\recflare-client`), BepInEx no longer loads:
no `LogOutput.log`, no `BepInEx.cfg`, empty `BepInEx/interop`. Root cause is a **loader-level crash,
not obfuscated-name drift**: the game **crashes inside `il2cpp_init`** while BepInEx's Doorstop
`winhttp.dll` proxy is hooked in. Evidence is the game's own `Player.log` crash stack:
`(GameAssembly) il2cpp_init` ← `(WINHTTP) WinHttpWriteProxySettings` (Doorstop proxy @ 0x180000000)
← `(UnityPlayer) UnityMain`.

Ruled out by comparison against the depot build `C:\Games\depots\471711\23191908` where BepInEx
worked (its log: `BepInEx 6.0.0-be.697 ... Running under Unity 2020.3.33f1`):
- BepInEx binaries are **byte-identical** (same md5 for BepInEx.Unity.IL2CPP.dll, Il2CppInterop.Runtime.dll 1.4.6, 0Harmony.dll) — not a BepInEx version regression.
- IL2CPP **metadata version is 27** on all builds — not a metadata bump.
- GameAssembly.dll PE layout/entropy (~6.49) is normal — **not packed/encrypted**.
So only the new game binary changed; it breaks the BepInEx/Doorstop il2cpp_init path.

**CRITICAL — the patch names are NOT the problem.** Verified against the raw `global-metadata.dat`
string tables: the 07-21 build shares the **same obfuscation seed as the depot build**
`C:\Games\depots\471711\23191908` (2026-06-14) that our patches already target. `GPFPFDBGCEK`,
`AMOHMPKKGHL` (Photon `PhotonPatches.cs`) and `FJLMLEPOKGE` (EAC IsReady) all exist in **both** depot
and 07-21, and the depot `BepInEx/interop` (Assembly-CSharp.dll, RecRoom.Rranticheat.Runtime.dll)
already declares them. So **the depot interop is a valid compile reference for 07-21** and the existing
patch names are correct. Vanadium's 07-10 build is a *different* seed (`OIMACPCFIKN`/`GBNKOFMAJPA`/
`HDEJKABEHLO`/`LEALBOODIEE`) — a red herring; don't chase those.

**07-21 cannot be statically dumped.** Latest Cpp2IL (2022.1.0-pre-release.21) **+** the
`StrippedCodeRegSupport` plugin still fails with "Failed to find code registration or metadata
registration" — the build strips BOTH registration structs. Static dumpers (Cpp2IL, Il2CppDumper,
BepInEx/ML file-based generators) can't reconstruct interop from disk; only a **runtime** dump
(in-process, querying live IL2CPP via GameAssembly's exports) works. This is why the community uses
MelonLoader — but even ML's file-based generator may fail; may need pre-generated assemblies.
Workaround for building: use the depot interop (names match).

Community fix = **MelonLoader** (`version.dll` proxy). Working reference mod:
`C:\Users\devin\Downloads\Vanadium\Mods\Vanadium.dll` = Skyfire "SSCS 2023 Patch" (decompiled to
`scratchpad/Vanadium.decompiled.cs`) — same jobs as our patches: HTTPManager.SendRequest redirect,
LegacyTlsAuthentication.NotifyServerCertificate skip, EACManager.GenerateChallengeResponse override,
Photon AppSettings postfixes, destroys CheatManager+EACManager on scene load.

Goal (per user 2026-07-21): a **reproducible, open-source, configurable** client patcher — not a
one-off. Tools local: `ilspycmd`; latest Cpp2IL pre.21 + StrippedCodeRegSupport plugin in
`scratchpad/tools`. See [reproducible-patcher-plan](reproducible-patcher-plan.md).
