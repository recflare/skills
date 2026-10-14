# `api/players/*/progression` wire shapes (2026 build)

> `GET api.<host>/api/players/v1/progression/xpEarnedToday` (svc **2 API**) returns a
> **BARE JSON INTEGER** — `0`, not an object.
> ⚠️ Returning the `Progression` object here throws
> `JsonParsingException: expected:'Number Token', actual:'{'` → `Malformed Response`.
> The `Progression` object `{PlayerId, Level, XP}` belongs on
> `/api/players/v2/progression/bulk`, which returns a **list** of them.
> ⚠️ **`PlayerId` is the wire key**; the C# property is `AccountId` (a `[DataMember]` rename).

Derived **2026-10-13** from build `20260323.14`, prompted by a live failure on the **Badges** page:

```
JsonParsingException: expected:'Number Token', actual:'{', at offset:0
Rethrow as RecNetMalformedResponseException: Malformed Response: '{"PlayerId":null,"Level":1,"XP":0}'
```

The server was serving a correctly-shaped `Progression` object on a route whose `T` is a plain `int`.
Identified from the `# Formatted Async Stack Trace` block, which named
`RecRoom.IGKUHSKEBTB.MOPNTKRIYUU` → `RecNet.BXWRVQYTGVG.SLBZOMDCGGC` — see
[2026-send-helper-tiers](../conventions/2026-send-helper-tiers.md) for that workflow.

## `GET api/players/v1/progression/xpEarnedToday` — a bare int

Route literal `0xFC61890`. Facade **`RecNet.Progressions.SLBZOMDCGGC() -> Task<int>`** `0x9536560`
(+0x110), and the instance wrapper `RecNet.BXWRVQYTGVG.SLBZOMDCGGC()` `0x952DBD0` whose builder is
generic inst **#86 = `int`**. Verb **GET** (`[HttpMethod statics + 0x08]` at `0x9536600`), service
**2 API** — ⚠️ an **inlined** request ctor, so the service is the field store
`mov dword ptr [rsi + 0x18], 2` at `0x9536638`, not an `r8d` immediate. No params.

```json
0
```

That is the whole body. This is a member of the
[nonobject-response-routes](../conventions/nonobject-response-routes.md) class: `{}`, `[]` and any object hard-fail. The
exception is **not** the generic `Malformed Response` first — Utf8Json throws
`JsonParsingException: expected:'Number Token', actual:'{'` and the sender wraps it. Compare
[number-token-parsing-exception](../conventions/number-token-parsing-exception.md), the 2025 note for the same class of error
(there, `T` was a bare `long?`).

`T` is a non-nullable `int`, so `null` throws too. Return `0` for "no XP earned today".

## `RecNet.Progression` — 3 keys, and the first one is renamed

Formatter `Utf8Json.Formatters.RecNet.WXOPQXWVEUX` `.ctor` **`0x8E0D480`** (+0x2B0):

| # | key | CLR | C# property |
|---|---|---|---|
| 1 | **`PlayerId`** | `int` | **`AccountId`** |
| 2 | `Level` | `int` | `Level` |
| 3 | `XP` | `int` | `XP` |

⚠️ **The wire key is `PlayerId`.** `ftypes.py` shows the field as `<AccountId>k__BackingField`, but
the formatter's key run never references `AccountId` at all — it is a `[DataMember(Name="PlayerId")]`
rename. Emitting `AccountId` would be silently dropped and the id would read as `0`. This is the
formatter-is-the-authority rule again; the declared property name is not the wire name.

⚠️ **All three are non-nullable `int`** — `"PlayerId": null` throws even on the correct route. Send a
real id or omit the key.

## `/api/players/v2/progression/bulk` — a list of them

Route literal `0xFC765C0`, state machine **`<GetProgressionsBulkServiceCall>d__21$$MoveNext`**
`0x954AE50` (+0x300), facade
`RecNet.Progressions.BDACJTJBZJF(IReadOnlyList<int>, ct) -> Task<List<Progression>>`.

Send is `ZWUODKCINOA<T>` with generic inst **#2967 = `List<RecNet.Progression>`** — so a **bare
array**, no envelope:

```json
[ { "PlayerId": 205, "Level": 1, "XP": 0 } ]
```

Service **2 API** (`mov dword ptr [rdi + 0x18], 2` at `0x954B06E`, inlined ctor again). The account
ids go through `NJPEKLKCVCG` with inst #86 (`int`) under the name **`id`** — the
`IReadOnlyList<T>` overload, so the parameter repeats once per id.

⚠️ **Note the leading slash** in the literal: `/api/players/v2/progression/bulk`, unlike every
sibling. Whether that produces a double slash against the service base URL was not checked — look
for `//api/players/...` in a proxy capture before assuming the path is clean.

**Not pinned:** the verb on the bulk route. The `HttpMethod` load for its ctor is in a block
`fn.py` did not reach cleanly, and the two `mov r14, qword ptr [rax]` sites it did find belong to a
later cold path. With a repeated `id` parameter it is **GET with `?id=…&id=…` if GET, a
form-urlencoded body if not** ([elhkhfjehlm-verb-dependent-params](../conventions/elhkhfjehlm-verb-dependent-params.md)) — check a capture
rather than guessing.

## The rest of `RecNet.Progressions`

`py msig.py Progressions` — 19 methods; the ones that reach the network:

| method | returns | note |
|---|---|---|
| **`SLBZOMDCGGC()`** | **`Task<int>`** | `xpEarnedToday`, derived above |
| **`BDACJTJBZJF(IReadOnlyList<int>, ct)`** | **`Task<List<Progression>>`** | `/v2/progression/bulk`, derived above |
| `UNTASGBSNQJ()` | `MPVTAJGPRUT<Progression>` | the caller's own progression |
| `EFRQEJBBDSX(int)` | `MPVTAJGPRUT<Progression>` | one account's progression |
| `FYLIRVERRTO(List<int>)` | `MPVTAJGPRUT<List<Progression>>` | the promise-flavoured bulk wrapper |

`YWPOQXTRYRV()`, `NYONBTTKOXF`, `MVGQDARQUFD`, `FFVAUJPUKAQ`, `NIXPVMMWVDG` and `WMPLSYUHBEJ` are
local cache accessors with no route of their own, so a `Progression` can also arrive by push.
The routes behind `UNTASGBSNQJ` / `EFRQEJBBDSX` were not chased; both deserialize a single
`Progression`, so the 3-key shape above applies.

Related: `api/storefronts/v1/buyProgressionEventXpBoost`, `external_room_progression/`,
`externalroomprogression/bulk` — not derived. For `api/progressionEvents/*` see
[progressionevents-event-by-id](progressionevents-event-by-id-wire-shape.md) and
[progressionevents-active](progressionevents-active-wire-shape.md).
