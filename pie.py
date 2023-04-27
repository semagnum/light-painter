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

"""Pie menu order: 4, 6, 2, 8, 7, 9, 1, 3"""
"""
7 8 9
4 - 6
1 2 3
"""

import bpy
from bl_ui.space_toolsystem_common import ToolSelectPanelHelper

from .operators import LP_OT_AreaLight, LP_OT_PointLight, LP_OT_SunLight, LP_OT_SpotLight, LP_OT_Sky
from .operators import LP_OT_ConvexLight, LP_OT_Skin, LP_OT_ShadowFlag


class PIE_MT_Paint(bpy.types.Menu):
    bl_label = 'Annotation Type'
    bl_idname = 'PIE_MT_Paint'

    def draw(self, context):
        """
        3 = clear all
        4, 6, 2, 8 = poly, draw, line, eraser
        """

        layout = self.layout.menu_pie()
        layout.scale_y = 1.2

        tool_names_label_icon = (
            ('builtin.annotate_polygon', 'Polygons', 'ops.gpencil.draw.poly'),
            ('builtin.annotate_eraser', 'Eraser', 'ops.gpencil.draw.eraser'),
            ('builtin.annotate_line', 'Lines', 'ops.gpencil.draw.line'),
            ('builtin.annotate', 'Freehand', 'ops.gpencil.draw'),
        )

        op_name = 'wm.tool_set_by_id'
        for name, label, icon in tool_names_label_icon:
            icon_val = ToolSelectPanelHelper._icon_value_from_icon_handle(icon)
            layout.operator(op_name, text=label, icon_value=icon_val).name = name

        # skip 3 times to get to 3
        for _ in range(3):
            layout.separator()

        layout.operator('gpencil.annotation_active_frame_delete', text='Clear all')


class PIE_MT_StrokePlacement(bpy.types.Menu):
    bl_label = 'Annotation Placement'
    bl_idname = 'PIE_MT_StrokePlacement'

    def draw(self, context):
        layout = self.layout.menu_pie()
        layout.prop(context.scene.tool_settings, 'annotation_stroke_placement_view3d',
                    text='Stroke placement', expand=True)


class PIE_MT_Light(bpy.types.Menu):
    bl_label = 'Light Paint'
    bl_idname = 'PIE_MT_Light'

    def draw(self, context):
        """
        1, 2, 4 = mesh hull, light tubes, shadow card
        7, 8, 9, 6, 3 = sky texture, sun, point, spot, area
        """
        layout = self.layout.menu_pie()
        layout.scale_y = 1.2

        layout.operator(LP_OT_ShadowFlag.bl_idname, icon='MESH_ICOSPHERE', text='Flag')
        layout.operator(LP_OT_SpotLight.bl_idname, icon='LIGHT_SPOT', text='Spot')
        layout.operator(LP_OT_Skin.bl_idname, icon='MOD_SKIN', text='Light Tubes')
        layout.operator(LP_OT_SunLight.bl_idname, icon='LIGHT_SUN', text='Sun')
        layout.operator(LP_OT_Sky.bl_idname, icon='WORLD', text='Sky Texture')
        layout.operator(LP_OT_PointLight.bl_idname, icon='LIGHT_POINT', text='Point')
        layout.operator(LP_OT_ConvexLight.bl_idname, icon='MESH_ICOSPHERE', text='Mesh Hull')
        layout.operator(LP_OT_AreaLight.bl_idname, icon='LIGHT_AREA', text='Area')
