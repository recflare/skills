# Chat settings partyinvite wire shape

> Wire shape of GET settings/partyinvite on the Chat service (svc 9) for recflare-2025 — a bare single-key object {InviteLinkLifetimeInMinutes}.

Derived **2026-08-17** from `C:\Games\recflare-2025` (build `20250718.01`) via
[recflare-2025-metadata-carve](../../../il2cpp-analysis/references/recflare-2025-metadata-carve.md).

`GET https://chat.<host>/settings/partyinvite` — **GET**, service **9 = Chat** (`mov r8d, 9`),
no query params, no body. The client sets a custom request timeout on it
(`MGPBDIAGCFD.DIDJOECFJII(TimeSpan, bool)`).

Response is a **bare single-key object**, no envelope — `TResponse = PNBHBEADJPF` (confirmed via
the `HPBKMCLEANE` methodSpec inst 1306):

```json
{ "InviteLinkLifetimeInMinutes": 60 }
```

Formatter `MCDDMGEAGCG` ctor `0x7650050`; one member, `int` at 0x10. Casing variants
(`inviteLinkLifetimeInMinutes` / `invitelinklifetimeinminutes`) also accepted.
`PNBHBEADJPF.CPOBHIECLEN` is the `0xA60520` no-op.

Two client accessors share the path and **both are GETs — there is no write endpoint**:
`PNAHAINBHAH.MOPLCAKKFEE` (`0x7CBAB30`, raw fetch) and `PNAHAINBHAH.NBDAFCHJCGM` (`0x7CBAC90`, the
cached accessor that returns the plain int). The cache is a static seeded to **-1** and only
refetched while it equals -1; the fetch is wrapped in the catch-and-log helper with
"Failed to get party invite settings".

**A `null` body throws.** The continuation lambda `<>c.BBIJHDGNNGN` (`0x7CBCE00`) dereferences the
DTO unguarded — a JSON `null` (or empty body) hits the NullReferenceException helper, gets swallowed
by the catch-and-log, and leaves the cache at -1, so every party invite is then evaluated against
-1 minutes and reads as **expired**. Always return the object.

Consumer: `RRUI.Data.PartyInviteChatMessageModel.HasPartyInviteExpired` (`0x259E7C0`) converts the
int to a double and compares it against the invite's age in minutes — so the value is a plain
lifetime in minutes, and larger means invites live longer.

**Why:** a single-scalar settings endpoint is easy to mistake for a bare number (cf.
[chat-cansenddm-wire-shape](chat-cansenddm-wire-shape.md), which really *is* a bare integer on the same service). This one is
an object with one named key.
