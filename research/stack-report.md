# Zero-budget, open-licence stack (current plan)

**Constraints (2026-09-25):** the games will be released as free, open-source software (GPL, MIT or Apache-style licences). There is no spending beyond the existing Claude (includes Claude Code) and ChatGPT accounts.
The paid options further down (Meshy, fal, ElevenLabs, Godot MCP Pro) are **out of scope**. Keep them only as references.

| Area | Pick | Licence of the tool / its output |
|---|---|---|
| Coding agent | Claude Code (in the Claude plan). Codex CLI (included with ChatGPT) can act as a second opinion or reviewer | Output belongs to you |
| Engine | Godot 4.7 | MIT |
| Engine MCP | hi-godot/godot-ai, or Coding-Solo/godot-mcp. For screenshots, a small script that runs the game under Xvfb and saves the viewport to PNG, instead of Godot MCP Pro | MIT |
| 3D | Blender 5 + Blender MCP (official Blender Lab MCP or ahujasid/mcp-for-blender), plus batch `blender -b -P` Python scripts that Claude writes | Blender GPL; your models are yours |
| 3D art direction | Pick a style Claude can build procedurally: stylised, toy-like or diorama, low to mid poly, with the "wow" coming from Godot lighting, shaders and particles rather than sculpted detail | |
| Ready-made 3D and animation | Quaternius (CC0 animated characters, Universal Animation Library), Kenney (CC0), Poly Haven (CC0), Poly Pizza (only models marked CC0 or CC-BY). Rigify in Blender for custom rigs | CC0 / CC-BY |
| Textures and HDRIs | ambientCG and Poly Haven (CC0), plus procedural textures and shaders written by Claude | CC0 |
| 2D images (concept art, UI, sprites, texture bases) | ChatGPT image generation, done by hand in the ChatGPT app (OpenAI assigns output rights to the user). Local alternative: FLUX.2 klein 4B or FLUX.1 schnell (both Apache-2.0) through ComfyUI, quantised to fit 6 GB (speed not tested) | Output yours; model weights Apache-2.0 |
| Sound effects | jsfxr (Claude writes the parameters and renders WAV), Python/NumPy synthesis written by Claude, Freesound (only clips marked CC0), Kenney audio (CC0) | Unlicense / CC0 |
| Music | Claude-composed MIDI or tracker files (Furnace/OpenMPT) rendered with FluidSynth and a free SoundFont (FluidR3_GM, MIT; GeneralUser GS). ACE-Step 1.5 (MIT, under 4 GB VRAM) runs locally to generate stems | MIT / your own work |
| Reference capture | MAME, VICE, FS-UAE/Amiberry, DOSBox Staging | GPL etc. |
| Hosting | GitHub (code + git-lfs), itch.io, Godot web export | Free |

**Avoid in an open-source repo:**
- Mixamo: Adobe's terms don't allow redistributing raw asset files.
- Stable Audio Open and Stable Fast 3D: the Stability community licence isn't an open licence.
- FLUX.2 [dev] and klein 9B: non-commercial weights.
- Hunyuan3D open weights: the licence excludes the EU, UK and South Korea.
- Suno and Udio free tiers: non-commercial, or no ownership of the output.
- ElevenLabs free tier: requires attribution and is non-commercial.

**Licensing the release:** code under GPL-3.0 or MIT, and assets under CC BY-SA 4.0 or CC0 (software licences fit art badly). Keep a `CREDITS`/provenance file listing every third-party asset with its licence and every AI-generated asset with its tool. Note that purely AI-generated output may not be copyrightable in some jurisdictions (e.g. US), which is harmless for a free release.

**Still applies:** use original names, and never ship original sprites, maps, music or sound. Re-implement mechanics from observation. The Wikipedia screenshots in `catalog/` are fair-use reference material; don't commit them to a public repo.

---

# AI-driven dev stack for remaking 80s/90s games

Research date: 2026-09-25. The aim is a solo developer on Linux, with Claude Code (Opus) doing most of the work. The target look is "Pac-Man Championship Edition", which means neon, bloom, particles and very clean readable shapes.

Target dev GPU: about **6 GB VRAM**. That GPU rules out running most open-weight 3D and image generators locally, so the stack below leans on hosted APIs for heavy generation. It keeps local models only where they fit in 6 GB.

Legend: [V] = verified on a primary source (repo, vendor page, distro package index). [S] = secondary source only (blog, aggregator). [?] = could not verify, treat with caution.

---

## 0. TL;DR: recommended stack

| Category | Pick | Alternatives |
|---|---|---|
| Engine | **Godot 4.7.x** . Text scenes (`.tscn`/`.tres`), GDScript, MIT | Babylon.js or Three.js with Playwright MCP (web). Bevy with `bevy_brp_mcp` (Rust). Unity and Unreal are not recommended here |
| Engine MCP | **godot-ai** (hi-godot, MIT, needs Godot 4.7+). Add **Godot MCP Pro** ($15 one-time) if you want game-runtime screenshots and input simulation | Coding-Solo/godot-mcp (MIT, CLI-only, no plugin). tugcantopaloglu/godot-mcp fork |
| "See the result" loop | Your own `tools/capture.sh`: run Godot under **Xvfb**, then `--write-movie` or a script that calls `get_viewport().get_texture().get_image().save_png()`. Claude reads the PNGs. Tests use **GdUnit4** | MCP screenshot tools (Godot MCP Pro). PlayGodot, from Randroids-Dojo skills |
| Claude skills | **GodotPrompter** (56 Godot skills) or **Randroids-Dojo/Godot-Claude-Skills** (GdUnit4, PlayGodot). Study **htdt/godogen** as a reference pipeline | alexmeckes/godot-claude-skills, HubDev-AI/godot-ai-builder |
| 3D DCC | **Blender 5.x** plus the **official Blender Lab MCP** (v1.0.3, 2026-09-11). Also plain `blender -b -P script.py` batch scripts, which Claude writes and runs directly | ahujasid/blender-mcp (now "mcp-for-blender", MIT, about 29k stars), which has Poly Haven, Sketchfab, Poly Pizza, Hyper3D Rodin and Hunyuan3D built in |
| AI 3D generation | **Meshy** (official MCP, text/image-to-3D, retexture, remesh, rig, animate; paid plans give full commercial ownership) | Tripo (cheapest, wide rig taxonomy; its official MCP is stale, so use it through fal MCP). Rodin Gen-2 (best mesh quality, reachable from blender-mcp). TRELLIS.2 (MIT, but needs 24 GB VRAM, so run it on a rented GPU) |
| Rigging and animation | Meshy/Tripo auto-rig for props and creatures. **AccuRIG 2** (free) plus ActorCore, or Mixamo, for humanoid soldiers | UniRig (MIT, self-hosted). Hand-written procedural animation in GDScript (often best for arcade games) |
| Engine interchange | **glTF 2.0 (.glb)** from Blender into Godot. Godot can also import `.blend` directly when Blender is on PATH | FBX only when a rigging tool forces it |
| 2D images, concept art, UI, textures | **GPT Image 2** via API (native transparent PNG) for sprites, UI and icons. **Nano Banana Pro** (Gemini 3 Pro Image) for edits and consistency. Both are reachable through the **fal MCP** (`mcp.fal.ai/mcp`) | FLUX.2 [klein] 4B (Apache-2.0, small enough to try locally) through ComfyUI plus **Comfy-Org/comfy-mcp**. Retro Diffusion MCP for true pixel art. ArmorLab or Poly Haven/ambientCG for PBR |
| VFX and shaders | **Claude writes them directly**: Godot shading language, GPUParticles2D/3D, WorldEnvironment glow/bloom, Compositor effects. This covers most of the PMCE look | Generated flipbook textures from image models for explosions and smoke |
| SFX | **ElevenLabs Sound Effects v2** through the official hosted **ElevenLabs MCP** (`api.elevenlabs.io/v1/mcp`) | **jsfxr** (npm, plus an `sfx` MCP/CLI) for procedural retro bleeps. Stable Audio Open (community licence, fine under $1M revenue) |
| Music | **ACE-Step 1.5** (MIT, local, fits in under 4 GB VRAM, so it fits a 6 GB card) for BGM stems. For tight arcade loops, **Claude-authored music** in Strudel, ABC or tracker formats (Furnace/OpenMPT) or MIDI rendered with FluidSynth | Suno (paid plan only; ownership is murky). ElevenLabs Music is **not** usable for a multi-platform commercial game without an Enterprise plan (see §5) |
| Adaptive music | Godot built-ins: **AudioStreamInteractive** (state switching), **AudioStreamSynchronized** (layers/stems), AudioStreamPlaylist | FMOD/Wwise are unnecessary here |
| Reference capture | **MAME 0.289** (Qix, Arkanoid), **VICE 3.10** (C64 Boulder Dash), **FS-UAE 3.2.35** or **Amiberry** (Amiga Cannon Fodder, Z), **DOSBox Staging 0.83** or **DOSBox-X** (Alley Cat, Z DOS). All except DOSBox-X are commonly packaged on Linux | ffmpeg or OBS for recording. MAME `-aviwrite` / `-snapshot` for scripted captures |
| Version control | git plus **git-lfs 3.8** (`dev-vcs/git-lfs`). Track `*.glb *.png *.wav *.ogg *.blend *.psd` | Keep generation prompts and seeds as text next to the assets so Claude can regenerate them |

**Why Godot:** every artifact Claude has to touch is plain text: scenes, resources, scripts, shaders, project settings, input maps and even the import settings (`.import`). It is MIT with no fees or accounts, it is packaged natively on Linux, it runs headless for tests and under Xvfb for pixel capture, and it has the richest MCP and skills ecosystem of any open engine in 2026. Built-in glow, HDR output (new in 4.7), GPUParticles and adaptive music cover the PMCE aesthetic without middleware.

**Why hosted APIs for generation:** 6 GB VRAM will not run TRELLIS.2 (24 GB reference), full Hunyuan3D 2.1 (about 29 GB for shape plus texture) or FLUX.2 [dev] (32B). Budget roughly $20–60 a month across Meshy, fal and ElevenLabs during production, or rent a GPU by the hour for open models.

**Suggested Claude Code MCP config (sketch):**
```bash
claude mcp add godot-ai -- godot-ai attach                     # after enabling the plugin in the editor
claude mcp add blender -- uvx mcp-for-blender                  # or the official Blender Lab MCP ("blender-mcp" entry point)
claude mcp add --transport http fal-ai https://mcp.fal.ai/mcp --header "Authorization: Bearer $FAL_KEY"
claude mcp add --transport http elevenlabs https://api.elevenlabs.io/v1/mcp   # OAuth
npx -y @meshy-ai/meshy-mcp-server                               # Meshy official (stdio), with MESHY_API_KEY
```
Check each project's README for the exact current command. These MCPs move fast.

---

## 1. Game engine

### What matters for AI-driven development
1. **Text-based project format.** Claude can diff, grep and edit it without the GUI.
2. **Headless or CLI run and test.** Claude can run the game, the tests and the exports.
3. **Pixel capture.** Claude (which is multimodal) can *look* at frames and compare them with reference captures of the original game.
4. **MCP server** for live editor and runtime introspection. This is useful but secondary, because 1–3 already give a full loop.

### Godot 4.x (recommended)
- **Version:** 4.7 stable, released 2026-06-18 ("Lights, Camera, Action!"). It adds AreaLight3D, HDR output, inline shader previews, the new Asset Store and Control offset transforms for UI animation. Latest is 4.7.2 (2026-08-18). [V] https://godotengine.org/releases/4.7/ , https://en.wikipedia.org/wiki/Godot_(game_engine)
- **Licence:** MIT, free.
- **Headless:** `--headless` disables rendering entirely, so it cannot produce screenshots. For pixels, run under **Xvfb** with the GL Compatibility (or Forward+) renderer and use `Viewport.get_texture().get_image()` or Movie Maker (`--write-movie out.png --fixed-fps 60 --quit-after N`). [S] https://github.com/godotengine/godot-proposals/issues/5790 plus several CI repos found in search
- **Testing:** **GdUnit4** v6.1.x supports Godot 4.5–4.6.3, and master tracks 4.7.1+. It has a CLI runner and JUnit/HTML reports. [V] https://github.com/godot-gdunit-labs/gdUnit4 . GUT is an alternative.

**Godot MCP servers (2026):**
| Server | Licence/cost | Notes |
|---|---|---|
| **hi-godot/godot-ai** | MIT, free | 46 tools and 120+ ops: scenes, nodes, scripts, signals, UI, materials, animation, particles, cameras. Editor plugin with a "Configure" button for Claude Code; `godot-ai attach` over stdio. Requires Godot 4.7+. About 2.6k stars. [V] https://github.com/hi-godot/godot-ai |
| **Godot MCP Pro** (youichi-uda) | Proprietary, **$15 one-time** | 187 tools, including **editor and game viewport screenshots, multi-frame capture, keyboard/mouse/action input simulation with frame timing**, and runtime analysis. Node.js plus a WebSocket plugin. Linux is not stated but should work (Node plus a Godot plugin) [?]. [V] https://github.com/youichi-uda/godot-mcp-pro , https://godotengine.org/asset-library/asset/4961 |
| **Coding-Solo/godot-mcp** | MIT | About 5.8k stars. Launches the editor, runs the project, captures debug output, creates scenes and manages UIDs. **No plugin needed, and no screenshots.** A good minimal option. [V] https://github.com/Coding-Solo/godot-mcp |
| tugcantopaloglu/godot-mcp | MIT (fork) | 157 tools, GDScript and C#, "tested with Godot 4.7". [S] https://github.com/tugcantopaloglu/godot-mcp |
| StraySpark Godot MCP | Commercial, from $39.99 | 137 tools. [S] https://www.strayspark.studio/blog/godot-mcp-setup-claude-code-2026 |

Caveat reported by StraySpark: GDScript's dynamic typing causes more failed tool calls, and the editor's auto-reload can conflict with agent edits. Mitigation: use static typing everywhere (`var x: int`), and let Claude edit files while the editor is closed, or rely on the MCP for live edits.

**Claude Code skills and reference pipelines for Godot:**
- **htdt/godogen** (MIT, about 7k stars). Autonomous game generation for Godot 4 (C#), Bevy and Babylon.js with Claude Code or Codex. Assets come from Gemini/Grok images and Tripo3D models. It **judges results from the running game** (live observation or video). This is the closest published analogue to this project and worth reading even if you do not adopt it. [V] https://github.com/htdt/godogen
- **jame581/GodotPrompter**: 56 domain skills (architecture, physics, shaders, audio, UI, and more). https://github.com/jame581/GodotPrompter
- **Randroids-Dojo/Godot-Claude-Skills**: GdUnit4, PlayGodot end-to-end automation, export helpers. https://github.com/Randroids-Dojo/Godot-Claude-Skills
- alexmeckes/godot-claude-skills (knowledge skills that complement godot-mcp), HubDev-AI/godot-ai-builder (plugin with 14 skills, 28 MCP tools and a Stop hook), sonic7881963/gamedev-skills (Godot headless testing).

### Unity 6
- Official **Unity MCP server** ships with the Unity AI assistant package (open beta, May 2026). [S] https://unity.com/blog/unity-ai-mcp-how-to-get-started , https://app.cinevva.com/news/2026-05-04-unity-ai-open-beta
- Community **CoplayDev/unity-mcp** (MIT, free, widely used). https://github.com/CoplayDev/unity-mcp
- Personal is free under $200k revenue and there is no runtime fee. [S] https://unity.com/blog/unity-is-canceling-the-runtime-fee . Reportedly **Personal users need a paid Unity AI subscription to use the official MCP** [S/?] https://discussions.unity.com/t/request-for-official-clarification-unity-mcp-access-subscription-requirements-and-future-policy/1720323
- Downsides for this use case: YAML scenes are text but full of GUIDs and fileIDs, so they are hard for an LLM to hand-edit safely. The engine is proprietary with account and licence friction. The Linux editor exists but is second-class. **Not recommended.**

### Unreal Engine 5.7/5.8
- UE 5.7 has an experimental in-editor AI Assistant. **UE 5.8 (2026-06-17) ships a first-party "Unreal MCP" plugin**, free and included. [S] https://dev.epicgames.com/documentation/unreal-engine/unreal-mcp-in-unreal-editor , https://www.pugetsystems.com/blog/2026/07/09/unreal-engine-mcp-hands-on-testing-ai-inside-the-editor/
- Downsides: binary `.uasset`/Blueprints (much less agent-friendly), a huge install and slow iteration, and a 5% royalty above $1M. Linux editor support for the MCP plugin is unverified [?]. It is overkill for Qix or Arkanoid. **Not recommended.**

### Bevy (Rust)
- Bevy is code-only (ECS) and has no editor, which is actually great for an agent. **bevy_brp_mcp / natepiano/bevy_brp** (v0.22.x) launches, inspects and mutates running apps via the Bevy Remote Protocol, with screenshots through `bevy_brp_extras`. [V] https://github.com/natepiano/bevy_brp , https://docs.rs/crate/bevy_brp_mcp/latest
- Downsides: breaking API changes on each release (LLM knowledge lags behind), slow Rust compile times, no visual editor for you to tweak things, and less built-in post-processing and particle tooling than Godot. A viable alternative if you prefer Rust.

### Web (Three.js / Babylon.js / PlayCanvas)
- Three.js has a WebGPURenderer and TSL. Babylon.js 8/9 is WGSL-native, with physics, GUI and an Inspector built in. [S] https://app.cinevva.com/blog/2026-06-09-web-game-engines-2026-comparison
- LLMs know Three.js extremely well, and "vibe-coded" web games are the most common AI-dev showcase.
- **Microsoft Playwright MCP** (`@playwright/mcp`) gives Claude a browser. WebGL canvases have an empty accessibility tree, so use screenshot/vision mode. [S] https://mcp.directory/blog/playwright-browser-mcp-guide-2026
- Pros: instant sharing (itch.io or a URL) and no build step. Cons: you have to assemble the engine yourself (audio mixing, post-processing and particles are all DIY or via libraries), and there is no scene editor.
- **Recommendation:** a strong alternative if browser distribution is the priority. Babylon.js is the more "engine-like" of the two, and godogen supports it.

---

## 2. 3D assets

### Blender plus MCP
**Official Blender Lab MCP.** Built by Blender developers and launched with Anthropic's "Claude for Creative Work" connectors (2026-04-28). Anthropic also funds Blender.
- It is an add-on inside Blender that talks over a TCP socket to a standalone MCP server (`blmcp`, entry point `blender-mcp`, stdio). It exposes the full Python API, blend-file forensics (datablock inventory, missing files, linked libraries), **viewport screenshots and thumbnail renders**, and search over the Python API reference and manual.
- Latest is **v1.0.3 (2026-09-11)**. It is a Lab project, "outside the current Blender roadmap".
- Security: it executes LLM-generated code with no guards.
- [V] https://projects.blender.org/lab/blender_mcp , https://www.anthropic.com/news/claude-for-creative-work , https://digitalproduction.com/2026/04/30/anthropic-funds-blender-ships-claude-connector/

**ahujasid/blender-mcp** (now published as `mcp-for-blender`). MIT, about 29k stars, Blender 3.0+, Python 3.10+ and uv.
- Tools cover object create/modify/delete, materials, scene inspection, arbitrary Python execution and GLB/FBX export.
- Integrations: **Poly Haven** (CC0 HDRIs, textures, models), **Sketchfab** (API key), **Poly Pizza** (low-poly), **Hyper3D Rodin** (text/image-to-3D) and **Hunyuan3D** (Tencent Cloud API or a self-hosted local API).
- Limits: downloads block Blender's UI thread, Poly Pizza's Cloudflare may block VPN or cloud IPs, and there is an optional `BLENDER_MCP_SAFE_MODE=1`.
- Install: `claude mcp add blender uvx mcp-for-blender`.
- [V] https://github.com/ahujasid/blender-mcp
- A DeemosTech fork adds deeper Rodin integration: https://github.com/DeemosTech/blender-mcp-rodin-integration

**What Blender MCP can and cannot do in practice:**
- Good at: blocking out and kitbashing low-to-mid-poly props from primitives and modifiers, procedural materials (shader nodes), lighting and look-dev, importing generated or library assets, batch cleanup (decimate, merge by distance, apply transforms, set origins), UV unwrap presets, baking, and **batch glTF export**. The PMCE-style neon aesthetic (simple emissive geometry, bevels, bloom) is well within reach.
- Weak at: organic sculpting, clean hand topology for deforming characters, and artistic judgement without visual feedback. Always have it take viewport screenshots or renders and iterate.
- **You don't strictly need MCP.** `blender -b file.blend -P script.py -- args` runs any bpy script headless. Claude can write reproducible asset-build scripts (checked into git) that regenerate every asset. This is more robust than interactive MCP sessions for a pipeline. Use MCP for exploration and batch scripts for production.

### AI 3D generation
| Tool | Type | Licence/cost | MCP / integration | Notes |
|---|---|---|---|---|
| **Meshy** (v5/v6) | Hosted | Pro $20/mo (1,000 credits), Studio $60. **Paid tiers give full ownership and commercial use**; free tier is CC BY 4.0. API assets are deleted after 3 days, so download them promptly | **Official MCP** `@meshy-ai/meshy-mcp-server` (about 20 tools: text/image-to-3D, remesh, retexture, **rig, animate**) | Best all-rounder for an agent. [V] https://www.meshy.ai/tutorials/meshy-mcp-guide , https://github.com/meshy-dev |
| **Tripo** (v3.x) | Hosted | From about $14–20/mo, around $0.10 per model | Official `VAST-AI-Research/tripo-mcp` is **stale** (alpha, no push since 2025-04) [S]. Use it via the REST API or fal MCP | Auto-rig v2.5 (Feb 2026) covers biped, quadruped, avian, serpentine and more, with Mixamo-compatible bone names. Used by godogen |
| **Hyper3D Rodin Gen-2** | Hosted | Creator $30/mo, Business $120/mo. Commercial on paid plans | **Built into blender-mcp** | Highest mesh quality and quad topology [S] |
| **Hunyuan3D** 2.1 (open) / 3.x (hosted) | Open weights (2.x) and API | **Tencent community licence excludes the EU, UK and South Korea** and caps use at 1M MAU. 3.0 and 3.1 are hosted-only | Built into blender-mcp (Tencent Cloud API or local server) | Best PBR texturing among open models, but needs about 29 GB VRAM for the full pipeline. **If you are EU-based, the open weights are not licensed for you.** [V] https://github.com/Tencent-Hunyuan/Hunyuan3D-2/blob/main/LICENSE |
| **TRELLIS.2** (Microsoft, 4B) | Open weights | **MIT** | ComfyUI nodes, fal | Image-to-3D with full PBR (base colour, metallic, roughness, alpha). Linux only, 24 GB VRAM reference (community builds about 8 GB, still too much for 6 GB). [V] https://github.com/microsoft/TRELLIS.2 |
| Stable Fast 3D / SPAR3D | Open weights | Stability community licence (free under $1M revenue) | ComfyUI, fal | Fast, lower quality. A usable fallback for tiny props [S] |

**Integration pattern:** generate a concept image (GPT Image or Nano Banana), run image-to-3D (Meshy/Tripo/Rodin), import into Blender (MCP or batch script), then decimate, fix scale and origin, and build the material. For PMCE style, **replace the generated textures with emissive or flat shader materials**. Finally export `.glb` into `res://assets/models/`.

For simple arcade games (Qix, Arkanoid, Boulder Dash), **procedural geometry written by Claude directly in Godot** (CSG, MeshInstance with generated ArrayMesh, MultiMesh) plus shaders will often beat AI-generated meshes. AI 3D pays off for Cannon Fodder soldiers, Z robots and vehicles, and Alley Cat props.

### Texturing (PBR)
- Poly Haven and ambientCG (CC0) through blender-mcp. [V]
- ArmorLab (free, open-source, local; photo to PBR, though non-albedo maps are weaker) [S]. Hosted options: 3D AI Studio, Meshy retexture, PBRgen. [S] https://www.3daistudio.com/blog/best-ai-texture-and-pbr-generators-2026
- An image model with a "seamless tileable" prompt, then Material Maker, Blender, or a small Python script to derive normal and roughness maps. Claude can write that script.

### Rigging and animation
- **Mixamo:** still online and free but unmaintained (it had an outage in June 2025). [S] https://app.cinevva.com/guides/free-character-animations-rigging
- **AccuRIG 2** (Reallusion, free desktop app, with the ActorCore animation library, FBX/USD export). Linux support is unverified (it is probably Windows-only; could run under Wine [?]). https://magazine.reallusion.com/2025/07/30/accurig-2-vs-mixamo-smarter-auto-rigging-for-3d-animators/
- **UniRig** (MIT code, SIGGRAPH 2025, self-hosted; bipeds, quadrupeds, birds).
- **Meshy and Tripo auto-rig and animate through the API/MCP.** This is the easiest agent-driven path.
- For top-down Cannon Fodder or Z units, consider **baked 3D-to-sprite rendering** (render animated 3D models from 8 directions in Blender batch mode into sprite sheets) or simple procedural animation (bob, lean, squash). Claude can script both reliably.

### Export
glTF 2.0 binary (`.glb`) is Godot's first-class import format. Keep the `.blend` sources in LFS and export via a `blender -b` script in a Makefile or justfile, so Claude can rebuild every asset deterministically.

---

## 3. 2D graphics, textures, concept art, UI, VFX

### Image generation (Sept 2026)
- **OpenAI GPT Image 2** tops the Artificial Analysis and LMArena image arenas. The API supports **`background="transparent"`** with PNG/WebP output, which is great for sprites, icons and UI. It costs about $0.006, $0.053 or $0.211 per 1024² image at low, medium or high quality. [V/S] https://developers.openai.com/api/reference/resources/images/methods/generate , https://community.openai.com/t/transparent-backgrounds-are-now-available-in-preview-for-gpt-image-2-in-the-api/1391541
  - A GPT Image 2.5 ("flare"/"sunburst" snapshots, 2026-09-08) is reported [?]. Only secondary sources were found.
- **Google Nano Banana Pro (Gemini 3 Pro Image)** leads the image-editing arenas and is strong at consistent characters and style across edits. Nano Banana 2 is the cheaper volume model. [S] https://www.buildmvpfast.com/articles/best-llms-2026-guide/image-generation-ai
- **FLUX.2** (Black Forest Labs, Nov 2025): Pro and Flex are API-only. [dev] 32B is under a non-commercial licence, though its outputs may be used commercially. **[klein] 4B is Apache-2.0**; [klein] 9B is non-commercial. klein 4B is the realistic local model on 6 GB (with quantisation) [?]. [V] https://bfl.ai/licensing , https://github.com/black-forest-labs/flux2
- Arena scores: https://arena.ai/leaderboard/text-to-image

### Plugging into Claude Code
- **fal MCP (official, hosted):** `https://mcp.fal.ai/mcp`. It provides `search_models`, `run_model`, `submit_job`, `upload_file` and more, covering 1,000+ models (FLUX, Nano Banana/GPT Image where offered, Tripo, TRELLIS, Stable Audio, ElevenLabs SFX...). Launched 2026-03-19. A single key gives you most generation needs. [V] https://blog.fal.ai/connect-your-ai-to-1-000-models-with-the-fal-mcp-server
- **ComfyUI MCPs** for local or cloud workflows: official **Comfy-Org/comfy-mcp** (local, built on comfy-cli), **Comfy-Org/comfy-cloud-mcp** (hosted, OAuth), artokun/comfyui-mcp (large community one), and ConstantineB6/Comfy-Pilot. [S] https://github.com/Comfy-Org/comfy-mcp
- Alternatively, Claude writes small Python scripts against the OpenAI or Gemini SDKs. This is often simpler and more reproducible than MCP. Store the prompts in `assets/prompts/*.yaml`.

### Sprites and pixel art
- **Retro Diffusion** has a hosted MCP, an API and an Aseprite plugin. It produces grid-aligned pixels with controlled palettes. [S] https://mcpservers.org/servers/retro-diffusion/retro-diffusion-mcp
- PixelLab (skeleton-posed 4/8-direction characters), Scenario (API plus MCP, hosts the RD animation model), and Ludo.ai Pro ($50/mo, includes API and MCP). [S] https://ludo.ai/compare/best-ai-sprite-generators
- For a "modern HD" look (not pixel art), the more reliable path is **3D model to sprite sheet renders in Blender**, or vector-style GPT Image output with transparency, cleaned by Claude-written scripts (trim, pad, pack atlas).

### VFX and shaders
This is where the PMCE look really comes from, and it is **fully within Claude's direct authoring ability**, with no generator needed:
- WorldEnvironment glow/bloom, tonemapping, and HDR output (4.7)
- Canvas and spatial shaders: emissive neon outlines, scanline/CRT overlays, chromatic aberration, trail ribbons, grid warps (the Geometry Wars style)
- GPUParticles2D/3D with sub-emitters, Trail/Ribbon meshes, and screen shake plus hit-stop in GDScript
- Godot 4.7 inline shader previews help Claude and the human iterate. [V] https://godotengine.org/releases/4.7/
- Verify via Xvfb frame captures that Claude inspects.

---

## 4. Sound effects

| Option | Type | Licence | Claude integration |
|---|---|---|---|
| **ElevenLabs Sound Effects v2** (Sep 2025) | Hosted, 48 kHz, up to about 30 s, seamless looping | **Paid plans: royalty-free commercial use.** Free plan requires attribution [S]. Not verified whether the "Studio Games" clause that applies to Music also covers SFX [?] | **Official hosted ElevenLabs MCP** at `https://api.elevenlabs.io/v1/mcp` (OAuth; the old local server is deprecated) [S] https://github.com/elevenlabs/elevenlabs-mcp . Also available via fal |
| **jsfxr / sfxr** | Procedural, deterministic | Unlicense (chr15m/jsfxr) [?] | `npm i jsfxr` plus sfxr-to-wav from the CLI. Claude can author the parameter JSON directly. There is also an `sfx` MCP/CLI (gteuscher) with render, preset and variations commands [S] https://glama.ai/mcp/servers/gteuscher/sfx-api . Ideal for arcade blips, pickups and bounces (Arkanoid, Qix) |
| ChipTone / BFXR | Procedural (web GUI) | Free | Manual only |
| **Stable Audio Open 1.0 / Small** | Open weights | Stability community licence (free commercial use under $1M annual revenue) [V] https://stability.ai/license | Local or ComfyUI. Small might fit 6 GB [?] |
| Stable Audio 2.5 | Hosted (fal about $0.20 per generation) | Licensed training data | fal MCP |
| AudioCraft / AudioGen (Meta) | Open | Code MIT, **weights CC-BY-NC**, so not usable for a commercial game | Not recommended |
| MOSS-SoundEffect v2.0 (May 2026) | Open | Licence not checked [?] | https://github.com/OpenMOSS/MOSS-TTS |
| MMAudio, TangoFlux | Open | Weights are likely non-commercial [?] | Not verified |

**Recommended approach:** a hybrid. jsfxr presets for UI and arcade sounds (Claude generates JSON, then renders WAV, fully reproducible), ElevenLabs SFX v2 for explosions, gunfire, footsteps and ambience loops, and Godot's AudioEffect buses (reverb, compressor, pitch randomisation via AudioStreamRandomizer) for variety.

---

## 5. Music

### Licensing (important)
- **ElevenLabs Music v2** (2026-05-26) is trained on licensed data (Merlin, Kobalt) and offers stems and inpainting. **However**, its model-specific terms allow commercial use on every plan below Enterprise Music *"except film, TV, radio, & Studio Games"*. "Studio Games" is defined as *"video games which are commercialised (either by sale, advertising or any other forms of monetisation) and made available for download or use through more than one platform."* So a paid game on both Steam and itch.io (for example) needs the Enterprise Music plan. The free plan also requires attribution. [V] https://elevenlabs.io/eleven-music-model-specific-terms
- **Suno:** free-tier output can never be used commercially. Paid tiers get a commercial-use licence but **no guarantee of copyright ownership**. After the Warner settlement (Nov 2025), licensed models launch in 2026 and v5.x is set for deprecation, with download caps on paid tiers. [S] https://www.digitalmusicnews.com/2025/12/22/suno-warner-music-deal-changes/ , https://musicinafrica.net/magazine/suno-adjusts-ai-music-ownership-terms-after-warner-music-partnership/
- **Udio:** after the UMG settlement (Oct 2025) it is a "walled garden" with **no downloads or export**, and the licensed platform has been in staged rollout since May 2026. **Unusable for games right now.** [S] https://www.billboard.com/pro/umg-udio-ai-deal-faq-artist-payments-user-downloads-lawsuit/
- **Stable Audio 2.5** (hosted) uses licensed data and allows commercial use on paid or API tiers. Stable Audio Open is under the community licence (under $1M revenue). [S]
- **ACE-Step 1.5** (Jan 2026; XL 4B variant too): **MIT**, and claims royalty-free training data. It runs in **under 4 GB VRAM** (under 10 s per song on an RTX 3090) and supports LoRA fine-tuning. Quality is reported between Suno v4.5 and v5. **The best fit for this machine and for clean licensing.** [V] https://github.com/ace-step/ACE-Step-1.5 , https://arxiv.org/abs/2602.00744
- MusicGen (AudioCraft): weights are CC-BY-NC, so it is not for commercial use.

### Claude-authored music (fully under your control, no licensing ambiguity)
- **Strudel** (TidalCycles in JS, live-coding patterns). MCPs: williamzujkowski/live-coding-music-mcp (28 tools, MIDI import/export) and phildougherty/strudel-mcp-bridge. [S] https://github.com/williamzujkowski/live-coding-music-mcp
- **ABC notation**: linxule/mcp-music-studio (scored composition plus Strudel). https://github.com/linxule/mcp-music-studio
- **Trackers:** Furnace (multi-chip chiptune; FM/SID/Paula) and OpenMPT/libopenmpt. Claude can emit MIDI or text patterns and render them via CLI. Tracker modules (.xm/.it) are tiny and loop-perfect, which suits the retro-remake vibe (the Amiga originals used MOD music).
- **MIDI plus FluidSynth/SF2 or a DAW:** Claude writes MIDI with `mido` or `pretty_midi`, renders with `fluidsynth` plus a good SoundFont, and exports per-layer stems for adaptive mixing.
- A Claude skill that composes full chiptune songs in JSON exists (GGPrompts chiptune-composer) [S].

### Adaptive/interactive music in Godot (4.3+)
- **AudioStreamSynchronized**: stems played in lock-step with per-layer volume, so you can add drums as intensity rises. This is the PMCE approach, where music layers build with combo and speed.
- **AudioStreamInteractive**: state machine clips (menu, play, danger, boss) with beat- or bar-synced transitions.
- **AudioStreamPlaylist**: sequenced tracks.
- [V] https://docs.godotengine.org/en/stable/classes/class_audiostreaminteractive.html , https://blog.blips.fm/articles/the-new-music-features-in-godot-43-explained
- Generate stems with ACE-Step (or render MIDI per instrument) and wire them into AudioStreamSynchronized. Claude edits the `.tres` directly.

---

## 6. Supporting tools

### Emulators for reference capture (Linux distro versions checked)
| Game(s) | Original platform | Emulator | Distro package |
|---|---|---|---|
| Qix, Arkanoid | Arcade | **MAME** (`-snapshot`, `-aviwrite`, `-wavwrite`, Lua scripting for automated input and RAM inspection) | `games-emulation/mame` 0.289 |
| Boulder Dash | C64 / Atari 8-bit | **VICE** (`x64sc`; monitor, `-exitscreenshot`, remote monitor for scripting) | `app-emulation/vice` 3.10 |
| Cannon Fodder, Z | Amiga | **FS-UAE** 3.2.35 (repo quiet for about a year) or **Amiberry** v8.3 (most active, flatpak) | `app-emulation/fs-uae` 3.2.35; Amiberry via flatpak or an overlay [S] |
| Alley Cat, Z (DOS), Cannon Fodder (DOS) | PC DOS | **DOSBox Staging** 0.83 or **DOSBox-X** 2026.08.31 | `games-emulation/dosbox-staging` 0.83.0. DOSBox-X is not in the main tree (build it or use flatpak) [V] https://dosbox-x.com/release-2026.08.31.html |

The value for Claude is that MAME's Lua and VICE's monitor let it **script captures and read game RAM**, for example exact enemy speeds, timer values and level layouts (Boulder Dash caves are small, documented data structures). Record the original with ffmpeg or OBS and have Claude compare frame grabs with the remake's Xvfb captures. **Use legally owned ROMs and disks only** (Alley Cat's original was freely distributed by its author per various sources [?]; verify).

### Version control
- git plus **git-lfs** (`dev-vcs/git-lfs` 3.8.0). A `.gitattributes` for `*.glb *.blend *.png *.jpg *.exr *.wav *.ogg *.flac *.psd *.kra`. Keep Godot `.import` files in git, and ignore `.godot/`.
- Commit the **generation provenance** (prompt, model, seed, date, licence tier) next to each asset, as YAML or JSON. You need it for licence audits and for regeneration.

### Other useful Claude Code pieces
- **Playwright MCP** (if you go web), **Context7 or docs MCPs** for current Godot 4.7 API docs (LLM training lags new APIs) [?], and a Claude Code **Stop hook** that runs GdUnit4 plus a capture before a task is considered done (as godot-ai-builder does).
- **ImageMagick / ffmpeg / Aseprite CLI**: Claude uses them for atlas packing, trimming, format conversion and GIF previews.

---

## 7. Legal notes (brief; not legal advice)
- **Names and logos are trademarks.** Boulder Dash® is owned by BBG Entertainment GmbH (registered in the US and EU), which still actively sells *Boulder Dash 40th Anniversary* [V] https://boulder-dash.com/legal/ . Arkanoid and Qix belong to Taito (Square Enix). Cannon Fodder belongs to Codemasters, now EA [S]. The Bitmap Brothers brand and IP, including Z, have belonged to Rebellion since 2019 [V] https://rebellion.com/rebellion-acquires-the-bitmap-brothers-brand-and-portfolio/ . Alley Cat was by Bill Williams for IBM/Synapse; its current rights holder is unclear [?]. **Use original titles** (e.g. "Neon Rockfall" rather than "Boulder Dash"). "Inspired by" wording in descriptions is generally fine, but avoid marks and logos in titles and art.
- **Mechanics and rules are not copyrightable, but expression is.** *Tetris Holding v. Xio* (2012) found infringement where the *overall look and feel* (board dimensions, piece shapes and colours, visual display) was copied even with new art. *Spry Fox v. Lolapps* confirmed that look and feel can be protected. [V] https://en.wikipedia.org/wiki/Tetris_Holding,_LLC_v._Xio_Interactive,_Inc.
- **Clean-room practice:** reimplement behaviour from observation and specs (your notes and measurements), not from disassembled code. **Never ship original sprites, maps or level data, music or sound.** Boulder Dash cave layouts and Z maps are expressive content, so design new levels (Claude can generate them procedurally or you design them). A distinctly different visual identity (the PMCE-style neon reinterpretation) strengthens your position considerably.
- **AI asset licences:** keep a per-asset record of the tool and plan (see provenance above). Watch out for ElevenLabs Music's "Studio Games" clause, Suno's ownership disclaimer, Hunyuan3D's EU/UK/KR exclusion, and non-commercial weights (FLUX.2 dev and klein 9B, AudioCraft). Pure AI output may not be copyrightable in some jurisdictions (e.g. US Copyright Office guidance), which matters little for a remake but means competitors could reuse unmodified AI assets.

---

## 8. Unverified or uncertain items
- GPT Image 2.5 (2026-09-08, "flare"/"sunburst"): secondary sources only.
- Unity MCP requiring a paid Unity AI subscription on Personal: forum and secondary sources only.
- Unreal MCP on the Linux editor: not confirmed.
- Godot MCP Pro on Linux: not stated, but likely.
- AccuRIG on Linux: likely Windows-only.
- Whether ElevenLabs **SFX** (not Music) output carries a similar "Studio Games" restriction: not checked. Read the SFX terms before shipping.
- Licences of MOSS-SoundEffect, MMAudio and TangoFlux, and whether Stable Audio Open Small or FLUX.2 klein 4B run acceptably on a 6 GB GPU.
- The tool counts and star numbers quoted come from READMEs as fetched and change constantly.
- Alley Cat's current rights status.
