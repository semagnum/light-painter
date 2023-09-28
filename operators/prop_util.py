import bpy


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
