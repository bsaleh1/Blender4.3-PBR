###################
# BEAK
###################
import bpy

# These values control the color and surface characteristics of the beak material (lighter, darker, shinier, rougher, etc)

MAT_NAME = "Beak_Keratin_Procedural"  # name of the material that will be created or reused

# Base color gradient from root to tip of the beak
COLOR_ROOT = (0.06, 0.06, 0.06, 1.0)   # near base (darker)
COLOR_MID  = (0.10, 0.08, 0.07, 1.0)   # middle tone
COLOR_TIP  = (0.20, 0.16, 0.12, 1.0)   # lighter tip
TIP_POSITION = 0.75                     # how far up the gradient the tip color appears
MID_POSITION = 0.40                     # how far up the gradient the mid color appears

# Surface roughness range — lower = glossier
ROUGH_MIN = 0.25
ROUGH_MAX = 0.55

# Texture scale and variation parameters
NOISE_SCALE     = 10.0   # fine pores
VORONOI_SCALE   = 40.0   # small pits
WAVE_SCALE      = 25.0   # long ridges
WAVE_DISTORTION = 0.5
WAVE_DETAIL     = 2.0

# Bump map intensity and blending factors
BUMP_STRENGTH    = 0.2
BUMP_DISTANCE    = 0.02
VORONOI_TO_BUMP  = 0.6
NOISE_TO_BUMP    = 0.4

# Global mapping scale
MAP_SCALE_X = 1.0
MAP_SCALE_Y = 1.0
MAP_SCALE_Z = 1.0

# Direction of the wave bands along the beak
WAVE_BANDS_DIRECTION = 'X'  # options: 'X', 'Y', 'Z'


def make_beak_keratin_material(name=MAT_NAME):
    # Create or fetch the material
    mat = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    nodes = nt.nodes
    links = nt.links

    # clear any existing nodes to start fresh
    for n in list(nodes):
        nodes.remove(n)

    # Core shader: Principled BSDF connected to Material Output
    out  = nodes.new("ShaderNodeOutputMaterial"); out.location = (1100, 0)
    bsdf = nodes.new("ShaderNodeBsdfPrincipled"); bsdf.location = (900, 0)
    links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])

    # Coordinate and Mapping nodes to control texture placement
    texcoord = nodes.new("ShaderNodeTexCoord"); texcoord.location = (-1100, 200)
    mapping  = nodes.new("ShaderNodeMapping"); mapping.location  = (-900, 200)
    mapping.inputs["Scale"].default_value = (MAP_SCALE_X, MAP_SCALE_Y, MAP_SCALE_Z)
    links.new(texcoord.outputs["Object"], mapping.inputs["Vector"])

    # Gradient texture to define root→tip coloration
    grad = nodes.new("ShaderNodeTexGradient"); grad.location = (-700, 200)
    grad.gradient_type = 'LINEAR'
    links.new(mapping.outputs["Vector"], grad.inputs["Vector"])

    # Color ramp for root/mid/tip tones
    grad_ramp = nodes.new("ShaderNodeValToRGB"); grad_ramp.location = (-450, 200)
    ramp = grad_ramp.color_ramp
    # ensure exactly 3 stops
    while len(ramp.elements) > 2:
        ramp.elements.remove(ramp.elements[-1])
    e0 = ramp.elements[0]; e1 = ramp.elements[1]
    e0.position = 0.0; e0.color = COLOR_ROOT
    e1.position = 1.0; e1.color = COLOR_TIP
    e_mid = ramp.elements.new(MID_POSITION); e_mid.color = COLOR_MID
    links.new(grad.outputs["Fac"], grad_ramp.inputs["Fac"])

    # Fine noise for subtle surface irregularities
    noise = nodes.new("ShaderNodeTexNoise"); noise.location = (-700, -150)
    noise.inputs["Scale"].default_value = NOISE_SCALE
    noise.inputs["Detail"].default_value = 6.0
    noise.inputs["Roughness"].default_value = 0.55
    links.new(mapping.outputs["Vector"], noise.inputs["Vector"])

    # Voronoi texture adds tiny cellular pits like keratin texture
    voro = nodes.new("ShaderNodeTexVoronoi"); voro.location = (-700, -400)
    voro.feature = 'F1'
    voro.distance = 'EUCLIDEAN'
    voro.inputs["Scale"].default_value = VORONOI_SCALE
    links.new(mapping.outputs["Vector"], voro.inputs["Vector"])

    # Wave texture for long streaks/ridges running along the beak
    wave = nodes.new("ShaderNodeTexWave"); wave.location = (-700, 500)
    wave.wave_type = 'BANDS'
    wave.bands_direction = WAVE_BANDS_DIRECTION
    wave.inputs["Scale"].default_value = WAVE_SCALE
    wave.inputs["Distortion"].default_value = WAVE_DISTORTION
    wave.inputs["Detail"].default_value = WAVE_DETAIL
    links.new(mapping.outputs["Vector"], wave.inputs["Vector"])

    # Combine gradient color with wave pattern for natural variation
    mix_color = nodes.new("ShaderNodeMix"); mix_color.location = (200, 200)
    mix_color.data_type = 'RGBA'
    mix_color.blend_type = 'MULTIPLY'
    mix_color.clamp_result = False
    mix_color.inputs[0].default_value = 0.15  # blend strength
    links.new(grad_ramp.outputs[0], mix_color.inputs[6])  # base color
    links.new(wave.outputs[0],      mix_color.inputs[7])  # modulation

    # Create roughness variation based on gradient + geometry
    rough_ramp = nodes.new("ShaderNodeValToRGB"); rough_ramp.location = (-250, -40)
    rr = rough_ramp.color_ramp
    while len(rr.elements) > 2:
        rr.elements.remove(rr.elements[-1])
    rr.elements[0].position = 0.0; rr.elements[0].color = (ROUGH_MAX, ROUGH_MAX, ROUGH_MAX, 1.0)
    rr.elements[1].position = 1.0; rr.elements[1].color = (ROUGH_MIN, ROUGH_MIN, ROUGH_MIN, 1.0)
    links.new(grad.outputs["Fac"], rough_ramp.inputs["Fac"])

    # Convert the color ramp output to a grayscale float for roughness
    to_bw = nodes.new("ShaderNodeRGBToBW"); to_bw.location = (-50, -40)
    links.new(rough_ramp.outputs["Color"], to_bw.inputs["Color"])

    # Use geometry's "Pointiness" for edge wear and micro-roughness
    geo = nodes.new("ShaderNodeNewGeometry"); geo.location = (-450, -260)

    # Blend roughness between ramp and pointiness
    mix_rough = nodes.new("ShaderNodeMix"); mix_rough.location = (100, -60)
    mix_rough.data_type = 'FLOAT'
    mix_rough.blend_type = 'MIX'
    mix_rough.inputs[0].default_value = 0.25
    links.new(to_bw.outputs["Val"],         mix_rough.inputs[1])
    links.new(geo.outputs["Pointiness"],    mix_rough.inputs[2])

    # Combine Voronoi and Noise for bump detail
    mul_v = nodes.new("ShaderNodeMath"); mul_v.location = (-450, -300); mul_v.operation = 'MULTIPLY'
    mul_v.inputs[1].default_value = VORONOI_TO_BUMP
    links.new(voro.outputs["Distance"], mul_v.inputs[0])

    mul_n = nodes.new("ShaderNodeMath"); mul_n.location = (-450, -430); mul_n.operation = 'MULTIPLY'
    mul_n.inputs[1].default_value = NOISE_TO_BUMP
    links.new(noise.outputs["Fac"], mul_n.inputs[0])

    # Add them together before passing to bump node
    add_h = nodes.new("ShaderNodeMath"); add_h.location = (-250, -350); add_h.operation = 'ADD'
    links.new(mul_v.outputs["Value"], add_h.inputs[0])
    links.new(mul_n.outputs["Value"], add_h.inputs[1])

    # Bump node adds surface depth based on the height map
    bump = nodes.new("ShaderNodeBump"); bump.location = (650, -150)
    bump.inputs["Strength"].default_value = BUMP_STRENGTH
    bump.inputs["Distance"].default_value = BUMP_DISTANCE
    links.new(add_h.outputs["Value"], bump.inputs["Height"])

    # Connect final color, roughness, and normal maps to BSDF
    links.new(mix_color.outputs["Result"], bsdf.inputs["Base Color"])
    links.new(mix_rough.outputs["Result"], bsdf.inputs["Roughness"])
    links.new(bump.outputs["Normal"],       bsdf.inputs["Normal"])

    return mat


# Build/update the material and confirm in the console
mat = make_beak_keratin_material()
print(f"Material '{mat.name}' ready.")
