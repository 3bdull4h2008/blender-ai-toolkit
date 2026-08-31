"""
Asset Management Operators - Handle import, delete, duplicate, and management
of AI-generated assets (3D models, images, materials) with disk persistence.
"""

import os
import bpy
from bpy.types import Operator


class AIAssetImportOperator(Operator):
    """Import a selected asset into the current scene."""
    bl_idname = "ai.asset_import"
    bl_label = "Import Asset"
    bl_description = "Import selected asset into the scene"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        props = context.scene.ai_toolkit

        if not props.asset_list:
            self.report({'WARNING'}, "No assets available to import")
            return {'CANCELLED'}

        idx = props.asset_list_index
        if idx < 0 or idx >= len(props.asset_list):
            self.report({'WARNING'}, "Please select an asset")
            return {'CANCELLED'}

        asset = props.asset_list[idx]

        try:
            asset_type = asset.asset_type
            filepath = asset.file_path if hasattr(asset, 'file_path') else ""

            if asset_type == "model_3d" and filepath and os.path.exists(filepath):
                # Import GLB/GLTF
                bpy.ops.import_scene.gltf(filepath=filepath)
                obj = bpy.context.active_object
                if obj:
                    self.report({'INFO'}, f"Imported: {obj.name}")

            elif asset_type == "image" and filepath and os.path.exists(filepath):
                # Import as reference image
                bpy.ops.image.open(filepath=filepath)
                self.report({'INFO'}, f"Imported image: {os.path.basename(filepath)}")

            elif asset_type == "material":
                # Create material from stored data
                mat_name = f"AI_Mat_{asset.model_id[:8]}"
                mat = bpy.data.materials.new(name=mat_name)
                mat.use_nodes = True
                if context.selected_objects:
                    for obj in context.selected_objects:
                        if obj.type == 'MESH':
                            obj.data.materials.append(mat)
                self.report({'INFO'}, f"Created material: {mat_name}")

            else:
                self.report({'INFO'}, f"Asset ready: {asset.prompt[:30]}")

            return {'FINISHED'}

        except Exception as e:
            self.report({'ERROR'}, f"Import failed: {str(e)}")
            return {'CANCELLED'}


class AIAssetDeleteOperator(Operator):
    """Delete a selected asset from the library."""
    bl_idname = "ai.asset_delete"
    bl_label = "Delete Asset"
    bl_description = "Remove selected asset from the library"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        props = context.scene.ai_toolkit

        if not props.asset_list:
            self.report({'WARNING'}, "No assets to delete")
            return {'CANCELLED'}

        idx = props.asset_list_index
        if idx < 0 or idx >= len(props.asset_list):
            self.report({'WARNING'}, "Select an asset to delete")
            return {'CANCELLED'}

        asset = props.asset_list[idx]
        asset_name = asset.prompt[:30]
        model_id = asset.model_id

        # Remove from collection
        props.asset_list.remove(idx)

        # Adjust index if needed
        if len(props.asset_list) == 0:
            props.asset_list_index = 0
        elif idx >= len(props.asset_list):
            props.asset_list_index = len(props.asset_list) - 1

        # Remove from disk
        from ...utils.file_utils import remove_asset_from_disk
        remove_asset_from_disk(model_id)

        self.report({'INFO'}, f"Deleted: {asset_name}")
        return {'FINISHED'}


class AIAssetDuplicateOperator(Operator):
    """Duplicate a selected asset."""
    bl_idname = "ai.asset_duplicate"
    bl_label = "Duplicate Asset"
    bl_description = "Create a copy of the selected asset"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        props = context.scene.ai_toolkit

        if not props.asset_list:
            self.report({'WARNING'}, "No assets to duplicate")
            return {'CANCELLED'}

        idx = props.asset_list_index
        if idx < 0 or idx >= len(props.asset_list):
            self.report({'WARNING'}, "Select an asset to duplicate")
            return {'CANCELLED'}

        source = props.asset_list[idx]

        # Create duplicate
        new_asset = props.asset_list.add()
        new_asset.model_id = f"{source.model_id}_copy"
        new_asset.asset_type = source.asset_type
        new_asset.prompt = f"{source.prompt} (copy)"
        new_asset.provider_id = source.provider_id
        new_asset.status = "ready"
        new_asset.favorite = False

        # Select the new item
        props.asset_list_index = len(props.asset_list) - 1

        # Save to disk
        from ...utils.file_utils import add_asset_to_disk
        add_asset_to_disk({
            "model_id": new_asset.model_id,
            "asset_type": new_asset.asset_type,
            "prompt": new_asset.prompt,
            "provider_id": new_asset.provider_id,
            "status": "ready",
            "favorite": False,
        })

        self.report({'INFO'}, "Asset duplicated")
        return {'FINISHED'}


class AIAssetToggleFavoriteOperator(Operator):
    """Toggle favorite status of selected asset."""
    bl_idname = "ai.asset_toggle_favorite"
    bl_label = "Toggle Favorite"
    bl_description = "Add or remove asset from favorites"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        props = context.scene.ai_toolkit

        if not props.asset_list:
            self.report({'WARNING'}, "No assets available")
            return {'CANCELLED'}

        idx = props.asset_list_index
        if idx < 0 or idx >= len(props.asset_list):
            self.report({'WARNING'}, "Select an asset first")
            return {'CANCELLED'}

        asset = props.asset_list[idx]
        asset.favorite = not asset.favorite

        # Update on disk
        from ...utils.file_utils import update_asset_on_disk
        update_asset_on_disk(asset.model_id, {"favorite": asset.favorite})

        status = "favorited" if asset.favorite else "unfavorited"
        self.report({'INFO'}, f"Asset {status}")
        return {'FINISHED'}


class AIAssetRefreshOperator(Operator):
    """Refresh the asset list from storage."""
    bl_idname = "ai.asset_refresh"
    bl_label = "Refresh Assets"
    bl_description = "Reload asset list from disk"
    bl_options = {'REGISTER'}

    def execute(self, context):
        props = context.scene.ai_toolkit

        from ...utils.file_utils import load_assets_from_disk
        disk_assets = load_assets_from_disk()

        # Clear and rebuild collection
        props.asset_list.clear()
        for asset_data in disk_assets:
            item = props.asset_list.add()
            item.model_id = asset_data.get("model_id", "")
            item.asset_type = asset_data.get("asset_type", "model_3d")
            item.prompt = asset_data.get("prompt", "")
            item.provider_id = asset_data.get("provider_id", "")
            item.status = asset_data.get("status", "ready")
            item.favorite = asset_data.get("favorite", False)

        self.report({'INFO'}, f"Loaded {len(disk_assets)} assets")
        return {'FINISHED'}


class AICancelGenerationOperator(Operator):
    """Cancel the current generation task."""
    bl_idname = "ai.cancel_generation"
    bl_label = "Cancel Generation"
    bl_description = "Cancel the current AI generation task"
    bl_options = {'REGISTER'}

    def execute(self, context):
        props = context.scene.ai_toolkit

        if not props.is_generating:
            self.report({'INFO'}, "No active generation to cancel")
            return {'CANCELLED'}

        # Cancel via task queue
        from ...core.task_queue import get_task_queue
        queue = get_task_queue()

        # Try to cancel any pending tasks
        with queue._lock:
            for task_id, task in list(queue._tasks.items()):
                if task.status.value == "pending":
                    task.status = task.status.CANCELLED

        props.is_generating = False
        props.generation_progress = 0.0
        props.status_message = "Cancelled"

        self.report({'INFO'}, "Generation cancelled")
        return {'FINISHED'}


# =============================================================================
# Registration
# =============================================================================

classes = (
    AIAssetImportOperator,
    AIAssetDeleteOperator,
    AIAssetDuplicateOperator,
    AIAssetToggleFavoriteOperator,
    AIAssetRefreshOperator,
    AICancelGenerationOperator,
)


def register():
    for cls in classes:
        try:
            bpy.utils.register_class(cls)
        except ValueError as e:
            if "already registered" in str(e):
                print(f"[AI Toolkit] {cls.__name__} already registered")


def unregister():
    for cls in reversed(classes):
        try:
            bpy.utils.unregister_class(cls)
        except (ValueError, RuntimeError):
            pass
