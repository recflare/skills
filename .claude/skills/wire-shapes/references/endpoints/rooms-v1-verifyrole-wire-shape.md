# Rooms v1 verifyRole wire shape

> POST api/rooms/v1/verifyRole (svc 2 API, NOT Rooms) sends 3 form fields and its response body is IGNORED ENTIRELY — the send helper is CNDMDLNHDLI, which never deserializes. Any 2xx with any body works; `{}` is fine.

Derived **2026-10-01** from build `20250718.01`.

`POST https://api.<host>/api/rooms/v1/verifyRole` — service **2 = API** (`mov r8d, 2` at `0x7DDB029`),
verb **POST** (`HttpMethod` statics `[rcx+0x20]` at `0x7DDB006`). Whole-route literal, slot
`0xD150F80`.

⚠️ **The path says `rooms` but the service is API (2), not Rooms (16).** It belongs on
`api.<host>`, not `rooms.<host>` — the same kind of mismatch as `privileges/*` living on Auth. Sibling
literals `api/rooms/v1/filters` and `api/rooms/v1/report/addScreenshot` share the prefix.

Client entry **`KCHDMOJGHJD.OBAFODBEOJB`** `0x7DDAEC0` (+0x310).

## Response — IGNORED

The send helper is **`MGPBDIAGCFD.CNDMDLNHDLI`** `0x7D9ACC0`, called at `0x7DDB141`. That is the
**no-response** helper: it does not deserialize, so there is no `T`, no formatter, and no shape to
match. Return **any 2xx**; `{}`, `204`, or a full object are all equivalent to the client.

Consequences worth being explicit about:

- **`IONCMJIACFI` cannot be raised here** — nothing parses the body, so an empty body is safe (unlike
  every `HPBKMCLEANE<List<T>>` route).
- **`LLCLDPPAGIJ` cannot be raised either** — there is no envelope, so `Success`/`Error` are not read.
  A failure has to be signalled with a **non-2xx status code**, not with `{"Success": false}`.
- The only thing the client can observe is the HTTP status. If the server wants to reject a role
  claim, it must return 4xx.

Other routes using this helper, for comparison: `customAvatarItems/v1/design` PUT and DELETE
([customavataritems-routes-wire-shapes](customavataritems-routes-wire-shapes.md)).

## Request — 3 form fields

Three `MGPBDIAGCFD.ELHKHFJEHLM` calls. The verb is POST, so these are an
**`application/x-www-form-urlencoded` body**, not a query string
([elhkhfjehlm-verb-dependent-params](../conventions/elhkhfjehlm-verb-dependent-params.md)):

| # | field | RVA of the add | source |
|---|---|---|---|
| 1 | `roomId` | `0x7DDB0A6` | `RecNet.Matchmaking.MLNNAKHOFCA` — the **current room**, read three times in this method |
| 2 | `role` | `0x7DDB0FF` | `HGMJJMJDHLJ.DDFDFBIGGHK(room, 0)` `0x7E10620`, boxed as an int |
| 3 | `context` | `0x7DDB12B` | passed in; added through a different `ELHKHFJEHLM` overload (`r9b = 1` at `0x7DDB114`) |

All three adds are unconditional — each is guarded only by the null-check on the request object, not
by a value test, so the server can rely on all three being present.

`role` is a **numeric enum** on the wire:

| value | name |
|---|---|
| 0 | `Guest` |
| 1 | `Host` |
| 2 | `Moderator` |
| 3 | `CoOwner` |
| 4 | `Creator` |

Two typedefs carry exactly this enum — `.ELFGHKKIEJB` (#22878) and `.OLFCKNLAAGC` (#8501) — and I did
not pin which one `DDFDFBIGGHK` returns. **It does not matter on the wire: the member values are
identical in both.**

⚠️ `Guest` is `0`, so an omitted or defaulted `role` reads as the lowest privilege — the safe
direction here, unlike the `Platform`/`Status` traps elsewhere.

## No validation to worry about

There is no response DTO, so there is no `CPOBHIECLEN` hook and nothing to omit incorrectly. This is
one of the few routes where the server genuinely cannot get the response shape wrong.
