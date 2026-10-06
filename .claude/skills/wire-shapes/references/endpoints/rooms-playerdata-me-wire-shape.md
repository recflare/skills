# Rooms playerdata/me wire shape

> GET rooms/{roomId}/playerdata/me (svc 16 Rooms) takes NO params and returns a BARE single-key object {"Data": "<string>"} — an opaque string blob, not nested JSON. The PUT on the same path is ENVELOPED, because it is the one that carries a friendlyActionDescription.

Derived **2026-10-01** from build `20250718.01`.
The bare-vs-enveloped split here is the cleanest example of the rule in
[rooms-isbanned](rooms-isbanned-wire-shape.md): **one path, two verbs, two different response tiers**, decided by which
helper the entry method calls.

`GET https://rooms.<host>/rooms/{roomId}/playerdata/me` — service **16 = Rooms** (facade
`OALMDGJKBJH`), verb **GET** (`HttpMethod` statics `[rcx+8]` at `0x7DF2078`).

Path is `String.Format("rooms/{0}/playerdata/me", roomId)` — literal slot **`0xD1A3390`**; the room id
is a **path segment**. **No params, no body.** There is no `playerdata/{accountId}` variant anywhere in
the build — `me` is the only form.

The GET lives in the async state machine **`KPMFJJJDHBL$$MoveNext`** `0x7DF1F50`.

## Response — BARE, one key

Send helper is **`OALMDGJKBJH.NDBMFFLDBBK<T>`** — one of the Rooms facade's two **description-less
(bare)** helpers, so there is no envelope. Generic inst **#2782** = **`.ADDGAOJJHIL`** (typedef
#23121), formatter `CMABAAMGFLP` `.ctor 0x7766B10`, **1 key** for its 1 declared field:

| # | key | CLR | off |
|---|---|---|---|
| 1 | `Data` | **string** | 0x10 |

```json
{ "Data": "whatever the room stored" }
```

⚠️ **`Data` is a flat string, not an object.** Whatever structure the room keeps inside it is the
room's business — if you store JSON there it must be sent as an **escaped string**, the same way
`ChatMessage.Contents` works ([chat-sendmessage](chat-sendmessage-wire-shape.md)). Emitting
`"Data": { ... }` will not deserialize.

`{}` deserializes fine (the single key is omittable, leaving `Data` null), but an **empty body** throws
`IONCMJIACFI`. Serve `{"Data":""}` or `{"Data":null}` for "no data yet" rather than a bare `204`.

Utf8Json accepts `Data` and `data` — only two casings exist for this key, because the camelCase and
all-lowercase forms coincide.

## The PUT on the same path is ENVELOPED

`OALMDGJKBJH.JKPOEEFPAFN` `0x7DFB390` uses the same literal with `HttpMethod` statics
**`[rcx+0x28]` = Put** (`0x7DFB4A2`) and carries the literal **`'save player room data'`** — a
`friendlyActionDescription`, which is the reliable tell for an **enveloped** helper on this facade.
So the write expects the envelope tier:

```json
{ "Success": true, "Error": null, "error_id": null }
```

(The exact envelope generic sits in a continuation built by `OAIFDLKBDGK..ctor` at `0x7DFB4F0`, which
I did not resolve; the valueless `JFNAKFCGDAO` is the shape every other description-carrying write on
this facade uses. Treat the presence of `Value` as unverified.)

**Do not serve one shape for both verbs on this path.** GET is bare, PUT is enveloped.

## Validation

`ADDGAOJJHIL.CPOBHIECLEN` is the shared no-op stub `0xA60520` — no post-deserialize validation, and
the key is omittable.

**Not traced:** what the client does with a `null` `Data`. Consumption happens past the state
machine's awaiter in code I did not follow, so prefer `""` over `null` if the room's circuits read the
value as a string.
