# Build 23191908 dump and rvas

> Full RVA-annotated Cpp2IL source dump for build 23191908 (2026-05-12) lives at C:\\Games\\RecRoom_Info; hook RVAs + the finding that TLS is in-process-only (BouncyCastle custom verifier, not system store)

`C:\Games\RecRoom_Info` (a git repo; also has [referee-protected-build-23191908](referee-protected-build-23191908.md)'s `DUMPING.md`) holds
per-assembly **Cpp2IL source dumps** under `Code/<timestamp>/`. The dir **`Code/2026-05-12_18-46-14/`**
is exactly build **23191908** (the installed depot 471711 build). Every method carries
`[Cpp2IlInjected.Address(RVA=..., Offset=..., VA=...)]` — so this is the source of **hardcoded per-build
RVAs** (user sanctioned hardcoding; game is dead). `RecNet.Runtime.cs` is the big one (BestHTTP +
BouncyCastle + RecNet). Bodies are stubbed (`return null`) — Cpp2IL recovers signatures/RVAs/field
offsets, **not** method bodies; to read actual logic you still need disassembly over a decrypted
GameAssembly (not present for this build in RecRoom_Info — only the .cs is).

**Hook RVAs for build 23191908** (GameAssembly VA = 0x180000000 + RVA; at runtime use actual load base +
RVA):
- `BestHTTP.HTTPManager.SendRequest(HTTPRequest)` — **RVA 0x8FA14B0** (VA 0x188FA14B0). Host-rewrite hook
  point (call-through). `RecNet.Runtime.cs:31869`.
- `LegacyTlsAuthentication.NotifyServerCertificate(Certificate)` — **RVA 0x8FA51E0** (VA 0x188FA51E0,
  vtable Slot 6). TLS accept-all hook point (replace-only). `RecNet.Runtime.cs:30152`.
- `LegacyTlsAuthentication.GetClientCredentials` — RVA 0x8FA5110 (Slot 7).
- `LegacyTlsAuthentication..ctor(Uri, ICertificateVerifyer, IClientCredentialsProvider)` — RVA 0x139A5F0.

**TLS validation — external-vs-in-process is NOT yet decided (I earlier over-claimed "in-process only").**
The client validates server certs via **BestHTTP's bundled BouncyCastle** (`BestHTTP.SecureProtocol.Org.
BouncyCastle.*`) through a custom `ICertificateVerifyer` — not the Windows store. But there are TWO
concrete verifiers, and which one RecNet wires in is NOT visible in the stubbed Cpp2IL source:
- `AlwaysValidVerifyer.IsValid(Uri, X509CertificateStructure[])` — **RVA 0xD24D80** (Slot 4). Accept-all
  by name. If this is the one in use, recflare's cert (even self-signed) is accepted → **external
  redirect works, Referee is moot.**
- `TimeValidVerifyer.IsValid` — **RVA 0x8FA73E0** (Slot 4). Validity-window check.
- `LegacyTlsAuthentication.NotifyServerCertificate` — RVA 0x8FA51E0 (Slot 6) — the enforcement point
  that calls `verifyer.IsValid`; field `verifyer` at offset 0x10, `TargetUri` at 0x20.
Cannot tell pin-vs-accept from stubbed bodies; needs disasm of a decrypted GA (older `recflare-client\
GameAssembly.dll`, 156 MB, is decrypted and framework-identical) OR — cheaper — an **empirical external
test**: on the GENUINE (Referee-happy) game, DNS-redirect ns.rec.net→recflare and watch Player.log for
whether TLS/host validation passes. If it connects, the whole Referee fight is unnecessary.

**Referee-proxy vector is DEFINITIVELY dead — matches DUMPING.md line 42** ("swapping Referee.dll for a
stub that exports jjiEVn [is] rejected"). Confirmed 3 ways: plain forwarder proxy, abort-defang, and
**PEB-loader-unlink stealth** (referee_stealth.c — successfully unlinked our module from all 3 loader
lists, still __fastfail'd at +0x69839d/+0x26f3179 ~4s after DllMain). The same +0x69839d convergence
also fires on a *pristine external read*, so Referee's tamper detection is multi-signal and not evadable
by hiding one signal. Its check gate fn `Referee+0x611580` is Themida byte-mutation/opaque-predicate
(stack-built constants) — static "always-pass" patching is a dead end. Defeating Referee for in-process
delivery would require dynamic RE (x64dbg+ScyllaHide; plan at tools/REFEREE_TRACE_PLAN.md) against a
Themida-VM anti-cheat that also fights debuggers. A pre-2-Dec-2025 build has no Referee at all and makes
the same two-hook redirect trivial (re-roll RVAs from that build's dir under RecRoom_Info/Code).
