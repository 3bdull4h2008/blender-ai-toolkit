"""
Blender Properties - Scene-level properties for the AI Toolkit.
These properties store the current state of the UI and generation parameters.
"""

import bpy
from bpy.types import PropertyGroup
from bpy.props import (
    StringProperty,
    BoolProperty,
    IntProperty,
    FloatProperty,
    EnumProperty,
    PointerProperty,
    CollectionProperty,
)


# =============================================================================
# Static Enum Items (compatible with all Blender versions)
# =============================================================================

PROVIDERS_3D = [
    ("meshy", "Meshy.ai", "Meshy.ai text/image-to-3D cloud API", 0),
    ("tripo", "Tripo3D", "Tripo3D fast 3D generation", 1),
    ("luma", "Luma AI", "Luma AI high-quality 3D", 2),
    ("csm", "CSM", "Common Sense Machines 3D", 3),
    ("comfy_3d", "ComfyUI (Local)", "Local ComfyUI 3D generation", 4),
]

PROVIDERS_IMAGE = [
    ("dalle", "DALL-E 3", "OpenAI DALL-E 3 image generation", 0),
    ("stability", "Stability AI", "Stability AI Stable Diffusion cloud", 1),
    ("comfy_image", "ComfyUI (Local)", "Local ComfyUI image generation", 2),
]

PROVIDERS_LLM = [
    ("openai", "OpenAI GPT", "OpenAI GPT-4/GPT-3.5", 0),
    ("anthropic", "Anthropic Claude", "Claude AI chat", 1),
    ("ollama", "Ollama (Local)", "Local LLM via Ollama", 2),
    ("lmstudio", "LM Studio (Local)", "Local LLM via LM Studio", 3),
]

PROVIDERS_MATERIAL = [
    ("stability_material", "Stability AI", "Stability AI PBR texture generation", 0),
    ("comfy_material", "ComfyUI (Local)", "Local ComfyUI material generation", 1),
]

TEMPLATE_CATEGORIES = [
    ("ALL", "All", "All templates", 0),
    ("character", "Characters", "Character templates", 1),
    ("environment", "Environments", "Environment templates", 2),
    ("prop", "Props", "Prop templates", 3),
    ("vehicle", "Vehicles", "Vehicle templates", 4),
    ("weapon", "Weapons", "Weapon templates", 5),
    ("architecture", "Architecture", "Building templates", 6),
    ("nature", "Nature", "Nature templates", 7),
    ("furniture", "Furniture", "Furniture templates", 8),
    ("texture", "Textures", "Texture templates", 9),
    ("hdri", "HDRI", "HDRI templates", 10),
    ("abstract", "Abstract", "Abstract templates", 11),
    ("custom", "Custom", "User-created templates", 12),
]

ART_STYLES = [
    ("realistic", "Realistic", "Photorealistic style"),
    ("cartoon", "Cartoon", "Stylized cartoon look"),
    ("low-poly", "Low Poly", "Low polygon count style"),
    ("anime", "Anime", "Anime/manga inspired"),
    ("cinematic", "Cinematic", "Movie-quality render style"),
    ("fantasy", "Fantasy", "Fantasy art style"),
]

IMAGE_SIZES = [
    ("512x512", "512 x 512", "Square small"),
    ("1024x1024", "1024 x 1024", "Square standard"),
    ("1024x1792", "1024 x 1792", "Portrait tall"),
    ("1792x1024", "1792 x 1024", "Landscape wide"),
]

IMAGE_QUALITY = [
    ("standard", "Standard", "Standard quality"),
    ("hd", "HD", "High detail quality"),
]

IMAGE_STYLES = [
    ("none", "None", "No style preset"),
    ("3d-model", "3D Model", "3D model render style"),
    ("anime", "Anime", "Anime illustration"),
    ("cinematic", "Cinematic", "Cinematic film look"),
    ("digital-art", "Digital Art", "Digital artwork"),
    ("photographic", "Photographic", "Photorealistic photo"),
    ("pixel-art", "Pixel Art", "Retro pixel art"),
    ("fantasy-art", "Fantasy Art", "Fantasy illustration"),
    ("tile-texture", "Tile Texture", "Tileable texture"),
]

HDRI_STYLES = [
    ("none", "None", "No style modifier"),
    ("photographic", "Photographic", "Realistic photography"),
    ("cinematic", "Cinematic", "Film-like lighting"),
    ("fantasy-art", "Fantasy", "Fantasy atmosphere"),
    ("digital-art", "Digital Art", "Artistic interpretation"),
]

ASSET_FILTER_TYPES = [
    ("ALL", "All", "Show all assets"),
    ("model_3d", "3D Models", "Show 3D models only"),
    ("image", "Images", "Show images only"),
    ("material", "Materials", "Show materials only"),
]


# =============================================================================
# Property Groups for Collections
# =============================================================================

class AIHistoryItem(PropertyGroup):
    """Single entry in generation history."""
    entry_id: StringProperty(name="Entry ID", default="")
    prompt: StringProperty(name="Prompt", default="")
    task_type: StringProperty(name="Task Type", default="")
    provider_id: StringProperty(name="Provider ID", default="")
    model_id: StringProperty(name="Model ID", default="")
    success: BoolProperty(name="Success", default=False)
    created_at: StringProperty(name="Created At", default="")


class AIAssetItem(PropertyGroup):
    """Single asset in the asset library."""
    model_id: StringProperty(name="Model ID", default="")
    asset_type: StringProperty(name="Asset Type", default="model_3d")
    prompt: StringProperty(name="Prompt", default="")
    provider_id: StringProperty(name="Provider ID", default="")
    status: StringProperty(name="Status", default="ready")
    favorite: BoolProperty(name="Favorite", default=False)
    file_path: StringProperty(name="File Path", subtype='FILE_PATH', default="")
    created_at: StringProperty(name="Created At", default="")


class AITemplateItem(PropertyGroup):
    """Single template in the template list (for UI display)."""
    template_id: StringProperty(name="Template ID", default="")
    name: StringProperty(name="Name", default="")
    category: StringProperty(name="Category", default="")
    prompt: StringProperty(name="Prompt Preview", default="")


class AINotificationItem(PropertyGroup):
    """Single notification entry."""
    title: StringProperty(name="Title", default="")
    message: StringProperty(name="Message", default="")
    notif_type: StringProperty(name="Type", default="info")  # info, warning, error, success
    timestamp: StringProperty(name="Timestamp", default="")
    read: BoolProperty(name="Read", default=False)


# =============================================================================
# Main Property Group
# =============================================================================

class AIToolkitProperties(PropertyGroup):
    """
    Main property group for the AI Toolkit.
    Stores all UI state, generation parameters, and configuration.
    """

    # === Active Tab ===
    active_tab: EnumProperty(
        name="Active Tab",
        description="Select the active AI feature tab",
        items=[
            ("MODEL_3D", "3D", "Generate 3D models from text/images", "MESH_DATA", 0),
            ("IMAGE", "Img", "Generate images from text", "IMAGE_DATA", 1),
            ("MATERIAL", "Mat", "Generate PBR materials & HDRI", "MATERIAL", 2),
            ("CHAT", "Chat", "AI Chat & Code Assistant", "CONSOLE", 3),
            ("SCENE", "Scene", "Compose scenes from text", "SCENE_DATA", 4),
            ("ASSETS", "Assets", "Manage AI-generated assets", "OUTLINER", 5),
            ("TEMPLATES", "Templates", "Prompt template library", "BOOKMARKS", 6),
            ("SETTINGS", "Set", "Configure API providers", "PREFERENCES", 7),
        ],
        default="MODEL_3D",
    )

    # === 3D Model Generation ===
    model_3d_provider: EnumProperty(
        name="3D Provider",
        description="Select 3D model generation provider",
        items=PROVIDERS_3D,
        default="meshy",
    )
    model_3d_prompt: StringProperty(
        name="Prompt",
        description="Describe the 3D model you want to generate",
        default="",
        maxlen=2000,
    )
    model_3d_negative_prompt: StringProperty(
        name="Negative Prompt",
        description="What to avoid in the generated model",
        default="",
        maxlen=500,
    )
    model_3d_reference_image: StringProperty(
        name="Reference Image",
        description="Optional reference image for image-to-3D",
        subtype='FILE_PATH',
        default="",
    )
    model_3d_art_style: EnumProperty(
        name="Art Style",
        description="Visual style for the generated model",
        items=ART_STYLES,
        default="realistic",
    )
    model_3d_seed: IntProperty(
        name="Seed",
        description="Random seed for reproducible results (0 = random)",
        default=0,
        min=0,
        max=2147483647,
    )
    model_3d_auto_import: BoolProperty(
        name="Auto Import",
        description="Automatically import generated models into scene",
        default=True,
    )
    model_3d_use_preview: BoolProperty(
        name="Preview First",
        description="Preview model before final import",
        default=False,
    )

    # === Image Generation ===
    image_provider: EnumProperty(
        name="Provider",
        description="Select image generation provider",
        items=PROVIDERS_IMAGE,
        default="dalle",
    )
    image_prompt: StringProperty(
        name="Prompt",
        description="Describe the image you want to generate",
        default="",
        maxlen=4000,
    )
    image_negative_prompt: StringProperty(
        name="Negative Prompt",
        description="What to avoid in the image",
        default="",
        maxlen=500,
    )
    image_size: EnumProperty(
        name="Size",
        description="Output image dimensions",
        items=IMAGE_SIZES,
        default="1024x1024",
    )
    image_quality: EnumProperty(
        name="Quality",
        description="Generation quality level",
        items=IMAGE_QUALITY,
        default="standard",
    )
    image_style_preset: EnumProperty(
        name="Style",
        description="Style preset for generation",
        items=IMAGE_STYLES,
        default="none",
    )
    image_auto_import: BoolProperty(
        name="Import as Plane",
        description="Auto-import generated image as a plane texture",
        default=True,
    )
    image_seed: IntProperty(
        name="Seed",
        description="Random seed (0 = random)",
        default=0,
        min=0,
        max=2147483647,
    )

    # === Material Generation ===
    material_provider: EnumProperty(
        name="Provider",
        description="Select material/texture generation provider",
        items=PROVIDERS_MATERIAL,
        default="stability_material",
    )
    material_prompt: StringProperty(
        name="Material Prompt",
        description="Describe the material or texture to generate",
        default="",
        maxlen=2000,
    )
    material_negative_prompt: StringProperty(
        name="Negative Prompt",
        default="",
        maxlen=500,
    )
    material_seamless: BoolProperty(
        name="Seamless/Tiling",
        description="Generate tileable textures",
        default=True,
    )
    material_apply_to_selected: BoolProperty(
        name="Apply to Selected",
        description="Apply generated material to selected object",
        default=True,
    )
    material_resolution: IntProperty(
        name="Resolution",
        description="Texture resolution in pixels",
        default=1024,
        min=256,
        max=4096,
    )
    # Texture map types to generate
    material_gen_diffuse: BoolProperty(name="Diffuse/Albedo", default=True)
    material_gen_normal: BoolProperty(name="Normal Map", default=True)
    material_gen_roughness: BoolProperty(name="Roughness", default=True)
    material_gen_metallic: BoolProperty(name="Metallic", default=False)
    material_gen_displacement: BoolProperty(name="Displacement", default=False)
    material_gen_ao: BoolProperty(name="Ambient Occlusion", default=False)
    material_seed: IntProperty(name="Seed", default=0, min=0, max=2147483647)

    # === HDRI Generation ===
    hdri_provider: EnumProperty(
        name="HDRI Provider",
        description="Select HDRI generation provider",
        items=[
            ("stability_hdri", "Stability AI", "Stability AI HDRI generation", 0),
            ("comfy_hdri", "ComfyUI (Local)", "Local ComfyUI HDRI generation", 1),
        ],
        default="stability_hdri",
    )
    hdri_prompt: StringProperty(
        name="Environment Description",
        description="Describe the environment/lighting for HDRI",
        default="",
        maxlen=2000,
    )
    hdri_negative_prompt: StringProperty(name="Negative Prompt", default="", maxlen=500)
    hdri_style: EnumProperty(
        name="Style",
        description="HDRI environment style",
        items=HDRI_STYLES,
        default="photographic",
    )
    hdri_seed: IntProperty(name="Seed", default=0, min=0, max=2147483647)

    # === LLM Chat ===
    llm_provider: EnumProperty(
        name="Provider",
        description="Select LLM chat provider",
        items=PROVIDERS_LLM,
        default="openai",
    )
    llm_prompt: StringProperty(
        name="Message",
        description="Your message or question for the AI",
        default="",
        maxlen=8000,
    )
    llm_system_prompt: StringProperty(
        name="System Prompt",
        description="Custom system prompt for the AI assistant",
        default="You are a helpful Blender expert assistant. Help with 3D modeling, "
                "materials, lighting, Python scripting, and general Blender questions.",
        maxlen=4000,
    )
    llm_response: StringProperty(
        name="AI Response",
        description="Latest AI response (read-only)",
        default="",
    )
    llm_temperature: FloatProperty(
        name="Temperature",
        description="Response creativity (0 = focused, 2 = creative)",
        default=0.7,
        min=0.0,
        max=2.0,
        step=0.1,
        precision=2,
    )
    llm_max_tokens: IntProperty(
        name="Max Tokens",
        description="Maximum response length",
        default=4096,
        min=256,
        max=128000,
    )
    llm_execute_code: BoolProperty(
        name="Execute Code",
        description="Auto-execute Blender Python code from responses",
        default=False,
    )
    llm_retry_on_error: BoolProperty(
        name="Retry on Error",
        description="Automatically send traceback to LLM for correction",
        default=True,
    )

    # === Scene Composer ===
    scene_prompt: StringProperty(
        name="Scene Description",
        description="Describe the scene you want to create",
        default="",
        maxlen=4000,
    )
    scene_include_ai_objects: BoolProperty(
        name="Include AI Objects",
        description="Include AI-generated placeholder objects",
        default=True,
    )

    # === Batch Generation ===
    batch_count: IntProperty(
        name="Variants",
        description="Number of variations to generate",
        default=4,
        min=2,
        max=16,
    )

    # === Mesh Cleanup ===
    mesh_cleanup_triangulate: BoolProperty(
        name="Triangulate",
        description="Convert quads to triangles during cleanup",
        default=False,
    )

    # === Templates ===
    template_category: EnumProperty(
        name="Category",
        description="Filter templates by category",
        items=TEMPLATE_CATEGORIES,
        default="ALL",
    )
    template_search: StringProperty(
        name="Search",
        description="Search templates by name",
        default="",
        maxlen=200,
    )
    template_selected_id: StringProperty(
        name="Selected",
        description="ID of currently selected template",
        default="",
    )

    # === Asset Management ===
    asset_filter_type: EnumProperty(
        name="Filter",
        description="Filter assets by type",
        items=ASSET_FILTER_TYPES,
        default="ALL",
    )
    asset_search_query: StringProperty(
        name="Search",
        description="Search assets by name or prompt",
        default="",
        maxlen=200,
    )
    asset_show_favorites_only: BoolProperty(
        name="Favorites Only",
        description="Only show favorited assets",
        default=False,
    )
    asset_list_index: IntProperty(
        name="Selected",
        description="Index of selected asset in list",
        default=0,
    )

    # === Collections ===
    history_list: CollectionProperty(type=AIHistoryItem)
    history_list_index: IntProperty(name="Selected History", default=0)
    asset_list: CollectionProperty(type=AIAssetItem)
    template_list: CollectionProperty(type=AITemplateItem)
    template_list_index: IntProperty(name="Selected Template", default=0)
    notification_list: CollectionProperty(type=AINotificationItem)
    notification_list_index: IntProperty(name="Selected Notification", default=0)

    # === Status ===
    status_message: StringProperty(
        name="Status",
        description="Current operation status message",
        default="Ready",
    )
    is_generating: BoolProperty(
        name="Generating",
        description="True when a generation task is in progress",
        default=False,
    )
    generation_progress: FloatProperty(
        name="Progress",
        description="Current generation progress (0-1)",
        default=0.0,
        min=0.0,
        max=1.0,
        precision=3,
    )
    unread_notifications: IntProperty(
        name="Unread",
        description="Number of unread notifications",
        default=0,
    )


# =============================================================================
# Registration
# =============================================================================

_CLASSES = (
    AIHistoryItem,
    AIAssetItem,
    AITemplateItem,
    AINotificationItem,
    AIToolkitProperties,
)


def register():
    """Register all property classes and add property group to Scene."""
    for cls in _CLASSES:
        try:
            bpy.utils.register_class(cls)
        except ValueError as e:
            if "already registered" in str(e):
                print(f"[AI Toolkit] {cls.__name__} already registered")
            else:
                raise

    # Register main property group on Scene
    try:
        bpy.types.Scene.ai_toolkit = PointerProperty(type=AIToolkitProperties)
    except Exception:
        pass


def unregister():
    """Unregister all property classes."""
    # Remove property group from Scene
    try:
        del bpy.types.Scene.ai_toolkit
    except AttributeError:
        pass

    # Unregister classes in reverse order
    for cls in reversed(_CLASSES):
        try:
            bpy.utils.unregister_class(cls)
        except (ValueError, RuntimeError):
            pass
