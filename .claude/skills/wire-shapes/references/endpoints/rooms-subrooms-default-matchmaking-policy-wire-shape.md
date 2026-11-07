# `PUT rooms/{id}/subrooms/{id}/default_matchmaking_policy` wire shape (2026)

> `PUT rooms.<host>/rooms/{roomId}/subrooms/{subRoomId}/default_matchmaking_policy` (svc **16 Rooms**)
> is **ENVELOPED** — `{Value: <63-key RoomDetailsDTO>, Success, Error, error_id}`.
> Request carries **one** param, `policy`, and because the verb is **PUT** that param is an
> **`application/x-www-form-urlencoded` body**, not a query string.
> The enum is the 3-member `RecNet.RoomInstanceMatchmakingPolicy` (`Default 0`, `Avoid 1`,
> `Ignore 2`) — the **persisted subroom default** behind the live-instance override
> [matchmaking-roominstance-matchpolicy](matchmaking-roominstance-matchpolicy-wire-shape.md).

Derived **2026-11-02** from build `20260323.14` via the 2026 carve
(`C:\Games\recnet-patcher\il2cpp-2026\`).

## The route

Path literal **`rooms/{0}/subrooms/{1}/default_matchmaking_policy`** = slot **`0xFD6B1F0`**, built
with `String.Format` at `0x95AA7E1`. Only **one** method references it:

```
RecNet.Rooms.DFMBMRNABHU$$ATYSFIRJPFS   0x95AA6A0   (body runs to ~0x95AA890)

Task<RecNet.Rooms.RoomDetailsDTO>
    ATYSFIRJPFS(long roomId, long subRoomId, RecNet.RoomInstanceMatchmakingPolicy policy,
                CancellationToken ct)
```

Same `DFMBMRNABHU` Rooms facade as `rooms/hot`, `photon_access_token` and the permissions PUTs
([rooms-subrooms-permissions](rooms-subrooms-permissions-wire-shape.md)), hence svc **16** and the
`rooms.<host>` subdomain.

⚠️ **`fstart.py` under-reports this one**: it returns `(0x95AA6A0, 0x95AA74F)` while the second
literal reference sits at `0x95AA7D3`. The next method (`rooms/{0}/subrooms/{1}/maxplayers`) starts
at `0x95AA898` — bound the window there, not at the `fstart` end.

| fact | evidence |
|---|---|
| verb **PUT** | `0x95AA79F mov rcx,[rax+0x20]` → `0x95AA7A3 mov rsi,[rcx+0x28]` — `+0x28` = `Put` |
| description | `'change default matchmaking policy'` (`0x95AA710` / `0x95AA817`) |
| send helper | `DFMBMRNABHU::MSBYXMTYOOH` **generic**, `<method inst #1359>` = `RecNet.Rooms.RoomDetailsDTO`, called at `0x95AA83B` |
| param closure | `.WVFYLUZMPCM::PTSONUDXKFM` `0x95C64F0`, allocated at `0x95AA737`, captures `policy` into `[rbp+0x10]` at `0x95AA745` |

**0 direct callers** (`callxref 0x95AA6A0`) — the whole facade is UJect-injected and
interface-dispatched, as with every other `DFMBMRNABHU` route. The enum's `TypeInfo` slot
(`0xFCC9988`) also has **only** the two boxing refs inside the closure, so there is no static path
to the UI that sets it; everywhere else the value travels as a plain `int`.

## Request — one form param

`slots2025.py` over the closure `0x95C64F0`–`0x95C656B` shows exactly **one**
`RGBOOBRDHEB$$NJPEKLKCVCG` (`0x95C6555`) and **zero** `FZNGWUAGAIN` (JSON body) / `YHPVSAVMRFS`
(raw body). The param name is the literal **`'policy'`**.

```
PUT /rooms/1162/subrooms/1307/default_matchmaking_policy
Content-Type: application/x-www-form-urlencoded

policy=Avoid
```

Bind it with `[FromForm]`. Non-GET verbs put `NJPEKLKCVCG` params in a form body — see
[elhkhfjehlm-verb-dependent-params](../conventions/elhkhfjehlm-verb-dependent-params.md).

⚠️ **Accept both the name and the number.** The enum is **boxed** at `0x95C653B` (the value-box
helper fires immediately before the `'policy'` literal), so `NJPEKLKCVCG(string, object)` stringifies
it — `Enum.ToString()` on an `int`-backed enum gives the **member name**. The final conversion is
behind a virtual dispatch that was not resolved statically, so parse `policy`
case-insensitively as an enum name **or** as an integer. Identical caveat to
[matchmaking-roominstance-matchpolicy](matchmaking-roominstance-matchpolicy-wire-shape.md).

### `RecNet.RoomInstanceMatchmakingPolicy` (typedef #22475, `int`)

| val | name | meaning |
|---|---|---|
| 0 | `Default` | normal matchmaking — the subroom accepts new players |
| 1 | `Avoid` | deprioritise — send players elsewhere when possible |
| 2 | `Ignore` | exclude from matchmaking entirely |

Values are **unchanged from 2025**, where the same enum was `.FDLHIHKECMA`. It is also key #15
(`MatchmakingPolicy`) of the `RoomInstance` DTO every matchmake route returns
([matchmake-v2-room](matchmake-v2-room-wire-shape.md)), and the type of the SubRoom DTO's
default-policy field. **This route writes the persisted default; `PUT roominstance/{id}/matchpolicy`
overrides it for one live instance.**

## Response — ENVELOPED

`T` = `RecNet.Rooms.RoomDetailsDTO`, and the envelope oracle
([2026-send-helper-tiers](../conventions/2026-send-helper-tiers.md)) returns **1 hit**:

```
py mfind.py RecNetResultObject_RoomDetails
  -> 0x953A5E0  RecNet.RecNetResultObject_RoomDetailsDTO$$.ctor
```

so a concrete `RecNetResultObject<RoomDetailsDTO>` is instantiated and this route is enveloped,
exactly like its facade sibling `PUT rooms/{id}/subrooms/{id}/permissions`, which uses the same
`MSBYXMTYOOH<RoomDetailsDTO>` helper.

```json
{ "Value": { "...": "the 63-key RoomDetailsDTO below" },
  "Success": true,
  "Error": null,
  "error_id": null }
```

Four keys, in that order, `error_id` lowercase with the underscore.

Return the room as it now stands — the same payload `GET rooms/{roomId}` serves
([rooms-room-by-id](rooms-room-by-id-wire-shape.md)) — with the subroom's default policy updated.

## ⚠️ The 2026 `RoomDetailsDTO` is NOT key-identical to the 2025 Room DTO

**Corrects** [rooms-subrooms-permissions](rooms-subrooms-permissions-wire-shape.md)'s "2026: shapes
UNCHANGED". The count is still 63, but **one key was removed and another added**, so a server
replaying its 2025 room payload is now sending one dead key and omitting one live one.

Formatter **`Utf8Json.Formatters.RecNet.Rooms.XZXZTXGVWHY`** `.ctor` **`0x8EE19C0`**
(`fstart` → `0x8EE464C`), `msig`-confirmed:

```
void                        Serialize(JsonWriter, RecNet.Rooms.RoomDetailsDTO, FSNHROPLCPN)
RecNet.Rooms.RoomDetailsDTO Deserialize(JsonReader, FSNHROPLCPN)
```

`____stringByteKeys` run = `0x8EE3B12`..`0x8EE45F6`, **63 keys**, derived-first ordering:

```
 1 DataBlob                  2 DataBlobHash              3 SubRooms
 4 Roles                     5 Tags                      6 LoadScreens
 7 PromoImages               8 PromoExternalContent      9 LastRoomModerationState
10 CurrentRoomModerationState  11 FlaggedAssets          12 ModeratorMessage
13 RoomBanDetails           14 CurrentSnapshotId        15 LatestSnapshotId
16 StagedSnapshotId         17 CompatibleSnapshotId     18 PublishStateAvailability
19 RestrictedCircuitsAllowListNames
20 RoomId                   21 Name                     22 FriendlyName
23 Description              24 ImageName                25 WarningMask
26 CustomWarning            27 CreatorAccountId         28 State
29 Accessibility            30 PublishState             31 SupportsLevelVoting
32 IsRRO                    33 SupportsScreens          34 SupportsWalkVR
35 SupportsTeleportVR       36 SupportsVRLow            37 SupportsQuest2
38 SupportsMobile           39 SupportsJuniors          40 AgeRating
41 MinLevel                 42 CreatedAt                43 PublishedAt
44 Stats                    45 RankingContext           46 IsDorm
47 MaxPlayerCalculationMode 48 MaxPlayers               49 PersistenceVersion
50 CloningAllowed           51 DisableMicAutoMute       52 DisableRoomComments
53 EncryptVoiceChat         54 LoadScreenLocked         55 UgcVersion
56 IsDeveloperOwned         57 IsJuniorCreated          58 CCU
59 IsRecRoomApproved        60 ExcludeFromLists         61 UgcSubVersion
62 MinUgcSubVersion         63 BoostCount
```

| delta vs `20250718.01` | |
|---|---|
| **`ToxmodEnabled` is GONE** | key #54 on 2025. **0 references** in the 2026 formatter (neither `____keyMapping` nor `____stringByteKeys`), and the whole binary holds only **one** `toxmod` literal, elsewhere. Sending it is harmless (unknown keys are dropped) but it reads nothing. |
| **`BoostCount` is NEW** | appended as the **last** key, after `MinUgcSubVersion`. Ties this DTO to [rooms-boosts-count](rooms-boosts-count-wire-shapes.md). |

Everything else keeps its 2025 name, position and order.

### `[DataMember]` renames on the snapshot ids

`ftypes.py RoomDetailsDTO` gives **31** fields; four of them are renamed on the wire, which is why a
name-based mapping fails here:

| CLR field | wire key | type |
|---|---|---|
| `CurrentRoomLoadSnapshotId` | **`CurrentSnapshotId`** | `Guid?` |
| `LatestRoomLoadSnapshotId` | **`LatestSnapshotId`** | `Guid?` |
| `StagedRoomLoadSnapshotId` | **`StagedSnapshotId`** | `Guid?` |
| `CompatibleRoomLoadSnapshotId` | **`CompatibleSnapshotId`** | `Guid?` |

All four are `Nullable<Guid>`, so `null` is legal.

### `UnlistedSubroom` has a backing field and NO key

`<UnlistedSubroom>k__BackingField` (`RecNet.Rooms.SubRoomDTO`) is declared on `RoomDetailsDTO` but
appears **nowhere** in the formatter (0 refs across both runs). It is `[IgnoreDataMember]` /
client-populated — **do not add an `UnlistedSubroom` key expecting it to land**; it will be dropped
silently. The unlisted subroom has to arrive inside the `SubRooms` array like any other.

Typed fields `RoomDetailsDTO` declares (the derived-class half of the key run):
`DataBlob`/`DataBlobHash` string, `SubRooms` `IReadOnlyList<SubRoomDTO>`, `Roles`
`IReadOnlyList<AccountRoleDTO>`, `Tags` `IReadOnlyList<TagDTO>`, `LoadScreens`
`IReadOnlyList<LoadScreenDTO>`, `PromoImages` `IReadOnlyList<string>`, `PromoExternalContent`
`IReadOnlyList<ExternalContentReferenceDTO>`, `Last`/`CurrentRoomModerationState`
`SubRoomDataSaveModerationState`, `FlaggedAssets` `IReadOnlyList<string>`, `ModeratorMessage` string,
`RoomBanDetails` `RoomBanDetailsDTO`, `PublishStateAvailability`
`RoomPublishStateAvailabilityDTO`, `RestrictedCircuitsAllowListNames` `IReadOnlyList<string>`. The
remaining 11 fields are obfuscated base-class members, four of them
`IReadOnlyList<ObscuredInt>` / `ObscuredInt?` — plain numbers on the wire.

## Traps

- **A bare `RoomDetailsDTO` fails.** The helper never unwraps anything, so the body must be the
  four-key envelope. A bare room object throws `JsonParsingException` in the
  `RecNetResultObject<RoomDetailsDTO>` formatter, surfaced as
  `RecNetMalformedResponseException: Malformed Response: '{…}'`
  ([ioncmjiacfi-malformed-response](../conventions/ioncmjiacfi-malformed-response.md)).
- **`204`/empty is not accepted.** This is `Task<T>`, not a non-generic `Task` — there is a
  deserialize target. An empty body or a literal `null` raises `Response was empty`.
- `Success: false` with a 200 faults the task (the envelope is checked); a non-2xx raises
  `RecNetWebException: HTTP Error {code}`.
- **Whether `Value` is consumed is not pinned.** The facade sibling `PUT …/permissions` is fronted by
  an interface method returning a non-generic `Task`, so its `Value` is parsed and dropped. The
  interface wrapper for *this* route could not be located statically (0 callers, and the enum's
  `TypeInfo` is referenced only in the closure), so assume the room **is** read and echo a real one.

**How to apply:** take the same room payload `GET rooms/{roomId}` already serves for this room,
update the subroom's default matchmaking policy, wrap it in `{Value, Success, Error, error_id}`, and
return 200. Accept `policy` from the form body as either `Default`/`Avoid`/`Ignore` or `0`/`1`/`2`.
