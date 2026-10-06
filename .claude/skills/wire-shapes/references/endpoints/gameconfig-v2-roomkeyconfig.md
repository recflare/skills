# api/config/v2 — RoomKeyConfig (and the null-section NRE class)

> A missing SECTION in the api/config/v2 game config is a null field, and the client dereferences several of them without a guard. `RoomKeyConfig: {"MaxKeysPerRoom": N}` absent => NRE in RoomKeyListModel.CheckIfCanCreateLink the moment the user presses "add room key".

Derived **2026-09-25** from build `20250718.01`, from a live client stack trace.

`GET/POST https://api.<host>/api/config/v2` — fetched by `MAFFJNOGKDL.ENLBBEIGLPN` `0x7CD4930`
(literal slot `0xD126890`). `MAFFJNOGKDL` is the game-config manager; it also serves the narrower
`api/config/v1/azurespeech`, `/v1/backtrace`, `/v1/freegiftbutton`.

## The crash

```
Object reference not set to an instance of an object.
  at LHMONGGMNAI.BKKOGNBEFAD ()
  at RRUI.Data.RoomKeyListModel.CheckIfCanCreateLink ()
  at RRUI.Data.RoomKeyListModelController+TryCreateLinkImpl.BMLFFKJGECG ()
  ... UnityEvent.Invoke -> UIInputModule
```

Two tiny methods, no allocation, no HTTP:

| RVA | body |
|---|---|
| `MAFFJNOGKDL.FGNEFLIBEBG` `0x7CD4C40` | `root = manager[+0x10]`; **throws if root null**; `return root[+0x40]` |
| `LHMONGGMNAI.BKKOGNBEFAD` `0x7D96950` | `s = FGNEFLIBEBG()`; `test rax,rax / je -> throw` at `0x7D9698F`; `return s[+0x10]` (an int) |

So the **root config loaded fine** — the throw is the second check: section `+0x40` came back null.

## Which section

Config root `.ICNOAAFAAEL` (typedef #21932, 9 fields), formatter `OJMEFDGOKEJ` `.ctor 0x7761640`.
The `____stringByteKeys` run is **8 keys against 9 fields** — one member carries no key — and pairs
by position and type:

| field off | key |
|---|---|
| 0x18 genericinst | `LevelProgressionMaps` |
| 0x20 szarray | `DailyObjectives` |
| 0x28 | `ServerMaintenance` |
| 0x30 | `AutoMicMutingConfig` |
| 0x38 | `StorefrontConfig` |
| **0x40 `.DIDGJAHOMJM`** | **`RoomKeyConfig`** |
| 0x48 | `RoomCurrencyConfig` |
| 0x50 string | `ShareBaseUrl` |

`.DIDGJAHOMJM` (typedef #21936) has exactly **one** field, an `int` at `0x10` — the value
`BKKOGNBEFAD` returns. Formatter `HMHFAEBGOPJ` `.ctor 0x7758030`, single key **`MaxKeysPerRoom`**.

## Fix

```json
"RoomKeyConfig": { "MaxKeysPerRoom": 10 }
```

The number is the client-side cap it compares the current key count against; the server-side refusal
is `RoomKeyResult.RoomKeyLimitReached (16)` on
[roomkeys-v1-create](roomkeys-v1-create-wire-shape.md). An **omitted key and an explicit `null` are identical** here —
both leave the field null and both crash.

## The general class

This is not a room-keys bug, it is the shape of every section on this config. A section object that
the server omits is a null field, and the client reads several of them without a guard, so the crash
lands wherever the relevant UI is opened rather than at config load. `RoomCurrencyConfig`,
`StorefrontConfig`, `ServerMaintenance` and `AutoMicMutingConfig` are the same shape of trap — ship
every section, even empty-ish, rather than waiting for each NRE.
