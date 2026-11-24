# Playerreporting v3 create wire shape

> POST api/PlayerReporting/v3/create (svc 2 API) returns a **bare** `RecNet.OkResponse` — a 2-key
> object `{"Success": bool, "Message": string}`. No envelope, no `Value`. The 2026 `{}`→null rule
> applies (object DTO), so the minimum valid body is one key — send both.

Derived **2026-11-11** from build `20260323.14` (il2cpp-2026 carve).

`POST https://api.<host>/api/PlayerReporting/v3/create` — path literal `0xFC3EF68`
(`api/PlayerReporting/v3/create`), referenced by exactly one method.

Client facade **`RecNet.PlayerReporting$$OSWBASYMGZI` `0x9532950`**:

```
static MPVTAJGPRUT<RecNet.OkResponse> OSWBASYMGZI(
    int a, .ReportCategory b, string c, float d, float? e, bool f, bool? g, bool h, bool i)
```

`MPVTAJGPRUT<T>` is the `RecRoom.Async` task wrapper, so the deserialize target is bare **`T =
RecNet.OkResponse`** ([2026-send-helper-tiers](../conventions/2026-send-helper-tiers.md): `Task<T>` =
bare DTO, not an envelope). The nine args are the report fields the client sends (reported player id,
`ReportCategory`, a message string, and the vote-kick/flag scalars); the request body was not fully
mapped field-by-field — the URL/verb/body are assembled in generic-shared async code that linear
disassembly desyncs on. Verb **POST** and service **2 (API)** follow the sibling pattern: every
`api/PlayerReporting/v1/*` route is POST svc 2, incl.
[moderationBlockDetails](playerreporting-moderationblockdetails-wire-shape.md).

## Response — BARE `OkResponse`, 2 keys

Formatter **`Utf8Json.Formatters.RecNet.PXYOGQEJKNX`** (`.ctor 0x964ee50`, `Serialize 0x964eca0`).
Type `RecNet.OkResponse` has exactly two auto-properties (via `ftypes`):
`<Success>k__BackingField` (bool), `<Message>k__BackingField` (string).

| # | wire key (serialized) | also accepted on read | CLR | nullable |
|---|---|---|---|---|
| 1 | `Success` | `success` | bool | no |
| 2 | `Message` | `message` | string | yes (may be `null`) |

The `____stringByteKeys` run emits **`Success` then `Message`** (PascalCase). No `[DataMember]`
rename — the only key spellings in the formatter ctor are the three Utf8Json casings of the two
property names. (`Msg`/`id` literals that trail the ctor window belong to the next method, not this
formatter.)

```json
{ "Success": true, "Message": null }
```

`Message` is free to be `null` or a human-readable string; the client reads `Success` to decide the
report outcome. Because this is an object DTO on 2026, a literal `{}` body deserializes to `null` and
throws `Malformed Response: '{}'`
([empty-json-object-deserializes-to-null](../conventions/empty-json-object-deserializes-to-null.md)) —
always emit at least the `Success` key.

## Sibling routes on `RecNet.PlayerReporting`

`v1/deviceId`, `v1/hile`, `v1/instantKick`, `v1/modKick`, `v1/moderationBlockDetails`, `v1/referee`,
`v1/roomModKick`, `v1/voteToKickReasons`, **`v3/create`**, `v3/voteToKick`.
