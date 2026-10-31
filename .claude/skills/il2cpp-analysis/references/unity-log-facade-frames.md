# Unity log facade frames

> In Rec Room Unity-side stack traces the top 5 frames are always the logging facade (DFFFAEKJJHP / CFGDDKLPHOL`1 / HDOEMDBOEDB) — noise. The first real frame is the one below them; room-gameplay components keep their real names.

Learned **2026-08-24** on build `20250718.01` while reading a Disc Golf error.

A `Debug.LogError` from game code always produces this prefix, and **none of it is the failing code**:

```
DFFFAEKJJHP:AMALEBJJDFF(LogType, Object, String, Object[])   <- log sink
UnityEngine.Logger:Log / UnityEngine.Debug:LogError
HDOEMDBOEDB:APKHGLJHJLF<T>(T category, object msg, ctx)      <- static log impl
CFGDDKLPHOL`1:APKHGLJHJLF(object msg, Nullable<ctx>)         <- per-category logger
<the method that actually failed>                            <- START HERE
```

`CFGDDKLPHOL\`1` / `HDOEMDBOEDB` are **not** helpers that failed — they are `LogError` overloads
(7 and 9 of them respectively, all named `APKHGLJHJLF`). The message string is built by the caller,
so its literals live in the *caller*, which is how you find it: `names.py` the first non-facade
frame.

**Room gameplay components are NOT obfuscated** — `DiscGolfManager`, `DiscGolfDisc`, `GameManager`,
`GameTeamManager`, `Tool` all keep their names, while their *methods* and *fields* are scrambled.
So a gameplay trace is far more readable than an HTTP one; `msig.py` / `fields2025.py` on the named
component usually identifies the failure in one or two steps.

# De-obfuscating an ASYNC frame: read the state machine off `Start`'s methodSpec

Added **2026-10-29** on build `20260323.14`, from an `HTTP Error 404` trace that named only
obfuscated facades.

An HTTP trace is the hard case — every frame is `RecNet.LEMLPUGKWSA.LHAFODXTBPA`-shaped and there is
no literal or caller to anchor on. But **async methods in this build are 1:1 with a
compiler-generated nested state machine, and those names survive obfuscation.** So:

```bash
py slots2025.py <obfuscated_method_rva> 200        # find AsyncTaskMethodBuilder`1::Start
#   -> ...::Start  <generic inst class=3008 method=66628>
py ginst.py --method 66628
#   -> inst#66628: ['.<GetRecentRoomOfferPurchasesForRoom>d__19']
```

Two commands, no `callxref`, no literal, no `mxref`. It worked on both obfuscated frames of that
trace at once (`KQPMJKEWIZA.WQDTRTKHEPO` → `GetRecentPurchasedRoomOffersForRoom`,
`LEMLPUGKWSA.LHAFODXTBPA` → `GetRecentRoomOfferPurchasesForRoom`), which immediately named the
route family and the owning facades.

Bonus: the **`class=`** instantiation on the same `Start`/`SetResult` methodSpec is
`AsyncTaskMethodBuilder<T>` — i.e. **`T` is the method's return type**, so one `ginst.py <class>`
also gives you the deserialize target of an HTTP facade without touching the send call.

⚠️ **Bound the window.** `slots2025.py <rva> 0x300` on a small async stub crosses into the *next*
method and prints a second `Start` with a different `method=` — in that trace, `method=66625` =
`<CreateRoomOffer>d__14`, a neighbour. Take the **first** `Start` after the method's own entry, or
re-run with a tighter window.

Two more notes on reading these traces:

- **An async frame appears twice in a row.** `LHAFODXTBPA` / `WQDTRTKHEPO` / `Cache.Get[TResponse]`
  each print two adjacent identical lines; that is the await resumption, not recursion.
- **A `FormattedAsyncException` block is several traces concatenated**, innermost first, separated by
  blank lines, ending at `AsyncMethodBuilderCore+<>c.<ThrowAsync>b__7_0`. The *last* block before
  that is the one with the outermost (and usually unobfuscated, UI-level) frames — read it first to
  learn what the user action was, then walk back up the earlier blocks for the HTTP detail. The
  exception type and message are on the **timestamped `[Exception]` line inside the block**, under
  `. ## Message`, not at the top.

**Team ids:** `EFGGHFMBDFC` is the shared team enum — `TEAM_1 = 0` … `TEAM_40 = 39`, plus
`ANY = -1`, `MIN_VALUE = -1`, `MAX_VALUE = 39`. Colour names ("Red Team") are display strings
resolved from the index, not enum members — don't grep for them.
