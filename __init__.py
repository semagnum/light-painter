#     Light Painter, Blender add-on that creates lights based on where the user paints.
#     Copyright (C) 2024 Spencer Magnusson
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
    import sys
    import types

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

    reload_package(sys.modules[__name__])

import bpy

from . import axis, operators, panel, preferences
from . import translations

bl_info = {
    'name': 'Light Painter',
    'author': 'Spencer Magnusson',
    'version': (1, 4, 0),
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

    preferences.VIEW3D_AddonPreferences,
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
kmi_added = []


def register():
    """Registers Light Painter operators and tools."""
    for cls in operators_to_register:
        bpy.utils.register_class(cls)

    texture_type_items = [
        ('NOISE', 'Noise', ''),
        ('MAGIC', 'Magic', ''),
        ('MUSGRAVE', 'Musgrave', ''),
        ('VORONOI', 'Voronoi', ''),
        ('WAVE', 'Wave', ''),
    ]

    # Musgrave node is merged into the Noise mode in Blender 4.1
    if bpy.app.version >= (4, 1, 0):
        texture_type_items.pop(2)

    bpy.types.WindowManager.lightpainter_texture_type = bpy.props.EnumProperty(
        name='Texture Type',
        items=texture_type_items,
        default='NOISE',
    )

    # In background mode (no GUI), we don't need to register the tools or panel.
    # stored to prevent unregistering tools that were never registered
    wm = bpy.context.window_manager
    kc = wm.keyconfigs.addon

    if kc:
        global REGISTERED_WITH_UI, kmi_added
        REGISTERED_WITH_UI = True

        km_lightpainter = kc.keymaps.get(preferences.KEYMAP_NAME)
        if km_lightpainter is None:
            km_lightpainter = kc.keymaps.new(name=preferences.KEYMAP_NAME, space_type='VIEW_3D', region_type='WINDOW')
        kmi_lightpainter = km_lightpainter.keymap_items

        from .keymap import UNIVERSAL_KEYMAP

        for default_keymap in list(UNIVERSAL_KEYMAP)[::-1]:
            km_copy = dict(default_keymap)
            name = km_copy.pop('name')
            kmi = kmi_lightpainter.new('wm.call_menu', **km_copy)
            kmi.properties.name = name
            kmi.active = False
            kmi_added.append(kmi)

        bpy.utils.register_tool(panel.VIEW3D_T_light_paint, separator=True)

        bpy.utils.register_tool(panel.VIEW3D_T_sky_paint, group=True)
        bpy.utils.register_tool(panel.VIEW3D_T_sun_paint, after=panel.VIEW3D_T_sky_paint.bl_idname)

        bpy.utils.register_tool(panel.VIEW3D_T_mesh_light_paint)
        bpy.utils.register_tool(panel.VIEW3D_T_tube_light_paint)
        bpy.utils.register_tool(panel.VIEW3D_T_flag_paint)
        bpy.utils.register_tool(panel.VIEW3D_T_light_paint_adjust)

        bpy.utils.register_class(panel.LIGHTPAINTER_PT_Texture)

        translations.register()


def unregister():
    """Unregisters Light Painter operators and lamp_tool_group."""

    global REGISTERED_WITH_UI, kmi_added
    if REGISTERED_WITH_UI:
        keymaps = bpy.context.window_manager.keyconfigs.addon.keymaps
        km = keymaps.get(preferences.KEYMAP_NAME)
        if km:
            kmi = km.keymap_items
            for item in kmi_added:
                kmi.remove(item)

            # only delete if it's empty!!
            if len(km.keymap_items) == 0:
                keymaps.remove(km)

        for tool in tools[::-1]:
            bpy.utils.unregister_tool(tool)

        bpy.utils.unregister_class(panel.LIGHTPAINTER_PT_Texture)
        translations.unregister()

    for cls in operators_to_register[::-1]:
        bpy.utils.unregister_class(cls)


if __name__ == '__main__':
    register()
