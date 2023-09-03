import bpy

from .prop_util import axis_prop, offset_prop
from ..axis import prep_stroke
from .base_tool import BaseLightPaintTool
from .lamp_util import get_average_normal
from .visibility import VisibilitySettings

EMISSIVE_MAT_NAME = 'LightPaint_Emissive'
MESH_DATA_NAME = 'LightPaint_Convex'
TUBE_DATA_NAME = 'LightPaint_Tube'


def assign_emissive_material(obj, color, emit_value: float):
    """Assigns an emissive material to a given object.

    :param obj: object to assign the emissive material.
    :param color: shader's emission color (1.0, 1.0, 1.0).
    :param emit_value: shader's emission value.
    """
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

    if len(obj.data.materials) == 0:
        obj.data.materials.append(material)  # Assign the new material
    else:
        obj.data.materials[0] = material


class LIGHTPAINTER_OT_Mesh(bpy.types.Operator, BaseLightPaintTool, VisibilitySettings):
    bl_idname = 'lightpainter.mesh'
    bl_label = 'Paint Mesh Light'
    bl_description = 'Adds or repositions mesh light to light surfaces specified by annotations'

    tool_id = 'view3d.lightpaint_mesh'

    axis: axis_prop('mesh')

    offset: offset_prop('mesh')

    flatten: bpy.props.BoolProperty(
        name='Flatten',
        description='If checked, projected vertices will be flattened before processing the convex hull',
        default=True
    )

    light_color: bpy.props.FloatVectorProperty(
        name='Color',
        size=4,
        default=[1.0, 1.0, 1.0, 1.0],
        min=0.0,
        soft_max=1.0,
        subtype='COLOR'
    )

    emit_value: bpy.props.FloatProperty(
        name='Emit Value',
        description='Emission shader\'s emit value',
        min=0.001,
        default=2.0,
    )

    def draw(self, _context):
        layout = self.layout

        layout.prop(self, 'axis')
        layout.prop(self, 'offset')
        layout.prop(self, 'flatten')

        layout.separator()

        layout.prop(self, 'light_color')
        layout.prop(self, 'emit_value')

        self.draw_visibility_props(layout)

    @staticmethod
    def generate_mesh(vertices, normals, flatten: bool):
        """Generates a mesh point cloud.

        :param vertices: list of points in world space
        :param normals: list of normals corresponding to the vertices
        :param flatten: if True, flattens the mesh into a plane

        :exception ValueError: if calculating the normal average fails

        :return: Blender mesh data
        """

        if not flatten:
            mesh_vertices = vertices
        else:
            # get average, negated normal (throws ValueError if average is zero vector)
            avg_normal = get_average_normal(normals)

            farthest_point = max((v.project(avg_normal).length_squared, v) for v in vertices)[1]

            mesh_vertices = tuple(v + (farthest_point - v).project(avg_normal) for v in vertices)

        mesh = bpy.data.meshes.new('LightPaint_Convex')
        mesh.from_pydata(mesh_vertices, [], [])

        return mesh

    def add_mesh_light(self, context, vertices, normals):
        """Adds an emissive convex hull mesh.

        :param context: Blender context
        :param vertices: a list of points in world space
        :param normals: a corresponding list of normals

        :return: Blender mesh object
        """
        bpy.ops.object.select_all(action='DESELECT')

        mesh = self.generate_mesh(vertices, normals, self.flatten)
        obj = bpy.data.objects.new(mesh.name, mesh)
        col = context.collection
        col.objects.link(obj)
        context.view_layer.objects.active = obj

        # go into edit mode, convex hull, cleanup, then get out
        bpy.ops.object.editmode_toggle()
        bpy.ops.mesh.convex_hull()
        bpy.ops.object.editmode_toggle()

        # assign emissive material to it
        assign_emissive_material(obj, self.light_color, self.emit_value)
        self.set_visibility(obj)

        return obj

    def execute(self, context):
        # skip if no strokes are currently drawn

        if len(self.mouse_path) == 0:
            return

        stroke_vertices = [coord for stroke in self.mouse_path for coord, normal in stroke]
        stroke_normals = [normal for stroke in self.mouse_path for coord, normal in stroke]
        offset_vertices, offset_normals, _ = prep_stroke(
            context, stroke_vertices, stroke_normals,
            self.axis, self.offset
        )

        try:
            self.add_mesh_light(context, offset_vertices, offset_normals)
        except ValueError as e:
            self.report({'ERROR'}, str(e))

        return {'FINISHED'}


class LIGHTPAINTER_OT_Tube_Light(bpy.types.Operator, BaseLightPaintTool, VisibilitySettings):
    bl_idname = 'lightpainter.tube_light'
    bl_label = 'Paint Mesh Light'
    bl_description = 'Adds or repositions mesh tube to light surfaces specified by annotations'

    tool_id = 'view3d.lightpaint_tube_light'

    axis: axis_prop('light tube')

    offset: offset_prop('light tube')

    merge_distance: bpy.props.FloatProperty(
        name='Merge by distance',
        description='Merge adjacent vertices closer than this distance',
        min=0.001,
        default=0.05,
        unit='LENGTH'
    )

    skin_radius: bpy.props.FloatProperty(
        name='Wire radius',
        min=0.001,
        default=0.1,
        unit='LENGTH'
    )

    is_smooth: bpy.props.BoolProperty(
        name='Smooth shading',
        description='If checked, skin modifier will set smooth faces',
        default=True
    )

    pre_subdiv: bpy.props.IntProperty(
        name='Wire path Subdivision',
        description='Subdivision level to smooth the wire path',
        min=0,
        default=2,
        soft_max=4,
    )

    post_subdiv: bpy.props.IntProperty(
        name='Wire surface subdivision',
        description='Subdivision level to smooth the wire\'s surface',
        min=0,
        default=2,
        soft_max=4,
    )

    light_color: bpy.props.FloatVectorProperty(
        name='Light Color',
        size=4,
        default=[1.0, 1.0, 1.0, 1.0],
        min=0.0,
        soft_max=1.0,
        subtype='COLOR'
    )

    emit_value: bpy.props.FloatProperty(
        name='Emit Value',
        description='Emission shader\'s emit value',
        min=0.001,
        default=2.0,
    )

    def draw(self, _context):
        layout = self.layout

        layout.prop(self, 'axis')
        layout.prop(self, 'offset')

        layout.separator()

        layout.prop(self, 'merge_distance')
        layout.prop(self, 'skin_radius')
        layout.prop(self, 'is_smooth')

        layout.label(text='Subdivision')
        row = layout.row()
        row.prop(self, 'pre_subdiv', text='Path')
        row.prop(self, 'post_subdiv', text='Surface')

        layout.separator()

        layout.prop(self, 'light_color', text='Color')
        layout.prop(self, 'emit_value')

        self.draw_visibility_props(layout)

    def execute(self, context):
        if len(self.mouse_path) == 0:
            return {'CANCELLED'}

        bpy.ops.object.select_all(action='DESELECT')

        mesh = bpy.data.meshes.new(TUBE_DATA_NAME)
        obj = bpy.data.objects.new(mesh.name, mesh)
        col = context.collection
        col.objects.link(obj)
        context.view_layer.objects.active = obj

        vertices = []
        edge_idx = []
        for stroke in self.mouse_path:
            stroke_vertices = [coord for coord, normal in stroke]
            stroke_normals = [normal for coord, normal in stroke]
            offset_vertices, _, _ = prep_stroke(
                context, stroke_vertices, stroke_normals,
                self.axis, self.offset
            )

            vertices += offset_vertices
            offset = 0 if len(edge_idx) == 0 else edge_idx[-1][-1] + 1
            edge_idx += [(start_idx + offset, end_idx + offset)
                         for start_idx, end_idx in zip(range(len(stroke) - 1),
                                                       range(1, len(stroke)))]

        mesh.from_pydata(vertices, edge_idx, [])

        bpy.ops.object.editmode_toggle()

        bpy.ops.mesh.remove_doubles(threshold=self.merge_distance)
        bpy.ops.mesh.separate(type='LOOSE')

        bpy.ops.object.editmode_toggle()

        all_wire_objs = context.selected_objects[:] + [context.view_layer.objects.active]

        for wire_obj in all_wire_objs:
            bpy.ops.object.select_all(action='DESELECT')
            wire_obj.select_set(True)
            context.view_layer.objects.active = wire_obj

            bpy.ops.object.modifier_add(type='SUBSURF')
            bpy.ops.object.modifier_add(type='SKIN')
            bpy.ops.object.modifier_add(type='SUBSURF')

            wire_obj.modifiers['Subdivision'].levels = self.pre_subdiv
            wire_obj.modifiers['Subdivision'].render_levels = self.pre_subdiv
            wire_obj.modifiers['Skin'].use_smooth_shade = self.is_smooth
            wire_obj.modifiers['Subdivision.001'].levels = self.post_subdiv
            wire_obj.modifiers['Subdivision.001'].render_levels = self.post_subdiv

            for v in wire_obj.data.skin_vertices[0].data:
                v.radius = [self.skin_radius, self.skin_radius]

            # assign emissive material to it
            assign_emissive_material(wire_obj, self.light_color, self.emit_value)
            self.set_visibility(wire_obj)

        return {'FINISHED'}
