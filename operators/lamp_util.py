import bpy
import math
from math import cos, pi, sin
from mathutils import Matrix, Vector
from mathutils.geometry import box_fit_2d
import numpy as np
from typing import Iterable

from .prop_util import offset_prop
from .visibility import VisibilitySettings

EPSILON = 0.01
PI_OVER_2 = pi / 2

NORMAL_ERROR = 'Average of normals results in a zero vector - unable to calculate average direction!'


def calc_power(power: float, distance: float) -> float:
    """Calculates relative light power based on inverse square law.
    relative power = initial power * squared distance

    :param power: light value at 1m.
    :param distance: distance from the light to the target object.
    :return: light power relative to distance
    """
    return power * (distance * distance)


def get_average_normal(normals: Iterable[Vector]) -> Vector:
    """Calculates average normal. Handles zero vector edge case as an error.

    :param normals: list of normal vectors
    :return: single normalized Vector representing the average
    """
    avg_normal = sum(normals, start=Vector())
    avg_normal.normalize()
    if avg_normal == Vector((0, 0, 0)):
        raise ValueError(NORMAL_ERROR)

    return avg_normal


def is_blocked(scene, depsgraph, origin: Vector, direction: Vector, max_distance=1.70141e+38) -> bool:
    """Check if a given point is occluded in a given direction.

    :param scene: scene
    :param depsgraph: the scene dependency graph
    :param origin: given point in world space as a Vector
    :param direction: given direction in world space as a Vector
    :param max_distance: maximum distance for raycast to check
    :return: True if anything is in that direction from that point, False otherwise
    """
    offset_origin = origin + direction * EPSILON
    is_hit, _, _, _, _, _ = scene.ray_cast(depsgraph, offset_origin, direction, distance=max_distance)

    return is_hit


def get_box(vertices, normal):
    """Given a set of vertices flattened along a plane and their normal, return an aligned rectangle.

    :param vertices: list of vertex coordinates in world space
    :param normal: normal of vertices for rectangle to be projected to
    :return: tuple of (coordinate of rect center, matrix for rotation, rect length, and rect width
    """
    # rotate hull so normal is pointed up, so we can ignore Z
    # find angle of fitted box
    align_to_z = normal.rotation_difference(Vector((0.0, 0.0, 1.0))).to_matrix()
    flattened_2d = [align_to_z @ v for v in vertices]

    # rotate hull by angle
    # get length and width
    angle = box_fit_2d([(v[0], v[1]) for v in flattened_2d])
    box_mat = Matrix.Rotation(angle, 3, 'Z')
    aligned_2d = [(box_mat @ Vector((co[0], co[1], 0))) for co in flattened_2d]
    xs = tuple(co[0] for co in aligned_2d)
    ys = tuple(co[1] for co in aligned_2d)

    x_min, x_max = min(xs), max(xs)
    y_min, y_max = min(ys), max(ys)

    length = x_max - x_min
    width = y_max - y_min

    center = align_to_z.inverted_safe() @ box_mat.inverted_safe() @ Vector((x_min + (length / 2),
                                                                            y_min + (width / 2),
                                                                            flattened_2d[0][2]))

    # return matrix, length and width of box
    return center, align_to_z.inverted_safe() @ box_mat.inverted_safe(), length, width


def calc_rank(dot_product: float, count: int) -> float:
    """Calculate the "rank" of an occlusion ray test.

    :param dot_product: dot product between the current vector and the ideal normal
    :param count: number of points that can "see" in that direction
    :return: a rank for comparison, higher is better
    """
    return (dot_product + 1) * count


def geo_to_dir(latitude, longitude) -> Vector:
    if latitude == pi/2:
        return Vector((0, 0, 1))
    x = sin(longitude)
    y = cos(longitude)
    z = sin(latitude)
    return Vector((x, y, z))


def get_occlusion_based_normal(
        context, vertices: Iterable, avg_normal: Vector,
        elevation_clamp: float, latitude_samples: int, longitude_samples: int
) -> Vector:
    """Find a normal that best points toward a given normal that's visible by the most points.

    :param context: Blender context
    :param vertices: list of points in world space as Vectors
    :param avg_normal: average normal as the preferred direction towards the sun lamp
    :param elevation_clamp: sun's max vertical angle
    :param latitude_samples: number of samples for occlusion testing along the latitudinal axis
    :param longitude_samples: number of samples for occlusion testing along the longitudinal axis
    :return: world space Vector pointing towards the sun
    """
    max_sun_elevation = elevation_clamp
    latitude_sample_size = latitude_samples
    latitude_samples = np.linspace(0, max_sun_elevation, latitude_sample_size)

    # since about half of longitudinal samples will not be viable (ie pointing away from ideal normal),
    # we will double its sample size.
    longitude_sample_size = longitude_samples * 2
    longitude_samples = np.linspace(0, 2 * pi, longitude_sample_size, endpoint=False)

    # iterate over each axis
    # if the resulting vector is all zeroes or the dot product of it and Z axis is too high, skip
    # if the dot product of it and Z axis is less than zero, skip (to avoid night)
    scene = context.scene
    depsgraph = context.evaluated_depsgraph_get()

    samples_loop = (geo_to_dir(lat, long).normalized()
                    for long in longitude_samples
                    for lat in latitude_samples
                    if geo_to_dir(lat, long).normalized().dot(avg_normal) > 0)

    def normal_rank(normal):
        vertex_visibility_count = sum(1 for v in vertices
                                      if not is_blocked(scene, depsgraph, v, normal))

        curr_rank = calc_rank(normal.dot(avg_normal), vertex_visibility_count)
        return curr_rank, normal

    sun_normal = max(normal_rank(normal) for normal in samples_loop)[1]

    return sun_normal


class LampUtils(VisibilitySettings):
    offset: offset_prop('lamp')

    is_power_relative: bpy.props.BoolProperty(
        name='Relative',
        description='Lamp power scales based on distance, relative to 1m',
        default=False,
    )

    power: bpy.props.FloatProperty(
        name='Power',
        description='Area light\'s emit value',
        min=0.001,
        default=10,
        # FIXME add power units back when fixed:
        # https://projects.blender.org/blender/blender/issues/77791#issuecomment-1069560
        # subtype='POWER',
        # unit='POWER',
    )

    radius: bpy.props.FloatProperty(
        name='Radius',
        description='Light size for ray shadow sampling',
        min=0.001,
        default=0.1,
        unit='LENGTH',
    )

    light_color: bpy.props.FloatVectorProperty(
        name='Color',
        size=3,
        default=(1.0, 1.0, 1.0),
        min=0.0,
        soft_max=1.0,
        subtype='COLOR',
    )

    # AREA SETTINGS
    min_size: bpy.props.FloatVectorProperty(
        name='Minimum size',
        description='Area lamp size will be clamped to these minimum values',
        size=2,
        min=0.001,
        default=(0.01, 0.01),
        unit='LENGTH',
    )

    shape: bpy.props.EnumProperty(
        name='Shape',
        description='Determine axis of offset',
        items=[
            ('RECTANGLE', 'Rectangle', ''),
            ('SQUARE', 'Square', ''),
            ('DISK', 'Disk', ''),
            ('ELLIPSE', 'Ellipse', ''),
        ],
        default='RECTANGLE',
    )

    def update_area_lamp(self, lamp, stroke):
        """Adds an area lamp.

        :param lamp: area lamp object
        :param stroke: tuple of vertices and normals

        :exception ValueError: if calculating the normal average fails

        :return: Blender lamp object
        """

        vertices, normals = stroke
        # get average, negated normal, THROWS ValueError if average is zero vector
        avg_normal = get_average_normal(normals)
        avg_normal.negate()

        farthest_point = max((v.project(avg_normal).length_squared, v) for v in vertices)[1]

        projected_vertices = tuple(v + (farthest_point - v).project(avg_normal) for v in vertices)

        center, mat, x_size, y_size = get_box(projected_vertices, avg_normal)
        rotation = mat.to_euler()
        rotation.rotate_axis('X', math.radians(180.0))

        # set light data properties
        lamp.location = center
        lamp.rotation_euler = rotation
        lamp.data.energy = calc_power(self.power, self.offset) if self.is_power_relative else self.power
        lamp.data.shape = self.shape
        if self.shape in {'RECTANGLE', 'ELLIPSE'}:
            lamp.data.size = max(self.min_size[0], x_size)
            lamp.data.size_y = max(self.min_size[1], y_size)
        else:
            max_size = max(x_size, y_size, self.min_size[0], self.min_size[1])
            lamp.data.size = max_size

        self.set_visibility(lamp)

    def update_point_lamp(self, lamp, stroke):
        """Updates point lamp.

        :param lamp: Blender lamp object
        :param stroke: tuple of vertices and strokes

        :exception ValueError: if calculating the normal average fails

        :return: Blender lamp object
        """
        vertices, normals = stroke

        # get average, negated normal, THROWS ValueError if average is zero vector
        avg_normal = get_average_normal(normals)
        avg_normal.negate()

        farthest_point = max((v.project(avg_normal).length_squared, v) for v in vertices)[1]

        projected_vertices = tuple(v + (farthest_point - v).project(avg_normal) for v in vertices)

        center = sum(projected_vertices, start=Vector()) / len(projected_vertices)

        # set light data properties
        lamp.location = center
        lamp.data.shadow_soft_size = self.radius
        lamp.data.energy = calc_power(self.power, self.offset) if self.is_power_relative else self.power
        self.set_visibility(lamp)

    def update_spot_lamp(self, lamp, orig_vertices, stroke):
        """Adds a spot lamp.

        :param lamp: Blender lamp object
        :param orig_vertices: stroke vertices without offset from their surface
        :param stroke: tuple of vertices and normals, potentially offset from their surface

        :exception ValueError: if calculating the normal average fails

        :return: Blender lamp object
        """
        vertices, normals = stroke

        # THROWS ValueError if average is zero vector
        avg_normal = get_average_normal(normals)
        avg_normal.negate()

        farthest_point = max((v.project(avg_normal).length_squared, v) for v in vertices)[1]

        projected_vertices = tuple(v + (farthest_point - v).project(avg_normal) for v in vertices)

        center = sum(projected_vertices, start=Vector()) / len(projected_vertices)
        rotation = Vector((0.0, 0.0, -1.0)).rotation_difference(avg_normal).to_euler()

        orig_center = sum(orig_vertices, start=Vector()) / len(orig_vertices)
        centers_dir = (orig_center - center).normalized()
        spot_angle = 2 * max((v - center).normalized().angle(centers_dir)
                             for v in orig_vertices)

        # set light data properties
        lamp.location = center
        lamp.rotation_euler = rotation
        lamp.data.spot_size = spot_angle
        lamp.data.energy = calc_power(self.power, self.offset) if self.is_power_relative else self.power
        lamp.data.shadow_soft_size = self.radius
        self.set_visibility(lamp)
