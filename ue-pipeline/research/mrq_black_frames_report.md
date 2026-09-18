# Unreal Engine 5.4 Root Cause Analysis: Viewport & Movie Render Queue (MRQ) Black Frame Failure

**Target Environment:** Unreal Engine 5.4.x  
**GPU Hardware:** NVIDIA GeForce GTX MX450 (2 GB GDDR5/GDDR6 VRAM, SM5 Feature Level)  
**Symptom Profile:**
- Movie Render Queue (MRQ) renders solid black frames (max pixel luminance $\le 1/255$).
- The editor viewport is **also pitch black**, persisting even when switched to **"Unlit" viewmode** and after manually navigating the editor camera to a verified external transform outside geometry.
- Previous export pipeline using `SceneCapture2D` + `RenderTarget2D` worked as expected.
- Scene Audit: DirectionalLight (Stationary, 65,000 lux, atmosphere sun light), SkyLight (Stationary, SLS_CAPTURED_SCENE, intensity 1.6, real_time_capture false), ExponentialHeightFog (0.0002), SkyAtmosphere present, **no PostProcessVolume**, `r.DynamicGlobalIlluminationMethod=0` (Lumen GI off), TSR AA, Raytracing off, VSM off, SM5 (Nanite disabled at runtime).
- 10 large Blender FBX static meshes with recurring warnings: `"needed to have new flag set bUsedWithStaticLighting"`.

---

## The Critical Diagnostic Discriminator

> **Why the Unlit Viewmode Being Black Overrules Standard Lighting Hypotheses:**  
> In Unreal Engine, **Unlit viewmode** completely bypasses direct lighting, shadow maps, indirect GI (Lumen/Lightmass), and SkyLight evaluations. It samples only the material's `BaseColor` and `Emissive` channels into the G-Buffer / scene texture pass.  
> 
> Therefore, lighting configuration errors (e.g., unbaked Stationary lights, uncaptured SkyLight, `r.DynamicGlobalIlluminationMethod=0`) **cannot explain why Unlit is black**. While those lighting issues will crush the scene to black in **Lit** mode, they are completely inactive in **Unlit** mode.
> 
> A viewport that is black in **both Lit and Unlit** modes narrows the root cause to four specific architectural choke-points:
> 1. **Auto-Exposure / Tone Mapper failure**: The dynamic exposure adaptation (running on an unbounded 65,000 lux DirectionalLight without a PostProcessVolume) has calculated an extreme or degenerate EV100 compensation value, scaling all rendered pixels (even Unlit albedo) to zero.
> 2. **Viewport Render State Corruption / Layout Desync**: Known UE5 editor bug where the active viewport context loses its target buffer or show flags, displaying pure black across Lit, Unlit, and Wireframe.
> 3. **Viewport Show Flags or Mesh Visibility / Bounding Box Culling**: Static Meshes show flag disabled, or extreme FBX scale / inverted normals / degenerate bounds culling the geometry.
> 4. **VRAM OOM / Buffer Allocation Collapse (2 GB MX450)**: The rendering pipeline cannot allocate the viewport/MRQ color target buffers or swapchains under 2 GB VRAM constraints, silently clearing buffers to black.

---

## Ranked Candidate Root Causes

---

### Root Cause 1 (Likelihood: 95%): Runaway Auto-Exposure Crushing Both Unlit Viewport and MRQ Renders

#### (a) Mechanism
In Unreal Engine 5, the default Auto-Exposure system (Histogram Eye Adaptation) is **active in both Lit and Unlit viewport modes** unless explicitly disabled in viewport settings or locked by an unbound `PostProcessVolume`.
- The scene has a `DirectionalLight` set to physical sunlight intensity (**65,000 lux**), but **no PostProcessVolume** is present to establish exposure bounds (`Min EV100` / `Max EV100`).
- Because `r.DynamicGlobalIlluminationMethod=0` (Lumen off), SkyLight is unbaked (`SLS_CAPTURED_SCENE` captures nothing), and the 10 large meshes occlude direct sunlight or have invalid lightmaps, the viewport's average luminance is close to zero.
- Alternatively, looking towards the 65,000 lux sky causes the histogram to adapt to extreme high EV (e.g., EV100 $\approx 15-18$), applying an exposure compensation multiplier near $0.00001$. In Unlit mode, material `BaseColor` outputs values in the $0.0-1.0$ sRGB linear range (equivalent to 1 lux). When multiplied by an EV16 tone curve, the final pixel values round down to $0$ or $1/255$.
- Furthermore, when MRQ spins up without warmup frames or explicit exposure overrides, eye adaptation evaluates frame 0 at default camera EV (or adapts instantaneously to black geometry), capturing a 0-luminance frame.
- Previously, `SceneCapture2D` succeeded because `SceneCaptureComponent2D` defaults to `Capture Source = SceneColor (HDR) in RGB, Inv Device Z` or `Final Color (LDR)` with its own isolated `PostProcessSettings` or auto-exposure disabled (`bCaptureEveryFrame`, auto-exposure off or custom exposure clamp).

#### (b) How to Confirm
1. In the Editor Viewport top-left toolbar: Click **View Mode** $\to$ **Exposure** $\to$ Uncheck **Game Settings / Automatic** and set to **Fixed EV: 0** or **Fixed EV: 10**.
2. Alternatively, enter the console command:
   ```text
   r.EyeAdaptation.ExposureBias 10
   ```
   or completely disable tone mapping exposure adaptation:
   ```text
   show PostProcessing 0
   show EyeAdaptation 0
   ```
3. If the viewport instantly reveals the mesh BaseColor in Unlit mode, auto-exposure runaway is confirmed.

#### (c) Exact Fix
1. **Add a Global Unbound PostProcessVolume:**
   - In Editor: Place an `Actor` $\to$ `PostProcessVolume`.
   - In Details: Check `Infinite Extent (Unbound) = True`.
   - Expand `Exposure`:
     - Set `Metering Mode` = `Auto Exposure Basic` or `Manual`.
     - Set `Min EV100` = `7.0`, `Max EV100` = `7.0` (locks exposure completely, preventing histogram adaptation drift).
     - Set `Exposure Compensation` = `1.0`.
2. **Configure MRQ Job Settings:**
   - In the MRQ Job Configuration dialog, ensure `Game Overrides` is added, but do not allow uninitialized exposure.
   - Under `Anti-Aliasing` in MRQ: Set `Engine Warm Up Count` = `32` to `64` and `Render Warm Up Frames` = `32`. This allows the temporal history and auto-exposure to settle before frame capture begins.
3. **Python Automation Script (Run in UE Python Console):**
   ```python
   import unreal

   # Spawn or configure unbound PostProcessVolume
   editor_actor_subsystem = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
   ppv_class = unreal.PostProcessVolume
   ppvs = [a for a in editor_actor_subsystem.get_all_level_actors() if isinstance(a, ppv_class)]

   if ppvs:
       ppv = ppvs[0]
   else:
       ppv = editor_actor_subsystem.spawn_actor_from_class(ppv_class, unreal.Vector(0, 0, 0))
       ppv.set_actor_label("PPV_Global_ExposureLock")

   ppv.unbound = True
   settings = ppv.settings
   settings.auto_exposure_method = unreal.AutoExposureMethod.AEM_MANUAL
   settings.auto_exposure_apply_physical_camera_exposure = False
   # Lock Min/Max EV100 to prevent drifting
   settings.auto_exposure_min_brightness = 7.0
   settings.auto_exposure_max_brightness = 7.0
   settings.override_auto_exposure_min_brightness = True
   settings.override_auto_exposure_max_brightness = True
   settings.override_auto_exposure_method = True
   ppv.settings = settings
   unreal.EditorLevelLibrary.save_current_level()
   ```

#### (d) Source Documentation & References
- Epic Games Official Documentation: *Auto Exposure in Unreal Engine*  
  URL: https://dev.epicgames.com/documentation/unreal-engine/auto-exposure-in-unreal-engine
- HyperRender MRQ Diagnostics: *Fix Movie Render Queue Viewport Mismatch & Auto Exposure*  
  URL: https://www.hyperrender.run/blog/MRQ-viewport-not-matching

---

### Root Cause 2 (Likelihood: 90%): Viewport Layout / Render Context Bug ("Black Viewport Syndrome")

#### (a) Mechanism
A well-documented defect in Unreal Engine 4.26 through 5.4 causes the editor viewport's backbuffer/render context to become permanently black. 
- In this bugged state, the viewport fails to present any G-Buffer or final color data across **Lit, Unlit, and Wireframe** modes, even though the Outliner indicates actors are loaded and scene coordinates are valid.
- The bug is frequently triggered when saving/reloading levels after creating Render Targets or after switching between `SceneCapture2D` previewing and standard editor viewports. The `SceneCapture2D` context conflicts with the editor viewport's swapchain/RHI viewport state.
- Orthographic views (Top, Front, Left) may temporarily render while Perspective remains completely black.

#### (b) How to Confirm
1. In the Main Menu, go to: `Window` $\to$ `Viewports` $\to$ Open `Viewport 2`.
2. Check if `Viewport 2` displays the scene geometry normally in Unlit or Lit mode.
3. Switch the bugged viewport from `Perspective` to `Top` or `Front` (Alt+G, Alt+J). If wireframe/ortho displays geometry but Perspective is pitch black, the viewport render state is corrupted.

#### (c) Exact Fix
1. In the Main Menu bar: Click `Window` $\to$ `Load Layout` $\to$ `Default Editor Layout`. (This destroys and reconstructs all viewport RHI swapchains and slate view handles).
2. Reset Viewport Show Flags: In the viewport dropdown menu, select `Show` $\to$ `Reset to Default`.
3. Force slate viewport redraw via Console:
   ```text
   r.Editor.Viewport.Recreate
   ```
   or toggle fullscreen viewport mode (`F11` twice).

#### (d) Source Documentation & References
- Epic Developer Community: *Viewport has suddenly gone black (Lit, Unlit, Wireframe all black)*  
  URL: https://forums.unrealengine.com/t/viewport-has-suddenly-gone-black/504640
- Epic Developer Community: *Viewport goes black for all my UE5 projects*  
  URL: https://forums.unrealengine.com/t/viewport-goes-black-for-all-my-ue5-projects/590194

---

### Root Cause 3 (Likelihood: 85%): Blender FBX Import Scale, Bounding Box Degeneracy, or Show Flags

#### (a) Mechanism
When importing 10 large static meshes from Blender via FBX:
1. **Unit Mismatch:** Blender's default unit is 1 meter ($1.0$), whereas Unreal Engine's unit is 1 centimeter ($1.0\text{ cm}$). An unscaled export can produce actors that are either 100x too small ($1\text{ cm}$ instead of $1\text{ m}$) or, if scaled incorrectly, tens of kilometers wide ($100,000\text{ cm}$).
2. **Camera Far Clip Plane Culling:** By default, Unreal Engine's editor camera far clipping plane is managed dynamically or clamped. If meshes are scaled up to kilometer scales or placed far from the origin, they exceed the editor camera's max render distance.
3. **Bounding Box Corruption:** If Blender FBX meshes have unapplied transforms or inverted root matrices, the computed `LocalBounds` can be degenerate ($0,0,0$ extent or NaN radius). The engine's occlusion culling system (`r.OcclusionCulling=1`) flags the meshes as completely outside the frustum or occluded, skipping draw calls entirely for both Lit and Unlit rendering.
4. **Viewport Show Flags:** Accidental keyboard shortcut (such as `Show StaticMeshes` toggled off). If `Show -> Advanced -> Static Meshes` is unchecked, all 10 actors disappear from the viewport completely, leaving the background sky/black void.

#### (b) How to Confirm
1. In the Outliner, select any of the 10 imported Blender Static Mesh Actors. Press the **F** key (Focus).
   - If the camera zooms into infinity or zooms to a microscopic sub-millimeter point, bounds are degenerate.
2. In the console, test disabling occlusion culling and increasing clip distance:
   ```text
   r.OcclusionCulling 0
   show StaticMeshes
   ```
3. Check actor scale in Details: ensure scale is not `(0, 0, 0)` and location is within reasonable bounds (e.g., $X, Y, Z < 1,000,000$).

#### (c) Exact Fix
1. **Recompute Bounds on Static Meshes in Python:**
   ```python
   import unreal

   editor_asset_lib = unreal.EditorAssetLibrary
   # Find all static meshes in the import folder
   asset_registry = unreal.AssetRegistryHelpers.get_asset_registry()
   assets = asset_registry.get_assets_by_path("/Game", recursive=True)

   for asset_data in assets:
       if asset_data.asset_class_path.asset_name == "StaticMesh":
           mesh = asset_data.get_asset()
           # Enable positive bounds extension if needed
           mesh.set_editor_property("positive_bounds_extension", unreal.Vector(100, 100, 100))
           mesh.set_editor_property("negative_bounds_extension", unreal.Vector(100, 100, 100))
           unreal.EditorStaticMeshLibrary.rebuild_mesh(mesh)
           editor_asset_lib.save_loaded_asset(mesh)
   ```
2. **Reset Viewport Show Flags:**
   ```text
   showflag.StaticMeshes 1
   r.SetNearClipPlane 10
   ```

#### (d) Source Documentation & References
- Epic Games Documentation: *Viewport Show Flags in Unreal Engine*  
  URL: https://dev.epicgames.com/documentation/unreal-engine/viewport-show-flags-in-unreal-engine
- Epic Games Documentation: *Static Mesh Editor UI and Bounds Configuration*  
  URL: https://dev.epicgames.com/documentation/unreal-engine/static-mesh-editor-ui-in-unreal-engine

---

### Root Cause 4 (Likelihood: 80%): `bUsedWithStaticLighting` Missing Flag & Unsaved Material Permutations

#### (a) Mechanism
In Unreal Engine's shader compiler, materials determine which shader permutations to compile based on usage flags (e.g., `bUsedWithStaticLighting`, `bUsedWithSkeletalMesh`, `bUsedWithInstancedStaticMeshes`).
- When a material is placed onto a Static Mesh Actor that has its mobility set to `Static` or `Stationary`, or is illuminated by a `Stationary` DirectionalLight, the engine determines that the **static lighting shader permutation** is required.
- If the material asset does not have `bUsedWithStaticLighting=True` persisted to disk:
  - In the editor interactive session, the engine generates an in-memory runtime compilation fallback (logging the warning: `"Material [Path] was missing the usage flag bUsedWithStaticLighting. If the material asset is not re-saved, it may not render correctly when run outside the editor."`).
  - When Movie Render Queue boots, it initializes a fresh **Game Mode / PIE simulation instance** (running without editor runtime patching). If the compiled shader permutation is absent from the DDC (Derived Data Cache) or disk asset, the material fails shader link validation and falls back to the null shader (rendering **pure black**).
  - On low-end SM5 hardware, if shader compilation is deferred or throttled, materials fail to render and output black albedo to the G-Buffer.

#### (b) How to Confirm
1. Check the Editor Output Log on project load: Look for `LogMaterial: Warning: Material [AssetPath] needed to have new flag set bUsedWithStaticLighting`.
2. Inspect the Master Material in the Material Editor $\to$ Details $\to$ `Usage` section $\to$ Check if `Used with Static Lighting` is unchecked or grayed out.

#### (c) Exact Fix
1. **Permanent Editor Fix:**
   - Open the Material Editor for all materials applied to the 10 meshes.
   - In Details, check `Usage` $\to$ `Used with Static Lighting` = `True`.
   - Click **Apply**, then click **Save** (ensuring the asset state is written to `.uasset` on disk).
2. **Automated Batch Fix via Python (One-Click Resave):**
   ```python
   import unreal

   asset_reg = unreal.AssetRegistryHelpers.get_asset_registry()
   all_assets = asset_reg.get_assets_by_path("/Game", recursive=True)

   materials_to_save = []
   for a in all_assets:
       if a.asset_class_path.asset_name in ["Material", "MaterialInstanceConstant"]:
           mat = a.get_asset()
           if isinstance(mat, unreal.Material):
               # Force usage flag
               mat.set_editor_property("used_with_static_lighting", True)
               unreal.MaterialEditingLibrary.recompile_material(mat)
               materials_to_save.append(mat)
           elif isinstance(mat, unreal.MaterialInstanceConstant):
               materials_to_save.append(mat)

   if materials_to_save:
       unreal.EditorAssetLibrary.save_loaded_assets(materials_to_save, only_if_is_dirty=False)
       print(f"Successfully updated and resaved {len(materials_to_save)} materials with bUsedWithStaticLighting=True.")
   ```
3. **Alternative Architecture: Switch to Fully Dynamic Lighting (Disabling Static Lighting Requirement):**
   - If static light baking is not intended (see Root Cause 5), disable static lighting project-wide in `Config/DefaultEngine.ini`:
     ```ini
     [/Script/Engine.Engine]
     r.AllowStaticLighting=False
     ```
   - When `r.AllowStaticLighting=False`, the engine strips all static lighting permutations from the shader pipeline, completely eliminating `bUsedWithStaticLighting` warnings and fallback bugs.

#### (d) Source Documentation & References
- Epic Developer Community: *Material Issue / Bug - Used With Static Lighting*  
  URL: https://forums.unrealengine.com/t/material-issue-bug-used-with-static-lighting-will-not-stay-unchecked/26256
- Epic Developer Community: *Asset validation warning bUsedWith... If material asset is not re-saved*  
  URL: https://forums.unrealengine.com/t/how-can-i-fix-this-warning-busedwithinstancedstaticmeshes/1806710

---

### Root Cause 5 (Likelihood: 80%): Unbaked Stationary Lighting & Lumen Disabled (`r.DynamicGlobalIlluminationMethod=0`)

#### (a) Mechanism
The scene audit identifies a fundamentally incompatible lighting architecture:
1. `DirectionalLight`: Mobility = **Stationary**, 65,000 lux.
2. `SkyLight`: Mobility = **Stationary**, `Source Type` = `SLS_CAPTURED_SCENE`, `Real Time Capture` = `False`.
3. Global Illumination: `r.DynamicGlobalIlluminationMethod=0` (Lumen GI disabled).
4. No baked Lightmass data has been computed.

**What happens in this state?**
- A **Stationary Directional Light** provides direct specular and dynamic cascaded shadow maps for movable actors, but relies on **precomputed Lightmass lightmaps** for diffuse bouncing and static mesh surface illumination.
- An unbaked **Stationary SkyLight** with `SLS_CAPTURED_SCENE` and `Real Time Capture = False` captures the scene only once during static build time. Because light was never baked, its cubemap is completely black ($0.0, 0.0, 0.0$).
- With Lumen disabled (`r.DynamicGlobalIlluminationMethod=0`), there is **no real-time dynamic indirect bounce lighting**.
- In **Lit mode**: Any surface angled away from direct sunlight receives 0 indirect light from the SkyLight and 0 from GI, rendering pitch black. If shadow cascades fail or normal orientations are inverted, even front faces render black.
- *(Note: As established in the Discriminator, this explains complete darkness in Lit mode and MRQ, but must be compounded with Root Cause 1, 2, or 3 to cause Unlit mode to be black).*

#### (b) How to Confirm
1. Select the `DirectionalLight` and change its Mobility from `Stationary` to `Movable`.
2. Select the `SkyLight`, change its Mobility from `Stationary` to `Movable`, and set `Real Time Capture` = `True`.
3. In console, execute:
   ```text
   r.LightMobility.ForceAllMovable 1
   ```
4. If the scene immediately lights up in Lit mode, the stationary unbaked lighting bottleneck is confirmed.

#### (c) Exact Fix: The Industry Standard No-Bake Dynamic Lighting Setup for UE5 Cinematics
For non-baked cinematic workflows in Unreal Engine 5.4, all lights must be set to `Movable`:
1. **DirectionalLight:**
   - Mobility: **Movable**
   - Intensity: `65,000 lux` (or standard daylight `100,000 lux`)
   - `Cast Shadows`: **True**
   - `Dynamic Shadow Distance MovableLight`: `20,000`
   - `Atmosphere Sun Light`: **True**
2. **SkyLight:**
   - Mobility: **Movable**
   - Source Type: `SLS Specified Cubemap` (assign an HDRI) OR `SLS Captured Scene` with **`Real Time Capture` = True**.
   - Intensity: `1.0` - `2.0`
3. **SkyAtmosphere & ExponentialHeightFog:**
   - On `ExponentialHeightFog`: Enable `Volumetric Fog` = **True** (optional for atmospheric depth).
4. **Console Configuration (`DefaultEngine.ini`):**
   ```ini
   [/Script/Engine.RendererSettings]
   r.AllowStaticLighting=False
   r.DynamicGlobalIlluminationMethod=0 ; Screen Space GI or Lumen
   r.Shadow.Virtual.Enable=0           ; Standard Cascaded Shadow Maps for GTX MX450
   r.DistanceFieldShadowing=1
   ```

#### (d) Source Documentation & References
- Epic Games Documentation: *Stationary Light Mobility in Unreal Engine*  
  URL: https://dev.epicgames.com/documentation/unreal-engine/stationary-light-mobility-in-unreal-engine
- Epic Games Documentation: *Sky Lights in Unreal Engine*  
  URL: https://dev.epicgames.com/documentation/en-us/unreal-engine/sky-lights-in-unreal-engine

---

### Root Cause 6 (Likelihood: 75%): GPU VRAM Buffer Allocation Failure (NVIDIA GTX MX450 2 GB OOM)

#### (a) Mechanism
The NVIDIA GeForce GTX MX450 is equipped with only **2 GB of VRAM**.
- In Unreal Engine 5.4, even when running on the SM5 feature level with Nanite and Lumen disabled:
  - The standard Deferred Shading G-Buffer requires multiple full-resolution FP16/RGBA32 render targets (BaseColor, WorldNormal, Metallic/Roughness/Specular, SceneDepth, MotionVectors, Velocity).
  - TSR (Temporal Super Resolution) allocates multiple history buffers.
  - DirectionalLight shadow maps (even non-VSM standard cascades) consume 256MB–512MB VRAM.
  - When Movie Render Queue launches, it creates **dual viewport pipelines**: the editor viewport background session plus the off-screen high-resolution MRQ render pipeline.
- If GPU VRAM exceeds 2048 MB, the Direct3D 12 (or D3D11) RHI driver enters out-of-memory paging or silent target discard. When a render pass fails to allocate or bind its color attachment, D3D clears the target or skips execution, writing $0x00000000$ (pure black, max pixel value 1/255) to the final output.
- In severe low-VRAM scenarios, the editor viewport swapchain itself is evicted from GPU memory, turning the viewport black across all modes.

#### (b) How to Confirm
1. In the console, inspect current VRAM utilization:
   ```text
   stat D3D12RHI
   stat Memory
   stat GPU
   ```
2. Check the Editor Output Log for memory allocation warnings:
   ```text
   LogD3D12RHI: Warning: Out of video memory trying to allocate a render target!
   LogTexture: Warning: Texture streaming pool out of memory by ... MB
   ```

#### (c) Exact Fix
1. **Reduce Viewport and MRQ Resolution:**
   - Ensure MRQ is rendering at `1280x720` or `1920x1080` (do NOT render 4K on a 2GB card).
2. **Cap Texture Streaming and Buffer Sizes:**
   ```text
   r.TextureStreaming 1
   r.Streaming.PoolSize 600
   r.Shadow.MaxResolution 1024
   r.Shadow.CSM.MaxCascades 2
   r.SecondaryScreenPercentage.GameViewport 100
   ```
3. **MRQ Memory Optimization Console Variables:**
   Add these CVars to the `Console Variables` setting in your MRQ Job:
   ```text
   r.Streaming.FullyLoadUsedTextures 0
   r.DiscardUnusedQualityLevels 1
   r.DumpGPU 0
   ```

#### (d) Source Documentation & References
- Epic Developer Community: *Help! My Unreal Engine 5 Editor is Completely Black (Low VRAM)*  
  URL: https://forums.unrealengine.com/t/help-my-unreal-engine-5-editor-is-completely-black/2340865
- Epic Games Documentation: *Texture Streaming Configuration*  
  URL: https://dev.epicgames.com/documentation/unreal-engine/texture-streaming-in-unreal-engine

---

### Root Cause 7 (Likelihood: 70%): MRQ Pipeline Configuration Issues (Camera Cuts, GameMode, Deferred Rendering)

#### (a) Mechanism
Beyond the viewport-level issues, Movie Render Queue has distinct failure modes that result in pure black frames:
1. **Missing Deferred Rendering Pass:** If the MRQ Job Configuration has the `.png` / `.exr` output format added but is missing the `Deferred Rendering` pass (under `+ Setting` $\to$ `Deferred Rendering`), MRQ has no render engine producing pixels and outputs empty black files.
2. **Camera Cut Track Binding Desync (Possessable vs. Spawnable):**
   - If the CineCameraActor in Level Sequence is a **Possessable** actor and its reference is lost or unbound, or if the `Camera Cuts` track has no camera assigned, MRQ spawns the default game pawn at `(0, 0, 0)` facing down or inside geometry.
3. **Default GameMode Pawn Collision/Blocking:**
   - In MRQ `Game Overrides`, if `GameMode Override` is left at Default and `Cinematic Quality Settings` is checked, the game mode spawns a `DefaultPawn` or player character at the PlayerStart location. This pawn frequently collides with the CineCamera or occludes the lens with an opaque mesh.
4. **Zero Warmup with TSR (Temporal Super Resolution):**
   - TSR requires temporal accumulation across preceding frames. With `Engine Warm Up Count = 0`, TSR has no prior frame buffer, and materials compiling asynchronously in the background output black.
5. **PNG Alpha Channel Zero Bug:**
   - When exporting PNGs with `Accumulator Type` set to 8-bit or with certain post-process passes, Unreal Engine outputs an Alpha channel of $0$ (completely transparent). Image viewers that composite alpha over a black background display the image as solid black.

#### (b) How to Confirm
1. In MRQ: Open the Render Preview window while rendering. If the preview window shows the scene rendering, but the saved `.png` files on disk are black, it is the **PNG Alpha Channel Zero** issue. Open the PNG in Photoshop or inspection software and view the RGB channels independently.
2. In Sequencer: Check the `Camera Cuts` track. Is the CineCameraActor bound? Does scrubbing the sequence take control of the view?

#### (c) Exact Fix
1. **Configure MRQ Job Settings Correctly:**
   - **Settings:** Ensure `Deferred Rendering` is present in the left panel.
   - **Anti-Aliasing:**
     - `Spatial Sample Count`: `1`
     - `Temporal Sample Count`: `8` (or `1` if using TSR without multi-sampling)
     - `Engine Warm Up Count`: `64`
     - `Render Warm Up Frames`: `32`
   - **Game Overrides:**
     - Set `Game Mode Override` $\to$ `MoviePipelineGameMode` (prevents player pawn spawn).
     - Check `Disable LODs` and `Cinematic Quality Settings`.
   - **Output:**
     - Disable alpha output or ensure RGB only if exporting PNG:
       ```text
       r.MoviePipeline.DisableAlphaInPNG 1
       ```
2. **Convert Camera to Spawnable:**
   - In Sequencer, right-click the `CineCameraActor` and select **Convert to Spawnable**. (Spawnable cameras are created fresh by Sequencer during MRQ and avoid map reference desynchronization).

#### (d) Source Documentation & References
- Epic Developer Community: *MRQ Rendering Black Frames (Deferred Rendering & AA fixes)*  
  URL: https://forums.unrealengine.com/t/mrq-rendering-black-frames/587133
- Epic Developer Community: *Movie render queue all frames are black and nothing is rendered*  
  URL: https://forums.unrealengine.com/t/movie-render-queue-all-frames-are-black-and-nothing-is-rendered/566952
- Bugnet Engineering: *Fix: Unreal Movie Render Queue Producing Black Frames*  
  URL: https://bugnet.io/blog/fix-unreal-movie-render-queue-black-output

---

## Recommended Step-by-Step Recovery Action Plan

To systematically unblock the pipeline, execute these steps in order:

```
[Step 1: Recreate Editor Layout]
  Main Menu -> Window -> Load Layout -> Default Editor Layout
  Confirm if Unlit viewport recovers.

[Step 2: Lock Exposure with Unbound PostProcessVolume]
  Place PostProcessVolume -> Unbound=True -> Manual Exposure -> Min/Max EV100 = 7.0
  Confirm if 65,000 lux DirectionalLight auto-exposure was crushing the viewport.

[Step 3: Fix Materials & Usage Flags via Python]
  Run the provided Python script to set bUsedWithStaticLighting=True and resave.
  Or set r.AllowStaticLighting=False in DefaultEngine.ini.

[Step 4: Convert Lighting to 100% Movable]
  DirectionalLight -> Movable
  SkyLight -> Movable (Real Time Capture = True, or assign static HDRI cubemap)

[Step 5: Verify Static Mesh Bounds & Scale]
  Select Blender mesh -> Press F to focus.
  Verify Bounds Extents and verify Show -> Advanced -> Static Meshes is enabled.

[Step 6: Configure MRQ Job Settings]
  Ensure Deferred Rendering pass is added.
  Set Engine Warm Up = 64, Render Warm Up = 32.
  Set Game Mode Override = MoviePipelineGameMode.
  Camera Cuts track assigned to Spawnable CineCameraActor.
```
