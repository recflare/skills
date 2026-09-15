# Unity bundle text scanning

> il2cpp-2025/bundlescan.py + lz4b.py decompress recflare-2025's 2745 LZ4 addressable bundles in ~85 s of pure Python and grep them for text — this fixes the false-negative trap where raw byte scans of StreamingAssets/aa find nothing.

Added **2026-09-02**. Fixes the blind spot noted in [avatar-item-desc-registry](../../rr-client-bringup/references/avatar-item-desc-registry.md), where a raw byte
scan of `Recroom_Release_Data` returned "not found" **even for a known-good control**, because the
addressable bundles are LZ4-compressed.

## The tools

`il2cpp-2025/lz4b.py` — pure-Python LZ4 *block* decompressor (no `lz4` package needed; the
environment has none). `il2cpp-2025/bundlescan.py` — UnityFS parser + text scanner:

```
py bundlescan.py <dir-of-.bundle> <comma,separated,terms> [limit]
```

Searches each term as **ASCII and UTF-16LE**, case-insensitively, and prints
`file @offset [kind] <±70 bytes of context>`.

## UnityFS gotchas that cost time

- Header: `"UnityFS\0"`, `u32 version`, unity-version cstr, unity-revision cstr, then
  `>Q size, >I compressedBlocksInfoSize, >I uncompressedBlocksInfoSize, >I flags`.
- `flags & 0x3F` = compression (2/3 = LZ4/LZ4HC). recflare-2025 bundles are all **`0x243`**.
- `flags & 0x200` (blockInfoNeedPaddingAtStart) ⇒ **align to 16 before the blocksInfo**.
- ⚠️ **Some bundles ALSO need the data section aligned to 16 after the blocksInfo, and some do
  not.** There is no flag for it — just try the raw offset, and on failure retry aligned. Without
  this, ~1/3 of bundles fail with a bogus `off == 0` on the first LZ4 sequence.
- blocksInfo layout: 16-byte hash, `>I blockCount`, then `blockCount × (>I uncompressed, >I
  compressed, >H flags)`, then the directory (`>Q offset, >Q size, >I flags, cstr name`).
- ⚠️ **LZ4 block streams end with a literals-only sequence.** After copying literals, break if fewer
  than 2 bytes remain — reading the match offset unconditionally throws `IndexError` on roughly
  every other block.

## Always run a positive control

A 0-hit result is meaningless without one. `bundlescan.py <dir> avatar 300` should return **~1400
hits** with real paths like `Assets/Core/Content/Avatar/Masks/UntuckedTee_Shirt_FourthFridays_Norm.png`.
Asset **paths** are plainly visible inside the decompressed bundles, so this scan does answer
"does an asset named X exist".

## Coverage map for "is <term> anywhere in the client"

1. il2cpp string literals — `out/stringliteral.json` (open `encoding='utf-8', errors='replace'`).
2. Metadata name blob — raw grep of `global-metadata.dat` (type/method/field names).
3. Uncompressed Unity data — `level*`, `*.assets`, `resources.assets`, `globalgamemanagers`:
   plain byte scan works.
4. **`StreamingAssets/aa/catalog.json`** — plaintext, lists every addressable **key/address**.
5. The 2745 `.bundle` files — needs `bundlescan.py`; ~85 s for the full set, 0 failures.

Remember RR streams most UGC/room content from the CDN at runtime, so even a clean sweep of all five
only proves the term is not in the **shipped** client.
