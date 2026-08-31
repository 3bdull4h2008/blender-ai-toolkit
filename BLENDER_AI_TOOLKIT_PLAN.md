# Blender AI Toolkit — Full Build Plan (2026-08-28; v2.1.1 Baseline)

> Single authoritative plan for the Blender AI Toolkit addon. The current codebase
> (v2.1.1) is a **well-architected skeleton** — professional UI with 8 tabs, 23
> operators, ~50 properties, and a scene composer that creates real Blender objects.
> However, **zero AI providers are implemented**. Every operator is a stub. The task
> queue cannot execute tasks. No HTTP requests are made anywhere. This plan turns
> the skeleton into a working product.

---

## Current State Audit (2026-08-28)

### What Works
| Feature | Status | Notes |
|---------|--------|-------|
| 8-tab sidebar UI | ✅ WORKING | Renders correctly in Blender 4.2+ |
| Tab switching | ✅ WORKING | `ai.set_tab` operator |
| Preferences panel | ✅ WORKING | API key fields render in Blender preferences |
| Settings display | ✅ WORKING | Shows preference values |
| Template apply | ✅ WORKING | Fills prompt fields by category |
| Template refresh | ✅ WORKING | Reloads 7 defaults |
| Asset delete (in-memory) | ✅ WORKING | Removes from CollectionProperty |
| Asset duplicate (in-memory) | ✅ WORKING | Copies metadata |
| Asset toggle favorite | ✅ WORKING | Flips boolean |
| Scene composer (keyword fallback) | ✅ WORKING | Creates primitives, lights, camera from keywords |
| Scene composer (LLM-assisted) | ❌ BROKEN | Task queue never executes |
| Progress bar / status | ⚠️ PARTIAL | Properties exist, operators set them, nothing runs |
| Notifications | ⚠️ PARTIAL | Console output works, UI list never populated |

### What Is Stubbed (22 operators, 0 implementations)
| Category | Operators | Implementation |
|----------|-----------|----------------|
| 3D Generation | `ai.generate_3d`, `ai.generate_3d_ref_image` | Validates + simulates, returns FINISHED |
| Image Generation | `ai.generate_image` | Same pattern |
| Material Generation | `ai.generate_material` | 12-line print stub |
| HDRI | `ai.apply_hdri` | 12-line print stub |
| Texture-to-Material | `ai.texture_to_material` | 12-line print stub |
| Mesh Cleanup | `ai.mesh_cleanup` | 12-line print stub |
| Batch Generate | `ai.batch_generate` | 12-line print stub |
| LLM Chat | `ai.chat` | Returns hardcoded placeholder |
| Code Execution | `ai.chat_execute_code` | Reports "not implemented" |
| Asset Import | `ai.asset_import` | Validates index, does nothing |
| Asset Refresh | `ai.asset_refresh` | Prints "refreshed" |
| Scene AI Objects | `ai.generate_scene_ai_objects` | Finds placeholders, `get_3d_provider()` returns None |

### Critical Bugs
1. **TaskQueue.submit() never executes tasks** — stores in dict, never calls `work_func`, no processing loop, no threading, no timers
2. **`get_3d_provider()` hardcoded to `return None`** — scene AI object generation always fails silently
3. **`AIComposeSceneOperator._on_complete` never fires** — TaskQueue never processes tasks, so callback never runs; also `task_info.result` is None → `result.get()` would crash
4. **`AISaveTemplateOperator` saves to in-memory only** — custom templates lost on restart
5. **`TemplateManager.refresh()` destroys custom templates** — clears all, reloads only defaults
6. **`NotificationManager` never syncs with `notification_list` property** — UI list never populated
7. **`AIAssetDeleteOperator` index bug** — when list becomes empty, `len - 1 = -1` (invalid)
8. **`SceneComposer._create_camera` ignores computed `direction`** — rotation hardcoded to (60, 0, 45)
9. **`scene_composer.py` line 310 `or True`** — leftover debug, always applies scale
10. **No HTTP client library imported anywhere** — no `requests`, `httpx`, `urllib` usage

---

## Competitive Analysis — Similar Projects

### 1. StableGen (sakalond/stablegen) ⭐⭐⭐⭐⭐
**What it is:** AI-powered 3D generation & texturing in Blender via ComfyUI backend.

| Aspect | Details |
|--------|---------|
| **Architecture** | Blender addon ↔ ComfyUI server (localhost HTTP). Heavy compute offloaded. |
| **Providers** | TRELLIS.2 (Microsoft), SDXL, FLUX.1-dev, Qwen Image Edit, Marigold, BiRefNet |
| **Features** | Text-to-3D, Image-to-3D, PBR texturing, decimation/remeshing, preview gallery |
| **Install** | ComfyUI + dependencies (~7-50GB) + Blender plugin |
| **Blender** | 4.2–4.5, 5.1+ |
| **License** | GPL-3.0 |
| **Pros** | Production-quality pipeline, multiple resolution modes, VRAM-conscious, mesh recovery, studio lighting, PBR decomposition |
| **Cons** | Requires ComfyUI (heavy setup), large download (7-50GB), no cloud fallback, single backend |
| **Takeaway** | Best architecture pattern: Blender addon as thin UI, heavy compute in separate process. Shows how to do mesh handling, import, scaling properly. |

### 2. blend-ai (HoldMyBeer-gg/blend-ai) ⭐⭐⭐⭐
**What it is:** MCP Server for Blender — control Blender via Claude through natural language.

| Aspect | Details |
|--------|---------|
| **Architecture** | Blender addon (TCP server) ↔ MCP Server ↔ Claude/external AI |
| **Providers** | Claude (via MCP), any MCP client |
| **Features** | 164 tools across 24 modules, procedural materials, mesh analysis, scene control |
| **Blender** | 4.2+ (Extension format) |
| **License** | AGPL-3.0 |
| **Pros** | Zero external deps in addon (pure bpy), expert prompts guide LLM, 164 tools, professional workflows, visual feedback |
| **Cons** | Requires Claude subscription, MCP adds complexity, no 3D model generation (only scene manipulation) |
| **Takeaway** | Proves pure-bpy addon with TCP socket server works. Shows how to guide LLM with expert prompts. Scene-aware context sending. Code execution with AST validation. |

### 3. MuAPI Blender Extension (SamurAIGPT/muapi-blender-extension) ⭐⭐⭐⭐
**What it is:** Cloud API for 3D generation (Tripo, Meshy, Hunyuan3D) in Blender.

| Aspect | Details |
|--------|---------|
| **Architecture** | Blender addon ↔ MuAPI cloud server |
| **Providers** | Tripo P1, Tripo H3.1, Meshy v6, Hunyuan3D v3 |
| **Features** | Text-to-3D, Image-to-3D, Multiview-to-3D, GLB import, async job queue |
| **Blender** | 4.2+ |
| **License** | GPL-3.0 |
| **Pros** | Clean API abstraction, async job queue with polling, proper error handling, supports multiple providers, auto-import GLB |
| **Cons** | Requires paid API, no local fallback, no material/HDRI generation |
| **Takeaway** | Closest to our project's scope. Shows proper async job queue pattern (thread + polling + timer). API abstraction layer design. GLB import pipeline. |

### 4. Tripo 3D Blender Plugin (VAST-AI-Research/tripo-3d-for-blender) ⭐⭐⭐⭐
**What it is:** Official Tripo AI integration for Blender.

| Aspect | Details |
|--------|---------|
| **Architecture** | Blender addon ↔ Tripo cloud API |
| **Providers** | Tripo only (text-to-3D, image-to-3D, multiview-to-3D) |
| **Features** | Real-time progress tracking, balance check, GLB import |
| **Blender** | 3.0+ |
| **License** | MIT |
| **Pros** | Official, well-maintained, simple install, progress tracking, API key validation |
| **Cons** | Single provider only, no material/HDRI, no chat |
| **Takeaway** | Shows how to implement proper API key validation and balance checking. Real-time progress tracking pattern. |

### 5. ComfyUI-BlenderAI-node (AIGODLIKE) ⭐⭐⭐
**What it is:** ComfyUI nodes inside Blender — convert ComfyUI workflows to Blender nodes.

| Aspect | Details |
|--------|---------|
| **Architecture** | Blender addon ↔ ComfyUI (node-based) |
| **Providers** | ComfyUI ecosystem (SDXL, ControlNet, 3D-Pack, etc.) |
| **Features** | AI materials, texture baking, camera input, Grease pencil masks, batch processing |
| **Blender** | 3.5–4.0 |
| **License** | GPL-3.0 |
| **Pros** | 1524 stars, mature, node-based workflow, camera real-time input, batch processing |
| **Cons** | Complex setup, older Blender versions, node-based (not everyone wants this) |
| **Takeaway** | Shows how to integrate ComfyUI properly. Texture baking workflow. Batch processing pattern. |

### 6. MeshGen (huggingface/meshgen) ⭐⭐⭐⭐
**What it is:** AI Agents control Blender with natural language.

| Aspect | Details |
|--------|---------|
| **Architecture** | Blender addon ↔ Multiple backends (Ollama, OpenAI, Anthropic, HF) |
| **Providers** | LLaMA-Mesh (local), Hyper3D, Ollama, OpenAI, Anthropic |
| **Features** | Natural language scene control, optional mesh generation, vision review |
| **Blender** | 4.2+ |
| **License** | MIT |
| **Pros** | Multiple backends, local-first option, HuggingFace backing, clean architecture |
| **Cons** | Mesh generation is optional addon, no material/HDRI generation |
| **Takeaway** | Multi-backend architecture pattern. Shows how to support both local (Ollama) and cloud (OpenAI/Anthropic) providers cleanly. |

### 7. blend-slop (meigo/blend-slop) ⭐⭐⭐
**What it is:** Chat panel with LLM code generation + Polyhaven integration.

| Aspect | Details |
|--------|---------|
| **Architecture** | Blender addon ↔ Claude/OpenAI/Ollama |
| **Providers** | Claude, OpenAI, Ollama (local) |
| **Features** | Chat, auto-execute code, error retry, Polyhaven (textures + HDRIs + models), scene context |
| **Blender** | 5.0+ |
| **License** | GPL-3.0 |
| **Pros** | Auto-execute with error retry, scene-aware context, Polyhaven integration (free assets), streaming |
| **Cons** | Requires API key, no 3D model generation |
| **Takeaway** | Error retry pattern (send traceback back to LLM). Scene context injection. Polyhaven as free asset source. |

### 8. Blender LLM Assistant (suryansh00001/Blender-Extension) ⭐⭐⭐
**What it is:** Multi-LLM code generation with security validation.

| Aspect | Details |
|--------|---------|
| **Architecture** | Blender addon ↔ OpenAI/Claude/Gemini |
| **Providers** | OpenAI, Anthropic, Google Gemini (free tier) |
| **Features** | Code preview mode, AST security validation, code history, multi-provider |
| **Blender** | 3.0+ |
| **License** | MIT |
| **Pros** | Gemini free tier, security validation (blocks dangerous imports), code preview, works on old Blender |
| **Cons** | No 3D generation, no material/HDRI, basic chat |
| **Takeaway** | Security validation pattern for code execution. Multi-provider with Gemini free tier. |

---

## What We Should Steal (Best Ideas from Competitors)

| Idea | Source | Why |
|------|--------|-----|
| **Thin Blender addon + heavy compute in separate process** | StableGen | Keeps Blender responsive, leverages ComfyUI ecosystem |
| **Async job queue with thread + polling + timer** | MuAPI | Proper async pattern, shows progress, allows cancellation |
| **Scene-aware context injection** | blend-slop, blend-ai | LLM sees current scene state for better responses |
| **Error retry: send traceback back to LLM** | blend-slop | Self-healing code generation |
| **AST security validation before code execution** | Blender LLM Assistant | Prevents dangerous operations |
| **Polyhaven as free asset source** | blend-slop | No API key needed, CC0 assets |
| **API key validation + balance check** | Tripo 3D | User knows if key works before generating |
| **Multi-provider abstraction with fallback** | MeshGen, MuAPI | Switch providers without changing UI |
| **Streaming responses** | blend-slop | Real-time feedback |
| **Preview gallery before committing** | StableGen | Generate multiple candidates, pick best |
| **Mesh auto-recovery** | StableGen | Handle corrupted imports gracefully |

---

## Phase Plan

### Phase 0 — Foundation & Infrastructure (Week 1)
**Goal:** Fix all critical bugs, build the async infrastructure, add HTTP client.

| Step | Description | Priority |
|------|-------------|----------|
| 0.1 | Fix `TaskQueue` — add `process()` method with `bpy.app.timers` integration. Tasks execute via threading, results dispatched on main thread via timers. | CRITICAL |
| 0.2 | Add `httpx` (async) or `urllib.request` (stdlib) HTTP client wrapper in `api/http_client.py` with timeout, retry, error handling | CRITICAL |
| 0.3 | Fix `AIAssetDeleteOperator` index bug — handle empty list case | HIGH |
| 0.4 | Fix `SceneComposer._create_camera` — use computed direction, remove `or True` debug line | HIGH |
| 0.5 | Fix `TemplateManager.refresh()` — preserve custom templates across refresh | HIGH |
| 0.6 | Connect `NotificationManager` to `notification_list` property — sync history to UI | MEDIUM |
| 0.7 | Add `requests` or `httpx` to addon dependencies (or use stdlib `urllib`) | CRITICAL |
| 0.8 | Add `api/http_client.py` — singleton HTTP client with session pooling, retry, timeout | CRITICAL |
| 0.9 | Add proper logging via `bpy.app.debug` and preferences `debug_mode` flag | MEDIUM |

**Gate 0:** Task queue executes tasks via timers. HTTP client can make GET/POST. All critical bugs fixed.

---

### Phase 1 — LLM Chat (First Working Feature) (Week 2)
**Goal:** Get real AI chat working with OpenAI, Anthropic, Ollama, LM Studio.

| Step | Description | Priority |
|------|-------------|----------|
| 1.1 | Implement `OpenAILLMProvider.generate()` — real API call to OpenAI chat completions endpoint | CRITICAL |
| 1.2 | Implement `AnthropicLLMProvider.generate()` — real API call to Anthropic messages endpoint | HIGH |
| 1.3 | Implement `OllamaLLMProvider.generate()` — real API call to Ollama `/api/chat` | HIGH |
| 1.4 | Implement `LMStudioLLMProvider.generate()` — real API call to LM Studio `/v1/chat/completions` | MEDIUM |
| 1.5 | Add conversation memory — store message history in `history_list` collection | HIGH |
| 1.6 | Update `AIChatOperator` to use real providers | CRITICAL |
| 1.7 | Add streaming responses (yield chunks, update UI incrementally) | MEDIUM |
| 1.8 | Add scene context injection — send current scene objects/materials/lights to LLM | HIGH |
| 1.9 | Implement `AIChatExecuteCodeOperator` — extract ```python blocks, validate with AST, execute in Blender context | HIGH |
| 1.10 | Add error retry — if code execution fails, send traceback back to LLM for correction | MEDIUM |

**Gate 1:** User can chat with OpenAI/Claude/Ollama in Blender sidebar. AI can generate and execute Blender Python code. Error retry works.

---

### Phase 2 — 3D Model Generation (Week 3-4)
**Goal:** Text-to-3D and Image-to-3D via Tripo3D and Meshy APIs.

| Step | Description | Priority |
|------|-------------|----------|
| 2.1 | Implement `api/model_3d/tripo.py` — Tripo3D API client (text-to-3D, image-to-3D, status polling) | CRITICAL |
| 2.2 | Implement `api/model_3d/meshy.py` — Meshy API client (text-to-3D, image-to-3D, status polling) | CRITICAL |
| 2.3 | Implement async job submission — submit to provider, poll for completion, download GLB | CRITICAL |
| 2.4 | Implement GLB/GLTF import — `bpy.ops.import_scene.gltf()` with error handling | CRITICAL |
| 2.5 | Add mesh auto-recovery — try to fix corrupted imports (non-manifold, normals) | HIGH |
| 2.6 | Implement `AIGenerate3DOperator.execute()` — wire to real providers | CRITICAL |
| 2.7 | Implement `AIGenerate3DRefImageOperator.execute()` — image-to-3D | HIGH |
| 2.8 | Add progress tracking — real progress from provider API | HIGH |
| 2.9 | Add cancellation support — cancel polling on user request | MEDIUM |
| 2.10 | Implement `AIGenerateSceneAIObjectsOperator` — wire `get_3d_provider()` to real providers | HIGH |
| 2.11 | Add Luma AI provider (stretch) | LOW |
| 2.12 | Add CSM provider (stretch) | LOW |

**Gate 2:** User can generate a 3D model from text or image via Tripo/Meshy. Model imports into Blender scene. Progress bar works. Cancel works.

---

### Phase 3 — Image Generation (Week 5)
**Goal:** Text-to-image via DALL-E 3 and Stability AI.

| Step | Description | Priority |
|------|-------------|----------|
| 3.1 | Implement `api/image/dalle.py` — DALL-E 3 API client | CRITICAL |
| 3.2 | Implement `api/image/stability.py` — Stability AI API client | HIGH |
| 3.3 | Implement `api/image/comfyui.py` — ComfyUI HTTP API client (workflow execution) | MEDIUM |
| 3.4 | Implement image download + import as plane or reference image | CRITICAL |
| 3.5 | Implement `AIGenerateImageOperator.execute()` — wire to real providers | CRITICAL |
| 3.6 | Add image preview before import | MEDIUM |
| 3.7 | Add seed control for reproducible results | LOW |

**Gate 3:** User can generate an image from text via DALL-E/Stability. Image imports into Blender scene.

---

### Phase 4 — Material & HDRI Generation (Week 6)
**Goal:** PBR material generation and HDRI environment generation.

| Step | Description | Priority |
|------|-------------|----------|
| 4.1 | Implement `api/material/stability.py` — Stability AI material generation (texture-to-maps) | HIGH |
| 4.2 | Implement `api/material/comfyui.py` — ComfyUI material workflow | MEDIUM |
| 4.3 | Implement PBR material creation — create Blender material from diffuse/normal/roughness/metallic maps | CRITICAL |
| 4.4 | Implement `AIGenerateMaterialOperator.execute()` | CRITICAL |
| 4.5 | Implement HDRI generation — Stability AI or ComfyUI | HIGH |
| 4.6 | Implement `AIApplyHDRIOperator.execute()` — download HDRI, set as world environment | CRITICAL |
| 4.7 | Implement `AITextureToMaterialOperator.execute()` — convert single texture to PBR material | MEDIUM |
| 4.8 | Add seamless/tiling texture generation | MEDIUM |

**Gate 4:** User can generate PBR materials and HDRI environments. Materials apply to selected objects.

---

### Phase 5 — Scene Composition Completion (Week 7)
**Goal:** Fix LLM-assisted scene composition, make it fully working.

| Step | Description | Priority |
|------|-------------|----------|
| 5.1 | Wire `AIComposeSceneOperator` to real LLM provider (currently broken because TaskQueue doesn't execute) | CRITICAL |
| 5.2 | Fix `_on_complete` callback chain — TaskQueue must execute and call on_complete | CRITICAL |
| 5.3 | Test JSON scene parsing with real LLM responses | HIGH |
| 5.4 | Improve keyword-based fallback scene creation | MEDIUM |
| 5.5 | Add material assignment from scene JSON | MEDIUM |

**Gate 5:** Scene composition uses real LLM, creates proper Blender scene with objects, materials, lights, camera.

---

### Phase 6 — Asset Management & Persistence (Week 8)
**Goal:** Persistent asset library, template storage, notification sync.

| Step | Description | Priority |
|------|-------------|----------|
| 6.1 | Implement asset storage — save generated assets metadata to JSON on disk | HIGH |
| 6.2 | Implement `AIAssetRefreshOperator` — reload asset list from disk | HIGH |
| 6.3 | Implement `AIAssetImportOperator` — import GLB/image/material from stored path | HIGH |
| 6.4 | Persist custom templates to disk (JSON file in addon storage) | HIGH |
| 6.5 | Sync `NotificationManager` with `notification_list` UI collection | MEDIUM |
| 6.6 | Add `unread_notifications` badge | LOW |

**Gate 6:** Assets persist across Blender restarts. Templates persist. Notifications appear in UI.

---

### Phase 7 — ComfyUI Integration (Week 9-10)
**Goal:** Full ComfyUI backend for all generation types (3D, image, material, HDRI).

| Step | Description | Priority |
|------|-------------|----------|
| 7.1 | Implement `api/comfyui/client.py` — ComfyUI HTTP API client (queue prompt, get image, get 3D) | HIGH |
| 7.2 | Implement workflow presets — pre-built ComfyUI workflows for common tasks | HIGH |
| 7.3 | Implement `api/comfyui/workflows/` — JSON workflow templates for each generation type | MEDIUM |
| 7.4 | Add ComfyUI connection test in preferences | MEDIUM |
| 7.5 | Add ComfyUI model browser (list available checkpoints, LoRAs) | LOW |

**Gate 7:** ComfyUI backend works for all generation types. Users can use local ComfyUI for free generation.

---

### Phase 8 — Polish, Testing & Release (Week 11-12)
**Goal:** Bug fixes, UX polish, documentation, Blender extension store submission.

| Step | Description | Priority |
|------|-------------|----------|
| 8.1 | Full UI/UX review — fix layout issues, add tooltips, improve error messages | HIGH |
| 8.2 | Add undo support to all operators | HIGH |
| 8.3 | Add keyboard shortcuts | LOW |
| 8.4 | Write README with installation, setup, and usage instructions | HIGH |
| 8.5 | Test on Blender 4.2 LTS, 4.3, 4.4, 5.0 | HIGH |
| 8.6 | Package as Blender Extension (.zip with manifest.toml) | HIGH |
| 8.7 | Submit to Blender Extension Store (optional) | LOW |

**Gate 8:** Release candidate. All features working. Tested on multiple Blender versions. Documentation complete.

---

## Architecture Decisions

| # | Decision | Choice | Rationale |
|---|----------|--------|-----------|
| A1 | HTTP client | `urllib.request` (stdlib) | No external dependencies in Blender addon. `requests` can't be pip-installed inside Blender easily. |
| A2 | Async pattern | `threading.Thread` + `bpy.app.timers` | Blender's GIL means threading for I/O is fine. Timers dispatch results on main thread. |
| A3 | 3D import format | GLB/GLTF via `bpy.ops.import_scene.gltf()` | Universal format supported by all providers (Tripo, Meshy, Luma, CSM) |
| A4 | ComfyUI integration | HTTP API (queue prompt, poll, download) | ComfyUI exposes REST API. No Python bridge needed. |
| A5 | Asset storage | JSON files in `~/.blender_ai_toolkit/` | Simple, portable, no database dependency |
| A6 | LLM system prompt | Hardcoded in preferences with scene context injection | Balances customization with simplicity |
| A7 | Code execution security | AST validation before `exec()` | Block dangerous imports (os, subprocess, shutil), validate structure |
| A8 | Provider abstraction | Base class + factory pattern (existing `BaseLLMProvider` pattern) | Extensible, clean, testable |
| A9 | Streaming | Generator functions yielding chunks | Python generators work with Blender timers for incremental UI updates |
| A10 | Error handling | Try/except with user-facing messages + console logging | Never crash Blender, always inform user |

---

## File Structure (Target)

```
blender_ai_toolkit/
├── __init__.py              # Registration, bl_info
├── manifest.toml            # Blender 4.2+ extension manifest
├── preferences.py           # API keys, provider URLs, settings
├── properties.py            # All Scene properties
├── api/
│   ├── __init__.py
│   ├── base.py              # GenerationRequest, GenerationResult
│   ├── http_client.py       # NEW: urllib-based HTTP client singleton
│   ├── llm/
│   │   ├── __init__.py
│   │   ├── base.py          # BaseLLMProvider (moved from openai_llm.py)
│   │   ├── openai.py        # NEW: OpenAI implementation
│   │   ├── anthropic.py     # NEW: Anthropic implementation
│   │   ├── ollama.py        # NEW: Ollama implementation
│   │   └── lmstudio.py      # NEW: LM Studio implementation
│   ├── model_3d/
│   │   ├── __init__.py
│   │   ├── base.py          # Base3DProvider
│   │   ├── tripo.py         # NEW: Tripo3D API
│   │   └── meshy.py         # NEW: Meshy API
│   ├── image/
│   │   ├── __init__.py
│   │   ├── base.py          # BaseImageProvider
│   │   ├── dalle.py         # NEW: DALL-E 3
│   │   ├── stability.py     # NEW: Stability AI
│   │   └── comfyui.py       # NEW: ComfyUI
│   ├── material/
│   │   ├── __init__.py
│   │   ├── base.py          # BaseMaterialProvider
│   │   ├── stability.py     # NEW: Stability AI
│   │   └── comfyui.py       # NEW: ComfyUI
│   └── hdri/
│       ├── __init__.py
│       ├── base.py          # BaseHDRIProvider
│       └── stability.py     # NEW: Stability AI
├── core/
│   ├── __init__.py
│   ├── task_queue.py        # FIXED: Real async execution with timers
│   ├── notifications/
│   │   └── notification_manager.py  # FIXED: Sync with UI
│   ├── scene_composer/
│   │   └── scene_composer.py  # FIXED: Camera direction, debug line
│   ├── templates/
│   │   └── template_manager.py  # FIXED: Persist to disk
│   ├── preview/             # EMPTY → remove or implement
│   └── workflow_presets/    # EMPTY → remove or implement
├── operators/
│   ├── __init__.py
│   ├── generate_3d.py       # IMPLEMENT: Wire to Tripo/Meshy
│   ├── generate_image.py    # IMPLEMENT: Wire to DALL-E/Stability
│   ├── chat.py              # IMPLEMENT: Real LLM calls + code exec
│   ├── asset_ops.py         # IMPLEMENT: Disk persistence + import
│   ├── template_ops.py      # IMPLEMENT: Disk persistence
│   ├── material_ops/
│   │   ├── generate_material.py  # IMPLEMENT
│   │   ├── texture_to_material.py  # IMPLEMENT
│   │   └── apply_hdri.py     # IMPLEMENT
│   ├── mesh_ops/
│   │   ├── mesh_cleanup.py   # IMPLEMENT
│   │   └── batch_generate.py  # IMPLEMENT
│   └── scene_ops/
│       └── compose_scene.py  # FIX: Wire to real LLM
├── ui/
│   ├── __init__.py
│   └── sidebar.py           # Polish: tooltips, error display
└── utils/
    ├── __init__.py
    ├── file_utils.py        # Add asset storage paths
    └── mesh_utils.py        # NEW: mesh cleanup, recovery, import
```

---

## Implementation Priority Matrix

| Feature | Impact | Effort | Priority |
|---------|--------|--------|----------|
| LLM Chat (OpenAI + Ollama) | HIGH | LOW | P0 — First |
| Task Queue fix | HIGH | LOW | P0 — First |
| HTTP Client | HIGH | LOW | P0 — First |
| 3D Generation (Tripo) | HIGH | MEDIUM | P1 — Second |
| 3D Generation (Meshy) | HIGH | MEDIUM | P1 — Second |
| Image Generation (DALL-E) | MEDIUM | LOW | P2 — Third |
| Material Generation | MEDIUM | MEDIUM | P2 — Third |
| HDRI Generation | MEDIUM | LOW | P2 — Third |
| Scene Composition fix | MEDIUM | LOW | P2 — Third |
| Asset Persistence | MEDIUM | LOW | P3 — Fourth |
| Template Persistence | LOW | LOW | P3 — Fourth |
| ComfyUI Integration | HIGH | HIGH | P4 — Fifth |
| Code Execution + Retry | HIGH | MEDIUM | P1 — Second |
| Mesh Cleanup | LOW | LOW | P5 — Last |
| Batch Generate | LOW | LOW | P5 — Last |

---

## Validation Plan

| Validator | Purpose | When |
|-----------|---------|------|
| Manual chat test | Send message → get real response | Phase 1 |
| Code execution test | AI generates bpy code → executes in Blender | Phase 1 |
| Tripo text-to-3D | Generate model → import GLB → verify mesh | Phase 2 |
| Meshy text-to-3D | Generate model → import GLB → verify mesh | Phase 2 |
| DALL-E image gen | Generate image → import to scene | Phase 3 |
| Material gen | Generate PBR → apply to cube → verify nodes | Phase 4 |
| HDRI gen | Generate HDRI → set as world → verify lighting | Phase 4 |
| Scene composition | Type "room with table" → verify objects created | Phase 5 |
| Persistence restart | Save asset → restart Blender → verify asset exists | Phase 6 |
| ComfyUI end-to-end | Generate via ComfyUI → verify output | Phase 7 |
| Multi-version test | Test on Blender 4.2, 4.3, 5.0 | Phase 8 |

---

## Risk Register

| Risk | Impact | Mitigation |
|------|--------|------------|
| Blender's GIL blocks threading | MEDIUM | I/O-bound HTTP calls release GIL; test early |
| API rate limits | LOW | Add retry with exponential backoff |
| GLB import fails on some models | MEDIUM | Add mesh recovery utilities |
| ComfyUI not installed | LOW | ComfyUI providers show "not connected" gracefully |
| API key security | HIGH | Never log keys, use PASSWORD subtype, local storage only |
| Blender version API changes | MEDIUM | Version checks in code, fallback paths |
| Large model downloads | LOW | Progress indicators, cancel support |
