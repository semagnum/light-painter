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


class LP_OT_ConvexLight(bpy.types.Operator):
    """Modal object selection with a ray cast"""
    bl_idname = 'semagnum.lp_convex_light'
    bl_label = 'Light Paint Convex Hull'
    bl_options = {'REGISTER', 'UNDO'}

    axis: axis_prop()

    offset: bpy.props.FloatProperty(
        name='Distance',
        description='Distance from the drawing along the vertex normal',
        min=0.0,
        default=0.0,
        unit='LENGTH'
    )

    visible_to_camera: bpy.props.BoolProperty(
        name='Visible to Camera',
        description='If unchecked, object will not be directly visible by camera (although it will still emit light)',
        options=set(),
        default=True
    )

    light_color: bpy.props.FloatVectorProperty(name="Light Color",
                                              size=4,
                                              default=[1.0, 1.0, 1.0, 1.0],
                                              min=0.0,
                                              soft_max=1.0,
                                              subtype='COLOR')

    emit_value: bpy.props.FloatProperty(
        name='Emit Value',
        description='Emission shader\'s emit value',
        min=0.001,
        default=2.0,
    )


    @classmethod
    def poll(cls, context):
        return has_strokes(context)

    def execute(self, context):
        bpy.ops.object.select_all(action='DESELECT')

        mesh = bpy.data.meshes.new('LightPaint_Convex')
        obj = bpy.data.objects.new(mesh.name, mesh)
        col = context.collection
        col.objects.link(obj)
        context.view_layer.objects.active = obj

        strokes = get_strokes(context, self.axis, self.offset)
        vertices = [v for stroke in strokes for v in stroke]

        mesh.from_pydata(vertices, [], [])

        # go into edit mode, convex hull, cleanup, then get out
        bpy.ops.object.editmode_toggle()

        bpy.ops.mesh.convex_hull()

        bpy.ops.object.editmode_toggle()

        # assign emissive material to it
        assign_emissive_material(obj, self.light_color, self.emit_value)

        obj.visible_camera = self.visible_to_camera

        return {'FINISHED'}
