if 'ConvexLight' in locals():
    import importlib
    reloadable_modules = [
        'base_tool',
        'draw',
        'visibility',
        'lamp_util',
        'flag_tool',
        'lamp_tool',
        'mesh_tool',
        'sky_tool',
        'lamp_add_gobos',
    ]
    for module_name in reloadable_modules:
        if module_name in locals():
            importlib.reload(locals()[module_name])

from .lamp_adjust_tool import LIGHTPAINTER_OT_Lamp_Adjust
from .lamp_tool import LIGHTPAINTER_OT_Lamp
from .mesh_tool import LIGHTPAINTER_OT_Mesh, LIGHTPAINTER_OT_Tube_Light
from .sky_tool import LIGHTPAINTER_OT_Sky, LIGHTPAINTER_OT_Sun
from .flag_tool import LIGHTPAINTER_OT_Flag
from .lamp_add_gobos import LIGHTPAINTER_OT_Lamp_Texture, LIGHTPAINTER_OT_Lamp_Texture_Remove
