# Api sanitize/v1 wire shape (the text purifier)

> POST api/sanitize/v1 (svc 2 API) sends a JSON body `.PurifyStringRequest`
> `{Value, ReplacementChar, Context, Intent, ruleset, PreRemoveBlockedCharacters}` and the response is
> a **BARE JSON STRING** — the purified text, nothing else. `{}` or an object throws `IONCMJIACFI`.
> The sibling POST api/sanitize/v1/isPure is the opposite: a BARE OBJECT with one key, `{"IsPure": true}`.
> This route is on the outgoing-chat path (`ChatThreadModel.TrySendTextMessage`), so getting it wrong
> breaks sending messages, not just display.

Derived **2026-10-05** from build `20250718.01`.
Facade **`.BDKFIHAHJPI`** (7 methods). Already listed in
[nonobject-response-routes](../conventions/nonobject-response-routes.md) as one of the `string`-typed routes —
this note is the full derivation behind that row.

Both routes are **POST**, service **2 = API** (`mov r8d, 2` at `0x7DA9599`), verb from the
`HttpMethod` static `[rcx+0x20]` at `0x7DA9576`.

| route | verb | entry | body `T` | response `T` |
|---|---|---|---|---|
| `api/sanitize/v1` | POST | `BDKFIHAHJPI.CIJIMPANKCL` `0x7DA9340` | inst #14970 = **`.PurifyStringRequest`** | inst #309 = **`string`** (bare) |
| `api/sanitize/v1/isPure` | POST | `BDKFIHAHJPI.AGHDIHBEAME` `0x7DA91A0` → `LMJHJFPBBFA.MoveNext` `0x7DB7E10` | inst #14969 = **`.IsStringPureRequest`** | inst #1378 = **`.IMKFJOLJOKL`** (1-key object) |

Both send with `MGPBDIAGCFD.HPBKMCLEANE<T>` — **response required** — and set the body with
`MGPBDIAGCFD.ELKIBCPINAP`, so this is a real **JSON** body, not form-urlencoded. There are **no
`ELHKHFJEHLM` calls on either route**: nothing goes in the query string.

⚠️ **Three of the six request-DTO type names are unobfuscated** — `.PurifyStringRequest`,
`.IsStringPureRequest`, and the class `StringSanitization` (literal `0xD20C5D0`). The obfuscator
missed them, so `msig.py` / `ftypes.py` read like source. Always try `ftypes.py` on a `TypeInfo` slot
whose name looks like English before reaching for key-literal intersection.

## Request body — `.PurifyStringRequest`, 6 keys

Formatter **`FOELGGEEOAK` `.ctor 0x76932E0`** (+0x770). The `____stringByteKeys` run is
`0x76937E2`..`0x7693965` — 6 keys, 1:1 with the 6 declared fields in declaration order:

| # | key | CLR | notes |
|---|---|---|---|
| 1 | `Value` | string | the text to purify |
| 2 | `ReplacementChar` | **`char`** | what masked characters become |
| 3 | `Context` | string | free-form caller tag |
| 4 | `Intent` | enum `.NJPGIIKLKAI` (int) | `Unspecified 0`, `Creation 1`, `Consumption 2` |
| 5 | **`ruleset`** | enum `.ILBPHHLHJLG` (int) | `Default 0`, `MoreRestrictive 1` |
| 6 | `PreRemoveBlockedCharacters` | bool | |

```json
{ "Value": "some user text", "ReplacementChar": "*", "Context": "chat",
  "Intent": 2, "ruleset": 0, "PreRemoveBlockedCharacters": false }
```

⚠️ **`ruleset` is lowercase.** It is the only lowercase key of the six — the CLR field is genuinely
named `ruleset`, not a `[DataMember]` rename, and the emitted key follows it. The deserialize
automata also accepts `Ruleset` and `ruleset`, but a server matching keys case-sensitively against a
PascalCase model will silently read `ruleset` as `Default`, which is the permissive value — so a
`MoreRestrictive` request would be honoured as `Default` and nothing would look broken.

`ReplacementChar` is a CLR `char`; Utf8Json's built-in char formatter writes it as a **one-character
JSON string** (`"*"`). That is standard Utf8Json behaviour rather than something byte-confirmed in
this build, so accept both `"*"` and a numeric code point if your deserializer is strict.

Both enums are plain integers on the wire — `Intent` and `ruleset` are `int`-backed, not byte.

## Response — a BARE JSON STRING

`HPBKMCLEANE<T>` with inst **#309 = `string`**. The entire body is one JSON string literal:

```json
"some user t**t"
```

- **Not** `{"Value": "..."}`, not `{"Result": "..."}`, not an envelope. An object body throws
  `IONCMJIACFI` ([ioncmjiacfi-malformed-response](../conventions/ioncmjiacfi-malformed-response.md)) — this route is one of the
  145 rows in [nonobject-response-routes](../conventions/nonobject-response-routes.md), and the stack trace will not name it.
- `""` is valid JSON and parses fine; `null` parses to a null string.
- A `204` / empty body throws, because the helper is the **required**-response tier.

The method's declared return type is `KPIPLFECKNC<.CAMCIOJELMK>` where `.CAMCIOJELMK` is
`{bool GAACBHPEJKO, string HLCOMEMBLJE}` — a **local** result wrapper the client builds around the
deserialized string. It is **not** a wire type; do not emit it.

## `api/sanitize/v1/isPure` — bare object, one key

Body `.IsStringPureRequest`, 4 fields — the same shape minus `ReplacementChar` and
`PreRemoveBlockedCharacters`:

| key | CLR |
|---|---|
| `Value` | string |
| `Context` | string |
| `Intent` | `.NJPGIIKLKAI` |
| `ruleset` | `.ILBPHHLHJLG` |

Response `.IMKFJOLJOKL` — formatter **`APGOCHNBJIJ` `.ctor 0x768BBC0`** (+0x220), run `0x768BD58`,
exactly one key:

```json
{ "IsPure": true }
```

Its single field is an obfuscated auto-property (`<PLLKLOAHECD>k__BackingField`), so the key name
came from xrefing the `IsPure` literal `0xD20F7D0` into the formatter `.ctor` — the field name is no
guide here. All three casings exist (`IsPure` / `isPure` / `ispure`).

⚠️ **The two routes are opposite tiers.** `sanitize/v1` is a bare scalar, `sanitize/v1/isPure` is a
bare object. Serving `{"Value": "..."}` for the first or a bare `true` for the second both throw. A
shared "sanitize" handler that returns one shape for both paths is the easy mistake.

The isPure path runs through **`.CBACIMLIBPF`** (TypeInfo at `0x7DB8007`), the shared serialized
request queue — so a sanitize response that never arrives stalls unrelated requests behind it
([serialized-request-queue-stall](../../../rr-client-bringup/references/serialized-request-queue-stall.md)).

## Why this route is load-bearing

`CIJIMPANKCL` has **11 call sites** and `AGHDIHBEAME` has **50**. The unobfuscated ones say what
breaks:

| caller | what breaks if sanitize fails |
|---|---|
| `RRUI.Data.ChatThreadModel.TrySendTextMessage` `0x2577610` | **sending a chat message** |
| `<TryUpdatePreferredName>d__29.MoveNext` `0x13C6740` | changing display name |
| `RecRoom.RoomNotificationsManager.ScheduleRoomNotification` `0xDD2B80` | room notifications |
| `RecRoom.CircuitsV2.CircuitsV2Manager.RpcSendMajorNotification` `0x10986D0` | circuit-driven notifications |
| `RecRoom.Players.PlayerInteractable.set_InteractionPrompt` `0x142F2C0` (isPure) | interaction prompt text |
| `RecRoom.Tools.RoomDoor.KBBHNDOFICL` / `RoomDoorV2.OFHGNIBBGIH` (isPure) | door label text |
| `SandboxSceneSpawnPointSpawner`, `SandboxSpectatorStreamPoint` (isPure) | spawn-point / stream-point names |

So a 404 or 500 here is not a cosmetic failure — it sits in front of every user-authored string the
client transmits or renders. **The simplest correct server is an identity purifier**: echo
`Value` back as a bare JSON string, and return `{"IsPure": true}` from `isPure`.

The failure path logs the literal **`'Error purifying string'`** (referenced at `0x7DA9463` and
`0x7DA9857`) from inside a catch in `CIJIMPANKCL`. **What the client falls back to on that path was
not traced** — whether it substitutes the original string or an empty one is unresolved, so do not
rely on a failed sanitize degrading gracefully.

## Two short-circuits before the request

`CIJIMPANKCL` does not always hit the network:

1. `String.IsNullOrWhiteSpace` at `0x7DA94C9` — blank input returns without a request.
2. `JNNLABIDEOO<string, string>.TryGetValue` at `0x7DA9508` — a **local memo cache** keyed by the
   input string (inst #265 = `<string, string>`), with `BDKFIHAHJPI.NJKPJELHHIJ` `0x7DA9B60` and
   `.NBMGOOMFHHF` `0x7DA9AC0` as its clear/populate helpers.

Practical consequence: **the same text is only sanitized once per session**, so you cannot test a
server-side change by retyping the same message — change the text or restart the client. A capture
that shows no request for a string you just typed is the cache, not a client bug.
