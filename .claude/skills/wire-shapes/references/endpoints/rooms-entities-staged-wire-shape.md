# Rooms entities staged wire shape

> GET rooms/{roomId}/entities/staged (svc 16 Rooms) is ENVELOPED — {Value:{SubRooms:[{SubRoomId,Name,SavedByAccountId,SaveDescription,CreatedAt}]},Success,Error,error_id}. Value.SubRooms must be a list, never null.

Derived **2026-09-16** from build `20250718.01`.
Envelope tiering follows the facade rule in [playerevents-v1-room](playerevents-v1-room-wire-shape.md); same facade as
[rooms-bans-history](rooms-bans-history-wire-shape.md) and [featuredrooms-current](featuredrooms-current-wire-shape.md).

`GET https://rooms.<host>/rooms/{roomId}/entities/staged` — service **16 = Rooms**, verb **GET**
(`HttpMethod` statics `[rcx+8]` at `0x7DF7682`, passed as the helper's `r8`). Path is
`String.Format("rooms/{0}/entities/staged", roomId)` — the room id is a **path segment**, and there
are **no query params and no body**.

Client entry `OALMDGJKBJH.DHMJPHNLJJI(long roomId, CancellationToken)` `0x7DF75C0` (+0x130),
description literal `'get room entity change list'`. Sibling route (not derived here):
`rooms/{0}/entities/staged/subroom/{1}`.

## ⚠️ ENVELOPED — the send generic alone will mislead you

The helper is **`OALMDGJKBJH.PJPLCMBOAFB<T>`**, not `HPBKMCLEANE<T>`. Its methodSpec generic inst
`#14740` resolves to `.EIFHMLNBFMI`, but that is **`T`, not the body** — `PJPLCMBOAFB<T>`'s state
machine awaits `TaskAwaiter<KGOJLHJNIOD<!T>>`, so the wire body is
**`KGOJLHJNIOD<EIFHMLNBFMI>`**. On `OALMDGJKBJH` *every* helper takes a leading
`friendlyActionDescription`, so **every route on this facade is enveloped**
([playerevents-v1-room](playerevents-v1-room-wire-shape.md)).

> Contrast [avatar-gifts-v2](avatar-gifts-v2-wire-shape.md): there the helper is `HPBKMCLEANE<T>` and *also* carries a
> description, yet the body is bare. The description is a reliable tell only via **which helper** it
> belongs to — `HPBKMCLEANE` = bare, `PJPLCMBOAFB` = enveloped. Resolve the helper, not the string.

```json
{ "Value": { "SubRooms": [
      { "SubRoomId": 1, "Name": "Main", "SavedByAccountId": 319,
        "SaveDescription": "", "CreatedAt": "2026-09-16T11:39:30Z" } ] },
  "Success": true, "Error": null, "error_id": null }
```

`error_id` is lowercase (`[DataMember]`); `Success`/`Error`/`Value` are PascalCase. A null envelope
or `Success == false` raises **`LLCLDPPAGIJ`**
([llcldppagij-envelope-failure-exception](../conventions/llcldppagij-envelope-failure-exception.md)).

## `Value` = `.EIFHMLNBFMI` — one key

Formatter `GAFEECGLEDD` `.ctor 0x7770C90` (+0x220) — a single `____stringByteKeys` entry
**`SubRooms`**, backed by the type's one field, `IReadOnlyList<BKNGIFHNCIH>` @0x10.

## `SubRooms[]` = `.BKNGIFHNCIH` — 5 keys

Formatter `CGPIMAAMPGG` `.ctor 0x77661A0` (+0x710), key run `0x776669F..0x77667D7`. The type declares
only **one** field (`long` @0x30); the other four come from its base, which has no formatter of its
own — consistent with **derived members emitted before base members**.

| # | key | CLR | note |
|---|---|---|---|
| 1 | `SubRoomId` | long | the declared field @0x30 — the only derived member |
| 2 | `Name` | string | |
| 3 | `SavedByAccountId` | int | |
| 4 | `SaveDescription` | string | |
| 5 | `CreatedAt` | DateTime | Utf8Json ISO-8601 (`NKLCFNHAFNB.ILIOAHGLMKI` in the deserializer) |

*`SubRoomId` is certain (declared field). The other four types are read off the deserializer's
reader primitives and RecNet convention, not from a base-class field table — the base type name did
not resolve through the typedef parent index.*

## Send `SubRooms: []`, never null

`EIFHMLNBFMI.CPOBHIECLEN` `0x7C74CA0` is **not** the shared no-op stub — it is a 3-instruction hook
that loads `SubRooms` (`[rcx+0x10]`) and tail-jumps to the list-validate helper
`EADLCOCJAGD.IANBCAFGFNL` `0x7623250`. That helper **returns false on a null list rather than
throwing** (same helper as [algorithmiclists](algorithmiclists-wire-shape.md) and
[econ-customavataritems-owned](econ-customavataritems-owned-wire-shape.md)), so a null does not crash — it fails validation and the
response is treated as unusable. An empty room stages `{"SubRooms": []}`.
