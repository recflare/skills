# Api images v1 report wire shape

> POST api/images/v1/{imageId}/report (svc 2 API) sends NO body and NO query params, and its response body is IGNORED ENTIRELY (CNDMDLNHDLI). The image id in the path plus the caller's token are the only inputs — the author id is never sent, so the server must resolve it from the image. No reason/category reaches the server either.

Derived **2026-10-02** from build `20250718.01`.
Sibling of [api-images-v6](api-images-v6-wire-shape.md) on the same facade `HPJKKCCECLH`.

`POST https://api.<host>/api/images/v1/{imageId}/report` — service **2 = API**
(`mov r8d, 2` at `0x7CF58FB`), verb **POST** (`HttpMethod` statics `[rcx+0x20]` at `0x7CF58A6`).

Path is `String.Format("{0}v1/{1}/report", "api/images/", imageId)` — built from the **shared
`api/images/` prefix** (slot `0xD12D0B8`), so grepping for `api/images/v1/` finds nothing.

Client entry **`HPJKKCCECLH.HGFICBPHMLD`** `0x7CF5790` (+0x200). Callers:
`LGAADMDDGGC.HDNAICBKPPD` `0x26D4870` (the report dialog) and the tail-jump wrapper
`PKEPMPCJDHL.HGFICBPHMLD` `0x7C985A0`.

## Request — genuinely empty

`slots2025.py` over the whole method returns **zero** `ELHKHFJEHLM` and **zero** `ELKIBCPINAP` calls.
There is no query string, no form body and no JSON body: the request is a bare POST whose only
payload is the `{imageId}` path segment.

**Consequences for the server, all forced by that:**

| the row needs | where it comes from |
|---|---|
| image id | the **path segment** |
| reporter id | the **auth token** — not in the request |
| image author id | **not sent** — the server must look it up from the image id |
| a reason / category | **never sent** — see below |

⚠️ **No reason or category reaches the server.** Whatever the report dialog collects client-side is
not transmitted on this route. Contrast `api/PlayerReporting/v3/create`, which is a separate route
with its own payload. So a `reason` column on the report table can only ever be null from here —
don't make it NOT NULL.

## Response — IGNORED

Send helper is **`MGPBDIAGCFD.CNDMDLNHDLI`** at `0x7CF5914` — the **no-response** helper. It does not
deserialize, so there is no `T`, no formatter and no shape to match.

Return **any 2xx**; `{}`, `204` and a full object are all equivalent to the client.

- **`IONCMJIACFI` cannot fire** — nothing parses the body, so an empty body is safe.
- **`LLCLDPPAGIJ` cannot fire** — no envelope, so `Success`/`Error` are not read. A rejection has to
  be a **non-2xx status code**; `{"Success": false}` with a 200 reads as success.
- The only thing the client can observe is the status code.

Same helper, same consequences as [rooms-v1-verifyrole](rooms-v1-verifyrole-wire-shape.md) and the
`customAvatarItems/v1/design` PUT/DELETE pair
([customavataritems-routes-wire-shapes](customavataritems-routes-wire-shapes.md)).

## Idempotency is the server's problem

Because the client ignores the response, it cannot tell a first report from a duplicate, and nothing
stops the dialog being submitted twice. If a duplicate `(imageId, reporterId)` should not create a
second row, enforce that server-side — the client will look identical either way.
