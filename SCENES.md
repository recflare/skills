# Scene location IDs — recflare-2025 (build 20250718.01)

`RoomInstance.Location` on the matchmaking wire is a **scene-location GUID string**, not a name.
The client resolves it through `IMKBHICHFMI.BOIPBPENDNC(string, out CFCLEMKANPO)`, whose
`Dictionary<string, CFCLEMKANPO>` is populated in `IMKBHICHFMI..cctor` (RVA `0x89B6FD0`). An
unrecognised value is **not** fatal: `GGCLDGNBNLI.CPOBHIECLEN` (`0x7D2ED90`) logs
*"RecNet game session contains unknown scene location ID"* and leaves the parsed enum at 0, so the
client silently loads DORM_ROOM instead.

Extracted from the `.cctor` by pairing each key literal with the `mov r8d, <enum value>` that
precedes its `Dictionary.Add`. The order matches the `CFCLEMKANPO` declaration exactly, gap at 29
included, which is the cross-check that the pairing is right.

Regenerate with:

```sh
export GAMEASSEMBLY="C:\Games\recnet-patcher\tools\metadump\out\GameAssembly.dll"
cd il2cpp-2025 && python rangedis.py 89b7290 89b7b90     # key literal, then mov r8d, <value>
```

| CFCLEMKANPO | Name | GUID |
|---|---|---|
| 0 | `DORM_ROOM` | `76d98498-60a1-430c-ab76-b54a29b7a163` |
| 1 | `REC_CENTER` | `cbad71af-0831-44d8-b8ef-69edafa841f6` |
| 2 | `LEGACY_CHARADES` | `4078dfed-24bb-4db7-863f-578ba48d726b` |
| 3 | `LAKE` | `f6f7256c-e438-4299-b99e-d20bef8cf7e0` |
| 4 | `PROPULSION` | `d9378c9f-80bc-46fb-ad1e-1bed8a674f55` |
| 5 | `DODGEBALL` | `3d474b26-26f7-45e9-9a36-9b02847d5e6f` |
| 6 | `THE_LOUNGE` | `a067557f-ca32-43e6-b6e5-daaec60b4f5a` |
| 7 | `PADDLEBALL` | `d89f74fa-d51e-477a-a425-025a891dd499` |
| 8 | `RIVER` | `e122fe98-e7db-49e8-a1b1-105424b6e1f0` |
| 9 | `HOMESTEAD` | `a785267d-c579-42ea-be43-fec1992d1ca7` |
| 10 | `QUARRY` | `ff4c6427-7079-4f59-b22a-69b089420827` |
| 11 | `CLEAR_CUT` | `380d18b5-de9c-49f3-80f7-f4a95c1de161` |
| 12 | `SPILLWAY` | `58763055-2dfb-4814-80b8-16fac5c85709` |
| 13 | `QUEST_FOR_THE_GOLDEN_TROPHY` | `91e16e35-f48f-4700-ab8a-a1b79e50e51b` |
| 14 | `ORIENTATION` | `c79709d8-a31b-48aa-9eb8-cc31ba9505e8` |
| 15 | `THE_RISE_OF_JUMBOTRON` | `acc06e66-c2d0-4361-b0cd-46246a4c455c` |
| 16 | `CURSE_OF_THE_CRIMSON_CAULDRON` | `949fa41f-4347-45c0-b7ac-489129174045` |
| 17 | `THE_ISLE_OF_LOST_SKULLS` | `7e01cfe0-820a-406f-b1b3-0a5bf575235c` |
| 18 | `SOCCER` | `6d5eea4b-f069-4ed0-9916-0e2f07df0d03` |
| 19 | `PERFORMANCE_HALL` | `9932f88f-3929-43a0-a012-a40b5128e346` |
| 20 | `PSVR_ROOM_CALIBRATION` | `f5fbd9c9-e853-4036-9d48-5f68e861af04` |
| 21 | `PARK` | `0a864c86-5a71-4e18-8041-8124e4dc9d98` |
| 22 | `WAREHOUSE` | `239e676c-f12f-489f-bf3a-d4c383d692c3` |
| 23 | `CYBERJUNK_CITY` | `9d6456ce-6264-48b4-808d-2d96b3d91038` |
| 24 | `MAKER_ROOM` | `a75f7547-79eb-47c6-8986-6767abcb4f92` |
| 25 | `FRONTIER_SQUADS` | `253fa009-6e65-4c90-91a1-7137a56a267f` |
| 26 | `FRONTIER_SOLOS` | `b010171f-4875-4e89-baba-61e878cd41e1` |
| 27 | `CRESCENDO_OF_THE_BLOOD_MOON` | `49cb8993-a956-43e2-86f4-1318f279b22a` |
| 28 | `BOWLING_ALLEY` | `ae929543-9a07-41d5-8ee9-dbbee8c36800` |
| 30 | `STUNTRUNNER` | `b7281665-a715-4051-826b-8e08e69c6172` |
| 31 | `STUNTRUNNER_THE_MAIN_EVENT` | `3a636bd2-f896-424c-9225-c184522c0d87` |
| 32 | `STUNTRUNNER_BASE_ROOM` | `882e9b96-7115-4b03-86f6-c0c9d8e22e00` |
| 33 | `REGISTRATION` | `cf61556d-68fd-4288-9ae5-7a512621e569` |
| 34 | `AR_ROOM` | `bf268f5f-b55b-41af-8628-32fa4b5d70b6` |
| 35 | `DRIVEIN` | `65ddbb48-5a01-4e3e-972d-e5c7419e2bc3` |
| 36 | `CHARADES_THE_INK_SPACE` | `a673712c-877f-4749-b69a-4a4c6310d545` |
| 37 | `THE_INK_SPACE_BASE_ROOM` | `1fa06e3c-c307-4c11-a91b-1fabcddb8a96` |
| 38 | `FRONTIER_UGC` | `a16bfd31-ffb9-46ac-a199-362c163130c0` |
| 39 | `RECRALLY` | `56193568-9ae0-498c-8a77-4df79dec91f5` |
| 40 | `MAKER_ROOM_2` | `5d4e40d8-f289-4295-a6e1-4f907835007d` |
| 41 | `CUSTOM_DORM_ROOM` | `1c92f780-baf1-4bd8-aa15-27cca0aa7396` |
| 42 | `CUSTOM_DORM_ROOM_2` | `6653a649-bb18-42dc-9742-c66a9399f1a5` |
| 43 | `MULTIPLAYER_ORIENTATION_LANDING_ZONE` | `e0fc5b83-d9d9-428d-b318-dbbf1b35ca6d` |
| 44 | `MULTIPLAYER_ORIENTATION_WELCOME_CENTER` | `3b15bc43-d57e-484e-b11a-7af3b5ff6a96` |
| 45 | `MULTIPLAYER_ORIENTATION_COMPETITION_HALLWAY` | `cf854ff6-5ede-46ca-a20c-1b730cc71b73` |
| 46 | `MULTIPLAYER_ORIENTATION_PRACTICE_GYM` | `e5fa3caf-1c5a-4cdf-bf1c-6edc71babb1f` |
| 47 | `MULTIPLAYER_ORIENTATION_CREATION_GALLERY` | `8886cb77-38c8-4663-af14-594ea9c48825` |
| 48 | `MULTIPLAYER_ORIENTATION_REWARDS_ROOM` | `8ebb8f5c-6319-4e5c-9f1f-31b1b2ccbf42` |
| 49 | `MULTIPLAYER_ORIENTATION_SANDBOX` | `2a5bd0b7-9f3a-4c5b-8d7d-37f75a33ce53` |
| 50 | `MULTIPLAYER_ORIENTATION_SANDBOX_R2` | `9a2522f6-85bc-41e7-ab98-c46dfc0113c5` |

`INVALID = -1` has no GUID — it is the parse-failure sentinel, never sent by the server.
Value **29 is unused** in the enum, so there are 50 scenes for values 0–50.

## Unity scene names (observed, not from the binary)

`Player.log` prints both halves of the mapping during a room load, so the Unity scene name for a
scene-location enum can be read straight off a capture:

```
[LoadScene(MAKER_ROOM)]:      ...
[Load Scene Basement]:        ...
```

| CFCLEMKANPO | Unity scene |
|---|---|
| 0 `DORM_ROOM` | `dormroom2` |
| 24 `MAKER_ROOM` | `Basement` |
| 40/41 `MAKER_ROOM_2` | **`ugcr2`** |

⚠️ **`MAKER_ROOM` (24) is the V1 maker room; `MAKER_ROOM_2` (40 here, **41** on build
`20260323.14`) is its Rooms-2.0 counterpart.** Serving the `MAKER_ROOM` GUID for a room whose
`UgcVersion` is `2` **hard-crashes the client** during the scene's `Awake` pass —
[basement-objectid-invalid-crash-2026](.claude/skills/rr-client-bringup/references/basement-objectid-invalid-crash-2026.md).
The GUIDs are stable across builds; **the integers are not** — re-read the registration `.cctor` per
build (`LWWSBHUHPZM..cctor` `0xa18be80` on 2026).

**`Basement` is `MAKER_ROOM`, not a fallback.** This matters when diagnosing "my custom room loads
as the Maker Room": the client's *silent* fallback is `DORM_ROOM`/`dormroom2`, and it is always
accompanied by the warning *"RecNet game session contains unknown scene location ID"*. Seeing
`Basement` with no warning means the server deliberately reported
`a75f7547-79eb-47c6-8986-6767abcb4f92`, and an empty-looking room is then a missing **subroom save**,
not a wrong scene — check `[Downloading Data] / SubRoom_DownloadAndParse` in the same log block.
