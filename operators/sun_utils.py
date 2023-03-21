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
import numpy as np
from typing import Iterable

EPSILON = 0.01


def is_blocked(scene, depsgraph, origin: Vector, direction: Vector) -> bool:
    """Check if a given point is occluded in a given direction.

    :param scene: scene
    :param depsgraph: scene dependency graph
    :param origin: given point in world space as a Vector
    :param direction: given direction in world space as a Vector
    :return: True if anything is in that direction from that point, False otherwise
    """
    offset_origin = origin + direction * EPSILON
    is_hit, _, _, _idx, _, _ = scene.ray_cast(depsgraph, offset_origin, direction)
    return is_hit


def calc_rank(dot_product: float, count: int) -> float:
    """Calculate the "rank" of an occlusion ray test.

    :param dot_product: dot product between the current vector and the ideal normal
    :param count: number of points that can "see" in that direction
    :return: a rank for comparison, higher is better
    """
    return (dot_product + 1) * count


class SunProps:
    """Sun operator related properties and functions."""
    normal_method: bpy.props.EnumProperty(
        name='Method',
        description='Method to determine sun direction',
        items=(
            ('AVERAGE', 'Average', 'Uses average of normals'),
            ('OCCLUSION', 'Occlusion', 'Casts rays to determine occlusion and optimal direction for visibility'),
        ),
        default='AVERAGE'
    )

    samples: bpy.props.IntProperty(
        name='Samples',
        description='Samples of normals to determine occlusion',
        min=2,
        default=12,
    )

    z_dot: bpy.props.FloatProperty(
        name='Z Dot Product',
        description='Anything ray above this dot product of Z will be excluded.'
                    'Forces the sun closer to the horizon, if possible, for more "dynamic shots".',
        min=0.0, soft_min=0.0,
        max=1.0, soft_max=1.0,
        default=0.75,
    )

    def draw_sun_props(self, layout):
        """Draw sun properties in a UI layout."""
        layout.prop(self, 'normal_method', expand=True)

        if self.normal_method == 'OCCLUSION':
            layout.prop(self, 'samples')
            layout.prop(self, 'z_dot')

    def get_occlusion_based_normal(self, context, vertices: Iterable, avg_normal: Vector) -> Vector:
        """Find a normal that best points toward a given normal that's visible by the most points.

        :param context: Blender context
        :param vertices: list of points in world space as Vectors
        :param avg_normal: average normal as the preferred direction towards the sun lamp
        :return: world space Vector pointing towards the sun
        """
        # get an arbitrary X and Y axis
        x_axis = avg_normal.cross(Vector((0, 0, 1)))
        y_axis = avg_normal.cross(x_axis)

        axes = (x_axis, y_axis, avg_normal)
        sample_size = self.samples
        max_z_dot = self.z_dot

        def get_axis_linspace(idx: int):
            """Get a linear sample for a given axis."""
            sample_min = min(axis[idx] for axis in axes)
            sample_max = max(axis[idx] for axis in axes)
            return np.linspace(sample_min, sample_max, sample_size)

        x_samples = get_axis_linspace(0)
        y_samples = get_axis_linspace(1)
        z_samples = get_axis_linspace(2)

        # iterate over each axis
        # if the resulting vector is all zeroes or the dot product of it and Z axis is too high, skip
        # if the dot product of it and Z axis is less than zero, skip (to avoid night)
        scene = context.scene
        depsgraph = context.evaluated_depsgraph_get()
        sun_normal = Vector((0, 0, -1))
        sun_rank = 0

        samples_loop = ((x, y, z)
                        for x in x_samples
                        for y in y_samples
                        for z in z_samples
                        if not (x == 0 and y == 0 and z == 0))

        for x, y, z in samples_loop:
            curr_vector = Vector((x, y, z)).normalized()

            # clamp tested vectors to prevent lighting from straight above,
            # to force lower sun angles and therefore more dynamic lighting
            z_dot = curr_vector.dot(Vector((0, 0, 1)))
            if z_dot < 0 or z_dot > max_z_dot:
                continue

            vertex_visibility_count = 0
            for v in vertices:
                if not is_blocked(scene, depsgraph, v, curr_vector):
                    vertex_visibility_count += 1

            curr_rank = calc_rank(curr_vector.dot(avg_normal), vertex_visibility_count)
            if calc_rank(curr_vector.dot(avg_normal), vertex_visibility_count) > sun_rank:
                sun_rank = curr_rank
                sun_normal = curr_vector

        return sun_normal
