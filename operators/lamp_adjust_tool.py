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

from math import pi, radians

import bpy
from mathutils import Vector

from .base_tool import BaseLightPaintTool
from ..keymap import get_kmi_str, is_event_command
from .lamp_util import get_average_normal, get_occlusion_based_normal, LampUtils, PI_OVER_2
from .prop_util import axis_prop, convert_val_to_unit_str, get_drag_mode_header
from ..axis import prep_stroke
if bpy.app.version >= (4, 1):
    from bpy.app.translations import pgettext_rpt as rpt_
else:
    from bpy.app.translations import pgettext_tip as rpt_


class LIGHTPAINTER_OT_Lamp_Adjust(bpy.types.Operator, BaseLightPaintTool, LampUtils):
    bl_idname = 'lightpainter.lamp_adjust'
    bl_label = 'Adjust Lamp'
    bl_description = 'Adjusts active lamp\'s position and rotation to light surfaces specified by annotations'

    tool_id = 'view3d.lightpaint_lamp_adjust'

    axis: axis_prop('lamp')

    # SUN ONLY METHODS

    normal_method: bpy.props.EnumProperty(
        name='Method',
        description='Method to determine sun direction',
        items=(
            ('AVERAGE', 'Average', 'Uses average of normals'),
            ('OCCLUSION', 'Occlusion', 'Casts rays to determine occlusion and optimal direction for visibility'),
        ),
        default='OCCLUSION'
    )

    longitude_samples: bpy.props.IntProperty(
        name='Azimuth Samples',
        description='Samples of normals around the azimuth. '
                    'Increasing samples improves precision at the cost of processing time',
        min=4,
        default=6,
    )

    latitude_samples: bpy.props.IntProperty(
        name='Elevation Samples',
        description='Samples of normals from the horizon to the maximum elevation. '
                    'Increasing samples improves precision at the cost of processing time',
        min=3,
        default=6,
    )

    elevation_clamp: bpy.props.FloatProperty(
        name='Max Sun Elevation',
        description='Tested normals will be scaled to at most this elevation.'
                    'Forces the sun closer to the horizon, allowing more dynamic lighting.',
        min=0.0, soft_min=0.0,
        max=PI_OVER_2, soft_max=PI_OVER_2,
        default=radians(60),
        step=10,
        subtype='ANGLE'
    )

    angle: bpy.props.FloatProperty(
        name='Angle',
        description='Angular diameter of the Sun as seen from the Earth',
        min=0.0,
        max=pi,
        default=0.00918043,
        step=10,
        subtype='ANGLE'
    )

    sun_power: bpy.props.FloatProperty(
        name='Power',
        description='Sun lamp\'s emit value',
        min=0.001,
        default=5,
    )

    def __init__(self, *args, **kwargs):
        bpy.types.Operator.__init__(self, *args, **kwargs)
        BaseLightPaintTool.__init__(self)

    @classmethod
    def poll(cls, context):
        active_obj = context.active_object
        return active_obj is not None and active_obj.type == 'LIGHT'

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False  # No animation

        lamp_type = context.active_object.data.type

        if lamp_type == 'SUN':
            layout.prop(self, 'normal_method', expand=True)

            col = layout.column()
            col.active = self.normal_method == 'OCCLUSION'
            col.prop(self, 'longitude_samples')
            col.prop(self, 'latitude_samples')
            layout.prop(self, 'elevation_clamp', slider=True)

            layout.separator()

            col = layout.column(align=True)
            col.prop(self, 'axis')
            col.prop(self, 'offset', text='Amount')

            layout.separator()

            layout.prop(self, 'light_color')
            layout.prop(self, 'sun_power')
            layout.prop(self, 'angle')
        else:
            if lamp_type == 'AREA':
                layout.prop(self, 'shape')
                layout.prop(self, 'min_size')
                layout.prop(self, 'spread')
            elif lamp_type == 'SPOT':
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

    def adjust_sun_lamp(self, context, lamp, stroke):
        vertices, normals = stroke

        try:
            avg_normal = get_average_normal(normals)
        except ValueError as e:
            self.report({'ERROR'}, str(e))
            return {'CANCELLED'}

        if self.normal_method == 'OCCLUSION':
            try:
                sun_normal = get_occlusion_based_normal(
                    context, vertices, avg_normal,
                    self.elevation_clamp, self.latitude_samples, self.longitude_samples
                )
            except ValueError:
                self.report({'ERROR'}, 'No valid directions found '
                                       '(add more samples or increase the elevation clamp!), using average normal')
                sun_normal = Vector(avg_normal)
        else:
            sun_normal = Vector(avg_normal)

        sun_normal.negate()

        # Sun only rotates, no location change
        rotation = Vector((0.0, 0.0, -1.0)).rotation_difference(sun_normal).to_euler()
        lamp.rotation_euler = rotation

        # set light data properties
        lamp.data.energy = self.sun_power
        lamp.data.angle = self.angle
        self.set_visibility(lamp)


    def get_header_text(self):
        if self.drag_attr == 'offset':
            return '{}: {}'.format(rpt_('Offset'),
                convert_val_to_unit_str(self.offset, 'LENGTH')
            ) + get_drag_mode_header()
        elif self.drag_attr == 'radius':
            return '{}: {}'.format(rpt_('Lamp radius'),
                convert_val_to_unit_str(self.radius, 'LENGTH')
            ) + get_drag_mode_header()
        elif self.drag_attr == 'power':
            return '{}: {}{}'.format(rpt_('Power'),
                convert_val_to_unit_str(self.power, 'POWER'),
                ' (relative)' if self.is_power_relative else ''
            ) + get_drag_mode_header()

        return super().get_header_text() + (
            '{}: {}, '.format(get_kmi_str('OFFSET_MODE'), rpt_('offset mode'),) +
            ('{}: {}, '.format((get_kmi_str('SIZE_MODE')), rpt_('radius mode')) if bpy.context.active_object.data.type != 'AREA' else '') +
            '{}: {}, '
            '{}: {} ({}), '
            '{}{}{}{}: {}axis ({}), '
            '{}: {} ({}), '
            '{}: {} ({}), '
            '{}: {} ({}), '
            '{}: {} ({})'
        ).format(
            get_kmi_str('POWER_MODE'), rpt_('power mode'),
            get_kmi_str('RELATIVE_POWER_TOGGLE'), rpt_('relative power'),'ON' if self.is_power_relative else 'OFF',
            get_kmi_str('AXIS_X'), get_kmi_str('AXIS_Y'), get_kmi_str('AXIS_Z'), get_kmi_str('AXIS_REFLECT'), rpt_('axis'), self.axis,
            get_kmi_str('VISIBILITY_TOGGLE_CAMERA'), rpt_('Camera'), 'ON' if self.visible_camera else 'OFF',
            get_kmi_str('VISIBILITY_TOGGLE_DIFFUSE'), rpt_('Diffuse'), 'ON' if self.visible_diffuse else 'OFF',
            get_kmi_str('VISIBILITY_TOGGLE_SPECULAR'), rpt_('Specular'), 'ON' if self.visible_specular else 'OFF',
            get_kmi_str('VISIBILITY_TOGGLE_VOLUME'),  rpt_('Volume'),'ON' if self.visible_volume else 'OFF',
        )

    def extra_paint_controls(self, context, event):
        mouse_x = event.mouse_x

        if is_event_command(event, 'OFFSET_MODE'):
            self.set_drag_attr('offset', mouse_x)

        elif is_event_command(event, 'SIZE_MODE') and context.active_object.data.type != 'AREA':
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

        lamp = context.active_object
        if lamp.type != 'LIGHT':
            self.report({'ERROR_INVALID_INPUT'}, 'Active object is not a lamp, aborting')
            return {'CANCELLED'}
        lamp_type = lamp.data.type

        lamp_update_funcs = {
            'AREA': self.update_area_lamp,
            'SPOT': lambda spot_lamp, stroke: self.update_spot_lamp(spot_lamp, orig_vertices, stroke),
            'POINT': self.update_point_lamp,
            'SUN': lambda sun_lamp, stroke: self.adjust_sun_lamp(context, sun_lamp, stroke),
        }

        try:
            lamp_update_funcs[lamp_type](lamp, (vertices, normals))
        except ValueError as e:
            self.report({'ERROR'}, str(e))
            return {'CANCELLED'}

        return {'FINISHED'}

    def invoke(self, context, event):
        """Use lamp's current parameters as a starting point.

        Sets light power, sun's power and angle, area's shape, and radius."""
        lamp = context.active_object
        lamp_data = lamp.data
        lamp_type = lamp_data.type

        # copied to ensure original value persists
        self.prev_matrix_world = lamp.matrix_world.copy()

        self.power = lamp_data.energy
        self.prev_power = self.power

        if lamp_type == 'SUN':
            self.sun_power = lamp_data.energy
            self.angle = lamp_data.angle

            self.prev_sun_power = self.sun_power
            self.prev_angle = self.angle
        elif lamp_type == 'AREA':
            self.shape = lamp_data.shape
            self.prev_shape = self.shape
            self.prev_size = lamp_data.size
            self.prev_size_y = lamp_data.size_y
        else:
            self.radius = lamp_data.shadow_soft_size
            self.prev_radius = self.radius

        return super().invoke(context, event)

    def cancel_callback(self, context):
        """Resets lamp properties."""
        lamp = context.active_object
        lamp_data = lamp.data
        lamp_type = lamp_data.type

        lamp.matrix_world = self.prev_matrix_world
        lamp_data.energy = self.prev_power

        if lamp_type == 'SUN':
            lamp_data.energy = self.prev_sun_power
            lamp_data.angle = self.prev_angle
        elif lamp_type == 'AREA':
            lamp_data.shape = self.prev_shape
            lamp_data.size = self.prev_size
            lamp_data.size_y = self.prev_size_y
        else:
            lamp_data.shadow_soft_size = self.prev_radius
