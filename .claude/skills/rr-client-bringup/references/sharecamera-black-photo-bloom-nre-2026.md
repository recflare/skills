# Black in-game photo = URP bloom threw inside ShareCamera's manual render (2026 build)

> `ArgumentNullException: Value cannot be null. Parameter name: value` from
> `MaterialPropertyBlock.SetTexture` ← `Blitter.BlitTexture` ← `PostProcessPass.SetupBloom`, with
> **`RecRoom.ShareCamera.EBULNOQVFJS`** at the bottom of the stack, means the capture render
> **aborted part-way through**. The photo is whatever was in the target `RenderTexture` when it
> aborted — i.e. **black**.
> ⚠️ **It also wedges the share camera**: the `endCameraRendering` hook never runs, so the capture
> promise is never settled, `[ShareCamera+0x2A0]` is never cleared, and every later shot is rejected
> with **`'A Render operation already exists'`**.
> **No server response is implicated** — this is entirely inside the render loop.

Derived **2026-10-20** from build `20260323.14`, from a live `Player.log`.

## How the capture actually works

**`RecRoom.ShareCamera.EBULNOQVFJS(Camera cam, RenderTexture target, Action<Camera> pre, Action<Camera> post, bool)`**
**`0xE77EF0`** — the capture routine, reached from `LHOCFVXPTOW(Camera)` `0xE7B380` inside the
coroutine `ShareCamera+OZCKAVUAAWF.MoveNext` `0xE97BD0`:

| # | site | what |
|---|---|---|
| 1 | `0xE77FCD` | `if (this.<pending> /*+0x2A0*/ != null)` → return `MRDAKWBRKMV.GUDOJFUBTFE("A Render operation already exists")` (`0xE78373`, literal `0xE77FBA`) |
| 2 | `0xE78021` | `[this+0x2A0] = new promise` |
| 3 | `0xE781D3` | `.Then(ShareCamera.ESLKPXRZQTP)` — success continuation `0xE784B0` |
| 4 | `0xE7821A` | `.SVIWMQAISAD(ShareCamera.ESGDSQYCHIG)` — **interface slot 5** on `RecRoom.Async.NXPIPFBMDQY`, i.e. the API's **Finally**; cleanup `0xE78390` |
| 5 | `0xE78264` | `RenderPipelineManager.beginCameraRendering += AEYPBQJZMJC.ENCKDYLKLYH` |
| 6 | `0xE78299` | `RenderPipelineManager.endCameraRendering += AEYPBQJZMJC.GZPKGXYQFTV` |
| 7 | `0xE782C4` | `cam.enabled = true` |
| 8 | **`0xE782FA`** | **`Camera.Render()`** — synchronous. **This is what throws.** |

`RecRoom.Async.NXPIPFBMDQY` method order is `XLBBHEFGNBM, XZWZNQSZZOI, RLHHDCOQUOX, Then, Error,`
**`SVIWMQAISAD(Action)`**`, ZISSNPREGJX, ZISSNPREGJX, Transform, YSGCLMXVFVI` — slot 5 is the
`Action`-taking, value-less, error-less one, so it is the Finally.

### The target swap happens *inside* `beginCameraRendering`

`AEYPBQJZMJC.ENCKDYLKLYH` **`0xE89B50`** (begin):

```
0xe89c5c  remove_beginCameraRendering     ; one-shot, unsubscribes itself
0xe89c67  Time.get_frameCount
0xe89ca3  Camera.get_targetTexture        ; save the camera's own target
0xe89cc2  Camera.set_targetTexture        ; swap in the capture RenderTexture
```

`AEYPBQJZMJC.GZPKGXYQFTV` **`0xE89FB0`** (end):

```
0xe8a072  remove_endCameraRendering
0xe8a086  Camera.set_targetTexture        ; restore the original target
0xe8a095  Behaviour.set_enabled           ; disable the camera again
0xe8a0bc  MRDAKWBRKMV.Complete            ; settle the promise -> photo is ready
```

## Why the photo is black, and why the camera then jams

The throw escapes `PostProcessPass.Execute` → `ScriptableRenderer.Execute` →
`UniversalRenderPipeline.Render` → `RenderPipelineManager.DoRenderLoop_Internal` → out of
`Camera.Render()` at step 8. So **`endCameraRendering` never fires**:

- nothing finished writing the capture `RenderTexture` → it keeps its cleared contents → **black**;
- `Camera.targetTexture` is **never restored** and the camera is **never re-disabled**;
- `MRDAKWBRKMV.Complete` is never called, so the promise never settles — and because
  `SVIWMQAISAD` is a **promise-settlement callback, not a CLR `try/finally`**, the cleanup
  `ESGDSQYCHIG` does not run either;
- `ESGDSQYCHIG` `0xE78390` is the only code that clears the guard
  (`mov qword ptr [rsi + 0x2A0], 0` at **`0xE78480`**) and removes the two render callbacks
  (`0xE7843F`, `0xE78474`), so **`[this+0x2A0]` stays non-null**.

➡️ **Every subsequent capture short-circuits at step 1** with
`'A Render operation already exists'` until the `ShareCamera` instance is rebuilt (put the tool away
/ respawn) or the client restarts.

⚠️ **Not verified**: whether `EBULNOQVFJS` wraps the `Camera.Render()` call in a managed
`try/finally` that would run the cleanup anyway — the toolkit does not expose the exception-handling
tables. **Decide it empirically**: `grep 'A Render operation already exists' Player.log`. Present ⇒
the state really is stuck; absent ⇒ something does clean up and only the one photo was lost.

The `JobTempAlloc has allocations that are more than the maximum lifespan of 4 frames old` warning
immediately afterwards is the expected side effect of a render loop abandoned mid-frame, not a
separate fault.

## Why bloom's source was null — two candidates, not distinguished

`SetupBloom` blits with a **null source RTHandle**. Both plausible causes are in the descriptor of
the swapped-in capture texture, not in any payload:

1. **A degenerate capture `RenderTexture`.** `ShareCamera.QQZCCWBSFHR(.Resolution, int, RenderTextureFormat, bool, string)`
   **`0xE7FD30`** builds the four targets from `BLLEJOXSUKY` `0xE74BF0` — `LiveRenderTexture (HDR)`,
   `CaptureRenderTexture (HDR)`, `LiveRenderTexture (LDR)`, `CaptureRenderTexture (LDR)`. The size
   comes from `get_CurrentPreviewResolutionOption` `0xE86810` (reads the serialized field
   `[this+0x2FC]`, **local, not server-driven**) fed into `YWVNGYMRGCX(int)` `0xE84F90`, which scales
   by `CurrentAspectRatio` at `[this+0x1C4]`. A zero/garbage aspect ratio yields a zero-dimension
   texture; URP then clamps the bloom mip chain to nothing and leaves the handle null.
2. **The mid-render target swap.** `cameraData` is built from the camera's *original* target before
   `ENCKDYLKLYH` substitutes the capture texture, so the post-process chain can be sized for one
   target and asked to blit another.

⚠️ `.Resolution` (typedef #50431) has **`POW2_8192x8192 = 0`** — the *default* value of the enum is
the **largest** resolution. Anything that leaves a `.Resolution` field zero-initialised asks for an
8192×8192 HDR target plus a bloom mip chain, which is a very plausible allocation failure. Watch for
this whenever a `.Resolution` reaches a render path from a parsed or defaulted value.

### Cheap discriminators

- Take a photo in the **other aspect ratio** (square vs wide — `LocalRequestSingleImage(bool isSelfieImage, bool isSquareImage, …)`) and at a different preview resolution (`ShareCameraPreviewResolution`: `Res_288P 0 · Res_360P 1 · Res_720P 2 · Res_1080P 3`). If only one combination fails, it is candidate 1.
- Note whether it reproduces **without alt-tabbing first** — the captured log has
  `OnApplicationFocus False` 35 s before and `True` 15 s before the throw, and a focus round trip can
  make URP reallocate RTHandles.

There is **no ShareCamera post-processing/bloom toggle** to switch off as a workaround — `msig`
on `ShareCamera` (255 methods) has no post/bloom/HDR-effect member, and no
`PostProcessing`/`Bloom` settings literal exists in the build.

## Unrelated noise in the same log window

- **`RoomQueryManager.QueryStaticListSource` NRE** two frames later (159224/159225) is the separate,
  already-documented discovery-carousel failure — see
  [post-join-residual-log-items-2026](post-join-residual-log-items-2026.md). It arrives via
  `CarouselListController+DiscoverySectionSpawnerImpl.OnModelChanged` → `RoomListViewModel.FetchData`
  (`async void`), is 404-driven, and has nothing to do with the camera.
- `Curl error 6: Could not resolve host: recroom-dataplane.rudderstack.com` and
  `[Backtrace]::Reponse code: 0, Response text: Cannot resolve destination host` are telemetry
  failing to phone home — expected when self-hosted, and switchable off per
  [telemetry-kill-switches](telemetry-kill-switches.md).
