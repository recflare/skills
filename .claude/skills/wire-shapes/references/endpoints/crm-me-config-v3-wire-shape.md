# `GET crm/me/config/v3` wire shape (2026 build only)

> `GET platformnotifications.<host>/crm/me/config/v3` (svc **17 PlatformNotifications**) is
> **ENVELOPED**: `{Value: <CrmAssignmentDTO>, Success, Error, error_id}`.
> `CrmAssignmentDTO` is only 2 keys — `UserConfig` and `BrazeConfig`.
> ⚠️ **`{}` throws `Malformed Response: '{}'`.** Serve the envelope, with `Value` either a real
> object or `null`.
> ⚠️ **2026 build `20260323.14` only.**

Derived **2026-10-13** from build `20260323.14`, after a live `Player.log` showed
`Malformed Response: '{}'` on this route. Found by reading the
`# Formatted Async Stack Trace` block, which named `RecRoom.Crm.CVXYJFBIQWL.QWOLGESYFLR` →
`RecNet.UQFHTYDUOCO.BHHMGTHOXDI` — see
[cv1-mappings-join-nre-2026](../../../rr-client-bringup/references/cv1-mappings-join-nre-2026.md) for that technique.

Service **17 = PlatformNotifications** (`mov r8d, 0x11` at `0x94B41F4`) — ⚠️ **not** Chat, API or a
"crm" subdomain, despite the path. Verb **GET** (`[HttpMethod statics + 0x08]` at `0x94B41D5`). Path
is the whole literal `crm/me/config/v3` (`0xFC98xxx` region), no params, no body.

Facade `RecNet.UQFHTYDUOCO.BHHMGTHOXDI()` `0x94B8110`, state machine
**`<GetCrmConfig>d__2$$MoveNext`** `0x94B40B0` (+0x330).

## The envelope

Send is `RGBOOBRDHEB::ZWUODKCINOA<T>` with generic inst
**#22913 = `RecNet.RecNetResultObject<RecNet.CrmAssignmentDTO>`**, and the state machine then calls
`RecNetResult\`1::get_Value` (class inst #1202 = `CrmAssignmentDTO`) — i.e. **the client unwraps
`Value` itself**, so the envelope is on the wire. `RecNet.ZBIGKCZRHCL` (the valueless envelope
interface) is also referenced, for the `Success` check.

Keys, in order, from the generated per-instantiation formatter (see
[2026-send-helper-tiers](../conventions/2026-send-helper-tiers.md)):

```json
{ "Value": { … }, "Success": true, "Error": null, "error_id": null }
```

⚠️ **`error_id` is lowercase with an underscore**, same as 2025 — the C# property is `ErrorId` but
there is a `[DataMember]` rename.

## `Value` — `RecNet.CrmAssignmentDTO`, 2 keys

Formatter `Utf8Json.Formatters.RecNet.DEVHDXJFPTK` `.ctor` **`0x9241A60`** (+0x230).

| # | key | CLR |
|---|---|---|
| 1 | `UserConfig` | `CrmUserDTO` |
| 2 | `BrazeConfig` | `BrazeConfigDTO` |

**`CrmUserDTO`** — formatter `HTLYWJBHYSO` `.ctor 0x9249340` (+0x2E0), 3 keys:

| # | key | CLR |
|---|---|---|
| 1 | `AssignedCrmType` | `RecNet.CrmType` (numeric enum) |
| 2 | `AssignedPushNotificationService` | **`PushNotificationServices?`** — nullable |
| 3 | `AllowPush` | bool |

**`BrazeConfigDTO`** — formatter `IJQUYRZOKON` `.ctor 0x8FF67B0` (+0x230), 2 keys: `AppId` (string),
`SdkEndpoint` (string).

### Enums (numeric — no member names in the string table)

`RecNet.CrmType : int` — `None 0`, `Braze 1`, `Rengage 2`.

`RecNet.PushNotificationServices : byte` — `APNS 0`, `Firebase 1`, `Mock 2`, `Braze 3`, `Rengage 4`.

## The right answer for a self-hosted server

There is no CRM, so assign none. `CrmType.None = 0` is exactly that:

```json
{ "Value": { "UserConfig": { "AssignedCrmType": 0,
                             "AssignedPushNotificationService": null,
                             "AllowPush": false },
             "BrazeConfig": null },
  "Success": true, "Error": null, "error_id": null }
```

`AssignedPushNotificationService` is the one nullable member, so `null` is legal there.
`BrazeConfig` is a reference type, so `null` is legal — and correct when `AssignedCrmType` is
`None`, since the Braze app id/endpoint would be meaningless.

⚠️ **`AllowPush` and `AssignedCrmType` are non-nullable** — a JSON `null` on either throws in the
formatter. Omit the key or send `false` / `0`.

### Why `{}` fails

`{}` is what the live server was returning, and the client threw `Malformed Response: '{}'`. The
envelope type is a class with a generated formatter, so an all-defaults parse *ought* to succeed —
**the exact throw condition was not pinned**, because `RGBOOBRDHEB.AIYNPFIEYFY<T>` and
`HBEADHYKUCU.MCHJISJGHLD<T>` are generic-shared and do not resolve to their own entries in
`methods.pkl`. The working hypothesis is that the helper rejects a null `Value` (or a
`Success == false`) with the same message. It does not change the fix: send the envelope above.

Compare [ioncmjiacfi-malformed-response](../conventions/ioncmjiacfi-malformed-response.md) — on 2025 that message means "`T` is
a list or scalar"; on 2026 an **empty** body gets its own distinct `Response was empty` exception, so
`Malformed Response` on this build is specifically "the body did not satisfy `T`".
