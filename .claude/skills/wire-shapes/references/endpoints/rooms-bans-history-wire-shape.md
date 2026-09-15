# Rooms bans history wire shape

> GET rooms/{roomId}/bans/history?id={accountId} (svc 16 Rooms) is ENVELOPED {Value:{ActiveBan, PreviousBans}, Success, Error, error_id}; the ban record has 7 wire keys (one [IgnoreDataMember] string is skipped) and nothing throws on null/empty.

Derived **2026-09-02** from build `20250718.01` via [recflare-2025-metadata-carve](../../../il2cpp-analysis/references/recflare-2025-metadata-carve.md).
Sibling of [rooms-isbanned-wire-shape](rooms-isbanned-wire-shape.md) on the same facade.

`GET https://rooms.<host>/rooms/{roomId}/bans/history?id={accountId}` — Rooms facade
`OALMDGJKBJH`, service **16** ([recnet-service-enum](../conventions/recnet-service-enum.md)), verb **GET** (`HttpMethod` statics `+0x08`,
read at `0x7DFCE61`). Literal `'rooms/{0}/bans/history'` `0xD19E560`.

Client entry `OALMDGJKBJH.LDBLKAHHPPN(long roomId, int accountId, CancellationToken)`
**`0x7DFCD50`** → `Task<BKNNNINMCJG>`.

**Query param `id`** = the account id, added by the display class `FBGCFEDMOAL.ABCLCIHJBHG`
`0x7DEAAC0` (field `accountId`, unobfuscated) via `ELHKHFJEHLM`. This is a **GET**, so it really is a
query string — see [elhkhfjehlm-verb-dependent-params](../conventions/elhkhfjehlm-verb-dependent-params.md). No body.

## ENVELOPED

Helper is `OALMDGJKBJH.PJPLCMBOAFB<BKNNNINMCJG>` (inst **14680**) **with** the leading
`friendlyActionDescription = 'get room ban history'` ⇒ enveloped, by the
[playerevents-v1-room-wire-shape](playerevents-v1-room-wire-shape.md) rule. Confirmed independently: Utf8Json generated a formatter for
the envelope instantiation itself — `NCKJMFLODLC : IHCMHKGLBEA<KGOJLHJNIOD<BKNNNINMCJG>>`,
`.ctor 0x7686C10`, keys `Value / Success / Error / error_id`.

```json
{ "Value": { "ActiveBan": { …7 keys… }, "PreviousBans": [ { …7 keys… } ] },
  "Success": true, "Error": null, "error_id": null }
```

`Value` = `.BKNNNINMCJG`, formatter `KKNKKFIADCE` `.ctor 0x7774920`, 2 keys:
`ActiveBan` (`AOKACCKKLMA`, nullable) and `PreviousBans` (`List<AOKACCKKLMA>`).

## The ban record `.AOKACCKKLMA : .HNJCGCLIIFG`

Formatter `KJKKOJCECDH` `.ctor 0x772CB60`, **7** wire keys — derived first, then base. The type
declares **8** fields; the derived `string` at `0x50` is `[IgnoreDataMember]` and never on the wire.

| # | key | CLR | offset |
|---|---|---|---|
| 1 | `Status` | enum `KKKLLOOPAMF` | 0x28 |
| 2 | `UnbannedByAccountId` | `int?` | 0x2c |
| 3 | `BanEndTime` | `DateTime?` | 0x38 |
| 4 | `Reason` | string | 0x48 |
| — | *(skipped)* | string | 0x50 |
| 5 | `AccountId` | int | 0x10 *(base)* |
| 6 | `BannedByAccountId` | `int?` | 0x14 *(base)* |
| 7 | `BanStartTime` | DateTime | 0x20 *(base)* |

`KKKLLOOPAMF`: **`Active 0`, `Elapsed 1`, `Lifted 2`**.

## Nothing throws on the data

`BKNNNINMCJG.CPOBHIECLEN` `0x7E06CD0`: reads `PreviousBans` (`this+0x18`); **null → immediate
return**; otherwise tail-jumps to the list validator `EADLCOCJAGD.IANBCAFGFNL`, which **returns
false on null rather than throwing** ([platformnotifications-wire-shapes](platformnotifications-wire-shapes.md)). `ActiveBan` is never
touched. `AOKACCKKLMA` has no hook of its own and its base's is the `0xA60520` no-op.

The only failure path is the envelope: null, or `Success != true`, raises
**`LLCLDPPAGIJ`** ([llcldppagij-envelope-failure-exception](../conventions/llcldppagij-envelope-failure-exception.md)) with
**`"Failed to get room ban history"`** — same generic helper family verified at `0x7DE7B4B` /
`0x7DE7B8E` in [rooms-leaderboards-wire-shape](rooms-leaderboards-wire-shape.md).

**How to apply:** "never banned" is
`{"Value":{"ActiveBan":null,"PreviousBans":[]},"Success":true}` — both members are safely
null/empty. `Status` distinguishes a live ban (`Active`) from an expired one (`Elapsed`) and a
manually lifted one (`Lifted`), so `ActiveBan` should carry `Status: 0` and the rest go in
`PreviousBans`.
