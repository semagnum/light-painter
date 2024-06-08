from __future__ import annotations


AXIS_KEYMAP = {
    'AXIS_X': {
        'type': 'X',
        'value': 'PRESS',
    },
    'AXIS_Y': {
        'type': 'Y',
        'value': 'PRESS',
    },
    'AXIS_Z': {
        'type': 'Z',
        'value': 'PRESS',
    },
    'AXIS_REFLECT': {
        'type': 'C',
        'value': 'PRESS',
    },
}

VISIBILITY_KEYMAP = {
    'VISIBILITY_TOGGLE_CAMERA': {
        'type': 'ONE',
        'visual_key': '1',
        'value': 'PRESS',
    },
    'VISIBILITY_TOGGLE_DIFFUSE': {
        'type': 'TWO',
        'visual_key': '2',
        'value': 'PRESS',
    },
    'VISIBILITY_TOGGLE_SPECULAR': {
        'type': 'THREE',
        'visual_key': '3',
        'value': 'PRESS',
    },
    'VISIBILITY_TOGGLE_VOLUME': {
        'type': 'FOUR',
        'visual_key': '4',
        'value': 'PRESS',
    },
}

UNIVERSAL_KEYMAP = {
    'PAINT': {
        'type': 'LEFTMOUSE',
        'visual_key': 'LMB',
        'ctrl': False,
    },

    'ERASE': {
        'type': 'LEFTMOUSE',
        'ctrl': True,
        'visual_key': 'Ctrl LMB',
    },
    'ERASER_DECREASE': {
        'type': 'LEFT_BRACKET',
        'visual_key': '[',
    },
    'ERASER_INCREASE': {
        'type': 'RIGHT_BRACKET',
        'visual_key': ']',
    },

    'END_STROKE': {
        'type': 'RIGHTMOUSE',
        'visual_key': 'RMB',
        'value': 'PRESS',
    },
    'CANCEL': {
        'type': 'ESC',
        'visual_key': 'Esc',
        'value': 'PRESS',
    },
    'FINISH': {
        'type': ('RET', 'NUMPAD_ENTER', 'SPACE'),
        'visual_key': 'Enter/Space',
        'value': 'PRESS',
    },

    # Lamp
    'OFFSET_MODE': {
        'type': 'G',
        'value': 'PRESS',
    },

    'SIZE_MODE': {
        'type': 'F',
        'shift': False,
        'value': 'PRESS',
    },

    'POWER_MODE': {
        'type': 'F',
        'shift': True,
        'visual_key': 'Shift F',
    },
    'RELATIVE_POWER_TOGGLE': {
        'type': 'R',
        'value': 'PRESS',
    },

    # Mesh
    'FLATTEN_TOGGLE': {
        'type': 'F',
        'value': 'PRESS',
    },

    # Lamp type
    'TYPE_TOGGLE': {
        'type': 'T',
        'value': 'PRESS',
    },
}
"""Contains a coherent keymap for all the Light Paint tools. Reconfigure to suit your preferences.
The format is as follows:
{
    'PAINT': { # name of the command
        'type': 'LEFTMOUSE', # name of the event. See https://docs.blender.org/api/current/bpy_types_enum_items/event_type_items.html
        'visual_key': 'LMB', # event's name for the user to see in the header
        'ctrl': True, # if Ctrl must be used to register the command
        'alt': True, # if Alt must be used to register the command
        'shift': True, # if Shift must be used to register the command
        'value': 'PRESS' # it will only register when the key is pressed ('RELEASE' for only when released)
    },
    # ...
}

Note that if a modifier key like `ctrl` isn't in the keymap, the event can still match despite it being pressed.
So if a key is used for 2+ events but with different modifiers, be sure to mark one with its modifier(s) as False.
"""

UNIVERSAL_KEYMAP.update(AXIS_KEYMAP)
UNIVERSAL_KEYMAP.update(VISIBILITY_KEYMAP)

UNIVERSAL_COMMAND_STR = {
    key: UNIVERSAL_KEYMAP[key].get('visual_key', str(UNIVERSAL_KEYMAP[key].get('type')))
    for key in UNIVERSAL_KEYMAP
}
"""A smaller dict containing just the visual_key attrs. Simplifies references when generating the header text."""


def get_matching_event(event) -> str | None:
    """Checks if Blender event matches our UNIVERSAL_KEYMAP,
    returns the matching command name (if none match, return None).
    """
    return next(
        (command_name
         for command_name in UNIVERSAL_KEYMAP.keys()
         if is_event_command(event, command_name))
        , None
    )


def is_event_command(event, command_name) -> bool:
    """Checks if Blender event matches a specific command, return True, False otherwise."""
    keymap_item = UNIVERSAL_KEYMAP.get(command_name, None)
    if keymap_item is None:
        return False

    kmi_types = keymap_item.get('type', [])
    if isinstance(kmi_types, str):
        matching_type = (event.type == kmi_types)
    else:
        matching_type = any(event.type == kmi_type for kmi_type in kmi_types)

    return (
            matching_type and
            ('value' not in keymap_item or event.value == keymap_item.get('value')) and
            ('shift' not in keymap_item or event.shift == keymap_item.get('shift')) and
            ('alt' not in keymap_item or event.alt == keymap_item.get('alt')) and
            ('ctrl' not in keymap_item or event.ctrl == keymap_item.get('ctrl'))
    )
