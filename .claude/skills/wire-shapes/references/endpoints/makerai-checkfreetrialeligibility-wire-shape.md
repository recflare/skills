# `GET api/makerai/checkfreetrialeligibility` wire shape (2026 build)

> `GET econ.<host>/api/makerai/checkfreetrialeligibility` (svc **28 Econ**) returns the
> **VALUELESS ENVELOPE ONLY** — `RecNet.RecNetResult` = `{Success, Error, error_id}`. No `Value`.
> ⚠️ A bare `false` throws `Malformed Response: 'false'`; so does `true`, `{}` is fine but means
> "eligible".
> ⚠️ **Cached for 1 hour** — one bad answer poisons the whole session. **Relaunch between
> server-side attempts.**

Derived **2026-10-13** from build `20260323.14`, from a live log that 404'd at `60.65s` and then,
once the route existed, answered `false` at `75.15s`:

```
Malformed Response: 'false'
  at Utf8Json.Formatters.RecNet.VTLMXGUPIAK.Deserialize
  at RecNet.BVIXCNIZYIX.DRECUPUEDKL
```

The formatter was **named directly in the trace** — `py msig.py VTLMXGUPIAK` gives
`Serialize(JsonWriter, RecNet.RecNetResult, …)`, which settles the shape in one call. See
[2026-send-helper-tiers](../conventions/2026-send-helper-tiers.md).

Route literal `'api/makerai/checkfreetrialeligibility'`, sites `0x94516C4` / `0x945176D`.
**GET** (`[HttpMethod statics + 0x08]` read at `0x9451751`), service **28 Econ**
(`mov r8d, 0x1c` at `0x9451774`).

Facade **`RecNet.BVIXCNIZYIX.DRECUPUEDKL(bool forceRefresh, ct) -> Task<RecNet.ZBIGKCZRHCL>`**
`0x9440A50` = **`CheckFreeTrialEligibility`** (from the builder's generic inst
**#66327 = `<CheckFreeTrialEligibility>d__46`**), state machine `0x9451630`.

## Response — the valueless envelope, 3 keys

`Task<ZBIGKCZRHCL>` is the tier where **the envelope *is* `T`** — so the body is the envelope
itself, with no `Value` member. Send generic inst **#3201 = `RecNet.RecNetResult`**.

| # | key | CLR |
|---|---|---|
| 1 | `Success` | bool |
| 2 | `Error` | string\|null |
| 3 | **`error_id`** | string\|null |

```json
{ "Success": true, "Error": null, "error_id": null }
```

⚠️ **`error_id` is lowercase with an underscore**, as everywhere else on this build. `ErrorId` is not
a string literal anywhere in the binary.

To deny eligibility, answer `{"Success": false, "Error": "Not eligible", "error_id": null}` — a
`Success: false` envelope is a *valid* response that the caller handles, not a malformed one.

⚠️ **This is not a boolean route.** The name reads like a predicate, but the client parses an object.
`false` / `true` / `0` / `1` all throw `Malformed Response`.

**Exact sibling:** [makerai-user-access](makerai-user-access-wire-shape.md) — same valueless-envelope shape. ⚠️ But note the
service differs: `makerai/user/access` is **svc 0 AI** while this one is **svc 28 Econ**, so they are
not necessarily on the same host. Read the service per route; the `makerai/` prefix does not imply
the AI service.

## ⚠️ 1-hour response cache

The request goes through `RGBOOBRDHEB.ORUUDATDRUN(TimeSpan, bool)` at `0x94517C0` with the TimeSpan
read from **`RecNet.Cache` statics `+0x18` = 1 hour** (`.cctor 0x9444C20`: `+0x00` 1 min, `+0x08`
5 min, `+0x10` 10 min, **`+0x18` 1 hour**, `+0x20` 24 h).

The `bool` second argument is the facade's own `forceRefresh` parameter (`movzx r8d, byte [rbx+0x20]`
at `0x94517B4`), so a caller *can* bypass the cache — but the boot path does not. **Relaunch the
client between server-side attempts rather than re-triggering the UI**, same discipline as
[club-home-me](club-home-me-wire-shape.md).

## Neighbours on `RecNet.BVIXCNIZYIX` (Maker AI / Roomie), not derived

`py msig.py BVIXCNIZYIX` — 64 methods. The ones that reach the network and their tiers:

| method | returns | tier |
|---|---|---|
| **`DRECUPUEDKL(bool, ct)`** | `Task<ZBIGKCZRHCL>` | valueless envelope — **this route** |
| `BIQSRUKAJTZ(bool, ct)` | `Task<ZBIGKCZRHCL>` | valueless envelope |
| `BBLSKGFLYJL(ct)` | `Task<ZBIGKCZRHCL>` | valueless envelope |
| `VUQKSXNCRYE(string, Guid, long, long, decimal, ct)` | `Task<ZBIGKCZRHCL>` | valueless envelope |
| `ITSULJHPPQX(bool, ct)` | `Task<AI.MakerAIBalancesDTO>` | **bare** |
| `ODPRZBRSIVE(ct)` | `Task<AI.MakerAIFreeTrialConfigDTO>` | **bare** |
| `NASOOMKVMEM(bool, ct)` | `Task<IAHBKPCLGPS<AI.RoomieEnergyDTO>>` | enveloped-with-value |
| `GCFHKMCNUPU(Guid, long, long, decimal, byte, ct)` | `Task<IAHBKPCLGPS<AI.RoomieEnergyDTO>>` | enveloped-with-value |

`ODPRZBRSIVE -> MakerAIFreeTrialConfigDTO` is the obvious partner of this route and is **not
derived** — expect it to be asked for next if the Maker AI free-trial UI is opened.
