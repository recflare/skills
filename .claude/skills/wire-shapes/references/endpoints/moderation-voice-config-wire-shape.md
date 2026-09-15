# Moderation voice config wire shape

> Wire shape of GET voice/config on the Moderation service (svc 18) for recflare-2025 — a bare {AccountId, ApiKey}, both STRINGS; these are the ToxMod credentials.

Derived **2026-08-20** from `C:\Games\recflare-2025` (build `20250718.01`) via
[recflare-2025-metadata-carve](../../../il2cpp-analysis/references/recflare-2025-metadata-carve.md).

`GET https://moderation.<host>/voice/config` — **GET** (`HttpMethod` statics `+0x08`), service
**18 = Moderation** (`mov r8d, 0x12`), no query params, no body. Client entry
`PHAEJFAEGAF.PGOHHEJLAAB()` at `0x7C96B90`, non-async; failure logs
**"Failed to download ToxMod configuration"**.

Response is a **bare object**, `PHAEJFAEGAF.KKKEGFJHGBO` (formatter `KIDABFDNBJD` ctor `0x76B30F0`),
exactly two keys:

```json
{ "AccountId": "12345", "ApiKey": "..." }
```

`AccountId` string 0x10, `ApiKey` string 0x18. **`AccountId` is a STRING, not a number** — the
obvious mistake is emitting the numeric account id. `CPOBHIECLEN` is the `0xA60520` no-op, so no
validation; the continuation just caches both onto a static.

**Why:** these are the **ToxMod** (voice moderation) credentials the client uses to talk to ToxMod
directly. Related: `ToxmodEnabled` on the room DTO ([rooms-contributedby-wire-shape](rooms-contributedby-wire-shape.md)), the sibling
`voice/requiresModeration`, and the AI-moderation endpoints `aimoderation/roomie/conversation` and
`aimoderation/roomie/enabledForPlayer`.

**How to apply:** if you are not running ToxMod, returning `{"AccountId":"","ApiKey":""}` is
structurally valid — nothing validates it — but check what the caching consumer does with blanks
before assuming voice chat still works.
