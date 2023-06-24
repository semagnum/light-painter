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
import math
from mathutils import Matrix, Vector
from mathutils.geometry import box_fit_2d

from ..input import axis_prop, get_strokes_and_normals, offset_prop, stroke_prop
from .method_util import get_average_normal, has_strokes, layout_group, relative_power_prop, calc_power
from .VisibilitySettings import VisibilitySettings


def get_box(vertices, normal):
    """Given a set of vertices flattened along a plane and their normal, return an aligned rectangle.

    :param vertices: list of vertex coordinates in world space
    :param normal: normal of vertices for rectangle to be projected to
    :return: tuple of (coordinate of rect center, matrix for rotation, rect length, and rect width
    """
    # rotate hull so normal is pointed up, so we can ignore Z
    # find angle of fitted box
    align_to_z = normal.rotation_difference(Vector((0.0, 0.0, 1.0))).to_matrix()
    flattened_2d = [align_to_z @ v for v in vertices]

    # rotate hull by angle
    # get length and width
    angle = box_fit_2d([(v[0], v[1]) for v in flattened_2d])
    box_mat = Matrix.Rotation(angle, 3, 'Z')
    aligned_2d = [(box_mat @ Vector((co[0], co[1], 0))) for co in flattened_2d]
    xs = tuple(co[0] for co in aligned_2d)
    ys = tuple(co[1] for co in aligned_2d)

    x_min, x_max = min(xs), max(xs)
    y_min, y_max = min(ys), max(ys)

    length = x_max - x_min
    width = y_max - y_min

    center = align_to_z.inverted_safe() @ box_mat.inverted_safe() @ Vector((x_min + (length / 2),
                                                                            y_min + (width / 2),
                                                                            flattened_2d[0][2]))

    # return matrix, length and width of box
    return center, align_to_z.inverted_safe() @ box_mat.inverted_safe(), length, width


class LP_OT_AreaLight(bpy.types.Operator, VisibilitySettings):
    """Modal object selection with a ray cast"""
    bl_idname = 'semagnum.lp_light_area'
    bl_label = 'Paint Area Lamp'
    bl_description = 'Adds an area lamp to the scene that is positioned and rotated to light surfaces specified by annotations'
    bl_options = {'REGISTER', 'UNDO'}

    axis: axis_prop()

    offset: offset_prop()

    stroke: stroke_prop('area lamp')

    shape: bpy.props.EnumProperty(
        name='Shape',
        description='Determine axis of offset',
        items=[
            ('RECTANGLE', 'Rectangle', ''),
            ('SQUARE', 'Square', ''),
            ('DISK', 'Disk', ''),
            ('ELLIPSE', 'Ellipse', ''),
        ],
        default='RECTANGLE'
    )

    power: bpy.props.FloatProperty(
        name='Power',
        description='Area light\'s emit value',
        min=0.001,
        default=10,
        subtype='POWER',
        unit='POWER'
    )

    is_power_relative: relative_power_prop()

    min_size: bpy.props.FloatVectorProperty(
        name='Minimum size',
        description='Lamp size will be clamped to these minimum values',
        size=2,
        min=0.001,
        default=(0.01, 0.01),
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
        box.prop(self, 'shape')
        box.prop(self, 'light_color')

        row = box.row()
        row.prop(self, 'power')
        row.prop(self, 'is_power_relative', toggle=True)
        box.prop(self, 'min_size')

        self.draw_visibility_props(layout)

    def add_lamp(self, context, stroke):
        """Adds an area lamp.

        :param context: Blender context
        :param stroke: tuple of vertices and normals

        :exception ValueError: if calculating the normal average fails

        :return: Blender lamp object
        """

        vertices, normals = stroke
        # get average, negated normal, THROWS ValueError if average is zero vector
        avg_normal = get_average_normal(normals)
        avg_normal.negate()

        farthest_point = max((v.project(avg_normal).length_squared, v) for v in vertices)[1]

        projected_vertices = tuple(v + (farthest_point - v).project(avg_normal) for v in vertices)

        center, mat, x_size, y_size = get_box(projected_vertices, avg_normal)
        rotation = mat.to_euler()
        rotation.rotate_axis('X', math.radians(180.0))

        bpy.ops.object.select_all(action='DESELECT')

        bpy.ops.object.light_add(type='AREA', align='WORLD', location=center, rotation=rotation, scale=(1, 1, 1))

        # set light data properties
        context.object.data.color = self.light_color
        context.object.data.energy = calc_power(self.power, self.offset) if self.is_power_relative else self.power
        context.object.data.shape = self.shape
        if self.shape in {'RECTANGLE', 'ELLIPSE'}:
            context.object.data.size = max(self.min_size[0], x_size)
            context.object.data.size_y = max(self.min_size[1], y_size)
        else:
            max_size = max(x_size, y_size, self.min_size[0], self.min_size[1])
            context.object.data.size = max_size

        self.set_visibility(context.object)

        return context.object

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
                self.add_lamp(context, (vertices, normals))
            except ValueError as e:
                self.report({'ERROR'}, str(e) + ' Changing lamp count to per stroke.')
                self.stroke = 'PER_STROKE'

        if self.stroke == 'PER_STROKE':
            new_lamps = []
            for stroke in strokes:
                try:
                    new_lamp = self.add_lamp(context, stroke)
                    new_lamps.append(new_lamp)
                except ValueError as e:
                    self.report({'ERROR'}, str(e))

            for lamp_obj in new_lamps:
                lamp_obj.select_set(True)

        return {'FINISHED'}
