# Llcldppagij envelope failure exception

> LLCLDPPAGIJ is recflare-2025's generic 'RecNet envelope reported failure' exception — thrown only when an ENVELOPED response is null or Success==false, never by a bare-DTO endpoint.

Identified **2026-08-20** on `C:\Games\recflare-2025` (build `20250718.01`) via
[recflare-2025-metadata-carve](../../../il2cpp-analysis/references/recflare-2025-metadata-carve.md), from the log line
`Error saving room for later: Exception of type 'LLCLDPPAGIJ' was thrown.`

`LLCLDPPAGIJ : MELLIJAOIBB : Exception`, ctor `LLCLDPPAGIJ(MPKGNLKJDEG response)` at `0x7C70790`.
The canonical thrower is the extension `POCKEGKCADF.AIHPPAPDEBL(this MPKGNLKJDEG response)`
(`0x7C750E0`), which is exactly:

```
if (response == null)  throw;
if (!response.Success) throw new LLCLDPPAGIJ(response);
```

**Its meaning is narrow and useful: an *enveloped* RecNet call came back null or with
`Success == false`.** `MPKGNLKJDEG` is implemented **only** by the envelope family — `JFNAKFCGDAO`,
`FFOENOGPGNH<T>`, `PMFNJIOOINF<T>`. A bare-DTO endpoint (e.g. anything returning `OOCDKDLBGOI`)
can never raise it. There are 34 throw sites; it is the client's generic "assert this call
succeeded", also used by e.g. the AI `realtime-session/create` path
([ai-realtime-session-create-wire-shape](../endpoints/ai-realtime-session-create-wire-shape.md)).

The exception message carries **no endpoint name**, so the client log cannot tell you which call
failed — correlate against the server access log for the request immediately preceding it.

## "Save room for later" specifically

`RRUI.Data.RoomModel.ToggleSavedForLaterAsync(string roomId)` (`0x2880280`), state machine
`KFDCPJGDNNB$$MoveNext` (`0x289A300`), catches any Exception and shows
`"Error saving room for later: " + message`.

The feature is **a curated list with the hardcoded name `__SavedForLater_Rooms`** and
`type = KJMOLELGPPF.Rooms (1)` — const `JPKHPKIDMGE` on `IIINMGAEJDB`. There is no `playlists/*`
endpoint on this build; it is all curated lists.

⚠️ **CORRECTED 2026-10-16 — the opposite is true.** This note used to say *"every curated-list
endpoint in that path returns a BARE DTO, so none of them can throw this"*. **Wrong**, and it cost
two bad answers. Only the three **GET**s are bare; **every write on that path is enveloped** and
every one of them can throw this:

| route | facade helper | body |
|---|---|---|
| `GET curatedlists/bulk?id=`, `GET curatedlists?…name=`, `GET curatedlists/{listId}` | `LMKONLJOAEP` / `NDBMFFLDBBK` | **bare** |
| `POST curatedlists/create` (`'create list'`) | `PJPLCMBOAFB` | `{Value, Success, Error, error_id}` |
| `PUT curatedlists/{listId}/items/{itemId}` (`'add item to list'`) | `PJPLCMBOAFB` | `{Value, …}` |
| `PUT curatedlists/{name}/items/{itemId}/createlistifneeded` (`'add item to list'`) | `PJPLCMBOAFB` | `{Value, …}` |
| `DELETE curatedlists/{listId}/items/{itemId}` (`'remove item from list'`) | `PJPLCMBOAFB` | `{Value, …}` |
| `DELETE curatedlists/{listId}` (`'delete list'`) | non-generic `PJPLCMBOAFB` | `{Success, Error, error_id}` |

The full measured table and the one-step way to read the tier off any 2025 route is in
[2025-facade-helper-tiers](2025-facade-helper-tiers.md). Also see
[curatedlists-lookup-and-pagesource-names](../endpoints/curatedlists-lookup-and-pagesource-names.md).

**How to apply:** when this exception appears, stop suspecting the bare endpoints and find the
enveloped call in the same flow — it is the only thing that can raise it.

## Reading the stack trace (2026-08-20)

`MEMPCBCLDEF\`1:MoveNext()` in these traces is **the localization state machine**
(`RecRoom.Localization.Runtime`, `GIECMNJOHGH<T>(this T enumValue, params object[]) where T : Enum`),
not the failing HTTP call. `KFDCPJGDNNB` awaits it to build the toast text and *then* logs the
already-caught exception. **Everything below the RRUI frame is the logging path — the trace never
shows where the exception was thrown.**

## ~~Leading suspect for the save-for-later failure: `POST contextualfeatures`~~ — RESOLVED, it was the writes

⚠️ **Resolved 2026-10-16.** The save-for-later failure was the curated-list **write** routes
themselves, which are enveloped (table above). The `contextualfeatures` theory below is kept because
the facade analysis in it is still accurate, but it is **not** the cause: a bare send whose `T` is
an envelope cannot throw this by itself.

### The original (superseded) theory

`IIINMGAEJDB.JDOEPIKNFMH(Dictionary<string, object>)` (`0x7E28B30`, state machine
`GFIFNJPCDHC$$MoveNext` `0x7E26420`) is a **POST to `contextualfeatures`** on the Lists service and
is the **only enveloped endpoint on that facade** — it returns `Task<JFNAKFCGDAO>`, i.e.
`{Success, Error, error_id}`, which is precisely what `AIHPPAPDEBL` asserts on.

Its one caller is `EJMMBCGFLOC.GCGKPFKOADD()` (`0x1845C20`), and **`EJMMBCGFLOC` is also the class
that looks up `__SavedForLater_Rooms`** via `IIINMGAEJDB.CMAOBOELHJM(name, KJMOLELGPPF.Rooms, ct)`.
Same manager, both jobs.

Symptom fit: the `createlistifneeded` PUT succeeds and `ItemIds` really does gain the room, yet the
UI reports "Error saving room for later" — because a *different*, enveloped call in the same flow
threw. If `POST contextualfeatures` is unimplemented or answers with anything that is not
`{"Success": true, "Error": null, "error_id": null}`, that is enough.

~~Also verified: `accessibility` and `type` on `createlistifneeded` are **query params**, not a form
body.~~ ⚠️ **RETRACTED 2026-10-16.** That line predates
[elhkhfjehlm-verb-dependent-params](elhkhfjehlm-verb-dependent-params.md) (2026-09-02), which proved
`ELHKHFJEHLM` branches on the verb. `createlistifneeded` is a **PUT**, so the two params go in an
`application/x-www-form-urlencoded` **body**. Same on 2026 —
[curatedlists-items-createlistifneeded](../endpoints/curatedlists-items-createlistifneeded-wire-shape.md).

## ⚠️ The actual thrower: the **no-response-value** tier asserts the envelope (2026-10-16)

Re-measured when this exception came back live on `PUT curatedlists/.../createlistifneeded`. The
`AIHPPAPDEBL` extension is only *one* of the 34 throw sites. The other ~30 are one per facade class,
and they are all the same thing: **the send helper behind a facade method that returns a non-generic
`Task`.** On the Lists facade that is `HJKOEIEIJPB$$MoveNext` `0x7E27390`:

```
0x7e273b0  AsyncTaskMethodBuilder::AwaitUnsafeOnCompleted   ; NON-generic builder -> outer is Task
0x7e273c8  MGPBDIAGCFD::HPBKMCLEANE  <generic inst 2849>    ; 2849 = .JFNAKFCGDAO
0x7e2755d  AsyncTaskMethodBuilder::SetResult                ; no argument
0x7e27649  call LLCLDPPAGIJ$$.ctor
```

So on `20250718.01` a "no response value" route is **not** body-agnostic: the helper deserializes
`{Success, Error, error_id}` with `HPBKMCLEANE` (*response required*) and throws if `Success` is not
`true`. **This is the opposite of 2026**, where the same tier discards the body — see the build-
difference box in [2026-send-helper-tiers](2026-send-helper-tiers.md). On 2025, **every valueless
write needs `{"Success": true, "Error": null, "error_id": null}` and a 2xx.**

### What the exception tells you about the response

Because the helper is the response-**required** one, the two failure modes separate cleanly:

| server answer | exception |
|---|---|
| `204`, empty body, or unparseable | **`IONCMJIACFI`** `Malformed Response` |
| `{}`, `{"Success": false, …}`, or any object without `Success: true` | **`LLCLDPPAGIJ`** |
| non-2xx (404, 500, …) | **`RecNetWebException: HTTP Error {0}`** |

So `LLCLDPPAGIJ` narrows the culprit a long way: the request got a **2xx whose body parsed** and whose
`Success` was not `true`. It is **not** a 404 and **not** an empty body. Grep the server access log
for a 2xx in that flow answering `{}`, `null`-ish JSON, a bare DTO where an envelope belongs, or an
explicit `Success: false`.

## Build fingerprint — this exception means the 2025 client

`LLCLDPPAGIJ`, `KFDCPJGDNNB` and `ONIHMLNNEEF` exist **only** in `20250718.01`; all three are
**absent** from the `20260323.14` index (0 hits in `methods.pkl` and `out/stringliteral.json`). The
2026 build keeps compiler-generated names, so its equivalent frame reads
`<SetRoomSavedForLaterStateAsync>d__142`, never `KFDCPJGDNNB`. **An obfuscated `*$$MoveNext` frame in
a Player.log is therefore a 2025 log**, and any wire shape quoted at it must be re-read from the 2025
index before it is trusted.
