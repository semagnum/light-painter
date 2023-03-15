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
from bl_ui.space_toolsystem_common import ToolSelectPanelHelper

from .operators import LP_OT_AreaLight, LP_OT_ConvexLight, LP_OT_Skin, LP_OT_PointLight, LP_OT_SunLight, LP_OT_SpotLight


ADDON_NAME = 'Light Paint'


class LP_PT_LightPaint(bpy.types.Panel):
    bl_space_type = 'VIEW_3D'
    bl_label = ADDON_NAME
    bl_category = ADDON_NAME
    bl_region_type = 'UI'
    bl_context = 'objectmode'

    def draw(self, context):
        layout = self.layout

        layout.label(text='Paint')

        layout.prop(context.scene.tool_settings, 'annotation_stroke_placement_view3d', text='')

        tool_names_label_icon = (
            ('builtin.annotate', 'Freehand', 'ops.gpencil.draw'),
            ('builtin.annotate_line', 'Lines', 'ops.gpencil.draw.line'),
            ('builtin.annotate_polygon', 'Polygons', 'ops.gpencil.draw.poly'),
            ('builtin.annotate_eraser', 'Eraser', 'ops.gpencil.draw.eraser'),
        )

        op_name = 'wm.tool_set_by_id'
        col = layout.column(align=True)
        for name, label, icon in tool_names_label_icon:
            icon_val = ToolSelectPanelHelper._icon_value_from_icon_handle(icon)
            col.operator(op_name, text=label, icon_value=icon_val).name = name

        erase_icon_id = ToolSelectPanelHelper._icon_value_from_icon_handle('ops.gpencil.draw.eraser')
        layout.operator('gpencil.annotation_active_frame_delete',
                        text='Clear all', icon_value=erase_icon_id)

        layout.separator()

        layout.label(text='Light')

        row = layout.row()
        row.alignment = 'CENTER'

        row.operator(LP_OT_PointLight.bl_idname, icon='LIGHT_POINT', text='')
        row.operator(LP_OT_SunLight.bl_idname, icon='LIGHT_SUN', text='')
        row.operator(LP_OT_SpotLight.bl_idname, icon='LIGHT_SPOT', text='')
        row.operator(LP_OT_AreaLight.bl_idname, icon='LIGHT_AREA', text='')

        row = layout.row()
        row.alignment = 'CENTER'

        row.operator(LP_OT_ConvexLight.bl_idname, icon='MESH_ICOSPHERE', text='')
        row.operator(LP_OT_Skin.bl_idname, icon='MOD_SKIN', text='')
