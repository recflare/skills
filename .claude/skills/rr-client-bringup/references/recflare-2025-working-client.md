# Recflare 2025 working client

> recflare-2025 + recnet-plugin-unstable is the WORKING archival client (enters rooms); supersedes the Themida-blocked recflare-client-unstable path.

The working archival setup as of **2026-08-15** — client `C:\Games\recflare-2025`
(build `20250718.01`), patched by `C:\Games\recnet-plugin-unstable` (C++/MinHook, injected).
It already bypasses Referee and redirects hosts, so it does **not** hit the Themida wall that
dead-ended `recflare-client-unstable` + `recnet-patcher` (see [unstable-build-identity-rvas](unstable-build-identity-rvas.md)).
Status as of **2026-08-17: PLAYABLE.** Boots, logs in, avatar, loads the dorm in ~4.8s, **joins
arbitrary rooms**, and holds a session indefinitely. Joining non-dorm rooms exercises matchmaking +
room instances + Photon game servers, so self-hosted Luxon is confirmed working end to end.

Four fixes got it there, in the order they were found — all four were needed:

1. [image-content-signature-bypass](image-content-signature-bypass.md) — hook `BLDFMLMAFLH` (`0x7CF32F0`) → true.
2. [serialized-request-queue-stall](serialized-request-queue-stall.md) — stub `datacollection.recflare.net` to an instant 200
   (room load 120.5s → ~5s). ⚠️ Blocking it in DNS made things WORSE, not better.
3. `api/config/v2` must include `StorefrontConfig {MinPlayerLevelForGifting, LatestStoreBadgeDateTime}`
   or `StoreBadgeNotifications` NREs every ~15s.
4. [cheatmanager-module-scan-quit](cheatmanager-module-scan-quit.md) — replace-only hook on `0x2148FB0`; this was the "auto logs out
   and quits" that masqueraded as a clean user quit.

- Launch: `C:\Games\recflare-2025\launch-patched.bat` (starts `Injector.exe`, then the game with
  `+forcemode:screen`). The injector loads `2025Patch.dll` **from beside `Injector.exe`**
  (`recnet-plugin-unstable\x64\Release\`), NOT from the game folder — a stale copy sits in
  `C:\Games\recflare-2025\` and is ignored, so don't "fix" a build by copying there.
- Build: `MSBuild 2025Patch.sln /p:Configuration=Release /p:Platform=x64` (vswhere to locate MSBuild).
- Hosts: API `ns.recflare.net`, Photon `photon.recflare.net` (self-hosted Luxon, via DNS hook on
  `getaddrinfo`/`GetAddrInfoW`). A `UsePhotonCloud` flag in `Patches.h` A/B-tests against real Photon
  Cloud — **Luxon was exonerated this way**; Cloud reproduced the failure identically.
- Diagnostics: `2025patch.log` next to the game exe (timestamped, flushed per line) plus Unity's
  `%USERPROFILE%\AppData\LocalLow\Against Gravity\Rec Room\Player.log`. **Player.log timestamps run
  3h behind `2025patch.log`** — offset by hand when correlating.
- The matching Cpp2IL dump is `RecRoom_Info/Code/2025-07-19_02-45-25` (verify via
  `SendRequest = 0x77E0950`). It is **signature-only — method bodies are stubs**, so it gives RVAs
  and shapes but no call graph or string literals.

- Diagnostic hooks still installed in `Patches.h` and safe to strip once no longer wanted:
  `[Pump]`/`[Send]` (CBACIMLIBPF queue), `[Exit]`/`[Quit]`/`[Shutdown]` (quit tracing), and the
  Photon `DeserializeEventData` event tracer. The four hooks above are the ones that must stay.

**Why:** two client folders and two patcher projects look interchangeable but aren't; the
`recnet-patcher` / `recflare-client-unstable` pair is a proven dead end (Themida anti-tamper kills
the session at ~35s regardless of patching), and re-testing there wastes days.

**How to apply:** do 2025-era archival work in `recnet-plugin-unstable` against `recflare-2025`.
Treat `recnet-patcher` as historical unless the target is specifically the 2025-04-29 build.
