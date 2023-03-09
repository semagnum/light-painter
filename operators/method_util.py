import bpy

MATERIAL_NAME = 'LightPaint_Emissive'


def generate_material(emit_value: float):
    material = bpy.data.materials.new(name=MATERIAL_NAME)

    material.use_nodes = True
    tree = material.node_tree

    tree.nodes.clear()

    output_node = tree.nodes.new(type='ShaderNodeOutputMaterial')
    emissive_node = tree.nodes.new(type='ShaderNodeEmission')

    # set emission value
    emissive_node.inputs[1].default_value = emit_value

    # connect
    tree.links.new(emissive_node.outputs[0], output_node.inputs['Surface'])

    return material


def assign_emissive_material(obj, emit_value: float):
    mat = generate_material(emit_value)
    obj.data.materials.append(mat)  # Assign the new material.
