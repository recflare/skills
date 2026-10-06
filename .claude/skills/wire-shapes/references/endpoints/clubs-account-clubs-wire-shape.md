# Clubs account/{id}/clubs wire shape

> GET account/{accountId}/clubs (svc 15 Clubs) takes NO params and returns a BARE ARRAY of the 16-key Club DTO NBOMJFLBIGC — ClubId/CreatorAccountId/IsRRO/ClubChatEnabled are CodeStage Obscured* types but plain numbers/bools on the wire, and four members are enums.

Derived **2026-09-30** from build `20250718.01`.
Third Clubs route derived; siblings [clubs-subscription-mine-member](clubs-subscription-mine-member-wire-shape.md) and
[clubs-subscription-id](clubs-subscription-id-wire-shape.md).

`GET https://clubs.<host>/account/{accountId}/clubs` — service **15 = Clubs** (`r8d = 0xF` at
`0x7CB1760`), verb **GET** (`HttpMethod` statics `[rcx+8]` at `0x7CB1713`).

Path is `String.Format("account/{0}/clubs", accountId)` — literal slot **`0xD0B6130`**; the id is a
**path segment**. **No params and no body** (no `ELHKHFJEHLM`, no `ELKIBCPINAP`); the only extra
builder call is `MGPBDIAGCFD.DIDJOECFJII` `0x7D9ADB0`, the response-cache TTL.

Client entry **`LNJNCFHNBOM.OKGAHPCHCLC`** `0x7CB15C0`. Callers: `RRUI.Data.ClubListModel.GIFIIMENEDF`
`0x25AA600` — **unobfuscated**, which confirms the route's purpose — and the tail-jump wrapper
`MAOFOGLKCFP.OKGAHPCHCLC` `0x7C72880`.

## Response — BARE ARRAY, no envelope

`MGPBDIAGCFD.HPBKMCLEANE<T>` (response required), generic inst **#1020** =
**`List<NBOMJFLBIGC>`**. `{}` or an empty body throws `IONCMJIACFI`; serve **`[]`**.

Element `.NBOMJFLBIGC` (typedef #21856) — the **Club** DTO, also embedded as field `0x00` of
`IDPBEBEBMPA`, the `club/{0}/details` response. Formatter **`MLDOEFKMDHN`** `.ctor 0x7651380`, key run
`0x765216C..0x76525EF` — **16 keys, 1:1 with the 16 declared fields**:

| # | key | CLR | off |
|---|---|---|---|
| 1 | `ClubId` | **`ObscuredLong`** | 0x10 |
| 2 | `Name` | string | 0x38 |
| 3 | `Description` | string | 0x40 |
| 4 | `MainImageName` | string | 0x48 |
| 5 | `State` | enum `EJANEACCGPO` | 0x50 |
| 6 | `CreatorAccountId` | **`ObscuredInt`** | 0x54 |
| 7 | `Category` | string | 0x68 |
| 8 | `Visibility` | enum `HMFICNMKFIF` | 0x70 |
| 9 | `Joinability` | enum `AGDIDLLPEAP` | 0x74 |
| 10 | `AllowJuniors` | bool | 0x78 |
| 11 | `MinLevel` | int | 0x7C |
| 12 | `MemberCount` | int | 0x80 |
| 13 | `IsRRO` | **`ObscuredBool`** | 0x84 |
| 14 | `ClubChatEnabled` | **`ObscuredBool`** | 0x90 |
| 15 | `ClubhouseRoomId` | `long?` | 0xA0 |
| 16 | `ClubType` | enum `DPPEPAJIHNE` | 0xB0 |

```json
[ { "ClubId": 207, "Name": "My Club", "Description": "…", "MainImageName": null,
    "State": 0, "CreatorAccountId": 205, "Category": null, "Visibility": 1,
    "Joinability": 0, "AllowJuniors": true, "MinLevel": 0, "MemberCount": 12,
    "IsRRO": false, "ClubChatEnabled": true, "ClubhouseRoomId": null, "ClubType": 0 } ]
```

The four `Obscured*` members are **plain numbers/bools on the wire** — no formatter exists for the
CodeStage wrappers, the generated code reads a primitive and relies on the implicit conversion.
`ClubhouseRoomId` is the one `genericinst`; the 16-byte stride to the next field (`0xA0`→`0xB0`)
matches `Nullable<long>` in this build's Mono layout, so `null` is valid there.

## The four enums

| enum | members |
|---|---|
| `EJANEACCGPO` **State** | `Active 0`, `PendingJunior 11`, `Moderation_PendingReview 100`, `Moderation_Closed 101`, `MarkedForDelete 1000` |
| `HMFICNMKFIF` **Visibility** | `Private 0`, `Public 1` |
| `AGDIDLLPEAP` **Joinability** | `Open 0`, `InviteOnly 1`, `AskToJoin 2` |
| `DPPEPAJIHNE` **ClubType** | `Generic 0`, `Creator 1` |

⚠️ **`State` is sparse** — `0, 11, 100, 101, 1000`, no contiguous run. An omitted `State` reads as
`Active (0)`, which is the permissive value, so a club you meant to hide shows up.

## Validation

`NBOMJFLBIGC.CPOBHIECLEN` is the shared no-op stub `0xA60520` — no per-element validation, every key
omittable.

**Not pinned:** whether a `null` *array* throws. The list is consumed inside a continuation lambda off
`ClubListModel.GIFIIMENEDF` that I did not follow to the iteration. The sibling pattern says assume it
does — `roomkeys/v1/room`'s consumer NREs on a null list
([roomkeys-v1-room](roomkeys-v1-room-wire-shape.md)) and `subscription/mine/member`'s NREs on a null *element*
([clubs-subscription-mine-member](clubs-subscription-mine-member-wire-shape.md)). Serve `[]`, never `null`, and no `null` entries.

## Finding this formatter

`typeslots.py NBOMJFLBIGC` → `mxref` finds **only** `ClubCode` and a UI behaviour, not the formatter,
because Utf8Json's generated resolver maps the type to an **integer index** rather than linking the
formatter statically — `PGHNJGDNFGC..cctor` does `dict.Add(typeof(NBOMJFLBIGC), 0x33F)` at
`0x7787D46`, and the formatter is produced from a switch on that index. Chasing the jump table is not
worth it; **intersect the key-literal xrefs instead**. `ClubId` has 65 referencing ctors and
`MemberCount` many more, but only **one** formatter ctor references both, and its 16-key run matches
the field list exactly. That intersection trick generalises to any DTO whose formatter resists the
TypeInfo route.
