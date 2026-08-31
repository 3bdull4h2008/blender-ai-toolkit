"""
Blender Preferences - Add-on preferences for API keys and provider configuration.
Accessible from Edit > Preferences > Add-ons > AI Toolkit.
"""

import bpy
from bpy.types import AddonPreferences
from bpy.props import (
    StringProperty,
    BoolProperty,
    IntProperty,
    EnumProperty,
)


class AIToolkitPreferences(AddonPreferences):
    """AI Toolkit add-on preferences - configure API keys and endpoints."""
    bl_idname = "blender_ai_toolkit"

    # === Provider API Keys ===
    # 3D Providers
    meshy_api_key: StringProperty(
        name="Meshy API Key",
        description="API key for Meshy.ai 3D generation",
        default="",
        subtype='PASSWORD',
    )
    tripo_api_key: StringProperty(
        name="Tripo API Key",
        description="API key for Tripo3D",
        default="",
        subtype='PASSWORD',
    )
    luma_api_key: StringProperty(
        name="Luma API Key",
        description="API key for Luma AI",
        default="",
        subtype='PASSWORD',
    )
    csm_api_key: StringProperty(
        name="CSM API Key",
        description="API key for Common Sense Machines",
        default="",
        subtype='PASSWORD',
    )

    # Image Providers
    openai_api_key: StringProperty(
        name="OpenAI API Key",
        description="API key for OpenAI (DALL-E + GPT)",
        default="",
        subtype='PASSWORD',
    )
    stability_api_key: StringProperty(
        name="Stability AI API Key",
        description="API key for Stability AI",
        default="",
        subtype='PASSWORD',
    )

    # LLM Providers
    anthropic_api_key: StringProperty(
        name="Anthropic API Key",
        description="API key for Anthropic Claude",
        default="",
        subtype='PASSWORD',
    )

    # === Local Provider URLs ===
    comfyui_url: StringProperty(
        name="ComfyUI URL",
        description="URL for local ComfyUI instance",
        default="http://127.0.0.1:8188",
    )
    ollama_url: StringProperty(
        name="Ollama URL",
        description="URL for local Ollama instance",
        default="http://127.0.0.1:11434",
    )
    lmstudio_url: StringProperty(
        name="LM Studio URL",
        description="URL for local LM Studio instance",
        default="http://127.0.0.1:1234/v1",
    )

    # === OpenAI Base URL (for custom endpoints) ===
    openai_base_url: StringProperty(
        name="OpenAI Base URL",
        description="Custom base URL for OpenAI-compatible API",
        default="https://api.openai.com/v1",
    )

    # === General Settings ===
    auto_import: BoolProperty(
        name="Auto Import",
        description="Automatically import generated assets into the scene",
        default=True,
    )
    max_concurrent_tasks: IntProperty(
        name="Max Concurrent Tasks",
        description="Maximum number of concurrent API tasks",
        default=3,
        min=1,
        max=10,
    )
    show_notifications: BoolProperty(
        name="Show Notifications",
        description="Show popup notifications when tasks complete",
        default=True,
    )
    debug_mode: BoolProperty(
        name="Debug Mode",
        description="Enable debug logging to console",
        default=False,
    )
    auto_free_vram: BoolProperty(
        name="Auto Free VRAM",
        description="Automatically free VRAM after ComfyUI generation",
        default=True,
    )
    preview_count: IntProperty(
        name="Preview Count",
        description="Number of preview images to generate",
        default=4,
        min=2,
        max=8,
    )

    # === Default Models ===
    default_llm_model: StringProperty(
        name="Default LLM Model",
        description="Default model identifier for LLM provider",
        default="",
    )
    default_image_model: StringProperty(
        name="Default Image Model",
        description="Default model for image generation",
        default="dall-e-3",
    )

    def draw(self, context):
        layout = self.layout

        # 3D Providers Section
        box = layout.box()
        box.label(text="3D Model Generation", icon='MESH_DATA')
        col = box.column(align=True)
        col.prop(self, "meshy_api_key")
        col.prop(self, "tripo_api_key")
        col.prop(self, "luma_api_key")
        col.prop(self, "csm_api_key")

        # Image Providers Section
        box = layout.box()
        box.label(text="Image Generation", icon='IMAGE_DATA')
        col = box.column(align=True)
        col.prop(self, "openai_api_key")
        col.prop(self, "stability_api_key")

        # LLM Providers Section
        box = layout.box()
        box.label(text="LLM Chat & Code", icon='CONSOLE')
        col = box.column(align=True)
        col.prop(self, "anthropic_api_key")
        col.prop(self, "openai_api_key")  # Shared key with DALL-E

        # Local Providers Section
        box = layout.box()
        box.label(text="Local Providers", icon='SYSTEM')
        col = box.column(align=True)
        col.prop(self, "comfyui_url")
        col.prop(self, "ollama_url")
        col.prop(self, "lmstudio_url")

        # Advanced Settings
        box = layout.box()
        box.label(text="Advanced", icon='SETTINGS')
        col = box.column(align=True)
        col.prop(self, "openai_base_url")
        col.prop(self, "auto_import")
        col.prop(self, "max_concurrent_tasks")
        col.prop(self, "show_notifications")
        col.prop(self, "debug_mode")
        col.prop(self, "auto_free_vram")
        col.prop(self, "preview_count")

    def get_provider_config(self, provider_id: str) -> dict:
        """Get configuration dict for a specific provider."""
        configs = {
            "meshy": {"api_key": self.meshy_api_key},
            "tripo": {"api_key": self.tripo_api_key},
            "luma": {"api_key": self.luma_api_key},
            "csm": {"api_key": self.csm_api_key},
            "comfy_3d": {"base_url": self.comfyui_url},
            "dalle": {"api_key": self.openai_api_key, "base_url": self.openai_base_url},
            "stability": {"api_key": self.stability_api_key},
            "comfy_image": {"base_url": self.comfyui_url},
            "openai": {"api_key": self.openai_api_key, "base_url": self.openai_base_url},
            "anthropic": {"api_key": self.anthropic_api_key},
            "ollama": {"base_url": self.ollama_url},
            "lmstudio": {"base_url": self.lmstudio_url},
            # Material providers
            "stability_material": {"api_key": self.stability_api_key},
            "comfy_material": {"base_url": self.comfyui_url},
            # HDRI providers
            "stability_hdri": {"api_key": self.stability_api_key},
            "comfy_hdri": {"base_url": self.comfyui_url},
        }
        return configs.get(provider_id, {})


classes = [AIToolkitPreferences]


def register():
    for cls in classes:
        try:
            bpy.utils.register_class(cls)
        except ValueError as e:
            if "already registered" in str(e):
                print(f"[AI Toolkit] {cls.__name__} already registered, skipping...")
            else:
                raise


def unregister():
    for cls in reversed(classes):
        try:
            bpy.utils.unregister_class(cls)
        except Exception:
            pass
