# Nametag badge icons — the blue checkmark is the Influencer badge

> The nametag badge is **`RecRoom.AppUI.AccountBadgeIconType`**, and the blue checkmark is
> **`Influencer = 3`** (the sprite field is literally named `InfluencerCheckMark`).
> It is **not** an account field and **not** a JWT role. The client decides it by fetching
> **`GET api/influencerpartnerprogram/influencers`** and testing `InfluencerIds.Contains(accountId)`.
> ⚠️ `Party` outranks it, so a player in your party shows the party badge instead of their checkmark.

> ⚠️ **This note is `20250718.01`.** On `20260323.14` `AccountBadgeIconType` has **11** members, not
> 4 — values 0–3 are unchanged (so the `influencerpartnerprogram` finding below still holds), but
> `Developer(4)`, `Cheer_Helpful(5)`, `Cheer_General(6)`, `Cheer_Sportsmanship(7)`,
> `Cheer_GreatHost(8)`, `Cheer_Creative(9)` and `League(10)` are new and the priority chain has
> **not** been re-derived for them. See
> [custom-badges-2026](custom-badges-2026-wire-shapes.md) §5.
> Unrelated to the *custom badge* feature (wearable avatar-item badges), which that note covers.

Derived **2026-10-08** from build `20250718.01`. Companion to
[jwt-role-privilege-claims](../conventions/jwt-role-privilege-claims.md) (the `Developer` / `Community Team` /
`Volunteer Mod` **text label**, a different element on the same nametag) and
[influencerpartnerprogram](influencerpartnerprogram-wire-shape.md) (the routes).

## `RecRoom.AppUI.AccountBadgeIconType` (typedef #41651, `int`)

| val | name | val | name |
|---|---|---|---|
| 0 | `None` | 6 | `Cheer_General` |
| 1 | `Party` | 7 | `Cheer_Sportsmanship` |
| 2 | `RRPlus` | 8 | `Cheer_GreatHost` |
| **3** | **`Influencer`** | 9 | `Cheer_Creative` |
| 4 | `Developer` | 10 | `League` |
| 5 | `Cheer_Helpful` | | |

The metadata also carries `InfluencerCheckMark`, `fullCheckMark` and `modCheckMark` as sprite-ish
names, plus `AccountBadgeIconConfig` / `AccountBadgeIconData` / `AccountBadgeIconView` /
`AccountBadgeIconBinder`, which map a type to a `badgeIcon` + `badgeOutlineIcon` pair.

## The nametag has four separate role/badge elements

`RecRoom.AppUI.PlayerNametagViewModel` — field names survived obfuscation:

| element | type | offset |
|---|---|---|
| `RoleBadgeIconType` | `AccountBadgeIconType` | backing field `0x7C` |
| `CheerBadgeIconType` | `AccountBadgeIconType` | — the player's *selected* cheer badge |
| `PlayerRoleType` | `AccountRoleIconType` | the room-role icon |
| `DeveloperLabel` | string | `Developer` / `Community Team` / `Volunteer Mod` |

`RecRoom.AppUI.AccountRoleIconType` (typedef #41655, `int`) — the **room**-role icon, unrelated to
the badge: `None 0`, `Banned 1`, `Host 2`, `Moderator 3`, `Contributor 4`, `CoOwner 5`,
`TemporaryCoOwner 6`, `Creator 7`, `RoomLevel 8`. (Note it is **not** the same numbering as the
wire-side `.PHBPGMMKBJJ`, where Host is 10 and Creator 255 —
[rooms-subrooms-permissions](rooms-subrooms-permissions-wire-shape.md).)

## `UpdateRoleBadge()` — the priority chain

`RecRoom.AppUI.PlayerNametagViewModel.UpdateRoleBadge()` **`0x7F123C0`** (+0x130) is four branches,
each ending in a `PropertyChanged('RoleBadgeIconType')` raise:

```csharp
if (this.inAPartyWithLocalPlayer)            RoleBadgeIconType = Party;        // 1  @0xA3
else if (this.isInfluencer)                  RoleBadgeIconType = Influencer;   // 3  @0xC8
else if (this.playerUIBridge.HasRecRoomPlus) RoleBadgeIconType = RRPlus;       // 2  @0xB0, slot 6
else                                         RoleBadgeIconType = None;         // 0
```

Reads: `cmp byte [rbx+0xA3]` at `0x7F123E5`, `cmp byte [rbx+0xC8]` at `0x7F123F2`, the bridge call
`mov ecx, 6 / call 0x2F50` at `0x7F12412` (interface-slot invoke — slot **6** of
`IPlayerUIBridge` is `get_HasRecRoomPlus()`), then the four stores of `0`/`2`/`3`/`1` into
`[rbx+0x7C]`.

⚠️ **`Party` wins.** A Video Partner who is in your party shows the party badge, not the checkmark —
so "the checkmark disappeared" can be a party, not a server bug.

⚠️ **`UpdateRoleBadge` never assigns `Developer (4)`, the `Cheer_*` values or `League (10)`.** Only
`0`/`1`/`2`/`3` come from here. The cheer values go through `CheerBadgeIconType` (fed by
`GetReputationAsync` → `.KBMCBHICFPL`; the tooltip `'The badge the player has selected'` and
`CheerBadgeImageImpl` / `HideIfNoCheerBadgeImpl` are that feature), and `Developer`/`League` are set
elsewhere — not derived.

## What feeds `isInfluencer` — the server-visible part

```
PlayerNametagViewModel.GetPlayerInfo()                              0x7F10990
  -> IAccountQueryManager.GetIsInfluencerAsync(accountId, ct)       interface slot 7
  -> AccountQueryManager.GetIsInfluencerAsync                       0x7EDAFC0
  -> ONDILCNHMJD.DAMGOFEEEED(int accountId) -> KPIPLFECKNC<bool>    0x7D00BE0
  -> ONDILCNHMJD.LMIHNAIFLOJ() -> KPIPLFECKNC<List<int>>            (cached all-influencers)
  -> ONDILCNHMJD.LEGLDPNOODH(continuationToken)                     GET api/influencerpartnerprogram/influencers
  -> list.Contains(accountId)
  -> viewModel.isInfluencer = result                                [+0xC8], written at 0x7F1BC9E
  -> UpdateRoleBadge()
```

`IAccountQueryManager.GetIsInfluencerAsync(int, CancellationToken) -> Task<bool>` kept its name, and
the call site matches exactly (`rcx` = manager, `edx` = accountId, `r8` = token, awaited, result
stored to `[rdi+0xC8]`).

**`ONDILCNHMJD.DAMGOFEEEED` makes no request of its own** — `names.py` over its 0x230 bytes returns
**zero literals**. It is a continuation (`KPIPLFECKNC<List<int>>.MEOHIKBIBDA`, inst class 1011 =
`List<int>`) over the cached list, with the lambda `DMLKJNOOMLD.BOLIBGHMEPH` doing the
`Contains`. So:

> **To give an account a blue checkmark, include its id in `InfluencerIds` on
> `GET api/influencerpartnerprogram/influencers`.** That is the only input.

```json
{ "InfluencerIds": [205, 220], "ContinuationToken": null }
```

### ✅ A flat static list is exactly right — `take=1000`, fetched ONCE, never paged

**CONFIRMED on a live server 2026-10-08:** adding the account id to `InfluencerIds` made the blue
checkmark appear on the nametag.

`ONDILCNHMJD.LMIHNAIFLOJ()` `0x7D01A20` is only **0xD0 bytes**: a null-check on a cached static
(`cmp qword ptr [rax+0x10], 0` at `0x7D01A63`) and **one** call to `LEGLDPNOODH` at `0x7D01A7C`.
There is **no paging loop** — the client fetches a single page, memoizes it, and **never follows
`ContinuationToken`**.

And `take` is a **hardcoded 1000**: `mov dword ptr [rsp+0x60], 0x3E8` at `0x7D017FA`, boxed at
`0x7D01802` and handed to `ELHKHFJEHLM('take', 1000)` at `0x7D01817`. Service **28 = Econ**
(`mov r8d, 0x1c` at `0x7D017D8`).

So the request is literally `GET api/influencerpartnerprogram/influencers?take=1000` and:

- **Return the whole list in one response.** Up to 1000 ids is all the client will ever read.
- **`ContinuationToken` is ignored** on this path — return `null`; a non-null token is harmless but
  pointless, and nothing will fetch page 2.
- A **static array of account ids is a perfectly correct implementation.** Real Rec Room has on the
  order of hundreds of Video Partners, which is why one 1000-item page suffices.

The list is **memoized for the process lifetime**, so a change will not appear until the client
restarts — expect to relaunch when testing, not merely rejoin. `InfluencerSupportedUpdate` (payload
`.JKBAKBGEGFI`, handler `ONDILCNHMJD.OCBHIOKMGFC`) notifies about *who you support*, not about who is
an influencer, so it will not refresh this cache.

### Two facade methods the routes note doesn't list

[influencerpartnerprogram](influencerpartnerprogram-wire-shape.md) correctly says the facade has **five routes**. `msig`
shows **13 methods**, two of which are local and route-less:

| method | what |
|---|---|
| `LMIHNAIFLOJ() -> KPIPLFECKNC<List<int>>` | the cached all-influencers list over `/influencers` |
| `DAMGOFEEEED(int) -> KPIPLFECKNC<bool>` | `LMIHNAIFLOJ().Contains(id)` — the checkmark predicate |

Also worth noting against that note: `BFNEKGBPEPD()` and `EAPJKBLGNMK(int)` are declared
`KPIPLFECKNC<Nullable<int>>`, which is the post-lambda facade type — the **wire** `T` is still plain
`int` with `0` as the sentinel, exactly as recorded there.

## Why searching for "verified" / "checkmark" finds nothing useful

The feature is named **Influencer** in code and **Video Partner** in the UI
([link-actionlink](link-actionlink-wire-shape.md)); the word *verified* is only used by the referral system, and
*checkmark* only appears as the sprite name `InfluencerCheckMark` plus Unity's own
`unity-checkmark` / `icon_checkmark` assets. There is no `IsVerified` anywhere
([account-dto](account-dto-wire-shape.md)).

So the three "special account" markers on a nametag, and where each comes from:

| marker | mechanism | server input |
|---|---|---|
| **blue checkmark** | `RoleBadgeIconType = Influencer` | `InfluencerIds` on `/influencers` |
| RR+ badge | `RoleBadgeIconType = RRPlus` | `IPlayerUIBridge.HasRecRoomPlus` |
| `Developer` / `Community Team` / `Volunteer Mod` text | `DeveloperLabel` + `DeveloperDisplayModes` | JWT `role` entry **plus a player-side opt-in toggle** |
