# Chat sendmessage wire shape

> POST thread/{threadId} (SendMessage, svc 9 Chat) returns {ChatMessage, ChatResult}; ChatMessage.Contents must be a JSON STRING {Type,Version,Data} with Data non-null or the client NREs on ChatMessage.MessageJson.

Derived **2026-08-24** from build `20250718.01` via [recflare-2025-metadata-carve](../../../il2cpp-analysis/references/recflare-2025-metadata-carve.md), diagnosing a
stackless NRE at `PNAHAINBHAH+JDNBOCGEHJE.NKJEOOFGBAD(FPCDJKBKEBO response)` (`0x7C9EF60`).

`POST thread/{threadId}` — **Chat** service ([recnet-service-enum](../conventions/recnet-service-enum.md)), `messageContents` param,
client entry `PNAHAINBHAH.DCJDOJEHBAO(long threadId, …)` `0x7CB66F0`, error literal
`'Failed to SendMessage'`. Send generic `HPBKMCLEANE<FPCDJKBKEBO>` — **bare, no envelope**.

**Response `FPCDJKBKEBO`** (formatter `DGNNCEHENHD` `.ctor 0x7647020`), 2 keys:
`ChatMessage` (object, 0x10) and **`ChatResult`** (enum `OOGFKCNGLBF`, 0x18).

**`RecNet.ChatMessage` has exactly 6 wire keys** (formatter `PDCPEBAEFCF` `.ctor 0x76590F0`) even
though the CLR type has 13 fields — the other 7 are client-side:
`ChatMessageId` long, `ChatThreadId` long, `SenderPlayerId` int, `TimeSent` DateTime,
`Contents` string, `ModerationState` enum `EHCPIALIFMN` (byte: Active 0, Junior_Pending 11,
Moderation_Pending 100, Moderation_Closed 101, Moderation_Banned 102, MarkedForDelete 255).

## The NRE: `Contents` is a nested JSON **string**, and `Data` must be non-null

`ChatMessage.MessageJson` (field `0x40`) is **not a wire key**. It is produced by the
post-deserialize hook `ChatMessage.CPOBHIECLEN` `0x7C9B1E0`, whose tail does:

```
rbx = this.Contents                              ; [rsi+0x30]
rax = JsonSerializer.Deserialize<MessageJson>(rbx) ; 0x7C9B4DA
if (rax == null)        -> log "Error parsing message!", MessageJson stays NULL
if (rax.Data == null)   -> same                    ; 0x7C9B4E9 tests [rax+0x18]
else this.MessageJson = rax                        ; 0x7C9B4F4
```

`MessageJson` (formatter `EHBOPHEFBLG` `.ctor 0x7647770`) = `Type` (enum `EDNOJBKNKKD`: Text 0,
PartyInvite 1, Photo 2, VoiceChatConnectionInfo 3), `Version` int, `Data` string.

The response handler then does, **only when `ChatResult == 0`**:
`response.ChatMessage` → throw if null (`0x7C9F025`) → `.MessageJson` → throw if null
(`0x7C9F036`) → reads `.Type`. `ChatResult == 3` logs the enum name; **any other value returns
silently**.

So a correct success response is:

```json
{ "ChatMessage": {
    "ChatMessageId": 1, "ChatThreadId": 42, "SenderPlayerId": 220,
    "TimeSent": "2026-08-24T12:00:00Z",
    "Contents": "{\"Type\":0,\"Version\":1,\"Data\":\"hello\"}",
    "ModerationState": 0 },
  "ChatResult": 0 }
```

`Contents` is an **escaped JSON string**, not a nested object, and its `Data` must be non-null —
a null `Data` leaves `MessageJson` null and produces the identical NRE with no other clue.
`FPCDJKBKEBO.CPOBHIECLEN` (`0x7C9CCA0`) only null-guards `ChatMessage` before calling into the
hook, so nothing else warns you.

`OOGFKCNGLBF` (ChatResult): Success 0, InvalidArguments 1, ThreadNotFound 2, MembershipNotFound 3,
PlayerAlreadyOnThread 4, CannotMessagePlayer 5, InvalidCharacters 6, RecentlyLeftThread 7,
ThreadTooLarge 8, InsufficientPermission 9, TooManyAffiliationThreads 10, UnderModeration 11,
MessageNotFound 12, InvalidThreadJoinType 13, PlayerBanned 14,
CannotMessagePlayerDueToLocalPrivacySetting 15, CannotMessagePlayerDueToRemotePrivacySetting 16,
SuccessWithPartialPlayersAddedToThreadDueToPrivacySetting 17,
CannotAddPlayersToThreadDueToPrivacySetting 18,
CannotConvertDirectMessageChatToGroupChatDueToPrivacySetting 19.

**Escape hatch while stubbing:** returning any `ChatResult` other than 0 or 3 makes the handler
return without touching `ChatMessage` at all.
