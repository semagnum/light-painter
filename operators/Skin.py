#     Light Paint, Blender add-on that creates lights based on where the user paints.
#     Copyright (C) 2023 Spencer Magnusson
#     semagnum@gmail.com
#
#     This program is free software: you can redistribute it and/or modify
#     it under the terms of the GNU General Public License as published by
#     the Free Software Foundation, either version 3 of the License, or
#     (at your option) any later version.
#
#     This program is distributed in the hope that it will be useful,
#     but WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#     GNU General Public License for more details.
#
#     You should have received a copy of the GNU General Public License
#     along with this program.  If not, see <https://www.gnu.org/licenses/>.


import bpy

from ..input import axis_prop, get_strokes
from .method_util import assign_emissive_material, has_strokes


class LP_OT_Skin(bpy.types.Operator):
    """Modal object selection with a ray cast"""
    bl_idname = 'semagnum.lp_light_tube'
    bl_label = 'Paint Light Tubes'
    bl_options = {'REGISTER', 'UNDO'}

    axis: axis_prop()

    offset: bpy.props.FloatProperty(
        name='Offset',
        description='Wire\'s offset from annotation along specified axis',
        min=0.0,
        default=0.0,
        unit='LENGTH'
    )

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
        options=set(),
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

    visible_to_camera: bpy.props.BoolProperty(
        name='Visible to Camera',
        description='If unchecked, object will not be directly visible by camera (although it will still emit light)',
        options=set(),
        default=True
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

    @classmethod
    def poll(cls, context):
        return has_strokes(context)

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True

        layout.prop(self, 'axis')
        layout.prop(self, 'offset')

        layout.separator()
        layout.label(text='Wire')
        layout.prop(self, 'merge_distance')
        layout.prop(self, 'skin_radius')
        layout.prop(self, 'is_smooth')
        layout.prop(self, 'pre_subdiv', text='Path subdivision')
        layout.prop(self, 'post_subdiv', text='Surface subdivision')

        layout.separator()
        layout.label(text='Shading')
        layout.prop(self, 'visible_to_camera')
        layout.prop(self, 'light_color')
        layout.prop(self, 'emit_value')

    def execute(self, context):
        bpy.ops.object.select_all(action='DESELECT')

        mesh = bpy.data.meshes.new('LightPaint_Skin')
        obj = bpy.data.objects.new(mesh.name, mesh)
        col = context.collection
        col.objects.link(obj)
        context.view_layer.objects.active = obj

        strokes = get_strokes(context, self.axis, self.offset)
        vertices = []
        edge_idx = []
        for stroke in strokes:
            vertices += stroke
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

            wire_obj.visible_camera = self.visible_to_camera

        return {'FINISHED'}
