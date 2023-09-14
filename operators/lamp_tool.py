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

from .prop_util import axis_prop
from ..axis import prep_stroke
from .base_tool import BaseLightPaintTool
from .lamp_util import LampUtils


class LIGHTPAINTER_OT_Lamp(bpy.types.Operator, BaseLightPaintTool, LampUtils):
    bl_idname = 'lightpainter.lamp'
    bl_label = 'Paint Lamp'
    bl_description = 'Adds lamp to light surfaces specified by annotations'

    tool_id = 'view3d.lightpaint_lamp'

    lamp_type: bpy.props.EnumProperty(
        name='Lamp Type',
        items=(
            ('POINT', 'Point', '', 'LIGHT_POINT', 0),
            ('SPOT', 'Spot', '', 'LIGHT_SPOT', 1),
            ('AREA', 'Area', '', 'LIGHT_AREA', 2),
        ),
        default='POINT',
    )

    axis: axis_prop('lamp')

    def draw(self, _context):
        layout = self.layout
        layout.prop(self, 'lamp_type')

        layout.separator()

        layout.prop(self, 'axis')
        layout.prop(self, 'offset')

        layout.separator()

        if self.lamp_type == 'AREA':
            layout.prop(self, 'shape')
            layout.prop(self, 'min_size')
        else:
            layout.prop(self, 'radius')

        layout.separator()

        layout.prop(self, 'light_color')
        row = layout.row()
        row.prop(self, 'power')
        row.prop(self, 'is_power_relative', toggle=True)

        layout.separator()

        self.draw_visibility_props(layout)

    def execute(self, context):
        stroke_vertices = [coord for stroke in self.mouse_path for coord, normal in stroke]
        stroke_normals = [normal for stroke in self.mouse_path for coord, normal in stroke]
        vertices, normals, orig_vertices = prep_stroke(
            context, stroke_vertices, stroke_normals,
            self.axis, self.offset
        )

        # skip if no strokes are currently drawn
        if len(stroke_vertices) == 0:
            return {'CANCELLED'}

        lamp_type = self.lamp_type

        # add new lamp (set as active object by default)
        bpy.ops.object.light_add(type=self.lamp_type, align='WORLD')

        lamp = context.active_object

        lamp_update_funcs = {
            'AREA': self.update_area_lamp,
            'SPOT': lambda spot_lamp, stroke: self.update_spot_lamp(spot_lamp, orig_vertices, stroke),
            'POINT': self.update_point_lamp,
        }

        try:
            lamp_update_funcs[lamp_type](lamp, (vertices, normals))
        except ValueError as e:
            self.report({'ERROR'}, str(e))
            return {'CANCELLED'}

        return {'FINISHED'}
