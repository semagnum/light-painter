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
import bmesh
from mathutils import Vector

VECTORS = {'X': Vector((1, 0, 0)), 'Y': Vector((0, 1, 0)), 'Z': Vector((0, 0, 1))}
"""List of arbitrary axes and their given vector."""
RAY_OFFSET = 0.001
"""Epsilon offset for ray casts, to prevent self-collisions."""


def reflect_vector(input_vector: Vector, normal: Vector) -> Vector:
    """Reflects input vector based on a given normal."""
    dn = 2 * input_vector.dot(normal)
    reflected_v = input_vector - normal * dn
    reflected_v.normalize()
    return reflected_v


def get_world_axis_normals(axis_val: str, count: int):
    return tuple(VECTORS[axis_val] for _ in range(count))


def prep_stroke(context, vertices: list[Vector], normals: list[Vector], axis: str, offset: float):
    if axis != 'NORMAL':
        if axis in VECTORS:
            normals = tuple(VECTORS[axis] for _ in range(len(vertices)))
        elif axis == 'REFLECT':
            scene = context.scene
            camera = scene.camera

            if camera is None:
                raise ValueError('Set a camera for your scene to use rim lighting!')

            camera_origin = camera.matrix_world.translation

            for idx, v, n in zip(range(len(vertices)), vertices, normals):
                direction = v - camera_origin
                direction.normalize()

                normals[idx] = reflect_vector(direction, n)

    orig_vertices = vertices[:]

    if offset != 0.0:
        vertices = tuple(
            v + n * offset
            for v, n in zip(vertices, normals)
        )

    if offset < 0.0:
        normals = [normal * -1 for normal in normals]

    return vertices, normals, orig_vertices
