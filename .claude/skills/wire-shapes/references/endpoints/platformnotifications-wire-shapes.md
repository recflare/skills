# Platformnotifications wire shapes

> Wire shapes of GET/PUT preferences and GET config/categories on the PlatformNotifications service (svc 17) for recflare-2025 — config/categories is a PAGED {Results,TotalResults} object (NOT a bare array), preferences is a bare MUTED deny-list.

Derived **2026-08-18** from `C:\Games\recflare-2025` (build `20250718.01`) via
[recflare-2025-metadata-carve](../../../il2cpp-analysis/references/recflare-2025-metadata-carve.md). All three live on `BJPFPDGICGB`, service **17 =
PlatformNotifications** (`mov r8d, 0x11`), host `platformnotifications.<domain>`. No query params.

**`GET /preferences`** (`MCNACMNPFLC`, `0x7D4F9D0`) → bare `PlatformNotificationPreferencesDTO`,
formatter `LNIBJMLFOFJ` ctor `0x7E69270`, exactly one key:

```json
{ "MutedCategories": [3, 9] }
```

`IReadOnlyList<ALGAOCCMGKH>` of **numeric** enum values. Note the polarity — it is a **mute
deny-list, not an enabled list**. `{"MutedCategories": []}` = everything on, which is the correct
default response, not `null`.

**`PUT /preferences`** (`OPEKFKDAIFP`, `0x7D4FF30`) — the client `.ToList()`s the categories, wraps
them in the *same* `PlatformNotificationPreferencesDTO`, and sends it as the JSON body via
`ELKIBCPINAP`. Returns the non-generic promise `JCFICNGFDLA`, so **no response body is deserialized
at all** — 204 or anything else is fine.

**`GET /config/categories`** (`FPGCMHCMIME`, `0x7D4EDF0`) — **CORRECTED 2026-08-24: this is a
PAGED OBJECT, not a bare array.** An earlier version of this note said "bare array"; sending one
gets `IONCMJIACFI: Malformed Response` ([ioncmjiacfi-malformed-response](../conventions/ioncmjiacfi-malformed-response.md)) because Utf8Json hits
`[` where it expects `{`.

The send generic is `HPBKMCLEANE<BJACLIGEIFP>`, and
`BJACLIGEIFP : FGLBCGIODIE<PlatformNotificationCategoryConfigDTO>` — the reusable paged base from
[subroom-saves-list-wire-shape](subroom-saves-list-wire-shape.md). Formatter `JODOKKNFJDB` `.ctor 0x7E65DF0`, keys **`Results`**
(`IReadOnlyList<T>`) and **`TotalResults`** (long):

```json
{ "Results": [ { "CategoryId": 2, "Importance": 0, "Name": "Friends",
                 "Description": "...", "IsMuteable": true } ], "TotalResults": 1 }
```

Element `PlatformNotificationCategoryConfigDTO`, formatter `MMOPAAAFFCO` ctor `0x7E6B2F0`, 5 keys:
`CategoryId` enum 0x10, `Importance` enum 0x14, `Name` string 0x18, `Description` string 0x20,
`IsMuteable` bool 0x28.

`BJACLIGEIFP.CPOBHIECLEN` (`0x7D4EC70`) tail-jumps `Results` into the list validator
`EADLCOCJAGD.IANBCAFGFNL`, which **returns false on null rather than throwing** — so a missing
`Results` degrades to an empty settings list instead of an exception.

**Why the first pass got it wrong — the general lesson.** The client method's *return type* is
`KPIPLFECKNC<List<PlatformNotificationCategoryConfigDTO>>`, which reads exactly like a bare list.
It is not the wire type: a `.Then` lambda (`<>c.KIMCCEBAJEF` / `OICBIEGANKC`) unwraps
`BJACLIGEIFP.Results` afterwards. **Always read `T` from the `HPBKMCLEANE<T>` / `CJBFDPLCIEJ<T>`
generic instantiation (`slots2025.py` + `ginst.py inst <N>`), never from the method signature.**
`/preferences` below was re-verified the same way and *is* genuinely bare.

`ALGAOCCMGKH` (CategoryId): Admin 0, Events 1, Friends 2, Chat 3, RoomNotifications 4, Creator 5,
Reengagement 6, FavoriteFriendOnline 7, GameplayInvites 8, Feed 9, Store 10, _Test1 999,
_Test2 1000, _Test3 1001, _Test4 1002, _Test5 1003, Bulk 9999.
`PMHCDEJLBNA` (Importance): Default 0, Low 1, High 2.
Both re-verified 2026-08-24 with `enumvals.py` ([il2cpp-field-default-values-compressed](../../../il2cpp-analysis/references/il2cpp-field-default-values-compressed.md)).

`PlatformNotificationPreferencesDTO` and `PlatformNotificationCategoryConfigDTO` both have the `0xA60520` no-op `CPOBHIECLEN` — no element-level validation; only the paged wrapper has the (non-throwing) list check above.

**Why:** the settings UI zips the two endpoints together —
`SettingsModel.GetPlatformNotifications()` returns
`Tuple<List<ALGAOCCMGKH>, List<PlatformNotificationCategoryConfigDTO>>`. `config/categories`
supplies the rows (label, blurb, whether a toggle is even shown), `preferences` supplies which are
off. **A category id that appears in `MutedCategories` but has no row in `config/categories` renders
nothing**, so the two must agree.

**How to apply:** `IsMuteable: false` hides the toggle — use it for Admin-type categories rather
than omitting the row.
