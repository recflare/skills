# Voice RSA key swap

> How to swap the hardcoded Tachyon RSA public key for your own so the server can decrypt CKA/CIA and read AT — single static-field write at BAOFAOBLAMJ..ctor 0x82795E0, plus the decrypt recipe and a free self-test via VB.

Derived **2026-08-25** on build `20250718.01`, to make the voice server able to authenticate clients
([voice-instance-routing](voice-instance-routing.md), [voice-handshake-key-exchange](voice-handshake-key-exchange.md)).

## The single point where the key enters

`BAOFAOBLAMJ..ctor` (`0x82795E0`, len `0x1C0`) — TachyonClient's constructor:

```
0x82796A3  new RSACryptoServiceProvider()      -> rdi
0x82796AC  this.KODJDHFMKAC (+0x40) = rdi      ; the "encrypt to Rec Room" RSA
0x827970B  rax = TypeInfo(DMIBBCKIGCG)
0x8279718  rdx = [rax+0x90]                    ; DMIBBCKIGCG statics
0x8279726  rdx = [rdx+8]                       ; KBANIKNNKKD  <- the RSA XML string
0x827972A  call [r9+0x200]                     ; rdi.FromXmlString(rdx)   (VIRTUAL)
```

The XML literal (`0xD106B70`, **243 chars**) is referenced **only** by `DMIBBCKIGCG..cctor`
(`0x827A820`) which stores it to statics+8. Nothing else in the binary uses it.

⚠️ `callxref` finds **zero** callers for `DMIBBCKIGCG.NDEDJKDIGGM()`/`CKAAEJMIMEF()` — the getters
are dead; the ctor reads the static field directly and `FromXmlString` is a virtual call. Don't hook
the getters.

## Preferred patch: one runtime static-field write (no code patching)

Set `DMIBBCKIGCG.KBANIKNNKKD` (statics **+0x8**) to your own `<RSAKeyValue>` XML **before the first
TachyonClient is constructed**. The ctor re-reads the field every time, so nothing else is needed —
no metadata edit, no inline hook, and **no key-size constraint** (2048-bit is fine; the client just
encrypts, and `CKA`/`CIA`/`VB` simply become 256 bytes).

Force the cctor first (touch the class), then write the field.

*Alternative — metadata patch:* the literal is 243 chars, and **any** 1024-bit key with exponent
65537 produces exactly 243 chars (`22 + 172 + 20 + 4 + 25`), so a byte-for-byte in-place swap works
with no stringLiteral table edit. Only do this if a runtime write isn't available — a mismatched
`global-metadata.dat` is what broke BepInEx before ([bepinex-crashes-new-build](../../rr-client-bringup/references/bepinex-crashes-new-build.md)).

## Server-side decrypt recipe

`RSACryptoServiceProvider.Encrypt(data, fOAEP: false)` at all three call sites (`r8d = 0`), so it is
**PKCS#1 v1.5**, not OAEP. The AES is `AesCryptoServiceProvider` defaults = **AES-256-CBC, PKCS7**.

1. RSA-decrypt `CKA` → 32-byte AES key; `CIA` → 16-byte IV.
2. AES-256-CBC/PKCS7 decrypt `AT` → UTF-8 `{"accountId":"…","environment":"…","accessToken":"…"}`.
3. Validate `accessToken` against your auth service; check its `accountId` equals the plaintext `AI`
   (that binds the otherwise-unauthenticated `AI`).
4. `CPK` decrypts the same way → the client's RSA public-key CspBlob, if you want it.

## Free self-test that the swap took effect

`VB` = `RSA(base64decode("GTLFaIAoniLKqHEJFIhcGw=="))`, a fixed 16-byte constant. After patching it
must decrypt to exactly:

```
19 32 c5 68 80 28 9e 22 ca a8 71 09 14 88 5c 1b
```

If `VB` decrypts to those bytes, the client is using your key — checkable before you trust anything
in `AT`. (The sibling constant `"QJwT58FheuEIXNlbnvEGlcC6n7Ury+BYFid4LNWLEJ4="`, 32 bytes, is not
used in this path.)
