import bpy
from mathutils import Vector

RAY_OFFSET = 0.001
MAX_RAY_DISTANCE = 0.1


def axis_prop():
    return bpy.props.EnumProperty(
        name='Axis',
        description='Determine axis of offset',
        items=[
            ('X', 'X', "", 1),
            ('Y', 'Y', "", 2),
            ('Z', 'Z', "", 3),
            ('NORMAL', 'Normal', 'Along annotation\'s vertex normal', 4),
            ('NORMAL-RAY', 'Normal + Surface', 'Casts rays to approximate normal of underlying surface', 5),
        ],
        default='NORMAL-RAY'
    )


def offset_points(context, vertices, normals, axis_val: str, offset_amount: float) -> Vector:
    if axis_val == 'X':
        vertices = [v + Vector((1, 0, 0)) * offset_amount for v in vertices]
    elif axis_val == 'Y':
        vertices = [v + Vector((0, 1, 0)) * offset_amount for v in vertices]
    elif axis_val == 'Z':
        vertices = [v + Vector((0, 0, 1)) * offset_amount for v in vertices]

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

    return vertices, normals
