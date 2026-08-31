"""Preset system with 30+ built-in presets for various generation tasks."""
from typing import Dict, List, Optional


class GenerationPreset:
    """A generation preset with all parameters."""

    def __init__(self, preset_id: str, name: str, category: str,
                 description: str, params: Dict):
        self.preset_id = preset_id
        self.name = name
        self.category = category
        self.description = description
        self.params = params

    def to_dict(self) -> Dict:
        return {
            "preset_id": self.preset_id,
            "name": self.name,
            "category": self.category,
            "description": self.description,
            "params": self.params,
        }


# =============================================================================
# 3D Model Presets
# =============================================================================

MODEL_3D_PRESETS = [
    GenerationPreset(
        "char_realistic", "Realistic Character", "character",
        "Photorealistic human character with PBR materials",
        {"art_style": "realistic", "negative_prompt": "cartoon, anime, low poly, deformed"},
    ),
    GenerationPreset(
        "char_cartoon", "Cartoon Character", "character",
        "Stylized cartoon character",
        {"art_style": "cartoon", "negative_prompt": "realistic, photographic, detailed"},
    ),
    GenerationPreset(
        "char_lowpoly", "Low Poly Character", "character",
        "Low polygon game-ready character",
        {"art_style": "low-poly", "negative_prompt": "high poly, detailed, smooth"},
    ),
    GenerationPreset(
        "char_anime", "Anime Character", "character",
        "Anime/manga style character",
        {"art_style": "anime", "negative_prompt": "realistic, 3d render"},
    ),
    GenerationPreset(
        "env_forest", "Forest Environment", "environment",
        "Lush forest with trees, rocks, foliage",
        {"art_style": "realistic", "negative_prompt": "indoor, urban, sci-fi"},
    ),
    GenerationPreset(
        "env_city", "City Environment", "environment",
        "Urban cityscape with buildings and streets",
        {"art_style": "realistic", "negative_prompt": "rural, nature, fantasy"},
    ),
    GenerationPreset(
        "env_dungeon", "Dungeon Environment", "environment",
        "Dark fantasy dungeon with torches and stone",
        {"art_style": "realistic", "negative_prompt": "bright, modern, clean"},
    ),
    GenerationPreset(
        "env_space", "Space Environment", "environment",
        "Sci-fi space station or alien planet",
        {"art_style": "realistic", "negative_prompt": "earth, nature, medieval"},
    ),
    GenerationPreset(
        "prop_weapon_sword", "Fantasy Sword", "weapon",
        "Ornate fantasy sword with intricate details",
        {"art_style": "fantasy", "negative_prompt": "modern, gun, sci-fi"},
    ),
    GenerationPreset(
        "prop_weapon_gun", "Sci-Fi Gun", "weapon",
        "Futuristic energy weapon",
        {"art_style": "realistic", "negative_prompt": "medieval, fantasy, knife"},
    ),
    GenerationPreset(
        "prop_potion", "Magic Potion", "prop",
        "Magical potion bottle with glowing liquid",
        {"art_style": "fantasy", "negative_prompt": "realistic, modern"},
    ),
    GenerationPreset(
        "prop_treasure", "Treasure Chest", "prop",
        "Ornate treasure chest with gold details",
        {"art_style": "fantasy", "negative_prompt": "modern, sci-fi"},
    ),
    GenerationPreset(
        "veh_car", "Sports Car", "vehicle",
        "Sleek aerodynamic sports car",
        {"art_style": "realistic", "negative_prompt": "cartoon, toy, old"},
    ),
    GenerationPreset(
        "veh_spaceship", "Spaceship", "vehicle",
        "Futuristic spacecraft",
        {"art_style": "realistic", "negative_prompt": "car, ground vehicle"},
    ),
    GenerationPreset(
        "veh_cartoon", "Cartoon Vehicle", "vehicle",
        "Stylized cartoon vehicle",
        {"art_style": "cartoon", "negative_prompt": "realistic, photographic"},
    ),
    GenerationPreset(
        "arch_house", "Modern House", "architecture",
        "Contemporary residential architecture",
        {"art_style": "realistic", "negative_prompt": "medieval, fantasy, ruined"},
    ),
    GenerationPreset(
        "arch_castle", "Fantasy Castle", "architecture",
        "Medieval fantasy castle with towers",
        {"art_style": "fantasy", "negative_prompt": "modern, sci-fi"},
    ),
    GenerationPreset(
        "arch_temple", "Ancient Temple", "architecture",
        "Ancient temple ruins with weathered stone",
        {"art_style": "realistic", "negative_prompt": "modern, clean, new"},
    ),
    GenerationPreset(
        "nature_tree", "Realistic Tree", "nature",
        "Detailed realistic tree with bark and leaves",
        {"art_style": "realistic", "negative_prompt": "cartoon, low poly"},
    ),
    GenerationPreset(
        "nature_rock", "Realistic Rock", "nature",
        "Natural rock formation with textures",
        {"art_style": "realistic", "negative_prompt": "cartoon, geometric"},
    ),
    GenerationPreset(
        "furniture_chair", "Modern Chair", "furniture",
        "Contemporary designer chair",
        {"art_style": "realistic", "negative_prompt": "medieval, fantasy, broken"},
    ),
    GenerationPreset(
        "furniture_table", "Wooden Table", "furniture",
        "Rustic wooden dining table",
        {"art_style": "realistic", "negative_prompt": "metal, glass, modern"},
    ),
    GenerationPreset(
        "abstract_crystal", "Abstract Crystal", "abstract",
        "Geometric crystal formation",
        {"art_style": "realistic", "negative_prompt": "organic, natural"},
    ),
    GenerationPreset(
        "abstract_portal", "Magic Portal", "abstract",
        "Glowing magical portal with particles",
        {"art_style": "fantasy", "negative_prompt": "realistic, modern"},
    ),
]

# =============================================================================
# Image Presets
# =============================================================================

IMAGE_PRESETS = [
    GenerationPreset(
        "img_portrait", "Portrait Photography", "portrait",
        "Professional portrait with studio lighting",
        {"style": "photographic", "quality": "hd"},
    ),
    GenerationPreset(
        "img_landscape", "Landscape Photography", "landscape",
        "Scenic landscape with dramatic lighting",
        {"style": "photographic", "quality": "hd"},
    ),
    GenerationPreset(
        "img_concept_art", "Concept Art", "concept",
        "Digital concept art for games/film",
        {"style": "digital-art", "quality": "hd"},
    ),
    GenerationPreset(
        "img_anime", "Anime Illustration", "anime",
        "Japanese anime style illustration",
        {"style": "anime", "quality": "standard"},
    ),
    GenerationPreset(
        "img_3d_render", "3D Render", "3d",
        "Photorealistic 3D render",
        {"style": "3d-model", "quality": "hd"},
    ),
    GenerationPreset(
        "img_pixel_art", "Pixel Art", "pixel",
        "Retro pixel art style",
        {"style": "pixel-art", "quality": "standard"},
    ),
    GenerationPreset(
        "img_fantasy", "Fantasy Art", "fantasy",
        "Epic fantasy illustration",
        {"style": "fantasy-art", "quality": "hd"},
    ),
    GenerationPreset(
        "img_product", "Product Photography", "product",
        "Clean product shot on white background",
        {"style": "photographic", "quality": "hd"},
    ),
]

# =============================================================================
# Material Presets
# =============================================================================

MATERIAL_PRESETS = [
    GenerationPreset(
        "mat_wood_oak", "Oak Wood", "wood",
        "Natural oak wood grain texture",
        {"seamless": True, "negative_prompt": "plastic, metal"},
    ),
    GenerationPreset(
        "mat_wood_dark", "Dark Walnut", "wood",
        "Dark walnut wood with rich grain",
        {"seamless": True, "negative_prompt": "light, pine"},
    ),
    GenerationPreset(
        "mat_metal_steel", "Brushed Steel", "metal",
        "Brushed stainless steel surface",
        {"seamless": True, "negative_prompt": "rust, gold, copper"},
    ),
    GenerationPreset(
        "mat_metal_gold", "Gold", "metal",
        "Polished gold metal surface",
        {"seamless": True, "negative_prompt": "silver, steel, rust"},
    ),
    GenerationPreset(
        "mat_stone_marble", "Marble", "stone",
        "White marble with gray veins",
        {"seamless": True, "negative_prompt": "wood, metal"},
    ),
    GenerationPreset(
        "mat_stone_granite", "Granite", "stone",
        "Polished granite countertop",
        {"seamless": True, "negative_prompt": "wood, plastic"},
    ),
    GenerationPreset(
        "mat_brick_red", "Red Brick", "brick",
        "Traditional red brick wall",
        {"seamless": True, "negative_prompt": "wood, metal"},
    ),
    GenerationPreset(
        "mat_concrete", "Concrete", "concrete",
        "Smooth concrete surface",
        {"seamless": True, "negative_prompt": "wood, metal, brick"},
    ),
    GenerationPreset(
        "mat_fabric_cotton", "Cotton Fabric", "fabric",
        "Woven cotton fabric texture",
        {"seamless": True, "negative_prompt": "hard, shiny"},
    ),
    GenerationPreset(
        "mat_fabric_leather", "Leather", "fabric",
        "Aged leather surface",
        {"seamless": True, "negative_prompt": "fabric, cotton"},
    ),
    GenerationPreset(
        "mat_glass_clear", "Clear Glass", "glass",
        "Transparent clear glass",
        {"seamless": True, "negative_prompt": "opaque, colored"},
    ),
    GenerationPreset(
        "mat_plastic_glossy", "Glossy Plastic", "plastic",
        "Shiny colored plastic surface",
        {"seamless": True, "negative_prompt": "matte, rough"},
    ),
]

# =============================================================================
# HDRI Presets
# =============================================================================

HDRI_PRESETS = [
    GenerationPreset(
        "hdri_studio", "Studio Lighting", "studio",
        "Professional studio soft lighting",
        {"style": "photographic", "negative_prompt": "outdoor, harsh"},
    ),
    GenerationPreset(
        "hdri_sunset", "Golden Sunset", "outdoor",
        "Warm golden hour sunset lighting",
        {"style": "cinematic", "negative_prompt": "midday, noon"},
    ),
    GenerationPreset(
        "hdri_night", "Night Sky", "outdoor",
        "Dark night with moonlight",
        {"style": "photographic", "negative_prompt": "day, bright, sun"},
    ),
    GenerationPreset(
        "hdri_forest", "Forest Environment", "outdoor",
        "Dappled forest lighting with trees",
        {"style": "photographic", "negative_prompt": "indoor, studio"},
    ),
    GenerationPreset(
        "hdri_overcast", "Overcast Day", "outdoor",
        "Soft overcast cloud lighting",
        {"style": "photographic", "negative_prompt": "sunny, harsh shadows"},
    ),
    GenerationPreset(
        "hdri_warehouse", "Warehouse Interior", "indoor",
        "Large warehouse with industrial lighting",
        {"style": "photographic", "negative_prompt": "outdoor, nature"},
    ),
    GenerationPreset(
        "hdri_fantasy", "Fantasy Atmosphere", "fantasy",
        "Magical glowing fantasy environment",
        {"style": "fantasy-art", "negative_prompt": "realistic, modern"},
    ),
]

# All presets combined
ALL_PRESETS = MODEL_3D_PRESETS + IMAGE_PRESETS + MATERIAL_PRESETS + HDRI_PRESETS


def get_preset(preset_id: str) -> Optional[GenerationPreset]:
    """Get a preset by ID."""
    for preset in ALL_PRESETS:
        if preset.preset_id == preset_id:
            return preset
    return None


def get_presets_by_category(category: str) -> List[GenerationPreset]:
    """Get all presets in a category."""
    return [p for p in ALL_PRESETS if p.category == category]


def get_presets_by_type(preset_type: str) -> List[GenerationPreset]:
    """Get presets by type (model_3d, image, material, hdri)."""
    type_map = {
        "model_3d": MODEL_3D_PRESETS,
        "image": IMAGE_PRESETS,
        "material": MATERIAL_PRESETS,
        "hdri": HDRI_PRESETS,
    }
    return type_map.get(preset_type, [])


def get_all_categories() -> List[str]:
    """Get all unique preset categories."""
    return list(set(p.category for p in ALL_PRESETS))


def get_preset_diff(preset_a: GenerationPreset, preset_b: GenerationPreset) -> Dict:
    """Get the differences between two presets."""
    diff = {}
    all_keys = set(preset_a.params.keys()) | set(preset_b.params.keys())
    for key in all_keys:
        val_a = preset_a.params.get(key)
        val_b = preset_b.params.get(key)
        if val_a != val_b:
            diff[key] = {"from": val_a, "to": val_b}
    return diff
