# Studio `cloud-builds/*` wire shapes (and how to read the Studio tool at all)

> `GET studio.<host>/cloud-builds/get-build-count-for-user?startTime=<ISO8601>` returns the
> **ENVELOPED** `{Value: <UserBuildCountDTO>, Success: bool, Error: string}`.
> `UserBuildCountDTO` is 7 PascalCase keys: `AccountId`, `StartTime`, `EndTime`,
> `SubRoomTotalBuildCount`, `SubRoomFailedBuildCount`, `AvatarItemTotalBuildCount`,
> `AvatarItemFailedBuildCount`.
> **Every** Studio cloud-build call is enveloped the same way, and the envelope has **no `error_id`** —
> it is `RecRoom.Core.Studio.RecNet.Result<T>`, not the game client's `KGOJLHJNIOD`.

Derived **2026-10-08** from **RecFlare Studio V2.0.0**, not the game client.

## ⚠️ Studio is MANAGED .NET — do not use the IL2CPP toolkit on it

Rec Room Studio is a **Unity Editor project**, so its code ships as ordinary managed assemblies.
Nothing in `il2cpp-2025/` applies and none of it is needed.

The code for this route lives in

```
S:\RecRoom\RecFlare Studio V2.0.0\RecFlare Studio V2.0.0\
  Library\PackageCache\com.recroom.studio.build@<hash>\Editor\RecRoom.Studio.Editor.Core.dll
```

`Library/PackageCache/com.recroom.*` holds every Rec Room package Unity has extracted (the
`RecRoomStudioPackages/*.tgz` tarballs are the sources of those). `Library/ScriptAssemblies/` holds
the project's own compiled assemblies.

### Finding which assembly owns a route

Grep the DLLs for the path as **UTF-16LE** — managed string literals live in the `#US` heap as
UTF-16, so a plain byte grep for ASCII misses them:

```python
needles = [b"cloud-builds", "cloud-builds".encode("utf-16le")]
```

One hit: `RecRoom.Studio.Editor.Core.dll`.

### Reading it: PowerShell reflection, no extra tooling

```powershell
$a = [System.Reflection.Assembly]::ReflectionOnlyLoadFrom($dll)
try { $t = $a.GetTypes() }
catch [System.Reflection.ReflectionTypeLoadException] { $t = $_.Exception.Types | ? { $_ -ne $null } }
```

`ReflectionOnlyLoadFrom` executes nothing. `GetTypes()` throws `ReflectionTypeLoadException` because
UnityEditor and `RecRoom.Studio.Common.Base.Runtime` are not preloaded — **catch it and use
`Exception.Types`**, which still yields most types. Individual `GetParameters()` calls on methods
whose parameters live in an unresolved assembly will throw; skip those and keep going.

⚠️ **Mixed obfuscation.** The **DTOs keep their real names** (`UserBuildCountDTO`, `CloudBuildDTO`,
`Result<T>`) because System.Text.Json serializes by name, while the **service classes are obfuscated**
(`OJHIOKLBMIC`, `KAHOAAGKPCK`, `OCOOLHLEDHD`) — the opposite emphasis from the client, where
everything is obfuscated. So you get exact wire shapes for free and only have to work to identify
which method is which route.

### The trick for bare-vs-enveloped

Reflection cannot read method bodies, so the declared return type does **not** tell you the wire
type — `PCLBLLJDLIO` returns `Task<UserBuildCountDTO>` while the wire is `Result<UserBuildCountDTO>`.
**Read the async state machine's fields instead:**

```
OJHIOKLBMIC+ECBEJINBCOE
  <>t__builder : AsyncTaskMethodBuilder<UserBuildCountDTO>          <- what the method returns
  <>u__1       : TaskAwaiter<Result<UserBuildCountDTO>>             <- what it DESERIALIZED
```

`<>u__N` awaiter field types are the deserialize targets. This is the managed equivalent of reading
a send helper's generic instantiation.

## The envelope — `RecRoom.Core.Studio.RecNet.Result<T>`

| # | key | CLR |
|---|---|---|
| 1 | `Value` | `T` |
| 2 | `Success` | bool |
| 3 | `Error` | string |

and the valueless `RecRoom.Core.Studio.RecNet.Result` = `{Success, Error}`.

⚠️ **No `error_id`.** The game client's RecNet envelopes (`JFNAKFCGDAO`, `KGOJLHJNIOD<T>`) carry a
lowercase `error_id` as a third/fourth key; the **Studio** envelope does not. Do not share an
envelope serializer between the two surfaces.

⚠️ **Property order is `Value`, `Success`, `Error`** and there are **no `[JsonPropertyName]`
attributes** on any of it.

### Casing is exact PascalCase

The serializer is **System.Text.Json**. Across every `com.recroom.*` assembly in the install, the only
files that even reference `PropertyNamingPolicy` / `PropertyNameCaseInsensitive` / `CamelCase` are
`System.Text.Json.dll` itself and SignalR's JSON protocol — **no Rec Room assembly sets either**. The
only `JsonSerializerOptions` setters `RecRoom.Studio.Editor.Core.dll` references are
`set_DefaultIgnoreCondition` and `set_IncludeFields`.

So: **keys must match the declared PascalCase names exactly.** camelCase will not bind, because
System.Text.Json is case-sensitive by default. (`IncludeFields = true` means public *fields* would
serialize too, but every DTO here uses properties, so it has no effect.
`DefaultIgnoreCondition` only affects writing.)

Note the contrast with the **query string**, which *is* camelCase — `startTime` is an explicit
string literal in the assembly, as are `cloudBuildId` and `creatorAccountId`.

## `GET cloud-builds/get-build-count-for-user?startTime=`

Client method `PCLBLLJDLIO(DateTime startTime, CancellationToken)`, state machine
`OJHIOKLBMIC+ECBEJINBCOE`. The one query param is `startTime`, an ISO-8601 instant
(`2026-10-08T18:26:56.2295073Z`).

### `UserBuildCountDTO` — 7 keys

`RecRoom.Core.Studio.RecNet.UserBuildCountDTO`:

| # | key | CLR |
|---|---|---|
| 1 | `AccountId` | `Int32` |
| 2 | `StartTime` | **`DateTimeOffset`** |
| 3 | `EndTime` | **`DateTimeOffset`** |
| 4 | `SubRoomTotalBuildCount` | `Int32` |
| 5 | `SubRoomFailedBuildCount` | `Int32` |
| 6 | `AvatarItemTotalBuildCount` | `Int32` |
| 7 | `AvatarItemFailedBuildCount` | `Int32` |

```json
{ "Value": { "AccountId": 2,
             "StartTime": "2026-10-08T18:26:56.2295073Z",
             "EndTime":   "2026-10-08T19:26:56.2295073Z",
             "SubRoomTotalBuildCount": 3,
             "SubRoomFailedBuildCount": 0,
             "AvatarItemTotalBuildCount": 0,
             "AvatarItemFailedBuildCount": 0 },
  "Success": true, "Error": null }
```

⚠️ **`StartTime` and `EndTime` are non-nullable `DateTimeOffset`** — a JSON `null` **throws**
(`JsonException`), unlike a missing key, which leaves `DateTimeOffset.MinValue`
(`0001-01-01T00:00:00+00:00`). Emit a real ISO-8601 instant or omit the key; never `null`.
The four counts are plain `Int32`, so `null` throws there too; omit them to mean 0.

Echoing the request's `startTime` back as `StartTime`, with `EndTime` = the end of the throttle
window, is the natural implementation.

## The rest of the `cloud-builds` family

Route literals in the assembly (all UTF-16):

```
cloud-builds
cloud-builds/create
cloud-builds/cancel
cloud-builds/for-room
cloud-builds/custom-avatar-item/{0}
cloud-builds/custom-avatar-item/{0}/save/{1}
cloud-builds/get-rate-limit-config
cloud-builds/get-build-count-for-user
```

Service `OJHIOKLBMIC` (impl; `KAHOAAGKPCK` mirrors it), with the deserialize target read from each
state machine — **all enveloped**:

| method | returns | wire `T` |
|---|---|---|
| `FFGAFBPGKOJ(string cloudBuildId, ct)` | `CloudBuildDTO` | `Result<CloudBuildDTO>` |
| `MPMJKCGEIGN(Guid, long, bool, string, ct)` | `CloudBuildDTO` | `Result<CloudBuildDTO>` |
| `BNPGEECINBF(long, long, int skip, int take, ct)` | `PagedResultsDTO<CloudBuildDTO>` | `Result<PagedResultsDTO<CloudBuildDTO>>` |
| `CHFMEILHFOC(Guid, int, int, ct)` | `PagedResultsDTO<CloudBuildDTO>` | `Result<PagedResultsDTO<CloudBuildDTO>>` |
| `ACAMICGEPMJ(string cloudBuildId, ct)` | `Task` (no value) | **`Result`** (valueless) |
| `NEKLALEIGGI(long, long, ct)` | `List<int>` | `Result<List<int>>` |
| `PCLBLLJDLIO(DateTime, ct)` | `UserBuildCountDTO` | `Result<UserBuildCountDTO>` |
| `ALGHIKPJOGC(ct)` | `CloudBuildRateLimitConfigDTO` | `Result<CloudBuildRateLimitConfigDTO>` |
| (remote run) | `RemoteRunDTO` | `Result<RemoteRunDTO>` |

Two more DTOs that come free:

**`CloudBuildDTO`** — `CloudBuildId` (string), `StartedAt` (DateTime), `CompletedAt`
(`DateTime?` — nullable, so `null` is legal here), `Error` (string), `UnityAssetId` (Guid),
`CreatedByAccountId` (Int32).

**`CloudBuildRateLimitConfigDTO`** — `BuildThrottleIntervalHours`, `WarnAfterBuildsPerInterval`,
`MaxBuildsPerInterval`, all `Int32`. This is the companion to the build count: the count route says
how many builds happened since `startTime`, this one says the ceiling.

Verb was not read from IL; `GET` follows from the query-string form of the request and the
`DateTime`-only parameter.
