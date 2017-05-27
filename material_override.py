import bpy, math, os
from mathutils import *
from bpy.app.handlers import persistent
from bpy.props import *
from .common import *

mo_names = {
        'DIFFUSE': "Diffuse Color",
        'DIFFUSE_SHADED': "Diffuse Shaded",
        'LIGHTING_ONLY': "Lighting Only",
        'SPECULAR': "Specular Color",
        'SPECULAR_SHADED': "Specular Shaded",
        'NORMAL': "Normal",
        'MATCAP': "Matcap",
        }

mo_icons = {
        'DIFFUSE': "POTATO",
        'DIFFUSE_SHADED': "MATERIAL",
        'LIGHTING_ONLY': "SMOOTH",
        'SPECULAR': "POTATO",
        'SPECULAR_SHADED': "MATERIAL",
        'NORMAL': "MATCAP_23",
        'MATCAP': "MATCAP_06",
        }

def load_matcap_image(img_name):

    filepath = get_addon_filepath() + 'lib.blend'

    # Load images
    with bpy.data.libraries.load(filepath) as (data_from, data_to):
        exist_images = [img.name for img in bpy.data.images]
        if img_name not in exist_images:
            data_to.images.append(img_name)

    return bpy.data.images.get(img_name)

def remove_temp_mats():
    temp_mat = bpy.data.materials.get('_temp_mat')

    if temp_mat:
        for o in bpy.data.objects:
            data = o.data
            if hasattr(data, 'materials') and data.materials:
                for i, m in enumerate(data.materials):
                    if data.materials[i] == temp_mat:
                        data.materials.pop(i, update_data=True)
        
        # better delete temp material too
        bpy.data.materials.remove(temp_mat)

def remove_alpha_temps(mats, disable_only=False):
    for m in mats:
        if not m: continue
        for i, ts in enumerate(m.texture_slots):
            if not ts: continue
            if not ts.texture: continue
            if '_alpha_temp_' in ts.texture.name:
                if disable_only:
                    ts.texture_coords = 'GLOBAL'
                    m.use_textures[i] = False
                else:
                    tex = ts.texture
                    img = tex.image
                    m.texture_slots.clear(i)
                    img.user_clear()
                    tex.user_clear()
                    bpy.data.images.remove(img)
                    bpy.data.textures.remove(tex)

def remove_matcap_textures():
    matcap_tex = bpy.data.textures.get('_matcap')
    if not matcap_tex: return

    # Remove matcap texture and images
    matcap_tex.user_clear()
    matcap_img = matcap_tex.image
    matcap_tex.image = None
    if matcap_img.users == 0:
        bpy.data.images.remove(matcap_img)
    bpy.data.textures.remove(matcap_tex)

def add_temp_mats():
    # Temporary material for materialless meshes
    temp_mat = bpy.data.materials.get('_temp_mat')
    if not temp_mat:
        temp_mat = bpy.data.materials.new('_temp_mat')

    # check materialless objects
    for o in bpy.data.objects:
        data = o.data
        if hasattr(data, 'materials') and not data.materials:
            data.materials.append(temp_mat)

    #for me in bpy.data.meshes:
    #    if not me.materials:
    #        me.materials.append(temp_mat)

def new_temp_alpha_tex(texslot):
    mat = texslot.id_data
    img = texslot.texture.image
    alpha_tex = bpy.data.textures.new('_alpha_temp_' + texslot.texture.name, 'IMAGE')
    alpha_tex.image = img.copy()
    alpha_tex.image.name = '_alpha_temp_' + img.name
    new_ts = mat.texture_slots.add()
    new_ts.texture = alpha_tex
    new_ts.texture_coords = 'UV'
    new_ts.use_map_alpha = True
    new_ts.use_map_color_diffuse = False
    new_ts.blend_type = texslot.blend_type
    new_ts.use_rgb_to_intensity = texslot.use_rgb_to_intensity
    new_ts.color = texslot.color
    new_ts.uv_layer = texslot.uv_layer

def get_active_matcap_space_data():

    # Get active area
    screen = bpy.context.screen
    area_id = screen.mo_props.active_index
    area = None

    # If valid index is defined
    if area_id > 0 and area_id < len(screen.areas):
        area = screen.areas[area_id]
        if area.type != 'VIEW_3D':
            area = None

    # If 3d area not found, search for it
    if not area:
        for i, a in enumerate(screen.areas):
            if a.type == 'VIEW_3D':
                screen.mo_props.active_index = i
                area = a
                break

    if area: return area.spaces[0]
    else: return None

def redo_duplicate_alphas(mats, mode):
    for m in mats:
        m.use_transparency = True

        disabled_idx = [int(idx) for idx in m.mo_props.disabled_slots.split()]

        alpha_temp_names = []
        alpha_temp_idx = []
        alpha_enabled_ts = []

        for i, ts in enumerate(m.texture_slots):
            if not ts: continue
            if not ts.texture: continue

            # Skip iteration if alpha temp found and store it to the list
            if '_alpha_temp_' in ts.texture.name:
                alpha_temp_names.append(ts.texture.name)
                alpha_temp_idx.append(i)
                continue

            if ts.use_map_alpha and i in disabled_idx:
                alpha_enabled_ts.append(ts)

        # Create temp alpha if it isn't already there
        for i, ats in enumerate(alpha_enabled_ts):
            if '_alpha_temp_' + ats.texture.name in alpha_temp_names:
                idx = alpha_temp_idx[i]
                m.use_textures[idx] = True
                m.texture_slots[idx].texture_coords = 'UV'
            else: 
                new_temp_alpha_tex(ats)

# Remove matcap texture and bring back material state
def bring_materials_to_original_state(mats, old_mode = ''):
    props = bpy.context.scene.mo_props
    
    for m in mats:
        if not m: continue

        # Restore material state
        m.use_shadeless = m.mo_props.original_use_shadeless
        m.use_nodes = m.mo_props.original_use_nodes
        m.use_transparency = m.mo_props.original_use_transparency
        if old_mode == 'SPECULAR':
            m.specular_color = m.diffuse_color
        if old_mode != 'DIFFUSE_SHADED':
            m.diffuse_intensity = m.mo_props.original_diffuse_intensity
        if old_mode not in {'DIFFUSE_SHADED', 'DIFFUSE'}:
            m.diffuse_color = m.mo_props.original_diffuse_color
        if old_mode != 'SPECULAR_SHADED':
            m.specular_intensity = m.mo_props.original_specular_intensity
        if old_mode == 'LIGHTING_ONLY':
            m.specular_color = m.mo_props.original_specular_color

        # Get indexes
        disabled_idx = [int(idx) for idx in m.mo_props.disabled_slots.split()]
        disabled_unused_idx = [int(idx) for idx in m.mo_props.disabled_unused_slots.split()]
        originally_not_diffuse_texs = [tex for tex in m.mo_props.originally_not_diffuse_texs.split(';') if tex != '']
        diffuse_factor_tex = [tex.split('#')[0] for tex in m.mo_props.original_tex_diffuse_factor.split(';') if tex != '']
        diffuse_factor= [float(tex.split('#')[1]) for tex in m.mo_props.original_tex_diffuse_factor.split(';') if tex != '']

        # Get matcap tex
        matcap_tex = bpy.data.textures.get('_matcap')

        for i, ts in enumerate(m.texture_slots):
            if not ts: continue
            if not ts.texture: continue

            if i in disabled_idx:
                m.use_textures[i] = True
                ts.texture_coords = 'UV'

            if i in disabled_unused_idx:
                ts.texture_coords = 'UV'
            
            if ts.texture.name in originally_not_diffuse_texs:
                ts.use_map_color_diffuse = False
            #else: ts.use_map_color_diffuse = False

            if ts.texture.name in diffuse_factor_tex:
                if old_mode == 'SPECULAR':
                    ts.specular_color_factor = ts.diffuse_color_factor
                if old_mode == 'NORMAL':
                    ts.normal_factor = ts.diffuse_color_factor
                idx = diffuse_factor_tex.index(ts.texture.name)
                ts.diffuse_color_factor = diffuse_factor[idx]

            if ts.texture.name == m.mo_props.originally_use_alpha_tex:
                ts.texture.use_alpha = True

            # Clear matcap ts
            if matcap_tex and ts.texture == matcap_tex:
                m.texture_slots.clear(i)

        m.mo_props.disabled_slots = ''
        m.mo_props.disabled_unused_slots = ''
        m.mo_props.originally_not_diffuse_texs = ''
        m.mo_props.original_tex_diffuse_factor = ''
        m.mo_props.original_use_shadeless = False
        m.mo_props.original_use_nodes = False
        m.mo_props.original_use_transparency = False

def override_materials(mode, mats):

    scene = bpy.context.scene
    props = scene.mo_props
    screen = bpy.context.screen
    area = bpy.context.area

    # Define channel mattered for override
    if mode in {'DIFFUSE', 'DIFFUSE_SHADED'}: channel_matters = 'use_map_color_diffuse'
    elif mode in {'SPECULAR', 'SPECULAR_SHADED'}: channel_matters = 'use_map_color_spec'
    elif mode in {'NORMAL', 'MATCAP'}: channel_matters = 'use_map_normal'

    # Save original state of all materials
    for m in bpy.data.materials:
        if m.use_shadeless:
            m.mo_props.original_use_shadeless = True
        if m.use_nodes:
            m.mo_props.original_use_nodes = True
        if m.use_transparency:
            m.mo_props.original_use_transparency = True
        
        m.mo_props.original_diffuse_color = m.diffuse_color
        m.mo_props.original_specular_color = m.specular_color
        m.mo_props.original_diffuse_intensity = m.diffuse_intensity
        m.mo_props.original_specular_intensity = m.specular_intensity
    
    # Save objects active material name
    for o in scene.objects:
        if o.active_material and o.mo_props.active_material_name != o.active_material.name:
            o.mo_props.active_material_name = o.active_material.name

    # Populate lightmap substrings
    if mode == 'LIGHTING_ONLY':
        lightmap_substrings = ['_lm', '_lightmap']
        lightmap_substrings.append(scene.bt_props.ao_suffix.lower())
        #lightmap_substrings.append(scene.bt_props.lights_suffix.lower())

    # Disable other channel on paint slot
    for m in mats:
        if not m: continue

        # Make material shadeless
        if mode not in {'DIFFUSE_SHADED', 'SPECULAR_SHADED', 'LIGHTING_ONLY'}:
            m.use_shadeless = True

        # Material override still not supporting nodes
        m.use_nodes = False

        if not props.keep_alpha:
            m.use_transparency = False
        
        if mode == 'DIFFUSE_SHADED':
            m.specular_intensity = 0.0 

        if mode == 'SPECULAR_SHADED':
            m.diffuse_intensity = 0.0 
            if m.use_shadeless:
                m.diffuse_color = Color((0.0, 0.0, 0.0))

        if mode == 'SPECULAR':
            m.diffuse_color = m.specular_color

        if mode == 'NORMAL':
            #m.diffuse_color = Color((0.22, 0.22, 1.0))
            m.diffuse_color = Color((0.0, 0.0, 1.0))
        
        if mode == 'LIGHTING_ONLY':
            m.diffuse_color = Color((1.0, 1.0, 1.0))
            m.specular_color = Color((0.0, 0.0, 0.0))

        # Flag for first normal found
        first_normal_found = False

        # List of alpha enabled related textures
        alpha_temp_names = []
        alpha_temp_idx = []
        alpha_enabled_ts = []

        for i, ts in enumerate(m.texture_slots):

            if not ts: continue
            if not ts.texture: continue
            if ts.texture.type != 'IMAGE': continue

            # Skip iteration for alpha only texture on diffuse mode
            if mode in {'DIFFUSE', 'DIFFUSE_SHADED'} and ts.use_map_alpha and not ts.use_map_color_diffuse:
                continue

            if mode in {'DIFFUSE_SHADED', 'SPECULAR_SHADED', 'LIGHTING_ONLY'} and ts.use_map_normal:
                continue

            if mode not in {'MATCAP', 'NORMAL'} and ts.use_stencil:
                continue

            #if (mode == 'LIGHTING_ONLY' and ts.texture.type == 'IMAGE' and ts.texture.image and 
            if (mode == 'LIGHTING_ONLY' and ts.texture.image and 
                any([x for x in lightmap_substrings if os.path.splitext(ts.texture.image.name)[0].lower().endswith(x)])):
                continue

            # Skip iteration if alpha temp found and store it to the list
            if '_alpha_temp_' in ts.texture.name:
                alpha_temp_names.append(ts.texture.name)
                alpha_temp_idx.append(i)
                continue

            # Store alpha enabled texture slot
            if props.keep_alpha and mode not in {'DIFFUSE'} and m.mo_props.original_use_transparency:
                if ts.use_map_alpha and m.use_textures[i]:
                    alpha_enabled_ts.append(ts)

            # Disable not related channel
            if mode == 'LIGHTING_ONLY' or not getattr(ts, channel_matters):
                ts.texture_coords = 'GLOBAL'
                if m.use_textures[i]:
                    m.use_textures[i] = False
                    m.mo_props.disabled_slots += str(i) + ' '
                else: m.mo_props.disabled_unused_slots += str(i) + ' '
                continue

            # Except matcap override is chosen, use diffuse channel
            if mode not in {'DIFFUSE_SHADED', 'SPECULAR_SHADED', 'MATCAP'} and not ts.use_map_color_diffuse:
                m.mo_props.originally_not_diffuse_texs += ts.texture.name + ';'
                ts.use_map_color_diffuse = True

            # Disable alpha channel on first normal
            if mode == 'NORMAL' and ts.use_map_normal: 
                if ts.texture.use_alpha and not first_normal_found:
                    ts.texture.use_alpha = False
                    m.mo_props.originally_use_alpha_tex = ts.texture.name
                first_normal_found = True
            
            if mode == 'SPECULAR' and ts.use_map_color_spec:
                m.mo_props.original_tex_diffuse_factor += ts.texture.name + '#' + str(ts.diffuse_color_factor) + ';'
                ts.diffuse_color_factor = ts.specular_color_factor

            if mode == 'NORMAL' and ts.use_map_normal:
                m.mo_props.original_tex_diffuse_factor += ts.texture.name + '#' + str(ts.diffuse_color_factor) + ';'
                ts.diffuse_color_factor = ts.normal_factor

        # Create temp alpha if it isn't already there
        if mode not in {'DIFFUSE', 'DIFFUSE_SHADED'}: 
            for i, ats in enumerate(alpha_enabled_ts):
                if '_alpha_temp_' + ats.texture.name in alpha_temp_names:
                    idx = alpha_temp_idx[i]
                    m.use_textures[idx] = True
                    m.texture_slots[idx].texture_coords = 'UV'
                else:
                    new_temp_alpha_tex(ats)

    if mode == 'MATCAP':
        # Store screen area index if not called from scene update
        if area:
            for i, a in enumerate(screen.areas):
                if a == area:
                    screen.mo_props.active_index = i

        # load matcap image
        space = bpy.context.space_data
        if not space or space.type != 'VIEW_3D': 
            space = get_active_matcap_space_data()
        matcap_icon = space.matcap_icon
        img_name = 'mc' + matcap_icon + '.jpg'
        matcap_img = bpy.data.images.get(img_name)
        if not matcap_img:
            matcap_img = load_matcap_image(img_name)

        # Create new texture if needed
        matcap_tex = bpy.data.textures.get('_matcap')
        if not matcap_tex:
            matcap_tex = bpy.data.textures.new('_matcap', 'IMAGE')
            matcap_tex.image = matcap_img

        # Toggle materials
        for m in mats:
            
            if not m: continue
            matcap_found = False
            
            for ts in m.texture_slots:
                if not ts: continue
                if ts.texture == matcap_tex:
                    matcap_found = True
            
            # apply matcap to material
            if not matcap_found:
                add_tex_to_last_texture_slot(m, matcap_tex, 'NORMAL')

def add_tex_to_last_texture_slot(mat, tex, tex_coords='UV'):
    new_ts = None
    for i in range(17, 0, -1):
        if not mat.texture_slots[i]:
            new_ts = mat.texture_slots.create(i)
            break
    if new_ts:
        new_ts.texture = tex
        new_ts.texture_coords = tex_coords

class ChangeActiveViewportMaterialOverride(bpy.types.Operator):
    bl_idname = "view3d.yp_change_view_id"
    bl_label = "Change active viewport"
    bl_description = "Change active viewport index for material override"

    @classmethod
    def poll(cls, context):
        return context.area.type == 'VIEW_3D'
    
    def execute(self, context):
        screen = context.screen
        area = context.area
        screen.mo_props.active_index = [i for i, a in enumerate(screen.areas) if a == area][0]
        return {'FINISHED'}

class RefreshPaintSlots(bpy.types.Operator):
    bl_idname = "material.yp_refresh_paint_slots"
    bl_label = "Refresh Texture Paint Slots"
    bl_description = "Refresh Texture Paint Slots"

    all_materials = BoolProperty(default=True)

    def texture_mode_and_back_again(self):
        if self.old_mode == 'TEXTURE_PAINT':
            bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.object.mode_set(mode='TEXTURE_PAINT')
        bpy.ops.object.mode_set(mode=self.old_mode)

    @classmethod
    def poll(cls, context):
        #obj = context.object
        #return in_active_layer(obj)
        return True

    def execute(self, context):
        obj = context.object
        scene = context.scene
        area = context.area

        # Remember selection and modes
        if obj: 
            old_active = obj.name
            old_mode = obj.mode
        old_selects = [o for o in context.selected_objects]

        # Halt update
        scene.mo_props.halt_update = True

        # Switch area to view3d
        old_area_type = area.type
        area.type = 'VIEW_3D'

        # Refresh all materials option
        if self.all_materials:
            mats = bpy.data.materials
        elif obj and obj.type == 'MESH':
            #mats = obj.data.materials
            mats = [get_active_material()]

        if not mats: return {'FINISHED'}

        if obj:
            bpy.ops.object.mode_set(mode='OBJECT')
            bpy.ops.object.select_all(action='DESELECT')

        # Create temporary object to store all materials
        bpy.ops.mesh.primitive_cube_add()
        temp_obj = context.object
        temp_obj.select = True

        # List for store material index that use nodes
        originally_use_nodes = []

        for m in mats:

            # Append the use nodes list
            if m.use_nodes:
                originally_use_nodes.append(True)
            else: originally_use_nodes.append(False)

            # Disable nodes because it's necessary
            m.use_nodes = False

            # Add material to temporary object
            temp_obj.data.materials.append(m)

        #return {'FINISHED'}

        # Refresh paint slots by set this variable
        #scene.tool_settings.image_paint.mode = 'MATERIAL'

        # Refresh paint slots by go to texture paint mode
        bpy.ops.object.mode_set(mode='TEXTURE_PAINT')
        bpy.ops.object.mode_set(mode='OBJECT')

        # Bring back material which originally use nodes
        for i, m in enumerate(mats):
            m.use_nodes = originally_use_nodes[i]

        # Delete temporary thingies
        temp_obj.data.materials.clear()
        bpy.ops.object.delete()

        # Restore selection
        for o in old_selects:
            o.select = True
        if obj:
            scene.objects.active = scene.objects.get(old_active)
            if in_active_layer(obj):
                bpy.ops.object.mode_set(mode=old_mode)

        # Do not update image editor hack
        if obj and obj.type == 'MESH' and obj.active_material:
            obj.active_material.paint_active_slot = obj.active_material.paint_active_slot

        # Bring back area type
        area.type = old_area_type

        # Enable update again
        scene.mo_props.halt_update = False

        return {"FINISHED"}

def remember_selected_paint_image():
    for m in bpy.data.materials:
        if m.paint_active_slot < len(m.texture_paint_images):
            m.mo_props.selected_image = m.texture_paint_images[m.paint_active_slot].name

def keep_selected_paint_image():
    for m in bpy.data.materials:
        for i, img in enumerate(m.texture_paint_images):
            if img.name == m.mo_props.selected_image:
                m.paint_active_slot = i
        m.mo_props.selected_image = ''

def make_image_editor_use_image_from_active_material(mode):
    obj = bpy.context.object
    screen = bpy.context.screen

    if not obj: return
    mat = obj.active_material

    if not mat: return
    if len(mat.texture_paint_images) < 1: return

    ps_idx = mat.paint_active_slot
    img = mat.texture_paint_images[ps_idx]

    ts_idx = mat.texture_paint_slots[ps_idx].index
    ts = mat.texture_slots[ts_idx]

    # Check if active paint slot is not using proper influence
    attr = ''
    if mode in {'DIFFUSE', 'DIFFUSE_SHADED'} and not ts.use_map_color_diffuse:
        attr = 'color_diffuse'
    elif mode in {'SPECULAR', 'SPECULAR_SHADED'} and not ts.use_map_color_spec:
        attr = 'color_spec'
    elif mode in {'NORMAL', 'MATCAP'} and not ts.use_map_normal:
        attr = 'normal'
    
    # Search for other image if above condition is met
    if attr != '':
        for i, ps_slot in enumerate(mat.texture_paint_slots):
            slot_idx = ps_slot.index
            slot = mat.texture_slots[slot_idx]
            if getattr(slot, 'use_map_' + attr):
                mat.paint_active_slot = i
                img = slot.texture.image
                break

    # Change image on the image editor
    for i, a in enumerate(screen.areas):
        space = a.spaces[0]
        if a.type == 'IMAGE_EDITOR' and not space.use_image_pin:
            space.image = img

class OverrideMaterialMenuEnum(bpy.types.Operator):
    bl_idname = "material.yp_override_material_menu_enum"
    bl_label = "Toggle Matcap Material Menu"
    bl_description = "Toggle all materials to use special material"
    bl_options = {'REGISTER', 'UNDO'}

    mode = EnumProperty(
        name = 'Mode',
        items = (('DIFFUSE', "Diffuse Color", "", 'POTATO', 0),
                 ('DIFFUSE_SHADED', "Diffuse Shaded", "", 'MATERIAL', 1),
                 ('SPECULAR', "Specular Color", "", 'POTATO', 2),
                 ('SPECULAR_SHADED', "Specular Shaded", "", 'MATERIAL', 3),
                 ('NORMAL', "Normal", "", 'MATCAP_23', 4 ),
                 ('MATCAP', "Matcap", "", 'MATCAP_06', 5),
                 ('LIGHTING_ONLY', "Lighting Only", "", 'SMOOTH', 6)),
        default = 'MATCAP')

    @classmethod
    def poll(cls, context):
        return context.scene.render.engine != 'CYCLES'

    def execute(self, context):
        bpy.ops.material.yp_override_material(mode=self.mode)
        return {'FINISHED'}

class OverrideMaterial(bpy.types.Operator):
    bl_idname = "material.yp_override_material"
    bl_label = "Toggle Matcap Material"
    bl_description = "Toggle all materials to use special material"
    bl_options = {'REGISTER', 'UNDO'}

    mode = EnumProperty(
        name = 'Mode',
        items = (('DIFFUSE', "Diffuse", ""),
                 ('DIFFUSE_SHADED', "Diffuse Shaded", ""),
                 ('LIGHTING_ONLY', "Lighting Only", ""),
                 ('SPECULAR', "Specular", ""),
                 ('SPECULAR_SHADED', "Specular Shaded", ""),
                 ('NORMAL', "Normal", ""),
                 ('MATCAP', "Matcap", ""),
                 ('OFF',  "Off", "")),
        default = 'OFF')

    @classmethod
    def poll(cls, context):
        return context.scene.render.engine != 'CYCLES'

    def execute(self, context):

        obj = context.object
        scene = context.scene
        props = scene.mo_props

        #if not obj:
        #    return {'FINISHED'}

        if hasattr(obj, 'active_material'):
            mat = obj.active_material
            if mat and mat.use_nodes:
                self.report({'WARNING'}, "Material override isn't supporting nodes, will use non-node material instead")

        # Restore all materials state first:
        if props.override_mode != 'OFF':
            if props.all_materials:
                mats = bpy.data.materials
            else: 
                #mats = [ms.material for ms in obj.material_slots]
                mats = [obj.active_material]
            remove_alpha_temps(mats, disable_only=True)
            remember_selected_paint_image()
            bring_materials_to_original_state(mats, props.override_mode)

        # Delete old matcap texture
        if props.override_mode == 'MATCAP':
            # Dangerous function!
            remove_matcap_textures()

        # Store override information
        props.override_mode = self.mode

        # Store object & material name
        if obj:
            props.active_object_name = obj.name
        #obj.mo_props.active_material_name = obj.active_material.name

        # Just delete temp mats and return if disable override
        if self.mode == 'OFF':
            mats = bpy.data.materials
            remove_alpha_temps(mats)
            remove_temp_mats()

            bpy.ops.material.yp_refresh_paint_slots()
            keep_selected_paint_image()
            make_image_editor_use_image_from_active_material(self.mode)

            return {'FINISHED'}

        # Reset lazy props
        props.lazy_keep_alpha = props.keep_alpha
        props.lazy_all_materials = props.all_materials

        # Add temp mats for materialess objects
        if props.all_materials:
            add_temp_mats()

        # Populate materials
        if props.all_materials:
            mats = bpy.data.materials
        else: 
            #mats = [ms.material for ms in obj.material_slots]
            mats = [obj.active_material]

        remember_selected_paint_image()
        override_materials(self.mode, mats)
        
        bpy.ops.material.yp_refresh_paint_slots()
        keep_selected_paint_image()
        make_image_editor_use_image_from_active_material(self.mode)

        return {'FINISHED'}

# UPDATE HANDLERS
@persistent
def change_matcap_event(scene):

    if not hasattr(bpy.context, 'object'):
        return

    obj = bpy.context.object
    gs = scene.game_settings 
    props = scene.mo_props

    if scene.mo_props.halt_update: return

    if props.override_mode == 'MATCAP':

        space = get_active_matcap_space_data()
        if not space: return
        
        if (space.viewport_shade == 'MATERIAL' or
            (space.viewport_shade == 'TEXTURED' and gs.material_mode == 'GLSL')):
            
            matcap_icon = space.matcap_icon
            img_name = 'mc' + matcap_icon + '.jpg'

            # if matcap changed
            matcap_tex = bpy.data.textures.get('_matcap')
            if matcap_tex.image.name != img_name:
                temp_name = matcap_tex.image.name
                matcap_tex.image = None
                bpy.data.images.remove(bpy.data.images[temp_name])

                matcap_img = load_matcap_image(img_name)
                matcap_tex.image = matcap_img

    if props.override_mode != 'OFF':

        # List of last operator used
        ops = bpy.context.window_manager.operators

        # Automatically add temp material to new mesh object
        if ops and 'MESH_OT' in ops[-1].bl_idname and not obj.data.materials:

            temp_mat = bpy.data.materials.get('_temp_mat')
            if not temp_mat:
                temp_mat = bpy.data.materials.new('_temp_mat')
                temp_mat.use_shadeless = True

                if props.override_mode == 'MATCAP':
                    add_tex_to_last_texture_slot(temp_mat, matcap_tex, 'NORMAL')

            obj.data.materials.append(temp_mat)
        
        # Action when keep alpha is changing
        if props.lazy_keep_alpha != props.keep_alpha:
            if props.all_materials:
                mats = bpy.data.materials
            else: 
                #mats = [ms.material for ms in obj.material_slots]
                mats = [obj.active_material]

            if props.keep_alpha:
                redo_duplicate_alphas(mats, props.override_mode)
            else:
                for m in mats: m.use_transparency = False
                remove_alpha_temps(mats, disable_only=True)
            props.lazy_keep_alpha = props.keep_alpha

        # Action when all materials is changing
        if props.lazy_all_materials != props.all_materials:

            if props.all_materials:
                #mats = [ms.material for ms in obj.material_slots]
                mats = [obj.active_material]
            else: mats = bpy.data.materials

            bring_materials_to_original_state(mats, props.override_mode)

            if props.all_materials:
                mats = bpy.data.materials
            else: 
                #mats = [ms.material for ms in obj.material_slots]
                mats = [obj.active_material]

            override_materials(props.override_mode, mats)

            props.lazy_all_materials = props.all_materials

        # Action when active object is changing
        if obj and props.active_object_name != obj.name:

            # Change material of selected object
            if not props.all_materials:
                old_obj = bpy.data.objects.get(props.active_object_name)
                if old_obj and old_obj.active_material:
                    #mats = [ms.material for ms in old_obj.material_slots]
                    mats = [old_obj.active_material]
                    remove_alpha_temps(mats, disable_only=True)
                    bring_materials_to_original_state(mats, props.override_mode)
                
                #mats = [ms.material for ms in obj.material_slots]
                if obj.active_material:
                    mats = [obj.active_material]
                    override_materials(props.override_mode, mats)

                #old_mode = obj.mode
                #bpy.ops.object.mode_set(mode='TEXTURE_PAINT')
                #bpy.ops.object.mode_set(mode=old_mode)

            props.active_object_name = obj.name

        # Action when active active material is changing
        if obj and obj.active_material and obj.mo_props.active_material_name != obj.active_material.name:

            # Change material of selected material
            if not props.all_materials:
                old_mat = bpy.data.materials.get(obj.mo_props.active_material_name)
                if old_mat:
                    mats = [old_mat]
                    remove_alpha_temps(mats, disable_only=True)
                    bring_materials_to_original_state(mats, props.override_mode)

                mats = [obj.active_material]
                override_materials(props.override_mode, mats)
                
            obj.mo_props.active_material_name = obj.active_material.name

# PANELS
def draw_material_recover_panel(self, context):
    if context.scene.mo_props.override_mode != 'OFF':
        c = self.layout.column()
        c.alert = True
        c.operator("material.yp_override_material", text="Recover All Materials & Textures!", icon='CANCEL').mode = 'OFF'
        c.alert = False

# PROPS

class ScreenMaterialOverrideProps(bpy.types.PropertyGroup):
    active_index = IntProperty(default=-1)

class SceneMaterialOverrideProps(bpy.types.PropertyGroup):
    override_mode = EnumProperty(
        items = (('DIFFUSE', "Diffuse", ""),
                 ('DIFFUSE_SHADED', "Diffuse Shaded", ""),
                 ('LIGHTING_ONLY', "Lighting Only", ""),
                 ('SPECULAR', "Specular", ""),
                 ('SPECULAR_SHADED', "Specular Shaded", ""),
                 ('NORMAL', "Normal", ""),
                 ('MATCAP', "Matcap", ""),
                 ('OFF',  "Cancel", "")),
        default = 'OFF')
    keep_alpha = BoolProperty(default=True)
    lazy_keep_alpha = BoolProperty(default=True)
    #keep_normal = BoolProperty(default=True)
    #lazy_keep_normal = BoolProperty(default=True)
    all_materials = BoolProperty(default=True)
    lazy_all_materials = BoolProperty(default=True)
    active_object_name = StringProperty(default='')
    halt_update = BoolProperty(default=False)

class ObjectMaterialOverideProps(bpy.types.PropertyGroup):
    active_material_name = StringProperty(default='')

class MaterialOverrideProps(bpy.types.PropertyGroup):
    original_use_shadeless = BoolProperty(default=False)
    original_use_nodes = BoolProperty(default=False)
    original_use_transparency = BoolProperty(default=False)
    disabled_slots = StringProperty(default='')
    disabled_unused_slots = StringProperty(default='')
    originally_not_diffuse_texs = StringProperty(default='')
    originally_use_alpha_tex = StringProperty(default='')
    original_tex_diffuse_factor = StringProperty(default='')
    #originally_normal_map = StringProperty(default='')
    original_diffuse_color = FloatVectorProperty(
            size=3, subtype='COLOR', default=(0.0,0.0,0.0), min=0.0, max=1.0)
    original_specular_color = FloatVectorProperty(
            size=3, subtype='COLOR', default=(0.0,0.0,0.0), min=0.0, max=1.0)
    original_diffuse_intensity = FloatProperty(default=0.0, min=0.0, max=1.0)
    original_specular_intensity = FloatProperty(default=0.0, min=0.0, max=1.0)
    selected_image = StringProperty(default='')

def register():
    bpy.types.Material.mo_props = PointerProperty(type=MaterialOverrideProps)
    bpy.types.Scene.mo_props = PointerProperty(type=SceneMaterialOverrideProps)
    bpy.types.Screen.mo_props = PointerProperty(type=ScreenMaterialOverrideProps)
    bpy.types.Object.mo_props = PointerProperty(type=ObjectMaterialOverideProps)
    bpy.app.handlers.scene_update_pre.append(change_matcap_event)
    bpy.types.MATERIAL_PT_context_material.append(draw_material_recover_panel)
    bpy.types.TEXTURE_PT_context_texture.append(draw_material_recover_panel)

def unregister():
    bpy.app.handlers.scene_update_pre.remove(change_matcap_event)
    bpy.types.MATERIAL_PT_context_material.remove(draw_material_recover_panel)
    bpy.types.TEXTURE_PT_context_texture.remove(draw_material_recover_panel)
