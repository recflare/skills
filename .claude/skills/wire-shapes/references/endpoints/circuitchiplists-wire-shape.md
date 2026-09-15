# Circuitchiplists wire shape

> GET api/CircuitChipLists/{name} (svc 2 API) returns a BARE ARRAY of GUID strings — a circuit-chip whitelist. Nullable send tolerates a null body at parse time, but the consumer NREs on a cached null list, so always serve [].

Derived **2026-08-27** from build `20250718.01` via [recflare-2025-metadata-carve](../../../il2cpp-analysis/references/recflare-2025-metadata-carve.md).

`GET api/CircuitChipLists/{listName}` — **GET** (`HttpMethod` statics `+0x08`), service **2 = API**.
Path is `String.Concat("api/CircuitChipLists/", listName)`, so the trailing segment is a free-form
list name; the two the client asks for are **`whiteglove1`** and **`whiteglove2`**
(`NOEKPCJEAHJ.HLEKCNNAPBA()` enumerates the names).

Client entry `NOEKPCJEAHJ.EALPGMHHEEN(string listName)` -> `Task<List<System.Guid>>`,
state machine `LKMAGEFIBEI$$MoveNext` `0x7C9F550`.
Send `MGPBDIAGCFD.CJBFDPLCIEJ<List<System.Guid>>` — the **nullable** variant.

## Response: a bare array of GUID strings

```json
["6da89ddf-f2e5-4c32-8b22-feb687683e36", "1c92f780-baf1-4bd8-aa15-27cca0aa7396"]
```

No object, no envelope, no wrapper — `T` is `List<Guid>` directly, so this belongs on
[nonobject-response-routes](../conventions/nonobject-response-routes.md). `{}` raises the malformed-response throw.

## Serve `[]`, never `null`

The nullable send means a `null` body will not throw at parse time — but the list is cached by name
and the membership check dereferences it:

```
NOEKPCJEAHJ.DACFOOCNLMB(string listName, Guid) 0x80DC0A0
  dict null/empty            -> return false
  TryGetValue miss           -> return false
  0x80DC114: test rcx, rcx
             je 0x80DC151    -> NullReferenceException   ; stored List<Guid> is null
```

So a null body converts a clean "not whitelisted" into a hard NRE the first time a chip is checked.

## What it gates

`NOEKPCJEAHJ` is a circuit-chip whitelist: `FMHOHELFFNG(Guid)` and `KMIKCJPJFPH(Guid)` are the
per-chip checks (the latter tries `whiteglove2` then `whiteglove1`), `DACFOOCNLMB(name, Guid)` is the
per-list check, `GEFLNIHHMMK()` is the loader. An empty array = nothing whitelisted, which is the
correct permissive-free default and never throws.
