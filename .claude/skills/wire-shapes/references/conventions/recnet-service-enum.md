# RecNet service enum

> The full RecNet service enum NNPMGHNBFMD for build 20250718.01 — 31 unobfuscated member names with values (Auth 1, API 2, Lists 13, Rooms 16, Econ 28 …); the number every wire-shape note calls 'svc N'.

Dumped **2026-08-24** from build `20250718.01` with `il2cpp-2025/enumvals.py`
(see [il2cpp-field-default-values-compressed](../../../il2cpp-analysis/references/il2cpp-field-default-values-compressed.md)). **Enum member names survive obfuscation**, so this
table is directly readable and should be re-dumped rather than re-derived on a new build.

`MGPBDIAGCFD..ctor(HttpMethod method, NNPMGHNBFMD service, string route)` — the middle arg (`r8d` at
the `AKJEAMCCEOH$$.ctor` call site) is this enum:

| # | name | # | name | # | name |
|---|---|---|---|---|---|
| 0 | AI | 11 | Accounts | 22 | PlayerSettings |
| 1 | Auth | 12 | Link | 23 | Studio |
| 2 | API | 13 | Lists | 24 | GameLogs |
| 3 | Commerce | 14 | RoomComments | 25 | Strings |
| 4 | Matchmaking | 15 | Clubs | 26 | StringsCDN |
| 5 | Notifications | 16 | Rooms | 27 | WWW |
| 6 | Images | 17 | PlatformNotifications | 28 | Econ |
| 7 | CDN | 18 | Moderation | 29 | Data |
| 8 | Storage | 19 | DataCollection | 30 | Cards |
| 9 | Chat | 20 | BugReporting | | |
| 10 | Leaderboard | 21 | Discovery | | |

Cross-checks every earlier note: Matchmaking 4 ([matchmake-v2-room-wire-shape](../endpoints/matchmake-v2-room-wire-shape.md)), Chat 9
([chat-cansenddm-wire-shape](../endpoints/chat-cansenddm-wire-shape.md)), Lists 13 ([algorithmiclists-wire-shape](../endpoints/algorithmiclists-wire-shape.md)), Rooms 16
([rooms-experience-wire-shape](../endpoints/rooms-experience-wire-shape.md)), PlatformNotifications 17, Moderation 18
([moderation-voice-config-wire-shape](../endpoints/moderation-voice-config-wire-shape.md)), Econ 28 ([econ-bulkpurchase-wire-shape](../endpoints/econ-bulkpurchase-wire-shape.md)).

**Verb map** (`System.Net.Http.HttpMethod` static-field offsets, read as `[klass+0x90] + N`):
`0x00` Delete, `0x08` Get, `0x20` Post, `0x28` Put.

## Build `20260323.14`: identical for 0–29, plus `Cards = 30`

`py enumvals.py Service` on the 2026 build (`RecNet.Service`, typedef #46523) — the enum **kept its
real name and all member names** on this build, so it reads directly. Values **0–29 are unchanged**
from 20250718.08's `NNPMGHNBFMD`, and there is one addition:

```
Cards = 30
```

So every `svc N` in this catalog transfers to the 2026 client as-is. Two 2026 routes pinned by it:
`crm/me/config/v3` is **17 PlatformNotifications** (not a Chat or API service, despite the name) and
`sampling?sessionId=` is **19 DataCollection**.
