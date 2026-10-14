# Rooms boosts count wire shapes (2026 build only)

> `GET rooms/{roomId}/boosts/{accountId}/count` returns a **BARE JSON INTEGER** — no object, no
> envelope. Its two siblings are `rooms/{roomId}/boosts/count` (also a bare `int`) and
> `rooms/{roomId}/boosts/counts` (a bare **`Dictionary<int,int>`**, i.e. a JSON object of
> accountId → count).
> ⚠️ **These routes do not exist in `20250718.01`** — Room Boosts is a 2026 feature. Derived against
> build **20260323.14**.

Derived **2026-10-13** from build `20260323.14` via the 2026 carve
([[recflare-2026-static-index]] → `C:\Games\recnet-patcher\il2cpp-2026\`). Everything else in this
catalog is 20250718.01 unless it says otherwise.

`GET https://rooms.<host>/rooms/{roomId}/boosts/{accountId}/count` — verb **GET**
(`HttpMethod` statics `[rcx+8]` at `0x95BD7C5`). Path is
`String.Format("rooms/{0}/boosts/{1}/count", roomId, accountId)`, whole-path template literal
**`0xFD63B40`**.

## Response — a bare integer

```json
3
```

Send is **`RecNet.Rooms.DFMBMRNABHU::Get<T>`** (methodref `0x95BD822`) with generic inst
**#86 = `int`**. The state machine's `AsyncTaskMethodBuilder<1>` is **also** inst #86, i.e. the
facade returns `Task<int>` and the awaited send returns `int` — **the same `T` on both sides, so
nothing is being unwrapped and there is no envelope.** (Compare the Studio API, where the builder is
`T` but the awaiter is `Result<T>`; that mismatch is what reveals a wrapper. See
[studio-cloud-builds](studio-cloud-builds-wire-shapes.md).)

⚠️ **Not an object.** `{}` or `{"count": 3}` throws the 2026 equivalent of `IONCMJIACFI` —
`Malformed Response: '…'` from `RecNet.RGBOOBRDHEB.AIYNPFIEYFY<T>`.

⚠️ **Not `null`.** `T` is plain `Int32`, so the formatter has no null path; return **`0`** for "no
boosts". Same rule as the 2025 influencer lookups
([influencerpartnerprogram](influencerpartnerprogram-wire-shape.md)) and the same failure as
[number-token-parsing-exception](../conventions/number-token-parsing-exception.md).

## The three routes

| route | state machine | wire `T` |
|---|---|---|
| `rooms/{roomId}/boosts/{accountId}/count` | `<GetPlayerActiveRoomBoostCount>d__42` `0x95BD6B0` (+0x2E0) | **`int`** |
| `rooms/{roomId}/boosts/count` | `<GetActiveRoomBoostCount>d__41` `0x95BB290` (+0x290) | **`int`** |
| `rooms/{roomId}/boosts/counts` | `<GetBoostCountsForPlayers>d__43` `0x95BC720` (+0x490) | **`Dictionary<int,int>`** (inst #2869) |

All three are **GET** on the Rooms service through `DFMBMRNABHU::Get<T>`, all bare.

`boosts/counts` carries **no query-param literals at all** — just the room id in the path — so it is
"every player in the room", not a filtered bulk lookup. A `Dictionary<int,int>` serializes as a JSON
object with the account id as the **key**, and System.Text-style int keys are written as strings:

```json
{ "205": 3, "220": 1 }
```

`rooms/{roomId}/boosts/count` is the room-wide total; `.../{accountId}/count` is one player's
contribution.

## ⚠️ `BoostCount` is a real Room DTO key in 2026 but not in 2025

`RecNet.Rooms.RoomDTO` has `get_BoostCount` / `set_BoostCount` (`0x1901B60` / `0x1901C20`) on the
2026 build. The **2025** Room DTO (`.HGMJJMJDHLJ`, 63 keys) has **no** `BoostCount` — which is why a
server that emits it is silently ignored by the 2025 client
([rooms-room-by-id](rooms-room-by-id-wire-shape.md) lists it among the dropped keys). If the same server feeds both
builds, emit it: 2026 reads it, 2025 drops it harmlessly.

Related 2026 surface, not derived here: `api/purchasableXpBoosts`,
`api/purchasableXpBoosts/activations`, `{0}/{1}/xpboosts`,
`{0}/{1}/xpboosts/{2}/previewEarnedXp` (the last two also exist in 2025), the gate
`RoomBoosts.Enabled` / `RecNet.RoomBoosts.RoomBoostEnabledConfig`, and the pushes
`RoomBoostNotificationDTO` `{RoomId, GlobalBoostCount}` and `RoomBoostConsumedNotificationDTO`
`{RoomId, AccountId, RequestId}`.

## Method note: 2026 leaks async method names

The declaring class's methods **are** obfuscated — a metadata scan for a method literally named
`GetPlayerActiveRoomBoostCount` finds nothing. But the compiler-generated state-machine type keeps
the original name as `<GetPlayerActiveRoomBoostCount>d__42`, so **`mxref` on a route literal lands
you on a nested type whose name tells you what the route does**. That is the cheapest naming signal
on this build; use it before trying to identify the facade method.
