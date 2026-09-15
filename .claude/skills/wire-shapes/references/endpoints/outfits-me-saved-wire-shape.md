# Outfits me saved wire shape

> Wire shape of GET api/outfits/me/saved — a BARE ARRAY of the same 8-key outfit DTO that GET/PUT outfits/me uses singly; client re-keys it by Slot.

Derived **2026-08-22** from build `20250718.01` via [recflare-2025-metadata-carve](../../../il2cpp-analysis/references/recflare-2025-metadata-carve.md).
Companion to [outfits-me-put-wire-shape](outfits-me-put-wire-shape.md).

`GET https://api.<host>/outfits/me/saved` — service **2 = API** (`mov r8d, 2`), verb **GET**
(`HttpMethod` statics `+0x08`; map `0x00` Delete / `0x08` Get / `0x20` Post / `0x28` Put).
**No query params, no body** (`AKJEAMCCEOH$$.ctor` 5th arg = 0). Client state machine
`EIIDOIICDGL$$MoveNext` `0x7D51C70` (+0x5E0); literal `'outfits/me/saved'` `0xD25B448`.

**Response is a BARE JSON ARRAY — no envelope.** Send generic is
`MGPBDIAGCFD::HPBKMCLEANE<List<KPPNBDELPNB>>` (T is the List *directly*, not wrapped in the
`KGOJLHJNIOD\`1` send-result interface and not in any of the three envelope tiers).

**Element `KPPNBDELPNB` — the SAME DTO as the PUT `outfits/me` body and the GET `outfits/me`
response.** 8 keys, formatter `GAHMAGAAONJ` `.ctor 0x76C4C50` (trailing `____stringByteKeys` run,
order verified against field offsets):

| key | CLR | off |
|---|---|---|
| `DataVersion` | long | 0x10 |
| `LegacyData` | `JMCEICICBNP` object | 0x18 |
| `CustomizationSettings` | string | 0x20 |
| `Selections` | `List<OEGPLENCKHH>` | 0x28 |
| `Slot` | int | 0x30 |
| `Name` | string | 0x38 |
| `Accessibility` | enum (number) | 0x40 |
| `ThumbnailFileName` | string | 0x48 |

- `LegacyData` (`JMCEICICBNP`, formatter `GIJAAPJGJON` `0x76C6760`): `SelectionsV1`, `SelectionsV2`,
  `FaceFeatures`, `SkinColor`, `HairColor` — **all string** (they are serialized sub-JSON blobs).
- `Selections` element (`OEGPLENCKHH`, formatter `HFHCADBJLJF` `0x76C8150`): `CustomAvatarItemId`
  Guid (JSON string), `BodyPart` int, `BakedUnityAssetFileName` string, `AdditionalConfiguration`
  string.
- `Accessibility` (`KLKIFENPGNG`) is **numeric**: `Private`=0, `Public`=1, `Unlisted`=2. Confirmed the
  per-build way — no `IHCMHKGLBEA<KLKIFENPGNG>` class exists and `'Unlisted'` is absent from
  `out/stringliteral.json`, so no by-name formatter was generated.
- **No post-deserialize validation.** `KPPNBDELPNB` implements the *interface* `PDDMBELEHHJ` and its
  `CPOBHIECLEN` is the `0xA60520` no-op.

**`Slot` is the primary key and duplicates are silently lost.** The awaiting method's builder is
`AsyncTaskMethodBuilder\`1<IReadOnlyDictionary<int, KPPNBDELPNB>>`: it `Clear()`s a
`Dictionary<int, KPPNBDELPNB>` then `set_Item(elem.Slot, elem)` per element — key read as
`mov edx, [rdi+0x30]`. Repeated `Slot` = last wins; a **null array element throws** (null check
branches to the throw path). An empty array `[]` is fine.

**vs `outfits/me`** (`NCBLEPFFJBE$$MoveNext` `0x7D62F60`): same service 2 + GET, but
`HPBKMCLEANE<KPPNBDELPNB>` — **one bare object, not an array**. So the two routes share an identical
element shape and differ only in cardinality: `/outfits/me` = the equipped outfit as a single object,
`/outfits/me/saved` = the saved-slot list as an array. (PUT `outfits/me` takes that object as its body
and replies with the valueless envelope — see [outfits-me-put-wire-shape](outfits-me-put-wire-shape.md).)

**How to apply:** serve `/outfits/me/saved` as `[]` when the player has none — never `{}` or an
envelope, or `KKEIDMPEHAL<T>` raises the malformed-response throw
([ioncmjiacfi-malformed-response](../conventions/ioncmjiacfi-malformed-response.md)). Give every element a distinct `Slot`.
