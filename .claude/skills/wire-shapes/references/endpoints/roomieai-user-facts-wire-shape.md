# Roomieai user facts wire shape

> Wire shape of GET roomieai/user/facts on the AI service (svc 0) for recflare-2025 — a bare {UserFacts:[{Id,Predicate,Object,Emotion,CreatedAt}], UserContext}.

Derived **2026-08-20** from `C:\Games\recflare-2025` (build `20250718.01`) via
[recflare-2025-metadata-carve](../../../il2cpp-analysis/references/recflare-2025-metadata-carve.md).

`GET https://ai.<host>/roomieai/user/facts` — **GET** (`HttpMethod` statics `+0x08`), service
**0 = AI** (`xor r8d, r8d`), **no query params and no body** (the method takes only a
`CancellationToken`, and the state machine has no `ELKIBCPINAP` and no param closure). Client entry
`KLCIJGPHMJE(CancellationToken)` at `0x7C7A070`, state machine `MCDOINNFICG$$MoveNext` (`0x7C902A0`).

**Bare object, no envelope** — the awaiter is `TaskAwaiter<JPLLGHHHFIE>` directly. Contrast
[ai-realtime-session-create-wire-shape](ai-realtime-session-create-wire-shape.md) on the same service, whose awaiter *is*
`KGOJLHJNIOD<T>`; envelope use is per-endpoint even within one service.

`JPLLGHHHFIE` (formatter `MHLEMMANJJI` ctor `0x77199D0`), 2 keys:

- `UserFacts` — `List<ELLDOKHIDOP>` 0x10
- `UserContext` — string 0x18

Each fact `ELLDOKHIDOP` (formatter `JEPHHLDNCCO` ctor `0x7715970`), 5 keys — `Id` string 0x10,
`Predicate` string 0x18, `Object` string 0x20, `Emotion` string 0x28, `CreatedAt` DateTime 0x30.

Both `CPOBHIECLEN` hooks are the shared `0xA60520` no-op — no validation, and
`{"UserFacts":[],"UserContext":""}` is a safe empty response.

**Why:** it is a subject-predicate-object triple store with the subject implied (the user), plus an
`Emotion` tag and a free-text `UserContext` blob. The client folds these into the assistant's system
instructions — see the config keys `RoomieAI.IncludeUserKnowledgeInInstructions` and
`RoomieAI.UserKnowledgeUpdateInterval`, which gate and pace that injection.

**How to apply:** siblings on the same service are `roomieai/user/access`,
`roomieai/user/processconversation` (the writer that mines facts out of a conversation),
`roomieai/chat`, `roomieai/describeimage`, `roomieai/describeimagefile`, `roomieai/session/spend`.
