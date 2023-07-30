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


if "bpy" in locals():
    import importlib
    reloadable_modules = [
        'input',
        'operators',
        'pie',
        'panel',
    ]
    for module_name in reloadable_modules:
        if module_name in locals():
            importlib.reload(locals()[module_name])

import bpy

from . import input, operators, pie, panel

bl_info = {
    'name': 'Light Paint',
    'author': 'Spencer Magnusson',
    'version': (0, 6, 4),
    'blender': (3, 5, 0),
    'description': 'Creates lights based on where the user paints',
    'location': 'View 3D > Light Paint',
    'support': 'COMMUNITY',
    'category': '3D View',
    'doc_url': 'https://semagnum.github.io/light-painter/',
    'tracker_url': 'https://github.com/semagnum/light-painter/issues',
}

classes = (operators.LP_OT_ConvexLight, operators.LP_OT_Skin, operators.LP_OT_ShadowFlag,
           operators.LP_OT_AreaLight, operators.LP_OT_PointLight, operators.LP_OT_SpotLight,
           operators.LP_OT_SunLight, operators.LP_OT_Sky,
           panel.LP_PT_Paint, panel.LP_PT_Light,
           pie.PIE_MT_Light, pie.PIE_MT_Paint, pie.PIE_MT_StrokePlacement)

addon_pie_keymap = []


def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    wm = bpy.context.window_manager
    if wm.keyconfigs.addon:
        pie_menu_op = 'wm.call_menu_pie'

        kc = wm.keyconfigs.addon
        km = kc.keymaps.new(name='3D View Generic', space_type='VIEW_3D')
        kmi = km.keymap_items.new(pie_menu_op, 'P', 'PRESS', shift=True)
        kmi.properties.name = "PIE_MT_Light"
        addon_pie_keymap.append((km, kmi))

        kmi = km.keymap_items.new(pie_menu_op, 'P', 'PRESS', ctrl=True, shift=True)
        kmi.properties.name = "PIE_MT_Paint"
        addon_pie_keymap.append((km, kmi))

        kmi = km.keymap_items.new(pie_menu_op, 'P', 'PRESS', ctrl=True, shift=True, alt=True)
        kmi.properties.name = "PIE_MT_StrokePlacement"
        addon_pie_keymap.append((km, kmi))


def unregister():
    for cls in classes[::-1]:
        bpy.utils.unregister_class(cls)

    wm = bpy.context.window_manager
    kc = wm.keyconfigs.addon
    if kc:
        for km, kmi in addon_pie_keymap:
            km.keymap_items.remove(kmi)
    addon_pie_keymap.clear()


if __name__ == '__main__':
    register()
