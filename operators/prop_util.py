import bpy

from ..keymap import get_kmi_str


def axis_prop(obj_descriptor: str) -> bpy.props.EnumProperty:
    """Returns axis property to determine direction of offset."""
    return bpy.props.EnumProperty(
        name='Offset Axis',
        description=f'Determine direction of {obj_descriptor}\'s offset',
        items=(
            ('X', 'X axis', 'Along the global X axis', 'AXIS_SIDE', 0),
            ('Y', 'Y axis', 'Along the global Y axis', 'AXIS_FRONT', 1),
            ('Z', 'Z axis', 'Along the global Z axis', 'AXIS_TOP', 2),
            ('NORMAL', 'Normal', 'Along surface normals', 'ORIENTATION_NORMAL', 3),
            ('REFLECT', 'Rim lighting',
             'Positions light to reflect onto the specified surface directly into the scene camera',
             'INDIRECT_ONLY_OFF',
             4),
        ),
        default='NORMAL',
    )


def offset_prop(obj_descriptor, default_val: float = 1.0) -> bpy.props.FloatProperty:
    """Returns offset property to determine amount of offset."""
    return bpy.props.FloatProperty(
        name='Offset',
        description=f'{obj_descriptor}\'s offset from annotation(s) along specified axis',
        default=default_val,
        unit='LENGTH'
    )


def convert_val_to_unit_str(val, unit_category, precision=5):
    context = bpy.context
    scene = context.scene
    unit_system = scene.unit_settings.system

    return bpy.utils.units.to_string(
        unit_system,
        unit_category,
        val,
        precision=precision,
        split_unit=False,
        compatible_unit=False,
    )


def get_drag_mode_header():
    return ', {}: cancel, any other tool key: confirm'.format(get_kmi_str('CANCEL'))
