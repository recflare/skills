# Econ store layer — the RRO Items / unified-search split

> Two accounts get different store UIs because `econ_store_layer / use_unified_avatar_item_search` buckets per user at statsigapi.net: false (the hardcoded default) shows the "RRO Items" / UGC chips, true shows the unified search screen that calls api/customAvatarItems/v1/search. Nothing on your server can influence it.

Diagnosed **2026-09-22** on build `20250718.01`.
Extends [statsig-layers-and-hook-point](statsig-layers-and-hook-point.md) (the layer system and the choke point) and
[avatar-item-desc-registry](avatar-item-desc-registry.md) (whose bundle-scan recipe the last section corrects).

## Symptom

Two users on the same server, same build, see different avatar-item stores:

| user | sees |
|---|---|
| A | a **"RRO Items"** toggle chip beside a UGC chip |
| B | a unified search screen that issues `POST api/customAvatarItems/v1/search` |

No server-side difference explains it, because the flag never reaches the server.

## The flag

**Layer `econ_store_layer`, param `use_unified_avatar_item_search`**, read with a **hardcoded default
of `false`** — `AGUI.StackedUI.RRUIRootScreen.ShowScreenAndGoToStoreItemSearch` `0x23BB1E0`:

```
0x23BB316  mov byte ptr [rsp+0x20], 0     ; defaultValue = false
0x23BB31B  call <layer param getter>
0x23BB320  test rax, rax
0x23BB323  je   ...                        ; branch
```

| value | result |
|---|---|
| **`false`** (default) | split chips — **`[RROItemsToggleChip]`** / UGC |
| **`true`** | unified avatar-item search → `api/customAvatarItems/v1/search` |

Three consumers switch on it, so screen, list and CAI list stay in step:
`AGUI.StackedUI.RRUIRootScreen.ShowScreenAndGoToStoreItemSearch`,
`RRUI.Data.StoreItemListModel.FKBOHBEFDIB` `0xB4E620`,
`RRUI.Data.CustomAvatarItemListModel.FFJBJHDOMAJ` `0x26443D0`.

## `econ_store_layer` — the four params

| param | where it lives | notes |
|---|---|---|
| `use_unified_avatar_item_search` | **DLL** (1 literal) | the split/unified switch above |
| `RRO_items_search_title` | **prefab only** (0 literals in the DLL) | chip label, default `"RRO Items"` |
| `UGC_search_text_title` | **prefab only** | the UGC chip's label |
| `has_warning_banner` | prefab | |

## ⚠️ Statsig bindings live in PREFABS, not GameAssembly.dll

`RRO_items_search_title` and `UGC_search_text_title` return **zero** hits in
`out/stringliteral.json`. They are Statsig-bound component fields serialised into prefabs — the raw
bytes read:

```
Models.Statsig  Assembly-CSharp   econ_store_layer   RRO_items_search_title   RRO Items
```

So **a param's absence from the DLL does not mean it does not exist.** Anything bound on a UI
component — label text, visibility — is only findable by scanning the bundles. The C#-read params
(like `use_unified_avatar_item_search`) *are* in the literal pool; the prefab-bound ones are not.

## Why two users diverge

Statsig is fetched from **`https://statsigapi.net/v1`**, hardcoded, `STATSIG-API-KEY` header, over
UnityWebRequest — it never touches your host. So either:

1. **one client cannot reach statsigapi.net** (firewall, DNS, proxy, offline at boot) and falls back
   to the hardcoded `false`, while the other gets the live value; or
2. **both reach it** and Rec Room's own Statsig project buckets the two account ids into different
   experiment arms.

Either way it is outside server control, which is what makes it look inexplicable.

**To make it deterministic:** block `statsigapi.net` (every flag falls to its hardcoded default —
`false` here, so everyone gets the RRO Items split), or hook
`MGDBOHJAGBN.LMKONLJOAEP<T>(paramName, defaultValue)` and key on `AKPIHMDHGLK() == "econ_store_layer"`
plus the param name ([statsig-layers-and-hook-point](statsig-layers-and-hook-point.md)). Blocking is simpler; hooking is the
option if you actually want the unified arm rather than merely consistency.

## ⚠️ bundlescan.py: the zeroed-bundle-directory trap

[avatar-item-desc-registry](avatar-item-desc-registry.md) says to scan `Recroom_Release_Data`. **There is more than one copy, and
not all of them are readable.** On this machine:

| path | first 8 bytes | usable |
|---|---|---|
| `C:\Games\Recroom_Release_Data\...\StandaloneWindows64` | `00 00 00 00 00 00 00 00` | **no** |
| `C:\Games\recflare-2025\Recroom_Release_Data\...\StandaloneWindows64` | `UnityFS\0` | **yes** |
| `C:\Games\recflare\Recroom_Release_Data\...\StandaloneWindows64` | `UnityFS\0` | yes (older build) |

`bundlescan.py` skips any file whose header is not `UnityFS` **without counting it as a failure**, so
the zeroed copy reports `scanned=0 failed=0 hits=0` — which reads exactly like "the string does not
exist". The working scan is `scanned=2745 failed=0 ... secs≈65`.

**Always include a positive control needle and check `scanned` is non-zero**, e.g.
`python bundlescan.py <dir> "rro items,inventions"`. That is what caught this; without the control
the empty result would have been reported as a real absence.
