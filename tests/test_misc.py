from blender_pretest import blender_fixture, run_blender, SINGLE_POINT


@blender_fixture
def context():
    import bpy
    return bpy.context


@blender_fixture
def ops():
    import bpy
    return bpy.ops


def test_sanity():
    """If this fails, you are probably not setup, period ;P."""
    assert 1 + 1 == 2


@run_blender
def test_relative_power(context, ops):
    """Relative power should follow: relative_power = apparent power * distance * distance
    """
    # map of power (first param), distance (second param) to result
    power_distance_answer = [
        (1.0, 1.0, 1.0),
        (10.0, 1.0, 10.0),
        (1.0, 10.0, 100.0),
        (10.0, 10.0, 1000.0),
    ]

    light_obj = context.scene.objects['Light']

    ops.object.select_all(action='DESELECT')
    context.view_layer.objects.active = light_obj

    for power, distance, answer in power_distance_answer:
        ops.lightpainter.lamp_adjust(
            str_mouse_path=SINGLE_POINT, offset=distance, axis='X',
            is_power_relative=True, power=power
        )
        assert light_obj.location[0] == distance
        assert light_obj.data.energy == answer


@run_blender
def test_area_lamp_rotation(context, ops):
    """Area lamps must be oriented appropriately."""
    from lightpainter.operators.lamp_util import get_box
    from mathutils import Vector

    vertices = [
        Vector((1, -1, 0)),
        Vector((-1, -1, 0)),
        Vector((-1, 1, 0)),
        Vector((1, 1, 0)),
    ]
    center, _, length, width = get_box(vertices, Vector((0, 0, 1)))
    assert all(expected == actual for expected, actual in zip((0.0, 0.0, 0.0), center))
    assert (2 - length) <= 0.0001
    assert (2 - width) <= 0.0001
