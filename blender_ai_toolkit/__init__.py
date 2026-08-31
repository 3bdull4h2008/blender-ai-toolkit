"""
Blender AI Toolkit - AI-powered 3D generation, image creation, and LLM chat for Blender.
========================================================================================

A comprehensive Blender extension that integrates multiple AI services for:
- Text/Image to 3D model generation (Meshy, Tripo3D, Luma, CSM, ComfyUI)
- Text to image generation (DALL-E 3, Stability AI, ComfyUI)
- PBR Material generation (Stability AI, ComfyUI)
- HDRI environment map generation (Stability AI)
- LLM Chat & Blender Python code generation (OpenAI, Anthropic, Ollama, LM Studio)
- Scene composition from text descriptions
- Prompt template library
- Batch generation
- Mesh cleanup
- Asset management with Model ID tracking

Version: 2.1.1
Blender: 4.2+
License: MIT
"""

bl_info = {
    "name": "AI Toolkit",
    "author": "AI Toolkit Contributors",
    "version": (2, 1, 1),
    "blender": (4, 2, 0),
    "location": "View3D > Sidebar > AI Toolkit",
    "description": "AI-powered 3D model generation, PBR materials, HDRI, scene composition, and LLM chat",
    "category": "3D View",
    "doc_url": "https://github.com/blender-ai-toolkit/docs",
    "tracker_url": "https://github.com/blender-ai-toolkit/issues",
}

import bpy


# =============================================================================
# Registration Helper
# =============================================================================

def _safe_register_class(cls):
    """Safely register a Blender class with error handling."""
    try:
        bpy.utils.register_class(cls)
        return True
    except ValueError as e:
        if "already registered" in str(e):
            print(f"[AI Toolkit] {cls.__name__} already registered")
            return True
        raise


def _safe_unregister_class(cls):
    """Safely unregister a Blender class."""
    try:
        bpy.utils.unregister_class(cls)
    except (ValueError, RuntimeError):
        pass


# =============================================================================
# Register
# =============================================================================

def register():
    """Register all add-on modules in the correct order."""
    print("[AI Toolkit] Registering...")

    # 1. Preferences
    from . import preferences
    preferences.register()

    # 2. Properties
    from . import properties
    properties.register()

    # 3. Operators - Core
    from .operators import generate_3d, generate_image, chat, asset_ops
    from .operators.material_ops import generate_material, texture_to_material, apply_hdri
    from .operators.scene_ops import compose_scene
    from .operators.mesh_ops import mesh_cleanup, batch_generate
    from .operators.template_ops import (
        AIApplyTemplateOperator,
        AIRefreshTemplatesOperator,
        AISaveTemplateOperator,
    )
    from .ui.sidebar import AISetTabOperator, AIToolkitPanel

    # All operator classes in registration order
    operator_classes = [
        # Tab switcher
        AISetTabOperator,
        # 3D Generation
        generate_3d.AIGenerate3DOperator,
        generate_3d.AIGenerate3DRefImageOperator,
        # Image Generation
        generate_image.AIGenerateImageOperator,
        # Material Operations
        generate_material.AIGenerateMaterialOperator,
        texture_to_material.AITextureToMaterialOperator,
        apply_hdri.AIApplyHDRIOperator,
        # Scene Composition
        compose_scene.AIComposeSceneOperator,
        compose_scene.AIGenerateSceneAIObjectsOperator,
        # Mesh Operations
        mesh_cleanup.AIMeshCleanupOperator,
        batch_generate.AIBatchGenerateOperator,
        # Chat Operations
        chat.AIChatOperator,
        chat.AIChatClearHistoryOperator,
        chat.AIChatExecuteCodeOperator,
        # Asset Management
        asset_ops.AIAssetImportOperator,
        asset_ops.AIAssetDeleteOperator,
        asset_ops.AIAssetDuplicateOperator,
        asset_ops.AIAssetToggleFavoriteOperator,
        asset_ops.AIAssetRefreshOperator,
        asset_ops.AICancelGenerationOperator,
        # Template Operations
        AIApplyTemplateOperator,
        AIRefreshTemplatesOperator,
        AISaveTemplateOperator,
    ]

    for cls in operator_classes:
        _safe_register_class(cls)

    # 4. UI Panel
    _safe_register_class(AIToolkitPanel)

    # 5. Start task queue
    from .core.task_queue import get_task_queue
    get_task_queue().start()

    print("[AI Toolkit] Registered successfully v2.1.1")


# =============================================================================
# Unregister
# =============================================================================

def unregister():
    """Unregister all add-on modules in reverse order."""
    print("[AI Toolkit] Unregistering...")

    # Import all modules
    from .ui.sidebar import AIToolkitPanel, AISetTabOperator
    from .operators.asset_ops import (
        AIAssetImportOperator, AIAssetDeleteOperator, AIAssetDuplicateOperator,
        AIAssetToggleFavoriteOperator, AIAssetRefreshOperator, AICancelGenerationOperator,
    )
    from .operators.chat import AIChatOperator, AIChatClearHistoryOperator, AIChatExecuteCodeOperator
    from .operators.generate_3d import AIGenerate3DOperator, AIGenerate3DRefImageOperator
    from .operators.generate_image import AIGenerateImageOperator
    from .operators.material_ops.generate_material import AIGenerateMaterialOperator
    from .operators.material_ops.texture_to_material import AITextureToMaterialOperator
    from .operators.material_ops.apply_hdri import AIApplyHDRIOperator
    from .operators.scene_ops.compose_scene import AIComposeSceneOperator, AIGenerateSceneAIObjectsOperator
    from .operators.mesh_ops.mesh_cleanup import AIMeshCleanupOperator
    from .operators.mesh_ops.batch_generate import AIBatchGenerateOperator
    from .operators.template_ops import (
        AIApplyTemplateOperator, AIRefreshTemplatesOperator, AISaveTemplateOperator,
    )

    # All classes in reverse order
    all_classes = [
        AIToolkitPanel,
        AISaveTemplateOperator,
        AIRefreshTemplatesOperator,
        AIApplyTemplateOperator,
        AICancelGenerationOperator,
        AIAssetRefreshOperator,
        AIAssetToggleFavoriteOperator,
        AIAssetDuplicateOperator,
        AIAssetDeleteOperator,
        AIAssetImportOperator,
        AIChatExecuteCodeOperator,
        AIChatClearHistoryOperator,
        AIChatOperator,
        AIBatchGenerateOperator,
        AIMeshCleanupOperator,
        AIGenerateSceneAIObjectsOperator,
        AIComposeSceneOperator,
        AIApplyHDRIOperator,
        AITextureToMaterialOperator,
        AIGenerateMaterialOperator,
        AIGenerateImageOperator,
        AIGenerate3DRefImageOperator,
        AIGenerate3DOperator,
        AISetTabOperator,
    ]

    for cls in all_classes:
        _safe_unregister_class(cls)

    # Properties
    from . import properties
    properties.unregister()

    # Preferences
    from . import preferences
    preferences.unregister()

    # Shutdown task queue
    try:
        from .core.task_queue import get_task_queue
        get_task_queue().shutdown()
    except Exception:
        pass

    print("[AI Toolkit] Unregistered")


if __name__ == "__main__":
    register()
