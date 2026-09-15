# RecRoom encrypt layer format

> The RecRoomClientEncryptLayer wire format in recflare-2025 — a TRAILING marker byte, 0x11 plaintext (+1 byte) or 0x2A encrypted (+9 = 8 nonce + marker); inbound is strip-only for 0x11.

Read out of the image **2026-08-21** on `C:\Games\recflare-2025` (build `20250718.01`).
Unblocks the voice server in [litenetlib-fork-encrypt-layer](litenetlib-fork-encrypt-layer.md) / [dissonance-voice-connection](dissonance-voice-connection.md).

## Corrected method map for `MGHAOMEMAHF` (RecRoomClientEncryptLayer)

Earlier guess (largest = outbound, 3-arg = inbound) was **backwards**:

| RVA | real |
| --- | --- |
| `0x735D760` `FMHFAJOCCHG` | **ProcessInboundPacket** |
| `0x735DC20` `FOFHJKKBKGJ` | **ProcessOutBoundPacket** |
| `0x735DF90` `GKKBCNBDNNF` | **SetKey** — `"RecRoomClientEncryptLayer Encryption Enabled {0}"` |
| `0x735E140` `OMFPKBDCHHM` | **ClearKey** — `"RecRoomClientEncryptLayer Endpoint Disconnected"` |
| `0x735E220` `.cctor` | `RandomNumberGenerator.Create()` -> static `[klass+0x90]`. Nothing else. |

## Format — TRAILING marker, variable length

**`ExtraPacketSizeForLayer = 9` is a worst-case RESERVATION, not the bytes actually added.**

Outbound (`0x735DC20`), branches only on `this.key` (field `0x18`) — **never** on packet property:

- **key == null** (`cmp qword [this+0x18], 0`): `data[length] = 0x11; length++`. **One byte. No RNG, no
  transform.**
- **key != null**: 8 random bytes from the static RNG written at `data[offset+length .. +8]`,
  Burst crypto call, then `length += 9` and `data[length-1] = 0x2A`.

Inbound (`0x735D760`): `marker = data[length-1]` (**last byte**), then

- `0x11` -> `length--` and return. **STRIP-ONLY — no key check, no validation.**
- `0x2A` -> drop (`length = 0`) if `length <= 9` **or** `this.key == null`; else decrypt, `length -= 9`.
- anything else -> log `"Discarding packet from {0} with unknown marker {1}"`, `length = 0` (drop).

`offset` is never modified in either direction — nothing is shifted, it is a pure trailer.

## Consequences

- A server that **appends a single `0x11` byte to every datagram** is accepted through the whole
  LiteNetLib + NGO handshake. No key needed, no bytes to reproduce.
- **Deduction (not read):** the observed 3 connect-data bytes `01 00 11` are really `01 00` plus the
  layer's trailing `0x11`.
- `SetKey(object, byte[])` copies **exactly 32 bytes** (`Buffer.BlockCopy(src,0,new byte[32],0,0x20)`)
  — AES-256-sized. It is the sink for `LiteNetLibTransport.RecRoom_SetEncryptionInfo`.

**Not established:** the cipher itself. `BJAEIACDDLH$$BAHFCECOEJD` (`0x73653E0`) is **Burst-compiled**
(branches on `BurstCompiler.IsEnabled`, static function-pointer fields), so naming the algorithm means
reading Burst native code — a separate job. Do not assume AES from the key size alone.
