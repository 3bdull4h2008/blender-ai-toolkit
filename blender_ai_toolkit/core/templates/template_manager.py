"""Template Manager for prompt templates with disk persistence."""
from dataclasses import dataclass, asdict
from enum import Enum
from typing import List, Optional
import os
import json


class TemplateCategory(Enum):
    CHARACTER = "character"
    ENVIRONMENT = "environment"
    PROP = "prop"
    VEHICLE = "vehicle"
    WEAPON = "weapon"
    ARCHITECTURE = "architecture"
    NATURE = "nature"
    FURNITURE = "furniture"
    TEXTURE = "texture"
    HDRI = "hdri"
    ABSTRACT = "abstract"
    CUSTOM = "custom"


@dataclass
class PromptTemplate:
    template_id: str
    name: str
    category: TemplateCategory
    prompt: str
    negative_prompt: str = ""
    default_params: dict = None

    def __post_init__(self):
        if self.default_params is None:
            self.default_params = {}

    def format_prompt(self) -> str:
        """Return the formatted prompt."""
        return self.prompt

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "template_id": self.template_id,
            "name": self.name,
            "category": self.category.value,
            "prompt": self.prompt,
            "negative_prompt": self.negative_prompt,
            "default_params": self.default_params,
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'PromptTemplate':
        """Create from dictionary."""
        return cls(
            template_id=data["template_id"],
            name=data["name"],
            category=TemplateCategory(data["category"]),
            prompt=data["prompt"],
            negative_prompt=data.get("negative_prompt", ""),
            default_params=data.get("default_params", {}),
        )


class TemplateManager:
    """Manages prompt templates with disk persistence for custom templates."""

    def __init__(self, storage_path: str = ""):
        self.storage_path = storage_path
        self._templates: dict = {}
        self._custom_file = os.path.join(storage_path, "custom_templates.json") if storage_path else ""
        # Initialize with defaults and load custom
        self._load_defaults()
        self._load_custom_from_disk()

    def get(self, template_id: str) -> Optional[PromptTemplate]:
        """Get a template by ID."""
        return self._templates.get(template_id)

    def get_all(self) -> List[PromptTemplate]:
        """Get all templates."""
        return list(self._templates.values())

    def add_custom(self, template: PromptTemplate):
        """Add a custom template and save to disk."""
        self._templates[template.template_id] = template
        self._save_custom_to_disk()

    def remove_custom(self, template_id: str):
        """Remove a custom template."""
        template = self._templates.get(template_id)
        if template and template.category == TemplateCategory.CUSTOM:
            del self._templates[template_id]
            self._save_custom_to_disk()

    def refresh(self):
        """Refresh templates from storage, preserving custom templates."""
        # Save custom templates before clearing
        custom_templates = {
            tid: t for tid, t in self._templates.items()
            if t.category == TemplateCategory.CUSTOM
        }
        self._templates.clear()
        self._load_defaults()
        # Restore custom templates
        self._templates.update(custom_templates)

    def _load_defaults(self):
        """Load default built-in templates."""
        default_templates = [
            PromptTemplate(
                template_id="default_character",
                name="Basic Character",
                category=TemplateCategory.CHARACTER,
                prompt="A detailed 3D character model, game-ready, clean topology",
                negative_prompt="low quality, blurry, distorted",
            ),
            PromptTemplate(
                template_id="default_environment",
                name="Forest Environment",
                category=TemplateCategory.ENVIRONMENT,
                prompt="Lush forest environment with trees, rocks, and foliage",
                negative_prompt="indoor, urban, man-made",
            ),
            PromptTemplate(
                template_id="default_architecture",
                name="Modern Building",
                category=TemplateCategory.ARCHITECTURE,
                prompt="Modern architectural building, glass and steel facade",
                negative_prompt="old, ruined, fantasy",
            ),
            PromptTemplate(
                template_id="default_vehicle",
                name="Sports Car",
                category=TemplateCategory.VEHICLE,
                prompt="Sleek sports car, aerodynamic design, realistic",
                negative_prompt="cartoon, toy, deformed",
            ),
            PromptTemplate(
                template_id="default_weapon",
                name="Fantasy Sword",
                category=TemplateCategory.WEAPON,
                prompt="Ornate fantasy sword with intricate details",
                negative_prompt="modern, gun, futuristic",
            ),
            PromptTemplate(
                template_id="default_texture",
                name="Wood Texture",
                category=TemplateCategory.TEXTURE,
                prompt="Seamless wood grain texture, natural oak pattern",
                negative_prompt="blurry, plastic, metal",
            ),
            PromptTemplate(
                template_id="default_hdri",
                name="Studio Lighting HDRI",
                category=TemplateCategory.HDRI,
                prompt="Professional studio lighting setup, soft shadows",
                negative_prompt="outdoor, harsh sunlight",
            ),
        ]

        for template in default_templates:
            self._templates[template.template_id] = template

    def _load_custom_from_disk(self):
        """Load custom templates from disk."""
        if not self._custom_file or not os.path.exists(self._custom_file):
            return

        try:
            with open(self._custom_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            for item in data:
                template = PromptTemplate.from_dict(item)
                self._templates[template.template_id] = template
        except (json.JSONDecodeError, IOError) as e:
            print(f"[AI Toolkit] Failed to load custom templates: {e}")

    def _save_custom_to_disk(self):
        """Save custom templates to disk."""
        if not self._custom_file:
            return

        custom = [
            t.to_dict() for t in self._templates.values()
            if t.category == TemplateCategory.CUSTOM
        ]

        try:
            os.makedirs(os.path.dirname(self._custom_file), exist_ok=True)
            with open(self._custom_file, 'w', encoding='utf-8') as f:
                json.dump(custom, f, indent=2, ensure_ascii=False)
        except IOError as e:
            print(f"[AI Toolkit] Failed to save custom templates: {e}")


# Global singleton
_template_manager: Optional[TemplateManager] = None


def get_template_manager(storage_path: str = "") -> TemplateManager:
    global _template_manager
    if _template_manager is None:
        _template_manager = TemplateManager(storage_path)
    return _template_manager
