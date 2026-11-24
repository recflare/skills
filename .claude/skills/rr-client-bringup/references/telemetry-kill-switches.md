# Telemetry kill switches

> How to switch off each third-party telemetry sink in recflare-2025: DataCollection.Enabled gate (data/event), Backtrace via missing server config or Backtrace.SampleRate, Statsig via an empty key (falls back to defaults). Statsig/Backtrace/Rudderstack URLs are HARDCODED to third-party hosts.

Derived **2026-08-27** from build `20250718.01` via [recflare-2025-metadata-carve](../../il2cpp-analysis/references/recflare-2025-metadata-carve.md).

## DataCollection (`data/event`, `data/events`) — CONFIRMED WORKING

Gate config **`DataCollection.Enabled`** (bool, **default `true`** — `mov r9b, 1` at `0x7612A55`),
read in the `LogAsync` path `DHBGIMFKGOM$$MoveNext` `0x76128E0` **before**
`ODDMMEODFGD.APMHOCBKNCH` `0x7E1B4C0` builds the request. Setting it false stops the HTTP call
entirely. Confirmed fixed by the user 2026-08-27; it was the endpoint behind
[serialized-request-queue-stall](serialized-request-queue-stall.md).

Both routes are svc **19 DataCollection**, POST, `CNDMDLNHDLI` (SendWithNoResponse) — body never
read, any 2xx works. `data/event` body is `{EventType, EventParams}` (both **strings**;
`EventParams` is escaped JSON). `data/events` is the batched multipart form (`file.bin`).

### 2026 build `20260323.14` — STILL `DataCollection.Enabled`, re-derived

Re-confirmed on build `20260323.14` (RVAs/obfuscated names re-rolled, mechanism identical). The
general event front door is `RecNet.Data.WILHGNSYVUU$$Event(string eventType[, int accountId])`
(`0x8D7CA00` / `0x8D7CFF0`); its terminal `<LogAsync>d__9$$MoveNext` `0x8D7AF10` reads game config
**`DataCollection.Enabled`** (literal `0xFD759D0`, **default `true`** — `mov r9b, 1`) and, when
false, **early-exits at `0x8D7B09B` (`test al,al; jne; jmp 0x8D7B157`) BEFORE** calling the pipeline
enqueue `RecNet.Data.FRNWCURICAL$$LYWKAPLYCNM` `0x95CB7A0`. So setting it false stops both
`data/event` (`<SendEvent>d__16` `0x95DE0F0`) and `data/events` (`<FlushCurrentBatch>d__23`
`0x95D6320`) at the source — no enqueue, no batch, no POST. `data/event` on 2026 is svc **19**
(`mov r8d,0x13`), JSON body via `FZNGWUAGAIN`, sent with the **no-response** helper
`RGBOOBRDHEB$$JEYAQXBXMRA` (`0x95DE3D6`) — response still ignored, so a returned body cannot signal
"disable"; the flag or the push below is the only client-side off switch.

> ⚠️ **Do not confuse with the AI collectors.** On 2026 the same `DataCollection.Enabled` key is
> *also* read by `RecNet.Data.WILHGNSYVUU$$ZOJHPRXFKVH` `0x8D7D410`, a bool getter whose only callers
> are MakerAI/RoomieAI/GameAI (`MakerAISystem..ctor`, `RoomieAIController`, …). Xref'ing *that getter*
> alone makes the flag look AI-only — it is not; the general path reads the flag directly in
> `<LogAsync>d__9`. Siblings `GameAI.DataCollection.Enabled`, `MakerAI.DataCollection.Enabled`,
> `RoomieAI.DataCollection.Enabled` are the per-AI-subsystem gates.

**Config delivery:** these keys are game configs served by **`GET api/gameconfigs/v1/all`** (the
`RecNet.LGHEBYOBKGV` / `GameConfigAccessRecord` store, `GameConfigs.RefreshAsync`), so the self-hosted
server sets them. The `Analytics.UseDataCollection` game config (read in `.REBSZBYFAIW$$OGXEZNPSKVL`
`0xD68220`) is the upstream analytics-routing switch. Per-event-type runtime kill switch is still the
websocket push **`DataCollectionEventDisabled`**: `RecNet.Data.FRNWCURICAL` subscribes at
`Initialize` `0x95CB5D0` (handler `QWBDSRMMMFF(.EventDTO)` `0x95CBA40`). Batch-cadence throttles
`DataCollection.MaxBatchSize` / `.MaxBatchDelaySeconds` are read in `GBAGBPAPVKT` `0x95CB220`.

Per-event-type kill switch: websocket channel **`DataCollectionEventDisabled`**, payload
`{EventType, ShouldBeSampled}` (formatter `DLAHGGAKEDE` `0x77205E0`), handler
`ODDMMEODFGD.FACPGDPODIL` `0x7E1BA50` ([notification-types-2025](../../wire-shapes/references/endpoints/notification-types-2025.md)).

Throttle instead of disable: `DataCollection.MaxBatchSize`, `.MaxBatchDelaySeconds`,
`.HeartbeatIntervalSeconds`, `.UseHeartbeatCoroutineDelays`, `.OneTimeData.Enabled`,
`.PerfMetrics.IntervalSeconds` / `.ExtraDataEnabled` / `.HitchThresholdOffset` /
`.FilteredTimeStats` / `.UseCoroutineDelays`, `.FilteredTimeFlags`, `.FilteredTimeStats`,
`.SkipPerfStatsFor`, `.LogFriendIdsWithSocialHeartbeat`.

## Backtrace (`submit.backtrace.io`)

Submit URL is **hardcoded** at `0x17E83B8`:
`https://submit.backtrace.io/recroom/<token>/json`. Not served by you.

`RecRoom.Core.BacktraceManager.ONGGDPGJLLF` `0x17EC0A0` has two clean off-ramps:

```
rbx = serverConfig[+0x48]
if (IsNullOrEmpty(rbx)) -> 0x17EC988   "Missing backtrace server config. Not initializing"
Regex.IsMatch(appVersion, rbx) == false ->  "Backtrace disabled for this game version"
```

So: **omit the backtrace server config**, or supply a version regex that does not match the build.
Gate configs read in `AKPIIMKJAIK$$MoveNext` `0x17E82B0`: **`Backtrace.SampleRate`**,
`Backtrace.ReportBudget`, `Backtrace.Deobfuscate`, `Backtrace.DeobfuscationUrl`,
`Backtrace.deobfuscationRate`. SampleRate 0 is the least invasive switch.

⚠️ The same method also holds the **Rudderstack** sink
`https://recroom-dataplane.rudderstack.com/v1/webhook?writeKey=...` — a third hardcoded destination.

## Statsig (`statsigapi.net`)

Base URL **hardcoded** in `JMNFDLFEBGD$$.cctor` `0x8E9E310`: `https://statsigapi.net/v1`.
Key sent as header **`STATSIG-API-KEY`** (`FCALOGKIBDI$$MoveNext` `0x8E9BAD0`).

**There is no "Statsig.Enabled" gate** — but every read degrades gracefully:
`'Statsig not ready for gate: '`, `'... for experiment: '`, `'... for layer: '`,
`'StatSig must be initialized before being used'`,
`'Timed out waiting for statsig to be ready for Jump Right In new layout, using default.'`,
`'Invalid key provided. Please check your Statsig console to get the right server key.'`

So an **empty/invalid key, or an unreachable statsigapi.net, makes every gate/experiment/layer fall
back to its client default** — which is the effective off switch. Prefer a fast rejection over a
black-hole drop (a hang costs the init timeout;
`engagementTitlescreenJumpRightInStatsigTimeout` is one such knob).

Statsig values seen in this build: layers `avatars_experiment_layer` (param `default_tab_name`),
`econ_store_layer`, `avatars_experiment_layer`; configs `cai_default_ordering`,
`CAI_search_includes_coach_items`, `extra_purchasable_item_ids_in_default_search`,
`experience_q1_always_open_last_notification`, `open_last_message_on_watch_open`,
`Discovery.Statsig.TitleScreenExperimentMode`.
