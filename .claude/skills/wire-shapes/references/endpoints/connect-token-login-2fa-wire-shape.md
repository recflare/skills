# `POST connect/token` — login, 2FA / TOTP and device-code flow

> The client's login endpoint is a standard IdentityServer-style **`POST connect/token`** on the
> **Auth** service. The entire 2FA / security-code challenge is **server-driven**: the client never
> validates a code locally. The server opts into a challenge by returning an OAuth-style
> `{"error":"<code>"}` body; the client shows the matching screen and re-POSTs with the extra field.
> A plain token response skips all of it.

Derived **2026-11-09** on `C:\Games\recflare-2026`, build **20260323.14**. RVAs are 2026-specific.
Service enum per [recnet-service-enum](../conventions/recnet-service-enum.md): **Auth = 1** (picks the
auth subdomain). This is NOT built through the usual `AKJEAMCCEOH..ctor` request path — it has its own
state machine, so verb/service are not read from an `HttpMethod` static here; it is a form-urlencoded
POST by construction.

## Request — `<ConstructLoginRequest>d__91$$MoveNext` `0x9504A30`

Route literal `'connect/token'` `0xFD87E50`. Base form fields (always sent):
`client_id` (`"recroom"`), `client_secret` (`"VxZ53kgbbEaRoZAeMe00MagtgD12GLL2"` — baked in the
binary), `grant_type`, `device_id`, `platform_id`, `cid`, `asid`, `time`, `build_key`, `ver`,
`platform`, `device_class`, `locale`, `isInitialLogin`.

The credential/challenge fields are added by `RecNet.Login$$HVQCCSJLKST` `0x94DE560`
(caller `RecNetLoginAccess$$IQFJKAIXDYF` `0x94E57A0`):

| form field | when present | meaning |
|---|---|---|
| `username` | password grant | login id |
| `password` | password grant | the password |
| `require_password` | `"true"` | client insists on a password grant |
| `login_context` | always on this path | opaque context token echoed back across the challenge round-trips |
| `security_code` | retry after `security_code required` | the emailed code |
| `2fa_code` | retry after `continue_2fa` | the 6-digit TOTP from the authenticator app |

A separate grant also exists: the device-code grant
(`urn:ietf:params:oauth:grant-type:device_code`), and a login-token grant (`login_token` +
`account_id`, used by the password-change path `IQFJKAIXDYF`).

## Response — OAuth JSON (bare, not a RecNet envelope)

Parsed by `<HandleLoginResponse>d__99$$MoveNext` `0x9509590`. Success keys (standard OAuth, C#
property names shown capitalised, wire is lowercase): `access_token`, `refresh_token`, `expires_in`,
`token_type`, `scope`, and for the device flow `device_code`, `user_code`, `verification_uri`,
`verification_uri_complete`, `interval`. Failure is `{"error":"<code>", "error_description":"..."}`.

**The `error` vocabulary the client branches on** (all literals live in `d__99`):

| `error` value | client reaction |
|---|---|
| `continue_2fa` | advance to the authenticator step → show `LoginSecurityCodeScreen`, collect `2fa_code`, re-POST |
| `invalid 2fa_code` | toast **"Incorrect 2FA code entered"**, re-prompt on the same screen |
| `security_code required` | prompt for the emailed security code, re-POST with `security_code` |
| `invalid security_code` | wrong email code, re-prompt |
| `hcr` / `hcr required` | human-challenge (captcha) required |
| `authorization_pending` / `slow_down` | device-code polling: keep polling / back off by `interval` |

Any other / absent `error` with a token body = success.

## Screens (title-screen login flow)

| element | RVA | role |
|---|---|---|
| screen id `LoginSecurityCodeScreen` | literal `0xFD51528` | the code-entry screen |
| `ManualLoginSecurityCodeButtonImpl$$OnButtonClicked` | `0x29A9130` | submit button |
| `TitleScreenFlowModel$$ManuallyLoginSecurityCode` | `0x29B6BE0` | enter the screen |
| `TitleScreenFlowModel$$CompleteLoginSecurityCodeScreen` | `0x29B5090` | on success |
| `TitleScreenFlowModel$$GoBackFromLoginSecurityCodeScreen` | `0x29B5940` | cancel / back |
| `<RunManualLoginState>d__128$$MoveNext` | `0x11310A0` | login state machine; holds **"Enter the {0} digit code from your authenticator app"** `0xFD2EBA0` and **"Incorrect 2FA code entered"** `0xFC0F580` |

The `{0}` in the prompt is a digit count, so the authenticator-code length is server/config-driven,
not hard-coded to 6 in the UI string.

## Persisted client state

`ClientSecurityState.Totp` `0xFD3A710` and `ClientSecurityState.KeyHash` `0xFD3A3C0` are cached by
`<LoginAsync>d__88` `0x950A470`, `<ExclusiveLoginAsync>d__89` `0x9505C30` and reused by
`<RunHeartbeatAsync>d__172` `0x950C8C0` — the remember-this-device material so a passed challenge is
not re-issued every launch.

## What this means for a self-hosted server

The challenge is entirely the server's decision. A recflare `connect/token` that returns a normal
token never triggers any 2FA screen. To exercise the flow, reply to the first POST with
`{"error":"continue_2fa"}` (or `"security_code required"`), then accept the client's retry carrying
`2fa_code` / `security_code` and issue the token. The client enforces nothing locally, so the server
owns code generation, delivery and verification. Treat 2FA as an opt-in capability, not a boot
requirement.
