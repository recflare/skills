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

## Sibling literal

`LNJNCFHNBOM.JKEGMAFLBEB` `0x7CAADB0` (+0x60) is only the tiny `String.Format` closure for this path;
the request lives in `NMFKLEADMOG`. Its neighbour in the same region handles
`club/{0}/permissions/{1}` with the description `'Modify Club Permissions'` — a
**description-carrying (enveloped)** helper, unlike this bare read.
