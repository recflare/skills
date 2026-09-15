# Chat thread party wire shape

> POST thread/party (svc 9 Chat, CreatePartyChat) takes NO params and returns a bare {ChatThread, ChatResult}; ChatThread is the 10-key DIEEJDGCEDB whose Messages/LatestMessage are full RecNet.ChatMessage objects, each re-validated by the ChatMessage hook.

Derived **2026-08-26** from build `20250718.01` via [recflare-2025-metadata-carve](../../../il2cpp-analysis/references/recflare-2025-metadata-carve.md).
Sibling of [chat-sendmessage-wire-shape](chat-sendmessage-wire-shape.md) - same `{X, ChatResult}` response family.

`POST thread/party` — **POST** (`HttpMethod` statics `+0x20`), service **9 Chat**. Client entry
`PNAHAINBHAH.CIFJOHHMAAL(string)` `0x7CB5DF0`, error literal `'Failed to CreatePartyChat'`.
Send `HPBKMCLEANE<AKKNLNOHPEO>` — **required response**, bare, no envelope.
**No query params and no body** (zero `ELHKHFJEHLM`/`ELKIBCPINAP` calls; builder ctor goes straight
to the send).

The same path also serves **GET** `thread/party` via `PNAHAINBHAH.GPEEICLEBBF(bool)` `0x7CB8480`
(`'Failed to GetPartyChat'`, query params `maxCount` + `mode`), which returns `DIEEJDGCEDB` directly
- i.e. the GET returns the bare thread, the POST returns the thread wrapped with `ChatResult`.

## Response `AKKNLNOHPEO` - 2 keys (formatter `OMDPHIFMGKB` `.ctor 0x7657610`)

`ChatThread` (`DIEEJDGCEDB`, 0x10) and `ChatResult` (`OOGFKCNGLBF`, 0x18) - the same ChatResult enum
as SendMessage (`Success 0`, `InvalidArguments 1`, `ThreadNotFound 2`, ... 20 members).

## `DIEEJDGCEDB` - 10 keys (formatter `HBKCDPNJGCD` `.ctor 0x764B180`)

| key | offset | type |
|---|---|---|
| `ChatThreadId` | 0x10 | long |
| `ChatThreadType` | 0x18 | enum `HMPLEAAOIBA`: **`Player 0`, `Club 1`, `Party 2`** |
| `LastReadMessageId` | 0x20 | long |
| `Messages` | 0x28 | `List<RecNet.ChatMessage>` |
| `LatestMessage` | 0x30 | `RecNet.ChatMessage` |
| `PlayerIds` | 0x38 | `List<int>` |
| `ChatThreadName` | 0x50 | string |
| `SnoozedUntil` | 0x58 | `DateTime?` |
| `IsFavorited` | 0x68 | bool |
| `ClubId` | 0x70 | `long?` |

13 declared fields -> 10 keys: `0x40` (bool) and `0x48` (long) are `[IgnoreDataMember]`, and `0x80`
is a plain field (not an auto-property) so it never serializes.

## Trap: nested ChatMessages are re-validated

`DIEEJDGCEDB.CPOBHIECLEN` walks `Messages` and calls **`RecNet.ChatMessage.CPOBHIECLEN`
`0x7C9B1E0` on each**, and does the same for `LatestMessage`. So every embedded message must satisfy
[chat-sendmessage-wire-shape](chat-sendmessage-wire-shape.md): `Contents` is an **escaped JSON string** `{Type,Version,Data}` with
`Data` non-null, and `TimeSent` (not `SentTime`) is the timestamp key. A null element inside
`Messages` hits an unguarded deref. Safest create response: `"Messages": []`, `"LatestMessage": null`.

The hook also branches on `ChatThreadType == 2 (Party)` into `DIEEJDGCEDB.KPABPNAMOIF` `0x7C9C070`,
so a party thread must actually be typed `2`. No string literals in the hook = no
"field is required" message; failures surface as a bare NullReferenceException.
