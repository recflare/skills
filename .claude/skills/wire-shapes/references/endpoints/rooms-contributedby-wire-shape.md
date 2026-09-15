# Rooms contributedby wire shape

> Wire shape of GET rooms/contributedby/me on the Rooms service for recflare-2025 — a bare array of the 44-key Room DTO (MIBODHPEFHP), the canonical room object.

Derived **2026-08-17** from `C:\Games\recflare-2025` (build `20250718.01`) via
[recflare-2025-metadata-carve](../../../il2cpp-analysis/references/recflare-2025-metadata-carve.md).

`GET https://rooms.<host>/rooms/contributedby/me` — **GET**, no query params, no body. Auth-scoped
(`me` = the bearer token's account); the sibling `rooms/contributedby/{0}` takes an explicit id.
Client entry `OALMDGJKBJH.BENDBOJADID(CancellationToken)` at `0x7DF5970`, non-async.

Response is a **bare array** — `TResponse = List<MIBODHPEFHP>` (confirmed by resolving the
`LMKONLJOAEP` methodSpec generic inst 1019), no envelope. `MIBODHPEFHP` is **the canonical Room
DTO** reused across the whole client, so this shape is worth keeping: formatter `DDKHBAGIPKL`
ctor `0x776A440`, deserializer `0x7769440`, 44 keys in `____stringByteKeys` order —

`RoomId`, `Name`, `FriendlyName`, `Description`, `ImageName`, `WarningMask`, `CustomWarning`,
`CreatorAccountId`, `State`, `Accessibility`, `PublishState`, `SupportsLevelVoting`, `IsRRO`,
`SupportsScreens`, `SupportsWalkVR`, `SupportsTeleportVR`, `SupportsVRLow`, `SupportsQuest2`,
`SupportsMobile`, `SupportsJuniors`, `AgeRating`, `MinLevel`, `CreatedAt`, `PublishedAt`, `Stats`,
`RankingContext`, `IsDorm`, `MaxPlayerCalculationMode`, `MaxPlayers`, `PersistenceVersion`,
`CloningAllowed`, `DisableMicAutoMute`, `DisableRoomComments`, `EncryptVoiceChat`, `ToxmodEnabled`,
`LoadScreenLocked`, `UgcVersion`, `IsDeveloperOwned`, `IsJuniorCreated`, `CCU`, `IsRecRoomApproved`,
`ExcludeFromLists`, `UgcSubVersion`, `MinUgcSubVersion`.

`Stats` is a nested object (formatter `OFDOPKINAMJ` ctor `0x774C710`): `CheerCount`,
`FavoriteCount`, `VisitorCount`, `VisitCount`, all int.

Enums: `WarningMask` **flags** (None 0, Scary 1, Mature 2, FlashingLights 4, IntenseMotion 8,
Violence 16, Custom 32, Reports 64); `State` byte (Active 0, Junior_Pending 11,
Moderation_Pending 100, Moderation_Closed 101, Moderation_Banned 102, MarkedForDelete 255);
`Accessibility` byte (Private 0, Public 1, Unlisted 2); `PublishState` (None 0, Beta 1, Update 2);
`AgeRating` byte (None 0, AllAges 1, Age13Plus 2); `MaxPlayerCalculationMode` byte (AllSubrooms 0,
OnlyEntrySubrooms 1).

**`RoomId`, `CreatorAccountId`, `IsRRO`, `CloningAllowed` are CodeStage `Obscured*` types in the CLR
but plain JSON number/bool on the wire** — no formatter exists for the Obscured types and the
generated deserializer calls only primitive `JsonReader` methods, relying on the implicit
conversion. Do not try to emit the obscured struct's internal fields.

Class constants worth knowing: `ImageName` default is `"DefaultRoomImage.jpg"`, sentinel RoomId is
`-1`. `MIBODHPEFHP.CPOBHIECLEN` (`0xFEA4F0`) is `nop; ret` — no validation, and note it is an
*empty body at its own address*, not the shared `0xA60520` stub, so "not 0xA60520" alone does not
mean a DTO validates anything.

**Why:** Cpp2IL's property names and the metadata backing-field names disagree on this build (the
obfuscator did not keep the `<prop>k__BackingField` convention), so pair keys to members by
**position and type**, not by name. Verified here by the two `[DataMember(Name=...)]` attributes
landing exactly on keys 2 and 3, and by obfuscated names that recur across DTOs
(`ANKPNEKDDOB`=RoomId, `OJKBJEGFJLO`=Name, `MHEGLADOCHA`=EncryptVoiceChat — same as in
[matchmake-v2-room-wire-shape](matchmake-v2-room-wire-shape.md)'s RoomInstance).

## Same shape: `GET rooms/base`

Checked **2026-08-20**. `OALMDGJKBJH.BBJBCHFIDLN(CancellationToken)` at `0x7DF57D0` — **GET**
(`HttpMethod` statics `+0x08`), **no query params, no body**, returns `Task<List<MIBODHPEFHP>>`:
a **bare array of the identical canonical 44-key Room DTO**, no envelope (no
`GJAFHDAFBNE<MIBODHPEFHP>` / `KGOJLHJNIOD<MIBODHPEFHP>` formatter exists).

So `rooms/base` and `rooms/contributedby/me` are byte-for-byte the same response shape; only the
selection differs. Contrast `featuredrooms/current`, which returns the **3-key summary** instead
([featuredrooms-current-wire-shape](featuredrooms-current-wire-shape.md)) — on the same service.

## There is an EXTENDED room DTO too — `HGMJJMJDHLJ : MIBODHPEFHP`

Found **2026-08-20**. Two types derive from the 44-key base: `AOCOBMKGJMD` (7 extra fields) and
**`HGMJJMJDHLJ` (30 extra fields)**, formatter `KHGGMDBONNN` ctor `0x773F5A0`. Utf8Json emits the
derived members **first**, then the 44 base keys.

`HGMJJMJDHLJ`'s derived keys: `DataBlob`, `DataBlobHash`, `SubRooms`, `Roles`, `Tags`,
`LoadScreens`, `PromoImages`, `PromoExternalContent`, `LastRoomModerationState`,
`CurrentRoomModerationState`, `FlaggedAssets`, `ModeratorMessage`, `RoomBanDetails`,
`CurrentSnapshotId`, `LatestSnapshotId`, `StagedSnapshotId`, `CompatibleSnapshotId`,
`PublishStateAvailability`, `RestrictedCircuitsAllowListNames`.

**`rooms/base` and `rooms/contributedby/me` both deserialize the BASE type**, so every derived key
is dropped there. Sending them is harmless but pointless; they only matter on whichever endpoint
returns the extended type.

Keys seen on a real modern server that exist in **neither** DTO (silently dropped, client has no
idea about them): `ExcludeFromSearch`, `BecameRRStudioRoomAt`, `IsPlacePlay`, `AutoLocalizeRoom`,
`LocalizationContext`, `RankedEntityId`, `BoostCount`.

**Easy miss when hand-building a room payload:** `FriendlyName` (the human-readable display name,
a `[DataMember]` rename) and `CCU` (`int?`). Both are easy to omit because `Name` looks like the
title and `CCU` looks like a stat — but `Name` is the internal slug (`devin1s_MakerRoom_0601`) and
`FriendlyName` is what the UI shows.
