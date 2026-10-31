# Avatar lockeditems bulk wire shape

> Wire shape of POST api/avatar/v1/lockeditems/bulk (svc 28 Econ) — JSON body {AvatarItemDescriptions:[string]}, response is a BARE ARRAY of a 10-key item DTO; also the AvatarItemType/Rarity enum values.

Derived **2026-08-24** from build `20250718.01` via [recflare-2025-metadata-carve](../../../il2cpp-analysis/references/recflare-2025-metadata-carve.md).
Sibling of [api-images-v6-wire-shape](api-images-v6-wire-shape.md); same envelope tiering as [outfits-me-put-wire-shape](outfits-me-put-wire-shape.md).

`POST https://econ.<host>/api/avatar/v1/lockeditems/bulk` — service **28 = Econ**
(`mov r8d, 0x1c`), verb **POST** (`HttpMethod` statics `+0x20`; map `0x00` Delete / `0x08` Get /
`0x20` Post / `0x28` Put). Client entry `OGAEDNMDDLF.ELAKLPNBBLC` `0x7CFFA50`; literal
`'api/avatar/v1/lockeditems/bulk'` `0xD122B78`.

**Body is JSON** — `MGPBDIAGCFD.ELKIBCPINAP<EGFPLBPPCCK>` (`WithBody<T>`) stores the DTO at `+0x40`
and stamps the body-kind enum `OOHAFGLGDNB` at `+0x48` = **`Json` (4)**
(`ImageJpg 0 / ImagePng 1 / VideoMp4 2 / BinaryData 3 / Json 4 / PlainText 5`).

```json
{ "AvatarItemDescriptions": ["<desc>", "<desc>"] }
```
`EGFPLBPPCCK` has exactly one member (`List<string>`); formatter `DPODBDFDNKN` `.ctor 0x76C3BA0`,
single `____stringByteKeys` entry `AvatarItemDescriptions`. **The client never sends an empty list** —
`ELAKLPNBBLC` checks `List.Count == 0` first and returns `Task.FromResult(new List<…>())` with no
HTTP call at all. A *null* list throws before the request.

**Response is a BARE JSON ARRAY — no envelope.** Send generic is
`MGPBDIAGCFD::HPBKMCLEANE<List<BGJHOEKDNED>>` (T is the `List` directly). Element `BGJHOEKDNED`,
formatter `KLBAEFOPOFB` `.ctor 0x76CA880` (trailing `____stringByteKeys` run at `0x76CB1E2..`):

| key | CLR | off | notes |
|---|---|---|---|
| `AvatarItemType` | enum int | 0x10 | `Outfit 0`, `HairDye 1`, `CustomOutfit 2` |
| `AvatarItemDesc` | string | 0x18 | the **payload**, echoed back from the request |
| `FriendlyName` | string | 0x20 | |
| `Tooltip` | string | 0x28 | |
| `Rarity` | enum int | 0x30 | `None -1`, `Common 0`, `Uncommon 10`, `Rare 20`, `Epic 30`, `Legendary 50` |
| `TagList` | string | 0x38 | **a STRING, not an array** |
| `AvatarItemId` | int | 0x40 | |
| `IsBaseAvatarItem` | bool | 0x44 | |
| `ThumbnailImage` | string | 0x48 | |
| `CreatedAt` | DateTime | 0x50 | Utf8Json ISO-8601 (`NKLCFNHAFNB.ILIOAHGLMKI`, no format literals) |

Enums are **numeric** — no `Legendary`/`Uncommon`/`CustomOutfit` literal exists in
`out/stringliteral.json`, so no by-name formatter was generated. Every key is accepted in all three
Utf8Json casings.

The key↔field pairing is **independently confirmed** by `LOFDJEDAGHN..ctor` `0x7628480`, which copies
the DTO straight through: `[+0x20]→FriendlyName`, `[+0x28]→Tooltip`, `[+0x30]→Rarity`,
`[+0x38]→TagList`, `[+0x40]→AvatarItemId`, `[+0x44]→IsBaseAvatarItem`, `[+0x48]→ThumbnailImage`,
`[+0x50]→CreatedAt` — and branches on `[+0x10]` with `test eax, 0xFFFFFFFD` (type ∈ {0,2}) /
`cmp eax, 1`, which also pins the enum values.

**Validation / failure modes**
- No post-deserialize hook: `BGJHOEKDNED.CPOBHIECLEN` is the `0xA60520` no-op.
- **A null array element throws** — `0x76284DE: test rdi, rdi ; je <throw>` in `LOFDJEDAGHN..ctor`.
- `AvatarItemDesc` is parsed per type (Outfit/CustomOutfit → `CLNKPHMDENM`, HairDye → `CAOGJAKDFBC`).
  An `AvatarItemType` outside {0,1,2} skips the parse entirely — no throw, item just has no payload.
- Per-element mapping exceptions are caught and logged (funclet `0x7CFFEC4`, reached only by
  exception) and that element is dropped; the whole call has an error continuation logging
  `"Failed to bulk download locked avatar item details"`.
- An empty body / `{}` / an envelope raises the malformed-response throw
  ([ioncmjiacfi-malformed-response](../conventions/ioncmjiacfi-malformed-response.md)) — serve `[]`, never `{}`.

**Sibling:** `GET api/avatar/v1/lockeditems?desc=<string>` (`OGAEDNMDDLF.DELPBBBJDOD` `0x7CFF500`) —
same service 28, `desc` added by the query-param adder `MGPBDIAGCFD.ELHKHFJEHLM`, and it uses the
**same** `HPBKMCLEANE<List<BGJHOEKDNED>>`, so even the singular route returns a **JSON array**.

**How to apply:** return one element per requested description, echoing `AvatarItemDesc` byte-for-byte
(the client re-parses it into the outfit/hair-dye payload). Order and count need not match the request
— the client maps element-wise with no lookup — but every element must be non-null.


## The whole `OGAEDNMDDLF` facade shares this DTO - and `v4/items` is the built-in catalogue

Added **2026-08-27**. Five routes, all service **28 Econ**, all sending
`HPBKMCLEANE<List<BGJHOEKDNED>>` - i.e. **every one returns a bare array of the 10-key DTO above**:

| method | route | verb | params |
|---|---|---|---|
| `GKPNEOBMMGN()` `0x7CFFF80` | **`api/avatar/v4/items`** | GET | **none** |
| `DHHFFDHPEKK()` `0x7CFF8A0` | `api/avatar/v1/defaultbaseavataritems` | GET | none |
| `KGAOKMJNEAP(ct)` `0x7D00210` | `api/avatar/v1/defaultunlocked` | GET | none |
| `DELPBBBJDOD(List<NPHONPGHNPF>)` `0x7CFF500` | `api/avatar/v1/lockeditems` | GET | `desc` |
| `ELAKLPNBBLC(List<NPHONPGHNPF>)` `0x7CFFA50` | `api/avatar/v1/lockeditems/bulk` | POST | body |

⚠️ **The declared return type lies.** All five are typed
`KPIPLFECKNC<List<LOFDJEDAGHN>>` / `Task<List<LOFDJEDAGHN>>`, but `LOFDJEDAGHN` is the *runtime*
model built by `LOFDJEDAGHN..ctor` `0x7628480` from the wire DTO. The **send generic is
`List<BGJHOEKDNED>`** - textbook case of [nonobject-response-routes](../conventions/nonobject-response-routes.md)'s rule: read `T` from the send
generic, never from the client method's return type.

⚠️ **These are on ECON (`econ.<host>`), not `api.<host>`,** despite the `api/` path prefix.

**`GET api/avatar/v4/items` is the full baked-in avatar-item catalogue** - the Unity-shipped clothing
(hats, shirts, legs, ...). If it returns `[]`, the client has **no built-in clothing at all** and any
wardrobe / "Clothing" tab shows only custom avatar items from `customAvatarItems/*`, which is a
completely separate facade (`LINCNKPIJDN`, service 2 API,
[customavataritems-routes-wire-shapes](customavataritems-routes-wire-shapes.md)). The two never mix: CAI search is hard-bound to
`GICBMFJFHLI` and cannot return `BGJHOEKDNED` items.

Ownership is decided separately by `api/playeritems/v1/isavataritemowned/bulk` and
`api/playeritems/v1/isavataritemowned/{0}/{1}`; the CAI equivalent is
`econ/customAvatarItems/v1/owned`.

# ✅ 2026 (`20260323.14`): facade renamed, five routes unchanged — and `defaultunlocked` gates FBA

Re-checked **2026-10-30**. Same five routes, same bare array, still service **28 Econ**
(`mov r8d, 0x1c` at `0x9499712` in the `defaultunlocked` builder).

| 2025 | 2026 |
|---|---|
| facade `OGAEDNMDDLF` | **`RecNet.DYSPCBGIIOA`** (`.ctor` takes `NSEJPLSROWY legacyAvatarItemDescSerializer`, `KJSSLRVSDKB runtimeMapperProvider`) |
| element DTO `BGJHOEKDNED` | **`RecNet.TFDFUXKLDZH`** |
| runtime model `LOFDJEDAGHN` | `RecNet.AvatarItemDetails` (compared by `DYSPCBGIIOA$$RNWIUYJLIXX(AvatarItemDetails, TFDFUXKLDZH)` `0x94994A0`) |
| `NPHONPGHNPF` desc | `RecRoom.AssetIds.AvatarItemDesc` |

| 2026 method | RVA | route |
|---|---|---|
| `XSKXZUSXGVK()` | `0x9499A30` | `api/avatar/v4/items` (literal `0xFC42118`) |
| `UEPYCVXKDPN()` | `0x94997B0` | `api/avatar/v1/defaultbaseavataritems` (`0xFC40698`) |
| `TECOASWPAHN(ct)` | `0x9499620` | `api/avatar/v1/defaultunlocked` (`0xFC409E8`) |
| `OURSPLCYJEW(List<AvatarItemDesc>)` | `0x94990B0` | `api/avatar/v1/lockeditems` (`0xFC40D38`) |
| `GXSFWRJLRWO(List<AvatarItemDesc>)` | `0x9498D40` | `api/avatar/v1/lockeditems/bulk` (`0xFC41088`) |

The first four return `MPVTAJGPRUT<List<TFDFUXKLDZH>>` / `Task<List<TFDFUXKLDZH>>`; the declared
type no longer lies on 2026 (it names the wire DTO directly), but still read `T` off the send
generic. ⚠️ `callxref` finds **0 callers** for all of them — the facade is injected through UJect
and every consumer calls it by interface, so trace consumers by literal or by DI, not by `callxref`.

## ⚠️ An incomplete `defaultunlocked` list silently breaks the Full Body Avatar swap

Confirmed on a live server **2026-10-30**: an FBA swap failed with a checkout dialog demanding
payment of **0**, and the fix was **adding the missing FBA items to the default avatar-item list** —
not any change to the pricing routes that actually threw.

Why: `RecRoom.Avatars.Outfit.OutfitManager` fills the body-type defaults from the **shipped**
`AvatarItemWardrobeRuntimeConfig`, then filters with `TryGetRandomUnlockedItem` — and *unlocked* is
what these routes decide:

- `TryGetDefaultTorsoItem(out AvatarItem, RecRoom.Protobuf.AvatarBodyType, bool)` `0x1599130`
- `TryGetDefaultLegsItem(out AvatarItem)` `0x1598CD0` — **FBA-only slot**
- `TryGetDefaultShoesItem(out AvatarItem)` `0x1598F00` — **FBA-only slot**

With nothing unlocked for those slots the editor falls back to browsable (unowned) items,
`OutfitManager.IsTrialItem` turns true, and the trial-item pricing chain runs and fails — see
[avatar-trial-item-pricing-chain-2026](avatar-trial-item-pricing-chain-2026.md).

➡️ **Legs and shoes do not exist on the classic body**, so a defaults list that looks complete for
classic can still be missing everything FBA needs. Cover every `AvatarBodyType`, not just the one
you tested with.

The download step is `OutfitManager$$DownloadDefaultAvatarItems(ct)` `0x158E400`
(`<…>d__66$$MoveNext` `0x15BCD80` → `OutfitManager$$MURLXFKYQPG(List<TFDFUXKLDZH>, bool)`
`0x1595170`). A **hard** failure there is a *login* blocker, not an FBA bug:
`<DownloadDefaultAvatarItems>d__243` `0xFE91D0` raises `LOGIN_CODE_BLOCK` (19) at `0xFE948C` →
`Unable to login (code: block)`
([login-error-code-words-2026](../../../rr-client-bringup/references/login-error-code-words-2026.md)).
A list that is present but incomplete boots fine and only breaks the swap.
