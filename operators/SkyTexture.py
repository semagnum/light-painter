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
from math import atan, atan2, pi, sqrt
from mathutils import Vector

from ..input import axis_prop, get_strokes_and_normals
from .method_util import has_strokes
from .sun_utils import SunProps


class LP_OT_Sky(bpy.types.Operator, SunProps):
    """Modal object selection with a ray cast"""
    bl_idname = 'semagnum.lp_sky'
    bl_label = 'Paint Sky texture'
    bl_description = 'Adds a sky texture to the scene world where the sun is rotated to light surfaces specified by annotations'
    bl_options = {'REGISTER', 'UNDO'}

    axis: axis_prop()

    @classmethod
    def poll(cls, context):
        return has_strokes(context)

    def draw(self, _context):
        layout = self.layout
        layout.prop(self, 'axis')
        self.draw_sun_props(layout)

    def execute(self, context):
        try:
            strokes = get_strokes_and_normals(context, self.axis, 0.0)
        except ValueError as e:
            self.report({'ERROR'}, str(e))
            return {'CANCELLED'}

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
                sun_normal = avg_normal
        else:
            sun_normal = avg_normal

        # get world texture
        bpy_data = context.blend_data
        new_world = bpy_data.worlds.new('Light Painter World')
        context.scene.world = new_world
        new_world.use_nodes = True
        world_node_tree = new_world.node_tree

        # add sky texture node, connect to background node
        background_node = world_node_tree.nodes['Background']
        sky_node = world_node_tree.nodes.new('ShaderNodeTexSky')
        world_node_tree.links.new(sky_node.outputs[0], background_node.inputs[0])

        # add data for sky texture
        # set sky type based on render engine
        if context.scene.render.engine == 'CYCLES':
            sky_node.sky_type = 'NISHITA'
            x, y, z = sun_normal
            if z == 0:  # prevent division by zero
                z = 0.0001
            sky_node.sun_elevation = atan((sqrt(x*x + y*y)) / z) + (pi * 0.5)
            sky_node.sun_rotation = atan2(x, y) + pi
        else:
            sky_node.sky_type = 'PREETHAM'
            sky_node.sun_direction = sun_normal  # vector pointing towards sun

        # connect both nodes

        return {'FINISHED'}
