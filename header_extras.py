import bpy, os
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

mode_icon_dict = {
        'OBJECT' : 'OBJECT_DATAMODE',
        'EDIT' : 'EDITMODE_HLT',
        'POSE' : 'POSE_HLT',
        'SCULPT' : 'SCULPTMODE_HLT',
        'VERTEX_PAINT' : 'VPAINT_HLT',
        'WEIGHT_PAINT' : 'WPAINT_HLT',
        'TEXTURE_PAINT' : 'TPAINT_HLT',
        'PARTICLE_EDIT' : 'PARTICLEMODE',
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

def is_inner_brighter_than_inner_sel():
    ui = bpy.context.user_preferences.themes[0].user_interface
    inner = ui.wcol_regular.inner
    inner_sel = ui.wcol_regular.inner_sel

    # Get luminance
    inner_lum = inner[0]  * 0.33 + inner[1] * 0.5 + inner[2] * 0.17
    inner_sel_lum = inner_sel[0]  * 0.33 + inner_sel[1] * 0.5 + inner_sel[2] * 0.17

    return inner_lum > inner_sel_lum

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

class YPSculptSettings(bpy.types.Operator):
    bl_idname = "view3d.yp_sculpt_settings"
    bl_label = "Sculpt Settings"
    bl_description = "Sculpt Settings"

    @classmethod
    def poll(cls, context):
        return context.object and context.object.mode == 'SCULPT'

    def draw(self, context):
        sculpt = context.scene.tool_settings.sculpt
        col = self.layout.column(align=True)

        col.prop(sculpt, "radial_symmetry", text='Radial')
        col.prop(sculpt, "use_symmetry_feather", text="Feather")

        row = col.row(align=True)
        row.label(text="Tiling:")
        row.prop(sculpt, "tile_x", text="X", toggle=True)
        row.prop(sculpt, "tile_y", text="Y", toggle=True)
        row.prop(sculpt, "tile_z", text="Z", toggle=True)
        col.prop(sculpt, "tile_offset", text="Tile Offset")

    def execute(self, context):
        return context.window_manager.invoke_popup(self, width=180) 

class YPSculptShadeSmoothOrFlat(bpy.types.Operator):
    bl_idname = "object.yp_shade_smooth_flat"
    bl_label = "Shade Smooth or Flat"
    bl_description = "Shade Smooth or Flat"

    shade = EnumProperty(
            name = 'Shade',
            description = 'Shade',
            items = (('SMOOTH', 'Smooth', ''),
                    ('FLAT', 'Flat', '')),
            default = 'SMOOTH')

    @classmethod
    def poll(cls, context):
        return context.object and context.object.type == 'MESH'

    def execute(self, context):
        scene = context.scene

        ori_selects = [o for o in scene.objects if o.select]
        for o in scene.objects:
            if o != context.object: 
                o.select = False

        context.object.select = True
        if self.shade == 'SMOOTH':
            bpy.ops.object.shade_smooth()
        else: bpy.ops.object.shade_flat()

        for o in scene.objects:
            if o in ori_selects:
                o.select = True
            else: o.select = False

        return {'FINISHED'}

class YPMultiresAdd(bpy.types.Operator):
    bl_idname = "object.yp_multires_add"
    bl_label = "Add Multires Modifier"
    bl_description = "Add Multires Modifier"

    apply_modifiers = EnumProperty(
            name = 'Apply Modifiers',
            description='Apply Modifiers (The original mesh will be backed up on layer 19)',
            items = (
                ('NONE', 'None', ''),
                ('ALL', 'All', ''),
                ('ABOVE_RIG', 'Only above Subsurf/Armature', '')),
            default = 'NONE')

    shade_flat = BoolProperty(
            name= 'Shade Flat',
            description = 'Shade Flat',
            default = True)

    @classmethod
    def poll(cls, context):
        return context.object and context.object.mode == 'SCULPT'

    def invoke(self, context, event):
        obj = context.object
        if len(obj.modifiers) > 0 :
            return context.window_manager.invoke_props_dialog(self, width=275)
        return self.execute(context)

    def draw(self, context):
        row = self.layout.split(percentage=0.4)
        col = row.column(align=True)
        col.label('Apply Modifiers:') #, icon='MODIFIER')
        col.label('')
        col.label('')
        col.label('Shade Flat:')

        col = row.column(align=True)
        col.prop(self, 'apply_modifiers', expand=True)
        col.prop(self, 'shade_flat', text='')

    def execute(self, context):
        scene = context.scene
        obj = context.object

        # Variable for subsurf
        subsurf_idx = -1
        subsurf_level = 0
        subsurf_type = 'CATMULL_CLARK'
        subsurf_show_viewport = False

        if self.apply_modifiers in {'ALL', 'ABOVE_RIG'}:

            # Backup original mesh
            bak_name = 'BACKUP-MULTIRES-' + obj.name
            bak_obj = obj.copy()
            bak_obj.data = bak_obj.data.copy()
            bak_obj.name = bak_name
            scene.objects.link(bak_obj)

            # Remove groups from duplicate object
            for g in bpy.data.groups:
                for o in g.objects:
                    if o == bak_obj:
                        g.objects.unlink(bak_obj)
                        break

            # Move duplicated object to layer 19
            for i in reversed(range(20)):
                if i == 19: bak_obj.layers[i] = True
                else: bak_obj.layers[i] = False

            obj.yp_he.backup_object = bak_obj

            # Make sure object data single user
            if obj.data.users > 1:
                obj.data = obj.data.copy()

            if self.apply_modifiers == 'ALL':
                for m in obj.modifiers:
                    bpy.ops.object.modifier_apply(apply_as='DATA', modifier=m.name)
            else:
                # Search for armature
                armature = None
                for i, m in enumerate(obj.modifiers):
                    if m.type == 'ARMATURE' and not armature:
                        armature = m

                # If armature found, apply all modifier above it
                if armature:
                    for m in obj.modifiers:
                        if m == armature: break
                        bpy.ops.object.modifier_apply(apply_as='DATA', modifier=m.name)

                # Now search for subsurf
                subsurf = None
                for i, m in enumerate(obj.modifiers):
                    if m.type == 'SUBSURF' and not subsurf:
                        subsurf = m
                        subsurf_idx = i
                        subsurf_level = m.levels
                        subsurf_type = m.subdivision_type
                        subsurf_show_viewport = m.show_viewport

                if subsurf:
                    # Apply modifiers above subsurf
                    for m in obj.modifiers:
                        if m == subsurf: break
                        if m.type == 'ARMATURE': continue
                        bpy.ops.object.modifier_apply(apply_as='DATA', modifier=m.name)

                    obj.modifiers.remove(subsurf)

                # If subsurf and armature not found, no need to use backup object
                if not armature and not subsurf:
                    bpy.data.objects.remove(bak_obj)

        mod = obj.modifiers.new('Multires', 'MULTIRES')
        mod.subdivision_type = subsurf_type

        if subsurf_idx > -1:
            # Get current modifier index which not necessarily on last index
            idx = len(obj.modifiers)-1
            for i, m in enumerate(obj.modifiers):
                if m == mod:
                    idx = i
                    break

            # Move modifier to subsurf index
            if idx > subsurf_idx:
                idx_diff = idx - subsurf_idx
                for i in range(idx_diff):
                    bpy.ops.object.modifier_move_up(modifier=mod.name)

            # Change the level
            if subsurf_show_viewport and subsurf_level > 0:
                for i in range(subsurf_level):
                    bpy.ops.object.multires_subdivide(modifier=mod.name)
                mod.levels = subsurf_level

        if self.shade_flat:
            bpy.ops.object.yp_shade_smooth_flat(shade='FLAT')

        return{'FINISHED'}

class YPMultiresRemove(bpy.types.Operator):
    bl_idname = "object.yp_multires_remove"
    bl_label = "Remove Multires Modifier"
    bl_description = "Remove Multires Modifier"
    bl_options = {'REGISTER', 'UNDO'}

    recover_backup = BoolProperty(
            name='Recover to original object',
            description='Try to recover previous subsurf modifier',
            default=True)

    @classmethod
    def poll(cls, context):
        return context.object and context.object.mode == 'SCULPT'

    def invoke(self, context, event):
        obj = context.object
        if obj.yp_he.backup_object:
            return context.window_manager.invoke_props_dialog(self, width=220)
        return self.execute(context)

    def draw(self, context):
        self.layout.prop(self, 'recover_backup')

    def execute(self, context):
        obj = context.object
        scene = context.scene

        if self.recover_backup and obj.yp_he.backup_object:

            # Remove all modifiers first
            for m in obj.modifiers:
                obj.modifiers.remove(m)

            # Get original object
            bak_obj = obj.yp_he.backup_object

            # Replace object data
            obj.data = bak_obj.data

            # Recover modifiers
            for m in bak_obj.modifiers:
                mod = obj.modifiers.new(m.name, m.type)
                attrs = dir(m)
                for attr in attrs:
                    if not attr.startswith(('__', 'bl_', 'rna_')):
                        try: setattr(mod, attr, getattr(m, attr))
                        except: pass

            # Remove duplicate object
            bpy.data.objects.remove(bak_obj)

            return {'FINISHED'}

        mod = [m for m in obj.modifiers if m.type == 'MULTIRES']
        if not mod: return {'CANCELLED'}
        mod = mod[0]
        obj.modifiers.remove(mod)

        # Remove duplicate object reference if user choose not to recover object
        #obj.yp_he.backup_object = None

        return {'FINISHED'}

class YPMultiresSubdivide(bpy.types.Operator):
    bl_idname = "object.yp_multires_subdivide"
    bl_label = "Multires Subdivide"
    bl_description = "Multires Subdivide"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        obj = context.object
        return any([m for m in obj.modifiers if m.type == 'MULTIRES'])
        #return hasattr(context, 'multires')

    def execute(self, context):
        obj = context.object

        if hasattr(context, 'multires'):
            mod = context.multires
        else: mod = [m for m in obj.modifiers if m.type == 'MULTIRES'][0]

        bpy.ops.object.multires_subdivide(modifier=mod.name)
        mod.levels = mod.sculpt_levels

        return {'FINISHED'}

class YPMultiresChangeSculptLevel(bpy.types.Operator):
    bl_idname = "object.yp_multires_change_sculpt_level"
    bl_label = "Change Multires Sculpt Level"
    bl_description = "Change multires Sculpt Level"
    bl_options = {'REGISTER', 'UNDO'}

    direction = EnumProperty(
            name='Direction',
            items = (('UP', 'Up', ''),
                    ('DOWN', 'Down', '')),
            default='UP')

    @classmethod
    def poll(cls, context):
        obj = context.object
        return any([m for m in obj.modifiers if m.type == 'MULTIRES'])
        #return hasattr(context, 'multires')

    def execute(self, context):
        obj = context.object

        if hasattr(context, 'multires'):
            mod = context.multires
        else: mod = [m for m in obj.modifiers if m.type == 'MULTIRES'][0]

        if self.direction == 'UP':
            mod.sculpt_levels += 1
        else: mod.sculpt_levels -= 1

        mod.levels = mod.sculpt_levels
        mod.render_levels = mod.sculpt_levels

        return{'FINISHED'}

class YPMultiresSettings(bpy.types.Operator):
    bl_idname = "view3d.yp_multires_settings"
    bl_label = "Multires Settings"
    bl_description = "Multires Settings"

    @classmethod
    def poll(cls, context):
        return context.object and context.object.mode == 'SCULPT'

    def check(self, context):
        return True

    def draw(self, context):
        obj = context.object
        mod = [m for m in obj.modifiers if m.type == 'MULTIRES']
        if not mod:
            self.layout.label('Multires is removed!')
            return
        mod = mod[0]

        col = self.layout.column()
        #col.context_pointer_set('multires', mod)

        col.label('Sculpt Level: ' + str(mod.sculpt_levels) + '/' + str(mod.total_levels))
        #row.operator("object.multires_subdivide", text="Subdivide").modifier = mod.name
        col.operator("object.multires_higher_levels_delete", text="Delete Higher").modifier = mod.name
        #col.operator("object.multires_reshape", text="Reshape").modifier = mod.name
        col.operator("object.multires_base_apply", text="Apply Base").modifier = mod.name
        col.prop(mod, "use_subsurf_uv")
        #col.prop(mod, "show_only_control_edges")

        row = col.row(align=True)
        row.prop(mod, "subdivision_type", expand=True)
        col.separator()

        col.operator("object.yp_multires_remove", text="Delete Multires", icon='ERROR')

    def execute(self, context):
        return context.window_manager.invoke_popup(self, width=180) 

class YPDyntopoSettings(bpy.types.Operator):
    bl_idname = "view3d.yp_dyntopo_settings"
    bl_label = "Dyntopo Settings"
    bl_description = "Dyntopo Settings"

    @classmethod
    def poll(cls, context):
        return context.object and context.object.mode == 'SCULPT'

    def check(self, context):
        return True

    def draw(self, context):
        sculpt = context.tool_settings.sculpt

        col = self.layout.column()

        if (sculpt.detail_type_method == 'CONSTANT'):
            col.operator("sculpt.detail_flood_fill")

        #row = col.row(align=True)
        col.prop(sculpt, "symmetrize_direction") #, text='')
        col.operator("sculpt.symmetrize")

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
    obj = context.object
    space = context.space_data
    gs = scene.game_settings 
    toolsettings = context.tool_settings
    mo_props = scene.mo_props
    area = context.area
    ypui = context.window_manager.yp_ui

    layout = self.layout
    #brighter_inner = is_inner_brighter_than_inner_sel()
    #print(brighter_inner)

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
    #row.prop(space, "show_backface_culling", text='', icon='MOD_WIREFRAME')
    row.prop(space, "show_backface_culling", text='', icon='SNAP_FACE')

    if obj and obj.type == 'MESH' and obj.mode == 'EDIT':
        row.prop(space, 'show_occlude_wire', text='', icon='MOD_WIREFRAME')

    if scene.render.engine in {'BLENDER_RENDER', 'BLENDER_GAME'}: 
        if space.viewport_shade == 'TEXTURED' and gs.material_mode == 'MULTITEXTURE':
            row.prop(space, "show_textured_shadeless", text='', icon='POTATO')

    if space.viewport_shade == 'SOLID':
        row.prop(space, "show_textured_solid", text='', icon='TEXTURE_SHADED')

    row = layout.row(align=True)
    #icon = 'ao' if brighter_inner and not space.fx_settings.use_ssao else 'ao_light'
    #row.prop(space.fx_settings, "use_ssao", text="", icon_value=custom_icons[icon].icon_id)
    row.prop(space.fx_settings, "use_ssao", text="", icon_value=custom_icons['ao'].icon_id)
    if space.fx_settings.use_ssao:
        row.operator('view3d.yp_ao_settings', text='', icon='SCRIPTWIN')

    if space.viewport_shade == 'SOLID':
        row = layout.row(align=True)
        #icon = 'matcap' if brighter_inner and not space.use_matcap else 'matcap_light'
        #row.prop(space, "use_matcap", text='', icon_value=custom_icons[icon].icon_id)
        row.prop(space, "use_matcap", text='', icon_value=custom_icons['matcap'].icon_id)
        if space.use_matcap:
            row.menu('VIEW3D_PT_yp_matcap_menu', icon='MATCAP_' + space.matcap_icon, text='')

    if space.region_3d.view_perspective == 'CAMERA':
        row = layout.row(align=True)
        #icon = 'dof' if brighter_inner and not space.fx_settings.use_dof else 'dof_light'
        #row.prop(space.fx_settings, "use_dof", text='', icon_value=custom_icons[icon].icon_id)
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

    brighter_inner = is_inner_brighter_than_inner_sel()

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

    ### Custom Header Starts

    row = layout.row(align=True)

    screen = context.screen
    area = context.area
    ypui = scene.yp_ui

    # Search for viewport area
    view3d_found = False
    for a in screen.areas:
        if a.type == 'VIEW_3D':
            view3d_found = True
            break

    if view3d_found or (screen.show_fullscreen and area.type == 'VIEW_3D'):

        mode_switcher_panel(row)

        obj = context.object
        if obj:
            row.label(mode_dict[obj.mode] + ' Mode')
        else:
            row.label("Object Mode")

    # Original reports banner
    row.template_reports_banner()
    row.separator()

    if bpy.app.autoexec_fail is True and bpy.app.autoexec_fail_quiet is False:
        row.label("Auto-run disabled", icon='ERROR')
        if bpy.data.is_saved:
            props = row.operator("wm.revert_mainfile", icon='SCREEN_BACK', text="Reload Trusted")
            props.use_scripts = True

        row.operator("script.autoexec_warn_clear", text="Ignore")

        # include last so text doesn't push buttons out of the header
        row.label(bpy.app.autoexec_fail_message)
        row = layout.row(align=True)
        return

    if view3d_found or (screen.show_fullscreen and area.type == 'VIEW_3D'):

        if not obj or (obj and obj.mode == 'OBJECT'):

            row.prop(scene.render, 'use_simplify', text='Simplify', icon='MOD_DECIM')
            if scene.render.use_simplify:
                row.prop(scene.render, 'simplify_subdivision', text='Level')
            row.separator()

        elif obj and obj.mode == 'TEXTURE_PAINT':
            paint = bpy.context.tool_settings.image_paint

            row.label('Mirror:', icon='MOD_MIRROR')
            icon = 'x' if brighter_inner and not paint.use_symmetry_x else 'x_light'
            row.prop(paint, "use_symmetry_x", text="", icon_value=custom_icons[icon].icon_id)
            icon = 'y' if brighter_inner and not paint.use_symmetry_y else 'y_light'
            row.prop(paint, "use_symmetry_y", text="", icon_value=custom_icons[icon].icon_id)
            icon = 'z' if brighter_inner and not paint.use_symmetry_z else 'z_light'
            row.prop(paint, "use_symmetry_z", text="", icon_value=custom_icons[icon].icon_id)
            row.separator()

        elif obj and obj.mode == 'SCULPT':

            sculpt = context.tool_settings.sculpt

            row.label('Mirror:', icon='MOD_MIRROR')
            icon = 'x' if brighter_inner and not sculpt.use_symmetry_x else 'x_light'
            row.prop(sculpt, "use_symmetry_x", text="", icon_value=custom_icons[icon].icon_id)
            icon = 'y' if brighter_inner and not sculpt.use_symmetry_y else 'y_light'
            row.prop(sculpt, "use_symmetry_y", text="", icon_value=custom_icons[icon].icon_id)
            icon = 'z' if brighter_inner and not sculpt.use_symmetry_z else 'z_light'
            row.prop(sculpt, "use_symmetry_z", text="", icon_value=custom_icons[icon].icon_id)

            row = layout.row(align=True)
            row.label('Lock:', icon='LOCKED')
            icon = 'x' if brighter_inner and not sculpt.lock_x else 'x_light'
            row.prop(sculpt, "lock_x", text="", icon_value=custom_icons[icon].icon_id)
            icon = 'y' if brighter_inner and not sculpt.lock_y else 'y_light'
            row.prop(sculpt, "lock_y", text="", icon_value=custom_icons[icon].icon_id)
            icon = 'z' if brighter_inner and not sculpt.lock_z else 'z_light'
            row.prop(sculpt, "lock_z", text="", icon_value=custom_icons[icon].icon_id)

            row = layout.row(align=True)
            row.operator('view3d.yp_sculpt_settings', text='', icon='SCRIPTWIN')
            row.separator()

            if context.sculpt_object.use_dynamic_topology_sculpting:
                row.prop(sculpt, "use_smooth_shading", text='Smooth', toggle=True)
                row.separator()
            else:
                row.operator("object.yp_shade_smooth_flat", text="Smooth").shade = 'SMOOTH'
                row.operator("object.yp_shade_smooth_flat", text="Flat").shade = 'FLAT'
                row.separator()

            mod = [m for m in obj.modifiers if m.type == 'MULTIRES']
            if mod:
                mod = mod[0]
                row.label('Multires', icon='MOD_MULTIRES')
                row.context_pointer_set('multires', mod)
                row.operator("object.yp_multires_subdivide", text="", icon='ZOOMIN')
                row.operator("object.yp_multires_change_sculpt_level", text="", icon='TRIA_LEFT').direction = 'DOWN'
                row.operator("object.yp_multires_change_sculpt_level", text="", icon='TRIA_RIGHT').direction = 'UP'
                row.operator('view3d.yp_multires_settings', text='', icon='MODIFIER')
                row.label('Level: ' + str(mod.sculpt_levels) + '/' + str(mod.total_levels))

            elif context.sculpt_object.use_dynamic_topology_sculpting:
                row.alert = True
                row.operator("sculpt.dynamic_topology_toggle", text='Dyntopo', icon='MOD_TRIANGULATE')
                row.alert = False

                #row.separator()
                #row = self.layout.row(align=True)

                #icon = 'TRIA_RIGHT' if ypui.expand_dyntopo_type_method else 'TRIA_DOWN'
                #row.prop(ypui, 'expand_dyntopo_type_method', text='', emboss=False, icon=icon)

                #row = self.layout.row(align=True)

                #if ypui.expand_dyntopo_type_method:
                #    row.prop(sculpt, "detail_type_method", expand=True)
                #else: row.prop(sculpt, "detail_type_method", text='', expand=False)

                row.prop(sculpt, "detail_type_method", text='', expand=False)

                if (sculpt.detail_type_method == 'CONSTANT'):
                    row.prop(sculpt, "constant_detail_resolution", text='')
                    row.operator("sculpt.sample_detail_size", text="", icon='EYEDROPPER')
                elif (sculpt.detail_type_method == 'BRUSH'):
                    row.prop(sculpt, "detail_percent", text='')
                else:
                    row.prop(sculpt, "detail_size", text='')

                row.operator('view3d.yp_dyntopo_settings', text='', icon='SCRIPTWIN')
                row = self.layout.row(align=True)

                icon = 'TRIA_RIGHT' if ypui.expand_dyntopo_refine_method else 'TRIA_DOWN'
                row.prop(ypui, 'expand_dyntopo_refine_method', text='', emboss=False, icon=icon)
                row = self.layout.row(align=True)

                if ypui.expand_dyntopo_refine_method:
                    row.prop(sculpt, "detail_refine_method", expand=True)
                else: row.prop(sculpt, "detail_refine_method", text='', expand=False)

                row = self.layout.row(align=True)

            else:
                row.operator('object.yp_multires_add', text='Multires', icon='MOD_MULTIRES')
                row = self.layout.row(align=True)

                row.operator("sculpt.dynamic_topology_toggle", text='Dyntopo', icon='MOD_TRIANGULATE')
                row = self.layout.row(align=True)

        elif obj and obj.type == 'ARMATURE' and obj.mode == 'POSE':
            row.prop(obj.data, 'use_auto_ik', toggle=True)
            row.separator()

        elif obj and obj.type in {'MESH', 'ARMATURE'} and obj.mode in {'EDIT', 'WEIGHT_PAINT'}:
            row.prop(obj.data, 'use_mirror_x', text='X Mirror', icon='MOD_MIRROR')
            if obj.type == 'MESH' and obj.data.use_mirror_x:
                row.prop(obj.data, 'use_mirror_topology', text='Topology', toggle=True)
            row.separator()

        elif obj and obj.mode == 'PARTICLE_EDIT':
            pass

    ### Custom Header Ends

    row.operator("wm.splash", text="", icon='BLENDER', emboss=False)
    row.label(text=scene.statistics(), translate=False)

original_global_header = bpy.types.INFO_HT_header.draw

class YPHEBackup(bpy.types.PropertyGroup):
    backup_object = PointerProperty(type=bpy.types.Object)

def register():
    # Custom Icon
    global custom_icons
    custom_icons = bpy.utils.previews.new()
    filepath = get_addon_filepath() + 'icons' + os.sep
    custom_icons.load('matcap', filepath + 'matcap_icon.png', 'IMAGE')
    custom_icons.load('ao', filepath + 'ao_icon.png', 'IMAGE')
    custom_icons.load('dof', filepath + 'dof_icon.png', 'IMAGE')
    custom_icons.load('x', filepath + 'x_icon.png', 'IMAGE')
    custom_icons.load('y', filepath + 'y_icon.png', 'IMAGE')
    custom_icons.load('z', filepath + 'z_icon.png', 'IMAGE')
    custom_icons.load('x_light', filepath + 'x_light_icon.png', 'IMAGE')
    custom_icons.load('y_light', filepath + 'y_light_icon.png', 'IMAGE')
    custom_icons.load('z_light', filepath + 'z_light_icon.png', 'IMAGE')

    bpy.types.Object.yp_he = PointerProperty(type=YPHEBackup)

def unregister():
    # Custom Icon
    global custom_icons
    bpy.utils.previews.remove(custom_icons)
