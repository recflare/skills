# RR event codes and rpc dispatch

> NILCDNBAPNO is the shared RR event-code enum for BOTH Photon RaiseEvent and the NGO named-message op byte (RR_RPC = 36); RPCs inside it are dispatched PUN-style by ViewId + method-name STRING, and RPC method names are unobfuscated.

Derived **2026-09-01** from build `20250718.01` via [recflare-2025-metadata-carve](../../il2cpp-analysis/references/recflare-2025-metadata-carve.md).
Companion to [rr-named-message-room-protocol](rr-named-message-room-protocol.md) and [photon-vs-gameserver-backend-switch](photon-vs-gameserver-backend-switch.md).

## The event-code enum

**There is no `Photon.Realtime.EventCode` type in this build** — a typedef-name scan finds only
`RecRoom.Sharing.PlayerEventCode` (unrelated). Photon's const-only `EventCode` class is inlined
away by il2cpp.

The RR event codes are **`.NILCDNBAPNO : byte`** — the *same* enum the NGO path uses as its
named-message op byte (full table in [rr-named-message-room-protocol](rr-named-message-room-protocol.md)). It starts at 4 and stops
at 106, leaving Photon's reserved 200–255 range clear, which is what you'd expect of a
`RaiseEvent` code space. **`RR_RPC = 36`.**

`typeslots.py NILCDNBAPNO` finds a single TypeInfo slot referenced only from
`FOMDMHNNNKP.AGMAPFJIFMH` — the Photon side passes the code as a plain `int`/`byte` and never needs
the TypeInfo, so xref silence there is not evidence against shared use.

## Inside event 36: RPCs are name-addressed, PUN-style

Dispatcher **`JLKPCEIDEDL.BJNDEFHHIOO(RecRoom.Foundation.ViewId viewId, string methodName,
.IALDHONKEJC sender, int, object[] parameters)`** `0x829ED20`. Its literals are straight PUN:
`"RPC method '{0}({2})' not found on object with networkView {1}. Implement as non-static. Apply
[PunRPC]."`, `'Malformed RPC; method name is null or empty'` `0xD2378F0`, `'Received RPC "'`,
`'" for viewID '`.

So the payload is **ViewId + method-name STRING + boxed arg array** — not an index.
`'Could not find RPC with index: '` `0xD126C00` exists but has **zero references**, so the
PUN `RpcList` index optimisation is not in use here.

Send side: `RecRoom.Networking.RRNetworkView.RPC(string methodName, OLHLIDNBNCP target,
object[] args)` `0x82B52E0` (plus `RPCBuffered` `0x82B51E0` and ~15 strongly-typed
`RpcAll(delegate, args…)` overloads), forwarding to the static
`EPMKPOOJBBN.EPLIGMFHLAB(ViewId, string methodName, target, JKPDADGJJHJ, object[])` `0x8266B20`.
`RRNetworkView.RefreshRpcMonoBehaviourCache` `0x82B55E0` is a purely local reflection cache.

`.OLHLIDNBNCP` = PUN `RpcTarget`, stock values: `All 0`, `Others 1`, `MasterClient 2`,
`AllBuffered 3`, `OthersBuffered 4`, `AllViaServer 5`, `AllBufferedViaServer 6`.

`RecRoom.Foundation.ViewId` is a struct with one instance field `int id` @0x10, plus consts
`MAX_VIEW_IDS`, `MAX_PLAYER_IDS`, `MAX_VIEW_SUB_IDS`, `DONT_DESTROY_ON_LEAVE_FLAG`,
`RUNTIME_INSTANTIATE_VIEW_ID_OFFSET`, `COMPILE_TIME_MAIN_ROOT_ID_OFFSET`.

## RPC method names are UNOBFUSCATED

Unlike everything else in `Assembly-CSharp` ([build-20230414-obfuscation](../../rr-client-bringup/references/build-20230414-obfuscation.md)), `Rpc*` method names
survive — they have to, because dispatch is by name. `methods.pkl` greps them directly. Respawn
family:

| method | RVA |
|---|---|
| `GameSpawnManager.RpcRespawnPlayer(Vector3 pos, Quaternion rot, RRNetworkView view, SeatManagement seat, bool, Tool, Guid, Tool, Guid, int[], Tool[], Guid[], bool)` | `0x2376260` |
| `GameSpawnManager.RpcRespawnPlayerFailed()` | `0x2376200` |
| `GameSpawnManager.RpcMasterRequestPlayerRespawn(int, int, bool, bool, bool, BODPIIIBABI, BODPIIIBABI, int[], BODPIIIBABI[], bool, bool)` | `0x2376060` |
| `GameSpawnManager.RpcMasterRequestPlayerRespawnAtPoint(int, RRNetworkView, bool, bool, BODPIIIBABI, BODPIIIBABI, int[], BODPIIIBABI[], bool, bool)` | `0x2375F00` |
| `RecRoomSceneManager.RpcRespawnPlayer(Vector3 pos, Quaternion rot, RRNetworkView view, bool)` | `0x24C4AA0` |
| `RecRoomSceneManager.RpcMasterRequestPlayerRespawn(bool, KODDFPHIGAD)` | `0x24C4AA0`-adjacent (`0x24C48C0`) |
| `Player.RpcAuthorityCV2Respawn` | `0x20AF8E0` |

The `RpcMaster*` naming convention marks client→master requests; the plain `Rpc*` are the
master→all broadcasts. Room-component RPCs follow the same pattern across managers
(`DodgeballManager.RpcOnPlayerHit`, `DiscGolfManager.RpcOnFinishHole`, …), matching
[unity-log-facade-frames](../../il2cpp-analysis/references/unity-log-facade-frames.md)'s note that room components keep real names.

**How to apply:** to enumerate every RPC the client will accept,
`grep` `methods.pkl` for method names starting `Rpc` — that IS the registry; there is no id table to
reverse.
