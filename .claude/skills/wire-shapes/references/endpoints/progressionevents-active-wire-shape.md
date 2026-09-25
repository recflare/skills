# api/progressionEvents/active wire shape

> GET api/progressionEvents/active (svc 2 API) takes NO params and returns a BARE NULLABLE NUMBER — `long?`. The whole body is a single integer. `-1` is the client's own "no active event" sentinel, so serve `-1`, not `[]`, not `{}`, not `null`.

Derived **2026-09-25** from build `20250718.01`.
Found while tracing the `NKJABNHBPCA "expected:'Number Token', actual:'['"` parse failure —
[number-token-parsing-exception](../conventions/number-token-parsing-exception.md) has the exception-to-route mapping and the scan that
produced it.

`GET https://api.<host>/api/progressionEvents/active` — service **2 = API** (`r8d = 2` at
`0x7D62423`), verb **GET** (`HttpMethod` statics `[rcx+8]` at `0x7D62400`). Whole-route literal
(slot `0xD146DD0`), no `String.Format`.

Client entry **`MPJLPOEEGIF.MLFAMKJMNOD`** `0x7D62330` (+0x230). `MPJLPOEEGIF` is the progression
events manager — the class carries the literal `progressionEventsManager` and an **unobfuscated**
field type `RecNet.ProgressionEventRecordDTO` at `+0x18`, which is what names it.

**No params, no body.** The only pre-send call is `MGPBDIAGCFD.DIDJOECFJII` `0x7D9ADB0` (the same
request-options/cache call `club/{0}/details` makes, fed from `NNMGBLLLIAH`) — no `ELHKHFJEHLM`, no
`ELKIBCPINAP`.

## Response — a bare number, no envelope, no object

Send helper is **`MGPBDIAGCFD.CJBFDPLCIEJ<T>(request, bool)`** — the *nullable-response* send, called
with `dl = 1` at `0x7D62488`. Methodref at `0x7D6247E`, generic inst **#59** = **`Nullable<long>`**
(methodSpec #827983, `.data` slot `0xD16C4B0`).

```
-1
```

That is the entire body. Not `{"Value": -1}`, not `[-1]`, not `{}`.

The formatter is `PBJNFCLHOCO` = `NullableInt64Formatter` (`Deserialize` `0x8D5EFC0`): `ReadIsNull`
first, then `ANAMOLLPKLG.CDMENBIFAFK` = `ReadInt64` `0x8D3AF50`, then a **16-byte** `Nullable<long>`
returned in `xmm0`. Sending an array gives `NKJABNHBPCA: expected:'Number Token', actual:'[', at
offset:0` — a Utf8Json `JsonParsingException`, **not** `IONCMJIACFI`, because the throw happens
inside the formatter before the send helper can wrap it.

## `-1` means "none" — and the client says so itself

Two independent places in the binary use `-1` as the sentinel, so this is not a guess:

| RVA | code | meaning |
|---|---|---|
| `0x7D6239D` | `cmp byte [rbx+0x20], 0` → `jne 0x7D624AB` → build `Nullable<long>(-1)` → `Task.FromResult` | the method **short-circuits without any HTTP call** and hands back `-1` when the manager's `bool LBBEEJICFKC` (`+0x20`) is set |
| `0x7D62870` | `MPJLPOEEGIF.NOMNCLOEHKN` — whole method is `Task.FromResult<long?>(-1)` | a dedicated "no active event" helper |

and two consumers test for it explicitly: `0x7D61A9A` (`MPJLPOEEGIF.HLCHIABMCOM`) and `0x7D62C76`
(`MPJLPOEEGIF.ODNHILEBKCB`), both as `if (this.<bool @0x20> && id == -1)`.

⚠️ **`null` parses but is not the same thing.** `NullableInt64Formatter` handles `null` fine
(`HasValue == false`), but every sentinel check in the manager compares against `-1`, and a
`GetValueOrDefault()` on a null would yield **`0`** — a plausible-looking event id. I did not pin how
the async continuation unwraps the `Nullable`, so treat `null` as untested and **serve `-1`**.

## Siblings

`api/progressionEvents` (literal slot `0xD146A38`) is the detail route, referenced by six methods on
the same manager — `BDENLPFKFCJ` `0x7D610B0`, `FKIMBDLBMGD` `0x7D61870`, `HLCHIABMCOM` `0x7D61990`,
`IAJAGBOFJDM` `0x7D61D00` among them. That is where `RecNet.ProgressionEventRecordDTO` is served;
`/active` only hands out the id. Related key literals in this build: `progressionEventId`,
`progressionEventRewardId`, `progressionEventPurchasableXpBoostId`.
