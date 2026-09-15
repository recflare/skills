def lz4_decompress(src, uncompressed_size):
    dst = bytearray(uncompressed_size); s = 0; d = 0; n = len(src)
    while s < n:
        tok = src[s]; s += 1
        lit = tok >> 4
        if lit == 15:
            while True:
                b = src[s]; s += 1; lit += b
                if b != 255: break
        if lit:
            dst[d:d+lit] = src[s:s+lit]; s += lit; d += lit
        if s + 2 > n: break
        off = src[s] | (src[s+1] << 8); s += 2
        ml = tok & 15
        if ml == 15:
            while True:
                b = src[s]; s += 1; ml += b
                if b != 255: break
        ml += 4
        p = d - off
        if off >= ml:
            dst[d:d+ml] = dst[p:p+ml]; d += ml
        else:
            for i in range(ml):
                dst[d] = dst[p+i]; d += 1
    return bytes(dst[:d])
