# Tech stack (zero budget, open licences)

Constraints: no spending beyond the existing **Claude** (includes Claude Code) and **ChatGPT** accounts. Everything shipped must be open-licensed. Development happens on Linux with
a consumer GPU with limited VRAM (plan for about 6 GB), so only small local AI models are possible. The full research with sources,
including paid options we rejected, is in [../research/stack-report.md](../research/stack-report.md).

| Area | Pick | Notes |
|---|---|---|
| Coding agent | **Claude Code** | Codex CLI (included with ChatGPT) as an optional second reviewer |
| Engine | **Godot 4.7** (MIT) | Text-based scenes, scripts and shaders; the AI can edit everything |
| Engine MCP | **hi-godot/godot-ai** (MIT) or Coding-Solo/godot-mcp (MIT) | No Godot MCP Pro (paid) |
| Letting the AI see the game | Run under **Xvfb**, save viewport frames to PNG; **GdUnit4** for tests | A small script in the repo |
| 3D | **Blender 5** + Blender MCP (official Blender Lab MCP, or ahujasid/mcp-for-blender) + `blender -b -P` batch scripts | glTF (.glb) into Godot |
| Art direction | Stylised, toy-like or diorama, low to mid poly; the "wow" comes from lighting, glow, particles and shaders | Chosen so Claude can build assets procedurally |
| Free asset kits | Quaternius, Kenney, Poly Haven, ambientCG (all CC0), Rigify for rigs | No Mixamo |
| 2D art, UI, concept art | ChatGPT image generation (by hand in the app), or local FLUX.2 klein 4B / FLUX.1 schnell (Apache-2.0) via ComfyUI | 6 GB VRAM needs quantised models (speed not tested) |
| Sound effects | **jsfxr** (Claude writes the parameters, renders WAV), Python synthesis, Kenney audio, CC0 Freesound clips | |
| Music | Claude-composed MIDI or tracker files (Furnace/OpenMPT) rendered with **FluidSynth** + FluidR3_GM (MIT) SoundFont; **ACE-Step 1.5** (MIT, under 4 GB VRAM) for generated stems | Adaptive layers via Godot AudioStreamInteractive/Synchronized |
| Reference capture | MAME, VICE, FS-UAE/Amiberry, DOSBox Staging (all packaged on Linux) | For timings, behaviours and missing screenshots |
| Hosting | GitHub (+ git-lfs for binaries), itch.io, Godot web export | |

## Setup still to do

- Install Godot 4.7, Blender 5, the emulators, FluidSynth and git-lfs.
- Register the MCP servers with Claude Code (`claude mcp add ...`; see the research report for commands).
- Write the capture script (Xvfb + viewport PNG) so the agent can check its own work visually.
