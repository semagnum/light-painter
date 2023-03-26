import bpy
from mathutils import Vector

VECTORS = {'X': Vector((1, 0, 0)), 'Y': Vector((0, 1, 0)), 'Z': Vector((0, 0, 1))}
"""List of arbitrary axes and their given vector."""
RAY_OFFSET = 0.001
"""Epsilon offset for raycasts, to prevent self-collisions."""


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
            ('NORMAL', 'Stroke Normal', 'Along annotation stroke\'s normal'),
            ('NORMAL-RAY', 'Surface Normal', 'Casts rays to estimate normal of underlying surface'),
            ('REFLECT', 'Rim lighting', 'Positions light to reflect onto the specified surface directly into the scene camera'),
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

    if axis_val in VECTORS:
        vertices = tuple(v + VECTORS[axis_val] * offset_amount
                         for v in vertices)
        normals = tuple(VECTORS[axis_val]
                        for _ in vertices)

    elif axis_val == 'NORMAL' and offset_amount != 0:
        vertices = tuple(v + n * offset_amount
                         for v, n in zip(vertices, normals))
    elif axis_val == 'NORMAL-RAY':
        offset_vertices = tuple(v + n * RAY_OFFSET for v, n in zip(vertices, normals))

        scene = context.scene
        depsgraph = context.evaluated_depsgraph_get()
        for idx, v, n in zip(range(len(offset_vertices)), offset_vertices, normals):
            is_hit, hit_loc, hit_normal, _idx, _obj, _matrix = scene.ray_cast(depsgraph, v, n * -1)
            if is_hit:
                normals[idx] = hit_normal
                vertices[idx] = hit_loc

        if offset_amount != 0:
            vertices = tuple(v + n * offset_amount
                             for v, n in zip(vertices, normals))
    elif axis_val == 'REFLECT':
        scene = context.scene
        camera = scene.camera
        camera_origin = camera.matrix_world.translation

        scene = context.scene
        depsgraph = context.evaluated_depsgraph_get()
        for idx, v, n in zip(range(len(vertices)), vertices, normals):
            direction = v - camera_origin
            direction.normalize()
            is_hit, hit_loc, hit_normal, _idx, _obj, _matrix = scene.ray_cast(depsgraph, camera_origin, direction)
            if is_hit:
                normals[idx] = reflect_vector(direction, hit_normal)
                vertices[idx] = hit_loc

        if offset_amount != 0:
            vertices = tuple(v + n * offset_amount
                             for v, n in zip(vertices, normals))

    return vertices, normals
