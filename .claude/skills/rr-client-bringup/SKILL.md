---
name: rr-client-bringup
description: Get an obfuscated Rec Room client to boot, stay alive and load rooms against a self-hosted server - launch-validation and anti-tamper scans, CheatManager module detection, Themida/Referee-protected builds, the image content-signature stall, the serialized HTTP queue, telemetry kill switches, and which loader vector works per build. Use for crashes, silent quits, hangs on load, or choosing how to inject into a new build.
---

# Rec Room client bring-up

Everything needed to make a client run against a self-hosted backend. These are **client-side**
failures: the server is usually fine and the symptom is a crash, a silent quit, or a load that never
finishes.

> Before resolving any obfuscated name from a log or trace, confirm **which build** you are on -
> see the `il2cpp-analysis` skill. Names and RVAs here are per-build and re-roll every update.

## Symptom -> reference

| Symptom | Read |
|---|---|
| `Launch validation failed. Is Rec Room installed correctly?` | `launch-validation-boot-failure` |
| Clean-looking "user quit" after idling, orderly logout | `cheatmanager-module-scan-quit` |
| Stuck on "Downloading", ~30 s timeout, room never loads | `image-content-signature-bypass` |
| Room load takes minutes, or works then breaks at random | `serialized-request-queue-stall` |
| BepInEx crashes in `il2cpp_init` | `bepinex-crashes-new-build` |
| New build: no il2cpp exports, no VERSION.dll import, decoy metadata | `referee-protected-build-23191908` |
| Injection refused / DLL planting ignored | `unstable-build-proxy-vector-wintrust` |
| Store or wardrobe items silently missing, no request, no log | `avatar-item-desc-registry` |

## The two counter-intuitive ones

**Blocking a dead telemetry host makes load *worse*, not better.** All client HTTP shares one FIFO
queue, so a host that hangs or refuses holds every later request behind it. Dead hosts must return an
instant 200/204. This single fact explains most of the "it worked yesterday" history -
`serialized-request-queue-stall`.

**A failed image signature check is not a cosmetic problem.** It stalls the same shared pump, so the
room save-data blob misses its timeout and the room never loads -
`image-content-signature-bypass`.

## Known-good configuration

`recflare-2025-working-client` records the combination that actually boots, enters arbitrary rooms
and holds a session, and the four fixes that were all required together. Start from it rather than
rebuilding a client from first principles.

## References

| Reference | What it settles |
|---|---|
| [avatar-item-desc-registry](references/avatar-item-desc-registry.md) | 2025 client resolves AvatarItemDesc through a CLIENT-BAKED descToCaidMapping built in Awake from the shipped wardrobe asset; an unknown desc is dropped SILENTLY with no log, and no server payload can add one |
| *(moved)* [rr-avatar-assets](../rr-avatar-assets/SKILL.md) | Resolving an AvatarItemDesc to the shipped asset/bundle, and packaging shipped items as CustomAvatarItem exports, now live in their own skill — `desc-registry-2023-layout` and `cai-export-format` moved there. |
| [bepinex-crashes-new-build](references/bepinex-crashes-new-build.md) | Why BepInEx stopped working after the 2026-07 Rec Room upgrade and how the diagnosis was reached |
| [build-20230414-obfuscation](references/build-20230414-obfuscation.md) | Installed Rec Room build at recflare-client is now manifest 3332492622123310277 (was 20230414 / 3668280474894052876); per-build obfuscated target names for Photon, EAC, Amplitude promise |
| [build-23191908-dump-and-rvas](references/build-23191908-dump-and-rvas.md) | Full RVA-annotated Cpp2IL source dump for build 23191908 (2026-05-12) lives at C:\\Games\\RecRoom_Info; hook RVAs + the finding that TLS is in-process-only (BouncyCastle custom verifier, not system store) |
| [cheatmanager-module-scan-quit](references/cheatmanager-module-scan-quit.md) | recflare-2025's CheatManager scans loaded modules, finds the injected 2025Patch.dll, and force-quits via SessionManager.FatalApplicationQuit(533223478) — the real cause of the idle \"auto logout + quit\". |
| [econ-store-layer-rro-items-split](references/econ-store-layer-rro-items-split.md) | Two accounts get different stores because econ_store_layer/use_unified_avatar_item_search buckets per user at statsigapi.net: false (the hardcoded default) shows the "RRO Items"/UGC chips, true shows the unified search that calls api/customAvatarItems/v1/search. Also: Statsig bindings live in PREFABS not the DLL, and bundlescan.py silently reports 0 on a zeroed bundle copy. |
| [image-content-signature-bypass](references/image-content-signature-bypass.md) | Mirrored rec.net images carry an unsatisfiable RSA content-signature; the failed check stalls the shared request pump and blocks ROOM LOAD, not just artwork. Bypass RVA for build 20250718.01. |
| [launch-validation-boot-failure](references/launch-validation-boot-failure.md) | SOLVED + runtime-confirmed: \"Launch validation failed. Is Rec Room installed correctly?\" = the client's NATIVE MEMORY INTEGRITY SCAN (OHEPLIHINHC) detecting BepInEx's own inline hooks. Fix = skip OHLMLHJNBAL |
| [recflare-2025-working-client](references/recflare-2025-working-client.md) | recflare-2025 + recnet-plugin-unstable is the WORKING archival client (enters rooms); supersedes the Themida-blocked recflare-client-unstable path. |
| [referee-protected-build-23191908](references/referee-protected-build-23191908.md) | Rec Room build 23191908 (depot 471711, downloaded 2026-08-11) ships Themida-packed Referee.dll; strips ALL il2cpp exports + VERSION.dll import + real global-metadata, breaking the native redirector's loader and all four il2cpp patches |
| [reproducible-patcher-plan](references/reproducible-patcher-plan.md) | The MelonLoader-based reproducible client patcher — architecture, status, and how names are resolved |
| [serialized-request-queue-stall](references/serialized-request-queue-stall.md) | The 2025 client serializes ALL HTTP through one FIFO queue; a retrying telemetry POST holds it ~25s and pushes the room-save blob past its 30s timeout. Blocking dead hosts makes this WORSE, not better. |
| [statsig-layers-and-hook-point](references/statsig-layers-and-hook-point.md) | Statsig layer params (watch_layer, econ_store_layer, avatars_experiment_layer...) are NOT reachable from the dotted gate-config object — separate system, hardcoded to statsigapi.net. Single choke point to force them all: MGDBOHJAGBN.LMKONLJOAEP<T>(paramName, default) on the layer object. |
| [telemetry-kill-switches](references/telemetry-kill-switches.md) | How to switch off each third-party telemetry sink in recflare-2025: DataCollection.Enabled gate (data/event), Backtrace via missing server config or Backtrace.SampleRate, Statsig via an empty key (falls back to defaults). Statsig/Backtrace/Rudderstack URLs are HARDCODED to third-party hosts. |
| [unstable-build-identity-rvas](references/unstable-build-identity-rvas.md) | recflare-client-unstable is Rec Room build 2025-04-29 (dump at RecRoom_Info/Code/2025-04-29_02-57-34); GameAssembly is on-disk-ENCRYPTED with stripped exports, so hook by hardcoded RVA at runtime |
| [unstable-build-proxy-vector-wintrust](references/unstable-build-proxy-vector-wintrust.md) | recflare-client-unstable (pre-Referee 2025 build) DEFEATS app-dir DLL planting (pre-loads System32 crypto); working loader vector is a DXGIDisplays.dll Unity-plugin proxy, NOT version/wintrust/bcrypt/crypt32 |
| [unstable-native-redirector-build](references/unstable-native-redirector-build.md) | How to build the native redirector.dll in ../recnet-patcher-unstable (x64, vcvars-in-same-call gotcha) |
