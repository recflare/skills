# Clubs club/account/{id}/created wire shape

> GET club/account/{accountId}/created (svc 15 Clubs) takes NO params and returns a BARE ARRAY of the same 16-key Club DTO (NBOMJFLBIGC) as account/{id}/clubs — identical generic inst #1020. This is the clubs an account CREATED; the other route is the clubs it BELONGS TO.

Derived **2026-10-02** from build `20250718.01`.
The 16-key element DTO, its four enums and the `Obscured*` handling are documented in
[clubs-account-clubs](clubs-account-clubs-wire-shape.md) — not duplicated here.

`GET https://clubs.<host>/club/account/{accountId}/created` — service **15 = Clubs**
(`mov r8d, 0xF` at `0x7CB0CCC`), verb **GET** (`HttpMethod` statics `[rcx+8]` at `0x7CB0C3D`).

Path is `String.Format("club/account/{0}/created", accountId)` — literal slot **`0xD1EC5C8`**; the
account id is a **path segment**.

Client entry **`LNJNCFHNBOM.NMFKLEADMOG`** `0x7CB0B50` (+0x290). Error literal
**`'Failed to GetPlayerCreatedClubs'`** — unobfuscated enough to confirm the route's purpose. Callers:
`RRUI.Data.ClubListModel.FPNPJBNMOGL` `0x25AA180` and the tail-jump wrapper
`MAOFOGLKCFP.NMFKLEADMOG` `0x7C72770`.

**No params, no body** — no `ELHKHFJEHLM`, no `ELKIBCPINAP`; the only extra builder call is
`MGPBDIAGCFD.DIDJOECFJII` `0x7CB0D2C`, the response-cache TTL.

## Response — BARE ARRAY, same DTO as `account/{id}/clubs`

`MGPBDIAGCFD.HPBKMCLEANE<T>` (response required), generic inst **#1020** =
**`List<NBOMJFLBIGC>`** — byte-for-byte the same instantiation
[clubs-account-clubs](clubs-account-clubs-wire-shape.md) uses. No envelope.

```json
[ { "ClubId": 207, "Name": "My Club", "Description": "…", "MainImageName": null,
    "State": 0, "CreatorAccountId": 2, "Category": null, "Visibility": 1,
    "Joinability": 0, "AllowJuniors": true, "MinLevel": 0, "MemberCount": 12,
    "IsRRO": false, "ClubChatEnabled": true, "ClubhouseRoomId": null, "ClubType": 0 } ]
```

`{}` or an empty body throws `IONCMJIACFI`; serve **`[]`**. `NBOMJFLBIGC.CPOBHIECLEN` is the shared
no-op `0xA60520`, so every key is omittable — but `State`'s `0` is `Active` and the enum is sparse,
which is the trap called out in the sibling note.

## The two account-scoped club lists

| route | meaning | entry | response |
|---|---|---|---|
| `account/{id}/clubs` | clubs the account **is a member of** | `LNJNCFHNBOM.OKGAHPCHCLC` `0x7CB15C0` | `List<NBOMJFLBIGC>` |
| `club/account/{id}/created` | clubs the account **created** | `LNJNCFHNBOM.NMFKLEADMOG` `0x7CB0B50` | `List<NBOMJFLBIGC>` |

Same DTO, same tier, same facade, **different prefixes** — one is `account/...`, the other
`club/account/...`. Both are consumed by `RRUI.Data.ClubListModel` (`GIFIIMENEDF` and
`FPNPJBNMOGL` respectively), so a server that serves one and 404s the other will leave one tab of
that UI empty.

For a self-hosted server the natural implementation is `created` = filter by
`CreatorAccountId == accountId`, and `clubs` = filter by membership. Nothing in the client enforces
that distinction — it renders whatever each route returns.

# ✅ 2026 (`20260323.14`): re-verified — shape unchanged, two new findings

Re-derived **2026-10-29**. **All 16 keys, their order, the four enums and the bare-array tier are
unchanged.** The DTO and facade are de-obfuscated now, and two things the 2025 note could not know
have come out.

| 2025 | 2026 |
|---|---|
| facade `LNJNCFHNBOM` | **`RecNet.Clubs`** |
| entry `NMFKLEADMOG` `0x7CB0B50` | **`RecNet.Clubs.PUHCOEPRIYA(int accountId)`** `0x9468770` → `MPVTAJGPRUT<List<RecNet.Club>>` |
| path closure `JKEGMAFLBEB` | `RecNet.Clubs.BZIPMSWGLQV(int)` `0x945EDD0` (returns the formatted path) |
| element `NBOMJFLBIGC` | **`RecNet.Club`** (16 fields) |
| formatter (unnamed) | **`Utf8Json.Formatters.RecNet.WFUFAZXIHKO`** `.ctor` **`0x9139D20`** (`msig`-confirmed) |
| literal `0xD1EC5C8` | `'club/account/{0}/created'` **`0xFD1C4E8`**, 6 refs |

Route re-confirmed: **GET** (`[statics+0x20]` at `0x9468856` → `[rcx+8]` at `0x946885A`), service
**15 = Clubs** (`mov r8d, 0xF` at `0x94688D1`), **no params, no body** (builder-action slot is
`mov qword [rsp+0x20], 0` at `0x94688C8`), response-cached via
`ORUUDATDRUN(TimeSpan, bool)` at `0x946893A` off `RecNet.Cache` statics. Error literal
`'Failed to GetPlayerCreatedClubs'` survives verbatim.

Key run from `WFUFAZXIHKO..ctor` (`0x913A54A`…`0x913A7BC`), 16 keys, **same order as 2025**:
`ClubId`, `Name`, `Description`, `MainImageName`, `State`, `CreatorAccountId`, `Category`,
`Visibility`, `Joinability`, `AllowJuniors`, `MinLevel`, `MemberCount`, `IsRRO`, `ClubChatEnabled`,
`ClubhouseRoomId`, `ClubType`.

2026 names the CLR members behind the opaque ones — three are `Obscured*` (plain numbers/bools on
the wire) and one is a `[DataMember]` rename:

```
ObscuredLong  BRUXVHCHRLS                  -> 'ClubId'
ObscuredInt   LMJQJTTKKNR                  -> 'CreatorAccountId'
string        <PrimaryTag>k__BackingField   -> 'Category'      <- rename; no 'PrimaryTag' literal exists
ObscuredBool  CNXXPRECRMO                  -> 'IsRRO'
ObscuredBool  VAXAKAUKNGM                  -> 'ClubChatEnabled'
```

Enums re-checked and **identical**, including the sparse `ClubState` trap: `Active 0`,
`PendingJunior 11`, `Moderation_PendingReview 100`, `Moderation_Closed 101`,
`MarkedForDelete 1000`. `ClubVisibility` Private 0/Public 1 · `ClubJoinability` Open 0/InviteOnly
1/AskToJoin 2 · `ClubType` Generic 0/Creator 1.

**No post-deserialize hook on 2026** — `msig RecNet.Club` shows only accessors, `Equals`/
`GetHashCode` and `ARMIVRDLSVE()` (the `Obscured*` re-encrypt); there is no `IULRMJBAHPG` and no
`EMSIIQRWASQ`. So every key stays omittable, and `[]` is safe.

## ⚠️ This route is only ever requested for SOMEONE ELSE's account

`RRUI.Data.ClubListModel$$RefreshPlayerCreatedClubsResults` **`0x254A4B0`** branches on identity:

```
0x254a5a6  call RecNet.Account$$get_AccountId      ; the local player
0x254a5b2  cmp  edi, eax                           ; requested accountId == local?
0x254a5b4  je   0x254a5d5
0x254a5ce  call Clubs.PUHCOEPRIYA(edi)             ; NO  -> club/account/{id}/created
0x254a5e5  call Clubs.UDLIHEWGJYH()                ; YES -> club/mine/created
```

**`club/mine/created` `0xFD1D228` is a NEW sibling** not in the 2025 note —
`RecNet.Clubs.UDLIHEWGJYH()` `0x946AF50`, same `MPVTAJGPRUT<List<Club>>`, no path segment, and it is
the one the client actually uses for the signed-in player. It has **4** callers
(`ClubListModel.RefreshCacheInternal`, `ClubAnnouncementCreationModel`, `ClubCreationModel`,
and the branch above) against this route's **1**.

➡️ So if you are testing `club/account/{yourOwnId}/created` and the client never asks for it, that
is expected — implement **both**, and give `club/mine/created` the same body.

## ⚠️ The description string does NOT mean enveloped on 2026

`PUHCOEPRIYA` passes `'Failed to GetPlayerCreatedClubs'` into
`KGLKSSUUEOH::XXATRYZHEBX<List<Club>>`, which on the 2025 heuristic ("a leading
`friendlyActionDescription` means enveloped") would tier this route as enveloped. It is **bare**:

- `XXATRYZHEBX<T>(MPVTAJGPRUT<T>, RecRoom.Log, string)` is a **log-on-failure decorator** —
  `T -> T`, and it takes a `RecRoom.Log`. The envelope collapse is `FQWUEPYTLAQ`
  (`MPVTAJGPRUT<RecNetResult<T>> -> MPVTAJGPRUT<T>`), and it is **not called here**.
- Envelope oracle: **no** `RecNetResultListObject_Club` and **no** `RecNetResultObject_Club`
  instantiation exists (the Clubs ones that do are `ClubAnnouncementList`, `ClubBannedAccount`,
  `ClubMembership`, `ClubMembershipRequest`, `ClubDetails`).

Recorded as a general correction in
[2026-send-helper-tiers](../conventions/2026-send-helper-tiers.md).

`ZWUODKCINOA<T>` and `SAXZOKINUQZ::CTZMMSFIPBH<T>` both carry methodSpec inst **#1091** =
`List<RecNet.Club>` — the deserialize target, confirmed with `ginst`.

## Sibling literal

`LNJNCFHNBOM.JKEGMAFLBEB` `0x7CAADB0` (+0x60) is only the tiny `String.Format` closure for this path;
the request lives in `NMFKLEADMOG`. Its neighbour in the same region handles
`club/{0}/permissions/{1}` with the description `'Modify Club Permissions'` — a
**description-carrying (enveloped)** helper, unlike this bare read.
