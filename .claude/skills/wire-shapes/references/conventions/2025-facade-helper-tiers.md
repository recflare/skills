# The 2025 facade helper tiers — on `20250718.01` the friendly string really does mean enveloped

> There are **two** helper layers on `20250718.01` and they are easy to confuse. The `MGPBDIAGCFD`
> methods (`HPBKMCLEANE` / `CJBFDPLCIEJ` / `CNDMDLNHDLI`) are on the **request object** and say
> nothing about envelopes. The tier that decides the wire shape is the **facade** helper, and there
> the 2025 rule holds exactly: **a leading `friendlyActionDescription` means the response is
> enveloped and the helper unwraps it.** On this build, that usually means **reads are bare and
> writes are enveloped on the very same path.**

Measured **2026-10-16** on the Lists facade (`.FCKNCPNDBBM`) after a live
`LLCLDPPAGIJ` on `DELETE curatedlists/{listId}/items/{itemId}` that a **bare** `CuratedListDTO` had
been returned to. See [curatedlists-items-createlistifneeded](../endpoints/curatedlists-items-createlistifneeded-wire-shape.md).

## The four facade helpers

Every 2025 facade class declares its own copy of these (`py msig.py <facade>` prints them):

| helper | signature | tier |
|---|---|---|
| `NDBMFFLDBBK<T>` | `(HttpMethod, route, ct, Action<MGPBDIAGCFD>) -> Task<T>` | **bare `T`** |
| `LMKONLJOAEP<T>` | same, class-bound wrapper | **bare `T`** |
| `PJPLCMBOAFB<T>` | **`(string friendlyActionDescription, HttpMethod, route, ct, action) -> Task<T>`** | **enveloped**: body is `{Value, Success, Error, error_id}`, helper asserts `Success` and returns `Value` |
| `ONEPMGPMHNC` / non-generic `PJPLCMBOAFB` | **`(string friendlyActionDescription, …) -> Task`** | **valueless envelope**: body is `{Success, Error, error_id}`, helper asserts `Success` |

Both description-carrying tiers throw **`LLCLDPPAGIJ`** when the envelope is missing or
`Success != true` ([llcldppagij-envelope-failure-exception](llcldppagij-envelope-failure-exception.md)).
The non-generic tier's shared body is `HJKOEIEIJPB$$MoveNext` `0x7E27390`, which sends
`MGPBDIAGCFD::HPBKMCLEANE<.JFNAKFCGDAO>` (generic inst **#2849**) on a **non-generic**
`AsyncTaskMethodBuilder` and calls `LLCLDPPAGIJ$$.ctor` at `0x7E27649`. The delete-list route
`ILFOMFFBFCF$$MoveNext` `0x7E2A880` starts that same state machine (`Start` spec **#77182**,
identical to `FCKNCPNDBBM$$PJPLCMBOAFB` `0x7E23F40`), which is how the two were tied together.

## How to read it off a route in one step

`py slots2025.py <state_machine_rva> 0x340` and look at the facade `MethodRef`:

```
MethodRef  .FCKNCPNDBBM::NDBMFFLDBBK  <generic inst method=2891>   -> bare .OOCDKDLBGOI
MethodRef  .FCKNCPNDBBM::PJPLCMBOAFB  <generic inst method=2891>   -> {Value: .OOCDKDLBGOI, Success, Error, error_id}
```

The `StringLiteral` on the next line or two is the `friendlyActionDescription`, and its presence
agrees with the helper name every time. `py ginst.py inst <n>` resolves the type argument.

## Worked table — the Lists facade, every curated-list route

This is the split that matters, because the **same path serves a bare GET and an enveloped write**:

| route | state machine | helper | description | wire shape |
|---|---|---|---|---|
| `GET curatedlists/bulk?id=` | `OBENNBMFBDA` `0x7E3A940` | `LMKONLJOAEP` (#2740) | — | **bare** `[CuratedListDTO]` |
| `GET curatedlists?creatorAccountId=&type=&name=` | `OCHMOLJGPJJ` `0x7E3AD60` | `NDBMFFLDBBK` (#2891) | — | **bare** `CuratedListDTO` |
| `GET curatedlists/{listId}` | `DLILMAHADBJ` `0x7E20D40` | `NDBMFFLDBBK` (#2891) | — | **bare** `CuratedListDTO` |
| `POST curatedlists/create` | `PCBNDMMHOIC` `0x7E3B430` | `PJPLCMBOAFB` (#2891) | `'create list'` | **enveloped** `{Value, …}` |
| `PUT curatedlists/{listId}/items/{itemId}` | `MKOBBNNCADE` `0x7E35F10` | `PJPLCMBOAFB` (#2891) | `'add item to list'` | **enveloped** `{Value, …}` |
| `PUT curatedlists/{name}/items/{itemId}/createlistifneeded` | `IMCOMMPAEDL` `0x7E2B090` | `PJPLCMBOAFB` (#2891) | `'add item to list'` | **enveloped** `{Value, …}` |
| `DELETE curatedlists/{listId}/items/{itemId}` | `FONPJGBLNHE` `0x7E260D0` | `PJPLCMBOAFB` (#2891) | `'remove item from list'` | **enveloped** `{Value, …}` |
| `DELETE curatedlists/{listId}` | `ILFOMFFBFCF` `0x7E2A880` | non-generic `PJPLCMBOAFB` | `'delete list'` | **valueless envelope** |
| `POST contextualfeatures` | `GFIFNJPCDHC` `0x7E26420` | `LMKONLJOAEP` (#2849) | — | **bare** — but `T` **is** `.JFNAKFCGDAO`, so the caller asserts |

inst **#2891** = `.OOCDKDLBGOI` (CuratedListDTO), **#2740** = `List<.OOCDKDLBGOI>`,
**#2849** = `.JFNAKFCGDAO` (the valueless envelope).

Note the last row: a *bare* send whose `T` happens to be an envelope type. That is why
`POST contextualfeatures` cannot throw `LLCLDPPAGIJ` by itself — the exception comes from whoever
calls `POCKEGKCADF.AIHPPAPDEBL` on the result.

## ⚠️ What this retires

- **"Every curated-list endpoint returns a bare DTO."** False, and it cost two wrong answers. It was
  read off the three GET routes.
- **Carrying a 2026 tier back to 2025.** 2026 moved the envelope into `T` and made the helper never
  unwrap, so on 2026 a facade returning `Task<SomeDTO>` really is bare
  ([2026-send-helper-tiers](2026-send-helper-tiers.md)). On 2025, `Task<SomeDTO>` through
  `PJPLCMBOAFB` is **enveloped**. The same facade method, same DTO, different body between builds.

**How to apply:** on a 2025 route, never answer "bare or enveloped" from the return type alone. Read
the facade helper name at the send site. If a route is a write and the client throws `LLCLDPPAGIJ`
at a payload you believe is correct, you are almost certainly missing the `{Value, Success, Error,
error_id}` wrapper.
