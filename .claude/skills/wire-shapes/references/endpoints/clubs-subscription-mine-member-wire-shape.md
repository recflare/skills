# Clubs subscription/mine/member wire shape

> GET subscription/mine/member (svc 15 Clubs) returns a BARE ARRAY of the 3-key FEANMHMOKPA {AccountId:int, ClubId:long, SubscriberCount:int}. ClubId is a long while both other members are ints. Two client entries share the route — one sends nothing, the other sends sort/skip/take as query params.

Derived **2026-09-24** from build `20250718.01`.
Sibling of [clubs-subscription-id](clubs-subscription-id-wire-shape.md), which covers `POST`/`DELETE subscription/{id}` on the
same service.

`GET https://clubs.<host>/subscription/mine/member` — service **15 = Clubs**
(`r8d = 0xF` at `0x7CD6841` / `0x7CD8689`), verb **GET** (`HttpMethod` statics `[rcx+8]` at
`0x7CD681E` / `0x7CD8666`). Whole-route literal (slot **`0xD08AAE0`**), no `String.Format`.

## Two client entries, same route

| entry | RVA | params |
|---|---|---|
| `MIAEIIPKLEI.DLDEEKKJNKF` | `0x7CD6720` | **none** — no `ELHKHFJEHLM`, no body |
| `OFADCHFHBKL.HIKFLCMOJGC` | `0x7CD8520` | `sort`, `skip`, `take`, in that order |

The verb is GET, so those three are **query string** params, not a form body
([elhkhfjehlm-verb-dependent-params](../conventions/elhkhfjehlm-verb-dependent-params.md)). They are added unconditionally on that path.
Both entries log **`"Failed to retrieve subscriptions"`** on failure.

## Response — BARE ARRAY, no envelope

Send helper is `MGPBDIAGCFD.HPBKMCLEANE<T>` (response required); generic inst **#1009** =
**`List<FEANMHMOKPA>`**. No envelope type anywhere in the chain. A `{}` body throws `IONCMJIACFI`
("Malformed Response") — serve **`[]`** when the player subscribes to nothing.

Element `.FEANMHMOKPA` (typedef #21884), formatter **`LFEDGPONDCG`** `.ctor 0x775CC40`.
`____stringByteKeys` run at `0x775CFA2` / `0x775CFF9` / `0x775D044` — **3 keys, 1:1 with the 3
declared fields**:

| # | key | CLR | off |
|---|---|---|---|
| 1 | `AccountId` | **int** | 0x10 |
| 2 | `ClubId` | **long** | 0x18 |
| 3 | `SubscriberCount` | **int** | 0x20 |

```json
[ { "AccountId": 205, "ClubId": 207, "SubscriberCount": 12 } ]
```

⚠️ **`ClubId` is a `long` between two `int`s.** Confirmed from the serializer
`LFEDGPONDCG.FBGBLPHHDGN` `0x775C900`, which emits key[0] → `mov edx, [rdi+0x10]` (32-bit write
`BDLOEIPNGEL.IOIPHMPDOHM`), key[1] → `mov rdx, [rdi+0x18]` (64-bit write `BDLOEIPNGEL.HFMBGFFFMNN`),
key[2] → `mov edx, [rdi+0x20]` (32-bit). Widening `AccountId` or narrowing `ClubId` on the server is
the easy mistake here.

`AccountId` is the **creator's player id**, not a club-membership row id — the same class carries
the literal `"Failed to GetConsumablesForFreeGiftButton. creatorPlayerId: {0}"`.

## What the client does with it

`MIAEIIPKLEI.PHOPJBPFLCC` `0x7CD6930` reduces the list to a `HashSet<int>` cached on the manager at
`[singleton+0x110]`:

```
list.Where(x => x.AccountId != this.<int field @0x10>)   // MIAEIIPKLEI.CINFHODIOHD  0x7CD6700
    .Select(x => x.AccountId)                            // <>c.JFDKINJNLCN          0xACA200
    -> new HashSet<int>(...)
```

Both lambdas dereference the element directly (`mov eax, [rdx+0x10]` after an il2cpp null check that
**throws**), so a `null` entry inside the array raises an NRE in the LINQ pass, not at deserialize
time. Never emit `[null]`. `ClubId` and `SubscriberCount` are not read on this path — only
`AccountId` — but they are still deserialized, so their types must be right.

## Siblings sharing the DTO

From the generated `nonobject-responses.txt` (this route *is* in it, lines 136–137 — unlike the
`String.Format`-built club routes):

| route | response T | method |
|---|---|---|
| `subscription/mine/member` | `List<FEANMHMOKPA>` | `MIAEIIPKLEI.DLDEEKKJNKF`, `OFADCHFHBKL.HIKFLCMOJGC` |
| `subscription/top/creators/today` | `List<FEANMHMOKPA>` | `LNJNCFHNBOM.KPNMJEKMDGL` |
| `subscription/subscriberCount/{0}` | **bare `int`** | `LNJNCFHNBOM.CJCAAJNIIMO`, `LNJNCFHNBOM.KDFFFEPFAII` |
