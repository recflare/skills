# JWT `role` / `rn.privilege` claims — the full list, and the nametag tags

> The client reads **two** claim names out of the auth token: **`role`** holds the feature/role list
> (`developer`, `moderator`, `influencer`, `screenshare`, `junior`, `whiteglove1/2`, …) and
> **`rn.privilege`** holds the ban list (`BanVChat`, `BanRmChat`, `BanPubInv`, `BanRumiAI`). Both are
> **lists of lowercase/CamelCase strings** tested with `List<string>.Contains`.
> The **"Volunteer Mod"** nametag is the `moderator` entry of `role` — but it is **opt-in**: the
> player still has to switch it on in their own settings. Nothing on any account DTO controls it.

Derived **2026-10-06** from build `20250718.01`, answering "how does a player get the Volunteer Mod
tag".

## The parser

**`PCGJFHLIGAC.APADKOMMKKJ(string, string, string)`** `0x7D17360` (+0xBB0) is the token-claims
parser. Every lookup goes through **`PCGJFHLIGAC.DIFENANFJCD(string name)`** `0x7D18F10` (+0x100),
which is a plain `List<string>.Contains` (methodref at `0x7D18F2E`) with `String.op_Equality` —
**exact, case-sensitive string match, no prefix or wildcard handling.**

The literal order in the method body shows the two claims and what each one gates:

| claim literal | at | entries queried after it |
|---|---|---|
| **`role`** | `0x7D17695` | `influencer`, `developer`, **`moderator`**, `screenshare`, `keepsake`, `livekeepsakeeventroomsaveoverride`, `multiinstanceevent`, `betastudio`, `junior`, `ugcloc`, `limitsv2`, `testaccountmemory`, `testaccountmultiplayer`, `whiteglove1`, `whiteglove2` |
| **`rn.privilege`** | `0x7D1790F` | `BanVChat`, `BanRmChat`, `BanPubInv`, `BanRumiAI` |

Note the casing split: the `role` entries are all lowercase, the `rn.privilege` ban entries are
**CamelCase with a `Ban` prefix**. `DIFENANFJCD` is case-sensitive, so `banvchat` does nothing.

Two more literals are present in the method's init block but have no `mov` use in the run —
`'BanRumiAI'` appears in both lists above because it is queried under `rn.privilege`; nothing else is
left over.

`SessionManager.get_IsDeveloper` `0x2179210` and `get_IsWhiteGloveCreator` are the surfaced forms of
two of these. There is **no** `SessionManager.get_IsModerator` — the moderator flag is read straight
from `PCGJFHLIGAC`.

## "Volunteer Mod" / "Developer" / "Community Team" — the nametag chain

The label is **not** a field on any player or account DTO. It is a per-player networked property
driven by a local setting:

1. **Token:** `role` must contain `moderator` (or `developer`). This is the only server-side input.
2. **Setting:** the player switches it on themselves. `ModeratorDisplayToggleImpl.BMLFFKJGECG`
   `0x22E1E80` is a straight toggle — `if (mode == 3) mode = 0; else mode = 3;`
   (`cmp al, 3` / `mov dl, 3` at `0x22E1EB9`..`0x22E1EC5`) — writing
   `SettingsModel.set_DeveloperDisplayMode` `0x22D4AF0`. `DeveloperDisplaySliderImpl` `0x22DCB60`
   writes the same setting and can select the other values.
3. **Replicate:** `JBECNBJNNIJ.NMOANIOKKLK` `0xFCF8B0` picks up the settings change, reads
   `Player.get_LocalPlayer` and calls `Player.set_DeveloperDisplayMode` `0x20B7D80`, which replicates
   to the other clients.
4. **Render:** on every remote client,
   `RecRoom.AppUI.PlayerNametagViewModel.OnDeveloperDisplayChanged` `0x7F11980` switches on the byte
   and tail-jumps to `set_DeveloperLabel` `0x7F12BD0`.

### `.DeveloperDisplayModes : byte` (typedef #56373)

| val | member | label shown above the head |
|---|---|---|
| 0 | `None` | *(no label)* |
| 1 | `CommunityTeam` | `Community Team` |
| 2 | `Developer` | `Developer` |
| **3** | **`Moderator`** | **`Volunteer Mod`** |

⚠️ **The enum member is `Moderator`, the displayed string is `Volunteer Mod`.** Searching the
binary for "Volunteer" finds only the three UI strings (`'Volunteer Mod'` `0xD098100`, the Circuits
node name `'Local Player Get Is Volunteer Mod'`, `LocalPlayerGetIsVolunteerModeratorNode`) and the
`[Tooltip]` *"Volunteer mods have gamewide moderation privileges (as opposed to room mods)"* on
`HideIfHasRoomRoleImpl.alwaysShowForVolunteerMods`. The plumbing is all spelled `Moderator` /
`DeveloperDisplay`, so grepping the user-visible wording does not reach it.

Interface: `RecRoom.AppUI.IPlayerUIBridge.get_DeveloperDisplay()` returns `DeveloperDisplayModes`,
with `add_OnDeveloperDisplayUpdated` for the change event; implementations are
`BFKJHDLNNGP.get_DeveloperDisplay` `0x24445E0` (tail-jumps to `Player.get_DeveloperDisplayMode`) and
`RRUI.Data.PlayerRoleModel.get_DeveloperDisplay` `0xA8E260`. The same three strings also appear in
`<GetPlayerInfo>d__80.MoveNext` `0x7F1B4A0` (the player-card path) and in
`DeveloperModeLabelImpl.KNNCCDEPPLO` `0x278E160`.

## What a self-hosted server has to do

**Put `moderator` in the `role` claim of the account's token. That is the whole server-side job.**

Then expect this, and do not treat it as a bug:

- **The tag will not appear until the player turns it on.** The default is `None (0)`, the toggle is
  in the player's own settings, and the setting is persisted client-side via `SettingsModel` — it is
  never sent to the server and never read back from it. A moderator who has never touched the toggle
  looks identical to a non-moderator.
- **The tag is replicated player-to-player, not served.** Other clients learn it from
  `Player.DeveloperDisplayMode` over the room session, so it only shows to people in the same room
  instance.
- **One account can show any of the three labels** if its token carries the matching entries — the
  slider picks which. `Developer` needs `developer` in `role`; `Community Team` has **no distinct
  `role` entry among the 15 queried**, so what gates value `1` was not determined.
- Adding `moderator` grants the gamewide-moderation UI as well, not just a cosmetic label — that is
  what the `HideIfHasRoomRoleImpl` tooltip is distinguishing from room-level mods
  ([rooms-subrooms-permissions](../endpoints/rooms-subrooms-permissions-wire-shape.md) covers the room-role side, which is a
  separate system).

## Also settles `screenshare`

`screenshare` is an entry in the **`role`** claim, queried at `0x7D1773B` through the same
`DIFENANFJCD` list lookup — not a separate claim and not a numeric flag. An earlier pass found it
wired to the runtime check `LPNHLJBDCLH.CFCLBPHHCCP` `0x7C85500`; what it ultimately gates is still
undetermined, but the way to grant it is now unambiguous.
