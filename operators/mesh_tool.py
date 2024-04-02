import bpy

from .base_tool import BaseLightPaintTool
from .lamp_util import get_average_normal
from .prop_util import axis_prop, convert_val_to_unit_str, get_drag_mode_header, offset_prop
from .visibility import VisibilitySettings
from ..axis import prep_stroke
from ..keymap import is_event_command, UNIVERSAL_COMMAND_STR as UCS

if bpy.app.version >= (4, 1):
    from bpy.app.translations import pgettext_rpt as rpt_
else:
    from bpy.app.translations import pgettext_tip as rpt_

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
    bl_description = 'Adds mesh light to light surfaces specified by annotations'

    tool_id = 'view3d.lightpaint_mesh'
    prev_vertices = ''

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

    def extra_paint_controls(self, context, event):
        mouse_x = event.mouse_x

        if is_event_command(event, 'OFFSET_MODE'):
            self.set_drag_attr('offset', mouse_x)

        elif is_event_command(event, 'POWER_MODE'):
            self.set_drag_attr('emit_value', mouse_x)

        elif is_event_command(event, 'FLATTEN_TOGGLE'):
            self.flatten = not self.flatten

        elif self.check_axis_event(event):
            pass  # if True, event is handled
        elif self.check_visibility_event(event):
            pass  # if True, event is handled

        else:
            return False

        return True

    # def get_header_text(self):
    #     if self.drag_attr == 'offset':
    #         return 'Offset: {}'.format(
    #             convert_val_to_unit_str(self.offset, 'LENGTH') + get_drag_mode_header()
    #         )
    #     elif self.drag_attr == 'emit_value':
    #         return 'Power: {}'.format(self.emit_value) + get_drag_mode_header()

    #     return super().get_header_text() + (
    #         '{}: flatten ({}), '
    #         '{}: offset mode, '
    #         '{}: power mode, '
    #         '{}{}{}{}: axis ({}), '
    #         '{}: Camera ({}), '
    #         '{}: Diffuse ({}), '
    #         '{}: Specular ({}), '
    #         '{}: Volume ({})'
    #     ).format(
    #         UCS['FLATTEN_TOGGLE'], 'ON' if self.flatten else 'OFF',
    #         UCS['OFFSET_MODE'],
    #         UCS['POWER_MODE'],
    #         UCS['AXIS_X'], UCS['AXIS_Y'], UCS['AXIS_Z'], UCS['AXIS_REFLECT'], self.axis,
    #         UCS['VISIBILITY_TOGGLE_CAMERA'], 'ON' if self.visible_camera else 'OFF',
    #         UCS['VISIBILITY_TOGGLE_DIFFUSE'], 'ON' if self.visible_diffuse else 'OFF',
    #         UCS['VISIBILITY_TOGGLE_SPECULAR'], 'ON' if self.visible_specular else 'OFF',
    #         UCS['VISIBILITY_TOGGLE_VOLUME'], 'ON' if self.visible_volume else 'OFF',
    #     )
    def get_header_text(self):
        if self.drag_attr == 'offset':
            return '{}: {}'.format(rpt_('Offset'),
                convert_val_to_unit_str(self.offset, 'LENGTH') + get_drag_mode_header()
            )
        elif self.drag_attr == 'emit_value':
            return '{}: {}'.format(rpt_('Power'),self.emit_value) + get_drag_mode_header()

        return super().get_header_text() + (
            '{}: {} ({}), '
            '{}: {}, '
            '{}: {}, '
            '{}{}{}{}: {} ({}), '
            '{}: {}, ({})'  # Camera mode, visibility status
            '{}: {}, ({})'  # Diffuse mode, visibility status
            '{}: {}, ({})'  # Specular mode, visibility status
            '{}: {}, ({})'  # Volume mode, visibility status
        ).format(
            UCS['FLATTEN_TOGGLE'], rpt_('flatten'), 'ON' if self.flatten else 'OFF',
            UCS['OFFSET_MODE'],rpt_('offset mode'),
            UCS['POWER_MODE'],rpt_('power mode'),
            UCS['AXIS_X'], UCS['AXIS_Y'], UCS['AXIS_Z'], UCS['AXIS_REFLECT'],rpt_('axis'), self.axis,
            UCS['VISIBILITY_TOGGLE_CAMERA'], rpt_('Camera'), rpt_('ON' if self.visible_camera else 'OFF'),
            UCS['VISIBILITY_TOGGLE_DIFFUSE'], rpt_('Diffuse'), rpt_('ON' if self.visible_diffuse else 'OFF'),
            UCS['VISIBILITY_TOGGLE_SPECULAR'], rpt_('Specular'), rpt_('ON' if self.visible_specular else 'OFF'),
            UCS['VISIBILITY_TOGGLE_VOLUME'], rpt_('Volume'), rpt_('ON' if self.visible_volume else 'OFF'),
        )


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

        return mesh_vertices

    def add_mesh_light(self, context, vertices, normals):
        """Adds an emissive convex hull mesh.

        :param context: Blender context
        :param vertices: a list of points in world space
        :param normals: a corresponding list of normals

        :return: Blender mesh object
        """
        mesh_vertices = self.generate_mesh(vertices, normals, self.flatten)
        mesh_obj = context.active_object
        mesh = mesh_obj.data

        # only updates geometry if changed
        # mitigates GH issue #50 in mesh constantly re-evaluating
        if str(mesh_vertices) != self.prev_vertices:
            mesh.clear_geometry()
            mesh.from_pydata(mesh_vertices, [], [])

            # go into edit mode, convex hull, cleanup, then get out
            bpy.ops.object.editmode_toggle()
            bpy.ops.mesh.convex_hull()
            bpy.ops.object.editmode_toggle()

            self.prev_vertices = str(mesh_vertices)

        # get emissive material, update emission value
        material = mesh_obj.data.materials[0]
        tree = material.node_tree
        emissive_node = next(node for node in tree.nodes if node.bl_idname == 'ShaderNodeEmission')
        emissive_node.inputs[1].default_value = self.emit_value

        self.set_visibility(mesh_obj)

    def update_light(self, context):
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

    def startup_callback(self, context):
        mesh = bpy.data.meshes.new('LightPaint_Convex')
        mesh_obj = bpy.data.objects.new(mesh.name, mesh)
        col = context.collection
        col.objects.link(mesh_obj)
        context.view_layer.objects.active = mesh_obj

        assign_emissive_material(mesh_obj, self.light_color, self.emit_value)

    def cancel_callback(self, context):
        """Deletes only our active object (our new tube light)."""
        with context.temp_override(selected_objects=[context.active_object]):
            bpy.ops.object.delete(use_global=False)


class LIGHTPAINTER_OT_Tube_Light(bpy.types.Operator, BaseLightPaintTool, VisibilitySettings):
    bl_idname = 'lightpainter.tube_light'
    bl_label = 'Paint Mesh Light'
    bl_description = 'Adds or repositions mesh tube to light surfaces specified by annotations'

    tool_id = 'view3d.lightpaint_tube_light'
    prev_edges = ''
    prev_vertices = ''

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

    def extra_paint_controls(self, context, event):
        mouse_x = event.mouse_x

        if is_event_command(event, 'OFFSET_MODE'):
            self.set_drag_attr('offset', mouse_x)

        elif is_event_command(event, 'SIZE_MODE'):
            self.set_drag_attr('skin_radius', mouse_x, drag_increment=0.05, drag_precise_increment=0.01)

        elif is_event_command(event, 'POWER_MODE'):
            self.set_drag_attr('emit_value', mouse_x)

        elif self.check_axis_event(event):
            pass  # if True, event is handled
        elif self.check_visibility_event(event):
            pass  # if True, event is handled

        else:
            return False

        return True

    # def get_header_text(self):
    #     if self.drag_attr == 'offset':
    #         return 'Offset: {}'.format(
    #             convert_val_to_unit_str(self.offset, 'LENGTH')
    #         ) + get_drag_mode_header()
    #     elif self.drag_attr == 'skin_radius':
    #         return 'Tube radius: {}'.format(
    #             convert_val_to_unit_str(self.skin_radius, 'LENGTH')
    #         ) + get_drag_mode_header()
    #     elif self.drag_attr == 'emit_value':
    #         return 'Power: {}'.format(self.emit_value) + get_drag_mode_header()

    #     return super().get_header_text() + (
    #         '{}: offset mode, '
    #         '{}: tube radius mode, '
    #         '{}: power mode, '
    #         '{}{}{}{}: axis ({}), '
    #         '{}: Camera ({}), '
    #         '{}: Diffuse ({}), '
    #         '{}: Specular ({}), '
    #         '{}: Volume ({})'
    #     ).format(
    #         UCS['OFFSET_MODE'],
    #         UCS['SIZE_MODE'],
    #         UCS['POWER_MODE'],
    #         UCS['AXIS_X'], UCS['AXIS_Y'], UCS['AXIS_Z'], UCS['AXIS_REFLECT'], self.axis,
    #         UCS['VISIBILITY_TOGGLE_CAMERA'], 'ON' if self.visible_camera else 'OFF',
    #         UCS['VISIBILITY_TOGGLE_DIFFUSE'], 'ON' if self.visible_diffuse else 'OFF',
    #         UCS['VISIBILITY_TOGGLE_SPECULAR'], 'ON' if self.visible_specular else 'OFF',
    #         UCS['VISIBILITY_TOGGLE_VOLUME'], 'ON' if self.visible_volume else 'OFF',
    #     )

    def get_header_text(self):
        if self.drag_attr == 'offset':
            return '{}: {}'.format(rpt_('Offset'),
                convert_val_to_unit_str(self.offset, 'LENGTH')
            ) + get_drag_mode_header()
        elif self.drag_attr == 'skin_radius':
            return '{}: {}'.format(rpt_('Tube radius'),
                convert_val_to_unit_str(self.skin_radius, 'LENGTH')
            ) + get_drag_mode_header()
        elif self.drag_attr == 'emit_value':
            return '{}: {}'.format(rpt_('Power'),self.emit_value) + get_drag_mode_header()

        return super().get_header_text() + (
            '{}: {}, '
            '{}: {}, '
            '{}: {}, '
            '{}{}{}{}: {} ({}), '
            '{}: {}, ({})'  # Camera mode, visibility status
            '{}: {}, ({})'  # Diffuse mode, visibility status
            '{}: {}, ({})'  # Specular mode, visibility status
            '{}: {}, ({})'  # Volume mode, visibility status
        ).format(
            UCS['OFFSET_MODE'],rpt_('offset mode'),
            UCS['SIZE_MODE'],rpt_('tube radius mode'),
            UCS['POWER_MODE'],rpt_('power mode'),
            UCS['AXIS_X'], UCS['AXIS_Y'], UCS['AXIS_Z'], UCS['AXIS_REFLECT'],rpt_('axis'), self.axis,
            UCS['VISIBILITY_TOGGLE_CAMERA'], rpt_('Camera'), rpt_('ON' if self.visible_camera else 'OFF'),
            UCS['VISIBILITY_TOGGLE_DIFFUSE'], rpt_('Diffuse'), rpt_('ON' if self.visible_diffuse else 'OFF'),
            UCS['VISIBILITY_TOGGLE_SPECULAR'], rpt_('Specular'), rpt_('ON' if self.visible_specular else 'OFF'),
            UCS['VISIBILITY_TOGGLE_VOLUME'], rpt_('Volume'), rpt_('ON' if self.visible_volume else 'OFF'),
        )

    def update_light(self, context):
        if len(self.mouse_path) == 0:
            return {'CANCELLED'}

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

        mesh_obj = context.active_object
        mesh = mesh_obj.data

        # only updates geometry if changed
        # mitigates GH issue #50 in mesh constantly re-evaluating
        if str(edge_idx) != self.prev_edges or str(vertices) != self.prev_vertices:
            mesh.clear_geometry()
            mesh.from_pydata(vertices, edge_idx, [])

            bpy.ops.mesh.customdata_skin_add()  # forces skin modifier data to exist/update

            bpy.ops.object.editmode_toggle()
            bpy.ops.mesh.remove_doubles(threshold=self.merge_distance)
            bpy.ops.object.skin_root_mark()
            bpy.ops.object.editmode_toggle()

            self.prev_vertices = vertices
            self.prev_edges = edge_idx

        for v in mesh_obj.data.skin_vertices[0].data:
            v.radius = [self.skin_radius, self.skin_radius]

        # get emissive material, update emission value
        material = mesh_obj.data.materials[0]
        tree = material.node_tree
        emissive_node = next(node for node in tree.nodes if node.bl_idname == 'ShaderNodeEmission')
        emissive_node.inputs[1].default_value = self.emit_value

        self.set_visibility(mesh_obj)

        return {'FINISHED'}

    def startup_callback(self, context):
        mesh = bpy.data.meshes.new(TUBE_DATA_NAME)
        mesh_obj = bpy.data.objects.new(mesh.name, mesh)
        col = context.collection
        col.objects.link(mesh_obj)
        context.view_layer.objects.active = mesh_obj

        bpy.ops.object.modifier_add(type='SUBSURF')
        bpy.ops.object.modifier_add(type='SKIN')
        bpy.ops.object.modifier_add(type='SUBSURF')

        mesh_obj.modifiers['Skin'].use_smooth_shade = self.is_smooth
        mesh_obj.modifiers['Subdivision'].levels = self.pre_subdiv
        mesh_obj.modifiers['Subdivision'].render_levels = self.pre_subdiv
        mesh_obj.modifiers['Subdivision.001'].levels = self.post_subdiv
        mesh_obj.modifiers['Subdivision.001'].render_levels = self.post_subdiv

        assign_emissive_material(mesh_obj, self.light_color, self.emit_value)

    def cancel_callback(self, context):
        """Deletes only our active object (our new tube light)."""
        with context.temp_override(selected_objects=[context.active_object]):
            bpy.ops.object.delete(use_global=False)