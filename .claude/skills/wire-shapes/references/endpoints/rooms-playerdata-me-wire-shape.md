# Rooms playerdata/me wire shape

> GET rooms/{roomId}/playerdata/me (svc 16 Rooms) takes NO params and returns a BARE single-key object {"Data": "<string>"} — an opaque string blob, not nested JSON. The PUT on the same path takes one form-urlencoded field `data` and DISCARDS its response body entirely (non-generic Task; the lambda status-checks and disposes the response unread), so any 2xx accepts - CORRECTED 2026-10-15, it is NOT enveloped.

Derived **2026-10-01** from build `20250718.01`.
The bare-vs-enveloped split here is the cleanest example of the rule in
[rooms-isbanned](rooms-isbanned-wire-shape.md): **one path, two verbs, two different response tiers**, decided by which
helper the entry method calls.

`GET https://rooms.<host>/rooms/{roomId}/playerdata/me` — service **16 = Rooms** (facade
`OALMDGJKBJH`), verb **GET** (`HttpMethod` statics `[rcx+8]` at `0x7DF2078`).

Path is `String.Format("rooms/{0}/playerdata/me", roomId)` — literal slot **`0xD1A3390`**; the room id
is a **path segment**. **No params, no body.** There is no `playerdata/{accountId}` variant anywhere in
the build — `me` is the only form.

The GET lives in the async state machine **`KPMFJJJDHBL$$MoveNext`** `0x7DF1F50`.

## Response — BARE, one key

Send helper is **`OALMDGJKBJH.NDBMFFLDBBK<T>`** — one of the Rooms facade's two **description-less
(bare)** helpers, so there is no envelope. Generic inst **#2782** = **`.ADDGAOJJHIL`** (typedef
#23121), formatter `CMABAAMGFLP` `.ctor 0x7766B10`, **1 key** for its 1 declared field:

| # | key | CLR | off |
|---|---|---|---|
| 1 | `Data` | **string** | 0x10 |

```json
{ "Data": "whatever the room stored" }
```

⚠️ **`Data` is a flat string, not an object.** Whatever structure the room keeps inside it is the
room's business — if you store JSON there it must be sent as an **escaped string**, the same way
`ChatMessage.Contents` works ([chat-sendmessage](chat-sendmessage-wire-shape.md)). Emitting
`"Data": { ... }` will not deserialize.

`{}` deserializes fine (the single key is omittable, leaving `Data` null), but an **empty body** throws
`IONCMJIACFI`. Serve `{"Data":""}` or `{"Data":null}` for "no data yet" rather than a bare `204`.

Utf8Json accepts `Data` and `data` — only two casings exist for this key, because the camelCase and
all-lowercase forms coincide.

## The PUT: ⚠️ CORRECTED 2026-10-15 — the response body is NEVER READ

> **An earlier revision of this note said the PUT is ENVELOPED and expects
> `{"Success": true, "Error": null, "error_id": null}`. That is WRONG on `20260323.14`.**
> It came from the 2025 "a `friendlyActionDescription` means enveloped" heuristic, which
> [2026-send-helper-tiers](../conventions/2026-send-helper-tiers.md) retired — on 2026 *every* send
> takes that argument, so `'save player room data'` carries no information. The old text already
> flagged the envelope as unverified. It is now measured: **the PUT discards the body entirely.
> Only the HTTP status code matters.**

### Measured chain (build `20260323.14`)

```
RecNet.Rooms.DFMBMRNABHU.RPYFCNTFABN(long roomId, string data, ct) -> Task      0x95b1a00
  literals 'rooms/{0}/playerdata/me' + 'save player room data'
  verb = HttpMethod statics [+0x28] = PUT                 (read at 0x95b1b04)
  tail-calls DFMBMRNABHU.QCRHMYXCMAX(description, method, path, ct, cfg) -> Task  0x95b1170
    uses the NON-GENERIC AsyncTaskMethodBuilder (AsyncTaskMethodBuilder$$get_Task, not `1)
      -> RGBOOBRDHEB.JEYAQXBXMRA(ct)                                             0x9537a00
        -> <SendWithNoResponseAsync>d__43$$MoveNext                              0x954c950
          -> RGBOOBRDHEB.YGADVOMHRVJ<bool>(lambda, ct)      generic inst #85 = bool
```

**The facade returns a non-generic `Task`** — tier 5, "no response value at all". The non-generic
builder, whose `SetResult()` takes no argument, is the independent confirmation.

### The proof: the entire lambda `<>c.EWCUIIBAZVI` `0x954d430`

```
0x954d487  call RecNet.XJAFUXFVGPU$$RBSYDGDRRZM   ; EnsureSuccessStatusCode-equivalent
0x954d4a1  mov  rdx, <Task::FromResult methodref>  ; generic inst #85 = bool
0x954d4a8  xor  ecx, ecx                           ; the value is literally `false`
0x954d4aa  call Task.FromResult<bool>(false)
0x954d4c3  call RecNet.XJAFUXFVGPU$$Dispose        ; response disposed, UNREAD
0x954d4f2  ret
```

That is the whole method. **No Utf8Json, no `ZWUODKCINOA`/`LIRIDCJIGGA`, no formatter and no envelope
type anywhere on the path** — the raw `XJAFUXFVGPU` is status-checked and disposed, and a constant
`false` goes back to a caller that throws it away.

### Server contract for the PUT

| | |
|---|---|
| accept | **any 2xx — `204 No Content` is ideal** |
| reject | any non-2xx ⇒ `RecNet.RecNetWebException: HTTP Error {0}` (`MLREETGNUXI.VEIQCOEFCVM` `0x94B0BA0`) |

`{}`, `null`, an empty body, `{"Success":true,…}` and a page of HTML are **all equally fine** — none
is parsed. There is also **no soft-failure channel**: `{"Success": false}` with a 200 reads as a
success. A failed save must be a non-2xx status.

⚠️ The 2025 build was **never** verified either way — the old claim rested on a continuation
(`OAIFDLKBDGK..ctor` `0x7DFB4F0`) that was not resolved. Don't carry the envelope claim to any build
without reading the helper.

## The PUT REQUEST: one form-urlencoded field, `data`

The `requestBuilderAction` is `QFCXJTSNKSN.PIFIWYRKBSX` `0x95b8200` (bounds `..0x95b8266`) and adds
exactly one parameter:

```
0x95b8238  mov  StringLiteral 'data'
0x95b8250  call RecNet.RGBOOBRDHEB$$NJPEKLKCVCG
```

`NJPEKLKCVCG` is the **verb-dependent** family
([elhkhfjehlm-verb-dependent-params](../conventions/elhkhfjehlm-verb-dependent-params.md)) and the verb is
**PUT, not GET**, so `data` lands in an **`application/x-www-form-urlencoded` body**, not the query
string:

```http
PUT /rooms/4017/playerdata/me HTTP/1.1
Content-Type: application/x-www-form-urlencoded

data=CAVKngIKGAoSChDwYc17BTwsTY1v0tKEcKIiGgIIAAoY...
```

The value is the base64 `rec_room.PlayerSaveData` below, url-encoded — `+` arrives as `%2B` and `=`
padding as `%3D`. **Read it from the form body, and url-decode before base64-decoding.**

⚠️ `names.py 0x95b8200 0x100` also prints `'id'` and `'description'`. Those are past `0x95b8266` and
belong to the **next** closure in the same display class — window overrun. Bound every literal dump
with `fstart.py`.

## One path, two verbs — but not the way this note used to say

| verb | request | response |
|---|---|---|
| **GET** | nothing | **bare** `{"Data": "<base64>"}` — required; an empty body throws `IONCMJIACFI` |
| **PUT** | form body `data=<base64>` | **nothing — body discarded; return `204`** |

## Validation

`ADDGAOJJHIL.CPOBHIECLEN` is the shared no-op stub `0xA60520` — no post-deserialize validation, and
the key is omittable.

## ✅ GET re-verified on 2026 (`20260323.14`), 2026-10-15

Independently re-derived on the 2026 build; the 2025 shape holds **unchanged**.

| | |
|---|---|
| route literal | `'rooms/{0}/playerdata/me'` slot **`0xFD679E0`**, `String.Format`, roomId is a path segment |
| facade | `RecNet.Rooms.DFMBMRNABHU.SZMQGBMXPSU(long roomId, ct) -> Task<RecNet.Rooms.PlayerRoomDataDTO>` `0x95b1d70` |
| state machine | `<GetMyPlayerRoomData>d__31$$MoveNext` `0x95bd380` |
| **verb** | **GET** — `HttpMethod` statics `[+0x08]`, read at `0x95bd495` |
| service | 16 Rooms, inherited from the facade (no per-method `r8d` immediate) |
| **params** | **none** — the `Action<RGBOOBRDHEB>` argument is **null** (`mov qword ptr [rsp+0x20], 0` at `0x95bd4da`), which also means **no body and no response-cache TTL** |
| tier | **bare `Task<T>`** — tier 1 in [2026-send-helper-tiers](../conventions/2026-send-helper-tiers.md); no envelope |
| formatter | `Utf8Json.Formatters.RecNet.Rooms.HQSCKLKXVYL` `.ctor 0x8ebb0e0`, confirmed by `msig`: `Deserialize(JsonReader, FSNHROPLCPN) -> RecNet.Rooms.PlayerRoomDataDTO` |

**One key, `Data`** (field offset `+0x10`), accepted casings `Data` and `data` — the camelCase and
all-lowercase forms coincide, which is why `names.py` on the `.ctor` prints only those two. The DTO
type name and its `get_Data`/`set_Data` accessors are **unobfuscated** on 2026.

```json
{ "Data": "CAVKngIKGAoSChDwYc17BTwsTY1v0tKEcKIiGgIIAAoY..." }
```

### RESOLVED — what a `null` or empty `Data` does (was "not traced")

The consumer `<DownloadAndParseData>d__1$$MoveNext` `0x10f9050` guards **both** levels before
decoding:

```
0x10f91f1  test rax, rax                 ; the DTO itself
0x10f91f1  je   0x10f922e                ;   null -> skip
0x10f91f3  cmp  qword ptr [rax + 0x10], 0 ; DTO.Data
0x10f91f8  je   0x10f922e                ;   null -> skip
0x10f9218  call System.Convert$$FromBase64String
0x10f921d  mov  [rbx + 0x48], rax        ; byte[] (stays NULL if skipped)
0x10f927b  call RecRoom.Versioning.RDSDSVSUBUU$$FWMNXSSWFPM(deps, bytes)
```

and the migration `RDSDSVSUBUU.FWMNXSSWFPM(.VQSBDUUAFGN deps, byte[] bytes)` `0xa587550` null-checks
the array itself:

```
0xa58759c  test rbx, rbx                 ; bytes
0xa58759f  je   0xa5875d6                ;   null -> load ReadOnlySequence<byte>.Empty
0xa587647  call FWMNXSSWFPM(deps, ReadOnlySequence<byte>)   0xa5870d0
```

So no bytes ⇒ `ReadOnlySequence<byte>.Empty` ⇒ a protobuf parse of zero bytes ⇒ a default
`PlayerSaveData` with `version = 0` (`V0NewPlayerSaveVersion`) ⇒ the V0→V5 migration chain runs.
**That is the intended new-player path and it throws nothing.**

**Therefore these three are equivalent and all safe for "this player has no save yet":**

```json
{}                      {"Data": null}                {"Data": ""}
```

(The earlier advice to "prefer `""` over `null`" was over-cautious — there is an explicit null guard.
`""` merely takes the `FromBase64String("")` → zero-length `byte[]` route to the same place.)

⚠️ **Still unresolved:** whether the send helper rejects a `null`/empty *HTTP body* before the
consumer's guard is reached. `DFMBMRNABHU.XNYOJFPCXJH<T>`'s async outer is at `0x390aa80`
(`fstart` bounds `..0x390abce`) but its state machine is **generic-shared and absent from
`methods.pkl`**, so the `ZWUODKCINOA` vs `LIRIDCJIGGA(bool)` question — and the allow-null flag the
tier note says to read from `dl` — cannot be settled with the current index. Both the 2025
derivation (`IONCMJIACFI` on an empty body) and the tier note's `Response was empty` case say an
absent value can throw there, so **always return the JSON object**; never a bare `204` or a
zero-length body.

## What is INSIDE `Data`: base64 of `rec_room.PlayerSaveData` (protobuf)

Resolved **2026-10-15** on build `20260323.14` from a live blob. `Data` is **not** opaque after all —
it is **base64 of a protobuf `rec_room.PlayerSaveData`**, the player's per-room persistent state
(Circuits cloud variables + equipment slots). Schemas recovered via
[protobuf-descriptor-recovery](../../../il2cpp-analysis/references/protobuf-descriptor-recovery.md) —
the obfuscated classes are `RecRoom.Protobuf.ZARSPYUTYUZ` etc., but `protoc`'s embedded
`FileDescriptorProto` keeps every real name.

```proto
// rec_room/persistence/player_save_data.proto     package rec_room
message PlayerSaveData {
  rec_room.PlayerSaveVersion                version = 1;
  repeated circuits_v2.PersistedValue       bools_DEPRECATED       = 2;
  repeated circuits_v2.PersistedValue       floats_DEPRECATED      = 3;
  repeated circuits_v2.PersistedValue       ints_DEPRECATED        = 4;
  repeated circuits_v2.PersistedValue       quaternions_DEPRECATED = 5;
  repeated circuits_v2.PersistedValue       strings_DEPRECATED     = 6;
  repeated circuits_v2.PersistedValue       vector3s_DEPRECATED    = 7;
  repeated circuits_v2.PersistedValue       colors_DEPRECATED      = 8;
  circuits_v2.PlayerCloudData               cloud_data = 9;   // <- the live one
  circuits_v2.InventoryItemEquipmentSlotsData
                                            inventory_item_equipment_slots_configuration = 10;
}

// circuits_v2/player_cloud_data.proto             package circuits_v2
message PlayerCloudData {                  // all fields `repeated PersistedValue` unless noted
  bools=1  floats=2  ints=3  quaternions=4  strings=5  vector3s=6  colors=7
  repeated circuits.VariantData reference_objects = 8;
  list_bools=9  list_floats=10 list_ints=11 list_quaternions=12
  list_strings=13 list_vector3s=14 list_colors=15
  rec_net_image=16  list_rec_net_image=17  rec_net_meshes=18  list_rec_net_meshes=19
}

// circuits_v2/persisted_value.proto
message PersistedValue {
  core.GuidData        guid            = 1;   // the authored variable id
  bytes                data_DEPRECATED = 2;
  circuits.VariantData value           = 3;
}

// core/guid_data.proto
message GuidData { bytes value = 1; }          // 16 bytes

// circuits/static/ev/variant_data.proto
message VariantData {                          // oneof "value"
  bool   bool   = 1;   int32  i32 = 2;   float f32 = 3;
  string string = 4;   bytes  bytes = 5;
}

// circuits_v2/inventory_item_equipment_slots_data.proto
message InventoryItemEquipmentSlotsData {
  repeated core.GuidData inventory_item_slot_entries = 1;   // one per slot; empty entry = slot empty
}

// rec_room/persistence/player_save_version.proto
enum PlayerSaveVersion {
  V0NewPlayerSaveVersion = 0;  V1CircuitsQuatConversion = 1;
  V2CloudDataInteriorMessage = 2;  V3PersistedValueVariantData = 3;
  V4InventoryItemEquipmentSlotsData = 4;
  V5InventoryItemEquipmentSlotsUpdatedMaximum = 5;  // == LatestPlayerSaveVersion
}
```

### Three traps for a server that stores or synthesises this blob

1. ⚠️ **`GuidData.value` is `Guid.ToByteArray()` — mixed-endian (little-endian first three groups)**,
   not the dashed text and not big-endian. `uuid.UUID(bytes_le=...)` in Python; `new Guid(byte[])` in
   C#. Reading it big-endian yields a plausible-looking but wrong GUID, which is the same trap as
   [searching GUIDs in bundle bytes](../../../rr-client-bringup/references/avatar-item-desc-registry.md).
2. **Use `cloud_data` (9), not the `*_DEPRECATED` lists (2–8).** The deprecated lists are the
   pre-`V2CloudDataInteriorMessage` layout; a live v5 blob leaves them empty. Writing values there
   silently loses them.
3. **`version` must be 5** on this build. It gates migrations, and the enum says 5 is `Latest`.

### A real decoded blob (`Guess_The_ColorRR`, 301 bytes)

```
PlayerSaveData {
  version = 5                                     // V5… / LatestPlayerSaveVersion
  cloud_data {
    bools (7):  7bcd61f0-… = false   bb0eb196-… = true    3de483ba-… = false
                978a2017-… = false   d4fc87fa-… = false   d3e7cd72-… = true
                69a5a94d-… = false
    ints  (4):  74c29519-… = 1       898dd9f2-… = 0       52d81be3-… = 0
                a5599665-… = 0
  }
  inventory_item_equipment_slots_configuration {
    inventory_item_slot_entries: 4 entries, every GuidData EMPTY  // 4 slots, none equipped
  }
}
```

So "player data" for this room is **11 Circuits cloud variables** (7 bool, 4 int) plus four empty
equipment slots. The 11 GUIDs are **authored in the room**, not client-shipped: 0 hits across
`out/stringliteral.json`, the Addressables catalog, all 2,787 shipped bundles and another room's
bake. They are meaningful only against that room's circuit graph, so a server must treat them as
opaque keys and round-trip them byte-for-byte.

An empty `PlayerCloudData` is a valid "new player": `{"Data": "CAU="}` is `version = 5` with nothing
else, which is strictly better than `""` or `null` for a blob the room's circuits will read.

## When the client actually issues the GET — it is NOT a room-load step

Traced **2026-10-15** on build `20260323.14`, answering "the PUT works but joining a room never
calls the GET". Two separate reasons it can be absent, and they need different fixes.

### The call chain (2026 names)

| layer | member |
|---|---|
| HTTP facade | `RecNet.Rooms.DFMBMRNABHU.SZMQGBMXPSU(long roomId, ct) -> Task<PlayerRoomDataDTO>` `0x95b1d70` |
| state machine | `<GetMyPlayerRoomData>d__31$$MoveNext` `0x95bd380`, send `DFMBMRNABHU::XNYOJFPCXJH<PlayerRoomDataDTO>` |
| **cached wrapper** | **`RecNet.Rooms.Client.SZMQGBMXPSU` `0x9595cb0`** |
| static proxy | `RecNet.Rooms.RoomsClientStaticProxy.SZMQGBMXPSU` `0x95d3b30` (tail-jmp to the above) |
| sole consumer | **`<DownloadAndParseData>d__1$$MoveNext` `0x10f9050`** |
| above that | CircuitsV2 `PlayerSaveDataManager` → `GetPlayerSaveDataAsyncDelegate` → `<GetPlayerSaveDataAsync>d__15` `0x2b2e8d0` |

> The obfuscator renamed the methods but **not the compiler-generated state-machine types**, so
> `<GetMyPlayerRoomData>d__31` and `<SaveMyPlayerRoomData>d__183` leak the original method names.
> Grepping `methods.pkl` for `<Name>d__N` is the cheapest way to find a renamed method here.

`<DownloadAndParseData>d__1` is the whole consumer: `Client.SZMQGBMXPSU(roomId, ct)` →
`System.Convert.FromBase64String(dto.Data)` → parse → `RecRoom.Versioning.RDSDSVSUBUU.FWMNXSSWFPM`
(the `PlayerSaveVersion` migration) → `Result<T>`. It lives in the lazy
`DownloadAndParseData`/`DownloadBundles`/`CreateDirectlyLoadableAssetBundleSource` data-source family,
i.e. it is **pull-based**: nothing fetches player data because the room loaded, only because something
asked for a player-save value.

**The one grep that separates "called and failed" from "never called":**

```
Error downloading save data! Try again later or on a better connection.
```

literal `0xFC..` in `0x10f9311`. Present ⇒ the request went out and failed. Absent ⇒ it never went out.

### Reason 1 — `RecNet.Cache`, key `player_room_data/{roomId}`, TTL **1 hour**

`Client.SZMQGBMXPSU` does not call the facade directly. It wraps it:

```csharp
static Task<T> RecNet.Cache.Get<T>(RecNet.Service service, string requestUri,
                                   TimeSpan maxCacheAge, bool forceRefreshCache,
                                   Func<CancellationToken, Task<T>> callback, CancellationToken ct)
```

(`Get` is **unobfuscated**; the siblings are `MUKVHZPLFPB(Service, string)` /
`LOGDMLQUAJN(Service, string)` = per-key invalidate, `IWBFCMJMQTL()` = clear all,
`TTIDZXQWKYM(Service, string)` = contains, `HWJSABCRIGB(Service, string)` = key builder.)

- `requestUri` is `String.Format("player_room_data/{0}", roomId)`, literal slot **`0xFC2FFE0`**.
- The composite key is `"{service}:{requestUri}"` → **`16:player_room_data/4017`**.
- `maxCacheAge` is read as `[RecNet.Cache static_fields + 0x18]`. Re-measured on this build from
  `.cctor` `0x9444c20` (static_fields at `Il2CppClass+0x20`), reading the `movsd` constants:

  | slot | value |
  |---|---|
  | `+0x00` | `FromMinutes(1)` |
  | `+0x08` | `FromMinutes(5)` |
  | `+0x10` | `FromMinutes(10)` |
  | **`+0x18`** | **`FromHours(1)`** ← this route |
  | `+0x20` | `FromHours(24)` |

- **`RecNet.Cache` is in-memory only** — no file-path literal in any of its 11 methods, so it dies
  with the process. It is a *different* layer from BestHTTP's on-disk `HTTPCache`: a `RecNet.Cache`
  hit means **no HTTP request at all**, whereas an `HTTPCache` hit still shows a request (304).

⚠️ **The save path warms the same key.** `<<SaveMyPlayerRoomData>g__SaveMyPlayerRoomDataHelperMethod|183_0>d`
`0x95a5660` formats `player_room_data/{0}` after the PUT succeeds and calls into the cache with it
(`0x95a5988` `String.Format`, then a generic-shared helper at `0x95a59d1`). **Not resolved:** whether
that writes the saved value through or evicts the entry — the target is generic-shared and
`methods.pkl` has no entry for it. Observationally, a client that PUTs and then rejoins issues no GET,
which is what a write-through would do.

So **"PUT works, GET never fires" is the expected shape within one client session.** Test it on a
cold start: relaunch the client (clears `RecNet.Cache`), join the room once, and grep for the request.
If it fires there, nothing is broken.

### Reason 2 — nothing demanded a player-save value

If the GET is absent even on a cold launch, the pull never happened. The room's circuits have to ask,
and they can only ask for variables they have **definitions** for — which arrive in the `FileType=6`
RoomMetadata blob referenced by `DataBlob` on `GET rooms/{roomId}?include=`. A server that omits
`DataBlob` leaves the client with no definitions, so there is nothing to load, **no request, and no
log line** — see [rooms-room-by-id](rooms-room-by-id-wire-shape.md), which records the same
silent-missing-request failure for the metadata blob itself.

Cross-check that costs nothing: if the client's PUT body already carries real variable GUIDs with
values, definitions *do* exist and Reason 2 is out.
