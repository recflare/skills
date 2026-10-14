# `POST player/verifylock` — there is no response shape (2026 build only)

> **The response body is never read.** `POST match.<host>/player/verifylock` is sent with the **raw**
> response helper, so no `T` is involved, no formatter runs, and nothing deserializes. The client
> inspects exactly one thing: the **HTTP status code**.
> **`409 Conflict` ⇒ the client force-logs-out** with the reason string `Conflict (409)`.
> **Every other status — including 200, 204, 400, 404 and 500 — means "lock is valid, do nothing."**
> Recommended: `204 No Content` when the lock is good, `409` when it is stale.
> ⚠️ **2026 build `20260323.14` only** — `player/verifylock` does not exist in `20250718.01`.

Derived **2026-10-13** from build `20260323.14` via the 2026 carve
([[recflare-2026-static-index]] → `C:\Games\recnet-patcher\il2cpp-2026\`). Everything else in this
catalog is 20250718.01 unless it says otherwise.

Route literal `0xFC23920`. Service **4 Matchmaking** (`mov r8d, 4` at `0x950F0B9`), hence
`match.<host>`. Verb **POST** — `[HttpMethod statics + 0x20]` = `post_method`, read at `0x950F09A`.

## When it fires

Entry point `<<OnNotificationsConnected>g__VerifyMatchLockTokenOrLogOutAsync|173_0>d$$MoveNext`
**`0x950EF50`** — a C# *local function* inside the notifications-connected handler, which is why the
original name survived obfuscation in full. It runs **every time the notification websocket
connects or reconnects**, not on a timer and not during room join.

That makes it easy to misread in a capture: a burst of `verifylock` calls means the notification
socket is flapping, not that matchmaking is retrying.

## The request

This route does **not** go through a typed service facade. The state machine builds a raw
`RecNet.RGBOOBRDHEB` and adds one parameter:

```csharp
var req = new RGBOOBRDHEB(HttpMethod.Post, Service.Matchmaking /*4*/, "player/verifylock");
req.NJPEKLKCVCG("LoginLock", RecNet.Matchmaking.JYFTEOAXDLG /*statics +0xC0, string*/, false, false);
using (var response = await req.NJDMOZYSDOQ(ct))
    RecNet.Matchmaking.WJITRSFCKUU(response);
```

`NJPEKLKCVCG` is 2026's `ELHKHFJEHLM` and is **verb-dependent** — see
[elhkhfjehlm-verb-dependent-params](../conventions/elhkhfjehlm-verb-dependent-params.md). This route is POST, so the single
parameter arrives as an **`application/x-www-form-urlencoded` body**:

```
LoginLock=<the token this client was issued at login>
```

**Not** a query string, **not** a JSON body.

`RecNet.Matchmaking.JYFTEOAXDLG` (statics `+0xC0`) is the client's cached login-lock token. The same
value is stamped into the matchmaking request DTOs as a key named `LoginLock` — all three casings
(`LoginLock` / `loginLock` / `loginlock`) are `____keyMapping` literals on
`RecNet.GoToRoomRequestDTO` (`ILQQDVMAYOA`), `RecNet.GoToRoomListRequestDTO` (`CFRGDFUVTRG`) and
`RecNet.GoToSubRoomRequestDTO` (`IUZZNPWNOTK`). So whatever a server issues as `LoginLock` on login
is what comes back both here and on every go-to-room call.

## Why there is no response shape

The send is **`RGBOOBRDHEB::NJDMOZYSDOQ(CancellationToken) -> Task<RecNet.XJAFUXFVGPU>`** — the
**raw** response helper, not the generic `ZWUODKCINOA<T>` / `LIRIDCJIGGA<T>` deserializing pair. The
awaiter's generic inst (#3260) is `RecNet.XJAFUXFVGPU` itself, i.e. the HTTP response wrapper:

```
RecNet.XJAFUXFVGPU..ctor(int statusCode, string, DisposableMemorySequence<byte> data,
                         string, string, bool, bool, HTTPCacheFileInfo cacheFileInfo)
```

Its first field (`+0x10`) is the status code. Nothing in this path ever asks for a formatter.

⚠️ **This is the tell for "body ignored" on 2026**, and it is a *different* tell from 2025's
`CNDMDLNHDLI`: look for the send helper returning `Task<XJAFUXFVGPU>` instead of `Task<T>`. A route
whose facade returns `Task<T>` always deserializes; a route that awaits `XJAFUXFVGPU` never does.

## The whole decision — `RecNet.Matchmaking.WJITRSFCKUU`

`static void WJITRSFCKUU(RecNet.XJAFUXFVGPU response)` **`0x94FFDA0`** (+0x120):

```csharp
if (response == null) return;                          // 0x94FFE01
if (response.StatusCode != 409) return;                // 0x94FFE0A: cmp dword [rbx+0x10], 0x199
                                                       //            jne -> plain ret
RecNet.Core.<forcedLogoutEvent @ statics+0x88>.Invoke("Conflict (409)");   // 0x94FFE54
var svc = DI.Get<RecNet.RZONXTZOIGY>();                // 0x94FFE70 / 0x94FFE86
svc.<...>();                                           // 0x94FFEA1, tail jump — the logout
```

`0x199` is **409** decimal, and `'Conflict (409)'` (literal, `0x94FFDEE`) is the reason string handed
to the logout event. That is the entire body of the method — there is no other branch, no retry, no
backoff, and no second status it reacts to.

### What a server should return

| status | client behaviour |
|---|---|
| **409 Conflict** | **Force logout**, reason `Conflict (409)`. This is the only way to kick a client from here. |
| 204 / 200 | nothing — lock accepted. **Recommended for the happy path.** |
| 400 / 401 / 500 | nothing — treated identically to success |
| **404** | **nothing** — an unimplemented route is silently "lock valid" |

⚠️ **404 is harmless here, which is the opposite of the usual situation.** If `verifylock` is one of
the routes in your 404 pile ([cv1-mappings-join-nre-2026](../../../rr-client-bringup/references/cv1-mappings-join-nre-2026.md) counts 46 in one
session), it is *not* contributing to the join failure — a 404 on this route cannot log anyone out.
Conversely, do **not** return 409 as a generic error: any 409 from this endpoint, for any reason,
ends the player's session.

A body of any kind is ignored, so returning one is harmless but pointless. The body on a 409 is
ignored too — the reason string the user eventually sees is the hardcoded `Conflict (409)`, not
anything the server supplies.
