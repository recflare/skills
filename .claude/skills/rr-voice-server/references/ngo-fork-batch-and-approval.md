# NGO fork batch and approval

> recflare-2025's forked NGO wire format — NetworkBatchHeader is 24 bytes with BatchCount MOVED to offset 16, and ConnectionApprovedMessage gained a `Payload` string that carries the Tachyon Carrot JSON into NetworkManager.RecRoom_ConnectionInfo.

Read **2026-08-21** from build `20250718.01`. NGO type names are **unobfuscated**
(`Unity.Netcode.*`), so this layer is far easier than [litenetlib-fork-encrypt-layer](litenetlib-fork-encrypt-layer.md) /
[recroom-encrypt-layer-format](recroom-encrypt-layer-format.md). Follows [voice-handshake-key-exchange](voice-handshake-key-exchange.md).

## Batch header — 24 bytes, only ONE real change

`fields2025.py NetworkBatchHeader` gives struct offsets directly:
`Magic` u16 @0, `BatchSize` u32 @4, `BatchHash` u64 @8, **`BatchCount` u16 @16**, size 24.
Stock declares BatchCount second (@2); this build declares it **last**, so natural alignment
pushes the struct 16 -> 24. That is the whole "fork". Bytes [2:4] and [18:24] are **padding**.

`HandleIncomingData` (`0x973F500`): reads 24 bytes; `Magic != 0x1160` -> LogError+return;
`BatchSize != datagram length` -> LogError+return;
**`XXHash.Hash64(buf+24, size-24, seed 0)` != BatchHash -> LogError + RETURN (batch rejected)**;
message loop bound is `word @16` (BatchCount) — offset 2 is never read.

## Bit-packed ints (`BytePacker`/`ByteUnpacker`, `0x972E840` / `0x972EF50`)

`encoded = (value << 3) | numBytes`, written LE in `numBytes` bytes; `numBytes = b0 & 7`.
For `numBytes == 5` the value is the raw LE u32 in bytes 1..4 (no shift). Signed callers ZigZag
first (`(n<<1) ^ (n>>63)`); the packer itself is unsigned and rejects `> 0x1FFFFFFF`.
So `0x81` = 1 byte, `0x81>>3` = 16, un-zigzag = **8**.

## ConnectionApprovedMessage — server->client (`Serialize` `0x972FE60`, `Deserialize` `0x972F7D0`)

Fields: `OwnerClientId` u64 @0, `NetworkTick` i32 @8, **`Payload` string @0x10 (FORK)**,
`m_ReceivedSceneObjectData` @0x18, `MessageVersions` NativeArray @0x20.

Order on the wire: bitpacked ZigZag `MessageVersions.Length`; then per entry `u32 Hash` raw LE +
bitpacked ZigZag `Version`; then bitpacked `OwnerClientId` (**ulong overload, NO zigzag**); then
bitpacked ZigZag `NetworkTick`; then, if `Payload != null`, bitpacked `Payload.Length` (unsigned)
followed by **one bitpacked ushort per UTF-16 char**. **No ConnectedClientIds, no
sceneObjectCount** — the fork dropped them (NGO here has no NetworkObject at all).

`Deserialize` calls **`SetServerMessageOrder`** mid-body, so the array order defines message-type
indices from then on; the approval itself is dispatched with the client's pre-approval local order.
Message hash = `XXHash.Hash32(UTF8(type name))` (`RegisterMessageType` `0x97414F0`).

## Where the Carrot JSON goes

`NetworkManager` field `<RecRoom_ConnectionInfo>k__BackingField` is at **offset 0x20**, and
`ConnectionApprovedMessage.Handle` (`0x972FB80`) does `nm[0x20] = this.Payload` then sets
`LocalClient.IsApproved = 1`. So **the `{"DR":"Carrot","KT":...}` blob is the `Payload` string**.

## The RSA blocker is smaller than it looked

In `CDJMICBEALM` (`0x8277880`): the `"Carrot"` string compare result is **only logged — nothing
branches on it**. `SessionKeyB` is passed to `RSA.Decrypt` with **no null check** (so `KT` must be
present), using RSA provider `[this+0x48]`. And `HCNIOOINPCA` (`0x82786B0`) does
`ExportCspBlob([this+0x48], includePrivate=false)` = **`CPK`**, while `AT/VB/CKA/CIA` are encrypted
with the *other* provider `[this+0x40]` (Rec Room's hardcoded modulus).

**So the server can mint a valid `KT` with the `CPK` the client just sent — no Rec Room private key
needed.** The transport key is then `AES.Key (= CKA, unknowable) XOR decrypt(KT)`, so the client
goes encrypted and locks you out. To stay plaintext, neuter `RecRoom_SetEncryptionInfo`
(`0x735CA20`) or the layer's SetKey (`0x735DF90`) client-side — a far smaller patch than swapping
the RSA modulus.

**Not established:** the client's pre-approval local message-type index for ConnectionApproved
(`PrioritizeMessageOrder` `0x9740790` not enumerated). Derive it from the captured request: the
8 hashes are in the client's local order and ConnectionRequest sits at index 1.
