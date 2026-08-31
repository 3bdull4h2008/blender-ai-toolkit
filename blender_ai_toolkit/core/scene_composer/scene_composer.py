"""
Scene Composer - Generate entire Blender scenes from text descriptions.
Uses LLM to parse scene descriptions and create object layouts with AI generation.
"""

import bpy
import json
import math
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List, Tuple
from enum import Enum


class ObjectType(Enum):
    PRIMITIVE = "primitive"       # Blender built-in primitives
    AI_GENERATED = "ai_generated" # Generated via AI API
    LIGHT = "light"               # Light objects
    CAMERA = "camera"             # Camera objects
    EMPTY = "empty"               # Empty placeholders


@dataclass
class SceneObject:
    """Describes a single object in a composed scene."""
    name: str
    object_type: ObjectType = ObjectType.PRIMITIVE
    primitive_type: str = "cube"  # cube, sphere, cylinder, cone, torus, plane, monkey
    ai_prompt: str = ""           # If AI-generated, the prompt to use
    location: Tuple[float, float, float] = (0.0, 0.0, 0.0)
    rotation: Tuple[float, float, float] = (0.0, 0.0, 0.0)
    scale: Tuple[float, float, float] = (1.0, 1.0, 1.0)
    color: Tuple[float, float, float, float] = (0.8, 0.8, 0.8, 1.0)
    metalness: float = 0.0
    roughness: float = 0.5
    emission_color: Optional[Tuple[float, float, float, float]] = None
    parent: str = ""  # Name of parent object


@dataclass
class SceneDescription:
    """A complete scene description parsed from text."""
    name: str = "AI Generated Scene"
    objects: List[SceneObject] = field(default_factory=list)
    background_color: Tuple[float, float, float] = (0.05, 0.05, 0.05)
    ambient_light: float = 0.2
    fog_enabled: bool = False
    fog_density: float = 0.01
    camera_location: Tuple[float, float, float] = (10.0, -10.0, 8.0)
    camera_target: Tuple[float, float, float] = (0.0, 0.0, 0.0)


class SceneComposer:
    """
    Composes Blender scenes from text descriptions.
    Uses LLM to parse natural language into structured scene layouts,
    then creates the scene using primitives and AI-generated models.
    """

    def __init__(self):
        self._last_scene: Optional[SceneDescription] = None

    def compose_from_text(self, text: str, llm_response: str = "") -> SceneDescription:
        """
        Parse a scene description from text.
        If llm_response is provided, parse it as JSON.
        Otherwise, create a basic scene from keyword analysis.
        """
        scene = SceneDescription(name="AI Scene")

        # Try to parse LLM JSON response
        if llm_response:
            try:
                # Extract JSON from code blocks
                import re
                json_match = re.search(r'```json\s*\n(.*?)```', llm_response, re.DOTALL)
                if json_match:
                    json_str = json_match.group(1)
                else:
                    json_str = llm_response

                data = json.loads(json_str)
                return self._parse_json_scene(data)
            except (json.JSONDecodeError, ValueError):
                pass

        # Fallback: keyword-based scene creation
        return self._create_from_keywords(text)

    def _parse_json_scene(self, data: Dict) -> SceneDescription:
        """Parse a JSON scene description into a SceneDescription."""
        scene = SceneDescription(
            name=data.get("name", "AI Scene"),
            background_color=tuple(data.get("background_color", [0.05, 0.05, 0.05])),
            ambient_light=data.get("ambient_light", 0.2),
            fog_enabled=data.get("fog_enabled", False),
            fog_density=data.get("fog_density", 0.01),
            camera_location=tuple(data.get("camera_location", [10, -10, 8])),
            camera_target=tuple(data.get("camera_target", [0, 0, 0])),
        )

        for obj_data in data.get("objects", []):
            obj = SceneObject(
                name=obj_data.get("name", "Object"),
                object_type=ObjectType(obj_data.get("type", "primitive")),
                primitive_type=obj_data.get("primitive", "cube"),
                ai_prompt=obj_data.get("ai_prompt", ""),
                location=tuple(obj_data.get("location", [0, 0, 0])),
                rotation=tuple(obj_data.get("rotation", [0, 0, 0])),
                scale=tuple(obj_data.get("scale", [1, 1, 1])),
                color=tuple(obj_data.get("color", [0.8, 0.8, 0.8, 1.0])),
                metalness=obj_data.get("metalness", 0.0),
                roughness=obj_data.get("roughness", 0.5),
                emission_color=tuple(obj_data.get("emission_color")) if obj_data.get("emission_color") else None,
                parent=obj_data.get("parent", ""),
            )
            scene.objects.append(obj)

        return scene

    def _create_from_keywords(self, text: str) -> SceneDescription:
        """Create a basic scene from keyword analysis of text."""
        scene = SceneDescription(name=f"Scene: {text[:40]}")
        text_lower = text.lower()

        # Always add a ground plane
        scene.objects.append(SceneObject(
            name="Ground",
            primitive_type="plane",
            location=(0, 0, 0),
            scale=(10, 10, 1),
            color=(0.3, 0.35, 0.3, 1.0),
            roughness=0.9,
        ))

        # Detect common elements
        if any(w in text_lower for w in ["room", "interior", "indoor", "house"]):
            self._add_room(scene)

        if any(w in text_lower for w in ["forest", "tree", "nature", "garden"]):
            self._add_trees(scene)

        if any(w in text_lower for w in ["city", "building", "urban", "skyscraper"]):
            self._add_buildings(scene)

        if any(w in text_lower for w in ["table", "desk", "furniture"]):
            self._add_table(scene)

        if any(w in text_lower for w in ["light", "lamp", "glow", "neon"]):
            self._add_lights(scene)

        # Add main AI-generated object at center
        scene.objects.append(SceneObject(
            name="Main Subject",
            object_type=ObjectType.AI_GENERATED,
            ai_prompt=text,
            location=(0, 0, 1),
        ))

        # Add camera and key light
        scene.objects.append(SceneObject(
            name="Camera",
            object_type=ObjectType.CAMERA,
            location=(8, -8, 6),
        ))
        scene.objects.append(SceneObject(
            name="Key Light",
            object_type=ObjectType.LIGHT,
            location=(5, -3, 8),
            color=(1.0, 0.95, 0.9, 1.0),
            emission_color=(1.0, 0.95, 0.9, 1.0),
        ))

        return scene

    def _add_room(self, scene: SceneDescription):
        """Add room elements."""
        scene.objects.append(SceneObject(
            name="Floor", primitive_type="plane",
            location=(0, 0, 0), scale=(5, 5, 1),
            color=(0.6, 0.5, 0.4, 1.0), roughness=0.7,
        ))
        scene.objects.append(SceneObject(
            name="Back Wall", primitive_type="plane",
            location=(0, -5, 2.5), rotation=(1.5708, 0, 0), scale=(5, 5, 1),
            color=(0.85, 0.85, 0.8, 1.0), roughness=0.8,
        ))

    def _add_trees(self, scene: SceneDescription):
        """Add simple tree representations."""
        for i in range(5):
            x = (i - 2) * 3 + (i % 2)
            y = (i % 3 - 1) * 2
            scene.objects.append(SceneObject(
                name=f"Tree_{i+1}", object_type=ObjectType.AI_GENERATED,
                ai_prompt="realistic tree, detailed bark and leaves",
                location=(x, y, 0), scale=(0.8, 0.8, 0.8),
            ))

    def _add_buildings(self, scene: SceneDescription):
        """Add building representations."""
        for i in range(4):
            x = (i - 1.5) * 4
            height = 3 + (i % 3) * 2
            scene.objects.append(SceneObject(
                name=f"Building_{i+1}", primitive_type="cube",
                location=(x, -8, height / 2), scale=(1.5, 1.5, height / 2),
                color=(0.5, 0.5, 0.55, 1.0), roughness=0.6, metalness=0.3,
            ))

    def _add_table(self, scene: SceneDescription):
        """Add a table."""
        scene.objects.append(SceneObject(
            name="Table Top", primitive_type="cube",
            location=(0, 0, 0.9), scale=(1.5, 1.0, 0.05),
            color=(0.55, 0.35, 0.2, 1.0), roughness=0.4,
        ))

    def _add_lights(self, scene: SceneDescription):
        """Add decorative lights."""
        colors = [(1, 0.3, 0.3), (0.3, 1, 0.3), (0.3, 0.3, 1), (1, 1, 0.3)]
        for i, color in enumerate(colors):
            angle = i * math.pi / 2
            x, y = math.cos(angle) * 4, math.sin(angle) * 4
            scene.objects.append(SceneObject(
                name=f"Light_{i+1}", object_type=ObjectType.LIGHT,
                location=(x, y, 3),
                emission_color=(*color, 1.0),
            ))

    def build_scene(self, description: SceneDescription, collection_name: str = "") -> bpy.types.Collection:
        """
        Build a Blender scene from a SceneDescription.
        Returns the collection containing all created objects.
        """
        col_name = collection_name or description.name.replace(" ", "_")
        collection = bpy.data.collections.get(col_name)
        if not collection:
            collection = bpy.data.collections.new(col_name)
            bpy.context.scene.collection.children.link(collection)

        # Set world background
        try:
            world = bpy.context.scene.world
            if not world:
                world = bpy.data.worlds.new("AI World")
                bpy.context.scene.world = world
            if world.use_nodes:
                bg_node = world.node_tree.nodes.get("Background")
                if bg_node:
                    bg_node.inputs[0].default_value = (*description.background_color, 1.0)
                    bg_node.inputs[1].default_value = description.ambient_light
        except Exception:
            pass

        # Create objects
        created_objects = {}
        for obj_desc in description.objects:
            obj = self._create_object(obj_desc, collection)
            if obj:
                created_objects[obj_desc.name] = obj

        # Set up parenting
        for obj_desc in description.objects:
            if obj_desc.parent and obj_desc.name in created_objects and obj_desc.parent in created_objects:
                created_objects[obj_desc.name].parent = created_objects[obj_desc.parent]

        # Set camera
        try:
            camera = created_objects.get("Camera")
            if camera and camera.type == 'CAMERA':
                bpy.context.scene.camera = camera
        except Exception:
            pass

        self._last_scene = description
        return collection

    def _create_object(self, obj_desc: SceneObject, collection: bpy.types.Collection) -> Optional[bpy.types.Object]:
        """Create a single Blender object from a SceneObject description."""
        obj = None

        if obj_desc.object_type == ObjectType.PRIMITIVE:
            obj = self._create_primitive(obj_desc)

        elif obj_desc.object_type == ObjectType.LIGHT:
            obj = self._create_light(obj_desc)

        elif obj_desc.object_type == ObjectType.CAMERA:
            obj = self._create_camera(obj_desc)

        elif obj_desc.object_type == ObjectType.EMPTY:
            bpy.ops.object.empty_add(location=obj_desc.location)
            obj = bpy.context.active_object
            obj.name = obj_desc.name

        elif obj_desc.object_type == ObjectType.AI_GENERATED:
            # Create a placeholder empty with AI prompt metadata
            bpy.ops.object.empty_add(type='CUBE', location=obj_desc.location)
            obj = bpy.context.active_object
            obj.name = f"[AI] {obj_desc.name}"
            obj.scale = obj_desc.scale
            obj["ai_prompt"] = obj_desc.ai_prompt
            obj["ai_generate"] = True
            obj.empty_display_size = 0.5

        if obj and obj_desc.object_type != ObjectType.AI_GENERATED:
            # Set transform
            obj.location = obj_desc.location
            obj.rotation_euler = obj_desc.rotation
            if obj_desc.object_type != ObjectType.PRIMITIVE:
                obj.scale = obj_desc.scale
            else:
                obj.scale = obj_desc.scale

            # Apply material
            if obj_desc.object_type not in (ObjectType.CAMERA, ObjectType.LIGHT):
                self._apply_material(obj, obj_desc)

        # Move to collection
        if obj:
            for col in obj.users_collection:
                col.objects.unlink(obj)
            collection.objects.link(obj)

        return obj

    def _create_primitive(self, desc: SceneObject) -> Optional[bpy.types.Object]:
        """Create a Blender primitive object."""
        primitives = {
            "cube": lambda: bpy.ops.mesh.primitive_cube_add(),
            "sphere": lambda: bpy.ops.mesh.primitive_uv_sphere_add(),
            "cylinder": lambda: bpy.ops.mesh.primitive_cylinder_add(),
            "cone": lambda: bpy.ops.mesh.primitive_cone_add(),
            "torus": lambda: bpy.ops.mesh.primitive_torus_add(),
            "plane": lambda: bpy.ops.mesh.primitive_plane_add(),
            "monkey": lambda: bpy.ops.mesh.primitive_monkey_add(),
            "ico_sphere": lambda: bpy.ops.mesh.primitive_ico_sphere_add(),
        }

        op = primitives.get(desc.primitive_type, primitives["cube"])
        try:
            op()
            obj = bpy.context.active_object
            obj.name = desc.name
            return obj
        except Exception:
            return None

    def _create_light(self, desc: SceneObject) -> Optional[bpy.types.Object]:
        """Create a light object."""
        try:
            color = desc.emission_color[:3] if desc.emission_color else desc.color[:3]
            bpy.ops.object.light_add(type='POINT', location=desc.location)
            obj = bpy.context.active_object
            obj.name = desc.name
            obj.data.energy = 1000
            obj.data.color = color
            return obj
        except Exception:
            return None

    def _create_camera(self, desc: SceneObject) -> Optional[bpy.types.Object]:
        """Create a camera object."""
        try:
            bpy.ops.object.camera_add(location=desc.location)
            obj = bpy.context.active_object
            obj.name = desc.name
            # Point camera at target using track-to constraint
            target_loc = (0.0, 0.0, 0.0)
            direction = (
                target_loc[0] - desc.location[0],
                target_loc[1] - desc.location[1],
                target_loc[2] - desc.location[2],
            )
            import math
            rot_x = math.atan2(
                math.sqrt(direction[0]**2 + direction[1]**2),
                direction[2]
            )
            rot_z = math.atan2(direction[1], direction[0])
            obj.rotation_euler = (rot_x, 0.0, rot_z)
            return obj
        except Exception:
            return None

    def _apply_material(self, obj: bpy.types.Object, desc: SceneObject):
        """Apply a material to an object based on its description."""
        try:
            mat = bpy.data.materials.new(name=f"AI_Mat_{desc.name}")
            mat.use_nodes = True
            bsdf = mat.node_tree.nodes.get("Principled BSDF")

            if bsdf:
                bsdf.inputs["Base Color"].default_value = desc.color
                bsdf.inputs["Metallic"].default_value = desc.metalness
                bsdf.inputs["Roughness"].default_value = desc.roughness

                if desc.emission_color:
                    emission_input = bsdf.inputs.get("Emission Color") or bsdf.inputs.get("Emission")
                    if emission_input:
                        emission_input.default_value = desc.emission_color
                    strength_input = bsdf.inputs.get("Emission Strength")
                    if strength_input:
                        strength_input.default_value = 5.0

            obj.data.materials.append(mat)
        except Exception:
            pass

    def get_ai_objects(self, collection: bpy.types.Collection) -> List[bpy.types.Object]:
        """Get all AI-placeholder objects in a collection that need generation."""
        return [
            obj for obj in collection.objects
            if obj.get("ai_generate")
        ]


# Global singleton
_scene_composer: Optional[SceneComposer] = None


def get_scene_composer() -> SceneComposer:
    global _scene_composer
    if _scene_composer is None:
        _scene_composer = SceneComposer()
    return _scene_composer
