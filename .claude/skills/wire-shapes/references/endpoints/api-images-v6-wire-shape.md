# Api images v6 wire shape

> Wire shape of GET api/images/v6?name= on the API service (svc 2) for recflare-2025 — a bare 13-key image record whose hook normalizes null ids to 0 rather than validating.

Derived **2026-08-18** from `C:\Games\recflare-2025` (build `20250718.01`) via
[recflare-2025-metadata-carve](../../../il2cpp-analysis/references/recflare-2025-metadata-carve.md).

`GET https://api.<host>/api/images/v6?name={imageName}` — **GET** (`HttpMethod` statics `+0x08`),
service **2 = API** (`mov r8d, 2`), single query param `name`. Client entry
`HPJKKCCECLH.MDCEPFFCKAA(string name)` at `0x7CF72C0`. Returns **one** record; the bulk sibling is
`api/images/v5/bulk`.

Response is a **bare object**, `HPJKKCCECLH.GBJHBCMJBNP` — no envelope. Formatter `BODPFLOJAIK`
ctor `0x78808B0`, 13 keys in `____stringByteKeys` order: `SavedImageId` long 0x10,
`ImageName` string 0x18, `PlayerId` int 0x20, `RoomId` long? 0x28, `PlayerEventId` long? 0x38,
`ClubId` long? 0x48, `Description` string 0x58, `Accessibility` enum 0x60,
`AccessibilityLocked` bool 0x64, `SavedImageType` enum 0x68, `CreatedAt` DateTime 0x70,
`CheerCount` int 0x78, `CommentCount` int 0x7c.

`Accessibility` `OKEAJPFBMGI`: Private 0, Public 1, FriendsOnly 2.
`SavedImageType` `BJFECDCCOPG`: None 0, ShareCamera 1, OutfitThumbnail 2, RoomThumbnail 3,
ProfileThumbnail 4, InventionThumbnail 5, PlayerEventThumbnail 6, RoomLoadScreen 7.

**The post-deserialize hook is a normalizer, not a validator** — `GBJHBCMJBNP.CPOBHIECLEN`
(`0x7CE6FE0`) is *not* the shared `0xA60520` stub, but all it does is: for each of `RoomId`,
`PlayerEventId`, `ClubId`, if `HasValue == false`, replace it with `0`. No throw anywhere in the
method. Omitting those three keys is therefore safe and they arrive as 0.

This is the concrete counter-example to "any RVA other than the shared stub means real validation" —
always disassemble the hook. (`MIBODHPEFHP.CPOBHIECLEN` at `0xFEA4F0` is the other kind: its own
`nop; ret`.)

**Why:** `Nullable<T>` in IL2CPP is laid out `{bool hasValue; T value}` — hasValue **first**, matching
the CLR declaration order. `cmp byte [obj+0x28], 0` on a `long?` field at 0x28 is testing HasValue,
not the low byte of the value. Getting this backwards inverts the reading of every nullable check.

**How to apply:** the content-signature check that stalls mirrored images
([image-content-signature-bypass](../../../rr-client-bringup/references/image-content-signature-bypass.md), `HPJKKCCECLH.BLDFMLMAFLH` at `0x7CF32F0`) lives on this same
class but is **not** part of this JSON — it is on the image fetch, not this metadata response.
