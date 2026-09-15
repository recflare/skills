# Serialized request queue stall

> The 2025 client serializes ALL HTTP through one FIFO queue; a retrying telemetry POST holds it ~25s and pushes the room-save blob past its 30s timeout. Blocking dead hosts makes this WORSE, not better.

`CBACIMLIBPF` (RecNet's System.Net.Http client) dispatches **every** request through a single
serial queue, in three stages:

| RVA | Method | Stage |
|---|---|---|
| `0x7CC4F20` / `0x7CC50D0` | `IBJKIAMJCDN(...)` | enqueue |
| `0x7CC6EA0` | `KOMEOKGFOBP(Queue, ct)` | pump (drains it) |
| `0x7CC29E0` | `CJOCHJBHGPM(uint seq, method, svc, path, ...)` | one actual send |

Only after `CJOCHJBHGPM` does it become a BestHTTP request. The `uint` first arg is a **global
monotonic sequence number**, not a retry count — proof the queue is serial.

**The failure:** the room-save blob is ~#101 in line. On 2026-08-17 it was enqueued at
`17:06:53.111` and not sent until `17:07:29.751` — **36.6s** — while `FetchRoomLoadDetails >
getRoomSaveData` times out at **30s**. Result: "Downloading" bar, `room_load_state
DOWNLOADING_DETAILS`, `Error downloading save data!`, `Unable to send message!`. Of that 36.6s,
**24.68s was ONE request**: `seq=66 svc=19 data/event` (DataCollection analytics) retrying three
times with backoff (~5.5s, ~13.7s) against a host that fails.

**⚠️ Blocking dead hosts makes this WORSE.** The intuition "NXDOMAIN fails in ms so blocking is
free" is wrong: the cost is the **retry backoff**, not the lookup, and the retries occupy the one
queue the blob is behind. `datacollection.recflare.net` must **succeed instantly** (200/204 stub) —
blocked and NXDOMAIN are equally bad. Fix the server stub FIRST, then unblock; unblocking without a
stub just restores NXDOMAIN. Purely external hosts (rudderstack, backtrace, statsig,
cloud.unity3d.com) are NOT on this queue, so blocking those stays correct.

**This also explains the "it worked, then I broke it" history:** it was always a race against the
30s timeout. Success/failure was jitter either side of the boundary — not a regression from any
config change. Don't hunt for what "changed".

**CONFIRMED FIXED 2026-08-17.** Stubbing `datacollection.recflare.net` `/data/event` (POST) and
`/sampling` (GET) to return instant 200s, then removing it from `kDeadHosts`, took the RoomLoad slice
from **120.5s (best case) / 30s-timeout failure** down to **5.1s** with zero failure markers. The
queue stalls were also most of the "dorm loads are very slow" complaint, not just the timeout.

Diagnostic hooks live in `recnet-plugin-unstable` as `[Pump]` / `[Send]` log lines (diagnostic only,
removable; low volume -- 9 and 107 lines in a full session). See [recflare-2025-working-client](recflare-2025-working-client.md) and [image-content-signature-bypass](image-content-signature-bypass.md) — the image
bug was a genuine hard stall of this same pump; this one is pure latency, so don't conflate them.

**Why:** three separate sessions were lost to "the blob is never dispatched", because every log
ended before the late send landed. It was always sent, just too late.

**How to apply:** before concluding a request was never made, confirm the log covers enough
wall-clock after it. To find what starves the queue, diff consecutive `[Send]` timestamps and look
for the single largest gap — that names the blocking request directly.
