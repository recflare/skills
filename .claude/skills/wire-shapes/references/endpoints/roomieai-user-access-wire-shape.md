# Roomieai user access wire shape

> Wire shape of GET roomieai/user/access on the AI service (svc 0) for recflare-2025 — ENVELOPED {Value:{MaxEnergyFromSubscriptions, EnergyLeft, OutputAudioEnabled}}.

Derived **2026-08-20** from `C:\Games\recflare-2025` (build `20250718.01`) via
[recflare-2025-metadata-carve](../../../il2cpp-analysis/references/recflare-2025-metadata-carve.md).

`GET https://ai.<host>/roomieai/user/access` — **GET** (`HttpMethod` statics `+0x08`), service
**0 = AI** (`xor r8d, r8d`), **no query params, no body**. Client entry
`KAJEHHLMOLL(bool forceRefreshCache = false, CancellationToken)` at `0x7C79D70`, state machine
`EDGACLONGNF$$MoveNext` (`0x7C7DD60`).

**`forceRefreshCache` is client-side only** — it never reaches the wire. The state machine has no
`ELKIBCPINAP` and no query-param closure; the flag only bypasses a local cache (the request also
carries an `NNMGBLLLIAH` cache/timeout config, same type as `settings/partyinvite`). A stale value
you return can therefore stick around until something forces a refresh.

**Response is enveloped** — awaiter is `TaskAwaiter<KGOJLHJNIOD<OENAFGIDDAM>>`:

```json
{ "Value": { "MaxEnergyFromSubscriptions": 1000, "EnergyLeft": 950, "OutputAudioEnabled": true },
  "Success": true, "Error": null, "error_id": null }
```

`OENAFGIDDAM` (formatter `OFEMINOCAMK` ctor `0x771B270`), 3 keys: `MaxEnergyFromSubscriptions`
long 0x10, `EnergyLeft` long 0x18, `OutputAudioEnabled` bool 0x20. `CPOBHIECLEN` is the `0xA60520`
no-op — no validation.

**Why:** this is Roomie AI's budget gate. `EnergyLeft` drives the "out of credit" UI
(`RoomieAI.Credits.LimitReachedLabel`, `RoomieAI.Credits.NoSubscription`,
`AI.InsufficientRoomieAICredit`), and `roomieai/session/spend` is the debit side. It ties into econ:
`RoomieCredits` is currency 500 and `RoomieEnergyPack` is BalanceType 1101 in
[econ-bulkpurchase-wire-shape](econ-bulkpurchase-wire-shape.md). `OutputAudioEnabled` gates Roomie's voice output
(`RoomieAI.DisablingOutputAudioNotificationPrompt`).

**How to apply:** contrast [roomieai-user-facts-wire-shape](roomieai-user-facts-wire-shape.md) — same service, **bare** response. Read
the envelope off each state machine's awaiter; it is not consistent per service.
