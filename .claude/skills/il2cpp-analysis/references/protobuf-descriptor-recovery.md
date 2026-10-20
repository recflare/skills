# Recovering real `.proto` schemas from the obfuscated client

> Rec Room's protobuf types live in `RecRoom.Protobuf.Runtime.dll` and **carry their real names**,
> because `protoc`'s C# output embeds the whole `FileDescriptorProto` as base64. IL2CPP keeps it as a
> run of **60-char string literals** that the generated `<File>Reflection..cctor` passes to
> `string.Concat`. Reassemble them in that method's literal order and you get the exact `.proto` —
> message names, **field names and field numbers, enum member names, oneofs**. No guessing from
> wire shape.

Established **2026-10-15** on build `20260323.14` while decoding a `rooms/{roomId}/playerdata/me`
blob; see [rooms-playerdata-me](../../wire-shapes/references/endpoints/rooms-playerdata-me-wire-shape.md)
for the result. This is the protobuf analogue of what `msig.py` does for Utf8Json DTOs.

## Why this matters

Everything else about these types is obfuscated — the C# class is
`RecRoom.Protobuf.ZARSPYUTYUZ`, `CircuitsV2.Protobuf.NGKAGSABHPR`, and so on. But the descriptor is
**data `protoc` generated**, so it was never renamed. 2,151 types in that assembly, and a large
fraction keep readable names (`AwardRoomKeyNodeData`, `UgcAccessibility`,
`CircuitGraphToolMappingRegistryData`). The descriptor gives you the rest.

## Procedure

**1. Harvest and decode every base64-looking literal.** Parse `out/stringliteral.json` for
`{value, address}` pairs (⚠️ the file is **not UTF-8** — read bytes and decode with
`errors="replace"`; `json.load` dies). Keep values matching `^[A-Za-z0-9+/]+={0,2}$` whose length is
a multiple of 4, and `base64.b64decode` each one **independently**.

> Chunks are 60 base64 chars = **45 bytes**, and 60 % 4 == 0, so **each chunk decodes on its own with
> no padding error**. That is what makes step 2 possible without knowing the order yet.

**2. Find the file you want** by searching the decoded fragments for `([A-Za-z0-9_/.]{4,80})\.proto`.
The *first* chunk of a descriptor begins with `\n<len><path>` because `name` is field 1 of
`FileDescriptorProto` — match `d.startswith(b"\n" + bytes([len(path)]) + path)` to find it exactly.

**3. `mxref.py <first_chunk_slot>` → the `<File>Reflection..cctor`.**

**4. `names.py <cctor_rva> 0x900` and take the `mov` rows in address order.** That is the
`string.Concat` argument list, i.e. the correct chunk order. The method also emits a `lea` block
holding the same chunks **shuffled**, plus the C# property names (`Version`, `CloudData`, …) — use
the `mov` run, not the `lea` run.

**5. Concatenate, `b64decode`, parse as `FileDescriptorProto`.** Only five field numbers are needed:

| message | fields used |
|---|---|
| `FileDescriptorProto` | 1 `name`, 2 `package`, 3 `dependency`, 4 `message_type`, 5 `enum_type` |
| `DescriptorProto` | 1 `name`, 2 `field`, 3 `nested_type`, 4 `enum_type`, 8 `oneof_decl` |
| `FieldDescriptorProto` | 1 `name`, 3 `number`, 4 `label`, 5 `type`, 6 `type_name`, 9 `oneof_index` |
| `EnumDescriptorProto` | 1 `name`, 2 `value` |
| `EnumValueDescriptorProto` | 1 `name`, 2 `number` |

`label`: 1 optional(implicit) · 2 optional · 3 **repeated**. `type`: 8 bool · 5 int32 · 2 float ·
9 string · 12 bytes · 11 message · 14 enum.

**6. Recurse through `dependency`** — the imports name the next files to pull. A `PlayerSaveData`
decode needs five files; each took one `mxref` + one `names.py`.

## Traps

- **A short descriptor is a single literal, not a run.** `core/guid_data.proto` (89 bytes) is two
  chunks; some are one. A "first chunk" scan that requires ≥3 consecutive base64 literals misses
  them — search all literals, any length, `len % 4 == 0`.
- **Literal-table order is NOT concatenation order.** The literals are ordered by metadata index and
  interleaved with unrelated strings — `"rooms/{0}/playerdata/me"` sits at `0xFD679E0`, directly
  after a descriptor chunk at `0xFD679D8`. Concatenating by address yields a blob whose ASCII is
  *nearly* readable, which is worse than useless: names come out spliced
  (`"4CV2SetPlayerDefinitio/google.golang.org/..."`). Always go through `names.py`.
- **Don't retype chunks by hand.** Two base64 strings of the same length both decode without error
  while differing in one byte, so a transcription slip produces a descriptor that parses and is
  wrong. Read them from the `names.py` output programmatically.
- `gateconfigs.py`, `dtoshape.py`, `regall.py`, `findm.py` are Tier B and do **not** run on a carved
  build; this procedure needs only `mxref.py`, `fstart.py` and `names.py`, which do.

## Worked list (build `20260323.14`)

| `.proto` | `<File>Reflection..cctor` | bytes |
|---|---|---|
| `rec_room/persistence/player_save_data.proto` | `RecRoom.Protobuf.ZARSPYUTYUZ` `0x9eedf20` | 871 |
| `circuits_v2/player_cloud_data.proto` | `CircuitsV2.Protobuf.NGKAGSABHPR` `0xa122600` | 1080 |
| `circuits_v2/persisted_value.proto` | `CircuitsV2.Protobuf.XVPZJPCMBYP` `0xa12d450` | 252 |
| `circuits/static/ev/variant_data.proto` | — (via `mxref` on its first chunk) | 194 |
| `core/guid_data.proto` | `RecRoom.Protobuf.Core.RRQMEHOAIZG` `0x9f52030` | 89 |
| `rec_room/persistence/player_save_version.proto` | `0x9ee23d0` | 353 |
| `circuits_v2/inventory_item_equipment_slots_data.proto` | `0xa10bad0` | — |

There are **~46 `rec_room/persistence/*.proto` files** (the room-save object types:
`shape_data`, `holotar_data`, `leaderboard_data`, `checkpoint_data`, `vehicle_data`, …) and a large
`circuits_v2/*` set, all recoverable the same way. `rec_room/persistence/holotar_data.proto` is the
one behind the `Error downloading Holotar data` warning in
[buffered-room-event-echo-stall-2026](../../rr-room-networking/references/buffered-room-event-echo-stall-2026.md).

## Relation to the "measure before naming a mechanism" rule

This is the cheap measurement that replaces inference. Field *numbers* and *types* are readable
straight off a protobuf wire blob, but field **meaning** is not — a `repeated {guid, oneof}` list
could be anything. One `names.py` call turns it into `circuits_v2.PlayerCloudData.bools`.
