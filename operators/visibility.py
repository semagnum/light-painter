import bpy


class VisibilitySettings:
    visible_camera: bpy.props.BoolProperty(
        name='Camera',
        description='If unchecked, object will not be directly visible by camera (although it will still emit light)',
        default=True
    )

    visible_diffuse: bpy.props.BoolProperty(
        name='Diffuse',
        description='If unchecked, object will not be directly visible by diffuse rays',
        default=True
    )

    visible_specular: bpy.props.BoolProperty(
        name='Specular',
        description='If unchecked, object will not be directly visible by specular or glossy rays',
        default=True
    )

    visible_volume: bpy.props.BoolProperty(
        name='Volume',
        description='If unchecked, object will not be directly visible by volumetric rays',
        default=True
    )

    def draw_visibility_props(self, layout):
        layout.label(text='Ray visibility')
        col = layout.column_flow(align=True, columns=2)
        col.prop(self, 'visible_camera')
        col.prop(self, 'visible_diffuse')
        col.prop(self, 'visible_specular')
        col.prop(self, 'visible_volume')

    def set_visibility(self, obj):
        obj.visible_camera = self.visible_camera
        obj.visible_diffuse = self.visible_diffuse
        obj.visible_glossy = self.visible_specular
        obj.visible_volume_scatter = self.visible_volume

        if obj.type == 'LIGHT':
            light_data = obj.data
            light_data.diffuse_factor = 1.0 if self.visible_diffuse else 0.0
            light_data.specular_factor = 1.0 if self.visible_specular else 0.0
            light_data.volume_factor = 1.0 if self.visible_volume else 0.0
