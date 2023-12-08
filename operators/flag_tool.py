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

import math

import bpy
from mathutils import Vector

from .base_tool import BaseLightPaintTool
from .prop_util import convert_val_to_unit_str, get_drag_mode_header
from .visibility import VisibilitySettings
from ..keymap import is_event_command, UNIVERSAL_COMMAND_STR

IS_BPY_V3 = bpy.app.version < (4, 0, 0)

FLAG_DATA_NAME = 'LightPaint_Flag'


# active object is counted twice
def get_selected_by_type(context, obj_type: str) -> tuple:
    """Retrieves all selected lights, including the active object.
    Prevents duplicates if the active object is also selected.

    :param context: Blender context
    :param obj_type: Blender object type
    :return: a generator of selected objects
    """
    light_objs_dict = {obj.name: obj for obj in context.selected_objects if obj.type == obj_type}
    if context.active_object and context.active_object.type == obj_type:
        light_objs_dict.update({context.active_object.name: context.active_object})

    return tuple(light_objs_dict.values())


def assign_flag_material(obj, color, opacity):
    """Assigns a shadow flag material to a given object.

    :param obj: object to assign th material.
    :param color: shader's surface color (1.0, 1.0, 1.0).
    :param opacity: shader's opacity
    """
    material = bpy.data.materials.new(name=FLAG_DATA_NAME)

    material.use_nodes = True
    tree = material.node_tree

    # find PBR and set color
    pbr_node = tree.nodes['Principled BSDF']
    pbr_node.inputs[0].default_value = color
    if IS_BPY_V3:
        pbr_node.inputs[21].default_value = opacity
    else:
        pbr_node.inputs[4].default_value = opacity

    material.blend_method = 'BLEND'
    material.shadow_method = 'HASHED'

    # Assign the new material.
    obj.data.materials.append(material)


def get_light_points(light_obj) -> list[Vector]:
    """Returns a list of points

    :param light_obj: object with light data
    :return: list of points
    """
    light_type = light_obj.data.type
    # if area, add all four corners
    if light_type == 'AREA':
        # rectangles and ellipses measure by length and width, the rest measure by area
        if light_obj.data.shape in ('RECTANGLE', 'ELLIPSE'):
            size_x = light_obj.data.size / 2
            size_y = light_obj.data.size_y / 2
        else:
            side_len = light_obj.data.size / 2
            size_x, size_y = side_len, side_len

        corners = [Vector((x, y, 0))
                   for x in (size_x, size_x * -1)
                   for y in (size_y, size_y * -1)]
        return [light_obj.matrix_world @ v for v in corners]
    return [light_obj.location]


class LIGHTPAINTER_OT_Flag(bpy.types.Operator, BaseLightPaintTool, VisibilitySettings):
    bl_idname = 'lightpainter.flag'
    bl_label = 'Paint Flag'
    bl_description = 'Adds mesh flag(s) to shadow surfaces specified by selected lights and annotations'

    tool_id = 'view3d.lightpaint_flag'

    # FLAG PROPERTIES
    factor: bpy.props.FloatProperty(
        name='Factor',
        description='Position between light and surface (0 is at the light, 1 is at the surface)',
        min=0.0001,
        max=1.0,
        default=0.5,
        subtype='FACTOR',
    )

    offset: bpy.props.FloatProperty(
        name='Offset',
        description='Sun lamp\'s offset from annotation(s) along specified axis',
        default=1.0,
        unit='LENGTH',
    )

    shadow_color: bpy.props.FloatVectorProperty(
        name='Color',
        description='Material color of the flag',
        size=4,
        default=[0.5, 0.5, 0.5, 1.0],
        min=0.0,
        soft_max=1.0,
        subtype='COLOR',
    )

    opacity: bpy.props.FloatProperty(
        name='Opacity',
        description='Material transparency of the flag',
        default=1.0,
        min=0.0,
        max=1.0,
    )

    @classmethod
    def poll(cls, context):
        return len(get_selected_by_type(context, 'LIGHT'))

    def draw(self, context):
        layout = self.layout

        light_objs = get_selected_by_type(context, 'LIGHT')
        has_sun = any(obj.data.type == 'SUN' for obj in light_objs)
        has_other_lamps = any(obj.data.type != 'SUN' for obj in light_objs)
        if has_sun:
            layout.prop(self, 'offset')
        if has_other_lamps:
            layout.prop(self, 'factor')

        layout.prop(self, 'shadow_color')
        layout.prop(self, 'opacity', slider=True)

        self.draw_visibility_props(layout)

    def extra_paint_controls(self, context, event):
        mouse_x = event.mouse_x

        # offset is for sun lamps, size is factor for the rest.
        if is_event_command(event, 'OFFSET_MODE'):
            self.set_drag_attr('offset', mouse_x)

        elif is_event_command(event, 'SIZE_MODE'):
            self.set_drag_attr('factor', mouse_x, drag_increment=0.05, drag_precise_increment=0.01)

        elif is_event_command(event, 'POWER_MODE'):
            self.set_drag_attr('opacity', mouse_x, drag_increment=0.05, drag_precise_increment=0.01)
       
        elif self.check_visibility_event(event):
            pass  # if True, event is handled

        else:
            return False

        return True

    def get_header_text(self):
        if self.drag_attr == 'factor':
            return 'Factor: {}'.format(self.factor) + get_drag_mode_header()
        elif self.drag_attr == 'offset':
            return 'Offset (for sun lamps): {}'.format(
                convert_val_to_unit_str(self.offset, 'LENGTH')
            ) + get_drag_mode_header()
        elif self.drag_attr == 'opacity':
            return 'Opacity: {}'.format(self.opacity) + get_drag_mode_header()

        return super().get_header_text() + (
            '{}: lamp factor mode, '
            '{}: sun lamp offset mode, '
            '{}: opacity mode, '
            '{}: Camera ({}), '
            '{}: Diffuse ({}), '
            '{}: Specular ({}), '
            '{}: Volume ({})'
        ).format(
            UNIVERSAL_COMMAND_STR['SIZE_MODE'],
            UNIVERSAL_COMMAND_STR['OFFSET_MODE'],
            UNIVERSAL_COMMAND_STR['POWER_MODE'],
            UNIVERSAL_COMMAND_STR['VISIBILITY_TOGGLE_CAMERA'], 'ON' if self.visible_camera else 'OFF',
            UNIVERSAL_COMMAND_STR['VISIBILITY_TOGGLE_DIFFUSE'], 'ON' if self.visible_diffuse else 'OFF',
            UNIVERSAL_COMMAND_STR['VISIBILITY_TOGGLE_SPECULAR'], 'ON' if self.visible_specular else 'OFF',
            UNIVERSAL_COMMAND_STR['VISIBILITY_TOGGLE_VOLUME'], 'ON' if self.visible_volume else 'OFF',
        )

    def add_card_for_lamp(self, context, mesh_obj, light_obj, vertices):
        mesh = mesh_obj.data
        mesh.clear_geometry()

        if light_obj.data.type == 'SUN':
            direction = (light_obj.matrix_world.to_3x3() @ Vector((0, 0, -1))).normalized()
            direction.negate()
            mesh_vertices = tuple(v + direction * self.offset
                                  for v in vertices)
        else:
            factor = self.factor
            if math.isclose(factor, 1.0):
                mesh_vertices = vertices
            else:
                mesh_vertices = tuple(light_v + (v - light_v) * factor
                                      for v in vertices
                                      for light_v in get_light_points(light_obj))

        mesh.from_pydata(mesh_vertices, [], [])

        # go into edit mode, convex hull, then get out
        context.view_layer.objects.active = mesh_obj
        bpy.ops.object.editmode_toggle()
        bpy.ops.mesh.convex_hull()
        bpy.ops.object.editmode_toggle()

        self.set_visibility(mesh_obj)

        material = mesh_obj.data.materials[0]
        tree = material.node_tree

        # find PBR and set color
        pbr_node = tree.nodes['Principled BSDF']
        if IS_BPY_V3:
            pbr_node.inputs[21].default_value = self.opacity
        else:
            pbr_node.inputs[4].default_value = self.opacity

    def update_light(self, context):
        light_objs = get_selected_by_type(context, 'LIGHT')
        mesh_objs = get_selected_by_type(context, 'MESH')
        if len(light_objs) == 0:
            self.report({'ERROR_INVALID_INPUT'}, 'Select lamp objects to be flagged for shadows!')
            return {'CANCELLED'}

        vertices = [coord for stroke in self.mouse_path for coord, normal in stroke]

        # skip if no strokes are currently drawn
        if len(vertices) == 0:
            return {'CANCELLED'}

        # add new mesh
        for mesh_obj, light_obj in zip(mesh_objs, light_objs):
            self.add_card_for_lamp(context, mesh_obj, light_obj, vertices)

        # select them so the panel can detect them correctly
        for light_obj in light_objs:
            light_obj.select_set(True)

        return {'FINISHED'}

    def startup_callback(self, context):
        # unselect any currently selected meshes,
        # to prevent them accidentally being deleted if modal cancels
        for mesh_obj in get_selected_by_type(context, 'MESH'):
            mesh_obj.select_set(False)

        for _ in get_selected_by_type(context, 'LIGHT'):
            mesh = bpy.data.meshes.new(FLAG_DATA_NAME)
            obj = bpy.data.objects.new(mesh.name, mesh)
            col = context.scene.collection
            col.objects.link(obj)
            obj.select_set(True)

            # To prevent an originally selected mesh from being still active,
            # make the others active (could just pick a light too)
            context.view_layer.objects.active = obj

            assign_flag_material(obj, self.shadow_color, self.opacity)

    def cancel_callback(self, context):
        """Deletes active object (our new lamp)."""
        if self.initialized:
            with context.temp_override(selected_objects=get_selected_by_type(context, 'MESH')):
                bpy.ops.object.delete(use_global=False)
