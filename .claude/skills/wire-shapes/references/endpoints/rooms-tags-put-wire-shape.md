# Rooms tags put wire shape

> PUT rooms/{id}/tags (svc 16 Rooms) takes autoTag/tag/primaryGenreTag as QUERY params with no body, and returns the ENVELOPED extended Room object — 44 base Room keys + 19 extras, 63 in total.

Derived **2026-08-25** from build `20250718.01`.

`PUT https://rooms.<host>/rooms/{roomId}/tags` — service **16 = Rooms**, verb **PUT**
(`HttpMethod` statics `+0x28`). Client entry
`OALMDGJKBJH.OOBMPJKLGJH(long roomId, IReadOnlyList<string> autoTag, IReadOnlyList<string> tag, string primaryGenreTag, ct)`
`0x7DFEEA0`, friendly description `'change room tags'`.

**Request: three QUERY params, no body.** The configure lambda `NKODHNCKOFB.GOCIPBJHAFC` `0x7DF4900`
adds them all via `MGPBDIAGCFD.ELHKHFJEHLM`: **`autoTag`** (repeated, list), **`tag`** (repeated,
list), **`primaryGenreTag`** (string). `primaryGenreTag` is the value picked from the
`RoomGenreTags` curated list ([curatedlists-lookup-and-pagesource-names](curatedlists-lookup-and-pagesource-names.md)).

## Response: ENVELOPED, and it is the whole room

Send is `PJPLCMBOAFB<HGMJJMJDHLJ>` — one of the room facade's **description-carrying** helpers, so it
awaits `KGOJLHJNIOD<T>` ([rooms-isbanned-wire-shape](rooms-isbanned-wire-shape.md) has the envelope hierarchy):

```json
{ "Value": { …the object below… }, "Success": true, "Error": null, "error_id": null }
```

**`HGMJJMJDHLJ : MIBODHPEFHP`** — a subclass of the canonical 44-key Room DTO
([rooms-contributedby-wire-shape](rooms-contributedby-wire-shape.md)). Formatter `KHGGMDBONNN` `.ctor 0x773F5A0` (a 0x5590-byte ctor);
trailing `____stringByteKeys` run at `0x774334A..0x77446AC`, **63 keys**, derived-first:

**19 derived keys (the delta over the plain Room DTO), in order:**
`DataBlob`, `DataBlobHash`, `SubRooms`, `Roles`, `Tags`, `LoadScreens`, `PromoImages`,
`PromoExternalContent`, `LastRoomModerationState`, `CurrentRoomModerationState`, `FlaggedAssets`,
`ModeratorMessage`, `RoomBanDetails`, `CurrentSnapshotId`, `LatestSnapshotId`, `StagedSnapshotId`,
`CompatibleSnapshotId`, `PublishStateAvailability`, `RestrictedCircuitsAllowListNames`

**then the 44 base Room keys**, starting `RoomId`, `Name`, `FriendlyName`, `Description`,
`ImageName`, … and ending `CCU`, `IsRecRoomApproved`, `ExcludeFromLists`, `UgcSubVersion`,
`MinUgcSubVersion`.

`HGMJJMJDHLJ` declares **29** instance fields but only **19** are serialized — the other 10
(`BECLHCFPHIK`, `OEPFNAPLCHH`, `MNBDHHNMHDP`, `JNMFDIPBAHI`, `MEEDGMEKFFC`, `MANJFHBLOLG`,
`BNFNJCHIEJF`, `EDGOINMHKFO`, `CAPDDDCHOFD`, `LFACABCLFDI`) are plain fields, not
`<X>k__BackingField` auto-properties, and never reach the wire. **The auto-property/plain-field split
is a reliable way to predict which members a formatter will emit** without reading the formatter.

**How to apply:** a tags PUT has to echo the **entire updated room**, not just the tags — the same
object `GET rooms/{id}` style routes return, plus the 19 extras. `Success: false` raises
[llcldppagij-envelope-failure-exception](../conventions/llcldppagij-envelope-failure-exception.md). `OOBMPJKLGJH` has **no direct callers** in the binary
(reached via delegate), so the consequence of a null `Value` was not traced — echo the room.

⚠️ **CORRECTION 2026-09-02:** where this note says the parameters are **query params**, they
are actually an **`application/x-www-form-urlencoded` request body** — `ELHKHFJEHLM` routes params
to the query string only for GET. See [elhkhfjehlm-verb-dependent-params](../conventions/elhkhfjehlm-verb-dependent-params.md). Response shape
unaffected.
