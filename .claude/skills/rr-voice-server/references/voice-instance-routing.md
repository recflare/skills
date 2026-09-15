# Voice instance routing

> The Tachyon voice connect payload carries NO room/instance id — only AI (account id, plaintext). Route voice by mapping account->instance at VoiceConnectionInfo issuance, or by giving each instance its own endpoint.

Established **2026-08-24** on build `20250718.01`, answering "can the voice server work out the room
instance from the wire?" — the concrete problem being a Tachyon server that broadcasts voice to every
connected client. Builds on [voice-handshake-key-exchange](voice-handshake-key-exchange.md).

**Answer: no. There is no room, instance, or chat-thread identifier anywhere in the connect payload.**
The six fields are exhaustively: `AI` account id, `AT` AES(auth JSON), `VB` fixed constant,
`CKA`/`CIA` AES key+IV RSA-wrapped, `CPK` client public key. Nothing else is sent at connect time —
the JSON *is* the NGO `ConnectionRequestMessage.ConnectionData`.

**The only readable identity is `AI` = the local account id as a decimal string.** Built in
`AJKGMOJALID.IFGCALLLPMN` `0xFDAF90` from `PHCHGFEEEMG.EBADLLKHNNM` (the ObscuredInt account id) via
`Int32.ToString()` — the same value Dissonance uses for its roster
([voice-roster-account-id](voice-roster-account-id.md)), so the two agree. `AT` is AES over
`{"accountId":"…","environment":"…","accessToken":"…"}` (literals at `0xFDB01B`/`0xFDB2C4`/`0xFDB354`,
warning `"No RecNet Access Token to write!"`).

**Only one `VoiceConnectionInfo` field reaches the server at all** — `IFGCALLLPMN` reads exactly one
field off its arg, `[connInfo+0x30]` = `DFDLLAPJKLK.AAOPFKJNMMA`, and it lands inside the
**encrypted** `AT`. So you cannot smuggle a routing key through the connection info without first
patching the RSA modulus.

## Two workable routings

1. **Map account → instance at issuance (no client change, no crypto).** The client can only reach
   the voice server because the *server* issued it a `VoiceConnectionInfo` from
   `POST voiceconnection/{chatThreadId}` ([dissonance-voice-connection](dissonance-voice-connection.md)) after
   `GET player/connection-info?roomInstanceId=` ([player-connection-info-wire-shape](../../wire-shapes/references/endpoints/player-connection-info-wire-shape.md)). At that
   moment the server knows account → room instance. Record it and look it up by `AI` on connect.
2. **Give each instance its own endpoint.** `VoiceConnectionInfo.Address` is server-minted, so a
   per-instance port (or per-instance voice server) makes routing implicit — nothing on the wire
   needs parsing. Most robust; survives any client change.

**`AI` is client-asserted and unauthenticated** — a plaintext string the client chose. If a client
must not be able to claim another account's instance, bind option 1 with a server-issued nonce, or
use option 2.

## Checked: the per-instance Photon token does NOT reach Tachyon

Worth ruling out explicitly, because it looks promising. `player/connection-info?roomInstanceId=`
does mint a per-instance `PhotonAuthToken` ([player-connection-info-wire-shape](../../wire-shapes/references/endpoints/player-connection-info-wire-shape.md)), and
`AJKGMOJALID.IFGCALLLPMN` *does* consume it — at its very end
(`0xFDB543`: `rdx = connInfo.[+0x30]` → virtual setter at vtable `+0x1B0`, i.e. Photon's
`AuthenticationValues.Token`). **But that property is never read into the Tachyon payload.** The
payload builder touches only slot 0 (`GLIJIEDEIIP` → `AI`) and slot 1 (`NOMCPEFNGIE` → `AT`) of the
`MJDGNHEBAAP` interface, and that interface declares exactly those two members. The Photon token
goes to **Photon realtime**, not to the voice server.

The three fields inside `AT` resolve as:

| field | source |
|---|---|
| `accountId` | `PHCHGFEEEMG.EBADLLKHNNM` → `Int32.ToString()` — the local account id |
| `environment` | `CBACIMLIBPF.HBOAMJDJLFI` / `IJPPCICMAIL` (the HTTP client config; compared against `'localhost'`) |
| `accessToken` | `PCGJFHLIGAC.NAAJNOKIHMD()` — **the RecNet access token**, not a Photon one (failure literal `"No RecNet Access Token to write!"`) |

**The one lever this does give you:** `accessToken` is a token *your* auth service mints, so you
could encode the room instance in it — no client patch needed. It is still inside the AES envelope,
so it only becomes readable if you have already patched the RSA modulus. If you are patching anyway,
this is a clean channel; if not, stick to the two routings above.
