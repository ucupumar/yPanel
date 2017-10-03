bl_info = {
    "name": "yPanel",
    "author": "Yusuf Umar",
    "version": (0, 1, 0),
    "blender": (2, 77, 0),
    "location": "3D View > Properties Panel > Top Row",
    "description": "Panel for some of your realtime content creation needs",
    "wiki_url": "http://twitter.com/ucupumar",
    "category": "3D View",
}

if "bpy" in locals():
    import imp
    #imp.reload(common)
    imp.reload(paint_slots)
    imp.reload(material_override)
    imp.reload(bake_tools)
    imp.reload(header_extras)
    #print("Reloaded yPanel multifiles")     
else:
    from . import paint_slots, material_override, bake_tools, header_extras #, common
    #print("Imported yPanel multifiles")     

import bpy, math, os
from mathutils import *
from bpy.app.handlers import persistent
from bpy.props import *
import bpy.utils.previews
from .common import *

class TogglePanel(bpy.types.Operator):
    bl_idname = "view3d.yp_panel_toggle"
    bl_label = "Toggle Panel"
    bl_description = "Toggle Panel"

    panel = StringProperty(default='')

    @classmethod
    def poll(cls, context):
        return context.area.type == 'VIEW_3D'
    
    def execute(self, context):
        screen = context.screen
        props = screen.yp_props
        area = context.area

        attr = [p for p in dir(props) if p.replace(self.panel, '') in {'collapsed_', 'uncollapsed_'}]
        if not attr: return {'FINISHED'}
        attr = attr[0]

        if screen.show_fullscreen:
            screen = bpy.data.screens[screen.name[:-10]]
            props = screen.yp_props
            idx = [i for i, a in enumerate(screen.areas) if (
                    len(a.spaces) == 0 or (a.type == 'INFO' and i != 0)
                    )][0]
        else: idx = [i for i, a in enumerate(screen.areas) if a == area][0]

        ids = [int(i[2:]) for i in getattr(props, attr).split()]

        if idx not in ids:
            setattr(props, attr, getattr(props, attr) + 'id' + str(idx) + ' ')
        else: setattr(props, attr, getattr(props, attr).replace('id' + str(idx) + ' ', ''))

        return {'FINISHED'}

# PANELS
class VIEW3D_PT_ypanel(bpy.types.Panel):
    bl_label = 'yPanel'
    bl_space_type = 'VIEW_3D'
    bl_context = "object"
    bl_region_type = 'UI'
    bl_options = {'DEFAULT_CLOSED'} 
    #bl_options = {'HIDE_HEADER'} 

    @classmethod
    def poll(cls,context):
        #return (context.active_object and (context.mode == 'PAINT_TEXTURE'))
        #return context.object
        return True

    def is_collapsed(self, panel):
        if self.panels[panel].collapse and self.id in self.panels[panel].ids:
            return True
        if not self.panels[panel].collapse and self.id not in self.panels[panel].ids:
            return True
        return False

    def object_panel(self):
        obj = bpy.context.object

        # Object name
        row = self.layout.row(align=True)
        row.prop(obj, "name", text="Object")

        if self.is_collapsed('object_setting'):
            row.operator('view3d.yp_panel_toggle', icon='SCRIPTWIN', text='').panel = 'object_setting'
        else:
            row.alert=True
            row.operator('view3d.yp_panel_toggle', icon='SCRIPTWIN', text='').panel = 'object_setting'
            row.alert=False

            box = self.layout.box()
            col = box.column(align=True)
            col.label('Draw Type:')
            row = col.row(align=True)
            row.prop(obj, 'draw_type', expand=True)

    def mode_panel(self):
    
        obj = bpy.context.object
    
        row = self.layout.row(align=True)
    
        # If mode panel is collapsed
        #if self.is_collapsed('mode_panel'):
        #    row.operator('view3d.yp_panel_toggle', icon='TRIA_RIGHT', text='', emboss=False).panel = 'mode_panel'
        #    row.label('Mode: ' + header_extras.mode_dict[obj.mode])
        #    return
    
        #row.operator('view3d.yp_panel_toggle', icon='TRIA_DOWN', text='', emboss=False).panel = 'mode_panel'
        if not obj:
            row.label('Mode: ' + header_extras.mode_dict['OBJECT'])
        else:
            row.label('Mode: ' + header_extras.mode_dict[obj.mode])
    
        row = self.layout.row(align=True)
    
        header_extras.mode_switcher_panel(self)

    def shading_panel(self):

        space = bpy.context.space_data
        gs = bpy.context.scene.game_settings 
        scene = bpy.context.scene
        obj = bpy.context.object

        row = self.layout.row(align=True)
        #if self.is_collapsed('shading_panel'):
        #    row.operator('view3d.yp_panel_toggle', icon='TRIA_RIGHT', text='', emboss=False).panel = 'shading_panel'
        #    row.label('Shading: ' + header_extras.shade_dict[space.viewport_shade])
        #    return
        
        #row.operator('view3d.yp_panel_toggle', icon='TRIA_DOWN', text='', emboss=False).panel = 'shading_panel'
        #row.operator('view3d.toggle_shading_panel', icon='TRIA_DOWN', text='', emboss=False)
        row.label('Shading: ' + header_extras.shade_dict[space.viewport_shade])

        #box = self.layout.box()
        #row = box.row(align=True)
        row = self.layout.row(align=True)
        row.prop(space, 'viewport_shade', text='', expand=True)
        row = row.row()
        if self.is_collapsed('shading_setting'):
            row.operator('view3d.yp_panel_toggle', icon='SCRIPTWIN', text='').panel = 'shading_setting'
        else:
            row.alert=True
            row.operator('view3d.yp_panel_toggle', icon='SCRIPTWIN', text='').panel = 'shading_setting'
            row.alert=False

            if space.viewport_shade == 'RENDERED':
                box = self.layout.box()
                box.label('Rendered shading has no settings!')
            else:
            #if space.viewport_shade != 'RENDERED':

                box = self.layout.box()
                col = box.column(align=True)
                row = col.row(align=True)
                if (scene.render.engine in {'BLENDER_RENDER', 'BLENDER_GAME'} and 
                    space.viewport_shade == 'TEXTURED'):
                    row.prop(gs, "material_mode", expand=True)
                    col.separator()

                row = col.row(align=True)
                row.prop(space, 'show_only_render')
                if self.is_collapsed('viewport_visual_setting'):
                    row.operator('view3d.yp_panel_toggle', icon='SCRIPTWIN', text='').panel = 'viewport_visual_setting'
                else:
                    row.alert=True
                    row.operator('view3d.yp_panel_toggle', icon='SCRIPTWIN', text='').panel = 'viewport_visual_setting'
                    row.alert=False

                    col = box.column()
                    inbox = col.box()
                    incol = inbox.column(align=True)
                    incol.active = not space.show_only_render

                    incol.prop(space, "show_outline_selected")
                    incol.prop(space, "show_all_objects_origin")
                    incol.prop(space, "show_relationship_lines")

                    split = incol.split(percentage=0.55)
                    split.prop(space, "show_floor", text="Grid Floor")

                    row = split.row(align=True)
                    row.prop(space, "show_axis_x", text="X", toggle=True)
                    row.prop(space, "show_axis_y", text="Y", toggle=True)
                    row.prop(space, "show_axis_z", text="Z", toggle=True)

                    sub = incol.column(align=True)
                    sub.active = space.show_floor
                    sub.prop(space, "grid_lines", text="Lines")
                    sub.prop(space, "grid_scale", text="Scale")
                    subsub = sub.column(align=True)
                    subsub.active = scene.unit_settings.system == 'NONE'
                    subsub.prop(space, "grid_subdivisions", text="Subdivisions")

                col.prop(space, "show_world")

                if space.viewport_shade == 'TEXTURED':
                    if scene.render.use_shading_nodes or gs.material_mode != 'GLSL':
                        col.prop(space, "show_textured_shadeless")
                if space.viewport_shade == 'SOLID':
                    col.prop(space, "show_textured_solid")
                    row = col.row(align=True)
                    row.prop(space, "use_matcap")
                    if self.is_collapsed('matcap_setting'):
                        row.operator('view3d.yp_panel_toggle', icon='SCRIPTWIN', text='').panel = 'matcap_setting'
                    else:
                        row.alert=True
                        row.operator('view3d.yp_panel_toggle', icon='SCRIPTWIN', text='').panel = 'matcap_setting'
                        row.alert=False

                        sub = col.column()
                        sub.active = space.use_matcap
                        sub.template_icon_view(space, "matcap_icon")

                col.prop(space, "show_backface_culling")
                if space.viewport_shade not in {'BOUNDBOX', 'WIREFRAME'}:
                    if obj and obj.mode == 'EDIT':
                        col.prop(space, "show_occlude_wire")
                if space.viewport_shade not in {'BOUNDBOX', 'WIREFRAME'}:

                    # DOF
                    if space.region_3d.view_perspective == 'CAMERA':
                        row = col.row(align=True)
                        row.prop(space.fx_settings, "use_dof")
                        if self.is_collapsed('dof_setting'):
                            row.operator('view3d.yp_panel_toggle', icon='SCRIPTWIN', text='').panel = 'dof_setting'
                        else:
                            row.alert=True
                            row.operator('view3d.yp_panel_toggle', icon='SCRIPTWIN', text='').panel = 'dof_setting'
                            row.alert=False

                            cam = scene.camera.data
                            dof_options = cam.gpu_dof
                            
                            col = box.column()
                            inbox = col.box()
                            incol = inbox.column()
                            incol.active = space.fx_settings.use_dof

                            split = incol.split(percentage=0.3)
                            split.label(text="Focus:")
                            split.prop(cam, "dof_object", text="")
                            sub = incol.column()
                            sub.active = (cam.dof_object is None)
                            sub.prop(cam, "dof_distance", text="Distance")

                            hq_support = dof_options.is_hq_supported
                            sub = incol.column()
                            sub.active = hq_support
                            sub.prop(dof_options, "use_high_quality")
                            incol.prop(dof_options, "fstop")
                            if dof_options.use_high_quality and hq_support:
                                incol.prop(dof_options, "blades")
                            

                    # SSAO
                    row = col.row(align=True)
                    row.prop(space.fx_settings, "use_ssao", text="Ambient Occlusion")
                    if self.is_collapsed('ssao_setting'):
                        row.operator('view3d.yp_panel_toggle', icon='SCRIPTWIN', text='').panel = 'ssao_setting'
                    else:
                        row.alert=True
                        row.operator('view3d.yp_panel_toggle', icon='SCRIPTWIN', text='').panel = 'ssao_setting'
                        row.alert=False
                        
                        col = box.column()
                        inbox = col.box()
                        incol = inbox.column(align=True)
                        incol.active = space.fx_settings.use_ssao

                        ssao_settings = space.fx_settings.ssao

                        if ssao_settings:
                            incol.prop(ssao_settings, "factor")
                            incol.prop(ssao_settings, "distance_max")
                            incol.prop(ssao_settings, "attenuation")
                            incol.prop(ssao_settings, "samples")
                            incol.prop(ssao_settings, "color")

                    row = col.row(align=True)
                    row.prop(scene.render, 'use_simplify', text='Simplify')
                    if self.is_collapsed('simplify_setting'):
                        row.operator('view3d.yp_panel_toggle', icon='SCRIPTWIN', text='').panel = 'simplify_setting'
                    else:
                        row.alert=True
                        row.operator('view3d.yp_panel_toggle', icon='SCRIPTWIN', text='').panel = 'simplify_setting'
                        row.alert=False

                        col = box.column()
                        inbox = col.box()
                        incol = inbox.column(align=True)
                        incol.active = space.fx_settings.use_ssao

                        incol.prop(scene.render, 'simplify_subdivision', text='Subdivision')
                        incol.prop(scene.render, 'simplify_child_particles', text='Child Particles')

                col.separator()

                if space.region_3d.view_perspective != 'CAMERA':
                    row = col.row(align=True)
                    row.prop(space, 'lens')
                    if self.is_collapsed('viewcam_setting'):
                        row.operator('view3d.yp_panel_toggle', icon='SCRIPTWIN', text='').panel = 'viewcam_setting'
                    else:
                        row.alert=True
                        row.operator('view3d.yp_panel_toggle', icon='SCRIPTWIN', text='').panel = 'viewcam_setting'
                        row.alert=False
                        col = box.column()
                        inbox = col.box()
                        incol = inbox.column(align=True)
                        incol.label(text="Clip:")
                        incol.prop(space, "clip_start", text="Start")
                        incol.prop(space, "clip_end", text="End")

    def material_override_recover_panel(self):

        col = self.layout.column()
        row = col.row(align=True)

        if self.is_collapsed('material_mask_recover'):
            row.operator('view3d.yp_panel_toggle', icon='TRIA_RIGHT', text='', emboss=False).panel = 'material_mask_recover'
            row.label('Material Override')
            return

        row.operator('view3d.yp_panel_toggle', icon='TRIA_DOWN', text='', emboss=False).panel = 'material_mask_recover'
        row.label('Material Override')

        box = col.box()
        col = box.column()

        col.alert = True
        col.operator("material.yp_override_material", text="Recover All Materials", icon='CANCEL').mode = 'OFF'
        col.alert = False

    def material_override_panel(self):

        scene = bpy.context.scene
        obj = bpy.context.object
        screen = bpy.context.screen
        area = bpy.context.area
        space = bpy.context.space_data
        mo_mode = scene.mo_props.override_mode

        col = self.layout.column()
        row = col.row(align=True)

        if self.is_collapsed('material_mask'):
            row.operator('view3d.yp_panel_toggle', icon='TRIA_RIGHT', text='', emboss=False).panel = 'material_mask'
            row.label('Material Override')
            return
        
        row.operator('view3d.yp_panel_toggle', icon='TRIA_DOWN', text='', emboss=False).panel = 'material_mask'
        row.label('Material Override')

        box = col.box()
        col = box.column()

        row = col.row(align=True)
        row.label('Diffuse:')

        if scene.mo_props.override_mode == 'DIFFUSE':
            row.alert = True
            row.operator("material.yp_override_material", text="Color", icon='POTATO').mode = 'OFF'
            row.alert = False
        else: row.operator("material.yp_override_material", text="Color", icon='POTATO').mode = 'DIFFUSE'

        if scene.mo_props.override_mode == 'DIFFUSE_SHADED':
            row.alert = True
            row.operator("material.yp_override_material", text="Shaded", icon='MATERIAL').mode = 'OFF'
            row.alert = False
        else: row.operator("material.yp_override_material", text="Shaded", icon='MATERIAL').mode = 'DIFFUSE_SHADED'

        row = col.row(align=True)
        row.label('Specular:')

        if scene.mo_props.override_mode == 'SPECULAR':
            row.alert = True
            row.operator("material.yp_override_material", text="Color", icon='POTATO').mode = 'OFF'
            row.alert = False
        else: row.operator("material.yp_override_material", text="Color", icon='POTATO').mode = 'SPECULAR'

        if scene.mo_props.override_mode == 'SPECULAR_SHADED':
            row.alert = True
            row.operator("material.yp_override_material", text="Shaded", icon='MATERIAL').mode = 'OFF'
            row.alert = False
        else: row.operator("material.yp_override_material", text="Shaded", icon='MATERIAL').mode = 'SPECULAR_SHADED'

        row = col.row(align=True)
        row.label('Normal:')

        if scene.mo_props.override_mode == 'NORMAL':
            row.alert = True
            row.operator("material.yp_override_material", text="Color", icon='POTATO').mode = 'OFF'
            row.alert = False
        else: row.operator("material.yp_override_material", text="Color", icon='POTATO').mode = 'NORMAL'

        if scene.mo_props.override_mode == 'MATCAP':
            row.alert = True
            row.operator("material.yp_override_material", text="Matcap", icon='MATCAP_' + space.matcap_icon).mode = 'OFF'
            row.alert = False
        else: row.operator("material.yp_override_material", text="Matcap", icon='MATCAP_' + space.matcap_icon).mode = 'MATCAP'

        row = col.split(percentage=0.3)
        row.label('Lighting:')
        
        if scene.mo_props.override_mode == 'LIGHTING_ONLY':
            row.alert = True
            row.operator("material.yp_override_material", text="Lighting Only", icon='SMOOTH').mode = 'OFF'
            row.alert = False
        else: row.operator("material.yp_override_material", text="Lighting Only", icon='SMOOTH').mode = 'LIGHTING_ONLY'

        c = col.column(align=True)
        c.prop(scene.mo_props, 'all_materials', text = "All Materials")
        if mo_mode != 'OFF':
            c.prop(scene.mo_props, 'keep_alpha', text = "Keep Alpha")
            #c.prop(scene.mo_props, 'keep_normal', text = "Keep Normal")

        if scene.mo_props.override_mode == 'MATCAP':

            area_id = -1
            for i, a in enumerate(screen.areas):
                if a == area:
                    area_id = i
                    break
        
            #c.label("Matlap Setting:")
            if not screen.show_fullscreen and screen.mo_props.active_index not in {-1, area_id}:
                c.operator("view3d.yp_change_view_id", text="Switch to this view", icon='ERROR')
            c.template_icon_view(space, "matcap_icon")

    def material_panel(self, mat, parent_mat = None):

        obj = bpy.context.object
        scene = bpy.context.scene
        mo_mode = scene.mo_props.override_mode
        engine = scene.render.engine

        col = self.layout.column()
        row = col.row(align=True)

        # If material panel is collapsed
        if self.is_collapsed('material_panel'):
            row.operator('view3d.yp_panel_toggle', icon='TRIA_RIGHT', text='', emboss=False).panel = 'material_panel'
            row.label('Materials')
            return
        
        # Material panel is uncollapsed
        row.operator('view3d.yp_panel_toggle', icon='TRIA_DOWN', text='', emboss=False).panel = 'material_panel'
        row.label('Materials')

        box = col.box()
        row = box.row()
        col = row.column()
        col.template_list("MATERIAL_UL_custom_matslots", "", obj, "material_slots", obj, "active_material_index", rows=3)
        #col.template_list("MATERIAL_UL_matslots", "", obj, "material_slots", obj, "active_material_index", rows=3)
        col = row.column(align=True)
        col.operator("object.material_slot_add", icon='ZOOMIN', text="")
        col.operator("object.material_slot_remove", icon='ZOOMOUT', text="")
        if len(obj.material_slots) > 1:

            col.operator("object.material_slot_move", icon='TRIA_UP', text="").direction = 'UP'
            col.operator("object.material_slot_move", icon='TRIA_DOWN', text="").direction = 'DOWN'

        if obj.mode == 'EDIT':
            row = box.row(align=True)
            row.operator("object.material_slot_assign", text="Assign")
            row.operator("object.material_slot_select", text="Select")
            row.operator("object.material_slot_deselect", text="Deselect")

        #split = box.split(percentage=0.8)
        row = box.row()
        row.template_ID(obj, "active_material", new="material.new")

        if mat:
            col = box.column()

            if parent_mat:
                row = col.row()
                row.label(text="", icon='NODETREE')
                row.prop(mat, "name", text="")
                col.separator()
            
            # DIFFUSE SETTING
            if mo_mode in {'OFF', 'DIFFUSE', 'DIFFUSE_SHADED'}:
                row = col.row(align=True)
                row.label('Diffuse:')
                row.prop(mat, "diffuse_color", text="")

                if engine != 'CYCLES' and mo_mode != 'DIFFUSE':
                    row.prop(mat, "diffuse_intensity", text="")

                    if self.is_collapsed('diffuse_setting'):
                        row.operator('view3d.yp_panel_toggle', icon='SCRIPTWIN', text='').panel = 'diffuse_setting'
                    else:
                        row.alert=True
                        row.operator('view3d.yp_panel_toggle', icon='SCRIPTWIN', text='').panel = 'diffuse_setting'
                        row.alert=False

                        #if mat.yp_props.show_diffuse_setting:
                        inbox = col.box()
                        incol = inbox.column()
                        incol.prop(mat, "diffuse_shader", text="")
                        incol.active = (not mat.use_shadeless)
                        if mat.diffuse_shader == 'OREN_NAYAR':
                            incol.prop(mat, "roughness")
                        elif mat.diffuse_shader == 'MINNAERT':
                            incol.prop(mat, "darkness")
                        elif mat.diffuse_shader == 'TOON':
                            incol.prop(mat, "diffuse_toon_size", text="Size")
                            incol.prop(mat, "diffuse_toon_smooth", text="Smooth")
                        elif mat.diffuse_shader == 'FRESNEL':
                            incol.prop(mat, "diffuse_fresnel", text="Fresnel")
                            incol.prop(mat, "diffuse_fresnel_factor", text="Factor")
                        incol.prop(mat, "use_diffuse_ramp", text="Ramp")  

                        if mat.use_diffuse_ramp:
                            incol.active = (not mat.use_shadeless)
                            incol.template_color_ramp(mat, "diffuse_ramp", expand=True)
                            incol.prop(mat, "diffuse_ramp_input", text="Input")
                            incol.prop(mat, "diffuse_ramp_blend", text="Blend")
                            incol.prop(mat, "diffuse_ramp_factor", text="Factor")

                        incol.prop(mat, 'use_vertex_color_paint')

                        col.separator()

            # SPECULAR SETTING
            if engine != 'CYCLES' and mo_mode in {'OFF', 'SPECULAR', 'SPECULAR_SHADED'}:
                row = col.row(align=True)
                row.label('Specular:')
                if mo_mode == 'SPECULAR':
                    row.prop(mat, "diffuse_color", text="")
                else:
                    row.prop(mat, "specular_color", text="")
                    row.prop(mat, "specular_intensity", text="")
                
                    if self.is_collapsed('specular_setting'):
                        row.operator('view3d.yp_panel_toggle', icon='SCRIPTWIN', text='').panel = 'specular_setting'
                    else:
                        row.alert=True
                        row.operator('view3d.yp_panel_toggle', icon='SCRIPTWIN', text='').panel = 'specular_setting'
                        row.alert=False

                        inbox = col.box()
                        incol = inbox.column()
                        incol.prop(mat, "specular_shader", text="")
                        if mat.specular_shader in {'COOKTORR', 'PHONG'}:
                            incol.prop(mat, "specular_hardness", text="Hardness")
                        elif mat.specular_shader == 'BLINN':
                            incol.prop(mat, "specular_hardness", text="Hardness")
                            incol.prop(mat, "specular_ior", text="IOR")
                        elif mat.specular_shader == 'WARDISO':
                            incol.prop(mat, "specular_slope", text="Slope")
                        elif mat.specular_shader == 'TOON':
                            incol.prop(mat, "specular_toon_size", text="Size")
                            incol.prop(mat, "specular_toon_smooth", text="Smooth")

                        incol.prop(mat, "use_specular_ramp", text="Ramp")
                        if mat.use_specular_ramp:
                            incol.template_color_ramp(mat, "specular_ramp", expand=True)
                            incol.prop(mat, "specular_ramp_input", text="Input")
                            incol.prop(mat, "specular_ramp_blend", text="Blend")
                            incol.prop(mat, "specular_ramp_factor", text="Factor")

                        col.separator()
            
            # ALPHA SETTING
            #if mo_mode in {'OFF', 'DIFFUSE', 'DIFFUSE_SHADED'}:
            if engine != 'CYCLES' and mo_mode in {'OFF'}:

                row = col.row(align=True)
                row.label('Alpha:')
                row.prop(mat, 'use_transparency', text='')
                row = row.row(align=True)
                row.active = mat.use_transparency
                row.prop(mat, 'alpha', text='')
                #row.prop(mat.yp_props, "show_transparency_setting", text="", icon='SCRIPTWIN')

                if self.is_collapsed('alpha_setting'):
                    row.operator('view3d.yp_panel_toggle', icon='SCRIPTWIN', text='').panel = 'alpha_setting'
                else:
                    row.alert=True
                    row.operator('view3d.yp_panel_toggle', icon='SCRIPTWIN', text='').panel = 'alpha_setting'
                    row.alert=False

                    rayt = mat.raytrace_transparency
                    game = mat.game_settings

                    inbox = col.box()
                    incol = inbox.column()
                    incol.prop(game, "alpha_blend", text="Blend")
                    incol.prop(mat, "transparency_method", text='Method')

                    if mat.transparency_method != 'MASK' and not mat.use_shadeless:
                        incol.prop(mat, "specular_alpha", text="Specular")

                    if not mat.use_shadeless:
                        incol.prop(rayt, "fresnel")
                        inincol = incol.column()
                        inincol.active = (rayt.fresnel > 0.0)
                        inincol.prop(rayt, "fresnel_factor", text="Blend")

                # SHADELESS SETTING
                if mo_mode in {'OFF'}:
                    row = col.row(align=True)
                    row.label('Shadeless:')
                    row.prop(mat, 'use_shadeless', text='')

    def paint_slots_panel(self, mat, uv_found, parent_mat = None):

        #tool_settings = bpy.context.tool_settings.image_paint

        obj = bpy.context.object
        scene = bpy.context.scene
        mo_mode = scene.mo_props.override_mode

        col = self.layout.column()
        row = col.row(align=True)

        if self.is_collapsed('paint_slots'):
            row.operator('view3d.yp_panel_toggle', icon='TRIA_RIGHT', text='', emboss=False).panel = 'paint_slots'
            row.label('Paint Slots')
            return
        
        row.operator('view3d.yp_panel_toggle', icon='TRIA_DOWN', text='', emboss=False).panel = 'paint_slots'
        row.label('Paint Slots')
        
        box = col.box()

        ## IF UV MAP NOT FOUND
        if not uv_found:
            row = box.row(align=True)
            row.alert = True
            row.operator("mesh.yp_add_simple_uvs", icon='ERROR')
            row.alert = False
            return

        real_slots_count = len([ts for ts in mat.texture_slots if 
                ts and ts.texture and ts.texture.type == 'IMAGE' and ts.texture.image and ts.texture_coords == 'UV'])
        slots_found = len(mat.texture_paint_slots)

        needs_update = real_slots_count != slots_found

        if not needs_update:
            for i, tps in enumerate(mat.texture_paint_slots):
                if tps.index < 0 or tps.index >= len(mat.texture_slots):
                    needs_update = True
                    break
                ts = mat.texture_slots[tps.index]
                if not ts or mat.texture_paint_images[i] != ts.texture.image:
                    needs_update = True
                    break

        row = box.row()
        row.template_list("TEXTURE_UL_custom_paint_slots", "", mat, "texture_paint_images",
                             mat, "paint_active_slot", rows=6)
        col = row.column(align=True)

        if scene.mo_props.override_mode == 'OFF':
            #col.operator_menu_enum("paint.add_texture_paint_slot", "type", icon='ZOOMIN', text='')
            col.operator_menu_enum("paint.yp_add_slot_with_context", "type", icon='NEW', text='')
        else: col.operator("paint.yp_add_slot_with_context", icon='NEW', text='')

        col.operator('paint.yp_add_slot_with_available_image', icon='IMAGE_DATA', text='')
        col.operator("paint.yp_open_paint_texture_from_file", icon='FILESEL', text='').new_slot = True

        if bpy.context.mode == 'PAINT_TEXTURE':
            col.operator("paint.yp_remove_texture_paint_slot_with_prompt", text="", icon='ZOOMOUT')
        else: col.operator("paint.yp_remove_texture_paint_slot", text="", icon='ZOOMOUT')

        col.operator("paint.yp_slot_move", text='', icon='TRIA_UP').type = 'UP'
        col.operator("paint.yp_slot_move", text='', icon='TRIA_DOWN').type = 'DOWN'
        col.menu("MATERIAL_MT_texture_paint_specials", icon='DOWNARROW_HLT', text='')

        #if bpy.context.mode == 'PAINT_TEXTURE' and parent_mat == mat:
        if bpy.context.mode == 'PAINT_TEXTURE' and parent_mat and mat.use_nodes:
            col = box.column(align=True)
            col.alert = True
            col.label('Cannot access this material node paint slots!')
            if parent_mat == mat:
                #col.label('Duplicate this material to access them!')
                #col.operator('material.yp_duplicate_to_non_node_material', text='Duplicate Material!', icon='ERROR')
                #col.label('Toggle Use Nodes to access paint slots!')
                col.operator('material.yp_disable_use_nodes', text='Disable Use Nodes!', icon='ERROR')
            else:
            #    col.label('Disable use nodes for this node material to access them!')
            #    col.operator('material.yp_duplicate_to_non_node_material', text='Disable Use Nodes!', icon='ERROR')
                col.operator('material.yp_disable_use_nodes', text='Disable Use Nodes!', icon='ERROR').mat_name = mat.name
            col.alert = False

        elif needs_update:
            col = box.column()
            col.alert = True
            col.operator('material.yp_refresh_paint_slots', text='Refresh Paint Slots!', icon='ERROR')
            col.alert = False

        # If paint slots not found, just return
        if not mat.texture_paint_slots:
            return

        slot = mat.texture_paint_slots[mat.paint_active_slot]

        ts_idx = mat.texture_paint_slots[mat.paint_active_slot].index
        tslot = mat.texture_slots[ts_idx]
        if tslot and tslot.texture and tslot.texture.image:
            tex = tslot.texture
            img = tex.image

            col = box.column()

            #row = col.row(align=True)
            #col.template_ID_preview(tslot, "texture", rows=3, cols=8)
            #col.template_ID_preview(tex, "image", rows=3, cols=8)
            #col.template_any_ID(tex, "image")
            #col.template_icon_view(tex, "image")
            #col.template_ID(tool_settings, 'canvas')
            #col.template_ID_preview(tool_settings, 'canvas')

            row = col.row(align=True)
            #row.template_ID(tex, "image", open="image.open", unlink='paint.yp_remove_texture_paint_slot')
            if bpy.context.mode == 'PAINT_TEXTURE':
                row.template_ID(tex, "image", 
                        #open='paint.yp_open_paint_texture_from_file', 
                        unlink='paint.yp_remove_texture_paint_slot_with_prompt')
            else: 
                row.template_ID(tex, "image", 
                        #open='paint.yp_open_paint_texture_from_file', 
                        unlink='paint.yp_remove_texture_paint_slot')
            #if img.is_dirty:
            row.operator("paint.yp_reload_texture_paint", text="", icon='FILE_REFRESH')
            if self.is_collapsed('generated_image_setting'):
                row.operator('view3d.yp_panel_toggle', icon='SCRIPTWIN', text='').panel = 'generated_image_setting'
            else:
                row.alert=True
                row.operator('view3d.yp_panel_toggle', icon='SCRIPTWIN', text='').panel = 'generated_image_setting'
                row.alert=False

                inbox = col.box()
                incol = inbox.column()

                if img.source == 'GENERATED':
                    incol.label('Generated image settings:')
                    row = incol.row()

                    col1 = row.column(align=True)
                    col1.prop(img, 'generated_width', text='X')
                    col1.prop(img, 'generated_height', text='Y')

                    col1.prop(img, 'use_generated_float', text='Float Buffer')
                    col2 = row.column(align=True)
                    col2.prop(img, 'generated_type', expand=True)

                    row = incol.row()
                    row.label('Color:')
                    row.prop(img, 'generated_color', text='')
                elif img.source == 'FILE':
                    #incol.label('Image Info:')
                    #is_packed = 'True' if img.packed_file else 'False'
                    #incol.label('Packed: ' + is_packed)

                    if not img.filepath:
                        incol.label('Image Path: -')
                    else:
                        incol.label('Path: ' + img.filepath)

                    image_format = 'RGBA'
                    image_bit = int(img.depth/4)
                    if img.depth in {24, 48, 96}:
                        image_format = 'RGB'
                        image_bit = int(img.depth/3)

                    incol.label('Info: ' + str(img.size[0]) + ' x ' + str(img.size[1]) +
                            ' ' + image_format + ' ' + str(image_bit) + '-bit')

                    incol.template_colorspace_settings(img, "colorspace_settings")
                    #incol.prop(img, 'use_view_as_render')
                    incol.prop(img, 'alpha_mode')
                    incol.prop(img, 'use_alpha')
                    #incol.prop(img, 'use_fields')
                    #incol.template_image(tex, "image", tex.image_user)
                    

            #if mo_mode in {'NORMAL'}:
            #    col.separator()
            #else:

            row = col.row(align=True)
            row.label('Influences:')

            if mo_mode == 'OFF':
                row.operator_menu_enum('texture.yp_add_new_influence', 'influence', icon='ZOOMIN', text='')

            ch_found = 0

            for ch, label in paint_slots.influence_names.items():

                if mo_mode in {'DIFFUSE', 'SPECULAR', 'NORMAL'} and ch not in {'color_diffuse', 'alpha'}: continue
                #if mo_mode == 'DIFFUSE' and ch not in {'color_diffuse', 'alpha'}: continue
                #if mo_mode == 'SPECULAR' and ch != 'color_diffuse': continue

                force_visible_influence = paint_slots.check_available_force_visible_influences(mat, ts_idx, ch)
                channel_active = getattr(tslot, 'use_map_' + ch)

                if channel_active or force_visible_influence:

                    row = col.row(align=True)
                    if mo_mode == 'OFF':

                        if channel_active:
                            row.operator('paint.yp_toggle_force_visible_influence', text='', icon='RESTRICT_VIEW_OFF').influence = ch
                        else:
                            row.operator('paint.yp_toggle_force_visible_influence', text='', icon='RESTRICT_VIEW_ON').influence = ch

                        if ch == 'normal' and not tex.use_normal_map:
                            row.prop(tslot, paint_slots.influence_factor[ch], text='Bump')
                        else:
                            row.prop(tslot, paint_slots.influence_factor[ch], text=label)

                        if ch == 'normal':
                            if tex.use_normal_map:
                                row.operator('texture.yp_toggle_normal_bump', text='', icon='MATCAP_23')
                            else:
                                row.operator('texture.yp_toggle_normal_bump', text='', icon='MATCAP_09')

                        row.operator('texture.yp_remove_influence', text='', icon='X').influence = ch

                    elif mo_mode == 'SPECULAR' and ch == 'color_diffuse':
                        row.prop(tslot, paint_slots.influence_factor[ch], text='Specular Color') #+' Factor')
                    elif mo_mode == 'NORMAL' and ch == 'color_diffuse':
                        if not tex.use_normal_map:
                            row.prop(tslot, paint_slots.influence_factor[ch], text='Bump')
                        else: row.prop(tslot, paint_slots.influence_factor[ch], text='Normal')
                    #elif mo_mode == 'DIFFUSE':
                    else:
                        row.prop(tslot, paint_slots.influence_factor[ch], text=label)

                    ch_found += 1

            if ch_found == 0:
                col.label('No influences found!', icon='ERROR')

            col.separator()
            row = col.row(align=True)
            row.prop(mat.texture_slots[slot.index], "blend_type", text='Blend')
            #row.prop(mat.yp_props, 'show_blend_setting', icon='SCRIPTWIN', text='')

            if self.is_collapsed('blend_setting'):
                row.operator('view3d.yp_panel_toggle', icon='SCRIPTWIN', text='').panel = 'blend_setting'
            else:
                row.alert=True
                row.operator('view3d.yp_panel_toggle', icon='SCRIPTWIN', text='').panel = 'blend_setting'
                row.alert=False

                inbox = col.box()
                incol = inbox.column()

                incol.prop(tslot, "use_rgb_to_intensity")
                if tslot.use_rgb_to_intensity:
                    incol.prop(tslot, "color", text="")
                incol.prop(tslot, "invert", text="Negative")
                incol.prop(tslot, "use_stencil")

                col.separator()

            row = col.row(align=True)
            row.prop_search(slot, "uv_layer", obj.data, "uv_textures", text="UV Map")

            if self.is_collapsed('uv_setting'):
                row.operator('view3d.yp_panel_toggle', icon='SCRIPTWIN', text='').panel = 'uv_setting'
            else:
                row.alert=True
                row.operator('view3d.yp_panel_toggle', icon='SCRIPTWIN', text='').panel = 'uv_setting'
                row.alert=False

                inbox = col.box()
                incol = inbox.column()
                incol.prop(tslot, "offset")
                incol.prop(tslot, "scale")
                #incol.separator()
                incol = inbox.column(align=True)
                incol.operator("paint.yp_bake_image_to_another_uv", text='Convert image to other UV', icon='RENDER_STILL').mode = 'ACTIVE_ONLY'
                #incol.operator("paint.yp_bake_image_to_another_uv", text='Convert all images to other UV', icon='RENDER_STILL').mode = 'ALL_MATERIAL_IMAGES'
                incol.operator("mesh.yp_add_simple_uvs", icon='ERROR', text='Redo simple UVs')
                
                col.separator()

            col = box.column(align=True)
            #if img and img.filepath != '':
            if img:
                if img.packed_file:
                    col.operator("paint.yp_save_as_texture_paint", text="Save & Unpack Image")
                elif img.filepath == '':
                    col.operator("paint.yp_save_as_texture_paint", text="Save Image")
                else: 
                    col.operator("paint.yp_save_texture_paint", text="Save Image")
                    col.operator("paint.yp_save_as_texture_paint", text="Save As Image")
            col.operator("image.save_dirty", text="Save All Images")

            #if not img.packed_file:
            col = box.column(align=True)
            col.operator("paint.yp_pack_image", text="Pack Image", icon='UGLYPACKAGE')
                #col.operator("paint.yp_pack_image", text="Unpack Image", icon='PACKAGE').reverse = True
            #else: col.operator("paint.yp_pack_image", text="Pack Image", icon='UGLYPACKAGE').reverse = False

    def bake_ao_settings_panel(self, box):

        scene = bpy.context.scene
        settings = bpy.context.scene.bt_props

        col = box.column()
        inbox = col.box()
        incol = inbox.column()
        incol.prop(settings, 'ao_suffix', text='Suffix')
        incol.prop(settings, 'ao_blend', text='Blend')

        #incol = inbox.column()

        light = scene.world.light_settings
        incol.prop(light, "gather_method") #, text='Method')

        #incol.label(text="Attenuation:")
        if light.gather_method == 'RAYTRACE':
            incol.prop(light, "distance")
        split = incol.split(percentage=0.35)
        #row = incol.row()
        split.prop(light, "use_falloff")
        inrow = split.row()
        inrow.active = light.use_falloff
        inrow.prop(light, "falloff_strength", text="Strength")

        if light.gather_method == 'RAYTRACE':
            #incol = split.column()

            #incol.label(text="Sampling:")
            incol.prop(light, "sample_method")

            #sub = incol.column()
            incol.prop(light, "samples")

            if light.sample_method == 'ADAPTIVE_QMC':
                incol.prop(light, "threshold")
                incol.prop(light, "adapt_to_speed", slider=True)
            elif light.sample_method == 'CONSTANT_JITTERED':
                incol.prop(light, "bias")

        if light.gather_method == 'APPROXIMATE':
            #incol = split.column()

            #incol.label(text="Sampling:")
            incol.prop(light, "passes")
            incol.prop(light, "error_threshold", text="Error")
            incol.prop(light, "use_cache")
            incol.prop(light, "correction")

        incol.prop(settings, "isolated_ao", text='Isolate object') #, text='Method')

    def bake_normals_settings_panel(self, box):

        obj = bpy.context.object
        scene = bpy.context.scene
        settings = bpy.context.scene.bt_props

        col = box.column()
        inbox = col.box()
        incol = inbox.column()
        #incol.enabled = bake_normal_possible
        incol.prop(settings, 'normals_suffix', text='Suffix')

        incol.prop(scene.render, 'bake_normal_space')

        incol = incol.column()
        multires_found = any([mod for mod in obj.modifiers if mod.type == 'MULTIRES'])
        incol.enabled = multires_found and not settings.use_highpoly
        incol.prop(settings, 'subdiv_base')
        incol.prop(settings, 'set_multires_level_to_base')

    def bake_dirty_vertex_color_settings_panel(self, box):

        settings = bpy.context.scene.bt_props

        col = box.column()
        inbox = col.box()
        incol = inbox.column()
        incol.prop(settings, 'dirty_suffix', text='Suffix')
        incol.prop(settings, 'dirty_blend', text='Blend')
        incol.prop(settings, 'dirt_blur_strength')
        incol.prop(settings, 'dirt_blur_iterations')
        incol.prop(settings, 'dirt_clean_angle')
        incol.prop(settings, 'dirt_angle')
        incol.prop(settings, 'dirt_only')

    def bake_lights_settings_panel(self, box):

        settings = bpy.context.scene.bt_props

        col = box.column()
        inbox = col.box()
        incol = inbox.column()
        incol.prop(settings, 'lights_suffix', text='Suffix')
        incol.prop(settings, 'lights_blend', text='Blend')
        incol.prop(settings, 'bake_light_type', text='Type')
        if settings.bake_light_type in {'SUN', 'HEMI'}:
            incol.prop(settings, 'bake_light_direction', text='Direction')
            row = incol.row(align=True)
            row.label('Light Color:')
            row.prop(settings, 'light_color', text='')
            incol.prop(settings, 'bake_light_linear', text='Linear')
        incol.prop(settings, 'set_shadeless_after_baking_lights')
        incol.prop(settings, "isolated_light", text='Isolate object') #, text='Method')

    def bake_diffuse_color_settings_panel(self, box):

        settings = bpy.context.scene.bt_props

        col = box.column()
        inbox = col.box()
        incol = inbox.column()
        incol.prop(settings, 'diffuse_color_suffix', text='Suffix')
        incol.prop(settings, 'color_blend', text='Blend')

    def bake_specular_color_settings_panel(self, box):

        settings = bpy.context.scene.bt_props

        col = box.column()
        inbox = col.box()
        incol = inbox.column()
        incol.prop(settings, 'specular_color_suffix', text='Suffix')
        incol.prop(settings, 'specular_blend', text='Blend')

    def bake_full_render_settings_panel(self, box):

        settings = bpy.context.scene.bt_props

        col = box.column()
        inbox = col.box()
        incol = inbox.column()
        incol.prop(settings, 'full_render_suffix', text='Suffix')
        incol.prop(settings, 'full_render_blend', text='Blend')
        incol.prop(settings, 'set_shadeless_after_baking_full_render')

    def bake_tools_panel(self, mat):

        obj = bpy.context.object
        scene = bpy.context.scene
        settings = bpy.context.scene.bt_props

        col = self.layout.column()
        row = col.row(align=True)

        if self.is_collapsed('bake_tools'):
            row.operator('view3d.yp_panel_toggle', icon='TRIA_RIGHT', text='', emboss=False).panel = 'bake_tools'
            row.label('Bake Tools')
            return
        
        row.operator('view3d.yp_panel_toggle', icon='TRIA_DOWN', text='', emboss=False).panel = 'bake_tools'
        row.label('Bake Tools')
        box = col.box()
        col = box.column()

        row = col.row(align=True)
        row.operator('view3d.yp_bake_stuffs', text='Bake', icon='RENDER_STILL').type = settings.bake_type

        row.prop(settings, 'bake_type', text='')
        if self.is_collapsed('bake_settings'):
            row.operator('view3d.yp_panel_toggle', icon='SCRIPTWIN', text='').panel = 'bake_settings'
        else:
            row.alert = True
            row.operator('view3d.yp_panel_toggle', icon='SCRIPTWIN', text='').panel = 'bake_settings'
            row.alert = False
            if settings.bake_type == 'AO':
                self.bake_ao_settings_panel(box)
            elif settings.bake_type == 'NORMALS':
                self.bake_normals_settings_panel(box)
            elif settings.bake_type == 'DIRTY':
                self.bake_dirty_vertex_color_settings_panel(box)
            elif settings.bake_type == 'LIGHTS':
                self.bake_lights_settings_panel(box)
            elif settings.bake_type == 'DIFFUSE_COLOR':
                self.bake_diffuse_color_settings_panel(box)
            elif settings.bake_type == 'SPECULAR_COLOR':
                self.bake_specular_color_settings_panel(box)
            elif settings.bake_type == 'FULL_RENDER':
                self.bake_full_render_settings_panel(box)

        #col = box.column(align=True)

        #row = col.row(align=True)
        #row.operator('view3d.yp_bake_stuffs', text='Bake AO', icon='RENDER_STILL').type = 'AO'
        #if self.is_collapsed('bake_ao_setting'):
        #    row.operator('view3d.yp_panel_toggle', icon='SCRIPTWIN', text='').panel = 'bake_ao_setting'
        #else:
        #    row.alert = True
        #    row.operator('view3d.yp_panel_toggle', icon='SCRIPTWIN', text='').panel = 'bake_ao_setting'
        #    row.alert = False
        #    self.bake_ao_settings_panel(box)
        #    col = box.column(align=True)

        #row = col.row(align=True)
        #inrow = row.row(align=True)
        ##inrow.enabled = bake_normal_possible
        #inrow.operator('view3d.yp_bake_stuffs', text='Bake Normal', icon='RENDER_STILL').type = 'NORMALS'
        #row = row.row(align=True)
        ##row.enabled = True
        #if self.is_collapsed('bake_normal_setting'):
        #    row.operator('view3d.yp_panel_toggle', icon='SCRIPTWIN', text='').panel = 'bake_normal_setting'
        #else:
        #    row.alert = True
        #    row.operator('view3d.yp_panel_toggle', icon='SCRIPTWIN', text='').panel = 'bake_normal_setting'
        #    row.alert = False
        #    self.bake_normals_settings_panel(box)
        #    col = box.column(align=True)

        #row = col.row(align=True)
        #row.operator('view3d.yp_bake_stuffs', text='Bake Dirty Vertex Color', icon='RENDER_STILL').type = 'DIRTY'
        #if self.is_collapsed('bake_vertex_color_setting'):
        #    row.operator('view3d.yp_panel_toggle', icon='SCRIPTWIN', text='').panel = 'bake_vertex_color_setting'
        #else:
        #    row.alert = True
        #    row.operator('view3d.yp_panel_toggle', icon='SCRIPTWIN', text='').panel = 'bake_vertex_color_setting'
        #    row.alert = False
        #    self.bake_dirty_vertex_color_settings_panel(box)
        #    col = box.column(align=True)

        #row = col.row(align=True)
        #row.operator('view3d.yp_bake_stuffs', text='Bake Lights', icon='RENDER_STILL').type = 'LIGHTS'
        #if self.is_collapsed('bake_lights_setting'):
        #    row.operator('view3d.yp_panel_toggle', icon='SCRIPTWIN', text='').panel = 'bake_lights_setting'
        #else:
        #    row.alert = True
        #    row.operator('view3d.yp_panel_toggle', icon='SCRIPTWIN', text='').panel = 'bake_lights_setting'
        #    row.alert = False
        #    self.bake_lights_settings_panel(box)
        #    col = box.column(align=True)

        #row = col.row(align=True)
        #row.operator('view3d.yp_bake_stuffs', text='Bake Diffuse Color', icon='RENDER_STILL').type = 'DIFFUSE_COLOR'
        #if self.is_collapsed('bake_diffuse_color_setting'):
        #    row.operator('view3d.yp_panel_toggle', icon='SCRIPTWIN', text='').panel = 'bake_diffuse_color_setting'
        #else:
        #    row.alert = True
        #    row.operator('view3d.yp_panel_toggle', icon='SCRIPTWIN', text='').panel = 'bake_diffuse_color_setting'
        #    row.alert = False
        #    self.bake_diffuse_color_settings_panel(box)
        #    col = box.column(align=True)

        #row = col.row(align=True)
        #row.operator('view3d.yp_bake_stuffs', text='Bake Specular Color', icon='RENDER_STILL').type = 'SPECULAR_COLOR'
        #if self.is_collapsed('bake_specular_color_setting'):
        #    row.operator('view3d.yp_panel_toggle', icon='SCRIPTWIN', text='').panel = 'bake_specular_color_setting'
        #else:
        #    row.alert = True
        #    row.operator('view3d.yp_panel_toggle', icon='SCRIPTWIN', text='').panel = 'bake_specular_color_setting'
        #    row.alert = False
        #    self.bake_specular_color_settings_panel(box)
        #    #col = box.column(align=True)

        col = box.column()

        row = col.row(align=True)
        row.label('Global Bake Settings')
        if self.is_collapsed('bake_global_setting'):
            row.operator('view3d.yp_panel_toggle', icon='SCRIPTWIN', text='').panel = 'bake_global_setting'
        else:
            row.alert = True
            row.operator('view3d.yp_panel_toggle', icon='SCRIPTWIN', text='').panel = 'bake_global_setting'
            row.alert = False

            inbox = col.box()
            incol = inbox.column()
            r = incol.row(align=True)
            r.label('AA:')
            r.prop(settings, "antialias", text='')
            r = r.row()
            r.enabled = settings.antialias
            r.prop(settings, "sample", text='') #, expand=True)

            incol.prop(settings, 'res_x', text='Width')
            incol.prop(settings, 'res_y', text='Height') #, expand=True)
            incol.prop(bpy.context.scene.render, "bake_margin")

            incol.prop(settings, 'overwrite', text='Overwrite matching suffix')
            incol.prop(settings, 'all_selected', text='All Selected Objects')
            if any([m for m in obj.modifiers if m.type == 'ARMATURE']):
                incol.prop(settings, 'use_rest_pose')

            incol.prop(settings, 'use_highpoly', text='Use Highpoly Mesh(es)')
            if settings.use_highpoly:
                incol.prop(settings, 'highpoly_prefix', text='Prefix')
                incol.prop(bpy.context.scene.render, "bake_distance")
                incol.prop(bpy.context.scene.render, "bake_bias")
            incol = incol.column()
            incol.active = not settings.use_highpoly
            #incol.prop(bpy.context.scene.render, 'use_bake_multires')
            #if bpy.context.scene.render.use_bake_multires:
            #    incol.prop(settings, 'multires_base')
            #    incol.prop(bpy.context.scene.render, "bake_bias")
            #    incol.prop(bpy.context.scene.render, "bake_samples")

    def symmetry_lock_panel(self):

        sculpt = bpy.context.tool_settings.sculpt

        col = self.layout.column()
        row = col.row(align=True)

        if self.is_collapsed('symmetry_lock'):
            row.operator('view3d.yp_panel_toggle', icon='TRIA_RIGHT', text='', emboss=False).panel = 'symmetry_lock'
            row.label('Symmetry / Lock')
            return
        
        row.operator('view3d.yp_panel_toggle', icon='TRIA_DOWN', text='', emboss=False).panel = 'symmetry_lock'
        row.label('Symmetry / Lock')
        box = col.box()
        col = box.column()

        row = col.row(align=True)
        row.label(text="Mirror:")
        row.prop(sculpt, "use_symmetry_x", text="X", toggle=True)
        row.prop(sculpt, "use_symmetry_y", text="Y", toggle=True)
        row.prop(sculpt, "use_symmetry_z", text="Z", toggle=True)

        col.prop(sculpt, "radial_symmetry", text="Radial")
        col.prop(sculpt, "use_symmetry_feather", text="Feather")

        row = col.row(align=True)
        row.label(text="Lock:")
        row.prop(sculpt, "lock_x", text="X", toggle=True)
        row.prop(sculpt, "lock_y", text="Y", toggle=True)
        row.prop(sculpt, "lock_z", text="Z", toggle=True)

        row = col.row(align=True)
        row.label(text="Tiling:")
        row.prop(sculpt, "tile_x", text="X", toggle=True)
        row.prop(sculpt, "tile_y", text="Y", toggle=True)
        row.prop(sculpt, "tile_z", text="Z", toggle=True)

        col.prop(sculpt, "tile_offset", text="Tile Offset")

    def dyntopo_panel(self):

        toolsettings = bpy.context.tool_settings
        sculpt = toolsettings.sculpt
        brush = sculpt.brush
        
        col = self.layout.column()
        row = col.row(align=True)

        if self.is_collapsed('dyntopo_panel'):
            row.operator('view3d.yp_panel_toggle', icon='TRIA_RIGHT', text='', emboss=False).panel = 'dyntopo_panel'
            row.label('Dyntopo')
            return
        
        row.operator('view3d.yp_panel_toggle', icon='TRIA_DOWN', text='', emboss=False).panel = 'dyntopo_panel'
        row.label('Dyntopo')
        box = col.box()
        col = box.column()

        if bpy.context.sculpt_object.use_dynamic_topology_sculpting:
            col.operator("sculpt.dynamic_topology_toggle", icon='X', text="Disable Dyntopo")
        else:
            col.operator("sculpt.dynamic_topology_toggle", icon='SCULPT_DYNTOPO', text="Enable Dyntopo")

        #col = layout.column()
        incol = col.column()
        incol.active = bpy.context.sculpt_object.use_dynamic_topology_sculpting
        sub = incol.column(align=True)
        sub.active = (brush and brush.sculpt_tool != 'MASK')
        if (sculpt.detail_type_method == 'CONSTANT'):
            row = sub.row(align=True)
            row.prop(sculpt, "constant_detail")
            row.operator("sculpt.sample_detail_size", text="", icon='EYEDROPPER')
        elif (sculpt.detail_type_method == 'BRUSH'):
            sub.prop(sculpt, "detail_percent")
        else:
            sub.prop(sculpt, "detail_size")
        sub.label('Detail Refine:')
        sub.prop(sculpt, "detail_refine_method", expand=True)
        sub.label('Detail Type:')
        sub.prop(sculpt, "detail_type_method", expand = True)
        #incol.separator()
        incol.prop(sculpt, "use_smooth_shading")
        incol.operator("sculpt.optimize")
        if (sculpt.detail_type_method == 'CONSTANT'):
            incol.operator("sculpt.detail_flood_fill")
        #incol.separator()
        row = incol.row(align=True)
        row.prop(sculpt, "symmetrize_direction", text='')
        row.operator("sculpt.symmetrize")

    def multires_panel(self):

        toolsettings = bpy.context.tool_settings
        sculpt = toolsettings.sculpt
        brush = sculpt.brush
        obj = bpy.context.object
        
        col = self.layout.column()
        row = col.row(align=True)

        if self.is_collapsed('multires_panel'):
            row.operator('view3d.yp_panel_toggle', icon='TRIA_RIGHT', text='', emboss=False).panel = 'multires_panel'
            row.label('Multires')
            return
        
        row.operator('view3d.yp_panel_toggle', icon='TRIA_DOWN', text='', emboss=False).panel = 'multires_panel'
        row.label('Multires')
        box = col.box()
        col = box.column(align=True)

        mod = [m for m in obj.modifiers if m.type == 'MULTIRES']

        if not mod:
            col.operator('object.modifier_add', text='Add multires modifier').type = 'MULTIRES'
            return

        mod = mod[0]

        split = col.split(percentage=0.25)
        split.label('Type:')
        row = split.row()
        row.prop(mod, "subdivision_type", expand=True)

        col.separator()

        col.prop(mod, "levels", text="Preview")
        col.prop(mod, "sculpt_levels", text="Sculpt")
        col.prop(mod, "render_levels", text="Render")

        col.separator()

        row = col.row(align=True)
        row.operator("object.shade_smooth", text="Smooth")
        row.operator("object.shade_flat", text="Flat")

        col.separator()
        col.enabled = obj.mode != 'EDIT'
        col.operator("object.multires_subdivide", text="Subdivide").modifier = mod.name
        col.operator("object.multires_higher_levels_delete", text="Delete Higher").modifier = mod.name
        col.operator("object.multires_reshape", text="Reshape").modifier = mod.name
        col.operator("object.multires_base_apply", text="Apply Base").modifier = mod.name
        col.separator()
        col.prop(mod, "use_subsurf_uv")
        col.prop(mod, "show_only_control_edges")

        col.separator()

        #row = col.row(align=True)
        if mod.is_external:
            col.operator("object.multires_external_pack", text="Pack External")
            #col.label()
            #col = col.row()
            col.prop(mod, "filepath", text="")
        else:
            col.operator("object.multires_external_save", text="Save External...").modifier = mod.name
            #row.label()

    def curve_panel(self):

        toolsettings = bpy.context.tool_settings
        sculpt = toolsettings.sculpt
        brush = sculpt.brush
        
        col = self.layout.column()
        row = col.row(align=True)

        if self.is_collapsed('curve_panel'):
            row.operator('view3d.yp_panel_toggle', icon='TRIA_RIGHT', text='', emboss=False).panel = 'curve_panel'
            row.label('Curve')
            return
        
        row.operator('view3d.yp_panel_toggle', icon='TRIA_DOWN', text='', emboss=False).panel = 'curve_panel'
        row.label('Curve')
        box = col.box()
        col = box.column()

        col.template_curve_mapping(brush, "curve", brush=True)

        #col = layout.column(align=True)
        row = col.row(align=True)
        row.operator("brush.curve_preset", icon='SMOOTHCURVE', text="").shape = 'SMOOTH'
        row.operator("brush.curve_preset", icon='SPHERECURVE', text="").shape = 'ROUND'
        row.operator("brush.curve_preset", icon='ROOTCURVE', text="").shape = 'ROOT'
        row.operator("brush.curve_preset", icon='SHARPCURVE', text="").shape = 'SHARP'
        row.operator("brush.curve_preset", icon='LINCURVE', text="").shape = 'LINE'
        row.operator("brush.curve_preset", icon='NOCURVE', text="").shape = 'MAX'

    def populate_ids(self):

        screen = bpy.context.screen
        area = bpy.context.area

        if screen.show_fullscreen:
            screen = bpy.data.screens[screen.name[:-10]]
            # Search for original id on non fullscreen screen
            self.id = [i for i, a in enumerate(screen.areas) if (
                    len(a.spaces) == 0 or (a.type == 'INFO' and i != 0)
                    )][0]
        else: self.id = [i for i, a in enumerate(screen.areas) if a == area][0]

        # Create panel struct and dictionary of panels
        class PanelStruct():
            def __init__(self):
                self.collapse = None
                self.ids = None
        self.panels = {}

        # Populate dictionary of panels
        prop_list = [prop for prop in dir(screen.yp_props) if 'collapsed_' in prop]
        for prop in prop_list:

            if prop.startswith('collapsed_'):
                name = prop.replace('collapsed_', '')
                collapse = True
            else:
                name = prop.replace('uncollapsed_', '')
                collapse = False

            self.panels[name] = PanelStruct()
            self.panels[name].collapse = collapse
            self.panels[name].ids = [int(i[2:]) for i in getattr(screen.yp_props, prop).split()]

    def draw(self, context):

        obj = context.object
        scene = context.scene
        mo_mode = scene.mo_props.override_mode
        space = context.space_data
        gs = context.scene.game_settings 
        engine = scene.render.engine

        self.populate_ids()

        # Main panel
        #row = self.layout.row(align=True)
        #if self.is_collapsed('main_ypanel'):
        #    row.operator('view3d.yp_panel_toggle', icon='RIGHTARROW', text='', emboss=False).panel = 'main_ypanel'
        #    row.label('yPanel')
        #    return
        #
        #row.operator('view3d.yp_panel_toggle', icon='DOWNARROW_HLT', text='', emboss=False).panel = 'main_ypanel'
        #row.label('yPanel')

        #self.object_panel()

        self.mode_panel() # Mode panel
        self.shading_panel() # Shading panel

        if engine in {'BLENDER_RENDER', 'BLENDER_GAME'}: # and context.mode not in {'SCULPT', 'PAINT_WEIGHT'}:

            # Material override panel only available on Material shading
            if ((space.viewport_shade == 'MATERIAL' or (gs.material_mode == 'GLSL' and space.viewport_shade == 'TEXTURED')) and 
                #context.mode not in {'SCULPT', 'PAINT_WEIGHT'}):
                context.mode not in {'PAINT_WEIGHT'}):
                self.material_override_panel() # Material override panel
            elif mo_mode != 'OFF':
                self.material_override_recover_panel() # Material override recover panel

        if obj and obj.type in {'MESH', 'CURVE'}:
            
            #if context.mode not in {'SCULPT', 'PAINT_WEIGHT'}:
            if context.mode not in {'PAINT_WEIGHT'}:

                mat = obj.active_material

                # Check if material is using nodes
                use_nodes = False
                parent_mat = None
                if mat and mat.use_nodes:
                    parent_mat = mat
                    mat = mat.active_node_material
                    use_nodes = True

                self.material_panel(mat, parent_mat) # Material Panel

                if obj.type == 'MESH' and engine != 'CYCLES' and mat and mo_mode != 'LIGHTING_ONLY':
                #if mat and not use_nodes and mo_mode != 'LIGHTING_ONLY':

                    # Check if uv is found
                    uv_found = False
                    if len(obj.data.uv_textures) > 0:
                        uv_found = True
                    
                    self.paint_slots_panel(mat, uv_found, parent_mat) # Paint slot panel

                    #if not use_nodes and uv_found:
                    #if uv_found and context.mode not in {'SCULPT'}:
                    if uv_found:
                        self.bake_tools_panel(mat) # Bake tools panel

            mod = [m for m in obj.modifiers if m.type == 'MULTIRES']
            if mod or context.mode == 'SCULPT':
                self.multires_panel()
            if context.mode == 'SCULPT':
                #self.curve_panel()
                self.symmetry_lock_panel()
                self.dyntopo_panel()

# UI LIST
class MATERIAL_UL_custom_matslots(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname):
        sce = context.scene
        ob = data
        slot = item
        ma = slot.material
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            if ma:
                manode = ma.active_node_material
                if manode:
                    layout.label(text="Node %s" % manode.name, translate=False, icon_value=layout.icon(manode))
                elif ma.use_nodes:
                    layout.label(text="Node <none>", translate=False, icon_value=icon)
                else:
                    layout.prop(ma, "name", text="", emboss=False, icon_value=icon)

                if sce.mo_props.override_mode == 'OFF':
                    layout.prop(ma, "use_nodes", icon='NODETREE', text="")
            else:
                layout.label(text="", translate=False, icon_value=icon)
        # 'GRID' layout type should be as compact as possible (typically a single icon!).
        elif self.layout_type in {'GRID'}:
            layout.alignment = 'CENTER'
            layout.label(text="", icon_value=icon)

class TEXTURE_UL_custom_paint_slots(bpy.types.UIList):
    global custom_icons
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        mat = context.object.active_material
        if mat.use_nodes:
            mat = mat.active_node_material
        texpaint = item
        if self.layout_type in {'DEFAULT'}:
            if texpaint:
                ts_idx = mat.texture_paint_slots[index].index
                ts = mat.texture_slots[ts_idx]
                row = layout.row(align=True)
                if '_alpha_temp_' in texpaint.name:
                    #row = layout.row(align=True)
                    #row.alert=True
                    row.label(text='', icon='ERROR')
                    row.prop(texpaint, 'name', text='', emboss=False)
                else:
                    row.prop(texpaint, 'name', text='', emboss=False, icon_value=icon)
                if texpaint.is_dirty:
                    row.label(text='', icon_value=custom_icons["asterisk"].icon_id)
                if texpaint.packed_file:
                    row.label(text='', icon='PACKAGE')
                #else: row.label(text='', icon='FILE_TICK')
                if ts.use_rgb_to_intensity:
                    row.prop(ts, 'color', text='', icon='COLOR')
                if mat.texture_paint_slots:
                    row.prop(mat, 'use_textures', text='', index=ts_idx)

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
    z_keybind_found = False

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

        # Search for Shift Alt Z keybind
        if kmi.type == 'Z' and kmi.shift and kmi.alt:
            if kmi.idname == 'view3d.yp_material_shade_toggle':
                z_keybind_found = True
                kmi.active = True
            else:
                # Deactivate other Shift Alt Z keybind
                kmi.active = False

    # Set F4 Keybind
    if not f4_keybind_found:
        new_shortcut = km.keymap_items.new('paint.yp_image_paint_toggle', 'F4', 'PRESS')

    # Set Shift Alt Z keybind
    if not z_keybind_found:
        new_shortcut = km.keymap_items.new('view3d.yp_material_shade_toggle', 'Z', 'PRESS', shift=True, alt=True)

# OPERATORS for keybinds
class ToggleImagePaintMode(bpy.types.Operator):
    bl_idname = "paint.yp_image_paint_toggle"
    bl_label = "Toggle Image Paint Mode"
    bl_description = "Toggle Image Paint Mode"

    @classmethod
    def poll(cls, context):
        return context.area.type == 'IMAGE_EDITOR'
    
    def execute(self, context):
        space = context.space_data
        if space.mode == 'VIEW':
            space.mode = 'PAINT'
        elif space.mode == 'PAINT':
            space.mode = 'VIEW'
        elif space.mode == 'MASK':
            space.mode = 'VIEW'
        return {'FINISHED'}

class ToggleMaterialShade(bpy.types.Operator):
    bl_idname = "view3d.yp_material_shade_toggle"
    bl_label = "Toggle Material Shade View"
    bl_description = "Toggle Material Shade View"

    @classmethod
    def poll(cls, context):
        return context.area.type == 'VIEW_3D'

    def execute(self, context):
        space = context.space_data
        if space.viewport_shade != 'MATERIAL':
            space.viewport_shade = 'MATERIAL'
        else:
            space.viewport_shade = 'SOLID'
        return {'FINISHED'}

# PROPS
class ScreenYPanelProps(bpy.types.PropertyGroup):
    # Settings
    uncollapsed_shading_setting = StringProperty(default='')
    uncollapsed_diffuse_setting = StringProperty(default='')
    uncollapsed_specular_setting = StringProperty(default='')
    uncollapsed_alpha_setting = StringProperty(default='')
    uncollapsed_generated_image_setting = StringProperty(default='')
    uncollapsed_blend_setting = StringProperty(default='')
    uncollapsed_uv_setting = StringProperty(default='')

    uncollapsed_bake_settings = StringProperty(default='')
    uncollapsed_bake_global_setting = StringProperty(default='')

    #uncollapsed_bake_ao_setting = StringProperty(default='')
    #uncollapsed_bake_normal_setting = StringProperty(default='')
    #uncollapsed_bake_vertex_color_setting = StringProperty(default='')
    #uncollapsed_bake_lights_setting = StringProperty(default='')
    #uncollapsed_bake_diffuse_color_setting = StringProperty(default='')
    #uncollapsed_bake_specular_color_setting = StringProperty(default='')

    uncollapsed_viewport_visual_setting = StringProperty(default='')
    uncollapsed_ssao_setting = StringProperty(default='')
    uncollapsed_dof_setting = StringProperty(default='')
    uncollapsed_matcap_setting = StringProperty(default='')
    uncollapsed_viewcam_setting = StringProperty(default='')
    uncollapsed_simplify_setting = StringProperty(default='')

    # Main Panels
    collapsed_shading_panel = StringProperty(default='')
    collapsed_mode_panel = StringProperty(default='')
    collapsed_material_mask_recover = StringProperty(default='')

    uncollapsed_main_ypanel = StringProperty(default='')
    uncollapsed_object_setting = StringProperty(default='')
    uncollapsed_material_mask = StringProperty(default='')
    uncollapsed_material_panel = StringProperty(default='')
    uncollapsed_paint_slots = StringProperty(default='')
    uncollapsed_bake_tools = StringProperty(default='')

    uncollapsed_symmetry_lock = StringProperty(default='')
    uncollapsed_curve_panel = StringProperty(default='')
    uncollapsed_dyntopo_panel = StringProperty(default='')
    uncollapsed_multires_panel = StringProperty(default='')

    # Header extra panel
    uncollapsed_header_extra = StringProperty(default='')

# REGISTERS
def register():
    # Custom Icon
    global custom_icons
    custom_icons = bpy.utils.previews.new()
    custom_icons.load('asterisk', get_addon_filepath() + 'asterisk_icon.png', 'IMAGE')

    # Operators
    bpy.utils.register_module(__name__)

    # Properties
    bpy.types.Screen.yp_props = PointerProperty(type=ScreenYPanelProps)
    #bpy.types.Material.yp_props = PointerProperty(type=MaterialYPanelProps)

    # Extras
    paint_slots.register()
    material_override.register()
    bake_tools.register()
    header_extras.register()

    # Keybind
    set_keybind()

def unregister():
    # Custom Icon
    global custom_icons
    bpy.utils.previews.remove(custom_icons)
    
    # Extras
    paint_slots.unregister()
    material_override.unregister()
    bake_tools.unregister()
    header_extras.unregister()

    # Operators
    bpy.utils.unregister_module(__name__)

if __name__ == "__main__":
    register()
