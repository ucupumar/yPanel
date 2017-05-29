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

class ToggleExtraHeader(bpy.types.Operator):
    bl_idname = "view3d.yp_toggle_extra_header"
    bl_label = "Toggle Extra Header"
    bl_description = "Toggle Extra Header"

    #header = EnumProperty(
    #    name = 'Header',
    #    items = (('GLOBAL', "Global", ""),
    #             ('VIEWPORT', "Viewport", "")),
    #    default = 'GLOBAL')

    @classmethod
    def poll(cls, context):
        return True

    def execute(self, context):
        scene = context.scene
        settings = scene.yp_props

        #if self.header == 'GLOBAL':
        #    settings.global_extra_header = not settings.global_extra_header
        #elif self.header == 'VIEWPORT':
        #    settings.viewport_extra_header = not settings.viewport_extra_header

        settings.global_extra_header = not settings.global_extra_header

        return {'FINISHED'}

class ToggleWire(bpy.types.Operator):
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
def mode_switcher_panel(self):

    obj = bpy.context.object

    row = self.layout.row(align=True)
    
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
    settings = scene.yp_props
    space = context.space_data
    gs = scene.game_settings 
    toolsettings = context.tool_settings
    mo_props = scene.mo_props
    screen = context.screen
    area = context.area

    if screen.show_fullscreen:
        screen = bpy.data.screens[screen.name[:-10]]
        # Search for original id on non fullscreen screen
        area_id = [i for i, a in enumerate(screen.areas) if (
                len(a.spaces) == 0 or (a.type == 'INFO' and i != 0)
                )][0]
    else: area_id = [i for i, a in enumerate(screen.areas) if a == area][0]
    active_ids = [int(i[2:]) for i in screen.yp_props.uncollapsed_header_extra.split()]

    layout = self.layout

    if area_id not in active_ids:
        layout.operator('view3d.yp_panel_toggle', icon='DOWNARROW_HLT', text='', emboss=False).panel = 'header_extra'
    else: 
        layout.operator('view3d.yp_panel_toggle', icon='RIGHTARROW', text='', emboss=False).panel = 'header_extra'

        #row = layout.row(align=True)
        #mode_switcher_panel(self)

        layout.prop(space, 'viewport_shade', text='', expand=True)
        layout.label('Shading: ' + shade_dict[space.viewport_shade])

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

            if space.viewport_shade == 'TEXTURED' and gs.material_mode == 'MULTITEXTURE':
                layout.prop(space, "show_textured_shadeless")

        layout.prop(space, 'show_only_render')
        layout.prop(space, "show_world")

        if space.viewport_shade == 'SOLID':
            layout.prop(space, "use_matcap")
            layout.prop(space, "show_textured_solid")

        layout.prop(space, "show_backface_culling")

        layout.prop(space.fx_settings, "use_ssao", text="AO")

        if space.region_3d.view_perspective == 'CAMERA':
            layout.prop(space.fx_settings, "use_dof", text='DOF')

        layout.prop(scene.render, 'use_simplify', text='Simplify')
        if scene.render.use_simplify:
            layout.prop(scene.render, 'simplify_subdivision', text='Level')
        
        row = layout.row()
        row.enabled = not space.show_only_render
        #if not space.show_only_render:
        row.operator('view3d.yp_toggle_display_wire', text='Wire')

        #if context.mode in {'OBJECT', 'EDIT'}:
        #    layout.prop(toolsettings, "snap_element", icon_only=True, expand=True)
        layout.prop(scene, "frame_current", text="")

def global_header_addition(self, context):
    scene = context.scene
    settings = scene.yp_props

    row = self.layout.row()

    if not settings.global_extra_header:
        #row.operator('view3d.yp_toggle_extra_header', icon='DOWNARROW_HLT', text='', emboss=False).header = 'GLOBAL'
        row.operator('view3d.yp_toggle_extra_header', icon='DOWNARROW_HLT', text='', emboss=False)
    else: 
        #row.operator('view3d.yp_toggle_extra_header', icon='RIGHTARROW', text='', emboss=False).header = 'GLOBAL'
        row.operator('view3d.yp_toggle_extra_header', icon='RIGHTARROW', text='', emboss=False)
        #row.template_layers()
        #scene = context.scene
        #row.prop(scene, 'layers', text='')
        #col = row.column(align=True)
        #col.prop(scene, 'layers', index=0, toggle=True, text='')
        #col.prop(scene, 'layers', index=10, toggle=True, text='')
        mode_switcher_panel(self)

        obj = context.object
        row = self.layout.row()
        if obj:
            #row = self.layout.row(align=True)
            row.label("Mode: " + mode_dict[obj.mode])
        else:
            row.label("No object selected!")

class SceneYPanelSetting(bpy.types.PropertyGroup):
    global_extra_header = BoolProperty(default=True)
    #viewport_extra_header = BoolProperty(default=True)

def register():
    bpy.types.Scene.yp_props = PointerProperty(type=SceneYPanelSetting)

    bpy.types.VIEW3D_HT_header.append(viewport_header_addition)
    bpy.types.INFO_HT_header.append(global_header_addition)

def unregister():
    # Remove extra panels
    bpy.types.VIEW3D_HT_header.remove(viewport_header_addition)
    bpy.types.INFO_HT_header.remove(global_header_addition)
