# Rooms roles wire shape

> GET rooms/{roomId}/roles (svc 16 Rooms) returns a BARE ARRAY of 4-key role records {AccountId, Role, LastChangedByAccountId, InvitedRole}; also records that nonobject-responses.txt does NOT cover the OALMDGJKBJH rooms facade.

Derived **2026-09-01** from build `20250718.01` via [recflare-2025-metadata-carve](../../../il2cpp-analysis/references/recflare-2025-metadata-carve.md).

`GET https://rooms.<host>/rooms/{roomId}/roles` — Rooms facade `OALMDGJKBJH`, **svc 16**
([recnet-service-enum](../conventions/recnet-service-enum.md)), verb **GET** (`HttpMethod` statics `+0x08`, read at `0x7DFADB6`).
Literal `'rooms/{0}/roles'` `0xD1A4560`. No query params, no body.

Client entry `OALMDGJKBJH.IPDNLBAOLKH(long roomId, CancellationToken)` **`0x7DFAD00`** →
`Task<List<FPMBNJIPBBL>>`, through the helper **`LMKONLJOAEP<List<FPMBNJIPBBL>>`** (generic inst
22038). `LMKONLJOAEP` takes **no leading `friendlyActionDescription`**, so by the rule in
[playerevents-v1-room-wire-shape](playerevents-v1-room-wire-shape.md) it is the **bare** helper — **no envelope**. This is the same
facade as [rooms-isbanned-wire-shape](rooms-isbanned-wire-shape.md) (enveloped) and [rooms-showcase-wire-shape](rooms-showcase-wire-shape.md) (bare),
confirming again that envelope status is per-helper, not per-facade.

## Response — BARE JSON ARRAY

Element `.FPMBNJIPBBL`, formatter `NJLPFJFNOEG` `.ctor 0x7734D90`, `____stringByteKeys` run = 4 keys,
1:1 with the 4 declared fields (offsets from `fields2025.py`):

| # | key | CLR | offset |
|---|---|---|---|
| 1 | `AccountId` | `ObscuredInt` → plain number | 0x10 |
| 2 | `Role` | enum `PHBPGMMKBJJ` (**byte**) | 0x24 |
| 3 | `LastChangedByAccountId` | `int?` | 0x28 |
| 4 | `InvitedRole` | enum `PHBPGMMKBJJ` | 0x30 |

```json
[ {"AccountId": 12345, "Role": 30, "LastChangedByAccountId": 678, "InvitedRole": 0} ]
```

Each key also accepts camelCase and all-lowercase (`accountId`/`accountid`); `Role` has only
`Role`/`role` (no third variant — it is already single-word lowercase).

`PHBPGMMKBJJ` (also `NewInventionRequestDTO.creatorAccountRole`, see
[inventions-v9-save-wire-shape](inventions-v9-save-wire-shape.md)): **`None 0`, `Banned 1`, `Host 10`, `Moderator 20`,
`Contributor 25`, `CoOwner 30`, `TemporaryCoOwner 31`, `Creator 255`.** Not 0/1/2 — spaced.

**No validation.** `FPMBNJIPBBL.CPOBHIECLEN` `0x7DEBB60` only calls `ObscuredInt.ADACFEEMPHN` to
re-encrypt `AccountId` (see [cheatmanager-module-scan-quit](../../../rr-client-bringup/references/cheatmanager-module-scan-quit.md) for why that matters — a raw write
without it is what error 385120's obscured-value detector catches). No throws, no required fields.
`[]` is a valid response. `InvitedRole` is a non-nullable enum, so send `0` (None) when there is no
pending invite; `LastChangedByAccountId` may be `null`.

Sibling routes on the same facade: `'rooms/{0}/roles/{1}'` `0xD1A48F0` (`BGNIGKMGEHC` `0x7DF5A40`,
`FNMGENEHJCI` `0x7DF95B0`) and `'rooms/{0}/roles/{1}/invite'` `0xD1A4C80` (`MPMNNFFFDLF`
`0x7DFD860`). `"Couldn't create role - roles not supported in this room"` `0xD150F58`.

## ⚠️ Correction to [nonobject-response-routes](../conventions/nonobject-response-routes.md)

`nonobject-responses.txt` (147 lines) **does not cover the `OALMDGJKBJH` rooms facade** — its only
`rooms/` entry is `rooms/requiring/` from `RecNet.Matchmaking`. This route (`List<FPMBNJIPBBL>`),
`rooms/contributedby/me` and `rooms/showcase/{id}` are all bare-collection routes that are missing
from it. The scan evidently only walked `MGPBDIAGCFD` send sites, not facade helpers like
`LMKONLJOAEP` / `NDBMFFLDBBK`. **Absence from that table is not evidence a route takes an object** —
derive the helper's `T` directly.
