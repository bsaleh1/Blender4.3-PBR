###############################
# SCALES
###############################
def make_scales_material(name="Proc_Scales"):
    # Get or create material
    mat = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    mat.use_nodes = True

    nt = mat.node_tree
    nt.nodes.clear()  # start from a clean node tree

    # Nodes
    out  = nt.nodes.new("ShaderNodeOutputMaterial"); out.location = (900, 0)   # material output
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled"); bsdf.location = (680, 0)  # main PBR shader

    coord = nt.nodes.new("ShaderNodeTexCoord"); coord.location = (-800, 0)     # object-space coords (stable for procedurals)
    mapn  = nt.nodes.new("ShaderNodeMapping");  mapn.location  = (-600, 0)     # global placement/scale control
    mapn.inputs["Scale"].default_value = (1.0, 0.6, 1.0)  # squash Y for scale/oval shapes

    voro  = nt.nodes.new("ShaderNodeTexVoronoi"); voro.location = (-380, 100)  # cell layout for scale boundaries
    voro.inputs["Scale"].default_value = 50.0

    ramp_edge = nt.nodes.new("ShaderNodeValToRGB"); ramp_edge.location = (-160, 100)  # sharpens cell edges
    r0, r1 = ramp_edge.color_ramp.elements[0], ramp_edge.color_ramp.elements[1]
    r0.position = 0.60; r0.color = (0, 0, 0, 1)   # black (inside cells)
    r1.position = 0.92; r1.color = (1, 1, 1, 1)   # white (near borders)

    ramp_cell = nt.nodes.new("ShaderNodeValToRGB"); ramp_cell.location = (-160, -120) # base color per cell
    rc0, rc1 = ramp_cell.color_ramp.elements[0], ramp_cell.color_ramp.elements[1]
    rc0.color = (0.08, 0.06, 0.05, 1)  # darker tone
    rc1.color = (0.25, 0.20, 0.15, 1)  # lighter tone

    sep = nt.nodes.new("ShaderNodeSeparateXYZ"); sep.location = (-380, -320)   # separate axes for vertical gradient
    ramp_grad = nt.nodes.new("ShaderNodeValToRGB"); ramp_grad.location = (-160, -320)  # overlap shading along Y
    g0, g1 = ramp_grad.color_ramp.elements[0], ramp_grad.color_ramp.elements[1]
    g0.position = 0.25; g0.color = (0.55, 0.55, 0.55, 1)  # darker lower region (overlap shadow)
    g1.position = 1.00; g1.color = (1, 1, 1, 1)          # brighter upper region

    noise = nt.nodes.new("ShaderNodeTexNoise"); noise.location = (-380, -520)  # subtle color variation within cells
    noise.inputs["Scale"].default_value = 20.0

    mix_noise = nt.nodes.new("ShaderNodeMixRGB"); mix_noise.location = (80, -80)  # blend base cell color with noise
    mix_noise.inputs["Fac"].default_value = 0.08  # very subtle variation

    mix_border = nt.nodes.new("ShaderNodeMixRGB"); mix_border.location = (280, 20)  # strengthen edges for definition
    mix_border.blend_type = 'MULTIPLY'
    mix_border.inputs["Fac"].default_value = 0.55

    mix_overlap = nt.nodes.new("ShaderNodeMixRGB"); mix_overlap.location = (480, 0)  # apply vertical overlap shading
    mix_overlap.blend_type = 'MULTIPLY'
    mix_overlap.inputs["Fac"].default_value = 1.0  # full effect

    invert = nt.nodes.new("ShaderNodeInvert"); invert.location = (280, -240)    # invert edge mask → height map orientation
    bump   = nt.nodes.new("ShaderNodeBump");   bump.location   = (680, -240)    # create physical relief on borders
    bump.inputs["Strength"].default_value = 0.25
    bump.inputs["Distance"].default_value = 0.10

    # Links
    L = nt.links.new
    L(coord.outputs["Object"], mapn.inputs["Vector"])   # use object coordinates → stable, non-UV based
    L(mapn.outputs["Vector"], voro.inputs["Vector"])
    L(mapn.outputs["Vector"], sep.inputs["Vector"])
    L(mapn.outputs["Vector"], noise.inputs["Vector"])

    L(voro.outputs["Distance"], ramp_edge.inputs["Fac"])  # distance-to-cell-border → edge ramp
    L(voro.outputs["Color"],    ramp_cell.inputs["Fac"])  # cell color ID → drive cell color ramp

    L(ramp_cell.outputs["Color"], mix_noise.inputs["Color1"])  # base cell color
    L(noise.outputs["Color"],     mix_noise.inputs["Color2"])  # add subtle noise

    L(mix_noise.outputs["Color"],  mix_border.inputs["Color1"])  # color pre-edges
    L(ramp_edge.outputs["Color"],  mix_border.inputs["Color2"])  # multiply in edge emphasis

    L(mix_border.outputs["Color"], mix_overlap.inputs["Color1"]) # result so far
    L(ramp_grad.outputs["Color"],  mix_overlap.inputs["Color2"]) # vertical overlap shading

    L(ramp_edge.outputs["Color"], invert.inputs["Color"])        # invert edge mask for bump sense
    L(invert.outputs["Color"],     bump.inputs["Height"])        # height map into bump

    L(sep.outputs["Y"], ramp_grad.inputs["Fac"])                 # drive gradient by Y axis

    L(mix_overlap.outputs["Color"], bsdf.inputs["Base Color"])   # final color to shader
    L(bump.outputs["Normal"],       bsdf.inputs["Normal"])       # normals from bump
    L(bsdf.outputs["BSDF"],         out.inputs["Surface"])       # shader to output

    return mat

# Run once to create/update the material in your .blend
make_scales_material()
print("Material 'Proc_Scales' is ready. Assign it from the Materials panel when needed.")
