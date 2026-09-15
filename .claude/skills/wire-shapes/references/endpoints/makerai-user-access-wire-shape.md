# Makerai user access wire shape

> Wire shape of GET makerai/user/access on the AI service (svc 0) for recflare-2025 — the VALUELESS envelope only, {Success, Error, error_id}, no Value.

Derived **2026-08-20** from `C:\Games\recflare-2025` (build `20250718.01`) via
[recflare-2025-metadata-carve](../../../il2cpp-analysis/references/recflare-2025-metadata-carve.md).

`GET https://ai.<host>/makerai/user/access?roomInstanceSpecificCheck={True|False}` — **GET**
(`HttpMethod` statics `+0x08`), service **0 = AI** (`xor r8d, r8d`), **no body**. Client entry
`HECBHOBDAGF(bool roomInstanceSpecificCheck, CancellationToken)`, state machine
`LFGAPAIDHAL$$MoveNext` (`0x7C83FB0`). The single query param is added via `ELHKHFJEHLM` as a boxed
bool, so it goes out as .NET `True`/`False` — parse case-insensitively.

**Response is the valueless envelope, nothing more** — the awaiter is
`TaskAwaiter<JFNAKFCGDAO>`:

```json
{ "Success": true, "Error": null, "error_id": null }
```

There is **no `Value` key**. Access is granted purely by `Success`. This is the sharpest contrast in
the AI service: [roomieai-user-access-wire-shape](roomieai-user-access-wire-shape.md) on the same service returns
`KGOJLHJNIOD<OENAFGIDDAM>` with `Value = {MaxEnergyFromSubscriptions, EnergyLeft,
OutputAudioEnabled}`, while MakerAI's access check carries no payload at all.

The method returns `Task<MPKGNLKJDEG>` (the envelope interface) to its caller rather than asserting,
so a `Success: false` is handled gracefully — it surfaces as "MakerAI Unavailable" / insufficient
credit UI rather than throwing [llcldppagij-envelope-failure-exception](../conventions/llcldppagij-envelope-failure-exception.md).

**Why:** MakerAI keeps its numbers in a **separate** sibling endpoint, `makerai/user/balances`;
Roomie bundles them into its access call. Related localization keys:
`AI.InsufficientMakerAICredit`, `AI.MakerAIUnavailable`, `AI.MakerAIDayPassSkuId`.

**How to apply:** other MakerAI endpoints on the same service are `makerai/user/balances`,
`makerai/image`, `makerai/rooms/search`, plus `api/makerai/activatefreetrial`,
`api/makerai/checkfreetrialeligibility`, `api/makerai/freetrialconfig` (those three are svc 2 API).
