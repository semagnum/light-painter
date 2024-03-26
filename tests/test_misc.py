from math import pi
from numpy import isclose as np_isclose
import os
from pathlib import Path
import pytest

import bpy
import addon_utils

from config import SINGLE_POINT


def get_zip_file_in_parent_dir():
    """Gets first zip file it can find.

    Since this will be in the tests/ folder,
    we need to go up a folder to find the zip file that compress.py builds.
    """
    parent_dir = Path(os.getcwd()).parent
    for root, dirs, files in os.walk(parent_dir):
        for file in files:
            if file.endswith(".zip"):
                return os.path.join(root, file)

    raise FileNotFoundError('No zip file to install into Blender!')


@pytest.fixture(scope="session", autouse=True)
def install_addon(request):
    """Installs the addon for testing. After the session is finished, it optionally uninstalls the add-on."""
    bpy.ops.preferences.addon_install(filepath=get_zip_file_in_parent_dir())

    addon_utils.modules_refresh()
    bpy.ops.script.reload()

    bpy.ops.preferences.addon_enable(module='lightpainter')

    yield

    # In my case (using symlinks), since this add-on is already enabled,
    # this installs the add-on twice.
    # So I need to delete the newly installed add-on folder afterward.

    import os
    import shutil
    if os.getenv('ADDON_INSTALL_PATH_TO_REMOVE') is not None:
        shutil.rmtree(os.getenv('ADDON_INSTALL_PATH_TO_REMOVE'))


@pytest.fixture
def context():
    import bpy
    return bpy.context


@pytest.fixture
def ops():
    import bpy
    # bpy module doesn't refresh the scene per test,
    # so I need to reload the file each time
    bpy.ops.wm.read_homefile()
    return bpy.ops


def test_sanity():
    """If this fails, you are probably not setup, period ;P."""
    assert 1 + 1 == 2


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


def test_area_lamp_rotation():
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


def test_gobos(context, ops):
    light_obj = context.scene.objects['Light']

    ops.object.select_all(action='DESELECT')
    context.view_layer.objects.active = light_obj

    from lightpainter.operators.lamp_add_gobos import TEXTURE_TYPE_TO_NODE

    # Musgrave doesn't exist in 4.0+, remove for tests of that version or higher
    import bpy
    if bpy.app.version[0] >= 4:
        TEXTURE_TYPE_TO_NODE.pop('MUSGRAVE')

    texture_types = list(TEXTURE_TYPE_TO_NODE)
    for texture_type in texture_types:
        context.window_manager.lightpainter_texture_type = texture_type
        ops.lightpainter.lamp_texture()
        ops.lightpainter.lamp_texture_remove()

def test_conversion():
    from mathutils import Vector
    from lightpainter.operators.lamp_util import geo_to_dir

    # vector -> latitude, longitude
    TEST_CONVERSIONS = [
        # y-axis
        (Vector((0, 1, 0)), (0, 0)),
        (Vector((0, -1, 0)), (0, pi)),

        # x-axis
        (Vector((1, 0, 0)), (0, pi / 2)),
        (Vector((-1, 0, 0)), (0, -pi / 2)),

        # z-up
        (Vector((0, 0, 1)), (pi / 2, 0)),
    ]

    def compare_vectors(vec1, vec2):
        return all(np_isclose(v2, v1, atol=0.001, rtol=0.001) for v1, v2 in zip(vec1, vec2))

    for v, geo in TEST_CONVERSIONS:
        result = geo_to_dir(geo[0], geo[1])
        assert compare_vectors(result, v), 'geo_to_dir {} => {} != {}'.format(geo, result, v)