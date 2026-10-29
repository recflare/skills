# Rooms subrooms/{id}/permissions wire shape (+ the full permission enum)

> PUT rooms/{roomId}/subrooms/{subRoomId}/permissions (svc 16 Rooms) sends
> `{"permissions": [{Permission, Role, Override, Type, Value}, …]}` — note the **lowercase
> `permissions`** wrapper — and returns the **ENVELOPED 63-key Room DTO**:
> `{Value: <Room>, Success, Error, error_id}`.
> `Permission` is the **member NAME** of the 42-member enum `.OGKGADHHDKM` (`Enum.ToString()`), e.g.
> `"CAN_USE_DELETE_ALL_BUTTON"` — the numeric values never reach the wire on this route.
> ⚠️ A **second** enum `.FFHJBMHNGMN` also declares `CAN_USE_DELETE_ALL_BUTTON`, with value **84**
> instead of **14**. It belongs to the in-room `GameRole` system, not to this route.

Derived **2026-10-06** from build `20250718.01`.
Response DTO is the same one documented in [rooms-room-by-id](rooms-room-by-id-wire-shape.md) — not repeated here.

> 🔄 **Re-verified on build `20260323.14` (2026-10-26)** — shapes unchanged, but the read-back has
> **two hard throws** that were not known in 2025, and one permission was **renamed**. Everything
> below is the 2025 derivation; see **[2026 update](#2026-update-build-20260323140)** at the end for
> the plain type names, the throws, and the rename. Read that section first if you are on 2026.

`PUT https://rooms.<host>/rooms/{roomId}/subrooms/{subRoomId}/permissions` — service **16 = Rooms**,
facade `OALMDGJKBJH`. Path is `String.Format("rooms/{0}/subrooms/{1}/permissions", roomId, subRoomId)`,
literal slot **`0xD1A81E8`**. Verb **PUT** (`HttpMethod` statics `[rcx+0x28]` at `0x7DF980E`).

Client entry **`OALMDGJKBJH.FOHKKKNNPAA`** `0x7DF96F0` (+0x1F0):

```
Task<.HGMJJMJDHLJ> FOHKKKNNPAA(long roomId, long subRoomId,
                               IReadOnlyList<.OAANAMJCIDA> permissions,
                               CancellationToken ct)
```

It carries the literal **`'change subroom permissions'`** at `0x7DF9892` — a
`friendlyActionDescription`, the reliable tell for an **enveloped** helper on this facade — and sends
with `OALMDGJKBJH.PJPLCMBOAFB<T>`, generic inst **#1188 = `.HGMJJMJDHLJ`**.

## Request body — `{"permissions": [...]}`

The body is the closure type **`.OCEEEKGNMFJ`**, which has exactly one field:

```
IReadOnlyList<.OAANAMJCIDA>  permissions
```

serialized at `0x7DF97A0` (`CFHGFDMFAOK.JLGMIHCIOPH`). **The wrapper key is lowercase
`permissions`** — the CLR field is genuinely named that, so the emitted key follows it. There are no
`ELHKHFJEHLM` calls, so nothing goes in the query string; the two ids are path segments only.

### The element — `.OAANAMJCIDA`, 5 keys

Formatter **`HFODKEFALPJ` `.ctor 0x773A710`** (+0x5C0), `____stringByteKeys` run
`0x773AAC0`..`0x773ABF8`. The 5 keys are 1:1 with the 5 fields and with the positional `.ctor`
`(string, PHBPGMMKBJJ, bool, IGAEHBCMEEN, string)`:

| # | key | CLR | off |
|---|---|---|---|
| 1 | `Permission` | **string** — an `.OGKGADHHDKM` member name | 0x10 |
| 2 | `Role` | enum `.PHBPGMMKBJJ` (**byte**) | 0x18 |
| 3 | `Override` | bool | 0x19 |
| 4 | `Type` | enum `.IGAEHBCMEEN` (**byte**) | 0x1a |
| 5 | `Value` | **string** | 0x20 |

```json
{ "permissions": [
    { "Permission": "CAN_USE_DELETE_ALL_BUTTON", "Role": 25,
      "Override": true, "Type": 0, "Value": "true" },
    { "Permission": "ROOM_LEVEL_THRESHOLD", "Role": 20,
      "Override": true, "Type": 1, "Value": "5" } ] }
```

`Permission` being a **string** is the load-bearing fact: `HPBPODPNPPO.MoveNext` calls
`System.Enum.ToString` at `0x8A7A941` immediately before `OAANAMJCIDA..ctor` at `0x8A7A98A`, so the
client writes the member *name*, never the integer. Consequence: **store and echo the name verbatim**
and do not map it to an int on the wire. A value the client cannot map would come through as the
decimal string (`Enum.ToString` on an unmapped int prints the number), so a numeric-looking
`Permission` is a sign of a client/server enum mismatch, not a valid request.

## `.OGKGADHHDKM` — the 42 permissions

This is the enum the route uses (typedef #58436, `int`-backed). Values are given because they are
what a server's own storage and any sibling route are likely keyed on, but **they do not appear on
this route's wire** — the name does. Note the gaps (2, 5, 10, 1005): those members were removed.

### Subroom / in-room tier (1–25)

| val | name | val | name |
|---|---|---|---|
| -1 | `INVALID` | 15 | `CAN_SAVE_INVENTIONS` |
| 1 | `CAN_EDIT_ROOM_ROLES` | 16 | `DISABLE_MIC_AUTO_MUTE` |
| 3 | `VOTE_KICK_PERMISSION` | 17 | `CAN_END_GAMES_EARLY` |
| 4 | `CAN_INVITE` | 18 | `CAN_USE_SHARE_CAM` |
| 6 | `CAN_TALK` | 19 | `DEPRECATED_CAN_EDIT_CIRCUITS` |
| 7 | `CAN_PRINT_PHOTOS` | 20 | `CAN_SPAWN_INVENTIONS` |
| 8 | `CAN_START_GAMES` | 21 | `CAN_SPAWN_CONSUMABLES` |
| 9 | `CAN_SELF_REVIVE` | 22 | `CAN_USE_ROOM_RESET_BUTTON` |
| 11 | `AUTO_ASSIGNED_GAME_ROLES` | 23 | `CAN_USE_PLAY_GIZMOS_TOGGLE` |
| 12 | `CAN_CHANGE_GAME_MODE` | 24 | `AUTO_ASSIGNED_PLAYER_TAGS` |
| 13 | `CAN_USE_MAKER_PEN` | 25 | `CAN_USE_RRS` |
| **14** | **`CAN_USE_DELETE_ALL_BUTTON`** | | |

### Room-wide tier (1000+)

| val | name | val | name |
|---|---|---|---|
| 1000 | `ROOM_LEVEL_THRESHOLD` | 1011 | `CAN_MOVE_SUBROOMS` |
| 1001 | `CAN_SAVE_ROOM` | 1012 | `CAN_DELETE_SUBROOMS` |
| 1002 | `CAN_PUBLISH_ROOM` | 1013 | `CAN_EDIT_SUBROOM_SETTINGS` |
| 1003 | `CAN_CLONE_ROOM` | 1014 | `CAN_RESET_CLOUD_VARIABLES` |
| 1004 | `CAN_RESTORE_ROOM` | 1015 | `CAN_DELETE_CLOUD_VARIABLES` |
| 1006 | `CAN_EDIT_MAIN_ROOM_SETTINGS` | 1016 | `CAN_EDIT_ROOM_PROGRESSION` |
| 1007 | `CAN_EDIT_ROOM_ECON_SETTINGS` | 1017 | `CAN_REMOVE_ROOM_BANS` |
| 1008 | `CAN_CREATE_SUBROOMS` | 1018 | `CAN_ADD_ROOM_BANS` |
| 1009 | `CAN_NAME_SUBROOMS` | 1019 | `CAN_MODIFY_ROOM_WIDE_ASSETS` |
| 1010 | `CAN_CLONE_SUBROOMS` | | |

The 1000+ block being room-scoped while the route is subroom-scoped is not a contradiction — the
route's response is the **whole Room**, and the client posts both tiers through the same list.

## ⚠️ Two different enums declare `CAN_USE_DELETE_ALL_BUTTON`

`py fieldfind.py CAN_USE_DELETE_ALL_BUTTON` returns **two** typedefs:

| typedef | type | `CAN_USE_DELETE_ALL_BUTTON` | what it is |
|---|---|---|---|
| #58436 | **`.OGKGADHHDKM`** | **14** | **this route's permission enum** |
| #11862 | `.FFHJBMHNGMN` | 84 | the in-room `GameRole` attribute enum |

Picking the wrong one silently gives wrong numbers for every overlapping name
(`CAN_USE_MAKER_PEN` 13 vs 80, `CAN_SAVE_INVENTIONS` 15 vs 81, `CAN_SPAWN_INVENTIONS` 20 vs 82,
`CAN_USE_ROOM_RESET_BUTTON` 22 vs 83, `CAN_USE_PLAY_GIZMOS_TOGGLE` 23 vs 87).

**How it was settled:** xref the TypeInfo slots.
`.FFHJBMHNGMN` (slot `0xD071840`) is referenced **only** by
`RecRoom.Systems.PlayerRoles.GameRole` (`ECKNPLKJDPH` `0xF047A0`, `PBOIHPJNMEL` `0xF07B30`,
`PMPAPJFBKCL` `0xF08080`). `.OGKGADHHDKM` (slot `0xD26A640`) is referenced by
`HPBPODPNPPO.MoveNext` `0x8A7A360` — the "Migrating permissions to RecNet:" routine — which
references `.OAANAMJCIDA`, `.OGKGADHHDKM` and `.PHBPGMMKBJJ` in the same method and constructs the
DTO. That co-reference is the proof; the shared member name is not.

`.FFHJBMHNGMN` is the bigger of the two (70 members) and is where all the movement/locomotion
settings live — `CAN_MOVE 4`, `CAN_FLY 8`, `VR_WALK_SPEED 21`, `SCREENS_MAX_JUMP_HEIGHT 45`,
`WALL_RUN_*`, `SLIDE_*`, `EQUIP_*`, `ITEM_PICKUP_*`, `PLAYER_TAGS 76`. If a permission name you are
looking at is about movement or equip slots, it is **not** on this route.

## `.PHBPGMMKBJJ` — the `Role` enum (byte, 8 members)

| val | name |
|---|---|
| 0 | `None` |
| 1 | `Banned` |
| 10 | `Host` |
| 20 | `Moderator` |
| 25 | `Contributor` |
| 30 | `CoOwner` |
| 31 | `TemporaryCoOwner` |
| 255 | `Creator` |

**Sparse and non-sequential** — `Role: 2` is not a role. `Creator` is `255`, so a `byte` column is
exactly wide enough and a signed `tinyint` is not.

## `.IGAEHBCMEEN` — the `Type` enum (byte, 3 members)

| val | name |
|---|---|
| 0 | `Bool` |
| 1 | `Int` |
| 2 | `StringList` |

`Value` is a **string** regardless of `Type`, so the type tag is what tells the server how to parse
it. Which permission uses which `Type` was **not derived** — no per-member mapping table was located
in the build. The names strongly suggest `Bool` for every `CAN_*`/`DISABLE_*`, `Int` for
`ROOM_LEVEL_THRESHOLD` and `VOTE_KICK_PERMISSION`, and `StringList` for `AUTO_ASSIGNED_GAME_ROLES`
and `AUTO_ASSIGNED_PLAYER_TAGS` — but that is inference from naming, not from the binary, and **the
encoding of a `StringList` `Value` (CSV, JSON array in a string, …) is unresolved**. Trust the
inbound `Type` rather than a table of your own, and echo `Value` back byte-for-byte.

## Response — ENVELOPED Room DTO

`PJPLCMBOAFB<T>` with inst **#1188 = `.HGMJJMJDHLJ`**, the same 63-key Room DTO that
`GET rooms/{id}?include=` returns bare — but here it is **enveloped**, because the helper carries a
description:

```json
{ "Value": { "DataBlob": "…", "DataBlobHash": "…", "SubRooms": [ … ], "Roles": [ … ], … },
  "Success": true, "Error": null, "error_id": null }
```

Full key list in [rooms-room-by-id](rooms-room-by-id-wire-shape.md). Two traps follow from that:

- **Same DTO, opposite tiers on two routes.** `GET rooms/{id}` is bare (`NDBMFFLDBBK`), this PUT is
  enveloped (`PJPLCMBOAFB`). Returning the bare Room here raises `LLCLDPPAGIJ`
  ([llcldppagij-envelope-failure-exception](../conventions/llcldppagij-envelope-failure-exception.md)), not `IONCMJIACFI`, and the
  visible symptom is only that the permission change never completes.
- **`Value` must carry the Room's `DataBlob`.** Because the client replaces its Room object from this
  response, a permissions PUT that returns a Room without `DataBlob` re-introduces the
  cloud-variables-show-as-"Unsaved" failure described in that note. Serve the same full Room you
  serve on the GET.

A `204` or an empty body fails the same way — `PJPLCMBOAFB` is a response-required helper, not the
fire-and-forget `CNDMDLNHDLI` tier.

## ⚠️ The UI toggle does NOT read this response — why a slider snaps back

Symptom: a bool toggle in the room-roles UI (e.g. **"Can Self-Revive?"** = `CAN_SELF_REVIVE 9`)
flips, the PUT succeeds, and the toggle reverts a moment later. **Fixing this response will not fix
that**, because the client throws the response away.

### The write discards `Value`

The interface method behind the UI is

```
.BOIBFMBGBGB.FOHKKKNNPAA(long roomId, long subRoomId, IReadOnlyList<.OAANAMJCIDA>) -> Task
```

a **non-generic `Task`** (`IHMMMAEAMKC.FOHKKKNNPAA` `0xF23DE0`, +0x90). The envelope is still
deserialized — so a wrong envelope faults the task — but the 63-key Room in `Value` is **parsed and
dropped**. No UI state is taken from it.

### The read-back is the MATCHMAKING room-instance payload

The same interface exposes the authoritative read:

```
.BOIBFMBGBGB.NPPNKOILMFK(CancellationToken) -> Task<.FEJPDKONECB>
.BOIBFMBGBGB.GJOBGOHMBDB(Action<.FEJPDKONECB>)   // add change listener
.BOIBFMBGBGB.AMIOOAOCIBJ(Action<.FEJPDKONECB>)   // remove
```

`IHMMMAEAMKC.NPPNKOILMFK` `0xF24030` guards on the current game session
(`RecNet.Matchmaking.HOGBJEEMMIP` → `GGCLDGNBNLI.LNKIECNGMJP()`, a `bool`) and delegates to
`KCHDMOJGHJD.NPPNKOILMFK` `0x7DDADD0`, whose `AsyncTaskMethodBuilder<T>` is inst **#1170 =
`.FEJPDKONECB`**.

**`.FEJPDKONECB` is the room-instance join payload.** Formatter **`DJFNPPHJPJA` `.ctor 0x77386F0`**
(+0x470) — confirmed by `py msig.py DJFNPPHJPJA`, whose `Serialize`/`Deserialize` name
`.FEJPDKONECB` outright — with a 3-key `____stringByteKeys` run at `0x7738A07`..`0x7738AA9`:

| # | key | CLR | field |
|---|---|---|---|
| 1 | `RoomInstanceId` | long | `AMKPFKOBAPI` |
| 2 | `PhotonAccessToken` | string | `ICPHPNCEGMD` |
| 3 | **`Permissions`** | `IReadOnlyList<.OAANAMJCIDA>` | `JNNNFICAFPB` |

```json
{ "RoomInstanceId": 123456, "PhotonAccessToken": "…",
  "Permissions": [ { "Permission": "CAN_SELF_REVIVE", "Role": 25,
                     "Override": true, "Type": 0, "Value": "true" }, … ] }
```

(`.FEJPDKONECB` declares a 4th field, a self-typed `EOKOBKKHEHK` clone slot, which is not a wire
key — the same pattern as `GGCLDGNBNLI.NIHEOMPJLFD`.)

`RoomInstanceId` + `PhotonAccessToken` next to `Permissions` identifies this as the **matchmaking
join / room-instance** response, **not** anything on the Rooms service. So:

> **The permission values the UI displays come from the matchmaking room-instance payload's
> `Permissions` array.** The Rooms PUT writes; matchmaking reads back. A server that persists the PUT
> but keeps serving the old `Permissions` in that payload produces exactly this snap-back.

### Why it looks like an optimistic-UI revert

`RRUI.Data.RoomPermissionModel` holds

```
Dictionary<.OGKGADHHDKM, object> MCKOCLIDLPO     // in-flight writes, keyed by permission
bool IsFieldRequestInProgress(.OGKGADHHDKM)      // 0xAD87F0 - ContainsKey on that dict
void BMLPAEEDGDK(.FEJPDKONECB)                   // 0xAD84C0 - the change-listener callback
```

Each UI row is one `.OGKGADHHDKM` member (`RRUI.Data.RolePermissionModel.get_RolePermission()`
returns `.OGKGADHHDKM`; `GetRolePermissionFriendlyName` `0x2849F90` renders the label). While the
write is in flight the row shows the **pending** value from `MCKOCLIDLPO`; once that entry clears,
the row falls back to whatever `BMLPAEEDGDK` last applied from `.FEJPDKONECB`. Two different faults
look identical:

1. **The PUT's task faulted** — wrong envelope → `LLCLDPPAGIJ` → the pending entry clears and the
   old value reappears. Cheapest to rule out: make the envelope exactly
   `{Value:{…}, Success:true, Error:null, error_id:null}` and confirm a `204`/bare body isn't being
   sent.
2. **The read-back still has the old value** — the matchmaking `Permissions` array was not updated.

### How to tell the two apart

- **Watch for an HTTP request after the PUT.** If a matchmaking fetch follows, that is the response
  to fix — its `Permissions` must contain the entry with the new `Value`. If **nothing** follows,
  the client is reading a cached session and the payload has to be right at join time (or refreshed
  by a push).
- Match on **`Permission` name *and* `Role`** — one `(Permission, Role)` pair per row, so echoing
  `CAN_SELF_REVIVE` under the wrong `Role` leaves the edited row unchanged.
- `CAN_SELF_REVIVE` is `Type: 0` (`Bool`) with `Value` a **string** (`"true"` / `"false"`), not a
  JSON boolean — `Value` is `string` on the DTO regardless of `Type`.
- The simplest correct server behaviour is to **echo the request's `permissions` array back** as the
  authoritative set in the matchmaking payload.

### ✅ CONFIRMED root cause: the read-back must carry the SAME `(Permission, Role)` pair

Diagnosed on a live server **2026-10-06**. The PUT body was one entry:

```json
[ { "Permission": "CAN_SELF_REVIVE", "Role": 10, "Override": true, "Type": 0, "Value": "True" } ]
```

and `/photon_access_token` came back with 14 entries covering **only `Role: 0` and `Role: 255`** —
no `Role: 10`. The Host row therefore had nothing to read, fell back to the default, and the toggle
reverted. The PUT itself was fine.

**`(Permission, Role)` is the lookup key, not `Permission` alone.** The applier is

```
static bool .DFBNLBFNPDP.LADMPAMHNKG(.PHBPGMMKBJJ role, .OGKGADHHDKM permission,
                                     .OAANAMJCIDA dto, .ACIOJEPKBOA)
```

— role and permission are separate arguments — and the read side is
`.DFBNLBFNPDP.CNLKIHKBDNB(.IALDHONKEJC subRoom, .OGKGADHHDKM permission)` `0x8A74040` with an
`(int, .OGKGADHHDKM)` overload at `0x8A740F0`. So an entry under the wrong `Role` is invisible to the
row being edited, and **`Role: 0` (`None`) is not a wildcard or a default-for-all** — it is just the
`None` tier.

Practical rule: the `Permissions` array must contain **one entry per `(Permission, Role)` pair the UI
can show** — every role tier in `.PHBPGMMKBJJ` the room actually uses, not only `None` and
`Creator`. A server that serves a hard-coded default set will revert every edit for every tier
missing from that set, while looking like a response-shape problem.

✅ **`Value: "True"` is correct — capital T.** The client's own PUT body uses `"True"`, i.e. .NET
`Boolean.ToString()`, so echoing that exact casing back is right. (This also closes the open
question in [jwt-role-privilege-claims](../conventions/jwt-role-privilege-claims.md)-style string handling — here the
client is the producer, so its own request is the authority on format.) `Type: 0` (`Bool`) with
`Override: true` is likewise what the client sends and what it expects back.

### Sibling: the ROOM-level permissions write

`.BOIBFMBGBGB.BAKBFPICHDM(long roomId, IReadOnlyList<.OAANAMJCIDA>) -> Task` is the room-scoped
twin, served by **`PUT rooms/{roomId}/permissions`** — `OALMDGJKBJH.BAKBFPICHDM` `0x7DF5610`
(+0x1C0), description literal **`'change room permissions'`** at `0x7DF578B`, so also **enveloped**.
The 1000+ block of `.OGKGADHHDKM` is what it carries. Its response is discarded the same way.

## Related

The Room DTO's `Roles` key (#4) is **not** the read-back for this write — see the section above. Its
element is **`.FPMBNJIPBBL`** (typedef #23096, 4 fields:
`ObscuredInt accountId`, `.PHBPGMMKBJJ role`, `int?`, `.PHBPGMMKBJJ role`), i.e. a **per-account role
assignment**, carrying no permission values at all. The in-client role object is `.JNGHOMKNFPP`
(`{PHBPGMMKBJJ roleType, Action<OGKGADHHDKM>, string name, bool}`), held in
`.DFBNLBFNPDP` as `Dictionary<PHBPGMMKBJJ, JNGHOMKNFPP>` plus an `OGKGADHHDKM[]`. Sibling write
routes on the same facade and literal family: `rooms/{0}/subrooms/{1}/modify`,
`.../accessibility`, `.../name`, `.../maxplayers`, `.../move`, `.../clone`,
`.../default_matchmaking_policy`, `.../autostage`, `.../publish_save`.

---

## 2026 update (build `20260323.14`)

Re-derived **2026-10-26**. **Both wire shapes are byte-for-byte unchanged from 2025.** What changed is
that `RecNet.Rooms` type names are **no longer obfuscated**, two **hard throws** in the applier are
now visible, and one permission **member name was renamed** — which matters because `Permission`
travels as the member *name*.

### Plain names for everything the 2025 text calls by an obfuscated name

| 2025 | 2026 |
|---|---|
| `OALMDGJKBJH` (facade) | `RecNet.Rooms.DFMBMRNABHU` |
| `FOHKKKNNPAA` `0x7DF96F0` (the PUT) | **`GXBPMUJHTAH` `0x95ADAB0`** |
| `BAKBFPICHDM` `0x7DF5610` (room-level twin) | **`POHARNOOWJH`** |
| `KCHDMOJGHJD.NPPNKOILMFK` (the read-back) | **`DFMBMRNABHU.HQCEGSSASNS` `0x95ADF40`** |
| `.OAANAMJCIDA` | **`RecNet.Rooms.RolePermissionDTO`** (#23466) |
| `.FEJPDKONECB` | **`RecNet.Rooms.PhotonAccessTokenAndPermissionsDTO`** (#23457) |
| `.HGMJJMJDHLJ` | **`RecNet.Rooms.RoomDetailsDTO`** |
| `.OGKGADHHDKM` (42 permissions) | **`RecRoom.DataLayer.RolePermission`** (#62218) |
| `.PHBPGMMKBJJ` (8 roles) | **`RecRoom.DataLayer.AccountRoleType`** (#62198) |
| `.IGAEHBCMEEN` (Bool/Int/StringList) | **`RecNet.Rooms.RolePermissionType`** (#23467) |
| `.FFHJBMHNGMN` (the GameRole decoy) | **`.RolePermission`** (#11339) — still a collision, see below |
| `.DFBNLBFNPDP` (the applier) | **`RecRoom.Systems.PlayerRoles.WXOXYAWQQII`** |
| `LADMPAMHNKG` (per-entry applier) | **`LGRKEJPRDSI`** |
| `BMLPAEEDGDK` (change listener) | **`JKEEZMLERNO` `0xA253210`** |
| `RoomPermissionModel.MCKOCLIDLPO` etc. | `RRUI.Data.RoomPermissionModel` — **fully unobfuscated** (`Set` `0x287DD60`, `OnPermissionsUpdated` `0x287D9D0`, `IsFieldRequestInProgress` `0x287D970`, `RefreshInternal` `0x287DA10`, `get_DefaultRoomRole` `0x287EFB0`) |

Enum values are **identical** to the 2025 tables — `AccountRoleType` is still the sparse
`0,1,10,20,25,30,31,255`, `RolePermissionType` still `Bool 0 / Int 1 / StringList 2`, and
`RolePermission` still carries the same 42 members at the same values.

### Both verbs re-confirmed

Facade signatures via `msig`:

```
Task<RoomDetailsDTO>                      GXBPMUJHTAH(long roomId, long subRoomId,
                                                      IReadOnlyList<RolePermissionDTO>, ct)
Task<RoomDetailsDTO>                      POHARNOOWJH(long roomId,
                                                      IReadOnlyList<RolePermissionDTO>, ct)
Task<PhotonAccessTokenAndPermissionsDTO>  HQCEGSSASNS(ct)
```

| route | verb | evidence |
|---|---|---|
| `rooms/{0}/subrooms/{1}/permissions` | **PUT** | `0x95ADBBF mov rcx,[rax+0x20]` → `0x95ADBC3 mov rsi,[rcx+0x28]` — **`+0x28` = `Put`** |
| `photon_access_token` | **GET** | `0x95ADFDB mov rcx,[rax+0x20]` → `0x95ADFF4 mov rdx,[rcx+8]` — **`+0x08` = `Get`** |

Both are svc **16 Rooms** — `photon_access_token` lives on the **same `DFMBMRNABHU` facade** as
`rooms/hot`, so `GET rooms.<host>/photon_access_token` is the correct URL. It takes a
`requestBuilderAction` of **`null`** (`[rsp+0x20] = 0` at `0x95ADFEB`), i.e. **no query parameters
and no body at all**.

### Envelope tiers — unchanged, and the 2026 helper taxonomy that proves it

The 2026 send helpers on `DFMBMRNABHU`, from `msig`:

| helper | signature | tier |
|---|---|---|
| `XNYOJFPCXJH<T>` / `Get<T>` | `(HttpMethod, route, ct, builder) -> Task<T>` | **bare** — no description |
| `MSBYXMTYOOH` | `(string desc, HttpMethod, route, ct, builder) -> Task` | enveloped, **`Value` discarded** |
| `MSBYXMTYOOH<T>` | `(string desc, HttpMethod, route, ct, builder) -> Task<T>` | **enveloped with `Value`** |
| `LKVNIZZZQYH<T>` | same shape | **enveloped with `Value`** |
| `HIMXSOWXWZF<T>` | `-> Task<List<T>>` | enveloped list |

So the 2025 rule still holds verbatim on 2026: **a leading `friendlyActionDescription` argument is the
envelope tell.** The PUT passes one (`rdx` = `'change subroom permissions'` at `0x95ADC3A`, then
`r8` = verb, `r9` = route, plus a generic type token in `[rsp+0x30]`) → **enveloped**. The GET passes
the verb in `rdx` with no description → **bare**.

⚠️ Worth stating because the sibling route **one method over** did lose its envelope on 2026:
`HAGCWUSHAAP` (`rooms/{0}/leaderboards/{1}`, `0x95ADC90`) returns **non-generic `Task`** and calls the
**non-generic** `MSBYXMTYOOH` at `0x95AF8E0` — see [rooms-leaderboards](rooms-leaderboards-wire-shape.md).
Envelope tier is still per-helper on 2026, and adjacency proves nothing.

### Wire keys re-read from the 2026 formatters

`PhotonAccessTokenAndPermissionsDTO` → formatter **`Utf8Json.Formatters.RecNet.Rooms.PFTAHAPWHXR`**
`.ctor 0x8EC2790` (msig-confirmed). `____stringByteKeys` = the trailing run
`0x8EC299E`/`0x8EC29CA`/`0x8EC29EE` — **3 keys, unchanged**:

| # | key | CLR |
|---|---|---|
| 1 | `RoomInstanceId` | long |
| 2 | `PhotonAccessToken` | string |
| 3 | `Permissions` | `IReadOnlyList<RolePermissionDTO>` |

The 2025 note's unexplained "4th self-typed clone slot" is now readable: it is a **static** named
**`Offline`** at offset `0x0000` (`.cctor 0x95CD8F0`), a client-side offline fallback instance. **Not
a wire key.**

`RolePermissionDTO` → formatter **`NNTZVNBXPEW`** `.ctor 0x8ED1C30`, trailing run
`0x8ED1E9D`..`0x8ED1F41` — **5 keys, unchanged**: `Permission`, `Role`, `Override`, `Type`, `Value`.
The positional `.ctor` is now self-naming:
`.ctor(string permission, AccountRoleType role, bool override, RolePermissionType type, string value)`.

**Neither DTO has a post-deserialize hook** — `msig` shows only property accessors and constructors
on both, so no validation hook can fire here. The throws below are in the *applier*, not the parser.

### 🔴 NEW: the applier has TWO HARD THROWS — one bad entry reverts EVERY toggle

This is the most important 2026 finding and it **upgrades the 2025 diagnosis**. The 2025 note
described a missing `(Permission, Role)` pair as making one row "fall back to the default". That is
not what happens. `WXOXYAWQQII.JKEEZMLERNO(PhotonAccessTokenAndPermissionsDTO)` `0xA253210` — the
function that consumes the `photon_access_token` payload — **throws**:

```
0xa2533be  je   0xa25388c            ; Permissions (DTO field +0x20) is null
0xa25388c  ...
0xa2538a3  lea  rcx, -> "recNetRoomPermissionsDtos"
0xa2538b8  call System.ArgumentNullException$$.ctor      ; THROW #1

0xa2534b0  movzx edx, al              ; the Role byte
0xa2534b3  call <TryGetValue on [r15+0x40]>   ; client's role -> defaults table
0xa2534b8  test al, al
           ...
0xa253915  lea  rcx, -> "Invalid role. No defaults found!"
0xa25392a  call System.InvalidOperationException$$.ctor  ; THROW #2
```

| # | trigger | throw |
|---|---|---|
| 1 | `Permissions` is **`null`** | `ArgumentNullException("recNetRoomPermissionsDtos")` |
| 2 | a `Role` byte with **no entry in the client's role-defaults table** | `InvalidOperationException("Invalid role. No defaults found!")` |

**Consequence:** these throw out of the apply loop, so the array is applied **all-or-nothing**. A
single entry carrying a `Role` the client cannot resolve discards **every** permission in the payload,
not just that entry — so every toggle in the UI reverts, which looks exactly like a response-shape
problem on the PUT. `AccountRoleType` is sparse, so any byte outside
`{0, 1, 10, 20, 25, 30, 31, 255}` — `2`, `5`, `11`, `100` — hits throw #2.

**`"Invalid role. No defaults found!"` is a greppable client-log string.** Searching the client log
for it is the single cheapest way to separate this from an envelope fault.

Rules that follow:

- **`Permissions` must be `[]`, never `null`.**
- **Every `Role` byte must be an `AccountRoleType` member.** Validate server-side against the sparse
  set; do not pass through a role id from your own schema.
- The all-or-nothing behaviour means **one stale row poisons the whole payload**, so a server that
  grew a new role tier must not emit it until the client build knows it.

### `(Permission, Role)` is still the composite key

Re-confirmed on 2026 — the per-entry applier takes role and permission as **separate arguments**:

```
static bool WXOXYAWQQII.LGRKEJPRDSI(RecRoom.DataLayer.AccountRoleType role,
                                    RecRoom.DataLayer.RolePermission permission,
                                    RecNet.Rooms.RolePermissionDTO dto,
                                    <>c__DisplayClass51_0 env)
```

with role-scoped lookups `WKQPMDPNGJB(AccountRoleType)` and `SVQSLRWPLNR(AccountRoleType, bool)`.
**`Role: 0` (`None`) is still not a wildcard.** The 2025 confirmed root cause — a PUT for `Role: 10`
(`Host`) reverting because the read-back only carried `Role 0` and `Role 255` — is unchanged on 2026.

### 🔴 NEW: `RolePermission` 19 was RENAMED — `DEPRECATED_CAN_EDIT_CIRCUITS` → `CAN_EDIT_CIRCUITS`

`Permission` goes on the wire as the **member name**, so this is a breaking rename for any server that
persisted the 2025 string:

| value | 2025 name | 2026 name |
|---|---|---|
| 19 | `DEPRECATED_CAN_EDIT_CIRCUITS` | **`CAN_EDIT_CIRCUITS`** |

A stored `"DEPRECATED_CAN_EDIT_CIRCUITS"` no longer matches anything the 2026 client resolves, so that
row reverts. Every other one of the 42 members kept its name and value.

### The two-enum collision got worse

`py fieldfind.py CAN_SELF_REVIVE` now returns **one** typedef (`RecRoom.DataLayer.RolePermission`), so
that name is safe to disambiguate with. But `CAN_USE_DELETE_ALL_BUTTON` still returns **two**, and the
decoy grew to **74 members**:

| typedef | name | `CAN_USE_DELETE_ALL_BUTTON` | `CAN_EDIT_CIRCUITS` |
|---|---|---|---|
| #62218 | **`RecRoom.DataLayer.RolePermission`** | **14** | **19** |
| #11339 | `.RolePermission` (GameRole) | 84 | 88 |

⚠️ **The two enums now share the *short* name `RolePermission` as well as member names**, so a
name-based lookup that used to be unambiguous no longer is — always qualify with
`RecRoom.DataLayer.`. `CAN_EDIT_CIRCUITS` is a **new** overlap created by the rename above. The
decoy's new members are `CREATION_RESTRICTIONS_APPLY 85`, `CAN_CREATE_ROLE_ASSIGNMENT_CHIPS 86`,
`CAN_EDIT_CIRCUITS 88`.

### 🔎 Open: there is a push channel for this payload

`RecNet.NotificationDto_PhotonAccessTokenAndPermissionsDTO` (`.ctor 0x9517C00`) exists, which means
the permissions payload **can be delivered as a websocket push**, not only on the GET. This closes the
2025 note's open question ("…or refreshed by a push") in the affirmative — a server *can* push updated
permissions instead of relying on a re-fetch.

⚠️ **The channel id is NOT derived.** The type has 0 call sites (registered by the generic notification
machinery) and only a `.ctor`, and `regall.py` is Tier B so it does not run on the carved build. Until
the id is pinned, assume the client only learns new permissions from `GET photon_access_token`.
