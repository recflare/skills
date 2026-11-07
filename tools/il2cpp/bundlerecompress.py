"""Rewrite a UnityFS bundle's storage blocks as chunked LZ4HC, in place of LZMA.

Why: Rec Room's room-asset loader refuses any bundle with a block that is both compressed and
streamed -- which is exactly what Unity's LZMA ("Standard") compression emits (one block, flags
0x41). The client then throws `Cannot create a DirectlyLoadableAssetBundleSource from an AssetBundle
that requires recompression` and the player sees "Error downloading room assets!". See
rr-client-bringup/references/room-asset-bundle-lzma-rejected-2026.md.

This is the offline equivalent of `AssetBundle.RecompressAssetBundleAsync(src, dst,
BuildCompression.LZ4Runtime)` -- it needs no Unity, no source project and no asset understanding,
because it only touches the ARCHIVE container: the payload bytes and the directory/node table are
copied through byte-for-byte, so every asset, PPtr and GUID inside is untouched.

    py -I bundlerecompress.py <in.bundle> <out.bundle> [--store] [--chunk N]

      --store     emit uncompressed blocks (flags 0) instead of LZ4HC -- bigger but no encode cost
      --chunk N   block size, default 131072 (0x20000), which is what Unity uses

Verifies itself: re-parses the output and asserts the recovered payload is identical to the input's.

Requires `lz4` (`py -m pip install lz4`); LZ4HC here is `lz4.block.compress(mode=
"high_compression")`, the same codec Unity writes. The LZ4HC flag only names the LZ4 family -- the
decoder is shared with plain LZ4, so a plain-LZ4 encoder would also be accepted.
"""
import os, sys, struct, hashlib, lzma

try:
    import lz4.block as lz4b
except ImportError:
    sys.exit("need the lz4 module: py -m pip install lz4")

CHUNK = 0x20000
SIG = b"UnityFS"


def unpack_lzma(data, out_size):
    """Unity LZMA block: 5-byte props (lc/lp/pb + dictSize LE32) then a raw LZMA1 stream."""
    p0 = data[0]
    lc = p0 % 9
    rem = p0 // 9
    lp = rem % 5
    pb = rem // 5
    dict_size = struct.unpack_from("<I", data, 1)[0]
    d = lzma.LZMADecompressor(format=lzma.FORMAT_RAW, filters=[{
        "id": lzma.FILTER_LZMA1, "lc": lc, "lp": lp, "pb": pb, "dict_size": dict_size}])
    out = d.decompress(data[5:], out_size)
    if len(out) != out_size:
        raise ValueError(f"LZMA produced {len(out)} bytes, header said {out_size}")
    return out


def read_header(b):
    if b[:7] != SIG:
        raise ValueError("not a UnityFS bundle")
    o = b.index(b"\0") + 1
    ver = struct.unpack_from(">I", b, o)[0]; o += 4
    s = o; o = b.index(b"\0", o) + 1; unity_version = b[s:o - 1]
    s = o; o = b.index(b"\0", o) + 1; unity_revision = b[s:o - 1]
    size, cbi, ubi, flags = struct.unpack_from(">QIII", b, o); o += 20
    return dict(ver=ver, uv=unity_version, ur=unity_revision, size=size,
                cbi=cbi, ubi=ubi, flags=flags, hdr_end=o)


def blocks_info_offset(h, total_len):
    o = h["hdr_end"]
    if h["ver"] >= 7 or (h["flags"] & 0x200):
        o = (o + 15) & ~15
    if h["flags"] & 0x80:                      # blocksInfo stored at the end
        return total_len - h["cbi"], o
    return o, o + h["cbi"]


def decode_blocks_info(raw, h):
    ct = h["flags"] & 0x3F
    if ct in (2, 3):
        return lz4b.decompress(raw, uncompressed_size=h["ubi"])
    if ct == 1:
        return unpack_lzma(raw, h["ubi"])
    return raw[:h["ubi"]]


def payload_of(path):
    b = open(path, "rb").read()
    h = read_header(b)
    bi_off, data_off = blocks_info_offset(h, len(b))
    bi = decode_blocks_info(b[bi_off:bi_off + h["cbi"]], h)
    data_hash = bi[:16]
    cnt = struct.unpack_from(">I", bi, 16)[0]
    blocks = [struct.unpack_from(">IIH", bi, 20 + 10 * i) for i in range(cnt)]
    directory = bi[20 + 10 * cnt:]              # node table, copied through verbatim

    # the data section may be 16-aligned after blocksInfo; try both and keep what adds up
    total_c = sum(c for _, c, _ in blocks)
    for start in (data_off, (data_off + 15) & ~15):
        if start + total_c <= len(b):
            out = bytearray(); o = start; ok = True
            for u, c, f in blocks:
                chunk = b[o:o + c]; o += c
                t = f & 0x3F
                try:
                    if t == 0:
                        if c != u: ok = False; break
                        out += chunk
                    elif t == 1:
                        out += unpack_lzma(chunk, u)
                    elif t in (2, 3):
                        out += lz4b.decompress(chunk, uncompressed_size=u)
                    else:
                        ok = False; break
                except Exception:
                    ok = False; break
            if ok and len(out) == sum(u for u, _, _ in blocks):
                return h, data_hash, blocks, directory, bytes(out), start
    raise ValueError("could not locate/decode the data section")


def build(h, data_hash, directory, payload, chunk, store):
    blocks, body = [], bytearray()
    for i in range(0, len(payload), chunk):
        raw = payload[i:i + chunk]
        if store:
            blocks.append((len(raw), len(raw), 0)); body += raw
            continue
        comp = lz4b.compress(raw, mode="high_compression", store_size=False)
        if len(comp) < len(raw):
            blocks.append((len(raw), len(comp), 3)); body += comp
        else:                                   # incompressible: store it, flags 0
            blocks.append((len(raw), len(raw), 0)); body += raw

    bi = bytearray(data_hash)
    bi += struct.pack(">I", len(blocks))
    for u, c, f in blocks:
        bi += struct.pack(">IIH", u, c, f)
    bi += directory
    ubi = len(bi)
    cbi_blob = lz4b.compress(bytes(bi), mode="high_compression", store_size=False)
    # the archive flags demand an LZ4-family blocksInfo, so never store it raw
    flags = (h["flags"] & ~0x3F) | 3

    head = bytearray(SIG + b"\0")
    head += struct.pack(">I", h["ver"])
    head += h["uv"] + b"\0" + h["ur"] + b"\0"
    size_at = len(head)
    head += struct.pack(">QIII", 0, len(cbi_blob), ubi, flags)
    if h["ver"] >= 7 or (flags & 0x200):
        head += b"\0" * ((-len(head)) % 16)
    out = bytearray(head) + cbi_blob
    out += b"\0" * ((-len(out)) % 16)
    out += body
    struct.pack_into(">Q", out, size_at, len(out))
    return bytes(out), blocks


def main():
    a = [x for x in sys.argv[1:] if not x.startswith("--")]
    if len(a) != 2:
        sys.exit(__doc__)
    store = "--store" in sys.argv
    chunk = CHUNK
    if "--chunk" in sys.argv:
        chunk = int(sys.argv[sys.argv.index("--chunk") + 1], 0)
    src, dst = a

    h, data_hash, blocks, directory, payload, _ = payload_of(src)
    print(f"in : {os.path.getsize(src):,} B  unity {h['ur'].decode()}  ver {h['ver']}  "
          f"flags {h['flags']:#x}")
    print(f"     {len(blocks)} block(s) {sorted({f for _, _, f in blocks})} -> "
          f"payload {len(payload):,} B")
    before = hashlib.md5(payload).hexdigest()

    out, nb = build(h, data_hash, directory, payload, chunk, store)
    open(dst, "wb").write(out)
    print(f"out: {len(out):,} B  {len(nb)} block(s) "
          f"{sorted({f for _, _, f in nb})}")

    h2, _, b2, _, p2, _ = payload_of(dst)
    after = hashlib.md5(p2).hexdigest()
    bad = [(i, f) for i, (_, _, f) in enumerate(b2) if (f & 0x3F) and (f & 0x40)]
    print(f"verify: payload md5 {before} -> {after} "
          f"{'MATCH' if before == after else 'MISMATCH'}; "
          f"needsRecompression={bool(bad)}")
    if before != after or bad:
        sys.exit("FAILED")


if __name__ == "__main__":
    main()
