---
name: wire-shapes
description: Derive the exact JSON/wire shape the obfuscated Rec Room IL2CPP client expects for an HTTP endpoint, a websocket push notification, or a DTO — and diagnose stackless NREs caused by a wrong one. Use whenever the question is "what should my server send for X" or "why does the client NRE on this response".
---

# Deriving a client-expected wire shape

The self-hosted server has to emit exactly what the client's Utf8Json formatters expect. The client
is IL2CPP and obfuscated, so you cannot read this from decompiled managed code — you recover it from
the generated formatters in `GameAssembly.dll`.

**Check the catalog first.** `references/CATALOG.md` indexes every route already derived — grep it
for a path fragment and read the one file it names. `references/conventions/` holds the cross-cutting
rules (service enum, envelope tiers, the two exception types, the verb-dependent parameter trap).
`SCENES.md` in this repo has the scene-location GUID table. If the answer is there, stop.

**The client binary is the only evidence.** What a server currently sends is not evidence of what the
client accepts — a route can be wrong in production and still "work" because nothing reads the field.
Derive the shape from the formatters, then compare. When you derive something new, add a file under
`references/endpoints/` and a row to `CATALOG.md`.

## Which flow applies

| client | Il2CppDumper | flow |
| --- | --- | --- |
| pre-2025 builds | works | Tier B scripts, `out/{dump.cs,script.json,stringliteral.json}` |
| **`recflare-2025` (`20250718.01`)** | **impossible** | carve pipeline + Tier A scripts |

Il2CppDumper cannot process the 2025 build: the shipped `global-metadata.dat` is a 47,962,260-byte
decoy of repeated `0x52`, `.text`/`il2cpp` are encrypted at rest, `Il2CppCodeRegistration` is
field-permuted, and its PE-loader fallback dies because `GameAssembly.dll` imports Referee. Anything
in this file that names `dump.cs` or `script.json` is the pre-2025 flow.

## Setup (once per game build)

Tools are in **`tools/il2cpp/`** in this repo — `tools/il2cpp/README.md` has the tier split, the
per-script table and the gotchas. **Set `GAMEASSEMBLY`, `GA_IMAGE` and `GA_METADATA` explicitly**;
the in-script defaults are absolute paths from the machine the toolkit was written on and will
silently read whatever happens to be there. Run scripts from the directory holding `methods.pkl`
and `out/stringliteral.json`.

The generated indexes are **not** in the repo (build-specific and large) — `carve/` produces them.

For a carved build, run `carve/` first — `metadump.exe` (passive reader, start it before the game),
then `solve_header.py` → `idtables{,2,3}.py` → `rebuild_metadata.py` → `rebuild_binary.py` →
`mkindex2025.py`. That yields the decrypted `GameAssembly.dll`, a real `global-metadata.dat`,
`methods.pkl` and `out/stringliteral.json`.

> **A stale `methods.pkl` is worse than none.** Every address resolves to a plausible but wrong name,
> silently. Confirm `methods.pkl.txt` names the same `GameAssembly.dll` mtime and size as the client
> you're targeting. Fast anchor check on `20250718.01`: `0x77E0950` must resolve to
> `BestHTTP.HTTPManager$$SendRequest`.

> **Build-specific constants are baked into `slots2025.py`, `fields2025.py` and `mkindex2025.py`** —
> metadata table offsets, `METADATA_REGISTRATION_RAW`, `TD_N`, `LOAD_BASE`. A new client changes all
> of them; the `idtables*` stages print the replacements.

## Already derived

**[`references/CATALOG.md`](references/CATALOG.md)** — 112 routes, one file each, indexed by service
and path. Grep it before deriving anything. (`PROMPTS.md` at the repo root has ready-made openers for
looking one up, deriving a missing one, and checking a live capture against the client.)

### Cross-cutting rules

| Rule | What it settles |
|---|---|
| [elhkhfjehlm-verb-dependent-params](references/conventions/elhkhfjehlm-verb-dependent-params.md) | CORRECTION: MGPBDIAGCFD.ELHKHFJEHLM is NOT a query-param adder — it branches on the verb. GET puts params in the query string; every other verb puts them in an application/x-www-form-urlencoded BODY. |
| [ioncmjiacfi-malformed-response](references/conventions/ioncmjiacfi-malformed-response.md) | IONCMJIACFI 'Malformed Response' in recflare-2025 is thrown by MGPBDIAGCFD.KKEIDMPEHAL<T> when the body is empty or fails to deserialize into T — a '{}' body means the endpoint expects an ARRAY or a scalar, not an object. |
| [llcldppagij-envelope-failure-exception](references/conventions/llcldppagij-envelope-failure-exception.md) | LLCLDPPAGIJ is recflare-2025's generic 'RecNet envelope reported failure' exception — thrown only when an ENVELOPED response is null or Success==false, never by a bare-DTO endpoint. |
| [number-token-parsing-exception](references/conventions/number-token-parsing-exception.md) | Utf8Json NKJABNHBPCA "expected:'Number Token', actual:'['" is NOT IONCMJIACFI — it means T is a bare `long?`. Exactly two routes in 20250718.01 are: GET dormroom/me (Rooms) and GET api/progressionEvents/active (API). |
| [nonobject-response-routes](references/conventions/nonobject-response-routes.md) | The 145 routes whose response T is a List or scalar — i.e. every endpoint that hard-fails with `Malformed Response: '{}'`. Generated table at il2cpp-2025/nonobject-responses.txt, plus the scan that rebuilds it. |
| [recnet-service-enum](references/conventions/recnet-service-enum.md) | The full RecNet service enum NNPMGHNBFMD for build 20250718.01 — 31 unobfuscated member names with values (Auth 1, API 2, Lists 13, Rooms 16, Econ 28 …); the number every wire-shape note calls 'svc N'. |

Two exception types are worth recognising on sight: `IONCMJIACFI` ("Malformed Response") means the
body would not deserialize into `T` — a `{}` body against a `List` or scalar `T` is the classic case,
and `nonobject-response-routes` is the candidate list. `LLCLDPPAGIJ` means an **enveloped** response
was null or `Success == false`, so a bare-DTO endpoint can never raise it.

## HTTP endpoint → response shape

1. **Find the endpoint literal.** `grep -in "<path fragment>" out/stringliteral.json`.
   Paths are often **assembled from more than one literal** — `rooms/{id}/experience` exists only as
   `"{0}/{1}/experience"` plus a separate `"rooms"`, and `algorithmiclists/HotList` as
   `"algorithmiclists/"` plus a caller-supplied name. Grep the distinctive *fragment*, not the URL.
2. **Find the method holding it.** `py mxref.py <slot_rva>` (carved build) or `py fxref.py`.
   `py callxref.py <method_rva>` walks outward to callers — direct `E8`/`E9` only.
3. **Confirm the method and read its params.** `py names.py <method_rva> 400` prints the URL literal
   and the query/form parameter names in order. Query params are frequently added in a **separate
   closure**, not the method itself — chase the `MethodDef` slot that `slots2025.py` shows.
4. **Get the response type.** For an async method, read it straight off the state machine's
   `AsyncTaskMethodBuilder<T>` in the Cpp2IL dump — that is the deserialize target, full stop.
   Otherwise `py slots2025.py <method_rva> 400` and resolve the send call's generic instantiation.

   | 2025 method on `MGPBDIAGCFD` | meaning |
   | --- | --- |
   | `HPBKMCLEANE<TResponse>` | send, response required |
   | `CJBFDPLCIEJ<TResponse>(bool)` | send, nullable response |
   | `CNDMDLNHDLI` | send, no response — **body ignored entirely** |
   | `KBIHOFDDIMI` | raw response |
   | `ELKIBCPINAP(byte[])` | sets the **request body** — its presence means there is one |
   | `ELHKHFJEHLM(name, value)` | adds a parameter — **query string on GET, form body on every other verb**. See `references/conventions/elhkhfjehlm-verb-dependent-params.md`; reading this as "query param" silently mis-specifies every non-GET route |

   API classes also expose a class-bound `LMKONLJOAEP<T>` wrapper that does the same thing.
   *(Pre-2025 names for the same roles: `BGBHKBJEMPI.OGJBBIDJGFI` / `DDKPNIIFDNB` / `ONDBGFGJBDE` /
   `MEKOIMDCOFB`.)*
5. **Dump the shape.** Find the DTO's Utf8Json formatter — `grep -n "IHCMHKGLBEA<TDto>" *.cs` in the
   Cpp2IL dump — and run `py names.py <formatter_ctor_rva> 900`. Cross-check with
   `py fields2025.py <TypeName>`. See *Reading formatter output* below.
   *(`dtoshape.py` does both at once but needs `dump.cs`, so it is pre-2025 only.)*
6. **Check for an envelope.** Read the type argument; do not assume.

**Resolve a generic call's real type argument from the methodSpec's generic inst**
(`MetadataRegistration` `_mr[2]`/`_mr[3]`), never from a nearby `TypeInfo` slot — they can name
different types in the same method. That is how `JsonUtility.FromJson<T>` on a discovery section was
pinned to `StorePageDiscoveryDisplayMetadata` when the adjacent slot said otherwise.

### Envelopes (2025 names)

| type | body |
| --- | --- |
| *(none)* | bare object or array — **common**, e.g. `curatedlists/bulk`, `rooms/contributedby/me` |
| `JFNAKFCGDAO` | `{Success, Error, error_id}` — no value; typical for writes |
| `KGOJLHJNIOD<T>` | adds `Value` — single object |
| `GJAFHDAFBNE<T>` | adds `Value` — list |

Envelope status is **per-helper, not per-facade** — the same API class exposes both bare and enveloped
helpers. The tell is a leading `friendlyActionDescription` string on the helper: present means
enveloped, absent means bare. `references/endpoints/rooms-showcase-wire-shape.md` records how
assuming otherwise went wrong.

`error_id` is lowercase (`[DataMember]`); `Success`/`Error`/`Value` are PascalCase. Which tier
applies is **per-endpoint and not inferable from the path or from a sibling endpoint**.

Bodies are not always objects: `thread/checkCanSendDirectMessageWithPrivacySetting` deserializes
into a plain enum, so the entire body is a **bare integer**.

### Verb and service

From the `AKJEAMCCEOH..ctor(HttpMethod, service, path)` call site: `r8d` is the service enum, and
the `HttpMethod` comes from `[klass+0x90]` (static fields) at a fixed offset —

`0x00` Delete · `0x08` **Get** · `0x10` Head · `0x18` Options · `0x20` **Post** · `0x28` **Put** · `0x30` Trace

`py rangedis.py <start> <end>` to read both. **Verify the verb, never infer it from the path** —
`outfits/me` and `rooms/{id}/experience` each serve two verbs with completely different responses.

Service enum `NNPMGHNBFMD` on `20250718.01`: 0 AI, 1 Auth, 2 API, 3 Commerce, 4 Matchmaking,
5 Notifications, 6 Images, 7 CDN, 8 Storage, 9 Chat, 10 Leaderboard, 11 Accounts, 12 Link, 13 Lists,
14 RoomComments, 15 Clubs, 16 Rooms, 17 PlatformNotifications, 18 Moderation, 19 DataCollection,
20 BugReporting, 21 Discovery, 22 PlayerSettings, 23 Studio, 24 GameLogs, 25 Strings, 26 StringsCDN,
27 WWW, 28 Econ, 29 Data. **Pre-2025 builds are shifted** (Rooms 14, Econ 26) — re-read the enum per
build. The service picks the subdomain, and it is not always the obvious one: `privileges/*` is on
Auth, not Accounts or API.

## Websocket notification → payload shape

`py regall.py` prints every subscription: channel key, payload DTO, handler. Then
`py dtoshape.py <PayloadType>`. The frame is `{"id": "<key>", "msg": {…}}` with `id` a **string**
even for numeric channels. The current table is `apps/notify/src/notification-types.ts` in the
server repo.

`regall.py` scans both `call rel32` and `jmp rel32` — the last registration in a method is usually
compiled as a **tail jump**, and missing those hid 26 of 68 subscriptions on the first pass.

An id with **no subscriber is silently dropped** — no log, no error. Always confirm the id is live
before debugging the server side.

> `regall.py` and `dtoshape.py` are Tier B (they need `script.json`/`dump.cs`) and do **not** run on
> a carved build. There, find the registration method by hand and read it with `slots2025.py`.

## Reading formatter output

The formatter `.ctor` builds `____keyMapping` (every accepted casing) and then `____stringByteKeys`
(one entry per serialized member, declaration order). In `names.py` output the trailing run with no
repeated casing **is** the shape; the earlier interleaved block is `____keyMapping`.

Pair keys to members by **position and type, not by name.** The obfuscator does not preserve the
`<prop>k__BackingField` convention, so Cpp2IL property names and metadata backing-field names
disagree. `py fields2025.py <TypeName>` gives fields with runtime offsets — matching the key count
and the type sequence against it is the real check, and it exposes members that carry no key.

- **Utf8Json accepts three casings** for each key — Original, camelCase, all-lowercase.
- **`[DataMember]` renames.** `BalanceType` goes on the wire as `Platform`. The formatter is the
  authority, never the C# name. A rename landing on the expected index also *confirms* the pairing.
- **`[IgnoreDataMember]` members never appear on the wire** but still have backing fields — that is
  why a type can have 17 fields and 15 keys.
- **Computed properties have no backing field and no key.**
- **Unknown members are dropped silently** — a typo'd key behaves exactly like an omitted one.
- **Inherited DTOs emit derived-class members before base members.**
- **Enums go on the wire as numbers**, unless a by-name formatter exists — and if one did, every
  member name would be a string literal. Grep a few distinctive member names against
  `stringliteral.json`; absent means numeric.
- **`Obscured*` (CodeStage anti-cheat) fields are plain numbers/bools on the wire.** No formatter
  exists for them; the generated code reads a primitive and relies on the implicit conversion.
- **`Nullable<T>` marks the optional fields** — the smallest, highest-yield list, because those are
  exactly the ones whose absence changes client behaviour.

## When a route 200s but the client shows nothing

No exception, no log, no failed request — just an empty list or a missing row. The body parsed fine,
so none of the exception types above fire. **A value the client silently filters on is wrong.**

Do not start with disassembly. Inlined getters have zero call sites and the filtering usually lives
in continuation lambdas inside generic-shared LINQ, so `callxref` returns nothing and nearby
field-offset reads mislead (a `[rax+0x78]` read in the inventions facade turned out to be on the
current *room* object, not the DTO).

**Diff a working route against the broken one instead.** Two routes often share a DTO while only one
renders:

1. Capture both payloads.
2. Diff the key sets and values.
3. **Discard every key that is absent from the working payload** — if the client renders without it,
   it cannot be the gate. This is what does the real pruning.
4. What remains is present in both with a different value. That is your candidate; it is usually a
   single field, and a one-line server change tests it.

Worked example: `inventions/v2/mine` returned a valid 28-key payload and rendered nothing while
`/v2/search` was fine. Step 3 cleared `LatestVersionNumber`, `ForceCannotPublish` and
`IsRecRoomApproved` (all absent from `/v2/search`), leaving **`UgcVersion` 0 vs 1** — confirmed as the
cause. See [inventions-v2-mine](references/endpoints/inventions-v2-mine-wire-shape.md).

⚠️ **An omitted key is indistinguishable from a wrong one here**, because a missing number
deserializes to `0`. Enumerate the keys the formatter declares and send all of them.

## Diagnosing a stackless NRE from a response

1. Get the throwing method's RVA (`py whatis2025.py <rva> --dump <cpp2il_dir>`, or the obfuscated
   name from the log).
2. `py rangedis.py` it — these are usually tiny. Look for a chained dereference with no null guard.
3. Check the DTO's post-deserialize hook — the `CPOBHIECLEN` virtual on types deriving `PDDMBELEHHJ`.
   **`0xA60520` is the shared no-op stub on `20250718.01`** (`0x6F84D0` on the older build).
   A different RVA is *not* proof of validation: `MIBODHPEFHP.CPOBHIECLEN` at `0xFEA4F0` is its own
   `nop; ret`. **Disassemble it** — real hooks are short and obvious, and often throw with a literal
   message you can grep, e.g. `"Matchmaking response has no RoomInstance field"`.
4. The fix is nearly always "send the nested object, even as a stub with non-matching ids" rather
   than omitting it. Known hard requirements: matchmaking needs `RoomInstance` whenever
   `ErrorCode == 0`; `settings/partyinvite` must not return `null` (the continuation dereferences it
   unguarded, the throw is swallowed, and every party invite then reads as expired).

## Traps that have cost real time here

- **This client strips `IMAGE_SCN_MEM_EXECUTE`** — code sections are `0xC0000020`, exec is granted at
  runtime. Any tool filtering sections on `MEM_EXECUTE` matches nothing and reports **0 refs for
  every target, silently**. `fxref.py` had exactly this bug.
- **Metadata-usage slots live in the on-disk `.data` only.** Generated code reaches literals through
  globals initialised to `(kind << 29) | (index * 2 + 1)`; the runtime overwrites them with real
  pointers. Read `.data`/`.rdata` from the **disk** PE, code from `ga_image.bin`.
- **Generic-shared code has one RVA per shape, not per instantiation.** A disassembler labels the
  call with whichever instantiation it saw first — usually the wrong DTO. The methodSpec slot at the
  call site is authoritative; that is what `slots2025.py` and `regall.py` read.
- **Enum constants often arrive as `lea ecx, [r8 + N]`,** not `mov ecx, N` — the register is zeroed
  and the constant folded into the displacement. A scanner matching only `mov` reports "not found".
- **Capstone desyncs.** A linear sweep from an arbitrary offset decodes garbage. Start from a known
  method boundary and bound the window by the next method start.
- **Attribute a call to the right method.** A window that overruns picks up the *next* method's
  calls — `names.py <rva> 1000` reads 0x1000 bytes and will cross into the next function.
- **Direct calls only.** These scripts scan `call rel32`; virtual and interface dispatch is invisible.
  An empty result means "not found by this method", not "does not exist".

## What survives a client upgrade

Enum member names *and values*, compiler-generated names (`<Method>b__0`, `<field>5__2`), Utf8Json key
literals, `[DataMember]` renames, and named string channels. **Everything else re-rolls** — every
`ABCDEFGHIJK` type/method name, every RVA, and every metadata table offset. Re-derive from signatures
and literals; never carry an obfuscated name across a build.

Obfuscated names *are* stable **within** a build and recur across DTOs — `ANKPNEKDDOB` is `RoomId`
in several unrelated types at once — which makes them a useful cross-check while you work, and
worthless the moment the client updates.
