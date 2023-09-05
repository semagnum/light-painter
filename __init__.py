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


if "bpy" in locals():
    import importlib
    reloadable_modules = [
        'axis',
        'operators',
        'panel',
    ]
    for module_name in reloadable_modules:
        if module_name in locals():
            importlib.reload(locals()[module_name])

import bpy

from . import axis, operators, panel

bl_info = {
    'name': 'Light Painter',
    'author': 'Spencer Magnusson',
    'version': (1, 0, 1),
    'blender': (3, 6, 0),
    'description': 'Creates lights based on where the user paints',
    'location': 'View 3D > Light Paint',
    'support': 'COMMUNITY',
    'category': '3D View',
    'doc_url': 'https://semagnum.github.io/light-painter/',
    'tracker_url': 'https://github.com/semagnum/light-painter/issues',
}

classes = (
    operators.LIGHTPAINTER_OT_Lamp,
    operators.LIGHTPAINTER_OT_Mesh,
    operators.LIGHTPAINTER_OT_Tube_Light,
    operators.LIGHTPAINTER_OT_Sky,
    operators.LIGHTPAINTER_OT_Flag
)

tools = (
    panel.VIEW3D_T_light_paint,
    panel.VIEW3D_T_mesh_light_paint,
    panel.VIEW3D_T_tube_light_paint,
    panel.VIEW3D_T_sky_paint,
    panel.VIEW3D_T_flag_paint,
)


def register():
    """Registers Light Painter operators and tools."""
    for cls in classes:
        bpy.utils.register_class(cls)

    first_idname = tools[0].bl_idname
    bpy.utils.register_tool(tools[0], separator=True,  group=True)
    for tool in tools[1:]:
        bpy.utils.register_tool(tool, after=first_idname)


def unregister():
    """Unregisters Light Painter operators and tools."""
    for tool in tools[::-1]:
        bpy.utils.unregister_tool(tool)

    for cls in classes[::-1]:
        bpy.utils.unregister_class(cls)


if __name__ == '__main__':
    register()
