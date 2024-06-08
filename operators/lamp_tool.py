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

from .base_tool import BaseLightPaintTool
from .lamp_util import LampUtils
from .prop_util import axis_prop, convert_val_to_unit_str, get_drag_mode_header
from ..axis import prep_stroke
from ..keymap import is_event_command, UNIVERSAL_COMMAND_STR as UCS
if bpy.app.version >= (4, 1):
    from bpy.app.translations import pgettext_rpt as rpt_
else:
    from bpy.app.translations import pgettext_tip as rpt_

LAMP_TYPES_ORDER = ('POINT', 'SPOT', 'AREA')


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
        layout.use_property_split = True
        layout.use_property_decorate = False  # No animation

        layout.prop(self, 'lamp_type')
        if self.lamp_type == 'AREA':
            layout.prop(self, 'shape')
            layout.prop(self, 'min_size')
            layout.prop(self, 'spread')
        elif self.lamp_type == 'SPOT':
            layout.prop(self, 'spot_blend')
        else:
            layout.prop(self, 'radius')

        layout.separator()

        col = layout.column(align=True)
        col.prop(self, 'axis')
        col.prop(self, 'offset', text='Amount')

        layout.separator()

        layout.prop(self, 'light_color')
        col = layout.column(align=True)
        col.prop(self, 'power')
        col.prop(self, 'is_power_relative')

        layout.separator()

        self.draw_visibility_props(layout)

    def get_header_text(self):
        if self.drag_attr == 'offset':
            return '{}: {}'.format(rpt_('Offset'),
                convert_val_to_unit_str(self.offset, 'LENGTH'),
            ) + get_drag_mode_header()
        elif self.drag_attr == 'radius':
            return '{}: {}'.format(rpt_('Lamp radius'),
                convert_val_to_unit_str(self.radius, 'LENGTH'),
            ) + get_drag_mode_header()
        elif self.drag_attr == 'power':
            return '{}: {}{}'.format(rpt_('Power'),
                                     convert_val_to_unit_str(self.power, 'POWER'),
                                     (' (relative)' if self.is_power_relative else '')
                                     ) + get_drag_mode_header()

        return super().get_header_text() + (
            '{}: {}, '
            '{}: {}, '.format(
                UCS['TYPE_TOGGLE'], rpt_('lamp type'),
                UCS['OFFSET_MODE'], rpt_('offset mode'),
            ) +
            ('{}: {}, '.format((UCS['SIZE_MODE']) if self.lamp_type != 'AREA' else '', rpt_('radius mode'))) +
            '{}: {}, '
            '{}: {} ({}), '
            '{}{}{}{}: {} ({}), '
            '{}: {} ({}), '
            '{}: {} ({}), '
            '{}: {} ({}), '
            '{}: {} ({})'
        ).format(
            UCS['POWER_MODE'], rpt_('power mode'),
            UCS['RELATIVE_POWER_TOGGLE'], rpt_('relative power'), 'ON' if self.is_power_relative else 'OFF',
            UCS['AXIS_X'], UCS['AXIS_Y'], UCS['AXIS_Z'], UCS['AXIS_REFLECT'], rpt_('axis'), self.axis,
            UCS['VISIBILITY_TOGGLE_CAMERA'], rpt_('Camera'), 'ON' if self.visible_camera else 'OFF',
            UCS['VISIBILITY_TOGGLE_DIFFUSE'], rpt_('Diffuse'), 'ON' if self.visible_diffuse else 'OFF',
            UCS['VISIBILITY_TOGGLE_SPECULAR'], rpt_('Specular'), 'ON' if self.visible_specular else 'OFF',
            UCS['VISIBILITY_TOGGLE_VOLUME'],  rpt_('Volume'),'ON' if self.visible_volume else 'OFF',
        )

    def extra_paint_controls(self, context, event):
        mouse_x = event.mouse_x

        if is_event_command(event, 'TYPE_TOGGLE'):
            next_index = (LAMP_TYPES_ORDER.index(self.lamp_type) + 1) % len(LAMP_TYPES_ORDER)
            self.lamp_type = LAMP_TYPES_ORDER[next_index]

        elif is_event_command(event, 'OFFSET_MODE'):
            self.set_drag_attr('offset', mouse_x)

        elif is_event_command(event, 'SIZE_MODE') and self.lamp_type != 'AREA':
            self.set_drag_attr('radius', mouse_x, drag_increment=0.01, drag_precise_increment=0.001)

        elif is_event_command(event, 'POWER_MODE'):
            self.set_drag_attr('power', mouse_x, drag_increment=10, drag_precise_increment=1)
        elif is_event_command(event, 'RELATIVE_POWER_TOGGLE'):
            self.is_power_relative = not self.is_power_relative

        elif self.check_axis_event(event):
            pass  # if True, event is handled
        elif self.check_visibility_event(event):
            pass  # if True, event is handled

        else:
            return False

        return True

    def update_light(self, context):
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
        lamp_obj = context.active_object
        lamp_obj.data.type = lamp_type

        lamp_update_funcs = {
            'AREA': self.update_area_lamp,
            'SPOT': lambda spot_lamp, stroke: self.update_spot_lamp(spot_lamp, orig_vertices, stroke),
            'POINT': self.update_point_lamp,
        }

        try:
            lamp_update_funcs[lamp_type](lamp_obj, (vertices, normals))
        except ValueError as e:
            self.report({'ERROR'}, str(e))
            return {'CANCELLED'}

        return {'FINISHED'}

    def startup_callback(self, context):
        bpy.ops.object.light_add(type=self.lamp_type, align='WORLD')

        lamp_obj = context.active_object
        lamp_obj.data.color = self.light_color

    def cancel_callback(self, context):
        """Deletes active object (our new lamp)."""
        bpy.data.objects.remove(context.active_object, do_unlink=True)
