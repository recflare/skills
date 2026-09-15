# Oculus nonce absent steam build

> auth/oculus/nonce does not exist in recflare-2025 — it is the Steam/PC build (Steamworks only, no Oculus Platform SDK), so the Oculus nonce flow is unreachable and its shape is not derivable from this binary.

Checked **2026-08-20** on `C:\Games\recflare-2025` (build `20250718.01`) via
[recflare-2025-metadata-carve](../../../il2cpp-analysis/references/recflare-2025-metadata-carve.md).

**There is no `oculus/nonce` literal, and no path literal containing `oculus` at all.** The only
`nonce` strings in the whole literal table are HTTP-digest and crypto messages
(`nonce="{0}", `, `cnonce=`, `cannot reuse nonce for GCM encryption`, `The message nonce length is
incorrect.`). The standalone `'oculus'` literal is referenced only by
`SteamPlatformManager.BCBMBDLOGPH` as a platform-name string.

**Reason: this is the Steam/PC build.** `Recroom_Release_Data/Plugins/` contains only
`Steamworks.NET`; there is no Oculus Platform SDK, and no `ovr_User_GetUserProof` /
entitlement symbols (`OculusPlatformSettings` exists only as a settings-asset name). The Oculus
nonce/user-proof handshake lives in the Quest build, so **its shape cannot be derived from this
binary** — do not guess one.

Account/auth surface that *is* present (host `auth.` = service 1, `account*` largely service 2 API):
`privileges/me/restrictions`, `account/me`, `account/me/haspassword`, `account/me/changepassword`,
`account/me/createlogintoken`, `account/me/remoteauth`, `account/recoverpassword`, `account/search`,
`account/bulk`, `account/isactivecreator/me`, `account/{0}/bio`, `account/{0}/clubs`,
`accountprivacysettings/{0}`, `platformid/{0}`. Matchmaking has its own `player/login` and
`player/exclusivelogin` (service 4, not account auth).

**How to apply:** same class of answer as `POST api/playerevents/v1` — when a path is absent from the
literal table *and* has no composed form, the client cannot be calling it; check whether the feature
belongs to a different platform build before assuming the server is at fault.
