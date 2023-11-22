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
    'version': (1, 1, 4),
    'blender': (3, 6, 0),
    'description': 'Creates lights based on where the user paints',
    'location': 'View 3D > Light Paint',
    'support': 'COMMUNITY',
    'category': '3D View',
    'doc_url': 'https://semagnum.github.io/light-painter/',
    'tracker_url': 'https://github.com/semagnum/light-painter/issues',
}

operators = (
    operators.LIGHTPAINTER_OT_Lamp,
    operators.LIGHTPAINTER_OT_Lamp_Adjust,
    operators.LIGHTPAINTER_OT_Mesh,
    operators.LIGHTPAINTER_OT_Tube_Light,
    operators.LIGHTPAINTER_OT_Sky,
    operators.LIGHTPAINTER_OT_Flag,
    operators.LIGHTPAINTER_OT_Lamp_Texture,
    operators.LIGHTPAINTER_OT_Lamp_Texture_Remove,
)

grouped_tools = (
    panel.VIEW3D_T_light_paint,
    panel.VIEW3D_T_mesh_light_paint,
    panel.VIEW3D_T_tube_light_paint,
    panel.VIEW3D_T_sky_paint,
)

REGISTERED_WITH_UI = False


def register():
    """Registers Light Painter operators and grouped_tools."""
    for cls in operators:
        bpy.utils.register_class(cls)

    bpy.types.WindowManager.lightpainter_texture_type = bpy.props.EnumProperty(
        name='Texture Type',
        items=[
            ('NOISE', 'Noise', ''),
            ('MAGIC', 'Magic', ''),
            ('MUSGRAVE', 'Musgrave', ''),
            ('VORONOI', 'Voronoi', ''),
            ('WAVE', 'Wave', ''),
        ],
        default='NOISE',
    )

    # In background mode (no GUI), we don't need to register the tools or panel.
    # stored to prevent unregistering tools that were never registered
    wm = bpy.context.window_manager
    kc = wm.keyconfigs.addon

    if kc:
        global REGISTERED_WITH_UI
        REGISTERED_WITH_UI = True
        first_idname = grouped_tools[0].bl_idname
        bpy.utils.register_tool(grouped_tools[0], separator=True, group=True)
        for tool in grouped_tools[1:]:
            bpy.utils.register_tool(tool, after=first_idname)

        bpy.utils.register_tool(panel.VIEW3D_T_flag_paint)
        bpy.utils.register_tool(panel.VIEW3D_T_light_paint_adjust)
        bpy.utils.register_class(panel.LIGHTPAINTER_PT_Texture)


def unregister():
    """Unregisters Light Painter operators and grouped_tools."""

    global REGISTERED_WITH_UI
    if REGISTERED_WITH_UI:
        for tool in grouped_tools[::-1]:
            bpy.utils.unregister_tool(tool)

        bpy.utils.unregister_tool(panel.VIEW3D_T_flag_paint)
        bpy.utils.unregister_tool(panel.VIEW3D_T_light_paint_adjust)
        bpy.utils.unregister_class(panel.LIGHTPAINTER_PT_Texture)

    for cls in operators[::-1]:
        bpy.utils.unregister_class(cls)


if __name__ == '__main__':
    register()
