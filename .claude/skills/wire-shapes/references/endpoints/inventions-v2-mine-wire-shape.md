# Inventions v2 mine wire shape

> GET api/inventions/v2/mine (svc 2 API) takes NO params and returns a BARE ARRAY of the same 28-key Invention DTO (KKBFDGFLMMA) as /v2/search. CONFIRMED 2026-10-02: a wrong `UgcVersion` makes every row VANISH from the client with no log and no error - the only symptom is an empty list. Its path is also a STATIC FIELD, not an inline literal, so xrefing the route string lands in the cctor and finds no request method.

Derived **2026-10-02** from build `20250718.01`.
The element DTO, its enums and its Obscured* handling are fully documented in
[inventions-v2-search](inventions-v2-search-wire-shape.md) — this note does not duplicate the 28-key table.

`GET https://api.<host>/api/inventions/v2/mine` — service **2 = API** (`mov r8d, 2` at `0x7CE89CD`),
verb **GET** (`HttpMethod` statics `[rcx+8]` at `0x7CE8982`).

Client entry **`GLAKFFIIDPF.BFLLGGKGLLK`** `0x7CE8890` (+0x290). **No params and no body** — no
`ELHKHFJEHLM`, no `ELKIBCPINAP`; the only extra builder call is `MGPBDIAGCFD.DIDJOECFJII`
`0x7CE8A11`, the response-cache TTL. The account comes from the auth token.

## Response — BARE ARRAY

`MGPBDIAGCFD.HPBKMCLEANE<T>` (response required), generic inst **#1015** =
**`List<KKBFDGFLMMA>`** — identical to `/v2/search`. No envelope, not paged.

```json
[ { "InventionId": 900001, "ReplicationId": "…", "CreatorPlayerId": 205,
    "Name": "My Thing", "Description": "", "LongDescription": "", "ImageName": null,
    "UgcVersion": 0, "CurrentVersionNumber": 1, "LatestVersionNumber": 1,
    "Accessibility": 0, "ForceCannotPublish": false,
    "ModifiedAt": "2026-01-01T00:00:00Z", "CreatedAt": "2026-01-01T00:00:00Z",
    "FirstPublishedAt": null, "CreationRoomId": null,
    "NumPlayersHaveUsedInRoom": 0, "NumDownloads": 0, "CheerCount": 0,
    "CreatorPermission": 100, "GeneralPermission": 0,
    "IsAGInvention": false, "IsCertifiedInvention": false, "IsRecRoomApproved": false,
    "AllowTrial": false, "Price": null, "HideFromPlayer": false,
    "DisplayMetadataJson": null } ]
```

`{}` or an empty body throws `IONCMJIACFI`; serve **`[]`** for "no inventions". `ModifiedAt` comes
**before** `CreatedAt`, and `DisplayMetadataJson` is nested JSON as an **escaped string** — both per
the search note.

## ⚠️ `UgcVersion` silently hides every row — CONFIRMED 2026-10-02

**Root cause of a real "none of my inventions appear" report.** The route returned 200 with a
structurally valid 28-key payload; the client rendered **nothing**, with no log line, no exception and
no failed request. `/v2/search` on the same server rendered fine.

The server was emitting **`UgcVersion: 0`**; every row `/v2/search` returns carries **`UgcVersion: 1`**.
Setting it to `1` fixed it.

`UgcVersion` is a **byte** at field offset `0x78`; getter `KKBFDGFLMMA.NBFPPLKCJMD` `0xD4C970` is
`movzx eax, byte ptr [rcx+0x78] ; ret`. That it is a format discriminator the client *filters* on is
corroborated by [inventions-v2-search](inventions-v2-search-wire-shape.md) taking an explicit **`ugcVersion` query param**.

**Omitting the key is the same bug**, because a missing byte deserializes to `0`. This is the worst
class of wire-shape fault in this codebase: valid JSON, no `IONCMJIACFI`, no `LLCLDPPAGIJ`, no NRE —
just an empty list.

### How it was found, in case another field behaves this way

Not by static tracing. The getter is **inlined with 0 call sites** and the filtering lives in
continuation lambdas inside generic-shared LINQ, so `callxref` yields nothing. One promising
`[rax+0x78]` read in `GLAKFFIIDPF.AGAJJIGKPHB` `0x7CE7E61` turned out to be on the current-room object
from `RecNet.Matchmaking.MLNNAKHOFCA`, **not** the Invention DTO.

What worked was **differential diffing of a working route against a broken one**: capture
`/v2/search` (renders) and `/v2/mine` (does not), diff the key sets, and discard every key that is
*absent* from the working payload — `/v2/search` omits `LatestVersionNumber`,
`ForceCannotPublish` and `IsRecRoomApproved` entirely and still renders, which clears all three. That
left exactly one key present in both with a different value.

Reach for that before more disassembly whenever two routes share a DTO and only one renders.

### `DisplayMetadataJson` decoded from the same diff

The working payload also populates `DisplayMetadataJson` where `/v2/mine` sent `null`, and its
contents are derivable — key `"0"` is `CurrentVersion.ChipsCost`:

| ChipsCost | DisplayMetadataJson |
|---|---|
| 0 | `{"0":0,"99":0}` |
| 28 | `{"0":28,"99":0}` |
| 47 | `{"0":47,"99":0}` |
| 104 | `{"0":104,"99":0}` |
| 320 | `{"0":320,"99":0}` |

Perfect correlation across ~90 rows. Emit `"{\"0\":<ChipsCost>,\"99\":0}"` as an **escaped string**
— it is a `string` field, not an object. `"99"` was `0` on every row, so its meaning is unknown.

## ⚠️ The path is a static field, which breaks the usual lookup

`mxref` on the `"api/inventions/v2/mine"` literal (slot `0xD135CD0`) returns **only
`GLAKFFIIDPF$$.cctor` `0x7CF0DF0`** — no request method at all. The cctor stores it into the facade's
static fields at **`+0x30`** (`mov qword ptr [rcx+0x30], rax` at `0x7CF11F0`), and the request method
reads it back:

```
0x7CE8997  mov rax, [rip+…]        ; GLAKFFIIDPF TypeInfo
0x7CE899E  mov rax, [rax+0x90]     ; -> static fields
0x7CE89AC  mov rsi, [rax+0x30]     ; <- the route string
0x7CE89C1  mov r9, rsi             ; passed as the path to AKJEAMCCEOH..ctor
```

**So `BFLLGGKGLLK` contains zero string literals** — `names.py` prints `0 literal reference(s)`,
which is exactly the signature of this pattern rather than a sign you have the wrong method.

How to find such a route's method, in order:
1. `mxref` the literal → lands in a `.cctor`; note the **static offset** it is stored to.
2. Scan `methodSpecs` for the plausible response `T` (here `List<KKBFDGFLMMA>`, spec **909049**),
   map the spec to its `.data` kind-6 slot, and `mxref` that → every method that sends that `T`.
3. Intersect with methods that read the static at that offset (`[typeinfo+0x90]` then `[+0x30]`).

That intersection gave exactly one candidate, and the `r9` assignment above confirms it directly.

Other `api/inventions/v2/*` literals are referenced from the same cctor, so **every route on this
facade is likely static-field-based** — expect the same dead end for `/v2/batch`,
`/v2/accessibility`, `/v2/cheer`, `/v2/delete`, `/v2/unpublish`, `/v2/update`, `/v2/updateprice`.

## Who consumes it

11 call sites, several unobfuscated, which is what confirms the route's purpose:

- `<FindInventions>d__2$$MoveNext` `0x135B8C0`
- `RecRoom.AGUI.ToolUIs.MakerPenPaletteMainScreen.GAGAFBKKJJH` `0xE7B2E0`
- `RecRoom.InventionLinkButtonTypeController.MMBCHPAMDLM` `0xDEC400`
- **`GPMLMCMPOLB.GAGAFBKKJJH`** `0x160B5C0` — the MakerPen palette controller

That last one matters: the palette's invention list is populated from this route, so a short or
inconsistent response here feeds straight into the palette UI. It is the same controller whose search
path can throw on desynced lists
([makerpen-palette-search-index-crash](../../../rr-client-bringup/references/makerpen-palette-search-index-crash.md)) — that crash is a client-side race
rather than a response-shape problem, but this is the route supplying its items.
