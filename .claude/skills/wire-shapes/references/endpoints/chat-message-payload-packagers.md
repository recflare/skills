# Chat message payload packagers

> The ChatMessage.Contents {Type,Version,Data} packager registry — only 4 packagers exist (Text v1, Text v2, PartyInvite v1, Photo v1); there is NO PlayerJoined/system message type, so a join line must be a Text message. Text v2 Data is a <=> / <-> token stream.

Derived **2026-09-09** from build `20250718.01` via [recflare-2025-metadata-carve](../../../il2cpp-analysis/references/recflare-2025-metadata-carve.md).
Extends [chat-sendmessage-wire-shape](chat-sendmessage-wire-shape.md) (which established that `ChatMessage.Contents` is an
**escaped JSON string** `{Type, Version, Data}` with `Data` non-null).

## `MessageJson` and the type enum

`.MessageJson` (formatter `EHBOPHEFBLG` `.ctor 0x7647770`) = `Type` (`EDNOJBKNKKD`), `Version` (int),
`Data` (string). **`.EDNOJBKNKKD : int` has exactly four members** — `Text 0`, `PartyInvite 1`,
`Photo 2`, `VoiceChatConnectionInfo 3`.

## The packager registry

`MOJCAIGCBGC.BPNJMIEMGCK(MessageJson, bool)` **`0x803EC90`** unpacks a message by looking up
`MOJCAIGCBGC.NCCKGGLACOH(int version, EDNOJBKNKKD type)` `0x803F7C0`.

Packager interface `.CBHBCILGKPC`: `ABOGEKBDALP() -> int` **Version**,
`DJNDAKOFMMJ() -> EDNOJBKNKKD` **Type**, `FGCCKLLPBMM(details)` pack, `BPNJMIEMGCK(MessageJson, bool)`
unpack. Concrete implementors, all deriving `OEPPGJEODLM\`1<TDetails>`:

| packager | Type | Version | details type |
|---|---|---|---|
| `.HFAGDNBKGCP` | Text 0 | **1** | `RecRoom.Chat.Runtime.TextMessageDetails` |
| `.BHGIEPAFNCB` | Text 0 | **2** | `RecRoom.Chat.Runtime.TextMessageDetails` |
| `.LEBAAGCKMEM` | PartyInvite 1 | 1 | `RecRoom.Chat.Runtime.PartyInviteMessageDetails` |
| `.FHOMAKIPFAI` | Photo 2 | 1 | `RecRoom.Chat.Runtime.PhotoMessageDetails` |

(Type/Version read from the constant-returning stubs `0xA60530`→0, `0xC20970`→1, `0xCE95F0`→2.)
**`VoiceChatConnectionInfo (3)` has no packager** — it never goes through chat rendering.

`RecRoom.Chat.Runtime` is an **unobfuscated namespace**; only those three `*MessageDetails` types
exist in it, and all three derive `.JIDGCBBKDKE` (the details base).

## ⚠️ There is NO "player joined" / system message payload

Nothing in the enum, the registry, or `RecRoom.Chat.Runtime` represents a membership/system event.
A "X joined the chat" line must be sent as a **Text** message.

An unknown `(Type, Version)` pair does **not** throw: the lookup misses, the client logs
`"No packager registered for the supplied message type ({0}) and version({1})."` and falls back to
constructing a plain `TextMessageDetails` (`0x803EE6B`). So invented types degrade to text rather
than breaking the thread — but they render as whatever raw `Data` happens to be.

## Text v1 vs v2 — this decides what `Data` may contain

- **Version 1** (`HFAGDNBKGCP`): `BPNJMIEMGCK` returns `TextMessageDetails` directly, no token
  parsing. **`Data` is the literal message text.** Use this for a join line.
- **Version 2** (`BHGIEPAFNCB.CGNJIHHNLEG` `0x803AAF0`): `Data` is a **token stream** — split on
  **`<=>`** into tokens, each token split on **`<->`** into parts (`String.IndexOf`/`Substring`
  chain at `0x803ABE5`–`0x803ACC7`). Malformed input logs
  `"Unable to parse chat token! '…'"` / `"Incompatible chat token encountered! '…'"`.
  This is the rich/mention form (`TextMessageDetails` carries
  `FHLIAIDPCMK<IHBCHLIONIM>` tokens + a `HashSet<PGHFNAPOFJB>`).

**How to apply** — safest join line:

```json
"Contents": "{\"Type\":0,\"Version\":1,\"Data\":\"Devin joined the chat\"}"
```

Remember `Contents` is a **string** containing that JSON, and the nested message must also satisfy
[chat-sendmessage-wire-shape](chat-sendmessage-wire-shape.md): `Data` non-null, timestamp key is **`TimeSent`**.

**Not established:** whether the client synthesises any join/leave line of its own from
`ChatThread.PlayerIds` changes ([chat-thread-party-wire-shape](chat-thread-party-wire-shape.md)). No join-related literal exists in
the chat code, so if such a line is wanted it has to come from the server as a Text message.
