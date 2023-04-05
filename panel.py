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

from .operators import has_strokes
from .operators import LP_OT_AreaLight, LP_OT_PointLight, LP_OT_SunLight, LP_OT_SpotLight, LP_OT_Sky
from .operators import LP_OT_ConvexLight, LP_OT_Skin, LP_OT_ConvexShadow


ADDON_NAME = 'Light Paint'


class LP_PT_Paint(bpy.types.Panel):
    bl_space_type = 'VIEW_3D'
    bl_label = 'Paint'
    bl_category = ADDON_NAME
    bl_region_type = 'UI'
    bl_context = 'objectmode'

    def draw(self, context):
        layout = self.layout
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

        layout.operator('gpencil.annotation_active_frame_delete', text='Clear all')


class LP_PT_Light(bpy.types.Panel):
    bl_space_type = 'VIEW_3D'
    bl_label = 'Add Light'
    bl_category = ADDON_NAME
    bl_region_type = 'UI'
    bl_context = 'objectmode'

    def draw(self, context):
        layout = self.layout

        if not has_strokes(context):
            layout.label(text='No annotation strokes found. Use the "Paint" panel to add strokes.', icon='ERROR')

        layout.operator(LP_OT_PointLight.bl_idname, icon='LIGHT_POINT', text='Point')
        layout.operator(LP_OT_SunLight.bl_idname, icon='LIGHT_SUN', text='Sun')
        layout.operator(LP_OT_SpotLight.bl_idname, icon='LIGHT_SPOT', text='Spot')
        layout.operator(LP_OT_AreaLight.bl_idname, icon='LIGHT_AREA', text='Area')
        layout.operator(LP_OT_Sky.bl_idname, icon='WORLD', text='Sky Texture')

        layout.separator()

        layout.operator(LP_OT_ConvexLight.bl_idname, icon='MESH_ICOSPHERE', text='Mesh Hull')
        layout.operator(LP_OT_Skin.bl_idname, icon='MOD_SKIN', text='Light Tubes')

        layout.separator()
        layout.operator(LP_OT_ConvexShadow.bl_idname, icon='MESH_ICOSPHERE', text='Flag')
