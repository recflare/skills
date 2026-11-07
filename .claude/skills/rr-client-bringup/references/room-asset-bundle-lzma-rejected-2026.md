# Room asset bundle rejected: LZMA storage blocks — "requires recompression" (2026)

> `InvalidOperationException: Cannot create a DirectlyLoadableAssetBundleSource from an AssetBundle
> that requires recompression`, surfaced to the player as
> **`Error downloading room assets! Try again later or on a better connection.`**
> It is **not** a download, network or hash problem. The bundle arrived intact and the client
> **rejected its compression format**: Rec Room's room-asset loader only accepts UnityFS storage
> blocks that are **uncompressed or LZ4/LZ4HC and NOT streamed**. A bundle built with Unity's
> **LZMA ("Standard") compression** has a single block with flags `0x41` and is refused.

Diagnosed **2026-11-04** on build `20260323.14`, room **`^MyLittleMonsters` (37468.53323)**,
instance 1704146, from a live `Player.log` plus the client's own validator.

## The log signature

```
[RoomLoad.RoomManager] START: StartAssetBundlePrefetch
InvalidOperationException: Cannot create a DirectlyLoadableAssetBundleSource from an AssetBundle that requires recompression
  at RecRoom.Injection.KCDCBWKPCKW.BBOFVPTQNEL (Guid a, RecNet.FilenameWithHash b, OnDownloadProgressDelegate c, ct)
  …
  at RecNet.Core.IDLRUCGALFZ (string a, string expectedHash, bool b, bool c, …)
  at RecNet.Core.CNJVQUKMZDV (…)  ->  RecNet.Core.OOLFEOLDQTG (HttpMethod, Service, string, …)
  …
RecRoom.Injection.<CreateDirectlyLoadableAssetBundleSource>d__7:MoveNext()
  at RecRoom.Injection.KCDCBWKPCKW.VGILEPWRVUZ (Nullable<T> a, IReadOnlyCollection<T> b,
                                                IReadOnlyCollection<T> c, RecNet.Rooms.AssetBundleLoadSource …)
[RoomLoad.RoomManager] END: StartAssetBundlePrefetch
ErrException`1::Error downloading room assets! Try again later or on a better connection.
```

⚠️ **The message blames the network and the hash check passed.** `IDLRUCGALFZ` is below the throw in
the stack and already called `SetResult`, so the bytes were downloaded (or served from cache) and
matched `expectedHash`. Nothing about the transfer is wrong. ⚠️ The retry message repeats ~5× and the
join then proceeds far enough to connect Tachyon and load `ugcr2`, so the log looks like a *late*
failure; the real one is this single line.

## The validator — exactly what the client accepts

`RecRoom.Injection.<CreateDirectlyLoadableAssetBundleSource>d__7$$MoveNext` **`0x10F7AD0`**:

| addr | step |
|---|---|
| `0x10F7C37`/`0x10F7C49` | build the URL — `"/room/" + Uri.EscapeDataString(…)` |
| `0x10F7CB9` | `RecNet.Core$$IDLRUCGALFZ` — download, honouring the BestHTTP on-disk cache |
| `0x10F7D0E` | fetch the **on-disk cache entry**; null ⇒ `RecNetUserFriendlyException(`**`'Could not load room because on-disk caching is disabled'`**`)` |
| **`0x10F7D68`** | **`RecRoom.Core.Studio.OVWVRFTNJPC$$VLRSRJOPTNI(string path)`** → `bool` |
| `0x10F7D6F` | `test al,al` / `je 0x10F7E91` — **false ⇒ throw the "requires recompression" `InvalidOperationException`** |

So the verdict is taken from the **cached file on disk**, by parsing it.

### `OVWVRFTNJPC.VLRSRJOPTNI` `0x1ACD680` — a hand-written UnityFS header parser

```
NLHWEPYTRLH()  signature            != "UnityFS"   -> throw  ('Invalid signature: ' + sig)
GKNMHSFIUUA()  uint32 version       > 8            -> throw  (version in the message)
NLHWEPYTRLH()  unityVersion
NLHWEPYTRLH()  unityRevision
LJTMVDWLEHB()  int64  size
GKNMHSFIUUA()  uint32 compressedBlocksInfoSize     [rsp+0x70]
GKNMHSFIUUA()  uint32 uncompressedBlocksInfoSize   [rsp+0x74]
                 cbi > ubi                         -> throw  'Compressed blocks info size should be
                                                               less than or equal to uncompressed …'
GKNMHSFIUUA()  uint32 archiveFlags                 [rsp+0x78]
   and eax,0x3f ; cmp al,3 ; jne -> throw          'Compression type for block header should be LZ4HC'
K4os LZ4Codec.Decode(blocksInfo)                   ; size mismatch -> throw
return !MWXPZYABIXT(decompressedBlocksInfo)        ; 0x1ACD990, then `xor bl,1`
```

`GKNMHSFIUUA`/`SJFCKHPDPJI`/`LJTMVDWLEHB` are **big-endian** uint32/uint16/uint64 readers (`UBBVCFMORHM`
is the shift-accumulate), matching Unity's archive header byte order.

⚠️ **The `cmp al,3` applies to the ARCHIVE header's `flags`, not to the data.** It only says the
*blocks-info table* is LZ4HC — which it always is for a Unity-built bundle. Hitting that throw
instead would print `'Compression type for block header should be LZ4HC'`, a **different** message
from the one in the log.

### `OVWVRFTNJPC.MWXPZYABIXT(byte[])` `0x1ACD1E0` — "does this need recompression?"

Parses the decompressed blocks-info and **scans the storage blocks**:

```
byte[16]  uncompressedDataHash
uint32    blockCount                 -> r14
for (i = 0; i < blockCount; i++):     ; 0x1ACD318 loop head, 0x1ACD394 `inc esi; jmp`
    uint32 uncompressedSize
    uint32 compressedSize
    uint16 flags                      -> al
    if (flags & 0x3F) == 0   continue          ; 0x1ACD34D
    if (flags & 0x40) == 0   continue          ; 0x1ACD351
    return true                                ; 0x1ACD355 — NEEDS RECOMPRESSION
return false
```

and `VLRSRJOPTNI` returns its **negation**, so:

> **A bundle is rejected iff ANY storage block is both compressed (`flags & 0x3F != 0`) and
> streamed (`flags & 0x40`).**

| block `flags` | meaning | verdict |
|---|---|---|
| `0x00` | uncompressed | **ok** |
| `0x02` / `0x03` | LZ4 / LZ4HC, not streamed | **ok** — this is what every shipped bundle uses |
| **`0x41`** | **LZMA + streamed** | **REJECTED** — what Unity's `BuildCompression.LZMA` ("Standard") emits |
| `0x43` | LZ4HC **+ streamed** | would also be rejected |

## Confirmed empirically from the client's own HTTP cache

`HTTPCache/` under `%LOCALAPPDATA%Low\Against Gravity\Rec Room\` holds the raw bodies. Ten were
UnityFS; **exactly one failed**, and it is the 115 MB room bundle:

```
HTTPCache/B85.data   115,229,645 B   etag "b9a9252aa09efb53e9d10856f2db86a5"
   unity=5.x.x ver=8 archComp=LZ4HC flags=0x243 blocks=1 blockFlags=[65]
   => NEEDS RECOMPRESSION -> REJECTED   (block 0, flags 0x41 = LZMA|streamed)

HTTPCache/B7C.data   118,546,962 B   blocks=2226 blockFlags=[0, 3]   => ok
HTTPCache/B5A.data                   blocks=43   blockFlags=[3]      => ok
…
```

The contrast is the whole diagnosis: **one block vs thousands.** LZMA compresses the entire payload
as a single streamed block; LZ4/LZ4HC chunks it at 128 KB, which is what makes a bundle
*directly loadable*. A `blocks=1` bundle is always this bug.

Reproduce with `tools/il2cpp/bundleflags.py` (implements both functions above):

```sh
py -I tools/il2cpp/bundleflags.py "$LOCALAPPDATA/../LocalLow/Against Gravity/Rec Room/HTTPCache"
py -I tools/il2cpp/bundleflags.py path/to/one.bundle
```

⚠️ **The BestHTTP cache makes this sticky.** The rejection happens *after* the download succeeds and
the entry is already cached, so every subsequent join re-reads the same bad file and fails
identically with no new request. A cached bundle from an earlier attempt will have an **older mtime
than the log** — do not take that as evidence it is unrelated. Clear `HTTPCache/` when re-testing.

## The fix — ✅ no source project and no Unity required

**This is a container-level problem, so it is fixable on the archived `.assetbundle` alone.** That
matters because these files are usually salvaged from the original live game, with no project to
rebuild from. The payload bytes and the directory/node table can be copied through verbatim; only
the storage-block framing changes, so every asset, PPtr and GUID inside is untouched.

`tools/il2cpp/bundlerecompress.py` does it offline (needs `py -m pip install lz4`):

```sh
py -I tools/il2cpp/bundlerecompress.py in.assetbundle out.assetbundle
  in : 115,229,645 B  unity 2021.3.29f1  ver 8  flags 0x243
       1 block(s) [65] -> payload 351,902,488 B
  out: 148,761,758 B  2685 block(s) [0, 3]
  verify: payload md5 429024e8… -> 429024e8… MATCH; needsRecompression=False
```

16 s for the 115 MB `^MyLittleMonsters` bundle. It decodes Unity's LZMA block (raw LZMA1 behind a
5-byte props header: `p0 = (pb*5+lp)*9+lc`, then dictSize LE32), re-chunks the payload at Unity's
128 KB, LZ4HC-compresses each chunk, stores any incompressible chunk with `flags 0`, rebuilds the
blocks-info (keeping the original 16-byte `uncompressedDataHash` and node table), and re-asserts the
round-tripped payload md5. `--store` emits `flags 0` blocks instead, if you would rather not compress
at all.

### ⚠️ Two consequences the server has to absorb

1. **The file hash changes**, and the client enforces it — `IDLRUCGALFZ(url, expectedHash, …)`. The
   hash is the file's **MD5** (the archived CDN object's `etag` matched it byte-for-byte here:
   `b9a9252aa09efb53e9d10856f2db86a5` → `9b0362f88cecc246e8f09140d883e100` after repacking). So
   update **`UnityAssetHash`** wherever the save serves it:
   `RecNet.Rooms.BakedUnitySubAssetDTO` is `{UnityAssetId: Guid, UnityAsset: string,
   UnityAssetHash: string}` → `RecNet.FilenameWithHash{Filename, Hash}`, carried by
   `UnitySubAssets` / `ReferencedUnityAssets` / `UnityAsset` / `UnityAssetHash` on
   `GET rooms/{id}/subrooms/{id}/saves/{saveId}`. Swapping the file without updating the hash just
   trades this error for a hash failure.
2. **LZ4HC is weaker than LZMA — expect the file to grow ~30 %** (115 MB → 149 MB here, from a
   336 MB payload). That is the price of direct loadability and is exactly why the official bundles
   are LZ4HC.

Scan a whole archive for the ones that need this:

```sh
py -I tools/il2cpp/bundleflags.py /path/to/assetbundles   # fix every "blocks=1 / REJECTED" hit
```

### If you *do* have a project, or a Unity install

Rebuild/recompress the room's bundle with **chunk-based LZ4HC**, not LZMA:

- Addressables: the group's *Bundle Compression* must be **LZ4** (`BuildCompression.LZ4Runtime`),
  not **LZMA**. LZMA is the Addressables default for *remote* groups, which is exactly how this
  happens to a self-hosted asset.
- `BuildPipeline.BuildAssetBundles`: **do not** pass `BuildAssetBundleOptions.None` (= LZMA); pass
  **`ChunkBasedCompression`**. `UncompressedAssetBundle` also passes the check, at the cost of size.
- Already have only the LZMA file? `AssetBundle.RecompressAssetBundleAsync(src, dst,
  BuildCompression.LZ4Runtime)` converts it without a rebuild — that API is named after the very
  thing the client refuses to do itself.

Then re-upload and clear the client's `HTTPCache/`.

**Why the client refuses:** `DirectlyLoadableAssetBundleSource` exists to hand the cached file
straight to `AssetBundle.LoadFromFile`-style loading with no intermediate copy. An LZMA bundle would
have to be fully decompressed into memory first — 115 MB here — so the loader declines rather than
silently paying that cost.

**How to apply:** on any `Error downloading room assets!`, ignore the wording and search the log for
`requires recompression`. If present, run `bundleflags.py` over `HTTPCache/`; the single file with
`blocks=1` / `blockFlags=[65]` is the offender, and its `etag` is the blob hash to find on the
server. Related but distinct: [room-load-unknown-prefab-studio-bundle-2026](room-load-unknown-prefab-studio-bundle-2026.md)
is the failure when the bundles are *valid* but the sub-asset list was never served.
