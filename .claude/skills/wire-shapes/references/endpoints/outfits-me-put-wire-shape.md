# Outfits me put wire shape

> Wire shape of PUT api/outfits/me — responds with the BARE 3-key envelope {Success, Error, error_id}, no Value key.

Derived **2026-08-17** from `C:\Games\recflare-2025` (build `20250718.01`) via
[recflare-2025-metadata-carve](../../../il2cpp-analysis/references/recflare-2025-metadata-carve.md).

`PUT https://api.<host>/outfits/me` — **PUT** (`HttpMethod` statics `+0x28` = `put_method`;
`+0x08` GET, `+0x20` POST), service **2 = API** (`mov r8d, 2`). Client entry
`IADEBGHMJIG.DBDHNNFDFBO(KPPNBDELPNB outfit)` (`0x7D58800`), state machine `AHOLFKMFPIA$$MoveNext`
(`0x7D4A4C0`). JSON body via `MGPBDIAGCFD.ELKIBCPINAP`. Note the same `outfits/me` literal is also
used by a **GET** state machine `NCBLEPFFJBE$$MoveNext` (`0x7D62F60`) — check the HttpMethod static
offset, not the path, to tell them apart.

**Response is `JFNAKFCGDAO` — the base envelope with NO `Value`**: exactly three keys in
`____stringByteKeys` order, `Success`, `Error`, `error_id` (formatter `OGMMAAFJCJG` ctor
`0x76887E0`). `error_id` is lowercase (`[DataMember(Name = "error_id")]`); `Success`/`Error` are
PascalCase; all accept their casing variants. So `{"Success":true,"Error":null,"error_id":null}`
is a complete valid response — adding a `Value` key is harmless but ignored.

`JFNAKFCGDAO.CPOBHIECLEN` is the `0xA60520` no-op — no validation. Neither call site
(`BOKCGGFPDGN$$MoveNext` `0x7D502B0`, `<<SetMySavedOutfit>b__0>d$$MoveNext` `0x7D68F10`) inspects
`Success` immediately after the await; the envelope object is just handed onward.

Request body `KPPNBDELPNB` (formatter `GAHMAGAAONJ` ctor `0x76C4C50`), 8 keys: `DataVersion` long
0x10, `LegacyData` object 0x18, `CustomizationSettings` string 0x20, `Selections` list 0x28,
`Slot` int 0x30, `Name` string 0x38, `Accessibility` enum 0x40, `ThumbnailFileName` string 0x48.

**Why:** RecNet has three envelope tiers — `JFNAKFCGDAO` (no value, used by write endpoints like
this), `KGOJLHJNIOD<T>` (single value, see [econ-bulkpurchase-wire-shape](econ-bulkpurchase-wire-shape.md)), and
`GJAFHDAFBNE<T>` (list) — and plenty of endpoints use no envelope at all
([curatedlists-bulk-wire-shape](curatedlists-bulk-wire-shape.md), [rooms-contributedby-wire-shape](rooms-contributedby-wire-shape.md)). Which tier applies is
per-endpoint; read it off the state machine's `AsyncTaskMethodBuilder<T>`.
