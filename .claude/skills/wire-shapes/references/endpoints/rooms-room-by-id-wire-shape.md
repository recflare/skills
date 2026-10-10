# Rooms rooms/{id}?include= wire shape (the Room DTO)

> GET rooms/{roomId}?include={mask} (svc 16 Rooms) returns the BARE 63-key Room DTO, and its **first two keys are `DataBlob` and `DataBlobHash`** — the room-level blob, i.e. the `FileType=6` RoomMetadata upload that carries cloud-variable definitions. Omit `DataBlob` and the client never fetches that blob, so saved cloud variables load as **"Unsaved"** with no error anywhere.

Derived **2026-10-03** from build `20250718.01`, while tracing why cloud variables stayed "Unsaved".

`GET https://rooms.<host>/rooms/{roomId}?include={mask}` — service **16 = Rooms**, facade
`OALMDGJKBJH`. Path is `String.Format("rooms/{0}", roomId)`, literal slot `0xD19C598`.

Client entry **`OALMDGJKBJH.AFKPOMIFDFD`** `0x7DF4DB0`, send **`OALMDGJKBJH.NDBMFFLDBBK<T>`** — the
facade's description-less (**bare**) helper, so **no envelope** — generic inst **#1188** =
**`.HGMJJMJDHLJ`**.

Two other methods share the `rooms/{0}` literal: `CHCIJIOCOPK` `0x7DF6410` (carries `'delete room'`,
so **enveloped**, `LMKONLJOAEP<inst 2723>`) and `IIDMNPMDLBC` `0x7DFA940` (`NDBMFFLDBBK<inst 1254>`).
Read which helper the entry method calls, every time.

## ⚠️ `DataBlob` is the room-metadata reference

The `____stringByteKeys` run begins at `0x774334A`:

| # | key |
|---|---|
| **1** | **`DataBlob`** |
| **2** | **`DataBlobHash`** |
| 3 | `SubRooms` |
| 4 | `Roles` |

This closes the room-save loop that [storage-upload](storage-upload-wire-shape.md) and
[rooms-subrooms-data](rooms-subrooms-data-wire-shape.md) leave open:

1. `POST upload` with `FileType=6` (**RoomMetadata** — cloud-variable definitions, room-level config)
   → `{Filename, Hash, OwnershipProof}`.
2. `POST rooms/{id}/subrooms/{id}/data` sends that as **`RoomData: {Filename, Hash, …}`**.
3. **`GET rooms/{id}?include=` returns it back as `DataBlob` / `DataBlobHash`.**

The names differ at every hop — `Filename` → `RoomData.Filename` → `DataBlob` — which is why
searching for `RoomDataFilename` finds only the unrelated Studio remote-run DTO `.CMPBBIDGFAK`, and
why the read-back path looked absent.

**Failure mode:** a server that persists `RoomData.Filename` but omits `DataBlob` from this response
leaves the client with no metadata blob to fetch. It then shows only the in-memory cloud variables,
all marked unsaved, **with no log line, no exception and no extra HTTP request** — the missing fetch
is a *consequence* of the missing key, so it will not appear in a capture.

The lighter Room formatter (`0x7747270`) carries `DataBlob` but **no `DataBlobHash`** in its run, so
the hash is optional on at least one variant.

## ⚠️ `RoomDataBlob` is not a wire key — confirmed from a live server payload

A self-hosted server was returning the room-metadata filename as **`RoomDataBlob` on each SubRoom**:

```json
"SubRooms": [ { "RoomDataBlob": "2026-10-04/008e8a3d-…", "CurrentSave": { "DataBlob": "…" } } ]
```

**`RoomDataBlob` does not exist as a string literal anywhere in build 20250718.01**, so Utf8Json drops
it silently. Two faults at once: wrong key *and* wrong level — **cloud data variables are room-level**
(user-confirmed 2026-10-03), so the reference belongs at the **top level of the Room object as
`DataBlob`**, which is key #1 of this DTO.

`DataBlob` and `SubRooms` sit in the **same** `____stringByteKeys` run (`0x774334A` and `0x77433EC`),
so one type carries both — the room-level blob is not a SubRoom member.

The SubRoom's own `CurrentSave.DataBlob` is a *different* value: the `FileType=1` SubRoomSave geometry
blob. Both keys are spelled `DataBlob`; only the nesting distinguishes them.

### Other keys in that payload the client drops

`ExcludeFromSearch`, `BecameRRStudioRoomAt`, `IsPlacePlay`, `AutoLocalizeRoom`,
`LocalizationContext`, `RankedEntityId`, `BoostCount` — none exist as literals in this build. Harmless
(unknown keys are dropped) but they indicate the server is modelled on a newer API, the same way the
inventions payload carried `ReferencedUnityAssetIds` and `CurrentVersion.HasBetaContent`.

Keys the DTO declares that the payload omitted: `DataBlob`, `DataBlobHash`, `FriendlyName`,
`LastRoomModerationState`, `CurrentRoomModerationState`, `FlaggedAssets`, `ModeratorMessage`,
`RoomBanDetails`, `LatestSnapshotId`, `StagedSnapshotId`, `CompatibleSnapshotId`,
`PublishStateAvailability`.

## Response — 63 keys, bare

Formatter `.ctor` **`0x773F5A0`** (+0x5590), run `0x774334A`..`0x77446AC`. Derived-first ordering, so
keys 1–19 are the most-derived members — and these are exactly the ones an `include` bitmask would
gate:

```
 1 DataBlob                  2 DataBlobHash              3 SubRooms
 4 Roles                     5 Tags                      6 LoadScreens
 7 PromoImages               8 PromoExternalContent      9 LastRoomModerationState
10 CurrentRoomModerationState  11 FlaggedAssets          12 ModeratorMessage
13 RoomBanDetails           14 CurrentSnapshotId        15 LatestSnapshotId
16 StagedSnapshotId         17 CompatibleSnapshotId     18 PublishStateAvailability
19 RestrictedCircuitsAllowListNames
```

then the base Room:

```
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
53 EncryptVoiceChat         54 ToxmodEnabled            55 LoadScreenLocked
56 UgcVersion               57 IsDeveloperOwned         58 IsJuniorCreated
59 CCU                      60 IsRecRoomApproved        61 ExcludeFromLists
62 UgcSubVersion            63 MinUgcSubVersion
```

`.HGMJJMJDHLJ` declares **30** fields; the run is **63** keys, so this is a subclass chain and the
remaining keys come from its bases. **Per-key CLR types are not pinned** — only the key names and
order were derived.

✅ **Formatter identification CONFIRMED 2026-10-06.** `0x773F5A0` was originally picked by
intersecting the `SubRooms` and `RoomId` key xrefs, which left two candidates (`0x773F5A0` and
`0x7747270`) and no way to choose. **`py msig.py <FormatterClass>` settles it directly** — a
generated Utf8Json formatter's `Serialize`/`Deserialize` pair names the concrete DTO in its
signature:

```
py msig.py KHGGMDBONNN   ->  void FBGBLPHHDGN(.BDLOEIPNGEL, .HGMJJMJDHLJ, .COIBJKJDIKH)
                             .HGMJJMJDHLJ LABNBGADOBH(.ANAMOLLPKLG, .COIBJKJDIKH)
py msig.py KNMBKOFNJCK   ->  ... .AOCOBMKGJMD ...
```

So `KHGGMDBONNN` `.ctor 0x773F5A0` is the formatter for `.HGMJJMJDHLJ` (= inst #1188) and the other
candidate `KNMBKOFNJCK` `.ctor 0x7747270` belongs to **`.AOCOBMKGJMD`**, a different Room-shaped DTO
that additionally carries a `Permissions` key.

**Generalisable — prefer this over key-literal intersection.** The resolver-index indirection
(`PGHNJGDNFGC..cctor` mapping type → integer) blocks `typeslots.py`→`mxref.py` in the formatter →
type direction, but the formatter class's own metadata signature carries `T` unobfuscated-as-to-shape.
Once you have a candidate formatter class name, `msig.py` on it is a one-call confirmation.

## `SubRooms[]` — the element shape (`.PNAGCNAKDLL`), 12 keys

Derived **2026-10-07**. Formatter **`MJDIFJOAEJM` `.ctor 0x7731450`** (+0xFE0),
`____stringByteKeys` run `0x7731FA4`..`0x77322E9`:

| # | key | CLR | off |
|---|---|---|---|
| 1 | `SubRoomId` | long | 0x10 |
| 2 | `RoomId` | long | 0x18 |
| 3 | `UnitySceneId` | enum `.CFCLEMKANPO` | 0x28 |
| 4 | `Name` | string | 0x38 |
| 5 | **`CurrentSave`** | **`.GCLKKDPHAON`** (the 15-key save record) | 0x40 |
| 6 | `LastModeratedSaveModerationState` | `.CCJNDAADAJO` byte | 0x48 |
| 7 | `IsSandbox` | bool | 0x49 |
| 8 | `MaxPlayers` | int | 0x4c |
| 9 | `Accessibility` | enum `.KHLCBNKACFL` | 0x50 |
| 10 | `DefaultMatchmakingPolicy` | enum `.FDLHIHKECMA` | 0x54 |
| 11 | `ShouldAutoStageSaves` | bool | 0x58 |
| 12 | `StagedSubRoomDataSaveId` | `long?` | 0x60 |

`UnitySceneId` is the scene-location enum — GUID table in `SCENES.md`. `DefaultMatchmakingPolicy`
is the same 3-member enum the live override uses
([matchmaking-roominstance-matchpolicy](matchmaking-roominstance-matchpolicy-wire-shape.md)).

The type declares **14** backing fields; the two strings at `0x20` and `0x30` have **no wire key**
(`[IgnoreDataMember]`), which is why 14 fields give 12 keys.

### ⚠️ `SubRooms[].CurrentSave` is the ONLY wire path for the room-load `OMVersion` gate

**No route returns a bare `.PNAGCNAKDLL`** — a scan of every generic instantiation finds it as no
send's `T`. It reaches the client **only nested here**, inside this route's `SubRooms` array. And
`RecNet.Matchmaking.FINBJKEJMJL()` hands exactly this object to the room-load check, which reads
`CurrentSave.OMVersion` ([rooms-subrooms-data](rooms-subrooms-data-wire-shape.md)).

So the `OMVersion` that can refuse a room load is **`SubRooms[].CurrentSave.OMVersion` in this
response** — *not* the `OMVersion` on `GET .../saves/{saveId}`
([subroom-save-by-id](subroom-save-by-id-wire-shape.md)) and *not* the one on
`saves/no_unity_assets`. Those two carry the same key name on the same DTO, so fixing it there looks
right and changes nothing. Diagnosed on a live server 2026-10-07, where `saves/{saveId}` was
returning `OMVersion: 138` and the room still refused to load.

## The `include` mask

The query param is the literal `'include'` (slot `0xD1F0F38`), built in
`GPOFACHPKIG.JFAHIFEIDPE` `0x7DEC310` / `HIOBANMMNAO.JFAHIFEIDPE` `0x7DEC5F0` (those classes also
carry `name`, `ugcSubVersion1`, `ugcSubVersion2`).

A captured room load sends **`include=767277`** = `0xBB52D`, bits
`{0,2,3,5,8,10,12,13,15,16,17,19}`. **The flags enum was not located**, so the bit→key mapping is
unresolved. Safest server behaviour is to **ignore `include` and return every key** — the client
drops unknown keys silently, and a missing one it wanted is the failure mode above.

## How this was found

Not by searching for the obvious name. `RoomMetadata`, `MetadataFilename`, `RoomDataSave` and
`CloudVariables` do not exist as wire keys anywhere in the build, and `RoomDataFilename` resolves only
to the Studio DTO. The route was found by **grepping the candidate Room formatters' key runs for
`blob|filename|hash|data`** after the semantic names all came up empty.

Generalisable: when a value is written under one name and read under another, search the *shape*
(`blob`, `hash`, `filename`) rather than the *concept* (`metadata`, `cloudvariable`).
