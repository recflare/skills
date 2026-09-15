# Curatedlists lookup and pagesource names

> GET curatedlists?creatorAccountId=&type=&name= returns ONE curated list (not an array), and the Discovery.PageSource.* names come from the GAEJAGAGEHB enum via Enum.ToString().

Derived **2026-08-19** from `C:\Games\recflare-2025` (build `20250718.01`) via
[recflare-2025-metadata-carve](../../../il2cpp-analysis/references/recflare-2025-metadata-carve.md).

## `GET curatedlists?creatorAccountId={int}&type={int}&name={string}`

**Returns a single object, not an array** — `Task<OOCDKDLBGOI>`. Client entry
`KCABHBCMOAE(int creatorAccountId, KJMOLELGPPF type, string name, CancellationToken)`, state machine
`OCHMOLJGPJJ$$MoveNext` (`0x7E3AD60`), **GET**, three query params added by the closure
`KJJLEMJOPIH.JNEJBCDBGEO` (`0x7E34D50`): `creatorAccountId` (I4), `type` (I4), `name` (string).
It is a unique-key lookup: (creator, type, name) → one list.

Body is the same bare 8-key DTO as [curatedlists-bulk-wire-shape](curatedlists-bulk-wire-shape.md): `ListId`, `CreatorAccountId`,
`Name`, `Description`, `ImageName`, `Type`, `ItemIds`, `CreatedAt`. `Type` values: Accounts 0,
Rooms 1, Inventions 2, CustomAvatarItems 3, PurchasableItems 4, Generic 5, ChipAndPort 6,
DiscoverySection 7, DiscoverySectionSubType 8.

## `name=RoomGenreTags&type=5` = the room-creation genre tag list (confirmed 2026-08-25)

Not a guess — the caller keeps its real name: **`RRUI.Data.RoomModel.FetchGenreTags()`**
(`0x286A8A0`) calls `IIINMGAEJDB.BDHNDGHJPOA("RoomGenreTags", type)` `0x7E27800` with
**`mov dl, 5`** (`Generic`), matching the observed query string exactly.

**`ItemIds` are the tag names as PLAIN STRINGS, used verbatim.** The continuation
`RoomModel.HOEDANPNBGC(OOCDKDLBGOI)` `0x286D500` is four instructions long:

```
tags = (list != null) ? list.ItemIds : null   ; [rdx+0x40] = MKAIKEPHBFL = ItemIds
this.<+0x468> = tags                          ; stored DIRECTLY, no parsing
UpdateTags()
```

⚠️ **`type=5` here does NOT mean unified store ids.** On `algorithmiclists` a `type=5` (Generic)
`Id` must be `0.<int>` / `1.<guid>` ([algorithmiclists-type5-unified-id](algorithmiclists-type5-unified-id.md)) — but that parsing lives
in the *store* consumer, not in the type value. This consumer never parses, so plain tag names are
correct here. The type field alone never tells you the id format; the consumer does.

`ItemIds` is `IReadOnlyList<string>`, so:

```json
{ "ListId": 1, "CreatorAccountId": 1, "Name": "RoomGenreTags", "Description": "",
  "ImageName": null, "Type": 5,
  "ItemIds": ["Adventure","Horror","Social","Sports","Roleplay"],
  "CreatedAt": "2026-01-01T00:00:00Z" }
```

**A null response is tolerated** (`test rdx, rdx ; je`) — tags become null, `UpdateTags()` still
runs, and room creation just offers no genre tags. It will not throw.

The strings are matched by **equality against the room's own tag values**:
`RoomModel.get_PrimaryGenreTag()` -> `string`, `get_SecondaryGenreTags()` -> `List<string>`,
`IsPopularTag(string)`, `TrySetPrimaryGenreTag(string)`. So this list must use exactly the same
spelling as the `Tags` you serve on the Room DTO ([rooms-contributedby-wire-shape](rooms-contributedby-wire-shape.md)).

`creatorAccountId=1` is supplied by the client (the facade adds it; `BDHNDGHJPOA` itself takes only
name+type). Key the lookup on all three as sent.

## Where `Discovery.PageSource.<X>` names come from

**`Discovery.PageSource.PlayExplore` is not a client literal** — it does not appear anywhere in the
carved binary, metadata, or literal table. It is a *server-side curated-list naming convention*.

The `<X>` half is the **page-source id**, and the client's set of them is the enum
`GAEJAGAGEHB`, converted by **`System.Enum.ToString()`** (confirmed: the call is in
`ANMLOMHCEDP$$MoveNext`, `0x7E40350`, the state machine behind
`NODJPHGACIC.DNLDAOPCOHJ(GAEJAGAGEHB, ct)`). Because it is `ToString()` and not string literals,
**most of these names never appear in `stringliteral.json`** — they live in metadata only, which is
why grepping the literal table for them mostly comes up empty.

The 17 ids: `WatchHome` 0, `PlayHighlight` 1, `CommunityBoard` 2, `MobileHome` 3, `StoreFeatured` 4,
`StoreClothing` 5, `StoreConsumables` 6, `PlayCategories` 7, `StoreInventions` 8, `TitleScreen` 9,
`PlayMenuTabs` 10, `OrientationStoreFeatured` 11, `AppNavPortalPanel` 12, `WWPanelList` 13,
`RecRoomPlusBenefits` 14, `RecCenterStorefront` 15, `RecCenterCommunityContent` 16 (`None` 999 is a
sentinel, never fetched).

There is also a **raw-string overload** `DNLDAOPCOHJ(string, ct)` used with ids outside the enum —
`"StoreCategories"` is one. So the enum is not the closed set. `PlayExplore` is in neither the enum
nor the literals on this build.

**Why:** page sources also chain — a section with `Source == "PageSource"` carries the next
page-source id in `SourceMetadata` (see [discovery-sections-pagesource-wire-shape](discovery-sections-pagesource-wire-shape.md)), so the live
set is discoverable by walking `sections/pagesource/{id}` from a known root rather than by reading
the binary.

**How to apply:** to enumerate what a server must define, take the 17 enum names, add
`StoreCategories`, then crawl each page's sections for `Source == "PageSource"` and follow
`SourceMetadata`.

## `PUT curatedlists/{name}/items/{itemId}/createlistifneeded`

Derived **2026-08-20**. **PUT** (`HttpMethod` statics `+0x28`), service 13 (Lists), **no request
body** (the state machine has no `ELKIBCPINAP`). Client entry
`FCKNCPNDBBM.GHNCHKLGKGC(string listName, string itemId, KJMOLELGPPF type,
KLKIFENPGNG accessibility, CancellationToken)` at `0x7E227E0`, state machine
`IMCOMMPAEDL$$MoveNext` (`0x7E2B090`). Telemetry label `"add item to list"`.

The path is **composed from three literals** — `"curatedlists/" + listName + "/items/" + itemId +
"/createlistifneeded"` — so grepping for the full path finds nothing; `/createlistifneeded` exists
alone at `0xD24DC38`. `{name}` is the list **name**, not an id, same key space as the
`curatedlists?name=` lookup above.

Two query params, both numeric enums, added via `ELHKHFJEHLM`:
`type` (`KJMOLELGPPF`) and `accessibility` (`KLKIFENPGNG` — Private 0, Public 1, Unlisted 2).

**Response is a bare `OOCDKDLBGOI`** — awaiter is `TaskAwaiter<OOCDKDLBGOI>`, no envelope. Same
8-key curated-list DTO as [curatedlists-bulk-wire-shape](curatedlists-bulk-wire-shape.md), and its `CPOBHIECLEN` is the `0xA60520`
no-op.

**Why:** it is an upsert — add `itemId` to the list named `listName`, creating the list with the
given `type`/`accessibility` if it does not exist. Return the resulting list either way, with
`ItemIds` already including the new item; the client uses the response as the list's new state.
