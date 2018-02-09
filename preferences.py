import bpy
from . import header_extras
from bpy.types import Operator, AddonPreferences
from bpy.props import StringProperty, IntProperty, BoolProperty

particle_brush_items = [
    ("NONE"  , "None"  , "Don’t use any brush"         , 0),
    ("COMB"  , "Comb"  , "Comb hairs"                  , 1),
    ("SMOOTH", "Smooth", "Smooth hairs"                , 2),
    ("ADD"   , "Add"   , "Add hairs"                   , 3),
    ("LENGTH", "Length", "Make hairs longer or shorter", 4),
    ("PUFF"  , "Puff"  , "Make hairs stand up"         , 5),
    ("CUT"   , "Cut"   , "Cut hairs"                   , 6),
    ("WEIGHT", "Weight", "Weight hair particles"       , 7)
    ]

particle_brush_keys = ("ONE","TWO","THREE","FOUR","FIVE","SIX","SEVEN","EIGHT")

class PARTICLE_OT_yp_select_brush(bpy.types.Operator):
    """Select a particle brush"""
    bl_idname = "particle.yp_select_brush"
    bl_label  = "Particle Select Brush"

    brush = bpy.props.EnumProperty(
                name = "Brush",
                default = "NONE",
                items = particle_brush_items
                )

    @classmethod
    def poll(self, context):
        return context.object and context.object.mode == 'PARTICLE_EDIT'

    def execute(self, context):
        context.scene.tool_settings.particle_edit.tool = self.brush
        for region in context.area.regions:
            if region.type == "TOOLS":
                region.tag_redraw()
        return {'FINISHED'}

def set_keybind():
    wm = bpy.context.window_manager
     
    f3_keybind_found = False
    f4_keybind_found = False
    f7_keybind_found = False
    
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

        if kmi.type == 'F7':
            if kmi.idname == 'object.mode_set' and kmi.properties.mode == 'PARTICLE_EDIT':
                f7_keybind_found = True
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

    # Set F7 Keybind
    if not f4_keybind_found:
        new_shortcut = km.keymap_items.new('object.mode_set', 'F7', 'PRESS')
        new_shortcut.properties.mode = 'PARTICLE_EDIT'
        new_shortcut.properties.toggle = True

    f4_keybind_found = False
    f9_keybind_found = False
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

        if kmi.type == 'F9':
            if kmi.idname == 'scene.yp_use_simplify_toggle':
                f9_keybind_found = True
                kmi.active = True
            else:
                # Deactivate other F9 keybind
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
                # Deactivate other D keybind
                kmi.active = False

    # Set F4 Keybind
    if not f4_keybind_found:
        new_shortcut = km.keymap_items.new('paint.yp_image_paint_toggle', 'F4', 'PRESS')

    # Set F9 Keybind
    if not f9_keybind_found:
        new_shortcut = km.keymap_items.new('scene.yp_use_simplify_toggle', 'F9', 'PRESS')

    # Set Shift Alt Z keybind
    if not z_keybind_found:
        new_shortcut = km.keymap_items.new('view3d.yp_material_shade_toggle', 'Z', 'PRESS', shift=True, alt=True)

    # Set D Keybind
    if not d_keybind_found:
        new_shortcut = km.keymap_items.new('view3d.yp_only_render_toggle', 'D', 'PRESS')

    # Particle edit keybinds
    km = wm.keyconfigs.addon.keymaps.get('Particle')
    if not km:
        km = wm.keyconfigs.addon.keymaps.new('Particle')

    for i, key in enumerate(particle_brush_keys):
        kmi_found = False
        kmis = [k for k in km.keymap_items if k.type == key]
        if kmis: 
            for kmi in kmis:
                if kmi.idname == 'particle.yp_select_brush': 
                    kmi.active = True
                    kmi_found = True
                else:
                    kmi.active = False

        if not kmi_found:
            kmi = km.keymap_items.new(
                idname = "particle.yp_select_brush",
                type = key,
                value = "PRESS",
                )           
            kmi.properties.brush = particle_brush_items[i][0]

def remove_keybind():
    wm = bpy.context.window_manager

    km = wm.keyconfigs.addon.keymaps.get('Object Non-modal')
    if km:
        for kmi in km.keymap_items:
            if kmi.type in {'F3', 'F4', 'F7'}:
                if ((kmi.type == 'F3' and kmi.idname == 'object.mode_set' and kmi.properties.mode == 'SCULPT') or
                    (kmi.type == 'F4' and kmi.idname == 'object.mode_set' and kmi.properties.mode == 'TEXTURE_PAINT') or
                    (kmi.type == 'F7' and kmi.idname == 'object.mode_set' and kmi.properties.mode == 'PARTICLE_EDIT')):
                    km.keymap_items.remove(kmi)
                else: kmi.active = True

    km = wm.keyconfigs.addon.keymaps.get('Window')
    if km:
        for kmi in km.keymap_items:
            if kmi.type in {'F4', 'F9', 'Z', 'D'}:
                if ((kmi.type == 'F4' and kmi.idname == 'paint.yp_image_paint_toggle') or
                    (kmi.type == 'F9' and kmi.idname == 'scene.yp_use_simplify_toggle') or
                    (kmi.type == 'Z' and kmi.shift and kmi.alt and kmi.idname == 'view3d.yp_material_shade_toggle') or
                    (kmi.type == 'D' and kmi.idname == 'view3d.yp_only_render_toggle')):
                    km.keymap_items.remove(kmi)
                else: kmi.active = True

    km = wm.keyconfigs.addon.keymaps.get('Particle')
    if km:
        for kmi in km.keymap_items:
            if kmi.type in particle_brush_keys:
                if kmi.idname =='particle.yp_select_brush':
                    km.keymap_items.remove(kmi)
                else: kmi.active = True

def update_use_keybind(self, context):
    if not self.use_keybind:
        remove_keybind()
    else: set_keybind()

def toggle_top_panel(enable):
    if enable:
        bpy.types.INFO_HT_header.remove(header_extras.modified_global_header)
        bpy.types.INFO_HT_header.remove(header_extras.original_global_header)
        bpy.types.INFO_HT_header.prepend(header_extras.modified_global_header)
    else:
        bpy.types.INFO_HT_header.remove(header_extras.modified_global_header)
        bpy.types.INFO_HT_header.remove(header_extras.original_global_header)
        bpy.types.INFO_HT_header.prepend(header_extras.original_global_header)

def toggle_bottom_panel(enable):
    if enable:
        bpy.types.VIEW3D_HT_header.append(header_extras.viewport_header_addition)
    else:
        bpy.types.VIEW3D_HT_header.remove(header_extras.viewport_header_addition)

def update_enable_top_panel(self, context):
    toggle_top_panel(self.enable_top_panel)

def update_enable_bottom_panel(self, context):
    toggle_bottom_panel(self.enable_bottom_panel)

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
        col.label(text='F9')
        col.label(text='Shift + Alt + Z')
        col.label(text='D')
        col.label(text='1-8')
        col=row.column(align=True)
        col.label(text=': Sculpt Mode toggle')
        col.label(text=': Texture Paint Mode toggle (also works on Image Editor)')
        col.label(text=': Particle Edit Mode toggle')
        col.label(text=': Use Simplify toggle')
        col.label(text=': Material Shade toggle')
        col.label(text=': Only Render (viewport) toggle')
        col.label(text=': Change particle edit brush (Particle Edit Mode)')

def register():
    prefs = bpy.context.user_preferences.addons.get('yPanel')
    if not prefs: prefs = bpy.context.user_preferences.addons.get('yPanel-master')
    if prefs: 
        prefs = prefs.preferences
        if prefs.use_keybind:
            set_keybind()
        if prefs.enable_top_panel:
            toggle_top_panel(True)
        if prefs.enable_bottom_panel:
            toggle_bottom_panel(True)
    else:
        set_keybind()
        toggle_top_panel(True)
        toggle_bottom_panel(True)

def unregister():
    remove_keybind()
    toggle_top_panel(False)
    toggle_bottom_panel(False)
