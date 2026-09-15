# Messages v3 delete wire shape

> POST api/messages/v3/delete (svc 2 API) sends {MessageIds:[long]} and IGNORES the response body entirely (SendWithNoResponse) — any 2xx works; the client also deletes locally first and never surfaces an error.

Derived **2026-08-24** from build `20250718.01` via [recflare-2025-metadata-carve](../../../il2cpp-analysis/references/recflare-2025-metadata-carve.md).

`POST https://api.<host>/api/messages/v3/delete` — service **2 = API** (`mov r8d, 2`,
[recnet-service-enum](../conventions/recnet-service-enum.md)), verb **POST** (`HttpMethod` statics `+0x20`), **no query params**.
Client entry `EGCFIPALFLN.LGHNMKKCMKJ(IEnumerable<long> messageIds)` `0x7D2A430`, literal
`0xD13C508`. It is the *only* `messages/v3` route in the binary.

**Request body** — `RecNet.DeleteMessagesRequestDTO` via `ELKIBCPINAP`, formatter `CHAEKIMDJHK`
`.ctor 0x7C0FF60`, exactly one key:

```json
{ "MessageIds": [ 101, 102 ] }
```

`MessageIds` is `List<long>`. (Field name is unobfuscated on the CLR type too.)

**There is no response shape.** The send is `MGPBDIAGCFD.CNDMDLNHDLI` (`0x7D2A782`) — the
*SendWithNoResponse* variant returning the non-generic promise `JCFICNGFDLA`. **The body is never
read or deserialized**, so 200 with anything, 204, or an empty body are all equally fine. Nothing
here can raise [ioncmjiacfi-malformed-response](../conventions/ioncmjiacfi-malformed-response.md) or [llcldppagij-envelope-failure-exception](../conventions/llcldppagij-envelope-failure-exception.md).

**The client deletes locally first and ignores failures.** Before sending it builds a
`HashSet<long>` of the ids, runs `List<PNAFJFAEEEE>.RemoveAll` over two local message lists and
calls `EGCFIPALFLN.FDNIAIILDNG`, then fires the request with a bare
`JMNHOAIMFBC.AOCLNBFKPEP` continuation. The method contains **no error string literals at all**, so
a failed delete leaves the UI looking successful until the next refetch — do not expect the client
to report a server-side failure here.

**Empty input short-circuits:** `Enumerable.Any(ids)` is checked first (`0x7D2A55E`) and an empty
sequence returns without issuing any HTTP request.
