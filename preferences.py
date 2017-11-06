import bpy
from . import header_extras
from bpy.types import Operator, AddonPreferences
from bpy.props import StringProperty, IntProperty, BoolProperty

def set_keybind():
    wm = bpy.context.window_manager
     
    f3_keybind_found = False
    f4_keybind_found = False
    
    # Object non modal keybinds
    # Get object non modal keymaps
    km = wm.keyconfigs.addon.keymaps.get('Object Non-modal')
    if not km:
        km = wm.keyconfigs.addon.keymaps.new('Object Non-modal')
    
    # Search for F3 & F4 keybind
    for kmi in km.keymap_items:
        
        if kmi.type == 'F3':
            if kmi.idname == 'object.mode_set' and kmi.properties.mode == 'SCULPT':
                f3_keybind_found = True
                kmi.active = True
            else:
                # Deactivate other F3 keybind
                kmi.active = False
                
        if kmi.type == 'F4':
            if kmi.idname == 'object.mode_set' and kmi.properties.mode == 'TEXTURE_PAINT':
                f4_keybind_found = True
                kmi.active = True
            else:
                # Deactivate other F4 keybind
                kmi.active = False

    # Set F3 Keybind
    if not f3_keybind_found:
        new_shortcut = km.keymap_items.new('object.mode_set', 'F3', 'PRESS')
        new_shortcut.properties.mode = 'SCULPT'
        new_shortcut.properties.toggle = True
    
    # Set F4 Keybind
    if not f4_keybind_found:
        new_shortcut = km.keymap_items.new('object.mode_set', 'F4', 'PRESS')
        new_shortcut.properties.mode = 'TEXTURE_PAINT'
        new_shortcut.properties.toggle = True

    f4_keybind_found = False
    f7_keybind_found = False
    z_keybind_found = False
    d_keybind_found = False

    # Mode change keybinds need Window keymaps
    km = wm.keyconfigs.addon.keymaps.get('Window')
    if not km:
        km = wm.keyconfigs.addon.keymaps.new('Window')

    for kmi in km.keymap_items:
        
        # Search for F4 keybind
        if kmi.type == 'F4':
            if kmi.idname == 'paint.yp_image_paint_toggle':
                f4_keybind_found = True
                kmi.active = True
            else:
                # Deactivate other F4 keybind
                kmi.active = False

        if kmi.type == 'F7':
            if kmi.idname == 'scene.yp_use_simplify_toggle':
                f7_keybind_found = True
                kmi.active = True
            else:
                # Deactivate other F7 keybind
                kmi.active = False

        # Search for Shift Alt Z keybind
        if kmi.type == 'Z' and kmi.shift and kmi.alt:
            if kmi.idname == 'view3d.yp_material_shade_toggle':
                z_keybind_found = True
                kmi.active = True
            else:
                # Deactivate other Shift Alt Z keybind
                kmi.active = False

        # Search for D keybind
        if kmi.type == 'D':
            if kmi.idname == 'view3d.yp_only_render_toggle':
                d_keybind_found = True
                kmi.active = True
            else:
                # Deactivate other F7 keybind
                kmi.active = False

    # Set F4 Keybind
    if not f4_keybind_found:
        new_shortcut = km.keymap_items.new('paint.yp_image_paint_toggle', 'F4', 'PRESS')

    # Set F7 Keybind
    if not f7_keybind_found:
        new_shortcut = km.keymap_items.new('scene.yp_use_simplify_toggle', 'F7', 'PRESS')

    # Set Shift Alt Z keybind
    if not z_keybind_found:
        new_shortcut = km.keymap_items.new('view3d.yp_material_shade_toggle', 'Z', 'PRESS', shift=True, alt=True)

    # Set D Keybind
    if not d_keybind_found:
        new_shortcut = km.keymap_items.new('view3d.yp_only_render_toggle', 'D', 'PRESS')

def remove_keybind():
    wm = bpy.context.window_manager
    km = wm.keyconfigs.addon.keymaps.get('Object Non-modal')
    if km:
        for kmi in km.keymap_items:
            if ((kmi.type == 'F3' and kmi.idname == 'object.mode_set' and kmi.properties.mode == 'SCULPT') or
                (kmi.type == 'F4' and kmi.idname == 'object.mode_set' and kmi.properties.mode == 'TEXTURE_PAINT')):
                km.keymap_items.remove(kmi)
    km = wm.keyconfigs.addon.keymaps.get('Window')
    if km:
        for kmi in km.keymap_items:
            if ((kmi.type == 'F4' and kmi.idname == 'paint.yp_image_paint_toggle') or
                (kmi.type == 'F7' and kmi.idname == 'scene.yp_use_simplify_toggle') or
                (kmi.type == 'Z' and kmi.shift and kmi.alt and kmi.idname == 'view3d.yp_material_shade_toggle') or
                (kmi.type == 'D' and kmi.idname == 'view3d.yp_only_render_toggle')):
                km.keymap_items.remove(kmi)

def update_use_keybind(self, context):
    if not self.use_keybind:
        remove_keybind()
    else: set_keybind()

def update_enable_top_panel(self, context):
    if self.enable_top_panel:
        bpy.types.INFO_HT_header.remove(header_extras.original_global_header)
        bpy.types.INFO_HT_header.prepend(header_extras.modified_global_header)
    else:
        bpy.types.INFO_HT_header.remove(header_extras.modified_global_header)
        bpy.types.INFO_HT_header.prepend(header_extras.original_global_header)

def update_enable_bottom_panel(self, context):
    if self.enable_bottom_panel:
        bpy.types.VIEW3D_HT_header.append(header_extras.viewport_header_addition)
    else:
        bpy.types.VIEW3D_HT_header.remove(header_extras.viewport_header_addition)

class yPanelPreferences(AddonPreferences):
    # this must match the addon name, use '__package__'
    # when defining this in a submodule of a python package.
    bl_idname = __package__

    enable_top_panel = BoolProperty(
            name="Top Panel",
            default=True,
            update=update_enable_top_panel
            )

    enable_bottom_panel = BoolProperty(
            name="Bottom Panel",
            default=True,
            update=update_enable_bottom_panel
            )

    use_keybind = BoolProperty(
            name="Use yPanel Shortcuts",
            default=True,
            update=update_use_keybind,
            )

    def draw(self, context):
        layout = self.layout

        box = layout.box()
        row = box.row()
        row.prop(self, "enable_top_panel")
        row.prop(self, "enable_bottom_panel")

        box = layout.box()
        box.prop(self, "use_keybind")

        #col=layout.column(align=True)
        #box.label(text="yPanel Shortcuts:")
        row=box.row(align=True)
        col=row.column(align=True)
        col.label(text='F3')
        col.label(text='F4')
        col.label(text='F7')
        col.label(text='Shift + Alt + Z')
        col.label(text='D')
        col=row.column(align=True)
        col.label(text=': Sculpt Mode toggle')
        col.label(text=': Texture Paint Mode toggle (also works on Image Editor)')
        col.label(text=': Use Simplify toggle')
        col.label(text=': Material Shade toggle')
        col.label(text=': Only Render (viewport) toggle')

def register():
    set_keybind()

def unregister():
    remove_keybind()
