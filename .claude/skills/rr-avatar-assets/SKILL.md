---
name: rr-avatar-assets
description: Resolve a Rec Room AvatarItemDesc to the shipped asset behind it and package shipped items as CustomAvatarItem exports - the resources.assets desc registry, the Addressables catalog, UnityFS bundle inspection, and the byte-exact CAI export folder format with deterministic ids. Use when you have opaque asset guids and need a name, a .bundle or an export folder, or when an avatar item will not render.
---

# Rec Room avatar assets

Two jobs, one pipeline:

1. **Identify** — you have an `AvatarItemDesc` (opaque asset guids, no name) and need the system
   name, the asset paths and the `.bundle` files that hold them.
2. **Package** — wrap those assets as a CustomAvatarItem export folder that matches the real
   exports byte for byte, with ids that survive a re-export.

```
desc  ->  resources.assets registry  ->  32-hex Unity asset guid
      ->  StreamingAssets/aa/catalog.json  ->  Assets/.../(Name).prefab  +  owning .bundle
      ->  (Name)/avatarItem.json + N/{bundles,thumbnail}
```

Tools are in **`tools/il2cpp/`**; `tools/il2cpp/README.md` has the full per-script table.

## Start here

| you have | run |
|---|---|
| a desc, want the name / assets / bundles | `py descresolve.py <data-dir> "<desc>"` |
| a 32-hex asset guid, want the bundle | `py aacatalog.py <aa-dir> <guid>` |
| a bundle, want to know what is in it | `py bundlepeek.py <dir> <bundles> <needles>` |
| a desc, want a finished export folder | `py caiexport.py fromdesc <data-dir> "<desc>" <out> [outfitType]` |
| an export folder, want it checked | `py caiexport.py verify <dir>` |
| just the ids for a desc | `py caiids.py "<desc>"` |

`<data-dir>` is e.g. `C:\Games\recflare-2023\RecRoom_Data`; `<aa-dir>` is its
`StreamingAssets\aa`. Note the 2023 build's data dir is `RecRoom_Data`, the 2025 build's is
`Recroom_Release_Data`.

## The four traps

These are the ones that produce a **confident wrong answer**, not an error:

| trap | what it looks like | the note |
|---|---|---|
| Descs are stored as 22-char **base64url** guids as well as dashed ones | decode a token, grep the dashed guid, get `0 hits` across the whole install and conclude the item is not in the build | [desc-registry-2023-layout](references/desc-registry-2023-layout.md) |
| A registry key is **not always one token** | the two halves of a combination desc each resolve to nothing; only the joined `a,b,` key exists | [desc-registry-2023-layout](references/desc-registry-2023-layout.md) |
| An itemId and a desc are **adjacent fields**, not one string | a pasted `id,desc` concatenation matches nothing anywhere | [desc-registry-2023-layout](references/desc-registry-2023-layout.md) |
| The **system name is not unique** | several descs resolve to one prefab name, so name-keyed ids merge distinct variants into one item | [cai-export-format](references/cai-export-format.md) |

Two more that bite at load time rather than lookup time:

- **Unity version.** The `S:\RecRoom\1` export library is `6000.0.27f1`; recflare-2025 runs
  `2021.3.41f1` and recflare-2023 runs `2020.3.33f1`. Unity refuses a bundle from a newer major
  version. Check before assuming an export will load.
- **Packaging.** Shipped built-ins are **Addressables** bundles with external dependency bundles.
  CAI bundles are self-contained `Main`+`Material` pairs whose *internal* name is derived from
  `UnityAssetId`. `caiexport.py` builds a correct wrapper around a shipped bundle, but that bundle
  still cannot resolve its dependencies — converting one to the other is a Unity **rebuild**, not a
  file copy.

## Reference notes

| note | one line |
|---|---|
| [desc-registry-2023-layout](references/desc-registry-2023-layout.md) | Both desc spellings, the two registry tables (material vs prefab), the item-id→name table, and the guid→asset-path→`.bundle` walk through the Addressables catalog. |
| [cai-export-format](references/cai-export-format.md) | The export folder layout and byte-exact formats (SHA-256 hashes, System.Text.Json default encoder, `AdditionalConfiguration` decoded), plus the desc-derived deterministic id scheme. |

Related skills: [rr-client-bringup](../rr-client-bringup/SKILL.md) for why a *built-in* avatar item
silently fails to render (`avatar-item-desc-registry` — the 2025 client's baked
`descToCaidMapping`), [il2cpp-analysis](../il2cpp-analysis/SKILL.md) for the UnityFS/LZ4 scanning
that `bundlepeek` and `bundlescan` share, and [wire-shapes](../wire-shapes/SKILL.md) for the
`customAvatarItems` routes and the `OutfitType` table (`Shirt 101`, `CustomShirt 105`, `Wrist 200`…).

## Verifying a change to any of this

Every claim in the notes was established by round-trip, and the round-trips are cheap to repeat:

- `caiexport.py verify "S:\RecRoom\1\(Floaties_Wrist)"` — the reference export must pass.
- Rebuilding `(Floaties_Wrist)` from its own parts must give **13 files, 0 differences**.
- `caiexport.py fromdesc` run twice, the second time with a different *spelling* of the same desc,
  must give **0 byte differences and 0 orphans**.
- `descresolve.py` on `E9VTiIVFPEa-OuQRto0e_Q,…` must end with `SYSTEM NAME: (SteamPunk_Shirt)`.

If a control fails, suspect the toolkit or the data dir before believing a negative result — a silent
`0 hits` has been wrong three separate ways here.
