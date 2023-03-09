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

from ..input import get_vertices_and_normals
from .method_util import assign_emissive_material


class LP_OT_ConvexHull(bpy.types.Operator):
    """Modal object selection with a ray cast"""
    bl_idname = 'semagnum.lp_convex_hull'
    bl_label = 'Light Paint Convex Hull'
    bl_options = {'REGISTER', 'UNDO'}

    distance: bpy.props.FloatProperty(
        name='Distance',
        description='Distance from the drawing along the vertex normal',
        min=0.001,
        default=5.0,
        unit='LENGTH'
    )

    emit_value: bpy.props.FloatProperty(
        name='Emit Value',
        description='Emission shader\'s emit value',
        min=0.001,
        default=2.0,
    )

    @classmethod
    def poll(cls, context):
        return hasattr(context.active_annotation_layer,
                       'active_frame') and context.active_annotation_layer.active_frame.strokes

    def execute(self, context):
        bpy.ops.object.select_all(action='DESELECT')

        mesh = bpy.data.meshes.new("ConvexHullLight")
        obj = bpy.data.objects.new(mesh.name, mesh)
        col = context.collection
        col.objects.link(obj)
        context.view_layer.objects.active = obj

        vertices, normals = get_vertices_and_normals(context)

        projected_vertices = [v + (norm * self.distance)
                              for v, norm in zip(vertices, normals)]

        mesh.from_pydata(projected_vertices, [], [])

        # go into edit mode, convex hull, cleanup, then get out
        bpy.ops.object.editmode_toggle()

        bpy.ops.mesh.convex_hull()

        bpy.ops.object.editmode_toggle()

        # assign emissive material to it
        assign_emissive_material(obj, self.emit_value)

        return {'FINISHED'}
