# Actor-number and view-id limits (2026)

> Build `20260323.14`. Everything here comes from disassembly unless marked otherwise.
> ⚠️ **In Rooms 1 (decimal mode), view and bulk ids are `actor * 100000 + sub` in unchecked int32.**
> Actor numbers ≥ 21,475 wrap negative, and the owner decoded from the id (`id / 100000`) no longer
> matches the player. Production outage, Nov 2 2026, 19:10–20:30 UTC: Tachyon's per-process
> client-id counter passed 21,474, every joiner failed to spawn, and a restart fixed it. A client in
> that window logged `Player.Awake` → `Player.KDJHNYTILXC` NullReferenceExceptions on every player
> spawn.
> ⚠️ **The actor number is the NGO client id truncated to int32** (`clientId == 0 ? -1 : (int)clientId`).
> Nothing range-checks it.

Toolkit: `C:\Games\recnet-patcher\il2cpp-2026\` with
`GAMEASSEMBLY=C:/Games/recnet-patcher/tools/metadump2026/out/GameAssembly.dll`.

## Where the actor number comes from

- **Room player class `RecRoom.Networking.DGGDXSNNWDX`:**
  - `+0x58` is the full `ulong clientId` from `NetworkedPlayerData`.
  - `+0x18` is the int actor number, `clientId == 0 ? -1 : (int)clientId` (low 32 bits).
  - Written in `DGGDXSNNWDX..ctor` `0x9A942BC` and in `HVFCFCFDHNM.EVLSEGFOZMO` `0x9A960F4`
    (update path).
- **Lookup:** `WTJJGMLMXED.QPJFGSUGGOJ` `0x9A9B5F0` linearly scans the *current room's* player list,
  comparing `player+0x18 == actor` in int32.
- **Room `+0x50`** = current master's actor number (int32). `SetMasterClient` sign-extends int32 ids
  back to u64 (`HVFCFCFDHNM.EKOJRVGZPFD` `0x9A95B0B`).
- **Incoming events carry an int sender.** `BDYKBXJFCLW.NQNFUQKKGRF` `0x9AB7ED0` looks it up only when
  `sender > 0`. If the lookup fails it logs `Received an RPC from an unkown sender: ActorNr={0}` and
  **still dispatches** the RPC with a null sender.

## Id formulas (decimal mode)

- **`ViewId.From(actor, sub, flag)`** `0x99C2980`: `actor*100000 + sub%50000 + (flag ? 0 : 50000)`.
- **Decoders:**
  - owner `ViewId.MRAOAUAYYFN` = `id / 100000` (C# truncating division);
  - sub `EICOHKOLLGY` = `(id % 100000) % 50000`;
  - flag `AASHYKCNPHN` = `(id % 100000) < 50000`.
- **`RRNetworkView.CreatorActorNr`** `0x9ACD1F0` is decoded from the view id. It is not stored.
- **Allocator `GJTJVGYFDKF.QNIKEUSAUET(owner, flag)`** `0x9AC53F0` (PUN-style `AllocateViewID`):
  - **owner ≠ 0:** `base = owner*100000` (`imul`, no check). One process-wide static counter per flag
    (`static+0` / `+4`) steps `sub` through 1..49,999. It skips ids already present in the local view
    registry and throws `AllocateViewID() failed. User {0} is out of viewIDs` after 50,000 tries.
  - **owner == 0 (scene):** `counter % 100000` with a minimum of 90,000, so ids run 90,000–99,999.
    It throws `...out of 'scene' viewIDs`.
  - The owner comes from the instantiating player (`InstantiateParameters+0x50`), or 0 for scene
    objects (`FYAXUXWCHZY.MOEHSOPNAYC` `0x9ABF03E`).
- **Bulk id** (`DGCCBGOLMZP.FGQYGCISRKO` `0x9ABA3E5`): `actor*100000 + counter`. The counter is a
  static at `+0x40`, starts at 0 and wraps at 100,000. **It has no collision check.**
- **View registration** (`RRNetworkView.MUAMQBPIOXS` `0x9AC9EE0`) is an int-keyed dictionary with no
  sign check, so negative ids register.

**Overflow worked example:** actor 21,475, sub 1.
1. `21475*100000` wraps to −2,147,467,296, so the id is −2,147,467,295.
2. It decodes to owner **−21,474**, which is not 21,475.
3. Ownership, `IsMine` and the creator are wrong for every object that player creates.

Limit: `actor ≤ 21,474` (`INT32_MAX / 100000`, with sub ≤ 99,999 still fitting). Actor 0 is
reserved for scene objects, and client id 0 (the server) maps to −1.

## Rooms 2 (packed mode)

- Mode flag `RecRoom.Foundation.XOKJTETAYJW` static `+4`: `== 2` means Rooms 2 (`HFBVZPEQACG`), `== 1`
  is `HEWPCIKSQQX`, `Reset` sets 0. The setter `NXPWHZJBIYZ` has no direct callers.
- In packed mode, ids are `creator << 20 | sub` (sub = `id & 0xFFFFF`, creator = `id >> 20` →
  `NetworkCreatorId` u16). `ViewId.From` throws `View ID does not support this in rooms 2`.
- **Untraced:** whether the creator field is the actor number or a separate per-room creator index.
  If it is the actor number, Rooms 2 caps it at 2,047 (positive int32) or 4,095.

## Reuse hazards (static reasoning)

- Cache-5 objects survive their creator, and their ids still decode to the old actor number. A new
  player given the same number becomes their creator for every `CreatorActorNr` check.
- The new client's bulk counter starts at 0. Bulk ids have no collision check, so they collide with
  the old actor's surviving cached 31/33 bulk ids, and a cache-6 `{0: bulkId}` removal then matches
  both.
- The view allocator only skips ids in the new client's own registry, so it avoids surviving views
  that client has loaded.
- Actor lookups only scan the current room's players, so the client compares actor numbers per room
  only.

## Untraced

- Per-actor state in gameplay code: `Player.GetFromActorNumber`, CircuitsV2
  `GetPlayerByActorNumberStatic`, the RemotePlayerLeft handling. `Player.*` is packer-protected.
- The Dissonance client-id width on the client.
- The Rooms 2 creator-id mapping.
