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

**Team ids:** `EFGGHFMBDFC` is the shared team enum — `TEAM_1 = 0` … `TEAM_40 = 39`, plus
`ANY = -1`, `MIN_VALUE = -1`, `MAX_VALUE = 39`. Colour names ("Red Team") are display strings
resolved from the index, not enum members — don't grep for them.
