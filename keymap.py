from __future__ import annotations

import bpy

PREFIX = 'LIGHT_PAINTER_'

UNIVERSAL_KEYMAP = (
    {
        'name': 'PAINT',
        'type': 'LEFTMOUSE',
        'value': 'ANY',
        'ctrl': 0,
    },

    {
        'name': 'ERASE',
        'type': 'LEFTMOUSE',
        'value': 'ANY',
        'ctrl': 1,
    },
    {
        'name': 'ERASER_DECREASE',
        'type': 'LEFT_BRACKET',
        'value': 'PRESS',
    },
    {
        'name': 'ERASER_INCREASE',
        'type': 'RIGHT_BRACKET',
        'value': 'PRESS',
    },

    {
        'name': 'END_STROKE',
        'type': 'RIGHTMOUSE',
        'value': 'PRESS',
    },
    {
        'name': 'CANCEL',
        'type': 'ESC',
        'value': 'PRESS',
    },
    {
        'name': 'FINISH',
        'type': 'RET',
        'value': 'PRESS',
    },

    # MODES

    {
        'name': 'OFFSET_MODE',
        'type': 'G',
        'value': 'RELEASE',
    },

    {
        'name': 'SIZE_MODE',
        'type': 'F',
        'shift': 0,
        'value': 'RELEASE',
    },

    {
        'name': 'POWER_MODE',
        'type': 'F',
        'shift': 1,
        'value': 'RELEASE',
    },

    # TOGGLES

    {
        'name': 'RELATIVE_POWER_TOGGLE',
        'type': 'R',
        'value': 'PRESS',
    },

    {
        'name': 'TYPE_TOGGLE',
        'type': 'T',
        'value': 'PRESS',
    },
    {
        'name': 'CONVEX_HULL_TOGGLE',
        'type': 'H',
        'value': 'PRESS',
    },

    # MESH
    {
        'name': 'FLATTEN_TOGGLE',
        'type': 'F',
        'value': 'PRESS',
        'shift': 0,
    },

    # AXIS
    {
        'name': 'AXIS_X',
        'type': 'X',
        'value': 'PRESS',
    },
    {
        'name': 'AXIS_Y',
        'type': 'Y',
        'value': 'PRESS',
    },
    {
        'name': 'AXIS_Z',
        'type': 'Z',
        'value': 'PRESS',
    },
    {
        'name': 'AXIS_REFLECT',
        'type': 'C',
        'value': 'PRESS',
    },

    # Visibility

    {
        'name': 'VISIBILITY_TOGGLE_CAMERA',
        'type': 'ONE',
        'value': 'PRESS',
    },
    {
        'name': 'VISIBILITY_TOGGLE_DIFFUSE',
        'type': 'TWO',
        'value': 'PRESS',
    },
    {
        'name': 'VISIBILITY_TOGGLE_SPECULAR',
        'type': 'THREE',
        'value': 'PRESS',
    },
    {
        'name': 'VISIBILITY_TOGGLE_VOLUME',
        'type': 'FOUR',
        'value': 'PRESS',
    },
)
"""Contains default keymap for all Light Painter tools."""

for kmi in UNIVERSAL_KEYMAP:
    kmi['name'] = PREFIX + kmi['name']


UNIVERSAL_KEYMAP_NAMES = tuple(kmi['name'] for kmi in UNIVERSAL_KEYMAP)
AXIS_KEYMAP = tuple(name for name in UNIVERSAL_KEYMAP_NAMES if '_AXIS_' in name)
VISIBILITY_KEYMAP = tuple(name for name in UNIVERSAL_KEYMAP_NAMES if '_VISIBILITY_' in name)


def compare_kmi_to_event(item, event):
    data = item.type
    event_data = event.type
    if item.value != 'ANY':
        data += item.value
        event_data += event.value
    data += str(item.shift * 1 | item.ctrl * 2 | item.alt * 4 | item.oskey * 8)
    event_data += str(event.shift * 1 | event.ctrl * 2 | event.alt * 4 | event.oskey * 8)

    return data == event_data


def get_matching_event(event) -> str | None:
    """Checks if Blender event matches our UNIVERSAL_KEYMAP,
    returns the matching command name (if none match, return None).
    """
    from .preferences import get_lightpainter_kmi

    return next(
        (
            item.properties.name.replace(PREFIX, '')
            for item in get_lightpainter_kmi(bpy.context)
            if compare_kmi_to_event(item, event)
        ),
        None,
    )


def is_event_command(event, command_name) -> bool:
    from .preferences import get_lightpainter_kmi

    if not command_name.startswith(PREFIX):
        command_name = PREFIX + command_name

    item = next(
        (item for item in get_lightpainter_kmi(bpy.context) if item.properties.name == command_name),
        None,
    )

    if item is None:
        return False

    return compare_kmi_to_event(item, event)


def get_kmi_str(command_name):
    from .preferences import get_lightpainter_kmi

    if not command_name.startswith(PREFIX):
        command_name = PREFIX + command_name

    item = next(
        (item for item in get_lightpainter_kmi(bpy.context) if item.properties.name == command_name),
        None,
    )

    if item is None:
        return ''

    return item.to_string()