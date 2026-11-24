# The RPC shortcut index table, and which RPC handlers can check their sender (2026)

> ⚠️ **This CORRECTS [rr-event-codes-and-rpc-dispatch](rr-event-codes-and-rpc-dispatch.md)**, which
> says RPCs are addressed by method-name string and that "there is no id table to reverse". On the
> wire they are addressed by a **u16 index** into a Rec Room-specific table. The table is
> `List<string> IBAPMQGLBTJ` on `RecRoom.Networking.BDYKBXJFCLW`, built at **runtime** from every
> method carrying `[RecRoom.Networking.RPC.RPCMethod]`. It is **not** PUN's `RpcList` (that is
> byte-indexed and cannot express the observed index 471) and it is **not sorted**, so it cannot be
> reconstructed from a name list.
>
> **The security finding:** an RPC handler can only identify its caller if it declares a
> `RecRoom.Networking.RPC.RPCInfo` parameter. **166 of 740** `Rpc*` signatures in build
> `20260323.14` do; the other ~574 receive no sender identity at all and are therefore structurally
> incapable of refusing a replayed call.

Derived **2026-11-08** on `C:\Games\recflare-2026`, build **20260323.14**, answering server-side
request #17. RVAs are 2026-specific.

> ✅ **DUMPED 2026-11-08 from a live client (read-only RPM).** Two corrections to the text below:
> the table is reached through **static** fields, not an instance —
> `GameAssembly + 0xFC1B068` (TypeInfo slot) → `Il2CppClass*` → `[klass+0x20]` statics →
> `+0x08` `Dictionary<string,int>` (name → index), `+0x10` `List<string>` (index → name); list
> `_items` at `+0x10`, `_size` at `+0x18`. Seen in `BDYKBXJFCLW$$QTOHYYOLPAS` `0x9AB8670`
> (index → name, bounds-checked against `_size`).
> And it **is** sorted — over the right set. The build had **513** entries: indexes **0–471** are
> one block of 472 `[RPCMethod]` names in case-insensitive order (21 of them do not start with
> `Rpc`, which is why the sort test over `Rpc*` names failed), and **472–512** are 41 entries
> appended later in registration order (room minigames, sprays, audio). The appended tail may depend
> on what the session loaded, so **dump per client session before keying rules on indexes ≥ 472**.
> The dump lives outside the repo; regenerate it rather than relying on a stored copy.

## 1. The index table

| thing | 2026 name | RVA / id |
|---|---|---|
| dispatcher / registry | `RecRoom.Networking.BDYKBXJFCLW` | — |
| **index → name** | `List<string> IBAPMQGLBTJ` | field |
| **name → index** | `Dictionary<string,int> HLRFJGEYBDY` | field |
| per-type method cache | `Dictionary<Type, List<RpcMethodInfo>> ZTTREQUHJIG` | field |
| param cache | `Dictionary<MethodInfo, ParameterInfo[]> UZSTIJZSUBD` | field |
| the attribute | `RecRoom.Networking.RPC.RPCMethod` | `Il2CppType` @ `0x9AB6118` |
| sender info type | `RecRoom.Networking.RPC.RPCInfo` | — |
| table builder | `BDYKBXJFCLW$$KAHTCERRCLO` | `0x9AB6030` (+0x890) |
| type enumeration | `BDYKBXJFCLW$$SIHUNGCXMNE` | `0x9AB8AB0` |
| big registration pass | `BDYKBXJFCLW$$MAHISLBOOLI` | `0x9AB68C0` (+0x1610) |
| inbound handler | `BDYKBXJFCLW$$NQNFUQKKGRF` | `0x9AB7ED0` |
| invoke step | `BDYKBXJFCLW$$PBCJLUYAOWC` | `0x9AB8150` |

`KAHTCERRCLO` builds the list with `Enumerable.Where/Select/ToList` over the attributed methods
(plus a special branch for `ISingletonRpcForwarder`, literal `'RPC method found on
ISingletonRpcForwarder but the target type was not provided'`). **There is no `Sort` and no
`OrderBy` in the builder**, so the index is LINQ enumeration order over the runtime type graph.

### Three orderings tested and REJECTED

Do not re-derive these; all three were checked against the server's live index↔shape observations
(index 127 = `[Vector3, Quaternion, Vector3, float, bool, byte]`, 455 = no params, 471 = 728-byte
blob) and none matched:

| candidate ordering | count | verdict |
|---|---|---|
| 2026 distinct `Rpc*` names, ordinal sorted | 470 | ✗ 127→`RpcHandVibrate`; max index 469 < 471 |
| 2025 (`20250718.01`) distinct `Rpc*` names, ordinal sorted | 436 | ✗ 455 and 471 out of range |
| 2026 metadata order (typedef order × method order, `Rpc*` filter) | 781 | ✗ 127→`RpcAuthorityCV2Respawn`, 104→`RpcLocalGoToRoom` (104 is observed as a 1–17 MB blob) |

The filter is also wrong in all three: the table holds every `[RPCMethod]` method, which is **not**
the same set as "methods named `Rpc*`".

### How to get the table authoritatively

The list is computed by the client at startup, so **read it from a running client** rather than
reconstructing it. Both directions are plain managed collections on `BDYKBXJFCLW`:

```
BDYKBXJFCLW (declaration order, instance)
  +0x10  RecRoom.Log                      OMWAZFACTUS
  +0x18  Dictionary<string,int>           HLRFJGEYBDY   <- name -> index (send side)
  +0x20  List<string>                      IBAPMQGLBTJ   <- index -> name (THE TABLE)
  +0x28  int                               WPLPYNSLRKA
  +0x30  RecRoom.Networking.IPPNDAIDDGN    XLAFHJYKMGQ
  +0x38  Stopwatch                         OJHWESEHPXY
  +0x40  Dictionary<MethodInfo,ParameterInfo[]>  UZSTIJZSUBD
  +0x48  Dictionary<Type,List<RpcMethodInfo>>    ZTTREQUHJIG
```

⚠️ Offsets are **inferred from declaration order** (8-byte slots from `+0x10`), not read off an
instance — verify the first entry before trusting the dump.

Enumerate `IBAPMQGLBTJ` once after room entry and the index is the list position. This is also the
only way to get a **build-exact** table, which matters because the ordering shifts whenever an
`[RPCMethod]` is added or removed anywhere in the codebase.

### Identify indexes WITHOUT the table: signature matching

The parameter list is on the wire (key 3) and every RPC's signature is in the binary, so a shape
often pins the method on its own. Build the signature corpus with:

```bash
# 152 classes declare Rpc* methods in 20260323.14
py -I -c "import pickle; m=pickle.load(open('methods.pkl','rb')); \
  print('\n'.join(sorted({n.split('\$\$')[0] for r,n in m if n.split('\$\$')[-1].startswith('Rpc')})))" \
  | tr -d '\r' > rpcclasses.txt
while read -r c; do short="${c##*.}"; \
  py -I msig.py "$short" 2>/dev/null | tr -d '\r' | grep -E "^ +[^ ]+ Rpc" | sed "s|^ *|$c :: |"; \
done < rpcclasses.txt > rpcsigs.txt      # 740 lines
```

⚠️ `msig.py` takes the **short** class name and its output is CRLF — `tr -d '\r'` or every
downstream grep silently matches nothing. The class list written from Python is CRLF too.

Results against the server's observations:

| observed shape | candidates | verdict |
|---|---|---|
| `[Vector3, Quaternion, Vector3, float, bool, byte]` | **1** | ✅ `RecRoom.Core.Combat.RangedWeapon.RpcFireShot(position, rotation, velocity, chargeAmount, misFire, shotId)` |
| `(string, string, string, <enum>, bool)` | **2** | `Player.RpcLocalGoToRoom(roomName, subroomName, welcomeMatName, RoomDoorInviteMode, forceNewInstance)` **or** `Player.RpcLocalValidateTargetAndGoToSubroomOfCurrentRoom(same)` — both are "move the victim to another room" |
| `[Vector3]` | **12** | ✗ not determined by shape |
| `[Vector3, float]` | **6** | ✗ not determined by shape (`Player.RpcAuthorityCV2SetPhysicsVelocity(Vector3 direction, float speed)` is *consistent*, not confirmed) |

## 2. Sender identity: `RPCInfo` or nothing

`RecRoom.Networking.RPC.RPCInfo` is the sender/view/timestamp struct (log literal
`'RPCInfo {{ sender: {0}, view: {1}, timestamp: {2} }}'`). **A handler that does not declare an
`RPCInfo` parameter is never told who called it**, so no amount of code in it can reject a replay.

```bash
grep -cE "RPCInfo" rpcsigs.txt      # 166 of 740
```

Handlers that DO take it look like:

```
RpcMasterRequestGuess(RPCInfo messageInfo)
RpcOnNotifiedOfDropPartyBeaconRequest(Guid beaconId, Vector3 worldspacePosition, string partyId,
                                      Nullable<Color> flagColor, RPCInfo info)
RpcRequestImage(RPCInfo photonMessageInfo)
```

The `RpcMasterRequest*` family taking `RPCInfo` is the design intent: a client→master request where
the master resolves the actor itself rather than trusting a parameter.

### Consequence for the relay

Because the large majority of handlers never learn their caller, **receive-side validation cannot
be added by any client-side reasoning about these RPCs — enforcement has to live in the relay.** The
relay *does* know the sender (it stamps the NGO sender id), the view id (key 0) and the index
(key 4), so it can do what the handlers cannot:

1. Dump the table once per client build (above) and key every rule on **index**.
2. For each index, decide who may legitimately send it — typically one of: the owner of the target
   view (`viewId / 100000 == sender actor`, see
   [actor-number-and-view-id-limits-2026](actor-number-and-view-id-limits-2026.md)), the current
   master, or anyone.
3. Drop or audit calls that violate that rule, and rate-limit per sender per index (the client's own
   `"RPC Heat"` / `'Error: You have sent too many RPCs too quickly.'` limiter is client-side and a
   modified client simply skips it).

The `Rpc*` naming convention is a useful first cut for step 2 but not proof: `RpcMaster*` are meant
to be sent *to* the master, plain `Rpc*` broadcasts are meant to come *from* the master or the view
owner, and `RpcAuthority*` asserts the sender is the object's authority — an assertion the receiver
does not verify.

## Q3 — `DevDisplayActive` is the nametag staff badge

- A player-scoped property registered in `Player.Awake` (literal `'DevDisplayActive'` `0xFDF99C8`;
  holder stored at `Player+0x360`). ⚠️ `slots2025.py`/`names.py` return nothing over
  `Player.Awake` (`0x19CF440`) — read it with `rangedis.py` from the `mxref` ref addresses.
- Its change callback is `RecRoom.AppUI.PlayerNametagViewModel$$OnDeveloperDisplayChanged`
  `0x96E9300`, which switches on a byte read from the player (interface slot 7):

  | value | label shown on that player's nametag to everyone |
  |---|---|
  | 1 | `Community Team` |
  | 2 | `Developer` |
  | 3 | `Volunteer Mod` |
  | other | none |

  ⚠️ That slot 7 returns the `DevDisplayActive` value is inferred from the callback name, not
  traced.
- **The receiver checks no role.** It renders whatever the player's record says, so any account can
  appear as "Developer" to the whole room. Relay rule: accept this key only from accounts whose token
  carries the matching role; otherwise drop the write (or force 0).
- The dev-tools UI (`RecRoom.AppUI.DevToolsViewModel`: `CanAccessDevTools`,
  `DeveloperToolsActive`, `ShouldShowDebugTools`) is gated by `UpdateBasedOnLocalAccount`
  `0x9705370` reading an `ObscuredBool` — on the local client only.
- Writers in general: per
  [synchronized-field-room-property-batching-2026](synchronized-field-room-property-batching-2026.md),
  receivers of op 102/103 check nothing about the writer beyond dropping their own echo. Any
  "only X may write key K" rule has to live in the relay. The full set of developer-only keys was
  **not** enumerated.

## Q4 — RPCs carrying free text shown to other players

From the signature corpus. "Text" lists the string parameters' positions in the params array
(key 3, 0-based):

| class | RPC | text at |
|---|---|---|
| `RecRoom.CircuitsV2.CircuitsV2Manager` | `RpcSendMajorNotification(string notification)` | 0 |
| `Player` | `RpcLocalCV2ShowBannerNotification(position, duration, string title, …, string mainText, …, string leftEmoji, string rightEmoji)` | 2, 6, 10, 11 |
| `RecRoom.Core.Creation.SandboxGizmos.TextScreen` | `RpcTextScreenMessage(string text, long ticks, bool hasColor, Color, bool skipMultiline, int channel)` | 0 |
| `RecRoom.Core.Creation.UGCSubtitleManager` | `RpcShowUgcSubtitle(int priority, string subtitle, float duration)` | 1 |
| `RecRoom.Players.PlayerChat` | `RpcChatMessage(string message, MessageType, RPCInfo)` | 0 |
| `RecRoom.Systems.Economy.RoomKeys.RoomKeysManager` | `RpcUpdateRoomKey(…, string name, string description, …, string imageName, …)` | 4, 5, 7 |
| `Player` | `RpcShowRoomDetailsForPlayer(string roomName)` | 0 |

Found by matching parameter *names* (`text`, `message`, `notification`, `title`, `subtitle`,
`name`, `description`, …), so treat the list as a floor, not a census.

## Q5 — the role signal: the relay already owns it

The client learns its role from data **the recflare server issues**, so an allow-list needs no new
signal:

- **Token claims.** `RecNet.Login$$WOQLZFVQMLV` `0x94E2340` reads claims `role` and
  `rn.privilege`. Values it recognises: `developer`, `moderator`, `screenshare`, `influencer`,
  `junior`, `whiteglove1`, `whiteglove2`, `betastudio`, `keepsake`,
  `livekeepsakeeventroomsaveoverride`, `testaccountmultiplayer`, `testaccountmemory`,
  `multiinstanceevent`, `ugcloc`, `limitsv2`; privileges `BanRumiAI`, `BanRmChat`, `BanPubInv`,
  `BanVChat`. Cf. the 2025 rules in
  [jwt-role-privilege-claims](../../wire-shapes/references/conventions/jwt-role-privilege-claims.md).
  ⚠️ 2026 has a `'|'` literal in this function, so it may now split on `|` where 2025 did no
  delimiter parsing — **unverified**; keep sending JSON arrays.
- **An HTTP check.** `RecNet.Accounts$$URSRLUZMIMB` `0x9422F60` issues
  **`GET role/developer/{accountId}`** (statics `+0x08` = GET; the id comes from
  `Accounts$$VPLUWCANMZA()` with no argument, i.e. the local account) and expects a **bare `bool`**
  (`ZWUODKCINOA<bool>`, inst #85, response required). Caller `VXCRGFZHQRH$$MoveNext` `0x2081BB0`.
  Service not pinned beyond the `RecNet.Accounts` facade.
- Whether the original service also enforced any of this server-side (a Photon plugin or webhook)
  cannot be seen from the client.

## Q6 — Photon-layer codes → wire codes

The full 2026 table is in
[room-opcode-permissions-and-master-election-2026](room-opcode-permissions-and-master-election-2026.md).
What the request needs:

| Photon layer | wire | name |
|---|---|---|
| 200 RPC | **36** | `RR_RPC` |
| 201 serialize | **28** | `RR_NetworkSynchronization` |
| 202 instantiate | **29** (one) / **31** (bulk) | `RR_NetworkInstantiate` / `RR_BulkInstantiate` |
| 204 destroy | **32** (one) / **33** (bulk) | `RR_Destroy` / `RR_BulkDestroy` |
| 207 destroy-player | — | no dedicated-path equivalent; a leave is `105`/`106` |

Corrections to the request's guesses: **27 is `RR_MasterLockBlockComplete`** (master-only), not an
anti-cheat heartbeat; **22 `RRBufferedRoomEvent`, 23 `RRClearBufferedRoomEvent`, 24
`RR_CreationOp`**. `NetworkEventCode` stops at **112**, so any 200–255 code on the dedicated path is
forged and must be rejected; "405" cannot be a byte code and could not be placed. The anti-cheat
heartbeat was not traced.

⚠️ That table lists 28 as master-only, but request #16 observed every player sending 28 at ~15/s —
re-check before turning that row into a rule.

## Still open

- The table itself (needs a dump from a running client).
- A full census of developer-only property keys.