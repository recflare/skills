# Subroom saves/{saveId} wire shape (the WITH-unity-assets save)

> GET rooms/{roomId}/subrooms/{subRoomId}/saves/{saveId} returns a **BARE 19-key object** — the
> subclass `.OOIBOPOFICP`, which is the 15-key `.GCLKKDPHAON` save record **plus 4 unity-asset keys
> that come FIRST** (`UnitySubAssets`, `ReferencedUnityAssets`, `UnityAsset`, `UnityAssetHash`).
> It is **not** a `{Results, TotalResults}` page and **not** the plain 15-key base that
> `saves/no_unity_assets` returns.

Derived **2026-10-07** from build `20250718.01`. This is the endpoint that
[subroom-saves-list](subroom-saves-list-wire-shape.md) predicted but did not derive ("there is a subclass
`OOIBOPOFICP : GCLKKDPHAON` adding two unity-asset lists that a different endpoint returns"). It
adds **four** keys, not two.

`GET https://rooms.<host>/rooms/{roomId}/subrooms/{subRoomId}/saves/{saveId}` — service
**16 = Rooms**, facade `OALMDGJKBJH`, verb **GET** (`HttpMethod` statics `[rcx+8]` at `0x7DF612A`).
Path is `String.Format("rooms/{0}/subrooms/{1}/saves/{2}", roomId, subRoomId, saveId)`, whole-path
template literal **`0xD1A8C98`**.

Client entry **`OALMDGJKBJH.CFBBMMGMFJJ`** `0x7DF6010` (+0x200):

```
Task<.OOIBOPOFICP> CFBBMMGMFJJ(long roomId, long subRoomId, long saveId,
                               byte? unityAssetTarget, int? unityAssetVersion,
                               CancellationToken)
```

Send is **`OALMDGJKBJH.NDBMFFLDBBK<T>`** (methodref `0x7DF61BB`) — the facade's **description-less**
helper, so **no envelope** — generic inst **#14931 = `.OOIBOPOFICP`**. There is no
`friendlyActionDescription` literal in the method, which is the cross-check
([rooms-room-by-id](rooms-room-by-id-wire-shape.md) uses the same helper).

The method does not build `AKJEAMCCEOH` itself; it tail-calls the facade-bound helper, which supplies
the service. So there is no `mov r8d, 0x10` to read here — svc 16 comes from `OALMDGJKBJH`.

## Query params — two, both optional

Added by the closure **`KDCGAHKPACJ.GFFAGAEOGDN`** `0x7DF09D0` (+0xD0) via `ELHKHFJEHLM`:

| param | CLR |
|---|---|
| `unityAssetTarget` | `byte?` |
| `unityAssetVersion` | `int?` |

Verb is **GET**, so these are a real **query string**
([elhkhfjehlm-verb-dependent-params](../conventions/elhkhfjehlm-verb-dependent-params.md)). They are the same pair the
listing route takes. No `ELKIBCPINAP`, so no body.

## Response — 19 keys, DERIVED-FIRST

Formatter **`ADNIOKLDNOI` `.ctor 0x778F5C0`** (+0x19B0), `____stringByteKeys` run
`0x7790836`..`0x7790DAC`. Utf8Json emits the **most-derived** members before the base, so the four
new keys lead:

```
 1 UnitySubAssets          2 ReferencedUnityAssets   3 UnityAsset
 4 UnityAssetHash
```

| # | key | CLR | off |
|---|---|---|---|
| 1 | `UnitySubAssets` | `List<.BAFMNFOKJIA>` | 0x90 |
| 2 | `ReferencedUnityAssets` | `List<.BAFMNFOKJIA>` | 0x98 |
| 3 | `UnityAsset` | string | 0xA0 |
| 4 | `UnityAssetHash` | string | 0xA8 |

then the 15 base keys of `.GCLKKDPHAON`, unchanged from
[subroom-saves-list](subroom-saves-list-wire-shape.md) / [rooms-subrooms-data](rooms-subrooms-data-wire-shape.md):

```
 5 SubRoomDataSaveId       6 SubRoomId               7 UnityAssetId
 8 ReferencedUnityAssetIds 9 DataBlob               10 DataBlobHash
11 PersistenceVersion     12 OMVersion              13 SavedByAccountId
14 SavedOnPlatform        15 SavedOnDeviceClass     16 Description
17 ModerationState        18 CreatedAt              19 UgcSubVersion
```

### `.BAFMNFOKJIA` — the asset element, 3 keys

Formatter **`AECFLKKNDND` `.ctor 0x7764480`** (+0x4B0), run `0x77647E2`..`0x7764884`:

| # | key | CLR | off |
|---|---|---|---|
| 1 | `UnityAssetId` | **`System.Guid`** | 0x10 |
| 2 | `UnityAsset` | string | 0x20 |
| 3 | `UnityAssetHash` | string | 0x28 |

⚠️ `UnityAssetId` here is a **non-nullable `Guid`**, unlike the save's own `UnityAssetId` (key #7),
which is `Guid?`. Utf8Json wants the plain 36-char dashed form.

```json
{ "UnitySubAssets": [
    { "UnityAssetId": "1fa06e3c-c307-4c11-a91b-1fabcddb8a96",
      "UnityAsset": "2026-10-07/ab12….bundle", "UnityAssetHash": "R0SVMvrAW4n…" } ],
  "ReferencedUnityAssets": [],
  "UnityAsset": "2026-10-07/cd34….bundle",
  "UnityAssetHash": "9fK2…",
  "SubRoomDataSaveId": 79472, "SubRoomId": 29208,
  "UnityAssetId": "1fa06e3c-c307-4c11-a91b-1fabcddb8a96",
  "ReferencedUnityAssetIds": [],
  "DataBlob": "2026-10-07/c63e2467-…", "DataBlobHash": null,
  "PersistenceVersion": 227, "OMVersion": 1,
  "SavedByAccountId": 205, "SavedOnPlatform": 0, "SavedOnDeviceClass": 2,
  "Description": "test1", "ModerationState": 0,
  "CreatedAt": "2026-10-07T00:00:00Z", "UgcSubVersion": 227 }
```

`UnityAsset` / `UnityAssetHash` appear **twice over** — once at the top level and once per element —
and share the backing-field names `EJMMGHFAJKE` / `MNPMJFJAKIH` on both types. The top-level pair is
the save's own baked bundle; the per-element pair is each sub-asset's.

Enums are unchanged: `SavedOnPlatform` `NLJFAOJNHDJ` (All -1, Steam 0, Oculus 1, PlayStation 2,
Xbox 3, RecNet 4, IOS 5, GooglePlay 6, Standalone 7, Pico 8, Switch 9), `SavedOnDeviceClass`
`KPOJCHHIMDA` (Unknown 0, VR 1, Screen 2, Mobile 3, VRLow 4, Quest2 5), `ModerationState`
`CCJNDAADAJO : byte` (None 0 … ModeratorDenied 6).

## The post-deserialize hook is NOT a validator

`OOIBOPOFICP.CPOBHIECLEN` is **`0x7E1DD60`** — a real body, not the shared `0xA60520` stub, which
makes it look like required-field validation. It is not. All 0x30 bytes are:

```
EADLCOCJAGD.IANBCAFGFNL(this.UnitySubAssets, 0);        // 0x7E1DD72, result DISCARDED
EADLCOCJAGD.IANBCAFGFNL(this.ReferencedUnityAssets, 0); // 0x7E1DD85, tail-jmp
```

and `static bool EADLCOCJAGD.IANBCAFGFNL(IEnumerable<T>)` `0x7623250` starts with
`test rbx, rbx / je 0x762345C`, where `0x762345C` is `xor al, al ; ret` — **a plain `return false`,
no throw**. `CPOBHIECLEN` is declared `void`, so the bool is discarded either way.

**So neither list is required and the hook cannot fail the parse** — `null`, `[]` and a populated
array are all safe for both. The base `GCLKKDPHAON.CPOBHIECLEN` and `BAFMNFOKJIA.CPOBHIECLEN` are
both the `0xA60520` no-op, so **no key on this route is mandatory**; every omission lands as
`null` / `0`.

This is the trap the skill warns about — a non-stub `CPOBHIECLEN` RVA does not mean validation.
Read the body before treating a field as required. (Serving `[]` rather than `null` is still better
practice, because consumers downstream of the parse may not be as tolerant; see
[circuitchiplists](circuitchiplists-wire-shape.md), where a cached null list NREs well after a clean parse.)

## Three routes under `saves/`, three different shapes

| route | response |
|---|---|
| `GET .../saves/no_unity_assets` | bare page `{Results: [15-key .GCLKKDPHAON], TotalResults}` ([subroom-saves-list](subroom-saves-list-wire-shape.md)) |
| **`GET .../saves/{saveId}`** | **bare 19-key `.OOIBOPOFICP`, no page wrapper** (this note) |
| `POST .../data` | enveloped `{Value:{Room, SubRoomDataSave}, …}` ([rooms-subrooms-data](rooms-subrooms-data-wire-shape.md)) |

`no_unity_assets` names the **element type**, not omitted fields — it is the one that returns the
plain base. Returning the page wrapper from `saves/{saveId}`, or the bare object from the listing,
throws `IONCMJIACFI` either way.

⚠️ `OMVersion` (key #12) is the field that can refuse a room load outright when it is `0` — see the
`OMVersion` section of [rooms-subrooms-data](rooms-subrooms-data-wire-shape.md).
