# Inventions v9 save wire shape

> POST api/inventions/v9/save (svc 2 API) returns the ENVELOPED {Value:{Status,Invention,InventionVersion,TagsResponse},Success,Error,error_id}; Value is required when Success=true or the client NREs, and Status is never read.

Derived **2026-08-29** from build `20250718.01` via [recflare-2025-metadata-carve](../../../il2cpp-analysis/references/recflare-2025-metadata-carve.md).

`POST https://api.<host>/api/inventions/v9/save` — service **2 = API**
([recnet-service-enum](../conventions/recnet-service-enum.md)), verb **POST** (`HttpMethod` statics `+0x20`; `+0x08` GET, `+0x28` PUT).
Literal `'api/inventions/v9/save'` `0xD1375F8`. Request builder `AKJEAMCCEOH..ctor(HttpMethod,
service, route)` `0x6FAA230`. JSON body = `RecNet.NewInventionRequestDTO` (19 unobfuscated fields)
via `MGPBDIAGCFD.ELKIBCPINAP`. No query params.

Client entry `EFOOFAABNHL.NKHKGLFLIAJ(.AOEMIBONGBD uploadResult)` **`0x7D08660`**, reached from
`GLAKFFIIDPF.HBAAPCFLHLF(byte[] blob, name, description, …)` `0x7CEACB0` (blob upload → then save).

## Response — ENVELOPED

Send generic is `MGPBDIAGCFD.HPBKMCLEANE<KGOJLHJNIOD<GCLKCLFIPED>>` (generic inst **1001**), i.e. the
envelope IS the deserialised type. Envelope formatter `ELHFLFHDGCF` `.ctor 0x767A730`, keys
`Value, Success, Error, error_id`.

Hierarchy (settles the offsets): **`KGOJLHJNIOD<T>` (0 own fields) : `FFOENOGPGNH<T>` (`Value`) :
`JFNAKFCGDAO` (`Success` bool, `Error` string, `error_id` string)**. Runtime layout
`+0x10 Success`, `+0x18 Error`, `+0x20 error_id`, `+0x28 Value` — confirmed by the consumers below.

`Value` = `.GCLKCLFIPED`, formatter `KAMPLEIBIHI` `.ctor 0x79B63F0`, 4 keys in declaration order:

| key | type |
|---|---|
| `Status` | enum `JCHEICCGKOB` (55 values, `Success = 0`) |
| `Invention` | `KKBFDGFLMMA` (28 keys, below) |
| `InventionVersion` | `KGLGMOJDLMG` (13 keys, below) |
| `TagsResponse` | `EKDKFKMDIIO` = `{Result, Tags}` |

```json
{"Value":{"Status":0,
          "Invention":{ …28 keys… },
          "InventionVersion":{ …13 keys… },
          "TagsResponse":{"Result":0,"Tags":[]}},
 "Success":true,"Error":null,"error_id":null}
```

## What the client actually reads — and what NREs

Two consumers, both on the same result:

1. `EFOOFAABNHL.HENFKAAIDFA` **`0x7D08540`** (registered as `.Then` inside `NKHKGLFLIAJ`):
   - envelope null → **NRE throw** (`0x7D085F9`)
   - `Success == false` → returns quietly, nothing recorded
   - `Success == true` **and `Value` null → NRE throw** (`0x7D08608`) ← the one hard requirement
   - `Value.Invention` null → returns quietly (invention id never recorded client-side)
   - else `Invention.InventionId` → `GLAKFFIIDPF.IBEEALEJCOO(long inventionId, List<string> tags)`
2. `<>c.HIBFEODDICO` **`0x1AE2AE0`** (outer `.Then` from `IINDJLBIDHM.MGLDIHNPDNA`):
   - result null → NRE; `Success` true → success path `EMOEFCLCLPA.CHALOPHBNMH(0)`
   - `Success` false → `Debug.LogFormat("[INV] Invention data blob upload failed: {0}", Error)`

So **`Success` and `Value.Invention.InventionId` are the whole contract**. `Status`,
`InventionVersion` and `TagsResponse` are deserialised but **never read on this route** — `Status`
in particular is *not* the failure channel here; `Success` + `Error` is. `Error` is the only text
that reaches the log.

**No deserialisation-time validation throws anywhere.** `KGLGMOJDLMG`/`EKDKFKMDIIO` have the
`0xA60520` no-op `CPOBHIECLEN`; `GCLKCLFIPED.CPOBHIECLEN` `0x7D09770` only re-encrypts the
`Obscured*` fields of `Invention` (inlined) and null-checks each of the other three members before
calling their hooks. Every key is omittable; omitted = default.

## `Invention` (`KKBFDGFLMMA`) — formatter `FFIJPCECJME` `.ctor 0x79B06C0`, 28 keys

`InventionId` ObscuredLong, `ReplicationId` string, `CreatorPlayerId` ObscuredInt, `Name` string,
`Description` string, `LongDescription` string, `ImageName` string, `UgcVersion` byte,
`CurrentVersionNumber` int, `LatestVersionNumber` int, `Accessibility` enum `KLKIFENPGNG`,
`ForceCannotPublish` bool, `ModifiedAt` DateTime, `CreatedAt` DateTime, `FirstPublishedAt`
DateTime?, `CreationRoomId` long?, `NumPlayersHaveUsedInRoom` int, `NumDownloads` int,
`CheerCount` int, `CreatorPermission` enum `KGCKBAIOBNL`, `GeneralPermission` enum `KGCKBAIOBNL`,
`IsAGInvention` ObscuredBool, `IsCertifiedInvention` ObscuredBool, `IsRecRoomApproved`
ObscuredBool, `AllowTrial` ObscuredBool, `Price` int?, `HideFromPlayer` bool,
`DisplayMetadataJson` string.

`Obscured*` are plain numbers/bools on the wire ([rooms-contributedby-wire-shape](rooms-contributedby-wire-shape.md)).

## `InventionVersion` (`KGLGMOJDLMG`) — formatter `ABNPBOMFBBB` `.ctor 0x79A58F0`, 13 keys

`InventionId` long, `ReplicationId` string, `VersionNumber` int, `HasBetaContent` bool,
`InstantiationCost` int, `LightsCost` int, `ChipsCost` int, `CloudVariablesCost` int,
`BlobName` string, `BlobHash` string, `CreatedAt` DateTime, `UgcAccessibility` `KLKIFENPGNG?`,
`ReferencedUnityAssetIds` Guid[].

## `TagsResponse` (`EKDKFKMDIIO`) — formatter `AEHFMEGNDGF` `.ctor 0x771E170`

`Result` enum `CJJEIGDCFGB`, `Tags` List<string>. Same shape as
[playerevent-tags-build-difference](playerevent-tags-build-difference.md)'s `TagModifyResult`.

## Enums (numeric on the wire)

- `JCHEICCGKOB` (invention `Status`, 55 members, sequential 0..54): `Success 0`,
  `InvalidParameters 1`, `PlayerCannotUpload 2`, `DuplicateName 3`, `NameTooShort 4`,
  `NameTooLong 5`, `NotCreator 6`, `DoesNotExist 7`, `ImageDoesNotExist 8`,
  `InventionLimitReached 9`, `DescriptionTooLong 10`, … `PlatformDoesntSupportInvention 54`.
- `KLKIFENPGNG` (`Accessibility`, `UgcAccessibility`): `Private 0`, `Public 1`, `Unlisted 2`.
- `KGCKBAIOBNL` (`CreatorPermission`, `GeneralPermission`): `Unassigned 0`,
  `LimitedOneUseOnly 10`, `DisallowKeyLock 15`, `UseOnly 20`, `EditAndSave 40`, `Publish 60`,
  `Charge 80`, `Unlimited 100`. **Not 0/1/2** — spaced by 5s/20s.
- `CJJEIGDCFGB` (`TagsResponse.Result`): `Success 0`, `TooManyTags 1`, `TagUseRestricted 2`,
  `InvalidTag 3`, `InappropriateTag 4`, `TagTooLong 5`, `TagNotFound 6`, `TagAlreadyExists 7`,
  `NoChange 8`, `TagRepeated 9`, `LacksPermission 10`, `RoomDoesNotExist 11`,
  `InventionDoesNotExist 12`, `ReservedWordViolation 13`.

**How to apply:** on failure return `{"Success":false,"Error":"<message>","Value":null}` — that is
safe (the null `Value` is never dereferenced when `Success` is false) and the message is the only
thing the client logs. Never return `Success:true` with a null/missing `Value`.
