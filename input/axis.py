import bpy
from mathutils import Vector

VECTORS = {'X': Vector((1, 0, 0)), 'Y': Vector((0, 1, 0)), 'Z': Vector((0, 0, 1))}
"""List of arbitrary axes and their given vector."""
RAY_OFFSET = 0.001
"""Epsilon offset for raycasts, to prevent self-collisions."""
MAX_RAY_DISTANCE = 0.1
"""Maximum distance for raycasts. Lowering this improves performance drastically."""


def reflect_vector(input_vector: Vector, normal: Vector) -> Vector:
    """Reflects input vector based on a given normal."""
    dn = 2 * input_vector.dot(normal)
    reflected_v = input_vector - normal * dn
    reflected_v.normalize()
    return reflected_v


def axis_prop() -> bpy.props.EnumProperty:
    """Returns axis property to be used by multiple operators."""
    return bpy.props.EnumProperty(
        name='Axis',
        description='Determine axis of offset',
        items=(
            ('X', 'X', ''),
            ('Y', 'Y', ''),
            ('Z', 'Z', ''),
            ('NORMAL', 'Normal', 'Along annotation\'s vertex normal'),
            ('NORMAL-RAY', 'Normal + Surface', 'Casts rays to estimate normal of underlying surface'),
            ('REFLECT', 'Reflect to camera', 'Casts rays from camera to determine offset,'
                                             'best for rim lighting and reflections'),
        ),
        default='NORMAL-RAY'
    )


def offset_points(context, vertices: list[Vector], normals: list[Vector],
                  axis_val: str, offset_amount: float) -> tuple[Vector, Vector]:
    """Offset the position of given vertices.

    :param context: Blender context
    :param vertices: list of vertices
    :param normals: correlating normal vectors
    :param axis_val: enumerator describing direction or axis of offset
    :param offset_amount: magnitude of offset
    :return: offset vertices and updated normals
    """
    if offset_amount == 0:
        return vertices, normals

    if axis_val in VECTORS:
        return tuple(v + VECTORS[axis_val] * offset_amount for v in vertices), tuple(VECTORS[axis_val] for _ in vertices)

    elif axis_val == 'NORMAL':
        vertices = tuple(v + n * offset_amount for v, n in zip(vertices, normals))
    elif axis_val == 'NORMAL-RAY':
        offset_vertices = tuple(v + n * RAY_OFFSET for v, n in zip(vertices, normals))

        scene = context.scene
        depsgraph = context.evaluated_depsgraph_get()
        for idx, v, n in zip(range(len(offset_vertices)), offset_vertices, normals):
            is_hit, _loc, hit_normal, _idx, _obj, _matrix = scene.ray_cast(depsgraph, v, n * -1,
                                                                           distance=MAX_RAY_DISTANCE)
            if is_hit:
                normals[idx] = hit_normal

        vertices = [v + n * offset_amount for v, n in zip(vertices, normals)]
    elif axis_val == 'REFLECT':
        scene = context.scene
        camera = scene.camera
        camera_origin = camera.matrix_world.translation

        scene = context.scene
        depsgraph = context.evaluated_depsgraph_get()
        for idx, v, n in zip(range(len(vertices)), vertices, normals):
            direction = v - camera_origin
            direction.normalized()
            is_hit, _loc, hit_normal, _idx, _obj, _matrix = scene.ray_cast(depsgraph, camera_origin, direction)
            if is_hit:
                normals[idx] = reflect_vector(direction, hit_normal)

        vertices = [v + n * offset_amount for v, n in zip(vertices, normals)]

    return vertices, normals
