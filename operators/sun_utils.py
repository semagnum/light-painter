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
from math import cos, pi, radians, sin
from mathutils import Vector
import numpy as np
from typing import Iterable

from .method_util import layout_group, is_blocked

EPSILON = 0.01
PI_OVER_2 = pi / 2


def calc_rank(dot_product: float, count: int) -> float:
    """Calculate the "rank" of an occlusion ray test.

    :param dot_product: dot product between the current vector and the ideal normal
    :param count: number of points that can "see" in that direction
    :return: a rank for comparison, higher is better
    """
    return (dot_product + 1) * count


def geo_to_dir(latitude, longitude) -> Vector:
    if latitude == pi/2:
        return Vector((0, 0, 1))
    x = sin(longitude)
    y = cos(longitude)
    z = sin(latitude)
    return Vector((x, y, z))


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

    longitude_samples: bpy.props.IntProperty(
        name='Azimuth Samples',
        description='Samples of normals around the azimuth. '
                    'Increasing samples improves precision at the cost of processing time',
        min=4,
        default=6,
    )

    latitude_samples: bpy.props.IntProperty(
        name='Elevation Samples',
        description='Samples of normals from the horizon to the maximum elevation. '
                    'Increasing samples improves precision at the cost of processing time',
        min=3,
        default=6,
    )

    sun_elevation_clamp: bpy.props.FloatProperty(
        name='Max Sun Elevation',
        description='Tested normals will be scaled to at most this elevation.'
                    'Forces the sun closer to the horizon, allowing more dynamic lighting.',
        min=0.0, soft_min=0.0,
        max=PI_OVER_2, soft_max=PI_OVER_2,
        default=radians(60),
        step=10,
        subtype='ANGLE'
    )

    def draw_sun_props(self, layout):
        """Draw sun properties in a UI layout."""
        box = layout_group(layout, text='Sun Position Method')
        row = box.row()
        row.prop(self, 'normal_method', expand=True)

        if self.normal_method == 'OCCLUSION':
            col = box.column(align=True)
            col.prop(self, 'longitude_samples')
            col.prop(self, 'latitude_samples')
            box.prop(self, 'sun_elevation_clamp', slider=True)

    def get_occlusion_based_normal(self, context, vertices: Iterable, avg_normal: Vector) -> Vector:
        """Find a normal that best points toward a given normal that's visible by the most points.

        :param context: Blender context
        :param vertices: list of points in world space as Vectors
        :param avg_normal: average normal as the preferred direction towards the sun lamp
        :return: world space Vector pointing towards the sun
        """
        max_sun_elevation = self.sun_elevation_clamp
        latitude_sample_size = self.latitude_samples
        latitude_samples = np.linspace(0, max_sun_elevation, latitude_sample_size)

        # since about half of longitudinal samples will not be viable (ie pointing away from ideal normal),
        # we will double its sample size.
        longitude_sample_size = self.longitude_samples * 2
        longitude_samples = np.linspace(0, 2 * pi, longitude_sample_size, endpoint=False)

        # iterate over each axis
        # if the resulting vector is all zeroes or the dot product of it and Z axis is too high, skip
        # if the dot product of it and Z axis is less than zero, skip (to avoid night)
        scene = context.scene
        depsgraph = context.evaluated_depsgraph_get()

        samples_loop = (geo_to_dir(lat, long).normalized()
                        for long in longitude_samples
                        for lat in latitude_samples
                        if geo_to_dir(lat, long).normalized().dot(avg_normal) > 0)

        def normal_rank(normal):
            vertex_visibility_count = sum(1 for v in vertices
                                          if not is_blocked(scene, depsgraph, v, normal))

            curr_rank = calc_rank(normal.dot(avg_normal), vertex_visibility_count)
            return curr_rank, normal

        sun_normal = max(normal_rank(normal) for normal in samples_loop)[1]

        return sun_normal
