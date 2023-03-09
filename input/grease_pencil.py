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


def get_vertices_and_normals(context):
    gp_layer = context.active_annotation_layer

    stroke_vertices = [point.co
                       for stroke in gp_layer.active_frame.strokes
                       for point in stroke.points]
    stroke_edge_indices = [(start_idx, end_idx)
                           for start_idx, end_idx in zip(range(len(stroke_vertices)),
                                                         list(range(1, len(stroke_vertices) - 1)) + [0])]

    # create mesh to get vertex normals

    stroke_mesh = bpy.data.meshes.new("myBeautifulMesh")  # add the new mesh
    stroke_mesh.from_pydata(stroke_vertices, stroke_edge_indices, tuple())

    bm_obj = bmesh.new()
    bm_obj.from_mesh(stroke_mesh)

    stroke_normals = [v.normal for v in bm_obj.verts]

    # now that we have the vertex normals, delete the mesh data
    bm_obj.free()
    bpy.data.meshes.remove(stroke_mesh, do_unlink=True)

    return stroke_vertices, stroke_normals
