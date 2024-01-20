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
    import os
    import types

    # double-check this add-on is imported, so it can be referenced and reloaded
    import lightpainter

    def reload_package(package):
        assert (hasattr(package, '__package__'))
        fn = package.__file__
        fn_dir = os.path.dirname(fn) + os.sep
        module_visit = {fn}
        del fn

        def reload_recursive_ex(module):
            module_iter = (
                module_child
                for module_child in vars(module).values()
                if isinstance(module_child, types.ModuleType)
            )
            for module_child in module_iter:
                fn_child = getattr(module_child, '__file__', None)
                if (fn_child is not None) and fn_child.startswith(fn_dir) and fn_child not in module_visit:
                    # print('Reloading:', fn_child, 'from', module)
                    module_visit.add(fn_child)
                    reload_recursive_ex(module_child)

            importlib.reload(module)

        return reload_recursive_ex(package)

    reload_package(lightpainter)

import bpy

from . import axis, operators, panel

bl_info = {
    'name': 'Light Painter',
    'author': 'Spencer Magnusson',
    'version': (1, 2, 7),
    'blender': (3, 6, 0),
    'description': 'Creates lights based on where the user paints',
    'location': 'View 3D > Light Paint',
    'support': 'COMMUNITY',
    'category': '3D View',
    'doc_url': 'https://semagnum.github.io/light-painter/',
    'tracker_url': 'https://github.com/semagnum/light-painter/issues',
}

operators_to_register = (
    operators.LIGHTPAINTER_OT_Lamp,
    operators.LIGHTPAINTER_OT_Lamp_Adjust,
    operators.LIGHTPAINTER_OT_Mesh,
    operators.LIGHTPAINTER_OT_Tube_Light,
    operators.LIGHTPAINTER_OT_Sky,
    operators.LIGHTPAINTER_OT_Sun,
    operators.LIGHTPAINTER_OT_Flag,
    operators.LIGHTPAINTER_OT_Lamp_Texture,
    operators.LIGHTPAINTER_OT_Lamp_Texture_Remove,
)

tools = (
    panel.VIEW3D_T_light_paint,
    panel.VIEW3D_T_sun_paint,
    panel.VIEW3D_T_sky_paint,
    panel.VIEW3D_T_mesh_light_paint,
    panel.VIEW3D_T_tube_light_paint,
    panel.VIEW3D_T_flag_paint,
    panel.VIEW3D_T_light_paint_adjust,
)

REGISTERED_WITH_UI = False


def register():
    """Registers Light Painter operators and tools."""
    for cls in operators_to_register:
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
        bpy.utils.register_tool(panel.VIEW3D_T_light_paint, separator=True)

        bpy.utils.register_tool(panel.VIEW3D_T_sky_paint, group=True)
        bpy.utils.register_tool(panel.VIEW3D_T_sun_paint, after=panel.VIEW3D_T_sky_paint.bl_idname)

        bpy.utils.register_tool(panel.VIEW3D_T_mesh_light_paint)
        bpy.utils.register_tool(panel.VIEW3D_T_tube_light_paint)
        bpy.utils.register_tool(panel.VIEW3D_T_flag_paint)
        bpy.utils.register_tool(panel.VIEW3D_T_light_paint_adjust)

        bpy.utils.register_class(panel.LIGHTPAINTER_PT_Texture)


def unregister():
    """Unregisters Light Painter operators and lamp_tool_group."""

    global REGISTERED_WITH_UI
    if REGISTERED_WITH_UI:
        for tool in tools[::-1]:
            bpy.utils.unregister_tool(tool)

        bpy.utils.unregister_class(panel.LIGHTPAINTER_PT_Texture)

    for cls in operators_to_register[::-1]:
        bpy.utils.unregister_class(cls)


if __name__ == '__main__':
    register()
