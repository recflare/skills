# Versioncheck islandedversions wire shape

> GET api/versioncheck/islandedversions (svc 2 API) returns a BARE JSON ARRAY OF STRINGS; it is a named boot step, and a null body caches null so the later Contains() check throws — return [] for empty, never null.

Derived **2026-09-01** from build `20250718.01` via [recflare-2025-metadata-carve](../../../il2cpp-analysis/references/recflare-2025-metadata-carve.md).

`GET https://api.<host>/api/versioncheck/islandedversions` — service **2 = API**
([recnet-service-enum](../conventions/recnet-service-enum.md)), verb **GET** (`HttpMethod` statics `+0x08`, read at `0x7DB6044`;
`mov r8d, 2` at `0x7DB6069`). Literal `0xD1577A0`. **No query params, no body** — neither
`ELHKHFJEHLM` nor `ELKIBCPINAP` appears anywhere in the method.

Client entry `KDEJBAHIGMF.JEKABGBDPDL()` **`0x7DB5F60`** → `JCFICNGFDLA` (the valueless promise), so
the caller never sees the payload; the `.Then` lambda caches it instead. Instance facade
`IGEDDFKHALJ` `0x7DB3A10` forwards to it. The sibling `KDEJBAHIGMF.GMBEMGIBLEI()` `0x7DB5A90` is
`api/versioncheck/v4` (`0xD157B38`), a different shape.

## Response — BARE JSON array of strings

Send generic `MGPBDIAGCFD.HPBKMCLEANE<List<string>>` (generic inst **1028** = `List<string>`).
No envelope, no DTO, therefore **no `CPOBHIECLEN` validation hook at all**.
Independently confirmed at line 95 of `il2cpp-2025/nonobject-responses.txt`
([nonobject-response-routes](../conventions/nonobject-response-routes.md)) — so `{}` here is a `IONCMJIACFI: Malformed Response`
([ioncmjiacfi-malformed-response](../conventions/ioncmjiacfi-malformed-response.md)), because Utf8Json wants `[`.

```json
["20250718.01", "20250612.03"]
```

## The null trap

`<>c.GBNBDAGNCLA(List<string>)` **`0x7DC1040`** stores the deserialised list **verbatim** into the
static `KDEJBAHIGMF.MMKOMCIKHNP` (statics `+0x08`) — no null check, no validation, nothing else.

`KDEJBAHIGMF.BAOMMMGIKMF(string version)` **`0x7DB59A0`** then:
- static is null → **throws `Exception("Islanded versions must be cached first")`** (`0xD226448`)
- otherwise tail-jumps into `List<string>.Contains(version)`

So a JSON `null` body deserialises fine, caches `null`, and detonates later at the first membership
check — a delayed failure far from the request. **`[]` is the correct empty answer, never `null`.**

## It is a boot step

`'VersionCheck.CacheIslandedVersions'` (`0xD058508`) is a named boot step — 22 refs, paired with
`'VersionCheck.VerifyGameVersion'` (`0xD0588A8`) across the boot state machines
(`GNICNPCBEOB$$MoveNext` `0xC21820`, `MMOHFFEFLPK$$MoveNext` `0x1020D20`, and 9 more). This request
therefore runs during boot, and a rejection stalls that step rather than surfacing anywhere useful.

**How to apply:** serve `[]` unless you actually run multiple client builds; the strings are client
version identifiers of the [two-client-builds-name-check](../../../il2cpp-analysis/references/two-client-builds-name-check.md) `20250718.01` form, matched by exact
`Contains`.
