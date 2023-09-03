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
from pathlib import Path

from .operators import (
    LIGHTPAINTER_OT_Lamp,
    LIGHTPAINTER_OT_Mesh,
    LIGHTPAINTER_OT_Tube_Light,
    LIGHTPAINTER_OT_Sky,
    LIGHTPAINTER_OT_Flag
)


def icon_path(name: str):
    return (Path(__file__).parent / ('light_painter.' + name)).as_posix()


class VIEW3D_T_light_paint(bpy.types.WorkSpaceTool):
    bl_idname = 'view3d.lightpaint_lamp'
    bl_space_type = 'VIEW_3D'
    bl_context_mode = 'OBJECT'
    bl_label = 'Light Paint'
    bl_operator = LIGHTPAINTER_OT_Lamp.bl_idname
    bl_icon = icon_path('light_paint')
    bl_keymap = (
        (LIGHTPAINTER_OT_Lamp.bl_idname, {'type': 'LEFTMOUSE', 'value': 'PRESS'}, None),
    )


class VIEW3D_T_mesh_light_paint(bpy.types.WorkSpaceTool):
    bl_idname = 'view3d.lightpaint_mesh'
    bl_space_type = 'VIEW_3D'
    bl_context_mode = 'OBJECT'
    bl_label = 'Mesh Light Paint'
    bl_operator = LIGHTPAINTER_OT_Mesh.bl_idname
    bl_icon = icon_path('mesh_light_paint')
    bl_keymap = (
        (LIGHTPAINTER_OT_Mesh.bl_idname, {'type': 'LEFTMOUSE', 'value': 'PRESS'}, None),
    )


class VIEW3D_T_tube_light_paint(bpy.types.WorkSpaceTool):
    bl_idname = 'view3d.lightpaint_tube_light'
    bl_space_type = 'VIEW_3D'
    bl_context_mode = 'OBJECT'
    bl_label = 'Tube Light Paint'
    bl_operator = LIGHTPAINTER_OT_Tube_Light.bl_idname
    bl_icon = icon_path('tube_light_paint')
    bl_keymap = (
        (LIGHTPAINTER_OT_Tube_Light.bl_idname, {'type': 'LEFTMOUSE', 'value': 'PRESS'}, None),
    )


class VIEW3D_T_sky_paint(bpy.types.WorkSpaceTool):
    bl_idname = 'view3d.lightpaint_sky'
    bl_space_type = 'VIEW_3D'
    bl_context_mode = 'OBJECT'
    bl_label = 'Sky Paint'
    bl_operator = LIGHTPAINTER_OT_Sky.bl_idname
    bl_icon = icon_path('sky_paint')
    bl_keymap = (
        (LIGHTPAINTER_OT_Sky.bl_idname, {'type': 'LEFTMOUSE', 'value': 'PRESS'}, None),
    )


class VIEW3D_T_flag_paint(bpy.types.WorkSpaceTool):
    bl_idname = 'view3d.lightpaint_flag'
    bl_space_type = 'VIEW_3D'
    bl_context_mode = 'OBJECT'
    bl_label = 'Shadow Paint'
    bl_operator = LIGHTPAINTER_OT_Flag.bl_idname
    bl_icon = icon_path('mesh_light_paint')
    bl_keymap = (
        (LIGHTPAINTER_OT_Flag.bl_idname, {'type': 'LEFTMOUSE', 'value': 'PRESS'}, None),
    )
