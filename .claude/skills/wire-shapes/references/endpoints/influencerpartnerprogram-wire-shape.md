# Influencerpartnerprogram wire shape

> GET api/influencerpartnerprogram/myinfluencer and /influencer?accountId= (svc 28 Econ) both return a BARE JSON INTEGER — the supported influencer's account id, with 0 as the client-side sentinel for 'none'.

Derived **2026-08-24** from build `20250718.01` via [recflare-2025-metadata-carve](../../../il2cpp-analysis/references/recflare-2025-metadata-carve.md).
Whole facade is the static class `ONDILCNHMJD`, service **28 = Econ** (`mov r8d, 0x1c`,
[recnet-service-enum](../conventions/recnet-service-enum.md)), all **GET** (`HttpMethod` statics `+0x08`).

**The facade is exactly five routes** — re-checked 2026-09-25, those are every
`api/influencerpartnerprogram*` literal in the build, and there is **no bare
`api/influencerpartnerprogram/` prefix literal**, so nothing here is `String.Format`-built and the
list is complete (contrast `api/roomkeys/`, which does have a prefix and therefore hidden routes).

| route | verb | params | response T | method |
|---|---|---|---|---|
| `/myinfluencer` | GET | none | bare **`int`** | `BFNEKGBPEPD()` `0x7D00650` |
| `/influencer` | GET | `accountId` (query) | bare **`int`** | `EAPJKBLGNMK(int)` `0x7D00E10` |
| `/influencers` | GET | `take`, `continuationToken` (query) | **`.GLIFCHFMKMH`** object | `LEGLDPNOODH(string)` `0x7D01680` |
| `/support` | **POST** | `influencerAccountId` (form) | **`JFNAKFCGDAO`** valueless envelope | `GOCFBHJMHEK(int)` `0x7D01130` |
| `/remove` | **POST** | `influencerAccountId` (form) | **`JFNAKFCGDAO`** valueless envelope | `KFJLKLKKPKP(int)` `0x7D013B0` |

All five are service **28 = Econ** (`mov r8d, 0x1c`). Verbs read from the `HttpMethod` statics:
`[rcx+8]` = Get on the three reads (`0x7D00801`, `0x7D00F3D`, `0x7D017B3`), `[rcx+0x20]` = Post on
`/support` (`0x7D0126A`) and `/remove` (`0x7D014C5`).

⚠️ **`/support` and `/remove` are POST, so `influencerAccountId` is a form-urlencoded BODY field**,
not a query param ([elhkhfjehlm-verb-dependent-params](../conventions/elhkhfjehlm-verb-dependent-params.md)).

## `/influencers` — a paged object, not a bare array

An earlier version of this note recorded the result as `List<int>`. That is the **cached field type**
(`ONDILCNHMJD.MDKOCOPIOAG` is `KPIPLFECKNC<List<int>>`), not the wire type. The send generic inst is
**#14781 = `.GLIFCHFMKMH`**, a 2-field object; formatter `COGAIDFDMPE` `.ctor`, key run
`0x79ACBED` / `0x79ACC44`:

| # | key | CLR |
|---|---|---|
| 1 | `InfluencerIds` | `List<int>` |
| 2 | `ContinuationToken` | string |

```json
{ "InfluencerIds": [205, 220], "ContinuationToken": null }
```

Query params are `take` and `continuationToken`. Error literal: `'Failed to get all influencers'`.

## `/support` and `/remove` — valueless envelope

Both send `HPBKMCLEANE<T>` with generic inst **#2849 = `JFNAKFCGDAO`**:

```json
{ "Success": true, "Error": null, "error_id": null }
```

`Success: false` or a null body throws `LLCLDPPAGIJ`
([llcldppagij-envelope-failure-exception](../conventions/llcldppagij-envelope-failure-exception.md)). Error literals
`'Failed to support influencer'` / `'Failed to stop supporting influencer'`.

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

## `CJBFDPLCIEJ` resolved (2026-09-25)

An earlier version of this note left the helper unpinned. `MGPBDIAGCFD.CJBFDPLCIEJ<T>(request, bool)`
is the **nullable-response** send — confirmed from
[progressionevents-active](progressionevents-active-wire-shape.md), where the same helper is instantiated over
`Nullable<long>` and called with the bool **`true`**. Here it is called with the bool **`false`**
(`xor edx, edx` at `0x7D00FFB`).

The nullability lives in that flag and in `T`, **not in the body format**. `T` here is generic inst
**#42 = plain `int`**, so the formatter is Utf8Json's `Int32Formatter`, which has no `ReadIsNull`
path — a literal `null` body would throw `NKJABNHBPCA` "expected:'Number Token'"
([number-token-parsing-exception](../conventions/number-token-parsing-exception.md)), and an empty body throws `IONCMJIACFI`.

So the "return `0`, never `null`" rule above is now backed by the formatter type, not only by the
`x => x == 0 ? null : x` continuation lambdas.

Re-verified 2026-09-25 on `/influencer?accountId=`: svc **28** (`mov r8d, 0x1c` at `0x7D00F60`),
verb **GET** (`mov rdi, [rcx+8]` at `0x7D00F3D`), one `ELHKHFJEHLM("accountId", …)` at `0x7D00F9F`,
send `CJBFDPLCIEJ<int>` at `0x7D01000`.
