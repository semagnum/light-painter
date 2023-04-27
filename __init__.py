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

from .operators import LP_OT_AreaLight, LP_OT_PointLight, LP_OT_SunLight, LP_OT_SpotLight, LP_OT_Sky
from .operators import LP_OT_ConvexLight, LP_OT_Skin, LP_OT_ShadowFlag
from .pie import PIE_MT_Light, PIE_MT_Paint
from .panel import LP_PT_Paint, LP_PT_Light

bl_info = {
    'name': 'Light Paint',
    'author': 'Spencer Magnusson',
    'version': (0, 5, 0),
    'blender': (3, 3, 0),
    'description': 'Creates lights based on where the user paints',
    'location': 'View 3D > Light Draw',
    'support': 'COMMUNITY',
    'category': '3D View',
    'doc_url': 'https://semagnum.github.io/light-painter/',
    'tracker_url': 'https://github.com/semagnum/light-painter/issues',
}

classes = (LP_OT_ConvexLight, LP_OT_Skin, LP_OT_ShadowFlag,
           LP_OT_AreaLight, LP_OT_PointLight, LP_OT_SunLight, LP_OT_SpotLight, LP_OT_Sky,
           LP_PT_Paint, LP_PT_Light, PIE_MT_Light, PIE_MT_Paint)

addon_pie_keymap = []

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    wm = bpy.context.window_manager
    if wm.keyconfigs.addon:
        kc = wm.keyconfigs.addon
        km = kc.keymaps.new(name='3D View Generic', space_type='VIEW_3D')
        kmi = km.keymap_items.new('wm.call_menu_pie', 'P', 'PRESS', shift=True)
        kmi.properties.name = "PIE_MT_Light"
        addon_pie_keymap.append((km, kmi))

        kmi = km.keymap_items.new('wm.call_menu_pie', 'P', 'PRESS', ctrl=True, shift=True)
        kmi.properties.name = "PIE_MT_Paint"
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
