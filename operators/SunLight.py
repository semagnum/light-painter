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

from ..input import axis_prop, get_strokes, RAY_OFFSET
from .method_util import has_strokes


class LP_OT_SunLight(bpy.types.Operator):
    """Modal object selection with a ray cast"""
    bl_idname = 'semagnum.lp_light_sun'
    bl_label = 'Paint Sun Lamp'
    bl_options = {'REGISTER', 'UNDO'}

    axis: axis_prop()

    shadow_distance: bpy.props.FloatProperty(
        name='Shadow detection ray distance',
        description='Distance from brushstrokes for occlusion tests.'
                    'The higher the value, the "higher" in the sky your sun will likely be.',
        min=0.001,
        default=100.0,
        unit='LENGTH'
    )

    power: bpy.props.FloatProperty(
        name='Power',
        description='Area light\'s emit value',
        min=0.001,
        default=10,
        subtype='POWER',
        unit='POWER'
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

    def draw(self, _context):
        layout = self.layout
        layout.use_property_split = True

        layout.prop(self, 'axis')
        layout.prop(self, 'shadow_distance')

        layout.separator()
        layout.label(text='Lamp')
        layout.prop(self, 'light_color')
        layout.prop(self, 'power')

    def execute(self, context):
        vertices = tuple(v for stroke in get_strokes(context, self.axis, 0.0) for v in stroke)
        offset_dist = self.shadow_distance
        hit_vertices = tuple(v for stroke in get_strokes(context, self.axis, offset_dist) for v in stroke)

        # get average, negated normal
        def is_blocked(scene, depsgraph, origin, direction):
            offset_origin = origin + direction * RAY_OFFSET
            is_hit, _, _, _idx, _, _ = scene.ray_cast(depsgraph, offset_origin, direction)
            return is_hit

        scene = context.scene
        depsgraph = context.evaluated_depsgraph_get()

        # get average, negated normal
        avg_normal = Vector()
        for v in vertices:
            for hit_v in hit_vertices:
                potential_normal = hit_v - v
                potential_normal.normalized()
                if not is_blocked(scene, depsgraph, v, potential_normal):
                    avg_normal += potential_normal

        avg_normal.normalized()
        avg_normal.negate()

        # rotation difference
        rotation = Vector((0.0, 0.0, -1.0)).rotation_difference(avg_normal).to_euler()

        bpy.ops.object.select_all(action='DESELECT')

        center = scene.cursor.location

        bpy.ops.object.light_add(type='SUN', align='WORLD', location=center, rotation=rotation, scale=(1, 1, 1))

        # set light data properties
        context.object.data.color = self.light_color
        context.object.data.energy = self.power

        return {'FINISHED'}
