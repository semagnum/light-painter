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
from math import pi, radians
from mathutils import Vector

from .prop_util import axis_prop
from ..axis import prep_stroke
from .base_tool import BaseLightPaintTool
from .lamp_util import get_average_normal, get_occlusion_based_normal, LampUtils, PI_OVER_2


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

    @classmethod
    def poll(cls, context):
        active_obj = context.active_object
        return active_obj is not None and active_obj.type == 'LIGHT'

    def draw(self, context):
        layout = self.layout
        layout.prop(self, 'axis')
        layout.prop(self, 'offset')

        layout.separator()

        lamp_type = context.active_object.data.type

        if lamp_type == 'SUN':
            layout.label(text='Method:')
            row = layout.row()
            row.prop(self, 'normal_method', expand=True)

            col = layout.column()
            col.active = self.normal_method == 'OCCLUSION'
            col.prop(self, 'longitude_samples')
            col.prop(self, 'latitude_samples')
            layout.prop(self, 'elevation_clamp', slider=True)

            layout.separator()

            layout.prop(self, 'light_color')
            layout.prop(self, 'sun_power')
            layout.prop(self, 'angle')
        else:
            if lamp_type == 'AREA':
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

    def mouse_update(self, context):
        """Callback right after a left or right mouse click release."""
        self.execute(context)

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
        lamp.data.color = self.light_color
        lamp.data.energy = self.sun_power
        lamp.data.angle = self.angle
        self.set_visibility(lamp)

    def execute(self, context):
        super().execute(context)

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

        Sets light color and power, sun's power and angle, area's shape, and radius."""
        lamp_data = context.active_object.data
        lamp_type = lamp_data.type

        self.light_color = lamp_data.color
        self.power = lamp_data.energy

        if lamp_type == 'SUN':
            self.sun_power = lamp_data.energy
            self.angle = lamp_data.angle
        elif lamp_type == 'AREA':
            self.shape = lamp_data.shape
        else:
            self.radius = lamp_data.shadow_soft_size

        return super().invoke(context, event)
