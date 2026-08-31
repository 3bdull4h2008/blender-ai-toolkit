"""Expert prompt system - guides LLM toward professional 3D results."""
from typing import Dict, List, Optional


EXPERT_PROMPTS = {
    "topology_best_practices": {
        "name": "Topology Best Practices",
        "description": "Guidelines for clean mesh topology",
        "prompt": """TOPOLOGY BEST PRACTICES for 3D modeling:

1. QUAD TOPOLOGY: Always prefer quads over triangles or n-gons. Quads subdivide cleanly, deform predictably, and work with all modifiers.

2. EDGE FLOW: Edges should follow the natural contours of the form. For characters, edge loops follow muscle groups. For hard surface, edges follow panel lines and bevels.

3. POLES: 
   - 3-edge poles: Good for starting edge loops, use at corners
   - 5-edge poles: Use where edge loops need to terminate
   - 6+ edge poles: Avoid in areas that deform, OK for static geometry

4. N-GON CLEANUP: Convert all n-gons to quads/tris before export. N-gons cause:
   - Shading artifacts
   - Subdivision surface problems
   - UV mapping issues
   - Boolean operation failures

5. FACE DENSITY: Distribute faces evenly. Avoid:
   - Dense clusters next to sparse areas
   - Long thin triangles (aspect ratio > 10:1)
   - Extremely small faces relative to neighbors

6. SYMMETRY: Use mirror modifier for symmetrical objects. Merge vertices along centerline with threshold.

7. MANIFOLD MESHES: Ensure all geometry is manifold (watertight):
   - No loose vertices/edges
   - No non-manifold edges
   - No internal faces
   - No zero-area faces""",
    },

    "scale_reference_guide": {
        "name": "Scale Reference Guide",
        "description": "Real-world dimensions for common objects",
        "prompt": """REAL-WORLD SCALE REFERENCES (meters):

HUMANOID:
  Adult male: 1.75m tall, 0.5m shoulder width
  Adult female: 1.65m tall, 0.45m shoulder width
  Child (10yr): 1.35m tall
  Eye height: 1.6m (adult)
  Arm span: ~height

FURNITURE:
  Dining table: 0.75m height, 1.2m x 0.8m top
  Chair: 0.45m seat height, 0.9m total height
  Bed: 0.6m height, 2.0m x 1.5m (queen)
  Door: 2.1m height, 0.9m width
  Kitchen counter: 0.9m height

VEHICLES:
  Sedan: 1.5m height, 4.5m length, 1.8m width
  SUV: 1.8m height, 5.0m length
  Truck: 2.5m height, 6.0m length
  Bicycle: 1.0m height, 1.8m length

ARCHITECTURE:
  Floor height: 3.0m (residential), 4.0m (commercial)
  Stair riser: 0.18m, tread: 0.28m
  Window: 1.2m height, 0.9m width (standard)
  Ceiling: 2.4m (residential), 3.0m (commercial)

WEAPONS:
  Sword length: 0.8-1.0m
  Rifle length: 1.0m
  Knife: 0.2-0.3m

SETUP IN BLENDER:
1. Set scene units to Metric
2. Set scale to 1.0
3. Apply scale to all objects (Ctrl+A > Scale)
4. Use real-world dimensions from the start""",
    },

    "lighting_principles": {
        "name": "Lighting Principles",
        "description": "Professional lighting setup guidelines",
        "prompt": """LIGHTING PRINCIPLES for 3D scenes:

THREE-POINT LIGHTING:
1. KEY LIGHT: Main light source, 45° from subject, slightly above
   - Strongest intensity (1000-5000W equivalent)
   - Warm color temperature (5000-6500K)

2. FILL LIGHT: Softens shadows from key light
   - 50-75% intensity of key
   - Opposite side of key
   - Cooler color temperature (7000-8000K)

3. RIM/BACK LIGHT: Separates subject from background
   - Behind subject, pointing toward camera
   - 75-100% intensity of key
   - Adds depth and dimension

LIGHT TYPES:
- Point: Omnidirectional, good for candles, bulbs
- Sun: Parallel rays, for outdoor/daylight
- Spot: Conical, for focused beams, stage lights
- Area: Soft shadows, for windows, softboxes

COLOR TEMPERATURE:
- Warm (3000K): Candlelight, sunset
- Neutral (5500K): Daylight
- Cool (7500K): Shade, overcast
- Blue (10000K+): Night sky

EEVEE vs CYCLES:
- EEVEE: Faster, use screen-space reflections, enable bloom
- Cycles: Accurate, use for final renders, enable denoising

HDRI LIGHTING:
- Use environment textures for realistic lighting
- Match HDRI to scene context (indoor/outdoor)
- Adjust strength for mood (0.5-2.0 typical)

SHADOW QUALITY:
- Soft shadows: Larger light source
- Hard shadows: Smaller/distant light source
- Contact shadows: Add subtle depth""",
    },

    "studio_lighting_setup": {
        "name": "Studio Lighting Setup",
        "description": "6-step professional studio lighting workflow",
        "prompt": """STUDIO LIGHTING WORKFLOW (6 Steps):

STEP 1: ENVIRONMENT SETUP
- Set world background to dark gray (0.05, 0.05, 0.05)
- Disable default light if present
- Set render engine (Cycles for quality, EEVEE for speed)

STEP 2: KEY LIGHT (Main)
- Add Area Light
- Position: 2-3m from subject, 45° left, 45° up
- Power: 1000W (adjust based on distance)
- Size: 1m x 1m (larger = softer shadows)
- Color: Slightly warm (1.0, 0.95, 0.9)

STEP 3: FILL LIGHT
- Add Area Light
- Position: Opposite side of key, lower angle
- Power: 500W (50% of key)
- Size: 1.5m x 1.5m (softer than key)
- Color: Slightly cool (0.9, 0.95, 1.0)

STEP 4: RIM LIGHT
- Add Spot Light or Area Light
- Position: Behind subject, pointing toward camera
- Power: 750W (75% of key)
- Size: 0.5m x 0.5m
- Color: Neutral white

STEP 5: ACCENT LIGHTS (Optional)
- Add Point Lights for highlights
- Position around subject for sparkle
- Power: 100-300W each
- Use sparingly

STEP 6: FINAL ADJUSTMENTS
- Check shadow softness (adjust light size)
- Balance color temperatures
- Add subtle HDRI for ambient (strength 0.1-0.3)
- Enable ambient occlusion for contact shadows""",
    },

    "material_workflow_guide": {
        "name": "Material Workflow Guide",
        "description": "PBR material creation guidelines",
        "prompt": """PBR MATERIAL WORKFLOW:

PRINCIPLED BSDF INPUTS:
- Base Color: Albedo/diffuse color (no lighting info)
- Metallic: 0.0 (dielectric) to 1.0 (metal)
- Roughness: 0.0 (mirror) to 1.0 (matte)
- Normal: Tangent space normal map
- Height/Displacement: Surface detail (use displacement modifier)
- Ambient Occlusion: Contact shadows

MATERIAL PRESETS:
METAL:
  Metallic: 1.0
  Roughness: 0.2-0.4
  Base Color: Gray (0.7-0.9) or metal color

PLASTIC:
  Metallic: 0.0
  Roughness: 0.3-0.5
  Base Color: Any color

WOOD:
  Metallic: 0.0
  Roughness: 0.6-0.8
  Base Color: Brown tones (0.3-0.6)

GLASS:
  Metallic: 0.0
  Roughness: 0.0-0.1
  Transmission: 1.0
  IOR: 1.45-1.5

FABRIC:
  Metallic: 0.0
  Roughness: 0.8-1.0
  Base Color: Any (use subsurface for skin)

STONE:
  Metallic: 0.0
  Roughness: 0.7-0.9
  Base Color: Gray/brown tones

TEXTURE COLOR SPACES:
- Base Color: sRGB
- Metallic: Non-Color
- Roughness: Non-Color
- Normal: Non-Color
- Displacement: Non-Color

UV MAPPING:
1. Mark seams along hard edges
2. Unwrap with Smart Project or Manual
3. Pack islands with margin (0.001-0.01)
4. Check for stretching in UV Editor""",
    },

    "character_basemesh_workflow": {
        "name": "Character Base Mesh Workflow",
        "description": "7-step character base mesh creation",
        "prompt": """CHARACTER BASE MESH WORKFLOW (7 Steps):

STEP 1: BLOCKOUT
- Start with default cube
- Add Mirror modifier (clipping enabled)
- Scale cube to rough torso proportions
- Add Loop Cuts for major landmarks

STEP 2: TORSO
- Shape torso with proportional editing
- Add chest and hip proportions
- Define waist with edge loops
- Keep geometry simple (8-12 vertical loops)

STEP 3: HEAD
- Extrude from torso top
- Shape skull with cube modeling
- Add eye sockets, nose, mouth cavities
- Keep symmetrical with mirror

STEP 4: ARMS
- Extrude from shoulder area
- Shape bicep, forearm, wrist
- Add elbow with 2-3 edge loops
- Hands can be separate objects initially

STEP 5: LEGS
- Extrude from hip area
- Shape thigh, knee, calf
- Add knee with 2-3 edge loops
- Feet can be separate objects initially

STEP 6: REFINEMENT
- Smooth transition areas
- Add muscle definition with subtle form
- Check proportions from all angles
- Use reference images

STEP 7: CLEANUP
- Merge separate parts if needed
- Ensure consistent face density
- Check for non-manifold edges
- Test subdivision surface modifier

PROPORTIONS (8-head system):
- Total height: 8 heads
- Shoulders: 2 heads wide
- Waist: 1 head wide
- Hips: 1.5 heads wide
- Arms: 3 heads long
- Legs: 4 heads long""",
    },

    "auto_critique_workflow": {
        "name": "Auto Critique Workflow",
        "description": "Visual feedback loop for quality assurance",
        "prompt": """AUTO-CRITIQUE WORKFLOW:

After generating or modifying a 3D model, perform this quality check:

1. VIEWPORT SCREENSHOT
   - Capture viewport from multiple angles
   - Use rendered mode for material check
   - Check silhouette from front, side, 3/4 view

2. GEOMETRY CHECK
   - Enter Edit Mode, select all
   - Mesh > Clean Up > Delete Loose
   - Check for non-manifold edges
   - Verify face normals point outward

3. TOPOLOGY CHECK
   - Check edge flow follows form
   - Verify quad dominance (>90% quads ideal)
   - Check for poles in deforming areas
   - Ensure even face distribution

4. PROPORTION CHECK
   - Compare to reference images
   - Check from multiple angles
   - Verify symmetry (if applicable)
   - Check real-world scale

5. MATERIAL CHECK
   - Verify UV mapping (no stretching)
   - Check texture resolution
   - Verify PBR values in correct ranges
   - Check for texture seams

6. LIGHTING CHECK
   - Render test image
   - Check shadow softness
   - Verify no overexposed areas
   - Check color balance

7. ITERATION
   - If issues found, fix and re-check
   - Document changes made
   - Compare before/after""",
    },

    "product_shot_setup": {
        "name": "Product Shot Setup",
        "description": "Professional product photography setup",
        "prompt": """PRODUCT SHOT SETUP:

CAMERA:
- Focal length: 85-135mm (telephoto for compression)
- Position: Eye level or slightly above
- Distance: 2-3x product size
- Enable depth of field (f/2.8-f/5.6)

LIGHTING:
- Key: Large softbox, 45° from product
- Fill: Reflector or second softbox
- Rim: Backlight for edge definition
- Background: Seamless white/gray

ENVIRONMENT:
- Use HDRI studio lighting
- Or 3-point light setup
- Enable ambient occlusion
- Consider area lights for soft shadows

COMPOSITION:
- Rule of thirds for placement
- Leave negative space
- Consider golden ratio
- Multiple angles: front, 3/4, detail

RENDER SETTINGS:
- Resolution: 2000x2000 minimum
- Samples: 500-1000 (Cycles)
- Enable denoising
- Output: PNG or EXR

POST-PROCESSING:
- Color correction
- Subtle vignette
- Sharpening
- Background cleanup""",
    },

    "scene_cleanup": {
        "name": "Scene Cleanup",
        "description": "Scene organization workflow",
        "prompt": "Scene cleanup workflow for organized Blender projects.",

    },

    "animation_turntable": {
        "name": "Animation Turntable",
        "description": "Turntable animation setup",
        "prompt": "Turntable animation setup for product展示.",

    },
}


def get_expert_prompt(prompt_id: str) -> Optional[str]:
    """Get an expert prompt by ID."""
    entry = EXPERT_PROMPTS.get(prompt_id)
    if entry:
        return entry["prompt"]
    return None


def get_all_expert_prompts() -> List[Dict]:
    """Get all expert prompts as a list of dicts."""
    return [
        {"id": k, "name": v["name"], "description": v["description"]}
        for k, v in EXPERT_PROMPTS.items()
    ]


def get_expert_prompt_for_task(task_type: str) -> str:
    """Get relevant expert prompts for a specific task type."""
    prompts = {
        "model_3d": ["topology_best_practices", "scale_reference_guide"],
        "material": ["material_workflow_guide"],
        "scene": ["lighting_principles", "studio_lighting_setup", "scale_reference_guide"],
        "character": ["character_basemesh_workflow", "topology_best_practices"],
        "product": ["product_shot_setup", "lighting_principles"],
    }

    selected = prompts.get(task_type, [])
    combined = []
    for pid in selected:
        prompt = get_expert_prompt(pid)
        if prompt:
            combined.append(prompt)

    return "\n\n---\n\n".join(combined)
