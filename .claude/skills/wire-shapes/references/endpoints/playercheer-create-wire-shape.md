# Playercheer create wire shape

> POST api/PlayerCheer/v1/create (svc 2 API) takes PlayerIdTo/CheerCategory/RoomId/Anonymous as QUERY params with no body and returns a BARE {Success, Message}; identical on both client builds.

Derived **2026-08-25** from build `20250718.01`, cross-checked against `20230414`.

`POST https://api.<host>/api/PlayerCheer/v1/create` — service **2 = API** (`mov r8d, 2`), verb
**POST** (`HttpMethod` statics `+0x20`). Client entry
`GODFFKHOCEE.PNGBPABIFMJ(long playerIdTo, CDLOLAJOAEG cheerCategory, bool anonymous)` `0x7C9D930`.

**Request: four QUERY params, no body** — all added with `MGPBDIAGCFD.ELHKHFJEHLM`, in this order:

| param | type |
|---|---|
| `PlayerIdTo` | long |
| `CheerCategory` | int (enum below) |
| `RoomId` | long — **not a method parameter**, taken from ambient room state |
| `Anonymous` | bool |

`CDLOLAJOAEG` (CheerCategory), numeric and **not sequential**:
`General 0`, `Helpful 10`, `Sportmanship 20` *(sic — one 's')*, `GreatHost 30`, `Creative 40`,
`RecRoomDeveloper 9000`.

## Response: BARE 2-key object

`HPBKMCLEANE<EBPLFPLICDI>` — T is the DTO directly, and `EBPLFPLICDI` derives `object` and implements
only `PDDMBELEHHJ` (the post-deserialize interface), **not** the envelope marker `MPKGNLKJDEG`
([rooms-isbanned-wire-shape](rooms-isbanned-wire-shape.md)). Formatter `EDPDEEKHLPD` `.ctor 0x7E5DC20`, 2 keys:

```json
{ "Success": true, "Message": null }
```

`Success` bool, `Message` string. **No validation** — `EBPLFPLICDI.CPOBHIECLEN` is the `0xA60520`
no-op, so a missing key just defaults.

**The "already cheered" message is client-side, not yours.** `'You have already cheered this player
very recently.'` is a *local rate limiter* at `0x7C9DB87`: the client compares a stored timestamp
against now and, if too soon, shows that string and **never issues the request**. Do not try to
produce it from `Message`.

The client method returns the valueless promise `JCFICNGFDLA`, so `Success`/`Message` are read by the
caller rather than asserted by the transport — nothing throws on `Success: false`.

## Cross-build: identical, no `ver` branch

On `20230414` the facade is `DINMFHPHBEG` with `ACBGPMOLJIH(long, MMCGOCLBAEG, bool)` — same three
params — and the response type is `BJMGAOAAKMM` = `{bool, string}`, matching `EBPLFPLICDI`
field-for-field. `MMCGOCLBAEG` has the same six members with the same values. A compiler-generated
name on that build spells the operation out: `<CreateCheer>b__7_0(BJMGAOAAKMM okResponse)`.
**One response body serves both clients.**

⚠️ **CORRECTION 2026-09-02:** where this note says the parameters are **query params**, they
are actually an **`application/x-www-form-urlencoded` request body** — `ELHKHFJEHLM` routes params
to the query string only for GET. See [elhkhfjehlm-verb-dependent-params](../conventions/elhkhfjehlm-verb-dependent-params.md). Response shape
unaffected.
