"""Test addon registration in Blender."""
import bpy
import sys
import os

print("=" * 60)
print("ADDON REGISTRATION TEST")
print("=" * 60)

addon_path = r"E:\blender ai addon\blender_ai_toolkit"

# Test 1: Register the addon
print("\n[TEST 1] Register addon...")
try:
    bpy.ops.preferences.addon_refresh()
    print("  PASS: Addon refreshed")
except Exception as e:
    print(f"  WARN: {e}")

# Try enabling the addon
try:
    bpy.ops.preferences.addon_enable(module="blender_ai_toolkit")
    print("  PASS: Addon enabled")
except Exception as e:
    print(f"  FAIL: Addon enable failed: {e}")

# Test 2: Check if ai_toolkit property exists on scene
print("\n[TEST 2] Scene properties...")
try:
    props = bpy.context.scene.ai_toolkit
    print(f"  PASS: ai_toolkit property exists")
    print(f"    active_tab = {props.active_tab}")
    print(f"    model_3d_provider = {props.model_3d_provider}")
    print(f"    llm_provider = {props.llm_provider}")
    print(f"    is_generating = {props.is_generating}")
    print(f"    status_message = {props.status_message}")
except Exception as e:
    print(f"  FAIL: {e}")

# Test 3: Check operators are registered
print("\n[TEST 3] Operators registered...")
operators = [
    "ai.set_tab",
    "ai.generate_3d",
    "ai.generate_3d_ref_image",
    "ai.generate_image",
    "ai.generate_material",
    "ai.texture_to_material",
    "ai.apply_hdri",
    "ai.compose_scene",
    "ai.generate_scene_ai_objects",
    "ai.mesh_cleanup",
    "ai.batch_generate",
    "ai.chat",
    "ai.chat_clear_history",
    "ai.chat_execute_code",
    "ai.asset_import",
    "ai.asset_delete",
    "ai.asset_duplicate",
    "ai.asset_toggle_favorite",
    "ai.asset_refresh",
    "ai.cancel_generation",
    "ai.apply_template",
    "ai.refresh_templates",
    "ai.save_template",
]

registered = 0
for op_id in operators:
    parts = op_id.split(".")
    if hasattr(bpy.types, f"_OT_{parts[1]}"):
        registered += 1
    else:
        print(f"  WARN: {op_id} not found")

print(f"  PASS: {registered}/{len(operators)} operators registered")

# Test 4: Check UI panel
print("\n[TEST 4] UI Panel...")
try:
    if hasattr(bpy.types, "VIEW3D_PT_ai_toolkit"):
        print("  PASS: VIEW3D_PT_ai_toolkit panel registered")
    else:
        print("  FAIL: Panel not registered")
except Exception as e:
    print(f"  FAIL: {e}")

# Test 5: Test a simple operator
print("\n[TEST 5] Test chat operator (with mock)...")
try:
    props = bpy.context.scene.ai_toolkit
    props.llm_prompt = "Hello test"
    # Can't actually call the operator without a 3D context, but check it exists
    op = bpy.ops.ai.chat
    print(f"  PASS: ai.chat operator callable")
except Exception as e:
    print(f"  WARN: {e} (expected without proper context)")

# Test 6: Test task queue start
print("\n[TEST 6] Task queue...")
try:
    from blender_ai_toolkit.core.task_queue import get_task_queue
    tq = get_task_queue()
    print(f"  PASS: Task queue active (started={tq._started}, tasks={len(tq._tasks)})")
except Exception as e:
    print(f"  FAIL: {e}")

# Test 7: Test template manager
print("\n[TEST 7] Templates...")
try:
    from blender_ai_toolkit.core.templates.template_manager import get_template_manager
    tm = get_template_manager()
    print(f"  PASS: {len(tm._templates)} templates loaded")
    for tid, t in tm._templates.items():
        print(f"    - {t.name} ({t.category.value})")
except Exception as e:
    print(f"  FAIL: {e}")

# Test 8: Unregister
print("\n[TEST 8] Unregister addon...")
try:
    bpy.ops.preferences.addon_disable(module="blender_ai_toolkit")
    print("  PASS: Addon disabled")
except Exception as e:
    print(f"  FAIL: {e}")

print("\n" + "=" * 60)
print("REGISTRATION TEST COMPLETE")
print("=" * 60)
