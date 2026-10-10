# Rooms experience wire shape

> Wire shape of GET rooms/{id}/experience on the Rooms service (svc 16) for recflare-2025 — a bare two-key object {Enabled, DailyLimit}.

Derived **2026-08-18** from `C:\Games\recflare-2025` (build `20250718.01`) via
[recflare-2025-metadata-carve](../../../il2cpp-analysis/references/recflare-2025-metadata-carve.md).

`GET https://rooms.<host>/rooms/{roomId}/experience` — **GET**, service **16 = Rooms**
(`mov r8d, 0x10`), no query params, no body. The path literal is the two-arg template
`"{0}/{1}/experience"` with `{0}` a hardcoded `"rooms"` literal and `{1}` the long room id, so
searching for `rooms/{0}/experience` finds nothing — search for `/experience` instead. Client entry
`JOOBKACKLJE.OPOLMNDLBND(long roomId, CancellationToken)` at `0x7DB5630`.

Response is a **bare object, no envelope** — `TResponse = PBOOAFNIPBL` (confirmed from the
`HPBKMCLEANE` methodSpec inst 2892). Formatter `GAMIGAPLLIK` ctor `0x7E7BAF0`, two keys:

```json
{ "Enabled": true, "DailyLimit": 1000 }
```

`Enabled` bool 0x10, `DailyLimit` int 0x14. `PBOOAFNIPBL.CPOBHIECLEN` is the `0xA60520` no-op — no
validation.

The setter confirms the semantics: `JOOBKACKLJE.FIOCOBOOIAA(long roomId, bool enabled,
int dailyLimit)` at `0x7DB4F60` is a **POST to the same path** that sends `enabled` and `dailyLimit`
as **query params** (lowercase camelCase, via `MGPBDIAGCFD.ELHKHFJEHLM`) with no body, and returns
the valueless envelope `JFNAKFCGDAO` — see [outfits-me-put-wire-shape](outfits-me-put-wire-shape.md) for that 3-key shape.
Same path, two verbs, two completely different response shapes.

Sibling endpoints on the same template are now derived — see
[rooms-experience-player](rooms-experience-player-wire-shape.md): `{0}/{1}/experience/player` GET
(`BPMPLEMPMHF` `0x7DB4D90`) returns a **different** bare DTO `.KBOCGEMKEOL`
`{RoomExperienceEnabled, Experience, ConcurrencyCode}`, its POST (`GBMHNIPLKGF` `0x7DB5150`,
form-body `increment` + `concurrencyCode`) is **enveloped** around that same DTO, and
`{0}/{1}/experience/coOwner` POST (`KMLGJHNBELM` `0x7DB53C0`) is the absolute-value twin
(`targetExperience`). **Do not reuse this note's `{Enabled, DailyLimit}` shape for `/player`.**

**Why:** this is the room-level XP feature's config — `DailyLimit` caps per-day XP earned in the
room. Returning `Enabled:false` disables room XP entirely for that room.

⚠️ **CORRECTION 2026-09-02:** where this note says the parameters are **query params**, they
are actually an **`application/x-www-form-urlencoded` request body** — `ELHKHFJEHLM` routes params
to the query string only for GET. See [elhkhfjehlm-verb-dependent-params](../conventions/elhkhfjehlm-verb-dependent-params.md). Response shape
unaffected.
