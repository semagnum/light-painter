import bpy

EMISSIVE_MAT_NAME = 'LightPaint_Emissive'
FLAG_MAT_NAME = 'LightPaint_Shadow'

def has_strokes(context):
    annot_layer = context.active_annotation_layer
    return hasattr(annot_layer, 'active_frame') and hasattr(annot_layer.active_frame,
                                                            'strokes') and annot_layer.active_frame.strokes

def generate_emissive_material(color, emit_value: float):
    material = bpy.data.materials.new(name=EMISSIVE_MAT_NAME)

    material.use_nodes = True
    tree = material.node_tree

    tree.nodes.clear()

    output_node = tree.nodes.new(type='ShaderNodeOutputMaterial')
    emissive_node = tree.nodes.new(type='ShaderNodeEmission')

    # set emission color and value
    emissive_node.inputs[0].default_value = color
    emissive_node.inputs[1].default_value = emit_value

    # connect
    tree.links.new(emissive_node.outputs[0], output_node.inputs['Surface'])

    return material


def assign_emissive_material(obj, color, emit_value: float):
    mat = generate_emissive_material(color, emit_value)
    obj.data.materials.append(mat)  # Assign the new material.


def generate_flag_material(color):
    material = bpy.data.materials.new(name=FLAG_MAT_NAME)

    material.use_nodes = True
    tree = material.node_tree

    # find PBR and set color
    pbr_node = tree.nodes["Principled BSDF"]
    pbr_node.inputs[0].default_value = color

    return material


def assign_flag_material(obj, color):
    material = bpy.data.materials.new(name=FLAG_MAT_NAME)

    material.use_nodes = True
    tree = material.node_tree

    # find PBR and set color
    pbr_node = tree.nodes["Principled BSDF"]
    pbr_node.inputs[0].default_value = color

    # Assign the new material.
    obj.data.materials.append(material)
