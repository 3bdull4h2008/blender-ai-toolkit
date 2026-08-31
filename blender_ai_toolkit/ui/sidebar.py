"""
AI Toolkit Sidebar UI - Main panel and tab system for the 3D View sidebar.
Provides a clean, organized interface for all AI generation features.
"""

import bpy
from bpy.types import Panel, Operator, UIList


# =============================================================================
# Tab Switcher Operator
# =============================================================================

class AISetTabOperator(Operator):
    """Switch between AI Toolkit tabs."""
    bl_idname = "ai.set_tab"
    bl_label = "Set Tab"
    bl_options = {'INTERNAL'}

    tab_name: bpy.props.StringProperty(
        name="Tab Name",
        description="Identifier of the tab to switch to",
        default="",
    )

    def execute(self, context):
        context.scene.ai_toolkit.active_tab = self.tab_name
        return {'FINISHED'}


# =============================================================================
# Custom UI List for Assets
# =============================================================================

class AI_ASSET_UL_list(UIList):
    """Custom UI list for asset display with status icons."""

    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index=0):
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            row = layout.row(align=True)
            # Favorite star
            row.prop(item, "favorite", icon='HEART' if item.favorite else 'BLANK1',
                     icon_only=True, emboss=False)
            # Type icon
            type_icons = {
                "model_3d": 'MESH_DATA',
                "image": 'IMAGE_DATA',
                "material": 'MATERIAL',
            }
            row.label(text="", icon=type_icons.get(item.asset_type, 'QUESTION'))
            # Name/prompt
            name_text = item.prompt[:35] + "..." if len(item.prompt) > 35 else item.prompt
            row.label(text=name_text or f"Asset {index + 1}")
            # Status
            status_icons = {
                "ready": 'CHECKMARK',
                "generating": 'TIME',
                "completed": 'FILE_TICK',
                "error": 'CANCEL',
            }
            row.label(text="", icon=status_icons.get(item.status, 'DOT'))

        elif self.layout_type in {'GRID'}:
            layout.alignment = 'CENTER'
            layout.label(text=item.name, icon='MESH_DATA')


# =============================================================================
# Main Panel
# =============================================================================

class AIToolkitPanel(Panel):
    """Main AI Toolkit panel in the 3D View sidebar."""
    bl_label = "AI Toolkit"
    bl_idname = "VIEW3D_PT_ai_toolkit"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "AI Toolkit"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        props = context.scene.ai_toolkit

        # === Tab Bar ===
        self._draw_tabs(layout, props)

        layout.separator(factor=0.3)

        # === Tab Content ===
        tab_drawers = {
            "MODEL_3D": self._draw_3d_tab,
            "IMAGE": self._draw_image_tab,
            "MATERIAL": self._draw_material_tab,
            "CHAT": self._draw_chat_tab,
            "SCENE": self._draw_scene_tab,
            "ASSETS": self._draw_assets_tab,
            "TEMPLATES": self._draw_templates_tab,
            "SETTINGS": self._draw_settings_tab,
        }

        drawer = tab_drawers.get(props.active_tab)
        if drawer:
            drawer(layout, context)

        # === Status Bar ===
        self._draw_status(layout, props)

    # =========================================================================
    # Tab Bar Drawing
    # =========================================================================

    def _draw_tabs(self, layout, props):
        """Draw the tab button bar."""
        TABS = [
            ("MODEL_3D", "3D", "MESH_DATA", "3D Generation"),
            ("IMAGE", "Img", "IMAGE_DATA", "Image Generation"),
            ("MATERIAL", "Mat", "MATERIAL", "Materials & HDRI"),
            ("CHAT", "Chat", "CONSOLE", "AI Chat"),
            ("SCENE", "Scene", "SCENE_DATA", "Scene Composer"),
            ("ASSETS", "Assets", "OUTLINER", "Asset Library"),
            ("TEMPLATES", "Temp", "BOOKMARKS", "Templates"),
            ("SETTINGS", "Set", "PREFERENCES", "Settings"),
        ]

        row = layout.row(align=True)
        row.scale_x = 0.85

        for tab_id, label, icon, tooltip in TABS:
            is_active = (props.active_tab == tab_id)
            op = row.operator(
                "ai.set_tab",
                text=label,
                icon=icon,
                depress=is_active,
                emboss=is_active,
            )
            op.tab_name = tab_id

    # =========================================================================
    # 3D Generation Tab
    # =========================================================================

    def _draw_3d_tab(self, layout, context):
        """Draw 3D model generation controls."""
        props = context.scene.ai_toolkit

        box = layout.box()
        box.label(text="Generate 3D Model", icon='MESH_DATA')

        col = box.column(align=True)
        col.prop(props, "model_3d_prompt", text="")
        col.separator(factor=0.2)
        col.prop(props, "model_3d_negative_prompt", text="Negative")

        # Options row
        row = box.row(align=True)
        row.prop(props, "model_3d_art_style", text="")
        row.prop(props, "model_3d_provider", text="")

        # Advanced options (collapsible)
        if prefs := context.preferences.addons.get("blender_ai_toolkit"):
            if prefs.preferences.auto_import:
                col = box.column(align=True)
                col.prop(props, "model_3d_seed")
                col.prop(props, "model_3d_use_preview")

        # Generate buttons
        row = box.row(align=True)
        row.scale_y = 1.4
        row.operator("ai.generate_3d", icon='RIGHTARROW_THIN')
        row.operator("ai.generate_3d_ref_image", icon='IMAGE_REFERENCE')

    # =========================================================================
    # Image Generation Tab
    # =========================================================================

    def _draw_image_tab(self, layout, context):
        """Draw image generation controls."""
        props = context.scene.ai_toolkit

        box = layout.box()
        box.label(text="Generate Image", icon='IMAGE_DATA')

        col = box.column(align=True)
        col.prop(props, "image_prompt", text="")
        col.separator(factor=0.2)
        col.prop(props, "image_negative_prompt", text="Negative")

        # Settings row
        row = box.row(align=True)
        row.prop(props, "image_size", text="")
        row.prop(props, "image_quality", text="")

        row = box.row(align=True)
        row.prop(props, "image_style_preset", text="")
        row.prop(props, "image_provider", text="")

        # Seed option
        if props.image_seed > 0:
            box.prop(props, "image_seed")

        # Generate button
        row = box.row()
        row.scale_y = 1.4
        row.operator("ai.generate_image", icon='RIGHTARROW_THIN')

    # =========================================================================
    # Material & HDRI Tab
    # =========================================================================

    def _draw_material_tab(self, layout, context):
        """Draw material/texture and HDRI generation controls."""
        props = context.scene.ai_toolkit

        # === Material Section ===
        mat_box = layout.box()
        mat_box.label(text="Generate Material", icon='MATERIAL')

        col = mat_box.column(align=True)
        col.prop(props, "material_prompt", text="")
        col.prop(props, "material_provider", text="")

        # Texture maps toggle
        row = mat_box.row(align=True)
        row.label(text="Maps:")
        row.prop(props, "material_gen_diffuse", text="Diffuse", toggle=True)
        row.prop(props, "material_gen_normal", text="Normal", toggle=True)
        row.prop(props, "material_gen_roughness", text="Rough", toggle=True)

        row = mat_box.row(align=True)
        row.prop(props, "material_gen_metallic", text="Metal", toggle=True)
        row.prop(props, "material_gen_displacement", text="Disp", toggle=True)
        row.prop(props, "material_gen_ao", text="AO", toggle=True)

        mat_row = mat_box.row()
        mat_row.scale_y = 1.2
        mat_row.operator("ai.generate_material", icon='RIGHTARROW_THIN')

        layout.separator()

        # === HDRI Section ===
        hdri_box = layout.box()
        hdri_box.label(text="Generate HDRI Environment", icon='WORLD')

        col = hdri_box.column(align=True)
        col.prop(props, "hdri_prompt", text="")
        col.prop(props, "hdri_style", text="")

        hdri_row = hdri_box.row()
        hdri_row.scale_y = 1.2
        hdri_row.operator("ai.apply_hdri", icon='WORLD')

    # =========================================================================
    # Chat Tab
    # =========================================================================

    def _draw_chat_tab(self, layout, context):
        """Draw LLM chat interface."""
        props = context.scene.ai_toolkit

        # Provider selection
        row = layout.row(align=True)
        row.prop(props, "llm_provider", text="")
        row.prop(props, "llm_temperature", text="T")

        # Response area (read-only display)
        response_box = layout.box()
        if props.llm_response:
            # Show truncated response
            response_text = props.llm_response
            if len(response_text) > 500:
                response_text = response_text[:500] + "\n... [truncated]"
            response_box.label(text="AI Response:", icon='CONSOLE')
            col = response_box.column(align=True)
            for line in response_text.split('\n')[:10]:
                col.label(text=line[:60])
        else:
            response_box.label(text="AI responses appear here", icon='INFO')

        # Input area
        input_col = layout.column(align=True)
        input_col.prop(props, "llm_prompt", text="")

        # Action buttons
        row = layout.row(align=True)
        row.scale_y = 1.2
        row.operator("ai.chat", icon='RIGHTARROW_THIN')
        row.operator("ai.chat_clear_history", icon='TRASH')

        # Options
        row = layout.row(align=True)
        row.prop(props, "llm_execute_code", text="Auto-Exec Code")
        row.operator("ai.chat_execute_code", icon='SCRIPT', text="Run Code")

    # =========================================================================
    # Scene Composer Tab
    # =========================================================================

    def _draw_scene_tab(self, layout, context):
        """Draw scene composition controls."""
        props = context.scene.ai_toolkit

        box = layout.box()
        box.label(text="Compose Scene from Text", icon='SCENE_DATA')

        col = box.column(align=True)
        col.prop(props, "scene_prompt", text="")
        col.prop(props, "scene_include_ai_objects")

        # Action buttons
        row = box.row(align=True)
        row.scale_y = 1.3
        row.operator("ai.compose_scene", icon='RIGHTARROW_THIN', text="Compose Scene")

        layout.separator()

        # Generate AI objects section
        gen_box = layout.box()
        gen_box.label(text="Generate AI Objects", icon='MESH_DATA')
        gen_box.label(text="Generate 3D models for all", icon='INFO')
        gen_box.label(text="AI placeholder objects in scene", icon='INFO')

        gen_row = gen_box.row()
        gen_row.scale_y = 1.2
        gen_row.operator("ai.generate_scene_ai_objects", icon='RIGHTARROW_THIN')

    # =========================================================================
    # Assets Tab
    # =========================================================================

    def _draw_assets_tab(self, layout, context):
        """Draw asset library browser."""
        props = context.scene.ai_toolkit

        # Filter controls
        filter_row = layout.row(align=True)
        filter_row.prop(props, "asset_filter_type", text="")
        filter_row.prop(props, "asset_show_favorites_only", text="", icon='HEART', toggle=True)

        search_row = layout.row(align=True)
        search_row.prop(props, "asset_search_query", text="", icon='VIEWZOOM')

        # Asset list
        layout.template_list(
            "AI_ASSET_UL_list", "",
            props, "asset_list",
            props, "asset_list_index",
            rows=5,
        )

        # Action buttons
        row = layout.row(align=True)
        row.operator("ai.asset_import", icon='APPEND_BLEND')
        row.operator("ai.asset_delete", icon='TRASH')
        row.operator("ai.asset_duplicate", icon='DUPLICATE')
        row.operator("ai.asset_toggle_favorite", icon='HEART')

        row = layout.row(align=True)
        row.operator("ai.asset_refresh", icon='FILE_PARENT')
        row.operator("ai.cancel_generation", icon='CANCEL')

    # =========================================================================
    # Templates Tab
    # =========================================================================

    def _draw_templates_tab(self, layout, context):
        """Draw prompt template library."""
        props = context.scene.ai_toolkit

        # Category filter & search
        row = layout.row(align=True)
        row.prop(props, "template_category", text="")
        row.prop(props, "template_search", text="", icon='VIEWZOOM')

        # Template list
        layout.template_list(
            "UI_UL_LIST", "",
            props, "template_list",
            props, "template_list_index",
            rows=6,
        )

        # Template actions
        row = layout.row(align=True)
        row.scale_y = 1.2
        row.operator("ai.apply_template", icon='CHECKMARK', text="Apply")
        row.operator("ai.save_template", icon='ADD', text="Save Current")
        row.operator("ai.refresh_templates", icon='FILE_PARENT', text="Refresh")

        # Info text
        info_box = layout.box()
        info_box.label(text="Tip: Select a template and click Apply", icon='INFO')
        info_box.label(text="to fill in the prompt fields.", icon='BLANK1')

    # =========================================================================
    # Settings Tab
    # =========================================================================

    def _draw_settings_tab(self, layout, context):
        """Draw settings and configuration help."""
        # Quick settings
        box = layout.box()
        box.label(text="Quick Settings", icon='SETTINGS')

        prefs = context.preferences.addons.get("blender_ai_toolkit")
        if prefs:
            p = prefs.preferences
            col = box.column(align=True)
            col.prop(p, "auto_import")
            col.prop(p, "show_notifications")
            col.prop(p, "debug_mode")
            col.prop(p, "max_concurrent_tasks")

        # API Keys instructions
        layout.separator()
        api_box = layout.box()
        api_box.label(text="API Configuration", icon='PREFERENCES')

        col = api_box.column(align=True)
        col.alignment = 'CENTER'
        col.label(text="To configure API keys:", icon='INFO')
        col.separator()
        col.label(text="1. Edit → Preferences → Add-ons", icon='RIGHTARROW')
        col.label(text="2. Find 'AI Toolkit'", icon='RIGHTARROW')
        col.label(text="3. Expand to set API keys", icon='RIGHTARROW')

        # Version info
        layout.separator()
        ver_box = layout.box()
        ver_box.label(text="AI Toolkit v2.1.1", icon='INFO')
        ver_box.label(text="Blender 4.2+ Compatible", icon='BLANK1')

    # =========================================================================
    # Status Display
    # =========================================================================

    def _draw_status(self, layout, props):
        """Draw status message and progress bar at bottom of panel."""
        # Progress bar during generation
        if props.is_generating:
            box = layout.box()
            box.label(text=props.status_message or "Processing...", icon='TIME')
            box.prop(props, "generation_progress", slider=True, text="Progress")

            # Cancel button
            row = box.row()
            row.operator("ai.cancel_generation", icon='CANCEL', text="Cancel")
        elif props.status_message and props.status_message != "Ready":
            # Show last status briefly
            row = layout.row()
            row.label(text=props.status_message, icon='INFO')


# =============================================================================
# Registration
# =============================================================================

classes = (
    AISetTabOperator,
    AI_ASSET_UL_list,
    AIToolkitPanel,
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
