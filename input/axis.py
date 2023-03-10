import bpy
from mathutils import Vector

VECTORS = {'X': Vector((1, 0, 0)), 'Y': Vector((0, 1, 0)), 'Z': Vector((0, 0, 1))}
RAY_OFFSET = 0.001
MAX_RAY_DISTANCE = 0.1


def reflect_vector(input_vector, normal):
    dn = 2 * input_vector.dot(normal)
    return input_vector - normal * dn


def axis_prop():
    return bpy.props.EnumProperty(
        name='Axis',
        description='Determine axis of offset',
        items=[
            ('X', 'X', '', 1),
            ('Y', 'Y', '', 2),
            ('Z', 'Z', '', 3),
            ('NORMAL', 'Normal', 'Along annotation\'s vertex normal', 4),
            ('NORMAL-RAY', 'Normal + Surface', 'Casts rays to estimate normal of underlying surface', 5),
            ('REFLECT', 'Reflect to camera', 'Casts rays from camera to determine offset, best for reflections', 6),
        ],
        default='NORMAL-RAY'
    )


def offset_points(context, vertices, normals, axis_val: str, offset_amount: float) -> Vector:
    if axis_val in VECTORS:
        vertices = [v + VECTORS[axis_val] * offset_amount for v in vertices]

    elif axis_val == 'NORMAL':
        vertices = [v + n * offset_amount for v, n in zip(vertices, normals)]
    elif axis_val == 'NORMAL-RAY':
        offset_vertices = [v + n * RAY_OFFSET for v, n in zip(vertices, normals)]

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
