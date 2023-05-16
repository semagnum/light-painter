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

from .axis import get_normals


def get_stroke_vertices(context, stroke, axis: str, offset_amount: float) -> tuple:
    """Given a annotation stroke, return its point and normal data.

    :param context: Blender context
    :param stroke: individual stroke annotation data
    :param axis: enumerator describing direction or axis of offset
    :param offset_amount: offset distance
    :return: tuple of stroke coordinates and correlating normals
    """
    stroke_vertices = [point.co for point in stroke.points]
    stroke_vertices, stroke_normals = get_normals(context, stroke_vertices, axis)

    if offset_amount != 0.0:
        stroke_vertices = tuple(v + n * offset_amount
                                for v, n in zip(stroke_vertices, stroke_normals))

    if offset_amount < 0.0:
        stroke_normals = [normal * -1 for normal in stroke_normals]

    return stroke_vertices, stroke_normals


def get_strokes(context, axis: str, offset_amount: float) -> tuple:
    """Get scene's current annotation stroke data.

    :param context: Blender context
    :param axis: enumerator describing direction or axis of offset
    :param offset_amount: offset distance
    :return: tuple of strokes, each a list of stroke coordinates
    """
    return tuple(stroke_data[0]
                 for stroke_data in get_strokes_and_normals(context, axis, offset_amount))


def get_strokes_and_normals(context, axis: str, offset_amount: float) -> tuple:
    """Get scene's current annotation stroke data, including estimated normals.

    :param context: Blender context
    :param axis: enumerator describing direction or axis of offset
    :param offset_amount: offset distance
    :return: tuple of strokes, each a tuple of a list of stroke coordinates and correlating normals
    """
    gp_frame = context.active_annotation_layer.active_frame

    return tuple(get_stroke_vertices(context, stroke, axis, offset_amount)
                 for stroke in gp_frame.strokes)
