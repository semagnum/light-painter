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
"""Epsilon offset for raycasts, to prevent self-collisions."""


def reflect_vector(input_vector: Vector, normal: Vector) -> Vector:
    """Reflects input vector based on a given normal."""
    dn = 2 * input_vector.dot(normal)
    reflected_v = input_vector - normal * dn
    reflected_v.normalize()
    return reflected_v


def axis_prop() -> bpy.props.EnumProperty:
    """Returns axis property to determine direction of offset."""
    return bpy.props.EnumProperty(
        name='Offset Axis',
        description='Determine direction of the new object\'s offset',
        items=(
            ('X', 'X', 'Along global X axis'),
            ('Y', 'Y', 'Along global Y axis'),
            ('Z', 'Z', 'Along global Z axis'),
            ('NORMAL', 'Stroke Normal', 'Along annotation stroke\'s normal'),
            ('NORMAL-RAY', 'Surface Normal',
             'The stroke will cast rays beneath itself to find the underlying surface\'s normal'),
            ('REFLECT', 'Rim lighting',
             'Positions light to reflect onto the specified surface directly into the scene camera'),
        ),
        default='NORMAL-RAY'
    )


def offset_prop(obj_descriptor='Lamp', default_val: float = 1.0) -> bpy.props.FloatProperty:
    """Returns offset property to determine amount of offset."""
    return bpy.props.FloatProperty(
        name='Offset',
        description=f'{obj_descriptor}\'s offset from annotation(s) along specified axis',
        default=default_val,
        unit='LENGTH'
    )


def stroke_prop(obj_name: str) -> bpy.props.EnumProperty:
    """Returns enumerator property to determine usage of grease pencil strokes.

    :param obj_name: type of the generated object for description, e.g. "lamp" or "flag"
    :return: bpy enumerator property for operators
    """
    return bpy.props.EnumProperty(
        name='Count',
        description=f'How many {obj_name}s are created per stroke',
        items=(
            ('ONE', 'One', f'All strokes will create a single {obj_name}'),
            ('PER_STROKE', 'Per stroke', f'Each stroke will create its own {obj_name}'),
        ),
        default='ONE'
    )


def get_stroke_normals(context, vertices: list[Vector]) -> list[Vector]:
    """Get grease pencil stroke (approximated) normals

    :param context: Blender context
    :param vertices: world space coordinates of grease pencil points
    :return: list of normalized normals in world space per vertex
    """
    stroke_edge_indices = tuple((start_idx, end_idx)
                                for start_idx, end_idx in zip(range(len(vertices) - 1),
                                                              range(1, len(vertices))))
    bpy_data = context.blend_data

    stroke_mesh = bpy_data.meshes.new('myBeautifulMesh')  # add the new mesh
    stroke_mesh.from_pydata(vertices, stroke_edge_indices, tuple())

    bm_obj = bmesh.new()
    bm_obj.from_mesh(stroke_mesh)

    normals = [v.normal.normalized() for v in bm_obj.verts]

    # now that we have the vertex normals, delete the mesh data
    bm_obj.free()
    bpy_data.meshes.remove(stroke_mesh, do_unlink=True)
    return normals


def get_normals(context, vertices: list[Vector], axis_val: str) -> tuple[list[Vector], tuple[Vector]]:
    """Update normals of given vertices based on the axis value.

    :param context: Blender context
    :param vertices: list of vertices
    :param normals: correlating normal vectors
    :param axis_val: enumerator describing direction or axis of offset
    :param offset_amount: magnitude of offset
    :return: offset vertices and updated normals
    """

    if axis_val in VECTORS:
        normals = tuple(VECTORS[axis_val] for _ in vertices)
    elif axis_val == 'NORMAL-RAY':
        normals = get_stroke_normals(context, vertices)
        offset_vertices = tuple(v + n * RAY_OFFSET for v, n in zip(vertices, normals))

        scene = context.scene
        depsgraph = context.evaluated_depsgraph_get()
        for idx, v, n in zip(range(len(offset_vertices)), offset_vertices, normals):
            is_hit, hit_loc, hit_normal, _idx, _obj, _matrix = scene.ray_cast(depsgraph, v, n * -1)
            if is_hit:
                normals[idx] = hit_normal
                vertices[idx] = hit_loc

    elif axis_val == 'REFLECT':
        scene = context.scene
        camera = scene.camera

        if camera is None:
            raise ValueError('Set a camera for your scene to use rim lighting!')

        camera_origin = camera.matrix_world.translation

        normals = get_stroke_normals(context, vertices)

        scene = context.scene
        depsgraph = context.evaluated_depsgraph_get()
        for idx, v, n in zip(range(len(vertices)), vertices, normals):
            direction = v - camera_origin
            direction.normalize()
            is_hit, hit_loc, hit_normal, _idx, _obj, _matrix = scene.ray_cast(depsgraph, camera_origin, direction)
            if is_hit:
                normals[idx] = reflect_vector(direction, hit_normal)
                vertices[idx] = hit_loc
    else:
        normals = get_stroke_normals(context, vertices)

    return vertices, tuple(normals)
