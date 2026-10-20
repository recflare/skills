# `POST api/consumables/v1/query/bulk` wire shape (2026 build)

> `POST econ.<host>/api/consumables/v1/query/bulk?configurationVersion=2` (svc **28 Econ**) takes
> **`configurationVersion` in the QUERY STRING** and **`descriptors` repeated in the
> form-urlencoded BODY**, and returns a **BARE ARRAY** of the same 8-key `RecNet.Consumable` that
> `api/consumables/v1/all` returns.
> ⚠️ **This route is on the BOOT-AWAITED path.** A 404 here produces
> `[Platform.BootSequence] ErroredPromiseException` ~0.13 s later and the full join cascade — see
> [cv1-mappings-join-nre-2026](../../../rr-client-bringup/references/cv1-mappings-join-nre-2026.md).
> ⚠️ **It is only called for descriptors MISSING from the local definition cache**, which is why a
> server that serves `api/consumables/v1/all` correctly can pass on one account and fail on another.

Derived **2026-10-13** from build `20260323.14`, from another player's `Player.log` in which this
route 404'd at `t=22.0954` and killed the join, while the same server joined cleanly from the
developer's own account.

Route literal `'api/consumables/v1/query/bulk'`, sites `0x9490A3B` / `0x9490D93`.
**POST** (`[HttpMethod statics + 0x20]` read at `0x9490D7B`), service **28 Econ**
(`mov r8d, 0x1c` at `0x9490D9A`).

## The chain — all three frames are in one boot-awaited call

The log's formatted async block names all three, innermost first:

| frame | real name | returns |
|---|---|---|
| `RecNet.Consumables.GKNNZFJGHJB` `0x947E840` | **`GetConsumableDefinitions(IEnumerable<string> descriptors, bool)`** | `Task<Dictionary<string, MGTBPZYXKTT>>` |
| `RecNet.Consumables.XGDWKDRZTDQ` `0x9480320` | **`ConvertBulkConsumableListToConsumableInstances(List<BulkConsumable>)`** | `Task<List<YFITXAVPIID>>` |
| `RecNet.Consumables.TTFUICYEDRZ` `0x947FE20` | **`DownloadUnlockedConsumables()`** | `Task<List<YFITXAVPIID>>` |

State machines: `<GetConsumableDefinitions>d__35` `0x94908B0`,
`<ConvertBulkConsumableListToConsumableInstances>d__48` `0x948D7A0`,
`<DownloadUnlockedConsumables>d__37` `0x948E580`.

So the sequence at boot is: **`GET api/consumables/v2/getUnlocked`** → for each row's
`ConsumableItemDesc`, resolve a definition → **`POST api/consumables/v1/query/bulk`** for whatever
is not already cached → build instances.

## ⚠️ Why this reproduces on one account and not another

`GetConsumableDefinitions` is a **cache-miss-only fetch**. Inside `d__35`:

- `Dictionary<string, RecNet.Consumable>.TryGetValue` (generic inst **#6181**) consults the
  already-known definitions,
- misses are collected into a `List<string>` (inst **#862**),
- that list becomes the repeated **`descriptors`** parameter,
- results are merged back with `Dictionary<string, MGTBPZYXKTT>.Add` (inst **#6232**).

`api/consumables/v1/all` is what populates that cache
([consumables-v1-v2-routes](consumables-v1-v2-routes-wire-shapes.md)). **So the route is reached only when a player owns a
consumable whose `ConsumableItemDesc` is absent from `/all`'s catalogue.** An account with no
unlocked consumables, or only ones `/all` already defines, never calls it — and the 404 stays
invisible.

**Diagnostic:** diff the `ConsumableItemDesc` values in the affected player's
`GET api/consumables/v2/getUnlocked` response against the descs in `api/consumables/v1/all`.
Anything in the former and not the latter is what gets requested here.

## Request — the two params go to DIFFERENT places

> ⚠️ **CORRECTED 2026-10-13.** This note first said both params were a form-urlencoded body, on the
> assumption that they went through the verb-dependent `NJPEKLKCVCG`. **They do not** — a live
> request showed `?configurationVersion=2` in the URL, and the slot dump confirms two *different*
> adders. See [elhkhfjehlm-verb-dependent-params](../conventions/elhkhfjehlm-verb-dependent-params.md) for the three-family rule.

| param | adder (slot dump) | lands in | value |
|---|---|---|---|
| **`configurationVersion`** | `RGBOOBRDHEB::ZTKGODPCQRW` (call `0x9490E08`) | **QUERY STRING** | the literal **`2`** (`mov dword ptr [rsp+0x108], 2` at `0x9490DD0`, then boxed) |
| **`descriptors`** | `RGBOOBRDHEB::KTGGWMNSEXK<T>`, generic inst **#862 = `string`** (MethodRef `0x9490DB4`) | **FORM BODY** | repeated once per requested desc |

```
POST /api/consumables/v1/query/bulk?configurationVersion=2
Content-Type: application/x-www-form-urlencoded

descriptors=VQSgL2pTLkWx4B3kwYG7UA&descriptors=9fKdR1pTLkWx4B3kwYG7UA
```

`configurationVersion=2` is the same concept as the `?supportedVersion=2` that
`api/consumables/v1/all` sends — same meaning, different parameter name. Do not key off the name
alone, and bind `descriptors` from the **body**, not the query.

## Response — bare array of 8-key `RecNet.Consumable`

Send is `RGBOOBRDHEB.ZWUODKCINOA<T>` with generic inst **#23347 = `List<RecNet.Consumable>`** →
**bare array, no envelope**. Identical DTO and formatter to `api/consumables/v1/all`
(`Utf8Json.Formatters.RecNet.FQGMEDSVAAD` `.ctor` `0x9125BB0`), so **one handler can serve both**.

`RecNet.Consumable` — 10 fields, **8 wire keys** (56 literal refs = 24 unique casings × 2 + 8 ✓):

| # | key | CLR |
|---|---|---|
| 1 | `ConsumableItemDesc` | string |
| 2 | `InitialCount` | int |
| 3 | `CreatedAt` | `DateTime` |
| 4 | `ThumbnailImageName` | string |
| 5 | `FriendlyName` | string |
| 6 | `RoomieCategory` | int |
| 7 | `ConsumableToolName` | string |
| 8 | `ConfigurationData` | **string holding JSON** |

⚠️ The two fields with **no wire key** are `PASXKXEHFNS` (string) and — importantly —
**`IsRROConsumable`** (bool). See the IsRRO trap below.

⚠️ `ConfigurationData` is a **JSON string**, not a nested object, and the C# field is
`ConsumableConfigurationData` — a `[DataMember]` rename. Same as on `/all`.

## ⚠️ Every requested descriptor must come back, or boot dies differently

`ConvertBulkConsumableListToConsumableInstances` looks each definition up with
`Dictionary<string, MGTBPZYXKTT>.TryGetValue` (inst #6232) at `0x948DB96` and, on the null path
(`test r12,r12 / je 0x948E066` at `0x948DCB6`), throws
**`ArgumentNullException("definition")`** (literal `0x948E07D`, ctor `0x948E092`).

So a `200` with a **subset** is not safe here — it fails the same boot-awaited promise as the 404,
just with a different exception. **Return a definition for every `descriptors` value you were sent.**
If a desc is genuinely unknown, returning a stub definition with that exact
`ConsumableItemDesc` is safer than omitting it.

## ⚠️ `IsRRO` must equal `!ConsumableItemDesc.StartsWith("ugc.")`

> ⚠️ **CORRECTED 2026-10-19.** An earlier revision of this section said "never send `IsRRO: true`
> — it can never match and throws unconditionally". **That was wrong**, and it caused real
> misdiagnosis: a first-party consumable requires `IsRRO: true`, and sending `false` is what throws.
> The error below was observed live in the **inverse** direction the old text claimed was impossible:
> `Key IsRRO=False does not match Definition IsRRO=True!`

The instance key is validated against the definition, throwing
**`InvalidDataException("Key IsRRO={0} does not match Definition IsRRO={1}!")`**
(literal `0xFE26FF8` on `20260323.14`), from
**`RecNet.Consumables+BXHGCFIHTWE..ctor(ConsumableInstanceKey, MGTBPZYXKTT, int, DateTime, int?, bool, bool, bool)`**.

- The **key** side is `RecNet.ConsumableInstanceKey{long InstanceId, bool IsRRO}`, and its `IsRRO`
  comes from the wire — `BulkConsumable.IsRRO` on `getUnlocked`, or the `IsRRO` key on the
  `ConsumableMappingAdded` push payload.
- The **definition** side is `MGTBPZYXKTT.get_IsRROConsumable()` (an **interface** — typedef #21810,
  `decl -1`, getters only), backed by `RecNet.Consumable.IsRROConsumable`, the only type in the
  build carrying that field. It is **not a wire key** on `/all` *or* `query/bulk` (both are the same
  8-key shape) — but it is **not always `false`** either, because it is **derived**.

**`RecNet.Consumable.EMSIIQRWASQ` `0x9473080`** (bounds `..0x94731BD`), the post-deserialize hook:

```
if (this.ConsumableItemDesc /* +0x10 */ == null) return;
this.IsRROConsumable /* +0x58 */ = !ConsumableItemDesc.StartsWith("ugc.");   ; 0x94730DD, xor al,1
```

The literal is **`'ugc.'`** (`lea` `0x94730B3`, `mov` `0x94730D6`). So **RRO = Rec Room Original**:

| `ConsumableItemDesc` | definition `IsRRO` | what the key side must send |
|---|---|---|
| starts with **`ugc.`** | `false` | **`IsRRO: false`** (or omit — deserializes to `false`) |
| anything else (first-party) | **`true`** | **`IsRRO: true`** |

✅ **The rule is "match the desc", not "always false".** Omitting the key is only correct for
`ugc.`-prefixed descs. For a first-party consumable — the common case for anything granted by
`bulkpurchase` out of the shipped catalogue — omitting `IsRRO` throws on the boot-awaited path, and
on the push path silently prevents the backpack row.

## Siblings on `RecNet.Consumables` reached by the same cache

| method | real name | route |
|---|---|---|
| `QDHFBWAJOUK(bool)` | `GetAllBuiltInConsumablesAsync` | `api/consumables/v1/all` — derived |
| **`GKNNZFJGHJB(IEnumerable<string>, bool)`** | **`GetConsumableDefinitions`** | **this route** |
| `LVWFDHJHQSS(string, bool)` | single-desc definition | not derived; expect the same DTO |
| `TTFUICYEDRZ()` | `DownloadUnlockedConsumables` | `api/consumables/v2/getUnlocked` — derived |
| `MNWHSFQBOOL(int)` | — | not derived |
| `MSHUBAJZUVZ(string, int, string, ConsumableConfigurationData)` | create custom consumable | `Task<RecNetResult<CreateCustomConsumableResponseDTO>>`, not derived |
