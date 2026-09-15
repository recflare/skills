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

**Every curated-list endpoint in that path returns a BARE DTO, so none of them can throw this:**
`POST curatedlists/create` (bare `OOCDKDLBGOI`),
`PUT curatedlists/{name}/items/{itemId}/createlistifneeded` (bare),
`PUT curatedlists/{listId}/items/{itemId}` (bare),
`DELETE curatedlists/{listId}/items/{itemId}` (bare — verb offset `[rcx+0x00]`).
See [curatedlists-lookup-and-pagesource-names](../endpoints/curatedlists-lookup-and-pagesource-names.md).

**How to apply:** when this exception appears, stop suspecting the bare endpoints and find the
enveloped call in the same flow — it is the only thing that can raise it.

## Reading the stack trace (2026-08-20)

`MEMPCBCLDEF\`1:MoveNext()` in these traces is **the localization state machine**
(`RecRoom.Localization.Runtime`, `GIECMNJOHGH<T>(this T enumValue, params object[]) where T : Enum`),
not the failing HTTP call. `KFDCPJGDNNB` awaits it to build the toast text and *then* logs the
already-caught exception. **Everything below the RRUI frame is the logging path — the trace never
shows where the exception was thrown.**

## Leading suspect for the save-for-later failure: `POST contextualfeatures`

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

Also verified: `accessibility` and `type` on `createlistifneeded` are **query params**, not a form
body — same `ELHKHFJEHLM` adder that produces the visible `?type=1` on `algorithmiclists`.
