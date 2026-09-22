# Auth role routes wire shape

> GET role/{roleName}?id=N (svc 1 Auth) returns a BARE JSON ARRAY OF INTS; `id` is repeatable and the VERB IS DYNAMIC — GET under 100 ids, POST (form body) at 100+. The sibling role/developer/{id} is a different route returning a BARE JSON BOOLEAN.

Derived **2026-09-16** from build `20250718.01`.
The dynamic verb is a live instance of [elhkhfjehlm-verb-dependent-params](../conventions/elhkhfjehlm-verb-dependent-params.md) — the same
call site emits query params or a form body depending on which verb it picked.

**Two different routes share the `role/` prefix. Do not conflate them.**

| route | method | verb | response |
|---|---|---|---|
| `role/{roleName}?id=` | `MPBOHFPJPOC$$MoveNext` `0x7C91D70` (+0x450) | **GET or POST** (see below) | **bare `List<int>`** |
| `role/developer/{id}` | `LPNHLJBDCLH$$AEADHDKOBDJ` `0x7C84560` (+0x180) | **GET** (`[rcx+8]` at `0x7C84627`) | **bare `bool`** |

Both are service **1 = Auth** (`mov r8d, 1` at `0x7C91F52` / `0x7C84691`), i.e. `auth.<host>`.
Both appear in the generated `nonobject-responses.txt` (lines 132–133), so **`{}` or an empty body
throws `IONCMJIACFI`** on either.

## `GET role/{roleName}?id=N` — the queried form

Path is `String.Concat("role/", roleName)` — the role name is a **free-form caller-supplied
segment**, so `role/developer` is just `roleName = "developer"`; the client has no baked list of
role names (`'role/'` is the only literal). `id` is added via
`MGPBDIAGCFD.ELHKHFJEHLM` (`0x7C91F63`) with an `int` value (generic inst #42), **once per id** —
it is repeatable: `?id=2&id=3&id=4`.

Response `T` = generic inst **#1011** = **`List<int>`** — a bare array of ints, no envelope:

```json
[2]
```

Serve `[]` for "none", never `{}` and never an empty body.

> **Semantics (inference, not proven from the binary):** the request passes a *set* of player ids
> and the response is a `List<int>`, which reads as "the subset of those ids that hold this role".
> `?id=2` returning `[2]` means player 2 is a developer; `[]` means not. The shape is certain; this
> reading of it is not.

### ⚠️ The verb is chosen at runtime by the id count

`rdx` at the `AKJEAMCCEOH..ctor` call is not a constant `HttpMethod` — there is **no `HttpMethod`
TypeInfo anywhere in the state machine**. It comes from
`MPDMKDOGMGF.FMECHGPBMNN(int n, int limit)` `0x7DBA250`, declared
`static HttpMethod FMECHGPBMNN(int, int)`, called as `FMECHGPBMNN(idCount, 100)`:

```
cmp edi, ebx          ; idCount vs 100
jge  -> returns HttpMethod statics [+0x20] = POST
else -> returns HttpMethod statics [+0x08] = GET
```

| id count | verb | where the ids go |
|---|---|---|
| **< 100** | **GET** | **query string** — `?id=2&id=3` |
| **≥ 100** | **POST** | **`application/x-www-form-urlencoded` body** — `id=2&id=3&…` |

That second row follows from `ELHKHFJEHLM` being verb-dependent
([elhkhfjehlm-verb-dependent-params](../conventions/elhkhfjehlm-verb-dependent-params.md)): GET puts params in the query string, every other
verb puts them in a form body. It is a URL-length guard.

**A server that only routes `GET /role/:name` will silently miss every bulk lookup of 100+ ids** —
those arrive as `POST /role/:name` with a form body and the same expected `List<int>` response.

## `GET role/developer/{id}` — the single-player form

Different facade, different shape. `String.Format("role/developer/{0}", id)` (`0x7C84669`) — the id
is a **path segment, not a query param**. The client method is
`static KPIPLFECKNC<bool> AEADHDKOBDJ()` — it takes **no arguments**; the id is filled from client
state via `LPNHLJBDCLH.GCHHELOPPPP` (`0x7C84642`). No `ELHKHFJEHLM`, no `ELKIBCPINAP` — no query
params and no body.

Response `T` = generic inst **#41** = **`bool`** — the entire body is a bare JSON boolean:

```json
true
```

Here `developer` is **hardcoded in the literal**, so this route exists only for the developer role,
unlike the queried form above which takes any role name.
