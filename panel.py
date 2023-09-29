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
    LIGHTPAINTER_OT_Lamp_Adjust,
    LIGHTPAINTER_OT_Mesh,
    LIGHTPAINTER_OT_Tube_Light,
    LIGHTPAINTER_OT_Sky,
    LIGHTPAINTER_OT_Flag,
    LIGHTPAINTER_OT_Lamp_Texture,
    LIGHTPAINTER_OT_Lamp_Texture_Remove,
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


class VIEW3D_T_light_paint_adjust(bpy.types.WorkSpaceTool):
    bl_idname = 'view3d.lightpaint_lamp_adjust'
    bl_space_type = 'VIEW_3D'
    bl_context_mode = 'OBJECT'
    bl_label = 'Adjust Light'
    bl_operator = LIGHTPAINTER_OT_Lamp_Adjust.bl_idname
    bl_icon = icon_path('light_paint_adjust')
    bl_keymap = (
        (LIGHTPAINTER_OT_Lamp_Adjust.bl_idname, {'type': 'LEFTMOUSE', 'value': 'PRESS'}, None),
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


class LIGHTPAINTER_PT_Texture(bpy.types.Panel):
    bl_label = 'Light Painter Gobos'
    bl_idname = 'LIGHTPAINTER_PT_Texture'
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "data"

    @classmethod
    def poll(cls, context):
        active_obj = context.active_object
        return active_obj is not None and active_obj.type == 'LIGHT' and context.engine == 'CYCLES'

    def draw(self, context):
        layout = self.layout

        if context.active_object.data.type not in {'POINT', 'SPOT'}:
            layout.label(text='Gobos are best with point or spot lamps.', icon='ERROR')
            layout.label(text='Results may not be as expected.')

        layout.prop(context.window_manager, 'lightpainter_texture_type')

        layout.operator(LIGHTPAINTER_OT_Lamp_Texture.bl_idname, icon='MATERIAL')
        layout.operator(LIGHTPAINTER_OT_Lamp_Texture_Remove.bl_idname, icon='MATERIAL')