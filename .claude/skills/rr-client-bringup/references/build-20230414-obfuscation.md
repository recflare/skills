# Build 20230414 obfuscation

> Installed Rec Room build at recflare-client is now manifest 3332492622123310277 (was 20230414 / 3668280474894052876); per-build obfuscated target names for Photon, EAC, Amplitude promise

Tracks the obfuscated Harmony targets per installed Rec Room build at `C:\Games\recflare-client`.
Full rename tables also live in the repo's `CLAUDE.md` ("Surviving a game-version upgrade").

## ⚠️ The installed client gets swapped between builds — always re-verify before analysing

Devin keeps multiple client builds and swaps `C:\Games\recflare-client` between them, so
`GameAssembly.dll` + `BepInEx/interop/` can change **mid-session**. On 2026-07-29 it flipped twice
inside one conversation. Never trust a name or RVA carried over from earlier in a session.

**One-second identity check** — byte-search `BepInEx/interop/*.dll` for a marker name:

| marker present | build | matching branch |
| --- | --- | --- |
| `HPEENKELKDJ`, `LAHBDKNMNHN`, `HGDLKGAFGLC` | 20230414 | `main` |
| `PAAJLJEEAKL`, `OOPPNGPPPLE`, `PKDPHCDFEND` | manifest 3332492622123310277 | `20230621` |

A branch whose obfuscated names don't match the installed interop **fails to compile** (CS0246 on
`typeof(...)`), which is itself a fast identity check — and the reason the tree must be on the branch
that matches the client. Cached Il2CppDumper dumps live in per-session scratchpads under
`%LOCALAPPDATA%\Temp\claude\C--Games-recnet-patcher\*\scratchpad\il2cpp\out\`; pick the one whose
`dump.cs` contains the marker rather than re-dumping (grep for the marker, ~1s).

**Compiler-generated names survive obfuscation and survive build swaps** — hoisted async locals
(`<inventionDataBlob>5__8`), display-class fields, `<Method>b__0`. Resolving a target by *those*
via Cecil (find the type whose fields include `inventionDataBlob`, then read its obfuscated name)
re-derives an obfuscated target for any build in seconds. This is strictly better than re-dumping.

## Previous: Steam manifest 3332492622123310277 (resolved 2026-07-27)

- Photon AppSettings: `PAAJLJEEAKL.PKPMKAKCJLO` — Assembly-CSharp, instance, **1 param** now
- EAC is-ready: `EACManager.EJDEKGFDNMB` (static, 0-param, non-getter bool)
- Amplitude promise type: `OOPPNGPPPLE` (was `LAHBDKNMNHN`), in `RecRoom.Promises.Runtime`
- `CheckForDUIDMismatch` out-param → `GKBGCOJDCLB` (bound as `__0`, no source change)

Two things this build taught that the old signature rules missed:

1. **The Photon target's arity changed** (0-param → 1-param), so "the only *0-param* method returning
   `AppSettings`" no longer finds it. Search on return type alone, across *all* interop — and note the
   identically-named `IBINNEHOCDK.PKPMKAKCJLO` in `RecRoom.Networking.PhotonImpl.Runtime` is the
   IL2CPP **interface** (base `Il2CppObjectBase`); patching it is a silent no-op ([reproducible-patcher-plan](reproducible-patcher-plan.md)).
2. **The csproj `<Reference>` list drifts every build** — this one dropped 11 interop assemblies and
   added 40. Stale entries are MSB3245 *warnings*, not errors, so they pile up unnoticed. Regenerate
   the whole `ItemGroup` from a directory listing of `BepInEx/interop/` after an upgrade.

## Previous: build 20230414 (manifest 3668280474894052876)

- Photon `HPEENKELKDJ.MGKINLFMJLB`; EAC `EACManager.MCFIOBHCFBB`; DUID out-param `BPOGCIINKBB`.

**Trap that cost several cycles (2026-07-22):** interop got regenerated with *different* name sets
across launches (14:13 → `IHODDIDPEOD/KOIFGPGJGKB`; 15:14 → `LEALBOODIEE/IMMGELPFGCK`; 15:31 → final).
Only the generation whose mtime is *after* the last game launch, that also gives a clean `typeof`
compile + clean HarmonyX load, is authoritative. Never trust a Cecil scan of an interop a later launch
may overwrite.
