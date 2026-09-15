# Image content signature bypass

> Mirrored rec.net images carry an unsatisfiable RSA content-signature; the failed check stalls the shared request pump and blocks ROOM LOAD, not just artwork. Bypass RVA for build 20250718.01.

Rec Room verifies an **RSA signature on every downloaded image**. A mirrored CDN serves the
archived asset *including* rec.net's original header, e.g.

```
GET https://img.recflare.net/tip.jpg?sig=p1     (the ?sig=p1 selects the signing key)
  -> 200, image/jpeg, valid JPEG (FF D8 FF DB)
  -> content-signature: key-id=KEY:RSA:p1.rec.net; data=<base64 RSA sig>
```

The client checks it against a public key compiled into the binary, fails, and throws
`MELLIJAOIBB: "Image signature verification failed"`. **This is unsatisfiable by construction** —
signing correctly needs Rec Room's private key — so on any archival/mirror server the check can
only ever be bypassed, never fixed server-side. Bytes being a valid image is irrelevant.

**The non-obvious part: it breaks ROOM LOAD, not just artwork.** Image fetches and the room
save-data blob share one request pump (`CBACIMLIBPF.KOMEOKGFOBP`, draining a `Queue`). The throw
stalls the pump, so every request queued behind it is never dispatched — it appears in the
`CBACIMLIBPF.IBJKIAMJCDN` hook but never reaches BestHTTP, mitmproxy, or the server access log.
Symptom: loading bar stuck on "Downloading", `room_load_state: DOWNLOADING_DETAILS`, then a 30s
timeout cancelling `FetchRoomLoadDetails > getRoomSaveData`, followed by `RaiseEvent(22) failed` /
`Unable to send message!` — all of which are teardown noise, not the cause. Photon is a red herring
here; it stays healthy (JoinGame returnCode=0) throughout.

Build `20250718.01` (dump `RecRoom_Info/Code/2025-07-19_02-45-25`), class `HPJKKCCECLH` in
`RecNet.Runtime.cs`:

| RVA | Member | Role |
|---|---|---|
| `0x7CF32F0` | `private static bool BLDFMLMAFLH(byte[] data, byte[] sig)` | **the verifier — hook to return true** |
| `0x7CF84E0` | `private static RSAParameters OGONMIPNEKK()` | baked-in public key |
| `0x7CF85F0` | `OIKINEOLHBL(string url, bool, ct)` | async; throws the exception |

Shipped in `C:\Games\recnet-plugin-unstable` (`VerifyImageSig_H`) — **CONFIRMED at runtime
2026-08-15**: images load and rooms are enterable. Names are obfuscated and rotate per build, so
re-derive by shape: the `bool(byte[], byte[])` static sitting adjacent to an `RSAParameters`-returning
static in the same class. See [recflare-2025-working-client](recflare-2025-working-client.md).

**Why:** cost me a long investigation chasing Photon, Luxon, `%2F` URL-encoding, and a supposed
never-sent request, because the actual exception was logged ~1s earlier under an unrelated-looking
message and the failing request simply went silent rather than erroring.

**How to apply:** when a request appears in the client-side hook but in NO transport log and NO
server access log, suspect a stalled shared request pump and look for a thrown exception in the
*preceding* second — not a broken URL. In Player.log, find the real error by walking the
inner-exception cascade to its top (`## Stack Trace` header); `TrySetCanceled` chains are fallout.
