# Rooms unity_assets/baked/bulk wire shape

> POST unity_assets/baked/bulk (svc 16 Rooms) is the **baked-asset-bundle lookup**: you hand it a list of UnityAsset GUIDs and it returns a **BARE ARRAY** of the 5-key `EFBKLOHNCCB` `{UnityAssetId, Target, Version, Filename, Hash}`. `Filename`/`Hash` are the storage-blob reference the client then downloads. Return `[]`, or rows whose `Filename` is null, and **no bundle download happens at all** — `[AssetBundle_Download]` and `RoomAssets_DownloadAndParse` return in ~0.0x ms in Player.log with no error anywhere.

Derived **2026-10-05** from build `20250718.01`, while tracing a custom room that loaded as an empty
`MAKER_ROOM`.

`POST https://rooms.<host>/unity_assets/baked/bulk` — service **16 = Rooms**, facade
**`OALMDGJKBJH`** (the service number comes from the facade's class-bound helper, not from this
method; the host in a live capture is `rooms.<host>`, which matches).

Verb **POST** — `HttpMethod` statics `[rcx+0x20]` at `0x7DF924C`. Whole-route literal
`'unity_assets/baked/bulk'` slot **`0xD1840F8`**, referenced only by the entry method.

Client entry **`OALMDGJKBJH.FJELNOFBKKI`** `0x7DF9140` (+0x190), whose carved signature is the
cleanest statement of the contract:

```
Task<List<EFBKLOHNCCB>> FJELNOFBKKI(IReadOnlyList<Guid> unityAssetIds, byte target, int version, CancellationToken ct)
```

## Request — form body, `id` repeated once per GUID

Params are added by the separate closure **`IAOHDCDDOCM.MPJOKEJNELD`** `0x7DEF4D0`, not by the entry
method — `slots2025.py` on the entry method alone shows no `ELHKHFJEHLM` at all. Chase the
`MethodDef` slot (`0x7DF9188`).

| # | param | CLR | added at |
|---|---|---|---|
| 1 | `target` | byte | `0x7DEF566` |
| 2 | `version` | int | `0x7DEF59B` |
| 3 | `id` | **`IEnumerable<Guid>`** — generic `ELHKHFJEHLM<Guid>` (inst #322) | `0x7DEF5BA` |

Because the verb is **POST**, `ELHKHFJEHLM` writes these to an
`application/x-www-form-urlencoded` **body**, not the query string
([elhkhfjehlm-verb-dependent-params](../conventions/elhkhfjehlm-verb-dependent-params.md)). The third call is the
**collection overload**, so `id` appears once per GUID — the same pattern as `accountIds` on
[itemwishlists-v1-routes](itemwishlists-v1-routes-wire-shapes.md):

```
POST /unity_assets/baked/bulk
Content-Type: application/x-www-form-urlencoded

target=0&version=227&id=4f0c1e4a-2b77-4b16-9a3e-5dbcfd7f2865&id=9a3e5dbc-fd7f-2865-8f0c-1e4a2b774b16
```

⚠️ **The `target` byte's enum is not pinned.** One layer up,
`KCHDMOJGHJD.FJELNOFBKKI(IReadOnlyList<Guid>, bool, JNILEFJFFJD, CancellationToken)` `0x7DD1A70`
takes **`JNILEFJFFJD : int`** = `Room = 0`, `Invention = 1`, and that is the obvious candidate for
the byte — but the cast was **not traced** (the launcher only stuffs the args into a state machine,
and the entry method has **zero** direct callers: a byte-scan of the whole image for `E8`/`E9` to
`0x7DF9140` returns 0 hits, so it is reached through the method-pointer table). Do not treat
`target == 0 ⇒ Room` as confirmed. It does not matter much for the server: the client supplies
`target` and `version`, so **filter on what was asked and echo it back**.

## Response — BARE ARRAY of 5 keys, no envelope

Send is **`OALMDGJKBJH.LMKONLJOAEP<T>`** (methodref `0x7DF91A0`), generic inst **#21814** =
**`List<EFBKLOHNCCB>`** — the type argument *is* the bare list, so there is **no envelope** here.

> `LMKONLJOAEP` on this facade is **not** a reliable bare/enveloped tell: `rooms/{0}` DELETE uses the
> same helper with an enveloped `T` ([rooms-room-by-id](rooms-room-by-id-wire-shape.md)). Resolve the
> instantiation every time; a `Task<List<…>>` return type is likewise not the wire type.

Formatter **`FNIPNKJJAHN` `.ctor 0x77390D0`** (+0x610), `____stringByteKeys` run
`0x77394CB`..`0x7739600` — 5 keys, 1:1 with the 5 declared fields of `EFBKLOHNCCB` (typedef #23097):

| # | key | CLR | off |
|---|---|---|---|
| 1 | `UnityAssetId` | **`System.Guid`** | 0x10 |
| 2 | `Target` | byte | 0x20 |
| 3 | `Version` | int | 0x24 |
| 4 | **`Filename`** | string | 0x28 |
| 5 | **`Hash`** | string | 0x30 |

```json
[ { "UnityAssetId": "4f0c1e4a-2b77-4b16-9a3e-5dbcfd7f2865",
    "Target": 0, "Version": 227,
    "Filename": "2026-10-05/a0d83019-675d-41c0-8924-c238c5a12ee8",
    "Hash": "R0SVMvrAW4n1TIF2lxaOAQZ5XXVJh7prEP6GpiLCrQo=" } ]
```

`{}` throws `IONCMJIACFI` ([ioncmjiacfi-malformed-response](../conventions/ioncmjiacfi-malformed-response.md)) — the client's
`NKJABNHBPCA` reads `expected:'[', actual:'{'`. An empty result is **`[]`**.

`Filename` is the same storage-blob path shape that
[storage-upload](storage-upload-wire-shape.md) returns and that
[rooms-subrooms-data](rooms-subrooms-data-wire-shape.md) commits — `<date>/<guid>`.

## ⚠️ No validation hook, which is exactly the hazard

`EFBKLOHNCCB.CPOBHIECLEN` is the shared no-op `0xA60520`, so **every key is omittable** and a row
with a null `Filename` deserializes cleanly. The client then has no blob to fetch, and because the
missing download is a *consequence* of the missing key rather than an error, it produces **no log
line, no exception and no HTTP request**. Same failure class as the `DataBlob` cloud-variable bug in
[rooms-room-by-id](rooms-room-by-id-wire-shape.md).

## How the failure looks in Player.log

This route feeds the asset-bundle stage of the room load. Its consumer is
**`FIONEPNJGBB.MoveNext`** `0x104E4E0`, which carries the literal **`'Run GetAssetBundle Tasks'`**
(`0x104E704`) — that is the link between this endpoint and the load timings. In the `StackTimer`
block of a room load, a working fetch and a broken one look like this:

```
          [Downloading Data]:                           Self: [ 217.77ms   7frames]   <- working (dorm)
            [AssetBundle_Download]:                     Self: [   1.31ms   0frames]
            [SubRoom_DownloadAndParse('KDGPCLGNAFG)']:  Self: [   9.40ms   0frames]

          [Downloading Data]:                           Self: [   0.51ms   0frames]   <- nothing fetched
            [AssetBundle_Download]:                     Self: [   0.02ms   0frames]
            [SubRoom_DownloadAndParse('KDGPCLGNAFG)']:  Self: [   0.01ms   0frames]
```

Sub-millisecond timings on those children mean **no blob reference was available**, not that the
download was fast. Check this route's `Filename`/`Hash` before looking anywhere else.

`KCHDMOJGHJD.NHDJMFCOCIP` `0x7DD9EE0` is the other consumer of the DTO and carries
`'Save {0} has a null UnityAssetId but a non-null UnityAsset, this should not happen.'` — a server
that returns a row whose `UnityAssetId` does not match a requested GUID can surface that line.

## Sibling

`rooms/{0}/subrooms/{1}/saves/no_unity_assets` (slot in the same literal region) is the *other* half
of the same load step — see [subroom-saves-list](subroom-saves-list-wire-shape.md). `unity_assets` appears in
exactly **two** literals in the whole build, these being both of them, so there is no third
unity-asset route to find.
