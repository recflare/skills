# Dorm exit overrider NRE on local-player spawn (2026 build)

> Two stackless-looking NREs at the **same frame**, one from `DormExitDoorOverrider.UPNDCAOOVMP`
> and one from `DormExitSignOverrider.UPNDCAOOVMP`, both via
> `DormExitOverrider.OnLocalPlayerCreated` → `SynchronizedFields.HLLHIGJPJKO`3.Set` →
> `RecRoom.DRORJRYTLBA.DRQUDZVNDXG(object, Type)`.
> **Cause: a `null` string component in a `SynchronizedField<bool,string,string>`.** The converter
> `DRQUDZVNDXG` has **no null guard** — a null value is an unconditional NRE.
> **Benign**: no join impact, no visual regression, fires at most once per dorm entry and only for
> the dorm's owner. Worth knowing because the fix is a **server-side config value**, not a patch.

Derived **2026-10-20** from build `20260323.14`, from a live `Player.log` pair at frame 49410.

## The exact failure

`RecRoom.DRORJRYTLBA.DRQUDZVNDXG(object a, Type b)` **`0xDEF630`** (bounds `..0xDEF6DE`) is a
value→target-type coercion helper:

```
0xdef65c: test rbx, rbx                 ; rbx = arg a
0xdef65f: je   0xdef6cd                 ; -> 0xc403a0 = the NRE thrower
0xdef66b: call System.Object$$GetType    ; a.GetType()
0xdef691: call RecRoom.DRORJRYTLBA$$CYWSOOQNBSP   ; find converter srcType -> b
0xdef69e: test rax, rax
0xdef6a1: jne  0xdef6b1                 ; converter found -> delegate invoke (tail jmp)
0xdef6a3: mov  rax, rbx                 ; else pass the value through unchanged
```

So `DRQUDZVNDXG(null, typeof(string))` **always** throws. There is no "null means leave it alone"
path. Every call site that can hand it a null reference type is an NRE waiting to happen.

## The chain, outermost first

| frame | RVA | what it does |
|---|---|---|
| `DormExitOverrider.OnLocalPlayerCreated` | `0x235ABF0` | calls vtable `[klass+0x238]` = `GJENVLBWPEM` unconditionally, then `[klass+0x248]` = `UPNDCAOOVMP` **only if** `Player.LocalPlayer.PlayerId == Matchmaking.CurrentRoom.CreatorAccountId` |
| `DormExit{Door,Sign}Overrider.UPNDCAOOVMP` | `0x235A7D0` / `0x235B560` | reads 3 values off the `RecRoom.OJHHBUWOOZE` field at `+0x40` and calls `Set` on its `HLLHIGJPJKO`3` field (`+0x58` door, `+0x78` sign) |
| `HLLHIGJPJKO`3.Set(a,b,c,checkPermission)` | `0x65B5EC0` (generic-shared, inst **#24297 = `['bool','string','string']`**) | short-circuits if all three already equal; else boxes them into an **`object[3]`** and calls `QPOMEWQYEQO.Set(arr, checkPermission, suppressCallback: false, requireModified: true)` |
| `QPOMEWQYEQO.Set` | `0x9ADF930` | thin forwarder; derives `b = (flags & 4) != 0` from `[this+0x40]` |
| `QPOMEWQYEQO.KNLLTZMWXQA` | `0x9ADF3A0` | permission check, `requireModified` compare, **network publish**, then `GZVZLBHWNUK` |
| `QPOMEWQYEQO.GZVZLBHWNUK` | `0x9ADECE0` | `old = get_Value()` (vtable `0x1C8`) → **`set_Value(arr)` (vtable `0x1D8`)** → revision bump `[this+0x50]` → change callback `[this+0x30]` |
| `HLLHIGJPJKO`3.WKQCQWTDRDC(object)` | generic-shared | the `set_Value` override — unpacks the `object[3]` and coerces each element with `DRQUDZVNDXG<T>`. **Throws here.** |

`DormExitOverrider.YINCCVZUZXL` `0x235AFC0` is the creator gate (`Player$$get_LocalPlayer` →
`get_PlayerId` vs `Matchmaking$$SYWBUHLOISP` → `RoomDTO$$get_CreatorAccountId`, then
`call [rax+0x248]`). That is why this only ever appears **in your own dorm**.

## Which component is null

The three values come from interface `RecRoom.OJHHBUWOOZE` (typedef **#10428**, 10 methods, no
fields), dispatched through the il2cpp interface-invoke thunk at `0x2350`
(`rcx` = slot, `rdx` = interface `Il2CppClass*`, `r8` = instance) with slots **2, 3, 4**. Sole
implementor: **`RecRoom.AYGCRIYBFLB`** (typedef #10420).

| slot | interface method | `AYGCRIYBFLB` body | value |
|---|---|---|---|
| 2 | `XALHAKHHUIW` → bool | `0xE313C0` | `HKWOPPFUUYY /*+0x68*/ == DormRoomExitTarget.Custom && BVJNJWYTISF /*+0x28*/ != null` |
| 3 | `XPMTSMTSVFO` → string | `0xE313E0` | `BVJNJWYTISF?.RawName` — `RoomDTO + 0x38` is `<RawName>k__BackingField` |
| 4 | `GUFLMCTNQKY` → string | folded trivial getter | `<BHESEEPXGDZ>k__BackingField /*+0x38*/` |

`RecRoom.DormRoomExitTarget` (typedef #10427) = **`Watch = 0`, `Custom = 1`**.

**Slot 3 is the null.** `BVJNJWYTISF` (`RecNet.Rooms.RoomDTO` at `+0x28`) is the room resolved from
the LiveOps key `LiveOps.DormExit.CustomTargetRoom`; with no such key it stays `null`, so
`XPMTSMTSVFO` returns `null` and `XALHAKHHUIW` returns `false` in the same breath. Slot 4 is *not*
the culprit — it is assigned `""` by the config-apply path below, which always runs.

## Where the values come from — `api/gameconfigs/v1/all`

`RecRoom.AYGCRIYBFLB.VQZGAVQPNPU` **`0xE30FD0`** (bounds `..0xE313B7`) is the config-apply method.
It reads `RecNet.LGHEBYOBKGV::Get<T>(string key, T default)` (the LiveOps/remote-config interface,
typedef #21797; sole implementor `RecNet.UWGOSGURDET`, whose store is filled from
**`GET api/gameconfigs/v1/all`** — literal `0xFC4A590`, static route descriptor built in
`UWGOSGURDET$$.cctor` `0x943C0F0`, failure logged as `"Failed to get all GameConfigs"`):

| key | default | lands in |
|---|---|---|
| `LiveOps.DormExit.Target` | `"DefaultToWatch"` | `HKWOPPFUUYY` `+0x68` (`DormRoomExitTarget`) |
| `LiveOps.DormExit.CustomDisplayName` | `""` | `<YVSNJEYTUOK>` `+0x40` |
| `LiveOps.DormExit.CustomInteractionLabel` | `""` | `<BHESEEPXGDZ>` `+0x38` → **slot 4** |
| `LiveOps.DormExit.CustomBGColor` | — | `ColorUtility.TryParseHtmlString` → `Color?` `+0x48` |
| `LiveOps.DormExit.SettingsOptionLabel` | `"Hub World"` | `<NXMOUQTXVWZ>` `+0x60` |
| `LiveOps.DormExit.CustomTargetRoom` | `""` | async room lookup → `BVJNJWYTISF` `+0x28` → **slot 3** |

`VQZGAVQPNPU` is called from `AYGCRIYBFLB..ctor` `0xE315B0` (two sites) and from the
config-changed handlers `EUJPFCUUFJK` `0xE30C30` / `XZCGNIXOVPK` `0xE313F0`, so the string defaults
*are* applied even with an empty config — only the room lookup can leave a null.

⚠️ **Not pinned:** which Rooms route resolves the name to a `RoomDTO`. The lookup is async
(`AsyncTaskMethodBuilder.Start` at `0xE31349`) and the state machine's `MoveNext` is generic-shared
and not adjacent to the class, so `callxref` does not reach it. The injected client is
`RecNet.Rooms.NFIQEQJDFAG` `LINUDCFWKSI` `+0x20` (implementor
`RecNet.Rooms.RoomsClientStaticProxy`, 100+ methods). A room-name→`RoomDTO` route is **not** in
`wire-shapes/CATALOG.md` yet.

## Why it is harmless

The throw lands in `set_Value`, i.e. **after** the publish in `KNLLTZMWXQA` but **before** the rest
of `GZVZLBHWNUK`. Consequences:

- the revision counter `[field+0x50]` is not bumped;
- the field's change callback `[field+0x30]` never fires (it was requested —
  `suppressCallback: false`, `0x65B615F: xor r9d, r9d`);
- `KNLLTZMWXQA`'s tail after `GZVZLBHWNUK` (`flags |= 2`, the second publish at `0x9ADF59B`) is
  skipped;
- the `object[3]` may already have gone out on the wire — the publish at `0x9ADF4C9`/`0x9ADF4EE`
  runs only when `(flags & 4)`, which is runtime state.

None of that is visible, because the *apply* side is `GJENVLBWPEM` (vtable `0x238`), which
`Start` `0x235AD70` and `OnLocalPlayerCreated` call **directly and unconditionally** on a separate
path. The door keeps its scene-default `TeleportationPortal` target and the sign its default text —
which is the correct behaviour when there is no custom exit target anyway.

The per-handler `try/catch` is in `RecRoom.BQUYOYJDJCS.Invoke()` — that is why the door and the sign
each log their own exception at the same frame instead of the first aborting the second.

## Server-side options

1. **Leave it.** Nothing downstream depends on it. This is the recommendation.
2. Serve `LiveOps.DormExit.CustomTargetRoom` in `GET api/gameconfigs/v1/all` as a room name that
   resolves to a real `RoomDTO`. That silences both NREs — but it also makes `XALHAKHHUIW` eligible
   to return `true`, so pair it with `LiveOps.DormExit.Target` left at its `DefaultToWatch` default
   unless you actually want the dorm exit door re-pointed.

Setting `LiveOps.DormExit.Target` alone does **not** help: slot 3 is read and coerced regardless of
the target enum.

Related: [cv1-mappings-join-nre-2026](cv1-mappings-join-nre-2026.md) (the 404 cascade — `LiveOps.*`
keys were already on its missing list), [post-join-residual-log-items-2026](post-join-residual-log-items-2026.md).
