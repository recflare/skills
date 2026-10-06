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

## Related

The `Roles` key (#4) of the Room DTO is the read-back side of this write. Its element shape was not
derived; the in-client role object is `.JNGHOMKNFPP`
(`{PHBPGMMKBJJ roleType, Action<OGKGADHHDKM>, string name, bool}`), held in
`.DFBNLBFNPDP` as `Dictionary<PHBPGMMKBJJ, JNGHOMKNFPP>` plus an `OGKGADHHDKM[]`. Sibling write
routes on the same facade and literal family: `rooms/{0}/subrooms/{1}/modify`,
`.../accessibility`, `.../name`, `.../maxplayers`, `.../move`, `.../clone`,
`.../default_matchmaking_policy`, `.../autostage`, `.../publish_save`.
