#     Light Painter, Blender add-on that creates lights based on where the user paints.
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

from ..input import axis_prop, get_strokes_and_normals, offset_prop, stroke_prop
from .method_util import assign_emissive_material, get_average_normal, has_strokes, layout_group
from .VisibilitySettings import VisibilitySettings


class LP_OT_ConvexLight(bpy.types.Operator, VisibilitySettings):
    """Modal object selection with a ray cast"""
    bl_idname = 'semagnum.lp_light_hull'
    bl_label = 'Paint Light Hull'
    bl_description = 'Adds an emissive convex hull to the scene that is positioned to light surfaces specified by annotations'
    bl_options = {'REGISTER', 'UNDO'}

    axis: axis_prop()

    stroke: stroke_prop('convex hull')

    offset: offset_prop(obj_descriptor='Hull')

    flatten: bpy.props.BoolProperty(
        name='Flatten',
        description='If checked, projected vertices will be flattened before processing the convex hull',
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

        layout.prop(self, 'stroke')
        layout.prop(self, 'axis')
        layout.prop(self, 'offset')
        layout.prop(self, 'flatten')

        box = layout_group(layout, text='Lamp')
        box.prop(self, 'light_color', text='Lamp color')
        box.prop(self, 'emit_value')

        self.draw_visibility_props(layout)

    def generate_mesh(self, vertices, normals, flatten: bool):
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
        try:
            strokes = get_strokes_and_normals(context, self.axis, self.offset)
        except ValueError as e:
            self.report({'ERROR'}, str(e))
            return {'CANCELLED'}

        if self.stroke == 'ONE':
            vertices = tuple(v for stroke in strokes for v in stroke[0])
            normals = (n for stroke in strokes for n in stroke[1])
            try:
                self.add_mesh_light(context, vertices, normals)
            except ValueError as e:
                self.report({'ERROR'}, str(e) + ' Changing mesh hull count to per stroke.')
                self.stroke = 'PER_STROKE'

        if self.stroke == 'PER_STROKE':
            new_lamps = []
            for stroke in strokes:
                vertices, normals = stroke
                try:
                    new_obj = self.add_mesh_light(context, vertices, normals)
                    new_lamps.append(new_obj)
                except ValueError as e:
                    self.report({'ERROR'}, str(e))

            for lamp_obj in new_lamps:
                lamp_obj.select_set(True)

        return {'FINISHED'}
