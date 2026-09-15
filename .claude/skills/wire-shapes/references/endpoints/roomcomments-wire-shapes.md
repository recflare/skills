# Roomcomments wire shapes

> Wire shapes of GET comments/get/{roomId} and POST comments/create/{roomId} on the RoomComments service for recflare-2025 — both bare RoomComment, and create sends everything as QUERY params with no body.

Derived **2026-08-20** from `C:\Games\recflare-2025` (build `20250718.01`) via
[recflare-2025-metadata-carve](../../../il2cpp-analysis/references/recflare-2025-metadata-carve.md). Both on `NDEIMPALPMG`; host `roomcomments.<domain>`
(service enum 14 = RoomComments — bound to the API class, not an inline constant).

**`GET comments/get/{roomId}?count={int}&minId={long}`** — `HGBGINCIIFA(long roomId, int count,
long minId)` (`0x7D9D4A0`), **GET**, two query params via `ELHKHFJEHLM`. Response is a **bare array**
of `RoomComment`, no envelope.

**`POST comments/create/{roomId}`** — `OHCILFMPOJD(long roomId, long subRoomId, string message,
RoomComment.LKNIJNDAODI style, float3? position)` (`0x7D9DFF0`), **POST** with **no body at all** —
all six params go in the **query string** via `ELHKHFJEHLM`: `message`, `subRoomId`, `style`,
`positionX`, `positionY`, `positionZ`. Response is **one bare `RoomComment`**. Failure logs
"Failed to Create Comment".

`RoomComment` is **unobfuscated** (formatter `CAPAFBKBEFE` ctor `0x7D6C6C0`), 11 keys:
`CommentId` long 0x18 (a `[DataMember(Name = "CommentId")]` rename), `RoomId` long 0x20,
`SubRoomId` long? 0x28, `AccountId` int? 0x38, `CreatedAt` DateTime 0x40, `Message` string 0x58,
`Style` enum 0x60, `Unread` bool 0x64, `PositionX` float? 0x68, `PositionY` float? 0x70,
`PositionZ` float? 0x78.

`Style` = `RoomComment.LKNIJNDAODI`: **Feedback 0, Idea 1, BugReport 2**.

**Position is three separate nullable floats on the wire, never a nested object.** The
post-deserialize hook (`0x7DA4580`) is a normalizer, not a validator:

```
if (PositionX.HasValue && PositionY.HasValue && PositionZ.HasValue)
    Position = new float3(X, Y, Z);   // the [IgnoreDataMember] float3? at 0x48
else
    Position = null;
```

**All three must be present together or the comment has no position** — and it never throws. The
`float3?` at 0x48 is `[IgnoreDataMember]`, internal only.

**How to apply:** siblings are `comments/delete/{0}`, `comments/read/{0}/{1}`,
`comments/unreadcounts`. Empty list response is `[]` — see
[ioncmjiacfi-malformed-response](../conventions/ioncmjiacfi-malformed-response.md) for why `{}` would throw there.

⚠️ **CORRECTION 2026-09-02:** where this note says the parameters are **query params**, they
are actually an **`application/x-www-form-urlencoded` request body** — `ELHKHFJEHLM` routes params
to the query string only for GET. See [elhkhfjehlm-verb-dependent-params](../conventions/elhkhfjehlm-verb-dependent-params.md). Response shape
unaffected.
