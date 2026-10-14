# `FailedToSpawnPlayer (Code 8700)` — a Studio bake served without its 81 dependency bundles

> `Unknown error loading room (Code 8700)` with
> `System.Exception: Failed to load scene 256:1. Unknown prefab <guid>`.
> ⚠️ **The named prefab is a red herring**, and so is every "missing script" line above it. The room's
> Studio bake downloaded fine, but it is **one of 82 serialized files**, and the server told the client
> about only that one. Every cross-bundle pointer therefore resolved to null.
> ⚠️ Not a crash — the client reports the result to matchmaking and returns you to the previous room.

Diagnosed **2026-10-14** on build `20260323.14`, room `21536/29208` `RunTheBlock`, immediately after
fixing the scene GUID in
[basement-objectid-invalid-crash-2026](basement-objectid-invalid-crash-2026.md).

## ⚠️ CORRECTION — this is NOT a bake/build version mismatch

The first version of this note concluded that the bake had been built against a different client
assembly, because Rec Room re-rolls obfuscated type names per build. **That was wrong**, and the
objection that killed it is the obvious one: there are thousands of Studio rooms, and Rec Room
plainly does not re-bake them on every release. Two measurements settle it:

1. **Unity-serialized classes are NOT obfuscated.** Of the 2,649 types in `20260323.14` that define
   `Awake`/`Start`/`Update`/`OnEnable`/…, only **223 (8.4%)** have an obfuscated 11-char leaf name.
   The other 91.6% keep real names — `RecRoom.RigidbodyEx`, `AGUI.StackedUI.*`,
   `MClusterManagerBehaviour`. That is the standard obfuscator constraint: you cannot rename a type
   Unity serializes by name, or every scene, prefab and bundle breaks. **Bakes are portable across
   builds by design.**
2. **Every script the bake references resolves in this client.** The bake's MonoScript table is
   intact and in the clear — 25 distinct `(m_ClassName, m_Namespace, m_AssemblyName)` triples across
   four assemblies, and **25/25 exist in this player's metadata**:

   | assembly | count | examples |
   |---|---|---|
   | `RecRoom.Studio.Common.Runtime` | 14 | `RecRoom.Core.Studio.MaterialMap`, `.RecRoomObjectPrefabRegistry`, `.RecRoomObjectPrefabRegistryAsset`, `.RecRoomParticleVfxRegistry`, `.RecRoomAudioClipRegistry`, `.RecRoomProjectileRegistry`, `.RecRoomStudioConsumableItemRegistry`, `.RecRoomVisualPostProcessing` |
   | `Unity.RenderPipelines.Universal.Runtime` | 7 | `Bloom`, `Tonemapping`, `UniversalAdditionalCameraData` |
   | `Unity.RenderPipelines.Core.Runtime` | 2 | `Volume`, `VolumeProfile` |
   | `UnityEngine.UI` | 2 | `EventSystem`, `StandaloneInputModule` |

So nothing about class identity is broken. **Keep this correction in mind before blaming a build
mismatch for anything bundle-shaped.**

## ✅ The actual cause: 81 of 82 serialized files were never downloaded

The downloaded bake's own serialized file is `CAB-d1280b78c90d3cedc7537257afc94108` (467 internal
references). Alongside it the file names **81 other CABs** as `archive:/CAB-…/CAB-…` externals:

```
distinct CAB ids in the bake:                  82   (1 own + 81 external)
present in the client's shipped Addressables:   0   (checked against all 2,787 bundles)
```

So those 81 are not client content and not optional — they are **other baked Unity assets that have
to be downloaded**, and nothing fetched them. In Unity, an unresolved external file makes every
pointer into it `null`, including `m_Script`, which is why the log reads the way it does.

## ✅ Confirmed from Rec Room's own artifacts: the bake is NOT self-contained

Rec Room served **two** files for this room's `UnityAssetId` `4a8f6366-…`, both genuine
(the 66 MB one is byte-identical to what the client downloaded — md5
`5b12bea158b34a21db587b986f4c7468`, matching the response `etag`):

| file | size | SerializedFile `targetPlatform` | meaning |
|---|---|---|---|
| `b8g5tbeq37bajy4f8j2x3iwb9.assetbundle` | 66,637,095 | **5** | Windows — **correct for a PC client** |
| `e3yi79poixrjakf0ana10c92k.assetbundle` | 18,006,100 | **13** | Android / Quest |

✅ **So the platform variant being served is right**, and `Version: 5` in the `baked/bulk` row is
irrelevant (that DTO has the shared no-op post-deserialize hook, so the client never checks it).

Both files carry the **same** internal serialized file `CAB-d1280b78c90d3cedc7537257afc94108`, the same
content (`Dumpster` ×69, `PrefabRegistry` ×6, `MaterialMap` ×7, both target prefab GUIDs) and the same
**81 external references** — but their 81 CAB names are **completely disjoint**, so external identity is
per-bake-build, not per-content.

⚠️ **Verified by parsing the SerializedFile header, not by grepping.** Both are v22,
`metadataSize = 192270`, `dataOffset = 192320`, and **exactly 81 distinct
`archive:/CAB-…/CAB-…` strings fall inside the metadata region** (the externals table; the other 240
hits of that pattern are in the data section and must not be counted). Do this parse before concluding
anything about a bundle's dependencies:

```python
import struct, re
d = open('decompressed.bin','rb').read()      # concatenated LZ4 blocks
dataoff = struct.unpack_from('>q', d, 0x20)[0]
ext = {m.group() for m in re.finditer(rb'archive:/CAB-[0-9a-f]{32}/CAB-[0-9a-f]{32}', d)
       if m.start() < dataoff}
print(len(ext))        # 0 = self-contained; 81 here
# platform: targetPlatform is the int32 right after the null-terminated unity version at 0x30
```

**Reading A (self-contained bake) is therefore dead.** A real Rec Room room bake depends on 81 sibling
bundles, and **none of the 81 are in this client's 2,787 shipped Addressables bundles** — for either
variant. They must be downloaded.

## Where the 81 belong: the save's `UnitySubAssets`

The 19-key save shape has exactly four slots for this, and the shape is already derived
([subroom-save-by-id](../../wire-shapes/references/endpoints/subroom-save-by-id-wire-shape.md)); on 2026 the DTO is
**`RecNet.Rooms.SubRoomDataSaveWithUnityAssetsDTO`**, formatter
`Utf8Json.Formatters.RecNet.Rooms.USBIHNXLYFL` `.ctor 0x8f0d830` (2025: `.OOIBOPOFICP` /
`ADNIOKLDNOI`):

| key | CLR |
|---|---|
| **`UnitySubAssets`** | `List<{UnityAssetId: Guid, UnityAsset: string, UnityAssetHash: string}>` |
| `ReferencedUnityAssets` | same element type |
| `UnityAsset` | string — the main bundle's blob path |
| `UnityAssetHash` | string |

recflare returns all four empty/null, so the client fetched the main bake through
`unity_assets/baked/bulk` and nothing else.

**`UnitySubAssets` is the slot** — one `UnityAssetId` whose bake is split across many bundles is what
"sub-assets" names, and it explains why `ReferencedUnityAssetIds` is legitimately `[]` in Rec Room's own
data (that list is for *other* UnityAssets a save references, e.g. inventions, not for the pieces of
this one).

⚠️ **Not yet proven**, because the real-Rec-Room export on hand is the **base** record — it does not
carry the four unity-asset keys at all, so it says nothing about `UnitySubAssets`:

```json
{"SubRoomDataSaveId":227575672,"SubRoomId":1384652020053214301,
 "UnityAssetId":"4a8f6366-9ec7-4bc0-81ce-e616b5a0bd31",
 "DataBlob":"2pp9khb214onhtjlxgqzjlek6.room","ReferencedUnityAssetIds":[],
 "PersistenceVersion":251,"OMVersion":198,"UgcSubVersion":449, …}
```

**Settle it by asking real Rec Room for the with-unity-assets shape**, which is exactly what those
query params are for:

```
GET rooms/{roomId}/subrooms/{subRoomId}/saves/{saveId}?unityAssetTarget=<n>&unityAssetVersion=<n>
```

If `UnitySubAssets` comes back with ~81 `{UnityAssetId, UnityAsset, UnityAssetHash}` rows, that is the
whole fix: mirror those 81 blobs and return the same list. The client needs no second round trip —
the filenames and hashes are inline.


## The failure sequence, in log order

| t | line |
|---|---|
| 123.5513 | `Processing Studio Asset Bundle...` |
| 123.55–123.98 | **`The referenced script (Unknown) on this Behaviour is missing!`** and `… (Game Object '[Dumpster_Instanced] (16)')` — **2,770 lines** |
| 123.9848+ | **`MaterialMap has a null entry at index 0 / 3 / 5 / 8 / 13 …`** (30+) |
| 124.2771+ | **`[RecRoomStudio] PrefabRegistry has a null PrefabRegistration or null Prefab at index 0 … N`** |
| 126.25+ | **`[ObjectModel.Dependencies.Load] Invalid RuntimeSpawnableToolConfig. (prefabId=…, persistenceId=…)`** — **~30 distinct prefab ids** |
| 126.2899 | `[ObjectModel.Serialization.Streaming] System.Exception: Unknown prefab 9cb86bbc-…` |
| 126.8040 | `Reporting result FailedToSpawnPlayer / (Code 8700) to RecNet Matchmaking` |

Note the shape of this: the registry ScriptableObjects **did** bind (their classes are in the bake
itself) — the client successfully enumerates the registry and finds its *entries* null. That is the
tell for a missing external file rather than a missing class.

⚠️ **`The referenced script … is missing!` has a baseline of 8 at every startup** (`'<null>'`,
`'[DebugConsole]'`, `''`) in a clean log too. Count them and look at *where* they cluster: 2,770 of
them between `Processing Studio Asset Bundle` and the registry read is the signal; the 8 at boot are
not.

Read the block **top-down**. `Invalid RuntimeSpawnableToolConfig` firing for ~30 different prefab ids
means the registry is empty; chasing the one GUID in the final exception leads nowhere.

## Where the exception comes from

`'Unknown prefab {0}'` literal `0xFC4EE68`, and a sibling `"Unknown prefab {0} '{1}'"` `0xFC4F1B8`,
have **one xref each**, both inside

```
RecRoom.ObjectModel.Systems.PrefabBakingService.NYTRCRTCJFT(RecRoom.DataLayer.RRObjectPrefabData a) -> .Baked
    0x9d01730, real bounds 0x9d01730..0x9d020c2
```

The variant matters: the `{0} '{1}'` form carries a **prefab name**, the `{0}`-only form does not.
Our log shows the `{0}`-only form — the client had no name either, consistent with an empty registry.

Surfaced through `RecRoom.ObjectModel.Transmission.MainLoadService.DMCOLWWIUMO(RRSceneLoadOperation)`
← `MainLoadService.LoadMain(SerializedDataWrapper, …)` ← `RoomOperation.DIZANNKBGBB`. The
`Failed to load scene {0}. ` prefix is literal `0xFCD0F28`.

## ✅ What now works, and a new scene-name mapping

With `UnitySceneId` corrected to `MAKER_ROOM_2` the whole pipeline runs — no `Crash!!!`, phases
advance through `DATA_DOWNLOADED` — and the log shows

```
[RoomLoad.RoomManager] START: LoadScene.SafeLoadSceneAsync(ugcr2)
```

✅ **`MAKER_ROOM_2` → Unity scene `ugcr2`**, now recorded in `SCENES.md` next to
`MAKER_ROOM` → `Basement` and `DORM_ROOM` → `dormroom2`.

## How to act on it

1. **Fetch the with-unity-assets save shape from real Rec Room** for this save, with
   `unityAssetTarget`/`unityAssetVersion` set, and read `UnitySubAssets`. That is the list of the 81
   missing blobs.
2. **Mirror those blobs and return the list** in `UnitySubAssets` on your own
   `GET rooms/{id}/subrooms/{id}/saves/{saveId}`. Also fill `UnityAsset`/`UnityAssetHash` with the main
   bake while you are there.
3. **Verification that needs no log reading:** `HTTPCache` should then hold **82** `UnityFS` bodies for
   this room instead of 1. Count recent `*.data` files whose first 7 bytes are `UnityFS`.
4. **Pick the blob by platform, not by filename.** Read the bundle's own `targetPlatform` (int32 after
   the unity-version string at `0x30`): **5** = Windows, **13** = Android. Serving the Android variant to
   a PC client would be a different, equally confusing failure.
4. **Same root class as the `Marker` prefab mismatch.** The dorm load still logs
   `Error deserializing SpawnableTool (Marker)(Clone): Serialized GUID 0848fb3e-… does not match prefab value e469ee80-…`
   ×8 — also a cross-file identity that does not resolve. Worth re-checking once the dependency
   serving is fixed.

## Recovering and inspecting a downloaded bake

BestHTTP caches response bodies, so the bundle can be read straight off disk — this is what settled
the whole question:

```
%USERPROFILE%\AppData\LocalLow\Against Gravity\Rec Room\HTTPCache\
  406        <- response headers only; the request URL is NOT stored
  406.data   <- 66,637,095 bytes
```

```
HTTP/1.1 200 OK   content-length: 66637095
etag: "5b12bea158b34a21db587b986f4c7468"   last-modified: Wed, 14 Oct 2026 16:05:42 GMT
server: cloudflare   cf-cache-status: DYNAMIC   server-timing: cfOrigin;dur=61
```

Header: `UnityFS` / version **8** / `5.x.x` / **`6000.0.27f1`** — exactly the client's engine. Decompress
all 1,213 LZ4 blocks (`bundlescan.py`'s header walk; `ver>=7` needs the 16-byte alignment) → 158,909,064
bytes. Useful probes on the result:

| probe | result |
|---|---|
| `Dumpster` ×16, `PrefabRegistry` ×3, `MaterialMap` ×4 | real `RunTheBlock` content |
| `Assembly-CSharp`, `MonoBehaviour` | 0 — the asset type trees are stripped, but the MonoScript table survives with `m_ClassName`/`m_Namespace`/`m_AssemblyName` |
| `CAB-[0-9a-f]{32}` | **82 distinct** — the dependency count |
| prefab `9cb86bbc-0745-f924-c851-a87245eefc86` | **FOUND** @ `11197064` |
| prefab `816b1ca3-747b-b294-5ba2-87cb653f3aa9` | **FOUND** @ `11191912` |

⚠️ **Search GUIDs as `uuid.UUID(g).bytes_le`.** Neither the dashed/undashed ASCII form, the big-endian
bytes, nor Unity's per-word-reversed hex form matches — only .NET's little-endian layout does. Grepping
for the text form finds nothing and reads as absence.

⚠️ **To test whether a CAB is client-shipped, read bundle headers, not bundle bodies.** A bundle's
serialized-file names live in its **compressed blocksInfo directory**, so `grep` over
`StreamingAssets/aa` finds nothing even when the CAB is there, and a full-payload decompression of
2,787 bundles is wasted work. Decompress only the blocksInfo block and regex `CAB-[0-9a-f]{32}` out of
it — all 2,787 index in seconds. Bundle *filenames* are not CAB ids, so testing `<cab>.bundle` also
proves nothing.

## Triage shortcut for next time

```bash
grep -nE 'Reporting result|referenced script|PrefabRegistry has a null|MaterialMap has a null|Invalid RuntimeSpawnableToolConfig|Unknown prefab' Player.log
```

- thousands of `referenced script … missing` **after** `Processing Studio Asset Bundle`, plus null
  registry entries and many `Invalid RuntimeSpawnableToolConfig` ⇒ **missing dependency bundles**, this
  note.
- `Invalid RuntimeSpawnableToolConfig` for **one** id with the registry otherwise healthy ⇒ a genuinely
  missing asset; chase that GUID.
- Sub-millisecond `[AssetBundle_Download]` in the `StackTimer` block ⇒ nothing fetched at all, i.e. a
  null `Filename` — see
  [rooms-unity-assets-baked-bulk](../../wire-shapes/references/endpoints/rooms-unity-assets-baked-bulk-wire-shape.md), not this note.
