import bpy
from math import atan, atan2, pi, radians, sqrt
from mathutils import Vector

from .prop_util import axis_prop
from ..axis import prep_stroke
from .base_tool import BaseLightPaintTool
from .lamp_util import get_occlusion_based_normal, get_average_normal, LampUtils, PI_OVER_2

WORLD_DATA_NAME = 'Light Painter World'


class LIGHTPAINTER_OT_Sky(bpy.types.Operator, BaseLightPaintTool, LampUtils):
    bl_idname = 'lightpainter.sky'
    bl_label = 'Paint Sky'
    bl_description = 'Rotates world sky texture to light surfaces specified by annotations'

    tool_id = 'view3d.lightpaint_sky'

    sky_type: bpy.props.EnumProperty(
        name='Type',
        items=(
            ('SKY', 'Sky Texture', '', 'LIGHT_HEMI', 0),
            ('SUN', 'Sun', '', 'LIGHT_SUN', 1),
        ),
        default='SKY',
    )

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

    # SKY TEXTURE

    texture_type: bpy.props.EnumProperty(
        name='Sky Model',
        description='Model used by sky texture node',
        items=(
            ('NISHITA', 'Nishita', ''),
            ('PREETHAM', 'Preetham', ''),
        ),
        default='NISHITA'
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
        default=5,
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
        row = layout.row()
        row.prop(self, 'sky_type', expand=True)
        layout.prop(self, 'axis')

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

        if self.sky_type == 'SUN':
            layout.prop(self, 'light_color')
            layout.prop(self, 'power')
            layout.prop(self, 'angle')
        elif self.sky_type == 'SKY':
            layout.label(text='Sky Texture Model:')
            row = layout.row()
            row.prop(self, 'texture_type', expand=True)

        layout.separator()

        self.draw_visibility_props(layout)

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

        world_data = context.scene.world.cycles_visibility
        world_data.camera = self.visible_camera
        world_data.diffuse = self.visible_diffuse
        world_data.glossy = self.visible_specular
        world_data.scatter = self.visible_volume

    def execute(self, context):
        super().execute(context)

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

        if self.sky_type == 'SKY':
            self.paint_sky_texture(context, sun_normal)
        elif self.sky_type == 'SUN':
            sun_normal.negate()

            # rotation difference
            rotation = Vector((0.0, 0.0, -1.0)).rotation_difference(sun_normal).to_euler()
            center = context.scene.cursor.location

            bpy.ops.object.light_add(type='SUN', align='WORLD', location=center, rotation=rotation, scale=(1, 1, 1))

            lamp = context.active_object

            # Sun only rotates, no location change
            lamp.rotation_euler = rotation

            # set light data properties
            lamp.data.color = self.light_color
            lamp.data.energy = self.power
            lamp.data.angle = self.angle
            self.set_visibility(lamp)

        return {'FINISHED'}
