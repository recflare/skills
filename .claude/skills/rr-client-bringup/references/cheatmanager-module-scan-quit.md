# Cheatmanager module scan quit

> recflare-2025's CheatManager scans loaded modules, finds the injected 2025Patch.dll, and force-quits via SessionManager.FatalApplicationQuit(533223478) — the real cause of the idle \"auto logout + quit\".

Build `20250718.01` ships a live anti-cheat module scan. `CheatManager` (Assembly-CSharp — the class
name is **not** obfuscated) enumerates loaded modules, strips the app directory from each path
(sibling closure `JFOAEHOCCIN.EAMAJENBDLL` does `s.Replace(appPath, "")`), formats them as
`[index:name]`, and calls:

```csharp
private sealed class LFKHKEPJKMB {        // compiler-generated closure, RVA 0x2148FB0
    public string filenames;              //   field @0x10
    internal void LOELLDBOINB() {
        SessionManager.FatalApplicationQuit(533223478, filenames);
    }
}
```

Confirmed at runtime 2026-08-17: fired with `filenames = "[0:2025Patch.dll]"` — the injected patch
DLL — 30ms before `AppExitState: Running => PreparingToExit`.

**Fix shipped and CONFIRMED 2026-08-17:** replace-only hook on `0x2148FB0`
(`RR::Methods::AntiCheat::ModuleScanDetected`), never calling the original. Session then ran 196s+
with zero `AppExitState` transitions, versus quits at 40/47/95/138s before. Suppresses the reaction, not the detection — the scan still finds us.
PEB loader-list unlinking (`recnet-patcher/src/memory/module_hide.c`) would defeat it at the source
and is the better fix if the scan ever grows a second consumer.

**The symptom is deeply misleading.** It presents as a *clean* shutdown, so every crash-shaped
hypothesis is wrong: `app_exit_state=ReadyForExit`, `crash_detected=false`, orderly Photon `Leave`,
`player/logout`, full `Application.quit`. Timing varies (40s-140s) with the scan, so it also looks
like a timeout. `player/logout`, Photon `Leave`/`Disconnect`, and `RaiseEvent` failures are ALL
downstream of the decision — logout lands 0.14s *after* it. Photon is provably innocent: with the
`DeserializeEventData` hooks in place there are zero `ErrorInfo` (251) events.

**How it was found (repeat this, it is fast):** the quit code `533223478` (`0x1FC85836`) is a fixed
constant baked into `LOELLDBOINB`, not a dynamic reason. Scanning GameAssembly.dll for the immediate
`B9 36 58 C8 1F` (`mov ecx, 0x1FC85836`) gave exactly ONE hit and landed directly in the call site.
Do that first after a build rolls, instead of walking stacks.

Also useful: `SessionManager` keeps most of its method names (`FatalApplicationQuit`,
`TryApplicationQuit`, `LogoutToBootScene`, `VerifyAccountRequirements`, `HandleRoomJoinFailure`,
`DefaultRoomGatesAsync`, `JuniorRoomCheck`) — dump them from `methods.pkl` with the
`SessionManager$$` prefix. `FatalApplicationQuit`'s compiled body IGNORES its message argument (it
tail-jumps to `TryApplicationQuit` with the code only), so read the message at the CALLER, not there.

**Why:** cost most of a session chasing server responses, Photon, and a real-but-unrelated
`StorefrontConfig` NRE, because a self-inflicted anti-cheat quit is indistinguishable from a clean
app exit in every log the client writes.

**How to apply:** on any "the client exits on its own and it looks clean" report for this build,
check `[CheatMgr]` / the module scan FIRST. See [recflare-2025-working-client](recflare-2025-working-client.md) and
[recflare-2025-metadata-carve](../../il2cpp-analysis/references/recflare-2025-metadata-carve.md).
