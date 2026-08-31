# Material Operators package
from .generate_material import AIGenerateMaterialOperator
from .texture_to_material import AITextureToMaterialOperator
from .apply_hdri import AIApplyHDRIOperator

__all__ = [
    "AIGenerateMaterialOperator",
    "AITextureToMaterialOperator",
    "AIApplyHDRIOperator",
]
