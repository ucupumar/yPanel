import bpy
from bpy.props import *
from . import material_override
from .common import *

ob_type_support_editmode = ['MESH', 'FONT', 'CURVE', 'SURFACE', 'META', 'LATTICE', 'ARMATURE']

mode_dict = {
        'OBJECT' : 'Object',
        'EDIT' : 'Edit',
        'POSE' : 'Pose',
        'SCULPT' : 'Sculpt',
        'VERTEX_PAINT' : 'Vertex Paint',
        'WEIGHT_PAINT' : 'Weight Paint',
        'TEXTURE_PAINT' : 'Texture Paint',
        'PARTICLE_EDIT' : 'Particle Edit',
        }

shade_dict = {
        'BOUNDBOX' : 'Bounding Box',
        'WIREFRAME' : 'Wireframe',
        'SOLID' : 'Solid',
        'TEXTURED': 'Textured',
        'MATERIAL': 'Material',
        'RENDERED': 'Rendered'
        }

def matcap_items(self, context):
    items = []
    for i in range(1,25):
        items.append((str(i).zfill(2), 'Matcap ' + str(i), '', 'MATCAP_' + str(i).zfill(2), i))
    return items

class YPSetMatcap(bpy.types.Operator):
    bl_idname = "view3d.yp_set_matcap"
    bl_label = "Set Matcap"
    bl_description = "Set Matcap"

    matcap = EnumProperty(
            name = 'Matcap',
            description = 'Matcap',
            items = matcap_items
            )

    @classmethod
    def poll(cls, context):
        return context.area.type == 'VIEW_3D'

    def execute(self, context):
        space = context.space_data
        space.matcap_icon = self.matcap
        return {'FINISHED'}

class YPDOFSettings(bpy.types.Operator):
    bl_idname = "view3d.yp_dof_settings"
    #bl_label = "DOF Settings (Don't forget to press OK to apply)"
    bl_label = "DOF Settings"
    bl_description = "DOF Settings"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return context.area.type == 'VIEW_3D'

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self, width=220)

    def draw(self, context):
        scene = context.scene
        space = context.space_data
        cam = scene.camera.data
        
        col = self.layout.column()

        split = col.split(percentage=0.3)
        split.label(text="Focus:")
        split.prop(cam, "dof_object", text="")
        sub = col.column()
        sub.active = (cam.dof_object is None)
        sub.prop(cam, "dof_distance", text="Distance")

        hq_support = cam.gpu_dof.is_hq_supported
        sub = col.column()
        sub.active = hq_support
        sub.prop(cam.gpu_dof, "use_high_quality")
        col.prop(cam.gpu_dof, "fstop")

        if cam.gpu_dof.use_high_quality and hq_support:
            col.prop(cam.gpu_dof, "blades")
        else: col.label('')

        self.layout.label("Don't forget to press OK to apply", icon='ERROR')

    def check(self, context):
        return True

    def execute(self, context):
        scene = context.scene
        space = context.space_data
        cam = scene.camera.data

        cam.dof_object = cam.dof_object
        cam.dof_distance = cam.dof_distance
        cam.gpu_dof.use_high_quality = cam.gpu_dof.use_high_quality
        cam.gpu_dof.fstop = cam.gpu_dof.fstop
        cam.gpu_dof.blades = cam.gpu_dof.blades

        return{'FINISHED'}

class YPAOSettings(bpy.types.Operator):
    bl_idname = "view3d.yp_ao_settings"
    bl_label = "AO Settings"
    bl_description = "AO Settings"

    @classmethod
    def poll(cls, context):
        return context.area.type == 'VIEW_3D'

    def draw(self, context):
        space = context.space_data
        col = self.layout.column(align=True)
        ssao_settings = space.fx_settings.ssao

        if ssao_settings:
            col.prop(ssao_settings, "factor")
            col.prop(ssao_settings, "distance_max")
            col.prop(ssao_settings, "attenuation")
            col.prop(ssao_settings, "samples")
            col.prop(ssao_settings, "color")

    def execute(self, context):
        return context.window_manager.invoke_popup(self, width=180) 

class YPMatcapMenu(bpy.types.Menu):
    bl_idname = "VIEW3D_PT_yp_matcap_menu"
    bl_description = 'Matcap'
    bl_label = "Matcap"

    @classmethod
    def poll(cls, context):
        return context.area.type == 'VIEW_3D'

    def draw(self, context):
        row = self.layout.row()
        col = row.column()
        for i in range(1,25):
            if i == 13: col = row.column()
            col.operator('view3d.yp_set_matcap', text='Matcap ' + str(i), icon='MATCAP_' + str(i).zfill(2)
                    ).matcap = str(i).zfill(2)

class YPToggleWire(bpy.types.Operator):
    bl_idname = "view3d.yp_toggle_display_wire"
    bl_label = "Toggle Display Wire"
    bl_description = "Toggle Display Wire"

    @classmethod
    def poll(cls, context):
        return True

    def execute(self, context):
        obj = context.object

        not_wired_found = any([o for o in bpy.data.objects 
            if in_active_layer(o) and o.type in {'MESH', 'CURVE'} and not o.show_wire])

        if not obj or obj.type not in {'MESH', 'CURVE'}:
            if not_wired_found:
                for o in bpy.data.objects:
                    if o.type in {'MESH', 'CURVE'}:
                        o.show_wire = True
                        o.show_all_edges = True
            else:
                for o in bpy.data.objects:
                    if o.type in {'MESH', 'CURVE'}:
                        o.show_wire = False

            return {'FINISHED'}

        if obj.show_wire:
            if not_wired_found:
                for o in bpy.data.objects:
                    if o.type in {'MESH', 'CURVE'}:
                        o.show_wire = True
                        o.show_all_edges = True
            else:
                for o in bpy.data.objects:
                    if o.type in {'MESH', 'CURVE'}:
                        o.show_wire = False
        else:
            obj.show_wire = not obj.show_wire
            obj.show_all_edges = True

        return {'FINISHED'}

#PANELS
def mode_switcher_panel(layout):

    obj = bpy.context.object

    row = layout.row(align=True)
    
    if not obj or obj.mode == 'OBJECT':
        row.alert = True

    row.operator('object.mode_set', icon='OBJECT_DATAMODE', text='').mode = 'OBJECT'

    if not obj or obj.mode == 'OBJECT':
        row.alert = False

    if obj and in_active_layer(obj):

        use_mode_particle_edit = (
                len(obj.particle_systems) > 0 or
                obj.soft_body or
                any([mod for mod in obj.modifiers if mod.type == 'CLOTH']))

        if obj.type in ob_type_support_editmode:
            if obj.mode == 'EDIT': row.alert = True
            row.operator('object.mode_set', icon='EDITMODE_HLT', text='').mode = 'EDIT'
            if obj.mode == 'EDIT': row.alert = False
        
        if obj.type == 'ARMATURE':
            if obj.mode == 'POSE': row.alert = True
            row.operator('object.mode_set', icon='POSE_HLT', text='').mode = 'POSE'
            if obj.mode == 'POSE': row.alert = False
        
        if obj.type == 'MESH':
            if obj.mode == 'SCULPT': row.alert = True
            row.operator('object.mode_set', icon='SCULPTMODE_HLT', text='').mode = 'SCULPT'
            if obj.mode == 'SCULPT': row.alert = False

            if obj.mode == 'VERTEX_PAINT': row.alert = True
            row.operator('object.mode_set', icon='VPAINT_HLT', text='').mode = 'VERTEX_PAINT'
            if obj.mode == 'VERTEX_PAINT': row.alert = False

            if obj.mode == 'WEIGHT_PAINT': row.alert = True
            row.operator('object.mode_set', icon='WPAINT_HLT', text='').mode = 'WEIGHT_PAINT'
            if obj.mode == 'WEIGHT_PAINT': row.alert = False

            if obj.mode == 'TEXTURE_PAINT': row.alert = True
            row.operator('object.mode_set', icon='TPAINT_HLT', text='').mode = 'TEXTURE_PAINT'
            if obj.mode == 'TEXTURE_PAINT': row.alert = False

        if use_mode_particle_edit:
            if obj.mode == 'PARTICLE_EDIT': row.alert = True
            row.operator('object.mode_set', icon='PARTICLEMODE', text='').mode = 'PARTICLE_EDIT'
            if obj.mode == 'PARTICLE_EDIT': row.alert = False

def viewport_header_addition(self, context):
    scene = context.scene
    space = context.space_data
    gs = scene.game_settings 
    toolsettings = context.tool_settings
    mo_props = scene.mo_props
    area = context.area
    ypui = context.window_manager.yp_ui

    layout = self.layout

    #layout.label('', icon='BLANK1')

    icon = 'TRIA_RIGHT' if ypui.show_header_extra else 'TRIA_DOWN'
    layout.prop(ypui, 'show_header_extra', emboss=False, text='', icon=icon)
    if not ypui.show_header_extra:
        return

    if space.viewport_shade == 'RENDERED':
        layout.label('No settings for rendered view!')
        return

    #layout.prop(space, 'viewport_shade', text='', expand=True)
    #layout.label('Shading: ' + shade_dict[space.viewport_shade])

    row = layout.row(align=True)
    row.prop(space, 'show_only_render', text='', icon='SMOOTH')
    row.prop(space, "show_world", text='', icon='WORLD')
    row.prop(space, "show_backface_culling", text='', icon='MOD_WIREFRAME')

    if scene.render.engine in {'BLENDER_RENDER', 'BLENDER_GAME'}: 
        if space.viewport_shade == 'TEXTURED' and gs.material_mode == 'MULTITEXTURE':
            row.prop(space, "show_textured_shadeless", text='', icon='POTATO')

    if space.viewport_shade == 'SOLID':
        row.prop(space, "show_textured_solid", text='', icon='TEXTURE_SHADED')

    row = layout.row(align=True)
    row.prop(space.fx_settings, "use_ssao", text="", icon_value=custom_icons['ao'].icon_id)
    if space.fx_settings.use_ssao:
        row.operator('view3d.yp_ao_settings', text='', icon='SCRIPTWIN')

    if space.viewport_shade == 'SOLID':
        row = layout.row(align=True)
        row.prop(space, "use_matcap", text='', icon_value=custom_icons["matcap"].icon_id)
        if space.use_matcap:
            row.menu('VIEW3D_PT_yp_matcap_menu', icon='MATCAP_' + space.matcap_icon, text='')

    if space.region_3d.view_perspective == 'CAMERA':
        row = layout.row(align=True)
        row.prop(space.fx_settings, "use_dof", text='', icon_value=custom_icons['dof'].icon_id)
        if space.fx_settings.use_dof:
            row.operator('view3d.yp_dof_settings', text='', icon='SCRIPTWIN')

    row = layout.row()
    row.enabled = not space.show_only_render
    #if not space.show_only_render:
    row.operator('view3d.yp_toggle_display_wire', text='', icon='WIRE')

    #layout.prop(scene, "frame_current", text="Frame")

    if scene.render.engine in {'BLENDER_RENDER', 'BLENDER_GAME'}: 
        if space.viewport_shade == 'TEXTURED':
            layout.prop(gs, "material_mode", expand=True)

        if ((gs.material_mode == 'GLSL' and space.viewport_shade == 'TEXTURED')
            or space.viewport_shade == 'MATERIAL'):

            if mo_props.override_mode == 'OFF':
                layout.operator_menu_enum("material.yp_override_material_menu_enum", "mode", 
                        icon='MATERIAL', text='Material Override')
            else:
                layout.alert = True
                layout.operator('material.yp_override_material', 
                        icon = material_override.mo_icons[mo_props.override_mode],
                        text = material_override.mo_names[mo_props.override_mode]).mode = 'OFF'
                layout.alert = False

        elif mo_props.override_mode != 'OFF':
            layout.alert = True
            layout.operator('material.yp_override_material', icon='CANCEL', text='Recover Material').mode = 'OFF'
            layout.alert = False

def modified_global_header(self, context):
    layout = self.layout

    window = context.window
    scene = context.scene
    rd = scene.render

    row = layout.row(align=True)
    row.template_header()

    bpy.types.INFO_MT_editor_menus.draw_collapsible(context, layout)

    if window.screen.show_fullscreen:
        layout.operator("screen.back_to_previous", icon='SCREEN_BACK', text="Back to Previous")
        layout.separator()
    else:
        layout.template_ID(context.window, "screen", new="screen.new", unlink="screen.delete")
        layout.template_ID(context.screen, "scene", new="scene.new", unlink="scene.delete")

    layout.separator()

    if rd.has_multiple_engines:
        layout.prop(rd, "engine", text="")

    layout.separator()

    layout.template_running_jobs()

    layout.template_reports_banner()

    row = layout.row(align=True)

    if bpy.app.autoexec_fail is True and bpy.app.autoexec_fail_quiet is False:
        row.label("Auto-run disabled", icon='ERROR')
        if bpy.data.is_saved:
            props = row.operator("wm.revert_mainfile", icon='SCREEN_BACK', text="Reload Trusted")
            props.use_scripts = True

        row.operator("script.autoexec_warn_clear", text="Ignore")

        # include last so text doesn't push buttons out of the header
        row.label(bpy.app.autoexec_fail_message)
        return

    mode_switcher_panel(row)

    obj = context.object
    if obj:
        row.label(mode_dict[obj.mode] + ' Mode')
    else:
        row.label("Object Mode")

    row.prop(scene.render, 'use_simplify', text='', icon='MOD_DECIM')
    if scene.render.use_simplify:
        row.prop(scene.render, 'simplify_subdivision', text='Simplify Level')

    row.separator()

    row.operator("wm.splash", text="", icon='BLENDER', emboss=False)
    row.label(text=scene.statistics(), translate=False)

original_global_header = bpy.types.INFO_HT_header.draw

def register():
    # Custom Icon
    global custom_icons
    custom_icons = bpy.utils.previews.new()
    custom_icons.load('matcap', get_addon_filepath() + 'matcap_icon.png', 'IMAGE')
    custom_icons.load('ao', get_addon_filepath() + 'ao_icon.png', 'IMAGE')
    custom_icons.load('dof', get_addon_filepath() + 'dof_icon.png', 'IMAGE')

def unregister():
    # Custom Icon
    global custom_icons
    bpy.utils.previews.remove(custom_icons)
