# Avatar hand/head offsets in the 2026 client — where they actually live

> `RecRoom.Avatars.{HandLogicOffsets, HeadLogicOffsets, PlatformSpecificPlayerHandOffsets}` exist in
> build `20260323.14` with exact field layouts, but **their values are NOT in the binary** — they are
> serialized Unity data on the `AvatarModernBodyBehaviour.configuration` field. The binary holds only
> the C# field initializers from `AvatarModernBodyConfiguration..ctor`, and that ctor sets **none** of
> the four offset fields.

Derived **2026-11-06** on `C:\games\recflare-2026` (build `20260323.14`) from the carved 2026
index (`C:\Gamesecnet-patcher\il2cpp-2026`, `GA_MR=0xEBF5810`); carve procedure in
[recflare-2025-metadata-carve](../../il2cpp-analysis/references/recflare-2025-metadata-carve.md).

## There is no `Assembly-CSharp.dll`

This is an IL2CPP build: the managed assemblies are AOT-compiled into `GameAssembly.dll` and the
managed DLLs are not shipped. There is nothing to decompile with dnSpy/ILSpy. What survives is
`global-metadata.dat` — type names, field names, field **order** and field **offsets** — which is
what the carve pipeline recovers. Field *values* of serialized classes are not metadata; they live in
the Unity asset that holds the component.

## The three types

`RecRoom.Avatars.PositionAndRotation` (typedef #54875) — **struct, 28 bytes**, the unit all four
offset fields are built from:

| off (inline) | type | field |
|---|---|---|
| `+0x00` | `UnityEngine.Vector3` | `Position` |
| `+0x0C` | `UnityEngine.Quaternion` | `Rotation` |

> `fields2025.py` prints value-type offsets **including the 0x10 boxed-object header**. For a struct
> used inline (as all of these are), subtract `0x10` from what it prints. The tables below are
> already corrected.

### `RecRoom.Avatars.HandLogicOffsets` (typedef #54883) — **class** (heap object, 0x10 header)

| off | field |
|---|---|
| `+0x10` | `FingerMidOffset` |
| `+0x2C` | `FingerTipOffset` |
| `+0x48` | `HandCenterOffset` |
| `+0x64` | `HandShakeOffset` |
| `+0x80` | `GravityPickupOffset` |
| `+0x9C` | `FistBumpOffset` |
| `+0xB8` | `HighFiveOffset` |
| `+0xD4` | `WatchMenuOriginOffset` |

It is a reference type, not a struct — the two `HandLogicOffsets` fields on the configuration sit
8 bytes apart (`0x2f8`, `0x300`), i.e. pointers. Its `.ctor` is `0xd10590`, the **shared trivial
`Object..ctor` stub**, so there are no compiled-in defaults.

### `RecRoom.Avatars.HeadLogicOffsets` (typedef #54885) — **struct, 112 bytes**, stored inline

| off (inline) | field |
|---|---|
| `+0x00` | `VoiceLinesOffset` |
| `+0x1C` | `VFXEmotesOffset` |
| `+0x38` | `FaceTriggerOffset` |
| `+0x54` | `MouthColliderOffset` |

### `RecRoom.Avatars.PlatformSpecificPlayerHandOffsets` (typedef #54882) — **struct, 192 bytes**, inline

| off (inline) | type | field |
|---|---|---|
| `+0x00` | `PositionAndRotation` | `Default` |
| `+0x1C` | `bool` | `HasSteamVrVive` |
| `+0x20` | `PositionAndRotation` | `SteamVrVive` |
| `+0x3C` | `bool` | `HasSteamVrOculus` |
| `+0x40` | `PositionAndRotation` | `SteamVrOculus` |
| `+0x5C` | `bool` | `HasSteamVrMicrosoft` |
| `+0x60` | `PositionAndRotation` | `SteamVrMicrosoft` |
| `+0x7C` | `bool` | `HasOculus` |
| `+0x80` | `PositionAndRotation` | `Oculus` |
| `+0x9C` | `bool` | `HasSteamVrIndex` |
| `+0xA0` | `PositionAndRotation` | `SteamVrIndex` |

The `Has*` bool gates each per-platform override; when false the runtime falls back to `Default`.
The field order **is** the serialized order, so this doubles as the layout for parsing the asset.

## Who owns them

`RecRoom.Avatars.AvatarModernBodyConfiguration` (typedef #52830, **91 fields**) — a serialized config
class, not a `ScriptableObject` subclass of its own; it is the type of the `configuration` field on
`RecRoom.Avatars.AvatarModernBodyBehaviour` (typedef #52829), which **is** a MonoBehaviour
(`Awake` `0x9822B60`, `OnEnable` `0x98238E0`, `OnDisable` `0x9823890`, `OnDestroy` `0x9823820`,
`CreateAvatarSystem` `0x9822FC0`).

Offsets of the four interesting fields inside `AvatarModernBodyConfiguration`:

| off | type | field |
|---|---|---|
| `0x0284` | `HeadLogicOffsets` (inline struct) | `HeadOffsets` |
| `0x02F8` | `HandLogicOffsets` (pointer) | `LeftHandOffsets` |
| `0x0300` | `HandLogicOffsets` (pointer) | `ModernBeanLeftHandOffsets` |
| `0x0308` | `PlatformSpecificPlayerHandOffsets` (inline struct) | `LeftPlayerHandPlatformOffsets` |

⚠️ **Only the LEFT hand is stored.** There is no `RightHandOffsets` / `RightPlayerHandPlatformOffsets`
field anywhere in the build (reverse field search over all typedefs returns exactly the four fields
above). The right hand is mirrored at runtime, so a patch that changes the left offsets changes both.

## So where are the numbers?

In the serialized `AvatarModernBodyBehaviour` component — a prefab or scene object, shipped either in
`resources.assets` or in an addressable bundle. Two ways to read the real values:

1. **Offline** — find the prefab carrying `AvatarModernBodyBehaviour` and parse its MonoBehaviour
   blob using the field order above. See [the Addressables catalog and bundle tooling](../SKILL.md)
   (`aacatalog.py`, `bundlescan.py`, `bundlepeek.py`).
2. **At runtime** — read the live object. `AvatarModernBodyBehaviour.configuration` is a pointer
   field on the component; from there the table above gives every offset.

## What the binary *does* give you: the ctor defaults

`AvatarModernBodyConfiguration..ctor` `0x9823AB0` is a real ctor (not the shared stub) and contains
74 C# field initializers as `mov dword ptr [rdi+OFF], <imm32>` float stores. **None of them land in
`0x0284`–`0x03C7`**, which is the proof that the offsets have no compiled-in defaults. The ones it
does set are the tuning scalars, e.g.:

```
0x0218 SteeringRotationalFollowTime     0.04      0x0410 LeaningAmount              0.45
0x0228 TurnDeadZoneAngle                70        0x041C LeaningMaxTurnAngle        50
0x022C TurnMaxHeadDifference            90        0x0420 VRMinHandMoveDistance      0.02
0x0230 MaxLocalHeadTurn                 45        0x0428 HandIkBlendInTime          0.3
0x0240 SpeedStopTime                    2         0x043C VRShoulderTwistIdle        0.2
0x0280 VerticalHipOffsetWhenProneForBeans -0.4    0x0458 ClimbingBodyTwistAmount    0.6
0x03D8 ClassicBeanHandSize              1.2       0x048C MinSnapAngle               80
```

Reproduce the full table with the two new tools:

```sh
py -I fields2025.py AvatarModernBodyConfiguration > cfg_fields.txt
py -I fn.py 0x9823AB0                             > cfg_ctor.txt
py -I ctordefaults.py cfg_fields.txt cfg_ctor.txt rdi
```

`ctordefaults.py` joins `mov dword ptr [reg+OFF], imm32` stores to field names and decodes the
immediate as an IEEE-754 float. `fieldowners.py <TypeName>` is the reverse field search that found
the owner — "which types have a field of this type", which `ftypes.py` cannot answer.

⚠️ A `Vector2`/`Vector3` field shows up as **consecutive stores**, only the first of which maps to a
field name; the rest print `<unmapped>` and belong to the preceding field (e.g. `0x046C SeatedLimits`
`-0.1` followed by `<unmapped>` `0.2` = `SeatedLimits = (-0.1, 0.2)`).

Not to be confused with
[il2cpp-field-default-values-compressed](../../il2cpp-analysis/references/il2cpp-field-default-values-compressed.md),
which reads `fieldDefaultValues` from the metadata — that table covers enum members and `const`
fields only, never an instance field initializer. Those live in the ctor's code, which is why this
needs a disassembly pass rather than a metadata walk.

**Why:** a field initializer in C# compiles into the ctor, so it survives into the binary; a value set
in the Unity inspector does not — it is written into the asset and overwrites the ctor's value at
deserialize time. For any serialized config, treat the ctor as "the default before the designer
touched it", never as the shipped value.
