"""Test script for Blender AI Toolkit addon."""
import sys
import os

# Add the addon path
addon_path = r"E:\blender ai addon"
sys.path.insert(0, addon_path)

print("=" * 60)
print("BLENDER AI TOOLKIT — TEST SCRIPT")
print(f"Python: {sys.version}")
print(f"Blender path: {addon_path}")
print("=" * 60)

# Test 1: Check all Python files for syntax errors
print("\n[TEST 1] Syntax check...")
errors = []
for root, dirs, files in os.walk(os.path.join(addon_path, "blender_ai_toolkit")):
    for f in files:
        if f.endswith(".py"):
            filepath = os.path.join(root, f)
            try:
                with open(filepath, "r", encoding="utf-8") as fh:
                    compile(fh.read(), filepath, "exec")
            except SyntaxError as e:
                errors.append(f"  FAIL: {filepath}: {e}")
                print(f"  FAIL: {filepath}: {e}")

if not errors:
    print("  PASS: All .py files compile clean")
else:
    print(f"  FAIL: {len(errors)} syntax errors found")

# Test 2: Check imports work (non-bpy modules)
print("\n[TEST 2] Import check (non-bpy modules)...")
sys.path.insert(0, os.path.join(addon_path, "blender_ai_toolkit"))

try:
    from api.base import GenerationRequest, GenerationResult
    print("  PASS: api.base")
except Exception as e:
    print(f"  FAIL: api.base: {e}")

try:
    from api.http_client import HTTPClient, get_http_client
    client = get_http_client()
    print(f"  PASS: api.http_client (timeout={client.timeout}, retries={client.max_retries})")
except Exception as e:
    print(f"  FAIL: api.http_client: {e}")

try:
    from api.llm.openai_llm import (
        BaseLLMProvider, OpenAILLMProvider, AnthropicLLMProvider,
        OllamaLLMProvider, LMStudioLLMProvider, get_llm_provider
    )
    print("  PASS: api.llm.openai_llm (all 5 provider classes)")
except Exception as e:
    print(f"  FAIL: api.llm.openai_llm: {e}")

try:
    from api.model_3d.providers import Tripo3DProvider, MeshyProvider
    print("  PASS: api.model_3d.providers")
except Exception as e:
    print(f"  FAIL: api.model_3d.providers: {e}")

try:
    from api.image.providers import DallEProvider, StabilityProvider, get_image_provider
    print("  PASS: api.image.providers")
except Exception as e:
    print(f"  FAIL: api.image.providers: {e}")

try:
    from core.task_queue import TaskQueue, TaskStatus, TaskInfo, get_task_queue
    print("  PASS: core.task_queue")
except Exception as e:
    print(f"  FAIL: core.task_queue: {e}")

try:
    from core.notifications.notification_manager import NotificationManager, get_notification_manager
    print("  PASS: core.notifications.notification_manager")
except Exception as e:
    print(f"  FAIL: core.notifications.notification_manager: {e}")

try:
    from core.templates.template_manager import TemplateManager, get_template_manager
    tm = get_template_manager()
    print(f"  PASS: core.templates.template_manager ({len(tm._templates)} templates)")
except Exception as e:
    print(f"  FAIL: core.templates.template_manager: {e}")

try:
    from core.scene_composer.scene_composer import SceneComposer, get_scene_composer
    print("  PASS: core.scene_composer.scene_composer")
except Exception as e:
    print(f"  FAIL: core.scene_composer.scene_composer: {e}")

# Test 3: Provider instantiation
print("\n[TEST 3] Provider instantiation...")
providers_to_test = [
    ("OpenAI", OpenAILLMProvider, {"api_key": "sk-test123"}),
    ("Anthropic", AnthropicLLMProvider, {"api_key": "sk-ant-test123"}),
    ("Ollama", OllamaLLMProvider, {}),
    ("LMStudio", LMStudioLLMProvider, {}),
    ("Tripo3D", Tripo3DProvider, {"api_key": "test_key"}),
    ("Meshy", MeshyProvider, {"api_key": "test_key"}),
    ("DALL-E", DallEProvider, {"api_key": "sk-test123"}),
    ("Stability", StabilityProvider, {"api_key": "test_key"}),
]

for name, cls, config in providers_to_test:
    try:
        p = cls(config)
        print(f"  PASS: {name} (is_configured={p.is_configured})")
    except Exception as e:
        print(f"  FAIL: {name}: {e}")

# Test 4: Task queue
print("\n[TEST 4] Task queue...")
try:
    tq = get_task_queue()
    print(f"  PASS: TaskQueue created (tasks={len(tq._tasks)})")
except Exception as e:
    print(f"  FAIL: TaskQueue: {e}")

# Test 5: HTTP client
print("\n[TEST 5] HTTP client...")
try:
    client = get_http_client()
    result = client.get("https://httpbin.org/get", timeout=10)
    if "error" not in result or result.get("status") == 200:
        print("  PASS: HTTP GET works")
    else:
        print(f"  WARN: HTTP GET returned: {result.get('message', result)}")
except Exception as e:
    print(f"  FAIL: HTTP client: {e}")

# Test 6: LLM provider factory
print("\n[TEST 6] LLM provider factory...")
for pid in ["openai", "anthropic", "ollama", "lmstudio"]:
    try:
        p = get_llm_provider(pid, None)
        if p is None:
            print(f"  WARN: get_llm_provider('{pid}') returned None (no prefs)")
        else:
            print(f"  PASS: get_llm_provider('{pid}') -> {type(p).__name__}")
    except Exception as e:
        print(f"  FAIL: get_llm_provider('{pid}'): {e}")

# Test 7: Check manifest.toml
print("\n[TEST 7] Manifest check...")
manifest_path = os.path.join(addon_path, "blender_ai_toolkit", "manifest.toml")
if os.path.exists(manifest_path):
    import tomllib
    with open(manifest_path, "rb") as f:
        manifest = tomllib.load(f)
    print(f"  PASS: manifest.toml (id={manifest.get('id')}, v={manifest.get('version')}, min={manifest.get('blender_version_min')})")
else:
    print("  FAIL: manifest.toml not found")

print("\n" + "=" * 60)
print("TEST COMPLETE")
print("=" * 60)
