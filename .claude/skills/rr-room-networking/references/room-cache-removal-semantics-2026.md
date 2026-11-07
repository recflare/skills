# Room-cache removal semantics (2026)

> Build `20260323.14`. Everything below comes from disassembly unless it is marked *Photon recall*.
> ⚠️ **Removal is a subset match, not byte-equality.** A cached event is removed when its code
> matches and its data dictionary contains **every** filter key with an equal value. Extra keys
> on the cached event (timestamp, args, payload) do not block the match.
> ⚠️ **A null filter with cache 6 means "every cached event of this code, from every actor".** The
> client sends it during a room reset for six codes at once. A server that only removes on
> byte-equal match ignores these, and the cache grows without bound.
> ⚠️ **Do not restrict removals to the sender's own events.** The owner of a view, or of an object
> after ownership transfer, removes events that someone else raised.

Toolkit: `C:\Games\recnet-patcher\il2cpp-2026\` with
`GAMEASSEMBLY=C:/Games/recnet-patcher/tools/metadump2026/out/GameAssembly.dll`.
All RVAs are for this build only.

## Raise paths

- **`RaiseEventOptions` = `RecRoom.Networking.BJJNNDTQGRE`**:
  - `+0x10` CachingOption (`RpcCacheOption`)
  - `+0x11` InterestGroup
  - `+0x18` TargetActors `int[]`
  - `+0x20` Receivers
  - `+0x21` SequenceChannel

  It has no sender or actor field apart from TargetActors.
- **Facade:** `PEJBWBFHLBI.WDVHFRRPINS(byte code, object data, opts, delivery)` at `0x9A92950`.
  It dispatches through an interface to the active backend.
- **NGO backend:** `WTJJGMLMXED.WDVHFRRPINS` `0x9A9BC80` → `HVFCFCFDHNM.WDVHFRRPINS` `0x9A98E50`
  (instance; code in `dl`; writes with `Unity.Netcode.FastBufferWriter`).
- **Every literal event code raised in the build** (scan of every direct call to both raise
  functions): 4, 5, 28, 29, 31, 32, 33, 34, 35, 36.
  - **Code 24 (`RR_CreationOp`) is never raised with a literal code.** Its keys are unknown.

## Identity keys per code

All identity values are boxed `System.Int32` on both the add and the removal path, so the wire
tag is always `0a`. Keys are always bytes (tag `05`).

| code | add (key: meaning) | cache on add | removal filter | removal site |
|---|---|---|---|---|
| 36 RR_RPC | 0: viewId, 1: timestamp, 2: method string **or** 4: ushort method index, 3: object[] args (only if non-empty) | caller's `RpcCacheOption` | `{0: viewId}`, no TargetActors | `SICUJCWHXQH.EGYYWDTTVPH` `0x9ACEA20` |
| 29 RR_NetworkInstantiate | keys 0–8 built in `DGCCBGOLMZP.ZJUWMZTPQXS` `0x9ABBED0`; **8 = instantiation id (int)** | variable | `{8: id}`; TargetActors=[creator] only if a creator is passed | `DGCCBGOLMZP.MZSMTMIDLCF` `0x9ABAB00` |
| 31 RR_BulkInstantiate | 0: bulk id, 1: payload | 5 | `{0: id}` | `DGCCBGOLMZP.ZXIGTJIVKCU` `0x9ABC420` |
| 33 RR_BulkDestroy | `{1:int[]}` uncached; `{1:int[]}` c5; `{0:id, 2:int}` c5; `{0:id, 1:int[]}` c5 | see left | `{0: id}` (same call as the 31 removal) | `ZXIGTJIVKCU` |
| 32 RR_Destroy | `{0: id}` | runtime object: uncached; **scene object: 5** | none | `DGCCBGOLMZP.DJHCYGFIMRG` `0x9AB9E90` |

**Destroy (`DJHCYGFIMRG`):**
- **Runtime object:** first `MZSMTMIDLCF(id, null)`, a code-29 removal from any actor, then code 32
  uncached.
- **Scene object:** code 32 `{0: viewId}` with **cache 5**. It must stay cached, because it makes
  late joiners destroy the scene object.

The server never needs to act on 32 or 33 itself; the client sends the removals.

## Who sends removals (why there is no sender restriction)

- **`RRNetworkView.ClearBufferedRPCsIfMine` `0x9AC9160`** sends the code-36 removal when the view's
  owner (`view+0x34`) is the local actor, **or** when the local player is master
  (`PEJBWBFHLBI.UDLRDKXWCRK`). The RPCs it clears may have been buffered by any actor.
- **`RRNetworkView.ClearBufferedRPCs` `0x9AC9360`** sends it unconditionally.
- **Destroying a runtime object** removes the creator's code 29 with no TargetActors. After an
  ownership transfer the destroyer is not the creator. A server rule of "own events unless master"
  leaves the creator's 29 cached, and every later joiner then spawns a ghost object.

## Full wipe (null filter, cache 6)

- `WTJJGMLMXED.HBDIHWPLQAC` `0x9A9ADF0` builds options with cache **6**, Receivers=1, **no
  TargetActors**, then raises codes **4, 31, 33, 29, 36, 32**, each with **data = null**.
- It is reached from facade `PEJBWBFHLBI.HBDIHWPLQAC` `0x9A909C0` (interface slot 0x10). The only
  caller of that is `CXPUHVTFTQT.KGUMWAHNODE` `0x13C3790`, which:
  1. raises code 5 carrying object[] `{ (int)0x43505353 }` (ASCII `SSPC`), then
  2. calls the wipe,

  bracketed by two writes to some state (`0x0a`, then `0x0b`).
- **Treat this as "remove every cached event of this code, from every actor".** Code 5 and the
  cache-5 globals of other codes are not wiped. This is a room reset; what triggers it is untraced
  (`KGUMWAHNODE` has no direct callers).

## Cache option values

- `RpcCacheOption` = {0, 4, 5, 6, 7}. **1/2/3 do not exist**, so reject them.
- **Cache 7** is sent only as code 29 with data null (`DGCCBGOLMZP.IPABKLSVSMR` `0x9ABA660`). Its
  caller is untraced (interface `YNSZYSIMCGL`, slot 2). *Photon recall:* purge the cache-4 events of
  actors that are no longer in the room; cache-5 events survive.

## Recommended server rule

```
on cache 6 (code C, filter F, targets T):
  for each cached event E with E.code == C:
    if T non-empty and E.sender not in T: keep
    if F is null or empty: remove
    elif every (k, v) in F has k in E.data and E.data[k] == v: remove
on cache 7: remove cache-4 events whose sender has left
never forward a cache-6/7 raise to other clients
```

## Untraced

- Code-24 keys.
- What triggers the reset (`KGUMWAHNODE`) and cache 7.
- Join replay ordering (cache vs property snapshot), and any replay count or byte cap.
- The NGO receive-side maximum message size. Send-side LiteNetLib caps a message at 65,535
  fragments (`TIMYJXHKVCH.YGADVOMHRVJ` `0x8BB34C0`), about 90 MB.
- The CircuitsV2 room-settings property-write bursts (`<group>.<abbr>_{MI,RO,EIO,ICA,RFM,OTV,BT}`).
  Their key builder is reached from `RoomSun.Start`.
