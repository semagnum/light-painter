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


import bmesh
import bpy
from bpy_extras import view3d_utils
import gpu
from gpu_extras.batch import batch_for_shader

from .util import redraw_areas, remove


def draw(shade, bat):
    shade.bind()
    shade.uniform_float("color", (0, 1, 0, 0.25))
    bat.draw(shade)


def calc_screen_ray(context, event):
    region = context.region
    rv3d = context.region_data
    coord = event.mouse_region_x, event.mouse_region_y
    view_vector = view3d_utils.region_2d_to_vector_3d(region, rv3d, coord)
    ray_origin = view3d_utils.region_2d_to_origin_3d(region, rv3d, coord)
    return ray_origin, view_vector


def raycast_meshes_within_collection(collection, matrix, ray_origin, ray_vector):
    # for each collection instance, call raycast_meshes_within_collection(nested_coll, matrix, ray_origin, ray_vector)
    # for each mesh, call obj.ray_cast

    # pick closest mesh hit from all instances and meshes
    # return matrix @ loc (for comparison with scene.ray_cast), object mesh data
    pass


def raycast_to_bmesh(depsgraph, ray_origin, scene, view_vector):
    # TODO if instances exist, call raycast_meshes_within_collection
    # for each collection instance:
    # get transform matrix through instances, cast a ray onto mesh BVH
    # if hit and ray is shorter, generate a bmesh
    # return bm_obj, hit_face_index, is_hit, matrix, hit_obj.name

    is_hit, loc, normal, hit_face_index, hit_obj, matrix = scene.ray_cast(depsgraph, ray_origin, view_vector)

    if not is_hit:
        return 0, None, False, matrix, ''

    bm_obj = bmesh.new()
    eval_mesh = hit_obj.evaluated_get(depsgraph).to_mesh(depsgraph=depsgraph)
    bm_obj.from_mesh(eval_mesh)

    return bm_obj, hit_face_index, is_hit, matrix, hit_obj.name


def main(context, event):
    scene = context.scene
    depsgraph = context.evaluated_depsgraph_get()

    # get the ray from the viewport and mouse cursor
    ray_origin, view_vector = calc_screen_ray(context, event)
    bm_obj, hit_index, is_hit, matrix, obj_name = raycast_to_bmesh(depsgraph, ray_origin, scene, view_vector)

    if is_hit:
        # get coordinates of hit polygon - at least one triangle

        tris = bm_obj.calc_loop_triangles()

        bm_obj.faces.ensure_lookup_table()
        try:
            face_vert_indices = tuple(v.index for v in bm_obj.faces[hit_index].verts)
        except IndexError:
            print('"{}" does not have a face of index {} - it only contains {}'
                  .format(obj_name, hit_index, len(bm_obj.faces)))
            return False, None, None

        verts = []
        all_indices = []

        for tri in tris:
            if all(loop.vert.index in face_vert_indices for loop in tri):
                tri_inds = []
                for loop in tri:
                    v_co = matrix @ loop.vert.co
                    try:
                        ind = verts.index(v_co)
                        tri_inds.append(ind)
                    except ValueError:
                        verts.append(v_co)
                        tri_inds.append(len(verts) - 1)
                all_indices.append(tri_inds)

        bm_obj.free()
        return True, verts, all_indices

    return False, None, None


class LP_OT_Draw(bpy.types.Operator):
    """Modal object selection with a ray cast"""
    bl_idname = "view3d.modal_operator_raycast"
    bl_label = "Light Paint Draw Test"

    def __init__(self):
        self.vertices = []
        self.tri_indices = []

        self.shader = None
        self.batch = None
        self.draw_handler = None

        self.lmb = False

    def modal(self, context, event):
        if event.type in {'MIDDLEMOUSE', 'WHEELUPMOUSE', 'WHEELDOWNMOUSE'}:
            return {'PASS_THROUGH'}

        elif event.type == 'LEFTMOUSE':
            self.lmb = (event.value == 'PRESS')

        elif event.type in {'RIGHTMOUSE', 'ESC'}:
            if self.draw_handler is not None:
                remove(bpy.types.SpaceView3D, self.draw_handler, bpy.context)
            return {'CANCELLED'}

        # allows click-drag
        if self.lmb:
            is_hit, v_coords, tri_indices = main(context, event)

            if not is_hit:
                return {'PASS_THROUGH'}
                # need to offset new indices
            offset = len(self.vertices)
            self.vertices += v_coords
            for ind_group in tri_indices:
                self.tri_indices.append([idx + offset for idx in ind_group])

            self.shader = gpu.shader.from_builtin('3D_UNIFORM_COLOR')
            self.batch = batch_for_shader(self.shader, 'TRIS', {"pos": self.vertices}, indices=self.tri_indices)
            if self.draw_handler is not None:
                remove(bpy.types.SpaceView3D, self.draw_handler, bpy.context)
            self.draw_handler = bpy.types.SpaceView3D.draw_handler_add(draw, (self.shader, self.batch),
                                                                       'WINDOW', 'POST_VIEW')
            redraw_areas(bpy.context)

        return {'RUNNING_MODAL'}

    def invoke(self, context, event):
        if context.space_data.type == 'VIEW_3D':
            context.window_manager.modal_handler_add(self)
            return {'RUNNING_MODAL'}
        else:
            self.report({'WARNING'}, "Active space must be a View3d")
            return {'CANCELLED'}
