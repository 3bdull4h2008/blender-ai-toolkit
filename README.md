# Blender AI Toolkit

AI-powered addon for Blender. Generate 3D models, images, PBR materials, and HDRI environments from text prompts. Chat with LLMs and execute Blender Python code directly.

Blender 4.2+ required.

## Features

**3D Generation** - Text-to-3D and Image-to-3D via Tripo3D, Meshy.ai, or local ComfyUI. Imports GLB directly into your scene.

**Image Generation** - DALL-E 3 and Stability AI. Multiple sizes, quality levels, style presets.

**Material Generation** - PBR material textures from text. Diffuse, normal, roughness, metallic maps.

**HDRI Generation** - Environment lighting from text descriptions. Applies directly to world settings.

**LLM Chat** - OpenAI, Anthropic, Claude, Ollama, LM Studio. Scene context injection. Auto-execute Blender Python code with error retry.

**Scene Composition** - Describe a scene in text, get a full Blender scene with objects, materials, lights, camera.

**Mesh Cleanup** - Remove doubles, fix normals, fill holes, delete loose geometry.

**Batch Generation** - Generate multiple variations of the same prompt.

**Asset Management** - Persistent asset library. Import, export, favorites.

**Preset System** - 30+ built-in presets for 3D models, images, materials, HDRI.

**ComfyUI Backend** - Use any diffusion model locally via ComfyUI. VRAM management included.

## Installation

1. Download the zip from this repository
2. Open Blender > Edit > Preferences > Add-ons
3. Click "Install from Disk" and select the zip
4. Enable the addon

## Setup

1. Go to Edit > Preferences > Add-ons > AI Toolkit
2. Enter your API keys for the providers you want to use
3. For local providers (Ollama, LM Studio, ComfyUI), make sure they are running

**Required for cloud providers:**
- OpenAI: API key from https://platform.openai.com
- Anthropic: API key from https://console.anthropic.com
- Stability AI: API key from https://platform.stability.ai
- Tripo3D: API key from https://platform.tripo3d.ai
- Meshy: API key from https://meshy.ai

**Local providers (no API key needed):**
- Ollama: Install from https://ollama.com, run `ollama pull llama3.2`
- LM Studio: Install from https://lmstudio.ai, download a model
- ComfyUI: Install from https://github.com/comfyanonymous/ComfyUI

## Usage

The addon adds a sidebar panel in the 3D viewport (press N to open, look for "AI Toolkit" tab).

**Generate a 3D model:**
1. Select the "3D" tab
2. Pick a provider (Meshy, Tripo, ComfyUI)
3. Type a description
4. Click "Generate"

**Chat with AI:**
1. Select the "Chat" tab
2. Pick a provider (OpenAI, Ollama, etc.)
3. Type your message
4. The AI can generate and execute Blender Python code

**Generate materials:**
1. Select the "Mat" tab
2. Describe the material
3. Click "Generate"
4. Apply to selected object

## Project Structure

```
blender_ai_toolkit/
├── __init__.py              # Registration
├── preferences.py           # API keys and settings
├── properties.py            # UI properties
├── api/
│   ├── http_client.py       # HTTP client (stdlib)
│   ├── comfyui_client.py    # ComfyUI integration
│   ├── llm/openai_llm.py   # OpenAI, Anthropic, Ollama, LM Studio
│   ├── model_3d/providers.py # Tripo3D, Meshy
│   ├── image/providers.py   # DALL-E 3, Stability AI
│   ├── material/providers.py # Stability AI, ComfyUI
│   └── hdri/providers.py    # Stability AI, ComfyUI
├── core/
│   ├── task_queue.py        # Async execution with timers
│   ├── expert_prompts.py    # Topology, lighting, PBR guides
│   ├── presets.py           # 30+ built-in presets
│   ├── job_manager.py       # Job history and re-download
│   ├── preview_gallery.py   # Multi-candidate previews
│   └── scene_composer/      # Text to scene
├── operators/               # All operators
├── ui/sidebar.py            # Sidebar panel
└── utils/
    ├── file_utils.py        # Asset/template persistence
    └── mesh_utils.py        # Mesh quality analysis
```

## Architecture

- No external Python dependencies. Uses only stdlib (`urllib`, `json`, `threading`).
- All API calls run in background threads via `bpy.app.timers`.
- Providers are abstracted behind a common interface.
- ComfyUI integration uses HTTP API + polling.

## Contributing

Fork, create a branch, make changes, open a PR.

## License

MIT
