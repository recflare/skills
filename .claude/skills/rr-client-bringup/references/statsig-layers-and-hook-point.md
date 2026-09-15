# Statsig layers and hook point

> Statsig layer params (watch_layer, econ_store_layer, avatars_experiment_layer...) are NOT reachable from the dotted gate-config object — separate system, hardcoded to statsigapi.net. Single choke point to force them all: MGDBOHJAGBN.LMKONLJOAEP<T>(paramName, default) on the layer object.

Derived **2026-08-27** from build `20250718.01` via [recflare-2025-metadata-carve](../../il2cpp-analysis/references/recflare-2025-metadata-carve.md).

## Two separate config systems — do not confuse them

| system | reader | key style | source |
|---|---|---|---|
| **gate configs** | `MEPJMFNAPAB.LMKONLJOAEP<T>` | dotted `Econ.*`, `DataCollection.*`, `Backtrace.*`, `UGC.*` | your server's config object |
| **Statsig** | `MGDBOHJAGBN.LMKONLJOAEP<T>` on a layer from `MCIAFEMJFEE` (StatsigModel) | snake_case layer + param | **`https://statsigapi.net/v1`**, hardcoded (`JMNFDLFEBGD$$.cctor` `0x8E9E310`), header `STATSIG-API-KEY`, over **UnityWebRequest** (not BestHTTP, so a BouncyCastle TLS bypass does not apply) |

**Nothing in the dotted config can set a Statsig param.** Every read passes a hardcoded default
(`mov byte [rsp+0x20], 0` for bools) and there is no gate-config fallback.

## The single choke point

`MGDBOHJAGBN` is the **layer object**: `AKPIHMDHGLK()` / `MPAAEPPJIEI()` return strings (layer name /
rule id) and **`!!T LMKONLJOAEP(string paramName, !!T defaultValue)`** is the param getter. The
StatsigModel interface `MCIAFEMJFEE` hands out layers (`LCBOIKBHCLI(string layerName, bool exposure)`)
and gates (`IEHGMHKHILJ(string, bool)`); call sites dispatch to interface **slot 0x13**.

**Hook `MGDBOHJAGBN.LMKONLJOAEP<bool>`** (generic-shared: one RVA per shape) and key on
`AKPIHMDHGLK()` + `paramName` to force any boolean flag in the game. That beats byte-patching each
consumer — flags are spread across dozens of call sites.

## `watch_layer` — the whole watch menu

`RecRoom.Core.WatchUI.get_UseNewWatchArchitecture` `0x1889710` =
`layer("watch_layer").Get("new_watch_architecture_enabled", false)`. Params seen on `watch_layer`:

- **`new_watch_architecture_enabled`** -> `WatchUI.get_UseNewWatchArchitecture` `0x1889710`
- **`rrui_people_menu_enabled`** -> `WatchUI.get_UseRRUIPeopleScreen` `0x18897B0`
- `create_tab_enabled`, `copy_room_button_text`
- `browser_tabs_preserve_history_enabled` -> `BrowserModel`
- `router_enable_prefill_routes`, `router_prefill_group`, `fallback_router_prefill_group`,
  `router_hidden_page_pool_size`, `router_override_hidden_page_pool_size` -> `Router` /
  `StatsigRouterPrefillConfig`
- `depth_multiplier` -> `PaletteTheme`

Other readers of the layer: `RRUIRootScreen.ShowScreenAndGoToCreateMenu` `0x23B2C60`,
`ShowScreenAndGoToMyDormsPage` `0x23B5F50`, `GoToStoreScreenButtonController` `0x25580E0`,
`Router.GetTouchStatsigExperiment` `0x8C8EC20`.

## Other layers worth knowing

- `econ_store_layer` — **`use_unified_avatar_item_search`** picks
  `RRUIRootScreen.storeItemServerSearchRoute` (+0x350) over `storeItemSearchRoute` (+0x348) in
  `ShowScreenAndGoToStoreItemSearch` `0x23BB1E0`; also `cai_default_ordering`,
  `extra_purchasable_item_ids_in_default_search`
- `avatars_experiment_layer` — `default_tab_name` (`GoToStatsigOverrideDefaultCustomizePage`
  `0x252B830`; tabs `AvatarType/SkinColor/BodyPaint/Hair/Beard/Hat/Glasses/Earrings/Necklaces/Tops/
  ShoulderBack/Gloves/Belts/Bottoms/Shoes`)
- `avatar_customization_x_store_layer`, `core_tq_layer`, `creator_2024q1_tq_layer`,
  `betterintro_orientation_layer`, `interfaces_widgetwatch_ux_flow` (AppNavMenu params),
  `interfaces_2025q1_appnav`

Statsig degrades gracefully when unreachable (`'Statsig not ready for layer: '`,
`'... for gate: '`, `'... for experiment: '`, `'Timed out waiting for statsig ... using default.'`),
so an empty key just pins everything to defaults — it cannot turn flags ON.
