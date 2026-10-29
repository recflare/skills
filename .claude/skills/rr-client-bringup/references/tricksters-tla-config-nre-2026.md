# `TrickstersTLAManager` ctor NRE = the `LiveOps.TLA.Tricksters` game config is missing

> A crash report whose stack is
> `TrickstersTLAManager.VKRUFYNKGCE` ← `AsyncTaskMethodBuilder.Start` ←
> `TrickstersTLAManager.SAVGDXVMHSP` ← `AsyncTaskMethodBuilder.Start` ←
> `TrickstersTLAManager.REEVPVXDANZ` ← `..ctor` ← `RuntimeConstructorInfo.InternalInvoke`
> means the server did not serve a usable **`LiveOps.TLA.Tricksters`** game config.
> The field `TrickstersEventConfig` is dereferenced with **no null guard** in the first
> *synchronous* segment of the async chain, so the NRE escapes `Start` twice and kills the
> **reflective DI construction** of the manager.
> **Nothing to do with images** — `recNetImageCache` in the ctor signature is a red herring; the
> image preload is downstream of the throw and never runs.

Derived **2026-10-22** from build `20260323.14`. Same family as
[dorm-exit-overrider-nre-2026](dorm-exit-overrider-nre-2026.md) — another `LiveOps.*` key from
`GET api/gameconfigs/v1/all` that the client consumes without a guard.

## Reading the stack

The frames are **async method names, not `MoveNext`** (IL2CPP attributes a struct state machine's
`MoveNext` to its method, and inlines the tiny entry stubs into their callers — which is why
`callxref` reports **0 direct call sites** for `SAVGDXVMHSP` `0x20A75D0` and `VKRUFYNKGCE`
`0x20A7AF0`). The real chain is:

| frame | RVA | what it really is |
|---|---|---|
| `..ctor` | `0x20A93B0` | constructed **reflectively** by UJect (`UJect.KLUMUBWDFVY`) |
| `REEVPVXDANZ` | `0x20A7260` | plain `void`; reads the config, then starts + `.Forget()`s the next method (`Create` `0x20A7514`, `Start` `0x20A7563`, `get_Task` `0x20A756F`, forget `0x20A7591`). **Only caller is the ctor**, at `0x20A9F33` |
| `SAVGDXVMHSP` | `<UpdateAndPreloadData>d__79$$MoveNext` `0x20B22A0` | starts + awaits the next method (`Create` `0x20B23D2`, `Start` `0x20B242A`, `get_Task` `0x20B2436`) |
| `VKRUFYNKGCE` | `<UpdateProgressionEvent>d__80$$MoveNext` `0x20B39A0` | **throws**, before its first await |

> 🔑 **The obfuscator renames methods but NOT the compiler-generated nested state-machine types**, so
> `TrickstersTLAManager`'s 24 nested types hand back the original method names for free
> (`<UpdateAndPreloadData>d__79`, `<UpdateProgressionEvent>d__80`, `<RunPeriodicUpdate>d__87`,
> `<CreateGhostEntry>d__88`, `<SpawnFreebieGhost>d__93`, `<RecordGhostsCollected>d__103`,
> `<UpdateSquadId>d__112`, …). Pair them to obfuscated methods by signature, then disambiguate by
> **state-machine struct size** (`<UpdateProgressionEvent>d__80` is `0x48` bytes, matching exactly
> what the `VKRUFYNKGCE` stub zeroes at `0x20A7B30`–`0x20A7B47`). `d__N` numbers do **not** index
> the surviving metadata method order. New toolkit scripts for this (`il2cpp-2026/`):
> **`nested.py <TypeName>`** lists a typedef's nested types with their methods,
> **`mtype.py <substr>`** finds typedefs by name substring, **`morder.py <TypeName>`** prints a
> type's methods in metadata declaration order.
>
> Local functions survive too: `XQHQUNHFMFY(string)` is
> `<UpdateAndPreloadData>g__LoadImage|79_0` — the image preloader, awaited 4× in `d__79`
> **after** the throw point.

## The throw

`<UpdateProgressionEvent>d__80$$MoveNext`, initial entry (`<>1__state == -1`, so it falls through
the whole state jump table to `0x20B3B81`):

```
0x20b3b81  test rsi, rsi            ; rsi = <>4__this
0x20b3b84  je   0x20b4588           ; -> 0xC403A0  (raise NullReferenceException)
0x20b3b8a  mov  rax, [rsi + 0x80]   ; this.IFRZNUZUPGC : TrickstersEventConfig
0x20b3b91  test rax, rax
0x20b3b94  je   0x20b4583           ; -> 0xC403A0  *** THE NRE ***
0x20b3b9a  cmp  qword ptr [rax + 0x30], 0   ; config.ProgressionEventId
0x20b3b9e  jg   0x20b3bbb
0x20b3ba0  mov  qword ptr [rsi + 0xf8], 0   ; ProgressionEventId <= 0: clear the cached DTO, return
```

`0xC403A0` is the codegen null-reference throw helper. There is **no `try`** between here and
`.ctor`, and because the throw happens **before the first await**, it propagates synchronously out
of both `AsyncTaskMethodBuilder.Start` calls and out of the constructor — so the DI container's
`RuntimeConstructorInfo.Invoke` is what reports it.

Later in the same pre-await segment (reached when `ProgressionEventId > 0`) two more fields are
dereferenced unguarded — `[this+0xB8]` = `XKCOLGLQMPY : RecNet.LMHPAVDNWPW`
(`recNetProgressionEvents`, throw at `0x20B4598`) and `[this+0x80]` again at `0x20B3CAD` — but
those are injected dependencies, which UJect would have failed on earlier. **The config is the
variable.**

## The only writer of that field

`REEVPVXDANZ` `0x20A7260`, and it is the **sole** writer of `[this+0x80]`:

```
0x20a72ce  mov byte ptr [rbx + 0x68], 1     ; CCQQRCKNVGS = true
0x20a72d2  mov r8, [rbx + 0xa8]             ; this.JAIQTXDFUSV : RecNet.LGHEBYOBKGV  (gameConfigsProvider)
0x20a72d9  test r8, r8
0x20a72dc  je   0x20a75bb                   ; -> 0xC403A0  (provider itself null => NRE here instead)
0x20a72e2  mov ecx, 3
0x20a72e7  mov r9, [rip + …]                ; "LiveOps.TLA.Tricksters"   literal 0xFCCABF8
0x20a72f5  call 0x23e0                      ; interface dispatch on the provider
0x20a7304  call 0x3c07b80                   ; cast/parse -> TrickstersEventConfig
0x20a7309  mov qword ptr [rbx + 0x80], rax  ; this.IFRZNUZUPGC = result      <-- ONLY WRITER
```

`mxref` on literal **`0xFCCABF8`** gives exactly **2** refs, both in this method — so
`LiveOps.TLA.Tricksters` is read in one place and feeds one field. If the key is absent, or its
value does not parse into `TrickstersEventConfig`, the field stays `null` and the NRE is
unconditional.

⚠️ **Not pinned**: whether the provider call is `LGHEBYOBKGV.Get<T>(key, default, parser)` or
`ZXWWRLSIAEB(string)` plus a JSON parse at `0x3C07B80` — both are in `methods.pkl` gaps and the
register layout (`r8` = provider, `r9` = key, `ecx` = 3) does not match a plain instance generic
call. It does not change the conclusion: one key in, one nullable field out.

`RecNet.LGHEBYOBKGV` (the provider interface) is:
`BHPIRXWHDPS()`, `KQGSXEIGJLQ/EBIMLXCCPKN(Action<GameConfigAccessRecord>)`,
`ZXWWRLSIAEB(string)->string`, **`Get<T>(string key, T defaultValue, PrefParsers.XMNUSNLGNCS<T>)`**,
`CWCTJLGLIGO(string)->bool`, `EETZPBNYFWB(bool)`, `FSEKRYEFVND/KEWKBCSBPUU(Action)`.

## Server fix

Serve `LiveOps.TLA.Tricksters` from `GET api/gameconfigs/v1/all` with a value that deserializes into
`TrickstersEventConfig`. **Cheapest safe value: set `ProgressionEventId` to `0`** — the branch at
`0x20B3B9E` then clears the cached `ProgressionEventDTO` and returns without ever touching
`recNetProgressionEvents`, the leaderboard routes, or the image preloader.

`.TrickstersEventConfig` (typedef #1767) — 30 fields, **all names unobfuscated**:

| off | type | name |
|---|---|---|
| 0x10 | `.TrickstersGhostConfig` | `GhostConfig` |
| 0x18 / 0x1c | int | `MaxSpawnableSpots` · `MaxSimultaneousGhosts` |
| 0x20 | float | `SpawnCooldown` |
| 0x24 / 0x28 | float | `ExcludedSpawnForwardAngles` · `ExcludedSpawnBackwardAngles` |
| **0x30** | **long** | **`ProgressionEventId`** ← the gate |
| 0x38 | long | `TimeLimitedEventId` |
| 0x40 / 0x44 | float | `DistanceBetweenSpawns` · `GhostSpawnChance` |
| 0x48 / 0x4c / 0x50 | float | `CollisionDefaultThreshold` · `CollisionCrouchThreshold` · `CollisionProneThreshold` |
| 0x54 / 0x58 | float | `MagnetAttractDistance` · `MagnetBoostedExtents` |
| 0x60 / 0x68 | string | `PointsToastImageLeft` · `PointsToastImageRight` |
| 0x70 / 0x74 / 0x78 | float | `PointsToastDuration` · `PointsToastAlpha` · `PointsIconAlpha` |
| 0x80 | list | `DisabledRoomIds` |
| 0x88 / 0x8c | int | `MuteDuration` · `MaxDailyProgress` |
| 0x90 | list | `ConsumableIdsForPoints` |
| 0x98 | list | `PreloadableImages` |
| 0xa0 | int | `ChatSuppressionMode` |
| 0xa4 | bool | `EnableGhostRecycling` |
| 0xa8 / 0xac | int | `ThrownWeaponCaptureMultiplier` · `AggregateBufferCount` |
| 0xb0 | float | `AggregateFlushDelay` |

`PreloadableImages` is what `<UpdateAndPreloadData>d__79` iterates (its `<>7__wrap1` is
`Enumerator<string>`) and hands to `recNetImageCache` — i.e. the images only load **after** the
progression-event step succeeds.

If the Tricksters event should simply be off, note that **there is no off switch on this path**:
the manager is constructed by DI regardless and `REEVPVXDANZ` always runs. A config object with
`ProgressionEventId: 0` is the "disabled" state; an absent key is a crash.

## `TrickstersTLAManager` field map (the useful half)

| off | type | field | ctor param |
|---|---|---|---|
| 0x68 | bool | `CCQQRCKNVGS` | set `true` first thing in `REEVPVXDANZ` |
| **0x80** | `.TrickstersEventConfig` | **`IFRZNUZUPGC`** | — (from the game config) |
| 0xa0 | `.FPGPSGBQPRA` | `WFTHDXABWOD` | `localPlayerPedometer` |
| 0xa8 | `RecNet.LGHEBYOBKGV` | `JAIQTXDFUSV` | `gameConfigsProvider` |
| 0xb0 | `RecRoom.Reactions.KWLRWMSEHCP` | `VQEBVQLEQSQ` | `customizer` |
| 0xb8 | `RecNet.LMHPAVDNWPW` | `XKCOLGLQMPY` | `recNetProgressionEvents` |
| 0xc0 | `RecRoom.Notifications.XBQMFDEXCLZ` | `XGQCKKAXSZQ` | `notifications` |
| 0xc8 | `RecRoom.Preferences.STAKPLUPOSH` | `PYOUHBOYEAW` | `accountPrefs` |
| 0xd0 | `RecNet.QYBATIJDFLA` | `AXVYEPISFLO` | `recNetMatchmaking` |
| 0xd8 | `RecNet.JTUOBZHLHMX` | `VCTIFTTPRYF` | `recNetImageCache` |
| 0xe0 | `RecNet.Interfaces.IGQMUQTCOVA` | `GSPRMAAZRCE` | `recNetOktoberTricks` |
| 0xe8 | `RecRoom.ProgressionEvents.RCSWNUGOUJA` | `GSEZWLRUZIJ` | `theProgressionEventsManager` |
| 0xf0 | `RecRoom.Audio.KBHKEFUCYYS` | `AWXNIIMMLXL` | `theAudioManager` |
| 0xf8 | `RecNet.ProgressionEventDTO` | `<XHJWWPLTEDV>k__BackingField` | cached; cleared when `ProgressionEventId <= 0` |

`RecNet.Interfaces.IGQMUQTCOVA` (`recNetOktoberTricks`) has only two members and is **not** on the
crash path:

```csharp
Task      MUFLBNPCWJN(bool, int, CancellationToken)
Task<int> KGHAOZAGJOK(CancellationToken)
```
