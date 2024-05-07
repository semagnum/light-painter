import bpy

TEXTURE_TYPE_TO_NODE = {
    'NOISE': 'ShaderNodeTexNoise',
    'MAGIC': 'ShaderNodeTexMagic',
    'MUSGRAVE': 'ShaderNodeTexMusgrave',
    'VORONOI': 'ShaderNodeTexVoronoi',
    'WAVE': 'ShaderNodeTexWave',
}


IS_BPY_V3 = bpy.app.version < (4, 0, 0)
OFFSET_AMOUNT = 180
GOBOS_WARNING = ('Gobos are best with point or spot lamps. '
                 'Results may not be as expected.')


def offset_node(curr_node, downstream_node):
    """Shifts left to the left of downstream nodes."""
    curr_node.location = (downstream_node.location[0] - OFFSET_AMOUNT, downstream_node.location[1])


def get_or_add_node(node_tree, bl_idname: str, downstream_node=None):
    """Gets node by type in node tree if it already exists, otherwise creates node and moves it."""
    curr_node = next((node for node in node_tree.nodes if node.bl_idname == bl_idname), None)
    if curr_node is None:
        curr_node = node_tree.nodes.new(type=bl_idname)
        if downstream_node is not None:
            offset_node(curr_node, downstream_node)
    return curr_node


class LIGHTPAINTER_OT_Lamp_Texture(bpy.types.Operator):
    bl_idname = 'lightpainter.lamp_texture'
    bl_label = 'Add Lamp Texture'
    bl_description = 'Adds texture to lamp to add variation'
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        active_obj = context.active_object
        return active_obj is not None and active_obj.type == 'LIGHT' and context.engine == 'CYCLES'

    def invoke(self, context, event):
        return context.window_manager.invoke_confirm(
            self, event,
            message=GOBOS_WARNING,
            confirm_text='Continue'
        )

    def execute(self, context):
        lamp = context.active_object
        tree = lamp.data.node_tree

        # if nodes is disabled, add all the nodes
        if tree is None or not lamp.data.use_nodes:
            lamp.data.use_nodes = True
            tree = lamp.data.node_tree

        output_node = get_or_add_node(tree, 'ShaderNodeOutputLight')
        emission_node = get_or_add_node(tree, 'ShaderNodeEmission', output_node)
        # map range (to make adjusting bright and dark areas easier)
        map_range_node = get_or_add_node(tree, 'ShaderNodeMapRange', emission_node)

        texture_type = context.window_manager.lightpainter_texture_type
        texture_node = get_or_add_node(tree, TEXTURE_TYPE_TO_NODE[texture_type], map_range_node)

        mapping_node = get_or_add_node(tree, 'ShaderNodeMapping', texture_node)
        if IS_BPY_V3:
            texture_coord_node = get_or_add_node(tree, 'ShaderNodeTexCoord', mapping_node)
        else:  # in Blender 4.0, it needs the geometry's Incoming socket instead
            texture_coord_node = get_or_add_node(tree, 'ShaderNodeNewGeometry', mapping_node)

        # link them all together
        if IS_BPY_V3:
            tree.links.new(texture_coord_node.outputs['Normal'], mapping_node.inputs['Vector'])
        else:
            tree.links.new(texture_coord_node.outputs['Incoming'], mapping_node.inputs['Vector'])
        tree.links.new(mapping_node.outputs[0], texture_node.inputs['Vector'])
        if texture_type == 'VORONOI':
            tree.links.new(texture_node.outputs['Distance'], map_range_node.inputs[0])
        else:
            tree.links.new(texture_node.outputs['Fac'], map_range_node.inputs[0])
        tree.links.new(map_range_node.outputs[0], emission_node.inputs[1])
        tree.links.new(emission_node.outputs[0], output_node.inputs[0])

        return {'FINISHED'}


class LIGHTPAINTER_OT_Lamp_Texture_Remove(bpy.types.Operator):
    bl_idname = 'lightpainter.lamp_texture_remove'
    bl_label = 'Remove Lamp Texture'
    bl_description = 'Removes texture from lamp'

    @classmethod
    def poll(cls, context):
        active_obj = context.active_object
        return (active_obj is not None and
                active_obj.type == 'LIGHT' and
                context.engine == 'CYCLES' and
                active_obj.data.use_nodes)

    def execute(self, context):
        lamp_data = context.active_object.data
        lamp_data.node_tree.nodes.clear()
        lamp_data.use_nodes = False
        return {'FINISHED'}
