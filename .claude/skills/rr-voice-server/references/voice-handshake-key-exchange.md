# Voice handshake key exchange

> The full recflare-2025 voice (Tachyon/NGO) connection handshake and AES key exchange — JSON payloads PAFCNOLGBNM in / PMFAAFNFMAL out, gated on an RSA keypair whose PUBLIC half is hardcoded in the client.

Traced **2026-08-21** on `C:\Games\recflare-2025` (build `20250718.01`) via
[recflare-2025-metadata-carve](../../il2cpp-analysis/references/recflare-2025-metadata-carve.md). Follows [dissonance-voice-connection](dissonance-voice-connection.md).

The voice session wrapper is `BAOFAOBLAMJ` in `RecRoom.Networking.PhotonImpl.Runtime`; its own log
literals name it **`TachyonClient`**. It holds two `RSACryptoServiceProvider` fields (0x40, 0x48), an
`AesCryptoServiceProvider` (0x50) and a `byte[]` (0x58).

## 1. Client → server: NGO connection-request payload

`BAOFAOBLAMJ.HCNIOOINPCA` = **`TachyonClient.SetDedicatedServerConnectionRequestPayload`**
(`0x82786B0`). It calls `RSA.Encrypt` several times, `RSA.ExportCspBlob`, then
`JsonConvert.SerializeObject` and installs the result as the NGO connection payload. The type is
`PAFCNOLGBNM` — **explicit `[JsonProperty]` names, so these are literal wire keys**:

| key | member | type |
| --- | --- | --- |
| `AI` | `AccountId` | string |
| `AT` | `AccessToken` | byte[] |
| `VB` | `VerificationBlob` | byte[] |
| `CKA` | `ClientKeyA` | byte[] |
| `CIA` | `ClientIVA` | byte[] |
| `CPK` | `ClientPublicKey` | byte[] (RSA CspBlob) |

All six are `Required.Always`. Newtonsoft serialises `byte[]` as base64.

## 2. Server → client: approval payload

Handled by `BAOFAOBLAMJ.CDJMICBEALM` = `NetworkManager_OnClientConnectedCallback` (`0x8277880`):
`JsonConvert.DeserializeObject<PMFAAFNFMAL>` → compare `Reason` to the literal **`"Carrot"`** →
`RSA.Decrypt(SessionKeyB)` → byte-wise combine with the client's own key material →
`LiteNetLibTransport.RecRoom_SetEncryptionInfo(ulong clientId, byte[] key)`.

| key | member | type | note |
| --- | --- | --- | --- |
| `DR` | `Reason` | string | `Required.Always`; **must be `"Carrot"`** |
| `KT` | `SessionKeyB` | byte[] | `Required.Default`; RSA-encrypted with the client's `CPK` |

So it is a **split-key scheme**: the client contributes `CKA`/`CIA`, the server contributes
`SessionKeyB`, and the transport key is derived from both.

## 3. The blocker: the server's RSA private key

`DMIBBCKIGCG` (`.cctor` `0x827A820`) holds three hardcoded constants:

- AES-256 key `QJwT58FheuEIXNlbnvEGlcC6n7Ury+BYFid4LNWLEJ4=`
- AES IV `GTLFaIAoniLKqHEJFIhcGw==`
- a **1024-bit RSA public key** (`<RSAKeyValue><Modulus>z7L4+nePWLb3f4OzskH39KyiuP1vilcqf3KN6WekBNOo0g7gBHNmt14Yh09rkyex4lHBM7DTEJOOjqlTloUBpIlt3wK4OUsY0k5M34Xtk7kS7QDglhyDk9cREKIpOcek7rQg/nEI5Vd3Xhx5K7YlYBUNsXmVMFEvcwwuWPUhbhE=</Modulus><Exponent>AQAB</Exponent></RSAKeyValue>`)

The client encrypts `AT`/`VB`/`CKA`/`CIA` **to that public key**, so a working voice server needs the
matching **private** key — which is Rec Room's and is not in the client. Practical route for a
self-hosted server: **patch the embedded modulus** to a keypair you control (the string is a plain
literal in `.data`), rather than trying to recover the original.

**How to apply:** the client's own offline path accepts `VoiceConnectionInfo = ""`; a dummy IP gets
as far as `FailedToConnectToVoice` / `COADIPLNFKJ: Client has already disconnected`, which is the
signal that address parsing and the connect attempt both worked.

## Exact field mapping of the client payload (derived 2026-08-24)

`TachyonClient.SetDedicatedServerConnectionRequestPayload` = `BAOFAOBLAMJ.HCNIOOINPCA` `0x82786B0`
builds `PAFCNOLGBNM` (6 fields) and `JsonConvert.SerializeObject`s it. Field order matches the
observed wire order:

| key | field | contents |
|---|---|---|
| `AI` | `GIMCDKIBOHE` string | a string pulled from Photon `AuthenticationValues.AuthPostData` |
| `AT` | `MAPJPBCKOCK` byte[] | **AES(UTF8(Photon auth token))** — symmetric, *not* RSA |
| `VB` | `IILCOGEICME` byte[] | `RSA_RR(base64decode("GTLFaIAoniLKqHEJFIhcGw=="))` — a fixed 16-byte secret |
| `CKA` | `MKPKGPAJGHA` byte[] | `RSA_RR(aes.Key)` |
| `CIA` | `CJPDMNPHBMB` byte[] | `RSA_RR(aes.IV)` |
| `CPK` | `IFMNNHCFJDO` byte[] | **AES(**`RSA.ExportCspBlob(clientKeypair, false)`**)** — also AES-wrapped, not plaintext |

`RSA_RR` = the client's `RSACryptoServiceProvider` loaded with the **hardcoded Rec Room public key**
in `DMIBBCKIGCG..cctor` `0x827A820`:

```
<RSAKeyValue><Modulus>z7L4+nePWLb3f4OzskH39KyiuP1vilcqf3KN6WekBNOo0g7gBHNmt14Yh09rkyex4lHBM7DT
EJOOjqlTloUBpIlt3wK4OUsY0k5M34Xtk7kS7QDglhyDk9cREKIpOcek7rQg/nEI5Vd3Xhx5K7YlYBUNsXmVMFEvcwwuWPUh
bhE=</Modulus><Exponent>AQAB</Exponent></RSAKeyValue>
```

Same cctor also holds `"QJwT58FheuEIXNlbnvEGlcC6n7Ury+BYFid4LNWLEJ4="` (32 B) and
`"GTLFaIAoniLKqHEJFIhcGw=="` (16 B, the `VB` payload).

**The AES key/IV are NOT hardcoded.** `DMIBBCKIGCG.EAIDKGJNAPP` `0x827A6D0` calls `GenerateKey()`
then `GenerateIV()` on the shared `AesCryptoServiceProvider` on every call, so each connection uses
a fresh AES-256-CBC/PKCS7 key+IV — which is exactly why they have to travel as `CKA`/`CIA`.

**So `AT` is only readable with Rec Room's RSA private key.** Three ways round it, in order of ease:
1. **You already know the plaintext** — it is whatever your own auth service put in the client's
   Photon `AuthPostData`. Nothing needs decrypting.
2. **Patch the modulus** in `DMIBBCKIGCG..cctor` to your own keypair; then `CKA`/`CIA` decrypt and
   `AT`/`CPK` follow.
3. **Ignore it** — per [ngo-fork-batch-and-approval](ngo-fork-batch-and-approval.md) the server never has to validate any of this.

`AuthPostData` is read as either `byte[]` or `string`; anything else throws
`"Photon AuthPostData has unexpected type!"` (`0x8278C5D`).
