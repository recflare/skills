# The player "room index" (`rrPnr`), the `P<n>` property scope, and how a death propagates (2026)

> **There are THREE different per-player integers and they are not interchangeable.**
> 1. the **actor number** = NGO `OwnerClientId` truncated to int — this is what `P<n>` in
>    `1.P5.HEALTH` is built from;
> 2. the **room index** = a dense `0..N-1` value that the client carries in the **player custom
>    property `"rrPnr"`** — this is the "room index" players and CircuitsV2 mean, and it is on the
>    wire (op 103), just not in the join response;
> 3. the account id.
>
> **Nothing in the gameplay layer requires actor numbers to be small, dense or per-room.** The
> `P<n>` holders are created lazily per *player object*, not over an index range. A death is a
> **master-sent `RpcAll` on event code 36**; the `1.P<n>.LAST_DEATH_*` room properties are the
> persistent state, not the trigger.

Derived **2026-11-06** on `C:\games\recflare-2026`, build **20260323.14**, answering server-side
request #16. All RVAs are 2026-specific. Builds on
[synchronized-field-room-property-batching-2026](synchronized-field-room-property-batching-2026.md)
(the op-102 machinery), [actor-number-and-view-id-limits-2026](actor-number-and-view-id-limits-2026.md)
(the `actor ≤ 21,474` bound) and [rr-event-codes-and-rpc-dispatch](rr-event-codes-and-rpc-dispatch.md)
(`RR_RPC = 36`).

## 1. The room index is the player property `"rrPnr"`

Both the `Player.PlayerIndex` property and the CircuitsV2 node **Player Get Room Index** resolve to
one function:

| thing | RVA |
|---|---|
| `Player$$get_PlayerIndex` | `0x19FEED0` (thunk; `chase.py` cannot follow it) |
| `RecRoom.CircuitsV2.HJKFMYJZGWR$$PlayerGetRoomIndexStatic` | `0x11EC970` |
| `RecRoom.CircuitsV2.HJKFMYJZGWR$$PlayerGetRoomIndex` | `0x11ECB00` |
| inverse node `RoomIndexGetPlayer{,Static}` | `0x1207230` / `0x1206EB0` |
| **the implementation** | **`RecRoom.Networking.ZEGGYZZBFYC$$ZIHHGCFQYDS` `0x9AD3220`** |

`PlayerGetRoomIndexStatic` is a one-liner — fetch the player argument, call `ZIHHGCFQYDS`, emit the
int:

```
0x11ECA2D  CV2Get.OQUVZCZNUEL(...)                  ; read the Player pin
0x11ECA55  ZEGGYZZBFYC.ZIHHGCFQYDS(player)          ; <- the room index, in eax
0x11ECA64  CircuitSignal.NGCEHQPUEKQ(eax)           ; emit
```

`ZIHHGCFQYDS(JNIVCIZIPSX player)`:

```
0x9AD329E  if (!PEJBWBFHLBI.TRCOSNUMZGT()) …                 ; network-state guards
0x9AD32C2  if (!PEJBWBFHLBI.EMKOBOVMZAE())  -> 0x9AD338C     ; fallback
0x9AD32DE  props = player.<iface slot 3>()                   ; JNIVCIZIPSX.AESCHFFDGAD = custom properties
0x9AD3302  if (props.TryGetValue("rrPnr", out v))            ; literal 'rrPnr' 0xFD79218
0x9AD3358     -> unbox; return (int)v                        ; *** THE AUTHORITATIVE VALUE ***
0x9AD331A  if (player.<iface slot 1>())                      ; RWMMIQRFASE (is-local)
0x9AD334F     return RRPlayerNumbering.instance[+0x20]       ; the cached local number
           else -> 0x9AD338C                                 ; fallback
```

So **the room index is a player custom property called `rrPnr`**, and every client reads the same
value for the same player because it is replicated, not computed. It is *not* derived from the actor
number, and it is *not* in the join response — which is why a wire capture of the join handshake
cannot find it. Look in the op-103 player-property traffic instead.

### Who maintains it: `RecRoom.Networking.RRPlayerNumbering`

Statics / fields (declaration order):

```
RecRoom.Log                OMWAZFACTUS
RRPlayerNumbering          instance
JNIVCIZIPSX[]              SortedPlayers
string                     RoomPlayerIndexedProp   = "RRPlayerNumbering"   (.cctor 0x9ACE940)
int                        UGPBFYITOQU                                     (instance +0x20)
```

| method | RVA | role |
|---|---|---|
| `Awake` | `0x9ACD870` | |
| `OnJoinedRoom` | `0x9ACE0D0` | |
| `OnLeftRoom` | `0x9ACE140` | |
| `QKGDAAFMNXC` | `0x9ACE1F0` | player-properties-changed hook: reads `'rrPnr'` off the player, then `RefreshData` (`0x9ACE2A3`) |
| `PYVWLWAETEU` / `VLRPTVXCOOC` | `0x9ACE1E0` | alias pair (shared RVA) |
| `RefreshData` | `0x9ACE2E0` | `Enumerable.OrderBy(...).ToArray()` + `Array.IndexOf` → rebuilds `SortedPlayers` |
| `AssignPlayerNumbers` | `0x9ACD720` | the free-slot allocator |
| `ClearLocalPlayerNumber` | `0x9ACDC60` | removes `'rrPnr'` |

`AssignPlayerNumbers(int capacity, IList players, int count)` is a textbook PUN `PlayerNumbering`
allocator:

```
HashSet<int> used = new HashSet<int>(capacity);            ; 0x9ACD794
int missing = 0;
for (i = 0; i < count; i++) {                             ; 0x9ACD7C0
    n = players[i].<vtable +0x18>();                      ; existing number
    if (n < 0) missing++;                                 ; 0x9ACD7D2  js
    else used.Add(n);                                     ; 0x9ACD7E9
}
for (j = 0; j < capacity && missing > 0; j++)             ; 0x9ACD810
    if (!used.Contains(j)) { missing--; … }                ; 0x9ACD821
    … assign at 0x9ACD84F (indirect call through [r13+0x18])
```

⚠️ **`callxref 0x9ACD720` finds 0 direct callers.** Either it is reached indirectly (delegate /
interface) or it is dead and the live path is `RefreshData`'s sort + `IndexOf`. **Unresolved** — do
not state which without further work.

The two `OrderBy` key lambdas in `RefreshData`:

| lambda | RVA | key |
|---|---|---|
| `<>c$$MSWOBNVYMIV` | `0x9ACFB20` | `player.<iface slot 0>()` = **the actor number** |
| `<>c$$MRWFPGALREC` | `0x9ACFA80` | `ZEGGYZZBFYC.ZIHHGCFQYDS(player)` = the room index |
| `<>c$$MSRHEHCBCXM` | `0x9ACFAD0` | same as above |

So the ordering that underpins the numbering is by **actor number ascending** — the same order the
join response already uses, which is what makes the numbering agree across clients.

⚠️ `ugc.out_of_bounds_player_index` (`0xFD48BC8`) and `ugc.repeat_player_index` (`0xFD48F18`) are
**not** networking errors: both live in `OFYRLOBOYPO` (`YIOIMITCCFI 0x28D93E0`, `NJSWHDMFHIM
0x28C7C30`) in the RRUI layer — UGC room-configuration validation strings.

## 2. `P<n>` is the ACTOR NUMBER, and holders are per-player and lazy

`QPOMEWQYEQO$$SOOMCABFMPG(JNIVCIZIPSX player, string field)` **`0x9ADF8A0`** builds the key:

```
0x9ADF8E9  eax = player.<iface slot 0>()          ; interface dispatch, ecx = 0
0x9ADF8FE  box eax
0x9ADF913  String.Format("P{0}.{1}", boxed, field)    ; literal 'P{0}.{1}' 0xFCD1928
```

`RecRoom.Networking.DataTypes.JNIVCIZIPSX` (typedef **#63376**) slot order, from `md.py type`:

```
0 MRAOAUAYYFN   <- the int used as P<n>
1 RWMMIQRFASE   <- is-local
2 KYKMBNYTUVB
3 AESCHFFDGAD   <- custom properties dictionary  (where rrPnr lives)
4 DMZEEOWBMSZ   5 BUIKFTEGNKO   6 FCTWFLMNATX   7 GEXXAQOTBPX   8 SOMYKQOUANF
9 IFYCFYUWQYQ  10 ONYTRAXWJBC  11 GDETIBMDZUI  12 TXPQVQIAOHQ
```

Implementations of slot 0: `RecRoom.Foundation.ViewId$$MRAOAUAYYFN` **`0x99C2B30`** —
`id / 100000` by magic multiply (`0x14F8B589`, `sar edx,13`), i.e. **the owner actor number**, with
an `id == -1 → 0` special case on the Rooms-2 branch (`0x99C2B79`); and
`RecRoom.Networking.DGGDXSNNWDX$$MRAOAUAYYFN` `0xD0C6A0` (the shared `mov eax,[rcx+0x18]; ret`).

**So `P<n>` carries the actor number, never the room index.** The server's inference was right.

### Registration: lazy, keyed by the player object, no index range

For the combat keys the holder object is `.VJJGHVZEUFH` (18 fields), constructed at
**`0x24CE2E0`**, and it holds the player it belongs to in `IULKTZKSJBZ : JNIVCIZIPSX`. It is
created by:

```
GameCombatManager$$YYXDEONWSKJ(player)            0x2370160      ; 68 call sites
  Dictionary<JNIVCIZIPSX, VJJGHVZEUFH>.TryGetValue(player, out s)   ; methodSpec class inst #5813
  if (!found) {
      s = new VJJGHVZEUFH(player, …)              0x2370278
      s.KJVGDGOLXZQ(…)                            0x23702B8
      dict[player] = s;
  }
  return s;
```

That is a **GetOrCreate keyed by the player object** — not an array, not a range, not
`0..maxPlayers-1`. The 13 keys are registered when that object is built, so the registered set is
exactly `{P<actor>.<field>}` for the actors whose state has been touched. **Actor numbers 5, 6 and
171 are all equally fine.**

⚠️ **Structural ordering hazard (NOT a diagnosis).** `GameCombatManager` has no join hook — only
`OnPlayerDisconnected` `0x236B280`; there is no `OnPlayerJoined`/`OnPlayerConnected`. Creation is on
first access. An inbound `1.P<k>.HEALTH` for a player whose combat state has never been touched
locally therefore has no holder and hits the `KeyNotFoundException` below. **This is the same client
code that works in production**, so something normally creates the state early enough (most likely
avatar spawn, which happens for every player on join) — this is a hazard to be aware of, not an
explanation for a bug. Per the standing rule, the server is the variable.

## 3. How a death reaches the other clients

### The 13 keys

Read off the `lea` run in `VJJGHVZEUFH$$.ctor` `0x24CE2E0` — declaration order, and exactly the
13 the server observed:

```
 1 HEALTH                  2 SHIELD_OVER_TIME        3 LAST_DAMAGE_TIME
 4 LAST_REVIVE_TIME        5 SHIELD                  6 HEALTH_OVER_TIME
 7 INVINCIBILITY_END_TIME  8 LAST_DEATH_START_TIME   9 LAST_REVIVE_OTHER_TIME
10 DBNO                   11 ENEMY_TARGETS          12 TIMES_REVIVED
13 LAST_DEATH_END_TIME
```

Value types come from the holder generics: `VLUPMVMSGQJ<int>`, `<float>`, `<ObscuredFloat>`,
`VLEUVBFAEII<bool, ObscuredInt>`, `VMKKEPUKIYK<ObscuredBool, ObscuredFloat, ObscuredFloat,
ObscuredInt>` ×2, `VMPRBWOHSJT<bool, bool, float, float, float>`. `DBNO` = "down but not out".

⚠️ `LAST_DEATH_ST` / `LAST_DEATH_EN` on the wire are **shortened** forms of
`LAST_DEATH_START_TIME` / `LAST_DEATH_END_TIME` (those are the registered literals, `0xFC16A90` /
`0xFC16740`; `LAST_DEATH_ST` is not a literal anywhere). **The shortening routine was not located** —
do not assume a particular rule (a 13-character truncation fits both samples and `ENEMY_TARGETS`,
but that is a guess, and the same length as the key count is a coincidence).

### Authority and the trigger

Everything that mutates the state is a `Master*` method; clients ask via `RpcMasterRequest*`:

| master-side | RVA |
|---|---|
| `MasterDamagePlayer` | `0x23671D0` / `0x2367210` |
| `MasterKillPlayer` | `0x23673A0` |
| `MasterRequestPlayerOnPlayerDamage` | `0x2368120` |
| `MasterRequestEnemyOnPlayerDamage` / `…MiscPlayerDamage` | `0x2367AB0` / `0x2367CF0` |
| `MasterSetPlayerHealth` / `MasterResetPlayerHealth` / `MasterRestorePlayerHealth` | `0x2368F40` / `0x2368BC0` / `0x2368DB0` |
| `MasterRequestPlayerRevive` / `…SelfRevive` / `…StartHandshakeRevive` | `0x2368570` / `0x2368910` / `0x2368990` |

The PvP path, `MasterRequestPlayerOnPlayerDamage` `0x2368120`:

```
0x2368365  MasterDamagePlayer(...)                       ; writes HEALTH / LAST_DEATH_* -> op 102
0x2368390  get_NetworkedView
0x23683EE  RRNetworkView.RpcAll(RpcOnPlayerDamagedPlayer, …)   ; 3 call sites (0x23683EE/0x23684D2/0x2368179)
```

and `MasterKillPlayer` `0x23673A0`:

```
0x23673F2  YYXDEONWSKJ(victim)                           ; get/create state
0x2367449  VJJGHVZEUFH.WWPMMGTLPIP(…)                    ; set the fields
0x23674C2  VJJGHVZEUFH.FTQJQVANHRO(…)
0x23674CF  VJJGHVZEUFH.SZZKNGRDFKM(…)
0x23674E0  GameCombatManager.XNITSFLWFEB(…)              ; local MasterOnlyPlayerDeathEvent
0x236756D  RRNetworkView.RpcAll(RpcOnMiscKilledPlayer, MiscDamageToPlayer)
```

**So: the master applies the damage, writes the room properties, and broadcasts an `RpcAll`. The
`RpcAll` is what makes the other clients play the death; the room properties are the state a late
joiner or a re-reader recovers it from.** RPCs ride **event code 36 (`RR_RPC`)**, name-addressed by
ViewId + method-name string — see
[rr-event-codes-and-rpc-dispatch](rr-event-codes-and-rpc-dispatch.md). `RpcAll` ⇒ `RpcTarget.All 0`.

Receive-side handlers and the local events they raise:

| handler | RVA | event |
|---|---|---|
| `RpcOnPlayerDamagedPlayer` | `0x236E2B0` | |
| `OnPlayerDamagedPlayer` | `0x236B010` | |
| `OnPlayerDownedPlayer` | `0x236B350` | `PlayerDownedPlayerEvent` (`add_` `0x23719D0`) |
| `OnPlayerKilledPlayer` | `0x236B5B0` | |
| `RpcOnEnemyDownedPlayer` / `OnEnemyDownedPlayer` | `0x236E000` / `0x236A2F0` | `EnemyDownedPlayerEvent` (`0x23711B0`) |
| `RpcOnMiscDownedPlayer` / `OnMiscDownedPlayer` | `0x236AF30` (shared) | `MiscDownedPlayerEvent` (`0x2371660`) |
| `RpcOnPlayerRevive` | `0x236E4E0` | |
| — | | `MasterOnlyPlayerDeathEvent` (`0x2371510`) — **master-local only** |

**The sender is the master**, not the victim and not the killer. `MasterOnlyPlayerDeathEvent` fires
only on the master, so a circuit wired to it never runs on the other clients.

Read-side helpers worth knowing: `GetPlayerHealth` `0x2363140`, `GetPlayerLastDeathStartTime`
`0x23631A0`, `GetPlayerLastDeathEndTime` `0x2363170`, `IsPlayerDownButNotOut` `0x2364B10`,
`get_IsLocalPlayerEliminated` `0x2372550`.

## 4. An unregistered key aborts the whole update

From [synchronized-field-room-property-batching-2026](synchronized-field-room-property-batching-2026.md):
`BINQQTSJVFC` `0x9ADBFA0` loops over the key list and throws

```
new KeyNotFoundException("Key " + key + " not found, this indicates a protocol error")
                                                   ; 0x9ADC383 / 0x9ADC3D2
```

**inside** the loop, so **every key after the offending one is lost** — it is not per-key recovery.

Its only callers are `EGADHTHBJZP` `0x9ADCD50` (0x87 bytes) and `WEUSWEDACHF` `0x9ADE050` (a
tail-jump thunk). **Neither has a catch funclet** (no `call 0x2880` entry), so the exception
propagates past the synchronized-field layer into whatever dispatches the op-102 message.

⚠️ **Whether the session survives is UNVERIFIED** — I did not establish whether the named-message
dispatcher wraps handlers in a try/catch, and the available `Player.log` contains no occurrence of
the text (it is from an unrelated room-load failure). The log text to grep for is
`indicates a protocol error`.

## 5. The `"S"` entry = `[writerActorNumber, keys[]]` — self-declared and trusted

`HQKOEQLMDOE$$OSJWIKZHINZ(IDictionary payload, out int senderActor, out string[] keys)`
**`0x9ADDCE0`**:

```
0x9ADDD5F  call [klass+0x2D8]           ; a VIRTUAL on `this` (the transport) -> an int
0x9ADDD61  [r15] = eax                  ; provisional senderActor
0x9ADDDDB  payload.TryGetValue("S", out s)        ; literal 'S' 0xFCD… (0x9ADDD2C)
0x9ADDE2C  if (s.Count <= 0)  bail
0x9ADDE5A  unbox s[0]
0x9ADDE5F  ecx = *(int*)…
0x9ADDE61  [r15] = ecx                  ; *** OVERWRITES the transport's value with S[0] ***
0x9ADDE64  if (s.Count <= 1)  bail
0x9ADDE6E  rbx = s[1]
0x9ADDEB8  [r14] = (string[]) rbx       ; out keys
```

So the i32 is the **writer's own actor number, declared in the payload**, and it **wins over** the
value the transport layer supplies. The server-stamped NGO sender id is fetched and then discarded.

Its single consumer is the echo filter in `QPOMEWQYEQO$$NVXRAZBQPMW` `0x9ADF780`:

```
0x9ADF7ED  if (senderActor != myActorNumber) flags &= ~2;
0x9ADF7F5  if (flags & 2) return;                       ; own echo -> dropped
```

**No update is rejected on mismatch**; the comparison exists only to drop the sender's own echo. It
is not validated against anything.

⚠️ **This is the one place where renumbering would bite.** `S[0]` is client-authored and trusted. If
a server rewrote actor numbers without rewriting `S[0]` (and `P<n>`) consistently, a receiver whose
own actor number happened to equal a stale `S[0]` would silently discard that update as its own
echo — no log, no error.

## 6. Nothing assumes dense or small actor numbers

Checked and clear:

- **`P<n>`** — the actor number, formatted into a string; holders registered per player object via
  `GameCombatManager.YYXDEONWSKJ`'s `Dictionary<JNIVCIZIPSX, VJJGHVZEUFH>`. No range, no array.
- **the room index** — a *separate* dense `0..N-1` value, carried in `rrPnr` and self-assigned by
  the client; independent of the actor number, so it stays dense no matter how large actor numbers
  get.
- **`RRPlayerNumbering.SortedPlayers`** — built by `OrderBy(...).ToArray()` from the live player
  list, so it is sized by **player count**, not by actor number.
- **no `1 << actorNumber` mask and no `actorNumber % n` team/spawn selection** found. Team and spawn
  selection go through a *team player index* instead: `GameTeamManager.GetTeamPlayerIndex`
  `0x25FA480`, `GetPlayerAtTeamPlayerIndex` `0x25F9BC0`, `GameSpawnPoint.get_GameTeamPlayerIndex`
  `0xD106E0`, `GamePlayerSpawnPoint.get_SupportedTeamPlayerIndex` `0xD64E40` — a team-scoped index,
  not the actor number.

The only hard bound is the pre-existing one: **`actor ≤ 21,474`**, because Rooms-1 view and bulk ids
are `actor * 100000 + sub` in unchecked int32 — see
[actor-number-and-view-id-limits-2026](actor-number-and-view-id-limits-2026.md). A server-wide
counter reaching ~200 is far inside that.

**So: no renumbering is required.** If renumbering is done anyway (e.g. for Photon parity),
the requirement is *not* "dense and small" but "consistent": the same integer must appear as the
NGO `OwnerClientId`, in `P<n>`, in `S[0]`, and in the ViewId's high part — and `rrPnr` must be left
alone, because it is a different number with its own allocator.

## Still open

- `RRPlayerNumbering.AssignPlayerNumbers` `0x9ACD720` has **0 direct callers**; whether it is live
  (reached indirectly) or dead is unresolved, and with it the exact capacity bound it iterates to.
- The `LAST_DEATH_START_TIME` → `LAST_DEATH_ST` shortening routine is not located.
- Whether the op-102 dispatcher catches the `KeyNotFoundException` (⇒ whether the session survives
  one unregistered key) is not established.
- The fallback value `ZIHHGCFQYDS` returns at `0x9AD338C` when `rrPnr` is absent and the player is
  remote was not read; it matters for what a circuit sees before the property replicates.
