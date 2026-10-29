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

# ✅ 2026 (`20260323.14`): re-verified — same wire shape, real names recovered

Re-derived **2026-10-20**. **The shape above is unchanged** — 3 keys on the group, 3 on the element,
bare, no envelope. What 2026 adds is de-obfuscated names and the identity of the key-less field.

| 2025 | 2026 |
|---|---|
| `OALMDGJKBJH.KJKKKAEFDPK` | **`RecNet.Rooms.DFMBMRNABHU.WJTOCIAXDUR(ct)`** `0x95B3D40` |
| `NGEIGAGNEIB` | **`RecNet.Rooms.FeaturedRoomGroupDTO`** (typedef #23448) |
| `LDKILCPGEPI` | formatter `Utf8Json.Formatters.RecNet.Rooms.OOIERBCAXRX` `.ctor` **`0x8EC2010`** (`..0x8EC2286`) |
| `OLPPPKGBPDA` | **`RecNet.Rooms.FeaturedRoomDTO`** (typedef #23447) |
| `JIAIDMLGAPP` | formatter `Utf8Json.Formatters.RecNet.Rooms.SDCQELIHPXC` `.ctor` **`0x8EC8270`** (`..0x8EC8546`) |

Route literal `'featuredrooms/current'` **`0xFC38228`** — `mxref` gives exactly **2** refs, both in
`WJTOCIAXDUR`. **GET**, from `[klass+0x20]` (the 2026 static-fields offset) at `0x95B3DDB` then
`[statics+0x08]` at `0x95B3DF4`. No query params, no body. Still routed through the class-bound send
`DFMBMRNABHU::XNYOJFPCXJH<T>` (generic inst **#3147 = `FeaturedRoomGroupDTO`**), so there is no
inline service constant — the Rooms host (svc 16) comes from the facade.

`Task<FeaturedRoomGroupDTO>` is the **plain tier** — bare object, no envelope
([2026-send-helper-tiers](../conventions/2026-send-helper-tiers.md)).

Group keys (**17** literal refs = 7 unique casings × 2 + 3 ✓):

| # | key | CLR | off |
|---|---|---|---|
| 1 | `FeaturedRoomGroupId` | long | 0x10 |
| 2 | `Name` | string | 0x18 |
| 3 | `Rooms` | `IReadOnlyList<FeaturedRoomDTO>` | 0x20 |

Element keys (**21** refs = 9 casings × 2 + 3 ✓) — `RoomId`, `RoomName`, `ImageName`.

## The 4th field is `SanitizedRoomName`, and it is computed CLIENT-SIDE

2026 names what the 2025 note could only call "the field at 0x20". `FeaturedRoomDTO` declares:

```
0x10  long    <RoomId>k__BackingField
0x18  string  <RawRoomName>k__BackingField           <- wire key 'RoomName'
0x20  string  <SanitizedRoomName>k__BackingField     <- NO KEY
0x28  string  <ImageName>k__BackingField
```

`SDCQELIHPXC$$Deserialize` **`0x8EC7E10`** writes exactly three offsets and never `+0x20`:

```
0x8ec7fcf: mov qword ptr [rbx + 0x10], rsi    ; RoomId
0x8ec7fe5: mov qword ptr [rbx + 0x18], r14    ; RawRoomName   <- 'RoomName'
0x8ec8003: mov qword ptr [rbx + 0x28], rbp    ; ImageName
```

Neither `RawRoomName` nor `SanitizedRoomName` exists as a string literal in the build, confirming
`RoomName` is a `[DataMember]` rename of `RawRoomName`. **Send `RoomName`; do not try to send a
sanitized variant** — same rule already recorded for `matchmake/event`
([matchmake-event](matchmake-event-wire-shape.md)): wire `Name` is `RawName`, `Sanitized*` is derived locally.

## 2026 post-deserialize hooks are ASYNC — `IULRMJBAHPG`, not `CPOBHIECLEN`

`RecNet.RTSPZODLERY` (typedef #46387) is the 2026 hook-runner pair, and it shows there are **two**
post-deserialize interfaces where 2025 had one (`PDDMBELEHHJ.CPOBHIECLEN`):

```csharp
static bool RTSPZODLERY.EMSIIQRWASQ(IEnumerable<RecNet.NFJCJJOZYBH>)   // SYNC  hook runner
static Task RTSPZODLERY.IULRMJBAHPG(IEnumerable<RecNet.KSRBBQPMHRN>)   // ASYNC hook runner  0x8DB43F0
```

- **`FeaturedRoomGroupDTO.IULRMJBAHPG` `0x4F579F0`** is three instructions — it only recurses:
  ```
  0x4f579f0: mov rcx, qword ptr [rcx + 0x20]   ; this.Rooms   -- NO null guard
  0x4f579f6: jmp RecNet.RTSPZODLERY$$IULRMJBAHPG
  ```
- **`FeaturedRoomDTO.IULRMJBAHPG` `0x95CC3F0`** is a real async method (its own
  `AsyncTaskMethodBuilder.Start`), which is where `SanitizedRoomName` is filled — sanitisation is a
  network round trip, which is *why* the hook is async at all.

### Confirmed **2026-10-28**: `IULRMJBAHPG` is `OnDeserializedAsync`, and the await is sanitisation

From [inventions-v2-batch](inventions-v2-batch-wire-shape.md). `RecNet.Invention.IULRMJBAHPG`
`0x94D2FC0` has exactly one nested type — **`<OnDeserializedAsync>d__122`** (`MoveNext`
`0x94E7E30`) — so the obfuscated virtual's original name is **`OnDeserializedAsync`**, build-wide.
Its body also pins what the async round trip actually is: interface slot **20** on
`RecNet.AQWHEEVHLXV`, which `morder` resolves to

```csharp
Task<string> SanitizeDisplayTextAsync(string displayText, SanitizeMode sanitizeMode, bool isChat)
```

called three times with `sanitizeMode = 3`, `isChat = false` (`0x94E8013`, `0x94E809A`, `0x94E8118`)
— once each for `Name`, `Description`, `LongDescription`. The same hook re-encrypts the DTO's six
`Obscured{Long,Int,Bool}` members via `OOBOIWNJMNP` (`0x94E7F37`…`0x94E7FB0`), which is the
independent proof those arrive as plain JSON numbers/bools.

➡️ So the general rule for a DTO with an `IULRMJBAHPG`: **every user-visible display string on it is
fed to `SanitizeDisplayTextAsync` unguarded — serve `""`, not `null`.** Here that is
`SanitizedRoomName`'s source; on `Invention` it is three fields at once.

⚠️ **Send `"Rooms": []`, never `null`.** The group hook hands `Rooms` straight into a method whose
parameter is `IEnumerable<…>` with no null check at the call site. The 2025 note's claim that the
list helper "returns false on a null list rather than throwing" was about the **sync** 2025 helper
and does **not** carry over to the async 2026 one — ⚠️ **not verified** either way here, because the
throw (if any) is inside a generic-shared `MoveNext` that `callxref` cannot reach. `[]` costs nothing
and sidesteps the question.

`{"FeaturedRoomGroupId":0,"Name":"","Rooms":[]}` remains safe.

## ⚠️ Do not confuse this with `.CommunityBoardDTO`

`FeaturedRoomGroup` is also a **wire key** on 2026 (`0xFD19310`), but it belongs to
`.CommunityBoardDTO` (formatter `Utf8Json.Formatters.RecNet.ODTIGZBBDPA` `.ctor` `0x91307D0`) — a
different route that **embeds** this same group object under that key. Grepping for
`FeaturedRoomGroup*` hits both; the `Id` variants (`0xFD19660`) are this route's.
