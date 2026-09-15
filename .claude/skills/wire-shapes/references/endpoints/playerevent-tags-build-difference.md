# Playerevent tags build difference

> PlayerEvent.Tags differs between the two clients: recflare-2025 wants List<string>, recflare-client wants List<{Tag, Type}> objects. Sending strings to recflare-client throws HEBOAMGAJAG Malformed Response.

Found **2026-08-25** diagnosing a `HEBOAMGAJAG: Malformed Response` on a `POST api/playerevents/v2`
response that was byte-perfect for the *other* build. See [two-client-builds-name-check](../../../il2cpp-analysis/references/two-client-builds-name-check.md) — the
`HEBOAMGAJAG` name is what identifies the client as `recflare-client`.

**The one field that differs:**

| build | JWT `ver` | `PlayerEvent.Tags` |
|---|---|---|
| `recflare-client` (**older**) | `20230414` | `List<{Tag, Type}>` → `[{"Tag":"celebration","Type":0}]` |
| `recflare-2025` (**newer**) | `20250718.01` | `List<string>` → `["celebration"]` |

⚠️ **Direction matters and is counter-intuitive: the OLD client gets the richer object form; the NEW
one gets bare strings.** Rec Room simplified it. Branch as
`int(ver[:8]) <= 20230414 ? objects : strings`.

Sending the string form to `recflare-client` makes Utf8Json hit `"` where it expects `{`, the
deserialize throws, and the whole response is rejected — so a create looks like a total failure even
though 17 of the 18 keys were right.

Derived from `il2cpp-tools/out/DummyDll/RecNet.Runtime.dll` with Mono.Cecil
(`C:\Games\recflare\BepInEx\core\Mono.Cecil.dll`) — the binary for that build is gone, but the
DummyDll carries every type and field signature:

```
IMIJPHJKLIM                       17-field PlayerEvent base (== 2025's NEMBNIGCMFK)
  NCBAEFEDLMK : IMIJPHJKLIM       + List<ALGBCBHPICC> Tags     <- the PlayerEvent
  IFDNDCKHPBD : IMIJPHJKLIM       + {int, bool}                 (a second variant)
ALGBCBHPICC                       { string, IHJBBBIJIDH }       <- the tag object
GDCLLKJIJPJ                       { NCBAEFEDLMK, CJDHONMNJNA, HPMDKMBJDDE }  <- the response
HPMDKMBJDDE                       { OLCMHCHELAH Result, List<string> Tags }  <- TagModifyResult
```

**Wire keys are `Tag` and `Type`**, in that order. DummyDll has no IL so its formatter keys are
unreadable; they were taken from the *2025* build's equivalent tag DTO `EOPJHDOGHKN`
(`{string, EEHJEEHMEFC}`, formatter `LBOEDPPEOJI` `.ctor 0x772D820`, trailing run at `0x772DA0D`),
and both literals are present in the older build's string table. JSON keys are the server contract
and do not re-roll between builds; only names and RVAs do.

`Type` enum (identical on both builds): **`General 0`, `Auto 1`, `AGOnly 2`, `Banned 3`**.

⚠️ **`TagModifyResult.Tags` is `List<string>` on BOTH builds** — only `PlayerEvent.Tags` is the
object form. Do not "fix" both.

The `Result` enum (`CJDHONMNJNA` here, `CPIAPAGENIK` on 2025) is member-for-member identical.

**How to apply:** the two are incompatible, so branch on the JWT `ver` claim
([two-client-builds-name-check](../../../il2cpp-analysis/references/two-client-builds-name-check.md)) — objects for `20230414`, strings above it. **A Mono.Cecil pass over
`il2cpp-tools/out/DummyDll/` is the fastest way to answer any `recflare-client` shape question**
now that its GameAssembly.dll is gone.
