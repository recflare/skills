# `GET api/roomkeys/v1/mine` — bare array of the **12**-key `RecNet.RoomKey` (2026)

> `GET api/roomkeys/v1/mine` (svc **28 Econ**) takes **no query params and no body** and returns a
> **bare JSON array** — `List<RecNet.RoomKey>`. No envelope, no wrapper.
> ⚠️ **On 2026 the element has 12 keys, not 10.** The 2025 derivation
> ([roomkeys-v1-room](roomkeys-v1-room-wire-shape.md)) described `.JODGFDKLMBO` with 10; build
> `20260323.14` adds **`IsGiftable`** (bool) and **`Visibility`** (enum) at the end.
> ⚠️ **Return `[]`, never `null`.** The send is the plain, non-nullable `ZWUODKCINOA<List<RoomKey>>`,
> so a `null` body **resolves successfully** with a null list — which then throws an
> unconditional NRE in `RoomKeysManager.PZHPRAJRVOR` at `0xFD673A`.

Derived **2026-10-22** from build `20260323.14`. Supersedes the "same as `/room`" aside in the 2025
note (line 65 there), which was true for the *tier* but is now wrong on the *key count*.

## Route

Facade **`RecNet.RoomKeys.OWTUJPMPXGM(bool forceRefresh)`** **`0x95460B0`** →
`RecRoom.Async.MPVTAJGPRUT<List<RecNet.RoomKey>>` (a value-or-error promise, not a `Task`).

| what | value | evidence |
|---|---|---|
| path | `api/roomkeys/v1/mine` | literal **`0xFC6BE30`**, `mxref` = exactly **2** refs, both in this method (`0x954610E` init `lea`, `0x9546180` use `mov`) — **so the route is the only literal: no params** |
| service | **28 = Econ** | `mov dword ptr [rsi+0x18], 0x1C` at `0x95461A8` |
| verb | **GET** | `[klass+0x20]` → `[statics+0x08]` at `0x9546165`–`0x9546170` |
| params | **none** | — |
| body | **none** | no `RGBOOBRDHEB` body setter in the method |
| response | `List<RecNet.RoomKey>` | the promise's `T`, confirmed by `msig` on the facade |

Unlike `/room`, the path is a **single whole literal** — it is not assembled from
`"api/roomkeys/v1/"` + a suffix, so grep for the full string.

### The `bool` is `forceRefresh`, and it never reaches the wire

```
0x95461e1  movzx r8d, bpl                 ; the bool argument
0x95461ec  call RecNet.RGBOOBRDHEB::ORUUDATDRUN(System.TimeSpan a, bool b)
0x9546202  call ZWUODKCINOA<List<RoomKey>>(default(CancellationToken))
0x9546225  jmp  <Task -> MPVTAJGPRUT adapter>
```

`ORUUDATDRUN(TimeSpan, bool)` installs a **client-side response cache** on the request. The sole
caller is **`RoomKeysManager.DownloadPurchasedKeys(bool forceRefresh)`** `0xFD4560` — the parameter
name survives obfuscation and names the flag outright. So the bool bypasses the *local* cache; it is
**not** a query parameter, and the server sees an identical URL either way.

⚠️ **This route is client-cached.** Relaunch (or trigger a `forceRefresh` path) between server-side
attempts, as with `makerai/checkfreetrialeligibility` and `club/home/me`. ⚠️ **Not verified**: the
TTL value — it comes from a static `TimeSpan` at `statics+0x18` of a class resolved through a
metadata slot, and the carve cannot read its `.cctor`-assigned value.

`DownloadPurchasedKeys` is reached from `MAVKTNEGJUC.NNTONBIXDML` `0xFE74F0` and
`NJBNOYAVOGN.RWMNZISTTGJ` `0x203BEF0`.

## Response

```json
[{"RoomKeyId":900001,"ReplicationId":"0f8c3a7e-1d42-4b90-9c11-7a6e5d2b8f03","RoomId":12,
  "Name":"VIP Key","Description":"","Price":0,"PurchaseCurrencyId":null,
  "CreatedAt":"2026-10-14T12:00:00Z","ImageName":"","Type":0,
  "IsGiftable":false,"Visibility":0}]
```

`[]` is the correct "no keys" answer.

### `RecNet.RoomKey` (typedef #22924) — 12 fields, 12 wire keys, no renames

Formatter **`Utf8Json.Formatters.RecNet.FWDJKUCRMCE`** `.ctor` **`0x8E744E0`**, confirmed by `msig`
(`Serialize(JsonWriter, RecNet.RoomKey, …)`). `____stringByteKeys` runs `0x8E74B10`…`0x8E74CCC` in
exact declaration order:

| # | key | CLR | off | notes |
|---|---|---|---|---|
| 1 | `RoomKeyId` | long | 0x10 | |
| 2 | `ReplicationId` | **`System.Guid`** | 0x18 | a Guid here, *not* a string — unlike the invention DTOs that reuse the key name |
| 3 | `RoomId` | long | 0x28 | |
| 4 | `Name` | string | 0x30 | |
| 5 | `Description` | string | 0x38 | |
| 6 | `Price` | int | 0x40 | |
| 7 | `PurchaseCurrencyId` | `Guid?` | 0x44 | nullable → **optional** |
| 8 | `CreatedAt` | `DateTime` | 0x58 | non-nullable; omit ⇒ `DateTime.MinValue` |
| 9 | `ImageName` | string | 0x60 | |
| 10 | `Type` | `RecRoom.DataLayer.RoomKeyType` | 0x68 | enum, **numeric** |
| 11 | **`IsGiftable`** | bool | 0x6C | **NEW on 2026** |
| 12 | **`Visibility`** | `RecRoom.DataLayer.UgcPurchasableItemVisibility` | 0x70 | **NEW on 2026**, enum, **numeric** |

All three casings exist per key (`RoomKeyId`/`roomKeyId`/`roomkeyid`, …); for `Name`, `Description`,
`Price`, `Type` and `Visibility` the camelCase and all-lowercase forms coincide, hence 2 entries
rather than 3.

Both enums are **numbers on the wire** — no member name (`CircuitEventKey`, `AlwaysVisible`,
`HiddenInWatchStore`) exists as a string literal in the build, so there is no by-name formatter:

```
RecRoom.DataLayer.RoomKeyType                  (#62219) : int   Key 0 · CircuitEventKey 1
RecRoom.DataLayer.UgcPurchasableItemVisibility (#62228) : int   AlwaysVisible 0 · HiddenInWatchStore 1
```

The 2025 enum `CAIBPLFEHJI` is this build's `RoomKeyType` — same two members, same values.

### No post-deserialize hook at all

`RecNet.RoomKey` declares **28 methods** = 24 property accessors + 3 static factories
(`XFACHNHPLKJ` ×2, `RJQAERLDPQZ`) + `.ctor`. There is **no `EMSIIQRWASQ` and no `IULRMJBAHPG`**, so
neither the sync nor the async 2026 hook runs — **zero per-element validation or normalization**.
Every key is accepted as sent, and an omitted key silently takes its CLR default (numbers `0`,
`CreatedAt` `DateTime.MinValue`, enums `0` = `Key` / `AlwaysVisible`).

## ⚠️ The list must not be null

The send is **`ZWUODKCINOA<List<RoomKey>>(ct)`** — the *plain* helper, **not**
`LIRIDCJIGGA(bool, ct)`, so there is no allow-null flag to read and nothing rejects a null value
([2026-send-helper-tiers](../conventions/2026-send-helper-tiers.md)). A `null` body therefore
resolves the promise **successfully** with a null list, and the continuation hands it to:

```
RoomKeysManager.PZHPRAJRVOR(IList<RecNet.RoomKey> a, bool b)   0xFD6590
  0xfd65ed  test rbx, rbx          ; rbx = the list
  0xfd65f0  je   0xfd673a          ; -> 0xC403A0  raise NullReferenceException
```

`0xC403A0` is the codegen NRE helper, so `null` is an **unconditional throw**, not a handled "no
keys". This is the same rule the 2025 note recorded for `/room`, re-confirmed on 2026 and reachable
from `/mine`.

A `{}` body fails earlier and differently — `T` is a `List`, so it raises
`IONCMJIACFI` "Malformed Response"
([ioncmjiacfi-malformed-response](../conventions/ioncmjiacfi-malformed-response.md), and
`nonobject-responses.txt` line 83 lists this route).

➡️ **`200 []`** for "this account owns no room keys". Never `null`, never `{}`, never 204.

## Sibling routes on `RecNet.RoomKeys` (42 methods)

| route | facade | returns |
|---|---|---|
| `api/roomkeys/v1/mine` | `OWTUJPMPXGM(bool)` `0x95460B0` | `List<RoomKey>` ← **this note** |
| `api/roomkeys/v1/room?roomId=` | `AYDXKHHPMBT(long)` `0x9543300` | `List<RoomKey>` ([2025 note](roomkeys-v1-room-wire-shape.md)) |
| — (cached variant) | `FCHSORGEVTO(bool, ct)` `0x95442A0` | `List<RoomKey>` |
| `api/roomkeys/v1/create` | `NDHONCQESZY` / `JCZDOFIPTSV` | `RoomKeyResponse` ([note](roomkeys-v1-create-wire-shape.md)) |
| `api/roomkeys/v1/awardbulk` | `LSSROQHKQVJ(IEnumerable<AwardRoomKeyRequest>, ct)` | `Task<List<RecNetResultObject<AwardRoomKeyResponse>>>` ([note](roomkeys-v1-awardbulk-wire-shape.md)) |
| `api/roomkeys/v1/owns/bulk` | `DWOUHCYYOTH(IReadOnlyList<DoesPlayerOwnRoomKeyRequest>, ct)` | `Task<List<DoesPlayerOwnRoomKeyResult>>` ([note](roomkeys-v1-owns-bulk-wire-shape.md)) |
| `api/roomkeys/v1/owns` | `DPNKMTAHCRM(long)` | `MPVTAJGPRUT<bool>` — **not derived** |
| `api/roomkeys/v1/revoke` | `MDKMLIUDHUG(RevokeRoomKeyRequest, ct)` | `Task<RecNetResult>` — **not derived** |

Note the 2026 facade mixes both async styles: the older routes return `MPVTAJGPRUT<T>` promises,
the newer bulk/revoke ones return real `Task<T>` and go through the
`RecNetResult*` envelope types.
