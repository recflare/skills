# AI realtime session create wire shape

> Wire shape of POST realtime-session/create on the AI service (svc 0) for recflare-2025 — 6-key body in, ENVELOPED {Value:{SessionId, ClientSecret}} out.

Derived **2026-08-20** from `C:\Games\recflare-2025` (build `20250718.01`) via
[recflare-2025-metadata-carve](../../../il2cpp-analysis/references/recflare-2025-metadata-carve.md).

`POST https://ai.<host>/realtime-session/create` — **POST** (`HttpMethod` statics `+0x20`), service
**0 = AI** (`xor r8d, r8d`), JSON body via `ELKIBCPINAP`, no query params. Client entry
`HMLMLNGIOHL(string aiType, string model, string instructions, VoiceOption voice,
string? transcriptionModel, float temperature, CancellationToken)` (`0x7C79200`), state machine
`BIJEGBCNBIP$$MoveNext` (`0x7C77E00`).

**Request** `NLPKOFKABKA` (formatter `MEGNLNKFEMM` ctor `0x7718E70`), 6 keys — `AIType` string 0x10,
`Model` string 0x18, `Instructions` string 0x20, `Voice` string 0x28, `TranscriptionModel`
string 0x30, `Temperature` float 0x38.

**`Voice` is a lowercased enum name on the wire**, not a number and not PascalCase: the state machine
calls `System.Enum.ToString()` then `String.ToLowerInvariant()`. `VoiceOption` = None -1, Coach 0,
Alloy 1, Ash 2, Ballad 3, Coral 4, Echo 5, Sage 6, Shimmer 7, Verse 8 → `"none"`, `"coach"`,
`"alloy"`, … Only `alloy` and `coral` exist as literals (defaults); the rest are produced at runtime,
so grepping the literal table for them finds nothing.

Model values present as literals: `gpt-4o-realtime-preview`, `gpt-4o-realtime-preview-2024-12-17`,
`gpt-4o-mini-realtime-preview`, `gpt-4o-mini-realtime-preview-2024-12-17`.

**Response IS enveloped** — the awaiter is `TaskAwaiter<KGOJLHJNIOD<NJJCKMNKLHJ>>`, so the wire body
is the single-value envelope (see [outfits-me-put-wire-shape](outfits-me-put-wire-shape.md) for the tiers):

```json
{ "Value": { "SessionId": "...", "ClientSecret": "..." },
  "Success": true, "Error": null, "error_id": null }
```

`NJJCKMNKLHJ` (formatter `OEBFMIODMGH` ctor `0x7703F10`) is only `SessionId` string 0x10 and
`ClientSecret` string 0x18. The method then maps that to a client-side `BFOBFLKGLKA` — that type is
**not** the wire shape.

**Why:** `ClientSecret` is the OpenAI ephemeral key — the client then dials
`wss://api.openai.com/v1/realtime?model=` directly. And `SessionId` must match what the realtime
channel later reports, or the client logs *"Initial session creation returned a different ID than is
being received from the realtime channel"*.

**How to apply:** sibling endpoint is `realtime-session/logs`. A websocket variant is gated behind the
`use_websocket_realtime_session` / `ai_2025q2_websocket_realtime_session` flags.
