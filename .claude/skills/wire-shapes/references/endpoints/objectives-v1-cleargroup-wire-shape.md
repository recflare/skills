# `POST api/objectives/v1/cleargroup` wire shape (2026 build)

> Returns a **SINGLE bare `ObjectiveGroupProgress` object** — 3 keys
> `{Group, IsCompleted, ClearedAt}`. **Not an array.**
> ⚠️ `[]` throws `Malformed Response: '[]'` and the feature logs
> `[RecNet.Features.Objectives] Error on server call: … Local objective state will not be reflected in server!`
> Request body is a JSON `ObjectiveGroupRequest`.

Derived **2026-10-13** from build `20260323.14`, against a live capture in which the server answered
`[]` and the client threw. The formatter was **named directly in the formatted async trace** —
`Utf8Json.Formatters.RecNet.VGCBANXFZSJ.Deserialize` — which is the fastest identification route
there is; see [2026-send-helper-tiers](../conventions/2026-send-helper-tiers.md).

Route literal `0xFC590C0`, facade
**`RecNet.Objectives.CFDJUWYXMPC(int group) -> MPVTAJGPRUT<ObjectiveGroupProgress>`** `0x951CE50`
(+0x400).

- Response send: `RGBOOBRDHEB::ZWUODKCINOA<T>` with generic inst **#18221 =
  `RecNet.ObjectiveGroupProgress`** — a single object, **bare**, no envelope.
- Request body: `RGBOOBRDHEB::FZNGWUAGAIN<T>` with generic inst **#23242 =
  `.ObjectiveGroupRequest`** — so this is a **JSON body**, not form-urlencoded.

## Response — `ObjectiveGroupProgress`, 3 keys

Formatter `Utf8Json.Formatters.RecNet.VGCBANXFZSJ` `.ctor` **`0x9654C70`** (+0x2B0):

| # | key | CLR |
|---|---|---|
| 1 | `Group` | `int` |
| 2 | `IsCompleted` | bool |
| 3 | `ClearedAt` | `DateTime` |

```json
{ "Group": 3, "IsCompleted": true, "ClearedAt": "2026-10-13T09:14:57Z" }
```

⚠️ **The DTO has a fourth field with no wire key:** `RequiresCompleteOnServer` (bool). It is
client-side only — emitting it is silently dropped, and the client cannot be told to set it.

⚠️ `ClearedAt` is a non-nullable `DateTime`, and `Group`/`IsCompleted` are non-nullable — a JSON
`null` on any of them throws. Omit the key instead (`ClearedAt` then reads as
`0001-01-01T00:00:00`).

Echoing back the `Group` that was requested, with `IsCompleted: true` and `ClearedAt` = now, is the
natural implementation.

## The sibling routes

`api/objectives/v1/completegroup`, `api/objectives/v1/myprogress`,
`api/objectives/v1/updateobjective` — **not derived**. `myprogress` is the likely place a *list* of
`ObjectiveGroupProgress` belongs, which is probably where the `[]` was meant to go; check its `T`
before reusing this shape.

Observed in the same capture: `POST /api/objectives/v1/cleargroup` returned `[]` and
`[RecNet.Features.Objectives] Error on server call: An error occurred. Local objective state will
not be reflected in server!` followed ~0.1 s later. That feature-level message is the cheapest
signal that an objectives route has a wrong shape — it is logged by the subsystem rather than by the
generic sender, so it names itself.
