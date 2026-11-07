# Synchronized fields: how room-property writes are batched, flushed and applied (2026)

> The client already coalesces room-property writes by key into a `Dictionary` and sends ONE op-102
> message per flush — but `XVLRBMXBFXK` 0x9ADE350 **force-flushes the instant a key would overwrite
> an unsent value**, so N `Set` calls to one key inside one frame produce exactly N single-key
> messages. That is the source of the 2,000–38,000-message batches. On receive, the only per-message
> side effect is a change counter (`QPOMEWQYEQO+0x50`); the change callback is a parameterless
> `Action` gated on `old != new`, and the sender's own echo is explicitly discarded.

Derived **2026-11-06** on `C:\games\recflare-2026`, build **20260323.14**, via
[recflare-2026-static-index]. All RVAs are 2026; none of them survive a client upgrade.

## Cast

| thing | 2026 name | RVA / id |
|---|---|---|
| per-frame driver | `SynchronizedFieldHandler.LateUpdate` | `0x219E070` |
| façade | `PUNNetworkManager.SendPendingRoomUpdates` / `…PlayerUpdates` | `0x15DFE70` / `0x15DFDF0` |
| backing interface | `RecRoom.Networking.SynchronizedFields.CHMQKBZFKAM` | typedef **#59501**, 18 slots |
| backing impl (the property store) | `…SynchronizedFields.HQKOEQLMDOE` | typedef **#59506** |
| transport subclass | `.QCPURAWMNPT` | `.ctor 0x2195F90` |
| one synchronized field | `…SynchronizedFields.QPOMEWQYEQO` | typedef **#59505** |
| field holder (generic) | `…SynchronizedFields.VLUPMVMSGQJ<T>` | generic — not in `methods.pkl` |
| registration helper | `…SynchronizedFields.PYYKKTMDHGB::OTDLLCUKOZB<T>`, `SyncData.From` | `SyncData.From 0x9AE0000` (**267** call sites) |

`CHMQKBZFKAM` slot order (0-based, as `md.py type CHMQKBZFKAM` prints it) — the `ecx` value at the
`sub_2530` interface thunk is this index:

```
0 ZXVAOWZZPYB   1 UDLRDKXWCRK   2 RDAQRODRSQN   3 Initialize    4 MEEQOUGEIRG   5 XOLUVPEUUNY
6 XVLRBMXBFXK   <- stage a ROOM-scoped write      (key, value)
7 BMDYWOMVLDM   <- stage a PLAYER-scoped write    (key, ?, value)
8 REPRDDNTUSL   9 KKTAAVPLUYF  10 OOEKGCJAFXW  11 EWNGHYBZNWE  12 JNFCTUUYGUB
13 EWNGHYBZNWE 14 JNFCTUUYGUB
15 CMULSMNIGUI  <- FLUSH pending ROOM properties
16 BJPMKQMKZQK  <- FLUSH pending PLAYER properties
17 CFROENWGNAZ  <- drop every staged+stored key with a given prefix (teardown)
```

`HQKOEQLMDOE` instance layout (declaration order, all 8 fields):

```
+0x10  Dictionary<object,object>  SBYUTKNJKUR   pending ROOM writes      (staging, coalescing)
+0x18  List<string>               TPNSDQJFVPZ   pending ROOM removals
+0x20  Dictionary<object,object>  TBJKRZWWUPF   pending PLAYER writes
+0x28  List<string>               QCDEMPQFFBX   pending PLAYER removals
+0x30  bool                       VYFQZHHNBDJ
+0x38  Dictionary<string,object>  KEFVWRVFBGN   the local ROOM property bag   <- merge target
+0x40  Dictionary<JNIVCIZIPSX, Dictionary<string,object>>  FPMKFQFEHYL        per-player bags
+0x48  HashSet<string>            IXWZSZOCCFM   registered-key -> field map lookups
```

`QPOMEWQYEQO` instance layout:

```
+0x10 Stack<CHMQKBZFKAM> NEVRPOFFVBG   +0x18 bool LVGZWBURLUD   +0x20 JNIVCIZIPSX ZVRGIMZDIMZ
+0x28 CIZSGDLSXXQ VCAJEJENTLV          +0x30 Action OTLTFWAVXED  (the change callback)
+0x38 CHMQKBZFKAM XPLUTNUNLFB          (the backing store)
+0x40 Flags XHLSMLWWHCX                bit0=1 dead/disposed · bit1=2 LOCAL-AUTHORITATIVE
                                        bit2=4 (read by `Set` 0x9ADF930 and `ZKPWRGVAXUL`)
                                        bit3=8 set on a local-only write
+0x48 object <YGQONKXPJOZ>             the boxed value
+0x50 int    <JFURXHTEHWD>             CHANGE COUNTER — the only per-message state
```

## Write path — why one key can produce thousands of messages

```
QPOMEWQYEQO.Set(value, …)                       0x9ADF930   (thin wrapper, forwards the compare flag)
  -> KNLLTZMWXQA(value, net, permCheck, …, compare)         0x9ADF3A0
       if (permCheck && net) and !ARIQEFXXHBQ()  -> return          // 0x9ADE730, permission gate
       if (compare && WJNQPFNORNA(value, Get())) -> return          // 0x9ADF9C0  EQUAL => NO WRITE
       if (!net)  { flags |= 8|2; GZVZLBHWNUK(value, …); return; }   // local only, nothing on the wire
       backing.slot6 XVLRBMXBFXK(key, value)     // room scope   (slot7 for player scope)
       flags |= 2
       GZVZLBHWNUK(value, …)                     // <- APPLY LOCALLY, IMMEDIATELY
```

```
HQKOEQLMDOE.XVLRBMXBFXK(key, value)             0x9ADE350
    if (!klass[0x308]())  return;                       // not connected
    if (!klass[0x318]())  return;                       // not allowed to write
    if (pending.ContainsKey(key)                        // 0x9ADE3F3  Dictionary.ContainsKey
        ||  pending.Count > 0x32)                       // 0x9ADE40C/0x9ADE411  limit 50
        CMULSMNIGUI();                                  // 0x9ADE41B  *** FLUSH NOW ***
    pending[key] = value;                               // 0x9ADE436
    removals.Remove(key);
```

```
HQKOEQLMDOE.CMULSMNIGUI()                       0x9ADCAF0   (= interface slot 15)
    if (!klass[0x308]())      return;
    if (pending.Count <= 0)   return;
    LLGSNKOIFCS(pending, removals, 0)           0x9ADD540   // payload-trace log only, scope tag 'S'
    klass[0x328](pending)                                   // -> QCPURAWMNPT.QCNXMFABQTD
    pending.Clear();  removals.Clear();
```

```
QCPURAWMNPT.QCNXMFABQTD(pending)                0x2195860
    if (this.NQHFFYIFCGO /*quitting*/) { log 'Trying to send photon room updates to server while
                                              application is quitting - this should not be happening';
                                         return; }
    payload = <build once from the whole dictionary>        0x2195B1C
    if (XOKJTETAYJW.HFBVZPEQACG())  ObjectModelManager.CHIQRJZUCBD() -> ONE send   (ecx=0x15)
    else                            PEJBWBFHLBI.GTZPFOOLMWN()        -> ONE send   (ecx=3)
```

**There is no per-entry send loop anywhere.** One flush = one op-102 message = one dictionary of up
to 51 keys.

### The consequence

`SynchronizedFieldHandler.LateUpdate` flushes once a frame, so the *steady-state* shape is one
multi-key message per frame. But `XVLRBMXBFXK` refuses to let a staged value be overwritten before
it has gone out: it flushes first. So **a loop that writes the same key N times inside one frame
emits exactly N messages, each carrying that one key.** A 2,461-message run of `22.SD_OTV` is 2,461
`Set` calls, not 2,461 frames.

The client is therefore deliberately preserving every intermediate value of a key on the wire. That
is the one thing a server-side coalescer changes — see "what consumes the sequence" below.

⚠️ **It is not a retry storm.** Neither `XVLRBMXBFXK` nor `CMULSMNIGUI` nor `QCNXMFABQTD` has a
retry, a queue-depth check or an ack; a write that cannot go out is dropped silently at the two
`klass[0x308]`/`klass[0x318]` guards. Nothing re-sends.

## Read path

```
OSJWIKZHINZ(payload, out keys, out senderActor)  0x9ADDCE0   // unpack; senderActor -> [r15]
BINQQTSJVFC(payload, …)                          0x9ADBFA0
    foreach (key in keys)
        if (!map.TryGetValue(key, out field))                      // [this+0x48]
            throw new KeyNotFoundException("Key " + key +
                  " not found, this indicates a protocol error");  // 0x9ADC383/0x9ADC3D2
        XKCWCWEVUEU(field, value, senderActor)   0x9ADE060
XKCWCWEVUEU: one QPOMEWQYEQO -> NVXRAZBQPMW ;  List<QPOMEWQYEQO> -> NVXRAZBQPMW on each
```

```
QPOMEWQYEQO.NVXRAZBQPMW(value, senderActor)      0x9ADF780
    if (senderActor != myActorNumber) flags &= ~2;     // 0x9ADF7ED/0x9ADF7F1
    if (flags & 2)  return;                            // 0x9ADF7F5  *** OWN ECHO IS DISCARDED ***
    GZVZLBHWNUK(value, suppressCallback: false, compare: true)
```

```
QPOMEWQYEQO.GZVZLBHWNUK(value, suppressCallback, compare, …)   0x9ADECE0
    if (flags & 1) return;
    old = klass[0x1C8]();                 // get current
    klass[0x1D8](value);                  // store
    JFURXHTEHWD = (JFURXHTEHWD + 1) % int.MaxValue;    // 0x9ADED5D..0x9ADED7B  <- per-message
    if (suppressCallback)                        return;
    if (OTLTFWAVXED == null)                     return;
    if (compare && WJNQPFNORNA(value, old))      return;   // EQUAL => NO CALLBACK
    OTLTFWAVXED.Invoke();                                  // parameterless Action, no value, no seq
```

`WJNQPFNORNA(a, b)` `0x9ADF9C0` is a deep compare: both `as IList` → length then element-wise
recursion; otherwise a tail-jump to `object.Equals(a, b)` (`0x89CA550`, a shared body `methods.pkl`
labels `System.Reflection.PropertyInfo$$op_Equality`). **Boxed primitives compare by value**, so a
repeat of the same number is detected as equal.

## What consumes the *sequence* of values

Only `JFURXHTEHWD` (`QPOMEWQYEQO+0x50`), bumped once per applied value on both the local and the
remote path. It has no non-inlined getter, and I did not locate a consumer (the type's TypeInfo slot
`0xFCA8350` has 89 refs, mostly UJect registration). Everything else is final-value-only:

- the stored value is one slot (`+0x48`);
- the change callback is a parameterless `Action` — it re-reads the current value and cannot observe
  how many writes produced it;
- the callback is already gated on `old != new`, so a run of identical values fires it **once**
  today;
- the room bag `KEFVWRVFBGN` is a `Dictionary<string,object>` — a merge target, last write wins.

⚠️ The counter's absolute value is already client-specific (a late joiner starts at 0; the writer
increments its own copy at `Set` time while receivers increment at apply time), so it cannot be
meaningfully compared across clients — but that is an argument, not a located consumer.

## Ordering across keys

Staging is a `Dictionary<object,object>` and the inbound side is a loop over the key list. No code
sequences one key against another; each key lands in its own `QPOMEWQYEQO` with its own `Action`.
Because the sender already hands an unordered `Dictionary` to `QCNXMFABQTD`, **the relative order of
distinct keys inside one message is already arbitrary**, so preserving "each key's last write in the
position of its last occurrence" is strictly stronger than anything the client guarantees.

## Photon's `PropertiesChanged` is dead in this build

`OnPhotonCustomRoomPropertiesChanged` has **exactly one** implementor in the whole image —
`RecRoom.ISIGTRQRRBU` — and it resolves to `0xD0A4C0`, the shared empty-body stub (`ret`), as does
`OnPhotonPlayerPropertiesChanged` and the other 20-odd `IPunCallbacks` members on that type. The
client does not consume Photon room-property notifications at all; the live path is the
`SynchronizedFields` layer above, whose own semantics are "merge each received key into a dictionary,
last write wins". A server that merges and sends fewer messages is the shape the client implements
for itself.

## Key naming

- room scope: `"<group>.<ABBREV>_<FIELD>"`; player scope: `"P{0}.{1}"` (`0x9ADD053`, `0x9ADDFE5`,
  `0x9ADE4BD`); the payload trace tags scope with `"S"` / `"P"` (`0x9ADD596`, `0x9ADD271`).
- `ABBREV` comes from the virtual `XYFFBKOESIK`:
  **`SD` = `RecRoom.CircuitsV2.RoomSettings.RoomSkydome`** (`0x12AD5F0`),
  **`BO` = `RoomBackgroundObjects`** (`0x12A90C0`),
  **`FND` = `RoomFog`** (`0x12AAC20`),
  **`RS` = `RoomSun`** (`0x12B1BF0`).
- Each element registers its own *setting* keys in `Awake`: `SD_HC SD_GT SD_HS SD_ST SD_GB SD_SB
  SD_HT` (`RoomSkydome.Awake 0x12AAFC0`, 7 × `SyncData.From`), `FND_SD FND_CI FND_FD`
  (`RoomFog.Awake 0x12A9760`), and `RoomSun.Start 0x12B1150` registers 13.
- A shared generic base routine (`0x7A99150` preload + `0x7A9950A` body, generic-shared so
  `methods.pkl` mislabels it `UnityEngine.UIElements.EventCallbackList$$Clear`) registers the seven
  common suffixes against the same `ABBREV`, with these value types:

  | suffix | value type (methodSpec inst) | change `Action` registered? |
  |---|---|---|
  | `_MI`  | `System.Guid` (#583) | no |
  | `_OTV` | **`bool` / `int` / `float`** (#7775 — one registration over three type args) | **yes** |
  | `_BT`  | `float` (#88) | no |
  | `_EIO` | `bool` (#85) | no |
  | `_RFM` | `int` (#86) | no |
  | `_RO`  | `System.Guid[]` (#7769) | no |
  | `_ICA` | `bool` (`VLUPMVMSGQJ<bool>.ctor`, class inst #85) | **yes** |

  The same routine builds `UZOSRLDNFPV<Action>` and
  `UZOSRLDNFPV<Action<JNIVCIZIPSX, RecRoom.Systems.PlayerRoles.GameRole>>` lists.

⚠️ **The English names behind `_MI _RO _EIO _ICA _RFM _OTV _BT` are NOT recovered.** The owning
class is generic, so the registration body is generic-shared and unattributed, and
`callxref`/`mxref` reach neither it nor the property names. Types and callback presence above are
read directly off the registration; anything else about them would be a guess.

## Still open

- The **180 s** room-load / buffered-event timeout constant is still not located: `immfind` finds no
  32-bit `180000` (`0x2BF20`) or `180.0f` (`0x43340000`) immediate anywhere near the room-load code,
  so it is almost certainly a `double`/`TimeSpan.FromSeconds(180)` constant loaded from `.rdata`,
  which the current tooling cannot scan. See
  [buffered-room-event-echo-stall-2026](buffered-room-event-echo-stall-2026.md).
- No consumer of `JFURXHTEHWD` located.
- What loop calls `Set` thousands of times per frame on `_OTV` / `_ICA` / `_BT` is not identified
  (the writers are generic `VLUPMVMSGQJ<T>` wrappers). A retry is ruled out; a per-tick circuit
  write is consistent with the evidence but unproven.
