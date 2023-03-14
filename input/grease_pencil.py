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
import bmesh

from .axis import offset_points


def get_stroke_vertices(context, stroke, axis: str, offset_amount: float) -> tuple:
    """Given a annotation stroke, return its point and normal data.

    :param context: Blender context
    :param stroke: individual stroke annotation data
    :param axis: enumerator describing direction or axis of offset
    :param offset_amount: offset distance
    :return: tuple of stroke coordinates and correlating normals
    """
    stroke_vertices = [point.co for point in stroke.points]
    stroke_edge_indices = tuple((start_idx, end_idx)
                                for start_idx, end_idx in zip(range(len(stroke_vertices) - 1),
                                                              range(1, len(stroke_vertices))))

    # create mesh to get vertex normals

    stroke_mesh = bpy.data.meshes.new('myBeautifulMesh')  # add the new mesh
    stroke_mesh.from_pydata(stroke_vertices, stroke_edge_indices, tuple())

    bm_obj = bmesh.new()
    bm_obj.from_mesh(stroke_mesh)

    stroke_normals = [v.normal for v in bm_obj.verts]

    # now that we have the vertex normals, delete the mesh data
    bm_obj.free()
    bpy.data.meshes.remove(stroke_mesh, do_unlink=True)

    stroke_vertices, stroke_normals = offset_points(context, stroke_vertices, stroke_normals, axis, offset_amount)

    return stroke_vertices, stroke_normals


def get_strokes(context, axis: str, offset_amount: float) -> tuple:
    """Get scene's current annotation stroke data.

    :param context: Blender context
    :param axis: enumerator describing direction or axis of offset
    :param offset_amount: offset distance
    :return: tuple of strokes, each a list of stroke coordinates
    """
    return tuple(stroke_data[0]
                 for stroke_data in get_strokes_and_normals(context, axis, offset_amount))


def get_strokes_and_normals(context, axis: str, offset_amount: float) -> tuple:
    """Get scene's current annotation stroke data, including estimated normals.

    :param context: Blender context
    :param axis: enumerator describing direction or axis of offset
    :param offset_amount: offset distance
    :return: tuple of strokes, each a tuple of a list of stroke coordinates and correlating normals
    """
    gp_frame = context.active_annotation_layer.active_frame

    return tuple(get_stroke_vertices(context, stroke, axis, offset_amount)
                 for stroke in gp_frame.strokes)
