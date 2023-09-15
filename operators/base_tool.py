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
from bpy_extras import view3d_utils
import traceback

from .draw import draw_callback_px

ERASER_SIZE_RATE = 10

PASS_THROUGH_EVENT_TYPES = {
    # view navigation
    'NUMPAD_0',
    'NUMPAD_1',
    'NUMPAD_2',
    'NUMPAD_3',
    'NUMPAD_4',
    'NUMPAD_5',
    'NUMPAD_6',
    'NUMPAD_7',
    'NUMPAD_8',
    'NUMPAD_9',
    # changing frames
    'LEFT_ARROW',
    'RIGHT_ARROW',
    'DOWN_ARROW',
    'UP_ARROW',
    # panning, zooming and orbiting
    'MIDDLEMOUSE',
    'MOUSEWHEEL',
    'WHEELUPMOUSE',
    'WHEELDOWNMOUSE',
    'WHEELINMOUSE',
    'WHEELOUTMOUSE',
    # switching to rendered view
    # also supports undo during the modal process, not sure if I want that
    # since with a tool it's just cancelled
    'Z',
}


def is_in_area(context, mouse_x, mouse_y):
    area = context.area
    regions = dict()
    for region in bpy.context.area.regions:
        regions[region.type] = region

    ui_width = regions["UI"].width
    header_height = regions["HEADER"].height + regions["TOOL_HEADER"].height
    tools_width = regions["TOOLS"].width

    area_min_x, area_min_y = area.x + tools_width, area.y
    area_max_x, area_max_y = area.x + area.width - tools_width - ui_width, area.y + area.height - header_height

    return area_min_x < mouse_x < area_max_x and area_min_y < mouse_y < area_max_y


class BaseLightPaintTool:
    bl_options = {'REGISTER', 'UNDO'}

    tool_id = ''

    def cancel(self, context):
        bpy.types.SpaceView3D.draw_handler_remove(self._handle, 'WINDOW')
        context.window.cursor_set('DEFAULT')
        context.area.header_text_set(None)
        return {'CANCELLED'}

    def execute(self, context):
        """Callback right before the tool is finished (user presses RET or ESC)."""

    def mouse_update(self, context):
        """Callback right after a left or right mouse click release."""

    def paint_controls(self, context, event):
        region = context.region
        rv3d = context.region_data

        region_x, region_y = event.mouse_region_x, event.mouse_region_y
        coord = region_x, region_y

        mouse_release = False
        self.curr_mouse_pos = coord

        if event.type.endswith('ALT'):
            self.is_alt_down = event.value == 'PRESS'

        if event.type == 'LEFTMOUSE':
            new_is_leftmouse_down = event.value == 'PRESS'
            just_pressed = new_is_leftmouse_down and not self.is_leftmouse_down
            mouse_release = not new_is_leftmouse_down and self.is_leftmouse_down
            self.is_leftmouse_down = new_is_leftmouse_down
            if just_pressed and (len(self.mouse_path) == 0 or not self.is_alt_down):
                self.mouse_path.append(list())
        elif event.type == 'RIGHTMOUSE':
            context.window.cursor_set('ERASER')
            new_is_rightmouse_down = event.value == 'PRESS'
            mouse_release = not new_is_rightmouse_down and self.is_rightmouse_down
            self.is_rightmouse_down = new_is_rightmouse_down

        if event.type == 'LEFT_BRACKET':
            self.eraser_size -= ERASER_SIZE_RATE
        elif event.type == 'RIGHT_BRACKET':
            self.eraser_size += ERASER_SIZE_RATE

        if self.is_rightmouse_down:
            self.mouse_path = self.erase_from_mouse_path(region, region_x, region_y, rv3d)

        elif self.is_leftmouse_down:
            scene = context.scene
            depsgraph = context.evaluated_depsgraph_get()
            clip_end = context.space_data.clip_end

            # get the ray from the viewport and mouse
            view_vector = view3d_utils.region_2d_to_vector_3d(region, rv3d, coord)
            ray_origin = view3d_utils.region_2d_to_origin_3d(region, rv3d, coord)

            is_hit, hit_location, hit_normal, _, _, _ = scene.ray_cast(depsgraph, ray_origin, view_vector,
                                                                       distance=clip_end)

            if is_hit:
                self.mouse_path[-1].append((hit_location, hit_normal))

        elif mouse_release:
            self.mouse_update(context)

    def erase_from_mouse_path(self, region, region_x, region_y, rv3d):
        # break paths into potentially new chunks and remove edges erased
        new_mouse_path = [[]]
        eraser_size_squared = self.eraser_size * self.eraser_size
        for path in self.mouse_path:
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
            if len(new_mouse_path[-1]) != 0:
                new_mouse_path.append(list())
        return new_mouse_path

    def modal(self, context, event):
        modal_status = {'RUNNING_MODAL'}

        if context.workspace.tools.from_space_view3d_mode(context.mode, create=False).idname != self.tool_id:
            modal_status = {'CANCELLED'}

        context.area.tag_redraw()

        if not is_in_area(context, event.mouse_x, event.mouse_y):
            context.window.cursor_set('DEFAULT')
            modal_status = {'PASS_THROUGH'}
        else:
            context.window.cursor_set('PAINT_BRUSH')

        if event.type in PASS_THROUGH_EVENT_TYPES:
            modal_status = {'PASS_THROUGH'}

        if event.type == 'ESC' and event.value == 'PRESS':
            modal_status = {'CANCELLED'}

        if event.type in {'RET', 'NUMPAD_ENTER', 'SPACE', 'E'} and event.value == 'PRESS':
            self.execute(context)
            modal_status = {'FINISHED'}

        context.area.header_text_set('LMB: paint surface, '
                                     'RMB: eraser, '
                                     'Left/Right bracket: decrease/increase eraser size, '
                                     'ENTER: finish and light surfaces, '
                                     'ESC: cancel'
                                     )

        # only run if not being cancelled?
        if modal_status == {'RUNNING_MODAL'}:
            self.paint_controls(context, event)
        elif modal_status == {'CANCELLED'} or modal_status == {'FINISHED'}:
            self.cancel(context)

        return modal_status

    def invoke(self, context, _event):
        if context.area.type == 'VIEW_3D':
            # Add the region drawing callback
            # the arguments we pass the callback
            args = (self, context)
            self._handle = bpy.types.SpaceView3D.draw_handler_add(draw_callback_px, args, 'WINDOW', 'POST_PIXEL')

            self.mouse_path = []
            self.is_leftmouse_down = False
            self.is_rightmouse_down = False
            self.curr_mouse_pos = None
            self.eraser_size = 50
            self.is_alt_down = False

            # force set current tool
            bpy.ops.wm.tool_set_by_id(name=self.tool_id)

            context.window_manager.modal_handler_add(self)
            context.window.cursor_set('PAINT_BRUSH')
            return {'RUNNING_MODAL'}
        else:
            self.report({'WARNING'}, "View3D not found, cannot run operator")
            return {'CANCELLED'}
