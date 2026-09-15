# Clubhousesearch mostactivenow wire shape

> GET clubhousesearch/mostactivenow (svc 4 Matchmaking) returns a BARE array of {RoomId, ClubId, PlayerCount} — and it is IDENTICAL on both client builds, unlike PlayerEvent.Tags.

Derived **2026-08-25** from build `20250718.01`, then cross-checked against `20230414`.

`GET https://match.<host>/clubhousesearch/mostactivenow` — service **4 = Matchmaking**
(`mov r8d, 4`, [recnet-service-enum](../conventions/recnet-service-enum.md)), verb **GET** (`HttpMethod` statics `+0x08`),
**no query params, no body**. Client entries `RecNet.Matchmaking.CELJBAIMOOO()` `0x7D39810` and
`MCGKBPKCGMB.CELJBAIMOOO()` `0x7D346C0` (same method on two facades); literal `0xD1F81F8`; the error
path logs `'Failed to get MostPopulatedClubhouseRoomSummaries'`, which is the best name for what this
returns.

**Response is a BARE JSON ARRAY — no envelope.** Send generic is
`MGPBDIAGCFD::HPBKMCLEANE<List<CPPEIGGHGOH>>` (T is the `List` directly). Element formatter
`MONFOADHHKG` `.ctor 0x7AC8770`, 3 keys, verified against the field offsets:

| key | CLR | off |
|---|---|---|
| `RoomId` | long | 0x10 |
| `ClubId` | long | 0x18 |
| `PlayerCount` | int | 0x20 |

```json
[ { "RoomId": 1159, "ClubId": 42, "PlayerCount": 7 } ]
```

Serve `[]` when nothing is active — it is a `List<T>` route, so `{}` raises the malformed-response
throw ([nonobject-response-routes](../conventions/nonobject-response-routes.md)). **No validation**: `CPPEIGGHGOH.CPOBHIECLEN` is the `0xA60520`
no-op. `ClubId` is a plain `long`, not nullable — send `0` rather than `null` for a room with no club.

## Cross-build: identical, no branch needed

Checked on `20230414` ([two-client-builds-name-check](../../../il2cpp-analysis/references/two-client-builds-name-check.md)) via Mono.Cecil over
`il2cpp-tools/out/DummyDll/RecNet.Runtime.dll`: the route literal and the
`MostPopulatedClubhouseRoomSummaries` error string both exist, and **exactly one** type in that
assembly has the `{Int64, Int64, Int32}` shape — `EAKEEKOJOAO`, whose first two fields carry the same
obfuscated names (`MCMOLLCNPHO`, `AJGPCPPJOBD`) that the PlayerEvent base uses for `RoomId` and
`ClubId` on that build. Same shape, same field identities, so **one response body serves both
clients** — unlike [playerevent-tags-build-difference](playerevent-tags-build-difference.md).

**Technique worth reusing:** with no binary for `20230414`, "how many types have exactly this field-type
sequence?" is a surprisingly sharp identifier — a 3-field `{long, long, int}` matched *one* type in
the whole RecNet.Runtime assembly. Cross-checking obfuscated field names against a DTO already
mapped on the same build then confirms which field is which.
