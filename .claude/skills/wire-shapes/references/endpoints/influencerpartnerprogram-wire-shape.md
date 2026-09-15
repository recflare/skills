# Influencerpartnerprogram wire shape

> GET api/influencerpartnerprogram/myinfluencer and /influencer?accountId= (svc 28 Econ) both return a BARE JSON INTEGER — the supported influencer's account id, with 0 as the client-side sentinel for 'none'.

Derived **2026-08-24** from build `20250718.01` via [recflare-2025-metadata-carve](../../../il2cpp-analysis/references/recflare-2025-metadata-carve.md).
Whole facade is the static class `ONDILCNHMJD`, service **28 = Econ** (`mov r8d, 0x1c`,
[recnet-service-enum](../conventions/recnet-service-enum.md)), all **GET** (`HttpMethod` statics `+0x08`).

| route | literal | method | result |
|---|---|---|---|
| `/myinfluencer` | `0xD131160` | `BFNEKGBPEPD()` `0x7D00650` | `int?` |
| `/influencer?accountId={int}` | `0xD130A30` | `EAPJKBLGNMK(int)` `0x7D00E10` | `int?` |
| `/influencers` | `0xD130DC8` | `LEGLDPNOODH(string)` `0x7D01680` | `List<int>` |
| `/support` | `0xD131890` | `GOCFBHJMHEK(int)` `0x7D01130` | — |
| `/remove` | `0xD1314F8` | `KFJLKLKKPKP(int)` `0x7D013B0` | — |

## Both influencer lookups return a BARE JSON INTEGER

```
220
```

Not an object, not an envelope, no `{"Value":…}`. The send generic is
`MGPBDIAGCFD.CJBFDPLCIEJ<int>` — **T is `int` directly**.

**`0` is the sentinel for "not supporting anyone."** The continuation lambdas are literally
`x => x == 0 ? (int?)null : (int?)x`:
`<>c.HLPCNGGHJOH` `0x7D036C0` (myinfluencer) and `<>c.MJCLAFLPNLA` `0x7D03FC0` (influencer) both do
`test ebx, ebx ; jne` → `xor eax, eax` (returns `default(Nullable<int>)`, i.e. hasValue = false)
otherwise `new Nullable<int>(x)`. So **return `0`, never `null` and never an empty body** — 0 is the
representation the client is built to read.

`accountId` is added by the query-param adder `MGPBDIAGCFD.ELHKHFJEHLM` and boxed as I4 → plain
number on the URL. `/influencer` also gets a client-side cache window via
`MGPBDIAGCFD.DIDJOECFJII(TimeSpan, bool)` read from a static config (not a literal).

**`/myinfluencer` is gated client-side**: `PCGJFHLIGAC.MOFKKEIIDKC(0)` runs first and the call is
short-circuited with a rejected promise carrying `'Not Logged in'` — no HTTP request is made when
logged out. Error paths log `"Failed to get my supported influencer"` /
`"Failed to get supported influencer"`, and the error lambda `<>c.EKFAPGNENIK` `0x7D035C0` clears the
cached value.

**Not fully pinned:** `CJBFDPLCIEJ(bool, CancellationToken)` is a send-with-response variant distinct
from `HPBKMCLEANE(CancellationToken)`, called here with `false`; it matches the older build's
*SendWithNullableResponse* slot but I did not decompile it (shared generic, rgctx). Returning `0`
sidesteps the question entirely.
