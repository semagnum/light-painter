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

from ..input import axis_prop, get_strokes_and_normals
from .method_util import has_strokes
from .sun_utils import SunProps


class LP_OT_SunLight(bpy.types.Operator, SunProps):
    """Modal object selection with a ray cast"""
    bl_idname = 'semagnum.lp_light_sun'
    bl_label = 'Paint Sun Lamp'
    bl_description = 'Adds a sun lamp to the scene at the 3D cursor that is rotated to light surfaces specified by annotations'
    bl_options = {'REGISTER', 'UNDO'}

    axis: axis_prop()

    @classmethod
    def poll(cls, context):
        return has_strokes(context)

    def draw(self, _context):
        layout = self.layout
        layout.use_property_split = True

        layout.prop(self, 'axis')

        self.draw_sun_props(layout)

    def execute(self, context):
        strokes = get_strokes_and_normals(context, self.axis, 0.0)
        vertices = tuple(v for stroke in strokes for v in stroke[0])
        normals = tuple(n for stroke in strokes for n in stroke[1])

        avg_normal = sum(normals, start=Vector())
        avg_normal.normalize()

        if self.normal_method == 'OCCLUSION':
            try:
                sun_normal = self.get_occlusion_based_normal(context, vertices, avg_normal)
            except ValueError:
                self.report({'ERROR'}, 'No valid directions found '
                                       '(add more samples or increase the elevation clamp!), using average normal')
                sun_normal = Vector(avg_normal)
        else:
            sun_normal = Vector(avg_normal)

        sun_normal.negate()

        # rotation difference
        rotation = Vector((0.0, 0.0, -1.0)).rotation_difference(sun_normal).to_euler()

        bpy.ops.object.select_all(action='DESELECT')

        center = context.scene.cursor.location

        bpy.ops.object.light_add(type='SUN', align='WORLD', location=center, rotation=rotation, scale=(1, 1, 1))

        return {'FINISHED'}
