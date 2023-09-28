import os
import blender_testing

if blender_testing.INSIDE_BLENDER:
    import bpy


run_blender = blender_testing.run_inside_blender(
    import_paths=[os.getcwd()]
)

blender_fixture = blender_testing.blender_fixture()

# Test values
SINGLE_POINT = """[
    [
        ((0, 0, 0), (1, 1, 1)),
    ]
]"""

SINGLE_STROKE = """[
    [
        ((0, 0, 0), (0, 0, 1)),
        ((1, 1, 1), (0, 0, 1))
    ]
]"""

SQUARE_STROKES = """[
    [
        ((1, -1, 0), (0, 0, 1)),
        ((-1, -1, 0), (0, 0, 1)),
        ((-1, 1, 0), (0, 0, 1)),
        ((1, 1, 0), (0, 0, 1)),
    ]
]"""