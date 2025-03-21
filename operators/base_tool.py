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

from math import floor, log10

import bmesh
import bpy
from bpy_extras import view3d_utils
from mathutils.bvhtree import BVHTree

from .. import __package__ as base_package
from ..keymap import get_kmi_str, is_event_command, get_matching_event, AXIS_KEYMAP, VISIBILITY_KEYMAP, PREFIX
from .draw import draw_callback_px
if bpy.app.version >= (4, 1):
    from bpy.app.translations import pgettext_rpt as rpt_
else:
    from bpy.app.translations import pgettext_tip as rpt_

AXIS_PREFIX_LEN = len('AXIS_')
VISIBILITY_PREFIX_LEN = len('VISIBILITY_TOGGLE_')

ERASER_SIZE_RATE = 10
INCREMENT_VAL = 0.1
PRECISE_INCREMENT_VAL = 0.01
SNAP_INCREMENT_VAL = 1
SNAP_PRECISE_INCREMENT_VAL = 0.1

KEYCONFIGS_CACHE = []


def is_nav_event(keyconfigs: bpy.types.KeyConfig, event: bpy.types.Event) -> bool:
    """Returns True if user event is for 3D viewport navigation, False otherwise.

    :param keyconfigs: Blender keymap configuration.
    :param event: user event (pressing a key, moving the mouse, etc.).
    """
    # initialize cache
    global KEYCONFIGS_CACHE
    if not KEYCONFIGS_CACHE:
        KEYCONFIGS_CACHE = [
            km
            for kc in keyconfigs
            for km in kc.keymaps
            if km is not None and km.name == '3D View'
        ]

    return any(
        km.keymap_items.match_event(event)
        for km in KEYCONFIGS_CACHE
    )


def is_in_area(area, mouse_x, mouse_y):
    """Checks if mouse coordinates are within Blender UI area."""
    return (
            (area.x <= mouse_x <= area.x + area.width) and
            (area.y <= mouse_y <= area.y + area.height)
    )


def get_convex_hit(clip_end, depsgraph, hit_location, hit_normal, hit_obj, ray_origin, view_vector, convex_bvh):
    distance = (hit_location - ray_origin).length

    if hit_obj.name in convex_bvh:
        obj_bvh = convex_bvh[hit_obj.name]
    else:
        obj_bmesh = bmesh.new()
        obj_bmesh.from_mesh(hit_obj.evaluated_get(depsgraph).data)
        bmesh.ops.convex_hull(obj_bmesh, input=obj_bmesh.verts)
        obj_bvh = BVHTree.FromBMesh(obj_bmesh)
        convex_bvh[hit_obj.name] = obj_bvh

    world_matrix = hit_obj.matrix_world
    world_quaternion = world_matrix.to_quaternion()
    local_matrix = world_matrix.inverted()
    world_destination = ray_origin + (view_vector * distance)
    local_origin = local_matrix @ ray_origin
    local_destination = local_matrix @ world_destination
    local_direction = (local_destination - local_origin)

    bvh_location, bvh_normal, _, _ = obj_bvh.ray_cast(local_origin, local_direction, clip_end)

    if bvh_location is not None:
        hit_location = world_matrix @ bvh_location
        hit_normal = bvh_normal
        hit_normal.rotate(world_quaternion)

    return hit_location, hit_normal


class BaseLightPaintTool:
    bl_options = {'REGISTER', 'UNDO'}

    tool_id = ''

    str_mouse_path: bpy.props.StringProperty(options={'HIDDEN'}, default='')

    def __init__(self):
        """Initialize variables to play nicely with pytest usage."""
        self._handle = None

        self.convex_hull = False
        self.convex_bvh = dict()

        self.mouse_path = []
        self.is_painting = False
        self.is_erasing = False
        self.show_eraser = False
        self.curr_mouse_pos = None
        self.eraser_size = 50
        self.area = None

        self.drag_attr = ''
        self.drag_prev_mouse_x = 0
        self.drag_increment = 0.1
        self.drag_precise_increment = 0.01
        self.drag_initial_val = 0

        # this ensures that the first mouse click/keypress (to run the tool) doesn't accidentally add points
        self.initialized = False

    def cancel(self, context):
        bpy.types.SpaceView3D.draw_handler_remove(self._handle, 'WINDOW')
        context.window.cursor_set('DEFAULT')
        context.area.header_text_set(None)
        context.workspace.status_text_set_internal(None)

    def set_drag_attr(self, attr: str, mouse_x,
                      drag_increment: float = INCREMENT_VAL, drag_precise_increment: float = PRECISE_INCREMENT_VAL
                      ):
        """Starts drag mode, setting the attribute and its increment and starting point and values."""
        self.drag_attr = attr
        self.drag_prev_mouse_x = mouse_x
        self.drag_initial_val = getattr(self, attr)
        self.drag_increment = drag_increment
        self.drag_precise_increment = drag_precise_increment

    def cancel_drag_attr(self, reset=False):
        """Cancels drag mode for an attribute, with the option to reset to its initial value."""
        if reset:
            setattr(self, self.drag_attr, self.drag_initial_val)
        self.drag_attr = ''

    def extra_paint_controls(self, _context, _event):
        """Callback for extra controls."""
        return False

    def check_axis_event(self, event) -> bool:
        assert hasattr(self, 'axis')
        axis_command = next(
            (command_name.replace(PREFIX, '')
             for command_name in AXIS_KEYMAP
             if is_event_command(event, command_name))
            , None
        )

        if axis_command is None:
            return False

        axis_pressed = axis_command[AXIS_PREFIX_LEN:]
        self.axis = 'NORMAL' if self.axis == axis_pressed else axis_pressed

        return True

    def check_visibility_event(self, event) -> bool:
        """Checks if Blender event matches our UNIVERSAL_KEYMAP,
        returns the matching command name (if none match, return None).
        """
        matching_visibility_event = next(
            (command_name.replace(PREFIX, '')
             for command_name in VISIBILITY_KEYMAP
             if is_event_command(event, command_name))
            , None
        )

        if matching_visibility_event is None:
            return False

        visibility_pressed = matching_visibility_event[VISIBILITY_PREFIX_LEN:]
        visibility_attr = 'visible_' + visibility_pressed.lower()
        setattr(self, visibility_attr, not getattr(self, visibility_attr))

        return True

    def get_header_text(self):
        return ('{}: {}, '
                '{}: {}, '
                '{}: {}, '
                '{}: {}, '
                '{}: {}, '
                '{}: {} ({}), '
                '{}/{}: {}, ').format(
            get_kmi_str('FINISH'), rpt_('confirm'),
            get_kmi_str('CANCEL'), rpt_('cancel'),
            get_kmi_str('PAINT'), rpt_('paint line'),
            get_kmi_str('ERASE'), rpt_('erase'),
            get_kmi_str('END_STROKE'), rpt_('new stroke'),
            get_kmi_str('CONVEX_HULL_TOGGLE'), rpt_('convex hull'), 'ON' if self.convex_hull else 'OFF',
            get_kmi_str('ERASER_DECREASE'),
            get_kmi_str('ERASER_INCREASE'), rpt_('eraser size'),
        )

    def paint_controls(self, context, event):
        region = context.region
        rv3d = context.region_data

        event_value = event.value
        region_x, region_y = event.mouse_region_x, event.mouse_region_y
        coord = region_x, region_y

        should_update = False
        self.curr_mouse_pos = coord

        if is_event_command(event, 'PAINT'):
            self.is_painting = event_value == 'PRESS'
        elif is_event_command(event, 'ERASE'):
            self.is_erasing = event_value == 'PRESS'
            self.show_eraser = self.is_erasing

        if is_event_command(event, 'END_STROKE'):
            self.mouse_path.append(list())

        if is_event_command(event, 'ERASER_DECREASE'):
            self.eraser_size -= ERASER_SIZE_RATE
            self.show_eraser = True
        elif is_event_command(event, 'ERASER_INCREASE'):
            self.eraser_size += ERASER_SIZE_RATE
            self.show_eraser = True

        if is_event_command(event, 'CONVEX_HULL_TOGGLE'):
            self.convex_hull = not self.convex_hull

        if self.is_erasing:
            context.window.cursor_set('ERASER')
            self.mouse_path = self.erase_from_mouse_path(region, region_x, region_y, rv3d)
            should_update = True
        elif self.is_painting:
            scene = context.scene
            depsgraph = context.evaluated_depsgraph_get()
            clip_end = context.space_data.clip_end

            # get the ray from the viewport and mouse
            view_vector = view3d_utils.region_2d_to_vector_3d(region, rv3d, coord)
            ray_origin = view3d_utils.region_2d_to_origin_3d(region, rv3d, coord)

            is_hit, hit_location, hit_normal, _, hit_obj, _ = scene.ray_cast(depsgraph, ray_origin, view_vector,
                                                                             distance=clip_end)

            if is_hit:
                if self.convex_hull and hit_obj.type == 'MESH':
                    hit_location, hit_normal = get_convex_hit(clip_end, depsgraph,
                                                              hit_location, hit_normal, hit_obj,
                                                              ray_origin, view_vector, self.convex_bvh)
                self.mouse_path[-1].append((hit_location, hit_normal))
                should_update = True

        result = self.extra_paint_controls(context, event)
        should_update = should_update or result

        if should_update:
            try:
                self.update_light(context)
            except ValueError as e:
                self.report({'ERROR'}, str(e))

    def erase_from_mouse_path(self, region, region_x, region_y, rv3d):
        # break paths into potentially new chunks and remove edges erased
        new_mouse_path = [[]]
        eraser_size_squared = self.eraser_size * self.eraser_size
        for idx, path in enumerate(self.mouse_path):
            for coord, normal in path:
                coord_screen_x, coord_screen_y = view3d_utils.location_3d_to_region_2d(region, rv3d, coord)
                dist_x = coord_screen_x - region_x
                dist_y = coord_screen_y - region_y
                distance = dist_x * dist_x + dist_y * dist_y
                if distance > eraser_size_squared:
                    new_mouse_path[-1].append((coord, normal))
                elif len(new_mouse_path[-1]) != 0:
                    new_mouse_path.append(list())

            # preserve original breaks between paths
            if len(new_mouse_path[-1]) != 0 and idx != (len(self.mouse_path) - 1):
                new_mouse_path.append(list())
        return new_mouse_path

    def update_keymap_text(self, context):
        preferences = self.preferences
        if preferences.keymap_header or preferences.keymap_status_bar:
            header_text = self.get_header_text()
            if preferences.keymap_header:
                context.area.header_text_set(header_text)
            if preferences.keymap_status_bar:
                context.workspace.status_text_set_internal(header_text)

    def modal(self, context, event):
        modal_status = 'RUNNING_MODAL'

        if context.workspace.tools.from_space_view3d_mode(context.mode, create=False).idname != self.tool_id:
            modal_status = 'CANCELLED'

        context.area.tag_redraw()

        cursor_type = 'PAINT_BRUSH'
        if self.drag_attr:  # cursor wrapping is handled in handle_drag_event
            cursor_type = 'SCROLL_X'
        elif not is_in_area(context.area, event.mouse_x, event.mouse_y):
            cursor_type = 'DEFAULT'
            modal_status = 'PASS_THROUGH'

        context.window.cursor_set(cursor_type)

        matching_event = get_matching_event(event)
        if matching_event is None and is_nav_event(context.window_manager.keyconfigs, event):
            modal_status = 'PASS_THROUGH'

        if not self.drag_attr:
            if is_event_command(event, 'CANCEL'):
                modal_status = 'CANCELLED'
            elif is_event_command(event, 'FINISH'):
                modal_status = 'FINISHED'
            elif modal_status == 'RUNNING_MODAL':
                self.paint_controls(context, event)
        else:
            self.handle_drag_event(context, event, matching_event)

        self.update_keymap_text(context)

        if modal_status in {'CANCELLED', 'FINISHED'}:
            self.cancel(context)
            if modal_status == 'CANCELLED':
                self.cancel_callback(context)

        return {modal_status}

    def handle_drag_event(self, context, event, matching_event):
        delta = event.mouse_x - self.drag_prev_mouse_x
        increment_val = (self.drag_precise_increment if event.shift else self.drag_increment)
        delta_val = delta * increment_val

        setattr(self, self.drag_attr, getattr(self, self.drag_attr) + delta_val)

        # snapping
        if event.ctrl:
            snap_increment_val = (SNAP_PRECISE_INCREMENT_VAL if event.shift else SNAP_INCREMENT_VAL)
            drag_val = round(getattr(self, self.drag_attr), -int(floor(log10(abs(snap_increment_val)))))
            setattr(self, self.drag_attr, drag_val)

        if matching_event is not None:
            self.cancel_drag_attr(matching_event == 'CANCEL')

        try:
            self.update_light(context)
        except ValueError as e:
            self.report({'ERROR'}, str(e))

        # wrap cursor around X-axis when going beyond region, allowing forever dragging
        region = context.region
        mouse_region_x = event.mouse_region_x
        drag_prev_mouse_region_x = self.drag_prev_mouse_x - region.x
        wrap_left_screen_edge = mouse_region_x <= 1 and mouse_region_x < drag_prev_mouse_region_x
        wrap_right_screen_edge = mouse_region_x >= region.width - 1 and mouse_region_x > drag_prev_mouse_region_x

        if wrap_left_screen_edge or wrap_right_screen_edge:
            if wrap_left_screen_edge:
                new_width = region.x + region.width + 1
            else:
                new_width = region.x - 1
            context.window.cursor_warp(new_width, event.mouse_y)
            self.drag_prev_mouse_x = new_width
        else:
            self.drag_prev_mouse_x = event.mouse_x

    def invoke(self, context, _event):
        if context.area.type == 'VIEW_3D':
            # Add the region drawing callback
            # the arguments we pass the callback
            args = (self, context)
            self.area = context.area
            self._handle = bpy.types.SpaceView3D.draw_handler_add(draw_callback_px, args, 'WINDOW', 'POST_PIXEL')

            self.mouse_path = [[]]
            self.is_erasing = False
            self.curr_mouse_pos = None
            self.eraser_size = 50

            self.preferences = context.preferences.addons[base_package].preferences

            # force set current tool
            bpy.ops.wm.tool_set_by_id(name=self.tool_id)

            context.window_manager.modal_handler_add(self)
            context.window.cursor_set('PAINT_BRUSH')
            self.startup_callback(context)
            return {'RUNNING_MODAL'}
        else:
            self.report({'WARNING'}, "View3D not found, cannot run operator")
            return {'CANCELLED'}

    def startup_callback(self, context):
        """Runs upon invoke(), allows setting up of modal (including adding new objects)."""
        pass

    def cancel_callback(self, context):
        """Runs upon cancelling operator - allows to manually handle undo (e.g. removing new objects)."""
        pass

    def execute(self, context):
        """Run by Python API. Mainly used for testing."""
        if len(self.str_mouse_path):
            import ast
            from mathutils import Vector
            stroke_list = ast.literal_eval(self.str_mouse_path)
            self.mouse_path = [
                [(Vector(coord), Vector(normal)) for coord, normal in stroke]
                for stroke in stroke_list
            ]

        try:
            self.startup_callback(context)
            return self.update_light(context)
        except ValueError as e:
            self.report({'ERROR'}, str(e))
            return {'CANCELLED'}
