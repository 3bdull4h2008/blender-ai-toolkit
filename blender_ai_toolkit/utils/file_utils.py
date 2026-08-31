"""File utilities for AI Toolkit"""
import os
import json
import bpy


def get_addon_storage_path():
    """Get the addon's storage directory path."""
    prefs = bpy.context.preferences.addons.get("blender_ai_toolkit")
    if prefs:
        # Use Blender's config directory
        base = os.path.join(bpy.utils.user_resource('CONFIG'), "ai_toolkit")
    else:
        base = os.path.join(os.path.expanduser("~"), ".blender_ai_toolkit")

    os.makedirs(base, exist_ok=True)
    return base


def generate_model_id():
    """Generate a unique model ID."""
    import uuid
    return f"model_{uuid.uuid4().hex[:12]}"


# =============================================================================
# Asset Persistence
# =============================================================================

def get_assets_file_path():
    """Get the path to the assets JSON file."""
    return os.path.join(get_addon_storage_path(), "assets.json")


def load_assets_from_disk():
    """Load assets from disk JSON file."""
    filepath = get_assets_file_path()
    if not os.path.exists(filepath):
        return []

    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        print(f"[AI Toolkit] Failed to load assets: {e}")
        return []


def save_assets_to_disk(assets: list):
    """Save assets to disk JSON file."""
    filepath = get_assets_file_path()
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(assets, f, indent=2, ensure_ascii=False)
    except IOError as e:
        print(f"[AI Toolkit] Failed to save assets: {e}")


def add_asset_to_disk(asset_data: dict):
    """Add a single asset to the disk storage."""
    assets = load_assets_from_disk()
    assets.append(asset_data)
    save_assets_to_disk(assets)


def remove_asset_from_disk(model_id: str):
    """Remove an asset by model_id from disk storage."""
    assets = load_assets_from_disk()
    assets = [a for a in assets if a.get("model_id") != model_id]
    save_assets_to_disk(assets)


def update_asset_on_disk(model_id: str, updates: dict):
    """Update an asset's fields on disk."""
    assets = load_assets_from_disk()
    for asset in assets:
        if asset.get("model_id") == model_id:
            asset.update(updates)
            break
    save_assets_to_disk(assets)


# =============================================================================
# Template Persistence
# =============================================================================

def get_templates_file_path():
    """Get the path to the templates JSON file."""
    return os.path.join(get_addon_storage_path(), "templates.json")


def load_templates_from_disk():
    """Load custom templates from disk."""
    filepath = get_templates_file_path()
    if not os.path.exists(filepath):
        return []

    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        print(f"[AI Toolkit] Failed to load templates: {e}")
        return []


def save_templates_to_disk(templates: list):
    """Save custom templates to disk."""
    filepath = get_templates_file_path()
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(templates, f, indent=2, ensure_ascii=False)
    except IOError as e:
        print(f"[AI Toolkit] Failed to save templates: {e}")
