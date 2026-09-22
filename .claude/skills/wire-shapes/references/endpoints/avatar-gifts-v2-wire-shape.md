# Avatar gifts v2 wire shape

> GET api/avatar/v2/gifts (svc 28 Econ) takes NO params and returns a BARE ARRAY of the 20-key gift-box DTO JKKPLHHIIHB — `{}` hard-fails with IONCMJIACFI 'Malformed Response'; every field is null-safe, so there is no hard-required key.

Derived **2026-09-15** from build `20250718.01`.
Sibling of [giftdropstore-v3](giftdropstore-v3-wire-shape.md) (the `GiftDrop` a box is rendered from)
and [avatar-lockeditems-bulk](avatar-lockeditems-bulk-wire-shape.md) (same bare-array tiering).

`GET https://econ.<host>/api/avatar/v2/gifts` — service **28 = Econ** (`mov r8d, 0x1c` at
`0x7CE0068`), verb **GET** (`HttpMethod` statics `[rcx+8]` at `0x7CE003C`; map `0x00` Delete /
`0x08` Get / `0x20` Post / `0x28` Put). Client entry `BOJBDLDPIGD.DIEPCDCMOLA` `0x7CDFF40`
(bounded by the next method at `0x7CE01B0`); literal `'api/avatar/v2/gifts'`.

**No request parameters and no body** — the method contains no `ELHKHFJEHLM` (param) and no
`ELKIBCPINAP` (body) call at all. The player is identified by the bearer token only.

## Response — a BARE JSON ARRAY, no envelope

Send generic is `MGPBDIAGCFD::HPBKMCLEANE<T>` (send, response required) whose methodSpec generic
inst `#16691` resolves to **`List<JKKPLHHIIHB>`** — T is the `List` directly, not
`GJAFHDAFBNE<…>`. An **empty array is `[]`**; a `{}` body throws `IONCMJIACFI`
"Malformed Response" (this route is on the generated list in
`../conventions/nonobject-response-routes.md`).

> **Envelope-tell exception.** This helper *does* take a leading description string
> (`'Failed to download gifts'`, passed in `r8` at the tail jump `0x7CE017F`), which
> `../conventions/llcldppagij-envelope-failure-exception.md` describes as the "enveloped" tell.
> Here it is **not** — the generic inst is the bare `List`. Resolve T from the methodSpec inst and
> treat the description string as advisory only.

Element `JKKPLHHIIHB`, formatter **`NCNCOBNIGCG`** (`.ctor 0x7C1FFC0`, `+0x1970`; resolver
`PGHNJGDNFGC` maps the type to formatter index **`0x3EC`**, jump table at RVA `0x77B1F50`,
case `0x77AC8A1`). Trailing `____stringByteKeys` run at `0x7C21193..0x7C2175A` — **20 keys**:

| # | key | CLR | off | notes |
|---|---|---|---|---|
| 1 | `Id` | `long?` | 0x10 | the box id; echoed back to `.../gifts/consume` as `Id=` |
| 2 | `PlayerId` | `int` | 0x20 | recipient |
| 3 | `FromPlayerId` | `int?` | 0x24 | sender; null/absent for a self-purchase |
| 4 | `ConsumableItemDesc` | string | 0x30 | non-empty ⇒ box renders as a consumable |
| 5 | `AvatarItemType` | enum int? | 0x38 | `Outfit 0`, `HairDye 1`, `CustomOutfit 2` |
| 6 | `AvatarItemDesc` | string | 0x40 | |
| 7 | `CustomAvatarItemId` | `Guid?` | 0x48 | |
| 8 | `EquipmentPrefabName` | string | 0x60 | non-empty ⇒ box renders as equipment |
| 9 | `EquipmentModificationGuid` | string | 0x68 | **a STRING, not a Guid** |
| 10 | `CurrencyType` | enum int | 0x70 | `Invalid 0`, `LaserTagTickets 1`, `RecCenterTokens 2`, `LostSkullsGold 100`, `DraculaSilver 101`, `RecRoyale_Season1 200`, `RoomCurrency 300`, `RoomInventoryItem 301`, `ProgressionEvent 400`, `RoomieCredits 500` |
| 11 | `Currency` | `int` | 0x74 | |
| 12 | `Xp` | `int` | 0x78 | |
| 13 | `GiftContext` | enum int | 0x7c | `None -1`, `Default 0`, `Game_Drop 2`, `Daily_Challenge_Complete 5`, `Reacquisition 20`, `Membership 21`, `GameRewards 50`, `LevelUp 100`, `Purchased_Gift_A..D 500..503`, `Friendotron_Gift 1300`, `ProgressionEvent 13000`, `Token 110100` … (**~120 members** — an earlier revision of this note said 30, which was a truncated dump) |
| 14 | `GiftRarity` | enum int | 0x80 | `None -1`, `Common 0`, `Uncommon 10`, `Rare 20`, `Epic 30`, `Legendary 50` |
| 15 | `Message` | string | 0x88 | |
| 16 | `Signature` | string | 0x90 | |
| 17 | `IsSignatureValid` | bool | 0x98 | |
| 18 | `Platform` | enum int | 0x9c | `All -1`, `Steam 0`, `Oculus 1`, `PlayStation 2`, `Xbox 3`, `RecNet 4`, `IOS 5`, `GooglePlay 6`, `Standalone 7`, `Pico 8`, `Switch 9` |
| 19 | `PlatformsToSpawnOn` | enum int | 0xa0 | **bit flags** — `None 0`, `Steam 1`, `Oculus 2`, `PlayStation 4`, `Xbox 8`, `RecNet 16`, `IOS 32`, `GooglePlay 64`, `Standalone 128`, `Pico 256`, `Switch 512`, `All -1` |
| 20 | `BalanceType` | enum int? | 0xa4 | `NonPurchasedNotUsableInP2P -2`, `NonPurchasedDefault -1`, `SteamPurchased 0`, `OculusPurchased 1`, `PlayStationPurchased 2`, `MicrosoftPurchased 3`, `RecNetPurchased 4`, `IOSPurchased 5`, `GooglePlayPurchased 6`, `PicoPurchased 8`, `SwitchPurchased 9`, `PlayStationNonPurchasedP2P 100`, `NonPlayStationNonPurchasedP2P 101`, `NonPurchasedEarnedByP2P 1000`, `NonPurchasedEarnedByP2Pv2 1001`, `RoomieEnergyPack 1101` |

Enums are **numeric** — no `LostSkullsGold` / `Uncommon` / `Purchased_Gift_A` /
`NonPurchasedEarnedByP2Pv2` literal exists in `out/stringliteral.json`, so no by-name formatter was
generated. Every key is accepted in all three Utf8Json casings (54 distinct casing literals for the
20 members, which is the count check that the run is complete).

Note `Platform` (#18) and `BalanceType` (#20) are **two separate keys** here — this DTO does *not*
carry the `BalanceType`→`Platform` `[DataMember]` rename seen elsewhere.

### Members with NO wire key

`JKKPLHHIIHB` has 25 backing fields but only 20 keys. The five at `0xac`–`0xc0`
(`bool`, `bool`, `string`, `string`, `bool`) are `[IgnoreDataMember]` and client-side only; the
three getter-only properties (`0x7626BB0`, `0x7626B90`, `0x7626B60`) are computed and likewise
absent. Sending any of them is harmless — unknown keys are dropped silently.

## Client-side requirements — none are hard

- **Post-deserialize hook `JKKPLHHIIHB.CPOBHIECLEN` `0x7626B00` is not validation.** It is not the
  shared `0xA60520` stub, but it only loads a static delegate from `[klass+0x90]` and tail-jumps to
  it when non-null; nothing registers one, so it is a no-op and cannot throw.
- **The three computed getters are null-safe**, so an omitted string cannot NRE there:
  `0x7626B60` = `!IsNullOrEmpty(ConsumableItemDesc)` (field `0x30`), `0x7626B90` =
  `!IsNullOrEmpty(EquipmentPrefabName)` (field `0x60`), `0x7626BB0` reads the `AvatarItemType?`
  at `0x38` as a value type. These two `IsNullOrEmpty` offsets are also the independent
  confirmation that the key↔field pairing above is right.

So the only real requirement is **the array itself**: return `[]`, never `{}` and never an empty
body.

## Cross-check against a live capture (2026-09-15)

Verified against a real `econ` response. **It matches** — bare array, 16 of the 20 keys present,
all with correct names, casings and types. Corrections to an earlier reading of
`packages/domain/src/gifts-db.ts`: that interface is `extends Record<string, unknown>` and is
**not exhaustive**, so it is not evidence of the wire. `FromPlayerId` and `GiftContext` *are*
written (`apps/econ/src/econ.app.ts:1865,1878`) and do appear in the capture.

- **Extra keys, dropped silently** (no client member): `ConsumableCount`, `ConsumableMappingId`,
  `ConsumablePreExistingCount`, `PackageType`, `CreatedAt`.
- **Absent, defaulting cleanly**: `PlayerId` → 0, `CustomAvatarItemId` → null, `Signature` → null,
  `IsSignatureValid` → false. Nothing in the deserialize path requires them: the hook is a no-op
  and the computed getters are null-safe. *Not provable beyond that* — all four getters are
  linker-folded shared bodies (`0xAAE1A0` 329 names, `0xAC8EE0` 174, `0xF67FB0` 27, `0x7626C30` 4),
  so call-site counts say nothing about who reads this DTO's fields.
- **Enum values in the capture are all legal**: `GiftContext 500` = `Purchased_Gift_A`,
  `GiftRarity 50` = `Legendary`, `Platform -1` = `All`, `PlatformsToSpawnOn -1` = `All`,
  `AvatarItemType 0` = `Outfit`, `CurrencyType 0` = `Invalid`.
- **`AvatarItemType 0` with a comma-separated `AvatarItemDesc` and a null `CustomAvatarItemId` is
  correct, not a mismatch** — the comma-separated guid string is the normal desc form for an
  Outfit, and `CustomAvatarItemId` belongs to the `CustomOutfit (2)` path. See
  [giftdropstore-v3](giftdropstore-v3-wire-shape.md) "How to apply". If such a box renders empty,
  the cause is downstream: the desc must exist in the client's baked `descToCaidMapping`, which
  drops unknown descs with no log.


## The SAME DTO is the GiftPackageReceivedImmediate push payload (2026-09-22)

`JKKPLHHIIHB` is not only the `GET api/avatar/v2/gifts` element — it is also the **websocket
notification payload** for three numeric channels on the `EMNAKPGIHDN` notification enum. Registered
in `BOJBDLDPIGD.OCOPJMCPGIB` `0x7CE12D0`, each via `LMBGGGGNBOB.KOOMBBKFAEP` with payload generic
inst **#1226 = `.JKKPLHHIIHB`**:

| id | name | handler |
|---|---|---|
| `0x1E` 30 | `GiftPackageReceived` | `PIIJJNOBBEK` |
| **`0x1F` 31** | **`GiftPackageReceivedImmediate`** | `OPPBJGOMECO` `0x7CE14A0` |
| `0x20` 32 | `GiftPackageRewardSelectionReceived` | `ODDHBJCKPHB` |

(The generated `notifications-2025.txt` lists only the 50 **string-keyed** channels, so none of these
appear there — another reason to treat that table as a lower bound.)

Frame is the standard `MDCEJFPDCEL<T>` envelope — **`Msg` then `Id`, and `Id` is a STRING** even for
a numeric channel ([messages-v2-message-type-payloads](messages-v2-message-type-payloads.md)):

```json
{ "Msg": { …the 20 keys above… }, "Id": "31" }
```

### ⚠️ Silent dedup by `Id` — the reason "some gifts arrive and some don't"

30 and 31 both tail into `BOJBDLDPIGD.KIDJJABEFLI(gift, immediate, …)` `0x7CE0A00`, which is
effectively:

```csharp
if (pending.All(g => g.Id != incoming.Id))   // predicate BINLAKBDJJF.LFEOCCGMBFA 0x7CDFB70
    pending.Add(incoming);                    // closure field is literally named `package`
```

The predicate compares the **`Nullable<long>` `Id`** at `+0x10` as
`(value differs) OR (hasValue differs)`. So **two boxes with the same `Id` — including two `null`s —
compare equal and the later one is dropped with no log at all.** Any push path that reuses an `Id`,
or omits it, silently loses every box after the first while a matching one is still unopened.

### "Misconfigured GiftPackage" is narrower than it reads

`BOJBDLDPIGD.LNEGDFEHGFJ(JKKPLHHIIHB)` `0x7CE0D40` logs
`"Misconfigured GiftPackage. Should have currency and currency type!"` on exactly one condition
(`0x7CE0E38`):

```
cmp [rbx+0x70], 0   ; CurrencyType == Invalid(0)
jne skip
cmp [rbx+0x74], 0   ; Currency != 0
je  skip
-> warn
```

i.e. **a currency amount with no currency type**. An XP-only box (`Currency == 0`) does *not* trip
it, so this warning is not the diagnostic for a missing XP gift.

The same method then tests `GiftContext` against
**{`Purchased_Gift_A..D` 500-503, `Friendotron_Gift` 1300}** (`0x7CE0E76`) to set a client-side flag —
every other context takes the other branch.
