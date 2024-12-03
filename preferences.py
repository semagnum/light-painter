import bpy
from rna_keymap_ui import _indented_layout

from .keymap import PREFIX


KEYMAP_NAME = '3D View Generic'


def get_lightpainter_kmi(context):
    """Get all keymap items for Light Painter."""
    keymap = context.window_manager.keyconfigs.user.keymaps[KEYMAP_NAME]
    return tuple(
        item
        for item in keymap.keymap_items
        if (
                item.idname == 'wm.call_menu' and
                item.properties and
                hasattr(item.properties, 'name') and
                item.properties.name.startswith(PREFIX)
        )
    )


class VIEW3D_AddonPreferences(bpy.types.AddonPreferences):
    bl_idname = __package__

    keymap_overlay: bpy.props.BoolProperty(
        name='Shortcuts Overlay',
        default=True,
        description='Show keymap in 3D view while using Light Painter tools (if there is enough space)',
    )
    keymap_header: bpy.props.BoolProperty(
        name='Shortcuts in 3D view header',
        default=False,
        description='Show keymap in 3D view header while using Light Painter tools',
    )
    keymap_status_bar: bpy.props.BoolProperty(
        name='Shortcuts in status bar',
        default=True,
        description='Show keymap in status bar while using Light Painter tools',
    )

    overlay_position: bpy.props.EnumProperty(
        name='Overlay Position',
        description='Position of overlay in the 3D view',
        items=(
            ('LEFT', 'Left', 'Bottom left corner'),
            ('CENTER', 'Center', 'Bottom center'),
            ('RIGHT', 'Right', 'Bottom right corner'),
        ),
        default='CENTER',
    )

    overlay_font_scale: bpy.props.FloatProperty(
        name='Overlay Font Scale',
        description='Multiplier of font scale used in the overlay',
        default=10.0,
        min=5.0,
        precision=1,
    )

    def draw(self, context):
        layout = self.layout

        layout.use_property_split = True
        layout.use_property_decorate = False

        layout.label(text='Tools Keymap')

        col = layout.column(align=True, heading='Display')
        col.prop(self, 'keymap_header', text='3D View Header')
        col.prop(self, 'keymap_status_bar', text='Status Bar')
        col.prop(self, 'keymap_overlay', text='Overlay')

        col = layout.column()
        col.active = self.keymap_overlay
        col.prop(self, 'overlay_position')
        col.prop(self, 'overlay_font_scale', text='Scale')

        col = layout.column()

        keymap = context.window_manager.keyconfigs.user.keymaps[KEYMAP_NAME]
        light_painter_kmi = get_lightpainter_kmi(context)

        for item in light_painter_kmi:
            self.draw_item(context, col, item, keymap)

    def draw_item(self, context, layout, item, keymap):
        map_type = item.map_type

        col = _indented_layout(layout, 0)

        if item.show_expanded:
            col = col.column(align=True)
            box = col.box()
        else:
            box = col.column()

        split = box.split()

        # header bar
        row = split.row(align=True)
        row.prop(item, 'show_expanded', text='', emboss=False)

        proper_name = item.properties.name.replace(PREFIX, '').replace('_', ' ').title()

        row.label(text=proper_name)

        row = split.row()
        row.prop(item, 'map_type', text='')
        if map_type in {'KEYBOARD', 'MOUSE', 'NDOF'}:
            row.prop(item, 'type', text='', full_event=True)
        elif map_type == 'TWEAK':
            subrow = row.row()
            subrow.prop(item, 'type', text='')
            subrow.prop(item, 'value', text='')
        elif map_type == 'TIMER':
            row.prop(item, 'type', text='')
        else:
            row.label()

        if item.is_user_modified:
            row.context_pointer_set('keymap', keymap)  # for 'keyitem_restore'
            row.operator('preferences.keyitem_restore', text='', icon='BACK').item_id = item.id

        # Expanded, additional event settings
        if not item.show_expanded:
            return

        box = col.box()

        split = box.split(factor=0.4)
        sub = split.row()

        # sub.prop(item, 'idname', text='')

        if map_type not in {'TEXTINPUT', 'TIMER'}:
            sub = split.column()
            subrow = sub.row(align=True)

            if map_type == 'KEYBOARD':
                subrow.prop(item, 'type', text='', event=True)
                subrow.prop(item, 'value', text='')
            elif map_type in {'MOUSE', 'NDOF'}:
                subrow.prop(item, 'type', text='')
                subrow.prop(item, 'value', text='')

            if map_type in {'KEYBOARD', 'MOUSE'} and item.value == 'CLICK_DRAG':
                subrow = sub.row()
                subrow.prop(item, 'direction')

            subrow = sub.row()
            subrow.scale_x = 0.75
            subrow.prop(item, 'any', toggle=True)
            # Use `*_ui` properties as integers aren't practical
            subrow.prop(item, 'shift_ui', toggle=True)
            subrow.prop(item, 'ctrl_ui', toggle=True)
            subrow.prop(item, 'alt_ui', toggle=True)
            subrow.prop(item, 'oskey_ui', text='Cmd', toggle=True)
