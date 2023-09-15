from bpy_extras import view3d_utils
import gpu
from gpu_extras.batch import batch_for_shader
from gpu_extras.presets import draw_circle_2d
from mathutils import Vector

DRAW_LINE_SIZE = 5.0
ERASE_CIRCLE_OUTLINE_SIZE = 2.0

PAINT_COLOR = (0.9, 0.9, 0.0, 0.5)
SEMI_PAINT_COLOR = (0.9, 0.9, 0.0, 0.25)
ERASE_COLOR = (1.0, 1.0, 1.0, 1.0)

CULLING_DOT_PRODUCT_FACTOR = 0.1


def draw_callback_px(self, context):
    region = context.region
    rv3d = context.region_data

    # 50% alpha, 2 pixel width line
    shader = gpu.shader.from_builtin('UNIFORM_COLOR')
    gpu.state.blend_set('ALPHA')
    gpu.state.line_width_set(DRAW_LINE_SIZE)

    paths_3d = [[coord for coord, _ in path] for path in self.mouse_path]

    # draw each path
    for path in paths_3d:
        path_2d = [view3d_utils.location_3d_to_region_2d(region, rv3d, coord) for coord in path]
        batch = batch_for_shader(shader, 'LINE_STRIP', {'pos': path_2d})
        shader.uniform_float('color', PAINT_COLOR)
        batch.draw(shader)

    if self.is_alt_down and len(paths_3d) > 0 and len(paths_3d[-1]) > 0:
        last_point = view3d_utils.location_3d_to_region_2d(region, rv3d, paths_3d[-1][-1])
        batch = batch_for_shader(shader, 'LINE_STRIP', {'pos': [last_point, self.curr_mouse_pos]})
        shader.uniform_float('color', SEMI_PAINT_COLOR)
        batch.draw(shader)

    if self.is_rightmouse_down:
        gpu.state.line_width_set(ERASE_CIRCLE_OUTLINE_SIZE)
        draw_circle_2d(Vector(self.curr_mouse_pos), ERASE_COLOR, self.eraser_size)

    # restore opengl defaults
    gpu.state.line_width_set(1.0)
    gpu.state.blend_set('NONE')
