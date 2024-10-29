import blf
from bpy_extras import view3d_utils
import gpu
from gpu_extras.batch import batch_for_shader
from gpu_extras.presets import draw_circle_2d
from mathutils import Vector

from .. import __package__ as base_package

DRAW_LINE_SIZE = 5.0
ERASE_CIRCLE_OUTLINE_SIZE = 2.0

PAINT_COLOR = (0.9, 0.9, 0.0, 0.5)
SEMI_PAINT_COLOR = (0.9, 0.9, 0.0, 0.25)
ERASE_COLOR = (1.0, 1.0, 1.0, 1.0)

CULLING_DOT_PRODUCT_FACTOR = 0.1

# 0 is default font, 1 is monospaced
FONT_ID = 1
MARGIN = 15
LINE_SPACE_MARGIN = 12

try:
    shader = gpu.shader.from_builtin('UNIFORM_COLOR')
except SystemError:
    import logging
    logging.error('Failed to load GPU API (likely running Blender in background mode).')
    shader = None


def draw_text_overlay(self, context):
    """Draws keymap overlay text"""
    if self.area != context.area:
        return

    region = next((r for r in context.area.regions if r.type == 'WINDOW'), None)
    if region is None:
        return

    preferences = context.preferences
    addon_preferences = preferences.addons[base_package].preferences
    DPI = preferences.system.dpi * preferences.system.pixel_size / 72
    FONT_SIZE = DPI * addon_preferences.overlay_font_scale
    LINE_SPACING = FONT_SIZE + LINE_SPACE_MARGIN

    text_to_display = self.get_header_text().split(', ')
    required_height = len(text_to_display) * LINE_SPACING
    max_line_length = max(map(len, text_to_display))
    max_to_colon_line_length = max([line.index(': ') for line in text_to_display])
    required_width = max_line_length * FONT_SIZE

    if region.width < required_width or region.height < required_height:
        return

    blf.size(FONT_ID, FONT_SIZE)

    anchor = addon_preferences.overlay_position
    if anchor == 'LEFT':
        x_position = MARGIN
    elif anchor == 'CENTER':
        x_position = (region.width / 2) - (required_width / 2)
    else:
        x_position = region.width - required_width - MARGIN

    try:
        FONT_COLOR = preferences.themes[0].user_interface.wcol_text.text
    except AttributeError as e:
        print('Failed to find font color, using off-white:', str(e))
        FONT_COLOR = (0.9, 0.9, 0.9)

    blf.color(FONT_ID, *FONT_COLOR, 1.0)
    blf.shadow(FONT_ID, 6, 0.0, 0.0, 0.0, 1.0)

    for idx, line in enumerate(text_to_display[::-1]):
        # center on colon
        colon_index = line.index(': ')
        if colon_index != -1:
            line = line[:colon_index].rjust(max_to_colon_line_length) + line[colon_index:]

        offset = idx * LINE_SPACING
        blf.position(FONT_ID, x_position, MARGIN + offset, 0)
        blf.draw(FONT_ID, line)


def draw_callback_px(self, context):
    """Draws light painting lines and calls for keymap overlay."""
    region = context.region
    rv3d = context.region_data

    # 50% alpha, 2 pixel width line
    gpu.state.blend_set('ALPHA')
    gpu.state.line_width_set(DRAW_LINE_SIZE)

    paths_3d = [[coord for coord, _ in path] for path in self.mouse_path]

    # draw each path
    for path in paths_3d:
        path_2d = [view3d_utils.location_3d_to_region_2d(region, rv3d, coord) for coord in path]
        batch = batch_for_shader(shader, 'LINE_STRIP', {'pos': path_2d})
        shader.uniform_float('color', PAINT_COLOR)
        batch.draw(shader)

    # print(paths_3d)
    if len(paths_3d) > 0 and len(paths_3d[-1]) > 0:
        last_point = view3d_utils.location_3d_to_region_2d(region, rv3d, paths_3d[-1][-1])
        batch = batch_for_shader(shader, 'LINE_STRIP', {'pos': [last_point, self.curr_mouse_pos]})
        shader.uniform_float('color', SEMI_PAINT_COLOR)
        batch.draw(shader)

    if self.show_eraser:
        gpu.state.line_width_set(ERASE_CIRCLE_OUTLINE_SIZE)
        draw_circle_2d(Vector(self.curr_mouse_pos), ERASE_COLOR, self.eraser_size)

    # restore opengl defaults
    gpu.state.line_width_set(1.0)
    gpu.state.blend_set('NONE')

    if context.preferences.addons[base_package].preferences.keymap_overlay:
        draw_text_overlay(self, context)
