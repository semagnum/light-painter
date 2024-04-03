from math import atan, atan2, pi, radians, sqrt

import bpy
from mathutils import Vector

from .base_tool import BaseLightPaintTool
from .lamp_util import get_average_normal, get_occlusion_based_normal, PI_OVER_2
from .prop_util import axis_prop, convert_val_to_unit_str, get_drag_mode_header
from .visibility import VisibilitySettings
from ..axis import prep_stroke
from ..keymap import is_event_command, UNIVERSAL_COMMAND_STR as UCS

if bpy.app.version >= (4, 1):
    from bpy.app.translations import pgettext_rpt as rpt_
else:
    from bpy.app.translations import pgettext_tip as rpt_

WORLD_DATA_NAME = 'Light Painter World'


class LIGHTPAINTER_OT_Sky(bpy.types.Operator, BaseLightPaintTool, VisibilitySettings):
    bl_idname = 'lightpainter.sky'
    bl_label = 'Paint Sky'
    bl_description = 'Rotates world sky texture to light surfaces specified by annotations'

    tool_id = 'view3d.lightpaint_sky'

    axis: axis_prop('sky')

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

    texture_type: bpy.props.EnumProperty(
        name='Sky Model',
        description='Model used by sky texture node',
        items=(
            ('NISHITA', 'Nishita', ''),
            ('PREETHAM', 'Preetham', ''),
        ),
        default='NISHITA'
    )

    size: bpy.props.FloatProperty(
        name='Sun size',
        description='Angular size of the sun',
        min=0.0,
        max=pi,
        default=0.009512,
        step=10,
        subtype='ANGLE'
    )

    power: bpy.props.FloatProperty(
        name='Power',
        description='Sun light\'s intensity',
        min=0.001,
        default=1,
    )

    def draw(self, _context):
        layout = self.layout
        layout.prop(self, 'axis')
        layout.prop(self, 'size')
        layout.prop(self, 'power')

        layout.separator()

        layout.label(text='Sky Texture Model:')
        row = layout.row()
        row.prop(self, 'texture_type', expand=True)

        layout.separator()

        layout.label(text='Method:')
        row = layout.row()
        row.prop(self, 'normal_method', expand=True)

        col = layout.column()
        col.active = self.normal_method == 'OCCLUSION'
        col.prop(self, 'longitude_samples')
        col.prop(self, 'latitude_samples')
        col.prop(self, 'elevation_clamp', slider=True)

        layout.separator()

        self.draw_visibility_props(layout)

    def extra_paint_controls(self, context, event):
        mouse_x = event.mouse_x

        if is_event_command(event, 'TYPE_TOGGLE'):
            self.texture_type = 'NISHITA' if self.texture_type == 'PREETHAM' else 'PREETHAM'

        elif is_event_command(event, 'SIZE_MODE'):
            self.set_drag_attr('size', mouse_x, drag_increment=0.01, drag_precise_increment=0.001)

        elif is_event_command(event, 'POWER_MODE'):
            self.set_drag_attr('power', mouse_x)

        elif self.check_axis_event(event):
            pass  # if True, Event is handled
        elif self.check_visibility_event(event):
            pass  # if True, event is handled
        else:
            return False

        return True

    # def get_header_text(self):
    #     if self.drag_attr == 'size':
    #         return 'Sun size: {}'.format(
    #             convert_val_to_unit_str(self.size, 'ROTATION')
    #         ) + get_drag_mode_header()
    #     elif self.drag_attr == 'power':
    #         return 'Power: {}'.format(self.power) + get_drag_mode_header()

    #     return super().get_header_text() + (
    #         '{}: radius mode, '
    #         '{}: power mode, '
    #         '{}{}{}{}: axis ({}), '
    #         '{}: Camera ({}), '
    #         '{}: Diffuse ({}), '
    #         '{}: Specular ({}), '
    #         '{}: Volume ({})'
    #     ).format(
    #         UCS['SIZE_MODE'],
    #         UCS['POWER_MODE'],
    #         UCS['AXIS_X'], UCS['AXIS_Y'], UCS['AXIS_Z'], UCS['AXIS_REFLECT'], self.axis,
    #         UCS['VISIBILITY_TOGGLE_CAMERA'], 'ON' if self.visible_camera else 'OFF',
    #         UCS['VISIBILITY_TOGGLE_DIFFUSE'], 'ON' if self.visible_diffuse else 'OFF',
    #         UCS['VISIBILITY_TOGGLE_SPECULAR'], 'ON' if self.visible_specular else 'OFF',
    #         UCS['VISIBILITY_TOGGLE_VOLUME'], 'ON' if self.visible_volume else 'OFF',
    #     )

    def get_header_text(self):
        if self.drag_attr == 'size':
            return '{}: {}'.format(rpt_('Sun size'),
                convert_val_to_unit_str(self.size, 'ROTATION')
            ) + get_drag_mode_header()
        elif self.drag_attr == 'power':
            return '{}: {}'.format(rpt_('Power: {}'),self.power) + get_drag_mode_header()

        return super().get_header_text() + (
            '{}: {}, '
            '{}: {}, '
            '{}{}{}{}: {} ({}), '
            '{}: {} ({}), '
            '{}: {} ({}), '
            '{}: {} ({}), '
            '{}: {} ({})'
        ).format(
            UCS['SIZE_MODE'], rpt_('radius mode'),
            UCS['POWER_MODE'], rpt_('power mode'),
            UCS['AXIS_X'], UCS['AXIS_Y'], UCS['AXIS_Z'], UCS['AXIS_REFLECT'],rpt_('axis'), self.axis,
            UCS['VISIBILITY_TOGGLE_CAMERA'],rpt_('Camera'), 'ON' if self.visible_camera else 'OFF',
            UCS['VISIBILITY_TOGGLE_DIFFUSE'],rpt_('Diffuse'), 'ON' if self.visible_diffuse else 'OFF',
            UCS['VISIBILITY_TOGGLE_SPECULAR'],rpt_('Specular'), 'ON' if self.visible_specular else 'OFF',
            UCS['VISIBILITY_TOGGLE_VOLUME'],rpt_('Volume'), 'ON' if self.visible_volume else 'OFF',
        )


    def paint_sky_texture(self, context, sun_normal):
        bpy_data = context.blend_data

        if WORLD_DATA_NAME not in bpy_data.worlds:
            new_world = bpy_data.worlds.new(WORLD_DATA_NAME)
            context.scene.world = new_world
            new_world.use_nodes = True
            world_node_tree = new_world.node_tree

            # add sky texture node, connect to background node
            background_node = world_node_tree.nodes['Background']
            sky_node = world_node_tree.nodes.new('ShaderNodeTexSky')
            world_node_tree.links.new(sky_node.outputs[0], background_node.inputs[0])
        else:
            existing_world = bpy_data.worlds[WORLD_DATA_NAME]
            context.scene.world = existing_world
            world_node_tree = existing_world.node_tree

            sky_node = world_node_tree.nodes['Sky Texture']

        # add data for sky texture
        # set sky type based on render engine
        texture_type = self.texture_type
        sky_node.sky_type = texture_type
        if texture_type == 'NISHITA':
            x, y, z = sun_normal
            if z == 0:  # prevent division by zero
                z = 0.0001
            sky_node.sun_elevation = atan((sqrt(x * x + y * y)) / z) + (pi * 0.5)
            sky_node.sun_rotation = atan2(x, y) + pi
        elif texture_type == 'PREETHAM':
            sky_node.sun_direction = sun_normal  # vector pointing towards sun

        sky_node.sun_size = self.size
        sky_node.sun_intensity = self.power

        world_data = context.scene.world.cycles_visibility
        world_data.camera = self.visible_camera
        world_data.diffuse = self.visible_diffuse
        world_data.glossy = self.visible_specular
        world_data.scatter = self.visible_volume

    def update_light(self, context):
        stroke_vertices = [coord for stroke in self.mouse_path for coord, normal in stroke]
        stroke_normals = [normal for stroke in self.mouse_path for coord, normal in stroke]
        vertices, normals, _ = prep_stroke(
            context, stroke_vertices, stroke_normals,
            self.axis, 0.0
        )

        # skip if no strokes are currently drawn
        if len(stroke_vertices) == 0:
            return {'CANCELLED'}

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

        self.paint_sky_texture(context, sun_normal)

        return {'FINISHED'}

    def startup_callback(self, context):
        new_world = context.blend_data.worlds.new(WORLD_DATA_NAME)
        self.prev_world = context.scene.world
        context.scene.world = new_world
        new_world.use_nodes = True
        world_node_tree = new_world.node_tree

        # add sky texture node, connect to background node
        background_node = world_node_tree.nodes['Background']
        sky_node = world_node_tree.nodes.new('ShaderNodeTexSky')
        world_node_tree.links.new(sky_node.outputs[0], background_node.inputs[0])

    def cancel_callback(self, context):
        """Delete any added sky or sun datablocks."""
        bpy.data.worlds.remove(context.scene.world)
        if self.prev_world:
            context.scene.world = self.prev_world


class LIGHTPAINTER_OT_Sun(bpy.types.Operator, BaseLightPaintTool, VisibilitySettings):
    bl_idname = 'lightpainter.sun'
    bl_label = 'Paint Sun'
    bl_description = 'Adds sun lamp to light surfaces specified by annotations'

    tool_id = 'view3d.lightpaint_sun'

    axis: axis_prop('sun')

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

    # SUN
    light_color: bpy.props.FloatVectorProperty(
        name='Color',
        size=3,
        default=(1.0, 1.0, 1.0),
        min=0.0,
        soft_max=1.0,
        subtype='COLOR'
    )

    power: bpy.props.FloatProperty(
        name='Power',
        description='Sun light\'s emit value',
        min=0.001,
        default=1,
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

    def draw(self, _context):
        layout = self.layout
        layout.prop(self, 'axis')
        layout.prop(self, 'light_color')
        layout.prop(self, 'power')
        layout.prop(self, 'angle')

        layout.separator()

        layout.label(text='Method:')
        row = layout.row()
        row.prop(self, 'normal_method', expand=True)

        col = layout.column()
        col.active = self.normal_method == 'OCCLUSION'
        col.prop(self, 'longitude_samples')
        col.prop(self, 'latitude_samples')
        col.prop(self, 'elevation_clamp', slider=True)

        layout.separator()

        self.draw_visibility_props(layout)

    def extra_paint_controls(self, context, event):
        mouse_x = event.mouse_x

        if is_event_command(event, 'SIZE_MODE'):
            self.set_drag_attr('angle', mouse_x, drag_increment=0.01, drag_precise_increment=0.001)

        elif is_event_command(event, 'POWER_MODE'):
            self.set_drag_attr('power', mouse_x, drag_increment=1, drag_precise_increment=0.1)

        elif self.check_axis_event(event):
            pass  # if True, event is handled
        elif self.check_visibility_event(event):
            pass  # if True, event is handled

        else:
            return False

        return True

    # def get_header_text(self):
    #     if self.drag_attr == 'angle':
    #         return 'Sun lamp radius: {}'.format(
    #             convert_val_to_unit_str(self.angle, 'ROTATION')
    #         ) + get_drag_mode_header()
    #     elif self.drag_attr == 'power':
    #         return 'Power: {}'.format(self.power) + get_drag_mode_header()

    #     return super().get_header_text() + (
    #         '{}: sun radius mode, '
    #         '{}: power mode, '
    #         '{}{}{}{}: axis ({}), '
    #         '{}: Camera ({}), '
    #         '{}: Diffuse ({}), '
    #         '{}: Specular ({}), '
    #         '{}: Volume ({})'
    #     ).format(
    #         UCS['SIZE_MODE'],
    #         UCS['POWER_MODE'],
    #         UCS['AXIS_X'], UCS['AXIS_Y'], UCS['AXIS_Z'], UCS['AXIS_REFLECT'], self.axis,
    #         UCS['VISIBILITY_TOGGLE_CAMERA'], 'ON' if self.visible_camera else 'OFF',
    #         UCS['VISIBILITY_TOGGLE_DIFFUSE'], 'ON' if self.visible_diffuse else 'OFF',
    #         UCS['VISIBILITY_TOGGLE_SPECULAR'], 'ON' if self.visible_specular else 'OFF',
    #         UCS['VISIBILITY_TOGGLE_VOLUME'], 'ON' if self.visible_volume else 'OFF',
    #     )

    def get_header_text(self):
        if self.drag_attr == 'angle':
            return '{}: {}'.format(rpt_('Sun lamp radius'),
                convert_val_to_unit_str(self.angle, 'ROTATION')
            ) + get_drag_mode_header()
        elif self.drag_attr == 'power':
            return '{}: {}'.format(rpt_('Power'),self.power) + get_drag_mode_header()

        return super().get_header_text() + (
            '{}: {}, '
            '{}: {}, '
            '{}{}{}{}: {} ({}), '
            '{}: {} ({}), '
            '{}: {} ({}), '
            '{}: {} ({}), '
            '{}: {} ({})'
        ).format(
            UCS['SIZE_MODE'], rpt_('sun radius mode'),
            UCS['POWER_MODE'], rpt_('power mode'),
            UCS['AXIS_X'], UCS['AXIS_Y'], UCS['AXIS_Z'], UCS['AXIS_REFLECT'],rpt_('axis'), self.axis,
            UCS['VISIBILITY_TOGGLE_CAMERA'],rpt_('Camera'), 'ON' if self.visible_camera else 'OFF',
            UCS['VISIBILITY_TOGGLE_DIFFUSE'],rpt_('Diffuse'), 'ON' if self.visible_diffuse else 'OFF',
            UCS['VISIBILITY_TOGGLE_SPECULAR'],rpt_('Specular'), 'ON' if self.visible_specular else 'OFF',
            UCS['VISIBILITY_TOGGLE_VOLUME'],rpt_('Volume'), 'ON' if self.visible_volume else 'OFF',
        )


    def update_light(self, context):
        stroke_vertices = [coord for stroke in self.mouse_path for coord, normal in stroke]
        stroke_normals = [normal for stroke in self.mouse_path for coord, normal in stroke]
        vertices, normals, _ = prep_stroke(
            context, stroke_vertices, stroke_normals,
            self.axis, 0.0
        )

        # skip if no strokes are currently drawn
        if len(stroke_vertices) == 0:
            return {'CANCELLED'}

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

        # rotation difference
        rotation = Vector((0.0, 0.0, -1.0)).rotation_difference(sun_normal).to_euler()
        center = context.scene.cursor.location

        if not context.active_object or context.active_object.type != 'LIGHT' or context.active_object.data.type != 'SUN':
            bpy.ops.object.light_add(type='SUN', align='WORLD', location=center, rotation=rotation, scale=(1, 1, 1))

        lamp = context.active_object

        # Sun only rotates, no location change
        lamp.rotation_euler = rotation

        # set light data properties
        lamp.data.energy = self.power
        lamp.data.angle = self.angle
        self.set_visibility(lamp)

        return {'FINISHED'}

    def startup_callback(self, context):
        center = context.scene.cursor.location
        bpy.ops.object.light_add(type='SUN', align='WORLD', location=center, scale=(1, 1, 1))

        lamp = context.active_object
        lamp.data.color = self.light_color

    def cancel_callback(self, context):
        """Delete added sun object."""
        with context.temp_override(selected_objects=[context.active_object]):
            bpy.ops.object.delete(use_global=False)
