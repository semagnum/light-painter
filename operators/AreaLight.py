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

from ..input import axis_prop, get_strokes_and_normals
from .method_util import has_strokes


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


class LP_OT_AreaLight(bpy.types.Operator):
    """Modal object selection with a ray cast"""
    bl_idname = 'semagnum.lp_light_area'
    bl_label = 'Paint Area Lamp'
    bl_options = {'REGISTER', 'UNDO'}

    axis: axis_prop()

    offset: bpy.props.FloatProperty(
        name='Offset',
        description='Light\'s offset from annotation along specified axis',
        min=0.0,
        default=1.0,
        unit='LENGTH'
    )

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
        layout.use_property_split = True

        layout.prop(self, 'axis')
        layout.prop(self, 'offset')

        layout.separator()
        layout.label(text='Lamp')
        layout.prop(self, 'shape')
        layout.prop(self, 'light_color')
        layout.prop(self, 'power')
        layout.prop(self, 'min_size')

    def execute(self, context):
        strokes = get_strokes_and_normals(context, self.axis, self.offset)
        vertices = tuple(v for stroke in strokes for v in stroke[0])
        normals = (n for stroke in strokes for n in stroke[1])

        # get average, negated normal
        avg_normal = sum(normals, start=Vector())
        avg_normal.normalize()
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
        context.object.data.size = max(self.min_size[0], x_size)
        context.object.data.size_y = max(self.min_size[1], y_size)
        context.object.data.energy = self.power
        context.object.data.shape = self.shape

        return {'FINISHED'}
