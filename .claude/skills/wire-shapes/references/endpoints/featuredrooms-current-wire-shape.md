# Featuredrooms current wire shape

> Wire shape of GET featuredrooms/current on the Rooms service for recflare-2025 — a bare {FeaturedRoomGroupId, Name, Rooms[]} where Rooms is a 3-key summary, NOT the full Room DTO.

Derived **2026-08-18** from `C:\Games\recflare-2025` (build `20250718.01`) via
[recflare-2025-metadata-carve](../../../il2cpp-analysis/references/recflare-2025-metadata-carve.md).

`GET https://rooms.<host>/featuredrooms/current` — **GET** (`HttpMethod` statics `+0x08`), no query
params, no body. Client entry `OALMDGJKBJH.KJKKKAEFDPK(CancellationToken)` at `0x7DFC8E0`; it goes
through the class-bound send helper, so there is no inline service constant — the Rooms host applies.

Response is a **bare object**, `NGEIGAGNEIB` (no envelope formatter exists for it). Formatter
`LDKILCPGEPI` ctor `0x772DF00`, 3 keys:

- `FeaturedRoomGroupId` long 0x10
- `Name` string 0x18
- `Rooms` `IReadOnlyList<OLPPPKGBPDA>` 0x20

**`Rooms` is a lightweight 3-key summary, not the canonical 44-key Room DTO** — this is the trap,
because `rooms/contributedby/me` on the same service returns full `MIBODHPEFHP` records
(see [rooms-contributedby-wire-shape](rooms-contributedby-wire-shape.md)). Element `OLPPPKGBPDA`, formatter `JIAIDMLGAPP` ctor
`0x77261E0`:

- `RoomId` long 0x10
- `RoomName` string 0x18 — the property is renamed by `[DataMember(Name = "RoomName")]`
- `ImageName` string 0x28

The field at 0x20 is `[IgnoreDataMember]` and carries **no key**, which is why the type has 4 backing
fields and 3 wire keys.

No hard requirements: `OLPPPKGBPDA.CPOBHIECLEN` is the `0xA60520` no-op, and
`NGEIGAGNEIB.CPOBHIECLEN` (`0x7DABD00`) is a 3-instruction tail-jump that hands `Rooms` to the
list-validate helper `EADLCOCJAGD.IANBCAFGFNL`, which returns false on a null list rather than
throwing. `{"FeaturedRoomGroupId":0,"Name":"","Rooms":[]}` is safe.

**Why:** the client's own naming (`featuredRoomGroup`, `FeaturedRoomGroupId` literals) shows this is
one *group* at a time — "current" selects which group is live, so the server picks the rotation and
the client just renders it.
