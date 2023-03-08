#     Light Paint, Blender add-on that creates lights based on where the user paints.
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


def reflect_vector(input_vector, normal):
    dn = 2 * input_vector.dot(normal)
    return input_vector - normal * dn


def redraw_areas(context):
    for area in context.window.screen.areas:
        if area.type == 'VIEW_3D':
            area.tag_redraw()


def remove(space_view_3d, handler, context):
    space_view_3d.draw_handler_remove(handler, 'WINDOW')
    redraw_areas(context)
