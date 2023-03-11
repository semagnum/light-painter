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
from math import sqrt
from mathutils import Vector

from ..input import axis_prop, get_strokes_and_normals
from .method_util import assign_emissive_material, has_strokes


class LP_OT_AreaLight(bpy.types.Operator):
    """Modal object selection with a ray cast"""
    bl_idname = 'semagnum.lp_light_lamp'
    bl_label = 'Light Paint: Lamp'
    bl_options = {'REGISTER', 'UNDO'}

    axis: axis_prop()

    offset: bpy.props.FloatProperty(
        name='Distance',
        description='Distance from the drawing along the vertex normal',
        min=0.0,
        default=1.0,
        unit='LENGTH'
    )

    shape: bpy.props.EnumProperty(
        name='Shape',
        description='Determine axis of offset',
        items=[
            ('SQUARE', 'Square', ''),
            ('DISK', 'Disk', ''),
        ],
        default='SQUARE'
    )

    power: bpy.props.FloatProperty(
        name='Power',
        description='Area light\'s emit value',
        min=0.001,
        default=10,
        subtype='POWER',
        unit='POWER'
    )

    light_color: bpy.props.FloatVectorProperty(name="Light Color",
                                               size=3,
                                               default=[1.0, 1.0, 1.0],
                                               min=0.0,
                                               soft_max=1.0,
                                               subtype='COLOR')

    @classmethod
    def poll(cls, context):
        return has_strokes(context)

    def execute(self, context):
        strokes = get_strokes_and_normals(context, self.axis, self.offset)
        vertices = tuple(v for stroke in strokes for v in stroke[0])
        normals = (n for stroke in strokes for n in stroke[1])

        # get average, negated normal
        avg_normal = sum(normals, start=Vector())
        avg_normal.normalized()
        avg_normal.negate()

        projected_vertices = tuple(v.project(avg_normal) for v in vertices)

        center = sum(projected_vertices, start=Vector()) / len(vertices)

        # length_squared is to reduce calculations to just the final sqrt,
        # to get the actual distance from center.
        # multiplying by 2 to get the diagonal (d), the equation for area (A) is:
        # A = (d ** 2) / 2
        size = ((sqrt(max((center - v).length_squared for v in projected_vertices)) * 2) ** 2) / 2
        rotation = Vector((0, 0, -1)).rotation_difference(avg_normal).to_euler()

        bpy.ops.object.select_all(action='DESELECT')

        bpy.ops.object.light_add(type='AREA', align='WORLD', location=center, rotation=(0, 0, 0), scale=(1, 1, 1))

        # set light data properties

        context.object.rotation_euler = rotation
        context.object.data.color = self.light_color
        context.object.data.size = size
        context.object.data.energy = self.power
        context.object.data.shape = self.shape

        return {'FINISHED'}
