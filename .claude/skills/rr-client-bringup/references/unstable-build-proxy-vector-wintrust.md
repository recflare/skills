# Unstable build proxy vector wintrust

> recflare-client-unstable (pre-Referee 2025 build) DEFEATS app-dir DLL planting (pre-loads System32 crypto); working loader vector is a DXGIDisplays.dll Unity-plugin proxy, NOT version/wintrust/bcrypt/crypt32

`C:\Games\recflare-client-unstable` is the pre-Referee/pre-Themida 2025 Rec Room build the user rolled
back to for archival (the [referee-protected-build-23191908](referee-protected-build-23191908.md) fight is abandoned - no Referee here).
It is the intended target of the native `C:\Games\recnet-patcher` redirector.

**Static-import DLL planting DOES NOT WORK on this build - all three crypto vectors are dead.**
`RecRoom.exe` (653 KB) is only a stub importing `RecRoom.exe.dll` (56 MB bootstrap; `UnityPlayer.dll`
also imports it). Nothing imports version.dll/winhttp here. `RecRoom.exe.dll`'s only proxyable imports
are one function each: `wintrust!WinVerifyTrust`, `bcrypt!BCryptGetProperty`, `crypt32!CryptMsgClose` -
but a live-process module snapshot proved **all three load from `C:\Windows\System32`, never the app
dir**. The bootstrap (itself a WinVerifyTrust/Authenticode integrity logger - `RecRoom.exe.log` is its
hash/signature trace, full of `0x800b0100` TRUST_E_NOSIGNATURE, tolerated) pre-loads the real System32
crypto DLLs by full path, so our planted copies are never consulted. DependentLoadFlags are 0x0 (not the
cause); the pre-load is. A wintrust proxy (165 forwarders) was built+deployed - **no
`rr_proxy_attach_*` breadcrumb and no redirector log ever appeared -> confirmed never loaded.**
`src/proxy/wintrust_proxy.c` is kept but unused.

**WORKING VECTOR - DXGIDisplays.dll Unity-plugin proxy.** A Rec Room first-party native plugin at
`RecRoom_Data\Plugins\x86_64\DXGIDisplays.dll` is LoadLibrary'd by UnityPlayer from that path at engine
startup (display setup - early and unconditional, before the ~5 s RecNet connection). No System32
equivalent, so replacing the file wins. `src/proxy/dxgi_proxy.c` = 15 forwarders (generic 4-ptr thunk)
to `DXGIDisplays_orig.dll` (a copy of the genuine plugin, same dir). `CMakeLists.txt`: `OUTPUT_NAME
"DXGIDisplays"`, `-DGAME_DIR` deploy copies the proxy into `RecRoom_Data/Plugins/x86_64`. The genuine
plugin must be renamed to `DXGIDisplays_orig.dll` ONCE by hand (done; also `.genuine_backup`). DllMain
(dllmain.c) / hook thread / il2cpp patches are unchanged and build-agnostic. `redirector.json`
(ns.rec.net -> ns.recflare.net) sits next to RecRoom.exe. DllMain has a diagnostic breadcrumb writing
`rr_proxy_attach_<pid>.txt` (remove later). **RRTexture.dll is a BAD vector** - loads too late (only on
first texture-compression call, gated behind server content the client never fetches). Recon-probe proxy
sources for both plugins predate this in `tools/plugin_proxy/`. BepInEx/doorstop 4.3.0 is in the dir but
the user confirmed it doesn't work with this Unity - ignore it. Build/x64 gotchas:
[unstable-native-redirector-build](unstable-native-redirector-build.md).
