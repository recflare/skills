# Room load dies with `Unknown prefab <guid>` = the room's SUB-ASSET bundles were never served (2026 build)

> `System.Exception: Failed to load scene 256:1. Unknown prefab <guid>` reported to matchmaking as
> **`FailedToSpawnPlayer / Code 8700`**, preceded by
> `[RecRoomStudio] PrefabRegistry has a null PrefabRegistration or null Prefab at index N`,
> `MaterialMap has a null entry at index N`,
> `[ObjectModel.Dependencies.Load] Invalid RuntimeSpawnableToolConfig (prefabId=…)` and a burst of
> `The referenced script (Unknown) on this Behaviour is missing!`.
> ➡️ A Studio room ships as a **Main bundle plus N sub-asset bundles**. The Main bundle arrived; the
> sub-assets did not, so every cross-bundle `PPtr` resolves to **null** — prefabs, materials and
> MonoScripts alike. **Server-side**: the room-load save record must advertise them in
> **`UnitySubAssets` / `ReferencedUnityAssets`**.

Derived **2026-10-20** from build `20260323.14`, from two live `Player.log` sessions plus the served
bundle itself.

## ⚠️ The decoy that cost the first pass

`%TEMP%\Against Gravity\Rec Room\roomAssetBundle.lz4.assetbundle` is **not** the room's bundle. A
stale copy of it had a `UnityFS` header of `2021.3.41f1` against a `6000.0.27f1` player, which looks
exactly like the smoking gun for a cross-version bundle — and is wrong. The real served bundle is
**`6000.0.27f1`**, matching the player. That temp file is also **not recreated** on a room join, so
its mtime says nothing about the current session.

**Fetch the bundle the server actually serves and read its header** (`room/unity/{roomId}/{name}.assetbundle`
on the CDN) before blaming the Unity version:

```sh
curl -sS -r 0-63 -o head.bin "https://<cdn>/room/unity/<roomId>/<name>.assetbundle"; xxd head.bin
# 00000000  UnityFS.....5.x. / x.6000.0.27f1...   <- the player's version = NOT a version problem
```

## The failing chain, in order

| when | what | where |
|---|---|---|
| 1 | `Processing Studio Asset Bundle...` → **1387 ×** `The referenced script (Unknown) on this Behaviour is missing!` | the Unity player, deserializing the Main bundle |
| 2 | **67 ×** `MaterialMap has a null entry at index N` (indices scattered over 0…169) | material patcher |
| 3 | **24 ×** `[RecRoomStudio] PrefabRegistry has a null PrefabRegistration or null Prefab at index N`, **indices 0…23 consecutive — i.e. EVERY entry** | `RecRoomObjectPrefabManager.RegisterPrefabs` **`0x1AE1A80`** (literal `0xFC46AF8`, null test `0x1AE1C08`: `list[i] == null` → log, skip) |
| 4 | phase `PRE_INSTANTIATE_OBJECTS` → `Invalid RuntimeSpawnableToolConfig` for the same **24 distinct** prefabIds | `RecRoom.ObjectModel.DHUBCHWESHX.EKAWSLCAAKZ` **`0x13C5860`** (literal `0xFCA5030`, use site `0x13C5F13`) |
| 5 | `System.Exception: Unknown prefab {0}` — **fatal** | `PrefabBakingService.NYTRCRTCJFT` **`0x9D01730`** (literal `0xFC4EE68`, ref `0x9D0205F`), via `RWMEENUXJSC(Guid, ObjectPrefabType)` `0x9D02DC0` ← `AsyncLoadSceneOperation` ← `MainLoadService.LoadMain` |
| 6 | `Room Load faulted`, `Unknown error loading room`, bounce to the dorm | `Reporting result FailedToSpawnPlayer / (Code 8700)` |

Step 3 is the cause and step 5 is the symptom. **The count match is the tell**: 24 null registrations
→ 24 unresolvable prefabIds. Steps 1–4 only *log*; only step 5 throws, and only for the one GUID the
scene's bake actually needs.

## Proof it is the sub-asset bundles, not the blob or the Main bundle

Decompress the served bundle (`bundlepeek.py`'s UnityFS/LZ4 path; `blocks=1213`, 159 MB payload) and:

- **All 24 prefabIds ARE in the Main bundle**, as `SerializedGuid.bytes` in **.NET `bytes_le`** order,
  in one contiguous ~45 KB run — the `RecRoomObjectPrefabEntry` array of
  `RecRoomObjectPrefabRegistryAsset`. So the registry is complete; only its *prefab references* are
  null.
- **Each entry names the bundle its prefab lives in.** The on-disk record is plainly readable:

  ```
  10 00 00 00  <16-byte UniqueId>           ; the prefabId the log complains about
  10 00 00 00  <16-byte UnityAssetId>       ; WHICH sub-asset bundle holds the prefab
  NN 00 00 00  (10 00 00 00 <16 bytes>) ×NN ; ReferencedUnityAssetIds
  ```

  For the captured room: 24 entries → 24 owning `UnityAssetId`s + 0…9 referenced each →
  **48 distinct sub-asset bundles required**. `scratchpad/entries.py` walks this.
- The Main bundle's serialized file declares **82 distinct external archives**
  (`archive:/CAB-<hash>/CAB-<hash>`), none of them its own CAB
  (`CAB-d1280b78c90d3cedc7537257afc94108`), and **no** benign `library/unity default resources` /
  `Resources/unity_builtin_extra` among them.
- **Nothing was ever downloaded for them.** `<DownloadBundles>d__4.MoveNext` **`0x1AF2800`** caches
  each sub-asset to disk — `String.Format("{0:N}.SubRoom.SubAsset.{1}.{2}.assetbundle", assetId, kind, 5)`
  (literal `0xFC704F0`) → `Path.Combine` `0x1AF2F0D` → `File.Exists` `0x1AF2F1A` → download. There is
  **not one `*.SubRoom.SubAsset.*.assetbundle` anywhere on disk**, so the client was never told any
  sub-asset existed. (Its state-machine neighbours `<DownloadAndParseData>d__3` and
  `<GetReferencedUnityAssetIdsAsync>d__5` confirm this is the room-load provider
  `RecRoom.RoomLoading.GRGAZRQUYTT`, not a Studio publish path.)

That accounts for all four log signatures at once: the prefabs, the materials **and** the MonoScripts
all live in those 82 archives.

### Where to fix it

`AssetBundleManager.WOLYFBNYLEH(main, IReadOnlyList<MVILAJVLXZW>, IReadOnlyList<MVILAJVLXZW>, ct)`
takes a **main bundle plus two lists**, and `MVILAJVLXZW` is just
`{ Guid GYAFDNEZEBJ(); Task<AssetBundle> MXGDCBSHXEI(); void KTPVZTZZLPV(); }`. Those two lists are
the two list keys on the room's save record:

**`GET rooms/{roomId}/subrooms/{subRoomId}/saves/{saveId}`** →
[subroom-save-by-id](../../wire-shapes/references/endpoints/subroom-save-by-id-wire-shape.md)

| key | CLR | what it must carry |
|---|---|---|
| `UnitySubAssets` | `List<{UnityAssetId: Guid, UnityAsset: string, UnityAssetHash: string}>` | one element per sub-asset bundle |
| `ReferencedUnityAssets` | same element | the transitively referenced ones |
| `UnityAsset` / `UnityAssetHash` | string | the **Main** bundle (this is the part that already works) |

Serving only `UnityAsset` loads only the Main bundle. ⚠️ Both lists are **optional** as far as the
parse goes — `OOIBOPOFICP.CPOBHIECLEN` discards the result of its list check, so `null` or `[]`
parses cleanly and the room then fails 20 s later in the bake with no mention of bundles. That is why
this presents as a prefab problem.

**Extract the required list from the Main bundle** (no server access needed): decompress it, take the
prefabIds out of the `Invalid RuntimeSpawnableToolConfig` lines, and read the `UnityAssetId` +
`ReferencedUnityAssetIds` that follow each one. Then make the save record advertise exactly those.

## `DHUBCHWESHX.EKAWSLCAAKZ` — the three-stage lookup (and why its message lies)

```
0x13c5e2f  call RecRoomObjectPrefabManager$$TryGetPrefabEntry   ; STUDIO / UGC catalog
0x13c5e36  je   0x13c5e48                                       ; miss -> fall through
0x13c5e43  jmp  0x13c60bc                                       ; hit  -> next view

0x13c5e7d  xor  edx, edx                                        ; <-- validate = FALSE
0x13c5e84  call KASFSOHNXPC$$FKUABOUEGZV(Guid, bool)            ; first-party tool fallback
0x13c5e8f  jne  0x13c5f43                                       ; non-null -> next view

0x13c5e9b  call MUKOWWTARUP$$NBOLYNLSHSX(ObjectPrefabType)      ; is a miss tolerable?
0x13c5ea2  jne  0x13c60bc                                       ; true  -> SILENTLY skip
0x13c5f39  call RecRoom.Log$$LIBCEQYQFAM                        ; false -> log 'Invalid …'
```

- Stage 1 is the **Studio/UGC** catalog — `RecRoomObjectPrefabManager.TryGetPrefabEntry` `0x1AE2000`,
  fed **only** by `AssetBundleManager` (`RegisterPrefabs` `0x1AE1A80`, callers
  `AssetBundleManager.BEBKFVAVAWE` `0x1ABE9F0` / `IRSWTGQZDJF` `0x1ABFE80`).
- Stage 2 is **purely local**: `KASFSOHNXPC` builds its dictionary from
  `RuntimeSpawnableToolConfigAsset.LoadAllFromResources()` **`0xF2C3D0`** =
  `Resources.LoadAll<…>("SpawnableTools")` (throws `"No spawnable tool configs loaded!"` if empty),
  and its only GUID-remap table (`QNQACCHVMXF` `0x20FD4A0`) is written from one place,
  `ShapeContainerPrefabSelector.Select` `0x1BF59C0`. **No server payload feeds stage 2** — a Studio
  prefab was never going to be found here.
- ⚠️ **"Invalid …" actually means NOT FOUND.** `FKUABOUEGZV` `0x20FB880` wraps `MVLMRHDZUCW`
  `0x20FC580` → `.ConfigAssetResult { Ok 0, Invalid 1, NotFound 2 }`. `Invalid` is only reachable
  when the `bool` arg is true, which runs the integrity hash
  (`RuntimeSpawnableToolConfigAsset.AppendToHash` → `DQXNGGMPSDQ.ZTCYPMHKYSC` `0x99524C0`) and
  **reports to `RecNet.PlayerReporting.URIIAIWYHPC` with code `0x1F4` (500)**. This caller passes
  **false** (`xor edx,edx` at `0x13C5E7D`), so only `NotFound` is possible and no report is sent.
  Do not chase a tamper/hash problem on the back of this line.

### `NBOLYNLSHSX` is the triage rule — only 3 prefab types are fatal

`RecRoom.DataLayer.MUKOWWTARUP.NBOLYNLSHSX(ObjectPrefabType)` **`0x9937FF0`** buckets the enum by
thousands (`(t/1000)*1000`) and returns **false only for `0x1B58` (7000) and `0x1F40` (8000)**:

| bucket | `ObjectPrefabType` members | miss is… |
|---|---|---|
| 7000 | `PrefabRootGameObject` 7000, `PrefabInternalGameObject` 7001 | **logged** (and bake-fatal) |
| 8000 | `Player` 8000 | **logged** |
| everything else | `Container` 1000-1002, `Shape_Primitive_*` 2000-20xx, `Empty` 4000, … | silently skipped |

So every GUID in the burst is a Unity prefab out of a Studio bundle. For every other prefab type the
GUID is irrelevant — the type identifies the prefab — which is why those misses cost nothing, and
why **stripping the 7000/7001 views from the room blob is the cheap unblock** if the bundles cannot
be served.

## Sibling failure: `Code 8715`, not 8700

A *different* room never reached the bake:

```
ErrException`1[RecRoom.NoEngine.DataStructures.JLTZKNUNHPJ]:
  Error downloading room assets! Try again later or on a better connection.
  at RecRoom.RoomLoading.RoomOperation.FetchDeserializationDataTask.Run (…)
Reporting result FailedToSpawnPlayer / (Code 8715)
```

It returned **123 ms** after `START: FetchDeserializationDataTask.Run('…')`, so it is an **HTTP
status**, not a slow or dropped connection — the "better connection" text is boilerplate.

| code | thrown by | means |
|---|---|---|
| **8700** | `PrefabBakingService` / scene load | assets arrived, a prefab GUID does not resolve |
| **8715** | `FetchDeserializationDataTask` | the room data / asset fetch itself failed |

## Reading the ids and names in these lines

`FetchDeserializationDataTask.Run('21536.29208')` is a **`<roomId>.<subRoomId>` pair**, not the
created room's id (the created rooms were `1509121` / `1509421`). The bundle URL embeds the same
first number — `room/unity/21536/<name>.assetbundle` — which is how to tie a log line to a CDN
object. Template → scene mapping, from `[LoadScene(<TEMPLATE>)]` and `SafeLoadSceneAsync(<scene>)`:

| template | scene |
|---|---|
| `DORM_ROOM` | `dormroom2` |
| `MAKER_ROOM` | `Basement` |
| `MAKER_ROOM_2` | `ugcr2` |

⚠️ The client loads **its own** `ugcr2` scene; the Studio scene inside the bundle
(`Assets/s/a/Rooms/<RoomName>/<RoomName>-<Sub>.unity`, the only `Assets/` path in the payload) is
content, not the loaded scene. Worth reading anyway — **if it names a different room than the one
being joined, the server has paired the wrong bundle with the blob.**

## Why you cannot check the client's catalogs from disk

**The 2026 client's Unity data files are encrypted at rest.** `globalgamemanagers`,
`resources.assets`, `sharedassets*` and even `ScriptingAssemblies.json` begin
`00 00 52 52 00 00 52 52` ("..RR..RR") followed by high-entropy bytes; `strings` yields nothing and
the Resources path literal `SpawnableTools` is absent. So "is GUID X in this build?" cannot be
answered by grepping `RecRoom_Data` — only the runtime can answer it.

Script identity, at least, checks out: the Main bundle's MonoScripts name assembly
**`RecRoom.Studio.Common.Runtime`**, namespace **`RecRoom.Core.Studio`**, and both that assembly name
and every referenced class (`RecRoomObjectPrefabRegistryAsset`, `RecRoomObjectPrefabEntry`,
`RecRoomStudioConsumableItemRegistryAsset`, `RecRoomProjectileRegistryAsset`,
`RecRoomParticleVfxRegistryAsset`, `RecRoomAudioClipRegistryAsset`, `RecRoomVisualPostProcessing`)
are present in `global-metadata.dat`. Studio-facing types are **not** obfuscated.

## Re-confirmed 2026-10-27 — nothing has changed server-side

Second account ("user 2") joined **21536/29208** at `13:45:03`, scene `ugcr2`, save
**`SubRoomDataSaveId:109350`**. Failure is **bit-identical** to the 2026-10-20 capture:

| signature | 10-20 | 10-27 |
|---|---|---|
| `The referenced script (Unknown) on this Behaviour is missing!` | 1387 | **1387** |
| `MaterialMap has a null entry at index N` | 67 | **67** |
| `[RecRoomStudio] PrefabRegistry has a null …` | 24 | **24** |
| distinct `prefabId=` in the `Invalid RuntimeSpawnableToolConfig` burst | 24 | **24** |
| fatal GUID | — | `9cb86bbc-0745-f924-c851-a87245eefc86` |
| report | 8700 | **8700** |

Timeline (`Player.log`, all one 54-second process): dorm `78/98` loads to COMPLETE → `13:45:03`
`devin is leaving to go to room: 21536/29208 instance:1606422` → phases run cleanly as far as
`PRE_INSTANTIATE_OBJECTS` at `13:45:09` → the 69-line `Invalid RuntimeSpawnableToolConfig` burst →
`Unknown prefab 9cb86bbc…` → `JoinRoomLoadWithPhoton threw exception: Room Load faulted` →
`Reporting result FailedToSpawnPlayer / (Code 8700)` → `Unknown error loading room (Code 8700)` →
`13:45:11` `devin is leaving to go to room: 78/98` = **bounced to the dorm**. That bounce is what
reads as "kicked"; the process never crashes.

**`FetchDeserializationDataTask.Run('21536.29208')` SUCCEEDED** (START `13:45:07.9409`, END
`13:45:08.4062`, 465 ms). So on this room the blob fetch is fine and only the **8700** branch is in
play — the 8715 sibling in this note is a *different* failure, and seeing a clean START/END pair for
`FetchDeserializationDataTask` is the one-line way to tell them apart.

**Still zero sub-asset bundles on disk.** A recursive search of `%LOCALAPPDATA%\..`/all of `AppData`
for `*SubAsset*` returns **no** `*.SubRoom.SubAsset.*.assetbundle` — only this investigation's own
scratchpad file. `grep -c "SubRoom.SubAsset"` over both `Player.log` and the 27 MB `Player-prev.log`
is **0**. The client has never been told a sub-asset exists, in any session.

### The minimal unblock for this one GUID

`scratchpad/bundle21536/required-subassets-21536.txt` line 11:

```
9cb86bbc-0745-f924-c851-a87245eefc86  ->  asset e4592dea-ef09-4439-b364-ad3c224035f8  refs 5
```

So the *fatal* prefab needs sub-asset **`e4592dea-ef09-4439-b364-ad3c224035f8`** plus its 5
referenced assets. Serving only those will get the bake past this GUID but will very likely throw on
the next one the scene bakes — the full 48 is the real fix.

### ⚠️ A clean Studio bundle elsewhere does NOT prove the sub-asset path works

The previous session joined **18426/27937** (save `117193`, scene **`reccenter`**) **10 times** and
logged `Processing Studio Asset Bundle...` **20 times** with **0** `PrefabRegistry has a null`, **0**
`MaterialMap has a null`, **0** `Invalid RuntimeSpawnableToolConfig` and only **2** missing scripts.
Tempting to read that as "the pipeline works, 21536 is special" — but that session also downloaded
**no sub-asset bundles at all**, so 18426's Main bundle is simply **self-contained**. It is evidence
that a complete Main bundle resolves cleanly, and **no** evidence about `UnitySubAssets` serving.
21536 is the first room on this server that needs cross-bundle prefabs.

### Cross-referencing the recflare server log by timestamp

This log carries **three different clocks** on the same line, which is how the first pass nearly
mis-dated the session:

- the `[HH:MM:SS]` prefix RR writes is **Pacific** (`[13:45:10]`)
- Dissonance's own `(HH:MM:SS.mmm)` is **UTC** (`(20:45:10.860)` on that same event, +7h)
- the file mtime is **system local** (here Eastern, 16:45)

➡️ When matching a `Player.log` line against a server-side request log, **add 7 hours** to the
bracket timestamp (PDT), not the system offset.

### 2026 names for the save DTOs — and the element shape is UNCHANGED

The save shape in [subroom-save-by-id](../../wire-shapes/references/endpoints/subroom-save-by-id-wire-shape.md)
was derived on the **2025** build. Checked against 2026 on 2026-10-27: these types are **fully
unobfuscated** on `20260323.14`, so no re-derivation is needed to name them.

| 2025 | 2026 |
|---|---|
| `.OOIBOPOFICP` | **`RecNet.Rooms.SubRoomDataSaveWithUnityAssetsDTO`** |
| `.GCLKKDPHAON` (base) | **`RecNet.Rooms.SubRoomDataSaveDTO`** |
| `.BAFMNFOKJIA` (element) | **`RecNet.Rooms.BakedUnitySubAssetDTO`** |
| — | `RecNet.Rooms.SaveSubRoomRequestDTO` (the write side) |

`msig.py RecNet.Rooms.SubRoomDataSaveWithUnityAssetsDTO` still declares
`List<BakedUnitySubAssetDTO> UnitySubAssets` / `ReferencedUnityAssets` plus `UnityAsset` /
`UnityAssetHash`, and `msig.py RecNet.Rooms.BakedUnitySubAssetDTO` gives **exactly the three**
properties the 2025 note records:

```
Guid   UnityAssetId
string UnityAsset
string UnityAssetHash
.ctor() / .ctor(Guid unityAssetId)
```

➡️ **Key drift is ruled out.** A tempting theory for "the lists are served but ignored" was that 2026
renamed the element's keys, so Utf8Json would silently drop them and leave records with a null
`UnityAsset` — which would look exactly like this failure. It does not: the 2025-derived shape is
still correct, and the reason nothing downloads is simply that **nothing is being served**.

### ⚠️ Do not `callxref` a trivial property getter on this build

IL2CPP **shares one body across every identical trivial getter**, so a getter RVA is not an anchor
for one type. `get_UnitySubAssets` resolves to `0xD3A0F0`, and `callxref 0xD3A0F0` returns **53**
sites, almost all in `System.Data` (`DataTable$$set_Namespace`, `ConstraintCollection$$Add`, …).
`get_ReferencedUnityAssets` `0xD106F0` gives 10 sites in `RecRoom.ObjectModel.Systems` and
`CircuitsV2`. The collision is visible directly in `mfind`: `0xD11E20` is simultaneously
`SaveSubRoomRequestDTO$$get_ReferencedUnityAssetIds`, `BakedUnitySubAssetDTO$$get_UnityAssetHash`
and `ConsumableConfigurationData$$get_UnityAssetData`.
➡️ To find who consumes a DTO field, anchor on the **route facade** or a **string literal**, never on
a `get_`/`set_` RVA.

### The payload this room needs, split into the two lists

`scratchpad/mkpayload.py` turns `required-subassets-21536.txt` into the skeleton at
`scratchpad/save-109350-unityassets-skeleton.json`. The split is clean:

| list | count | what |
|---|---|---|
| `UnitySubAssets` | **24** | the owning bundle of each of the 24 failing prefabIds |
| `ReferencedUnityAssets` | **24** | the transitively referenced bundles that are not themselves an owner |
| total distinct | **48** | every owner also appears in the distinct set (0 missing) |

Only `UnityAssetId` can be recovered from the Main bundle. **`UnityAsset` (the CDN path) and
`UnityAssetHash` have to come from the server's own asset table** — they cannot be derived
client-side, and the client needs both to build the download URL and the cache filename
(`{assetId:N}.SubRoom.SubAsset.{kind}.5.assetbundle`).

## Unrelated noise in the same window

- `Error deserializing SpawnableTool (Marker)(Clone): Serialized GUID … does not match prefab value …`
  arrives after the bounce to the dorm — a separate per-object deserialize mismatch.
- `RoomQueryManager.QueryStaticListSource` NRE, `giftdropstore/{type}` 404,
  `Malformed Response: '[]'` on objectives — see
  [post-join-residual-log-items-2026](post-join-residual-log-items-2026.md).
- The log simply ends after `OnApplicationFocus False`; **no crash dump is written**. The process does
  not crash — the room load does.
