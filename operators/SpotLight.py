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
from mathutils import Vector

from ..input import axis_prop, get_strokes, get_strokes_and_normals, offset_prop, stroke_prop
from .method_util import get_average_normal, has_strokes, layout_group
from .VisibilitySettings import VisibilitySettings


class LP_OT_SpotLight(bpy.types.Operator, VisibilitySettings):
    """Modal object selection with a ray cast"""
    bl_idname = 'semagnum.lp_light_spot'
    bl_label = 'Paint Spot Lamp'
    bl_description = 'Adds a spot lamp to the scene that is positioned and rotated to light surfaces specified by annotations'
    bl_options = {'REGISTER', 'UNDO'}

    axis: axis_prop()

    stroke: stroke_prop('spot lamp')

    offset: offset_prop()

    power: bpy.props.FloatProperty(
        name='Power',
        description='Area light\'s emit value',
        min=0.001,
        default=10,
        subtype='POWER',
        unit='POWER'
    )

    radius: bpy.props.FloatProperty(
        name='Radius',
        description='Light size for ray shadow sampling',
        min=0.001,
        default=0.1,
        unit='LENGTH'
    )

    light_color: bpy.props.FloatVectorProperty(
        name='Color',
        size=3,
        default=(1.0, 1.0, 1.0),
        min=0.0,
        soft_max=1.0,
        subtype='COLOR'
    )

    @classmethod
    def poll(cls, context):
        return has_strokes(context)

    def draw(self, context):
        layout = self.layout
        layout.prop(self, 'stroke')
        layout.prop(self, 'axis')
        layout.prop(self, 'offset')

        box = layout_group(layout, text='Lamp')
        box.prop(self, 'light_color')
        box.prop(self, 'power')
        box.prop(self, 'radius')

        self.draw_visibility_props(layout)

    def add_lamp(self, context, orig_vertices, stroke):
        """Adds a spot lamp.

        :param context: Blender context
        :param orig_vertices: stroke vertices without offset from their surface
        :param stroke: tuple of vertices and normals, potentially offsetted from their surface

        :exception ValueError: if calculating the normal average fails

        :return: Blender lamp object
        """
        vertices, normals = stroke

        # THROWS ValueError if average is zero vector
        avg_normal = get_average_normal(normals)
        avg_normal.negate()

        farthest_point = max((v.project(avg_normal).length_squared, v) for v in vertices)[1]

        projected_vertices = tuple(v + (farthest_point - v).project(avg_normal) for v in vertices)

        center = sum(projected_vertices, start=Vector()) / len(projected_vertices)
        rotation = Vector((0.0, 0.0, -1.0)).rotation_difference(avg_normal).to_euler()

        orig_center = sum(orig_vertices, start=Vector()) / len(orig_vertices)
        centers_dir = (orig_center - center).normalized()
        spot_angle = 2 * max((v - center).normalized().angle(centers_dir)
                             for v in orig_vertices)

        bpy.ops.object.select_all(action='DESELECT')

        bpy.ops.object.light_add(type='SPOT', align='WORLD', location=center, rotation=rotation, scale=(1, 1, 1))

        # set light data properties
        context.object.data.color = self.light_color
        context.object.data.spot_size = spot_angle
        context.object.data.energy = self.power
        context.object.data.shadow_soft_size = self.radius
        self.set_visibility(context.object)

        return context.object

    def execute(self, context):
        try:
            strokes = get_strokes_and_normals(context, self.axis, self.offset)
            orig_strokes = get_strokes(context, self.axis, 0.0)
        except ValueError as e:
            self.report({'ERROR'}, str(e))
            return {'CANCELLED'}

        if self.stroke == 'ONE':
            vertices = tuple(v for stroke in strokes for v in stroke[0])
            normals = (n for stroke in strokes for n in stroke[1])

            orig_vertices = tuple(v for stroke in orig_strokes for v in stroke)
            try:
                self.add_lamp(context, orig_vertices, (vertices, normals))
            except ValueError as e:
                self.report({'ERROR'}, str(e) + ' Changing mesh hull count to per stroke.')
                self.stroke = 'PER_STROKE'

        if self.stroke == 'PER_STROKE':
            new_lamps = []
            for i in range(len(strokes)):
                try:
                    lamp_obj = self.add_lamp(context, orig_strokes[i], strokes[i])
                    new_lamps.append(lamp_obj)
                except ValueError as e:
                    self.report({'ERROR'}, str(e))

            for lamp_obj in new_lamps:
                lamp_obj.select_set(True)

        return {'FINISHED'}
