# Chat chatPrivacySetting wire shape

> GET thread/chatPrivacySetting (svc 9 Chat) returns a BARE 3-key object {PlayerId, DirectMessagePrivacySetting, GroupChatPrivacySetting}; the two settings are byte enums Friends 0 / Favorites 1 / NoOne 2. The SAME path also serves PUT, which takes both settings as FORM fields and returns the valueless envelope.

Derived **2026-09-15** from build `20250718.01`.
Distinct from [chat-cansenddm](chat-cansenddm-wire-shape.md) (`thread/checkCanSendDirectMessageWithPrivacySetting`),
which is a different route returning a bare integer.

Literal `'thread/chatPrivacySetting'` slot `0xD0E5A30`, referenced by **two** methods on
`PNAHAINBHAH` — this path serves **two verbs**, so do not infer one from the other.

| verb | method | description string | response T |
|---|---|---|---|
| **GET** | `PNAHAINBHAH.BPIBGEGNKDO` `0x7CB5C90` (+0x160) | `'Unable to retrieve chat privacy settings'` | `.IIKNFHFIECG` — **bare object** |
| **PUT** | `PNAHAINBHAH.KJFDNLFLHJD` `0x7CB9FE0` (+0x210) | `'Unable to set chat privacy settings'` | `.JFNAKFCGDAO` — valueless envelope |

Service **9 = Chat** for both (`mov r8d, 9`). Verbs read from the `HttpMethod` statics at the
`AKJEAMCCEOH..ctor` call site: GET `[rcx+8]` (`0x7CB5D52`), PUT `[rcx+0x28]` (`0x7CBA0D6`).

## GET — request

**No parameters.** `BPIBGEGNKDO` contains no `ELHKHFJEHLM` and no `ELKIBCPINAP` call; the bearer
token identifies the player.

## GET — response is a BARE object, no envelope

Send generic `MGPBDIAGCFD::HPBKMCLEANE<T>` with generic inst `#14811` = **`.IIKNFHFIECG`** — the DTO
directly, not `KGOJLHJNIOD<…>`. Formatter **`MLGKGAOIELA`** `.ctor 0x7652C00` (+0x4b0); resolver
`PGHNJGDNFGC` index **`0x33B`**, jump table RVA `0x77B1F50`, case `0x77AAAE6`. Trailing
`____stringByteKeys` run at `0x7652F62..0x7653004` — **3 keys**:

| # | key | CLR | off | notes |
|---|---|---|---|---|
| 1 | `PlayerId` | int | 0x10 | |
| 2 | `DirectMessagePrivacySetting` | `AOOGIFEMGLJ` byte enum | 0x14 | `Friends 0`, `Favorites 1`, `NoOne 2` |
| 3 | `GroupChatPrivacySetting` | `BJHJCPEEHDP` byte enum | 0x15 | `Friends 0`, `Favorites 1`, `NoOne 2` |

```json
{ "PlayerId": 319, "DirectMessagePrivacySetting": 0, "GroupChatPrivacySetting": 0 }
```

The two enums are **separate typedefs** (#21745 / #21746) that happen to share identical members —
do not assume one is reused for both. Both are declared `byte`, but Utf8Json writes them as plain
JSON numbers.

Enums are **numeric** — `NoOne` has 0 occurrences in `out/stringliteral.json`, so no by-name
formatter was generated (positive control: `PlayerId` and `GroupChatPrivacySetting` return 1 each;
the single `Favorites` hit is an unrelated UI literal, and a by-name formatter would require *every*
member name present). All three keys are accepted in all three Utf8Json casings.

The type declares exactly 3 fields and the formatter emits exactly 3 keys — nothing is
`[IgnoreDataMember]`, nothing is computed.

## No validation

`IIKNFHFIECG.CPOBHIECLEN` **is** the shared no-op stub `0xA60520` (4877 method names fold onto that
RVA), so there is no post-deserialize hook and every key is omittable. Omitted members default to
`0` — which is `Friends`, the most permissive setting, so an empty `{}` reads as
"everyone's friends can DM me", not as a locked-down default.

## PUT — the sibling setter

Takes both settings as **`ELHKHFJEHLM` parameters** named `directMessagePrivacySetting` and
`groupChatPrivacySetting` (`0x7CBA13F`, `0x7CBA176`). Because the verb is **PUT, not GET**, those go
in an `application/x-www-form-urlencoded` **body**, not the query string — see
[elhkhfjehlm-verb-dependent-params](../conventions/elhkhfjehlm-verb-dependent-params.md).

```
PUT https://chat.<host>/thread/chatPrivacySetting
Content-Type: application/x-www-form-urlencoded

directMessagePrivacySetting=0&groupChatPrivacySetting=0
```

Response is `JFNAKFCGDAO` — the **valueless envelope** `{Success, Error, error_id}`, no `Value` key
(`error_id` lowercase, the other two PascalCase).
